import fs from 'node:fs';
import path from 'node:path';
import { chartUrlFor, ensureDir, safeName } from './config.mjs';

export async function gotoChart(page, run, symbol, interval) {
  const url = chartUrlFor(run, symbol, interval);
  await page.goto(url, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('domcontentloaded').catch(() => {});
  await page.waitForTimeout(5000);
  return url;
}

export async function checkAuth(page) {
  const url = page.url();
  const bodyText = await page.locator('body').innerText({ timeout: 10000 }).catch(() => '');
  const cookies = await page.context().cookies('https://www.tradingview.com').catch(() => []);
  const cookieNames = cookies.map((cookie) => cookie.name).sort();
  const hasSessionCookie = cookieNames.some((name) => /^sessionid/i.test(name) || /sessionid|auth/i.test(name));
  const authRequired = /\/accounts\/signin|sign in|log in/i.test(url) || /\b(sign in|log in)\b/i.test(bodyText.slice(0, 3000));
  return {
    authenticated: hasSessionCookie && !authRequired,
    url,
    hasSessionCookie,
    authRequiredTextVisible: authRequired,
    cookieNames,
  };
}

async function firstVisible(page, locators) {
  for (const locator of locators) {
    const item = typeof locator === 'string' ? page.locator(locator).first() : locator.first();
    if (await item.isVisible().catch(() => false)) return item;
  }
  return null;
}

async function firstVisibleMatching(page, locators, predicate) {
  for (const locator of locators) {
    const collection = typeof locator === 'string' ? page.locator(locator) : locator;
    const count = Math.min(await collection.count().catch(() => 0), 150);
    for (let index = 0; index < count; index += 1) {
      const candidate = collection.nth(index);
      if (!(await candidate.isVisible().catch(() => false))) continue;
      const box = await candidate.boundingBox().catch(() => null);
      if (await predicate(candidate, box)) return candidate;
    }
  }
  return null;
}

function escapeRegExp(value) {
  return String(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

export async function clickFirst(page, locators, label) {
  const item = await firstVisible(page, locators);
  if (!item) throw new Error(`Could not find ${label}`);
  await item.click();
  return true;
}

export async function probeTradingViewSurfaces(page) {
  const bodyText = await page.locator('body').innerText({ timeout: 10000 }).catch(() => '');
  const title = await page.title().catch(() => '');
  return {
    chartLoaded: /TradingView|Watchlist|Indicators|Alert|Publish/i.test(bodyText) || /TradingView/i.test(title),
    pineEditorTextPresent: /Pine Editor/i.test(bodyText),
    strategyTesterTextPresent: /Strategy Tester/i.test(bodyText),
    exportTextPresent: /Export|Download/i.test(bodyText),
    title,
  };
}

export async function openBottomTab(page, names) {
  const labels = Array.isArray(names) ? names : [names];
  const locators = labels.flatMap((name) => [
    page.getByRole('tab', { name: new RegExp(name, 'i') }),
    page.getByRole('button', { name: new RegExp(name, 'i') }),
    page.getByText(new RegExp(name, 'i')),
  ]);
  return clickFirst(page, locators, labels.join('/'));
}

export async function openStrategyReport(page) {
  const bodyText = await page.locator('body').innerText({ timeout: 5000 }).catch(() => '');
  if (/Strategy Report|List of trades|Total P&L|Profit Factor/i.test(bodyText)) {
    const expandedHint = /Metrics|List of trades|Total P&L|Profit Factor/i.test(bodyText);
    if (expandedHint) return { method: 'already-visible' };
  }

  const labels = ['Strategy Report', 'Strategy Tester', 'Tester'];
  const locators = labels.flatMap((name) => [
    page.getByRole('tab', { name: new RegExp(name, 'i') }),
    page.getByRole('button', { name: new RegExp(name, 'i') }),
    page.getByText(new RegExp(name, 'i')),
  ]);
  await clickFirst(page, locators, labels.join('/'));
  await page.waitForTimeout(2500);

  const afterText = await page.locator('body').innerText({ timeout: 5000 }).catch(() => '');
  if (!/Strategy Report|List of trades|Total P&L|Profit Factor|Metrics/i.test(afterText)) {
    throw new Error('Clicked strategy surface but Strategy Report contents did not become visible');
  }
  return { method: 'clicked-strategy-report' };
}

export async function openStrategyMetricsTab(page) {
  const viewport = page.viewportSize() || { width: 1440, height: 950 };
  const metricsTab = await firstVisibleMatching(page, [
    page.getByRole('button', { name: /^Metrics$/i }),
    page.getByRole('tab', { name: /^Metrics$/i }),
    page.getByText(/^Metrics$/i),
  ], async (_candidate, box) => {
    if (!box) return false;
    return box.y > viewport.height * 0.34 && box.y < viewport.height * 0.47 && box.x < viewport.width * 0.20;
  });
  if (metricsTab) {
    await metricsTab.click({ force: true });
    await page.waitForTimeout(900);
    return { status: 'ok' };
  }
  return { status: 'not-found' };
}

export async function setStrategyReportDateRange(page, rangeMode) {
  if (!rangeMode || /^current|default|none$/i.test(String(rangeMode))) {
    return { status: 'skipped', rangeMode: rangeMode || null };
  }

  await openStrategyReport(page);
  const viewport = page.viewportSize() || { width: 1440, height: 950 };
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
    return /\d{4}.*(—|-).*?\d{4}|date|calendar/i.test(label);
  });
  if (dateButton) {
    await dateButton.click({ force: true });
  } else {
    await page.mouse.click(viewport.width * 0.57, viewport.height * 0.398);
  }
  await page.waitForTimeout(900);

  const labelsByMode = {
    'range-from-chart': ['Range from chart', 'Chart range'],
    'chart': ['Range from chart', 'Chart range'],
    'entire-history': ['Entire history', 'All history', 'All data', 'All'],
    'entire history': ['Entire history', 'All history', 'All data', 'All'],
    'all': ['Entire history', 'All history', 'All data', 'All'],
  };
  const targetLabels = labelsByMode[String(rangeMode).toLowerCase()] || [String(rangeMode)];
  let target = null;
  let targetLabel = targetLabels[0];
  for (const candidateLabel of targetLabels) {
    target = await firstVisible(page, [
      page.getByRole('menuitemcheckbox', { name: new RegExp(escapeRegExp(candidateLabel), 'i') }),
      page.getByRole('menuitem', { name: new RegExp(escapeRegExp(candidateLabel), 'i') }),
      page.getByText(new RegExp(`^${escapeRegExp(candidateLabel)}$`, 'i')),
    ]);
    if (target) {
      targetLabel = candidateLabel;
      break;
    }
  }
  if (!target) {
    const bodyText = await page.locator('body').innerText({ timeout: 5000 }).catch(() => '');
    throw new Error(`Could not find Strategy Tester date range option "${targetLabels.join(' | ')}". Visible text sample: ${bodyText.slice(-1200)}`);
  }

  await target.click({ force: true });
  await page.waitForTimeout(1200);
  return { status: 'ok', rangeMode, selected: targetLabel };
}

export async function waitForStrategyReportReady(page, options = {}) {
  const timeoutMs = Number(options.timeoutMs || 180000);
  const pollMs = Number(options.pollMs || 5000);
  const expectedTitle = options.expectedTitle || '';
  const start = Date.now();
  let lastText = '';

  while (Date.now() - start < timeoutMs) {
    await page.waitForTimeout(pollMs);
    await openStrategyReport(page).catch(() => {});
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
      };
    }
  }

  return {
    status: 'timeout',
    elapsedMs: Date.now() - start,
    textSample: lastText.slice(-1600),
  };
}

