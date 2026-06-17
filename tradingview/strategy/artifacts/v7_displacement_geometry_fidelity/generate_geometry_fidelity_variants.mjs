#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const repoRoot = path.resolve(process.argv.includes('--cwd') ? process.argv[process.argv.indexOf('--cwd') + 1] : process.cwd());
const strategyRoot = path.join(repoRoot, 'tradingview/strategy');
const artifactRoot = path.join(strategyRoot, 'artifacts/v7_displacement_geometry_fidelity');
const outDir = path.join(artifactRoot, 'generated');
const templatePath = path.join(strategyRoot, 'unity_utm_strategy_v7_profitability_risk_harness_template.pine');
const manifestPath = path.join(artifactRoot, 'tv_geometry_fidelity_runs.json');

const profiles = [
  {
    id: 'displacement-current-1-50',
    variant: 'candidate_displacement_quality_current',
    label: 'Displacement Quality',
    title: 'Displacement Current 1.50',
    description: 'Current Displacement Quality control: range/ATR >= 1.50, TP1 1.0R.',
    minEntryRangeAtr: 1.5,
  },
  {
    id: 'exit-tp1-1-5r',
    variant: 'candidate_exit_tp1_1_5r',
    label: 'Displacement Quality',
    title: 'Exit TP1 1.5R',
    description: 'Exit geometry test: current Displacement Quality entries with wider TP1 at 1.5R.',
    minEntryRangeAtr: 1.5,
    tp1R: 1.5,
  },
  {
    id: 'exit-risk-floor-100bps',
    variant: 'candidate_exit_risk_floor_100bps',
    label: 'Displacement Quality',
    title: 'Risk Floor 100bps',
    description: 'Stop geometry test: current Displacement Quality with a simple 100bps minimum stop distance.',
    minEntryRangeAtr: 1.5,
    minRiskBps: 100,
  },
  {
    id: 'stop-floor-2atr',
    variant: 'candidate_stop_floor_2atr',
    label: 'Displacement Stop Floor',
    title: 'Stop Floor 2ATR',
    description: 'Stop geometry test: require stop distance to be at least 2.0 ATR.',
    minEntryRangeAtr: 1.5,
    minStopDistanceAtr: 2.0,
  },
  {
    id: 'displacement-1-35',
    variant: 'candidate_displacement_1_35',
    label: 'Displacement Quality',
    title: 'Displacement 1.35',
    description: 'Displacement robustness test: range/ATR >= 1.35.',
    minEntryRangeAtr: 1.35,
  },
  {
    id: 'displacement-1-75',
    variant: 'candidate_displacement_1_75',
    label: 'Displacement Quality',
    title: 'Displacement 1.75',
    description: 'Displacement robustness test: range/ATR >= 1.75.',
    minEntryRangeAtr: 1.75,
  },
  {
    id: 'displacement-2-00',
    variant: 'candidate_displacement_2_00',
    label: 'Displacement Quality',
    title: 'Displacement 2.00',
    description: 'Displacement robustness test: range/ATR >= 2.00.',
    minEntryRangeAtr: 2.0,
  },
  {
    id: 'retest-fidelity',
    variant: 'candidate_retest_fidelity',
    label: 'Displacement Retest Fidelity',
    title: 'Retest Fidelity',
    description: 'UTM fidelity test: displacement creates setup, then entry waits for armed-zone retest/continuation confirmation.',
    minEntryRangeAtr: 1.5,
  },
];

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

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function patchStringInputDefault(source, inputLabel, value) {
  const pattern = new RegExp(`input\\.string\\("[^"]+", "${escapeRegExp(inputLabel)}"`);
  return source.replace(pattern, `input.string("${value}", "${inputLabel}"`);
}

function patchFloatInputDefault(source, inputLabel, value) {
  const pattern = new RegExp(`input\\.float\\(-?\\d+(?:\\.\\d+)?, "${escapeRegExp(inputLabel)}"`);
  return source.replace(pattern, `input.float(${Number(value).toFixed(2)}, "${inputLabel}"`);
}

