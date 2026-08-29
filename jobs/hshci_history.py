"""恒生医疗保健指数(HSHCI.HK) 长周期完整轨迹 — 2021.7 至今 绝对点位。

一条线讲完「−70% → 翻倍 → 回调」：2021.7 高位 → 2024.6 见底(−69%) →
2025.9 反弹峰(较底 +118%, ×2.2) → 今。

产物:
  data/external/hshci_history_monthly.csv  — committed, 看板 + Excel 下载读
  data/external/hshci_history.png          — 独立日历时间单线图(带 4 个里程碑标注)

数据: Wind 指数月收盘点位 w.wsd("HSHCI.HI", Period=M)（HSHCI 不在 Yahoo）。
Wind 月线的末点自动落在最新交易日 → 天然满足「末点为最新交易日」口径。
2026-08-29 起由 iFind 切换 Wind（iFind 2026-08-21 停用）；切换时已用三个
历史月锚点（2021-07 / 2024-06 / 2025-09）核对，两源逐分不差，见 ANCHORS。

Run（须本机 Wind 终端在线；WindPy 绑 python3.14）:
    python3.14 jobs/hshci_history.py
"""

from __future__ import annotations

import csv
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT_CSV = REPO / "data" / "external" / "hshci_history_monthly.csv"
OUT_PNG = REPO / "data" / "external" / "hshci_history.png"

START = "2021-07-01"
SOURCE_LABEL = "Wind 指数月收盘(末点最新交易日)"

# 换源连续性锚点：iFind 时代烘焙值，Wind 返回值必须逐一吻合，防止拿错指数/口径。
ANCHORS = {
    "2021-07-30": 6797.79,   # 起点高位
    "2024-06-28": 2083.51,   # 见底月
    "2025-09-30": 4551.28,   # 反弹峰月
}

INK = "#1A1A1A"
GREY = "#8A8580"
CMSI_RED = "#C8102E"


def fetch_rows() -> list[tuple[str, float]]:
    """Wind 月线 HSHCI.HI；带锚点连续性校验，不通过就拒绝写盘。"""
    from WindPy import w

    w.start()
    r = w.wsd("HSHCI.HI", "close", START, date.today().isoformat(), "Period=M")
    if r.ErrorCode != 0:
        sys.exit(f"[fatal] Wind ErrorCode={r.ErrorCode}, 不写盘（保留旧 CSV）")
    rows = [(t.isoformat() if hasattr(t, "isoformat") else str(t), round(float(c), 2))
            for t, c in zip(r.Times, r.Data[0]) if c == c]  # NaN guard
    if len(rows) < 55:
        sys.exit(f"[fatal] Wind 只返回 {len(rows)} 个月点(<55)，疑截断，不写盘")
    got = dict(rows)
    for d, expect in ANCHORS.items():
        if abs(got.get(d, float("nan")) - expect) > 0.01:
            sys.exit(f"[fatal] 锚点 {d} 校验失败: Wind={got.get(d)} vs iFind烘焙={expect}，"
                     f"疑指数/口径漂移，不写盘")
    return rows


def milestones(rows):
    """start / trough / recovery-peak(after trough) / now — data-driven, no hardcoded prose."""
    closes = [c for _, c in rows]
    i_start = 0
    i_trough = min(range(len(rows)), key=lambda i: closes[i])
    i_peak = max(range(i_trough, len(rows)), key=lambda i: closes[i])
    i_now = len(rows) - 1
    return {
        "start": (rows[i_start][0], closes[i_start]),
        "trough": (rows[i_trough][0], closes[i_trough], closes[i_trough] / closes[i_start] - 1),
        "peak": (rows[i_peak][0], closes[i_peak], closes[i_peak] / closes[i_trough] - 1),
        "now": (rows[i_now][0], closes[i_now],
                closes[i_now] / closes[i_peak] - 1, closes[i_now] / closes[i_start] - 1),
    }


def _ym(d: str) -> str:
    """'2024-06-28' → '2024.6'（里程碑标签随数据走，不再硬编码年月）。"""
    y, m, _ = d.split("-")
    return f"{y}.{int(m)}"


def write_csv(rows, asof: str):
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "close", "source", "asof"])
        for d, c in rows:
            w.writerow([d, c, SOURCE_LABEL, asof])