export async function openPineEditor(page) {
  await openBottomTab(page, ['Pine Editor', 'Pine']);
  await page.waitForTimeout(1500);
}

export async function setPineEditorText(page, source) {
  const monacoSet = await page.evaluate((value) => {
    const monaco = globalThis.monaco;
    if (monaco?.editor?.getModels) {
      const models = monaco.editor.getModels();
      if (models.length) {
        models[0].setValue(value);
        return true;
      }
    }
    return false;
  }, source).catch(() => false);
  if (monacoSet) return { method: 'monaco-model' };

  const editor = await firstVisible(page, [
    page.locator('.monaco-editor textarea'),
    page.locator('textarea'),
    page.locator('[contenteditable="true"]'),
    page.locator('.cm-content'),
    page.locator('.view-lines'),
  ]);
  if (!editor) throw new Error('Could not locate Pine Editor input');
  await editor.click({ force: true });
  await page.keyboard.press(process.platform === 'darwin' ? 'Meta+A' : 'Control+A');

  const clipboardPaste = await page.evaluate(async (value) => {
    await navigator.clipboard.writeText(value);
    return true;
  }, source).catch(() => false);
  if (clipboardPaste) {
    await page.keyboard.press(process.platform === 'darwin' ? 'Meta+V' : 'Control+V');
    await page.waitForTimeout(1500);
    return { method: 'clipboard-paste' };
  }

  if (process.env.TV_ALLOW_KEYBOARD_INSERT === '1') {
    await page.keyboard.insertText(source);
    return { method: 'keyboard-insert', warning: 'keyboard insertion can corrupt Pine indentation through editor auto-indent' };
  }

  throw new Error(
    'Could not write to clipboard for Pine Editor paste. Refusing keyboard insertion because it can corrupt Pine indentation. Set TV_ALLOW_KEYBOARD_INSERT=1 only for short one-line smoke tests.',
  );
}

