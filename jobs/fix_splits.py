#!/usr/bin/env python3
"""拆股回溯复权 —— 修 prices_daily 里「拆股前入库、之后没被回调」的旧行。

背景 (2026-09-02 实锤): fetch_eod 用 auto_adjust=False 增量抓取。Yahoo 的 Close 本身就是
拆股回调后的序列, 但增量只拉新日期, 拆股前已入库的行永远停在拆股前价格 → CRWD 2026-06-29
4:1 拆股后库里 06-26 收 701.09 / 06-29 收 185.73, adj_close == close, 任何用该表算区间收益
的地方 (YTD / RRG / 相对表现) 对它都是错的 (原始 −51.8%, 修正后 +92.6%)。

做法 (幂等, 云端 cron 每次跑):
    1. 全表扫 prices_daily: 日间 close 比值落在 [RATIO_LO, RATIO_HI] 之外 = 断崖候选。
    2. 只对断崖票向 Yahoo 拉「断崖前一日」的当前 Close: 因子 = 库内 prev_close / Yahoo prev_close。
       因子 ≠ 1 且与断崖比值 prev/next 吻合 (相对误差 < FACTOR_TOL) 才确认 —— Yahoo 已把历史按该
       因子回调、库里没跟上。真崩盘 (MRNA/MLTX) Yahoo 当日收盘与库内一致 → 因子 1 → 不动。
       不按 yfinance splits 事件日匹配, 因为: ① 事件日 ≠ 价格生效日 (CRWD 事件 07-02, 断崖 06-29);
       ② 断崖可能在上次 backfill 窗口起点而非拆股日 (KLAC 事件 2026-06-12, 断崖 2025-12-09,
       因为 backfill 已把 12-09 起的行重写成回调价); ③ JP 票 Yahoo 常缺事件 (1306.T/3110.T/5801.T)。
       splits 事件只作报告注记。
    3. 确认的: 断崖日之前所有行 open/high/low/close/adj_close/close_usd/adj_close_usd ÷ 因子,
       volume × 因子 —— 与今天重新整段下载得到的序列一致。回调后断崖消失, 再跑不会重复回调。
    4. 对不上的断崖只列报告, 不动数据。

用法:
    python3 jobs/fix_splits.py            # 报告 + 回调
    python3 jobs/fix_splits.py --dry-run  # 只报告
    python3 jobs/fix_splits.py --only CRWD,1306.T
fetch_eod.main 在价格 upsert 后调用 run_split_fix(conn) (try/except, 永不阻断 cron)。
"""
from __future__ import annotations

import argparse
import sqlite3
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "snapshots.db"

RATIO_LO, RATIO_HI = 0.55, 1.8     # 日间 close 比值 (今日/昨日) 出此区间 = 断崖候选 (单日 ±45% 以上)
FACTOR_TOL = 0.12                  # |prev/next ÷ factor − 1| 容差 (拆股日本身还有正常涨跌)
MIN_FACTOR_DEV = 0.10              # 因子距 1 至少 10% 才算 Yahoo 回调过 (排除正常日内差异)
PRICE_COLS = ("open", "high", "low", "close", "adj_close", "close_usd", "adj_close_usd")


def detect_discontinuities(conn: sqlite3.Connection, only: list[str] | None = None) -> list[dict]:
    """全表扫日间 close 断崖 → [{ticker, date, prev_date, prev_close, close, ratio}]."""
    q = "SELECT ticker, date, close FROM prices_daily WHERE close IS NOT NULL AND close > 0"
    params: tuple = ()
    if only:
        q += f" AND ticker IN ({','.join('?' * len(only))})"
        params = tuple(only)
    df = pd.read_sql_query(q + " ORDER BY ticker, date", conn, params=params)
    if df.empty:
        return []
    df["prev_close"] = df.groupby("ticker")["close"].shift(1)
    df["prev_date"] = df.groupby("ticker")["date"].shift(1)
    df["ratio"] = df["close"] / df["prev_close"]
    hits = df[(df["ratio"] < RATIO_LO) | (df["ratio"] > RATIO_HI)]
    return [
        {"ticker": r.ticker, "date": r.date, "prev_date": r.prev_date,
         "prev_close": float(r.prev_close), "close": float(r.close), "ratio": float(r.ratio)}
        for r in hits.itertuples(index=False)
    ]


