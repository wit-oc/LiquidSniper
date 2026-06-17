#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { loadConfig, parseArgs, writeReport } from './lib/config.mjs';
import { listFilesRecursive, numericStats, parseCsv } from './lib/csv.mjs';

function latestRunDir(baseDir, runId) {
  const root = path.join(baseDir, runId);
  if (!fs.existsSync(root)) return baseDir;
  const dirs = fs.readdirSync(root)
    .map((name) => path.join(root, name))
    .filter((candidate) => fs.statSync(candidate).isDirectory())
    .sort();
  return dirs.at(-1) || root;
}

function evaluateCheck(stats, check) {
  const actual = stats?.[check.stat || 'latest'];
  const expected = Number(check.value);
  if (!Number.isFinite(actual)) return { ok: false, actual, expected, reason: 'missing_numeric_value' };
  switch (check.operator) {
    case '>': return { ok: actual > expected, actual, expected };
    case '>=': return { ok: actual >= expected, actual, expected };
    case '<': return { ok: actual < expected, actual, expected };
    case '<=': return { ok: actual <= expected, actual, expected };
    case '==': return { ok: actual === expected, actual, expected };
    case '!=': return { ok: actual !== expected, actual, expected };
    default: return { ok: false, actual, expected, reason: `unsupported_operator:${check.operator}` };
  }
}

const args = parseArgs();
const loaded = loadConfig(args);
const validation = loaded.run.validation || {};
const artifactsRoot = args.artifacts ? path.resolve(args.artifacts) : latestRunDir(loaded.artifactsDir, loaded.runId);
const csvFiles = listFilesRecursive(artifactsRoot, '.csv');
const failures = [];
const files = [];
const allColumns = new Set();
const allRows = [];

for (const file of csvFiles) {
  const rows = parseCsv(fs.readFileSync(file, 'utf8'));
  const columns = rows.length ? Object.keys(rows[0]) : [];
  columns.forEach((column) => allColumns.add(column));
  rows.forEach((row) => allRows.push(row));
  files.push({ file, rowCount: rows.length, columns });
}

for (const column of validation.requiredColumns || []) {
  if (!allColumns.has(column)) failures.push({ type: 'missing_column', column });
}

if (validation.minCsvFiles && csvFiles.length < validation.minCsvFiles) {
  failures.push({ type: 'min_csv_files', actual: csvFiles.length, expected: validation.minCsvFiles });
}

if (validation.minRows && allRows.length < validation.minRows) {
  failures.push({ type: 'min_rows', actual: allRows.length, expected: validation.minRows });
}

for (const column of validation.nonConstantColumns || []) {
  const stats = numericStats(allRows, column);
  if (!stats) {
    failures.push({ type: 'missing_numeric_column', column });
  } else if (stats.uniqueCount < 2) {
    failures.push({ type: 'constant_column', column, stats });
  }
}

for (const column of validation.nonZeroColumns || []) {
  const stats = numericStats(allRows, column);
  if (!stats) {
    failures.push({ type: 'missing_numeric_column', column });
  } else if (stats.nonZeroCount < 1) {
    failures.push({ type: 'zero_only_column', column, stats });
  }
}

const numericChecks = [];
for (const check of validation.numericChecks || []) {
  const stats = numericStats(allRows, check.column);
  const evaluated = evaluateCheck(stats, check);
  numericChecks.push({ ...check, stats, ...evaluated });
  if (!evaluated.ok) failures.push({ type: 'numeric_check_failed', check, stats, evaluated });
}

const report = {
  status: failures.length ? 'failed' : 'ok',
  command: 'tv-validate',
  runId: loaded.runId,
  artifactsRoot,
  csvFileCount: csvFiles.length,
  rowCount: allRows.length,
  columns: Array.from(allColumns).sort(),
  files,
  numericChecks,
  failures,
};

const outPath = path.join(artifactsRoot, 'validation-report.json');
writeReport(outPath, report);
console.log(JSON.stringify(report, null, 2));
if (report.status === 'failed') process.exitCode = 1;
