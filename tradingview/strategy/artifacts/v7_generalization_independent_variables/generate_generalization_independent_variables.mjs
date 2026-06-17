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
const strategyRoot = path.join(repoRoot, 'tradingview/strategy');
const artifactRoot = path.join(strategyRoot, 'artifacts/v7_generalization_independent_variables');
const generatedDir = path.join(artifactRoot, 'generated');
const sourcePinePath = path.join(strategyRoot, 'artifacts/v7_fixed_percent_stop_sidebar/generated/v7-fixed-stop-structural-control-125bps.pine');
const sourceManifestPath = path.join(strategyRoot, 'artifacts/v7_fixed_percent_stop_sidebar/tv_fixed_percent_stop_runs.json');
const outputManifestPath = path.join(artifactRoot, 'tv_generalization_independent_variables_runs.json');

const sourceRunId = 'v7-fixed-stop-structural-control-125bps';
const baseTitle = 'Unity UTM Strategy v7 Generalization IV';
const sourceTitle = 'Unity UTM Strategy v7 Fixed Percent Stop Sidebar Structural Control 125bps';
const sourceLogic = 'unity-utm-v7-fixed-percent-stop-sidebar-structural-control-125bps';

const mappings = [
  { label: 'REQ AIO Internal Bullish MSS', value: 'The Oracle AIO - [Unity] - V2: Internal Bullish MSS' },
  { label: 'REQ AIO Internal Bearish MSS', value: 'The Oracle AIO - [Unity] - V2: Internal Bearish MSS' },
  { label: 'DIAG AIO Buy Trend Alert', value: 'The Oracle AIO - [Unity] - V2: Buy Trend Alert' },
  { label: 'DIAG AIO Sell Trend Alert', value: 'The Oracle AIO - [Unity] - V2: Sell Trend Alert' },
  { label: 'REQ Oracle Strength', value: 'The Oracle Strength - [Unity] - V2: Oracle Strength' },
  { label: 'Optional AIO Internal Bullish BOS', value: 'The Oracle AIO - [Unity] - V2: Internal Bullish BOS' },
  { label: 'Optional AIO Internal Bearish BOS', value: 'The Oracle AIO - [Unity] - V2: Internal Bearish BOS' },
  { label: 'DIAG Phase1 Bus Regime Direction', value: 'HTF Phase 1 Structure v3.3 (structure-first): Bus Regime Direction' },
  { label: 'DIAG Phase1 Bus CHoCH Direction', value: 'HTF Phase 1 Structure v3.3 (structure-first): Bus CHoCH Direction' },
  { label: 'DIAG Phase1 Bus BoS Direction', value: 'HTF Phase 1 Structure v3.3 (structure-first): Bus BoS Direction' },
];

const symbols = [
  'BINANCE:ZECUSDT',
  'BINANCE:ADAUSDT',
  'BINANCE:LINKUSDT',
  'BINANCE:XRPUSDT',
  'BINANCE:ARBUSDT',
  'BINANCE:PYTHUSDT',
  'BINANCE:SEIUSDT',
  'BINANCE:BTCUSDT',
  'BINANCE:ETHUSDT',
  'BINANCE:SOLUSDT',
  'BINANCE:BNBUSDT',
  'BINANCE:DOGEUSDT',
  'BINANCE:LTCUSDT',
  'BINANCE:HYPEUSDT.P',
  'BINANCE:AEROUSDT.P',
  'BINANCE:RENDERUSDT.P',
];

