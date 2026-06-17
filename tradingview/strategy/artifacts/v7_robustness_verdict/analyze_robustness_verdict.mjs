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
const manifestPath = path.resolve(repoRoot, args.manifest || 'tradingview/strategy/artifacts/v7_fixed_percent_stop_sidebar/tv_fixed_percent_stop_runs.json');
const automationDir = path.resolve(repoRoot, args.automationDir || 'tradingview/strategy/artifacts/v7_fixed_percent_stop_sidebar/tradingview/automation');
const outputDir = path.resolve(repoRoot, args.output || 'tradingview/strategy/artifacts/v7_robustness_verdict');
const telemetryDir = path.resolve(repoRoot, args.telemetryDir || 'tradingview/strategy/.telemetry/outputs/v7_robustness_verdict');
const initialCapital = Number(args.initialCapital || 10000);
const controlRunIds = new Set([
  'v7-fixed-stop-structural-control-100bps',
  'v7-fixed-stop-structural-control-125bps',
]);

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function walk(dir, predicate, out = []) {
  if (!fs.existsSync(dir)) return out;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full, predicate, out);
    else if (!predicate || predicate(full)) out.push(full);
  }
  return out;
}

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = '';
  let quoted = false;
  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    const next = text[index + 1];
    if (quoted && char === '"' && next === '"') {
      field += '"';
      index += 1;
    } else if (char === '"') {
      quoted = !quoted;
    } else if (!quoted && char === ',') {
      row.push(field);
      field = '';
    } else if (!quoted && (char === '\n' || char === '\r')) {
      if (char === '\r' && next === '\n') index += 1;
      row.push(field);
      if (row.some((value) => value !== '')) rows.push(row);
      row = [];
      field = '';
    } else {
      field += char;
    }
  }
  if (field || row.length) {
    row.push(field);
    if (row.some((value) => value !== '')) rows.push(row);
  }
  if (!rows.length) return [];
  const headers = rows[0].map((header) => String(header || '').replace(/^\uFEFF/, '').trim());
  return rows.slice(1).map((values) => Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ''])));
}

function num(value) {
  if (value === null || value === undefined) return NaN;
  const cleaned = String(value)
    .replace(/\u2212/g, '-')
    .replace(/[‪‬]/g, '')
    .replace(/[$,%\s\u202f]/g, '')
    .replace(/,/g, '');
  if (!cleaned || cleaned === '-' || cleaned.toLowerCase() === 'nan') return NaN;
  const match = cleaned.match(/[+-]?\d+(?:\.\d+)?/);
  return match ? Number(match[0]) : NaN;
}

function finite(value, fallback = 0) {
  return Number.isFinite(value) ? value : fallback;
}

function nullable(value) {
  return Number.isFinite(value) ? value : null;
}

function fmt(value, digits = 2) {
  return Number.isFinite(value) ? value.toFixed(digits) : 'n/a';
}

function rel(file) {
  return file ? path.relative(repoRoot, file) : null;
}

function safePath(value, reportPath) {
  if (!value) return null;
  if (path.isAbsolute(value)) return value;
  const fromRepo = path.resolve(repoRoot, value);
  if (fs.existsSync(fromRepo)) return fromRepo;
  return path.resolve(path.dirname(reportPath), value);
}

function firstField(row, names) {
  for (const name of names) {
    if (row[name] !== undefined && row[name] !== '') return row[name];
  }
  return '';
}

function parseTradeTime(value) {
  const match = String(value || '').match(/^(\d{4})-(\d{2})-(\d{2})\s+(\d{2}):(\d{2})/);
  if (!match) return null;
  const [, year, month, day, hour, minute] = match;
  return new Date(Date.UTC(Number(year), Number(month) - 1, Number(day), Number(hour), Number(minute)));
}

