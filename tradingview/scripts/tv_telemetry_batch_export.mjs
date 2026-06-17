#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import {
  commandArtifactDir,
  loadConfig,
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
  savePineScript,
  saveScreenshot,
  setPineEditorText,
} from '../../codex/skills/tradingview-pine-loop/scripts/lib/actions.mjs';
import { openStrategySettings, rowValue } from './tv_apply_v6_mappings.mjs';

const BATCHES = {
  'oracle-strength-smoke': [
    ['Slot 01', 'The Oracle Strength - [Unity] - V2: Oracle Strength'],
    ['Slot 02', 'The Oracle Strength - [Unity] - V2: Plot', 1],
    ['Slot 03', 'The Oracle Strength - [Unity] - V2: Histogram'],
    ['Slot 04', 'The Oracle Strength - [Unity] - V2: MACD'],
    ['Slot 05', 'The Oracle Strength - [Unity] - V2: Signal'],
  ],
  'oracle-strength-plots-1': [
    ['Slot 01', 'The Oracle Strength - [Unity] - V2: Plot', 1],
    ['Slot 02', 'The Oracle Strength - [Unity] - V2: Plot', 2],
    ['Slot 03', 'The Oracle Strength - [Unity] - V2: Plot', 3],
    ['Slot 04', 'The Oracle Strength - [Unity] - V2: Plot', 4],
  ],
  'oracle-strength-plots-2': [
    ['Slot 01', 'The Oracle Strength - [Unity] - V2: Plot', 5],
    ['Slot 02', 'The Oracle Strength - [Unity] - V2: Plot', 6],
    ['Slot 03', 'The Oracle Strength - [Unity] - V2: Plot', 7],
    ['Slot 04', 'The Oracle Strength - [Unity] - V2: Oracle Strength'],
  ],
  'oracle-strength-named': [
    ['Slot 01', 'The Oracle Strength - [Unity] - V2: RSI'],
    ['Slot 02', 'The Oracle Strength - [Unity] - V2: RSI-based MA'],
    ['Slot 03', 'The Oracle Strength - [Unity] - V2: CVD'],
    ['Slot 04', 'The Oracle Strength - [Unity] - V2: Midline'],
    ['Slot 05', 'The Oracle Strength - [Unity] - V2: Upper'],
    ['Slot 06', 'The Oracle Strength - [Unity] - V2: Lower'],
  ],
  'oracle-strength-a2': [
    ['Slot 01', 'The Oracle Strength - [Unity] - V2: Lower'],
    ['Slot 02', 'The Oracle Strength - [Unity] - V2: Upper Bollinger Band'],
    ['Slot 03', 'The Oracle Strength - [Unity] - V2: Lower Bollinger Band'],
  ],
  'oracle-aio-state': [
    ['Slot 01', 'The Oracle AIO - [Unity] - V2: EMA Bullish'],
    ['Slot 02', 'The Oracle AIO - [Unity] - V2: EMA Bearish'],
    ['Slot 03', 'The Oracle AIO - [Unity] - V2: Bullish FVG'],
    ['Slot 04', 'The Oracle AIO - [Unity] - V2: Bearish FVG'],
    ['Slot 05', 'The Oracle AIO - [Unity] - V2: Internal Bullish BOS'],
    ['Slot 06', 'The Oracle AIO - [Unity] - V2: Internal Bullish MSS'],
    ['Slot 07', 'The Oracle AIO - [Unity] - V2: Internal Bearish BOS'],
    ['Slot 08', 'The Oracle AIO - [Unity] - V2: Internal Bearish MSS'],
    ['Slot 09', 'The Oracle AIO - [Unity] - V2: Up trend'],
    ['Slot 10', 'The Oracle AIO - [Unity] - V2: Down Trend'],
    ['Slot 11', 'The Oracle AIO - [Unity] - V2: UpTrend Begins'],
    ['Slot 12', 'The Oracle AIO - [Unity] - V2: DownTrend Begins'],
    ['Slot 13', 'The Oracle AIO - [Unity] - V2: Buy Trend Alert'],
    ['Slot 14', 'The Oracle AIO - [Unity] - V2: Sell Trend Alert'],
    ['Slot 15', 'The Oracle AIO - [Unity] - V2: Plot', 1],
    ['Slot 16', 'The Oracle AIO - [Unity] - V2: Plot', 2],
  ],
  'phase1-structure': [
    ['Slot 01', 'HTF Phase 1 Structure v3.3 (structure-first): Bus BoS Direction'],
    ['Slot 02', 'HTF Phase 1 Structure v3.3 (structure-first): Bus CHoCH Direction'],
    ['Slot 03', 'HTF Phase 1 Structure v3.3 (structure-first): Bus Continuation Break Direction'],
    ['Slot 04', 'HTF Phase 1 Structure v3.3 (structure-first): Bus Weak Break Direction'],
    ['Slot 05', 'HTF Phase 1 Structure v3.3 (structure-first): Bus Regime Direction'],
    ['Slot 06', 'HTF Phase 1 Structure v3.3 (structure-first): BoS'],
    ['Slot 07', 'HTF Phase 1 Structure v3.3 (structure-first): CHoCH'],
    ['Slot 08', 'HTF Phase 1 Structure v3.3 (structure-first): Continuation Break'],
    ['Slot 09', 'HTF Phase 1 Structure v3.3 (structure-first): Weak break'],
  ],
};

