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
} from '../../../../codex/skills/tradingview-pine-loop/scripts/lib/config.mjs';
import { launchTradingView } from '../../../../codex/skills/tradingview-pine-loop/scripts/lib/browser.mjs';
import {
  addPineToChart,
  checkAuth,
  closePineEditor,
  detectCompileStatus,
  exportStrategyData,
  gotoChart,
  openPineEditor,
  openStrategyReport,
  saveScreenshot,
  setPineEditorText,
  waitForStrategyReportReady,
} from '../../../../codex/skills/tradingview-pine-loop/scripts/lib/actions.mjs';
import { manualSettingsGate, parseStrategyMetrics } from '../../../scripts/tv_strategy_text_matrix.mjs';
import { applyV6MappingsToPage } from '../../../scripts/tv_apply_v6_mappings.mjs';

function flagEnabled(value) {
  return value === true || value === 'true' || value === '1' || value === 1;
}

function escapeRegExp(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

async function firstVisible(page, locators) {
  for (const locator of locators) {
    const collection = typeof locator === 'string' ? page.locator(locator) : locator;
    const count = Math.min(await collection.count().catch(() => 0), 30);
    for (let index = 0; index < count; index += 1) {
      const candidate = collection.nth(index);
      if (await candidate.isVisible().catch(() => false)) return candidate;
    }
  }
  return null;
}

async function firstVisibleMatching(page, locators, predicate) {
  for (const locator of locators) {
    const collection = typeof locator === 'string' ? page.locator(locator) : locator;
    const count = Math.min(await collection.count().catch(() => 0), 60);
    for (let index = 0; index < count; index += 1) {
      const candidate = collection.nth(index);
      if (!(await candidate.isVisible().catch(() => false))) continue;
      const box = await candidate.boundingBox().catch(() => null);
      if (await predicate(candidate, box)) return candidate;
    }
  }
  return null;
}

async function openStrategyMetricsTab(page) {
  const viewport = page.viewportSize() || { width: 1440, height: 950 };
  const metricsTab = await firstVisibleMatching(page, [
    page.getByRole('button', { name: /^Metrics$/i }),
    page.getByText(/^Metrics$/i),
  ], async (_candidate, box) => {
    if (!box) return false;
    return box.y > viewport.height * 0.34 && box.y < viewport.height * 0.47 && box.x < viewport.width * 0.20;
  });
  if (metricsTab) {
    await metricsTab.click({ force: true });
    await page.waitForTimeout(900);
  }
}

function formatUsDate(iso) {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) throw new Error(`Invalid custom date: ${iso}`);
  return `${date.getUTCMonth() + 1}/${date.getUTCDate()}/${date.getUTCFullYear()}`;
}

function formatIsoDate(iso) {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) throw new Error(`Invalid custom date: ${iso}`);
  return date.toISOString().slice(0, 10);
}

const monthNames = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
];

function monthIndex(name) {
  return monthNames.findIndex((item) => item.toLowerCase() === String(name).toLowerCase());
}

function monthOrdinal(date) {
  return date.getUTCFullYear() * 12 + date.getUTCMonth();
}

async function openSnapshotStrategyReport(page, expectedTitle = '') {
  const currentText = await page.locator('body').innerText({ timeout: 5000 }).catch(() => '');
  const currentTitleOk = !expectedTitle || currentText.toLowerCase().includes(String(expectedTitle).toLowerCase());
  const currentReportVisible =
    /[A-Z][a-z]{2}\s+\d{1,2},\s+20\d{2}\s+—\s+[A-Z][a-z]{2}\s+\d{1,2},\s+20\d{2}/.test(currentText) ||
    /Strategy Report|List of trades|Total P&L|Profit Factor|requires trade data|script makes even one trade/i.test(currentText);
  if (currentReportVisible && (currentTitleOk || /requires trade data|script makes even one trade/i.test(currentText))) {
    return { method: 'already-visible-snapshot-report' };
  }

  try {
    return await openStrategyReport(page);
  } catch (error) {
    const bodyText = await page.locator('body').innerText({ timeout: 5000 }).catch(() => '');
    const titleOk = !expectedTitle || bodyText.toLowerCase().includes(String(expectedTitle).toLowerCase());
    const reportVisible =
      /[A-Z][a-z]{2}\s+\d{1,2},\s+20\d{2}\s+—\s+[A-Z][a-z]{2}\s+\d{1,2},\s+20\d{2}/.test(bodyText) ||
      /Strategy Report|List of trades|Total P&L|Profit Factor|requires trade data|script makes even one trade/i.test(bodyText);
    if (reportVisible && (titleOk || /requires trade data|script makes even one trade/i.test(bodyText))) {
      return {
        method: 'visible-after-open-fallback',
        warning: String(error.message || error),
      };
    }
    throw error;
  }
}

