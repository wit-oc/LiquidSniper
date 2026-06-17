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
const manifestPath = path.resolve(repoRoot, args.manifest || 'tradingview/strategy/artifacts/v7_liquidity_scope_sanity/tv_liquidity_scope_sanity_runs.json');
const automationDir = path.resolve(repoRoot, args.automationDir || 'tradingview/strategy/artifacts/v7_liquidity_scope_sanity/tradingview/automation');
const outputDir = path.resolve(repoRoot, args.output || 'tradingview/strategy/artifacts/v7_liquidity_scope_sanity');
const telemetryDir = path.resolve(repoRoot, args.telemetryDir || 'tradingview/strategy/.telemetry/outputs/v7_liquidity_scope_sanity');
const initialCapital = Number(args.initialCapital || 10000);
const runId = args.run || 'v7-liquidity-scope-sanity-125bps';
const fallbackMetadata = {
  'BINANCE:BTCUSDT': { asset: 'BTC', regimeTier: 'prior failed control', liquidityTier: 'major', priorOutcome: 'fail' },
  'BINANCE:ETHUSDT': { asset: 'ETH', regimeTier: 'major control', liquidityTier: 'major', priorOutcome: 'diagnostic-only' },
  'BINANCE:ZECUSDT': { asset: 'ZEC', regimeTier: 'prior admitted control', liquidityTier: 'mid', priorOutcome: 'pass' },
  'BINANCE:ADAUSDT': { asset: 'ADA', regimeTier: 'prior admitted control', liquidityTier: 'mid', priorOutcome: 'pass' },
  'BINANCE:LINKUSDT': { asset: 'LINK', regimeTier: 'prior admitted control', liquidityTier: 'mid', priorOutcome: 'pass' },
  'BINANCE:XRPUSDT': { asset: 'XRP', regimeTier: 'prior admitted control', liquidityTier: 'major', priorOutcome: 'pass' },
  'BINANCE:SOLUSDT': { asset: 'SOL', regimeTier: 'prior failed control', liquidityTier: 'major', priorOutcome: 'fail' },
  'BINANCE:BNBUSDT': { asset: 'BNB', regimeTier: 'prior failed control', liquidityTier: 'major', priorOutcome: 'fail' },
  'BINANCE:DOGEUSDT': { asset: 'DOGE', regimeTier: 'prior failed control', liquidityTier: 'major', priorOutcome: 'fail' },
  'BINANCE:LTCUSDT': { asset: 'LTC', regimeTier: 'major control', liquidityTier: 'major', priorOutcome: 'marginal' },
};
const baseline = {
  zecPf: 2.458,
  zecDdPct: 2.92,
  admittedBasketPf: 2.055,
  admittedBasketDdPct: 3.60,
  universalBasketPf: 1.305,
  universalBasketDdPct: 13.10,
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

function pfValue(row) {
  if (Number.isFinite(row.profitFactor)) return row.profitFactor;
  if (finite(row.grossProfit) > 0 && finite(row.grossLoss) === 0) return Infinity;
  return 0;
}

function shortSymbol(symbol) {
  return symbol.replace('BINANCE:', '').replace('USDT', '');
}

function assetLabel(symbol, metadata = {}) {
  return metadata[symbol]?.asset || shortSymbol(symbol).replace(/\.P$/, '');
}

function symbolMeta(symbol, metadata = {}) {
  return {
    asset: assetLabel(symbol, metadata),
    regimeTier: metadata[symbol]?.regimeTier || 'smaller/reflexive',
    liquidityTier: metadata[symbol]?.liquidityTier || 'smaller/reflexive',
    priorOutcome: metadata[symbol]?.priorOutcome || 'new',
    aliasGroup: metadata[symbol]?.aliasGroup || '',
  };
}

function rangeLabel(range) {
  return range?.label ? range.label.replace(/\s+—\s+/, ' to ') : 'n/a';
}

function safePath(value, reportPath) {
  if (!value) return null;
  if (path.isAbsolute(value)) {
    if (fs.existsSync(value)) return value;
    const relocated = value.replace(
      '/tradingview/strategy/artifacts/v7_symbol_scope_expansion/tradingview/automation/',
      '/tradingview/strategy/artifacts/v7_liquidity_scope_sanity/tradingview/automation/',
    );
    return fs.existsSync(relocated) ? relocated : value;
  }
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
  const metadata = { ...fallbackMetadata, ...(run.symbolMetadata || {}) };
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
      const strategyFile = safePath(result.strategyData?.path, reportPath);
      const textPath = safePath(result.textPath, reportPath);
      const key = [result.symbol, result.label].join('|');
      const existingPath = strategyFile && fs.existsSync(strategyFile) ? strategyFile : textPath && fs.existsSync(textPath) ? textPath : reportPath;
      const mtimeMs = fs.statSync(existingPath).mtimeMs;
      const candidate = { reportPath, report, run, result, strategyFile, textPath, mtimeMs };
      const previous = selected.get(key);
      if (!previous || candidate.mtimeMs > previous.mtimeMs) selected.set(key, candidate);
    }
  }
  return { manifest, run, metadata, selected, rejected };
}

