"""恒生医疗保健指数(HSHCI.HK) 两轮下跌对比图。

把 2021-07→2024-06 的结构性熊市，与 2025-08→今 的本轮回调，各自 rebased=100、
按「距起点月数」对齐叠在一张图上——同一起跑线直接比下跌深度与节奏。

数据：iFind 指数月收盘点位（HSHCI 不在 Yahoo，必须 iFind）；本轮起点用 2025-08-01
日频 4132.88（与看板相对表现锚点一致），末点 2026-06-01 日频 3357.89。
来源: iFind 指数行情，截至 2026-06-03。

Run:
    uv run --with pandas --with matplotlib python jobs/hshci_drawdown_compare.py
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT_PNG = REPO / "data" / "external" / "hshci_drawdown_compare.png"

# (date, 月收盘) — iFind 指数行情
PERIOD_A = [
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
]
PERIOD_B = [
    ("2025-08-01", 4132.88),  # 日频锚点（与看板相对表现一致）
    ("2025-08-29", 4325.82), ("2025-09-30", 4551.28), ("2025-10-31", 4048.32),
    ("2025-11-28", 4044.78), ("2025-12-31", 3661.52), ("2026-01-30", 3974.92),
    ("2026-02-27", 3889.51), ("2026-03-31", 3688.14), ("2026-04-30", 3730.51),
    ("2026-05-29", 3383.26), ("2026-06-01", 3357.89),  # 末点 日频
]

INK = "#1A1A1A"
GREY = "#8A8580"
CMSI_RED = "#C8102E"
ASOF = "2026-06-03"


def _series(rows):
    """→ (elapsed_months[list], rebased[list], pct_total, trough_pct)."""
    d0 = date.fromisoformat(rows[0][0])
    base = rows[0][1]
    xs, ys = [], []
    for ds, px in rows:
        dd = date.fromisoformat(ds)
        xs.append((dd - d0).days / 30.4375)
        ys.append(px / base * 100.0)
    pct_total = ys[-1] - 100.0
    trough_pct = min(ys) - 100.0
    return xs, ys, pct_total, trough_pct


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import rcParams

    rcParams["font.sans-serif"] = ["Arial Unicode MS"]
    rcParams["axes.unicode_minus"] = False

    ax_xs, a_ys, a_tot, a_tr = _series(PERIOD_A)
    bx_xs, b_ys, b_tot, b_tr = _series(PERIOD_B)

    fig, ax = plt.subplots(figsize=(10.2, 6.0), dpi=200)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    ax.axhline(100, color=INK, lw=1.0, ls=(0, (4, 4)), alpha=0.5, zorder=2)

    ax.plot(ax_xs, a_ys, color=GREY, lw=2.4, zorder=3,
            label=f"2021.7 – 2024.6（结构性熊市，{a_tot:+.0f}%）")
    ax.plot(bx_xs, b_ys, color=CMSI_RED, lw=3.0, zorder=4,
            label=f"2025.8 – 今（本轮，{b_tot:+.0f}%）")

    # endpoint markers + labels
    ax.scatter([ax_xs[-1]], [a_ys[-1]], color=GREY, s=36, zorder=5)
    ax.scatter([bx_xs[-1]], [b_ys[-1]], color=CMSI_RED, s=44, zorder=6)
    ax.annotate(f"{a_tot:+.1f}%", (ax_xs[-1], a_ys[-1]), textcoords="offset points",
                xytext=(8, -2), fontsize=11, fontweight="bold", color=GREY, va="center")
    ax.annotate(f"{b_tot:+.1f}%", (bx_xs[-1], b_ys[-1]), textcoords="offset points",
                xytext=(8, 0), fontsize=12, fontweight="bold", color=CMSI_RED, va="center")

    # same-elapsed-time read: where was A at B's current elapsed month?
    b_end = bx_xs[-1]
    import bisect
    j = bisect.bisect_left(ax_xs, b_end)
    if 0 < j < len(a_ys):
        a_at = a_ys[j]
        ax.scatter([ax_xs[j]], [a_at], facecolors="white", edgecolors=GREY, s=40, zorder=5, lw=1.6)
        ax.annotate(f"同期第 {b_end:.0f} 个月\n上轮已 {a_at-100:+.0f}%",
                    (ax_xs[j], a_at), textcoords="offset points", xytext=(6, -34),
                    fontsize=8.5, color=GREY)

    ax.set_title("恒生医疗保健指数：两轮下跌对比（各自起点 = 100）",
                 fontsize=15.5, fontweight="bold", pad=14, color=INK)
    ax.set_xlabel("距起点月数", fontsize=12)
    ax.set_ylabel("指数（起点 = 100）", fontsize=12)
    ax.legend(loc="upper right", fontsize=10.5, frameon=False)

    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(True, color="#ECECEC", lw=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.set_xlim(-1, max(ax_xs) + 3)
    ax.set_ylim(min(min(a_ys), min(b_ys)) - 6, max(max(a_ys), max(b_ys)) + 6)

    note = (f"上轮 35 个月 {a_tot:+.0f}%（谷底 {a_tr:+.0f}%）；本轮 {b_end:.0f} 个月 {b_tot:+.0f}%"
            f"（自 2025-09 波峰 4551 算 {3357.89/4551.28*100-100:+.0f}%）。"
            f"来源：iFind 指数月收盘，截至 {ASOF}。")
    fig.text(0.01, 0.012, note, fontsize=8, color=GREY)
    fig.subplots_adjust(left=0.085, right=0.965, top=0.91, bottom=0.13)
    fig.savefig(OUT_PNG, facecolor="white")
    plt.close(fig)

    print(f"[ok] {OUT_PNG}")
    print(f"  A 2021.7-2024.6: 100 → {a_ys[-1]:.1f}  ({a_tot:+.1f}%, 谷底 {a_tr:+.1f}%)")
    print(f"  B 2025.8-今    : 100 → {b_ys[-1]:.1f}  ({b_tot:+.1f}%, {b_end:.1f} 个月)")


if __name__ == "__main__":
    main()