async function clickDateRangeButton(page, expectedTitle = '') {
  await openSnapshotStrategyReport(page, expectedTitle);
  await openStrategyMetricsTab(page);
  const viewport = page.viewportSize() || { width: 1440, height: 950 };
  const dateText = await firstVisibleMatching(page, [
    page.getByText(/[A-Z][a-z]{2}\s+\d{1,2},\s+20\d{2}\s+—\s+[A-Z][a-z]{2}\s+\d{1,2},\s+20\d{2}/),
  ], async (_candidate, box) => {
    if (!box) return false;
    return box.y > viewport.height * 0.34 && box.y < viewport.height * 0.70;
  });
  if (dateText) {
    const label = await dateText.innerText().catch(() => '');
    await dateText.click({ force: true });
    await page.waitForTimeout(1000);
    return { method: 'date-range-text', label };
  }
  const dateButton = await firstVisibleMatching(page, [
    page.locator('button, [role="button"]'),
  ], async (candidate, box) => {
    if (!box) return false;
    const inStrategyHeader = box.y > viewport.height * 0.34 && box.y < viewport.height * 0.43 && box.x > viewport.width * 0.38 && box.x < viewport.width * 0.98;
    if (!inStrategyHeader) return false;
    const label = await candidate.evaluate((element) => [
      element.textContent || '',
      element.getAttribute('aria-label') || '',
      element.getAttribute('title') || '',
      element.getAttribute('data-name') || '',
    ].join(' ')).catch(() => '');
    return /\d{4}.*(—|-).*?\d{4}|date|calendar|range|all|history/i.test(label);
  });
  if (dateButton) {
    const label = await dateButton.evaluate((element) => [
      element.textContent || '',
      element.getAttribute('aria-label') || '',
      element.getAttribute('title') || '',
      element.getAttribute('data-name') || '',
    ].join(' ')).catch(() => '');
    await dateButton.click({ force: true });
    await page.waitForTimeout(1000);
    return { method: 'button', label };
  }
  await page.mouse.click(viewport.width * 0.57, viewport.height * 0.398);
  await page.waitForTimeout(1000);
  return { method: 'coordinate-fallback' };
}

async function clickDateRangeMenuOption(page, labels) {
  for (const label of labels) {
    const option = await firstVisible(page, [
      page.getByRole('menuitemcheckbox', { name: new RegExp(escapeRegExp(label), 'i') }),
      page.getByRole('menuitem', { name: new RegExp(escapeRegExp(label), 'i') }),
      page.getByRole('button', { name: new RegExp(escapeRegExp(label), 'i') }),
      page.getByText(new RegExp(`^${escapeRegExp(label)}$`, 'i')),
    ]);
    if (option) {
      await option.click({ force: true });
      await page.waitForTimeout(1200);
      return label;
    }
  }
  return null;
}

async function clickDeepStrategyReportPrompt(page) {
  const open = await firstVisible(page, [
    page.getByRole('button', { name: /^Open strategy report$/i }),
    page.getByText(/^Open strategy report$/i),
  ]);
  if (!open) return { status: 'not-found' };
  await open.click({ force: true });
  await page.waitForTimeout(1800);
  return { status: 'clicked' };
}

