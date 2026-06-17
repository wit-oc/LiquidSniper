#!/usr/bin/env node
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const args = Object.fromEntries(process.argv.slice(2).map((arg, index, all) => {
  if (!arg.startsWith('--')) return [];
  const key = arg.slice(2);
  const next = all[index + 1];
  return [key, next && !next.startsWith('--') ? next : true];
}).filter((pair) => pair.length));

const root = path.resolve(args.cwd || process.cwd());
const runDir = path.resolve(root, args.runDir || '');
if (!runDir || !fs.existsSync(runDir)) {
  throw new Error(`Missing or invalid --runDir: ${args.runDir || ''}`);
}
const outJson = path.resolve(root, args.outJson || 'tradingview/strategy/artifacts/v7_pdf_strategy_refinement/canary_j_pressure_test_metrics.json');
const outMd = path.resolve(root, args.outMd || 'tradingview/strategy/artifacts/v7_pdf_strategy_refinement/CANARY_J_PRESSURE_TEST_RESULTS.md');

const numPattern = '(?:NaN|-?\\d+(?:\\.\\d+)?)';
const fieldPattern = new RegExp(
  `-Q(?<Q>${numPattern})-C(?<C>${numPattern})-R(?<R>${numPattern})` +
  `-B(?<B4H>-?\\d+)/(?<B1D>-?\\d+)` +
  `-M(?<M>${numPattern})-A(?<A>${numPattern})-S(?<S>${numPattern})-SS(?<SS>${numPattern})` +
  `-RB(?<RB>${numPattern})-ATR(?<ATR>${numPattern})-ER(?<ER>${numPattern})` +
  `-DR(?<DR>${numPattern})-RA(?<RA>${numPattern})`,
);

function rel(file) {
  return path.relative(root, file);
}

function walk(dir, predicate, out = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(full, predicate, out);
    else if (!predicate || predicate(full)) out.push(full);
  }
  return out;
}

function xmlFromZip(file, member) {
  return execFileSync('unzip', ['-p', file, member], { encoding: 'utf8', maxBuffer: 50 * 1024 * 1024 });
}

function decodeXml(value) {
  return String(value || '')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'")
    .replace(/&amp;/g, '&');
}

function columnIndex(ref) {
  const letters = String(ref || '').replace(/\d+/g, '');
  let value = 0;
  for (const char of letters) value = value * 26 + (char.charCodeAt(0) - 64);
  return value - 1;
}

function excelSerialToIso(value) {
  const serial = Number(value);
  if (!Number.isFinite(serial)) return '';
  const millis = Math.round((serial - 25569) * 86400 * 1000);
  const date = new Date(millis);
  return date.toISOString().slice(0, 16).replace('T', ' ');
}

function parseSheetRows(file, sheet = 'xl/worksheets/sheet4.xml') {
  const xml = xmlFromZip(file, sheet);
  const rows = [];
  for (const rowMatch of xml.matchAll(/<row\b[^>]*>([\s\S]*?)<\/row>/g)) {
    const values = [];
    for (const cellMatch of rowMatch[1].matchAll(/<c\b([^>]*)>([\s\S]*?)<\/c>/g)) {
      const attrs = cellMatch[1];
      const body = cellMatch[2];
      const ref = attrs.match(/\br="([^"]+)"/)?.[1] || '';
      const type = attrs.match(/\bt="([^"]+)"/)?.[1] || '';
      const raw = decodeXml(body.match(/<v>([\s\S]*?)<\/v>/)?.[1] || '');
      const index = columnIndex(ref);
      values[index] = type === 'str' ? raw : raw;
    }
    rows.push(values.map((value) => value ?? ''));
  }
  if (!rows.length) return [];
  const headers = rows[0].map((header) => String(header || '').trim());
  return rows.slice(1).map((values) => Object.fromEntries(headers.map((header, index) => {
    const value = values[index] ?? '';
    return [header, header === 'Date and time' ? excelSerialToIso(value) : value];
  })));
}

function numeric(value) {
  const cleaned = String(value ?? '').replace(/[,%$\s]/g, '');
  if (!cleaned || cleaned === 'NaN') return null;
  const parsed = Number(cleaned);
  return Number.isFinite(parsed) ? parsed : null;
}

function parseSignal(signal) {
  const parsed = {};
  const fields = fieldPattern.exec(signal)?.groups || {};
  for (const [key, value] of Object.entries(fields)) {
    parsed[key] = key === 'B4H' || key === 'B1D' ? Number(value) : numeric(value);
  }
  if (fields.B4H && fields.B1D) parsed.B = `${fields.B4H}/${fields.B1D}`;
  return parsed;
}

function symbolFromCsv(file) {
  const match = path.basename(file).match(/^(.+?)_15m_strategy\.csv$/);
  return match ? match[1].replace('_', ':') : path.basename(file, '.csv');
}