function patchTemplate(template, profile) {
  const runId = `v7-disp-geometry-${profile.id}`;
  const title = `Unity UTM Strategy v7 Geometry Test ${profile.title}`;
  const logic = `unity-utm-v7-geometry-test-${profile.id}`;
  let source = template
    .replace('"Unity UTM Strategy v7 Profitability Risk Harness Template"', `"${title}"`)
    .replace('input.string("unity-utm-v7-profitability-risk-harness-template", "Logic Version"', `input.string("${logic}", "Logic Version"`);
  source = patchStringInputDefault(source, 'Profitability Risk Test Profile', profile.label);
  source = patchFloatInputDefault(source, 'Minimum Entry Range / ATR', profile.minEntryRangeAtr ?? 1.5);
  if (profile.tp1R !== undefined) source = patchFloatInputDefault(source, 'TP1 R', profile.tp1R);
  if (profile.minRiskBps !== undefined) source = patchFloatInputDefault(source, 'Minimum Stop Distance (bps)', profile.minRiskBps);
  if (profile.minStopDistanceAtr !== undefined) source = patchFloatInputDefault(source, 'Minimum Stop Distance / ATR', profile.minStopDistanceAtr);
  return { runId, title, source };
}

ensureDir(outDir);
const template = fs.readFileSync(templatePath, 'utf8');
const runs = profiles.map((profile) => {
  const { runId, title, source } = patchTemplate(template, profile);
  const scriptFile = path.join(outDir, `${runId}.pine`);
  fs.writeFileSync(scriptFile, source);
  return {
    id: runId,
    description: `${profile.description} BTC/ETH/ZEC on 15m and 5m.`,
    variant: profile.variant,
    stopMode: 'sweep',
    geometry: profile.title,
    kind: 'strategy',
    scriptPath: path.relative(repoRoot, scriptFile),
    scriptName: `Codex Scratch - ${runId}`,
    scriptTitle: title,
    expectedStrategyTitle: title,
    requiresManualSettingsCommit: true,
    requiresSourceContractVerification: true,
    applyV6MappingsEachSymbol: true,
    samePaneSymbolSwitch: false,
    reuseV6MappingsAfterSamePaneSwitch: false,
    saveLayoutAfterInstall: false,
    strategyReportDateRange: 'Entire history',
    v6Mappings: mappings,
    chartUrl: 'https://www.tradingview.com/chart/EU0fwd29/?symbol=BINANCE:BTCUSDT&interval=15',
    symbols: ['BINANCE:BTCUSDT', 'BINANCE:ETHUSDT', 'BINANCE:ZECUSDT'],
    timeframes: [
      { label: '15m', interval: '15' },
      { label: '5m', interval: '5' },
    ],
    exportChartData: false,
    exportStrategyData: true,
    validation: {
      minCsvFiles: 6,
      minRows: 1,
      requiredColumns: [],
      nonConstantColumns: [],
      nonZeroColumns: [],
      numericChecks: [],
    },
    strategyReportReadyTimeoutMs: 240000,
  };
});

const manifest = {
  version: 1,
  defaultRun: runs[0].id,
  defaults: {
    chromeProfileEnv: 'TV_CHROME_PROFILE_DIR',
    chromeChannel: 'chromium',
    headless: false,
    artifactsDir: 'tradingview/strategy/artifacts/v7_displacement_geometry_fidelity/tradingview/automation',
    scriptNamePrefix: 'Codex Scratch',
    timeoutMs: 30000,
    navigationTimeoutMs: 60000,
    downloadTimeoutMs: 240000,
    waitAfterLoadMs: 10000,
    ignoreDefaultArgs: ['--use-mock-keychain', '--password-store=basic', '--disable-sync'],
    viewport: { width: 1440, height: 950 },
  },
  runs,
};

fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));
console.log(JSON.stringify({ outDir, manifestPath, runs: runs.length, slots: runs.length * 6 }, null, 2));