export async function savePineScript(page, scriptName) {
  await clickFirst(page, [
    page.getByRole('button', { name: /^Save$/i }),
    page.getByRole('button', { name: /Save/i }),
    page.locator('button:has-text("Save")'),
  ], 'Save button');
  await page.waitForTimeout(1000);

  if (scriptName) {
    const nameInput = await firstVisible(page, [
      page.locator('input[placeholder*="name" i]'),
      page.locator('input[type="text"]'),
    ]);
    if (nameInput) {
      await nameInput.fill(scriptName).catch(() => {});
      const confirm = await firstVisible(page, [
        page.getByRole('button', { name: /Save|OK|Create/i }),
        page.locator('button:has-text("Save"), button:has-text("OK"), button:has-text("Create")'),
      ]);
      if (confirm) await confirm.click().catch(() => {});
    }
  }
  await page.waitForTimeout(3000);
}

export async function addPineToChart(page) {
  const addButton = await firstVisible(page, [
    page.getByRole('button', { name: /Add to chart|Update on chart/i }),
    page.locator('button:has-text("Add to chart"), button:has-text("Update on chart")'),
    page.locator('button[aria-label*="Add to chart" i], button[aria-label*="Update on chart" i]'),
    page.locator('button[title*="Add to chart" i], button[title*="Update on chart" i]'),
    page.locator('[data-name*="add-to-chart" i], [data-name*="update" i]'),
    page.getByText(/Add to chart|Update on chart/i),
  ]);
  if (!addButton) throw new Error('Could not find Add to chart button');
  const state = await addButton.evaluate((node) => ({
    disabled: Boolean(node.disabled) || node.getAttribute('aria-disabled') === 'true',
    text: String(node.textContent || ''),
    title: node.getAttribute('title') || '',
    aria: node.getAttribute('aria-label') || '',
  })).catch(() => ({ disabled: false, text: '', title: '', aria: '' }));
  if (state.disabled && /update on chart/i.test(`${state.text} ${state.title} ${state.aria}`)) {
    await page.waitForTimeout(1000);
    return { status: 'already-current', button: state };
  }
  await addButton.click({ force: true });
  await page.waitForTimeout(5000);
  return { status: 'clicked', button: state };
}

export async function closePineEditor(page) {
  const closeButton = await firstVisible(page, [
    page.getByRole('button', { name: /^Close$/i }),
    page.locator('button[aria-label*="Close" i]'),
    page.locator('[data-name*="close" i]'),
  ]);
  if (closeButton) {
    await closeButton.click().catch(() => {});
    await page.waitForTimeout(1500);
    return { status: 'ok', method: 'close-button' };
  }
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(1000);
  return { status: 'unknown', method: 'escape' };
}

