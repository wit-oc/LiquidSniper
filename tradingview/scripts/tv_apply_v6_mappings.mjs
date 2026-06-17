#!/usr/bin/env node
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  commandArtifactDir,
  loadConfig,
  parseArgs,
  writeReport,
} from '../../codex/skills/tradingview-pine-loop/scripts/lib/config.mjs';
import { launchTradingView } from '../../codex/skills/tradingview-pine-loop/scripts/lib/browser.mjs';
import { checkAuth, gotoChart, saveScreenshot } from '../../codex/skills/tradingview-pine-loop/scripts/lib/actions.mjs';

const STRATEGY_ROW_Y = 318;

export const DEFAULT_MAPPINGS = [
  {
    label: 'REQ Oracle Strength',
    value: 'The Oracle Strength - [Unity] - V2: Oracle Strength',
  },
  {
    label: 'REQ Oracle AIO Up Trend',
    value: 'The Oracle AIO - [Unity] - V2: Up trend',
  },
  {
    label: 'REQ Oracle AIO Down Trend',
    value: 'The Oracle AIO - [Unity] - V2: Down Trend',
  },
  {
    label: 'M14 HTF Phase1 CHoCH Direction',
    value: 'HTF Phase 1 Structure v3.3 (structure-first): Bus CHoCH Direction',
  },
  {
    label: 'M15 CHoCH Sequence',
    value: 'Filter Orders',
  },
];

function mappingsFromOptions(options = {}) {
  return Array.isArray(options.mappings) && options.mappings.length ? options.mappings : DEFAULT_MAPPINGS;
}

