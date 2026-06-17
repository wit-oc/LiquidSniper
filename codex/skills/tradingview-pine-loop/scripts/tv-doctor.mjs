#!/usr/bin/env node
import path from 'node:path';
import { commandArtifactDir, loadConfig, parseArgs, writeReport } from './lib/config.mjs';
import { launchTradingView } from './lib/browser.mjs';
import {
  checkAuth,
  gotoChart,
  openBottomTab,
  openPineEditor,
  probeTradingViewSurfaces,
  saveScreenshot,
} from './lib/actions.mjs';

const args = parseArgs();
const loaded = loadConfig(args);
const outDir = commandArtifactDir(loaded.artifactsDir, loaded.runId, 'doctor');
let context;

try {
  const browser = await launchTradingView({ defaults: loaded.defaults, artifactsDir: outDir });
  context = browser.context;
  const page = browser.page;
  const url = await gotoChart(page, loaded.run, loaded.run.symbols?.[0] || loaded.run.symbol || 'BINANCE:BTCUSDT', loaded.run.timeframes?.[0]?.interval || loaded.run.interval || '15');
  const auth = await checkAuth(page);
  const surfacesBefore = await probeTradingViewSurfaces(page);
  const probes = {
    pineEditorOpenAttempt: 'not_attempted',
    strategyTesterOpenAttempt: 'not_attempted',
  };
  try {
    await openPineEditor(page);
    probes.pineEditorOpenAttempt = 'ok';
  } catch (error) {
    probes.pineEditorOpenAttempt = `failed:${error.message}`;
  }
  try {
    await openBottomTab(page, ['Strategy Tester', 'Tester']);
    probes.strategyTesterOpenAttempt = 'ok';
  } catch (error) {
    probes.strategyTesterOpenAttempt = `failed:${error.message}`;
  }
  const surfacesAfter = await probeTradingViewSurfaces(page);
  const screenshot = path.join(outDir, 'doctor.png');
  await saveScreenshot(page, screenshot);
  const warnings = [];
  if (!surfacesAfter.pineEditorTextPresent) warnings.push('Pine Editor text was not visible after probe; bottom panel may be hidden or TradingView UI changed.');
  if (!surfacesAfter.strategyTesterTextPresent) warnings.push('Strategy Tester text was not visible after probe; this can be normal before a strategy is added.');
  if (!surfacesAfter.exportTextPresent) warnings.push('Export controls were not visible from the default chart state.');
  const report = {
    status: auth.authenticated && (surfacesBefore.chartLoaded || surfacesAfter.chartLoaded) ? 'ok' : 'degraded',
    command: 'tv-doctor',
    runId: loaded.runId,
    url,
    auth,
    surfacesBefore,
    surfacesAfter,
    probes,
    warnings,
    screenshot,
  };
  writeReport(path.join(outDir, 'doctor-report.json'), report);
  console.log(JSON.stringify(report, null, 2));
} catch (error) {
  const report = { status: 'failed', command: 'tv-doctor', runId: loaded.runId, error: String(error.stack || error) };
  writeReport(path.join(outDir, 'doctor-report.json'), report);
  console.log(JSON.stringify(report, null, 2));
  process.exitCode = 1;
} finally {
  await context?.close().catch(() => {});
}