function parseReportRange(textPath) {
  if (!textPath || !fs.existsSync(textPath)) return null;
  const text = fs.readFileSync(textPath, 'utf8');
  const match = text.match(/([A-Z][a-z]{2}\s+\d{1,2},\s+202\d)\s+—\s+([A-Z][a-z]{2}\s+\d{1,2},\s+202\d)/);
  if (!match) return null;
  const start = new Date(`${match[1]} 00:00:00 GMT`);
  const end = new Date(`${match[2]} 23:59:59 GMT`);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return null;
  return { label: match[0], start: start.toISOString(), end: end.toISOString() };
}

function systemLabel(variant) {
  if (variant === 'fixed_stop_structural_control_100bps') return 'Structural Control 100bps';
  if (variant === 'fixed_stop_structural_control_125bps') return 'Structural Control 125bps';
  return variant;
}

function parseEntrySignal(signal) {
  const text = String(signal || '');
  const sideMatch = text.match(/V7[A-Z]*-(L|S)-/);
  const valuePatterns = {
    riskPct: /-R(-?\d+(?:\.\d+)?|NaN)/,
    mssAge: /-M(-?\d+(?:\.\d+)?|NaN)/,
    alertAge: /-A(-?\d+(?:\.\d+)?|NaN)/,
    strengthAge: /-S(-?\d+(?:\.\d+)?|NaN)/,
    strengthSlope: /-SS(-?\d+(?:\.\d+)?|NaN)/,
    entryRiskBps: /-RB(-?\d+(?:\.\d+)?|NaN)/,
    atrBps: /-ATR(-?\d+(?:\.\d+)?|NaN)/,
    entryRangeAtr: /-DR(-?\d+(?:\.\d+)?|NaN)/,
    stopDistanceAtr: /-RA(-?\d+(?:\.\d+)?|NaN)/,
    minRiskFloorBps: /-MF(-?\d+(?:\.\d+)?|NaN)/,
    stopBufferBps: /-SB(-?\d+(?:\.\d+)?|NaN)/,
    tp1R: /-T1(-?\d+(?:\.\d+)?|NaN)/,
    stop: /-SL(-?\d+(?:\.\d+)?)/,
  };
  const values = {};
  for (const [name, pattern] of Object.entries(valuePatterns)) {
    const match = text.match(pattern);
    values[name] = match ? nullable(num(match[1])) : null;
  }
  const tpMatch = text.match(/-TP(-?\d+(?:\.\d+)?)\/(-?\d+(?:\.\d+)?)\/(-?\d+(?:\.\d+)?)/);
  return {
    side: sideMatch?.[1] === 'L' ? 'long' : sideMatch?.[1] === 'S' ? 'short' : 'unknown',
    tp1: tpMatch ? num(tpMatch[1]) : null,
    tp2: tpMatch ? num(tpMatch[2]) : null,
    tp3: tpMatch ? num(tpMatch[3]) : null,
    ...values,
  };
}

function classifyExit(exitRow, entryInfo) {
  const signal = String(exitRow.Signal || '');
  if (/Open/i.test(signal)) return 'open';
  if (/MAXHOLD/i.test(signal)) return 'max_hold';
  if (/CLOSESTOP/i.test(signal)) return 'close_stop';
  const price = num(exitRow['Price USDT']);
  if (!Number.isFinite(price) || !Number.isFinite(entryInfo.stop)) return 'unknown';
  const tolerance = Math.max(0.02, Math.abs(price) * 0.0015);
  if (Math.abs(price - entryInfo.stop) <= tolerance) return 'stop';
  for (const [name, target] of [['tp1', entryInfo.tp1], ['tp2', entryInfo.tp2], ['tp3', entryInfo.tp3]]) {
    if (Number.isFinite(target) && Math.abs(price - target) <= tolerance) return name;
  }
  return 'unknown';
}

function parentKey(row) {
  return [
    row['Trade #'] || row['Trade number'] || '',
    row.Type || '',
    row['Date and time'] || '',
    row.Signal || '',
    row['Price USDT'] || '',
  ].join('|');
}

