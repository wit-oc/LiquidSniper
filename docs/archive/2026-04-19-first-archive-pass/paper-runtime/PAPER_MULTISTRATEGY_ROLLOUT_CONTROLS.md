# Paper Multi-Strategy Rollout Controls

## Feature flags
- `LIQUIDSNIPER_FEATURE_STRATEGY_ACCOUNTS` (default: true)
- `LIQUIDSNIPER_FEATURE_PAPER_PARALLEL` (default: false)
- `LIQUIDSNIPER_EMERGENCY_STOP` (default: false)
- `LIQUIDSNIPER_ROLLBACK_SINGLE_STRATEGY` (default: false)

## Emergency stop
Set `LIQUIDSNIPER_EMERGENCY_STOP=true` to block all new entries immediately with reason `EMERGENCY_STOP_ACTIVE`.

## Rollback drill
1. Set `LIQUIDSNIPER_ROLLBACK_SINGLE_STRATEGY=true`
2. Set `LIQUIDSNIPER_FEATURE_PAPER_PARALLEL=false`
3. Keep only `intraday` enabled in strategy_accounts.
4. Verify non-paper remains single-mode and no parallel fan-out paths are active.
