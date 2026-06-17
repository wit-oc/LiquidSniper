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
const strategyRoot = path.join(repoRoot, 'tradingview/strategy');
const sourceTelemetryRoot = path.resolve(repoRoot, args.sourceTelemetryRoot || 'tradingview/strategy/.telemetry/outputs/v7_generalization_independent_variables');
const sourceArtifactRoot = path.resolve(repoRoot, args.sourceArtifactRoot || 'tradingview/strategy/artifacts/v7_generalization_independent_variables');
const outputRoot = path.resolve(repoRoot, args.output || 'tradingview/strategy/artifacts/v7_admission_routing_spike');
const telemetryRoot = path.resolve(repoRoot, args.telemetryRoot || 'tradingview/strategy/.telemetry/outputs/v7_admission_routing_spike');
const outputPath = path.join(outputRoot, 'admission_routing_metrics.md');
const telemetryPath = path.join(telemetryRoot, 'admission_routing_metrics.json');
const initialCapital = Number(args.initialCapital || 10000);
const baselineRunId = 'v7-generalization-baseline-125bps';
const qualityRunId = 'v7-generalization-quality-score-3';

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function rel(file) {
  return path.relative(repoRoot, file);
}

function readJson(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
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

function pct(count, total) {
  return total ? count / total * 100 : null;
}

function average(values) {
  const clean = values.filter(Number.isFinite);
  return clean.length ? clean.reduce((sum, value) => sum + value, 0) / clean.length : null;
}

function median(values) {
  const clean = values.filter(Number.isFinite).sort((a, b) => a - b);
  if (!clean.length) return null;
  const mid = Math.floor(clean.length / 2);
  return clean.length % 2 ? clean[mid] : (clean[mid - 1] + clean[mid]) / 2;
}

function quantile(values, q) {
  const clean = values.filter(Number.isFinite).sort((a, b) => a - b);
  if (!clean.length) return null;
  const pos = (clean.length - 1) * q;
  const base = Math.floor(pos);
  const rest = pos - base;
  if (clean[base + 1] === undefined) return clean[base];
  return clean[base] + rest * (clean[base + 1] - clean[base]);
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

function parseEncodedNumber(text, pattern) {
  const match = String(text || '').match(pattern);
  return match ? nullable(num(match[1])) : null;
}

function levelQualityScore(quality) {
  if (!Number.isFinite(quality)) return 0;
  if (quality >= 4) return 3;
  if (quality >= 3) return 2;
  if (quality >= 2) return 1;
  return 0;
}

function parseEntrySignal(signal) {
  const text = String(signal || '');
  const sideMatch = text.match(/V7[A-Z]*-(L|S)-/);
  const biasMatch = text.match(/-B(-?\d+(?:\.\d+)?|NaN)\/(-?\d+(?:\.\d+)?|NaN)/);
  const tpMatch = text.match(/-TP(-?\d+(?:\.\d+)?)\/(-?\d+(?:\.\d+)?)\/(-?\d+(?:\.\d+)?)/);
  const armQuality = parseEncodedNumber(text, /-Q(-?\d+(?:\.\d+)?|NaN)(?=-|$)/);
  const activeQualityScore = parseEncodedNumber(text, /-C(-?\d+(?:\.\d+)?|NaN)(?=-|$)/);
  const levelScore = levelQualityScore(armQuality);
  const side = sideMatch?.[1] === 'L' ? 'long' : sideMatch?.[1] === 'S' ? 'short' : 'unknown';
  const strengthSlope = parseEncodedNumber(text, /-SS(-?\d+(?:\.\d+)?|NaN)/);
  const sideMultiplier = side === 'long' ? 1 : side === 'short' ? -1 : 0;
  return {
    signal: text,
    side,
    armQuality,
    activeQualityScore,
    levelScore,
    nonLevelQualityScore: Number.isFinite(activeQualityScore) ? activeQualityScore - levelScore : null,
    bias4hSide: biasMatch ? nullable(num(biasMatch[1])) : null,
    bias1dSide: biasMatch ? nullable(num(biasMatch[2])) : null,
    riskPct: parseEncodedNumber(text, /-R(-?\d+(?:\.\d+)?|NaN)(?=-|$)/),
    mssAge: parseEncodedNumber(text, /-M(-?\d+(?:\.\d+)?|NaN)/),
    alertAge: parseEncodedNumber(text, /-A(-?\d+(?:\.\d+)?|NaN)(?=-|$)/),
    strengthAge: parseEncodedNumber(text, /-S(-?\d+(?:\.\d+)?|NaN)(?=-|$)/),
    strengthSlope,
    sideAlignedStrengthSlope: Number.isFinite(strengthSlope) ? strengthSlope * sideMultiplier : null,
    absStrengthSlope: Number.isFinite(strengthSlope) ? Math.abs(strengthSlope) : null,
    entryRiskBps: parseEncodedNumber(text, /-RB(-?\d+(?:\.\d+)?|NaN)/),
    atrBps: parseEncodedNumber(text, /-ATR(-?\d+(?:\.\d+)?|NaN)/),
    entryRangeBps: parseEncodedNumber(text, /-ER(-?\d+(?:\.\d+)?|NaN)/),
    entryRangeAtr: parseEncodedNumber(text, /-DR(-?\d+(?:\.\d+)?|NaN)/),
    stopDistanceAtr: parseEncodedNumber(text, /-RA(-?\d+(?:\.\d+)?|NaN)/),
    minRiskFloorBps: parseEncodedNumber(text, /-MF(-?\d+(?:\.\d+)?|NaN)/),
    stopBufferBps: parseEncodedNumber(text, /-SB(-?\d+(?:\.\d+)?|NaN)/),
    stopExitModeCode: parseEncodedNumber(text, /-XM(-?\d+(?:\.\d+)?|NaN)/),
    tp1R: parseEncodedNumber(text, /-T1(-?\d+(?:\.\d+)?|NaN)/),
    activeProfileOk: parseEncodedNumber(text, /-PF(-?\d+(?:\.\d+)?|NaN)/),
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

function parseParentTrades(strategyFile) {
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

function groupBy(items, keyFn) {
  const groups = new Map();
  for (const item of items) {
    const key = keyFn(item);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(item);
  }
  return groups;
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
    profitFactor: grossLoss > 0 ? grossProfit / grossLoss : grossProfit > 0 ? Infinity : 0,
    totalTrades,
    winningTrades,
    losingTrades,
    winRatePct: pct(winningTrades, totalTrades),
    maxDrawdownPct,
    tp1FirstPct: pct(parents.filter((item) => /^tp/.test(item.firstEvent)).length, totalTrades),
    stopFirstPct: pct(parents.filter((item) => item.firstEvent === 'stop' || item.firstEvent === 'close_stop').length, totalTrades),
    maxHoldPct: pct(parents.filter((item) => item.firstEvent === 'max_hold').length, totalTrades),
    avgMfeR: average(parents.map((item) => item.mfeR)),
    avgMaeR: average(parents.map((item) => item.maeR)),
    avgRiskBps: average(parents.map((item) => item.entryRiskBps)),
    avgAtrBps: average(parents.map((item) => item.atrBps)),
    avgEntryRangeAtr: average(parents.map((item) => item.entryRangeAtr)),
    avgStopDistanceAtr: average(parents.map((item) => item.stopDistanceAtr)),
    avgActiveQualityScore: average(parents.map((item) => item.activeQualityScore)),
    avgArmQuality: average(parents.map((item) => item.armQuality)),
    avgNonLevelQualityScore: average(parents.map((item) => item.nonLevelQualityScore)),
    avgStrengthAge: average(parents.map((item) => item.strengthAge)),
    avgSideAlignedStrengthSlope: average(parents.map((item) => item.sideAlignedStrengthSlope)),
    avgAbsStrengthSlope: average(parents.map((item) => item.absStrengthSlope)),
  };
}

function aggregateBy(parents, keyFn, rowFn) {
  return [...groupBy(parents, keyFn)].map(([key, rows]) => ({
    key,
    ...rowFn(key, rows),
    ...reportFromParents(rows),
  }));
}

function sourcePath(slot) {
  if (!slot.sourceFile) return null;
  const file = path.resolve(repoRoot, slot.sourceFile);
  return fs.existsSync(file) ? file : null;
}

function readRun(runId) {
  const file = path.join(sourceTelemetryRoot, runId, 'liquidity_scope_sanity_metrics.json');
  if (!fs.existsSync(file)) throw new Error(`Missing telemetry: ${file}`);
  const metrics = readJson(file);
  const parents = [];
  const rawCoverage = [];
  for (const slot of metrics.aggregate.slots || []) {
    const filePath = sourcePath(slot);
    const parsed = filePath ? parseParentTrades(filePath) : [];
    rawCoverage.push({
      symbol: slot.symbol,
      timeframe: slot.timeframe,
      slotStatus: slot.slotStatus,
      sourceFile: slot.sourceFile,
      parsedTrades: parsed.length,
      telemetryTrades: slot.totalTrades || 0,
      rawAvailable: Boolean(filePath),
    });
    for (const parent of parsed) {
      parents.push({
        ...parent,
        runId,
        symbol: slot.symbol,
        asset: slot.asset,
        timeframe: slot.timeframe,
        regimeTier: slot.regimeTier,
        liquidityTier: slot.liquidityTier || null,
        priorOutcome: slot.priorOutcome || null,
        window: classifyWindow(parent, slot.reportRange),
      });
    }
  }
  return { runId, metrics, parents, rawCoverage };
}

function slotKey(row) {
  return `${row.symbol}|${row.timeframe}`;
}

function windowKey(row) {
  return `${row.symbol}|${row.window}`;
}

function scopeRows(parents) {
  const scopes = [
    ['All symbols', () => true],
    ['Prior admitted controls', (row) => row.regimeTier === 'prior admitted control'],
    ['Prior failed controls', (row) => row.regimeTier === 'prior failed control'],
    ['Major controls', (row) => row.regimeTier === 'major control'],
    ['Perp route probes', (row) => row.regimeTier === 'perp route probe'],
    ['Failed+perp controls', (row) => row.regimeTier === 'prior failed control' || row.regimeTier === 'perp route probe'],
  ];
  return scopes.map(([scope, predicate]) => ({ scope, ...reportFromParents(parents.filter(predicate)) }));
}

function timeframeRows(parents) {
  return aggregateBy(parents, slotKey, (key, rows) => ({
    symbol: rows[0]?.symbol,
    asset: rows[0]?.asset,
    timeframe: rows[0]?.timeframe,
    regimeTier: rows[0]?.regimeTier,
  })).sort((a, b) => `${a.asset}-${a.timeframe}`.localeCompare(`${b.asset}-${b.timeframe}`));
}

function windowRows(parents) {
  return aggregateBy(parents, windowKey, (key, rows) => ({
    symbol: rows[0]?.symbol,
    asset: rows[0]?.asset,
    window: rows[0]?.window,
    regimeTier: rows[0]?.regimeTier,
  })).sort((a, b) => `${a.asset}-${a.window}`.localeCompare(`${b.asset}-${b.window}`));
}

function symbolRows(parents) {
  return aggregateBy(parents, (row) => row.symbol, (key, rows) => ({
    symbol: rows[0]?.symbol,
    asset: rows[0]?.asset,
    regimeTier: rows[0]?.regimeTier,
    liquidityTier: rows[0]?.liquidityTier,
  })).sort((a, b) => `${a.asset}`.localeCompare(`${b.asset}`));
}

function classifySlot(row) {
  if (row.totalTrades < 3) return 'thin';
  if (row.totalPnl > 0 && row.profitFactor >= 1.25 && row.maxDrawdownPct <= 5) return 'pass_like';
  if (row.totalPnl > 0 && row.profitFactor >= 1.0 && row.maxDrawdownPct <= 7) return 'marginal_like';
  return 'fail_like';
}

function summarizeCandidate(id, title, family, validity, description, parents, baselineSummary, qualitySummary) {
  const basket = reportFromParents(parents);
  const tRows = timeframeRows(parents);
  const wRows = windowRows(parents);
  const sRows = symbolRows(parents);
  const positiveRows = tRows.filter((row) => row.totalTrades > 0 && row.totalPnl > 0).length;
  const negativeRows = tRows.filter((row) => row.totalTrades > 0 && row.totalPnl < 0).length;
  const pfFailRows = tRows.filter((row) => row.totalTrades > 0 && finite(row.profitFactor) < 1).length;
  const ddOverFiveRows = tRows.filter((row) => row.totalTrades > 0 && finite(row.maxDrawdownPct) > 5).length;
  const negativeWindows = wRows.filter((row) => row.totalTrades >= 3 && row.totalPnl < 0).length;
  const admitted = reportFromParents(parents.filter((row) => row.regimeTier === 'prior admitted control'));
  const failedAndPerp = reportFromParents(parents.filter((row) => row.regimeTier === 'prior failed control' || row.regimeTier === 'perp route probe'));
  const retainedTradesPct = baselineSummary.basket.totalTrades ? parents.length / baselineSummary.basket.totalTrades * 100 : null;
  const admittedProfitRetentionPct = baselineSummary.admitted.totalPnl ? admitted.totalPnl / baselineSummary.admitted.totalPnl * 100 : null;
  const deltaPnl = basket.totalPnl - baselineSummary.basket.totalPnl;
  const deltaPf = finite(basket.profitFactor) - finite(baselineSummary.basket.profitFactor);
  const deltaDd = finite(basket.maxDrawdownPct) - finite(baselineSummary.basket.maxDrawdownPct);
  const qs3DeltaPnl = basket.totalPnl - qualitySummary.basket.totalPnl;
  const qs3DeltaPf = finite(basket.profitFactor) - finite(qualitySummary.basket.profitFactor);
  const qs3DeltaDd = finite(basket.maxDrawdownPct) - finite(qualitySummary.basket.maxDrawdownPct);
  const admittedProtected = admitted.totalTrades >= 50
    && admitted.totalPnl >= baselineSummary.admitted.totalPnl * 0.60
    && admitted.profitFactor >= 2.0
    && admitted.maxDrawdownPct <= 4.25;
  const retentionPenalty = retainedTradesPct < 40 ? (40 - retainedTradesPct) * 0.35 : 0;
  const slotCoveragePenalty = tRows.length < 16 ? (16 - tRows.length) * 0.75 : 0;
  const score = (finite(basket.profitFactor) - finite(baselineSummary.basket.profitFactor)) * 16
    + (baselineSummary.basket.maxDrawdownPct - basket.maxDrawdownPct) * 0.8
    + (baselineSummary.negativeRows - negativeRows) * 1.2
    + (baselineSummary.pfFailRows - pfFailRows) * 1.3
    + (baselineSummary.negativeWindows - negativeWindows) * 0.9
    + (failedAndPerp.totalPnl - baselineSummary.failedAndPerp.totalPnl) / 350
    + (admittedProtected ? 4 : -6)
    - Math.max(0, 60 - finite(admittedProfitRetentionPct)) * 0.18
    - retentionPenalty
    - slotCoveragePenalty;
  return {
    id,
    title,
    family,
    validity,
    description,
    basket,
    scopes: scopeRows(parents),
    timeframeRows: tRows,
    windowRows: wRows,
    symbolRows: sRows,
    positiveRows,
    negativeRows,
    pfFailRows,
    ddOverFiveRows,
    negativeWindows,
    admitted,
    failedAndPerp,
    admittedProtected,
    retainedTradesPct,
    admittedProfitRetentionPct,
    deltaPnl,
    deltaPf,
    deltaDd,
    qs3DeltaPnl,
    qs3DeltaPf,
    qs3DeltaDd,
    score,
  };
}

function buildBaselineSummary(baselineParents, qualityParents) {
  const basket = reportFromParents(baselineParents);
  const admitted = reportFromParents(baselineParents.filter((row) => row.regimeTier === 'prior admitted control'));
  const failedAndPerp = reportFromParents(baselineParents.filter((row) => row.regimeTier === 'prior failed control' || row.regimeTier === 'perp route probe'));
  const tRows = timeframeRows(baselineParents);
  const wRows = windowRows(baselineParents);
  const qualityBasket = reportFromParents(qualityParents);
  return {
    basket,
    admitted,
    failedAndPerp,
    timeframeRows: tRows,
    windowRows: wRows,
    positiveRows: tRows.filter((row) => row.totalTrades > 0 && row.totalPnl > 0).length,
    negativeRows: tRows.filter((row) => row.totalTrades > 0 && row.totalPnl < 0).length,
    pfFailRows: tRows.filter((row) => row.totalTrades > 0 && finite(row.profitFactor) < 1).length,
    ddOverFiveRows: tRows.filter((row) => row.totalTrades > 0 && finite(row.maxDrawdownPct) > 5).length,
    negativeWindows: wRows.filter((row) => row.totalTrades >= 3 && row.totalPnl < 0).length,
    quality: {
      basket: qualityBasket,
      admitted: reportFromParents(qualityParents.filter((row) => row.regimeTier === 'prior admitted control')),
      failedAndPerp: reportFromParents(qualityParents.filter((row) => row.regimeTier === 'prior failed control' || row.regimeTier === 'perp route probe')),
    },
  };
}

function applySlotPredicate(parents, predicate) {
  const keep = new Set(timeframeRows(parents).filter(predicate).map((row) => slotKey(row)));
  return parents.filter((row) => keep.has(slotKey(row)));
}

function routeOneTimeframeBy(parents, valueFn, direction = 'max') {
  const bySymbol = groupBy(timeframeRows(parents), (row) => row.symbol);
  const keep = new Set();
  for (const rows of bySymbol.values()) {
    const ranked = rows
      .filter((row) => row.totalTrades > 0 && Number.isFinite(valueFn(row)))
      .sort((a, b) => direction === 'max' ? valueFn(b) - valueFn(a) : valueFn(a) - valueFn(b));
    if (ranked[0]) keep.add(slotKey(ranked[0]));
  }
  return parents.filter((row) => keep.has(slotKey(row)));
}

function walkForwardLatestGate(parents) {
  const bySlot = groupBy(parents, slotKey);
  const admitted = new Set();
  for (const [key, rows] of bySlot.entries()) {
    const train = rows.filter((row) => row.window === 'early' || row.window === 'middle');
    const report = reportFromParents(train);
    if (report.totalTrades >= 6 && report.profitFactor >= 1.2 && report.maxDrawdownPct <= 5) {
      admitted.add(key);
    }
  }
  return parents.filter((row) => row.window === 'latest' && admitted.has(slotKey(row)));
}

function latestOnly(parents) {
  return parents.filter((row) => row.window === 'latest');
}

function traitRows(parents, slots) {
  const slotClass = new Map(slots.map((row) => [slotKey(row), classifySlot(row)]));
  const rows = parents.map((row) => ({ ...row, slotClass: slotClass.get(slotKey(row)) || 'unknown' }));
  const traits = [
    ['Active Quality Score', 'activeQualityScore'],
    ['Level Quality', 'armQuality'],
    ['Non-Level Quality Score', 'nonLevelQualityScore'],
    ['MSS Age', 'mssAge'],
    ['Alert Age', 'alertAge'],
    ['Strength Age', 'strengthAge'],
    ['Side-Aligned Strength Slope', 'sideAlignedStrengthSlope'],
    ['Absolute Strength Slope', 'absStrengthSlope'],
    ['ATR bps', 'atrBps'],
    ['Entry Range / ATR', 'entryRangeAtr'],
    ['Entry Risk bps', 'entryRiskBps'],
    ['Stop Distance / ATR', 'stopDistanceAtr'],
  ];
  return traits.map(([label, field]) => {
    const pass = rows.filter((row) => row.slotClass === 'pass_like').map((row) => row[field]);
    const fail = rows.filter((row) => row.slotClass === 'fail_like').map((row) => row[field]);
    const all = rows.map((row) => row[field]);
    return {
      trait: label,
      field,
      passAvg: average(pass),
      passMedian: median(pass),
      failAvg: average(fail),
      failMedian: median(fail),
      deltaAvg: Number.isFinite(average(pass)) && Number.isFinite(average(fail)) ? average(pass) - average(fail) : null,
      p25: quantile(all, 0.25),
      p50: quantile(all, 0.5),
      p75: quantile(all, 0.75),
      availablePct: pct(all.filter(Number.isFinite).length, all.length),
    };
  });
}

function groupTraitRows(parents) {
  const groups = [
    ['Timeframe 15m', (row) => row.timeframe === '15m'],
    ['Timeframe 5m', (row) => row.timeframe === '5m'],
    ['Prior admitted controls', (row) => row.regimeTier === 'prior admitted control'],
    ['Prior failed controls', (row) => row.regimeTier === 'prior failed control'],
    ['Major controls', (row) => row.regimeTier === 'major control'],
    ['Perp route probes', (row) => row.regimeTier === 'perp route probe'],
  ];
  return groups.map(([group, predicate]) => {
    const rows = parents.filter(predicate);
    return {
      group,
      trades: rows.length,
      pnl: reportFromParents(rows).totalPnl,
      pf: reportFromParents(rows).profitFactor,
      dd: reportFromParents(rows).maxDrawdownPct,
      avgQuality: average(rows.map((row) => row.activeQualityScore)),
      avgNonLevelQuality: average(rows.map((row) => row.nonLevelQualityScore)),
      avgStrengthAge: average(rows.map((row) => row.strengthAge)),
      avgSideAlignedSlope: average(rows.map((row) => row.sideAlignedStrengthSlope)),
      avgEntryRangeAtr: average(rows.map((row) => row.entryRangeAtr)),
      avgStopDistanceAtr: average(rows.map((row) => row.stopDistanceAtr)),
      avgAtrBps: average(rows.map((row) => row.atrBps)),
    };
  });
}

function table(lines, headers, rows, rowFn) {
  lines.push(`| ${headers.join(' | ')} |`);
  lines.push(`| ${headers.map((header) => /Trades|P&L|PF|Win|DD|Rows|Windows|Score|Delta|%|Avg|Median|P25|P50|P75/.test(header) ? '---:' : '---').join(' | ')} |`);
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

function main() {
  const baseline = readRun(baselineRunId);
  const quality = readRun(qualityRunId);
  const baselineSummary = buildBaselineSummary(baseline.parents, quality.parents);
  const qualitySummary = {
    basket: reportFromParents(quality.parents),
    admitted: reportFromParents(quality.parents.filter((row) => row.regimeTier === 'prior admitted control')),
    failedAndPerp: reportFromParents(quality.parents.filter((row) => row.regimeTier === 'prior failed control' || row.regimeTier === 'perp route probe')),
  };

  const rules = [
    {
      id: 'actual_quality_score_3',
      title: 'Actual Quality Score 3',
      family: 'control',
      validity: 'tradingview-export',
      description: 'Actual exported QS3 control from TradingView, not a simulation.',
      parents: quality.parents,
    },
    {
      id: 'qs3_five_minute_only',
      title: 'QS3 + 5m Only',
      family: 'timeframe-routing',
      validity: 'qs3-plus-one-routing-variable',
      description: 'Applies the static 5m routing rule to the already-proven QS3 control.',
      parents: quality.parents.filter((row) => row.timeframe === '5m'),
    },
    {
      id: 'qs3_fifteen_minute_only',
      title: 'QS3 + 15m Only',
      family: 'timeframe-routing',
      validity: 'qs3-plus-one-routing-variable',
      description: 'Applies the static 15m routing rule to the already-proven QS3 control.',
      parents: quality.parents.filter((row) => row.timeframe === '15m'),
    },
    {
      id: 'qs3_route_by_avg_quality',
      title: 'QS3 + Route Higher Avg Quality TF',
      family: 'timeframe-routing',
      validity: 'lookahead-diagnostic',
      description: 'Diagnostic only: applies full-history higher-average-quality timeframe routing to QS3.',
      parents: routeOneTimeframeBy(quality.parents, (row) => finite(row.avgActiveQualityScore), 'max'),
    },
    {
      id: 'qs3_entry_risk_bps_lte_250',
      title: 'QS3 + Entry Risk <= 250 bps',
      family: 'risk-efficiency',
      validity: 'qs3-plus-one-entry-variable',
      description: 'Applies one risk-efficiency admission variable to QS3.',
      parents: quality.parents.filter((row) => finite(row.entryRiskBps) <= 250),
    },
    {
      id: 'qs3_stop_distance_atr_lte_4_5',
      title: 'QS3 + Stop Distance / ATR <= 4.5',
      family: 'risk-efficiency',
      validity: 'qs3-plus-one-entry-variable',
      description: 'Applies one stop-efficiency admission variable to QS3.',
      parents: quality.parents.filter((row) => finite(row.stopDistanceAtr) <= 4.5),
    },
    {
      id: 'emulated_quality_score_gte_3',
      title: 'Entry Quality Score >= 3',
      family: 'entry-quality',
      validity: 'entry-time',
      description: 'Direct QS3 decomposition: keep baseline trades where encoded active quality score is at least 3.',
      parents: baseline.parents.filter((row) => finite(row.activeQualityScore) >= 3),
    },
    {
      id: 'entry_quality_score_gte_4',
      title: 'Entry Quality Score >= 4',
      family: 'entry-quality',
      validity: 'entry-time',
      description: 'Stricter version of the QS3 gate.',
      parents: baseline.parents.filter((row) => finite(row.activeQualityScore) >= 4),
    },
    {
      id: 'level_quality_gte_3',
      title: 'Level Quality >= 3',
      family: 'quality-component',
      validity: 'entry-time',
      description: 'Tests whether the level/sweep quality component alone explains QS3 lift.',
      parents: baseline.parents.filter((row) => finite(row.armQuality) >= 3),
    },
    {
      id: 'non_level_quality_gte_2',
      title: 'Non-Level Quality >= 2',
      family: 'quality-component',
      validity: 'entry-time',
      description: 'Tests the non-level confirmation residual: bias/BOS/alert/phase quality minus level score.',
      parents: baseline.parents.filter((row) => finite(row.nonLevelQualityScore) >= 2),
    },
    {
      id: 'strength_age_lte_3',
      title: 'Strength Age <= 3',
      family: 'strength-freshness',
      validity: 'entry-time',
      description: 'Requires fresher Oracle Strength confirmation.',
      parents: baseline.parents.filter((row) => finite(row.strengthAge) <= 3),
    },
    {
      id: 'directional_strength_aligned',
      title: 'Directional Strength Aligned',
      family: 'trend-persistence-proxy',
      validity: 'entry-time',
      description: 'Requires strength slope to align with trade direction at entry.',
      parents: baseline.parents.filter((row) => finite(row.sideAlignedStrengthSlope) >= 0),
    },
    {
      id: 'entry_range_atr_gte_2',
      title: 'Entry Range / ATR >= 2',
      family: 'displacement-quality',
      validity: 'entry-time',
      description: 'Requires stronger displacement than the current 1.5 ATR floor.',
      parents: baseline.parents.filter((row) => finite(row.entryRangeAtr) >= 2),
    },
    {
      id: 'stop_distance_atr_lte_4_5',
      title: 'Stop Distance / ATR <= 4.5',
      family: 'risk-efficiency',
      validity: 'entry-time',
      description: 'Avoids structurally wide, low-efficiency entries.',
      parents: baseline.parents.filter((row) => finite(row.stopDistanceAtr) <= 4.5),
    },
    {
      id: 'entry_risk_bps_lte_250',
      title: 'Entry Risk <= 250 bps',
      family: 'risk-efficiency',
      validity: 'entry-time',
      description: 'Avoids very wide market-price risk at entry.',
      parents: baseline.parents.filter((row) => finite(row.entryRiskBps) <= 250),
    },
    {
      id: 'moderate_atr_bps_75_250',
      title: 'ATR bps 75 to 250',
      family: 'volatility-admission',
      validity: 'entry-time',
      description: 'Keeps moderate-volatility entries, excluding very quiet and very hot conditions.',
      parents: baseline.parents.filter((row) => finite(row.atrBps) >= 75 && finite(row.atrBps) <= 250),
    },
    {
      id: 'slot_avg_quality_gte_3',
      title: 'Slot Avg Quality >= 3',
      family: 'slot-admission',
      validity: 'slot-calibration',
      description: 'Admits whole symbol/timeframe slots whose historical average entry quality is at least 3.',
      parents: applySlotPredicate(baseline.parents, (row) => finite(row.avgActiveQualityScore) >= 3),
    },
    {
      id: 'route_by_avg_quality',
      title: 'Route To Higher Avg Quality TF',
      family: 'timeframe-routing',
      validity: 'lookahead-diagnostic',
      description: 'Diagnostic only: selects one timeframe per asset using full-history average quality.',
      parents: routeOneTimeframeBy(baseline.parents, (row) => finite(row.avgActiveQualityScore), 'max'),
    },
    {
      id: 'route_by_lower_stop_atr',
      title: 'Route To Lower Stop/ATR TF',
      family: 'timeframe-routing',
      validity: 'lookahead-diagnostic',
      description: 'Diagnostic only: selects one timeframe per asset using lower full-history stop distance / ATR.',
      parents: routeOneTimeframeBy(baseline.parents, (row) => finite(row.avgStopDistanceAtr), 'min'),
    },
    {
      id: 'five_minute_only',
      title: '5m Only',
      family: 'timeframe-routing',
      validity: 'static-timeframe',
      description: 'Simple static timeframe admission check.',
      parents: baseline.parents.filter((row) => row.timeframe === '5m'),
    },
    {
      id: 'fifteen_minute_only',
      title: '15m Only',
      family: 'timeframe-routing',
      validity: 'static-timeframe',
      description: 'Simple static timeframe admission check.',
      parents: baseline.parents.filter((row) => row.timeframe === '15m'),
    },
  ];

  const candidates = rules.map((rule) => summarizeCandidate(
    rule.id,
    rule.title,
    rule.family,
    rule.validity,
    rule.description,
    rule.parents,
    baselineSummary,
    qualitySummary,
  )).sort((a, b) => b.score - a.score);

  const latestControl = summarizeCandidate(
    'latest_window_control',
    'Latest Window Control',
    'walk-forward',
    'evaluation-control',
    'Baseline latest-window trades only.',
    latestOnly(baseline.parents),
    {
      ...baselineSummary,
      basket: reportFromParents(latestOnly(baseline.parents)),
      admitted: reportFromParents(latestOnly(baseline.parents).filter((row) => row.regimeTier === 'prior admitted control')),
      failedAndPerp: reportFromParents(latestOnly(baseline.parents).filter((row) => row.regimeTier === 'prior failed control' || row.regimeTier === 'perp route probe')),
      negativeRows: timeframeRows(latestOnly(baseline.parents)).filter((row) => row.totalTrades > 0 && row.totalPnl < 0).length,
      pfFailRows: timeframeRows(latestOnly(baseline.parents)).filter((row) => row.totalTrades > 0 && finite(row.profitFactor) < 1).length,
      negativeWindows: windowRows(latestOnly(baseline.parents)).filter((row) => row.totalTrades >= 3 && row.totalPnl < 0).length,
    },
    qualitySummary,
  );
  const walkForward = summarizeCandidate(
    'walk_forward_stability_gate',
    'Walk-Forward Stability Gate',
    'slot-admission',
    'prior-window-calibration',
    'Admit latest-window trades only when the same slot had early+middle PF >= 1.2, at least 6 trades, and DD <= 5.',
    walkForwardLatestGate(baseline.parents),
    {
      ...baselineSummary,
      basket: reportFromParents(latestOnly(baseline.parents)),
      admitted: reportFromParents(latestOnly(baseline.parents).filter((row) => row.regimeTier === 'prior admitted control')),
      failedAndPerp: reportFromParents(latestOnly(baseline.parents).filter((row) => row.regimeTier === 'prior failed control' || row.regimeTier === 'perp route probe')),
      negativeRows: timeframeRows(latestOnly(baseline.parents)).filter((row) => row.totalTrades > 0 && row.totalPnl < 0).length,
      pfFailRows: timeframeRows(latestOnly(baseline.parents)).filter((row) => row.totalTrades > 0 && finite(row.profitFactor) < 1).length,
      negativeWindows: windowRows(latestOnly(baseline.parents)).filter((row) => row.totalTrades >= 3 && row.totalPnl < 0).length,
    },
    qualitySummary,
  );

  const slotDiagnostics = timeframeRows(baseline.parents).map((row) => ({
    ...row,
    slotClass: classifySlot(row),
  }));
  const diagnostics = {
    traitSeparation: traitRows(baseline.parents, slotDiagnostics),
    groupTraits: groupTraitRows(baseline.parents),
    slotDiagnostics,
    qs3Removed: reportFromParents(baseline.parents.filter((row) => finite(row.activeQualityScore) < 3)),
    qs3Kept: reportFromParents(baseline.parents.filter((row) => finite(row.activeQualityScore) >= 3)),
    rawCoverage: {
      baseline: baseline.rawCoverage,
      quality: quality.rawCoverage,
    },
    unavailableTraits: [
      'Direct wick/sweep frequency before entry is not in the exported closed-trade telemetry; entryRangeAtr and stopDistanceAtr are used as pre-trade sweep/chop proxies.',
      'Direct multi-bar trend persistence is not in the exported closed-trade telemetry; side-aligned strength slope and non-level quality residual are used as proxies.',
      'Alert age is mostly unavailable/null in the current System A path, so it is not a useful discriminator in this pass.',
    ],
  };

  const lines = ['# V7 Admission Routing Spike Metrics', ''];
  lines.push(`Source artifact: \`${rel(sourceArtifactRoot)}\``);
  lines.push(`Source telemetry: \`${rel(sourceTelemetryRoot)}\``);
  lines.push('');
  lines.push('## Coverage');
  table(lines, ['Run', 'Parsed Trades', 'Telemetry Trades', 'Raw Slots Available'], [
    {
      run: 'Baseline 125bps',
      parsed: baseline.parents.length,
      telemetry: baseline.metrics.aggregate.parents.length,
      rawSlots: baseline.rawCoverage.filter((row) => row.rawAvailable).length,
    },
    {
      run: 'Quality Score 3',
      parsed: quality.parents.length,
      telemetry: quality.metrics.aggregate.parents.length,
      rawSlots: quality.rawCoverage.filter((row) => row.rawAvailable).length,
    },
  ], (row) => [row.run, row.parsed, row.telemetry, `${row.rawSlots}/32`]);
  lines.push('');
  lines.push('## Controls');
  table(lines, ['Control', 'Trades', 'P&L', 'PF', 'Win %', 'DD %'], [
    { title: 'Baseline 125bps', ...baselineSummary.basket },
    { title: 'Actual Quality Score 3', ...qualitySummary.basket },
    { title: 'Emulated QS>=3 From Baseline', ...diagnostics.qs3Kept },
    { title: 'Removed By QS>=3', ...diagnostics.qs3Removed },
  ], (row) => [row.title, ...metricCells(row)]);
  lines.push('');
  lines.push('## Candidate Ranking');
  table(lines, ['Rule', 'Family', 'Validity', 'Trades', 'Retained %', 'Admit P&L Retained %', 'P&L', 'PF', 'Win %', 'DD %', 'PF<1 Rows', 'Neg Windows', 'Admit Protected', 'Score'], candidates, (row) => [
    row.title,
    row.family,
    row.validity,
    fmt(row.basket.totalTrades, 0),
    fmt(row.retainedTradesPct, 1),
    fmt(row.admittedProfitRetentionPct, 1),
    fmt(row.basket.totalPnl),
    fmt(row.basket.profitFactor, 3),
    fmt(row.basket.winRatePct, 1),
    fmt(row.basket.maxDrawdownPct, 2),
    row.pfFailRows,
    row.negativeWindows,
    row.admittedProtected ? 'yes' : 'no',
    fmt(row.score, 2),
  ]);
  lines.push('');
  lines.push('## Delta Versus Controls');
  table(lines, ['Rule', 'Delta P&L vs Base', 'Delta PF vs Base', 'Delta DD vs Base', 'Delta P&L vs QS3', 'Delta PF vs QS3', 'Delta DD vs QS3'], candidates, (row) => [
    row.title,
    fmt(row.deltaPnl),
    fmt(row.deltaPf, 3),
    fmt(row.deltaDd, 2),
    fmt(row.qs3DeltaPnl),
    fmt(row.qs3DeltaPf, 3),
    fmt(row.qs3DeltaDd, 2),
  ]);
  lines.push('');
  lines.push('## Scope Rows For Top Candidates');
  const topScopeRows = candidates.slice(0, 8).flatMap((candidate) => candidate.scopes.map((scope) => ({ candidate: candidate.title, ...scope })));
  table(lines, ['Rule', 'Scope', 'Trades', 'P&L', 'PF', 'Win %', 'DD %'], topScopeRows, (row) => [
    row.candidate,
    row.scope,
    ...metricCells(row),
  ]);
  lines.push('');
  lines.push('## Trait Separation');
  table(lines, ['Trait', 'Available %', 'Pass Avg', 'Fail Avg', 'Delta Avg', 'P25', 'P50', 'P75'], diagnostics.traitSeparation, (row) => [
    row.trait,
    fmt(row.availablePct, 1),
    fmt(row.passAvg, 3),
    fmt(row.failAvg, 3),
    fmt(row.deltaAvg, 3),
    fmt(row.p25, 3),
    fmt(row.p50, 3),
    fmt(row.p75, 3),
  ]);
  lines.push('');
  lines.push('## Group Trait Diagnostics');
  table(lines, ['Group', 'Trades', 'P&L', 'PF', 'DD %', 'Avg Quality', 'Avg Non-Level Quality', 'Avg Strength Age', 'Avg Side Slope', 'Avg Range/ATR', 'Avg Stop/ATR', 'Avg ATR bps'], diagnostics.groupTraits, (row) => [
    row.group,
    row.trades,
    fmt(row.pnl),
    fmt(row.pf, 3),
    fmt(row.dd, 2),
    fmt(row.avgQuality, 3),
    fmt(row.avgNonLevelQuality, 3),
    fmt(row.avgStrengthAge, 3),
    fmt(row.avgSideAlignedSlope, 3),
    fmt(row.avgEntryRangeAtr, 3),
    fmt(row.avgStopDistanceAtr, 3),
    fmt(row.avgAtrBps, 2),
  ]);
  lines.push('');
  lines.push('## Walk-Forward Stability Check');
  table(lines, ['Check', 'Trades', 'P&L', 'PF', 'Win %', 'DD %', 'PF<1 Rows', 'Neg Windows'], [latestControl, walkForward], (row) => [
    row.title,
    ...metricCells(row.basket),
    row.pfFailRows,
    row.negativeWindows,
  ]);
  lines.push('');
  lines.push('## Trait Availability Notes');
  for (const note of diagnostics.unavailableTraits) lines.push(`- ${note}`);
  lines.push('');

  while (lines[lines.length - 1] === '') lines.pop();
  ensureDir(outputRoot);
  ensureDir(telemetryRoot);
  fs.writeFileSync(outputPath, `${lines.join('\n')}\n`);
  fs.writeFileSync(telemetryPath, `${JSON.stringify({
    generatedAt: new Date().toISOString(),
    sourceArtifactRoot: rel(sourceArtifactRoot),
    sourceTelemetryRoot: rel(sourceTelemetryRoot),
    controls: {
      baseline: baselineSummary,
      quality: qualitySummary,
    },
    candidates,
    walkForward: {
      latestControl,
      walkForward,
    },
    diagnostics,
  }, null, 2)}\n`);
  console.log(JSON.stringify({
    outputPath,
    telemetryPath,
    baselineTrades: baseline.parents.length,
    qualityTrades: quality.parents.length,
    topCandidate: candidates[0]?.id || null,
  }, null, 2));
}

main();