async function visibleDateInputs(page) {
  const viewport = page.viewportSize() || { width: 1440, height: 950 };
  const inputs = [];
  const collection = page.locator('input');
  const count = Math.min(await collection.count().catch(() => 0), 80);
  for (let index = 0; index < count; index += 1) {
    const input = collection.nth(index);
    if (!(await input.isVisible().catch(() => false))) continue;
    const box = await input.boundingBox().catch(() => null);
    if (!box || box.y < viewport.height * 0.30) continue;
    const meta = await input.evaluate((element) => ({
      type: element.getAttribute('type') || '',
      placeholder: element.getAttribute('placeholder') || '',
      aria: element.getAttribute('aria-label') || '',
      title: element.getAttribute('title') || '',
      value: element.value || '',
    })).catch(() => ({}));
    inputs.push({ input, box, meta });
  }
  return inputs.sort((a, b) => a.box.y === b.box.y ? a.box.x - b.box.x : a.box.y - b.box.y);
}

async function fillDateInput(input, iso) {
  const variants = [formatIsoDate(iso), formatUsDate(iso)];
  let lastError = null;
  for (const value of variants) {
    try {
      await input.click({ force: true });
      await input.fill(value);
      await input.press('Tab').catch(() => {});
      return value;
    } catch (error) {
      lastError = error;
    }
  }
  throw lastError || new Error(`Unable to fill date input for ${iso}`);
}

async function currentCalendarMonth(page) {
  const heading = await firstVisibleMatching(page, [
    page.getByText(new RegExp(`^(${monthNames.join('|')})\\s+20\\d{2}$`)),
  ], async (_candidate, box) => Boolean(box && box.y > 250));
  if (!heading) return null;
  const text = (await heading.innerText().catch(() => '')).trim();
  const match = text.match(/^([A-Za-z]+)\s+(20\d{2})$/);
  if (!match) return null;
  const month = monthIndex(match[1]);
  const year = Number(match[2]);
  if (month < 0 || !Number.isFinite(year)) return null;
  const box = await heading.boundingBox().catch(() => null);
  return { text, month, year, ordinal: year * 12 + month, box };
}

async function clickCalendarNav(page, direction, monthInfo) {
  const viewport = page.viewportSize() || { width: 1440, height: 950 };
  const label = direction < 0 ? /previous|prev|back|left/i : /next|forward|right/i;
  const semantic = await firstVisibleMatching(page, [
    page.locator('button, [role="button"]'),
  ], async (candidate, box) => {
    if (!box || box.y < viewport.height * 0.34) return false;
    const text = await candidate.evaluate((element) => [
      element.textContent || '',
      element.getAttribute('aria-label') || '',
      element.getAttribute('title') || '',
      element.getAttribute('data-name') || '',
    ].join(' ')).catch(() => '');
    return label.test(text) && /month|calendar|date|prev|next|left|right|back|forward/i.test(text);
  });
  if (semantic) {
    await semantic.click({ force: true });
    await page.waitForTimeout(500);
    return 'semantic';
  }

  if (!monthInfo?.box) throw new Error('Calendar month heading not found for navigation fallback');
  const y = monthInfo.box.y + monthInfo.box.height / 2;
  const x = direction < 0 ? Math.max(10, monthInfo.box.x - 36) : Math.min(viewport.width - 10, monthInfo.box.x + monthInfo.box.width + 36);
  await page.mouse.click(x, y);
  await page.waitForTimeout(500);
  return 'coordinate';
}

