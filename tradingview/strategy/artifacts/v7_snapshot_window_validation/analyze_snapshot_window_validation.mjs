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
const manifestPath = path.resolve(repoRoot, args.manifest || 'tradingview/strategy/artifacts/v7_snapshot_window_validation/tv_snapshot_window_validation_runs.json');
const automationDir = path.resolve(repoRoot, args.automationDir || 'tradingview/strategy/artifacts/v7_snapshot_window_validation/tradingview/automation');
const outputDir = path.resolve(repoRoot, args.output || 'tradingview/strategy/artifacts/v7_snapshot_window_validation');
const telemetryDir = path.resolve(repoRoot, args.telemetryDir || 'tradingview/strategy/.telemetry/outputs/v7_snapshot_window_validation');
const initialCapital = Number(args.initialCapital || 10000);
const minEvidenceTrades = Number(args.minEvidenceTrades || 5);
const minWindowCoveragePct = Number(args.minWindowCoveragePct || 75);
const metricsBaseName = String(args.metricsBaseName || 'snapshot_window_validation_metrics');

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

function fmt(value, digits = 2) {
  return Number.isFinite(value) ? value.toFixed(digits) : 'n/a';
}

function fmtPct(value) {
  return Number.isFinite(value) ? `${value.toFixed(1)}%` : 'n/a';
}

function safeName(value) {
  return String(value).replace(/[^a-z0-9._-]+/gi, '_');
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
  return match ? num(match[1]) : NaN;
}

