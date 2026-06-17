#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { commandArtifactDir, loadConfig, parseArgs, resolveFromRoot, safeName, writeReport } from './lib/config.mjs';
import { launchTradingView } from './lib/browser.mjs';
import {
  addPineToChart,
  checkAuth,
  closePineEditor,
  detectCompileStatus,
  gotoChart,
  openPineEditor,
  savePineScript,
  saveChartLayout,
  saveScreenshot,
  setPineEditorText,
} from './lib/actions.mjs';

const args = parseArgs();
const loaded = loadConfig(args);
const outDir = commandArtifactDir(loaded.artifactsDir, loaded.runId, 'install');
let context;

try {
  const scriptPath = resolveFromRoot(loaded.root, args.script || loaded.run.scriptPath);
  const source = fs.readFileSync(scriptPath, 'utf8');
  const scriptName = args.name || loaded.run.scriptName || `${loaded.defaults.scriptNamePrefix || 'Codex Scratch'} - ${path.basename(scriptPath, '.pine')}`;
  const browser = await launchTradingView({ defaults: loaded.defaults, artifactsDir: outDir });
  context = browser.context;
  const page = browser.page;
  const item = {
    symbol: loaded.run.symbols?.[0] || loaded.run.symbol || 'BINANCE:BTCUSDT',
    interval: loaded.run.timeframes?.[0]?.interval || loaded.run.interval || '15',
  };
  const url = await gotoChart(page, loaded.run, item.symbol, item.interval);
  const auth = await checkAuth(page);
  if (!auth.authenticated) throw new Error(`TradingView session is not authenticated: ${auth.url}`);
  await openPineEditor(page);
  const editor = await setPineEditorText(page, source);
  await savePineScript(page, scriptName);
  await addPineToChart(page);
  const compile = await detectCompileStatus(page);
  let layoutSave = { status: 'skipped' };
  if (compile.status !== 'failed' && loaded.run.saveLayoutAfterInstall !== false) {
    const closeEditor = await closePineEditor(page).catch((error) => ({ status: 'failed', error: String(error.message || error) }));
    layoutSave = await saveChartLayout(page)
      .then((result) => ({ ...result, closeEditor }))
      .catch((error) => ({ status: 'failed', closeEditor, error: String(error.message || error) }));
  }
  const screenshot = path.join(outDir, 'install.png');
  await saveScreenshot(page, screenshot);
  const report = {
    status: compile.status === 'failed' ? 'failed' : compile.status,
    command: 'tv-install-pine',
    runId: loaded.runId,
    kind: loaded.run.kind,
    scriptPath,
    scriptName,
    sourceBytes: Buffer.byteLength(source),
    url,
    auth,
    editor,
    compile,
    layoutSave,
    screenshot,
  };
  writeReport(path.join(outDir, 'install-report.json'), report);
  console.log(JSON.stringify(report, null, 2));
  if (report.status === 'failed') process.exitCode = 1;
} catch (error) {
  const report = { status: 'failed', command: 'tv-install-pine', runId: loaded.runId, error: String(error.stack || error) };
  writeReport(path.join(outDir, 'install-report.json'), report);
  console.log(JSON.stringify(report, null, 2));
  process.exitCode = 1;
} finally {
  await context?.close().catch(() => {});
}