function parentTrades(strategyFile) {
  const rows = parseCsv(fs.readFileSync(strategyFile, 'utf8'));
  const groups = new Map();
  for (let index = 0; index < rows.length; index += 1) {
    const row = rows[index];
    if (!/^Entry\b/i.test(row.Type || '')) continue;
    const key = parentKey(row);
    if (!groups.has(key)) groups.set(key, { entry: row, exits: [] });
    if (rows[index - 1] && /^Exit\b/i.test(rows[index - 1].Type || '')) {
      groups.get(key).exits.push(rows[index - 1]);
    }
  }
  return [...groups.values()].map((group) => {
    const info = parseEntrySignal(group.entry.Signal);
    const entryPrice = num(group.entry['Price USDT']);
    const entryTime = parseTradeTime(group.entry['Date and time']);
    const qty = group.exits.reduce((sum, row) => sum + finite(num(row?.['Size (qty)'])), 0);
    const riskDistance = info.side === 'long' ? entryPrice - info.stop : info.side === 'short' ? info.stop - entryPrice : NaN;
    const riskUsd = Number.isFinite(riskDistance) && riskDistance > 0 ? riskDistance * qty : NaN;
    const pnl = group.exits.reduce((sum, row) => sum + finite(num(firstField(row || {}, ['Net P&L USDT', 'Net PnL USDT']))), 0);
    const mfeUsd = group.exits.reduce((sum, row) => sum + finite(num(row?.['Favorable excursion USDT'])), 0);
    const maeUsd = group.exits.reduce((sum, row) => sum + finite(num(row?.['Adverse excursion USDT'])), 0);
    const exitEvents = group.exits
      .map((row) => ({ row, event: classifyExit(row || {}, info) }))
      .filter((event) => event.row);
    const firstClosedEvent = exitEvents.find((event) => event.event !== 'open') || null;
    const openEvent = exitEvents.find((event) => event.event === 'open') || null;
    return {
      entryTime: entryTime ? entryTime.toISOString() : null,
      entryDate: group.entry['Date and time'],
      entryPrice,
      pnl,
      mfeR: Number.isFinite(riskUsd) && riskUsd > 0 ? mfeUsd / riskUsd : null,
      maeR: Number.isFinite(riskUsd) && riskUsd > 0 ? maeUsd / riskUsd : null,
      firstEvent: firstClosedEvent?.event || (openEvent ? 'open' : 'unknown'),
      hasOpenExit: Boolean(openEvent),
      exitCount: group.exits.length,
      ...info,
    };
  });
}

function average(values) {
  const clean = values.filter(Number.isFinite);
  return clean.length ? clean.reduce((sum, value) => sum + value, 0) / clean.length : null;
}

function pct(count, total) {
  return total ? count / total * 100 : null;
}

function groupBy(items, keyFn) {
  const groups = new Map();
  for (const item of items) {
    const key = keyFn(item);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(item);
  }
  return groups;
}

function classifyWindow(parent, range) {
  const time = parent.entryTime ? Date.parse(parent.entryTime) : NaN;
  const start = range?.start ? Date.parse(range.start) : NaN;
  const end = range?.end ? Date.parse(range.end) : NaN;
  if (!Number.isFinite(time) || !Number.isFinite(start) || !Number.isFinite(end) || end <= start) return 'unknown';
  const third = (end - start) / 3;
  if (time < start + third) return 'early';
  if (time < start + third * 2) return 'middle';
  return 'latest';
}