const symbolMetadata = {
  'BINANCE:ZECUSDT': { asset: 'ZEC', regimeTier: 'prior admitted control', liquidityTier: 'mid', priorOutcome: 'pass' },
  'BINANCE:ADAUSDT': { asset: 'ADA', regimeTier: 'prior admitted control', liquidityTier: 'mid', priorOutcome: 'pass' },
  'BINANCE:LINKUSDT': { asset: 'LINK', regimeTier: 'prior admitted control', liquidityTier: 'mid', priorOutcome: 'pass' },
  'BINANCE:XRPUSDT': { asset: 'XRP', regimeTier: 'prior admitted control', liquidityTier: 'major', priorOutcome: 'pass' },
  'BINANCE:ARBUSDT': { asset: 'ARB', regimeTier: 'prior admitted control', liquidityTier: 'smaller/reflexive', priorOutcome: 'pass' },
  'BINANCE:PYTHUSDT': { asset: 'PYTH', regimeTier: 'prior admitted control', liquidityTier: 'smaller/reflexive', priorOutcome: 'pass' },
  'BINANCE:SEIUSDT': { asset: 'SEI', regimeTier: 'prior admitted control', liquidityTier: 'smaller/reflexive', priorOutcome: 'pass' },
  'BINANCE:BTCUSDT': { asset: 'BTC', regimeTier: 'prior failed control', liquidityTier: 'major', priorOutcome: 'fail' },
  'BINANCE:ETHUSDT': { asset: 'ETH', regimeTier: 'major control', liquidityTier: 'major', priorOutcome: 'diagnostic-only' },
  'BINANCE:SOLUSDT': { asset: 'SOL', regimeTier: 'prior failed control', liquidityTier: 'major', priorOutcome: 'fail' },
  'BINANCE:BNBUSDT': { asset: 'BNB', regimeTier: 'prior failed control', liquidityTier: 'major', priorOutcome: 'fail' },
  'BINANCE:DOGEUSDT': { asset: 'DOGE', regimeTier: 'prior failed control', liquidityTier: 'major', priorOutcome: 'fail' },
  'BINANCE:LTCUSDT': { asset: 'LTC', regimeTier: 'major control', liquidityTier: 'major', priorOutcome: 'marginal' },
  'BINANCE:HYPEUSDT.P': { asset: 'HYPE', regimeTier: 'perp route probe', liquidityTier: 'smaller/reflexive', priorOutcome: 'spot-route-unresolved' },
  'BINANCE:AEROUSDT.P': { asset: 'AERO', regimeTier: 'perp route probe', liquidityTier: 'smaller/reflexive', priorOutcome: 'spot-route-unresolved' },
  'BINANCE:RENDERUSDT.P': { asset: 'RENDER', regimeTier: 'perp route probe', liquidityTier: 'smaller/reflexive', priorOutcome: 'spot-route-fail', aliasGroup: 'RENDER/RNDR' },
};