async function installPineInCurrentSession(page, loaded, args) {
  const scriptPath = resolveFromRoot(loaded.root, args.script || loaded.run.scriptPath);
  const source = fs.readFileSync(scriptPath, 'utf8');
  const scriptName = args.name || loaded.run.scriptName || `Codex Scratch - ${path.basename(scriptPath, '.pine')}`;
  await openPineEditor(page);
  const editor = await setPineEditorText(page, source);
  await savePineScript(page, scriptName);
  const addToChart = await addPineToChart(page)
    .then(() => ({ status: 'ok' }))
    .catch(async (error) => {
      const bodyText = await page.locator('body').innerText({ timeout: 5000 }).catch(() => '');
      if (bodyText.includes('Unity Telemetry Discovery v1')) {
        return { status: 'already-present-or-no-button', error: String(error.message || error) };
      }
      throw error;
    });
  const compile = await detectCompileStatus(page);
  const closeEditor = await closePineEditor(page).catch((error) => ({ status: 'failed', error: String(error.message || error) }));
  await page.waitForTimeout(1500);
  return { scriptPath, scriptName, editor, addToChart, compile, closeEditor };
}

async function clickRowCombobox(page, labelText) {
  const label = page.getByText(labelText, { exact: true }).first();
  await label.scrollIntoViewIfNeeded();
  await page.waitForTimeout(200);
  const comboBox = await page.evaluate((label) => {
    const compact = (value) => String(value || '').replace(/\s+/g, ' ').trim();
    const labels = [...document.querySelectorAll('body *')]
      .filter((node) => compact(node.textContent) === label)
      .map((node) => {
        const rect = node.getBoundingClientRect();
        return { x: rect.x, y: rect.y, width: rect.width, height: rect.height };
      });
    if (!labels.length) return null;
    const labelRect = labels[0];
    const labelCenter = labelRect.y + labelRect.height / 2;
    return [...document.querySelectorAll('button[role="combobox"]')]
      .map((node) => {
        const rect = node.getBoundingClientRect();
        return {
          x: rect.x,
          y: rect.y,
          width: rect.width,
          height: rect.height,
          distance: Math.abs((rect.y + rect.height / 2) - labelCenter),
        };
      })
      .filter((combo) => combo.x > labelRect.x)
      .sort((a, b) => a.distance - b.distance)[0] || null;
  }, labelText);
  if (!comboBox) throw new Error(`Could not locate combobox for row label: ${labelText}`);
  await page.mouse.click(comboBox.x + comboBox.width / 2, comboBox.y + comboBox.height / 2);
  await page.waitForTimeout(700);
}

async function selectRowSource(page, label, value, occurrence = 1) {
  await clickRowCombobox(page, label);
  const options = page.getByRole('option', { name: value, exact: true });
  const count = await options.count();
  if (count < occurrence) {
    throw new Error(`Option "${value}" occurrence ${occurrence} not found for ${label}; only ${count} visible`);
  }
  const option = options.nth(occurrence - 1);
  await option.scrollIntoViewIfNeeded();
  await option.click();
  await page.waitForTimeout(650);
  return { label, value, occurrence, count };
}

async function applyBatchMappings(page, title, mappings) {
  const openedSettings = await openStrategySettings(page, title);
  const applied = [];
  for (const [label, value, occurrence = 1] of mappings) {
    applied.push(await selectRowSource(page, label, value, occurrence));
  }
  const after = {};
  for (const [label] of mappings) {
    after[label] = await rowValue(page, label);
  }
  await page.getByRole('button', { name: /^Ok$/i }).click();
  await page.waitForTimeout(2500);
  return { openedSettings, applied, after };
}

async function firstVisible(page, locators) {
  for (const locator of locators) {
    const item = typeof locator === 'string' ? page.locator(locator).first() : locator.first();
    if (await item.isVisible().catch(() => false)) return item;
  }
  return null;
}

