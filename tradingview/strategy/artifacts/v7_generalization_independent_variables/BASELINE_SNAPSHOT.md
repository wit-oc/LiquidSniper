# V7 Generalization Baseline Snapshot

Snapshot date: 2026-05-30

## Protected Strategy State

This artifact protects the current candidate before the independent-variable generalization pass. The source candidate is not edited by this pass.

| Item | Value |
| --- | --- |
| Branch | `codex/unity-utm-feasibility-spike` |
| HEAD | `f5a58c1045feb7d1600a00729097044daae98851` |
| Current candidate source | `tradingview/strategy/artifacts/v7_fixed_percent_stop_sidebar/generated/v7-fixed-stop-structural-control-125bps.pine` |
| Source lines | 953 |
| Source SHA-256 | `f8e367119e684ec7f3f23460b54927b5e7b7f4a8b02c2cf7c6549484dc3755bb` |
| Source manifest | `tradingview/strategy/artifacts/v7_fixed_percent_stop_sidebar/tv_fixed_percent_stop_runs.json` |
| Source manifest SHA-256 | `abb16835194b9a45e74be9da6681fbfe286bba9e62ae22a66e944c64e5d0f443` |

## Git Status Snapshot

At snapshot time, the worktree was intentionally dirty from the ongoing Unity UTM v7 feasibility spike.

| Check | Value |
| --- | ---: |
| Staged file count | 82 |
| Staged diff stat | 19,574 insertions / 1 deletion |

Relevant staged V7 artifacts already present before this pass included:

- `tradingview/strategy/artifacts/v7_fixed_percent_stop_sidebar/*`
- `tradingview/strategy/artifacts/v7_liquidity_scope_sanity/*`
- `tradingview/strategy/artifacts/v7_liquidity_scope_perp_probe/*`
- `tradingview/strategy/artifacts/v7_stop_engine_robustness/*`
- `tradingview/strategy/artifacts/v7_displacement_geometry_fidelity/*`
- `tradingview/strategy/artifacts/v7_robustness_verdict/*`
- `tradingview/strategy/UNITY_UTM_V7_VERDICT_LEARNINGS.md`

Unrelated unstaged/untracked files also existed outside this artifact family. This pass does not revert or mutate those files.

## Baseline Evidence Being Protected

Prior broad liquidity-scope baseline:

- Manifest: `tradingview/strategy/artifacts/v7_liquidity_scope_sanity/tv_liquidity_scope_sanity_runs.json`
- Manifest SHA-256: `3bbee52196450b8e5d0627a2717c14f3e9138bf3bc451e74682a2b8b5ccbf709`
- Metrics: `tradingview/strategy/artifacts/v7_liquidity_scope_sanity/liquidity_scope_sanity_metrics.md`
- Verdict: `tradingview/strategy/artifacts/v7_liquidity_scope_sanity/LIQUIDITY_SCOPE_SANITY_VERDICT.md`
- Read: all-symbol basket remained unacceptable; admitted pass set was `ZEC`, `ADA`, `LINK`, `XRP`, `ARB`, `PYTH`, `SEI`.

Targeted Binance `.P` route probe:

- Manifest: `tradingview/strategy/artifacts/v7_liquidity_scope_perp_probe/tv_liquidity_scope_perp_probe_runs.json`
- Manifest SHA-256: `b8514a0c4b00e3249101aa57e93965d0febc640924ffea8c21fcc9366e158136`
- Metrics: `tradingview/strategy/artifacts/v7_liquidity_scope_perp_probe/liquidity_scope_sanity_metrics.md`
- Verdict: `tradingview/strategy/artifacts/v7_liquidity_scope_perp_probe/PERP_ROUTE_PROBE_VERDICT.md`
- Read: `.P` fixed coverage for `HYPE`, `AERO`, and `RENDER`, but all three failed robustness gates under the current 125 bps profile.

## Generalization Test Boundary

This pass uses the protected 125 bps candidate as the baseline and tests independent variables only. It does not combine variables unless a follow-up is explicitly warranted by results.

Matrix symbols:

- Prior admitted controls: `ZEC`, `ADA`, `LINK`, `XRP`, `ARB`, `PYTH`, `SEI`
- Prior failed/major controls: `BTC`, `ETH`, `SOL`, `BNB`, `DOGE`, `LTC`
- Binance perp route probes: `HYPEUSDT.P`, `AEROUSDT.P`, `RENDERUSDT.P`

Timeframes: `15m` and `5m` over TradingView entire available history.

Independent variables:

- `Quality Score 3`: trade-quality filter only.
- `ATR Regime Filter`: volatility/risk adaptation only, layered on the current Displacement Quality profile.
- `Close Confirmed Stop`: stop/exit behavior only.

Decision emphasis remains drawdown first, then profit factor, then reasonable win rate. Broad improvement across symbols/timeframes matters more than best-case P&L.
