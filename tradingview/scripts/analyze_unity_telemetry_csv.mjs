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
  const cleaned = String(value)
    .replace(/\u2212/g, '-')
    .replace(/[,%\s]/g, '')
    .replace(/[^\d.+-]/g, '');
  if (!cleaned || cleaned === '-' || cleaned === '.' || cleaned === '+') return null;
  const parsed = Number(cleaned);
  return Number.isFinite(parsed) ? parsed : null;
}

function quantile(values, q) {
  const sorted = values.filter(Number.isFinite).sort((a, b) => a - b);
  if (!sorted.length) return null;
  const idx = (sorted.length - 1) * q;
  const low = Math.floor(idx);
  const high = Math.ceil(idx);
  if (low === high) return sorted[low];
  return sorted[low] + (sorted[high] - sorted[low]) * (idx - low);
}

function pct(count, total) {
  return total > 0 ? Number((count / total).toFixed(6)) : null;
}

function columnFor(headers, slot, kind) {
  const slotText = String(slot).padStart(2, '0');
  const pattern = new RegExp(`UTD\\s+Slot\\s+${slotText}\\s+${kind}`, 'i');
  const idx = headers.findIndex((header) => pattern.test(header));
  return idx >= 0 ? idx : null;
}

function summarizeSlot(slot, rows, rawIdx, sideIdx, classIdx) {
  const raw = [];
  const side = [];
  const cls = [];
  for (const row of rows) {
    raw.push(numeric(row[rawIdx]));
    side.push(numeric(row[sideIdx]));
    cls.push(numeric(row[classIdx]));
  }

  const validRaw = raw.filter((value) => value != null);
  const validSide = side.filter((value) => value != null);
  const validClass = cls.filter((value) => value != null);
  const total = rows.length;
  const classCounts = { na: 0, close: 0, state: 0, price: 0, osc: 0, other: 0 };
  for (const value of cls) {
    if (value === 0) classCounts.na += 1;
    else if (value === 1) classCounts.close += 1;
    else if (value === 2) classCounts.state += 1;
    else if (value === 3) classCounts.price += 1;
    else if (value === 4) classCounts.osc += 1;
    else classCounts.other += 1;
  }
  const sideCounts = { bear: 0, flat: 0, bull: 0, other: 0 };
  for (const value of side) {
    if (value === -1) sideCounts.bear += 1;
    else if (value === 0) sideCounts.flat += 1;
    else if (value === 1) sideCounts.bull += 1;
    else sideCounts.other += 1;
  }

  let sideFlips = 0;
  let zeroCrosses = 0;
  let prevSide = null;
  for (const value of side) {
    if (value == null || value === 0) continue;
    if (prevSide != null && value !== prevSide) {
      sideFlips += 1;
      zeroCrosses += 1;
    }
    prevSide = value;
  }

  const usableOscPct = pct(classCounts.osc, total);
  const usableStatePct = pct(classCounts.state, total);
  const closePct = pct(classCounts.close, total);
  const naPct = pct(classCounts.na, total);
  const pricePct = pct(classCounts.price, total);
  const dynamicRaw = new Set(validRaw.map((value) => Number(value.toFixed(8)))).size;
  const recommendedUse =
    usableOscPct >= 0.75 && sideFlips > 0
      ? 'oscillator_candidate'
      : usableStatePct >= 0.75 && (sideCounts.bull > 0 || sideCounts.bear > 0)
        ? 'state_candidate'
        : pricePct >= 0.75
          ? 'price_scale_only'
          : closePct >= 0.75
            ? 'reject_close_like'
            : naPct >= 0.75
              ? 'reject_mostly_na'
              : dynamicRaw > 8
                ? 'inspect_mixed'
                : 'low_information';

  return {
    slot: String(slot).padStart(2, '0'),
    rows: total,
    raw: {
      validCount: validRaw.length,
      validPct: pct(validRaw.length, total),
      min: validRaw.length ? Math.min(...validRaw) : null,
      max: validRaw.length ? Math.max(...validRaw) : null,
      p05: quantile(validRaw, 0.05),
      median: quantile(validRaw, 0.5),
      p95: quantile(validRaw, 0.95),
      uniqueRounded: dynamicRaw,
    },
    classCounts,
    classPct: Object.fromEntries(Object.entries(classCounts).map(([key, value]) => [key, pct(value, total)])),
    sideCounts,
    sidePct: Object.fromEntries(Object.entries(sideCounts).map(([key, value]) => [key, pct(value, validSide.length || total)])),
    sideFlips,
    zeroCrosses,
    recommendation: recommendedUse,
  };
}

function main() {
  const args = parseArgs();
  if (!args.csv) {
    console.error('Usage: node tradingview/scripts/analyze_unity_telemetry_csv.mjs --csv path/to/chart.csv [--out report.json]');
    return 2;
  }
  const csvPath = path.resolve(args.csv);
  const text = fs.readFileSync(csvPath, 'utf8');
  const parsed = parseCsv(text).filter((row) => row.some((cell) => String(cell).trim().length));
  if (parsed.length < 2) throw new Error(`CSV has no data rows: ${csvPath}`);
  const headers = parsed[0];
  const rows = parsed.slice(1);
  const slots = [];
  for (let slot = 1; slot <= 16; slot += 1) {
    const rawIdx = columnFor(headers, slot, 'Raw');
    const sideIdx = columnFor(headers, slot, 'Side');
    const classIdx = columnFor(headers, slot, 'Class');
    if (rawIdx == null || sideIdx == null || classIdx == null) {
      slots.push({
        slot: String(slot).padStart(2, '0'),
        status: 'missing_columns',
        columns: { rawIdx, sideIdx, classIdx },
      });
      continue;
    }
    slots.push({
      status: 'ok',
      columns: {
        raw: headers[rawIdx],
        side: headers[sideIdx],
        class: headers[classIdx],
      },
      ...summarizeSlot(slot, rows, rawIdx, sideIdx, classIdx),
    });
  }

  const report = {
    command: 'analyze-unity-telemetry-csv',
    csvPath,
    rows: rows.length,
    generatedAt: new Date().toISOString(),
    slots,
  };
  const outPath = args.out ? path.resolve(args.out) : path.join(path.dirname(csvPath), 'unity-telemetry-analysis.json');
  fs.writeFileSync(outPath, `${JSON.stringify(report, null, 2)}\n`);
  console.log(JSON.stringify({ status: 'ok', outPath, rows: rows.length, slotCount: slots.length }, null, 2));
  return 0;
}

process.exitCode = main();