async function goToCalendarMonth(page, iso) {
  const target = new Date(iso);
  if (Number.isNaN(target.getTime())) throw new Error(`Invalid target calendar date: ${iso}`);
  const targetOrdinal = monthOrdinal(target);
  let info = await currentCalendarMonth(page);
  if (!info) throw new Error('Custom calendar month heading was not found');
  const visited = [];
  for (let attempt = 0; attempt < 24 && info.ordinal !== targetOrdinal; attempt += 1) {
    visited.push(info.text);
    const direction = targetOrdinal < info.ordinal ? -1 : 1;
    await clickCalendarNav(page, direction, info);
    const next = await currentCalendarMonth(page);
    if (!next) throw new Error(`Calendar month disappeared while navigating from ${info.text} to ${formatIsoDate(iso)}`);
    if (next.ordinal === info.ordinal) {
      throw new Error(`Calendar could not navigate ${direction < 0 ? 'before' : 'after'} ${info.text}; target was ${formatIsoDate(iso)}. Visited: ${visited.join(' -> ')}`);
    }
    info = next;
  }
  if (info.ordinal !== targetOrdinal) {
    throw new Error(`Calendar did not reach target month ${formatIsoDate(iso)}. Last month: ${info.text}. Visited: ${visited.join(' -> ')}`);
  }
  return info;
}

async function clickCalendarDay(page, iso) {
  const target = new Date(iso);
  if (Number.isNaN(target.getTime())) throw new Error(`Invalid target calendar date: ${iso}`);
  const day = String(target.getUTCDate());
  const monthInfo = await goToCalendarMonth(page, iso);
  const dayCell = await firstVisibleMatching(page, [
    page.getByRole('button', { name: new RegExp(`^${day}$`) }),
    page.getByText(new RegExp(`^${day}$`)),
  ], async (_candidate, box) => {
    if (!box || !monthInfo.box) return false;
    return box.y > monthInfo.box.y + 28 && box.y < monthInfo.box.y + 330 && box.x > monthInfo.box.x - 260 && box.x < monthInfo.box.x + 360;
  });
  if (!dayCell) throw new Error(`Could not find calendar day ${day} in ${monthInfo.text}`);
  await dayCell.click({ force: true });
  await page.waitForTimeout(600);
  return { day, month: monthInfo.text };
}

async function fillCalendarDateRange(page, start, end) {
  await page.waitForTimeout(1000);
  const bodyText = await page.locator('body').innerText({ timeout: 5000 }).catch(() => '');
  if (!/Backtesting dates|Select first available date|Cancel\s+Select/i.test(bodyText)) {
    throw new Error(`Custom calendar is not visible. Visible text sample: ${bodyText.slice(-1500)}`);
  }
  const pickedStart = await clickCalendarDay(page, start);
  const pickedEnd = await clickCalendarDay(page, end);
  const select = await firstVisible(page, [
    page.getByRole('button', { name: /^Select$/i }),
    page.locator('button:has-text("Select")'),
  ]);
  if (!select) throw new Error('Could not find Select button in custom Strategy Tester date calendar');
  await select.click({ force: true });
  await page.waitForTimeout(1800);
  return { status: 'ok', inputMode: 'calendar', pickedStart, pickedEnd };
}

async function applyCustomStrategyReportDateRange(page, range, expectedTitle = '') {
  const start = range.start;
  const end = range.end;
  if (!start || !end) throw new Error(`Custom Strategy Tester date range requires start/end: ${JSON.stringify(range)}`);
  const opened = await clickDateRangeButton(page, expectedTitle);
  const selected = await clickDateRangeMenuOption(page, [
    'Custom range',
    'Custom date range',
    'Custom dates',
    'Date range',
    'Custom',
  ]);
  await page.waitForTimeout(1000);

  let inputs = await visibleDateInputs(page);
  if (inputs.length < 2 && !selected) {
    const bodyText = await page.locator('body').innerText({ timeout: 5000 }).catch(() => '');
    throw new Error(`Could not open custom Strategy Tester date inputs. Visible text sample: ${bodyText.slice(-1500)}`);
  }
  if (inputs.length < 2) {
    await page.waitForTimeout(1500);
    inputs = await visibleDateInputs(page);
  }
  if (inputs.length < 2) {
    const calendarResult = await fillCalendarDateRange(page, start, end);
    return {
      status: 'ok',
      mode: 'custom',
      opened,
      selected: selected || 'calendar',
      start,
      end,
      ...calendarResult,
    };
  }

  const fromInput = inputs.find((item) => /from|start/i.test(`${item.meta.placeholder} ${item.meta.aria} ${item.meta.title}`)) || inputs[0];
  const toInput = inputs.find((item) => /to|end/i.test(`${item.meta.placeholder} ${item.meta.aria} ${item.meta.title}`) && item !== fromInput) || inputs[1];
  const filledStart = await fillDateInput(fromInput.input, start);
  const filledEnd = await fillDateInput(toInput.input, end);

  const apply = await firstVisible(page, [
    page.getByRole('button', { name: /Apply|OK|Done|Save/i }),
    page.locator('button:has-text("Apply"), button:has-text("OK"), button:has-text("Done"), button:has-text("Save")'),
  ]);
  if (apply) {
    await apply.click({ force: true });
  } else {
    await page.keyboard.press('Enter').catch(() => {});
  }
  await page.waitForTimeout(1800);
  return { status: 'ok', mode: 'custom', opened, selected: selected || 'direct-inputs', start, end, filledStart, filledEnd };
}

