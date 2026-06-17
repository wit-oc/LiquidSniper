#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const args = Object.fromEntries(process.argv.slice(2).map((arg, index, all) => {
  if (!arg.startsWith('--')) return [];
  const key = arg.slice(2);
  const next = all[index + 1];
  return [key, next && !next.startsWith('--') ? next : true];
}).filter((pair) => pair.length));

const repoRoot = path.resolve(args.cwd || process.cwd());
const manifestPath = path.resolve(repoRoot, args.manifest || 'tradingview/strategy/artifacts/v7_generalization_independent_variables/tv_generalization_independent_variables_runs.json');
const automationDir = path.resolve(repoRoot, args.automationDir || 'tradingview/strategy/artifacts/v7_generalization_independent_variables/tradingview/automation');
const outputRoot = path.resolve(repoRoot, args.output || 'tradingview/strategy/artifacts/v7_generalization_independent_variables');
const telemetryRoot = path.resolve(repoRoot, args.telemetryRoot || 'tradingview/strategy/.telemetry/outputs/v7_generalization_independent_variables');
const analyzerPath = path.resolve(repoRoot, 'tradingview/strategy/artifacts/v7_liquidity_scope_sanity/analyze_liquidity_scope_sanity.mjs');
const comparePath = path.resolve(repoRoot, 'tradingview/strategy/artifacts/v7_generalization_independent_variables/compare_generalization_independent_variables.mjs');

function runNode(script, scriptArgs) {
  const result = spawnSync(process.execPath, [script, ...scriptArgs], {
    cwd: repoRoot,
    stdio: 'inherit',
  });
  if (result.status !== 0) {
    throw new Error(`${path.relative(repoRoot, script)} failed with exit code ${result.status}`);
  }
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

if (!fs.existsSync(manifestPath)) throw new Error(`Missing manifest: ${manifestPath}`);
if (!fs.existsSync(analyzerPath)) throw new Error(`Missing analyzer: ${analyzerPath}`);

const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
const selectedRuns = args.run && args.run !== 'all'
  ? manifest.runs.filter((run) => run.id === args.run)
  : manifest.runs;

if (!selectedRuns.length) {
  throw new Error(`No runs selected from ${manifestPath}`);
}

for (const run of selectedRuns) {
  const runOutput = path.join(outputRoot, 'metrics', run.id);
  const runTelemetry = path.join(telemetryRoot, run.id);
  ensureDir(runOutput);
  ensureDir(runTelemetry);
  runNode(analyzerPath, [
    '--cwd', repoRoot,
    '--manifest', path.relative(repoRoot, manifestPath),
    '--automationDir', path.relative(repoRoot, automationDir),
    '--output', path.relative(repoRoot, runOutput),
    '--telemetryDir', path.relative(repoRoot, runTelemetry),
    '--run', run.id,
  ]);
}

runNode(comparePath, [
  '--cwd', repoRoot,
  '--manifest', path.relative(repoRoot, manifestPath),
  '--telemetryRoot', path.relative(repoRoot, telemetryRoot),
  '--output', path.relative(repoRoot, outputRoot),
]);
