#!/usr/bin/env node
import path from 'node:path';
import {
  commandArtifactDir,
  loadConfig,
  matrixItems,
  parseArgs,
  safeName,
  writeReport,
} from './lib/config.mjs';
import { launchTradingView } from './lib/browser.mjs';
import {
  checkAuth,
  exportChartData,
  exportStrategyData,
  gotoChart,
  saveScreenshot,
} from './lib/actions.mjs';

const args = parseArgs();
const loaded = loadConfig(args);
const outDir = commandArtifactDir(loaded.artifactsDir, loaded.runId, 'matrix');
let context;

try {
  const browser = await launchTradingView({ defaults: loaded.defaults, artifactsDir: outDir });
  context = browser.context;
  const page = browser.page;
  const timeoutMs = Number(args.downloadTimeoutMs || loaded.defaults.downloadTimeoutMs || 120000);
  const results = [];

  for (const item of matrixItems(loaded.run)) {
    const itemDir = path.join(outDir, safeName(item.symbol), safeName(item.label));
    const result = { ...item, status: 'unknown', exports: [] };
    try {
      result.url = await gotoChart(page, loaded.run, item.symbol, item.interval);
      const auth = await checkAuth(page);
      if (!auth.authenticated) throw new Error(`TradingView session is not authenticated: ${auth.url}`);
      await page.waitForTimeout(Number(loaded.run.waitAfterLoadMs || loaded.defaults.waitAfterLoadMs || 8000));
      if (loaded.run.kind === 'strategy') {
        const strategyCsv = await exportStrategyData(page, itemDir, item, timeoutMs, loaded.run);
        result.exports.push({ kind: 'strategy', path: strategyCsv });
      }
      if (loaded.run.exportChartData !== false) {
        const chartCsv = await exportChartData(page, itemDir, item, timeoutMs);
        result.exports.push({ kind: 'chart', path: chartCsv });
      }
      result.status = 'ok';
    } catch (error) {
      result.status = 'failed';
      result.error = String(error.stack || error);
      result.screenshot = path.join(itemDir, 'failure.png');
      await saveScreenshot(page, result.screenshot);
      result.textSnapshot = path.join(itemDir, 'failure-text.txt');
      const text = await page.locator('body').innerText({ timeout: 5000 }).catch((textError) => `failed to read body text: ${textError}`);
      await import('node:fs').then((fs) => {
        fs.writeFileSync(result.textSnapshot, text);
      });
    }
    results.push(result);
  }

  const report = {
    status: results.every((result) => result.status === 'ok') ? 'ok' : 'failed',
    command: 'tv-run-matrix',
    runId: loaded.runId,
    outDir,
    results,
  };
  writeReport(path.join(outDir, 'matrix-report.json'), report);
  console.log(JSON.stringify(report, null, 2));
  if (report.status === 'failed') process.exitCode = 1;
} catch (error) {
  const report = { status: 'failed', command: 'tv-run-matrix', runId: loaded.runId, error: String(error.stack || error) };
  writeReport(path.join(outDir, 'matrix-report.json'), report);
  console.log(JSON.stringify(report, null, 2));
  process.exitCode = 1;
} finally {
  await context?.close().catch(() => {});
}
