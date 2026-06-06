"""相对轮动图 (RRG / Relative Rotation Graph) — 计算核 + 自包含 HTML 渲染.

WHAT — 把一篮子板块指数相对一个基准的「相对强弱 × 动量」投影到四象限坐标，
回答"这个板块的强是否已被资金定价、走到顺时针的哪一步"。源自公开的 JdK
RS-Ratio / RS-Momentum 框架 (Julius de Kempenaer)；本模块是其可复现实现。

定位 (周期 agent 研判)：RRG 是**正交的"内部时间维度"测量仪**，不是择时信号——
它描述「已发生的相对状态」(高置信事实)，不预测「方向」(无预测力)。页面文案与
两条护栏 (lib.regime 级别水印 / lib.crowding 拥挤度叠加) 共同防止被误用为择时器。

────────────────────────────────────────────────────────────────────────────
归一化口径 (LOCKED — 全站一致，改这里等于改坐标系，需同步 docstring)：
  bars     : 周频 (W-FRI 收盘)。RRG 是周频工具；中信"领先象限 8–9 周后超额转负"
             的回测亦为周级别。日频输入会被 resample 到 W-FRI (对已是周线的数据幂等)。
  RS       : 100 * close_sector / close_benchmark        (按周对齐)
  RS-Ratio : 100 + Z(RS, W_R)          横轴 — 强弱/左右侧。Z = 滚动 z-score(ddof=0)
  RS-Mom   : 100 + Z(ΔRS-Ratio, W_M)   纵轴 — 改善/转弱。Δ = 1 周差分
  动量加速度: Δ(RS-Mom) 的符号 + Z(Δ(RS-Mom), W_M)   (中信前瞻信号 parity)
  象限     : (RS-Ratio≷100, RS-Mom≷100) → Leading / Weakening / Lagging / Improving
             顺时针演进 Improving→Leading→Weakening→Lagging
  尾巴     : 最近 TAIL 周的 (RS-Ratio, RS-Mom) 轨迹点

默认参数 (v1, tunable)：W_R=20w, W_M=10w, TAIL=8w。
  WHY 20/10 而非中信式 26/13：v1 seed 仅 ~52 周历史 (iFind 周线单调用 ~80 行上限)。
  26 周 z-score 会吃掉一半样本、有效 RRG 史过短。20/10 在 52 周下留 ~30 周有效史、
  尾巴 8 周从容。待 v2 拉 ~2 年历史后可切 26/13 贴合中信口径。
  ⚠️ 实测教训 (docs/plans/2026-06-05-rrg-crowding-data-sources.md)：60 日窗口下
  医药生物 RS 明明在跌却被归一化噪声判成"Improving"——短窗象限翻转=噪声。足量
  历史 + 级别水印是对冲，不可省。
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass

import numpy as np
import pandas as pd

# ── 口径常量 (LOCKED) ────────────────────────────────────────────────────────
W_R_DEFAULT = 20          # RS-Ratio z-score 窗口 (周)
W_M_DEFAULT = 10          # RS-Momentum z-score 窗口 (周)
TAIL_DEFAULT = 8          # 尾巴周数

QUADRANTS = ("Leading", "Weakening", "Lagging", "Improving")
_QUAD_CN = {
    "Leading": "领先", "Weakening": "转弱", "Lagging": "滞后", "Improving": "改善",
}
_QUAD_DESC_CN = {
    "Leading": "强且改善", "Weakening": "强但转弱",
    "Lagging": "弱且转弱", "Improving": "弱但反弹",
}
_QUAD_DESC_EN = {
    "Leading": "strong & improving", "Weakening": "strong but fading",
    "Lagging": "weak & deteriorating", "Improving": "weak but recovering",
}
# 交互 tooltip 用的一句话「读法」(轮动到哪一步)
_QUAD_READ_CN = {
    "Leading": "顺时针强势段 — 留意是否过热见顶",
    "Weakening": "强势后段 — 仍强但动量在泄",
    "Lagging": "顺时针弱势段 — 又弱又在走弱",
    "Improving": "轮动早段 — 弱但在反弹，可能转强",
}
_QUAD_READ_EN = {
    "Leading": "clockwise strong leg — watch for overheating",
    "Weakening": "late-strong — still strong but fading",
    "Lagging": "clockwise weak leg — weak & deteriorating",
    "Improving": "early leg — weak but recovering",
}


@dataclass
class RRGPoint:
    """一个板块在 RRG 上的当前读数 + 轨迹尾巴。"""
    label: str
    rs_ratio: float
    rs_momentum: float
    accel: float              # Δ(RS-Mom) 原值；符号=加速/减速
    accel_z: float            # 归一化加速度 (前瞻信号)
    quadrant: str
    tail: list[tuple[pd.Timestamp, float, float]]   # [(date, rsr, rsm), ...] 旧→新
    n_valid: int              # 有效 RRG 周数 (诊断短窗噪声用)


# ── 内部工具 ────────────────────────────────────────────────────────────────

def _to_weekly(s: pd.Series) -> pd.Series:
    """resample 到 W-FRI 收盘。对已是周五周线的数据幂等。"""
    s = s.dropna().sort_index()
    if not isinstance(s.index, pd.DatetimeIndex):
        s.index = pd.to_datetime(s.index)
    return s.resample("W-FRI").last().dropna()


def _zscore(s: pd.Series, win: int) -> pd.Series:
    """滚动 z-score (population std, ddof=0 → 确定性)。窗口不足返回 NaN。"""
    mu = s.rolling(win).mean()
    sd = s.rolling(win).std(ddof=0)
    return (s - mu) / sd.replace(0.0, np.nan)


def quadrant_of(rs_ratio: float, rs_momentum: float) -> str:
    if rs_ratio >= 100 and rs_momentum >= 100:
        return "Leading"
    if rs_ratio >= 100 and rs_momentum < 100:
        return "Weakening"
    if rs_ratio < 100 and rs_momentum < 100:
        return "Lagging"
    return "Improving"


def quadrant_label(q: str, *, prefer_cn: bool) -> str:
    return f"{_QUAD_CN[q]}({_QUAD_DESC_CN[q]})" if prefer_cn else q


def equal_weight_composite(closes: pd.DataFrame, *, min_names: int = 3) -> pd.Series:
    """一篮成分股收盘 → 等权合成「板块指数」(个股下沉 RRG 的内生基准)。

    WHY 不是简单 rebase 取均值：成分股起止 ragged (晚上市的股若按自身首值再基化到
    100 会在中途插入一个跳变点，污染横截面均值)。改用**横截面平均日收益链式**——每个
    交易日 = 当日有数成分股的等权平均收益，再 cumprod 到 100 基点。新名只在它有连续两点
    后才贡献收益，天然容忍 ragged、无再基化跳变。

    closes  : wide df, index=date, columns=ticker (日频或周频均可，compute_rrg 内部会
              统一 resample 到 W-FRI)。
    返回单一 close 序列，可直接当 compute_rrg 的 benchmark；成分不足 min_names 返回空。
    """
    if closes is None or closes.empty or closes.shape[1] < min_names:
        return pd.Series(dtype=float)
    cl = closes.sort_index()
    avg_ret = cl.pct_change().mean(axis=1, skipna=True).dropna()
    if avg_ret.empty:
        return pd.Series(dtype=float)
    return 100.0 * (1.0 + avg_ret).cumprod()


def usd_convert(local: pd.Series, fx: pd.Series | None, *, freeze: bool = False) -> pd.Series:
    """本币板块指数 → USD 计价 (跨市场同框 / 护栏③ 用)。

    fx = 本币/USD 汇率 (yfinance CNY=X / HKD=X，即 1 USD 兑多少本币) → USD 值 = 本币 / fx。
    freeze=True → 汇率冻结在公共起点 fx₀，**剥离汇率变动**，只保留板块本币驱动的路径
    (护栏③：USD 面板含汇率 beta，冻结面板剥离之，二者位移 = 该板块的汇率 beta 贡献)。
    fx=None (美股，本就 USD) → 原样返回。

    FX 为日频、板块多为周频：把 fx 前向填充对齐到板块日期 (汇率连续，ffill 一两天无碍)，
    避免周五逢假日时 inner-join 丢整周。
    """
    s = local.dropna().sort_index()
    if fx is None:
        return s
    f = fx.dropna().sort_index()
    if s.empty or f.empty:
        return pd.Series(dtype=float)
    f_on_s = f.reindex(s.index.union(f.index)).ffill().reindex(s.index)
    df = pd.concat({"s": s, "f": f_on_s}, axis=1).dropna()
    if df.empty:
        return pd.Series(dtype=float)
    denom = float(df["f"].iloc[0]) if freeze else df["f"]
    return (df["s"] / denom).rename(None)


# ── 计算核 (纯 pandas/numpy — 无 streamlit / 无 db，可独立单测) ───────────────

def compute_rrg(
    sectors: dict[str, pd.Series],
    benchmark: pd.Series,
    *,
    w_r: int = W_R_DEFAULT,
    w_m: int = W_M_DEFAULT,
    tail: int = TAIL_DEFAULT,
) -> list[RRGPoint]:
    """把 {板块名: 收盘序列} + 基准序列 → 每板块的 RRG 读数 + 尾巴。

    输入序列可日频或周频 (内部统一 resample 到 W-FRI)。基准须覆盖板块日期范围。
    板块历史不足 (有效 RRG 周数 < tail) 仍返回，n_valid 标低让上层提示噪声风险。
    返回按 (quadrant 顺时针, rs_ratio desc) 确定性排序。
    """
    bench_w = _to_weekly(benchmark)
    out: list[RRGPoint] = []

    for label, raw in sectors.items():
        sec_w = _to_weekly(raw)
        # 对齐到两者公共周 (inner join — 容忍 ragged 起止，如中信通信少最新一周)
        df = pd.concat({"sec": sec_w, "bench": bench_w}, axis=1).dropna()
        if len(df) < w_r + 2:
            # 历史太短，仍输出一个低置信点 (用末值近似，n_valid=0)
            if df.empty:
                continue
            rs_last = float(df["sec"].iloc[-1] / df["bench"].iloc[-1] * 100)
            out.append(RRGPoint(label, 100.0, 100.0, 0.0, 0.0,
                                quadrant_of(100.0, 100.0),
                                [(df.index[-1], 100.0, 100.0)], 0))
            continue

        rs = df["sec"] / df["bench"] * 100.0
        rs_ratio = 100.0 + _zscore(rs, w_r)
        rs_mom = 100.0 + _zscore(rs_ratio.diff(), w_m)
        accel = rs_mom.diff()
        accel_z = _zscore(rs_mom.diff(), w_m)

        valid = pd.concat({"rsr": rs_ratio, "rsm": rs_mom}, axis=1).dropna()
        n_valid = len(valid)
        if n_valid == 0:
            continue

        last = valid.index[-1]
        rsr_last = float(valid["rsr"].iloc[-1])
        rsm_last = float(valid["rsm"].iloc[-1])
        tail_pts = [
            (idx, float(r.rsr), float(r.rsm))
            for idx, r in valid.tail(tail).iterrows()
        ]
        out.append(RRGPoint(
            label=label,
            rs_ratio=rsr_last,
            rs_momentum=rsm_last,
            accel=float(accel.loc[last]) if last in accel.index and not pd.isna(accel.loc[last]) else 0.0,
            accel_z=float(accel_z.loc[last]) if last in accel_z.index and not pd.isna(accel_z.loc[last]) else 0.0,
            quadrant=quadrant_of(rsr_last, rsm_last),
            tail=tail_pts,
            n_valid=n_valid,
        ))

    # 确定性排序：象限顺时针 → 同象限内 RS-Ratio 降序
    order = {q: i for i, q in enumerate(("Leading", "Weakening", "Lagging", "Improving"))}
    out.sort(key=lambda p: (order[p.quadrant], -p.rs_ratio))
    return out


# ── 渲染 (自包含 HTML+SVG，零 CDN；theme 懒加载保持上方计算核可独立单测) ────────

# 四象限底色 (faint tint) — Leading=teal好角 / Lagging=red坏角，守 teal↑/red↓ 锁定语义
_QUAD_TINT = {
    "Leading": "#e8f2f0",      # 接近 UP_TINT 更淡
    "Improving": "#eef0f6",    # 冷蓝 — 弱但反弹
    "Weakening": "#f6efe0",    # 暖琥珀 — 强但转弱
    "Lagging": "#f7ecec",      # 接近 DOWN_TINT 更淡
}


def _fmt_date(ts) -> str:
    try:
        return pd.Timestamp(ts).strftime("%Y-%m-%d")
    except Exception:
        return str(ts)


def render_rrg_html(
    points: list["RRGPoint"],
    meta: dict[str, dict],
    *,
    prefer_cn: bool,
    market_label: str,
    regime: dict | None = None,
    as_of: str | None = None,
    tail: int = TAIL_DEFAULT,
    point_colors: dict[str, str] | None = None,
    group_legend: list[tuple[str, str]] | None = None,
) -> tuple[str, int]:
    """四象限 RRG 自包含 HTML doc + iframe 高度。

    points : compute_rrg 输出
    meta   : {point.label: {"overheated": bool, "cz": float}}  护栏②叠加信息
    regime : lib.regime.regime_banner 输出 (护栏①水印)，None 则不显示
    point_colors : {label: hex}  按点显式着色 (跨市场=按市场)，缺省回落 RS 强弱 diverging
    group_legend : [(name, hex)]  色块图例 (如 A股/港股/美股)，None 不显示
    """
    from html import escape as _esc

    from lib import theme as t
    from lib.charts import _diverging_color

    if not points:
        doc = ("<!doctype html><html><head><meta charset='utf-8'></head><body>"
               f"<div style='font-family:sans-serif;padding:24px;color:#8a8580'>"
               f"{'暂无数据' if prefer_cn else 'No data'}</div></body></html>")
        return doc, 120

    # ── 自适应坐标范围 (值簇在 100 附近，按最大偏离对称取窗) ──
    devs = []
    for p in points:
        devs.append(abs(p.rs_ratio - 100)); devs.append(abs(p.rs_momentum - 100))
        for _, rsr, rsm in p.tail:
            devs.append(abs(rsr - 100)); devs.append(abs(rsm - 100))
    R = max(3.0, max(devs) * 1.18) if devs else 3.0

    # 画布几何 (viewBox 内固定像素)
    OX, OY, PW, PH = 78, 60, 520, 520
    cx = lambda v: OX + (v - (100 - R)) / (2 * R) * PW
    cy = lambda v: OY + PH - (v - (100 - R)) / (2 * R) * PH
    x100, y100 = cx(100), cy(100)

    svg = [f"<svg viewBox='0 0 720 {OY + PH + 34}' width='100%' role='img'>"]

    # 象限底色
    quad_rects = [
        ("Leading", x100, OY, OX + PW - x100, y100 - OY),
        ("Improving", OX, OY, x100 - OX, y100 - OY),
        ("Weakening", x100, y100, OX + PW - x100, OY + PH - y100),
        ("Lagging", OX, y100, x100 - OX, OY + PH - y100),
    ]
    for q, x, y, w, h in quad_rects:
        svg.append(f"<rect x='{x:.1f}' y='{y:.1f}' width='{w:.1f}' height='{h:.1f}' fill='{_QUAD_TINT[q]}'/>")

    # 象限角标 (中文大字 + 英文/描述小字)
    corner = {
        "Leading": (OX + PW - 10, OY + 22, "end"),
        "Improving": (OX + 10, OY + 22, "start"),
        "Weakening": (OX + PW - 10, OY + PH - 24, "end"),
        "Lagging": (OX + 10, OY + PH - 24, "start"),
    }
    for q, (tx, ty, anc) in corner.items():
        if prefer_cn:
            svg.append(
                f"<text x='{tx:.0f}' y='{ty:.0f}' text-anchor='{anc}' font-size='14' "
                f"font-weight='800' fill='{t.INK_3}' opacity='.85'>{_QUAD_CN[q]}"
                f"<tspan font-size='9' font-weight='600' fill='{t.INK_4}'> {q}</tspan></text>"
            )
            svg.append(
                f"<text x='{tx:.0f}' y='{ty+14:.0f}' text-anchor='{anc}' font-size='9.5' "
                f"fill='{t.INK_4}' opacity='.8'>{_QUAD_DESC_CN[q]}</text>"
            )
        else:
            svg.append(
                f"<text x='{tx:.0f}' y='{ty:.0f}' text-anchor='{anc}' font-size='13' "
                f"font-weight='800' fill='{t.INK_3}' opacity='.85'>{q}</text>"
            )

    # 网格框 + 十字中线 (100/100)
    svg.append(f"<rect x='{OX}' y='{OY}' width='{PW}' height='{PH}' fill='none' stroke='{t.PAPER_EDGE}' stroke-width='1'/>")
    svg.append(f"<line x1='{x100:.1f}' y1='{OY}' x2='{x100:.1f}' y2='{OY+PH}' stroke='{t.INK_3}' stroke-width='1.1' stroke-dasharray='4 3' opacity='.6'/>")
    svg.append(f"<line x1='{OX}' y1='{y100:.1f}' x2='{OX+PW}' y2='{y100:.1f}' stroke='{t.INK_3}' stroke-width='1.1' stroke-dasharray='4 3' opacity='.6'/>")

    # 坐标轴刻度值 (轴端 = 100∓R, 中心 = 100)
    def _tick(x, y, val, anc="middle"):
        svg.append(f"<text x='{x:.0f}' y='{y:.0f}' text-anchor='{anc}' font-size='9' "
                   f"font-family='{t.FONT_MONO}' fill='{t.INK_4}'>{val:.0f}</text>")
    _tick(x100, OY + PH + 13, 100.0)
    _tick(OX + 16, OY + PH + 13, 100 - R)
    _tick(OX + PW - 16, OY + PH + 13, 100 + R)
    _tick(OX - 7, y100 + 3, 100.0, "end")
    _tick(OX - 7, OY + PH - 4, 100 - R, "end")
    _tick(OX - 7, OY + 11, 100 + R, "end")

    # 轴标题
    xlab = "相对强弱 RS-Ratio →" if prefer_cn else "RS-Ratio (relative strength) →"
    ylab = "动量 RS-Momentum →" if prefer_cn else "RS-Momentum →"
    svg.append(f"<text x='{OX+PW/2:.0f}' y='{OY+PH+27:.0f}' text-anchor='middle' font-size='11' font-weight='700' fill='{t.INK_2}'>{_esc(xlab)}</text>")
    svg.append(f"<text x='16' y='{OY+PH/2:.0f}' text-anchor='middle' font-size='11' font-weight='700' fill='{t.INK_2}' transform='rotate(-90 16 {OY+PH/2:.0f})'>{_esc(ylab)}</text>")

    # 头点坐标 + 标签防重叠 (按 hy 贪心避让，撞了往下挪)
    heads = [[(cx(rsr), cy(rsm)) for _, rsr, rsm in p.tail] for p in points]
    label_y: dict[int, float] = {}
    _boxes: list[tuple[float, float]] = []
    for i in sorted(range(len(points)), key=lambda k: heads[k][-1][1]):
        hx, hy = heads[i][-1]
        ly = hy + 4
        for _ in range(10):
            if not any(abs(ly - by) < 12 and abs(hx - bx) < 78 for bx, by in _boxes):
                break
            ly += 12
        _boxes.append((hx, ly)); label_y[i] = ly

    # 每个板块整组包进 <g class='sec' data-i>，供内联 JS 做 hover 高亮/弹框/点击钉住
    sec_data: list[dict] = []
    for i, p in enumerate(points):
        info = meta.get(p.label, {})
        hot = bool(info.get("overheated"))
        cz = info.get("cz")
        hue = (point_colors or {}).get(p.label) or _diverging_color(p.rs_ratio - 100, cap=4.0)
        pts_xy = heads[i]
        cell: list[str] = []
        if len(pts_xy) >= 2:
            poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts_xy)
            cell.append(f"<polyline points='{poly}' fill='none' stroke='{hue}' stroke-width='1.6' opacity='.4'/>")
        n = len(pts_xy)
        for j, (x, y) in enumerate(pts_xy[:-1]):
            op = 0.16 + 0.5 * (j / max(1, n - 1)); rr = 1.7 + 1.5 * (j / max(1, n - 1))
            cell.append(f"<circle cx='{x:.1f}' cy='{y:.1f}' r='{rr:.1f}' fill='{hue}' opacity='{op:.2f}'/>")
        hx, hy = pts_xy[-1]
        ring = f"stroke='{t.DOWN}' stroke-width='2.6'" if hot else f"stroke='#fff' stroke-width='1.3'"
        cell.append(f"<circle cx='{hx:.1f}' cy='{hy:.1f}' r='6.5' fill='{hue}' {ring}/>")
        # 防重叠标签 + 引导线
        ly = label_y[i]
        if abs(ly - (hy + 4)) > 6:
            cell.append(f"<line x1='{hx+6:.1f}' y1='{hy:.1f}' x2='{hx+9:.1f}' y2='{ly-3:.1f}' "
                        f"stroke='{t.INK_4}' stroke-width='.7'/>")
        # 加速度字形 (▲加速/▼减速/·平) — 中信前瞻信号显式化
        if p.accel > 0.04:
            gly = f"<tspan fill='{t.UP_DEEP}' font-weight='700'>▲</tspan> "; acc_g, acc_cn, acc_en = "▲", "加速", "accel"
        elif p.accel < -0.04:
            gly = f"<tspan fill='{t.DOWN}' font-weight='700'>▼</tspan> "; acc_g, acc_cn, acc_en = "▼", "减速", "decel"
        else:
            gly = f"<tspan fill='{t.INK_4}'>·</tspan> "; acc_g, acc_cn, acc_en = "·", "平", "flat"
        tag = (f" <tspan fill='{t.DOWN}' font-weight='700'>[{'过热' if prefer_cn else 'HOT'}]</tspan>"
               if hot else "")
        czs = f" z{cz:+.1f}" if isinstance(cz, (int, float)) and cz == cz else ""
        noise = "" if p.n_valid >= tail else (" ⚠短史" if prefer_cn else " ⚠short")
        cell.append(
            f"<text x='{hx+11:.1f}' y='{ly:.1f}' font-size='11.5' font-weight='600' fill='{t.INK}'>"
            f"{gly}{_esc(p.label)}<tspan font-size='9' fill='{t.INK_3}' font-weight='500'>{_esc(czs)}{_esc(noise)}</tspan>{tag}</text>"
        )
        svg.append(f"<g class='sec' data-i='{i}'>{''.join(cell)}</g>")
        # 交互弹框卡片 (Python 端拼好 i18n+转义; JS 只 set innerHTML)。内容按 George 选定:
        # 板块名 + 象限&读法 + 动量加速/减速 (不放 RS 数值/拥挤z, 保持干净)
        hot_chip = ((" <span class='hot'>[过热]</span>" if prefer_cn else " <span class='hot'>[HOT]</span>")
                    if hot else "")
        brL, brR = ("（", "）") if prefer_cn else (" (", ")")
        mom_lbl = "动量：" if prefer_cn else "Momentum: "
        qline = f"{_QUAD_CN[p.quadrant]} {p.quadrant}" if prefer_cn else p.quadrant
        desc = _QUAD_DESC_CN[p.quadrant] if prefer_cn else _QUAD_DESC_EN[p.quadrant]
        read = _QUAD_READ_CN[p.quadrant] if prefer_cn else _QUAD_READ_EN[p.quadrant]
        acc_txt = f"{acc_g} {acc_cn if prefer_cn else acc_en}"
        card = (
            f"<div class='th'>{_esc(p.label)}{hot_chip}</div>"
            f"<div class='tq'>{_esc(qline)}{brL}{_esc(desc)}{brR}</div>"
            f"<div class='tr'>{_esc(read)}</div>"
            f"<div class='tm'>{mom_lbl}{_esc(acc_txt)}</div>"
        )
        sec_data.append({"html": card})

    svg.append("</svg>")

    # ── 外壳: 标题 / regime 水印 / 图 / 图例 / 第一性原则免责 ──
    title = ("板块轮动 · 相对轮动图 (RRG)" if prefer_cn else "Sector Rotation · RRG")
    reg_html = ""
    if regime:
        if regime.get("is_tactical"):
            reg_html = (f"<div class='wm tac'>{_esc(regime.get('watermark',''))}"
                        f"<span class='bk'>{_esc(regime.get('backdrop',''))}</span></div>")
        else:
            lvl = "战略级别" if prefer_cn else "Strategic regime"
            reg_html = (f"<div class='wm str'>🟢 {lvl}<span class='bk'>{_esc(regime.get('backdrop',''))}</span></div>")
    legend = (
        "<div class='key'>"
        f"<b>{'读法' if prefer_cn else 'How to read'}:</b> "
        f"{'顺时针演进 改善→领先→转弱→滞后 · 点=板块当前位置 · 尾巴=近' if prefer_cn else 'Clockwise: Improving→Leading→Weakening→Lagging · dot=now · tail=last '}{tail}{'周轨迹' if prefer_cn else 'w'} · "
        f"<span style='color:{t.DOWN};font-weight:700'>{'红圈[过热]=Leading且拥挤(护栏②)' if prefer_cn else 'red ring [HOT]=Leading & crowded'}</span>"
        f" · <span style='color:{t.INK_3}'>👆 {'悬停高亮 · 点击钉住' if prefer_cn else 'hover to highlight · click to pin'}</span>"
        "</div>"
    )
    group_html = ""
    if group_legend:
        chips = " ".join(
            f"<span class='chip'><i style='background:{c}'></i>{_esc(name)}</span>"
            for name, c in group_legend
        )
        group_html = f"<div class='grp'>{chips}</div>"
    disclaimer = (
        "<div class='disc'>⚠ "
        + ("<b>RRG 描述「已发生的相对状态」(高置信事实)，不预测「方向」(无预测力)。</b>"
           "它回答\"走到哪一步了\"，不回答\"下一步涨不涨\"。轮动信号须配合上层周期级别与基本面使用。"
           if prefer_cn else
           "<b>RRG describes the relative state that has already happened (high-confidence fact), "
           "not future direction (no predictive power).</b> It answers \"how far along,\" not \"up next?\"")
        + "</div>"
    )
    css = f"""
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{background:{t.PAPER};color:{t.INK};font-family:{t.FONT_STACK};padding:6px 4px 14px;-webkit-font-smoothing:antialiased}}
    .mh{{display:flex;align-items:baseline;gap:10px;border-bottom:2px solid {t.INK};padding-bottom:8px}}
    .mh h1{{font-size:18px;font-weight:700;letter-spacing:-.2px}}
    .mh .mkt{{font-size:11px;font-weight:700;color:#fff;background:{t.CMSI_RED};padding:2px 7px;border-radius:2px}}
    .mh .as{{margin-left:auto;font-family:{t.FONT_MONO};font-size:10.5px;color:{t.INK_3}}}
    .wm{{margin:9px 0 2px;padding:6px 11px;border-radius:0 3px 3px 0;font-size:11.5px;display:flex;gap:8px;align-items:center}}
    .wm.tac{{background:{t.DOWN_TINT};border-left:3px solid {t.DOWN};color:{t.DOWN_DEEP};font-weight:700}}
    .wm.str{{background:{t.UP_TINT};border-left:3px solid {t.UP};color:{t.UP_DEEP};font-weight:600}}
    .wm .bk{{margin-left:auto;font-weight:500;color:{t.INK_3};font-size:10.5px}}
    .key{{font-size:10.5px;color:{t.INK_2};margin:8px 2px 2px;line-height:1.5}}
    .grp{{display:flex;flex-wrap:wrap;gap:12px;margin:6px 2px 0;font-size:11px;color:{t.INK_2}}}
    .grp .chip{{display:inline-flex;align-items:center;gap:5px;font-weight:600}}
    .grp .chip i{{width:11px;height:11px;border-radius:50%;display:inline-block}}
    .disc{{margin-top:10px;border-top:1px solid {t.PAPER_RULE};padding-top:9px;font-size:10.5px;color:{t.INK_3};line-height:1.55}}
    .disc b{{color:{t.INK_2}}}
    g.sec{{transition:opacity .12s ease}}
    #rtip{{position:fixed;display:none;z-index:60;pointer-events:none;max-width:236px;
      background:#fff;border:1px solid {t.PAPER_RULE};border-left:3px solid {t.CMSI_RED};
      box-shadow:0 4px 16px rgba(0,0,0,.14);border-radius:3px;padding:8px 11px;
      font-size:11px;line-height:1.5;color:{t.INK}}}
    #rtip .th{{font-weight:700;font-size:12.5px;margin-bottom:2px}}
    #rtip .th .hot{{color:{t.DOWN};font-weight:700;font-size:10px}}
    #rtip .tq{{font-weight:600;color:{t.INK_2}}}
    #rtip .tr{{color:{t.INK_3};font-size:10.5px;margin:2px 0 0}}
    #rtip .tm{{color:{t.INK_2};margin-top:3px}}
    """
    # ── 交互层 (内联 vanilla JS, 零 CDN/自包含 → 国内安全; 与数据表的 click-sort 同机制) ──
    # hover: 高亮该板块整组(其余淡化) + 弹样式化卡片; click: 钉住; 点别处取消。
    sec_js = json.dumps(sec_data, ensure_ascii=False)
    tip_div = "<div id='rtip'></div>"
    script = (
        "<script>(function(){"
        f"var S={sec_js};"
        "var tip=document.getElementById('rtip');"
        "var gs=document.querySelectorAll('g.sec');var pin=null;"
        "function pos(x,y){var w=tip.offsetWidth,h=tip.offsetHeight;var nx=x+14,ny=y+14;"
        "if(nx+w>window.innerWidth-6)nx=x-w-14;if(nx<4)nx=4;"
        "if(ny+h>window.innerHeight-6)ny=y-h-14;if(ny<4)ny=4;"
        "tip.style.left=nx+'px';tip.style.top=ny+'px';}"
        "function show(i,x,y){tip.innerHTML=S[i].html;tip.style.display='block';pos(x,y);}"
        "function hi(i){for(var k=0;k<gs.length;k++){gs[k].style.opacity=(gs[k].getAttribute('data-i')===i)?'1':'0.1';}}"
        "function clr(){for(var k=0;k<gs.length;k++){gs[k].style.opacity='1';}tip.style.display='none';}"
        "for(var k=0;k<gs.length;k++){(function(g){var i=g.getAttribute('data-i');g.style.cursor='pointer';"
        "g.addEventListener('mouseenter',function(e){if(pin===null){hi(i);show(i,e.clientX,e.clientY);}});"
        "g.addEventListener('mousemove',function(e){if(pin===null)pos(e.clientX,e.clientY);});"
        "g.addEventListener('mouseleave',function(){if(pin===null)clr();});"
        "g.addEventListener('click',function(e){e.stopPropagation();"
        "if(pin===i){pin=null;clr();}else{pin=i;hi(i);show(i,e.clientX,e.clientY);}});"
        "})(gs[k]);}"
        "document.addEventListener('click',function(){if(pin!==null){pin=null;clr();}});"
        "})();</script>"
    )
    body = (
        f"<header class='mh'><h1>{title}</h1>"
        f"<span class='mkt'>{_esc(market_label)}</span>"
        f"<span class='as'>{('截至 ' if prefer_cn else 'as of ') + _esc(as_of) if as_of else ''}</span></header>"
        f"{reg_html}{legend}{group_html}{''.join(svg)}{disclaimer}{tip_div}"
    )
    doc = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<style>{css}</style></head><body>{body}{script}</body></html>"
    )
    height = OY + PH + 34 + 150          # svg viewBox + header/regime/legend/disclaimer
    if group_legend:
        height += 26                     # market color legend row
    return doc, int(height)
