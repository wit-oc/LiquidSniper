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
  return rows.filter((item) => item.some((cell) => String(cell).trim().length));
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

function median(values) {
  const sorted = values.filter(Number.isFinite).sort((a, b) => a - b);
  if (!sorted.length) return null;
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}

function pct(count, total) {
  return total > 0 ? Number((count / total).toFixed(6)) : null;
}

function col(headers, name) {
  const index = headers.indexOf(name);
  if (index < 0) throw new Error(`Missing required column "${name}"`);
  return index;
}

function firstAge(rows, side, sideColumn, windowBars) {
  for (const row of rows) {
    const age = row.armAge;
    if (age == null || age <= 0 || age > windowBars) continue;
    if (row[sideColumn] === side) return age;
  }
  return null;
}

function maxAge(...values) {
  const valid = values.filter((value) => value != null);
  return valid.length === values.length ? Math.max(...valid) : null;
}

function analyze(csvPath, options = {}) {
  const windowBars = Number(options.window || 96);
  const text = fs.readFileSync(csvPath, 'utf8');
  const parsed = parseCsv(text);
  if (parsed.length < 2) throw new Error(`CSV has no data rows: ${csvPath}`);
  const headers = parsed[0];
  const rows = parsed.slice(1);
  const indexes = {
    time: col(headers, 'time'),
    armId: col(headers, 'AUD Arm Id'),
    setupSide: col(headers, 'AUD Setup Side'),
    armAge: col(headers, 'AUD Arm Age'),
    levelFamily: col(headers, 'AUD Level Family'),
    levelQuality: col(headers, 'AUD Level Quality'),
    sweepBps: col(headers, 'AUD Sweep Bps'),
    riskBps: col(headers, 'AUD Risk Bps'),
    rejectCode: col(headers, 'AUD Primary Reject Code'),
    sourceOk: col(headers, 'AUD Source Contract OK'),
    phaseChoch: col(headers, 'AUD Phase1 CHoCH Side'),
    phaseBos: col(headers, 'AUD Phase1 BoS Side'),
    aioMss: col(headers, 'AUD AIO MSS Side'),
    aioBos: col(headers, 'AUD AIO BoS Side'),
    aioAny: col(headers, 'AUD AIO Any Structure Side'),
    strength: col(headers, 'AUD Oracle Strength Side'),
    phaseEntryReady: col(headers, 'AUD Phase Entry Ready'),
    aioEntryReady: col(headers, 'AUD AIO Entry Ready'),
  };

  const byArm = new Map();
  const rejectHistogram = {};
  let mappedRows = 0;
  for (const raw of rows) {
    const mapped = {
      time: numeric(raw[indexes.time]),
      armId: numeric(raw[indexes.armId]),
      setupSide: numeric(raw[indexes.setupSide]),
      armAge: numeric(raw[indexes.armAge]),
      levelFamily: numeric(raw[indexes.levelFamily]),
      levelQuality: numeric(raw[indexes.levelQuality]),
      sweepBps: numeric(raw[indexes.sweepBps]),
      riskBps: numeric(raw[indexes.riskBps]),
      rejectCode: numeric(raw[indexes.rejectCode]),
      sourceOk: numeric(raw[indexes.sourceOk]),
      phaseChoch: numeric(raw[indexes.phaseChoch]),
      phaseBos: numeric(raw[indexes.phaseBos]),
      aioMss: numeric(raw[indexes.aioMss]),
      aioBos: numeric(raw[indexes.aioBos]),
      aioAny: numeric(raw[indexes.aioAny]),
      strength: numeric(raw[indexes.strength]),
      phaseEntryReady: numeric(raw[indexes.phaseEntryReady]),
      aioEntryReady: numeric(raw[indexes.aioEntryReady]),
    };
    if (mapped.sourceOk === 1) mappedRows += 1;
    const rejectKey = String(mapped.rejectCode ?? 'null');
    rejectHistogram[rejectKey] = (rejectHistogram[rejectKey] || 0) + 1;
    if (mapped.armId == null || mapped.setupSide === 0 || mapped.armAge == null) continue;
    if (!byArm.has(mapped.armId)) byArm.set(mapped.armId, []);
    byArm.get(mapped.armId).push(mapped);
  }

  const arms = [];
  for (const [armId, armRows] of byArm.entries()) {
    armRows.sort((a, b) => (a.armAge ?? 0) - (b.armAge ?? 0));
    const first = armRows[0];
    const side = first.setupSide;
    const phaseChochAge = firstAge(armRows, side, 'phaseChoch', windowBars);
    const phaseBosAge = firstAge(armRows, side, 'phaseBos', windowBars);
    const aioMssAge = firstAge(armRows, side, 'aioMss', windowBars);
    const aioBosAge = firstAge(armRows, side, 'aioBos', windowBars);
    const aioAnyAge = firstAge(armRows, side, 'aioAny', windowBars);
    const strengthAge = firstAge(armRows, side, 'strength', windowBars);
    const riskAge = armRows.find((row) => row.armAge > 0 && row.armAge <= windowBars && row.riskBps != null && row.riskBps >= 15 && row.riskBps <= 600)?.armAge ?? null;
    const phaseEntryAge = maxAge(phaseChochAge, strengthAge, riskAge);
    const aioEntryAge = maxAge(aioAnyAge, strengthAge, riskAge);
    const plottedPhaseEntryAge = armRows.find((row) => row.armAge > 0 && row.armAge <= windowBars && row.phaseEntryReady === 1)?.armAge ?? null;
    const plottedAioEntryAge = armRows.find((row) => row.armAge > 0 && row.armAge <= windowBars && row.aioEntryReady === 1)?.armAge ?? null;
    arms.push({
      armId,
      side,
      levelFamily: first.levelFamily,
      levelQuality: first.levelQuality,
      sweepBps: first.sweepBps,
      rows: armRows.length,
      phaseChochAge,
      phaseBosAge,
      aioMssAge,
      aioBosAge,
      aioAnyAge,
      strengthAge,
      riskAge,
      phaseEntryAge,
      aioEntryAge,
      plottedPhaseEntryAge,
      plottedAioEntryAge,
    });
  }

  const count = (fn) => arms.filter(fn).length;
  const phaseChochCount = count((arm) => arm.phaseChochAge != null);
  const aioMssCount = count((arm) => arm.aioMssAge != null);
  const aioBosCount = count((arm) => arm.aioBosAge != null);
  const aioAnyCount = count((arm) => arm.aioAnyAge != null);
  const strengthCount = count((arm) => arm.strengthAge != null);
  const riskCount = count((arm) => arm.riskAge != null);
  const phaseEntryCount = count((arm) => arm.phaseEntryAge != null);
  const aioEntryCount = count((arm) => arm.aioEntryAge != null);
  const phaseOrAioStructCount = count((arm) => arm.phaseChochAge != null || arm.aioAnyAge != null);
  const phaseOrAioEntryCount = count((arm) => (arm.phaseChochAge != null || arm.aioAnyAge != null) && arm.strengthAge != null && arm.riskAge != null);

  return {
    csvPath: path.resolve(csvPath),
    rows: rows.length,
    mappedRows,
    mappedRowPct: pct(mappedRows, rows.length),
    windowBars,
    rejectHistogram,
    arms: {
      count: arms.length,
      long: count((arm) => arm.side === 1),
      short: count((arm) => arm.side === -1),
      phaseChoch: phaseChochCount,
      phaseBos: count((arm) => arm.phaseBosAge != null),
      aioMss: aioMssCount,
      aioBos: aioBosCount,
      aioAny: aioAnyCount,
      strength: strengthCount,
      riskOk: riskCount,
      phaseEntryReady: phaseEntryCount,
      aioEntryReady: aioEntryCount,
      phaseOrAioStructure: phaseOrAioStructCount,
      phaseOrAioEntryReady: phaseOrAioEntryCount,
    },
    rates: {
      phaseChochPerArm: pct(phaseChochCount, arms.length),
      aioMssPerArm: pct(aioMssCount, arms.length),
      aioBosPerArm: pct(aioBosCount, arms.length),
      aioAnyPerArm: pct(aioAnyCount, arms.length),
      strengthPerArm: pct(strengthCount, arms.length),
      riskOkPerArm: pct(riskCount, arms.length),
      phaseEntryReadyPerArm: pct(phaseEntryCount, arms.length),
      aioEntryReadyPerArm: pct(aioEntryCount, arms.length),
      phaseOrAioEntryReadyPerArm: pct(phaseOrAioEntryCount, arms.length),
    },
    timing: {
      medianPhaseChochAge: median(arms.map((arm) => arm.phaseChochAge)),
      medianPhaseBosAge: median(arms.map((arm) => arm.phaseBosAge)),
      medianAioMssAge: median(arms.map((arm) => arm.aioMssAge)),
      medianAioBosAge: median(arms.map((arm) => arm.aioBosAge)),
      medianAioAnyAge: median(arms.map((arm) => arm.aioAnyAge)),
      medianStrengthAge: median(arms.map((arm) => arm.strengthAge)),
      medianPhaseEntryAge: median(arms.map((arm) => arm.phaseEntryAge)),
      medianAioEntryAge: median(arms.map((arm) => arm.aioEntryAge)),
    },
    armDetails: arms,
  };
}

function main() {
  const args = parseArgs();
  if (!args.csv) {
    console.error('Usage: node tradingview/scripts/analyze_structure_feed_audit_csv.mjs --csv path/to/chart.csv [--out report.json] [--window 96]');
    return 2;
  }
  const report = {
    command: 'analyze-structure-feed-audit-csv',
    generatedAt: new Date().toISOString(),
    ...analyze(args.csv, args),
  };
  const outPath = args.out ? path.resolve(args.out) : path.join(path.dirname(path.resolve(args.csv)), 'structure-feed-audit-analysis.json');
  fs.writeFileSync(outPath, `${JSON.stringify(report, null, 2)}\n`);
  console.log(JSON.stringify({ status: 'ok', outPath, arms: report.arms.count, rows: report.rows }, null, 2));
  return 0;
}

process.exitCode = main();