function reportFromParents(parents) {
  const ordered = [...parents].sort((a, b) => Date.parse(a.entryTime || '') - Date.parse(b.entryTime || ''));
  let equity = initialCapital;
  let peak = initialCapital;
  let maxDrawdownPct = 0;
  for (const parent of ordered) {
    equity += finite(parent.pnl);
    peak = Math.max(peak, equity);
    maxDrawdownPct = Math.max(maxDrawdownPct, peak > 0 ? (peak - equity) / peak * 100 : 0);
  }
  const pnlValues = parents.map((parent) => finite(parent.pnl));
  const grossProfit = pnlValues.filter((value) => value > 0).reduce((sum, value) => sum + value, 0);
  const grossLoss = Math.abs(pnlValues.filter((value) => value < 0).reduce((sum, value) => sum + value, 0));
  const winningTrades = pnlValues.filter((value) => value > 0).length;
  const losingTrades = pnlValues.filter((value) => value < 0).length;
  const totalTrades = parents.length;
  return {
    totalPnl: pnlValues.reduce((sum, value) => sum + value, 0),
    grossProfit,
    grossLoss,
    profitFactor: grossLoss > 0 ? grossProfit / grossLoss : grossProfit > 0 ? null : 0,
    totalTrades,
    winningTrades,
    losingTrades,
    winRatePct: totalTrades ? winningTrades / totalTrades * 100 : null,
    maxDrawdownPct,
    positiveTrades: winningTrades,
    negativeTrades: losingTrades,
    tp1FirstPct: pct(parents.filter((item) => /^tp/.test(item.firstEvent)).length, totalTrades),
    stopFirstPct: pct(parents.filter((item) => item.firstEvent === 'stop' || item.firstEvent === 'close_stop').length, totalTrades),
    maxHoldPct: pct(parents.filter((item) => item.firstEvent === 'max_hold').length, totalTrades),
    avgMfeR: average(parents.map((item) => item.mfeR)),
    avgMaeR: average(parents.map((item) => item.maeR)),
    avgRiskBps: average(parents.map((item) => item.entryRiskBps)),
    avgStopDistanceAtr: average(parents.map((item) => item.stopDistanceAtr)),
  };
}

function readSelectedReports() {
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  const runMeta = new Map(manifest.runs.filter((run) => controlRunIds.has(run.id)).map((run) => [run.id, run]));
  const selected = new Map();
  const rejected = [];
  for (const reportPath of walk(automationDir, (file) => path.basename(file) === 'pine-text-matrix-report.json')) {
    let report;
    try {
      report = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
    } catch (error) {
      rejected.push({ reportPath: rel(reportPath), reason: error.message });
      continue;
    }
    const run = runMeta.get(report.runId);
    if (!run) continue;
    for (const result of report.results || []) {
      if (result.status !== 'ok') continue;
      const strategyFile = safePath(result.strategyData?.path, reportPath);
      const textPath = safePath(result.textPath, reportPath);
      if (!strategyFile || !fs.existsSync(strategyFile)) {
        rejected.push({ reportPath: rel(reportPath), runId: report.runId, symbol: result.symbol, timeframe: result.label, reason: 'missing strategy csv' });
        continue;
      }
      const key = [report.runId, result.symbol, result.label].join('|');
      const mtimeMs = fs.statSync(strategyFile).mtimeMs;
      const candidate = { reportPath, report, run, result, strategyFile, textPath, mtimeMs };
      const previous = selected.get(key);
      if (!previous || candidate.mtimeMs > previous.mtimeMs) selected.set(key, candidate);
    }
  }
  return { manifest, runMeta, selected, rejected };
}

function buildRows() {
  const { runMeta, selected, rejected } = readSelectedReports();
  const rows = [];
  const missing = [];
  for (const run of runMeta.values()) {
    for (const symbol of run.symbols || []) {
      for (const timeframe of run.timeframes || []) {
        const key = [run.id, symbol, timeframe.label].join('|');
        const item = selected.get(key);
        if (!item) {
          missing.push({ runId: run.id, system: systemLabel(run.variant), symbol, timeframe: timeframe.label });
          continue;
        }
        const reportRange = parseReportRange(item.textPath);
        const parents = parentTrades(item.strategyFile).map((parent) => ({
          ...parent,
          runId: run.id,
          system: systemLabel(run.variant),
          variant: run.variant,
          symbol,
          timeframe: timeframe.label,
          window: classifyWindow(parent, reportRange),
        }));
        rows.push({
          runId: run.id,
          system: systemLabel(run.variant),
          variant: run.variant,
          symbol,
          timeframe: timeframe.label,
          interval: timeframe.interval,
          reportRange,
          sourceFile: rel(item.strategyFile),
          textPath: rel(item.textPath),
          reportPath: rel(item.reportPath),
          parents,
          summary: reportFromParents(parents),
        });
      }
    }
  }
  return { rows, missing, rejected };
}

