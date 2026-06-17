#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const repoRoot = path.resolve(process.argv.includes('--cwd') ? process.argv[process.argv.indexOf('--cwd') + 1] : process.cwd());
const strategyRoot = path.join(repoRoot, 'tradingview/strategy');
const artifactRoot = path.join(strategyRoot, 'artifacts/v7_leverage_stop_sidebar');
const outDir = path.join(artifactRoot, 'generated');
const templatePath = path.join(strategyRoot, 'unity_utm_strategy_v7_profitability_risk_harness_template.pine');
const manifestPath = path.join(artifactRoot, 'tv_leverage_stop_runs.json');

const profiles = [
  {
    id: 'uniform-100x-100bps',
    variant: 'leverage_stop_uniform_100x_100bps',
    title: 'Uniform 100x 100bps',
    description: 'Control plus creator-style 100x leverage stop floor: 100bps applied uniformly.',
    minRiskBps: 100,
    maxRiskBps: 600,
    stopMode: 'leverage-floor',
  },
  {
    id: 'control-125bps',
    variant: 'leverage_stop_control_125bps',
    title: 'Control 125bps',
    description: 'Drawdown-first control from the latest stop-engine verdict: 125bps applied uniformly.',
    minRiskBps: 125,
    maxRiskBps: 600,
    stopMode: 'leverage-floor',
  },
  {
    id: 'uniform-50x-200bps',
    variant: 'leverage_stop_uniform_50x_200bps',
    title: 'Uniform 50x 200bps',
    description: 'Creator-style 50x leverage stop floor: 200bps applied uniformly.',
    minRiskBps: 200,
    maxRiskBps: 600,
    stopMode: 'leverage-floor',
  },
  {
    id: 'uniform-20x-500bps',
    variant: 'leverage_stop_uniform_20x_500bps',
    title: 'Uniform 20x 500bps',
    description: 'Creator-style 20x leverage stop floor: 500bps applied uniformly.',
    minRiskBps: 500,
    maxRiskBps: 750,
    stopMode: 'leverage-floor',
  },
  {
    id: 'uniform-10x-1000bps',
    variant: 'leverage_stop_uniform_10x_1000bps',
    title: 'Uniform 10x 1000bps',
    description: 'Creator-style 10x leverage stop floor: 1000bps applied uniformly.',
    minRiskBps: 1000,
    maxRiskBps: 1500,
    stopMode: 'leverage-floor',
  },
  {
    id: 'profile-btc100-eth200-zec500',
    variant: 'leverage_stop_profile_btc100_eth200_zec500',
    title: 'Profile BTC100 ETH200 ZEC500',
    description: 'Market-profile leverage floor: BTC 100bps, ETH 200bps, ZEC 500bps.',
    minRiskBps: 100,
    maxRiskBps: 750,
    stopMode: 'leverage-profile',
    symbolFloors: { BTC: 100, ETH: 200, ZEC: 500 },
  },
  {
    id: 'profile-btc125-eth500-zec1000',
    variant: 'leverage_stop_profile_btc125_eth500_zec1000',
    title: 'Profile BTC125 ETH500 ZEC1000',
    description: 'Wider market-profile leverage floor: BTC 125bps, ETH 500bps, ZEC 1000bps.',
    minRiskBps: 125,
    maxRiskBps: 1500,
    stopMode: 'leverage-profile',
    symbolFloors: { BTC: 125, ETH: 500, ZEC: 1000 },
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

function effectiveFloorExpr(profile) {
  if (!profile.symbolFloors) return 'min_risk_bps';
  const { BTC, ETH, ZEC } = profile.symbolFloors;
  return `str.contains(syminfo.ticker, "BTC") ? ${BTC}.0 : str.contains(syminfo.ticker, "ETH") ? ${ETH}.0 : str.contains(syminfo.ticker, "ZEC") ? ${ZEC}.0 : min_risk_bps`;
}

function patchEffectiveFloor(source, profile) {
  const maxLine = /max_risk_bps = input\.float\([^\n]+\n/;
  const effectiveBlock =
    `$&effective_min_risk_bps = ${effectiveFloorExpr(profile)}\n` +
    'effective_max_risk_bps = math.max(max_risk_bps, effective_min_risk_bps)\n';
  let patched = source.replace(maxLine, effectiveBlock);
  patched = patched
    .replaceAll('longRiskBps >= min_risk_bps and longRiskBps <= max_risk_bps', 'longRiskBps >= effective_min_risk_bps and longRiskBps <= effective_max_risk_bps')
    .replaceAll('shortRiskBps >= min_risk_bps and shortRiskBps <= max_risk_bps', 'shortRiskBps >= effective_min_risk_bps and shortRiskBps <= effective_max_risk_bps')
    .replaceAll('"-MF" + str.tostring(min_risk_bps, "#.##")', '"-MF" + str.tostring(effective_min_risk_bps, "#.##")');
  return patched;
}

function patchTemplate(template, profile) {
  const runId = `v7-leverage-stop-${profile.id}`;
  const title = `Unity UTM Strategy v7 Leverage Stop Sidebar ${profile.title}`;
  const logic = `unity-utm-v7-leverage-stop-sidebar-${profile.id}`;
  let source = template
    .replace('"Unity UTM Strategy v7 Profitability Risk Harness Template"', `"${title}"`)
    .replace('input.string("unity-utm-v7-profitability-risk-harness-template", "Logic Version"', `input.string("${logic}", "Logic Version"`);
  source = patchStringInputDefault(source, 'Profitability Risk Test Profile', 'Displacement Quality');
  source = patchStringInputDefault(source, 'Stop Engine Label', 'Sweep Wick');
  source = patchStringInputDefault(source, 'Stop Exit Mode', 'Hard Stop');
  source = patchFloatInputDefault(source, 'Minimum Entry Range / ATR', 1.5);
  source = patchFloatInputDefault(source, 'Minimum Stop Distance (bps)', profile.minRiskBps);
  source = patchFloatInputDefault(source, 'Maximum Stop Distance (bps)', profile.maxRiskBps);
  source = patchFloatInputDefault(source, 'Invalidation Stop Buffer (bps)', 4);
  source = patchFloatInputDefault(source, 'TP1 R', 1.0);
  source = patchEffectiveFloor(source, profile);
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
    description: `${profile.description} BTC/ETH/ZEC on 15m and 5m. Sidebar-only leverage stop floor pressure test.`,
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
    artifactsDir: 'tradingview/strategy/artifacts/v7_leverage_stop_sidebar/tradingview/automation',
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
