#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';

function parseArgs(argv = process.argv.slice(2)) {
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

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = '';
  let inQuotes = false;
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    const next = text[i + 1];
    if (inQuotes) {
      if (ch === '"' && next === '"') {
        field += '"';
        i += 1;
      } else if (ch === '"') {
        inQuotes = false;
      } else {
        field += ch;
      }
    } else if (ch === '"') {
      inQuotes = true;
    } else if (ch === ',') {
      row.push(field);
      field = '';
    } else if (ch === '\n') {
      row.push(field);
      rows.push(row);
      row = [];
      field = '';
    } else if (ch !== '\r') {
      field += ch;
    }
  }
  if (field.length || row.length) {
    row.push(field);
    rows.push(row);
  }
  return rows;
}

function numeric(value) {
  if (value == null) return null;
  const cleaned = String(value).replace(/\uFEFF/g, '').replace(/\u2212/g, '-').replace(/[,%\s]/g, '');
  if (!cleaned || cleaned === '-' || cleaned === '.' || cleaned === '+') return null;
  const parsed = Number(cleaned);
  return Number.isFinite(parsed) ? parsed : null;
}

function findColumn(headers, name) {
  const idx = headers.findIndex((header) => header === name);
  if (idx >= 0) return idx;
  throw new Error(`Missing column: ${name}`);
}

function slotRawColumn(headers, slot) {
  const slotText = String(slot).padStart(2, '0');
  return findColumn(headers, `UTD Slot ${slotText} Raw`);
}

function active(value) {
  return value != null && value !== 0;
}

function recent(rows, index, columns, lookbackBars) {
  const start = Math.max(0, index - lookbackBars);
  for (let rowIndex = start; rowIndex <= index; rowIndex += 1) {
    for (const column of columns) {
      if (active(numeric(rows[rowIndex][column]))) return true;
    }
  }
  return false;
}

function eventSummary(rows, columns, side, lookbackBars) {
  const alertColumn = side === 'buy' ? columns.buyAlert : columns.sellAlert;
  const structureColumns = side === 'buy' ? [columns.bullBos, columns.bullMss] : [columns.bearBos, columns.bearMss];
  const trendColumn = side === 'buy' ? columns.upTrend : columns.downTrend;
  const emaColumn = side === 'buy' ? columns.emaBull : columns.emaBear;
  const trendBeginColumn = side === 'buy' ? columns.upTrendBegins : columns.downTrendBegins;
  const events = [];
  let previousActive = false;

  rows.forEach((row, index) => {
    const isActive = active(numeric(row[alertColumn]));
    if (!isActive) {
      previousActive = false;
      return;
    }
    const isPulseStart = !previousActive;
    previousActive = true;
    const time = numeric(row[columns.time]);
    const strength = numeric(row[columns.oracleStrength]);
    events.push({
      barIndex: index,
      time,
      iso: time == null ? null : new Date(time * 1000).toISOString(),
      close: numeric(row[columns.close]),
      pulseStart: isPulseStart,
      strength,
      strengthAligned: side === 'buy' ? strength != null && strength > 0 : strength != null && strength < 0,
      emaAligned: active(numeric(row[emaColumn])),
      trendActive: active(numeric(row[trendColumn])),
      trendBeginsRecent: recent(rows, index, [trendBeginColumn], lookbackBars),
      structureRecent: recent(rows, index, structureColumns, lookbackBars),
    });
  });

  const count = events.length;
  const pulses = events.filter((event) => event.pulseStart).length;
  const pct = (value) => count ? Number((value / count).toFixed(4)) : null;
  return {
    side,
    count,
    pulses,
    strengthAligned: events.filter((event) => event.strengthAligned).length,
    strengthAlignedPct: pct(events.filter((event) => event.strengthAligned).length),
    emaAligned: events.filter((event) => event.emaAligned).length,
    emaAlignedPct: pct(events.filter((event) => event.emaAligned).length),
    trendActive: events.filter((event) => event.trendActive).length,
    trendActivePct: pct(events.filter((event) => event.trendActive).length),
    trendBeginsRecent: events.filter((event) => event.trendBeginsRecent).length,
    trendBeginsRecentPct: pct(events.filter((event) => event.trendBeginsRecent).length),
    structureRecent: events.filter((event) => event.structureRecent).length,
    structureRecentPct: pct(events.filter((event) => event.structureRecent).length),
    events,
  };
}

function main() {
  const args = parseArgs();
  if (!args.csv) {
    console.error('Usage: node tradingview/scripts/analyze_aio_alert_spike_csv.mjs --csv chart.csv [--lookback-bars 12] [--out report.json]');
    return 2;
  }

  const csvPath = path.resolve(args.csv);
  const lookbackBars = Number(args['lookback-bars'] || 12);
  const parsed = parseCsv(fs.readFileSync(csvPath, 'utf8')).filter((row) => row.some((cell) => String(cell).trim()));
  if (parsed.length < 2) throw new Error(`CSV has no data rows: ${csvPath}`);
  const headers = parsed[0].map((header) => header.replace(/^\uFEFF/, ''));
  const rows = parsed.slice(1);
  const columns = {
    time: findColumn(headers, 'time'),
    close: findColumn(headers, 'close'),
    oracleStrength: findColumn(headers, 'Oracle Strength'),
    emaBull: slotRawColumn(headers, 1),
    emaBear: slotRawColumn(headers, 2),
    bullBos: slotRawColumn(headers, 5),
    bullMss: slotRawColumn(headers, 6),
    bearBos: slotRawColumn(headers, 7),
    bearMss: slotRawColumn(headers, 8),
    upTrend: slotRawColumn(headers, 9),
    downTrend: slotRawColumn(headers, 10),
    upTrendBegins: slotRawColumn(headers, 11),
    downTrendBegins: slotRawColumn(headers, 12),
    buyAlert: slotRawColumn(headers, 13),
    sellAlert: slotRawColumn(headers, 14),
  };

  const report = {
    command: 'analyze-aio-alert-spike-csv',
    csvPath,
    rows: rows.length,
    lookbackBars,
    generatedAt: new Date().toISOString(),
    buy: eventSummary(rows, columns, 'buy', lookbackBars),
    sell: eventSummary(rows, columns, 'sell', lookbackBars),
  };
  const outPath = args.out ? path.resolve(args.out) : path.join(path.dirname(csvPath), 'aio-alert-spike-analysis.json');
  fs.writeFileSync(outPath, `${JSON.stringify(report, null, 2)}\n`);
  console.log(JSON.stringify({
    status: 'ok',
    outPath,
    rows: report.rows,
    buy: {
      count: report.buy.count,
      strengthAlignedPct: report.buy.strengthAlignedPct,
      structureRecentPct: report.buy.structureRecentPct,
    },
    sell: {
      count: report.sell.count,
      strengthAlignedPct: report.sell.strengthAlignedPct,
      structureRecentPct: report.sell.structureRecentPct,
    },
  }, null, 2));
  return 0;
}

process.exitCode = main();