function summarizeGroup(parents, fields) {
  return { ...fields, ...reportFromParents(parents) };
}

function byKey(parents, keyFn, fieldsFn) {
  return [...groupBy(parents, keyFn).entries()].map(([key, group]) => summarizeGroup(group, fieldsFn(key, group)));
}

function aggregate(rows) {
  const parents = rows.flatMap((row) => row.parents);
  const basket = byKey(
    parents,
    (item) => item.system,
    (system) => ({ system, scope: 'all_symbols_all_timeframes' }),
  );
  const windows = byKey(
    parents,
    (item) => [item.system, item.window].join('|'),
    (key) => {
      const [system, window] = key.split('|');
      return { system, window, scope: 'all_symbols_all_timeframes' };
    },
  ).sort((a, b) => `${a.system}-${a.window}`.localeCompare(`${b.system}-${b.window}`));
  const windowSymbols = byKey(
    parents,
    (item) => [item.system, item.window, item.symbol].join('|'),
    (key) => {
      const [system, window, symbol] = key.split('|');
      return { system, window, symbol };
    },
  );
  const windowTimeframes = byKey(
    parents,
    (item) => [item.system, item.window, item.timeframe].join('|'),
    (key) => {
      const [system, window, timeframe] = key.split('|');
      return { system, window, timeframe };
    },
  );
  const windowSides = byKey(
    parents,
    (item) => [item.system, item.window, item.side].join('|'),
    (key) => {
      const [system, window, side] = key.split('|');
      return { system, window, side };
    },
  );
  const slots = rows.map((row) => ({
    system: row.system,
    symbol: row.symbol,
    timeframe: row.timeframe,
    reportRange: row.reportRange,
    sourceFile: row.sourceFile,
    ...row.summary,
  }));
  const candidateParents = parents.filter((item) => item.system === 'Structural Control 125bps');
  const symbolScopes = [
    ['All symbols', (item) => true],
    ['BTC+ETH only', (item) => item.symbol !== 'BINANCE:ZECUSDT'],
    ['ETH+ZEC only', (item) => item.symbol !== 'BINANCE:BTCUSDT'],
    ['ZEC only', (item) => item.symbol === 'BINANCE:ZECUSDT'],
    ['BTC only', (item) => item.symbol === 'BINANCE:BTCUSDT'],
    ['ETH only', (item) => item.symbol === 'BINANCE:ETHUSDT'],
  ].map(([scope, predicate]) => summarizeGroup(candidateParents.filter(predicate), { system: 'Structural Control 125bps', scope }));
  const timeframeScopes = [
    ['15m+5m', (item) => true],
    ['15m only', (item) => item.timeframe === '15m'],
    ['5m only', (item) => item.timeframe === '5m'],
  ].map(([scope, predicate]) => summarizeGroup(candidateParents.filter(predicate), { system: 'Structural Control 125bps', scope }));
  return { parents, basket, windows, windowSymbols, windowTimeframes, windowSides, slots, symbolScopes, timeframeScopes };
}