async function setSnapshotStrategyReportDateRange(page, rangeMode, expectedTitle = '') {
  if (!rangeMode || /^current|default|none$/i.test(String(rangeMode))) return { status: 'skipped', rangeMode: rangeMode || null };
  const range = typeof rangeMode === 'object' ? rangeMode : { mode: String(rangeMode) };
  if (/^custom$/i.test(String(range.mode || ''))) return applyCustomStrategyReportDateRange(page, range, expectedTitle);

  const opened = await clickDateRangeButton(page, expectedTitle);
  const labelsByMode = {
    'range-from-chart': ['Range from chart', 'Chart range'],
    chart: ['Range from chart', 'Chart range'],
    'entire-history': ['Entire history', 'All history', 'All data', 'All'],
    'entire history': ['Entire history', 'All history', 'All data', 'All'],
    all: ['Entire history', 'All history', 'All data', 'All'],
  };
  const labels = labelsByMode[String(range.mode || rangeMode).toLowerCase()] || [String(range.mode || rangeMode)];
  const selected = await clickDateRangeMenuOption(page, labels);
  if (!selected) {
    const bodyText = await page.locator('body').innerText({ timeout: 5000 }).catch(() => '');
    throw new Error(`Could not find Strategy Tester date range option "${labels.join(' | ')}". Visible text sample: ${bodyText.slice(-1200)}`);
  }
  return { status: 'ok', mode: range.mode || rangeMode, opened, selected };
}

async function downloadSnapshotFromAction(page, action, outPath, timeoutMs) {
  let downloadError = null;
  const downloadPromise = page.waitForEvent('download', { timeout: timeoutMs }).catch((error) => {
    downloadError = error;
    return null;
  });
  await action();
  const download = await downloadPromise;
  if (!download) {
    throw new Error(`Snapshot fallback download did not start within ${timeoutMs}ms. ${downloadError ? downloadError.message : ''}`.trim());
  }
  await download.saveAs(outPath);
  return outPath;
}

