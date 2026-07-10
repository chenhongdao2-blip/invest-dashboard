"""一次性构建 高股息 v1/v2 全量评分明细 → data/external/hd_v1_v2_full_scorecard.csv

对应生科 v4/v5 的 v4_v5_full_scorecard.md（L6 归因附表），HD 版从评分底稿直接生成：
  v1 (34支, 2026-03-20 建仓): 「高股息名单_Agent增强版_2026-03-19.xlsx」Agent总分/分项
      —— 已核: Agent总分与 dashboard hd_picks.csv 34/34 完全一致（招行 87=49/22/16）。
      xlsx 有 37 支，其中 3 支(信义光能/中国海外发展/中国石油股份)不在建仓池 → 剔除。
  v2 (54支, 2026-06-11 建仓): 「高股息Part2_定性评分底稿_2026-06-10.xlsx」总分排名 sheet
      —— 已核: 54 支完整、book 20 支总分与 hd_picks_v2.csv 完全一致（美的 84=47/20/17）。

段收益: yfinance auto_adjust=True 含息复权（归因正式口径为 Wind TR，或有小差 → 表格
脚注已声明）。段区间: v1 = 2026-03-20 → 2026-06-11；v2 = 2026-06-11 → 2026-07-07。
同时打印「选中效果」汇总（Top20等权/全池等权/仅未建仓/3466 段收益）供页面常量使用。

运行: .venv/bin/python jobs/build_hd_scorecard.py   （需代理 127.0.0.1:7897）
"""
import os

import pandas as pd
import yfinance as yf

os.environ.setdefault("HTTP_PROXY", "http://127.0.0.1:7897")
os.environ.setdefault("HTTPS_PROXY", "http://127.0.0.1:7897")

REPO = "/Users/gcc/invest-dashboard"
V1_XLSX = ("/Users/gcc/Desktop/Desktop - GCC的MacBook Pro/📈 高股息研究专项/"
           "名单评分历史/高股息名单_Agent增强版_2026-03-19.xlsx")
V2_XLSX = "/Users/gcc/Desktop/💰 港股高股息策略/高股息Part2_定性评分底稿_2026-06-10.xlsx"
OUT = f"{REPO}/data/external/hd_v1_v2_full_scorecard.csv"

SEGS = {"hd_v1": ("2026-03-20", "2026-06-11"), "hd_v2": ("2026-06-11", "2026-07-07")}
BENCH = "3466.HK"

# v2 总分排名 sheet 行业 slug → 中文（held 20 直接用 hd_picks_v2 的中文 sector）
SECTOR_CN = {
    "consumer": "消费", "bank": "银行", "insurance": "保险", "utility": "公用",
    "energy": "能源", "telecom": "电讯", "industrial": "工业", "property": "地产",
    "property_mgmt": "物管", "transport": "交通", "infra": "基建", "materials": "材料",
    "healthcare": "医疗", "tech": "科技", "financial": "金融", "coal": "煤炭",
    "oil_gas": "油气", "highway": "高速公路", "port": "港口", "shipping": "航运",
    "textile": "纺织", "apparel": "服装", "food_bev": "食品饮料", "gas": "燃气",
    "power": "电力", "nickel_metal": "镍金属", "steel": "钢铁", "chemical": "化工",
}


def grade_band(total: float) -> str:
    """评级带与 2026-03 报告一致: ≥80 优秀 / 70-79 良好 / 60-69 中等 / <60 一般"""
    if total >= 80:
        return "优秀"
    if total >= 70:
        return "良好"
    if total >= 60:
        return "中等"
    return "一般"


def build_v1() -> pd.DataFrame:
    x = pd.ExcelFile(V1_XLSX).parse("Sheet1")
    hd = pd.read_csv(f"{REPO}/data/external/hd_picks.csv")
    xm = {str(r["股票代码"]): r for _, r in x.iterrows()}
    rows = []
    for _, p in hd.iterrows():  # hd_picks rank order = Agent总分 desc
        r = xm[p["ticker"]]
        assert int(r["Agent总分"]) == int(p["score"]), (p["ticker"], r["Agent总分"], p["score"])
        rows.append({
            "version": "hd_v1", "num": int(p["rank"]), "held": int(p["rank"]) <= 20,
            "tick": p["ticker"], "name": p["name"], "sector": p["sector"],
            "gov": int(r["Agent_治理"]), "fin": int(r["Agent_财务"]),
            "moat": int(r["Agent_护城河"]), "final": int(r["Agent总分"]),
            "status": grade_band(int(r["Agent总分"])),
        })
    return pd.DataFrame(rows)