def yahoo_ref_close(ticker: str, day: str) -> float | None:
    """Yahoo 今天对 `day` 的 Close (auto_adjust=False 下 Close 已按拆股回调、未按分红回调). 失败 None."""
    try:
        import yfinance as yf
        d0 = date.fromisoformat(day)
        h = yf.download(ticker, start=d0.isoformat(), end=(d0 + timedelta(days=1)).isoformat(),
                        auto_adjust=False, progress=False)
    except Exception as e:  # noqa: BLE001 - 单票失败不阻断
        print(f"  ! {ticker}: yahoo fetch failed ({e})")
        return None
    if h is None or h.empty:
        return None
    col = h["Close"]
    if isinstance(col, pd.DataFrame):
        col = col.iloc[:, 0]
    col = col.dropna()
    return float(col.iloc[0]) if len(col) else None


def infer_factor(hit: dict, ref_prev_close: float | None) -> float | None:
    """库内 prev_close / Yahoo 当前 prev_close = Yahoo 已回调的因子; 与断崖比值吻合才返回, 否则 None."""
    if not ref_prev_close or ref_prev_close <= 0:
        return None
    factor = hit["prev_close"] / ref_prev_close
    if abs(factor - 1) < MIN_FACTOR_DEV:
        return None                                   # Yahoo 也是这个价 → 真涨跌, 不是回调
    implied = hit["prev_close"] / hit["close"]          # 4:1 拆股 ≈ 4; 1:10 反向 ≈ 0.1
    if abs(implied / factor - 1) > FACTOR_TOL:
        return None                                   # Yahoo 改了但与断崖对不上, 不敢动
    return factor


def apply_split(conn: sqlite3.Connection, ticker: str, before_date: str, factor: float) -> int:
    """断崖日之前的行按因子回调; 返回改动行数."""
    sets = ", ".join(f"{c} = {c} / ?" for c in PRICE_COLS) + ", volume = CAST(volume * ? AS INTEGER)"
    cur = conn.execute(
        f"UPDATE prices_daily SET {sets} WHERE ticker = ? AND date < ?",
        tuple([factor] * len(PRICE_COLS)) + (factor, ticker, before_date),
    )
    return cur.rowcount


def run_split_fix(conn: sqlite3.Connection, apply: bool = True, only: list[str] | None = None,
                  ref_close_lookup=yahoo_ref_close, sleep: float = 0.5) -> dict:
    """主入口. 返回 {'fixed': [...], 'unexplained': [...]}; 每项含 ticker/date/ratio(/factor/rows).

    ref_close_lookup(ticker, day) → Yahoo 当前对该日的 Close (测试注入合成值)。"""
    fixed: list[dict] = []
    unexplained: list[dict] = []
    tickers = sorted({h["ticker"] for h in detect_discontinuities(conn, only)})
    for tk in tickers:
        judged: set[str] = set()          # 本票已判「非回调」的断崖日, 不再重复查
        while True:
            # 每次回调后重新探测: 回调改的是断崖之前的全部行, 更早断崖的 prev/close 快照会失效
            pending = [h for h in detect_discontinuities(conn, [tk]) if h["date"] not in judged]
            if not pending:
                break
            hit = max(pending, key=lambda h: h["date"])   # 先处理最晚的断崖
            ref = ref_close_lookup(tk, hit["prev_date"])
            if sleep:
                time.sleep(sleep)
            f = infer_factor(hit, ref)
            if f is None:
                judged.add(hit["date"])
                unexplained.append(hit)
                ref_s = f"Yahoo {hit['prev_date']} 收 {ref:.2f}" if ref else "Yahoo 无数据"
                print(f"  ? {tk} {hit['prev_date']}→{hit['date']} close {hit['prev_close']:.2f}→{hit['close']:.2f} "
                      f"(×{hit['ratio']:.3f}) {ref_s}, 非回调, 不动")
                continue
            n = apply_split(conn, tk, hit["date"], f) if apply else 0
            fixed.append({**hit, "factor": f, "rows": n})
            print(f"  {'✓' if apply else '·'} {tk} {hit['date']} Yahoo 已回调因子 {f:.4g} → 回调 {hit['date']} 之前"
                  f"{' ' + str(n) + ' 行' if apply else ' (dry-run)'}")
            if not apply:
                judged.add(hit["date"])   # dry-run 不改库, 断崖不会消失, 防死循环
    if apply and fixed:
        conn.commit()
    return {"fixed": fixed, "unexplained": unexplained}


def main() -> None:
    ap = argparse.ArgumentParser(description="prices_daily 拆股回溯复权")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", default="", help="逗号分隔 ticker")
    args = ap.parse_args()
    if not DB_PATH.exists():
        raise SystemExit(f"DB not found: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    only = [t.strip() for t in args.only.split(",") if t.strip()] or None
    out = run_split_fix(conn, apply=not args.dry_run, only=only)
    print(f"[fix_splits] fixed={len(out['fixed'])} unexplained={len(out['unexplained'])}"
          f"{' (dry-run)' if args.dry_run else ''}")


if __name__ == "__main__":
    main()
