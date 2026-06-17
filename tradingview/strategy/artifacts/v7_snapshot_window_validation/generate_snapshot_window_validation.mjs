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
const artifactRoot = path.join(strategyRoot, 'artifacts/v7_snapshot_window_validation');
const generatedDir = path.join(artifactRoot, 'generated');
const sourcePinePath = path.join(strategyRoot, 'artifacts/v7_generalization_independent_variables/generated/v7-generalization-quality-score-3.pine');
const sourceManifestPath = path.join(strategyRoot, 'artifacts/v7_generalization_independent_variables/tv_generalization_independent_variables_runs.json');
const outputManifestPath = path.join(artifactRoot, 'tv_snapshot_window_validation_runs.json');

const sourceRunId = 'v7-generalization-quality-score-3';
const sourceTitle = 'Unity UTM Strategy v7 Generalization IV Quality Score 3';
const sourceLogic = 'unity-utm-v7-generalization-quality-score-3';

const symbols = {
  BTC: 'BINANCE:BTCUSDT',
  ETH: 'BINANCE:ETHUSDT',
  SOL: 'BINANCE:SOLUSDT',
  BNB: 'BINANCE:BNBUSDT',
  DOGE: 'BINANCE:DOGEUSDT',
  ZEC: 'BINANCE:ZECUSDT',
  ARB: 'BINANCE:ARBUSDT',
  LINK: 'BINANCE:LINKUSDT',
  XRP: 'BINANCE:XRPUSDT',
  HYPE: 'BINANCE:HYPEUSDT.P',
  AERO: 'BINANCE:AEROUSDT.P',
  VIRTUAL: 'BINANCE:VIRTUALUSDT.P',
  RENDER: 'BINANCE:RENDERUSDT.P',
};

const allRepresentative = [
  symbols.BTC,
  symbols.ETH,
  symbols.SOL,
  symbols.BNB,
  symbols.DOGE,
  symbols.ZEC,
  symbols.ARB,
  symbols.LINK,
  symbols.XRP,
  symbols.HYPE,
  symbols.AERO,
  symbols.VIRTUAL,
  symbols.RENDER,
];

const longHistory2024 = [
  symbols.BTC,
  symbols.ETH,
  symbols.SOL,
  symbols.BNB,
  symbols.DOGE,
  symbols.ZEC,
  symbols.ARB,
  symbols.LINK,
  symbols.XRP,
  symbols.RENDER,
];

const longHistory2022 = [
  symbols.BTC,
  symbols.ETH,
  symbols.SOL,
  symbols.BNB,
  symbols.DOGE,
  symbols.ZEC,
  symbols.LINK,
  symbols.XRP,
];

const longHistory2021 = longHistory2022;

const windows = [
  {
    id: 'latest-2026',
    label: 'Latest 2026 available 5m window',
    regime: 'latest available',
    start: '2026-03-22T00:00:00Z',
    end: '2026-06-02T23:59:00Z',
    symbols: allRepresentative,
  },
  {
    id: 'prior-2026',
    label: 'Prior 2026 5m window',
    regime: 'prior adjacent',
    start: '2025-12-15T00:00:00Z',
    end: '2026-03-14T23:59:00Z',
    symbols: allRepresentative,
  },
  {
    id: 'q4-2025',
    label: 'Q4 2025 reflexive window',
    regime: '2025 current cycle',
    start: '2025-09-01T00:00:00Z',
    end: '2025-11-30T23:59:00Z',
    symbols: allRepresentative,
  },
  {
    id: 'q3-2024',
    label: 'Q3 2024 cycle window',
    regime: '2024 cycle',
    start: '2024-07-01T00:00:00Z',
    end: '2024-09-30T23:59:00Z',
    symbols: longHistory2024,
  },
  {
    id: 'bear-2022',
    label: '2022 bear window',
    regime: '2022 bear',
    start: '2022-05-01T00:00:00Z',
    end: '2022-07-31T23:59:00Z',
    symbols: longHistory2022,
  },
  {
    id: 'top-2021',
    label: '2021 bull/top window',
    regime: '2021 bull/top',
    start: '2021-10-01T00:00:00Z',
    end: '2021-12-31T23:59:00Z',
    symbols: longHistory2021,
  },
];

