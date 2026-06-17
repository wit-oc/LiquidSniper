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
const manifestPath = path.resolve(repoRoot, args.manifest || 'tradingview/strategy/artifacts/v7_verdict/tv_verdict_harness_runs.json');
const automationDir = path.resolve(repoRoot, args.automationDir || 'tradingview/strategy/artifacts/v7_verdict/tradingview/automation');
const outputDir = path.resolve(repoRoot, args.output || 'tradingview/strategy/artifacts/v7_verdict');
const initialCapital = Number(args.initialCapital || 10000);
const outputName = args.name || 'verdict_harness_metrics';
const reportTitle = args.title || 'V7 Verdict Harness Metrics';

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
  for (let i = 0; i < text.length; i += 1) {
    const char = text[i];
    const next = text[i + 1];
    if (quoted && char === '"' && next === '"') {
      field += '"';
      i += 1;
    } else if (char === '"') {
      quoted = !quoted;
    } else if (!quoted && char === ',') {
      row.push(field);
      field = '';
    } else if (!quoted && (char === '\n' || char === '\r')) {
      if (char === '\r' && next === '\n') i += 1;
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

function compactLines(text) {
  return text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
}

function firstField(row, names) {
  for (const name of names) {
    if (row[name] !== undefined && row[name] !== '') return row[name];
  }
  return '';
}

function numericAfterLabel(lines, label, { which = 'first', offset = null, maxLookahead = 8 } = {}) {
  const values = [];
  for (let index = 0; index < lines.length; index += 1) {
    if (lines[index].toLowerCase() !== label.toLowerCase()) continue;
    if (offset !== null) {
      const value = num(lines[index + offset]);
      if (Number.isFinite(value)) values.push(value);
      continue;
    }
    for (let lookahead = 1; lookahead <= maxLookahead; lookahead += 1) {
      const value = num(lines[index + lookahead]);
      if (Number.isFinite(value)) {
        values.push(value);
        break;
      }
    }
  }
  if (!values.length) return NaN;
  return which === 'last' ? values[values.length - 1] : values[0];
}

function parseReportText(textPath) {
  if (!textPath || !fs.existsSync(textPath)) return {};
  const lines = compactLines(fs.readFileSync(textPath, 'utf8'));
  return {
    closedNetPnl: numericAfterLabel(lines, 'Net P&L'),
    openPnl: numericAfterLabel(lines, 'Open P&L', { which: 'last' }),
    openTrades: numericAfterLabel(lines, 'Total open trades'),
  };
}

function systemLabel(variant) {
  if (variant === 'system_a_current') return 'A Current';
  if (variant === 'system_a_baseline') return 'A Baseline';
  if (variant === 'risk_veto_175bps') return 'Risk Veto 175bps';
  if (variant === 'risk_damp_150bps') return 'Risk Damp 150bps';
  if (variant === 'quality_directional_strength_slope') return 'Directional Strength Slope';
  if (variant === 'quality_bos_phase_agreement') return 'BOS/Phase Agreement';
  if (variant === 'candidate_displacement_quality') return 'Displacement Quality';
  if (variant === 'candidate_displacement_quality_current') return 'Displacement 1.50 Current';
  if (variant === 'candidate_displacement_1_35') return 'Displacement 1.35';
  if (variant === 'candidate_displacement_1_75') return 'Displacement 1.75';
  if (variant === 'candidate_displacement_2_00') return 'Displacement 2.00';
  if (variant === 'candidate_exit_tp1_1_5r') return 'Exit TP1 1.5R';
  if (variant === 'candidate_exit_risk_floor_100bps') return 'Risk Floor 100bps';
  if (variant === 'candidate_stop_floor_2atr') return 'Stop Floor 2ATR';
  if (variant === 'candidate_retest_fidelity') return 'Retest Fidelity';
  if (variant === 'stop_engine_current') return 'Stop Engine Current';
  if (variant === 'stop_engine_floor_75bps') return 'Stop Floor 75bps';
  if (variant === 'stop_engine_floor_100bps') return 'Stop Floor 100bps';
  if (variant === 'stop_engine_floor_125bps') return 'Stop Floor 125bps';
  if (variant === 'stop_engine_buffer_20bps_floor_100bps') return 'Wide Buffer 20bps + Floor 100bps';
  if (variant === 'stop_engine_close_confirm_floor_100bps') return 'Close Confirmed + Floor 100bps';
  if (variant === 'leverage_stop_uniform_100x_100bps') return 'Uniform 100x / 100bps';
  if (variant === 'leverage_stop_control_125bps') return 'Control 125bps';
  if (variant === 'leverage_stop_uniform_50x_200bps') return 'Uniform 50x / 200bps';
  if (variant === 'leverage_stop_uniform_20x_500bps') return 'Uniform 20x / 500bps';
  if (variant === 'leverage_stop_uniform_10x_1000bps') return 'Uniform 10x / 1000bps';
  if (variant === 'leverage_stop_profile_btc100_eth200_zec500') return 'Profile BTC100 ETH200 ZEC500';
  if (variant === 'leverage_stop_profile_btc125_eth500_zec1000') return 'Profile BTC125 ETH500 ZEC1000';
  if (variant === 'fixed_stop_structural_control_100bps') return 'Structural Control 100bps';
  if (variant === 'fixed_stop_structural_control_125bps') return 'Structural Control 125bps';
  if (variant === 'fixed_stop_uniform_100x_100bps') return 'Fixed 100x / 1.0%';
  if (variant === 'fixed_stop_uniform_50x_200bps') return 'Fixed 50x / 2.0%';
  if (variant === 'fixed_stop_uniform_20x_500bps') return 'Fixed 20x / 5.0%';
  if (variant === 'fixed_stop_uniform_10x_1000bps') return 'Fixed 10x / 10.0%';
  if (variant === 'fixed_stop_profile_btc100_eth200_zec500') return 'Fixed Profile BTC100 ETH200 ZEC500';
  if (variant === 'fixed_stop_profile_btc125_eth500_zec1000') return 'Fixed Profile BTC125 ETH500 ZEC1000';
  if (variant === 'candidate_displacement_atr_regime') return 'Displacement ATR Regime';
  if (variant === 'system_b_alert_score') return 'B Alert Score';
  if (variant === 'system_b_alert_required') return 'B Alert Required';
  return variant;
}

function stopLabel(stopMode) {
  if (stopMode === 'sweep') return 'Sweep Wick';
  if (stopMode === 'sweep-buffer') return 'Sweep Wide Buffer';
  if (stopMode === 'sweep-close-confirmed') return 'Sweep Close Confirmed';
  if (stopMode === 'leverage-floor') return 'Leverage Floor';
  if (stopMode === 'leverage-profile') return 'Leverage Profile';
  if (stopMode === 'structural-control') return 'Structural Control';
  if (stopMode === 'fixed-percent') return 'Fixed Percent';
  if (stopMode === 'fixed-percent-profile') return 'Fixed Percent Profile';
  if (stopMode === 'mss-swing') return 'MSS Swing';
  if (stopMode === 'retest-poi') return 'Retest POI';
  return stopMode;
}

function safePath(value, reportPath) {
  if (!value) return null;
  if (path.isAbsolute(value)) return value;
  const fromRepo = path.resolve(repoRoot, value);
  if (fs.existsSync(fromRepo)) return fromRepo;
  return path.resolve(path.dirname(reportPath), value);
}

function parseEntrySignal(signal) {
  const text = String(signal || '');
  const sideMatch = text.match(/V7[A-Z]*-(L|S)-/);
  const systemMatch = text.match(/-SYS(.+?)-STOP/);
  const stopModeMatch = text.match(/-STOP(.+?)-(?:PDL|PWL|PML|SWING_LOW|PDH|PWH|PMH|SWING_HIGH)-L/);
  const levelMatch = text.match(/-(PDL|PWL|PML|SWING_LOW|PDH|PWH|PMH|SWING_HIGH)-L/);
  const values = {};
  for (const [name, pattern] of Object.entries({
    armedLevel: /-L(-?\d+(?:\.\d+)?)/,
    levelQuality: /-Q(-?\d+(?:\.\d+)?)/,
    qualityScore: /-C(-?\d+(?:\.\d+)?)/,
    riskPct: /-R(-?\d+(?:\.\d+)?)/,
    mssAge: /-M(-?\d+(?:\.\d+)?|NaN)/,
    alertAge: /-A(-?\d+(?:\.\d+)?|NaN)/,
    strengthAge: /-S(-?\d+(?:\.\d+)?|NaN)/,
    strengthSlope: /-SS(-?\d+(?:\.\d+)?|NaN)/,
    entryRiskBps: /-RB(-?\d+(?:\.\d+)?|NaN)/,
    atrBps: /-ATR(-?\d+(?:\.\d+)?|NaN)/,
    entryRangeBps: /-ER(-?\d+(?:\.\d+)?|NaN)/,
    entryRangeAtr: /-DR(-?\d+(?:\.\d+)?|NaN)/,
    stopDistanceAtr: /-RA(-?\d+(?:\.\d+)?|NaN)/,
    minRiskFloorBps: /-MF(-?\d+(?:\.\d+)?|NaN)/,
    fixedStopBps: /-FB(-?\d+(?:\.\d+)?|NaN)/,
    stopBufferBps: /-SB(-?\d+(?:\.\d+)?|NaN)/,
    stopExitModeCode: /-XM(-?\d+(?:\.\d+)?|NaN)/,
    tp1R: /-T1(-?\d+(?:\.\d+)?|NaN)/,
    profileOk: /-PF(-?\d+(?:\.\d+)?|NaN)/,
    stop: /-SL(-?\d+(?:\.\d+)?)/,
  })) {
    const match = text.match(pattern);
    values[name] = match ? nullable(num(match[1])) : null;
  }
  const biasMatch = text.match(/-B(-?\d+)\/(-?\d+)/);
  const tpMatch = text.match(/-TP(-?\d+(?:\.\d+)?)\/(-?\d+(?:\.\d+)?)\/(-?\d+(?:\.\d+)?)/);
  return {
    side: sideMatch?.[1] === 'L' ? 'long' : sideMatch?.[1] === 'S' ? 'short' : 'unknown',
    commentSystem: systemMatch?.[1] || null,
    commentStopMode: stopModeMatch?.[1] || null,
    levelFamily: levelMatch?.[1] || 'unknown',
    bias4h: biasMatch ? num(biasMatch[1]) : null,
    bias1d: biasMatch ? num(biasMatch[2]) : null,
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
    if (!groups.has(key)) {
      groups.set(key, { entry: row, exits: [], firstRowIndex: index });
    }
    if (rows[index - 1] && /^Exit\b/i.test(rows[index - 1].Type || '')) {
      groups.get(key).exits.push(rows[index - 1]);
    }
  }
  return [...groups.values()].map((group) => {
    const info = parseEntrySignal(group.entry.Signal);
    const entryPrice = num(group.entry['Price USDT']);
    const qty = group.exits.reduce((sum, row) => sum + finite(num(row?.['Size (qty)'])), 0);
    const riskDistance = info.side === 'long' ? entryPrice - info.stop : info.side === 'short' ? info.stop - entryPrice : NaN;
    const riskUsd = Number.isFinite(riskDistance) && riskDistance > 0 ? riskDistance * qty : NaN;
    const riskBps = Number.isFinite(riskDistance) && Number.isFinite(entryPrice) && entryPrice !== 0 ? Math.abs(riskDistance) / entryPrice * 10000 : NaN;
    const pnl = group.exits.reduce((sum, row) => sum + finite(num(firstField(row || {}, ['Net P&L USDT', 'Net PnL USDT']))), 0);
    const mfeUsd = group.exits.reduce((sum, row) => sum + finite(num(row?.['Favorable excursion USDT'])), 0);
    const maeUsd = group.exits.reduce((sum, row) => sum + finite(num(row?.['Adverse excursion USDT'])), 0);
    const exitEvents = group.exits
      .map((row) => ({ row, event: classifyExit(row || {}, info), time: row?.['Date and time'] || '' }))
      .filter((event) => event.row);
    const firstClosedEvent = exitEvents.find((event) => event.event !== 'open') || null;
    const openEvent = exitEvents.find((event) => event.event === 'open') || null;
    return {
      entryTime: group.entry['Date and time'],
      entrySignal: group.entry.Signal,
      entryPrice,
      qty,
      riskDistance,
      riskUsd,
      riskBps: nullable(riskBps),
      pnl,
      mfeUsd,
      maeUsd,
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

function bucket(value, cuts, labels) {
  if (!Number.isFinite(value)) return 'unknown';
  for (let index = 0; index < cuts.length; index += 1) {
    if (value <= cuts[index]) return labels[index];
  }
  return labels[labels.length - 1];
}

function riskBucket(item) {
  return bucket(item.riskBps, [100, 175], ['risk<=100', 'risk100-175', 'risk>175']);
}

function atrBucket(item) {
  return bucket(item.atrBps, [75, 150], ['atr<=75', 'atr75-150', 'atr>150']);
}

function rangeBucket(item) {
  return bucket(item.entryRangeBps, [40, 90], ['range<=40', 'range40-90', 'range>90']);
}

function displacementBucket(item) {
  return bucket(item.entryRangeAtr, [1.25, 1.5], ['disp<=1.25atr', 'disp1.25-1.5atr', 'disp>1.5atr']);
}

function stopFloorBucket(item) {
  if (!Number.isFinite(item.minRiskFloorBps)) return 'floor_unknown';
  if (item.minRiskFloorBps < 75) return 'floor_baseline';
  if (item.minRiskFloorBps < 100) return 'floor75';
  if (item.minRiskFloorBps < 125) return 'floor100';
  return 'floor125plus';
}

function exitReasonBucket(item) {
  return item.firstEvent || 'unknown';
}

function summarizeParents(parents, fields) {
  const total = parents.length;
  const closed = parents.filter((item) => !item.hasOpenExit);
  const firstTp = parents.filter((item) => /^tp/.test(item.firstEvent)).length;
  const firstStop = parents.filter((item) => item.firstEvent === 'stop' || item.firstEvent === 'close_stop').length;
  const firstCloseStop = parents.filter((item) => item.firstEvent === 'close_stop').length;
  const maxHold = parents.filter((item) => item.firstEvent === 'max_hold').length;
  const unknown = parents.filter((item) => item.firstEvent === 'unknown').length;
  const open = parents.filter((item) => item.hasOpenExit).length;
  return {
    ...fields,
    parentTrades: total,
    closedParentTrades: closed.length,
    openParentTrades: open,
    tpBeforeStopRatePct: pct(firstTp, total),
    stopBeforeTpRatePct: pct(firstStop, total),
    closeStopFirstRatePct: pct(firstCloseStop, total),
    maxHoldFirstRatePct: pct(maxHold, total),
    unknownFirstRatePct: pct(unknown, total),
    avgMfeR: average(parents.map((item) => item.mfeR)),
    avgMaeR: average(parents.map((item) => item.maeR)),
    avgRiskBps: average(parents.map((item) => item.riskBps)),
    avgRiskPct: average(parents.map((item) => item.riskPct)),
    avgMssAge: average(parents.map((item) => item.mssAge)),
    avgAlertAge: average(parents.map((item) => item.alertAge)),
    avgStrengthAge: average(parents.map((item) => item.strengthAge)),
    avgStrengthSlope: average(parents.map((item) => item.strengthSlope)),
    avgAtrBps: average(parents.map((item) => item.atrBps)),
    avgEntryRangeBps: average(parents.map((item) => item.entryRangeBps)),
    avgEntryRangeAtr: average(parents.map((item) => item.entryRangeAtr)),
    avgStopDistanceAtr: average(parents.map((item) => item.stopDistanceAtr)),
    avgMinRiskFloorBps: average(parents.map((item) => item.minRiskFloorBps)),
    avgFixedStopBps: average(parents.map((item) => item.fixedStopBps)),
    avgStopBufferBps: average(parents.map((item) => item.stopBufferBps)),
    avgTp1R: average(parents.map((item) => item.tp1R)),
    avgLevelQuality: average(parents.map((item) => item.levelQuality)),
    avgQualityScore: average(parents.map((item) => item.qualityScore)),
    closedNetPnlFromParents: closed.reduce((sum, item) => sum + item.pnl, 0),
    longParents: parents.filter((item) => item.side === 'long').length,
    shortParents: parents.filter((item) => item.side === 'short').length,
  };
}

function sumRows(rows, field) {
  return rows.reduce((sum, row) => sum + finite(row.report[field]), 0);
}

function reportFromParents(parents) {
  const ordered = [...parents].sort((a, b) => {
    const aTime = Date.parse(a.entryTime || '');
    const bTime = Date.parse(b.entryTime || '');
    return finite(aTime) - finite(bTime);
  });
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
    closedNetPnl: pnlValues.reduce((sum, value) => sum + value, 0),
    openPnl: 0,
    openTrades: 0,
    maxDrawdownPct,
    totalTrades,
    winRatePct: totalTrades ? winningTrades / totalTrades * 100 : null,
    profitFactor: grossLoss > 0 ? grossProfit / grossLoss : grossProfit > 0 ? null : 0,
    grossProfit,
    grossLoss,
    winningTrades,
    losingTrades,
  };
}

function metricOrFallback(value, fallback) {
  return Number.isFinite(nullable(value)) ? nullable(value) : nullable(fallback);
}

function summarizeRows(rows, fields) {
  const grossProfit = sumRows(rows, 'grossProfit');
  const grossLoss = sumRows(rows, 'grossLoss');
  const trades = sumRows(rows, 'totalTrades');
  const wins = sumRows(rows, 'winningTrades');
  const losses = sumRows(rows, 'losingTrades');
  return {
    ...fields,
    rows: rows.length,
    totalPnl: sumRows(rows, 'totalPnl'),
    closedNetPnl: sumRows(rows, 'closedNetPnl'),
    openPnl: sumRows(rows, 'openPnl'),
    grossProfit,
    grossLoss,
    profitFactor: grossLoss > 0 ? grossProfit / grossLoss : grossProfit > 0 ? null : 0,
    totalTrades: trades,
    winningTrades: wins,
    losingTrades: losses,
    winRatePct: trades ? wins / trades * 100 : null,
    maxRowDrawdownPct: Math.max(...rows.map((row) => finite(row.report.maxDrawdownPct))),
    avgRowDrawdownPct: average(rows.map((row) => row.report.maxDrawdownPct)),
    positiveRows: rows.filter((row) => finite(row.report.totalPnl) > 0).length,
    openTrades: sumRows(rows, 'openTrades'),
    notEnoughDataRows: rows.filter((row) => row.report.hasNotEnoughData).length,
  };
}

function fmt(value, digits = 2) {
  return Number.isFinite(value) ? value.toFixed(digits) : 'n/a';
}

function readReports() {
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
  const runMeta = new Map(manifest.runs.map((run) => [run.id, run]));
  const selected = new Map();
  const allReports = walk(automationDir, (file) => path.basename(file) === 'pine-text-matrix-report.json');
  const rejected = [];
  for (const reportPath of allReports) {
    let report;
    try {
      report = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
    } catch (error) {
      rejected.push({ reportPath, reason: error.message });
      continue;
    }
    const runId = report.runId;
    const meta = runMeta.get(runId);
    if (!meta) continue;
    for (const result of report.results || []) {
      if (result.status !== 'ok') continue;
      const noTradeData = result.strategyData?.status === 'no_trade_data' || result.noTradeData || result.metrics?.hasNotEnoughData;
      const strategyFile = safePath(result.strategyData?.path, reportPath);
      if ((!strategyFile || !fs.existsSync(strategyFile)) && !noTradeData) {
        rejected.push({ reportPath, runId, symbol: result.symbol, timeframe: result.label, reason: 'missing strategy csv' });
        continue;
      }
      const textPath = safePath(result.textPath, reportPath);
      const key = [runId, result.symbol, result.label].join('|');
      const mtimeTarget = strategyFile && fs.existsSync(strategyFile)
        ? strategyFile
        : textPath && fs.existsSync(textPath)
          ? textPath
          : reportPath;
      const mtimeMs = fs.statSync(mtimeTarget).mtimeMs;
      const candidate = { reportPath, report, meta, result, strategyFile: strategyFile && fs.existsSync(strategyFile) ? strategyFile : null, textPath, mtimeMs, noTradeData };
      const previous = selected.get(key);
      if (!previous || candidate.mtimeMs > previous.mtimeMs) selected.set(key, candidate);
    }
  }
  return { manifest, selected, rejected };
}

function buildRows() {
  const { manifest, selected, rejected } = readReports();
  const rows = [];
  const missing = [];
  for (const run of manifest.runs) {
    for (const symbol of run.symbols || []) {
      for (const timeframe of run.timeframes || []) {
        const key = [run.id, symbol, timeframe.label].join('|');
        const item = selected.get(key);
        if (!item) {
          missing.push({ runId: run.id, system: systemLabel(run.variant), stopMode: stopLabel(run.stopMode), symbol, timeframe: timeframe.label });
          continue;
        }
        const reportText = parseReportText(item.textPath);
        const parents = item.noTradeData ? [] : parentTrades(item.strategyFile);
        const metrics = item.result.metrics || {};
        const fallback = reportFromParents(parents);
        const report = {
          dateRange: metrics.dateRange || null,
          totalPnl: metricOrFallback(metrics.totalPnl, fallback.totalPnl),
          closedNetPnl: metricOrFallback(reportText.closedNetPnl, fallback.closedNetPnl),
          openPnl: metricOrFallback(reportText.openPnl, fallback.openPnl),
          openTrades: metricOrFallback(reportText.openTrades, fallback.openTrades),
          maxDrawdownPct: metricOrFallback(metrics.maxDrawdownPct, fallback.maxDrawdownPct),
          totalTrades: metricOrFallback(metrics.totalTrades, fallback.totalTrades),
          winRatePct: metricOrFallback(metrics.profitableTradesPct, fallback.winRatePct),
          profitFactor: metricOrFallback(metrics.profitFactor, fallback.profitFactor),
          grossProfit: metricOrFallback(metrics.grossProfit, fallback.grossProfit),
          grossLoss: metricOrFallback(metrics.grossLoss, fallback.grossLoss),
          winningTrades: metricOrFallback(metrics.winningTrades, fallback.winningTrades),
          losingTrades: metricOrFallback(metrics.losingTrades, fallback.losingTrades),
          hasNotEnoughData: Boolean(metrics.hasNotEnoughData),
        };
        rows.push({
          runId: run.id,
          system: systemLabel(run.variant),
          variant: run.variant,
          stopMode: stopLabel(run.stopMode),
          stopModeId: run.stopMode,
          symbol,
          timeframe: timeframe.label,
          interval: timeframe.interval,
          sourceFile: item.strategyFile,
          reportPath: item.reportPath,
          textPath: item.textPath,
          mtimeMs: item.mtimeMs,
          report,
          execution: {
            validFullClose: finite(report.openTrades) === 0 && Math.abs(finite(report.openPnl)) < initialCapital * 0.001,
            openPnlPctInitialCapital: finite(report.openPnl) / initialCapital * 100,
            singleExitHarness: parents.every((parent) => parent.exitCount <= 1),
            parentTradeCountMatchesReport: finite(report.totalTrades) === parents.length,
          },
          telemetry: summarizeParents(parents, {}),
          parents: parents.map((parent) => ({
            ...parent,
            runId: run.id,
            system: systemLabel(run.variant),
            variant: run.variant,
            stopMode: stopLabel(run.stopMode),
            stopModeId: run.stopMode,
            symbol,
            timeframe: timeframe.label,
          })),
        });
      }
    }
  }
  return { rows, missing, rejected };
}

function aggregate(rows) {
  const allParents = rows.flatMap((row) => row.parents);
  const rowSummaries = [];
  for (const [key, group] of groupBy(rows, (row) => [row.system, row.stopMode].join('|'))) {
    const [system, stopMode] = key.split('|');
    rowSummaries.push(summarizeRows(group, { system, stopMode, symbol: 'basket', timeframe: 'all' }));
  }
  for (const [key, group] of groupBy(rows, (row) => [row.system, row.stopMode, row.timeframe].join('|'))) {
    const [system, stopMode, timeframe] = key.split('|');
    rowSummaries.push(summarizeRows(group, { system, stopMode, symbol: 'basket', timeframe }));
  }
  for (const [key, group] of groupBy(rows, (row) => [row.system, row.stopMode, row.symbol].join('|'))) {
    const [system, stopMode, symbol] = key.split('|');
    rowSummaries.push(summarizeRows(group, { system, stopMode, symbol, timeframe: 'all' }));
  }

  const telemetry = [];
  for (const [key, parents] of groupBy(allParents, (item) => [item.system, item.stopMode].join('|'))) {
    const [system, stopMode] = key.split('|');
    telemetry.push(summarizeParents(parents, { system, stopMode, symbol: 'basket', timeframe: 'all', side: 'all' }));
  }
  for (const [key, parents] of groupBy(allParents, (item) => [item.system, item.stopMode, item.timeframe].join('|'))) {
    const [system, stopMode, timeframe] = key.split('|');
    telemetry.push(summarizeParents(parents, { system, stopMode, symbol: 'basket', timeframe, side: 'all' }));
  }
  for (const [key, parents] of groupBy(allParents, (item) => [item.system, item.stopMode, item.symbol, item.timeframe].join('|'))) {
    const [system, stopMode, symbol, timeframe] = key.split('|');
    telemetry.push(summarizeParents(parents, { system, stopMode, symbol, timeframe, side: 'all' }));
  }
  for (const [key, parents] of groupBy(allParents, (item) => [item.system, item.stopMode, item.symbol, item.timeframe, item.side].join('|'))) {
    const [system, stopMode, symbol, timeframe, side] = key.split('|');
    telemetry.push(summarizeParents(parents, { system, stopMode, symbol, timeframe, side }));
  }

  const regimeTelemetry = [];
  for (const [key, parents] of groupBy(allParents, (item) => [item.system, item.stopMode, riskBucket(item)].join('|'))) {
    const [system, stopMode, bucketName] = key.split('|');
    regimeTelemetry.push(summarizeParents(parents, { system, stopMode, regimeType: 'risk_bps', regime: bucketName }));
  }
  for (const [key, parents] of groupBy(allParents, (item) => [item.system, item.stopMode, atrBucket(item)].join('|'))) {
    const [system, stopMode, bucketName] = key.split('|');
    regimeTelemetry.push(summarizeParents(parents, { system, stopMode, regimeType: 'atr_bps', regime: bucketName }));
  }
  for (const [key, parents] of groupBy(allParents, (item) => [item.system, item.stopMode, rangeBucket(item)].join('|'))) {
    const [system, stopMode, bucketName] = key.split('|');
    regimeTelemetry.push(summarizeParents(parents, { system, stopMode, regimeType: 'entry_range_bps', regime: bucketName }));
  }
  for (const [key, parents] of groupBy(allParents, (item) => [item.system, item.stopMode, displacementBucket(item)].join('|'))) {
    const [system, stopMode, bucketName] = key.split('|');
    regimeTelemetry.push(summarizeParents(parents, { system, stopMode, regimeType: 'entry_range_atr', regime: bucketName }));
  }
  for (const [key, parents] of groupBy(allParents, (item) => [item.system, item.stopMode, stopFloorBucket(item)].join('|'))) {
    const [system, stopMode, bucketName] = key.split('|');
    regimeTelemetry.push(summarizeParents(parents, { system, stopMode, regimeType: 'stop_floor_bps', regime: bucketName }));
  }
  for (const [key, parents] of groupBy(allParents, (item) => [item.system, item.stopMode, exitReasonBucket(item)].join('|'))) {
    const [system, stopMode, bucketName] = key.split('|');
    regimeTelemetry.push(summarizeParents(parents, { system, stopMode, regimeType: 'exit_reason', regime: bucketName }));
  }
  return { rowSummaries, telemetry, regimeTelemetry };
}

function markdown(rows, missing, rejected, rowSummaries, telemetry, regimeTelemetry, expectedSlots) {
  const lines = [`# ${reportTitle}`, ''];
  lines.push(`Generated from ${rows.length} selected strategy exports. Expected slots: ${expectedSlots}. Missing slots: ${missing.length}.`);
  lines.push('');
  lines.push('## Coverage');
  lines.push('| Missing | Rejected report candidates | Invalid full-close rows | Parent/report mismatches |');
  lines.push('|---:|---:|---:|---:|');
  lines.push(`| ${missing.length} | ${rejected.length} | ${rows.filter((row) => !row.execution.validFullClose).length} | ${rows.filter((row) => !row.execution.parentTradeCountMatchesReport).length} |`);
  if (missing.length) {
    lines.push('');
    lines.push('Missing slots:');
    for (const item of missing) lines.push(`- ${item.system} / ${item.stopMode} / ${item.symbol} / ${item.timeframe}`);
  }
  lines.push('');
  lines.push('## Basket Backtest Summary');
  lines.push('| System | Stop | Rows | Trades | Total P&L | Closed Net | PF | Win % | Max Row DD % | Positive Rows | NED Rows |');
  lines.push('|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|');
  for (const row of rowSummaries.filter((item) => item.symbol === 'basket' && item.timeframe === 'all')) {
    lines.push(`| ${row.system} | ${row.stopMode} | ${row.rows} | ${fmt(row.totalTrades, 0)} | ${fmt(row.totalPnl)} | ${fmt(row.closedNetPnl)} | ${fmt(row.profitFactor, 3)} | ${fmt(row.winRatePct, 1)} | ${fmt(row.maxRowDrawdownPct, 2)} | ${row.positiveRows} | ${row.notEnoughDataRows} |`);
  }
  lines.push('');
  lines.push('## Basket Telemetry');
  lines.push('| System | Stop | Parents | TP1 First % | Stop First % | CloseStop % | MaxHold % | Avg MFE R | Avg MAE R | Avg Risk bps | Avg Min Floor bps | Avg Fixed Stop bps | Avg Buffer bps | Avg Range/ATR | Avg Stop/ATR | Avg TP1 R | Avg Alert Age | Avg Strength Slope | Long | Short |');
  lines.push('|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|');
  for (const row of telemetry.filter((item) => item.symbol === 'basket' && item.timeframe === 'all' && item.side === 'all')) {
    lines.push(`| ${row.system} | ${row.stopMode} | ${row.parentTrades} | ${fmt(row.tpBeforeStopRatePct, 1)} | ${fmt(row.stopBeforeTpRatePct, 1)} | ${fmt(row.closeStopFirstRatePct, 1)} | ${fmt(row.maxHoldFirstRatePct, 1)} | ${fmt(row.avgMfeR, 2)} | ${fmt(row.avgMaeR, 2)} | ${fmt(row.avgRiskBps, 1)} | ${fmt(row.avgMinRiskFloorBps, 1)} | ${fmt(row.avgFixedStopBps, 1)} | ${fmt(row.avgStopBufferBps, 1)} | ${fmt(row.avgEntryRangeAtr, 2)} | ${fmt(row.avgStopDistanceAtr, 2)} | ${fmt(row.avgTp1R, 2)} | ${fmt(row.avgAlertAge, 1)} | ${fmt(row.avgStrengthSlope, 3)} | ${row.longParents} | ${row.shortParents} |`);
  }
  lines.push('');
  lines.push('## Symbol/Timeframe Backtest');
  lines.push('| System | Stop | Symbol | TF | Trades | Total P&L | PF | Win % | DD % | NED | Source |');
  lines.push('|---|---|---|---:|---:|---:|---:|---:|---:|---|---|');
  for (const row of rows) {
    const source = row.sourceFile ? path.relative(outputDir, row.sourceFile) : 'no trade data';
    lines.push(`| ${row.system} | ${row.stopMode} | ${row.symbol} | ${row.timeframe} | ${fmt(row.report.totalTrades, 0)} | ${fmt(row.report.totalPnl)} | ${fmt(row.report.profitFactor, 3)} | ${fmt(row.report.winRatePct, 1)} | ${fmt(row.report.maxDrawdownPct, 2)} | ${row.report.hasNotEnoughData ? 'yes' : 'no'} | ${source} |`);
  }
  lines.push('');
  lines.push('## Symbol/Timeframe Telemetry');
  lines.push('| System | Stop | Symbol | TF | Side | Parents | TP1 First % | Stop First % | CloseStop % | Avg MFE R | Avg MAE R | Avg Risk bps | Avg Min Floor bps | Avg Fixed Stop bps | Avg Buffer bps | Avg MSS Age | Avg Alert Age | Avg Strength Age | Avg Strength Slope |');
  lines.push('|---|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|');
  for (const row of telemetry.filter((item) => item.symbol !== 'basket')) {
    lines.push(`| ${row.system} | ${row.stopMode} | ${row.symbol} | ${row.timeframe} | ${row.side} | ${row.parentTrades} | ${fmt(row.tpBeforeStopRatePct, 1)} | ${fmt(row.stopBeforeTpRatePct, 1)} | ${fmt(row.closeStopFirstRatePct, 1)} | ${fmt(row.avgMfeR, 2)} | ${fmt(row.avgMaeR, 2)} | ${fmt(row.avgRiskBps, 1)} | ${fmt(row.avgMinRiskFloorBps, 1)} | ${fmt(row.avgFixedStopBps, 1)} | ${fmt(row.avgStopBufferBps, 1)} | ${fmt(row.avgMssAge, 1)} | ${fmt(row.avgAlertAge, 1)} | ${fmt(row.avgStrengthAge, 1)} | ${fmt(row.avgStrengthSlope, 3)} |`);
  }
  lines.push('');
  lines.push('## Regime Telemetry');
  lines.push('| System | Stop | Regime Type | Regime | Parents | P&L | TP1 First % | Stop First % | CloseStop % | Avg MFE R | Avg MAE R | Avg Risk bps | Avg Min Floor bps | Avg Fixed Stop bps | Avg Buffer bps | Avg ATR bps | Avg Range bps | Avg Range/ATR | Avg Stop/ATR | Avg TP1 R | Long | Short |');
  lines.push('|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|');
  for (const row of regimeTelemetry) {
    lines.push(`| ${row.system} | ${row.stopMode} | ${row.regimeType} | ${row.regime} | ${row.parentTrades} | ${fmt(row.closedNetPnlFromParents)} | ${fmt(row.tpBeforeStopRatePct, 1)} | ${fmt(row.stopBeforeTpRatePct, 1)} | ${fmt(row.closeStopFirstRatePct, 1)} | ${fmt(row.avgMfeR, 2)} | ${fmt(row.avgMaeR, 2)} | ${fmt(row.avgRiskBps, 1)} | ${fmt(row.avgMinRiskFloorBps, 1)} | ${fmt(row.avgFixedStopBps, 1)} | ${fmt(row.avgStopBufferBps, 1)} | ${fmt(row.avgAtrBps, 1)} | ${fmt(row.avgEntryRangeBps, 1)} | ${fmt(row.avgEntryRangeAtr, 2)} | ${fmt(row.avgStopDistanceAtr, 2)} | ${fmt(row.avgTp1R, 2)} | ${row.longParents} | ${row.shortParents} |`);
  }
  return `${lines.join('\n')}\n`;
}

const { rows, missing, rejected } = buildRows();
const { rowSummaries, telemetry, regimeTelemetry } = aggregate(rows);
ensureDir(outputDir);
const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
const expectedSlots = manifest.runs.reduce((sum, run) => {
  return sum + (run.symbols || []).length * (run.timeframes || []).length;
}, 0);

const publicRows = rows.map(({ parents, ...row }) => row);
fs.writeFileSync(path.join(outputDir, `${outputName}.json`), JSON.stringify({
  generatedAt: new Date().toISOString(),
  manifestPath,
  automationDir,
  initialCapital,
  expectedSlots,
  selectedSlots: rows.length,
  missing,
  rejected,
  rows: publicRows,
  rowSummaries,
  telemetry,
  regimeTelemetry,
}, null, 2));
fs.writeFileSync(path.join(outputDir, `${outputName}.md`), markdown(rows, missing, rejected, rowSummaries, telemetry, regimeTelemetry, expectedSlots));

console.log(JSON.stringify({
  outputDir,
  expectedSlots,
  selectedSlots: rows.length,
  missingSlots: missing.length,
  rejectedCandidates: rejected.length,
  invalidFullCloseRows: rows.filter((row) => !row.execution.validFullClose).length,
  parentReportMismatches: rows.filter((row) => !row.execution.parentTradeCountMatchesReport).length,
}, null, 2));
