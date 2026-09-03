"""拆股回溯复权 (jobs/fix_splits.py) —— 合成 sqlite + 注入 Yahoo 参考收盘, 不碰网络."""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "jobs"))
from fix_splits import apply_split, detect_discontinuities, infer_factor, run_split_fix  # noqa: E402

SCHEMA = """CREATE TABLE prices_daily (
    ticker TEXT, date TEXT, open REAL, high REAL, low REAL, close REAL, adj_close REAL,
    volume INTEGER, currency TEXT, close_usd REAL, adj_close_usd REAL,
    PRIMARY KEY (ticker, date))"""


def _db(rows):
    conn = sqlite3.connect(":memory:")
    conn.execute(SCHEMA)
    conn.executemany("INSERT INTO prices_daily VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                     [(t, d, c, c, c, c, c, v, "USD", c, c) for t, d, c, v in rows])
    return conn


def _crwd_like():
    # 库里 06-26 收 701.09 → 06-29 收 185.73 (4:1); Yahoo 今天给 06-26 的是 175.27 (已回调)
    return _db([("CRWD", "2026-06-25", 678.65, 3_000_000), ("CRWD", "2026-06-26", 701.09, 2_850_000),
                ("CRWD", "2026-06-29", 185.73, 19_759_000), ("CRWD", "2026-06-30", 190.79, 14_752_000),
                ("OK", "2026-06-26", 10.0, 100), ("OK", "2026-06-29", 10.5, 100)])


YAHOO = {("CRWD", "2026-06-26"): 175.27}      # 701.09 / 4 ≈ 175.27


def _ref(tk, day):
    return YAHOO.get((tk, day))


def test_detect_finds_only_the_cliff():
    hits = detect_discontinuities(_crwd_like())
    assert [(h["ticker"], h["date"]) for h in hits] == [("CRWD", "2026-06-29")]
    assert abs(hits[0]["ratio"] - 185.73 / 701.09) < 1e-6


def test_infer_factor_rules():
    hit = detect_discontinuities(_crwd_like())[0]
    assert abs(infer_factor(hit, 175.27) - 4.0) < 0.01     # Yahoo 已按 4 回调 → 因子 4
    assert infer_factor(hit, 701.09) is None                # Yahoo 也是 701 → 真崩盘 (MRNA/MLTX 型)
    assert infer_factor(hit, 350.0) is None                 # Yahoo 改了 (×2) 但与断崖 ×4 对不上 → 不动
    assert infer_factor(hit, None) is None


def test_run_fix_backadjusts_rows_before_cliff_and_is_idempotent():
    conn = _crwd_like()
    out = run_split_fix(conn, apply=True, ref_close_lookup=_ref, sleep=0)
    assert [(f["ticker"], round(f["factor"], 3), f["rows"]) for f in out["fixed"]] == [("CRWD", 4.0, 2)]
    got = dict(conn.execute("SELECT date, close FROM prices_daily WHERE ticker='CRWD'").fetchall())
    assert abs(got["2026-06-26"] - 175.27) < 0.01 and got["2026-06-29"] == 185.73
    vol = conn.execute("SELECT volume FROM prices_daily WHERE ticker='CRWD' AND date='2026-06-26'").fetchone()[0]
    assert vol == int(2_850_000 * (701.09 / 175.27))
    usd = conn.execute("SELECT close_usd, adj_close_usd FROM prices_daily WHERE ticker='CRWD' AND date='2026-06-25'").fetchone()
    assert abs(usd[0] - 678.65 / 4) < 0.05 and abs(usd[1] - 678.65 / 4) < 0.05
    again = run_split_fix(conn, apply=True, ref_close_lookup=_ref, sleep=0)   # 断崖已消失 → 无候选
    assert again["fixed"] == [] and again["unexplained"] == []


def test_unexplained_cliff_is_reported_not_touched():
    conn = _crwd_like()
    out = run_split_fix(conn, apply=True, ref_close_lookup=lambda t, d: 701.09, sleep=0)   # Yahoo 与库一致 = 真崩盘
    assert out["fixed"] == [] and [(u["ticker"], u["date"]) for u in out["unexplained"]] == [("CRWD", "2026-06-29")]
    assert conn.execute("SELECT close FROM prices_daily WHERE ticker='CRWD' AND date='2026-06-26'").fetchone()[0] == 701.09


def test_dry_run_changes_nothing_and_terminates():
    conn = _crwd_like()
    out = run_split_fix(conn, apply=False, ref_close_lookup=_ref, sleep=0)
    assert len(out["fixed"]) == 1 and out["fixed"][0]["rows"] == 0
    assert conn.execute("SELECT close FROM prices_daily WHERE ticker='CRWD' AND date='2026-06-26'").fetchone()[0] == 701.09


def test_two_splits_same_ticker_resolve_from_latest_backwards():
    # 2:1 在 03-02 生效 (库里 100→51), 再 4:1 在 06-29 (200→52); Yahoo 今天: 03-01 收 12.5 (100/8), 06-26 收 50 (200/4)
    conn = _db([("X", "2026-03-01", 100.0, 100), ("X", "2026-03-02", 51.0, 100),
                ("X", "2026-06-26", 200.0, 100), ("X", "2026-06-29", 52.0, 100)])
    ref = {("X", "2026-06-26"): 50.0, ("X", "2026-03-01"): 12.5}
    out = run_split_fix(conn, apply=True, ref_close_lookup=lambda t, d: ref.get((t, d)), sleep=0)
    assert [(round(f["factor"], 2), f["date"]) for f in out["fixed"]] == [(4.0, "2026-06-29"), (2.0, "2026-03-02")]
    got = dict(conn.execute("SELECT date, close FROM prices_daily WHERE ticker='X'").fetchall())
    assert abs(got["2026-03-01"] - 12.5) < 1e-9 and abs(got["2026-03-02"] - 12.75) < 1e-9 and got["2026-06-26"] == 50.0


def test_reverse_split_factor_below_one():
    conn = _db([("RS", "2026-03-01", 1.0, 1000), ("RS", "2026-03-02", 10.2, 100)])   # 1:10 反向; Yahoo 03-01 收 10.0
    hit = detect_discontinuities(conn)[0]
    assert abs(infer_factor(hit, 10.0) - 0.1) < 1e-9
    assert apply_split(conn, "RS", "2026-03-02", 0.1) == 1
    assert abs(conn.execute("SELECT close FROM prices_daily WHERE ticker='RS' AND date='2026-03-01'").fetchone()[0] - 10.0) < 1e-9