async function visibleControls(page) {
  return page.locator('button, [role="button"], [aria-label], [data-name]').evaluateAll((nodes) => {
    return nodes
      .map((node) => {
        const rect = node.getBoundingClientRect();
        const style = window.getComputedStyle(node);
        return {
          text: String(node.textContent || '').replace(/\s+/g, ' ').trim(),
          aria: node.getAttribute('aria-label'),
          title: node.getAttribute('title'),
          x: Math.round(rect.x),
          y: Math.round(rect.y),
          width: Math.round(rect.width),
          height: Math.round(rect.height),
          visible: rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none',
        };
      })
      .filter((item) => item.visible);
  });
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

async function visibleTextCenterY(page, text) {
  const box = await visibleTextBox(page, text);
  return box ? box.y + box.height / 2 : null;
}

async function visibleTextBox(page, text) {
  return page.evaluate((needle) => {
    const compact = (value) => String(value || '').replace(/\s+/g, ' ').trim();
    const needleLower = compact(needle).toLowerCase();
    const nodes = [...document.querySelectorAll('body *')]
      .map((node) => {
        const rect = node.getBoundingClientRect();
        const style = window.getComputedStyle(node);
        return {
          text: compact(node.textContent),
          x: rect.x,
          y: rect.y + rect.height / 2,
          top: rect.y,
          width: rect.width,
          height: rect.height,
          area: rect.width * rect.height,
          visible: rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none',
        };
      })
      .filter((item) => item.visible && item.text.toLowerCase().includes(needleLower) && item.area > 0 && item.area < 30000)
      .sort((a, b) => a.area - b.area);
    return nodes[0] || null;
  }, text).catch(() => null);
}

async function strategyDialogText(page) {
  const candidates = [
    page.locator('[data-name="indicator-properties-dialog"]').first(),
    page.locator('[role="dialog"]').filter({ hasText: /Inputs|Style|Properties|Visibility/i }).first(),
    page.locator('[data-dialog-name], [data-name*="dialog" i]').filter({ hasText: /Inputs|Style|Properties|Visibility/i }).first(),
  ];
  for (const candidate of candidates) {
    const text = await candidate.innerText({ timeout: 2500 }).catch(() => '');
    if (text) return text;
  }
  return '';
}

async function closeAnyDialogOrMenu(page) {
  await page.keyboard.press('Escape').catch(() => {});
  await page.waitForTimeout(400);
}

async function openStrategyPanelSettings(page, strategyTitle) {
  const titleBox = await visibleTextBox(page, strategyTitle);
  if (!titleBox || titleBox.y < 250) return { status: 'skipped', reason: 'strategy title not visible in tester panel', titleBox };

  await page.mouse.click(titleBox.x + titleBox.width + 14, titleBox.y);
  await page.waitForTimeout(900);
  const settingsItem = await firstVisible(page, [
    page.getByRole('menuitem', { name: /settings/i }),
    page.getByText(/^Settings$/i),
    page.getByText(/Strategy settings/i),
    page.locator('[role="menuitem"]:has-text("Settings")'),
  ]);
  if (!settingsItem) {
    await closeAnyDialogOrMenu(page);
    return { status: 'failed', reason: 'settings menu item not found', titleBox };
  }

  await settingsItem.click({ force: true });
  await page.waitForTimeout(2000);
  return { status: 'clicked', titleBox };
}

async function openIndicatorLegend(page, strategyTitle) {
  const probeLegendState = async () => {
    const strategyY = await visibleTextCenterY(page, strategyTitle);
    const controls = await visibleControls(page);
    const hasSettings = controls.some((item) => {
      const isSettings = /settings/i.test(item.aria || '') || /settings/i.test(item.title || '');
      return isSettings && item.x >= 200 && item.x <= 620 && item.y >= 35 && item.y <= 860;
    });
    return { strategyY, hasSettings };
  };

  const initialState = await probeLegendState();
  if (initialState.hasSettings && initialState.strategyY) {
    return { status: 'ok', strategyY: initialState.strategyY };
  }

  const attempts = [
    async () => {
      const legendButton = await firstVisible(page, [
        page.locator('button[aria-label*="Show indicators legend" i]'),
        page.locator('button[title*="Show indicators legend" i]'),
        page.locator('[aria-label*="Show indicators legend" i]'),
      ]);
      if (legendButton) await legendButton.click({ force: true });
    },
    async () => { await page.mouse.click(80, 82); },
    async () => { await page.mouse.click(84, 101); },
    async () => { await page.mouse.click(68, 58); },
  ];

  for (const attempt of attempts) {
    await attempt().catch(() => {});
    await page.waitForTimeout(900);
    const state = await probeLegendState();
    if (state.hasSettings && state.strategyY) {
      return { status: 'ok', strategyY: state.strategyY };
    }
    await page.keyboard.press('Escape').catch(() => {});
    await page.waitForTimeout(250);
  }

  return { status: 'failed', strategyY: null };
}

export async function openStrategySettings(page, strategyTitle) {
  const reportTitle = page.getByText('Strategy Report', { exact: true }).first();
  const reportBox = await reportTitle.boundingBox().catch(() => null);
  if (reportBox && reportBox.y > 250) {
    const collapseButton = page.locator('[data-name="toggle-visibility-button"]').first();
    if (await collapseButton.isVisible().catch(() => false)) {
      await collapseButton.click({ force: true }).catch(() => {});
    } else {
      await page.mouse.click(903, reportBox.y + reportBox.height / 2).catch(() => {});
    }
    await page.waitForTimeout(1800);
  }

  const legendOpen = await openIndicatorLegend(page, strategyTitle);
  const strategyY = legendOpen.strategyY || STRATEGY_ROW_Y;
  await page.mouse.move(180, strategyY);
  await page.waitForTimeout(500);

  const controls = await visibleControls(page);
  const rowCandidates = controls
    .filter((item) => {
      const isSettings = /settings/i.test(item.aria || '') || /settings/i.test(item.title || '');
      return isSettings && item.x >= 240 && item.x <= 540 && item.y >= 60 && item.y <= 850 && Math.abs((item.y + item.height / 2) - strategyY) <= 40;
    })
    .sort((a, b) => Math.abs((a.y + a.height / 2) - strategyY) - Math.abs((b.y + b.height / 2) - strategyY));
  const fixedCandidates = controls
    .filter((item) => {
      const isSettings = /settings/i.test(item.aria || '') || /settings/i.test(item.title || '');
      return isSettings && item.x >= 250 && item.x <= 520 && item.y >= 220 && item.y <= 380;
    })
    .sort((a, b) => Math.abs(a.y - STRATEGY_ROW_Y) - Math.abs(b.y - STRATEGY_ROW_Y));
  const looseCandidates = controls
    .filter((item) => {
      const isSettings = /settings/i.test(item.aria || '') || /settings/i.test(item.title || '');
      return isSettings && item.x >= 200 && item.x <= 620 && item.y >= 35 && item.y <= 860;
    })
    .sort((a, b) => Math.abs((a.y + a.height / 2) - strategyY) - Math.abs((b.y + b.height / 2) - strategyY));
  const candidates = rowCandidates.length ? rowCandidates : fixedCandidates.length ? fixedCandidates : looseCandidates;
  const target = candidates[0];
  if (!target) {
    const settingsControls = controls
      .filter((item) => /settings/i.test(item.aria || '') || /settings/i.test(item.title || ''))
      .map((item) => ({
        x: item.x,
        y: item.y,
        width: item.width,
        height: item.height,
        text: String(item.text || '').replace(/\s+/g, ' ').trim().slice(0, 80),
        aria: item.aria,
        title: item.title,
      }))
      .slice(0, 30);
    throw new Error(`Could not find settings button for ${strategyTitle}. Legend: ${JSON.stringify(legendOpen)} Settings: ${JSON.stringify(settingsControls)}`);
  }
  await page.mouse.click(target.x + target.width / 2, target.y + target.height / 2);
  await page.waitForTimeout(2500);

  const dialogText = await page.locator('[data-name="indicator-properties-dialog"]').innerText({ timeout: 10000 }).catch(() => '');
  const firstDialogText = dialogText || await strategyDialogText(page);
  if (!firstDialogText.toLowerCase().includes(strategyTitle.toLowerCase())) {
    await closeAnyDialogOrMenu(page);
    const panelOpen = await openStrategyPanelSettings(page, strategyTitle);
    const panelDialogText = await strategyDialogText(page);
    if (!panelDialogText.toLowerCase().includes(strategyTitle.toLowerCase())) {
      throw new Error(`Opened wrong settings dialog. Expected "${strategyTitle}", saw "${panelDialogText.slice(0, 120) || firstDialogText.slice(0, 120)}". Panel fallback: ${JSON.stringify(panelOpen)}`);
    }
  }
  return target;
}

export async function rowValue(page, labelText) {
  return page.evaluate((label) => {
    const elements = [...document.querySelectorAll('body *')];
    const labels = elements.filter((node) => (node.textContent || '').trim() === label);
    if (!labels.length) return null;
    const labelRect = labels[0].getBoundingClientRect();
    const labelCenter = labelRect.y + labelRect.height / 2;
    const combos = [...document.querySelectorAll('button[role="combobox"]')].map((node) => {
      const rect = node.getBoundingClientRect();
      return {
        text: (node.textContent || '').replace(/\s+/g, ' ').trim(),
        x: rect.x,
        y: rect.y,
        height: rect.height,
        distance: Math.abs((rect.y + rect.height / 2) - labelCenter),
      };
    });
    return combos
      .filter((combo) => combo.x > labelRect.x)
      .sort((a, b) => a.distance - b.distance)[0]?.text || null;
  }, labelText);
}

export async function selectRowValue(page, labelText, optionText) {
  const label = page.getByText(labelText, { exact: true }).first();
  await label.scrollIntoViewIfNeeded();
  await page.waitForTimeout(250);
  const box = await label.boundingBox();
  if (!box) throw new Error(`Could not locate row label: ${labelText}`);

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
  const option = page.getByText(optionText, { exact: true }).last();
  await option.scrollIntoViewIfNeeded();
  await option.click();
  await page.waitForTimeout(800);
}

export async function collectValues(page, mappings = DEFAULT_MAPPINGS) {
  const out = {};
  for (const item of mappings) {
    out[item.label] = await rowValue(page, item.label);
  }
  return out;
}

export async function applyV6MappingsToPage(page, strategyTitle, options = {}) {
  const mappings = mappingsFromOptions(options);
  const openedSettings = await openStrategySettings(page, strategyTitle);
  const before = await collectValues(page, mappings);

  for (const item of mappings) {
    if (before[item.label] !== item.value) {
      await selectRowValue(page, item.label, item.value);
    }
  }

  const after = await collectValues(page, mappings);
  const expected = Object.fromEntries(mappings.map((item) => [item.label, item.value]));
  const status = mappings.every((item) => after[item.label] === item.value) ? 'ok' : 'failed';
  const okButton = await firstVisible(page, [
    page.getByRole('button', { name: /^Ok$/i }),
    page.getByRole('button', { name: /^OK$/i }),
    page.locator('[data-name*="submit" i]'),
    page.locator('button:has-text("Ok")'),
    page.locator('button:has-text("OK")'),
  ]);
  if (okButton) {
    await okButton.click({ force: true });
  } else {
    await page.keyboard.press('Enter').catch(() => {});
    await page.waitForTimeout(800);
    const dialogStillOpen = await page.locator('[data-name="indicator-properties-dialog"]').isVisible().catch(() => false);
    if (dialogStillOpen) {
      await page.keyboard.press('Escape').catch(() => {});
    }
  }
  await page.waitForTimeout(Number(options.waitAfterOkMs ?? 4000));

  return {
    status,
    openedSettings,
    mappings,
    before,
    after,
    expected,
  };
}

async function main() {
  const args = parseArgs();
  const loaded = loadConfig(args);
  const outDir = commandArtifactDir(loaded.artifactsDir, loaded.runId, 'apply-v6-mappings');
  let context;

  try {
    const browser = await launchTradingView({ defaults: loaded.defaults, artifactsDir: outDir });
    context = browser.context;
    const page = browser.page;
    await gotoChart(page, loaded.run, loaded.run.symbols?.[0] || 'BINANCE:BTCUSDT', loaded.run.timeframes?.[0]?.interval || '15');
    const auth = await checkAuth(page);
    if (!auth.authenticated) throw new Error(`TradingView session is not authenticated: ${auth.url}`);
    await page.waitForTimeout(Number(loaded.run.waitAfterLoadMs || loaded.defaults.waitAfterLoadMs || 8000));

    const mapping = await applyV6MappingsToPage(page, loaded.run.expectedStrategyTitle || loaded.run.scriptTitle || '', {
      mappings: loaded.run.v6Mappings,
    });
    const screenshot = path.join(outDir, 'mapped-layout.png');
    await saveScreenshot(page, screenshot);
    const report = {
      status: mapping.status,
      command: 'tv-apply-v6-mappings',
      runId: loaded.runId,
      outDir,
      ...mapping,
      screenshot,
    };
    writeReport(path.join(outDir, 'apply-v6-mappings-report.json'), report);
    console.log(JSON.stringify(report, null, 2));
    if (report.status !== 'ok') process.exitCode = 1;
  } catch (error) {
    const report = {
      status: 'failed',
      command: 'tv-apply-v6-mappings',
      runId: loaded.runId,
      outDir,
      error: String(error.stack || error),
    };
    writeReport(path.join(outDir, 'apply-v6-mappings-report.json'), report);
    console.log(JSON.stringify(report, null, 2));
    process.exitCode = 1;
  } finally {
    await context?.close().catch(() => {});
  }
}

if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) {
  await main();
}
