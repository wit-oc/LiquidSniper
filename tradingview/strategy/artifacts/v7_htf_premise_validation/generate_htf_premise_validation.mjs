#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const args = Object.fromEntries(process.argv.slice(2).map((arg, index, all) => {
  if (!arg.startsWith('--')) return [];
  const key = arg.slice(2);
  const next = all[index + 1];
  return [key, next && !next.startsWith('--') ? next : true];
}).filter((pair) => pair.length));

const repoRoot = path.resolve(args.cwd || path.join(process.cwd(), '../..'));
const strategyRoot = path.join(repoRoot, 'tradingview/strategy');
const artifactRoot = path.join(strategyRoot, 'artifacts/v7_htf_premise_validation');
const generatedDir = path.join(artifactRoot, 'generated');
const sourcePinePath = path.join(strategyRoot, 'artifacts/v7_generalization_independent_variables/generated/v7-generalization-quality-score-3.pine');
const sourceManifestPath = path.join(strategyRoot, 'artifacts/v7_generalization_independent_variables/tv_generalization_independent_variables_runs.json');
const outputManifestPath = path.join(artifactRoot, 'tv_htf_premise_validation_runs.json');

const sourceRunId = 'v7-generalization-quality-score-3';
const sourceTitle = 'Unity UTM Strategy v7 Generalization IV Quality Score 3';
const sourceLogic = 'unity-utm-v7-generalization-quality-score-3';
const validationTitle = 'Unity UTM Strategy v7 HTF Premise QS3 Validation';
const validationLogic = 'unity-utm-v7-htf-premise-qs3-validation';

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
  'BINANCE:VIRTUALUSDT.P',
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
  'BINANCE:VIRTUALUSDT.P': { asset: 'VIRTUAL', regimeTier: 'perp route probe', liquidityTier: 'smaller/reflexive', priorOutcome: 'new' },
  'BINANCE:RENDERUSDT.P': { asset: 'RENDER', regimeTier: 'perp route probe', liquidityTier: 'smaller/reflexive', priorOutcome: 'spot-route-fail', aliasGroup: 'RENDER/RNDR' },
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

function patchRequired(source, from, to, label) {
  if (!source.includes(from)) throw new Error(`Unable to patch ${label}`);
  return source.replace(from, to);
}

function buildPine(source) {
  let patched = patchRequired(source, `"${sourceTitle}"`, `"${validationTitle}"`, 'strategy title');
  patched = patchRequired(patched, `"${sourceLogic}"`, `"${validationLogic}"`, 'logic version');
  patched = patchRequired(
    patched,
    'enable_backtest_window = input.bool(true, "Enable Backtest Window", group=g_time)',
    'enable_backtest_window = input.bool(false, "Enable Backtest Window", group=g_time)',
    'backtest window default',
  );
  if (!/min_quality_score\s*=\s*input\.int\(3,\s*"Minimum Quality Score To Trade"/.test(patched)) {
    throw new Error('Source Pine is not the QS3 candidate; minimum quality score is not 3.');
  }
  if (!/test_profile\s*=\s*input\.string\("Displacement Quality"/.test(patched)) {
    throw new Error('Source Pine is not the current Displacement Quality candidate.');
  }
  return patched;
}

if (!fs.existsSync(sourcePinePath)) throw new Error(`Missing QS3 generated source Pine: ${sourcePinePath}`);
if (!fs.existsSync(sourceManifestPath)) throw new Error(`Missing source manifest: ${sourceManifestPath}`);

ensureDir(generatedDir);

const sourceManifest = readJson(sourceManifestPath);
const sourceRun = sourceManifest.runs.find((run) => run.id === sourceRunId);
if (!sourceRun) throw new Error(`Missing source run ${sourceRunId}`);

const scriptPath = path.join(generatedDir, 'v7-htf-premise-qs3-validation.pine');
fs.writeFileSync(scriptPath, buildPine(fs.readFileSync(sourcePinePath, 'utf8')));

const run = {
  ...sourceRun,
  id: 'v7-htf-premise-qs3-4h',
  description: 'TradingView-only HTF premise validation: raw 4H port of current QS3 Displacement Quality candidate with Pine backtest window disabled. No threshold tuning.',
  variant: 'htf_premise_qs3_4h',
  geometry: 'QS3 4H HTF Premise Validation',
  scriptPath: path.relative(repoRoot, scriptPath),
  scriptName: 'Codex Scratch - v7-htf-premise-qs3-4h',
  scriptTitle: validationTitle,
  expectedStrategyTitle: validationTitle,
  strategyReportDateRange: 'Entire history',
  chartUrl: 'https://www.tradingview.com/chart/EU0fwd29/?symbol=BINANCE:BTCUSDT&interval=240',
  symbols,
  symbolMetadata,
  timeframes: [{ label: '4H', interval: '240' }],
  validation: {
    ...sourceRun.validation,
    minCsvFiles: symbols.length,
  },
};

writeJson(outputManifestPath, {
  version: 1,
  defaultRun: run.id,
  defaults: {
    ...sourceManifest.defaults,
    artifactsDir: 'tradingview/strategy/artifacts/v7_htf_premise_validation/tradingview/automation',
  },
  runs: [run],
});

console.log(JSON.stringify({
  artifactRoot,
  sourcePinePath,
  outputManifestPath,
  generatedPine: scriptPath,
  run: run.id,
  symbols: symbols.length,
  timeframe: run.timeframes[0],
}, null, 2));
