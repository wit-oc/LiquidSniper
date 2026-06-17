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
const artifactRoot = path.join(repoRoot, 'tradingview/strategy/artifacts/v7_liquidity_scope_perp_probe');
const generatedDir = path.join(artifactRoot, 'generated');
const sourcePinePath = path.join(repoRoot, 'tradingview/strategy/artifacts/v7_fixed_percent_stop_sidebar/generated/v7-fixed-stop-structural-control-125bps.pine');
const sourceManifestPath = path.join(repoRoot, 'tradingview/strategy/artifacts/v7_fixed_percent_stop_sidebar/tv_fixed_percent_stop_runs.json');
const outputPinePath = path.join(generatedDir, 'v7-liquidity-scope-perp-probe-125bps.pine');
const outputManifestPath = path.join(artifactRoot, 'tv_liquidity_scope_perp_probe_runs.json');

const runId = 'v7-liquidity-scope-perp-probe-125bps';
const scriptTitle = 'Unity UTM Strategy v7 Liquidity Scope Perp Probe 125bps';
const symbols = [
  'BINANCE:HYPEUSDT.P',
  'BINANCE:AEROUSDT.P',
  'BINANCE:RENDERUSDT.P',
];
const symbolMetadata = {
  'BINANCE:HYPEUSDT.P': { asset: 'HYPE', regimeTier: 'smaller/reflexive perp probe', liquidityTier: 'smaller/reflexive', priorOutcome: 'spot-route-unresolved' },
  'BINANCE:AEROUSDT.P': { asset: 'AERO', regimeTier: 'smaller/reflexive perp probe', liquidityTier: 'smaller/reflexive', priorOutcome: 'spot-route-unresolved' },
  'BINANCE:RENDERUSDT.P': { asset: 'RENDER', regimeTier: 'smaller/reflexive perp probe', liquidityTier: 'smaller/reflexive', priorOutcome: 'spot-route-fail', aliasGroup: 'RENDER/RNDR' },
};

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
  '"unity-utm-v7-liquidity-scope-perp-probe-125bps"',
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
    artifactsDir: 'tradingview/strategy/artifacts/v7_liquidity_scope_perp_probe/tradingview/automation',
  },
  runs: [
    {
      ...sourceRun,
      id: runId,
      description: 'Fixed V7 System A Displacement Quality 125bps structural stop candidate on Binance USDT.P routes for HYPE, AERO, and RENDER. Targeted route sanity probe only.',
      variant: 'liquidity_scope_perp_probe_125bps',
      geometry: 'Liquidity Scope Perp Probe 125bps',
      scriptPath: 'tradingview/strategy/artifacts/v7_liquidity_scope_perp_probe/generated/v7-liquidity-scope-perp-probe-125bps.pine',
      scriptName: `Codex Scratch - ${runId}`,
      scriptTitle,
      expectedStrategyTitle: scriptTitle,
      symbols,
      symbolMetadata,
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
