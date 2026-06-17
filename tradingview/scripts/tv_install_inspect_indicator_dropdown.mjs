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

function compact(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

async function visibleControls(page) {
  return page.locator('button, [role="button"], [aria-label], [data-name], [role="menuitem"]').evaluateAll((nodes) => {
    const compactText = (value) => String(value || '').replace(/\s+/g, ' ').trim();
    return nodes
      .map((node) => {
        const rect = node.getBoundingClientRect();
        const style = window.getComputedStyle(node);
        return {
          tag: node.tagName,
          text: compactText(node.textContent),
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
      .filter((item) => item.visible && (item.text || item.aria || item.title || item.dataName))
      .sort((a, b) => a.y - b.y || a.x - b.x);
  });
}

async function main() {
  const args = parseArgs();
  const loaded = loadConfig(args);
  const outDir = commandArtifactDir(loaded.artifactsDir, loaded.runId, 'install-inspect-dropdown');
  let context;

  try {
    const scriptPath = resolveFromRoot(loaded.root, args.script || loaded.run.scriptPath);
    const source = fs.readFileSync(scriptPath, 'utf8');
    const scriptName = args.name || loaded.run.scriptName || `Codex Scratch - ${path.basename(scriptPath, '.pine')}`;
    const browser = await launchTradingView({ defaults: loaded.defaults, artifactsDir: outDir });
    context = browser.context;
    const page = browser.page;
    await gotoChart(page, loaded.run, loaded.run.symbols?.[0] || 'BINANCE:BTCUSDT', loaded.run.timeframes?.[0]?.interval || '15');
    const auth = await checkAuth(page);
    if (!auth.authenticated) throw new Error(`TradingView session is not authenticated: ${auth.url}`);

    await openPineEditor(page);
    const editor = await setPineEditorText(page, source);
    await savePineScript(page, scriptName);
    await addPineToChart(page);
    const compile = await detectCompileStatus(page);
    const closeEditor = await closePineEditor(page).catch((error) => ({ status: 'failed', error: String(error.message || error) }));
    await page.waitForTimeout(1500);

    await page.mouse.click(Number(args.x || 86), Number(args.y || 102));
    await page.waitForTimeout(1200);

    const screenshot = path.join(outDir, 'dropdown.png');
    await saveScreenshot(page, screenshot);
    const bodyTextPath = path.join(outDir, 'body.txt');
    fs.writeFileSync(bodyTextPath, await page.locator('body').innerText({ timeout: 10000 }).catch(() => ''));
    const controls = (await visibleControls(page)).map((item) => ({
      ...item,
      text: compact(item.text).slice(0, 220),
    }));
    const report = {
      status: compile.status === 'failed' ? 'failed' : 'ok',
      command: 'tv-install-inspect-indicator-dropdown',
      runId: loaded.runId,
      outDir,
      scriptPath,
      scriptName,
      auth,
      editor,
      compile,
      closeEditor,
      screenshot,
      bodyTextPath,
      controls,
    };
    writeReport(path.join(outDir, 'install-inspect-dropdown-report.json'), report);
    console.log(JSON.stringify(report, null, 2));
    if (report.status !== 'ok') process.exitCode = 1;
  } catch (error) {
    const report = {
      status: 'failed',
      command: 'tv-install-inspect-indicator-dropdown',
      runId: loaded.runId,
      outDir,
      error: String(error.stack || error),
    };
    writeReport(path.join(outDir, 'install-inspect-dropdown-report.json'), report);
    console.log(JSON.stringify(report, null, 2));
    process.exitCode = 1;
  } finally {
    await context?.close().catch(() => {});
  }
}

await main();
