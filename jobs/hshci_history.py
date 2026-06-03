"""恒生医疗保健指数(HSHCI.HK) 长周期完整轨迹 — 2021.7 至今 绝对点位。

一条线讲完「−70% → 翻倍 → 回调」：2021.7 高位 → 2024.6 见底(−69%) →
2025.9 反弹峰(较底 +118%, ×2.2) → 今(较峰 −26%)。

产物:
  data/external/hshci_history_monthly.csv  — committed, 看板 + Excel 下载读
  data/external/hshci_history.png          — 独立日历时间单线图(带 4 个里程碑标注)

数据: iFind 指数月收盘点位(HSHCI 不在 Yahoo)；末点 2026-06-01 日频 3357.89
(与看板相对表现末点一致)。来源: iFind 指数行情，截至 2026-06-03。

Run:
    uv run --with pandas --with matplotlib python jobs/hshci_history.py
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT_CSV = REPO / "data" / "external" / "hshci_history_monthly.csv"
OUT_PNG = REPO / "data" / "external" / "hshci_history.png"
ASOF = "2026-06-03"

# (date, 收盘点位) — iFind 指数月收盘；末点为 2026-06-01 日频
ROWS = [
    ("2021-07-30", 6797.79), ("2021-08-31", 6189.86), ("2021-09-30", 6055.17),
    ("2021-10-29", 5533.48), ("2021-11-30", 5386.32), ("2021-12-31", 4726.51),
    ("2022-01-31", 4040.59), ("2022-02-28", 4042.98), ("2022-03-31", 3675.70),
    ("2022-04-29", 3379.05), ("2022-05-31", 3354.39), ("2022-06-30", 3844.93),
    ("2022-07-29", 3620.03), ("2022-08-31", 3461.51), ("2022-09-30", 2816.60),
    ("2022-10-31", 2790.86), ("2022-11-30", 3571.49), ("2022-12-30", 3812.62),
    ("2023-01-31", 4114.84), ("2023-02-28", 3683.29), ("2023-03-31", 3491.70),
    ("2023-04-28", 3601.89), ("2023-05-31", 3126.47), ("2023-06-30", 2981.44),
    ("2023-07-31", 3239.02), ("2023-08-31", 2925.05), ("2023-09-29", 2897.64),
    ("2023-10-31", 3043.83), ("2023-11-30", 3087.24), ("2023-12-29", 2877.71),
    ("2024-01-31", 2186.31), ("2024-02-29", 2456.25), ("2024-03-28", 2268.46),
    ("2024-04-30", 2286.03), ("2024-05-31", 2204.20), ("2024-06-28", 2083.51),
    ("2024-07-31", 2098.40), ("2024-08-30", 2176.41), ("2024-09-30", 2736.02),
    ("2024-10-31", 2422.17), ("2024-11-29", 2411.19), ("2024-12-31", 2332.91),
    ("2025-01-28", 2342.90), ("2025-02-28", 2720.31), ("2025-03-31", 2921.43),
    ("2025-04-30", 2953.49), ("2025-05-30", 3182.64), ("2025-06-30", 3450.04),
    ("2025-07-31", 4236.57), ("2025-08-29", 4325.82), ("2025-09-30", 4551.28),
    ("2025-10-31", 4048.32), ("2025-11-28", 4044.78), ("2025-12-31", 3661.52),
    ("2026-01-30", 3974.92), ("2026-02-27", 3889.51), ("2026-03-31", 3688.14),
    ("2026-04-30", 3730.51), ("2026-05-29", 3383.26), ("2026-06-01", 3357.89),
]

INK = "#1A1A1A"
GREY = "#8A8580"
CMSI_RED = "#C8102E"


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


def write_csv():
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date", "close", "source", "asof"])
        for d, c in ROWS:
            w.writerow([d, c, "iFind 指数月收盘(末点日频)", ASOF])


def render_png():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from matplotlib import rcParams

    rcParams["font.sans-serif"] = ["Arial Unicode MS"]
    rcParams["axes.unicode_minus"] = False

    xs = [date.fromisoformat(d) for d, _ in ROWS]
    ys = [c for _, c in ROWS]
    m = milestones(ROWS)

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
    ax.annotate(f"2021.7 高位\n{sv:,.0f}", (sd, sv), textcoords="offset points",
                xytext=(6, 8), fontsize=10, fontweight="bold", color=INK)
    td, tv = pt("trough")
    ax.annotate(f"2024.6 见底 {tv:,.0f}\n自高位 {m['trough'][2]:+.0%}", (td, tv),
                textcoords="offset points", xytext=(-6, -42), fontsize=10,
                fontweight="bold", color=GREY, ha="center")
    pd_, pv = pt("peak")
    ax.annotate(f"2025.9 反弹 {pv:,.0f}\n较底 {m['peak'][2]:+.0%} (×{1+m['peak'][2]:.1f})",
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

    note = (f"完整轨迹：2021.7 {sv:,.0f} → 2024.6 见底 {tv:,.0f}（{m['trough'][2]:+.0%}）"
            f" → 2025.9 反弹 {pv:,.0f}（较底 {m['peak'][2]:+.0%}）→ 今 {nv:,.0f}"
            f"（较峰 {m['now'][2]:+.0%}，较 2021.7 仍 {m['now'][3]:+.0%}）。"
            f"来源：iFind 指数月收盘，截至 {ASOF}。")
    fig.text(0.01, 0.012, note, fontsize=8, color=GREY)
    fig.subplots_adjust(left=0.085, right=0.965, top=0.91, bottom=0.12)
    fig.savefig(OUT_PNG, facecolor="white")
    plt.close(fig)


def main():
    write_csv()
    render_png()
    m = milestones(ROWS)
    print(f"[ok] {OUT_CSV}")
    print(f"[ok] {OUT_PNG}")
    print(f"  start {m['start'][1]:,.0f} → trough {m['trough'][1]:,.0f} ({m['trough'][2]:+.1%}) "
          f"→ peak {m['peak'][1]:,.0f} ({m['peak'][2]:+.1%}) → now {m['now'][1]:,.0f} "
          f"(vs peak {m['now'][2]:+.1%}, vs start {m['now'][3]:+.1%})")


if __name__ == "__main__":
    main()
