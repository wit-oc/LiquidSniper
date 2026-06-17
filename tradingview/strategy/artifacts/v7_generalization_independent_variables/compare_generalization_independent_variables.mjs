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
const artifactRoot = path.resolve(repoRoot, args.output || 'tradingview/strategy/artifacts/v7_generalization_independent_variables');
const manifestPath = path.resolve(repoRoot, args.manifest || 'tradingview/strategy/artifacts/v7_generalization_independent_variables/tv_generalization_independent_variables_runs.json');
const telemetryRoot = path.resolve(repoRoot, args.telemetryRoot || 'tradingview/strategy/.telemetry/outputs/v7_generalization_independent_variables');
const outputPath = path.join(artifactRoot, 'generalization_independent_variables_metrics.md');
const outputJsonPath = path.join(strategyRoot, '.telemetry/outputs/v7_generalization_independent_variables/generalization_independent_variables_metrics.json');

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

function pf(row) {
  return Number.isFinite(row?.profitFactor) ? row.profitFactor : 0;
}

function fmt(value, digits = 2) {
  return Number.isFinite(value) ? value.toFixed(digits) : 'n/a';
}

function shortSymbol(symbol) {
  return String(symbol || '').replace('BINANCE:', '').replace('USDT', '');
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
  lines.push(`| ${headers.map((header) => header.match(/%|P&L|PF|DD|Trades|Rows|Slots|Score/) ? '---:' : '---').join(' | ')} |`);
  for (const row of rows) lines.push(`| ${rowFn(row).join(' | ')} |`);
}

function byKey(rows, keyFn) {
  return new Map(rows.map((row) => [keyFn(row), row]));
}

function rowKey(row) {
  return `${row.symbol}|${row.timeframe}`;
}

function symbolKey(row) {
  return row.symbol;
}

function summarizeRun(run, metrics) {
  const aggregate = metrics.aggregate;
  const timeframeRows = aggregate.timeframeRows || [];
  const symbolRows = aggregate.symbolClassifications || [];
  const windowRows = aggregate.windowRows || [];
  const basket = aggregate.basket || aggregate.scopeRows?.find((row) => row.scope === 'All symbols') || {};
  const okSlots = timeframeRows.filter((row) => row.slotStatus === 'ok').length;
  const noTradeSlots = timeframeRows.filter((row) => row.slotStatus === 'no_trade_data').length;
  const failedSlots = metrics.failed?.length || timeframeRows.filter((row) => row.slotStatus === 'failed').length;
  const missingSlots = metrics.missing?.length || timeframeRows.filter((row) => row.slotStatus === 'missing').length;
  const positiveRows = timeframeRows.filter((row) => finite(row.totalTrades) > 0 && finite(row.totalPnl) > 0).length;
  const negativeRows = timeframeRows.filter((row) => finite(row.totalTrades) > 0 && finite(row.totalPnl) < 0).length;
  const pfFailRows = timeframeRows.filter((row) => finite(row.totalTrades) > 0 && pf(row) < 1).length;
  const ddOverFiveRows = timeframeRows.filter((row) => finite(row.totalTrades) > 0 && finite(row.maxDrawdownPct) > 5).length;
  const negativeWindows = windowRows.filter((row) => finite(row.totalTrades) >= 3 && finite(row.totalPnl) < 0).length;
  const passSymbols = symbolRows.filter((row) => row.classification === 'pass').map((row) => row.asset);
  const marginalSymbols = symbolRows.filter((row) => row.classification === 'marginal').map((row) => row.asset);
  const failSymbols = symbolRows.filter((row) => row.classification === 'fail').map((row) => row.asset);
  return {
    runId: run.id,
    variant: run.variant,
    title: run.geometry || run.scriptTitle,
    description: run.description,
    okSlots,
    noTradeSlots,
    failedSlots,
    missingSlots,
    positiveRows,
    negativeRows,
    pfFailRows,
    ddOverFiveRows,
    negativeWindows,
    passSymbols,
    marginalSymbols,
    failSymbols,
    basket,
    timeframeRows,
    symbolRows,
    windowRows,
  };
}

