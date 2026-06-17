#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { parseCsv } from '../../../../codex/skills/tradingview-pine-loop/scripts/lib/csv.mjs';

const root = path.resolve(process.cwd());
const artifactRoot = path.join(root, 'tradingview/strategy/artifacts/v7_pdf_strategy_refinement');
const sourceDir = path.join(root, 'tradingview/strategy/artifacts/v7_artifacts');
const outJson = path.join(artifactRoot, 'pdf_refinement_candidate_metrics.json');
const outMd = path.join(artifactRoot, 'pdf_refinement_candidate_metrics.md');

const numPattern = '(?:NaN|-?\\d+(?:\\.\\d+)?)';
const fieldPattern = new RegExp(
  `-Q(?<Q>${numPattern})-C(?<C>${numPattern})-R(?<R>${numPattern})` +
  `-B(?<B4H>-?\\d+)/(?<B1D>-?\\d+)` +
  `-M(?<M>${numPattern})-A(?<A>${numPattern})-S(?<S>${numPattern})-SS(?<SS>${numPattern})` +
  `-RB(?<RB>${numPattern})-ATR(?<ATR>${numPattern})-ER(?<ER>${numPattern})` +
  `-DR(?<DR>${numPattern})-RA(?<RA>${numPattern})`,
);
const levelPattern = /-STOP[^-]+-(?<level>[A-Z_]+)-L(?<levelPrice>[^-]+)-Q/;

function numeric(value) {
  const cleaned = String(value ?? '').replace(/[%,$\s]/g, '');
  if (!cleaned || cleaned === 'NaN') return null;
  const parsed = Number(cleaned);
  return Number.isFinite(parsed) ? parsed : null;
}

function routeFromFile(file) {
  const match = path.basename(file).match(/Quality_Score_3_(.+?)_2026-/);
  return match ? match[1].replace('_', ':') : path.basename(file, '.csv');
}

function parseDate(value) {
  const [date, time] = String(value).split(' ');
  const [year, month, day] = date.split('-').map(Number);
  const [hour, minute] = time.split(':').map(Number);
  return new Date(Date.UTC(year, month - 1, day, hour, minute));
}

function parseSignal(signal) {
  const parsed = {};
  const fields = fieldPattern.exec(signal)?.groups || {};
  for (const [key, value] of Object.entries(fields)) {
    parsed[key] = key === 'B4H' || key === 'B1D' ? Number(value) : numeric(value);
  }
  if (fields.B4H && fields.B1D) parsed.B = `${fields.B4H}/${fields.B1D}`;
  const level = levelPattern.exec(signal)?.groups || {};
  if (level.level) parsed.level = level.level;
  if (level.levelPrice) parsed.levelPrice = numeric(level.levelPrice);
  return parsed;
}

function stats(rows) {
  const pnl = rows.map((row) => row.pnl).filter(Number.isFinite);
  const grossProfit = pnl.filter((value) => value > 0).reduce((sum, value) => sum + value, 0);
  const grossLoss = -pnl.filter((value) => value < 0).reduce((sum, value) => sum + value, 0);
  return {
    trades: rows.length,
    net: pnl.reduce((sum, value) => sum + value, 0),
    pf: grossLoss > 0 ? grossProfit / grossLoss : null,
    winPct: rows.length ? (pnl.filter((value) => value > 0).length / rows.length) * 100 : 0,
  };
}

function groupBy(rows, keyFn) {
  const groups = new Map();
  for (const row of rows) {
    const key = keyFn(row);
    groups.set(key, [...(groups.get(key) || []), row]);
  }
  return [...groups.entries()]
    .map(([key, grouped]) => ({ key, ...stats(grouped) }))
    .sort((a, b) => String(a.key).localeCompare(String(b.key)));
}

function table(title, rows) {
  const lines = [
    `### ${title}`,
    '',
    '| Key | Trades | Net | PF | Win % |',
    '|---|---:|---:|---:|---:|',
  ];
  for (const row of rows) {
    lines.push(`| ${row.key} | ${row.trades} | ${row.net.toFixed(2)} | ${row.pf == null ? 'inf' : row.pf.toFixed(3)} | ${row.winPct.toFixed(1)} |`);
  }
  lines.push('');
  return lines.join('\n');
}

const files = fs.readdirSync(sourceDir)
  .filter((file) => file.endsWith('.csv'))
  .map((file) => path.join(sourceDir, file))
  .sort();

const trades = [];
for (const file of files) {
  const rows = parseCsv(fs.readFileSync(file, 'utf8').replace(/^\uFEFF/, ''));
  const byNumber = new Map();
  for (const row of rows) {
    const key = row['Trade number'];
    const current = byNumber.get(key) || {};
    if (/^Entry/i.test(row.Type)) current.entry = row;
    if (/^Exit/i.test(row.Type)) current.exit = row;
    byNumber.set(key, current);
  }
  for (const [tradeNumber, pair] of byNumber.entries()) {
    if (!pair.entry || !pair.exit) continue;
    const entryAt = parseDate(pair.entry['Date and time']);
    trades.push({
      route: routeFromFile(file),
      tradeNumber: Number(tradeNumber),
      side: /long/i.test(pair.entry.Type) ? 'long' : 'short',
      entryAt,
      entryMinute: entryAt.getUTCMinutes(),
      entryHour: entryAt.getUTCHours(),
      weekday: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'][entryAt.getUTCDay()],
      pnl: numeric(pair.exit['Net PnL USDT'] || pair.exit['Net PnL BTC']),
      ...parseSignal(pair.entry.Signal),
    });
  }
}

