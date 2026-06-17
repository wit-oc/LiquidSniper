#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const repoRoot = path.resolve(process.argv.includes('--cwd') ? process.argv[process.argv.indexOf('--cwd') + 1] : process.cwd());
const strategyRoot = path.join(repoRoot, 'tradingview/strategy');
const artifactRoot = path.join(strategyRoot, 'artifacts/v7_fixed_percent_stop_sidebar');
const outDir = path.join(artifactRoot, 'generated');
const templatePath = path.join(strategyRoot, 'unity_utm_strategy_v7_profitability_risk_harness_template.pine');
const manifestPath = path.join(artifactRoot, 'tv_fixed_percent_stop_runs.json');

const profiles = [
  {
    id: 'structural-control-100bps',
    variant: 'fixed_stop_structural_control_100bps',
    title: 'Structural Control 100bps',
    description: 'Current structural Sweep Wick hard-floor control at 100bps.',
    minRiskBps: 100,
    maxRiskBps: 600,
    stopMode: 'structural-control',
  },
  {
    id: 'structural-control-125bps',
    variant: 'fixed_stop_structural_control_125bps',
    title: 'Structural Control 125bps',
    description: 'Current structural Sweep Wick hard-floor control at 125bps.',
    minRiskBps: 125,
    maxRiskBps: 600,
    stopMode: 'structural-control',
  },
  {
    id: 'uniform-100x-100bps',
    variant: 'fixed_stop_uniform_100x_100bps',
    title: 'Fixed 100x 1pct',
    description: 'Creator-style 100x fixed-percent stop: 1.0% / 100bps from entry.',
    fixedStopBps: 100,
    minRiskBps: 0,
    maxRiskBps: 10000,
    stopMode: 'fixed-percent',
  },
  {
    id: 'uniform-50x-200bps',
    variant: 'fixed_stop_uniform_50x_200bps',
    title: 'Fixed 50x 2pct',
    description: 'Creator-style 50x fixed-percent stop: 2.0% / 200bps from entry.',
    fixedStopBps: 200,
    minRiskBps: 0,
    maxRiskBps: 10000,
    stopMode: 'fixed-percent',
  },
  {
    id: 'uniform-20x-500bps',
    variant: 'fixed_stop_uniform_20x_500bps',
    title: 'Fixed 20x 5pct',
    description: 'Creator-style 20x fixed-percent stop: 5.0% / 500bps from entry.',
    fixedStopBps: 500,
    minRiskBps: 0,
    maxRiskBps: 10000,
    stopMode: 'fixed-percent',
  },
  {
    id: 'uniform-10x-1000bps',
    variant: 'fixed_stop_uniform_10x_1000bps',
    title: 'Fixed 10x 10pct',
    description: 'Creator-style 10x fixed-percent stop: 10.0% / 1000bps from entry.',
    fixedStopBps: 1000,
    minRiskBps: 0,
    maxRiskBps: 10000,
    stopMode: 'fixed-percent',
  },
  {
    id: 'profile-btc100-eth200-zec500',
    variant: 'fixed_stop_profile_btc100_eth200_zec500',
    title: 'Fixed Profile BTC100 ETH200 ZEC500',
    description: 'Fixed-percent market profile: BTC 1.0%, ETH 2.0%, ZEC 5.0%.',
    minRiskBps: 0,
    maxRiskBps: 10000,
    stopMode: 'fixed-percent-profile',
    symbolStops: { BTC: 100, ETH: 200, ZEC: 500 },
  },
  {
    id: 'profile-btc125-eth500-zec1000',
    variant: 'fixed_stop_profile_btc125_eth500_zec1000',
    title: 'Fixed Profile BTC125 ETH500 ZEC1000',
    description: 'Wider fixed-percent market profile: BTC 1.25%, ETH 5.0%, ZEC 10.0%.',
    minRiskBps: 0,
    maxRiskBps: 10000,
    stopMode: 'fixed-percent-profile',
    symbolStops: { BTC: 125, ETH: 500, ZEC: 1000 },
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

function fixedStopExpr(profile) {
  if (!profile.symbolStops) return `${Number(profile.fixedStopBps).toFixed(1)}`;
  const { BTC, ETH, ZEC } = profile.symbolStops;
  return `str.contains(syminfo.ticker, "BTC") ? ${BTC}.0 : str.contains(syminfo.ticker, "ETH") ? ${ETH}.0 : str.contains(syminfo.ticker, "ZEC") ? ${ZEC}.0 : ${BTC}.0`;
}

function patchExact(source, before, after, label) {
  if (!source.includes(before)) {
    throw new Error(`Unable to patch ${label}; source block not found.`);
  }
  return source.replace(before, after);
}

function patchFixedPercentStopModel(source, profile) {
  const originalRiskBlock = `longStopAnchor = armInvalidation
shortStopAnchor = armInvalidation
longStop = setupSide == 1 and not na(longStopAnchor) ? longStopAnchor * (1.0 - stop_buffer_bps / 10000.0) : na
shortStop = setupSide == -1 and not na(shortStopAnchor) ? shortStopAnchor * (1.0 + stop_buffer_bps / 10000.0) : na
longRisk = not na(longStop) ? close - longStop : na
shortRisk = not na(shortStop) ? shortStop - close : na
longRiskBps = not na(longRisk) and longRisk > 0 ? longRisk / close * 10000.0 : na
shortRiskBps = not na(shortRisk) and shortRisk > 0 ? shortRisk / close * 10000.0 : na
longStopDistanceAtr = not na(longRiskBps) and not na(entryAtrBps) and entryAtrBps > 0 ? longRiskBps / entryAtrBps : na
shortStopDistanceAtr = not na(shortRiskBps) and not na(entryAtrBps) and entryAtrBps > 0 ? shortRiskBps / entryAtrBps : na`;

  const fixedRiskBlock = `longStopAnchor = armInvalidation
shortStopAnchor = armInvalidation
fixed_stop_bps = ${fixedStopExpr(profile)}
fixed_stop_pct = fixed_stop_bps / 10000.0
longStop = setupSide == 1 ? close * (1.0 - fixed_stop_pct) : na
shortStop = setupSide == -1 ? close * (1.0 + fixed_stop_pct) : na
longRisk = not na(longStop) ? close - longStop : na
shortRisk = not na(shortStop) ? shortStop - close : na
longRiskBps = not na(longRisk) and longRisk > 0 ? longRisk / close * 10000.0 : na
shortRiskBps = not na(shortRisk) and shortRisk > 0 ? shortRisk / close * 10000.0 : na
longStopDistanceAtr = not na(longRiskBps) and not na(entryAtrBps) and entryAtrBps > 0 ? longRiskBps / entryAtrBps : na
shortStopDistanceAtr = not na(shortRiskBps) and not na(entryAtrBps) and entryAtrBps > 0 ? shortRiskBps / entryAtrBps : na`;

  let patched = patchExact(source, originalRiskBlock, fixedRiskBlock, 'fixed percent risk block');
  patched = patched.replace(
    'options=["Sweep Wick", "Sweep Wide Buffer", "Sweep Close Confirmed"]',
    'options=["Sweep Wick", "Sweep Wide Buffer", "Sweep Close Confirmed", "Fixed Percent"]',
  );
  patched = patchStringInputDefault(patched, 'Stop Engine Label', 'Fixed Percent');
  patched = patchExact(
    patched,
    ' + "-MF" + str.tostring(min_risk_bps, "#.##") + "-SB" + str.tostring(stop_buffer_bps, "#.##")',
    ' + "-MF" + str.tostring(min_risk_bps, "#.##") + "-FB" + str.tostring(fixed_stop_bps, "#.##") + "-SB" + str.tostring(stop_buffer_bps, "#.##")',
    'fixed stop entry telemetry',
  );
  return patched;
}

function patchTemplate(template, profile) {
  const runId = `v7-fixed-stop-${profile.id}`;
  const title = `Unity UTM Strategy v7 Fixed Percent Stop Sidebar ${profile.title}`;
  const logic = `unity-utm-v7-fixed-percent-stop-sidebar-${profile.id}`;
  let source = template
    .replace('"Unity UTM Strategy v7 Profitability Risk Harness Template"', `"${title}"`)
    .replace('input.string("unity-utm-v7-profitability-risk-harness-template", "Logic Version"', `input.string("${logic}", "Logic Version"`);
  source = patchStringInputDefault(source, 'Profitability Risk Test Profile', 'Displacement Quality');
  source = patchStringInputDefault(source, 'Stop Exit Mode', 'Hard Stop');
  source = patchFloatInputDefault(source, 'Minimum Entry Range / ATR', 1.5);
  source = patchFloatInputDefault(source, 'Minimum Stop Distance (bps)', profile.minRiskBps);
  source = patchFloatInputDefault(source, 'Maximum Stop Distance (bps)', profile.maxRiskBps);
  source = patchFloatInputDefault(source, 'Invalidation Stop Buffer (bps)', 4);
  source = patchFloatInputDefault(source, 'TP1 R', 1.0);
  if (profile.fixedStopBps || profile.symbolStops) {
    source = patchFixedPercentStopModel(source, profile);
  } else {
    source = patchStringInputDefault(source, 'Stop Engine Label', 'Sweep Wick');
  }
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
    description: `${profile.description} BTC/ETH/ZEC on 15m and 5m. Sidebar-only fixed-percent stop practicality spike.`,
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
    artifactsDir: 'tradingview/strategy/artifacts/v7_fixed_percent_stop_sidebar/tradingview/automation',
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
