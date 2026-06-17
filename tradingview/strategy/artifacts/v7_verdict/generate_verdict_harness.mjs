#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const repoRoot = path.resolve(process.argv.includes('--cwd') ? process.argv[process.argv.indexOf('--cwd') + 1] : process.cwd());
const strategyRoot = path.join(repoRoot, 'tradingview/strategy');
const outDir = path.join(strategyRoot, 'artifacts/v7_verdict/generated');
const templatePath = path.join(strategyRoot, 'unity_utm_strategy_v7_verdict_harness_template.pine');
const manifestPath = path.join(strategyRoot, 'artifacts/v7_verdict/tv_verdict_harness_runs.json');

const systems = [
  { id: 'a-current', variant: 'system_a_current', label: 'A Current', title: 'A Current' },
  { id: 'b-alert-score', variant: 'system_b_alert_score', label: 'B Alert Score', title: 'B Alert Score' },
  { id: 'b-alert-required', variant: 'system_b_alert_required', label: 'B Alert Required', title: 'B Alert Required' },
];

const stops = [
  { id: 'sweep', label: 'Sweep Wick', title: 'Sweep Wick' },
  { id: 'mss-swing', label: 'MSS Swing', title: 'MSS Swing' },
  { id: 'retest-poi', label: 'Retest POI', title: 'Retest POI' },
];

const mappings = [
  { label: 'REQ AIO Internal Bullish MSS', value: 'The Oracle AIO - [Unity] - V2: Internal Bullish MSS' },
  { label: 'REQ AIO Internal Bearish MSS', value: 'The Oracle AIO - [Unity] - V2: Internal Bearish MSS' },
  { label: 'REQ AIO Buy Trend Alert', value: 'The Oracle AIO - [Unity] - V2: Buy Trend Alert' },
  { label: 'REQ AIO Sell Trend Alert', value: 'The Oracle AIO - [Unity] - V2: Sell Trend Alert' },
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

function patchTemplate(template, system, stop) {
  const title = `Unity UTM Strategy v7 Verdict ${system.title} ${stop.title}`;
  const logic = `unity-utm-v7-verdict-${system.id}-${stop.id}`;
  return template
    .replace('"Unity UTM Strategy v7 Verdict Harness Template"', `"${title}"`)
    .replace('input.string("unity-utm-v7-verdict-harness-template", "Logic Version"', `input.string("${logic}", "Logic Version"`)
    .replace('input.string("A Current", "Verdict System"', `input.string("${system.label}", "Verdict System"`)
    .replace('input.string("Sweep Wick", "Verdict Stop Mode"', `input.string("${stop.label}", "Verdict Stop Mode"`);
}

ensureDir(outDir);
const template = fs.readFileSync(templatePath, 'utf8');
const runs = [];

for (const system of systems) {
  for (const stop of stops) {
    const runId = `v7-verdict-${system.id}-${stop.id}`;
    const scriptFile = path.join(outDir, `${runId}.pine`);
    const source = patchTemplate(template, system, stop);
    fs.writeFileSync(scriptFile, source);
    runs.push({
      id: runId,
      description: `Verdict harness: ${system.label}, ${stop.label} stop, BTC/ETH/ZEC on 15m and 5m.`,
      variant: system.variant,
      stopMode: stop.id,
      kind: 'strategy',
      scriptPath: path.relative(repoRoot, scriptFile),
      scriptName: `Codex Scratch - ${runId}`,
      scriptTitle: `Unity UTM Strategy v7 Verdict ${system.title} ${stop.title}`,
      expectedStrategyTitle: `Unity UTM Strategy v7 Verdict ${system.title} ${stop.title}`,
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
    });
  }
}

const manifest = {
  version: 1,
  defaultRun: runs[0].id,
  defaults: {
    chromeProfileEnv: 'TV_CHROME_PROFILE_DIR',
    chromeChannel: 'chromium',
    headless: false,
    artifactsDir: 'tradingview/strategy/artifacts/v7_verdict/tradingview/automation',
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
