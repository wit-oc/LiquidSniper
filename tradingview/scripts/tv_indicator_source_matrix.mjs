#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import {
  commandArtifactDir,
  ensureDir,
  loadConfig,
  matrixItems,
  parseArgs,
  resolveFromRoot,
  safeName,
  writeReport,
} from '../../codex/skills/tradingview-pine-loop/scripts/lib/config.mjs';
import { launchTradingView } from '../../codex/skills/tradingview-pine-loop/scripts/lib/browser.mjs';
import {
  addPineToChart,
  checkAuth,
  closePineEditor,
  detectCompileStatus,
  gotoChart,
  openPineEditor,
  saveScreenshot,
  setPineEditorText,
} from '../../codex/skills/tradingview-pine-loop/scripts/lib/actions.mjs';
import { manualSettingsGate, switchSymbolSamePane } from './tv_strategy_text_matrix.mjs';
import { applyV6MappingsToPage } from './tv_apply_v6_mappings.mjs';

function flagEnabled(value) {
  return value === true || value === 'true' || value === '1' || value === 1;
}

async function firstVisible(page, locators) {
  for (const locator of locators) {
    const item = typeof locator === 'string' ? page.locator(locator).first() : locator.first();
    if (await item.isVisible().catch(() => false)) return item;
    const collection = typeof locator === 'string' ? page.locator(locator) : locator;
    const count = Math.min(await collection.count().catch(() => 0), 20);
    for (let index = 0; index < count; index += 1) {
      const candidate = collection.nth(index);
      if (await candidate.isVisible().catch(() => false)) return candidate;
    }
  }
  return null;
}

async function downloadFromAction(page, action, outPath, timeoutMs) {
  let downloadError = null;
  const downloadPromise = page.waitForEvent('download', { timeout: timeoutMs }).catch((error) => {
    downloadError = error;
    return null;
  });
  await action();
  const download = await downloadPromise;
  if (!download) {
    throw new Error(`Download did not start within ${timeoutMs}ms. ${downloadError ? downloadError.message : ''}`.trim());
  }
  await download.saveAs(outPath);
  return outPath;
}

async function exportChartDataFromMainMenu(page, outPath, timeoutMs = 120000) {
  const action = async () => {
    await page.keyboard.press('Escape').catch(() => {});
    await page.waitForTimeout(400);
    const collapseButton = page.locator('[data-name="toggle-visibility-button"]').first();
    if (await collapseButton.isVisible().catch(() => false)) {
      await collapseButton.click({ force: true }).catch(() => {});
      await page.waitForTimeout(700);
    }
    const layoutButton = page.locator('[data-name="save-load-menu"], button[aria-label*="Manage layouts"]').first();
    if (await layoutButton.isVisible().catch(() => false)) {
      await layoutButton.click({ force: true });
    } else {
      await page.mouse.click(1083, 18);
    }
    await page.waitForTimeout(1600);
    const exportData = await firstVisible(page, [
      page.locator('[role="menuitem"]:has-text("Download chart data")'),
      page.locator('text="Download chart data..."'),
      page.locator('text="Download chart data…"'),
      page.getByText(/Download chart data/i),
      page.getByText(/Export chart data/i),
      page.getByText(/Export data/i),
      page.getByRole('menuitem', { name: /Download chart data|Export chart data|Export data|Export/i }),
    ]);
    if (!exportData) {
      const bodyText = await page.locator('body').innerText({ timeout: 5000 }).catch(() => '');
      throw new Error(`Could not find chart data export control from layout menu. Visible text sample: ${bodyText.slice(0, 1200)}`);
    }
    await exportData.click({ force: true });
    await page.waitForTimeout(1200);
    const confirm = await firstVisible(page, [
      page.getByRole('button', { name: /^Download$/i }),
      page.getByRole('button', { name: /^Export$/i }),
      page.locator('button:has-text("Download")'),
      page.locator('button:has-text("Export")'),
    ]);
    if (confirm) await confirm.click({ force: true });
  };
  return downloadFromAction(page, action, outPath, timeoutMs);
}

const args = parseArgs();
const loaded = loadConfig(args);
const outDir = commandArtifactDir(loaded.artifactsDir, loaded.runId, 'indicator-source-matrix');
const scriptPath = resolveFromRoot(loaded.root, args.script || loaded.run.scriptPath);
const source = fs.readFileSync(scriptPath, 'utf8');
const setupGate = manualSettingsGate(loaded, args);
const applySourceMappings =
  flagEnabled(args['apply-v6-mappings-each-symbol']) ||
  flagEnabled(args['apply-v6-mappings']) ||
  flagEnabled(loaded.run.applyV6MappingsEachSymbol);