async function exportChartData(page, outDir, item, batchId, timeoutMs = 120000) {
  const outPath = path.join(outDir, `${safeName(item.symbol)}_${safeName(item.label)}_${safeName(batchId)}_chart.csv`);
  let downloadError = null;
  const downloadPromise = page.waitForEvent('download', { timeout: timeoutMs }).catch((error) => {
    downloadError = error;
    return null;
  });
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(400);
  const panelToggle = page.locator('[data-name="toggle-visibility-button"]').first();
  if (await panelToggle.isVisible().catch(() => false)) {
    const label = await panelToggle.evaluate((element) => [
      element.textContent || '',
      element.getAttribute('aria-label') || '',
      element.getAttribute('title') || '',
    ].join(' ')).catch(() => '');
    if (!/open panel/i.test(label)) {
      await panelToggle.click({ force: true }).catch(() => {});
      await page.waitForTimeout(700);
    }
  }
  const menu = await firstVisible(page, [
    page.locator('[data-name="save-load-menu"]'),
    page.getByRole('button', { name: /Save all charts/i }),
    page.locator('button:has-text("Sherlock-Copy-v3")'),
  ]);
  if (!menu) throw new Error('Could not find layout menu for chart-data export');
  await menu.click();
  await page.waitForTimeout(700);
  const downloadItem = await firstVisible(page, [
    page.getByRole('row', { name: /Download chart data/i }),
    page.locator('[aria-label="Download chart data"]'),
    page.getByText(/Download chart data/i),
    page.getByText(/Export chart data/i),
    page.getByRole('menuitem', { name: /Download chart data|Export chart data/i }),
  ]);
  if (!downloadItem) throw new Error('Could not find Download chart data menu item');
  await downloadItem.click();
  await page.waitForTimeout(1500);
  const maybeDialogButton = await firstVisible(page, [
    page.getByRole('button', { name: /Export|Download/i }),
    page.locator('button:has-text("Export"), button:has-text("Download")'),
  ]);
  if (maybeDialogButton) await maybeDialogButton.click().catch(() => {});
  const download = await downloadPromise;
  if (!download) {
    throw new Error(`Chart data download did not start within ${timeoutMs}ms. ${downloadError ? downloadError.message : ''}`.trim());
  }
  await download.saveAs(outPath);
  const sample = fs.readFileSync(outPath, 'utf8').slice(0, 200);
  if (/^\uFEFF?Trade #,Type,Date and time/i.test(sample)) {
    throw new Error(`Downloaded Strategy Tester trades instead of chart data: ${outPath}`);
  }
  return outPath;
}

async function main() {
  const args = parseArgs();
  const loaded = loadConfig(args);
  const batchId = args.batch || 'oracle-strength-a1';
  const mappings = BATCHES[batchId];
  if (!mappings) throw new Error(`Unknown batch "${batchId}". Available: ${Object.keys(BATCHES).join(', ')}`);
  const outDir = commandArtifactDir(loaded.artifactsDir, loaded.runId, `telemetry-${batchId}`);
  const title = args.title || loaded.run.scriptTitle || 'Unity Telemetry Discovery v1';
  let context;
  let page;

  try {
    const browser = await launchTradingView({ defaults: loaded.defaults, artifactsDir: outDir });
    context = browser.context;
    page = browser.page;
    const item = {
      symbol: loaded.run.symbols?.[0] || 'BINANCE:BTCUSDT',
      interval: loaded.run.timeframes?.[0]?.interval || '15',
      label: loaded.run.timeframes?.[0]?.label || '15m',
    };
    await gotoChart(page, loaded.run, item.symbol, item.interval);
    const auth = await checkAuth(page);
    if (!auth.authenticated) throw new Error(`TradingView session is not authenticated: ${auth.url}`);
    await page.waitForTimeout(Number(loaded.run.waitAfterLoadMs || loaded.defaults.waitAfterLoadMs || 8000));

    const install = await installPineInCurrentSession(page, loaded, args);
    const mapping = await applyBatchMappings(page, title, mappings);
    const screenshot = path.join(outDir, `${safeName(batchId)}.png`);
    await saveScreenshot(page, screenshot);
    const csv = await exportChartData(page, outDir, item, batchId, Number(args.timeoutMs || 120000));
    const report = {
      status: 'ok',
      command: 'tv-telemetry-batch-export',
      runId: loaded.runId,
      batchId,
      outDir,
      title,
      item,
      install,
      mapping,
      screenshot,
      csv,
    };
    writeReport(path.join(outDir, 'telemetry-batch-report.json'), report);
    console.log(JSON.stringify(report, null, 2));
  } catch (error) {
    const failureScreenshot = page ? path.join(outDir, 'failure.png') : null;
    const failureBodyTextPath = page ? path.join(outDir, 'failure-body.txt') : null;
    if (page && failureScreenshot) {
      await saveScreenshot(page, failureScreenshot).catch(() => {});
    }
    if (page && failureBodyTextPath) {
      const bodyText = await page.locator('body').innerText({ timeout: 5000 }).catch(() => '');
      fs.writeFileSync(failureBodyTextPath, bodyText);
    }
    const report = {
      status: 'failed',
      command: 'tv-telemetry-batch-export',
      runId: loaded.runId,
      batchId,
      outDir,
      failureScreenshot,
      failureBodyTextPath,
      error: String(error.stack || error),
    };
    writeReport(path.join(outDir, 'telemetry-batch-report.json'), report);
    console.log(JSON.stringify(report, null, 2));
    process.exitCode = 1;
  } finally {
    await context?.close().catch(() => {});
  }
}

await main();
