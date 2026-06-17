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
const manifestPath = path.resolve(repoRoot, args.manifest || 'tradingview/strategy/artifacts/v7_symbol_scope_expansion/tv_symbol_scope_expansion_runs.json');
const automationDir = path.resolve(repoRoot, args.automationDir || 'tradingview/strategy/artifacts/v7_symbol_scope_expansion/tradingview/automation');
const outputDir = path.resolve(repoRoot, args.output || 'tradingview/strategy/artifacts/v7_symbol_scope_expansion');
const telemetryDir = path.resolve(repoRoot, args.telemetryDir || 'tradingview/strategy/.telemetry/outputs/v7_symbol_scope_expansion');
const initialCapital = Number(args.initialCapital || 10000);
const runId = args.run || 'v7-symbol-scope-expansion-125bps';
const originalSymbols = new Set(['BINANCE:BTCUSDT', 'BINANCE:ETHUSDT', 'BINANCE:ZECUSDT']);
const baseline = {
  zecPf: 2.458,
  zecDdPct: 2.92,
};

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

function rel(file) {
  return file ? path.relative(repoRoot, file) : null;
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

function shortSymbol(symbol) {
  return symbol.replace('BINANCE:', '').replace('USDT', '');
}

function rangeLabel(range) {
  return range?.label ? range.label.replace(/\s+—\s+/, ' to ') : 'n/a';
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

function parseEntrySignal(signal) {
  const text = String(signal || '');
  const sideMatch = text.match(/V7[A-Z]*-(L|S)-/);
  const patterns = {
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
  for (const [name, pattern] of Object.entries(patterns)) {
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
  const run = manifest.runs.find((item) => item.id === runId);
  if (!run) throw new Error(`Missing run ${runId} in ${manifestPath}`);
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
    if (report.runId !== runId) continue;
    for (const result of report.results || []) {
      if (result.status !== 'ok') {
        rejected.push({ reportPath: rel(reportPath), runId, symbol: result.symbol, timeframe: result.label, reason: `status:${result.status}` });
        continue;
      }
      const strategyFile = safePath(result.strategyData?.path, reportPath);
      const textPath = safePath(result.textPath, reportPath);
      if (!strategyFile || !fs.existsSync(strategyFile)) {
        rejected.push({ reportPath: rel(reportPath), runId, symbol: result.symbol, timeframe: result.label, reason: 'missing strategy csv' });
        continue;
      }
      const key = [result.symbol, result.label].join('|');
      const mtimeMs = fs.statSync(strategyFile).mtimeMs;
      const candidate = { reportPath, report, run, result, strategyFile, textPath, mtimeMs };
      const previous = selected.get(key);
      if (!previous || candidate.mtimeMs > previous.mtimeMs) selected.set(key, candidate);
    }
  }
  return { manifest, run, selected, rejected };
}

function buildRows() {
  const { run, selected, rejected } = readSelectedReports();
  const rows = [];
  const missing = [];
  for (const symbol of run.symbols || []) {
    for (const timeframe of run.timeframes || []) {
      const key = [symbol, timeframe.label].join('|');
      const item = selected.get(key);
      if (!item) {
        missing.push({ runId, symbol, timeframe: timeframe.label });
        continue;
      }
      const reportRange = parseReportRange(item.textPath);
      const parents = parentTrades(item.strategyFile).map((parent) => ({
        ...parent,
        runId,
        symbol,
        timeframe: timeframe.label,
        window: classifyWindow(parent, reportRange),
      }));
      rows.push({
        runId,
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
  return { rows, missing, rejected };
}

function summarizeGroup(parents, fields) {
  return { ...fields, ...reportFromParents(parents) };
}

function aggregateBy(parents, keyFn, fieldsFn) {
  return [...groupBy(parents, keyFn).entries()].map(([key, group]) => summarizeGroup(group, fieldsFn(key, group)));
}

function classifySymbol(summary, windows) {
  const nonLatest = windows.filter((row) => row.window !== 'latest');
  const stableOutsideLatest = nonLatest.some((row) => finite(row.totalPnl) > 0) && !nonLatest.every((row) => finite(row.totalPnl) <= 0);
  const latestOnly = finite(summary.totalPnl) > 0 && nonLatest.every((row) => finite(row.totalPnl) <= 0);
  if (finite(summary.profitFactor) >= 1.35 && finite(summary.maxDrawdownPct) <= 5 && finite(summary.totalTrades) >= 10 && stableOutsideLatest) {
    return 'pass';
  }
  if (finite(summary.profitFactor) >= 1.2 && finite(summary.maxDrawdownPct) <= 6 && finite(summary.totalTrades) >= 8 && !latestOnly) {
    return 'marginal';
  }
  if (finite(summary.profitFactor) >= 1.35 && finite(summary.totalTrades) < 10) {
    return 'diagnostic-only';
  }
  return 'fail';
}

function aggregate(rows) {
  const parents = rows.flatMap((row) => row.parents);
  const slots = rows.map((row) => ({
    symbol: row.symbol,
    timeframe: row.timeframe,
    reportRange: row.reportRange,
    sourceFile: row.sourceFile,
    ...row.summary,
  }));
  const basket = summarizeGroup(parents, { scope: 'all_symbols_all_timeframes' });
  const symbolRows = aggregateBy(
    parents,
    (item) => item.symbol,
    (symbol) => ({ symbol, cohort: originalSymbols.has(symbol) ? 'original' : 'expansion' }),
  ).sort((a, b) => shortSymbol(a.symbol).localeCompare(shortSymbol(b.symbol)));
  const windowRows = aggregateBy(
    parents,
    (item) => [item.symbol, item.window].join('|'),
    (key) => {
      const [symbol, window] = key.split('|');
      return { symbol, window, cohort: originalSymbols.has(symbol) ? 'original' : 'expansion' };
    },
  ).sort((a, b) => `${shortSymbol(a.symbol)}-${a.window}`.localeCompare(`${shortSymbol(b.symbol)}-${b.window}`));
  const timeframeRows = aggregateBy(
    parents,
    (item) => [item.symbol, item.timeframe].join('|'),
    (key) => {
      const [symbol, timeframe] = key.split('|');
      return { symbol, timeframe, cohort: originalSymbols.has(symbol) ? 'original' : 'expansion' };
    },
  ).sort((a, b) => `${shortSymbol(a.symbol)}-${a.timeframe}`.localeCompare(`${shortSymbol(b.symbol)}-${b.timeframe}`));
  const sideRows = aggregateBy(
    parents,
    (item) => [item.symbol, item.side].join('|'),
    (key) => {
      const [symbol, side] = key.split('|');
      return { symbol, side, cohort: originalSymbols.has(symbol) ? 'original' : 'expansion' };
    },
  ).sort((a, b) => `${shortSymbol(a.symbol)}-${a.side}`.localeCompare(`${shortSymbol(b.symbol)}-${b.side}`));
  const symbolClassifications = symbolRows.map((summary) => {
    const windows = windowRows.filter((row) => row.symbol === summary.symbol);
    const classification = classifySymbol(summary, windows);
    return { ...summary, classification };
  });
  const addedPasses = symbolClassifications.filter((row) => row.cohort === 'expansion' && row.classification === 'pass');
  const addedMarginals = symbolClassifications.filter((row) => row.cohort === 'expansion' && row.classification === 'marginal');
  const admittedSymbols = new Set(symbolClassifications.filter((row) => row.classification === 'pass').map((row) => row.symbol));
  const marginalSymbols = new Set(symbolClassifications.filter((row) => row.classification === 'marginal').map((row) => row.symbol));
  const scopeRows = [
    ['All symbols', (item) => true],
    ['Original BTC/ETH/ZEC', (item) => originalSymbols.has(item.symbol)],
    ['Expansion symbols', (item) => !originalSymbols.has(item.symbol)],
    ['Admitted pass symbols', (item) => admittedSymbols.has(item.symbol)],
    ['Marginal symbols', (item) => marginalSymbols.has(item.symbol)],
    ['Failed symbols', (item) => !admittedSymbols.has(item.symbol) && !marginalSymbols.has(item.symbol)],
  ].map(([scope, predicate]) => summarizeGroup(parents.filter(predicate), { scope }));
  const zec = symbolClassifications.find((row) => row.symbol === 'BINANCE:ZECUSDT');
  const zecProtected = zec
    && (finite(zec.profitFactor) >= 2.0 || finite(zec.profitFactor) >= baseline.zecPf * 0.85)
    && finite(zec.maxDrawdownPct) <= 3.5;
  const verdict = {
    addedPasses: addedPasses.map((row) => shortSymbol(row.symbol)),
    addedMarginals: addedMarginals.map((row) => shortSymbol(row.symbol)),
    zecProtected,
    broadCandidate: addedPasses.length >= 2 && zecProtected,
    btcOutlier: Boolean(addedPasses.length >= 2 && symbolClassifications.find((row) => row.symbol === 'BINANCE:BTCUSDT')?.classification === 'fail'),
    zecOutlier: addedPasses.length === 0 && Boolean(zecProtected),
  };
  verdict.label = verdict.broadCandidate
    ? 'symbol-admission model'
    : verdict.zecOutlier
      ? 'ZEC outlier'
      : addedPasses.length || addedMarginals.length
        ? 'limited symbol-admission diagnostic'
        : 'reject broad V7';
  verdict.recommendation = verdict.broadCandidate
    ? 'Proceed to a symbol-admission implementation test, preserving ZEC and admitting only independently passing symbols.'
    : verdict.zecOutlier
      ? 'Do not broaden V7 yet; treat ZEC as the only implementation-grade symbol and keep other coins diagnostic.'
      : 'Do not implement broad V7 yet; use passing or marginal expansion symbols only for a focused follow-up diagnostic.';
  return { parents, slots, basket, scopeRows, symbolRows, windowRows, timeframeRows, sideRows, symbolClassifications, verdict };
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

function table(lines, headers, rows, rowFn) {
  lines.push(`| ${headers.join(' | ')} |`);
  lines.push(`| ${headers.map((header) => header.match(/%|P&L|PF|DD|Trades|Rows/) ? '---:' : '---').join(' | ')} |`);
  for (const row of rows) lines.push(`| ${rowFn(row).join(' | ')} |`);
}

function markdown(rows, missing, rejected, aggregateResult) {
  const lines = ['# V7 Symbol Scope Expansion Metrics', ''];
  lines.push(`Generated from ${rows.length} selected Strategy Tester exports. Expected slots: 20. Missing: ${missing.length}. Rejected candidates: ${rejected.length}.`);
  lines.push('');
  lines.push('## Coverage');
  table(lines, ['Expected slots', 'Selected slots', 'Missing', 'Rejected'], [{ expected: 20, selected: rows.length, missing: missing.length, rejected: rejected.length }], (row) => [
    row.expected,
    row.selected,
    row.missing,
    row.rejected,
  ]);
  lines.push('');
  lines.push('## Source Ranges');
  table(lines, ['Symbol', 'TF', 'Report range', 'Trades', 'P&L', 'PF', 'Win %', 'DD %'], aggregateResult.slots, (row) => [
    shortSymbol(row.symbol),
    row.timeframe,
    rangeLabel(row.reportRange),
    ...metricCells(row),
  ]);
  lines.push('');
  lines.push('## Symbol Classification');
  table(lines, ['Symbol', 'Cohort', 'Class', 'Trades', 'P&L', 'PF', 'Win %', 'DD %', 'TP1 first %', 'Stop first %'], aggregateResult.symbolClassifications, (row) => [
    shortSymbol(row.symbol),
    row.cohort,
    row.classification,
    fmt(row.totalTrades, 0),
    fmt(row.totalPnl),
    fmt(row.profitFactor, 3),
    fmt(row.winRatePct, 1),
    fmt(row.maxDrawdownPct, 2),
    fmt(row.tp1FirstPct, 1),
    fmt(row.stopFirstPct, 1),
  ]);
  lines.push('');
  lines.push('## Scope Summary');
  table(lines, ['Scope', 'Trades', 'P&L', 'PF', 'Win %', 'DD %'], aggregateResult.scopeRows, (row) => [
    row.scope,
    ...metricCells(row),
  ]);
  lines.push('');
  lines.push('## Windowed Robustness');
  table(lines, ['Symbol', 'Window', 'Trades', 'P&L', 'PF', 'Win %', 'DD %'], aggregateResult.windowRows, (row) => [
    shortSymbol(row.symbol),
    row.window,
    ...metricCells(row),
  ]);
  lines.push('');
  lines.push('## Timeframe Contribution');
  table(lines, ['Symbol', 'TF', 'Trades', 'P&L', 'PF', 'Win %', 'DD %'], aggregateResult.timeframeRows, (row) => [
    shortSymbol(row.symbol),
    row.timeframe,
    ...metricCells(row),
  ]);
  lines.push('');
  lines.push('## Directional Contribution');
  table(lines, ['Symbol', 'Side', 'Trades', 'P&L', 'PF', 'Win %', 'DD %'], aggregateResult.sideRows, (row) => [
    shortSymbol(row.symbol),
    row.side,
    ...metricCells(row),
  ]);
  lines.push('');
  lines.push('## Verdict Inputs');
  lines.push('');
  lines.push(`- Label: ${aggregateResult.verdict.label}`);
  lines.push(`- Added passes: ${aggregateResult.verdict.addedPasses.length ? aggregateResult.verdict.addedPasses.join(', ') : 'none'}`);
  lines.push(`- Added marginals: ${aggregateResult.verdict.addedMarginals.length ? aggregateResult.verdict.addedMarginals.join(', ') : 'none'}`);
  lines.push(`- ZEC profit-protection passed: ${aggregateResult.verdict.zecProtected ? 'yes' : 'no'}`);
  lines.push(`- Recommendation: ${aggregateResult.verdict.recommendation}`);
  return `${lines.join('\n')}\n`;
}

const { rows, missing, rejected } = buildRows();
const aggregateResult = aggregate(rows);
ensureDir(outputDir);
ensureDir(telemetryDir);
fs.writeFileSync(path.join(telemetryDir, 'symbol_scope_expansion_metrics.json'), JSON.stringify({
  generatedAt: new Date().toISOString(),
  manifestPath: rel(manifestPath),
  automationDir: rel(automationDir),
  initialCapital,
  runId,
  rows: rows.map(({ parents, ...row }) => row),
  missing,
  rejected,
  aggregate: aggregateResult,
}, null, 2));
fs.writeFileSync(path.join(outputDir, 'symbol_scope_expansion_metrics.md'), markdown(rows, missing, rejected, aggregateResult));
console.log(JSON.stringify({
  outputDir,
  telemetryPath: path.join(telemetryDir, 'symbol_scope_expansion_metrics.json'),
  selectedSlots: rows.length,
  missingSlots: missing.length,
  rejectedCandidates: rejected.length,
  verdict: aggregateResult.verdict,
}, null, 2));