const symbolMetadata = {
  'BINANCE:BTCUSDT': { asset: 'BTC', regimeTier: 'major representative', liquidityTier: 'major', priorOutcome: 'failed-control' },
  'BINANCE:ETHUSDT': { asset: 'ETH', regimeTier: 'major representative', liquidityTier: 'major', priorOutcome: 'diagnostic-only' },
  'BINANCE:SOLUSDT': { asset: 'SOL', regimeTier: 'large alt representative', liquidityTier: 'major', priorOutcome: 'failed-control' },
  'BINANCE:BNBUSDT': { asset: 'BNB', regimeTier: 'large alt representative', liquidityTier: 'major', priorOutcome: 'failed-control' },
  'BINANCE:DOGEUSDT': { asset: 'DOGE', regimeTier: 'large alt representative', liquidityTier: 'major/reflexive', priorOutcome: 'failed-control' },
  'BINANCE:ZECUSDT': { asset: 'ZEC', regimeTier: 'prior admitted control', liquidityTier: 'mid', priorOutcome: 'pass' },
  'BINANCE:ARBUSDT': { asset: 'ARB', regimeTier: 'prior admitted control', liquidityTier: 'smaller/reflexive', priorOutcome: 'pass' },
  'BINANCE:LINKUSDT': { asset: 'LINK', regimeTier: 'prior admitted control', liquidityTier: 'mid', priorOutcome: 'pass' },
  'BINANCE:XRPUSDT': { asset: 'XRP', regimeTier: 'prior admitted control', liquidityTier: 'major', priorOutcome: 'pass' },
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

function timeMs(iso) {
  const value = Date.parse(iso);
  if (!Number.isFinite(value)) throw new Error(`Invalid ISO timestamp: ${iso}`);
  return value;
}

function titleCaseWindow(id) {
  return id.split('-').map((part) => part.toUpperCase()).join(' ');
}

function buildPine(source, window) {
  const validationTitle = `Unity UTM Strategy v7 Snapshot QS3 5m ${titleCaseWindow(window.id)}`;
  const validationLogic = `unity-utm-v7-snapshot-qs3-5m-${window.id}`;
  let patched = patchRequired(source, `"${sourceTitle}"`, `"${validationTitle}"`, 'strategy title');
  patched = patchRequired(patched, `"${sourceLogic}"`, `"${validationLogic}"`, 'logic version');
  patched = patched.replace(
    /enable_backtest_window = input\.bool\((true|false), "Enable Backtest Window", group=g_time\)/,
    'enable_backtest_window = input.bool(true, "Enable Backtest Window", group=g_time)',
  );
  patched = patched.replace(
    /backtest_start = input\.time\(\d+, "Backtest Start", group=g_time\)/,
    `backtest_start = input.time(${timeMs(window.start)}, "Backtest Start", group=g_time)`,
  );
  patched = patched.replace(
    /backtest_end = input\.time\(\d+, "Backtest End", group=g_time\)/,
    `backtest_end = input.time(${timeMs(window.end)}, "Backtest End", group=g_time)`,
  );
  if (!/min_quality_score\s*=\s*input\.int\(3,\s*"Minimum Quality Score To Trade"/.test(patched)) {
    throw new Error('Source Pine is not the QS3 candidate; minimum quality score is not 3.');
  }
  if (!/test_profile\s*=\s*input\.string\("Displacement Quality"/.test(patched)) {
    throw new Error('Source Pine is not the current Displacement Quality candidate.');
  }
  return { pine: patched, validationTitle, validationLogic };
}

if (!fs.existsSync(sourcePinePath)) throw new Error(`Missing QS3 generated source Pine: ${sourcePinePath}`);
if (!fs.existsSync(sourceManifestPath)) throw new Error(`Missing source manifest: ${sourceManifestPath}`);

ensureDir(generatedDir);

const sourceManifest = readJson(sourceManifestPath);
const sourceRun = sourceManifest.runs.find((run) => run.id === sourceRunId);
if (!sourceRun) throw new Error(`Missing source run ${sourceRunId}`);
const sourcePine = fs.readFileSync(sourcePinePath, 'utf8');

const runs = windows.map((window) => {
  const { pine, validationTitle } = buildPine(sourcePine, window);
  const scriptPath = path.join(generatedDir, `v7-snapshot-qs3-5m-${window.id}.pine`);
  fs.writeFileSync(scriptPath, pine);
  return {
    ...sourceRun,
    id: `v7-snapshot-qs3-5m-${window.id}`,
    description: `TradingView-only snapshot window validation for QS3 + 5m: ${window.label}. Uses only the existing Pine backtest window inputs; no threshold or strategy logic changes.`,
    variant: `snapshot_qs3_5m_${window.id.replace(/-/g, '_')}`,
    stopMode: 'structural-control',
    geometry: 'QS3 5m Snapshot Window',
    scriptPath: path.relative(repoRoot, scriptPath),
    scriptName: `Codex Scratch - v7-snapshot-qs3-5m-${window.id}`,
    scriptTitle: validationTitle,
    expectedStrategyTitle: validationTitle,
    strategyReportDateRange: {
      mode: 'custom',
      start: window.start,
      end: window.end,
      source: 'Strategy Tester date range dropdown',
    },
    chartUrl: 'https://www.tradingview.com/chart/EU0fwd29/?symbol=BINANCE:BTCUSDT&interval=5',
    symbols: window.symbols,
    symbolMetadata,
    snapshotWindow: {
      id: window.id,
      label: window.label,
      regime: window.regime,
      start: window.start,
      end: window.end,
      requestedDays: Math.round((timeMs(window.end) - timeMs(window.start)) / 86400000) + 1,
      dateSource: 'Pine backtest_start/backtest_end inputs',
    },
    timeframes: [{ label: '5m', interval: '5' }],
    validation: {
      ...sourceRun.validation,
      minCsvFiles: window.symbols.length,
    },
  };
});

writeJson(outputManifestPath, {
  version: 1,
  defaultRun: runs[0].id,
  defaults: {
    ...sourceManifest.defaults,
    artifactsDir: 'tradingview/strategy/artifacts/v7_snapshot_window_validation/tradingview/automation',
  },
  runs,
});

console.log(JSON.stringify({
  artifactRoot,
  sourcePinePath,
  outputManifestPath,
  generatedDir,
  runs: runs.map((run) => ({
    id: run.id,
    symbols: run.symbols.length,
    window: run.snapshotWindow,
  })),
  totalSlots: runs.reduce((sum, run) => sum + run.symbols.length * run.timeframes.length, 0),
}, null, 2));