def build_v2() -> pd.DataFrame:
    d = pd.ExcelFile(V2_XLSX).parse("总分排名", header=0).dropna(subset=["代码"])
    v2 = pd.read_csv(f"{REPO}/data/external/hd_picks_v2.csv")
    held_map = {r["ticker"].replace(".HK", "").lstrip("0"): r for _, r in v2.iterrows()}
    rows = []
    for _, r in d.iterrows():
        code4 = str(r["代码"]).replace(".HK", "").lstrip("0")
        tick = f"{code4.zfill(4)}.HK"
        hp = held_map.get(code4)
        sector = hp["sector"] if hp is not None else SECTOR_CN.get(str(r["行业"]), str(r["行业"]))
        kill = str(r["kill_switches"]) if pd.notna(r["kill_switches"]) else ""
        status = str(r["评级"]) + (f" · {kill}" if kill else "")
        if hp is not None:
            assert int(r["总分"]) == int(hp["score"]), (tick, r["总分"], hp["score"])
        rows.append({
            "version": "hd_v2", "num": int(r["排名"]), "held": hp is not None,
            "tick": tick, "name": str(r["名称"]), "sector": sector,
            "gov": int(r["治理/55"]), "fin": int(r["财务/25"]),
            "moat": int(r["护城河/20"]), "final": int(r["总分"]),
            "status": status,
        })
    return pd.DataFrame(rows)


def seg_returns(df: pd.DataFrame) -> pd.DataFrame:
    out = []
    for ver, (d0, d1) in SEGS.items():
        sub = df[df["version"] == ver].copy()
        ticks = sub["tick"].tolist() + [BENCH]
        px = yf.download(
            ticks,
            start=(pd.Timestamp(d0) - pd.Timedelta(days=7, unit=None)).date().isoformat(),
            end=(pd.Timestamp(d1) + pd.Timedelta(days=2, unit=None)).date().isoformat(),
            auto_adjust=True, progress=False, threads=True,
        )
        close = px["Close"] if isinstance(px.columns, pd.MultiIndex) else px[["Close"]]

        def seg(t: str) -> float | None:
            if t not in close.columns:
                return None
            s = close[t].dropna()
            a = s[s.index <= pd.Timestamp(d0)]
            b = s[s.index <= pd.Timestamp(d1)]
            if a.empty or b.empty:
                return None
            return (b.iloc[-1] / a.iloc[-1] - 1) * 100

        sub["seg_ret"] = [None if (v := seg(t)) is None else round(v, 1)
                          for t in sub["tick"]]
        miss = sub[sub["seg_ret"].isna()]["tick"].tolist()
        if miss:
            print(f"[{ver}] NO PRICE DATA: {miss}")

        # 选中效果汇总（等权口径，隔离 ranking quality；基准=3466 风格基准）
        held = sub[sub["held"]]["seg_ret"].dropna()
        pool = sub["seg_ret"].dropna()
        unheld = sub[~sub["held"]]["seg_ret"].dropna()
        b = seg(BENCH)
        print(f"[{ver}] summary: top20_ew={held.mean():+.2f}%  pool_ew={pool.mean():+.2f}%  "
              f"unheld_ew={unheld.mean():+.2f}%({len(unheld)}支)  3466={b:+.2f}%  "
              f"diff={held.mean() - pool.mean():+.2f}pp")
        out.append(sub)
    return pd.concat(out, ignore_index=True)


if __name__ == "__main__":
    df = pd.concat([build_v1(), build_v2()], ignore_index=True)
    print(f"v1 rows: {(df.version == 'hd_v1').sum()} (held {df[df.version == 'hd_v1'].held.sum()})  "
          f"v2 rows: {(df.version == 'hd_v2').sum()} (held {df[df.version == 'hd_v2'].held.sum()})")
    df = seg_returns(df)
    df.to_csv(OUT, index=False)
    print(f"wrote {OUT}: {len(df)} rows")