function compareToBaseline(summary, baseline) {
  const baseTimeframes = byKey(baseline.timeframeRows, rowKey);
  const baseSymbols = byKey(baseline.symbolRows, symbolKey);
  let improvedSlots = 0;
  let degradedSlots = 0;
  let mixedSlots = 0;
  for (const row of summary.timeframeRows) {
    const base = baseTimeframes.get(rowKey(row));
    if (!base || finite(row.totalTrades) === 0 || finite(base.totalTrades) === 0) continue;
    const pnlDelta = finite(row.totalPnl) - finite(base.totalPnl);
    const pfDelta = pf(row) - pf(base);
    const ddDelta = finite(base.maxDrawdownPct) - finite(row.maxDrawdownPct);
    if (pnlDelta > 0 && pfDelta >= 0 && ddDelta >= 0) improvedSlots += 1;
    else if (pnlDelta < 0 && pfDelta < 0) degradedSlots += 1;
    else mixedSlots += 1;
  }
  let improvedSymbols = 0;
  let degradedSymbols = 0;
  for (const row of summary.symbolRows) {
    const base = baseSymbols.get(symbolKey(row));
    if (!base || finite(row.totalTrades) === 0 || finite(base.totalTrades) === 0) continue;
    const pnlDelta = finite(row.totalPnl) - finite(base.totalPnl);
    const pfDelta = pf(row) - pf(base);
    const ddDelta = finite(base.maxDrawdownPct) - finite(row.maxDrawdownPct);
    if (pnlDelta > 0 && pfDelta >= 0 && ddDelta >= 0) improvedSymbols += 1;
    else if (pnlDelta < 0 && pfDelta < 0) degradedSymbols += 1;
  }
  const score = (pf(summary.basket) - pf(baseline.basket)) * 10
    + (finite(baseline.basket.maxDrawdownPct) - finite(summary.basket.maxDrawdownPct)) * 0.5
    + (summary.positiveRows - baseline.positiveRows) * 1.5
    - (summary.negativeRows - baseline.negativeRows)
    + (improvedSlots - degradedSlots) * 0.75
    + (improvedSymbols - degradedSymbols);
  return {
    ...summary,
    deltaPnl: finite(summary.basket.totalPnl) - finite(baseline.basket.totalPnl),
    deltaPf: pf(summary.basket) - pf(baseline.basket),
    deltaDd: finite(summary.basket.maxDrawdownPct) - finite(baseline.basket.maxDrawdownPct),
    improvedSlots,
    degradedSlots,
    mixedSlots,
    improvedSymbols,
    degradedSymbols,
    score,
  };
}

