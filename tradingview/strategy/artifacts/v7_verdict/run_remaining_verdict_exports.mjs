#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';

const repoRoot = path.resolve(process.argv.includes('--cwd') ? process.argv[process.argv.indexOf('--cwd') + 1] : process.cwd());
const logDir = path.join(repoRoot, 'tradingview/strategy/artifacts/v7_verdict/export_logs');
const config = 'tradingview/strategy/artifacts/v7_verdict/tv_verdict_harness_runs.json';
const allRuns = [
  'v7-verdict-a-current-sweep',
  'v7-verdict-a-current-mss-swing',
  'v7-verdict-a-current-retest-poi',
  'v7-verdict-b-alert-score-sweep',
  'v7-verdict-b-alert-score-mss-swing',
  'v7-verdict-b-alert-score-retest-poi',
  'v7-verdict-b-alert-required-sweep',
  'v7-verdict-b-alert-required-mss-swing',
  'v7-verdict-b-alert-required-retest-poi',
];

const onlyRunsArg = process.argv.includes('--runs') ? process.argv[process.argv.indexOf('--runs') + 1] : '';
const startAfterArg = process.argv.includes('--start-after') ? process.argv[process.argv.indexOf('--start-after') + 1] : '';
const onlySymbolArg = process.argv.includes('--only-symbol') ? process.argv[process.argv.indexOf('--only-symbol') + 1] : '';
const continueOnFailure = process.argv.includes('--continue-on-failure');
let runs = onlyRunsArg ? onlyRunsArg.split(',').map((item) => item.trim()).filter(Boolean) : allRuns;
if (startAfterArg) {
  const startAfterIndex = runs.indexOf(startAfterArg);
  if (startAfterIndex === -1) {
    throw new Error(`Unknown --start-after run: ${startAfterArg}`);
  }
  runs = runs.slice(startAfterIndex + 1);
}

for (const runId of runs) {
  if (!allRuns.includes(runId)) {
    throw new Error(`Unknown run id: ${runId}`);
  }
}

fs.mkdirSync(logDir, { recursive: true });

function runOne(runId) {
  return new Promise((resolve) => {
    const startedAt = new Date();
    const childArgs = [
      'tradingview/scripts/tv_pine_text_matrix.mjs',
      '--cwd', repoRoot,
      '--config', config,
      '--run', runId,
    ];
    if (onlySymbolArg) {
      childArgs.push('--only-symbol', onlySymbolArg);
    }
    const child = spawn(process.execPath, childArgs, {
      cwd: repoRoot,
      env: process.env,
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    let stdout = '';
    let stderr = '';
    child.stdout.on('data', (chunk) => { stdout += chunk; });
    child.stderr.on('data', (chunk) => { stderr += chunk; });
    child.on('close', (code) => {
      const finishedAt = new Date();
      const stdoutPath = path.join(logDir, `${runId}.stdout.json`);
      const stderrPath = path.join(logDir, `${runId}.stderr.txt`);
      fs.writeFileSync(stdoutPath, stdout);
      fs.writeFileSync(stderrPath, stderr);
      let status = 'unknown';
      let ok = 0;
      let failed = 0;
      let outDir = null;
      try {
        const report = JSON.parse(stdout);
        status = report.status;
        outDir = report.outDir;
        ok = (report.results || []).filter((item) => item.status === 'ok').length;
        failed = (report.results || []).filter((item) => item.status !== 'ok').length;
      } catch {
        status = code === 0 ? 'unparsed-ok' : 'unparsed-failed';
      }
      resolve({ runId, code, status, ok, failed, outDir, stdoutPath, stderrPath, startedAt, finishedAt });
    });
  });
}

for (const runId of runs) {
  console.log(`[${new Date().toISOString()}] start ${runId}`);
  const result = await runOne(runId);
  const seconds = Math.round((result.finishedAt - result.startedAt) / 1000);
  console.log(`[${new Date().toISOString()}] done ${runId} code=${result.code} status=${result.status} ok=${result.ok} failed=${result.failed} seconds=${seconds}`);
  if (result.outDir) console.log(`  outDir=${result.outDir}`);
  console.log(`  stdout=${result.stdoutPath}`);
  console.log(`  stderr=${result.stderrPath}`);
  if (!continueOnFailure && (result.code !== 0 || result.status !== 'ok' || result.failed > 0)) {
    process.exitCode = result.code || 1;
    break;
  }
  if (continueOnFailure && (result.code !== 0 || result.status !== 'ok' || result.failed > 0)) {
    process.exitCode = result.code || 1;
  }
}