async function exportSnapshotStrategyDataFallback(page, outDir, item, timeoutMs, expectedTitle = '') {
  ensureDir(outDir);
  await openSnapshotStrategyReport(page, expectedTitle);
  await clickDeepStrategyReportPrompt(page).catch(() => {});
  const outPath = path.join(outDir, `${safeName(item.symbol)}_${safeName(item.label)}_strategy.csv`);
  const action = async () => {
    const tradesTab = await firstVisible(page, [
      page.getByRole('button', { name: /List of trades/i }),
      page.getByText(/List of trades/i),
    ]);
    if (tradesTab) {
      await tradesTab.click({ force: true });
      await page.waitForTimeout(900);
    }
    const viewport = page.viewportSize() || { width: 1440, height: 950 };
    const menu = await firstVisibleMatching(page, [
      page.locator('[data-qa-id="tab-menu-trigger"]'),
      page.locator('button[title*="Open context menu" i], [role="button"][title*="Open context menu" i]'),
      page.locator('button, [role="button"]'),
    ], async (candidate, box) => {
      if (!box) return false;
      const inStrategyHeader = box.y > viewport.height * 0.30 && box.y < viewport.height * 0.43 && box.x > 250 && box.x < viewport.width * 0.62;
      if (!inStrategyHeader) return false;
      const label = await candidate.evaluate((element) => [
        element.textContent || '',
        element.getAttribute('aria-label') || '',
        element.getAttribute('title') || '',
        element.getAttribute('data-name') || '',
        element.getAttribute('data-qa-id') || '',
      ].join(' ')).catch(() => '');
      return /context menu|tab-menu-trigger|open context/i.test(label) || (box.width >= 18 && box.width <= 44 && box.height >= 18 && box.height <= 44);
    });
    if (!menu) throw new Error('Could not find Strategy Tester tab/context menu trigger for fallback export.');
    await menu.click({ force: true });
    await page.waitForTimeout(900);
    const exportData = await firstVisible(page, [
      page.getByRole('menuitem', { name: /Export data|Download data|Download CSV|Download|Export/i }),
      page.getByRole('button', { name: /Export data|Download data|Download CSV|Download|Export/i }),
      page.getByText(/Export data|Download data|Download CSV|Download|Export/i),
    ]);
    if (!exportData) throw new Error('Could not find export/download item after opening Strategy Tester context menu.');
    await exportData.click({ force: true });
  };
  return downloadSnapshotFromAction(page, action, outPath, timeoutMs);
}

async function waitForSnapshotStrategyReportReady(page, options = {}) {
  const timeoutMs = Number(options.timeoutMs || 180000);
  const pollMs = Number(options.pollMs || 5000);
  const expectedTitle = options.expectedTitle || '';
  const start = Date.now();
  let lastText = '';
  let deepPromptClicks = 0;

  while (Date.now() - start < timeoutMs) {
    await page.waitForTimeout(pollMs);
    const prompt = await clickDeepStrategyReportPrompt(page).catch(() => ({ status: 'failed' }));
    if (prompt.status === 'clicked') deepPromptClicks += 1;
    await openSnapshotStrategyReport(page, expectedTitle).catch(() => {});
    await openStrategyMetricsTab(page).catch(() => {});
    lastText = await page.locator('body').innerText({ timeout: 10000 }).catch(() => '');
    const titleOk = !expectedTitle || lastText.toLowerCase().includes(String(expectedTitle).toLowerCase());
    const hasMetricEvidence = /Total P&L|Net profit|Max equity drawdown|Total trades|Profit Factor|Gross profit|Gross loss/i.test(lastText);
    const hasTradeRowEvidence = /\bEntry\b/i.test(lastText) && /\bExit\b/i.test(lastText) && /Show on chart|USDT|USD/i.test(lastText);
    const hasEmptyEvidence = /No trades|No data|Not enough data|requires trade data|script makes even one trade/i.test(lastText);
    if (titleOk && (hasMetricEvidence || hasTradeRowEvidence || hasEmptyEvidence)) {
      return {
        status: 'ready',
        elapsedMs: Date.now() - start,
        hasMetricEvidence,
        hasTradeRowEvidence,
        hasEmptyEvidence,
        deepPromptClicks,
      };
    }
  }

  return {
    status: 'timeout',
    elapsedMs: Date.now() - start,
    deepPromptClicks,
    textSample: lastText.slice(-1600),
  };
}

const args = parseArgs();
const loaded = loadConfig(args);
const outDir = commandArtifactDir(loaded.artifactsDir, loaded.runId, 'snapshot-window-matrix');
const scriptPath = resolveFromRoot(loaded.root, args.script || loaded.run.scriptPath);
const source = fs.readFileSync(scriptPath, 'utf8');
const setupGate = manualSettingsGate(loaded, args);
const applySourceMappings =
  flagEnabled(args['apply-v6-mappings-each-symbol']) ||
  flagEnabled(args['apply-v6-mappings']) ||
  flagEnabled(loaded.run.applyV6MappingsEachSymbol);