const filters = {
  '30m/1h close alignment': (row) => row.entryMinute === 0 || row.entryMinute === 30,
  'stop ATR floor >= 3': (row) => Number.isFinite(row.RA) && row.RA >= 3,
  '30m/1h + stop ATR floor': (row) => (row.entryMinute === 0 || row.entryMinute === 30) && Number.isFinite(row.RA) && row.RA >= 3,
  'fresh strength <= 2 bars': (row) => Number.isFinite(row.S) && row.S <= 2,
  '30m/1h + fresh strength + stop ATR floor': (row) => (row.entryMinute === 0 || row.entryMinute === 30) && Number.isFinite(row.S) && row.S <= 2 && Number.isFinite(row.RA) && row.RA >= 3,
  'daily-confirmed longs': (row) => !(row.side === 'long' && !(row.B4H === 1 && row.B1D === 1)),
};

const report = {
  sourceDir,
  files: files.map((file) => path.relative(root, file)),
  baseline: stats(trades),
  groups: {
    routeSide: groupBy(trades, (row) => `${row.route} ${row.side}`),
    level: groupBy(trades, (row) => row.level || 'unknown'),
    quality: groupBy(trades, (row) => `Q${row.Q} C${row.C}`),
    alertPresence: groupBy(trades, (row) => `${row.side} ${Number.isFinite(row.A) ? 'alert' : 'no_alert'}`),
    biasSide: groupBy(trades, (row) => `${row.B || 'unknown'} ${row.side}`),
    strengthAge: groupBy(trades, (row) => {
      if (!Number.isFinite(row.S)) return 'Sna';
      if (row.S <= 2) return 'S0-2';
      if (row.S <= 6) return 'S3-6';
      return 'S7+';
    }),
    riskBps: groupBy(trades, (row) => {
      if (!Number.isFinite(row.RB)) return 'RBna';
      if (row.RB < 150) return 'RB<150';
      if (row.RB < 250) return 'RB150-250';
      return 'RB250+';
    }),
    stopAtr: groupBy(trades, (row) => {
      if (!Number.isFinite(row.RA)) return 'RAna';
      if (row.RA < 3) return 'RA<3';
      if (row.RA < 5) return 'RA3-5';
      return 'RA5+';
    }),
    minute: groupBy(trades, (row) => (row.entryMinute === 0 || row.entryMinute === 30) ? '00/30' : '15/45'),
    weekday: groupBy(trades, (row) => row.weekday),
  },
  filters: Object.fromEntries(Object.entries(filters).map(([name, predicate]) => {
    const kept = trades.filter(predicate);
    const removed = trades.filter((row) => !predicate(row));
    return [name, { kept: stats(kept), removed: stats(removed) }];
  })),
};

fs.mkdirSync(artifactRoot, { recursive: true });
fs.writeFileSync(outJson, `${JSON.stringify(report, null, 2)}\n`);

const lines = [
  '# PDF Refinement Candidate Metrics',
  '',
  `Source exports: ${files.length}`,
  '',
  `Baseline: ${report.baseline.trades} trades, net ${report.baseline.net.toFixed(2)}, PF ${report.baseline.pf.toFixed(3)}, win ${report.baseline.winPct.toFixed(1)}%.`,
  '',
  '## Candidate Post-Filters',
  '',
  '| Filter | Kept Trades | Kept Net | Kept PF | Kept Win % | Removed Trades | Removed Net |',
  '|---|---:|---:|---:|---:|---:|---:|',
];
for (const [name, value] of Object.entries(report.filters)) {
  lines.push(`| ${name} | ${value.kept.trades} | ${value.kept.net.toFixed(2)} | ${value.kept.pf == null ? 'inf' : value.kept.pf.toFixed(3)} | ${value.kept.winPct.toFixed(1)} | ${value.removed.trades} | ${value.removed.net.toFixed(2)} |`);
}
lines.push('');
lines.push(table('Route Side', report.groups.routeSide));
lines.push(table('Level', report.groups.level));
lines.push(table('Quality Pair', report.groups.quality));
lines.push(table('Alert Presence', report.groups.alertPresence));
lines.push(table('Bias Side', report.groups.biasSide));
lines.push(table('Strength Age', report.groups.strengthAge));
lines.push(table('Risk Bps', report.groups.riskBps));
lines.push(table('Stop ATR', report.groups.stopAtr));
lines.push(table('Entry Minute', report.groups.minute));
lines.push(table('Weekday', report.groups.weekday));
fs.writeFileSync(outMd, `${lines.join('\n')}\n`);

console.log(JSON.stringify({
  status: 'ok',
  trades: trades.length,
  outJson,
  outMd,
}, null, 2));