function evaluate(aggregateResult) {
  const candidate = aggregateResult.basket.find((item) => item.system === 'Structural Control 125bps');
  const candidateWindows = aggregateResult.windows.filter((item) => item.system === 'Structural Control 125bps');
  const latest = candidateWindows.find((item) => item.window === 'latest');
  const earlyMiddle = candidateWindows.filter((item) => item.window !== 'latest');
  const btcEth = aggregateResult.symbolScopes.find((item) => item.scope === 'BTC+ETH only');
  const zec = aggregateResult.symbolScopes.find((item) => item.scope === 'ZEC only');
  const flags = [];
  if (!candidate || finite(candidate.profitFactor) < 1.2) {
    flags.push('Full-history PF is below 1.20.');
  }
  if (latest && earlyMiddle.length && earlyMiddle.every((item) => finite(item.totalPnl) <= 0)) {
    flags.push('Latest window is the only profitable window.');
  }
  if (latest && earlyMiddle.some((item) => finite(item.maxDrawdownPct) > Math.max(5, finite(latest.maxDrawdownPct) + 2))) {
    flags.push('Drawdown expands materially outside the latest window.');
  }
  if (candidate && btcEth && zec) {
    const zecShare = Math.abs(finite(zec.totalPnl)) / Math.max(1, Math.abs(finite(candidate.totalPnl)));
    if (zecShare >= 0.75 && (finite(btcEth.profitFactor) < 1.2 || finite(btcEth.totalPnl) <= 0)) {
      flags.push('ZEC explains most of the edge while BTC+ETH are weak.');
    }
  }
  const strongCandidate = candidate
    && finite(candidate.profitFactor) >= 1.35
    && finite(candidate.maxDrawdownPct) <= 5
    && flags.length === 0;
  return {
    strongCandidate,
    flags,
    recommendation: strongCandidate
      ? 'Implement 125bps structural V7.'
      : 'Reject broad 125bps V7 as overfit/symbol-concentrated; keep only as symbol-scoped diagnostic unless a follow-up proves non-ZEC robustness.',
  };
}

function table(lines, headers, rows, rowFn) {
  lines.push(`| ${headers.join(' | ')} |`);
  lines.push(`| ${headers.map((header) => header.match(/%|P&L|PF|DD|Trades|Rows/) ? '---:' : '---').join(' | ')} |`);
  for (const row of rows) lines.push(`| ${rowFn(row).join(' | ')} |`);
}

function metricCells(row) {
  return [
    fmt(row.totalTrades, 0),
    fmt(row.totalPnl),
    fmt(row.profitFactor, 3),
    fmt(row.winRatePct, 1),
    fmt(row.maxDrawdownPct, 2),
  ];
}

