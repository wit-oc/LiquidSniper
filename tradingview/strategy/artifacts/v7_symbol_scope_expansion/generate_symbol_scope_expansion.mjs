#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const args = Object.fromEntries(process.argv.slice(2).map((arg, index, all) => {
  if (!arg.startsWith('--')) return [];
  const key = arg.slice(2);
  const next = all[index + 1];
  return [key, next && !next.startsWith('--') ? next : true];
}).filter((pair) => pair.length));

const repoRoot = path.resolve(args.cwd || process.cwd());
const artifactRoot = path.join(repoRoot, 'tradingview/strategy/artifacts/v7_symbol_scope_expansion');
const generatedDir = path.join(artifactRoot, 'generated');
const sourcePinePath = path.join(repoRoot, 'tradingview/strategy/artifacts/v7_fixed_percent_stop_sidebar/generated/v7-fixed-stop-structural-control-125bps.pine');
const sourceManifestPath = path.join(repoRoot, 'tradingview/strategy/artifacts/v7_fixed_percent_stop_sidebar/tv_fixed_percent_stop_runs.json');
const outputPinePath = path.join(generatedDir, 'v7-symbol-scope-expansion-125bps.pine');
const outputManifestPath = path.join(artifactRoot, 'tv_symbol_scope_expansion_runs.json');

const runId = 'v7-symbol-scope-expansion-125bps';
const scriptTitle = 'Unity UTM Strategy v7 Symbol Scope Expansion 125bps';
const symbols = [
  'BINANCE:BTCUSDT',
  'BINANCE:ETHUSDT',
  'BINANCE:ZECUSDT',
  'BINANCE:SOLUSDT',
  'BINANCE:BNBUSDT',
  'BINANCE:XRPUSDT',
  'BINANCE:DOGEUSDT',
  'BINANCE:LTCUSDT',
  'BINANCE:ADAUSDT',
  'BINANCE:LINKUSDT',
];

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

function writeJson(file, value) {
  fs.writeFileSync(file, `${JSON.stringify(value, null, 2)}\n`);
}

if (!fs.existsSync(sourcePinePath)) {
  throw new Error(`Missing source Pine: ${sourcePinePath}`);
}
if (!fs.existsSync(sourceManifestPath)) {
  throw new Error(`Missing source manifest: ${sourceManifestPath}`);
}

ensureDir(generatedDir);

const sourcePine = fs.readFileSync(sourcePinePath, 'utf8');
let generatedPine = sourcePine.replace(
  '"Unity UTM Strategy v7 Fixed Percent Stop Sidebar Structural Control 125bps"',
  `"${scriptTitle}"`,
);
if (generatedPine === sourcePine) {
  throw new Error('Did not replace the Pine strategy title.');
}
generatedPine = generatedPine.replace(
  '"unity-utm-v7-fixed-percent-stop-sidebar-structural-control-125bps"',
  '"unity-utm-v7-symbol-scope-expansion-125bps"',
);
fs.writeFileSync(outputPinePath, generatedPine);

const sourceManifest = readJson(sourceManifestPath);
const sourceRun = sourceManifest.runs.find((run) => run.id === 'v7-fixed-stop-structural-control-125bps');
if (!sourceRun) {
  throw new Error('Missing source 125bps run in fixed-percent sidebar manifest.');
}

const manifest = {
  version: 1,
  defaultRun: runId,
  defaults: {
    ...sourceManifest.defaults,
    artifactsDir: 'tradingview/strategy/artifacts/v7_symbol_scope_expansion/tradingview/automation',
  },
  runs: [
    {
      ...sourceRun,
      id: runId,
      description: 'Fixed V7 System A Displacement Quality 125bps structural stop candidate across original and expansion symbols. Classification-only symbol admission pass.',
      variant: 'symbol_scope_expansion_125bps',
      geometry: 'Symbol Scope Expansion 125bps',
      scriptPath: 'tradingview/strategy/artifacts/v7_symbol_scope_expansion/generated/v7-symbol-scope-expansion-125bps.pine',
      scriptName: `Codex Scratch - ${runId}`,
      scriptTitle,
      expectedStrategyTitle: scriptTitle,
      symbols,
      validation: {
        ...sourceRun.validation,
        minCsvFiles: symbols.length * sourceRun.timeframes.length,
      },
    },
  ],
};

writeJson(outputManifestPath, manifest);

console.log(JSON.stringify({
  artifactRoot,
  outputPinePath,
  outputManifestPath,
  runId,
  symbols: symbols.length,
  slots: symbols.length * sourceRun.timeframes.length,
}, null, 2));