const applySourceMappingsFirstItemOnly =
  flagEnabled(args['apply-v6-mappings-first-item-only']) ||
  flagEnabled(loaded.run.applyV6MappingsFirstItemOnly);
const installFirstItemOnly =
  flagEnabled(args['install-first-item-only']) ||
  flagEnabled(loaded.run.installFirstItemOnly);
const onlySymbol = typeof args['only-symbol'] === 'string' ? args['only-symbol'] : null;
const onlySymbols = typeof args['only-symbols'] === 'string'
  ? String(args['only-symbols']).split(',').map((item) => item.trim()).filter(Boolean)
  : null;
const allItems = matrixItems(loaded.run);
const items = onlySymbols
  ? onlySymbols.flatMap((symbol) => allItems.filter((item) => item.symbol === symbol))
  : onlySymbol
    ? allItems.filter((item) => item.symbol === onlySymbol)
    : allItems;
const strategyReportDateRange = loaded.run.strategyReportDateRange || null;
const strategyReportReadyTimeoutMs = Number(args.strategyReportReadyTimeoutMs || loaded.run.strategyReportReadyTimeoutMs || 180000);

if (setupGate.status !== 'ok') {
  const report = {
    status: setupGate.status,
    command: 'tv-snapshot-window-matrix',
    runId: loaded.runId,
    outDir,
    scriptPath,
    setupGate,
    results: [],
  };
  writeReport(path.join(outDir, 'pine-text-matrix-report.json'), report);
  console.log(JSON.stringify(report, null, 2));
  process.exitCode = 1;
} else {
  let context;
  try {
    const browser = await launchTradingView({ defaults: loaded.defaults, artifactsDir: outDir });
    context = browser.context;
    const page = browser.page;
    const results = [];

    for (let itemIndex = 0; itemIndex < items.length; itemIndex += 1) {
      const item = items[itemIndex];
      const itemDir = path.join(outDir, safeName(item.symbol), safeName(item.label));
      ensureDir(itemDir);
      const result = { ...item, status: 'unknown', scriptPath };
      try {
        result.url = await gotoChart(page, loaded.run, item.symbol, item.interval);
        const auth = await checkAuth(page);
        if (!auth.authenticated) throw new Error(`TradingView session is not authenticated: ${auth.url}`);
        await page.waitForTimeout(Number(loaded.run.waitAfterLoadMs || loaded.defaults.waitAfterLoadMs || 8000));
        await page.keyboard.press('Escape').catch(() => {});
        await page.waitForTimeout(250);
        await page.keyboard.press('Escape').catch(() => {});
        await page.waitForTimeout(250);

        const shouldInstallScript = !installFirstItemOnly || itemIndex === 0;
        if (shouldInstallScript) {
          await openPineEditor(page);
          result.editor = await setPineEditorText(page, source);
          await addPineToChart(page);
          result.compile = await detectCompileStatus(page);
          await closePineEditor(page).catch(() => {});
        } else {
          result.editor = {
            status: 'skipped',
            reason: 'Pine install was performed on the first matrix item and the chart strategy was reused.',
          };
          result.compile = {
            status: 'skipped',
            reason: 'Pine install was performed on the first matrix item and the chart strategy was reused.',
          };
        }

        const shouldApplySourceMappings = applySourceMappings && shouldInstallScript && (!applySourceMappingsFirstItemOnly || itemIndex === 0);
        if (shouldApplySourceMappings) {
          result.mapping = await applyV6MappingsToPage(page, loaded.run.expectedStrategyTitle || loaded.run.scriptTitle || '', {
            mappings: loaded.run.v6Mappings,
          });
          if (result.mapping.status !== 'ok') throw new Error(`Source mapping failed for ${item.symbol} ${item.label}`);
        } else if (applySourceMappings && applySourceMappingsFirstItemOnly) {
          result.mapping = {
            status: 'skipped',
            reason: 'Source mappings were applied on the first matrix item and reused for this chart script.',
          };
        }

        const expectedTitle = loaded.run.expectedStrategyTitle || loaded.run.scriptTitle || '';
        await openSnapshotStrategyReport(page, expectedTitle);
        await openStrategyMetricsTab(page);
        if (strategyReportDateRange) {
          result.strategyReportDateRange = await setSnapshotStrategyReportDateRange(page, strategyReportDateRange, expectedTitle);
          result.deepStrategyReportPrompt = await clickDeepStrategyReportPrompt(page).catch((error) => ({
            status: 'failed',
            error: String(error.message || error),
          }));
          result.strategyReportReady = await waitForSnapshotStrategyReportReady(page, {
            timeoutMs: strategyReportReadyTimeoutMs,
            expectedTitle,
          });
          if (result.strategyReportReady.status !== 'ready') throw new Error(`Strategy report did not become ready after selecting ${JSON.stringify(strategyReportDateRange)}`);
        }
        await openStrategyMetricsTab(page);
        const text = await page.locator('body').innerText({ timeout: 10000 });
        const textPath = path.join(itemDir, 'strategy-report-text.txt');
        fs.writeFileSync(textPath, text);
        const screenshot = path.join(itemDir, 'strategy-report.png');
        await saveScreenshot(page, screenshot);
        const metrics = parseStrategyMetrics(text);
        const reportTitleOk = !expectedTitle || metrics.title === expectedTitle || text.toLowerCase().includes(expectedTitle.toLowerCase());
        result.status = reportTitleOk ? 'ok' : 'failed';
        result.metrics = metrics;
        result.noTradeData = Boolean(metrics.hasNotEnoughData);
        result.textPath = textPath;
        result.screenshot = screenshot;
        if (!reportTitleOk) result.error = `Strategy Report is showing "${metrics.title}", not expected "${loaded.run.expectedStrategyTitle}"`;

        if (loaded.run.exportStrategyData) {
          if (result.noTradeData) {
            result.strategyData = {
              status: 'no_trade_data',
              reason: 'TradingView report has no trade data; counted as a valid zero-trade slot.',
            };
          } else {
            try {
              result.strategyData = {
                status: 'ok',
                path: await exportStrategyData(page, itemDir, item, Number(args.downloadTimeoutMs || loaded.defaults.downloadTimeoutMs || 120000), loaded.run),
              };
            } catch (error) {
              try {
                result.strategyData = {
                  status: 'ok',
                  path: await exportSnapshotStrategyDataFallback(
                    page,
                    itemDir,
                    item,
                    Number(args.downloadTimeoutMs || loaded.defaults.downloadTimeoutMs || 120000),
                    expectedTitle,
                  ),
                  fallback: 'strategy-tab-context-menu',
                  primaryError: String(error.stack || error),
                };
              } catch (fallbackError) {
                result.strategyData = {
                  status: 'failed',
                  error: String(fallbackError.stack || fallbackError),
                  primaryError: String(error.stack || error),
                };
              }
            }
          }
          if (result.strategyData.status !== 'ok' && result.strategyData.status !== 'no_trade_data') {
            result.status = 'failed';
            result.error = result.strategyData.error;
          }
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
      command: 'tv-snapshot-window-matrix',
      runId: loaded.runId,
      outDir,
      setupGate,
      applySourceMappings,
      applySourceMappingsFirstItemOnly,
      installFirstItemOnly,
      exportChartData: false,
      strategyReportDateRange,
      itemCount: items.length,
      results,
    };
    writeReport(path.join(outDir, 'pine-text-matrix-report.json'), report);
    console.log(JSON.stringify(report, null, 2));
    if (report.status === 'failed') process.exitCode = 1;
  } catch (error) {
    const report = { status: 'failed', command: 'tv-snapshot-window-matrix', runId: loaded.runId, error: String(error.stack || error) };
    writeReport(path.join(outDir, 'pine-text-matrix-report.json'), report);
    console.log(JSON.stringify(report, null, 2));
    process.exitCode = 1;
  } finally {
    await context?.close().catch(() => {});
  }
}
