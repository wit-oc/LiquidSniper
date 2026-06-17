#!/usr/bin/env node
import fs from 'node:fs';
import path from 'node:path';
import { parseArgs, writeReport } from '../../codex/skills/tradingview-pine-loop/scripts/lib/config.mjs';

const DEFAULT_ADVERSARIAL = new Set(['BINANCE:BTCUSDT', 'BINANCE:ETHUSDT', 'BINANCE:ZECUSDT']);
const THRESHOLDS = {
  minTotalTrades: 30,
  minSymbolsWithTenTrades: 3,
  minCombinedProfitFactor: 1.2,
  maxWorstSymbolDrawdownPct: 10,
  minAdversarialProfitFactor: 1.0,
  maxPositivePnlShare: 0.6,
  minPerSymbolProfitFactorWithTenTrades: 0.8,
  maxPerSymbolDrawdownPctWithTenTrades: 25,
};

function num(value) {
  return typeof value === 'number' && Number.isFinite(value) ? value : null;
}

function sum(values) {
  return values.reduce((acc, value) => acc + (num(value) ?? 0), 0);
}

function max(values) {
  const valid = values.map(num).filter((value) => value != null);
  return valid.length ? Math.max(...valid) : null;
}

function pfFromRows(rows) {
  const grossProfit = sum(rows.map((row) => row.metrics?.grossProfit));
  const grossLoss = sum(rows.map((row) => Math.abs(num(row.metrics?.grossLoss) ?? 0)));
  if (grossLoss > 0) return grossProfit / grossLoss;
  return null;
}

function gate(name, passed, detail) {
  return { name, passed: Boolean(passed), detail };
}