function parseEntrySignal(signal) {
  const text = String(signal || '');
  const sideMatch = text.match(/V7[A-Z]*-(L|S)-/);
  const tpMatch = text.match(/-TP(-?\d+(?:\.\d+)?)\/(-?\d+(?:\.\d+)?)\/(-?\d+(?:\.\d+)?)/);
  return {
    side: sideMatch?.[1] === 'L' ? 'long' : sideMatch?.[1] === 'S' ? 'short' : 'unknown',
    activeQualityScore: parseEncodedNumber(text, /-C(-?\d+(?:\.\d+)?|NaN)(?=-|$)/),
    entryRiskBps: parseEncodedNumber(text, /-RB(-?\d+(?:\.\d+)?|NaN)/),
    stop: parseEncodedNumber(text, /-SL(-?\d+(?:\.\d+)?)/),
    tp1: tpMatch ? num(tpMatch[1]) : NaN,
    tp2: tpMatch ? num(tpMatch[2]) : NaN,
    tp3: tpMatch ? num(tpMatch[3]) : NaN,
  };
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

function parentTrades(strategyFile) {
  const rows = parseCsv(fs.readFileSync(strategyFile, 'utf8'));
  const groups = new Map();
  for (let index = 0; index < rows.length; index += 1) {
    const row = rows[index];
    if (!/^Entry\b/i.test(row.Type || '')) continue;
    const key = parentKey(row);
    if (!groups.has(key)) groups.set(key, { entry: row, exits: [] });
    if (rows[index - 1] && /^Exit\b/i.test(rows[index - 1].Type || '')) groups.get(key).exits.push(rows[index - 1]);
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
    return {
      entryTime: entryTime ? entryTime.toISOString() : null,
      entryDate: group.entry['Date and time'],
      pnl,
      mfeR: Number.isFinite(riskUsd) && riskUsd > 0 ? mfeUsd / riskUsd : null,
      maeR: Number.isFinite(riskUsd) && riskUsd > 0 ? maeUsd / riskUsd : null,
      firstEvent: firstClosedEvent?.event || 'unknown',
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

function pfValue(row) {
  if (Number.isFinite(row.profitFactor)) return row.profitFactor;
  if (finite(row.grossProfit) > 0 && finite(row.grossLoss) === 0) return Infinity;
  return 0;
}

function safePath(value, reportPath) {
  if (!value) return null;
  if (path.isAbsolute(value)) return fs.existsSync(value) ? value : value;
  const fromRepo = path.resolve(repoRoot, value);
  if (fs.existsSync(fromRepo)) return fromRepo;
  return path.resolve(path.dirname(reportPath), value);
}

function evidenceRank(candidate) {
  const result = candidate?.result || {};
  const strategyStatus = result.strategyData?.status || null;
  const strategyFileOk = candidate?.strategyFile && fs.existsSync(candidate.strategyFile);
  const textPathOk = candidate?.textPath && fs.existsSync(candidate.textPath);
  if (result.status === 'ok' && strategyStatus === 'ok' && strategyFileOk) return 4;
  if (result.status === 'ok' && strategyStatus === 'no_trade_data' && textPathOk) return 4;
  if (result.status === 'ok' && textPathOk) return 3;
  if (strategyStatus === 'ok' && strategyFileOk) return 2;
  if (textPathOk) return 1;
  return 0;
}

function overlapDays(aStartIso, aEndIso, bStartIso, bEndIso) {
  const start = Math.max(Date.parse(aStartIso), Date.parse(bStartIso));
  const end = Math.min(Date.parse(aEndIso), Date.parse(bEndIso));
  if (!Number.isFinite(start) || !Number.isFinite(end) || end < start) return 0;
  return Math.round((end - start) / 86400000) + 1;
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

function selectedReports(runId) {
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
    const reportRangeMode = typeof report.strategyReportDateRange === 'object'
      ? String(report.strategyReportDateRange.mode || '')
      : String(report.strategyReportDateRange || '');
    if (!/^custom$/i.test(reportRangeMode)) {
      rejected.push({
        reportPath: rel(reportPath),
        reason: `snapshot validation requires Strategy Tester custom date range; found ${reportRangeMode || 'none'}`,
      });
      continue;
    }
    for (const result of report.results || []) {
      const strategyFile = safePath(result.strategyData?.path, reportPath);
      const textPath = safePath(result.textPath, reportPath);
      const key = [result.symbol, result.label].join('|');
      const existingPath = strategyFile && fs.existsSync(strategyFile) ? strategyFile : textPath && fs.existsSync(textPath) ? textPath : reportPath;
      const candidate = { reportPath, report, result, strategyFile, textPath, mtimeMs: fs.statSync(existingPath).mtimeMs };
      const previous = selected.get(key);
      if (!previous) {
        selected.set(key, candidate);
        continue;
      }
      const candidateRank = evidenceRank(candidate);
      const previousRank = evidenceRank(previous);
      if (candidateRank > previousRank || (candidateRank === previousRank && candidate.mtimeMs > previous.mtimeMs)) {
        selected.set(key, candidate);
      }
    }
  }
  return { selected, rejected };
}

function classify(summary, coverage) {
  if (!coverage.adequate) return { classification: 'inconclusive', reason: coverage.reason };
  if (summary.totalTrades === 0) return { classification: 'inconclusive', reason: 'adequate window coverage but no trades' };
  if (summary.totalTrades < minEvidenceTrades) {
    if (summary.totalPnl > 0 && pfValue(summary) >= 1.25) return { classification: 'thin-positive', reason: `positive but fewer than ${minEvidenceTrades} trades` };
    if (summary.totalPnl < 0 || pfValue(summary) < 1) return { classification: 'thin-negative', reason: `negative/weak but fewer than ${minEvidenceTrades} trades` };
    return { classification: 'inconclusive', reason: `fewer than ${minEvidenceTrades} evidence trades` };
  }
  if (summary.totalPnl > 0 && pfValue(summary) >= 1.25 && finite(summary.maxDrawdownPct) <= 12) return { classification: 'pass', reason: 'meets snapshot PF/P&L/DD gate' };
  if (summary.totalPnl < 0 || pfValue(summary) < 1) return { classification: 'fail', reason: 'negative expectancy over adequate sample' };
  return { classification: 'marginal', reason: 'positive but below confirmation gate' };
}

function conciseError(value) {
  return String(value || '')
    .replace(/\s+/g, ' ')
    .replace(/^Error:\s*/i, '')
    .slice(0, 240);
}

function buildWindowCoverage(run, reportRange, slotStatus, slotError = '') {
  const requested = run.snapshotWindow;
  if (!requested) return { adequate: false, status: 'coverage-failure', reason: 'run has no snapshotWindow metadata', overlapDays: 0, overlapPct: 0 };
  if (!reportRange) return { adequate: false, status: 'coverage-failure', reason: 'TradingView report range was not detectable', overlapDays: 0, overlapPct: 0 };
  const days = requested.requestedDays || Math.round((Date.parse(requested.end) - Date.parse(requested.start)) / 86400000) + 1;
  const overlap = overlapDays(reportRange.start, reportRange.end, requested.start, requested.end);
  const overlapPct = days ? overlap / days * 100 : 0;
  if (slotStatus === 'failed' || slotStatus === 'missing') {
    return { adequate: false, status: 'coverage-failure', reason: conciseError(slotError) || 'missing or failed export', overlapDays: overlap, overlapPct };
  }
  if (overlapPct < minWindowCoveragePct) {
    return {
      adequate: false,
      status: 'coverage-failure',
      reason: `TradingView returned ${fmtPct(overlapPct)} of requested window`,
      overlapDays: overlap,
      overlapPct,
    };
  }
  return { adequate: true, status: overlapPct >= 99 ? 'covered' : 'partial-covered', reason: 'requested window covered', overlapDays: overlap, overlapPct };
}

function buildRows(manifest) {
  const rows = [];
  const rejected = [];
  const missing = [];
  const failed = [];
  for (const run of manifest.runs || []) {
    const { selected, rejected: rejectedReports } = selectedReports(run.id);
    rejected.push(...rejectedReports);
    for (const symbol of run.symbols || []) {
      for (const timeframe of run.timeframes || []) {
        const key = [symbol, timeframe.label].join('|');
        const item = selected.get(key);
        const meta = symbolMeta(symbol, run);
        const base = {
          runId: run.id,
          windowId: run.snapshotWindow?.id || run.id,
          windowLabel: run.snapshotWindow?.label || run.id,
          requestedStart: run.snapshotWindow?.start || null,
          requestedEnd: run.snapshotWindow?.end || null,
          requestedDays: run.snapshotWindow?.requestedDays || null,
          symbol,
          timeframe: timeframe.label,
          interval: timeframe.interval,
          ...meta,
        };
        if (!item) {
          const reportRange = null;
          const coverage = buildWindowCoverage(run, reportRange, 'missing', 'No matrix result found.');
          const summary = reportFromParents([]);
          missing.push({ runId: run.id, symbol, timeframe: timeframe.label });
          rows.push({ ...base, slotStatus: 'missing', slotError: 'No matrix result found.', reportRange, coverage, parents: [], summary, ...classify(summary, coverage) });
          continue;
        }
        const reportRange = parseReportRange(item.textPath);
        const strategyFileOk = item.strategyFile && fs.existsSync(item.strategyFile);
        const strategyStatus = item.result.strategyData?.status || null;
        const slotFailed = item.result.status !== 'ok' || (!strategyFileOk && strategyStatus !== 'no_trade_data');
        if (slotFailed) {
          const reason = item.result.error || item.result.strategyData?.error || `status:${item.result.status || 'unknown'}`;
          const coverage = buildWindowCoverage(run, reportRange, 'failed', reason);
          const summary = reportFromParents([]);
          failed.push({ runId: run.id, symbol, timeframe: timeframe.label, reason, reportPath: rel(item.reportPath) });
          rows.push({
            ...base,
            slotStatus: 'failed',
            slotError: reason,
            reportRange,
            sourceFile: strategyFileOk ? rel(item.strategyFile) : null,
            textPath: rel(item.textPath),
            reportPath: rel(item.reportPath),
            coverage,
            parents: [],
            summary,
            ...classify(summary, coverage),
          });
          continue;
        }
        const parents = strategyStatus === 'no_trade_data'
          ? []
          : parentTrades(item.strategyFile).map((parent) => ({ ...parent, ...base }));
        const summary = reportFromParents(parents);
        const coverage = buildWindowCoverage(run, reportRange, strategyStatus === 'no_trade_data' ? 'no_trade_data' : 'ok');
        rows.push({
          ...base,
          slotStatus: strategyStatus === 'no_trade_data' ? 'no_trade_data' : 'ok',
          slotError: strategyStatus === 'no_trade_data' ? item.result.strategyData?.reason || 'TradingView report has no trade data.' : null,
          reportRange,
          sourceFile: strategyStatus === 'no_trade_data' ? null : rel(item.strategyFile),
          textPath: rel(item.textPath),
          reportPath: rel(item.reportPath),
          coverage,
          parents,
          summary,
          ...classify(summary, coverage),
        });
      }
    }
  }
  return { rows, missing, failed, rejected };
}

function summarizeGroup(rows, fields) {
  const parents = rows.flatMap((row) => row.parents || []);
  return { ...fields, ...reportFromParents(parents), slots: rows.length };
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

function aggregate(rows) {
  const coveredRows = rows.filter((row) => row.coverage.adequate);
  const nonLatestCovered = coveredRows.filter((row) => row.windowId !== 'latest-2026');
  const passes = coveredRows.filter((row) => row.classification === 'pass');
  const fails = coveredRows.filter((row) => row.classification === 'fail');
  const destructive = coveredRows.filter((row) => row.classification === 'fail' || row.classification === 'thin-negative');
  const coveragePct = rows.length ? coveredRows.length / rows.length * 100 : 0;
  const nonLatestCoveragePct = rows.filter((row) => row.windowId !== 'latest-2026').length
    ? nonLatestCovered.length / rows.filter((row) => row.windowId !== 'latest-2026').length * 100
    : 0;
  const label = coveragePct < 50 || nonLatestCovered.length === 0
    ? 'not enough TradingView historical coverage'
    : passes.length >= Math.ceil(coveredRows.length * 0.35) && destructive.length <= Math.floor(coveredRows.length * 0.25)
      ? 'snapshot-supported candidate'
      : destructive.length > Math.floor(coveredRows.length * 0.35)
        ? 'candidate downgraded'
        : 'mixed / unconfirmed';
  const recommendation = label === 'not enough TradingView historical coverage'
    ? 'Do not confirm QS3 + 5m until TradingView can provide older 5m windows through Deep Backtesting or another TradingView-sourced export path.'
    : label === 'snapshot-supported candidate'
      ? 'Keep QS3 + 5m as the leading implementation candidate and harden execution/monitoring without adding filters.'
      : label === 'candidate downgraded'
        ? 'Downgrade QS3 + 5m and revise the execution layer before implementation.'
        : 'Keep QS3 + 5m as promising but unconfirmed; inspect weak windows before implementation.';
  const windowRows = [...groupBy(rows, (row) => row.windowId).entries()].map(([windowId, group]) => {
    const covered = group.filter((row) => row.coverage.adequate);
    return {
      windowId,
      windowLabel: group[0]?.windowLabel || windowId,
      requestedStart: group[0]?.requestedStart || null,
      requestedEnd: group[0]?.requestedEnd || null,
      expectedSlots: group.length,
      coveredSlots: covered.length,
      coveragePct: group.length ? covered.length / group.length * 100 : 0,
      passSlots: covered.filter((row) => row.classification === 'pass').length,
      failSlots: covered.filter((row) => row.classification === 'fail').length,
      thinPositiveSlots: covered.filter((row) => row.classification === 'thin-positive').length,
      thinNegativeSlots: covered.filter((row) => row.classification === 'thin-negative').length,
      ...reportFromParents(covered.flatMap((row) => row.parents || [])),
    };
  });
  const symbolRows = [...groupBy(coveredRows, (row) => row.symbol).entries()].map(([symbol, group]) => ({
    symbol,
    asset: group[0]?.asset || shortSymbol(symbol),
    coveredWindows: new Set(group.map((row) => row.windowId)).size,
    passWindows: group.filter((row) => row.classification === 'pass').length,
    failWindows: group.filter((row) => row.classification === 'fail').length,
    thinPositiveWindows: group.filter((row) => row.classification === 'thin-positive').length,
    thinNegativeWindows: group.filter((row) => row.classification === 'thin-negative').length,
    ...reportFromParents(group.flatMap((row) => row.parents || [])),
  }));
  return {
    label,
    recommendation,
    coverage: {
      expectedSlots: rows.length,
      coveredSlots: coveredRows.length,
      coveragePct,
      nonLatestCoveredSlots: nonLatestCovered.length,
      nonLatestCoveragePct,
      missingSlots: rows.filter((row) => row.slotStatus === 'missing').length,
      failedSlots: rows.filter((row) => row.slotStatus === 'failed').length,
      coverageFailureSlots: rows.filter((row) => !row.coverage.adequate).length,
    },
    basket: reportFromParents(coveredRows.flatMap((row) => row.parents || [])),
    passSlots: passes.length,
    failSlots: fails.length,
    destructiveSlots: destructive.length,
    windowRows,
    symbolRows,
  };
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
  lines.push(`| ${headers.map((header) => /%|P&L|PF|DD|Trades|Slots|Windows|Days/.test(header) ? '---:' : '---').join(' | ')} |`);
  for (const row of rows) lines.push(`| ${rowFn(row).join(' | ')} |`);
}

function rangeLabel(range) {
  return range?.label ? range.label.replace(/\s+—\s+/, ' to ') : 'n/a';
}

function markdown(manifest, rows, summary) {
  const lines = ['# V7 Snapshot Window Validation Metrics', ''];
  lines.push(`Generated from ${manifest.runs.length} configured window run(s). Evidence trade gate: ${minEvidenceTrades} trades. Window coverage gate: ${minWindowCoveragePct}%.`);
  lines.push('');
  lines.push('## Verdict Inputs');
  lines.push('');
  lines.push(`- Primary verdict: ${summary.label}`);
  lines.push(`- Covered slots: ${summary.coverage.coveredSlots}/${summary.coverage.expectedSlots} (${fmt(summary.coverage.coveragePct, 1)}%)`);
  lines.push(`- Covered non-latest slots: ${summary.coverage.nonLatestCoveredSlots} (${fmt(summary.coverage.nonLatestCoveragePct, 1)}%)`);
  lines.push(`- Coverage-failure slots: ${summary.coverage.coverageFailureSlots}`);
  lines.push(`- Pass slots: ${summary.passSlots}`);
  lines.push(`- Fail slots: ${summary.failSlots}`);
  lines.push(`- Destructive slots including thin-negative: ${summary.destructiveSlots}`);
  lines.push(`- Recommendation: ${summary.recommendation}`);
  lines.push('');
  lines.push('## Covered Basket');
  table(lines, ['Scope', 'Trades', 'P&L', 'PF', 'Win %', 'DD %'], [{ scope: 'covered_slots', ...summary.basket }], (row) => [row.scope, ...metricCells(row)]);
  lines.push('');
  lines.push('## Window Summary');
  table(lines, ['Window', 'Requested', 'Covered Slots', 'Coverage %', 'Pass', 'Fail', 'Thin+', 'Thin-', 'Trades', 'P&L', 'PF', 'Win %', 'DD %'], summary.windowRows, (row) => [
    row.windowId,
    `${String(row.requestedStart).slice(0, 10)} to ${String(row.requestedEnd).slice(0, 10)}`,
    `${row.coveredSlots}/${row.expectedSlots}`,
    fmt(row.coveragePct, 1),
    fmt(row.passSlots, 0),
    fmt(row.failSlots, 0),
    fmt(row.thinPositiveSlots, 0),
    fmt(row.thinNegativeSlots, 0),
    ...metricCells(row),
  ]);
  lines.push('');
  lines.push('## Symbol Persistence On Covered Windows');
  table(lines, ['Asset', 'Symbol', 'Covered Windows', 'Pass', 'Fail', 'Thin+', 'Thin-', 'Trades', 'P&L', 'PF', 'Win %', 'DD %'], summary.symbolRows, (row) => [
    row.asset,
    shortSymbol(row.symbol),
    fmt(row.coveredWindows, 0),
    fmt(row.passWindows, 0),
    fmt(row.failWindows, 0),
    fmt(row.thinPositiveWindows, 0),
    fmt(row.thinNegativeWindows, 0),
    ...metricCells(row),
  ]);
  lines.push('');
  lines.push('## Per-Symbol Window Classifications');
  table(lines, ['Window', 'Asset', 'TV Symbol', 'Status', 'Coverage', 'Class', 'Reason', 'Requested', 'TV Range', 'Overlap %', 'Trades', 'P&L', 'PF', 'Win %', 'DD %'], rows, (row) => [
    row.windowId,
    row.asset,
    shortSymbol(row.symbol),
    row.slotStatus,
    row.coverage.status,
    row.classification,
    row.reason,
    `${String(row.requestedStart).slice(0, 10)} to ${String(row.requestedEnd).slice(0, 10)}`,
    rangeLabel(row.reportRange),
    fmt(row.coverage.overlapPct, 1),
    ...metricCells(row.summary),
  ]);
  lines.push('');
  lines.push('## Run Inventory');
  table(lines, ['Run', 'Window', 'Symbols', 'Requested Days'], manifest.runs, (run) => [
    run.id,
    run.snapshotWindow?.id || 'n/a',
    fmt((run.symbols || []).length, 0),
    fmt(run.snapshotWindow?.requestedDays, 0),
  ]);
  return `${lines.join('\n')}\n`;
}

const manifest = readJson(manifestPath);
const built = buildRows(manifest);
const rowsForOutput = built.rows.map(({ parents, ...row }) => ({
  ...row,
  ...row.summary,
}));
const summary = aggregate(built.rows);

ensureDir(outputDir);
ensureDir(telemetryDir);

const telemetry = {
  generatedAt: new Date().toISOString(),
  manifestPath: rel(manifestPath),
  automationDir: rel(automationDir),
  initialCapital,
  minEvidenceTrades,
  minWindowCoveragePct,
  rows: rowsForOutput,
  missing: built.missing,
  failed: built.failed,
  rejected: built.rejected,
  aggregate: {
    ...summary,
    parents: built.rows.flatMap((row) => row.parents || []),
  },
};

fs.writeFileSync(path.join(telemetryDir, `${metricsBaseName}.json`), JSON.stringify(telemetry, null, 2));
fs.writeFileSync(path.join(outputDir, `${metricsBaseName}.md`), markdown(manifest, built.rows, summary));

console.log(JSON.stringify({
  outputDir,
  telemetryPath: path.join(telemetryDir, `${metricsBaseName}.json`),
  expectedSlots: summary.coverage.expectedSlots,
  coveredSlots: summary.coverage.coveredSlots,
  coverageFailureSlots: summary.coverage.coverageFailureSlots,
  verdict: {
    label: summary.label,
    recommendation: summary.recommendation,
  },
}, null, 2));
