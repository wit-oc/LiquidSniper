from liquidsniper.core.db import init_db


def test_strategy_account_migration_backfills_defaults(tmp_path):
    conn = init_db(str(tmp_path / "ls.db"))
    rows = conn.execute(
        "SELECT strategy, enabled FROM strategy_accounts WHERE account_id='paper_default' ORDER BY strategy"
    ).fetchall()

    assert rows == [("intraday", 1), ("scalp", 0), ("swing", 0)]

    idx = conn.execute("PRAGMA index_list('strategy_accounts')").fetchall()
    assert any(int(row[2]) == 1 for row in idx)
