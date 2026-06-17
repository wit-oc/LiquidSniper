#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  commandArtifactDir,
  ensureDir,
  loadConfig,
  matrixItems,
  parseArgs,
  safeName,
  writeReport,
} from '../../codex/skills/tradingview-pine-loop/scripts/lib/config.mjs';
import { launchTradingView } from '../../codex/skills/tradingview-pine-loop/scripts/lib/browser.mjs';
import { checkAuth, gotoChart, openStrategyReport, saveScreenshot } from '../../codex/skills/tradingview-pine-loop/scripts/lib/actions.mjs';
import { applyV6MappingsToPage } from './tv_apply_v6_mappings.mjs';

export function normalizeNumber(value) {
  if (value == null) return null;
  const cleaned = String(value)
    .replace(/\u2212/g, '-')
    .replace(/[,%\s]/g, '')
    .replace(/[^\d.+-]/g, '');
  if (!cleaned || cleaned === '-' || cleaned === '.' || cleaned === '+') return null;
  const parsed = Number(cleaned);
  return Number.isFinite(parsed) ? parsed : null;
}

function compactLines(text) {
  return text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0);
}

function afterLabel(lines, label, offset = 1) {
  const index = lines.findIndex((line) => line.toLowerCase() === label.toLowerCase());
  return index >= 0 ? lines[index + offset] : null;
}

export function parseStrategyMetrics(text) {
  const lines = compactLines(text);
  const titleIndex = lines.findIndex((line) => line === 'Strategy Report');
  const title = titleIndex >= 0 ? lines[titleIndex + 1] || null : null;
  const dateRange = titleIndex >= 0 ? lines[titleIndex + 2] || null : null;
  return {
    title,
    dateRange,
    totalPnl: normalizeNumber(afterLabel(lines, 'Total P&L')),
    totalPnlPct: normalizeNumber(afterLabel(lines, 'Total P&L', 3)),
    maxDrawdown: normalizeNumber(afterLabel(lines, 'Max equity drawdown')),
    maxDrawdownPct: normalizeNumber(afterLabel(lines, 'Max equity drawdown', 3)),
    totalTrades: normalizeNumber(afterLabel(lines, 'Total trades')),
    profitableTradesPct: normalizeNumber(afterLabel(lines, 'Profitable trades')),
    profitFactor: normalizeNumber(afterLabel(lines, 'Profit factor')),
    grossProfit: normalizeNumber(afterLabel(lines, 'Gross profit')),
    grossProfitPct: normalizeNumber(afterLabel(lines, 'Gross profit', 3)),
    grossLoss: normalizeNumber(afterLabel(lines, 'Gross loss')),
    grossLossPct: normalizeNumber(afterLabel(lines, 'Gross loss', 3)),
    winningTrades: normalizeNumber(afterLabel(lines, 'Winning trades')),
    losingTrades: normalizeNumber(afterLabel(lines, 'Losing trades')),
    maxIntrabarDrawdownPct: normalizeNumber(afterLabel(lines, 'Max equity drawdown (intrabar)', 3)),
    hasNotEnoughData: /Not enough data to display|requires trade data|script makes even one trade|No trades|No data/i.test(text),
  };
}

function flagEnabled(value) {
  return value === true || value === 'true' || value === '1' || value === 1;
}

