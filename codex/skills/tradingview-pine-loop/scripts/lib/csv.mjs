import fs from 'node:fs';
import path from 'node:path';

export function parseCsv(text) {
  const rows = [];
  let row = [];
  let cell = '';
  let quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    const next = text[i + 1];
    if (quoted) {
      if (ch === '"' && next === '"') {
        cell += '"';
        i += 1;
      } else if (ch === '"') {
        quoted = false;
      } else {
        cell += ch;
      }
      continue;
    }
    if (ch === '"') {
      quoted = true;
    } else if (ch === ',') {
      row.push(cell);
      cell = '';
    } else if (ch === '\n') {
      row.push(cell.replace(/\r$/, ''));
      rows.push(row);
      row = [];
      cell = '';
    } else {
      cell += ch;
    }
  }
  if (cell.length || row.length) {
    row.push(cell.replace(/\r$/, ''));
    rows.push(row);
  }
  const header = rows.shift() || [];
  return rows
    .filter((values) => values.some((value) => String(value).trim() !== ''))
    .map((values) => Object.fromEntries(header.map((key, index) => [key, values[index] ?? ''])));
}

export function listFilesRecursive(root, ext) {
  if (!fs.existsSync(root)) return [];
  const out = [];
  for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
    const full = path.join(root, entry.name);
    if (entry.isDirectory()) out.push(...listFilesRecursive(full, ext));
    if (entry.isFile() && full.toLowerCase().endsWith(ext.toLowerCase())) out.push(full);
  }
  return out;
}

export function numericStats(rows, column) {
  const values = rows
    .map((row) => Number(String(row[column] ?? '').replace(/[%,$\s]/g, '')))
    .filter((value) => Number.isFinite(value));
  if (!values.length) return null;
  return {
    count: values.length,
    min: Math.min(...values),
    max: Math.max(...values),
    latest: values[values.length - 1],
    nonZeroCount: values.filter((value) => value !== 0).length,
    uniqueCount: new Set(values.map((value) => String(value))).size,
  };
}
