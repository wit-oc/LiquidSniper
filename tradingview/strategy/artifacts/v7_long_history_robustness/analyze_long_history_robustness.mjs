#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

const args = Object.fromEntries(process.argv.slice(2).map((arg, index, all) => {
  if (!arg.startsWith('--')) return [];
  const key = arg.slice(2);
  const next = all[index + 1];
  return [key, next && !next.startsWith('--') ? next : true];
}).filter((pair) => pair.length));

const repoRoot = path.resolve(args.cwd || path.join(process.cwd(), '../..'));
const manifestPath = path.resolve(repoRoot, args.manifest || 'tradingview/strategy/artifacts/v7_long_history_robustness/tv_long_history_robustness_runs.json');
const automationDir = path.resolve(repoRoot, args.automationDir || 'tradingview/strategy/artifacts/v7_long_history_robustness/tradingview/automation');
const outputDir = path.resolve(repoRoot, args.output || 'tradingview/strategy/artifacts/v7_long_history_robustness');
const telemetryDir = path.resolve(repoRoot, args.telemetryDir || 'tradingview/strategy/.telemetry/outputs/v7_long_history_robustness');
const initialCapital = Number(args.initialCapital || 10000);
const minCoverageDays = Number(args.minCoverageDays || 365);
const minEvidenceTrades = Number(args.minEvidenceTrades || 20);
const minDiagnosticTrades = Number(args.minDiagnosticTrades || 5);
const primaryTimeframe = String(args.primaryTimeframe || '5m');
const reportTitle = String(args.reportTitle || 'V7 Long-History Robustness Metrics');
const candidateLabel = String(args.candidateLabel || `QS3 + ${primaryTimeframe}`);
const metricsBaseName = String(args.metricsBaseName || 'long_history_robustness_metrics');

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function rel(file) {
  return file ? path.relative(repoRoot, file) : null;
}

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
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

function rangeLabel(range) {
  return range?.label ? range.label.replace(/\s+—\s+/, ' to ') : 'n/a';
}

function shortSymbol(symbol) {
  return String(symbol || '').replace('BINANCE:', '').replace('USDT', '');
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
  const match = text.match(/([A-Z][a-z]{2}\s+\d{1,2},\s+20\d{2})\s+—\s+([A-Z][a-z]{2}\s+\d{1,2},\s+20\d{2})/);
  if (!match) return null;
  const start = new Date(`${match[1]} 00:00:00 GMT`);
  const end = new Date(`${match[2]} 23:59:59 GMT`);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return null;
  return {
    label: match[0],
    start: start.toISOString(),
    end: end.toISOString(),
    days: Math.max(1, Math.round((end - start) / 86400000) + 1),
  };
}

function parseEncodedNumber(text, pattern) {
  const match = String(text || '').match(pattern);
  return match ? nullable(num(match[1])) : null;
}

