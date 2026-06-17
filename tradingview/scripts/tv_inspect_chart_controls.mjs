#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import {
  commandArtifactDir,
  loadConfig,
  parseArgs,
  writeReport,
} from '../../codex/skills/tradingview-pine-loop/scripts/lib/config.mjs';
import { launchTradingView } from '../../codex/skills/tradingview-pine-loop/scripts/lib/browser.mjs';
import { checkAuth, gotoChart, saveScreenshot } from '../../codex/skills/tradingview-pine-loop/scripts/lib/actions.mjs';

function compact(value) {
  return String(value || '').replace(/\s+/g, ' ').trim().slice(0, 160);
}

function escapeRegExp(value) {
  return String(value || '').replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function absoluteUrl(baseUrl, maybeUrl) {
  if (!maybeUrl) return '';
  try {
    return new URL(maybeUrl, baseUrl).toString();
  } catch {
    return '';
  }
}

async function activeLayoutName(page) {
  const aria = await page.locator('[data-qa-id="main-menu-button"]').first().getAttribute('aria-label', { timeout: 1500 }).catch(() => '');
  const match = String(aria || '').match(/Active layout:\s*([^\n\r]+)/i);
  return match ? compact(match[1]) : null;
}

async function waitForActiveLayout(page, expected, timeoutMs = 30000) {
  const started = Date.now();
  let actual = await activeLayoutName(page);
  while (compact(actual).toLowerCase() !== expected.toLowerCase() && Date.now() - started < timeoutMs) {
    await page.waitForTimeout(1000);
    actual = await activeLayoutName(page);
  }
  return actual;
}

async function loadLayoutByName(page, layoutName) {
  const expected = compact(layoutName);
  if (!expected) return { status: 'skipped', reason: 'No layout name provided.' };
  const before = await activeLayoutName(page);
  if (compact(before).toLowerCase() === expected.toLowerCase()) {
    return { status: 'already-active', expected, before, after: before };
  }

  const saveLoadMenu = page.locator('[data-name="save-load-menu"]').first();
  if (await saveLoadMenu.isVisible().catch(() => false)) {
    await saveLoadMenu.click({ timeout: 10000 });
  } else {
    await page.getByLabel(/Manage layouts/i).first().click({ timeout: 10000 });
  }
  await page.waitForTimeout(600);
  const openLayoutRow = page.getByRole('row', { name: /Open layout/i }).first();
  if (await openLayoutRow.isVisible().catch(() => false)) {
    await openLayoutRow.click();
  } else {
    await page.locator('text=/Open layout/i').first().click({ timeout: 10000 });
  }
  await page.waitForTimeout(1500);

  const layoutRow = page
    .locator('[data-name="load-chart-dialog-item"]')
    .filter({ hasText: new RegExp(`^\\s*${escapeRegExp(expected)}`, 'i') })
    .first();
  if (!(await layoutRow.isVisible().catch(() => false))) {
    const bodyText = await page.locator('body').innerText({ timeout: 5000 }).catch(() => '');
    throw new Error(`Could not find TradingView layout "${expected}". Visible text sample: ${bodyText.slice(-1800)}`);
  }

  const rowMeta = await layoutRow.evaluate((node) => ({
    text: String(node.textContent || '').replace(/\s+/g, ' ').trim(),
    href: node.getAttribute('href') || node.href || '',
    dataName: node.getAttribute('data-name') || '',
    role: node.getAttribute('role') || '',
  })).catch(() => ({}));
  const directUrl = absoluteUrl(page.url(), rowMeta.href);
  const title = layoutRow
    .locator('[data-name="list-item-title"]')
    .filter({ hasText: new RegExp(`^\\s*${escapeRegExp(expected)}\\s*$`, 'i') })
    .first();
  const titleVisible = await title.isVisible().catch(() => false);
  const method = titleVisible ? 'title-click' : 'row-click';
  await (titleVisible ? title : layoutRow).click({ force: true });

  let after = await waitForActiveLayout(page, expected, 30000);
  let fallback = null;
  if (compact(after).toLowerCase() !== expected.toLowerCase() && directUrl && directUrl !== page.url()) {
    await page.goto(directUrl, { waitUntil: 'domcontentloaded', timeout: 60000 });
    await page.waitForTimeout(5000);
    after = await waitForActiveLayout(page, expected, 30000);
    fallback = { method: 'row-href-goto', directUrl };
  }
  return {
    status: compact(after).toLowerCase() === expected.toLowerCase() ? 'ok' : 'failed',
    expected,
    before,
    after,
    method,
    rowMeta,
    directUrl,
    fallback,
  };
}

async function visibleControls(page) {
  return page.locator('button, [role="button"], [aria-label], [data-name]').evaluateAll((nodes) => {
    return nodes
      .map((node) => {
        const rect = node.getBoundingClientRect();
        const style = window.getComputedStyle(node);
        return {
          tag: node.tagName,
          text: node.textContent,
          aria: node.getAttribute('aria-label'),
          role: node.getAttribute('role'),
          title: node.getAttribute('title'),
          dataName: node.getAttribute('data-name'),
          href: node.getAttribute('href') || node.href || '',
          className: node.getAttribute('class'),
          x: Math.round(rect.x),
          y: Math.round(rect.y),
          width: Math.round(rect.width),
          height: Math.round(rect.height),
          visible: rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none',
        };
      })
      .filter((item) => item.visible)
      .sort((a, b) => a.y - b.y || a.x - b.x);
  });
}

async function clickStrategySettings(page, strategyTitle) {
  const legendToggle = await page.locator('button[title="Hide indicators legend"], button[aria-label="Hide indicators legend"]').first();
  if (await legendToggle.isVisible().catch(() => false)) {
    await legendToggle.click().catch(() => {});
    await page.waitForTimeout(800);
  }
  await page.mouse.click(84, 101).catch(() => {});
  await page.waitForTimeout(800);
  // TradingView hides per-study legend actions until the row is hovered.
  // In this saved layout the v6 strategy row is in the main chart legend.
  await page.mouse.move(180, 318);
  await page.waitForTimeout(500);
  const controls = await visibleControls(page);
  const strategyIndex = controls.findIndex((item) => compact(item.text).includes(strategyTitle));
  const strategyY = strategyIndex >= 0 ? controls[strategyIndex].y : null;
  const candidates = controls.filter((item) => {
    const isSettings = /settings/i.test(item.aria || '') || /settings/i.test(item.title || '');
    const inChartLegend = item.x >= 250 && item.x <= 520 && item.y >= 220 && item.y <= 380;
    const nearStrategy = strategyY == null || Math.abs(item.y - strategyY) <= 36;
    return isSettings && inChartLegend && nearStrategy;
  });
  const strategyRowY = 318;
  const sortedCandidates = candidates.sort((a, b) => Math.abs(a.y - strategyRowY) - Math.abs(b.y - strategyRowY));
  const target = sortedCandidates[0] || controls
    .filter((item) => {
    const isSettings = /settings/i.test(item.aria || '') || /settings/i.test(item.title || '');
    return isSettings && item.x >= 250 && item.x <= 520 && item.y >= 220 && item.y <= 380;
    })
    .sort((a, b) => Math.abs(a.y - strategyRowY) - Math.abs(b.y - strategyRowY))[0];
  if (!target) {
    const settingsControls = controls
      .filter((item) => /settings/i.test(item.aria || '') || /settings/i.test(item.title || ''))
      .map((item) => ({
        x: item.x,
        y: item.y,
        width: item.width,
        height: item.height,
        text: compact(item.text),
        aria: item.aria,
        title: item.title,
        dataName: item.dataName,
      }));
    throw new Error(`Could not find settings button for ${strategyTitle}. Settings candidates: ${JSON.stringify(settingsControls)}`);
  }
  await page.mouse.click(target.x + target.width / 2, target.y + target.height / 2);
  await page.waitForTimeout(2500);
  return target;
}

async function main() {
  const args = parseArgs();
  const loaded = loadConfig(args);
  const outDir = commandArtifactDir(loaded.artifactsDir, loaded.runId, 'inspect-controls');
  let context;

  try {
    const browser = await launchTradingView({ defaults: loaded.defaults, artifactsDir: outDir });
    context = browser.context;
    const page = browser.page;
    await gotoChart(page, loaded.run, loaded.run.symbols?.[0] || 'BINANCE:BTCUSDT', loaded.run.timeframes?.[0]?.interval || '15');
    const auth = await checkAuth(page);
    if (!auth.authenticated) throw new Error(`TradingView session is not authenticated: ${auth.url}`);
    await page.waitForTimeout(Number(loaded.run.waitAfterLoadMs || loaded.defaults.waitAfterLoadMs || 8000));
    const layoutLoadName = args['load-layout'] || (loaded.run.loadExpectedActiveLayout ? loaded.run.expectedActiveLayout : null);
    const layoutLoad = layoutLoadName ? await loadLayoutByName(page, layoutLoadName) : null;
    if (layoutLoad?.status === 'ok') {
      await gotoChart(page, loaded.run, loaded.run.symbols?.[0] || 'BINANCE:BTCUSDT', loaded.run.timeframes?.[0]?.interval || '15');
      await page.waitForTimeout(Number(loaded.run.waitAfterLayoutLoadMs || loaded.run.waitAfterLoadMs || loaded.defaults.waitAfterLoadMs || 8000));
    }
    const openedSettings = args['open-strategy-settings']
      ? await clickStrategySettings(page, loaded.run.expectedStrategyTitle || loaded.run.scriptTitle || '')
      : null;
    const comboY = args['click-combobox-y'] ? Number(args['click-combobox-y']) : null;
    if (Number.isFinite(comboY)) {
      await page.mouse.click(799, comboY + 17);
      await page.waitForTimeout(1500);
    }
    const comboIndex = args['click-combobox-index'] ? Number(args['click-combobox-index']) : null;
    if (Number.isInteger(comboIndex)) {
      const combo = page.locator('button[role="combobox"]').nth(comboIndex);
      await combo.scrollIntoViewIfNeeded();
      await page.waitForTimeout(300);
      await combo.click();
      await page.waitForTimeout(1500);
    }
    const clicks = typeof args.clicks === 'string'
      ? String(args.clicks)
        .split(';')
        .map((item) => item.split(',').map((part) => Number(part.trim())))
        .filter(([x, y]) => Number.isFinite(x) && Number.isFinite(y))
      : [];
    const clickX = args['click-x'] ? Number(args['click-x']) : null;
    const clickY = args['click-y'] ? Number(args['click-y']) : null;
    if (clicks.length) {
      for (const [x, y] of clicks) {
        await page.mouse.click(x, y);
        await page.waitForTimeout(1500);
      }
    } else if (Number.isFinite(clickX) && Number.isFinite(clickY)) {
      await page.mouse.click(clickX, clickY);
      await page.waitForTimeout(1500);
    }
    const screenshot = path.join(outDir, 'chart.png');
    await saveScreenshot(page, screenshot);
    const bodyText = await page.locator('body').innerText({ timeout: 10000 }).catch(() => '');
    const controls = (await visibleControls(page)).map((item) => ({
      ...item,
      text: compact(item.text),
      className: compact(item.className),
    }));
    const report = {
      status: 'ok',
      command: 'tv-inspect-chart-controls',
      runId: loaded.runId,
      outDir,
      url: page.url(),
      activeLayout: await activeLayoutName(page),
      expectedActiveLayout: loaded.run.expectedActiveLayout || null,
      layoutLoad,
      screenshot,
      openedSettings,
      bodyTextPath: path.join(outDir, 'body.txt'),
      controls,
    };
    fs.writeFileSync(report.bodyTextPath, bodyText);
    writeReport(path.join(outDir, 'inspect-controls-report.json'), report);
    console.log(JSON.stringify(report, null, 2));
  } catch (error) {
    const report = {
      status: 'failed',
      command: 'tv-inspect-chart-controls',
      runId: loaded.runId,
      outDir,
      error: String(error.stack || error),
    };
    writeReport(path.join(outDir, 'inspect-controls-report.json'), report);
    console.log(JSON.stringify(report, null, 2));
    process.exitCode = 1;
  } finally {
    await context?.close().catch(() => {});
  }
}

await main();