export function manualSettingsGate(loaded, args = {}) {
  const settingsRequired = Boolean(loaded.run.requiresManualSettingsCommit);
  const automatedSettingsCommit =
    flagEnabled(args['apply-v6-mappings-each-symbol']) ||
    flagEnabled(args['apply-v6-mappings']) ||
    flagEnabled(loaded.run.applyV6MappingsEachSymbol);
  const settingsAcknowledged =
    args['settings-committed'] === true ||
    args['manual-settings-ok'] === true ||
    process.env.TV_MANUAL_SETTINGS_COMMITTED === '1' ||
    automatedSettingsCommit;
  const sourceRequired = Boolean(loaded.run.requiresSourceContractVerification);
  const sourceAcknowledged =
    args['source-contract-verified'] === true ||
    args['source-mapping-verified'] === true ||
    process.env.TV_SOURCE_CONTRACT_VERIFIED === '1' ||
    automatedSettingsCommit;
  const status = settingsRequired && !settingsAcknowledged
    ? 'setup_unverified'
    : sourceRequired && !sourceAcknowledged
      ? 'source_unverified'
      : 'ok';
  return {
    settingsRequired,
    settingsAcknowledged,
    sourceRequired,
    sourceAcknowledged,
    automatedSettingsCommit,
    evidenceMode: automatedSettingsCommit && flagEnabled(loaded.run.samePaneSymbolSwitch)
      ? 'settings-dialog-mapping-commit-initial-load-same-pane-reuse'
      : automatedSettingsCommit
        ? 'settings-dialog-mapping-commit-per-symbol'
        : 'manual',
    status,
    hypothesisId: loaded.run.hypothesisId || null,
    expectation: [
      settingsRequired && !settingsAcknowledged
        ? 'Open strategy/indicator settings, re-enter scalar values and input.source mappings, commit with OK, then run with --settings-committed.'
        : null,
      sourceRequired && !sourceAcknowledged
        ? 'Verify the v6 HUD/table shows Unity src=true and sourceBlock=0, then run with --source-contract-verified.'
        : null,
    ].filter(Boolean).join(' '),
  };
}

async function firstVisible(page, locators) {
  for (const locator of locators) {
    const item = typeof locator === 'string' ? page.locator(locator).first() : locator.first();
    if (await item.isVisible().catch(() => false)) return item;
  }
  return null;
}

async function closeStrategyReportIfOpen(page) {
  const reportTitle = page.getByText('Strategy Report', { exact: true }).first();
  const reportBox = await reportTitle.boundingBox().catch(() => null);
  if (reportBox && reportBox.y > 250) {
    await page.mouse.click(903, reportBox.y + reportBox.height / 2).catch(() => {});
    await page.waitForTimeout(1000);
    return true;
  }
  return false;
}

async function clickSymbolChooser(page) {
  await page.mouse.click(110, 18);
  await page.waitForTimeout(900);
  if (await symbolSearchInput(page)) return 'top-left-symbol-coordinate';
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(300);

  const chooser = await firstVisible(page, [
    page.locator('button[title="Symbol search"]'),
    page.locator('[title="Symbol search"]'),
    page.getByRole('button', { name: /Symbol search/i }),
    page.getByRole('button', { name: /Change symbol/i }),
    page.locator('[aria-label*="Change symbol" i]'),
    page.locator('[data-name*="symbol-search" i]'),
  ]);

  if (chooser) {
    await chooser.click({ force: true });
    await page.waitForTimeout(900);
    if (await symbolSearchInput(page)) return 'symbol-search-control';
    await page.keyboard.press('Escape').catch(() => {});
    await page.waitForTimeout(300);
  }

  await page.mouse.click(86, 18);
  await page.waitForTimeout(900);
  if (await symbolSearchInput(page)) return 'symbol-search-coordinate-fallback';
  await page.keyboard.press('Escape').catch(() => {});
  return 'symbol-search-coordinate-fallback';
}

async function symbolSearchInput(page) {
  return firstVisible(page, [
    page.locator('[data-name="symbol-search-dialog"] input'),
    page.locator('[role="dialog"] input[type="text"]'),
    page.locator('[role="dialog"] input'),
    page.locator('input[placeholder*="Search" i]'),
    page.locator('input[type="search"]'),
  ]);
}

async function clickSymbolResult(page, symbol) {
  const [exchange, ticker] = symbol.includes(':') ? symbol.split(':') : ['', symbol];
  const candidates = [
    page.locator('[data-name="symbol-search-dialog"] [role="row"]').filter({ hasText: ticker }).filter({ hasText: exchange }),
    page.locator('[data-name="symbol-search-dialog"] [role="option"]').filter({ hasText: ticker }).filter({ hasText: exchange }),
    page.locator('[role="dialog"] [role="row"]').filter({ hasText: ticker }).filter({ hasText: exchange }),
    page.locator('[role="dialog"] [role="option"]').filter({ hasText: ticker }).filter({ hasText: exchange }),
    page.locator('[data-name="symbol-search-items-dialog"] [role="row"]').filter({ hasText: ticker }).filter({ hasText: exchange }),
    page.locator('[data-name="symbol-search-items-dialog"] [role="option"]').filter({ hasText: ticker }).filter({ hasText: exchange }),
  ];

  const result = await firstVisible(page, candidates);
  if (!result) return null;
  await result.click({ force: true });
  return 'exact-result-click';
}