function stats(rows) {
  const pnl = rows.map((row) => row.pnl).filter(Number.isFinite);
  const grossProfit = pnl.filter((value) => value > 0).reduce((sum, value) => sum + value, 0);
  const grossLoss = -pnl.filter((value) => value < 0).reduce((sum, value) => sum + value, 0);
  return {
    trades: rows.length,
    net: pnl.reduce((sum, value) => sum + value, 0),
    grossProfit,
    grossLoss,
    pf: grossLoss > 0 ? grossProfit / grossLoss : (grossProfit > 0 ? null : 0),
    winPct: rows.length ? (pnl.filter((value) => value > 0).length / rows.length) * 100 : 0,
    avg: rows.length ? pnl.reduce((sum, value) => sum + value, 0) / rows.length : 0,
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

function strengthAgeBucket(row) {
  if (!Number.isFinite(row.S)) return 'Sna';
  if (row.S <= 2) return 'S0-2';
  if (row.S <= 6) return 'S3-6';
  return 'S7+';
}

function pfText(value) {
  return value == null ? 'n/a' : value.toFixed(3);
}

function metricTable(title, rows) {
  const lines = [
    `## ${title}`,
    '',
    '| Key | Trades | Net USDT | PF | Win % | Avg USDT |',
    '| --- | ---: | ---: | ---: | ---: | ---: |',
  ];
  for (const row of rows) {
    lines.push(`| ${row.key} | ${row.trades} | ${row.net.toFixed(2)} | ${pfText(row.pf)} | ${row.winPct.toFixed(2)} | ${row.avg.toFixed(2)} |`);
  }
  lines.push('');
  return lines.join('\n');
}

const reportPath = path.join(runDir, 'pine-text-matrix-report.json');
const harness = fs.existsSync(reportPath) ? JSON.parse(fs.readFileSync(reportPath, 'utf8')) : null;
const csvFiles = walk(runDir, (file) => file.endsWith('_15m_strategy.csv')).sort();

const trades = [];
for (const file of csvFiles) {
  const symbol = symbolFromCsv(file);
  const rows = parseSheetRows(file);
  const byNumber = new Map();
  for (const row of rows) {
    const key = row['Trade number'];
    const current = byNumber.get(key) || {};
    if (/^Entry/i.test(row.Type || '')) current.entry = row;
    if (/^Exit/i.test(row.Type || '')) current.exit = row;
    byNumber.set(key, current);
  }
  for (const [tradeNumber, pair] of byNumber.entries()) {
    if (!pair.entry || !pair.exit) continue;
    const parsed = parseSignal(pair.entry.Signal);
    trades.push({
      symbol,
      tradeNumber: Number(tradeNumber),
      side: /long/i.test(pair.entry.Type) ? 'long' : 'short',
      entryAt: pair.entry['Date and time'],
      exitAt: pair.exit['Date and time'],
      pnl: numeric(pair.exit['Net PnL USDT']),
      entrySignal: pair.entry.Signal,
      ...parsed,
    });
  }
}

const shortC3 = trades.filter((row) => row.side === 'short' && row.C === 3);
const result = {
  runDir: rel(runDir),
  reportPath: fs.existsSync(reportPath) ? rel(reportPath) : null,
  harness: harness ? {
    status: harness.status,
    itemCount: harness.itemCount,
    symbolsOverride: harness.symbolsOverride || null,
    ranges: (harness.results || []).map((row) => ({
      symbol: row.symbol,
      status: row.status,
      title: row.activeStrategyReportTitle,
      range: row.visibleStrategyReportDateLabel,
    })),
  } : null,
  csvFiles: csvFiles.map(rel),
  basket: stats(trades),
  groups: {
    symbol: groupBy(trades, (row) => row.symbol),
    side: groupBy(trades, (row) => row.side),
    symbolSide: groupBy(trades, (row) => `${row.symbol} ${row.side}`),
    confluence: groupBy(trades, (row) => `${row.side} C${row.C ?? 'na'}`),
    shortC3BySymbol: groupBy(shortC3, (row) => row.symbol),
    shortC3ByStrengthAge: groupBy(shortC3, strengthAgeBucket),
    shortC3DelayedSlopePass: groupBy(shortC3, (row) => {
      const delayed = Number.isFinite(row.S) && row.S >= 3 && row.S <= 6;
      return delayed ? (row.SS <= -0.70 ? 'S3-6 slope<=-0.70' : 'S3-6 slope>-0.70') : 'outside S3-6';
    }),
  },
  trades,
};

fs.mkdirSync(path.dirname(outJson), { recursive: true });
fs.writeFileSync(outJson, `${JSON.stringify(result, null, 2)}\n`);

const lines = [
  '# Canary J Pressure Test Results',
  '',
  `Run directory: \`${result.runDir}\``,
  '',
  '## Harness Proof',
  '',
  `- Status: \`${result.harness?.status || 'unknown'}\``,
  `- Symbols: ${result.harness?.symbolsOverride?.map((symbol) => `\`${symbol}\``).join(', ') || 'unknown'}`,
  '- Layout/title/date-range proof is in the harness JSON and per-symbol report text/screenshots.',
  '',
  '## Basket',
  '',
  '| Trades | Net USDT | Gross Profit | Gross Loss | PF | Win % | Avg USDT |',
  '| ---: | ---: | ---: | ---: | ---: | ---: | ---: |',
  `| ${result.basket.trades} | ${result.basket.net.toFixed(2)} | ${result.basket.grossProfit.toFixed(2)} | ${result.basket.grossLoss.toFixed(2)} | ${pfText(result.basket.pf)} | ${result.basket.winPct.toFixed(2)} | ${result.basket.avg.toFixed(2)} |`,
  '',
  metricTable('By Symbol', result.groups.symbol),
  metricTable('By Side', result.groups.side),
  metricTable('By Symbol And Side', result.groups.symbolSide),
  metricTable('By Side And Confluence', result.groups.confluence),
  metricTable('Short C3 By Symbol', result.groups.shortC3BySymbol),
  metricTable('Short C3 By Strength Age', result.groups.shortC3ByStrengthAge),
  metricTable('Short C3 Delayed Slope Gate', result.groups.shortC3DelayedSlopePass),
  '## Initial Read',
  '',
  'This is a pressure-test artifact, not a final promotion decision. Compare it against the original four-symbol Canary J basket and then run at least one high-beta/failure-control batch before tuning the threshold again.',
  '',
];
fs.writeFileSync(outMd, `${lines.join('\n')}\n`);

console.log(JSON.stringify({
  status: 'ok',
  trades: trades.length,
  outJson,
  outMd,
}, null, 2));