const samePaneSymbolSwitch = flagEnabled(args['same-pane-symbol-switch']) || flagEnabled(loaded.run.samePaneSymbolSwitch);
const reuseMappingsAfterSamePaneSwitch = samePaneSymbolSwitch && loaded.run.reuseV6MappingsAfterSamePaneSwitch !== false;
const onlySymbol = typeof args['only-symbol'] === 'string' ? args['only-symbol'] : null;
const items = onlySymbol
  ? matrixItems(loaded.run).filter((item) => item.symbol === onlySymbol)
  : matrixItems(loaded.run);

if (setupGate.status !== 'ok') {
  const report = {
    status: setupGate.status,
    command: 'tv-indicator-source-matrix',
    runId: loaded.runId,
    outDir,
    scriptPath,
    setupGate,
    results: [],
  };
  writeReport(path.join(outDir, 'indicator-source-matrix-report.json'), report);
  console.log(JSON.stringify(report, null, 2));
  process.exitCode = 1;
} else {
  let context;

  try {
    const browser = await launchTradingView({ defaults: loaded.defaults, artifactsDir: outDir });
    context = browser.context;
    const page = browser.page;
    const results = [];
    let chartLoaded = false;
    let installedAndMapped = false;

    for (const item of items) {
      const itemDir = path.join(outDir, safeName(item.symbol), safeName(item.label));
      ensureDir(itemDir);
      const result = { ...item, status: 'unknown', scriptPath };
      try {
        if (!samePaneSymbolSwitch || !chartLoaded) {
          result.url = await gotoChart(page, loaded.run, item.symbol, item.interval);
          const auth = await checkAuth(page);
          if (!auth.authenticated) throw new Error(`TradingView session is not authenticated: ${auth.url}`);
          await page.waitForTimeout(Number(loaded.run.waitAfterLoadMs || loaded.defaults.waitAfterLoadMs || 8000));
          chartLoaded = true;
        } else {
          result.symbolSwitch = await switchSymbolSamePane(page, item, loaded);
          result.url = page.url();
        }
        if (!samePaneSymbolSwitch || !installedAndMapped) {
          await openPineEditor(page);
          result.editor = await setPineEditorText(page, source);
          await addPineToChart(page);
          result.compile = await detectCompileStatus(page);
          await closePineEditor(page).catch(() => {});
          if (applySourceMappings) {
            result.mapping = await applyV6MappingsToPage(page, loaded.run.expectedStrategyTitle || loaded.run.scriptTitle || '', {
              mappings: loaded.run.v6Mappings,
            });
            if (result.mapping.status !== 'ok') {
              throw new Error(`Source mapping failed for ${item.symbol} ${item.label}`);
            }
          }
          installedAndMapped = true;
        } else if (applySourceMappings && reuseMappingsAfterSamePaneSwitch) {
          result.mapping = {
            status: 'ok',
            reused: true,
            reason: 'Same-pane symbol switch reused the already mapped indicator instance.',
          };
        }
        await page.waitForTimeout(Number(loaded.run.waitBeforeExportMs || 2500));
        result.screenshot = path.join(itemDir, 'chart.png');
        await saveScreenshot(page, result.screenshot);
        const chartCsv = path.join(itemDir, `${safeName(item.symbol)}_${safeName(item.label)}_chart.csv`);
        result.chartData = {
          path: await exportChartDataFromMainMenu(page, chartCsv, Number(args.downloadTimeoutMs || loaded.defaults.downloadTimeoutMs || 120000)),
        };
        result.status = 'ok';
      } catch (error) {
        result.status = 'failed';
        result.error = String(error.stack || error);
        result.screenshot = path.join(itemDir, 'failure.png');
        await saveScreenshot(page, result.screenshot).catch(() => {});
      }
      results.push(result);
    }

    const report = {
      status: results.every((result) => result.status === 'ok') ? 'ok' : 'failed',
      command: 'tv-indicator-source-matrix',
      runId: loaded.runId,
      outDir,
      setupGate,
      applySourceMappings,
      samePaneSymbolSwitch,
      reuseMappingsAfterSamePaneSwitch,
      itemCount: items.length,
      results,
    };
    writeReport(path.join(outDir, 'indicator-source-matrix-report.json'), report);
    console.log(JSON.stringify(report, null, 2));
    if (report.status === 'failed') process.exitCode = 1;
  } catch (error) {
    const report = { status: 'failed', command: 'tv-indicator-source-matrix', runId: loaded.runId, error: String(error.stack || error) };
    writeReport(path.join(outDir, 'indicator-source-matrix-report.json'), report);
    console.log(JSON.stringify(report, null, 2));
    process.exitCode = 1;
  } finally {
    await context?.close().catch(() => {});
  }
}
