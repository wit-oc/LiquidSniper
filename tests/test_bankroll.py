from liquidsniper.core.bankroll import BankrollState


def test_bankroll_reserve_release_and_realize() -> None:
    b = BankrollState(10000)

    assert b.reserve_risk(500) is True
    s1 = b.snapshot()
    assert s1.available_usd == 9500
    assert s1.reserved_risk_usd == 500

    b.release_reserved(300)
    s2 = b.snapshot()
    assert s2.available_usd == 9800
    assert s2.reserved_risk_usd == 200

    b.realize_pnl(150)
    s3 = b.snapshot()
    assert s3.available_usd == 9950
    assert s3.realized_pnl_usd == 150


def test_bankroll_rejects_over_reserve() -> None:
    b = BankrollState(1000)
    assert b.reserve_risk(1200) is False
    s = b.snapshot()
    assert s.available_usd == 1000
    assert s.reserved_risk_usd == 0