function parseEntrySignal(signal) {
  const text = String(signal || '');
  const sideMatch = text.match(/V7[A-Z]*-(L|S)-/);
  const tpMatch = text.match(/-TP(-?\d+(?:\.\d+)?)\/(-?\d+(?:\.\d+)?)\/(-?\d+(?:\.\d+)?)/);
  return {
    signal: text,
    side: sideMatch?.[1] === 'L' ? 'long' : sideMatch?.[1] === 'S' ? 'short' : 'unknown',
    activeQualityScore: parseEncodedNumber(text, /-C(-?\d+(?:\.\d+)?|NaN)(?=-|$)/),
    riskPct: parseEncodedNumber(text, /-R(-?\d+(?:\.\d+)?|NaN)(?=-|$)/),
    mssAge: parseEncodedNumber(text, /-M(-?\d+(?:\.\d+)?|NaN)/),
    alertAge: parseEncodedNumber(text, /-A(-?\d+(?:\.\d+)?|NaN)(?=-|$)/),
    strengthAge: parseEncodedNumber(text, /-S(-?\d+(?:\.\d+)?|NaN)(?=-|$)/),
    strengthSlope: parseEncodedNumber(text, /-SS(-?\d+(?:\.\d+)?|NaN)/),
    entryRiskBps: parseEncodedNumber(text, /-RB(-?\d+(?:\.\d+)?|NaN)/),
    atrBps: parseEncodedNumber(text, /-ATR(-?\d+(?:\.\d+)?|NaN)/),
    entryRangeBps: parseEncodedNumber(text, /-ER(-?\d+(?:\.\d+)?|NaN)/),
    entryRangeAtr: parseEncodedNumber(text, /-DR(-?\d+(?:\.\d+)?|NaN)/),
    stopDistanceAtr: parseEncodedNumber(text, /-RA(-?\d+(?:\.\d+)?|NaN)/),
    stop: parseEncodedNumber(text, /-SL(-?\d+(?:\.\d+)?)/),
    tp1: tpMatch ? num(tpMatch[1]) : null,
    tp2: tpMatch ? num(tpMatch[2]) : null,
    tp3: tpMatch ? num(tpMatch[3]) : null,
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

function yearBucket(parent) {
  const year = parent.entryTime ? new Date(parent.entryTime).getUTCFullYear() : null;
  return year ? String(year) : 'unknown';
}

function regimeBucket(parent) {
  const year = parent.entryTime ? new Date(parent.entryTime).getUTCFullYear() : null;
  if (!year) return 'unknown';
  if (year <= 2018) return '2017-2018 prior cycle';
  if (year <= 2020) return '2019-2020 accumulation';
  if (year === 2021) return '2021 bull/top';
  if (year === 2022) return '2022 bear';
  if (year === 2023) return '2023 recovery';
  if (year === 2024) return '2024 cycle';
  return '2025-2026 current';
}

function windowBucket(parent, range) {
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
    tpFirstPct: pct(parents.filter((item) => /^tp/.test(item.firstEvent)).length, totalTrades),
    stopFirstPct: pct(parents.filter((item) => item.firstEvent === 'stop' || item.firstEvent === 'close_stop').length, totalTrades),
    avgMfeR: average(parents.map((item) => item.mfeR)),
    avgMaeR: average(parents.map((item) => item.maeR)),
    avgRiskBps: average(parents.map((item) => item.entryRiskBps)),
    avgQualityScore: average(parents.map((item) => item.activeQualityScore)),
  };
}

function safePath(value, reportPath) {
  if (!value) return null;
  if (path.isAbsolute(value)) return fs.existsSync(value) ? value : value;
  const fromRepo = path.resolve(repoRoot, value);
  if (fs.existsSync(fromRepo)) return fromRepo;
  return path.resolve(path.dirname(reportPath), value);
}

function loadSelectedReports(runId) {
  const manifest = readJson(manifestPath);
  const run = manifest.runs.find((item) => item.id === runId);
  if (!run) throw new Error(`Missing run ${runId} in ${manifestPath}`);
  const selected = new Map();
  const rejected = [];
  for (const reportPath of walk(automationDir, (file) => path.basename(file) === 'pine-text-matrix-report.json')) {
    let report;
    try {
      report = readJson(reportPath);
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
      const candidate = { reportPath, report, run, result, strategyFile, textPath, mtimeMs: fs.statSync(existingPath).mtimeMs };
      const previous = selected.get(key);
      if (!previous || candidate.mtimeMs > previous.mtimeMs) selected.set(key, candidate);
    }
  }
  return { manifest, run, selected, rejected };
}

function symbolMeta(symbol, run) {
  const metadata = run.symbolMetadata?.[symbol] || {};
  return {
    asset: metadata.asset || shortSymbol(symbol).replace(/\.P$/, ''),
    regimeTier: metadata.regimeTier || 'unknown',
    liquidityTier: metadata.liquidityTier || 'unknown',
    priorOutcome: metadata.priorOutcome || 'unknown',
    aliasGroup: metadata.aliasGroup || '',
  };
}

function buildRows(runId) {
  const { run, selected, rejected } = loadSelectedReports(runId);
  const rows = [];
  const missing = [];
  const failed = [];
  for (const symbol of run.symbols || []) {
    for (const timeframe of run.timeframes || []) {
      const key = [symbol, timeframe.label].join('|');
      const item = selected.get(key);
      const meta = symbolMeta(symbol, run);
      if (!item) {
        missing.push({ runId, symbol, timeframe: timeframe.label });
        rows.push({
          runId,
          symbol,
          timeframe: timeframe.label,
          interval: timeframe.interval,
          reportRange: null,
          slotStatus: 'missing',
          slotError: 'No matrix result found.',
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
        year: yearBucket(parent),
        marketRegime: regimeBucket(parent),
        window: windowBucket(parent, reportRange),
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
  return { run, rows, missing, failed, rejected, expectedSlots: (run.symbols || []).length * (run.timeframes || []).length };
}

function summarizeGroup(parents, fields) {
  return { ...fields, ...reportFromParents(parents) };
}

function aggregateBy(parents, keyFn, fieldsFn) {
  return [...groupBy(parents, keyFn).entries()].map(([key, group]) => summarizeGroup(group, fieldsFn(key, group)));
}

function classifyRow(row) {
  const days = row.reportRange?.days || 0;
  if (row.slotStatus === 'missing' || row.slotStatus === 'failed') return { classification: 'inconclusive', reason: row.slotError || 'missing/failed export' };
  if (row.slotStatus === 'no_trade_data') return { classification: 'inconclusive', reason: 'valid export with no trades' };
  if (days < minCoverageDays) return { classification: 'inconclusive', reason: `history under ${minCoverageDays} days` };
  if (row.summary.totalTrades < minDiagnosticTrades) return { classification: 'inconclusive', reason: `fewer than ${minDiagnosticTrades} trades` };
  if (row.summary.totalTrades < minEvidenceTrades) {
    const pf = pfValue(row.summary);
    if (pf >= 1.35 && finite(row.summary.totalPnl) > 0) return { classification: 'thin-positive', reason: `positive but fewer than ${minEvidenceTrades} trades` };
    if (pf < 1 && finite(row.summary.totalPnl) < 0) return { classification: 'thin-negative', reason: `negative but fewer than ${minEvidenceTrades} trades` };
    return { classification: 'inconclusive', reason: `fewer than ${minEvidenceTrades} evidence trades` };
  }
  const pf = pfValue(row.summary);
  if (pf >= 1.25 && finite(row.summary.totalPnl) > 0 && finite(row.summary.maxDrawdownPct) <= 12) {
    return { classification: 'pass', reason: 'meets PF/P&L/DD evidence gate' };
  }
  if (pf < 1 || finite(row.summary.totalPnl) < 0) {
    return { classification: 'fail', reason: 'negative expectancy over sufficient sample' };
  }
  return { classification: 'marginal', reason: 'positive but below confirmation gate' };
}

function aggregateRun(runId) {
  const built = buildRows(runId);
  const parents = built.rows.flatMap((row) => row.parents);
  const slotRows = built.rows.map((row) => {
    const classification = classifyRow(row);
    return {
      runId: row.runId,
      symbol: row.symbol,
      asset: row.asset,
      regimeTier: row.regimeTier,
      liquidityTier: row.liquidityTier,
      priorOutcome: row.priorOutcome,
      timeframe: row.timeframe,
      slotStatus: row.slotStatus,
      slotError: row.slotError,
      reportRange: row.reportRange,
      sourceFile: row.sourceFile,
      textPath: row.textPath,
      reportPath: row.reportPath,
      ...row.summary,
      ...classification,
    };
  });
  const evidenceRows = slotRows.filter((row) => row.timeframe === primaryTimeframe && ['ok', 'no_trade_data'].includes(row.slotStatus));
  const coveredRows = evidenceRows.filter((row) => (row.reportRange?.days || 0) >= minCoverageDays);
  const historyGate = {
    timeframe: primaryTimeframe,
    minCoverageDays,
    eligibleRows: evidenceRows.length,
    coveredRows: coveredRows.length,
    cappedRows: evidenceRows.length - coveredRows.length,
    coveredPct: evidenceRows.length ? coveredRows.length / evidenceRows.length * 100 : 0,
    materiallyCapped: evidenceRows.length > 0 && coveredRows.length <= evidenceRows.length / 2,
  };
  const yearRows = aggregateBy(
    parents,
    (item) => [item.symbol, item.timeframe, item.year].join('|'),
    (key) => {
      const [symbol, timeframe, year] = key.split('|');
      const row = built.rows.find((item) => item.symbol === symbol && item.timeframe === timeframe);
      return { symbol, asset: row?.asset || shortSymbol(symbol), timeframe, year, regimeTier: row?.regimeTier || 'unknown' };
    },
  ).sort((a, b) => `${a.asset}-${a.timeframe}-${a.year}`.localeCompare(`${b.asset}-${b.timeframe}-${b.year}`));
  const regimeRows = aggregateBy(
    parents,
    (item) => [item.symbol, item.timeframe, item.marketRegime].join('|'),
    (key) => {
      const [symbol, timeframe, marketRegime] = key.split('|');
      const row = built.rows.find((item) => item.symbol === symbol && item.timeframe === timeframe);
      return { symbol, asset: row?.asset || shortSymbol(symbol), timeframe, marketRegime, regimeTier: row?.regimeTier || 'unknown' };
    },
  ).sort((a, b) => `${a.asset}-${a.timeframe}-${a.marketRegime}`.localeCompare(`${b.asset}-${b.timeframe}-${b.marketRegime}`));
  const windowRows = aggregateBy(
    parents,
    (item) => [item.symbol, item.timeframe, item.window].join('|'),
    (key) => {
      const [symbol, timeframe, window] = key.split('|');
      const row = built.rows.find((item) => item.symbol === symbol && item.timeframe === timeframe);
      return { symbol, asset: row?.asset || shortSymbol(symbol), timeframe, window, regimeTier: row?.regimeTier || 'unknown' };
    },
  ).sort((a, b) => `${a.asset}-${a.timeframe}-${a.window}`.localeCompare(`${b.asset}-${b.timeframe}-${b.window}`));
  const scopeRows = [
    ['All symbols', () => true],
    ['Prior admitted controls', (item) => item.regimeTier === 'prior admitted control'],
    ['Prior failed controls', (item) => item.regimeTier === 'prior failed control'],
    ['Major controls', (item) => item.regimeTier === 'major control'],
    ['Perp route probes', (item) => item.regimeTier === 'perp route probe'],
    ['Failed+perp controls', (item) => item.regimeTier === 'prior failed control' || item.regimeTier === 'perp route probe'],
  ].map(([scope, predicate]) => summarizeGroup(parents.filter(predicate), { scope }));
  const basket = summarizeGroup(parents, { scope: 'all_symbols' });
  const positiveYearsBySymbol = new Map();
  for (const row of yearRows) {
    if (finite(row.totalPnl) > 0 && finite(row.totalTrades) >= minDiagnosticTrades) {
      const key = `${row.symbol}|${row.timeframe}`;
      positiveYearsBySymbol.set(key, (positiveYearsBySymbol.get(key) || 0) + 1);
    }
  }
  const slotRowsWithPersistence = slotRows.map((row) => {
    const eligibleYearRows = yearRows.filter((item) => item.symbol === row.symbol && item.timeframe === row.timeframe && finite(item.totalTrades) >= minDiagnosticTrades);
    const positiveYears = positiveYearsBySymbol.get(`${row.symbol}|${row.timeframe}`) || 0;
    if (
      row.classification === 'pass'
      && (row.reportRange?.days || 0) >= 730
      && eligibleYearRows.length >= 2
      && positiveYears < 2
    ) {
      return {
        ...row,
        classification: 'marginal',
        reason: 'positive total result but lacks multi-year persistence',
      };
    }
    return row;
  });
  const persistenceRows = slotRowsWithPersistence.map((row) => ({
    symbol: row.symbol,
    asset: row.asset,
    timeframe: row.timeframe,
    classification: row.classification,
    totalTrades: row.totalTrades,
    totalPnl: row.totalPnl,
    profitFactor: row.profitFactor,
    maxDrawdownPct: row.maxDrawdownPct,
    reportRange: row.reportRange,
    positiveYears: positiveYearsBySymbol.get(`${row.symbol}|${row.timeframe}`) || 0,
    positiveYearShare: yearRows.filter((item) => item.symbol === row.symbol && item.timeframe === row.timeframe && finite(item.totalTrades) >= minDiagnosticTrades).length
      ? (positiveYearsBySymbol.get(`${row.symbol}|${row.timeframe}`) || 0) / yearRows.filter((item) => item.symbol === row.symbol && item.timeframe === row.timeframe && finite(item.totalTrades) >= minDiagnosticTrades).length * 100
      : null,
  }));
  const passes = slotRowsWithPersistence.filter((row) => row.classification === 'pass');
  const fails = slotRowsWithPersistence.filter((row) => row.classification === 'fail');
  const thin = slotRowsWithPersistence.filter((row) => row.classification.startsWith('thin-'));
  const verdict = {
    label: historyGate.materiallyCapped
      ? 'not enough historical coverage'
      : passes.length >= Math.ceil(slotRowsWithPersistence.length * 0.5) && fails.length <= Math.floor(slotRowsWithPersistence.length * 0.25)
        ? 'candidate broadly supported'
        : passes.length > 0 && fails.length > 0
          ? 'mixed / symbol-specific'
          : passes.length > 0
            ? 'thin or narrow support'
            : 'candidate rejected',
    historyGate,
    passAssets: passes.map((row) => row.asset),
    failAssets: fails.map((row) => row.asset),
    thinAssets: thin.map((row) => `${row.asset}:${row.classification}`),
    recommendation: historyGate.materiallyCapped
      ? `Do not confirm ${candidateLabel}. Acquire deeper ${primaryTimeframe} history through TradingView Deep Backtesting or another TradingView-sourced export path before tuning.`
      : passes.length >= Math.ceil(slotRowsWithPersistence.length * 0.5) && fails.length <= Math.floor(slotRowsWithPersistence.length * 0.25)
        ? 'Proceed to implementation hardening without adding filters.'
        : 'Do not lock the strategy as globally robust; inspect failed symbols and temporal concentration before any implementation commitment.',
  };
  return { ...built, parents, basket, slotRows: slotRowsWithPersistence, scopeRows, yearRows, regimeRows, windowRows, persistenceRows, verdict };
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
  lines.push(`| ${headers.map((header) => /%|P&L|PF|DD|Trades|Days|Years|Rows/.test(header) ? '---:' : '---').join(' | ')} |`);
  for (const row of rows) lines.push(`| ${rowFn(row).join(' | ')} |`);
}

function markdown(results) {
  const primary = results.find((item) => item.run.id === 'v7-long-history-qs3-5m') || results[0];
  const control = results.find((item) => item.run.id === 'v7-long-history-qs3-15m-control');
  const lines = [`# ${reportTitle}`, ''];
  lines.push(`Generated from ${results.length} run(s). Minimum coverage gate: ${minCoverageDays} days. Evidence trade gate: ${minEvidenceTrades} trades.`);
  lines.push('');
  lines.push('## Verdict Inputs');
  lines.push('');
  lines.push(`- Primary verdict: ${primary.verdict.label}`);
  lines.push(`- ${primaryTimeframe} rows with >=${minCoverageDays} days: ${primary.verdict.historyGate.coveredRows}/${primary.verdict.historyGate.eligibleRows}`);
  lines.push(`- Materially capped under one year: ${primary.verdict.historyGate.materiallyCapped ? 'yes' : 'no'}`);
  lines.push(`- Pass assets: ${primary.verdict.passAssets.length ? primary.verdict.passAssets.join(', ') : 'none'}`);
  lines.push(`- Fail assets: ${primary.verdict.failAssets.length ? primary.verdict.failAssets.join(', ') : 'none'}`);
  lines.push(`- Thin assets: ${primary.verdict.thinAssets.length ? primary.verdict.thinAssets.join(', ') : 'none'}`);
  lines.push(`- Recommendation: ${primary.verdict.recommendation}`);
  lines.push('');
  for (const result of results) {
    lines.push(`## Run: ${result.run.id}`);
    lines.push('');
    lines.push(`Expected slots: ${result.expectedSlots}. Accounted: ${result.rows.length}. Missing: ${result.missing.length}. Failed: ${result.failed.length}. Rejected report candidates: ${result.rejected.length}.`);
    lines.push('');
    lines.push('### Basket');
    table(lines, ['Scope', 'Trades', 'P&L', 'PF', 'Win %', 'DD %'], [result.basket], (row) => [
      row.scope,
      ...metricCells(row),
    ]);
    lines.push('');
    lines.push('### Per-Symbol Metrics And Classification');
    table(lines, ['Asset', 'TV Symbol', 'Tier', 'Prior', 'TF', 'Status', 'Class', 'Reason', 'Range', 'Days', 'Trades', 'P&L', 'PF', 'Win %', 'DD %'], result.slotRows, (row) => [
      row.asset,
      shortSymbol(row.symbol),
      row.regimeTier,
      row.priorOutcome,
      row.timeframe,
      row.slotStatus,
      row.classification,
      row.reason,
      rangeLabel(row.reportRange),
      fmt(row.reportRange?.days, 0),
      ...metricCells(row),
    ]);
    lines.push('');
    lines.push('### Scope Summary');
    table(lines, ['Scope', 'Trades', 'P&L', 'PF', 'Win %', 'DD %'], result.scopeRows, (row) => [
      row.scope,
      ...metricCells(row),
    ]);
    lines.push('');
    lines.push('### Temporal Persistence');
    table(lines, ['Asset', 'TF', 'Class', 'Positive Years', 'Positive Year %', 'Trades', 'P&L', 'PF', 'DD %'], result.persistenceRows, (row) => [
      row.asset,
      row.timeframe,
      row.classification,
      fmt(row.positiveYears, 0),
      fmt(row.positiveYearShare, 1),
      fmt(row.totalTrades, 0),
      fmt(row.totalPnl),
      fmt(row.profitFactor, 3),
      fmt(row.maxDrawdownPct, 2),
    ]);
    lines.push('');
    lines.push('### Market Regime Segments');
    table(lines, ['Asset', 'TF', 'Regime', 'Trades', 'P&L', 'PF', 'Win %', 'DD %'], result.regimeRows, (row) => [
      row.asset,
      row.timeframe,
      row.marketRegime,
      ...metricCells(row),
    ]);
    lines.push('');
    lines.push('### Year Segments');
    table(lines, ['Asset', 'TF', 'Year', 'Trades', 'P&L', 'PF', 'Win %', 'DD %'], result.yearRows, (row) => [
      row.asset,
      row.timeframe,
      row.year,
      ...metricCells(row),
    ]);
    lines.push('');
    lines.push('### Early/Middle/Latest Windows');
    table(lines, ['Asset', 'TF', 'Window', 'Trades', 'P&L', 'PF', 'Win %', 'DD %'], result.windowRows, (row) => [
      row.asset,
      row.timeframe,
      row.window,
      ...metricCells(row),
    ]);
    lines.push('');
  }
  if (control) {
    lines.push('## Control Note');
    lines.push('');
    lines.push('The 15m control is included only to test whether long-history evidence contradicts prior 15m weakness. It is not promoted by this validation unless the primary verdict explicitly supports it.');
    lines.push('');
  }
  return `${lines.join('\n')}\n`;
}

const manifest = readJson(manifestPath);
const runIds = args.run
  ? String(args.run).split(',').map((item) => item.trim()).filter(Boolean)
  : manifest.runs.map((run) => run.id);
const results = runIds.map(aggregateRun);

ensureDir(outputDir);
ensureDir(telemetryDir);
fs.writeFileSync(path.join(telemetryDir, 'long_history_robustness_metrics.json'), JSON.stringify({
  generatedAt: new Date().toISOString(),
  manifestPath: rel(manifestPath),
  automationDir: rel(automationDir),
  initialCapital,
  minCoverageDays,
  minEvidenceTrades,
  minDiagnosticTrades,
  results: results.map((result) => ({
    run: result.run,
    expectedSlots: result.expectedSlots,
    rows: result.rows.map(({ parents, ...row }) => row),
    missing: result.missing,
    failed: result.failed,
    rejected: result.rejected,
    aggregate: {
      parents: result.parents,
      basket: result.basket,
      slotRows: result.slotRows,
      scopeRows: result.scopeRows,
      yearRows: result.yearRows,
      regimeRows: result.regimeRows,
      windowRows: result.windowRows,
      persistenceRows: result.persistenceRows,
      verdict: result.verdict,
    },
  })),
}, null, 2));
fs.writeFileSync(path.join(telemetryDir, `${metricsBaseName}.json`), JSON.stringify({
  generatedAt: new Date().toISOString(),
  manifestPath: rel(manifestPath),
  automationDir: rel(automationDir),
  initialCapital,
  minCoverageDays,
  minEvidenceTrades,
  minDiagnosticTrades,
  primaryTimeframe,
  results: results.map((result) => ({
    run: result.run,
    expectedSlots: result.expectedSlots,
    rows: result.rows.map(({ parents, ...row }) => row),
    missing: result.missing,
    failed: result.failed,
    rejected: result.rejected,
    aggregate: {
      parents: result.parents,
      basket: result.basket,
      slotRows: result.slotRows,
      scopeRows: result.scopeRows,
      yearRows: result.yearRows,
      regimeRows: result.regimeRows,
      windowRows: result.windowRows,
      persistenceRows: result.persistenceRows,
      verdict: result.verdict,
    },
  })),
}, null, 2));
fs.writeFileSync(path.join(outputDir, `${metricsBaseName}.md`), markdown(results));
console.log(JSON.stringify({
  outputDir,
  telemetryPath: path.join(telemetryDir, `${metricsBaseName}.json`),
  runs: results.map((result) => ({
    runId: result.run.id,
    selectedSlots: result.rows.length,
    missingSlots: result.missing.length,
    failedSlots: result.failed.length,
    verdict: result.verdict,
  })),
}, null, 2));
