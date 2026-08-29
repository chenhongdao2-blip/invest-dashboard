"""申万31行业 + 港股HSCI行业 周线 → seed CSV → sw_industry_daily (RRG 板块轮动).

2026-08-29 起替代 jobs/pull_sw_industry_ifind.py（iFind 2026-08-21 停用后该管道
死亡，数据卡在 2026-06-05）。本脚本是**可直接运行的 Wind 版**，不再是「父会话
MCP recipe」——WindPy 绑 python3.14，本地 Wind 终端在线即可跑。

沿用两段式：本地拉 → committed seed CSV → jobs/load_sw_industry.py 入库
（loader 任何环境可跑；cloud workflow 亦可对 committed seed 幂等入库）。

ticker 命名铁律：**db / RRG 页的 key 保持 iFind 时代原样**（801xxx.SL /
HSCI*.HK / HSI.GI / 000300.SH），Wind 代码只做内部映射：
    801xxx.SL → 801xxx.SI    HSCI*.HK → HSCI*.HI    HSI.GI → HSI.HI
换源连续性（2026-08-29 实测）：801010/801780/HSCICD/000300 四锚点收盘价与
iFind 旧值逐分不差；换手率口径差 <1%（801010: 9.2202 vs 9.2295）。

Run:  python3.14 jobs/pull_sw_industry_wind.py        # 拉取+写 seed+入库
"""
from __future__ import annotations

import csv
import sqlite3
import subprocess
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DB = REPO / "data" / "snapshots.db"
SEED_A = REPO / "data" / "external" / "sw_industry_seed.csv"
SEED_HK = REPO / "data" / "external" / "hk_sector_seed.csv"
START = "2025-06-01"

# 换源锚点：iFind 时代收盘价，Wind 必须逐一吻合（防拿错指数族）。
ANCHORS = {  # (ticker, date) -> close
    ("801010.SL", "2026-06-05"): 2379.55,
    ("801780.SL", "2026-06-05"): 3954.25,
    ("HSCICD.HK", "2026-06-05"): 2563.90,
    ("000300.SH", "2026-06-05"): 4816.9199,
    ("HSCIE.HK", "2026-06-05"): 15348.36,
    ("HSCIT.HK", "2026-06-05"): 1674.62,
}

# Wind 助记符与 iFind/HSI 官方不完全一致：6 个行业换了字母（2026-08-29 用
# w.wss sec_name 撒网实测；直接 .HK→.HI 会得到 EC=0 全 None 的 Wind 经典陷阱）。
_HK_OVERRIDE = {
    "HSCIE.HK": "HSCIEN.HI",   # 能源业
    "HSCIF.HK": "HSCIFN.HI",   # 金融业
    "HSCIIG.HK": "HSCIIN.HI",  # 工业
    "HSCIM.HK": "HSCIMT.HI",   # 原材料业
    "HSCIT.HK": "HSCITC.HI",   # 电讯业
    "HSCIU.HK": "HSCIUT.HI",   # 公用事业
}


def wind_code(ticker: str) -> str:
    if ticker == "HSI.GI":
        return "HSI.HI"
    if ticker in _HK_OVERRIDE:
        return _HK_OVERRIDE[ticker]
    if ticker.endswith(".SL"):
        return ticker[:-3] + ".SI"
    if ticker.endswith(".HK"):
        return ticker[:-3] + ".HI"
    return ticker  # 000300.SH


def universe() -> list[tuple[str, str, str]]:
    """(ticker, name_cn, market) 从 db 派生 —— 刷新对象=已存在的板块集合, 不漂移。"""
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    rows = con.execute(
        "SELECT DISTINCT ticker, name_cn, market FROM sw_industry_daily ORDER BY market, ticker"
    ).fetchall()
    con.close()
    if len(rows) < 40:  # 32 A股 + 12 HK
        sys.exit(f"[fatal] db 里只有 {len(rows)} 个板块(<40)，宇宙异常，不刷新")
    return rows


def fetch(w, ticker: str) -> list[tuple[str, float, float | None]]:
    r = w.wsd(wind_code(ticker), "close,turn", START, date.today().isoformat(), "Period=W")
    if r.ErrorCode != 0:
        print(f"  [warn] {ticker} Wind ErrorCode={r.ErrorCode}，跳过")
        return []
    closes, turns = r.Data[0], (r.Data[1] if len(r.Data) > 1 else [None] * len(r.Times))
    out = []
    for t, c, tr in zip(r.Times, closes, turns):
        if c != c or c is None:  # NaN guard
            continue
        out.append((t.isoformat() if hasattr(t, "isoformat") else str(t),
                    round(float(c), 4),
                    round(float(tr), 4) if tr is not None and tr == tr else None))
    return out


def main() -> None:
    from WindPy import w

    w.start()
    a_rows, hk_rows, fetched = [], [], {}
    for ticker, name_cn, market in universe():
        series = fetch(w, ticker)
        if not series:
            continue
        fetched[ticker] = dict((d, c) for d, c, _ in series)
        bucket = hk_rows if market == "hk" else a_rows
        for d, c, tr in series:
            bucket.append((ticker, name_cn, d, c, tr))
        print(f"  {ticker} {name_cn}: {len(series)} 周点, 末点 {series[-1][0]} {series[-1][1]}")

    # 锚点连续性校验：任一失败即拒绝写盘
    for (ticker, d), expect in ANCHORS.items():
        got = fetched.get(ticker, {}).get(d)
        if got is None or abs(got - expect) > 0.01:
            sys.exit(f"[fatal] 锚点 {ticker}@{d} 校验失败: Wind={got} vs iFind={expect}，不写盘")

    n_a = len({r[0] for r in a_rows})
    n_hk = len({r[0] for r in hk_rows})
    if n_a < 30 or n_hk < 10:
        sys.exit(f"[fatal] 覆盖不足 a_share={n_a} hk={n_hk}，不写盘")

    for path, rows in ((SEED_A, a_rows), (SEED_HK, hk_rows)):
        with path.open("w", newline="", encoding="utf-8") as f:
            wcsv = csv.writer(f)
            wcsv.writerow(["ticker", "name_cn", "date", "close", "turnover_rate"])
            wcsv.writerows(rows)
        print(f"[ok] {path.name}: {len(rows)} 行 / {len({r[0] for r in rows})} 板块")

    # 入库（幂等 upsert）+ manifest
    subprocess.run([sys.executable, str(REPO / "jobs" / "load_sw_industry.py")], check=True)
    subprocess.run([sys.executable, str(REPO / "jobs" / "update_manifest.py"),
                    "sw_industry_daily", "ok"], check=False)


if __name__ == "__main__":
    main()