function markdown(data) {
  const { rows, missing, rejected, aggregateResult, verdict } = data;
  const lines = ['# V7 Robustness Verdict Metrics', ''];
  lines.push(`Generated from ${rows.length} selected structural-control Strategy Tester exports. Expected slots: 12. Missing: ${missing.length}. Rejected candidates: ${rejected.length}.`);
  lines.push('');
  lines.push('## Source Ranges');
  lines.push('');
  table(lines, ['System', 'Symbol', 'TF', 'Report range', 'Trades', 'P&L', 'PF', 'Win %', 'DD %'], aggregateResult.slots, (row) => [
    row.system,
    row.symbol.replace('BINANCE:', ''),
    row.timeframe,
    row.reportRange?.label || 'n/a',
    ...metricCells(row),
  ]);
  lines.push('');
  lines.push('## Full-History Control Check');
  lines.push('');
  table(lines, ['System', 'Trades', 'P&L', 'PF', 'Win %', 'DD %', 'TP1 first %', 'Stop first %'], aggregateResult.basket, (row) => [
    row.system,
    fmt(row.totalTrades, 0),
    fmt(row.totalPnl),
    fmt(row.profitFactor, 3),
    fmt(row.winRatePct, 1),
    fmt(row.maxDrawdownPct, 2),
    fmt(row.tp1FirstPct, 1),
    fmt(row.stopFirstPct, 1),
  ]);
  lines.push('');
  lines.push('## Windowed Robustness');
  lines.push('');
  lines.push('Windows are calendar thirds of each symbol/timeframe report range, then basketed by relative window. 15m reports cover Oct 31, 2025 to May 28, 2026; 5m reports cover Mar 15, 2026 to May 28, 2026.');
  lines.push('');
  table(lines, ['System', 'Window', 'Trades', 'P&L', 'PF', 'Win %', 'DD %'], aggregateResult.windows, (row) => [
    row.system,
    row.window,
    ...metricCells(row),
  ]);
  lines.push('');
  lines.push('## Candidate Symbol Windows');
  lines.push('');
  table(
    lines,
    ['Window', 'Symbol', 'Trades', 'P&L', 'PF', 'Win %', 'DD %'],
    aggregateResult.windowSymbols.filter((row) => row.system === 'Structural Control 125bps').sort((a, b) => `${a.window}-${a.symbol}`.localeCompare(`${b.window}-${b.symbol}`)),
    (row) => [row.window, row.symbol.replace('BINANCE:', ''), ...metricCells(row)],
  );
  lines.push('');
  lines.push('## Candidate Timeframe Windows');
  lines.push('');
  table(
    lines,
    ['Window', 'TF', 'Trades', 'P&L', 'PF', 'Win %', 'DD %'],
    aggregateResult.windowTimeframes.filter((row) => row.system === 'Structural Control 125bps').sort((a, b) => `${a.window}-${a.timeframe}`.localeCompare(`${b.window}-${b.timeframe}`)),
    (row) => [row.window, row.timeframe, ...metricCells(row)],
  );
  lines.push('');
  lines.push('## Candidate Long/Short Windows');
  lines.push('');
  table(
    lines,
    ['Window', 'Side', 'Trades', 'P&L', 'PF', 'Win %', 'DD %'],
    aggregateResult.windowSides.filter((row) => row.system === 'Structural Control 125bps').sort((a, b) => `${a.window}-${a.side}`.localeCompare(`${b.window}-${b.side}`)),
    (row) => [row.window, row.side, ...metricCells(row)],
  );
  lines.push('');
  lines.push('## Symbol-Scope Test');
  lines.push('');
  table(lines, ['Scope', 'Trades', 'P&L', 'PF', 'Win %', 'DD %'], aggregateResult.symbolScopes, (row) => [
    row.scope,
    ...metricCells(row),
  ]);
  lines.push('');
  lines.push('## Timeframe Contribution Test');
  lines.push('');
  table(lines, ['Scope', 'Trades', 'P&L', 'PF', 'Win %', 'DD %'], aggregateResult.timeframeScopes, (row) => [
    row.scope,
    ...metricCells(row),
  ]);
  lines.push('');
  lines.push('## Overfit Sanity Verdict');
  lines.push('');
  if (verdict.flags.length) {
    lines.push('Fail / conditional. Abort further refinement optimization from this pass.');
    lines.push('');
    for (const flag of verdict.flags) lines.push(`- ${flag}`);
  } else {
    lines.push('Pass. No abort flags triggered.');
  }
  lines.push('');
  lines.push(`Recommendation: ${verdict.recommendation}`);
  return `${lines.join('\n')}\n`;
}

const { rows, missing, rejected } = buildRows();
const aggregateResult = aggregate(rows);
const verdict = evaluate(aggregateResult);
ensureDir(outputDir);
ensureDir(telemetryDir);
fs.writeFileSync(path.join(telemetryDir, 'robustness_verdict_metrics.json'), JSON.stringify({
  generatedAt: new Date().toISOString(),
  manifestPath: rel(manifestPath),
  automationDir: rel(automationDir),
  initialCapital,
  rows: rows.map(({ parents, ...row }) => row),
  missing,
  rejected,
  aggregate: aggregateResult,
  verdict,
}, null, 2));
fs.writeFileSync(path.join(outputDir, 'robustness_verdict_metrics.md'), markdown({ rows, missing, rejected, aggregateResult, verdict }));
console.log(JSON.stringify({
  outputDir,
  telemetryPath: path.join(telemetryDir, 'robustness_verdict_metrics.json'),
  selectedSlots: rows.length,
  missingSlots: missing.length,
  rejectedCandidates: rejected.length,
  verdict,
}, null, 2));