const variants = [
  {
    id: 'baseline-125bps',
    variant: 'baseline_125bps',
    title: 'Baseline 125bps',
    description: 'Protected current candidate: System A Displacement Quality with 125bps hard structural stop floor.',
    patch(source) {
      return source;
    },
  },
  {
    id: 'quality-score-3',
    variant: 'trade_quality_score_3',
    title: 'Quality Score 3',
    description: 'Independent trade-quality filter: raise Minimum Quality Score To Trade from 2 to 3.',
    patch(source) {
      return patchIntInputDefault(source, 'Minimum Quality Score To Trade', 3);
    },
  },
  {
    id: 'atr-regime-filter',
    variant: 'atr_regime_filter',
    title: 'ATR Regime Filter',
    description: 'Independent volatility/risk adaptation: add the existing ATR regime damp/veto to Displacement Quality.',
    patch(source) {
      return patchStringInputDefault(source, 'Profitability Risk Test Profile', 'Displacement ATR Regime');
    },
  },
  {
    id: 'close-confirmed-stop',
    variant: 'close_confirmed_stop',
    title: 'Close Confirmed Stop',
    description: 'Independent stop/exit test: require close-confirmed invalidation instead of hard intrabar stop.',
    patch(source) {
      let patched = patchStringInputDefault(source, 'Stop Exit Mode', 'Close Confirmed');
      patched = patchStringInputDefault(patched, 'Stop Engine Label', 'Sweep Close Confirmed');
      return patched;
    },
  },
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

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function patchStringInputDefault(source, inputLabel, value) {
  const pattern = new RegExp(`input\\.string\\("[^"]+", "${escapeRegExp(inputLabel)}"`);
  if (!pattern.test(source)) throw new Error(`Unable to patch string input: ${inputLabel}`);
  return source.replace(pattern, `input.string("${value}", "${inputLabel}"`);
}

function patchIntInputDefault(source, inputLabel, value) {
  const pattern = new RegExp(`input\\.int\\(-?\\d+, "${escapeRegExp(inputLabel)}"`);
  if (!pattern.test(source)) throw new Error(`Unable to patch int input: ${inputLabel}`);
  return source.replace(pattern, `input.int(${Number(value)}, "${inputLabel}"`);
}

function patchRunIdentity(source, variant) {
  const runId = `v7-generalization-${variant.id}`;
  const title = `${baseTitle} ${variant.title}`;
  const logic = `unity-utm-v7-generalization-${variant.id}`;
  let patched = source.replace(`"${sourceTitle}"`, `"${title}"`);
  if (patched === source) throw new Error(`Did not replace strategy title for ${variant.id}`);
  patched = patched.replace(`"${sourceLogic}"`, `"${logic}"`);
  if (!patched.includes(`"${logic}"`)) throw new Error(`Did not replace logic version for ${variant.id}`);
  return { runId, title, logic, source: variant.patch(patched) };
}

if (!fs.existsSync(sourcePinePath)) throw new Error(`Missing source Pine: ${sourcePinePath}`);
if (!fs.existsSync(sourceManifestPath)) throw new Error(`Missing source manifest: ${sourceManifestPath}`);

ensureDir(generatedDir);

const sourcePine = fs.readFileSync(sourcePinePath, 'utf8');
const sourceManifest = readJson(sourceManifestPath);
const sourceRun = sourceManifest.runs.find((run) => run.id === sourceRunId);
if (!sourceRun) throw new Error(`Missing source run ${sourceRunId}`);

const runs = variants.map((variant) => {
  const identity = patchRunIdentity(sourcePine, variant);
  const scriptPath = path.join(generatedDir, `${identity.runId}.pine`);
  fs.writeFileSync(scriptPath, identity.source);
  return {
    ...sourceRun,
    id: identity.runId,
    description: `${variant.description} Generalization matrix across admitted candidates, failed/major controls, and Binance .P route probes.`,
    variant: variant.variant,
    geometry: variant.title,
    scriptPath: path.relative(repoRoot, scriptPath),
    scriptName: `Codex Scratch - ${identity.runId}`,
    scriptTitle: identity.title,
    expectedStrategyTitle: identity.title,
    strategyReportDateRange: 'Entire history',
    chartUrl: 'https://www.tradingview.com/chart/EU0fwd29/?symbol=BINANCE:BTCUSDT&interval=15',
    v6Mappings: mappings,
    symbols,
    symbolMetadata,
    timeframes: [
      { label: '15m', interval: '15' },
      { label: '5m', interval: '5' },
    ],
    validation: {
      ...sourceRun.validation,
      minCsvFiles: symbols.length * 2,
    },
  };
});

const manifest = {
  version: 1,
  defaultRun: runs[0].id,
  defaults: {
    ...sourceManifest.defaults,
    artifactsDir: 'tradingview/strategy/artifacts/v7_generalization_independent_variables/tradingview/automation',
  },
  runs,
};

writeJson(outputManifestPath, manifest);

console.log(JSON.stringify({
  artifactRoot,
  sourcePinePath,
  outputManifestPath,
  variants: runs.map((run) => run.id),
  symbols: symbols.length,
  slotsPerRun: symbols.length * 2,
  totalSlots: symbols.length * 2 * runs.length,
}, null, 2));
