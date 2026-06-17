#!/usr/bin/env node
import path from 'node:path';
import readline from 'node:readline/promises';
import { stdin as input, stdout as output } from 'node:process';
import { commandArtifactDir, loadConfig, parseArgs, writeReport } from './lib/config.mjs';
import { launchTradingView } from './lib/browser.mjs';
import { checkAuth, gotoChart, saveScreenshot } from './lib/actions.mjs';

const args = parseArgs();
const loaded = loadConfig(args);
const outDir = commandArtifactDir(loaded.artifactsDir, loaded.runId, 'login');
let context;

try {
  const browser = await launchTradingView({ defaults: loaded.defaults, artifactsDir: outDir });
  context = browser.context;
  const page = browser.page;
  const symbol = loaded.run.symbols?.[0] || loaded.run.symbol || 'BINANCE:BTCUSDT';
  const interval = loaded.run.timeframes?.[0]?.interval || loaded.run.interval || '15';
  const url = await gotoChart(page, loaded.run, symbol, interval);

  console.log('\nTradingView Chrome profile is open.');
  console.log('1. Log into TradingView in the opened browser if needed.');
  console.log('2. Open/save the intended chart layout.');
  console.log('3. Map any private/vendor input.source() settings manually.');
  console.log('4. Return here and press Enter. Do not close Chrome yourself.\n');

  const rl = readline.createInterface({ input, output });
  await rl.question('Press Enter after TradingView is logged in and the layout is saved...');
  rl.close();

  const auth = await checkAuth(page);
  const storageStatePath = path.join(outDir, 'storage-state.json');
  await context.storageState({ path: storageStatePath }).catch(() => {});
  const screenshot = path.join(outDir, 'login.png');
  await saveScreenshot(page, screenshot);
  const report = {
    status: auth.authenticated ? 'ok' : 'auth_required',
    command: 'tv-login',
    runId: loaded.runId,
    url,
    auth,
    storageStatePath,
    screenshot,
    note: 'The browser was closed by Playwright to flush the persistent Chrome profile. Use tv-doctor next.',
  };
  writeReport(path.join(outDir, 'login-report.json'), report);
  console.log(JSON.stringify(report, null, 2));
  if (!auth.authenticated) process.exitCode = 1;
} catch (error) {
  const report = { status: 'failed', command: 'tv-login', runId: loaded.runId, error: String(error.stack || error) };
  writeReport(path.join(outDir, 'login-report.json'), report);
  console.log(JSON.stringify(report, null, 2));
  process.exitCode = 1;
} finally {
  await context?.close().catch(() => {});
}