function scoreReport(report) {
  const rows = Array.isArray(report.results) ? report.results : [];
  const okRows = rows.filter((row) => row.status === 'ok' && row.metrics);
  const tradeRows = okRows.filter((row) => (num(row.metrics.totalTrades) ?? 0) > 0);
  const symbolsWithTenTrades = okRows.filter((row) => (num(row.metrics.totalTrades) ?? 0) >= 10);
  const adversarialRows = okRows.filter((row) => DEFAULT_ADVERSARIAL.has(row.symbol));

  const totalTrades = sum(okRows.map((row) => row.metrics.totalTrades));
  const activeSymbols = tradeRows.length;
  const combinedProfitFactor = pfFromRows(okRows);
  const adversarialProfitFactor = pfFromRows(adversarialRows);
  const netPnl = sum(okRows.map((row) => row.metrics.totalPnl));
  const worstSymbolDrawdownPct = max(okRows.map((row) => row.metrics.maxIntrabarDrawdownPct ?? row.metrics.maxDrawdownPct));
  const maxPositivePnl = max(okRows.map((row) => Math.max(0, num(row.metrics.totalPnl) ?? 0))) ?? 0;
  const maxSymbolPnlShare = netPnl > 0 ? maxPositivePnl / netPnl : null;
  const hasGrossEvidence = okRows.length > 0 && okRows.every((row) => num(row.metrics.grossProfit) != null && num(row.metrics.grossLoss) != null);
  const severeSymbolFailures = symbolsWithTenTrades.filter((row) => {
    const pf = num(row.metrics.profitFactor);
    const dd = num(row.metrics.maxIntrabarDrawdownPct ?? row.metrics.maxDrawdownPct);
    return (pf != null && pf < THRESHOLDS.minPerSymbolProfitFactorWithTenTrades) ||
      (dd != null && dd > THRESHOLDS.maxPerSymbolDrawdownPctWithTenTrades);
  });

  const setup = report.setupGate || {};
  const hasSetupGate = Boolean(report.setupGate);
  const gates = [
    gate('manual_gate_evidence_present', hasSetupGate, 'report.setupGate must be present'),
    gate('settings_committed', setup.settingsRequired ? setup.settingsAcknowledged : true, setup),
    gate('source_contract_verified', setup.sourceRequired ? setup.sourceAcknowledged : true, setup),
    gate('matrix_status_ok', report.status === 'ok', `report.status=${report.status}`),
    gate('all_rows_ok', rows.length > 0 && rows.every((row) => row.status === 'ok'), `${okRows.length}/${rows.length} rows ok`),
    gate('gross_profit_loss_available', hasGrossEvidence, 'combined PF requires gross profit/loss fields'),
    gate('minimum_total_trades', totalTrades >= THRESHOLDS.minTotalTrades, `totalTrades=${totalTrades}`),
    gate('minimum_symbols_with_ten_trades', symbolsWithTenTrades.length >= THRESHOLDS.minSymbolsWithTenTrades, `symbolsWithTenTrades=${symbolsWithTenTrades.length}`),
    gate('combined_profit_factor', combinedProfitFactor != null && combinedProfitFactor >= THRESHOLDS.minCombinedProfitFactor, `combinedPF=${combinedProfitFactor}`),
    gate('worst_symbol_drawdown', worstSymbolDrawdownPct != null && worstSymbolDrawdownPct <= THRESHOLDS.maxWorstSymbolDrawdownPct, `worstSymbolDDPct=${worstSymbolDrawdownPct}`),
    gate('adversarial_btc_eth_zec_pf', adversarialProfitFactor != null && adversarialProfitFactor >= THRESHOLDS.minAdversarialProfitFactor, `adversarialPF=${adversarialProfitFactor}`),
    gate('pnl_concentration', maxSymbolPnlShare != null && maxSymbolPnlShare <= THRESHOLDS.maxPositivePnlShare, `maxSymbolPnlShare=${maxSymbolPnlShare}`),
    gate('no_severe_symbol_failure', severeSymbolFailures.length === 0, severeSymbolFailures.map((row) => `${row.symbol}:trades=${row.metrics.totalTrades},pf=${row.metrics.profitFactor},dd=${row.metrics.maxIntrabarDrawdownPct ?? row.metrics.maxDrawdownPct}`).join('; ') || 'none'),
  ];

  return {
    status: gates.every((item) => item.passed) ? 'candidate_pass' : 'candidate_rejected',
    hypothesisId: setup.hypothesisId || null,
    summary: {
      totalTrades,
      activeSymbols,
      netPnl,
      combinedProfitFactor,
      adversarialProfitFactor,
      worstSymbolDrawdownPct,
      maxSymbolPnlShare,
      symbolsWithTenTrades: symbolsWithTenTrades.length,
      severeSymbolFailures: severeSymbolFailures.length,
      thresholds: THRESHOLDS,
    },
    gates,
    symbols: okRows.map((row) => ({
      symbol: row.symbol,
      timeframe: row.label,
      trades: row.metrics.totalTrades,
      pnl: row.metrics.totalPnl,
      pf: row.metrics.profitFactor,
      grossProfit: row.metrics.grossProfit,
      grossLoss: row.metrics.grossLoss,
      maxDrawdownPct: row.metrics.maxIntrabarDrawdownPct ?? row.metrics.maxDrawdownPct,
      notEnoughData: row.metrics.hasNotEnoughData,
    })),
  };
}

function main() {
  const args = parseArgs();
  if (!args.report) {
    console.error('Usage: node tradingview/scripts/tv_score_text_matrix.mjs --report artifacts/.../text-matrix-report.json');
    return 2;
  }

  const reportPath = path.resolve(args.report);
  const report = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
  const scored = {
    command: 'tv-score-text-matrix',
    reportPath,
    ...scoreReport(report),
  };
  const outPath = path.join(path.dirname(reportPath), 'candidate-score-report.json');
  writeReport(outPath, scored);
  console.log(JSON.stringify(scored, null, 2));
  return scored.status === 'candidate_pass' ? 0 : 1;
}

process.exitCode = main();
