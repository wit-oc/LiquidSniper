import fs from 'node:fs';
import path from 'node:path';

export function parseArgs(argv = process.argv.slice(2)) {
  const args = {};
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (!token.startsWith('--')) continue;
    const key = token.slice(2);
    const next = argv[i + 1];
    if (!next || next.startsWith('--')) {
      args[key] = true;
    } else {
      args[key] = next;
      i += 1;
    }
  }
  return args;
}

export function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, 'utf8'));
}

export function resolveFromRoot(root, maybePath) {
  if (!maybePath) return maybePath;
  return path.isAbsolute(maybePath) ? maybePath : path.resolve(root, maybePath);
}

export function loadConfig(args) {
  const root = path.resolve(args.cwd || process.cwd());
  const configPath = resolveFromRoot(root, args.config || 'tradingview/config/tv_automation_runs.json');
  const config = readJson(configPath);
  const runId = args.run || config.defaultRun;
  if (!runId) {
    throw new Error('Missing --run and no defaultRun in config');
  }
  const run = (config.runs || []).find((candidate) => candidate.id === runId);
  if (!run) {
    throw new Error(`Run not found: ${runId}`);
  }
  const defaults = config.defaults || {};
  const artifactsDir = resolveFromRoot(root, args.artifacts || defaults.artifactsDir || 'artifacts/tradingview/automation');
  return { root, configPath, config, defaults, runId, run, artifactsDir };
}

export function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
  return dir;
}

export function safeName(value) {
  return String(value || 'unknown')
    .replace(/[^a-zA-Z0-9._-]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 120);
}

export function timestamp() {
  return new Date().toISOString().replace(/[:.]/g, '-');
}

export function commandArtifactDir(baseDir, runId, command, stamp = timestamp()) {
  return ensureDir(path.join(baseDir, safeName(runId), `${stamp}-${safeName(command)}`));
}

export function matrixItems(run) {
  const symbols = run.symbols && run.symbols.length ? run.symbols : [run.symbol || 'BINANCE:BTCUSDT'];
  const timeframes = run.timeframes && run.timeframes.length
    ? run.timeframes
    : [{ label: run.timeframe || '15m', interval: run.interval || '15' }];
  const out = [];
  for (const symbol of symbols) {
    for (const tf of timeframes) {
      const item = typeof tf === 'string' ? { label: tf, interval: tf } : tf;
      out.push({ symbol, label: item.label || item.interval, interval: item.interval || item.label });
    }
  }
  return out;
}

export function chartUrlFor(run, symbol, interval) {
  const base = run.chartUrl || 'https://www.tradingview.com/chart/';
  const url = new URL(base);
  url.searchParams.set('symbol', symbol);
  url.searchParams.set('interval', interval);
  return url.toString();
}

export function writeReport(filePath, payload) {
  ensureDir(path.dirname(filePath));
  fs.writeFileSync(filePath, `${JSON.stringify(payload, null, 2)}\n`);
}