def render_png(rows, asof: str):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib import rcParams

    rcParams["font.sans-serif"] = ["Arial Unicode MS"]
    rcParams["axes.unicode_minus"] = False

    xs = [date.fromisoformat(d) for d, _ in rows]
    ys = [c for _, c in rows]
    m = milestones(rows)

    fig, ax = plt.subplots(figsize=(11.0, 6.0), dpi=200)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    ax.plot(xs, ys, color=CMSI_RED, lw=2.6, zorder=3)
    ax.fill_between(xs, ys, min(ys) - 200, color=CMSI_RED, alpha=0.05, zorder=1)

    def pt(key):
        d = date.fromisoformat(m[key][0]); return d, m[key][1]

    for key, color in [("start", INK), ("trough", GREY), ("peak", CMSI_RED), ("now", CMSI_RED)]:
        d, v = pt(key)
        ax.scatter([d], [v], color=color, s=46, zorder=5)

    sd, sv = pt("start")
    ax.annotate(f"{_ym(m['start'][0])} 高位\n{sv:,.0f}", (sd, sv), textcoords="offset points",
                xytext=(6, 8), fontsize=10, fontweight="bold", color=INK)
    td, tv = pt("trough")
    ax.annotate(f"{_ym(m['trough'][0])} 见底 {tv:,.0f}\n自高位 {m['trough'][2]:+.0%}", (td, tv),
                textcoords="offset points", xytext=(-6, -42), fontsize=10,
                fontweight="bold", color=GREY, ha="center")
    pd_, pv = pt("peak")
    ax.annotate(f"{_ym(m['peak'][0])} 反弹 {pv:,.0f}\n较底 {m['peak'][2]:+.0%} (×{1+m['peak'][2]:.1f})",
                (pd_, pv), textcoords="offset points", xytext=(-150, 6), fontsize=10,
                fontweight="bold", color=CMSI_RED)
    nd, nv = pt("now")
    ax.annotate(f"今 {nv:,.0f}\n较峰 {m['now'][2]:+.0%}", (nd, nv),
                textcoords="offset points", xytext=(10, -6), fontsize=10.5,
                fontweight="bold", color=CMSI_RED, va="center")

    ax.set_title("恒生医疗保健指数：2021.7 以来完整轨迹（绝对点位）",
                 fontsize=15.5, fontweight="bold", pad=14, color=INK)
    ax.set_ylabel("指数点位", fontsize=12)
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.xaxis.set_minor_locator(mdates.MonthLocator((1, 7)))

    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(True, axis="y", color="#ECECEC", lw=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.set_ylim(min(ys) - 250, max(ys) + 450)

    note = (f"完整轨迹：{_ym(m['start'][0])} {sv:,.0f} → {_ym(m['trough'][0])} 见底 {tv:,.0f}"
            f"（{m['trough'][2]:+.0%}）→ {_ym(m['peak'][0])} 反弹 {pv:,.0f}"
            f"（较底 {m['peak'][2]:+.0%}）→ 今 {nv:,.0f}"
            f"（较峰 {m['now'][2]:+.0%}，较 {_ym(m['start'][0])} 仍 {m['now'][3]:+.0%}）。"
            f"来源：Wind 指数月收盘，截至 {asof}。")
    fig.text(0.01, 0.012, note, fontsize=8, color=GREY)
    fig.subplots_adjust(left=0.085, right=0.965, top=0.91, bottom=0.12)
    fig.savefig(OUT_PNG, facecolor="white")
    plt.close(fig)


def main():
    rows = fetch_rows()
    asof = rows[-1][0]
    write_csv(rows, asof)
    render_png(rows, asof)
    m = milestones(rows)
    print(f"[ok] {OUT_CSV}  ({len(rows)} 月点, 截至 {asof}, 源 Wind)")
    print(f"[ok] {OUT_PNG}")
    print(f"  start {m['start'][1]:,.0f} → trough {m['trough'][1]:,.0f} ({m['trough'][2]:+.1%}) "
          f"→ peak {m['peak'][1]:,.0f} ({m['peak'][2]:+.1%}) → now {m['now'][1]:,.0f} "
          f"(vs peak {m['now'][2]:+.1%}, vs start {m['now'][3]:+.1%})")


if __name__ == "__main__":
    main()