function buildRows() {
  const { run, metadata, selected, rejected } = readSelectedReports();
  const rows = [];
  const missing = [];
  const failed = [];
  for (const symbol of run.symbols || []) {
    for (const timeframe of run.timeframes || []) {
      const key = [symbol, timeframe.label].join('|');
      const item = selected.get(key);
      const meta = symbolMeta(symbol, metadata);
      if (!item) {
        missing.push({ runId, symbol, timeframe: timeframe.label });
        rows.push({
          runId,
          symbol,
          timeframe: timeframe.label,
          interval: timeframe.interval,
          reportRange: null,
          sourceFile: null,
          textPath: null,
          reportPath: null,
          slotStatus: 'missing',
          slotError: 'No matrix result found for this symbol/timeframe.',
          ...meta,
          parents: [],
          summary: reportFromParents([]),
        });
        continue;
      }
      const reportRange = parseReportRange(item.textPath);
      const strategyFileOk = item.strategyFile && fs.existsSync(item.strategyFile);
      const strategyStatus = item.result.strategyData?.status || null;
      if (item.result.status !== 'ok' || (!strategyFileOk && strategyStatus !== 'no_trade_data')) {
        const reason = item.result.error || item.result.strategyData?.error || `status:${item.result.status || 'unknown'}`;
        failed.push({ runId, symbol, timeframe: timeframe.label, reason, reportPath: rel(item.reportPath) });
        rows.push({
          runId,
          symbol,
          timeframe: timeframe.label,
          interval: timeframe.interval,
          reportRange,
          sourceFile: strategyFileOk ? rel(item.strategyFile) : null,
          textPath: rel(item.textPath),
          reportPath: rel(item.reportPath),
          slotStatus: 'failed',
          slotError: reason,
          ...meta,
          parents: [],
          summary: reportFromParents([]),
        });
        continue;
      }
      if (strategyStatus === 'no_trade_data') {
        rows.push({
          runId,
          symbol,
          timeframe: timeframe.label,
          interval: timeframe.interval,
          reportRange,
          sourceFile: null,
          textPath: rel(item.textPath),
          reportPath: rel(item.reportPath),
          slotStatus: 'no_trade_data',
          slotError: item.result.strategyData?.reason || 'TradingView report has no trade data.',
          ...meta,
          parents: [],
          summary: reportFromParents([]),
        });
        continue;
      }
      const parents = parentTrades(item.strategyFile).map((parent) => ({
        ...parent,
        runId,
        symbol,
        timeframe: timeframe.label,
        ...meta,
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
        slotStatus: 'ok',
        slotError: null,
        ...meta,
        parents,
        summary: reportFromParents(parents),
      });
    }
  }
  return { rows, missing, failed, rejected, expectedSlots: (run.symbols || []).length * (run.timeframes || []).length };
}

function summarizeGroup(parents, fields) {
  return { ...fields, ...reportFromParents(parents) };
}

function aggregateBy(parents, keyFn, fieldsFn) {
  return [...groupBy(parents, keyFn).entries()].map(([key, group]) => summarizeGroup(group, fieldsFn(key, group)));
}

function classifySymbol(summary, windows, slotRows) {
  const validSlots = slotRows.filter((row) => row.slotStatus === 'ok' || row.slotStatus === 'no_trade_data').length;
  const failedSlots = slotRows.filter((row) => row.slotStatus === 'failed').length;
  const missingSlots = slotRows.filter((row) => row.slotStatus === 'missing').length;
  const noTradeSlots = slotRows.filter((row) => row.slotStatus === 'no_trade_data').length;
  if (validSlots === 0 || finite(summary.totalTrades) < 5) {
    return {
      classification: 'insufficient-data',
      validSlots,
      failedSlots,
      missingSlots,
      noTradeSlots,
      reason: validSlots === 0 ? 'no valid exported slots' : 'fewer than 5 trades',
    };
  }
  const nonLatest = windows.filter((row) => row.window !== 'latest');
  const latest = windows.find((row) => row.window === 'latest');
  const stableOutsideLatest = nonLatest.some((row) => finite(row.totalPnl) > 0) && !nonLatest.every((row) => finite(row.totalPnl) <= 0);
  const latestOnly = finite(summary.totalPnl) > 0 && nonLatest.every((row) => finite(row.totalPnl) <= 0);
  const latestDefensible = !latest || finite(latest.totalTrades) < 3 || finite(latest.totalPnl) >= -Math.max(250, Math.abs(finite(summary.totalPnl)) * 0.5);
  if (pfValue(summary) >= 1.35 && finite(summary.maxDrawdownPct) <= 5 && finite(summary.totalTrades) >= 10 && stableOutsideLatest) {
    return {
      classification: latestDefensible ? 'pass' : 'marginal',
      validSlots,
      failedSlots,
      missingSlots,
      noTradeSlots,
      reason: latestDefensible ? 'meets PF/DD/trade/window gates' : 'latest window is too weak for full pass',
    };
  }
  if (pfValue(summary) >= 1.2 && finite(summary.maxDrawdownPct) <= 6 && finite(summary.totalTrades) >= 8 && !latestOnly) {
    return { classification: 'marginal', validSlots, failedSlots, missingSlots, noTradeSlots, reason: 'meets relaxed PF/DD gate' };
  }
  if (pfValue(summary) >= 1.35 && finite(summary.totalTrades) < 10) {
    return { classification: 'diagnostic-only', validSlots, failedSlots, missingSlots, noTradeSlots, reason: 'positive PF but low trade count' };
  }
  return { classification: 'fail', validSlots, failedSlots, missingSlots, noTradeSlots, reason: 'does not meet PF/DD/window gates' };
}

function aggregate(rows) {
  const parents = rows.flatMap((row) => row.parents);
  const slots = rows.map((row) => ({
    symbol: row.symbol,
    asset: row.asset,
    regimeTier: row.regimeTier,
    priorOutcome: row.priorOutcome,
    timeframe: row.timeframe,
    slotStatus: row.slotStatus,
    slotError: row.slotError,
    reportRange: row.reportRange,
    sourceFile: row.sourceFile,
    ...row.summary,
  }));
  const basket = summarizeGroup(parents, { scope: 'all_symbols_all_timeframes' });
  const symbolRows = [...groupBy(rows, (item) => item.symbol).entries()].map(([symbol, slotRows]) => {
    const symbolParents = slotRows.flatMap((row) => row.parents);
    const meta = {
      symbol,
      asset: slotRows[0]?.asset || shortSymbol(symbol),
      regimeTier: slotRows[0]?.regimeTier || 'smaller/reflexive',
      liquidityTier: slotRows[0]?.liquidityTier || 'smaller/reflexive',
      priorOutcome: slotRows[0]?.priorOutcome || 'new',
      aliasGroup: slotRows[0]?.aliasGroup || '',
      totalSlots: slotRows.length,
      okSlots: slotRows.filter((row) => row.slotStatus === 'ok').length,
      noTradeSlots: slotRows.filter((row) => row.slotStatus === 'no_trade_data').length,
      failedSlots: slotRows.filter((row) => row.slotStatus === 'failed').length,
      missingSlots: slotRows.filter((row) => row.slotStatus === 'missing').length,
    };
    return summarizeGroup(symbolParents, meta);
  }).sort((a, b) => a.asset.localeCompare(b.asset));
  const windowRows = aggregateBy(
    parents,
    (item) => [item.symbol, item.window].join('|'),
    (key) => {
      const [symbol, window] = key.split('|');
      const row = rows.find((item) => item.symbol === symbol);
      return { symbol, asset: row?.asset || shortSymbol(symbol), regimeTier: row?.regimeTier || 'smaller/reflexive', window };
    },
  ).sort((a, b) => `${a.asset}-${a.window}`.localeCompare(`${b.asset}-${b.window}`));
  const timeframeRows = rows.map((row) => ({
    symbol: row.symbol,
    asset: row.asset,
    regimeTier: row.regimeTier,
    timeframe: row.timeframe,
    slotStatus: row.slotStatus,
    ...row.summary,
  })).sort((a, b) => `${a.asset}-${a.timeframe}`.localeCompare(`${b.asset}-${b.timeframe}`));
  const sideRows = aggregateBy(
    parents,
    (item) => [item.symbol, item.side].join('|'),
    (key) => {
      const [symbol, side] = key.split('|');
      const row = rows.find((item) => item.symbol === symbol);
      return { symbol, asset: row?.asset || shortSymbol(symbol), regimeTier: row?.regimeTier || 'smaller/reflexive', side };
    },
  ).sort((a, b) => `${a.asset}-${a.side}`.localeCompare(`${b.asset}-${b.side}`));
  const tierRows = aggregateBy(
    parents,
    (item) => item.regimeTier,
    (regimeTier) => ({ regimeTier }),
  ).sort((a, b) => a.regimeTier.localeCompare(b.regimeTier));
  const symbolClassifications = symbolRows.map((summary) => {
    const windows = windowRows.filter((row) => row.symbol === summary.symbol);
    const slotRows = rows.filter((row) => row.symbol === summary.symbol);
    const classification = classifySymbol(summary, windows, slotRows);
    return { ...summary, ...classification };
  });
  const newSymbols = symbolClassifications.filter((row) => row.regimeTier === 'smaller/reflexive');
  const addedPasses = newSymbols.filter((row) => row.classification === 'pass');
  const addedMarginals = newSymbols.filter((row) => row.classification === 'marginal');
  const smallerPassKeys = [...new Set(addedPasses.map((row) => row.aliasGroup || row.asset))];
  const positiveSmallerPasses = addedPasses.filter((row) => finite(row.totalPnl) > 0);
  const smallerPassPnl = positiveSmallerPasses.reduce((sum, row) => sum + finite(row.totalPnl), 0);
  const topSmallerPassPnl = Math.max(0, ...positiveSmallerPasses.map((row) => finite(row.totalPnl)));
  const topSmallerPassShare = smallerPassPnl > 0 ? topSmallerPassPnl / smallerPassPnl * 100 : null;
  const outlierDependent = Number.isFinite(topSmallerPassShare) && topSmallerPassShare > 75;
  const admittedSymbols = new Set(symbolClassifications.filter((row) => row.classification === 'pass').map((row) => row.symbol));
  const marginalSymbols = new Set(symbolClassifications.filter((row) => row.classification === 'marginal').map((row) => row.symbol));
  const scopeRows = [
    ['All symbols', (item) => true],
    ['Prior admitted controls', (item) => item.regimeTier === 'prior admitted control'],
    ['Prior failed controls', (item) => item.regimeTier === 'prior failed control'],
    ['Major controls', (item) => item.regimeTier === 'major control'],
    ['Smaller/reflexive candidates', (item) => item.regimeTier === 'smaller/reflexive'],
    ['Admitted pass symbols', (item) => admittedSymbols.has(item.symbol)],
    ['Smaller/reflexive pass symbols', (item) => admittedSymbols.has(item.symbol) && item.regimeTier === 'smaller/reflexive'],
    ['Marginal symbols', (item) => marginalSymbols.has(item.symbol)],
    ['Failed symbols', (item) => !admittedSymbols.has(item.symbol) && !marginalSymbols.has(item.symbol)],
  ].map(([scope, predicate]) => summarizeGroup(parents.filter(predicate), { scope }));
  const priorAdmittedRows = parents.filter((item) => item.regimeTier === 'prior admitted control');
  const priorAdmittedSummary = summarizeGroup(priorAdmittedRows, { scope: 'prior_admitted_controls' });
  const zec = symbolClassifications.find((row) => row.symbol === 'BINANCE:ZECUSDT');
  const zecProtected = zec
    && (pfValue(zec) >= 2.0 || pfValue(zec) >= baseline.zecPf * 0.85)
    && finite(zec.maxDrawdownPct) <= 3.5;
  const priorAdmittedProtected = pfValue(priorAdmittedSummary) >= baseline.admittedBasketPf * 0.85
    && finite(priorAdmittedSummary.maxDrawdownPct) <= 5;
  const unavailableSymbols = symbolClassifications
    .filter((row) => row.validSlots === 0)
    .map((row) => row.asset);
  const verdict = {
    addedPasses: addedPasses.map((row) => row.asset),
    addedMarginals: addedMarginals.map((row) => row.asset),
    smallerPassAssets: smallerPassKeys,
    topSmallerPassShare,
    outlierDependent,
    zecProtected,
    priorAdmittedProtected,
    insufficientDataSymbols: unavailableSymbols,
    lowerLiquiditySupported: smallerPassKeys.length >= 3 && !outlierDependent && zecProtected && priorAdmittedProtected,
    lowerLiquidityWeaklySupported: smallerPassKeys.length > 0 && !unavailableSymbols.length,
  };
  verdict.label = verdict.lowerLiquiditySupported
    ? 'lower-liquidity thesis supported'
    : smallerPassKeys.length >= 3
      ? 'lower-liquidity thesis weakly supported'
      : unavailableSymbols.length >= newSymbols.length
        ? 'insufficient data'
        : smallerPassKeys.length > 0 || addedMarginals.length > 0
          ? 'symbol-admission only'
          : 'lower-liquidity thesis rejected';
  verdict.recommendation = verdict.lowerLiquiditySupported
    ? 'Proceed to a liquidity-aware symbol-admission implementation test using only independently passing smaller/reflexive symbols plus protected prior admitted controls.'
    : smallerPassKeys.length >= 3
      ? 'Do not implement a global liquidity-tier rule yet; inspect outlier dependence and latest-window behavior before admitting these symbols.'
      : smallerPassKeys.length > 0 || addedMarginals.length > 0
        ? 'Keep V7 as symbol-admission only; admit no liquidity tier globally and use passing smaller symbols only for follow-up diagnostics.'
        : 'Reject the lower-liquidity expansion thesis for now; continue with the prior admitted symbol set unless a different independent variable is tested.';
  return { parents, slots, basket, scopeRows, tierRows, symbolRows, windowRows, timeframeRows, sideRows, symbolClassifications, verdict };
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

function markdown(rows, missing, failed, rejected, expectedSlots, aggregateResult) {
  const lines = ['# V7 Liquidity Scope Sanity Metrics', ''];
  lines.push(`Generated from ${rows.length} selected or accounted Strategy Tester slots. Expected slots: ${expectedSlots}. Missing: ${missing.length}. Failed slots: ${failed.length}. Rejected report candidates: ${rejected.length}.`);
  lines.push('');
  lines.push('## Coverage');
  table(lines, ['Expected slots', 'Accounted slots', 'Missing', 'Failed', 'Rejected'], [{ expected: expectedSlots, selected: rows.length, missing: missing.length, failed: failed.length, rejected: rejected.length }], (row) => [
    row.expected,
    row.selected,
    row.missing,
    row.failed,
    row.rejected,
  ]);
  lines.push('');
  lines.push('## Source Ranges');
  table(lines, ['Asset', 'TV Symbol', 'Tier', 'Prior', 'TF', 'Status', 'Report range', 'Trades', 'P&L', 'PF', 'Win %', 'DD %'], aggregateResult.slots, (row) => [
    row.asset,
    shortSymbol(row.symbol),
    row.regimeTier,
    row.priorOutcome,
    row.timeframe,
    row.slotStatus,
    rangeLabel(row.reportRange),
    ...metricCells(row),
  ]);
  lines.push('');
  lines.push('## Symbol Classification');
  table(lines, ['Asset', 'TV Symbol', 'Tier', 'Prior', 'Class', 'Slots ok/no/failed/missing', 'Reason', 'Trades', 'P&L', 'PF', 'Win %', 'DD %', 'TP1 first %', 'Stop first %'], aggregateResult.symbolClassifications, (row) => [
    row.asset,
    shortSymbol(row.symbol),
    row.regimeTier,
    row.priorOutcome,
    row.classification,
    `${row.okSlots}/${row.noTradeSlots}/${row.failedSlots}/${row.missingSlots}`,
    row.reason,
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
  lines.push('## Liquidity Tier Comparison');
  table(lines, ['Tier', 'Trades', 'P&L', 'PF', 'Win %', 'DD %'], aggregateResult.tierRows, (row) => [
    row.regimeTier,
    ...metricCells(row),
  ]);
  lines.push('');
  lines.push('## Windowed Robustness');
  table(lines, ['Asset', 'Tier', 'Window', 'Trades', 'P&L', 'PF', 'Win %', 'DD %'], aggregateResult.windowRows, (row) => [
    row.asset,
    row.regimeTier,
    row.window,
    ...metricCells(row),
  ]);
  lines.push('');
  lines.push('## Timeframe Contribution');
  table(lines, ['Asset', 'Tier', 'TF', 'Status', 'Trades', 'P&L', 'PF', 'Win %', 'DD %'], aggregateResult.timeframeRows, (row) => [
    row.asset,
    row.regimeTier,
    row.timeframe,
    row.slotStatus,
    ...metricCells(row),
  ]);
  lines.push('');
  lines.push('## Directional Contribution');
  table(lines, ['Asset', 'Tier', 'Side', 'Trades', 'P&L', 'PF', 'Win %', 'DD %'], aggregateResult.sideRows, (row) => [
    row.asset,
    row.regimeTier,
    row.side,
    ...metricCells(row),
  ]);
  lines.push('');
  lines.push('## Verdict Inputs');
  lines.push('');
  lines.push(`- Label: ${aggregateResult.verdict.label}`);
  lines.push(`- Smaller/reflexive passes: ${aggregateResult.verdict.addedPasses.length ? aggregateResult.verdict.addedPasses.join(', ') : 'none'}`);
  lines.push(`- Smaller/reflexive marginals: ${aggregateResult.verdict.addedMarginals.length ? aggregateResult.verdict.addedMarginals.join(', ') : 'none'}`);
  lines.push(`- Independent smaller/reflexive pass assets: ${aggregateResult.verdict.smallerPassAssets.length ? aggregateResult.verdict.smallerPassAssets.join(', ') : 'none'}`);
  lines.push(`- Top smaller/reflexive pass P&L share: ${fmt(aggregateResult.verdict.topSmallerPassShare, 1)}%`);
  lines.push(`- Outlier-dependent pass set: ${aggregateResult.verdict.outlierDependent ? 'yes' : 'no'}`);
  lines.push(`- ZEC profit-protection passed: ${aggregateResult.verdict.zecProtected ? 'yes' : 'no'}`);
  lines.push(`- Prior admitted controls protected: ${aggregateResult.verdict.priorAdmittedProtected ? 'yes' : 'no'}`);
  lines.push(`- Insufficient/unavailable symbols: ${aggregateResult.verdict.insufficientDataSymbols.length ? aggregateResult.verdict.insufficientDataSymbols.join(', ') : 'none'}`);
  lines.push(`- Recommendation: ${aggregateResult.verdict.recommendation}`);
  return `${lines.join('\n')}\n`;
}

const { rows, missing, failed, rejected, expectedSlots } = buildRows();
const aggregateResult = aggregate(rows);
ensureDir(outputDir);
ensureDir(telemetryDir);
fs.writeFileSync(path.join(telemetryDir, 'liquidity_scope_sanity_metrics.json'), JSON.stringify({
  generatedAt: new Date().toISOString(),
  manifestPath: rel(manifestPath),
  automationDir: rel(automationDir),
  initialCapital,
  runId,
  rows: rows.map(({ parents, ...row }) => row),
  missing,
  failed,
  rejected,
  aggregate: aggregateResult,
}, null, 2));
fs.writeFileSync(path.join(outputDir, 'liquidity_scope_sanity_metrics.md'), markdown(rows, missing, failed, rejected, expectedSlots, aggregateResult));
console.log(JSON.stringify({
  outputDir,
  telemetryPath: path.join(telemetryDir, 'liquidity_scope_sanity_metrics.json'),
  selectedSlots: rows.length,
  missingSlots: missing.length,
  failedSlots: failed.length,
  rejectedCandidates: rejected.length,
  verdict: aggregateResult.verdict,
}, null, 2));
