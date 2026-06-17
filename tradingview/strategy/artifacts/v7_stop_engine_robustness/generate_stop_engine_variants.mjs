#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const repoRoot = path.resolve(process.argv.includes('--cwd') ? process.argv[process.argv.indexOf('--cwd') + 1] : process.cwd());
const strategyRoot = path.join(repoRoot, 'tradingview/strategy');
const artifactRoot = path.join(strategyRoot, 'artifacts/v7_stop_engine_robustness');
const outDir = path.join(artifactRoot, 'generated');
const templatePath = path.join(strategyRoot, 'unity_utm_strategy_v7_profitability_risk_harness_template.pine');
const manifestPath = path.join(artifactRoot, 'tv_stop_engine_runs.json');

const profiles = [
  {
    id: 'current',
    variant: 'stop_engine_current',
    stopMode: 'sweep',
    stopEngineLabel: 'Sweep Wick',
    title: 'Current Stop Baseline',
    description: 'Current Displacement Quality stop engine: 4bps invalidation buffer and baseline minimum stop distance.',
    minRiskBps: 15,
    stopBufferBps: 4,
    stopExitMode: 'Hard Stop',
  },
  {
    id: 'floor-75bps',
    variant: 'stop_engine_floor_75bps',
    stopMode: 'sweep',
    stopEngineLabel: 'Sweep Wick',
    title: 'Stop Floor 75bps',
    description: 'Stop-distance robustness test: current stop engine with 75bps minimum stop distance.',
    minRiskBps: 75,
    stopBufferBps: 4,
    stopExitMode: 'Hard Stop',
  },
  {
    id: 'floor-100bps',
    variant: 'stop_engine_floor_100bps',
    stopMode: 'sweep',
    stopEngineLabel: 'Sweep Wick',
    title: 'Stop Floor 100bps',
    description: 'Stop-distance robustness test: current stop engine with 100bps minimum stop distance.',
    minRiskBps: 100,
    stopBufferBps: 4,
    stopExitMode: 'Hard Stop',
  },
  {
    id: 'floor-125bps',
    variant: 'stop_engine_floor_125bps',
    stopMode: 'sweep',
    stopEngineLabel: 'Sweep Wick',
    title: 'Stop Floor 125bps',
    description: 'Stop-distance robustness test: current stop engine with 125bps minimum stop distance.',
    minRiskBps: 125,
    stopBufferBps: 4,
    stopExitMode: 'Hard Stop',
  },
  {
    id: 'buffer-20bps-floor-100bps',
    variant: 'stop_engine_buffer_20bps_floor_100bps',
    stopMode: 'sweep-buffer',
    stopEngineLabel: 'Sweep Wide Buffer',
    title: 'Wide Buffer 20bps Floor 100bps',
    description: 'Sweep-tolerance test: structural stop with 20bps invalidation buffer and 100bps minimum stop distance.',
    minRiskBps: 100,
    stopBufferBps: 20,
    stopExitMode: 'Hard Stop',
  },
  {
    id: 'close-confirm-floor-100bps',
    variant: 'stop_engine_close_confirm_floor_100bps',
    stopMode: 'sweep-close-confirmed',
    stopEngineLabel: 'Sweep Close Confirmed',
    title: 'Close Confirmed Floor 100bps',
    description: 'Sweep-tolerance diagnostic: TP limit plus close-confirmed invalidation with 100bps minimum stop distance.',
    minRiskBps: 100,
    stopBufferBps: 4,
    stopExitMode: 'Close Confirmed',
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
  const runId = `v7-stop-engine-${profile.id}`;
  const title = `Unity UTM Strategy v7 Stop Engine Test ${profile.title}`;
  const logic = `unity-utm-v7-stop-engine-test-${profile.id}`;
  let source = template
    .replace('"Unity UTM Strategy v7 Profitability Risk Harness Template"', `"${title}"`)
    .replace('input.string("unity-utm-v7-profitability-risk-harness-template", "Logic Version"', `input.string("${logic}", "Logic Version"`);
  source = patchStringInputDefault(source, 'Profitability Risk Test Profile', 'Displacement Quality');
  source = patchStringInputDefault(source, 'Stop Engine Label', profile.stopEngineLabel);
  source = patchStringInputDefault(source, 'Stop Exit Mode', profile.stopExitMode);
  source = patchFloatInputDefault(source, 'Minimum Entry Range / ATR', 1.5);
  source = patchFloatInputDefault(source, 'Minimum Stop Distance (bps)', profile.minRiskBps);
  source = patchFloatInputDefault(source, 'Invalidation Stop Buffer (bps)', profile.stopBufferBps);
  source = patchFloatInputDefault(source, 'TP1 R', 1.0);
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
    stopMode: profile.stopMode,
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
    artifactsDir: 'tradingview/strategy/artifacts/v7_stop_engine_robustness/tradingview/automation',
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
