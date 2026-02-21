from datetime import datetime, timezone

from liquidsniper.core.paper_policy import ThrottleState, evaluate_gates, load_profile_policy


def test_load_profile_policy_defaults(monkeypatch):
    monkeypatch.delenv("LIQUIDSNIPER_PROFILE_ID", raising=False)
    policy = load_profile_policy()
    assert policy.profile_id == "I"
    assert policy.htf_anchor_tf == "4H"
    assert policy.daily_max_trades > 0
    assert policy.daily_max_loss_usd > 0
    assert policy.max_active_risk_positions == 2


def test_evaluate_gates_blocks_profile_conditions(monkeypatch):
    monkeypatch.setenv("LIQUIDSNIPER_PROFILE_ID", "S")
    monkeypatch.setenv("LIQUIDSNIPER_REQUIRE_CANDLE_CLOSE", "true")
    monkeypatch.setenv("LIQUIDSNIPER_HTF_CHOP_MAX", "40")
    monkeypatch.setenv("LIQUIDSNIPER_MIN_SECONDARY_HITS", "2")
    policy = load_profile_policy()

    state = ThrottleState.empty("2026-02-20")
    out = evaluate_gates(
        policy=policy,
        state=state,
        now=datetime(2026, 2, 20, 14, 31, tzinfo=timezone.utc),
        idempotency_key="k1",
        side="buy",
        candle_closed=False,
        candle_ts="2026-02-20T14:30:00+00:00",
        htf_chop=52.0,
        sr_first_retest=True,
        bos_choch=False,
        secondary_hits=1,
    )
    assert out.accepted is False
    assert "CANDLE_NOT_CLOSED" in out.reason_codes
    assert "HTF_CHOP_BLOCKED" in out.reason_codes
    assert "BIAS_NOT_PERMITTED" in out.reason_codes
    assert "CONFLUENCE_TOO_WEAK" in out.reason_codes


def test_evaluate_gates_blocks_throttle_conditions(monkeypatch):
    monkeypatch.setenv("LIQUIDSNIPER_PROFILE_ID", "I")
    monkeypatch.setenv("LIQUIDSNIPER_COOLDOWN_SECONDS", "600")
    monkeypatch.setenv("LIQUIDSNIPER_DAILY_MAX_TRADES", "1")
    monkeypatch.setenv("LIQUIDSNIPER_MAX_DAILY_LOSS_USD", "500")
    monkeypatch.setenv("LIQUIDSNIPER_MAX_ACTIVE_RISK_POSITIONS", "2")
    monkeypatch.setenv("LIQUIDSNIPER_REQUIRE_CANDLE_CLOSE", "false")
    monkeypatch.setenv("LIQUIDSNIPER_MIN_SECONDARY_HITS", "0")
    monkeypatch.setenv("LIQUIDSNIPER_HTF_CHOP_MAX", "100")

    policy = load_profile_policy()
    state = ThrottleState(
        trading_day="2026-02-20",
        last_entry_ts="2026-02-20T14:30:00+00:00",
        trades_open=2,
        executed_today=1,
        realized_pnl_today_usd=-600.0,
        seen_idempotency_keys=["dup-key"],
        open_positions=[
            {"position_id": "p1", "symbol": "BTCUSDT", "strategy": "intraday", "status": "open", "stop_state": "initial", "opened_cycle": 1, "tp1_ts": None},
            {"position_id": "p2", "symbol": "ETHUSDT", "strategy": "intraday", "status": "open", "stop_state": "initial", "opened_cycle": 1, "tp1_ts": None},
        ],
    )

    out = evaluate_gates(
        policy=policy,
        state=state,
        now=datetime(2026, 2, 20, 14, 35, tzinfo=timezone.utc),
        idempotency_key="dup-key",
        side="buy",
        candle_closed=True,
        candle_ts="2026-02-20T14:35:00+00:00",
        htf_chop=10.0,
        sr_first_retest=True,
        bos_choch=True,
        secondary_hits=3,
    )

    assert out.accepted is False
    assert out.reason_codes[0] == "RISK_DAILY_LOSS_CAP_BREACH"
    assert "IDEMPOTENCY_DUPLICATE" in out.reason_codes
    assert "DAILY_CAP_REACHED" in out.reason_codes
    assert "ACTIVE_RISK_CAP_REACHED" in out.reason_codes
    assert "COOLDOWN_ACTIVE" in out.reason_codes