export async function switchSymbolSamePane(page, item, loaded, options = {}) {
  const startedAt = Date.now();
  const beforeUrl = page.url();
  const symbol = item.symbol;
  const ticker = symbol.includes(':') ? symbol.split(':')[1] : symbol;

  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(400);
  await closeStrategyReportIfOpen(page);
  const chooserMethod = await clickSymbolChooser(page);

  const input = await symbolSearchInput(page);
  if (!input) throw new Error('Could not find TradingView symbol search input');
  await input.fill(symbol);
  await page.waitForTimeout(1000);

  const resultMethod = await clickSymbolResult(page, symbol);
  if (!resultMethod) {
    await page.keyboard.press('Enter');
  }
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(Number(options.waitAfterSwitchMs ?? loaded.run.waitAfterSymbolSwitchMs ?? 6000));

  const bodyText = await page.locator('body').innerText({ timeout: 5000 }).catch(() => '');
  return {
    status: 'ok',
    method: resultMethod ? `${chooserMethod}+${resultMethod}` : `${chooserMethod}+enter`,
    symbol,
    interval: item.interval,
    beforeUrl,
    afterUrl: page.url(),
    visibleTicker: bodyText.toUpperCase().includes(String(ticker).toUpperCase()),
    elapsedMs: Date.now() - startedAt,
  };
}

async function waitForStrategyReportText(page, timeoutMs = 15000) {
  const startedAt = Date.now();
  let text = '';
  do {
    await page.waitForTimeout(1000);
    text = await page.locator('body').innerText({ timeout: 10000 }).catch(() => '');
    if (/Total P&L|Total trades|Not enough data to display/i.test(text)) return text;
  } while (Date.now() - startedAt < timeoutMs);
  return text;
}

