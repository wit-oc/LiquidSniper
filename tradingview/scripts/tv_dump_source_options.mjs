#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import {
  commandArtifactDir,
  loadConfig,
  parseArgs,
  resolveFromRoot,
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
import { openStrategySettings } from './tv_apply_v6_mappings.mjs';

async function installPineInCurrentSession(page, loaded, args) {
  const scriptPath = resolveFromRoot(loaded.root, args.script || loaded.run.scriptPath);
  const source = fs.readFileSync(scriptPath, 'utf8');
  const scriptName = args.name || loaded.run.scriptName || `Codex Scratch - ${path.basename(scriptPath, '.pine')}`;
  await openPineEditor(page);
  const editor = await setPineEditorText(page, source);
  await savePineScript(page, scriptName);
  await addPineToChart(page);
  const compile = await detectCompileStatus(page);
  const closeEditor = await closePineEditor(page).catch((error) => ({ status: 'failed', error: String(error.message || error) }));
  await page.waitForTimeout(1500);
  return { scriptPath, scriptName, editor, compile, closeEditor };
}

async function clickRowCombobox(page, labelText) {
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
    const combos = [...document.querySelectorAll('button[role="combobox"]')]
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
      .sort((a, b) => a.distance - b.distance);
    return combos[0] || null;
  }, labelText);
  if (!comboBox) throw new Error(`Could not locate combobox for row label: ${labelText}`);
  await page.mouse.click(comboBox.x + comboBox.width / 2, comboBox.y + comboBox.height / 2);
  await page.waitForTimeout(1200);
  return { labelBox: { x: box.x, y: box.y, width: box.width, height: box.height }, comboBox };
}

async function visibleOptions(page) {
  return page.locator('[role="option"], [role="menuitem"], button, [data-name]').evaluateAll((nodes) => {
    const compact = (value) => String(value || '').replace(/\s+/g, ' ').trim();
    return nodes
      .map((node) => {
        const rect = node.getBoundingClientRect();
        const style = window.getComputedStyle(node);
        return {
          text: compact(node.textContent),
          aria: node.getAttribute('aria-label'),
          title: node.getAttribute('title'),
          role: node.getAttribute('role'),
          dataName: node.getAttribute('data-name'),
          x: Math.round(rect.x),
          y: Math.round(rect.y),
          width: Math.round(rect.width),
          height: Math.round(rect.height),
          visible: rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none',
        };
      })
      .filter((item) => item.visible && (item.text || item.aria || item.title))
      .sort((a, b) => a.y - b.y || a.x - b.x);
  });
}

function annotateDuplicates(options) {
  const seen = new Map();
  return options.map((option) => {
    const key = option.text || option.aria || option.title || '';
    const count = seen.get(key) || 0;
    seen.set(key, count + 1);
    return {
      ...option,
      occurrence: count + 1,
    };
  });
}

async function main() {
  const args = parseArgs();
  const loaded = loadConfig(args);
  const outDir = commandArtifactDir(loaded.artifactsDir, loaded.runId, 'dump-source-options');
  const title = args.title || loaded.run.scriptTitle || loaded.run.expectedStrategyTitle || '';
  const rowLabel = args.row || 'Slot 01';
  let context;

  try {
    const browser = await launchTradingView({ defaults: loaded.defaults, artifactsDir: outDir });
    context = browser.context;
    const page = browser.page;
    await gotoChart(page, loaded.run, loaded.run.symbols?.[0] || 'BINANCE:BTCUSDT', loaded.run.timeframes?.[0]?.interval || '15');
    const auth = await checkAuth(page);
    if (!auth.authenticated) throw new Error(`TradingView session is not authenticated: ${auth.url}`);
    await page.waitForTimeout(Number(loaded.run.waitAfterLoadMs || loaded.defaults.waitAfterLoadMs || 8000));
    const install = args['install-first'] ? await installPineInCurrentSession(page, loaded, args) : null;

    const openedSettings = await openStrategySettings(page, title);
    const rowBox = await clickRowCombobox(page, rowLabel);
    const screenshot = path.join(outDir, 'source-options.png');
    await saveScreenshot(page, screenshot);
    const bodyTextPath = path.join(outDir, 'body.txt');
    fs.writeFileSync(bodyTextPath, await page.locator('body').innerText({ timeout: 10000 }).catch(() => ''));
    const options = annotateDuplicates(await visibleOptions(page));
    const report = {
      status: 'ok',
      command: 'tv-dump-source-options',
      runId: loaded.runId,
      outDir,
      title,
      rowLabel,
      install,
      openedSettings,
      rowBox,
      screenshot,
      bodyTextPath,
      options,
    };
    writeReport(path.join(outDir, 'source-options-report.json'), report);
    console.log(JSON.stringify(report, null, 2));
  } catch (error) {
    const report = {
      status: 'failed',
      command: 'tv-dump-source-options',
      runId: loaded.runId,
      outDir,
      title,
      rowLabel,
      error: String(error.stack || error),
    };
    writeReport(path.join(outDir, 'source-options-report.json'), report);
    console.log(JSON.stringify(report, null, 2));
    process.exitCode = 1;
  } finally {
    await context?.close().catch(() => {});
  }
}

await main();
