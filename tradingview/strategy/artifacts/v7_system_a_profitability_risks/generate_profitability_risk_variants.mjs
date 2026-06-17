#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const repoRoot = path.resolve(process.argv.includes('--cwd') ? process.argv[process.argv.indexOf('--cwd') + 1] : process.cwd());
const strategyRoot = path.join(repoRoot, 'tradingview/strategy');
const artifactRoot = path.join(strategyRoot, 'artifacts/v7_system_a_profitability_risks');
const outDir = path.join(artifactRoot, 'generated');
const templatePath = path.join(strategyRoot, 'unity_utm_strategy_v7_profitability_risk_harness_template.pine');
const manifestPath = path.join(artifactRoot, 'tv_profitability_risk_runs.json');

const profiles = [
  {
    id: 'baseline',
    variant: 'system_a_baseline',
    label: 'Baseline',
    title: 'Baseline',
    description: 'Clean System A foundation with additional risk/volatility telemetry.',
  },
  {
    id: 'risk-veto-175bps',
    variant: 'risk_veto_175bps',
    label: 'Risk Veto 175bps',
    title: 'Risk Veto 175bps',
    description: 'Reject entries whose sweep-wick stop distance exceeds 175 bps.',
  },
  {
    id: 'risk-damp-150bps',
    variant: 'risk_damp_150bps',
    label: 'Risk Damp 150bps',
    title: 'Risk Damp 150bps',
    description: 'Halve risk on entries whose sweep-wick stop distance exceeds 150 bps.',
  },
  {
    id: 'directional-strength-slope',
    variant: 'quality_directional_strength_slope',
    label: 'Directional Strength Slope',
    title: 'Directional Strength Slope',
    description: 'Require Oracle Strength slope to be moving in the trade direction at entry.',
  },
  {
    id: 'bos-phase-agreement',
    variant: 'quality_bos_phase_agreement',
    label: 'BOS/Phase Agreement',
    title: 'BOS Phase Agreement',
    description: 'Require same-side AIO BOS or Phase1 CHoCH/BOS agreement beyond internal MSS.',
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

function patchInputDefault(source, inputLabel, value) {
  const pattern = new RegExp(`input\\.string\\("[^"]+", "${escapeRegExp(inputLabel)}"`);
  return source.replace(pattern, `input.string("${value}", "${inputLabel}"`);
}

function patchTemplate(template, profile) {
  const title = `Unity UTM Strategy v7 Risk Test ${profile.title}`;
  const logic = `unity-utm-v7-risk-test-${profile.id}`;
  return patchInputDefault(
    template
      .replace('"Unity UTM Strategy v7 Profitability Risk Harness Template"', `"${title}"`)
      .replace('input.string("unity-utm-v7-profitability-risk-harness-template", "Logic Version"', `input.string("${logic}", "Logic Version"`),
    'Profitability Risk Test Profile',
    profile.label,
  );
}

ensureDir(outDir);
const template = fs.readFileSync(templatePath, 'utf8');
const runs = profiles.map((profile) => {
  const runId = `v7-system-a-risk-${profile.id}`;
  const scriptFile = path.join(outDir, `${runId}.pine`);
  fs.writeFileSync(scriptFile, patchTemplate(template, profile));
  return {
    id: runId,
    description: `${profile.description} BTC/ETH/ZEC on 15m and 5m.`,
    variant: profile.variant,
    stopMode: 'sweep',
    kind: 'strategy',
    scriptPath: path.relative(repoRoot, scriptFile),
    scriptName: `Codex Scratch - ${runId}`,
    scriptTitle: `Unity UTM Strategy v7 Risk Test ${profile.title}`,
    expectedStrategyTitle: `Unity UTM Strategy v7 Risk Test ${profile.title}`,
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
    artifactsDir: 'tradingview/strategy/artifacts/v7_system_a_profitability_risks/tradingview/automation',
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
console.log(JSON.stringify({ outDir, manifestPath, runs: runs.length }, null, 2));