export async function saveChartLayout(page) {
  const saveButton = await firstVisible(page, [
    page.getByRole('button', { name: /^Save$/i }),
    page.locator('button[aria-label*="Save" i]'),
    page.locator('button:has-text("Save")'),
    page.locator('[data-name*="save" i]'),
    page.locator('[aria-label*="Layout" i]'),
    page.getByText(/Sherlock|Save layout|Layout/i),
  ]);
  if (saveButton) {
    await saveButton.click();
    await page.waitForTimeout(3500);
    return { status: 'ok', method: 'button' };
  }

  await page.keyboard.press(process.platform === 'darwin' ? 'Meta+S' : 'Control+S');
  await page.waitForTimeout(3500);
  const bodyText = await page.locator('body').innerText({ timeout: 5000 }).catch(() => '');
  return {
    status: 'unknown',
    method: 'keyboard-shortcut',
    note: /saved|save/i.test(bodyText) ? 'Save-related text visible after shortcut' : 'No explicit save confirmation detected',
  };
}

export async function detectCompileStatus(page) {
  const bodyText = await page.locator('body').innerText({ timeout: 10000 }).catch(() => '');
  const lowered = bodyText.toLowerCase();
  const errorPatterns = [
    /script could not be translated/i,
    /compilation error/i,
    /syntax error/i,
    /undeclared identifier/i,
    /mismatched input/i,
    /cannot call/i,
    /error at/i,
  ];
  const successPatterns = [
    /added to chart/i,
    /script saved/i,
    /compiled/i,
    /updated on chart/i,
    /strategy report/i,
    /total p&l/i,
    /list of trades/i,
    /profit factor/i,
  ];
  const errors = errorPatterns.filter((pattern) => pattern.test(bodyText)).map((pattern) => String(pattern));
  const matchedSuccess = successPatterns.filter((pattern) => pattern.test(bodyText)).map((pattern) => String(pattern));
  const success = errors.length === 0 && matchedSuccess.length > 0;
  return {
    status: errors.length ? 'failed' : success ? 'ok' : 'unknown',
    matchedErrors: errors,
    matchedSuccess,
    textSample: lowered.slice(0, 4000),
  };
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

async function assertExpectedStrategyReport(page, expectedTitle) {
  if (!expectedTitle) return { status: 'skipped' };
  const bodyText = await page.locator('body').innerText({ timeout: 5000 }).catch(() => '');
  if (bodyText.includes(expectedTitle)) return { status: 'ok', expectedTitle };

  const match = bodyText.match(/Strategy Report\s+([^\n]+)\s+/i);
  const activeTitle = match?.[1]?.trim() || 'unknown';
  throw new Error(`Strategy Report is showing "${activeTitle}", not expected "${expectedTitle}". Install/add the target strategy and save the chart layout before running the matrix.`);
}

export async function exportStrategyData(page, outDir, item, timeoutMs = 120000, run = {}) {
  ensureDir(outDir);
  await openStrategyReport(page);
  await assertExpectedStrategyReport(page, run.expectedStrategyTitle || run.scriptTitle);
  await page.waitForTimeout(3500);
  const outPath = path.join(outDir, `${safeName(item.symbol)}_${safeName(item.label)}_strategy.csv`);
  const action = async () => {
    const tradesTab = await firstVisible(page, [
      page.getByRole('button', { name: /List of trades/i }),
      page.getByText(/List of trades/i),
    ]);
    if (tradesTab) {
      await tradesTab.click({ force: true });
      await page.waitForTimeout(1200);
    }
    const viewport = page.viewportSize() || { width: 1440, height: 950 };
    const exportButton = await firstVisibleMatching(page, [
      page.getByRole('button', { name: /Download|Export/i }),
      page.locator('button[aria-label*="Download" i]'),
      page.locator('button[aria-label*="Export" i]'),
      page.locator('button[title*="Download" i]'),
      page.locator('button[title*="Export" i]'),
      page.locator('[data-name*="download" i]'),
      page.locator('[data-name*="export" i]'),
      page.locator('[data-qa-id*="download" i]'),
      page.locator('[data-qa-id*="export" i]'),
      page.locator('button, [role="button"]'),
    ], async (candidate, box) => {
      if (!box) return false;
      const inStrategyHeader = box.y > viewport.height * 0.34 && box.y < viewport.height * 0.47 && box.x > viewport.width * 0.35 && box.x < viewport.width * 0.72;
      if (!inStrategyHeader) return false;
      const label = await candidate.evaluate((element) => [
        element.textContent || '',
        element.getAttribute('aria-label') || '',
        element.getAttribute('title') || '',
        element.getAttribute('data-name') || '',
        element.getAttribute('data-qa-id') || '',
      ].join(' ')).catch(() => '');
      if (/download|export|csv/i.test(label)) return true;
      const compactHeaderIcon = box.width >= 20 && box.width <= 44 && box.height >= 20 && box.height <= 44 && box.x > viewport.width * 0.44 && box.x < viewport.width * 0.55;
      return compactHeaderIcon;
    });
    const fallbackExportButton = exportButton || await firstVisible(page, [
      page.getByRole('button', { name: /Download|Export/i }),
      page.locator('button[aria-label*="Download" i]'),
      page.locator('button[aria-label*="Export" i]'),
      page.locator('button[title*="Download" i]'),
      page.locator('button[title*="Export" i]'),
      page.getByText(/Download|Export data|Export/i),
    ]);
    if (!fallbackExportButton) {
      const controls = await page.locator('button, [role="button"]').evaluateAll((elements) => elements
        .map((element) => {
          const rect = element.getBoundingClientRect();
          return {
            text: element.textContent?.trim().slice(0, 80) || '',
            aria: element.getAttribute('aria-label') || '',
            title: element.getAttribute('title') || '',
            dataName: element.getAttribute('data-name') || '',
            dataQaId: element.getAttribute('data-qa-id') || '',
            x: Math.round(rect.x),
            y: Math.round(rect.y),
            width: Math.round(rect.width),
            height: Math.round(rect.height),
          };
        })
        .filter((item) => item.width > 0 && item.height > 0 && item.y > 250 && item.x < 1050)
        .slice(0, 80));
      throw new Error(`Could not find Strategy Tester export control. Visible report-area controls: ${JSON.stringify(controls)}`);
    }
    await fallbackExportButton.click({ force: true });
    await page.waitForTimeout(800);
    const exportData = await firstVisible(page, [
      page.getByRole('menuitem', { name: /Export data|Download data|Download CSV|Download|Export/i }),
      page.getByRole('menuitem', { name: /Export/i }),
      page.getByRole('menuitem', { name: /Download/i }),
      page.getByRole('button', { name: /Download CSV|Download|Export/i }),
      page.locator('[role="menuitem"]:has-text("Export")'),
      page.locator('[role="menuitem"]:has-text("Download")'),
    ]);
    if (exportData) await exportData.click({ force: true });
  };
  return downloadFromAction(page, action, outPath, timeoutMs);
}

export async function exportChartData(page, outDir, item, timeoutMs = 120000) {
  ensureDir(outDir);
  const outPath = path.join(outDir, `${safeName(item.symbol)}_${safeName(item.label)}_chart.csv`);
  const action = async () => {
    const menu = await firstVisible(page, [
      page.getByRole('button', { name: /main menu|menu|more/i }),
      page.locator('button[aria-label*="menu" i]'),
      page.locator('button[aria-label*="More" i]'),
    ]);
    if (menu) {
      await menu.click();
      await page.waitForTimeout(800);
    }
    const exportData = await firstVisible(page, [
      page.getByText(/Export chart data/i),
      page.getByText(/Export data/i),
      page.getByRole('menuitem', { name: /Export/i }),
    ]);
    if (!exportData) throw new Error('Could not find chart data export control');
    await exportData.click();
  };
  return downloadFromAction(page, action, outPath, timeoutMs);
}

export async function saveScreenshot(page, filePath) {
  ensureDir(path.dirname(filePath));
  await page.screenshot({ path: filePath, fullPage: false }).catch(() => {});
}
