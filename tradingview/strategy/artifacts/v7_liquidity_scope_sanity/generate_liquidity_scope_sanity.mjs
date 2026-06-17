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
const artifactRoot = path.join(repoRoot, 'tradingview/strategy/artifacts/v7_liquidity_scope_sanity');
const generatedDir = path.join(artifactRoot, 'generated');
const sourcePinePath = path.join(repoRoot, 'tradingview/strategy/artifacts/v7_fixed_percent_stop_sidebar/generated/v7-fixed-stop-structural-control-125bps.pine');
const sourceManifestPath = path.join(repoRoot, 'tradingview/strategy/artifacts/v7_fixed_percent_stop_sidebar/tv_fixed_percent_stop_runs.json');
const outputPinePath = path.join(generatedDir, 'v7-liquidity-scope-sanity-125bps.pine');
const outputManifestPath = path.join(artifactRoot, 'tv_liquidity_scope_sanity_runs.json');

const runId = 'v7-liquidity-scope-sanity-125bps';
const scriptTitle = 'Unity UTM Strategy v7 Liquidity Scope Sanity 125bps';
const symbols = [
  'BINANCE:BTCUSDT',
  'BINANCE:ETHUSDT',
  'BINANCE:ZECUSDT',
  'BINANCE:ADAUSDT',
  'BINANCE:LINKUSDT',
  'BINANCE:XRPUSDT',
  'BINANCE:SOLUSDT',
  'BINANCE:BNBUSDT',
  'BINANCE:DOGEUSDT',
  'BINANCE:LTCUSDT',
  'BINANCE:HYPEUSDT',
  'BINANCE:AEROUSDT',
  'BINANCE:VIRTUALUSDT',
  'BINANCE:FETUSDT',
  'BINANCE:RENDERUSDT',
  'BINANCE:RNDRUSDT',
  'BINANCE:WIFUSDT',
  'BINANCE:SEIUSDT',
  'BINANCE:TIAUSDT',
  'BINANCE:SUIUSDT',
  'BINANCE:INJUSDT',
  'BINANCE:JUPUSDT',
  'BINANCE:ONDOUSDT',
  'BINANCE:ENAUSDT',
  'BINANCE:PYTHUSDT',
  'BINANCE:PENDLEUSDT',
  'BINANCE:ARBUSDT',
  'BINANCE:OPUSDT',
];
const symbolMetadata = {
  'BINANCE:BTCUSDT': { asset: 'BTC', regimeTier: 'prior failed control', liquidityTier: 'major', priorOutcome: 'fail' },
  'BINANCE:ETHUSDT': { asset: 'ETH', regimeTier: 'major control', liquidityTier: 'major', priorOutcome: 'diagnostic-only' },
  'BINANCE:ZECUSDT': { asset: 'ZEC', regimeTier: 'prior admitted control', liquidityTier: 'mid', priorOutcome: 'pass' },
  'BINANCE:ADAUSDT': { asset: 'ADA', regimeTier: 'prior admitted control', liquidityTier: 'mid', priorOutcome: 'pass' },
  'BINANCE:LINKUSDT': { asset: 'LINK', regimeTier: 'prior admitted control', liquidityTier: 'mid', priorOutcome: 'pass' },
  'BINANCE:XRPUSDT': { asset: 'XRP', regimeTier: 'prior admitted control', liquidityTier: 'major', priorOutcome: 'pass' },
  'BINANCE:SOLUSDT': { asset: 'SOL', regimeTier: 'prior failed control', liquidityTier: 'major', priorOutcome: 'fail' },
  'BINANCE:BNBUSDT': { asset: 'BNB', regimeTier: 'prior failed control', liquidityTier: 'major', priorOutcome: 'fail' },
  'BINANCE:DOGEUSDT': { asset: 'DOGE', regimeTier: 'prior failed control', liquidityTier: 'major', priorOutcome: 'fail' },
  'BINANCE:LTCUSDT': { asset: 'LTC', regimeTier: 'major control', liquidityTier: 'major', priorOutcome: 'marginal' },
  'BINANCE:HYPEUSDT': { asset: 'HYPE', regimeTier: 'smaller/reflexive', liquidityTier: 'smaller/reflexive', priorOutcome: 'new' },
  'BINANCE:AEROUSDT': { asset: 'AERO', regimeTier: 'smaller/reflexive', liquidityTier: 'smaller/reflexive', priorOutcome: 'new' },
  'BINANCE:VIRTUALUSDT': { asset: 'VIRTUAL', regimeTier: 'smaller/reflexive', liquidityTier: 'smaller/reflexive', priorOutcome: 'new' },
  'BINANCE:FETUSDT': { asset: 'FET', regimeTier: 'smaller/reflexive', liquidityTier: 'smaller/reflexive', priorOutcome: 'new' },
  'BINANCE:RENDERUSDT': { asset: 'RENDER', regimeTier: 'smaller/reflexive', liquidityTier: 'smaller/reflexive', priorOutcome: 'new', aliasGroup: 'RENDER/RNDR' },
  'BINANCE:RNDRUSDT': { asset: 'RNDR', regimeTier: 'smaller/reflexive', liquidityTier: 'smaller/reflexive', priorOutcome: 'new', aliasGroup: 'RENDER/RNDR' },
  'BINANCE:WIFUSDT': { asset: 'WIF', regimeTier: 'smaller/reflexive', liquidityTier: 'smaller/reflexive', priorOutcome: 'new' },
  'BINANCE:SEIUSDT': { asset: 'SEI', regimeTier: 'smaller/reflexive', liquidityTier: 'smaller/reflexive', priorOutcome: 'new' },
  'BINANCE:TIAUSDT': { asset: 'TIA', regimeTier: 'smaller/reflexive', liquidityTier: 'smaller/reflexive', priorOutcome: 'new' },
  'BINANCE:SUIUSDT': { asset: 'SUI', regimeTier: 'smaller/reflexive', liquidityTier: 'smaller/reflexive', priorOutcome: 'new' },
  'BINANCE:INJUSDT': { asset: 'INJ', regimeTier: 'smaller/reflexive', liquidityTier: 'smaller/reflexive', priorOutcome: 'new' },
  'BINANCE:JUPUSDT': { asset: 'JUP', regimeTier: 'smaller/reflexive', liquidityTier: 'smaller/reflexive', priorOutcome: 'new' },
  'BINANCE:ONDOUSDT': { asset: 'ONDO', regimeTier: 'smaller/reflexive', liquidityTier: 'smaller/reflexive', priorOutcome: 'new' },
  'BINANCE:ENAUSDT': { asset: 'ENA', regimeTier: 'smaller/reflexive', liquidityTier: 'smaller/reflexive', priorOutcome: 'new' },
  'BINANCE:PYTHUSDT': { asset: 'PYTH', regimeTier: 'smaller/reflexive', liquidityTier: 'smaller/reflexive', priorOutcome: 'new' },
  'BINANCE:PENDLEUSDT': { asset: 'PENDLE', regimeTier: 'smaller/reflexive', liquidityTier: 'smaller/reflexive', priorOutcome: 'new' },
  'BINANCE:ARBUSDT': { asset: 'ARB', regimeTier: 'smaller/reflexive', liquidityTier: 'smaller/reflexive', priorOutcome: 'new' },
  'BINANCE:OPUSDT': { asset: 'OP', regimeTier: 'smaller/reflexive', liquidityTier: 'smaller/reflexive', priorOutcome: 'new' },
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
  '"unity-utm-v7-liquidity-scope-sanity-125bps"',
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
    artifactsDir: 'tradingview/strategy/artifacts/v7_liquidity_scope_sanity/tradingview/automation',
  },
  runs: [
    {
      ...sourceRun,
      id: runId,
      description: 'Fixed V7 System A Displacement Quality 125bps structural stop candidate across controls and smaller/reflexive symbols. Classification-only liquidity-scope sanity pass.',
      variant: 'liquidity_scope_sanity_125bps',
      geometry: 'Liquidity Scope Sanity 125bps',
      scriptPath: 'tradingview/strategy/artifacts/v7_liquidity_scope_sanity/generated/v7-liquidity-scope-sanity-125bps.pine',
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