function main() {
  const manifest = readJson(manifestPath);
  const summaries = [];
  const missingTelemetry = [];
  for (const run of manifest.runs || []) {
    const telemetryPath = path.join(telemetryRoot, run.id, 'liquidity_scope_sanity_metrics.json');
    if (!fs.existsSync(telemetryPath)) {
      missingTelemetry.push({ runId: run.id, telemetryPath: rel(telemetryPath) });
      continue;
    }
    summaries.push(summarizeRun(run, readJson(telemetryPath)));
  }

  const baseline = summaries.find((item) => item.runId === 'v7-generalization-baseline-125bps') || summaries[0];
  const compared = baseline ? summaries.map((summary) => (
    summary.runId === baseline.runId
      ? {
          ...summary,
          deltaPnl: 0,
          deltaPf: 0,
          deltaDd: 0,
          improvedSlots: 0,
          degradedSlots: 0,
          mixedSlots: 0,
          improvedSymbols: 0,
          degradedSymbols: 0,
          score: 0,
        }
      : compareToBaseline(summary, baseline)
  )) : [];
  const ranked = compared.filter((row) => row.runId !== baseline?.runId).sort((a, b) => b.score - a.score);

  const lines = ['# V7 Generalization Independent Variables Metrics', ''];
  lines.push(`Manifest: \`${rel(manifestPath)}\``);
  lines.push(`Telemetry root: \`${rel(telemetryRoot)}\``);
  lines.push('');
  if (missingTelemetry.length) {
    lines.push('## Missing Telemetry');
    table(lines, ['Run', 'Expected telemetry path'], missingTelemetry, (row) => [row.runId, `\`${row.telemetryPath}\``]);
    lines.push('');
  }
  if (!baseline) {
    lines.push('No completed baseline telemetry was found. Run the TradingView matrix and analyzer before reading this as a verdict.');
  } else {
    lines.push('## Coverage');
    table(lines, ['Variant', 'OK Slots', 'No Trade', 'Failed', 'Missing'], compared, (row) => [
      row.title,
      row.okSlots,
      row.noTradeSlots,
      row.failedSlots,
      row.missingSlots,
    ]);
    lines.push('');
    lines.push('## Basket Scorecard');
    table(lines, ['Variant', 'Trades', 'P&L', 'PF', 'Win %', 'DD %', 'Positive Rows', 'Negative Rows', 'PF<1 Rows', 'DD>5 Rows'], compared, (row) => [
      row.title,
      ...metricCells(row.basket),
      row.positiveRows,
      row.negativeRows,
      row.pfFailRows,
      row.ddOverFiveRows,
    ]);
    lines.push('');
    lines.push('## Baseline Delta Ranking');
    table(lines, ['Variant', 'Delta P&L', 'Delta PF', 'Delta DD %', 'Improved Slots', 'Degraded Slots', 'Improved Symbols', 'Degraded Symbols', 'Score'], ranked, (row) => [
      row.title,
      fmt(row.deltaPnl),
      fmt(row.deltaPf, 3),
      fmt(row.deltaDd, 2),
      row.improvedSlots,
      row.degradedSlots,
      row.improvedSymbols,
      row.degradedSymbols,
      fmt(row.score, 2),
    ]);
    lines.push('');
    lines.push('## Symbol Classifications');
    table(lines, ['Variant', 'Pass', 'Marginal', 'Fail'], compared, (row) => [
      row.title,
      row.passSymbols.length ? row.passSymbols.join(', ') : 'none',
      row.marginalSymbols.length ? row.marginalSymbols.join(', ') : 'none',
      row.failSymbols.length ? row.failSymbols.join(', ') : 'none',
    ]);
    lines.push('');
    lines.push('## Timeframe Rows');
    const rows = compared.flatMap((summary) => summary.timeframeRows.map((row) => ({ ...row, title: summary.title })));
    table(lines, ['Variant', 'Asset', 'TF', 'Status', 'Trades', 'P&L', 'PF', 'Win %', 'DD %'], rows, (row) => [
      row.title,
      row.asset || shortSymbol(row.symbol),
      row.timeframe,
      row.slotStatus,
      ...metricCells(row),
    ]);
    lines.push('');
    lines.push('## Window Robustness');
    const windowRows = compared.flatMap((summary) => summary.windowRows.map((row) => ({ ...row, title: summary.title })));
    table(lines, ['Variant', 'Asset', 'Window', 'Trades', 'P&L', 'PF', 'Win %', 'DD %'], windowRows, (row) => [
      row.title,
      row.asset || shortSymbol(row.symbol),
      row.window,
      ...metricCells(row),
    ]);
  }

  ensureDir(artifactRoot);
  ensureDir(path.dirname(outputJsonPath));
  fs.writeFileSync(outputPath, `${lines.join('\n')}\n`);
  fs.writeFileSync(outputJsonPath, `${JSON.stringify({
    generatedAt: new Date().toISOString(),
    manifestPath: rel(manifestPath),
    telemetryRoot: rel(telemetryRoot),
    missingTelemetry,
    baselineRunId: baseline?.runId || null,
    compared,
    ranked,
  }, null, 2)}\n`);
  console.log(JSON.stringify({
    outputPath,
    outputJsonPath,
    completedRuns: summaries.length,
    missingRuns: missingTelemetry.length,
    baselineRunId: baseline?.runId || null,
    topVariant: ranked[0]?.runId || null,
  }, null, 2));
}

main();