async function main() {
  const args = parseArgs();
  const loaded = loadConfig(args);
  const outDir = commandArtifactDir(loaded.artifactsDir, loaded.runId, 'text-matrix');
  const setupGate = manualSettingsGate(loaded, args);
  const samePaneSymbolSwitch = flagEnabled(args['same-pane-symbol-switch']) || flagEnabled(loaded.run.samePaneSymbolSwitch);
  const applyV6MappingsEachSymbol =
    flagEnabled(args['apply-v6-mappings-each-symbol']) ||
    flagEnabled(args['apply-v6-mappings']) ||
    flagEnabled(loaded.run.applyV6MappingsEachSymbol);
  const reuseMappingsAfterSamePaneSwitch = samePaneSymbolSwitch && loaded.run.reuseV6MappingsAfterSamePaneSwitch !== false;
  const onlySymbol = typeof args['only-symbol'] === 'string' ? args['only-symbol'] : null;
  const allItems = onlySymbol
    ? matrixItems(loaded.run).filter((item) => item.symbol === onlySymbol)
    : matrixItems(loaded.run);
  const maxItems = args['max-items'] === true || args['max-items'] == null ? allItems.length : Number(args['max-items']);
  const items = Number.isFinite(maxItems) ? allItems.slice(0, Math.max(0, maxItems)) : allItems;
  let context;

  if (setupGate.status !== 'ok') {
    const report = {
      status: setupGate.status,
      command: 'tv-strategy-text-matrix',
      runId: loaded.runId,
      outDir,
      setupGate,
      samePaneSymbolSwitch,
      applyV6MappingsEachSymbol,
      reuseMappingsAfterSamePaneSwitch,
      results: [],
    };
    writeReport(path.join(outDir, 'text-matrix-report.json'), report);
    console.log(JSON.stringify(report, null, 2));
    process.exitCode = 1;
    return;
  }

  try {
    const browser = await launchTradingView({ defaults: loaded.defaults, artifactsDir: outDir });
    context = browser.context;
    const page = browser.page;
    const results = [];
    let chartLoaded = false;
    let persistentMapping = null;
    let persistentMappingSymbol = null;

    for (const item of items) {
      const itemDir = path.join(outDir, safeName(item.symbol), safeName(item.label));
      ensureDir(itemDir);
      const result = { ...item, status: 'unknown' };
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
        if (applyV6MappingsEachSymbol && (!reuseMappingsAfterSamePaneSwitch || !persistentMapping)) {
          result.mapping = await applyV6MappingsToPage(page, loaded.run.expectedStrategyTitle || loaded.run.scriptTitle || '', {
            mappings: loaded.run.v6Mappings,
          });
          if (result.mapping.status !== 'ok') {
            throw new Error(`Source mapping failed for ${item.symbol} ${item.label}`);
          }
          persistentMapping = result.mapping;
          persistentMappingSymbol = `${item.symbol} ${item.label}`;
        } else if (applyV6MappingsEachSymbol && persistentMapping) {
          result.mapping = {
            status: persistentMapping.status,
            reused: true,
            reusedFrom: persistentMappingSymbol,
            reason: 'Same-pane symbol switching keeps the chart study instance alive; no URL reload occurred.',
            mappings: persistentMapping.mappings,
            before: persistentMapping.after,
            after: persistentMapping.after,
            expected: persistentMapping.expected,
          };
        }
        const preflight = {};
        try {
          preflight.chartTextPath = path.join(itemDir, 'chart-preflight-text.txt');
          preflight.chartScreenshot = path.join(itemDir, 'chart-preflight.png');
          fs.writeFileSync(preflight.chartTextPath, await page.locator('body').innerText({ timeout: 10000 }));
          await saveScreenshot(page, preflight.chartScreenshot);
        } catch (preflightError) {
          preflight.error = String(preflightError.stack || preflightError);
        }
        result.preflight = preflight;
        await openStrategyReport(page);
        const text = await waitForStrategyReportText(page, Number(loaded.run.waitForStrategyReportMs || 15000));
        const textPath = path.join(itemDir, 'strategy-report-text.txt');
        fs.writeFileSync(textPath, text);
        const screenshot = path.join(itemDir, 'strategy-report.png');
        await saveScreenshot(page, screenshot);
        const metrics = parseStrategyMetrics(text);
        result.status = metrics.title ? 'ok' : 'failed';
        result.metrics = metrics;
        result.textPath = textPath;
        result.screenshot = screenshot;
        if (loaded.run.expectedStrategyTitle && metrics.title !== loaded.run.expectedStrategyTitle) {
          result.status = 'failed';
          result.error = `Strategy Report is showing "${metrics.title}", not expected "${loaded.run.expectedStrategyTitle}"`;
        }
      } catch (error) {
        result.status = 'failed';
        result.error = String(error.stack || error);
        result.screenshot = path.join(itemDir, 'failure.png');
        await saveScreenshot(page, result.screenshot);
      }
      results.push(result);
    }

    const report = {
      status: results.every((result) => result.status === 'ok') ? 'ok' : 'failed',
      command: 'tv-strategy-text-matrix',
      runId: loaded.runId,
      outDir,
      setupGate,
      samePaneSymbolSwitch,
      applyV6MappingsEachSymbol,
      reuseMappingsAfterSamePaneSwitch,
      itemCount: items.length,
      results,
    };
    writeReport(path.join(outDir, 'text-matrix-report.json'), report);
    console.log(JSON.stringify(report, null, 2));
    if (report.status === 'failed') process.exitCode = 1;
  } catch (error) {
    const report = { status: 'failed', command: 'tv-strategy-text-matrix', runId: loaded.runId, error: String(error.stack || error) };
    writeReport(path.join(outDir, 'text-matrix-report.json'), report);
    console.log(JSON.stringify(report, null, 2));
    process.exitCode = 1;
  } finally {
    await context?.close().catch(() => {});
  }
}

if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) {
  await main();
}
