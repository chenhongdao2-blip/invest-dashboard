"""IPO 公司详情块 — 总账×阶梯（方案 2a），原生 <details>/<summary>。

HC Capital Markets 页每支港股医疗 IPO 一行:
  收起 = 总账行(信息含量摘要 + 涨幅徽章)
  展开 = 左档案卡(基本信息 + 对外授权大数 + 合作方图谱) + 右阶梯(管线阶段梯队 + BD 按年)

数据全部预构建、运行时零查询:
  row    = data/external/hk_hc_ipo_tracker.csv 一行(jobs/build_hk_ipo_tracker.py)
  detail = data/external/hk_ipo_pharma_detail.json 按 code 取(jobs/build_ipo_pharma_detail.py,
           PharmCube MCP 预构建)。Streamlit 进程无 MCP,只读 on-disk dict。

设计基准: 落地代码/11_ipo_detail_reference.html。所有颜色走 lib.theme token,无裸 hex、
无 emoji、无 box-shadow、border-radius ≤2px。状态类(caret 旋转/hover/open 态)在 theme._CSS
的 IPO_DETAIL_CSS 段。
"""
from __future__ import annotations

from html import escape as _esc

import streamlit as st

from lib import i18n, theme as T


# ── 数值/金额 helpers ──────────────────────────────────────────────────────
def _num(x) -> float | None:
    """CSV/JSON 值 → float,空/nan/None/"" 安全返回 None。"""
    if x is None:
        return None
    s = str(x).strip()
    if s in ("", "nan", "None", "NaN", "-"):
        return None
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def _fmt_deal_value(v_m: float | int | None) -> str:
    """PharmCube deal value(USD 百万) → $NNNM,或 $N.NNB(≥1000m)。空/≤0 → ""。"""
    v = _num(v_m)
    if v is None or v <= 0:
        return ""
    return f"${v / 1000:.2f}B" if v >= 1000 else f"${v:.0f}M"


def _fmt_deal_sum(total_m: float | int | None) -> str:
    """合计/按年小计(USD 百万) → $X.XXB / $NNNM。0/空 → ""。"""
    v = _num(total_m)
    if v is None or v <= 0:
        return ""
    return f"${v / 1000:.2f}B" if v >= 1000 else f"${v:.0f}M"


def _first_str(x) -> str:
    s = "" if x is None else str(x).strip()
    return "" if s in ("nan", "None", "NaN") else s


# ── 管线阶段梯队 ────────────────────────────────────────────────────────────
# 组序: 最前沿 → 最早。申报临床落在 I期 之后、临床前 之前。
_PHASE_ORDER = [
    "批准上市", "申请上市", "III期临床", "II期临床",
    "I/II期临床", "I期临床", "申报临床", "临床前",
]
_PHASE_RANK = {p: i for i, p in enumerate(_PHASE_ORDER)}
_LADDER_MAX = 8   # 入梯药物总上限(防恒瑞 532 条爆版)


def _phase_tile_style(phase: str) -> tuple[str, str, str]:
    """返回(bg, border_left_color, text_color) — 相位牌配色分档。
    申请上市及以上 = UP_TINT + UP_DEEP 肋 + UP_DEEP 字;III期 = PAPER_BAND + INK 肋;
    II期 = PAPER_DEEP + INK_3 肋;更早 = PAPER_DEEP + INK_4 肋。"""
    rank = _PHASE_RANK.get(phase, 99)
    if rank <= _PHASE_RANK["申请上市"]:          # 批准上市 / 申请上市
        return T.UP_TINT, T.UP_DEEP, T.UP_DEEP
    if rank == _PHASE_RANK["III期临床"]:
        return T.PAPER_BAND, T.INK, T.INK
    if rank == _PHASE_RANK["II期临床"]:
        return T.PAPER_DEEP, T.INK_3, T.INK_3
    return T.PAPER_DEEP, T.INK_4, T.INK_3


def _disease_short(disease: str) -> str:
    """适应症取前 2 个(逗号分隔)用「 · 」连接。"""
    parts = [p.strip() for p in str(disease).replace("，", ",").split(",") if p.strip()]
    return " · ".join(parts[:2])


# ── 主入口 ──────────────────────────────────────────────────────────────────
def render_ipo_detail(row: dict, detail: dict | None = None) -> None:
    """一支 IPO 的公司详情 <details>。一次 st.markdown(unsafe_allow_html=True)。

    Args:
        row: hk_hc_ipo_tracker.csv 一行(dict)。
        detail: hk_ipo_pharma_detail.json 按 code 取的 dict,或 None。
    """
    detail = detail or {}
    name_cn = _esc(_first_str(row.get("name_cn")) or "—")
    code = _esc(_first_str(row.get("code")))
    sub_sector = _esc(_first_str(row.get("sub_sector")))
    is_18a = _first_str(row.get("is_18a")).lower() in ("true", "1", "yes")
    is_susp = _first_str(row.get("suspended")).lower() in ("true", "1", "yes")
    no_offer = _first_str(row.get("no_offer")).lower() in ("true", "1", "yes")
    broke = _first_str(row.get("broke")).lower() in ("true", "1", "yes")

    pipeline = detail.get("pipeline", []) or []
    bd = detail.get("bd", []) or []
    pipeline_total = int(detail.get("pipeline_total", 0) or 0)
    bd_total = int(detail.get("bd_total", 0) or 0)
    has_archive = pipeline_total > 0 or bd_total > 0

    disclosed = [d for d in bd if _num(d.get("value_usd_m"))]
    disclosed_sum_m = sum(_num(d.get("value_usd_m")) for d in disclosed)

    summary = _summary_row(
        name_cn, code, sub_sector, is_18a, is_susp, no_offer, broke,
        row, pipeline_total, bd_total, disclosed, disclosed_sum_m, has_archive,
    )
    body = _detail_body(
        row, pipeline, bd, pipeline_total, bd_total,
        disclosed, disclosed_sum_m, is_18a, has_archive,
    )
    st.markdown(f"<details>{summary}{body}</details>", unsafe_allow_html=True)


def _summary_row(name_cn, code, sub_sector, is_18a, is_susp, no_offer, broke,
                 row, pipeline_total, bd_total, disclosed, disclosed_sum_m,
                 has_archive) -> str:
    mono = T.FONT_MONO
    # ② 名称 + code · sub_sector · 18A
    meta_bits = [b for b in (code, sub_sector, ("18A" if is_18a else "")) if b]
    name_html = (
        f'<span style="display:flex;align-items:baseline;gap:9px;">'
        f'<span style="font-size:15px;font-weight:700;color:{T.INK};">{name_cn}</span>'
        f'<span style="font-family:{mono};font-size:11px;color:{T.INK_3};">'
        f'{" · ".join(meta_bits)}</span></span>'
    )

    # ③ 情报摘要
    if has_archive:
        parts = [
            f'{i18n.t("capital.ipo.detail.pipeline")} '
            f'<b style="color:{T.INK};font-weight:700;">{pipeline_total}</b>',
            f'BD <b style="color:{T.INK};font-weight:700;">{bd_total}</b>',
        ]
        if disclosed:
            parts.append(
                f'{i18n.t("capital.ipo.detail.disclosed")} '
                f'<b style="color:{T.INK};font-weight:700;">'
                f'{_fmt_deal_sum(disclosed_sum_m)}</b>'
            )
        intel_html = (
            f'<span style="font-family:{mono};font-size:12px;color:{T.INK_3};'
            f'font-variant-numeric:tabular-nums;">{" · ".join(parts)}</span>'
        )
    else:
        intel_html = (
            f'<span style="font-family:{mono};font-size:12px;color:{T.INK_4};">'
            f'{i18n.t("capital.ipo.detail.no_archive")}</span>'
        )

    # ④ 涨幅徽章
    ret = _num(row.get("ret_pct"))
    up = ret is not None and ret >= 0
    ret_color = T.UP if up else T.DOWN
    ret_txt = f"{ret:+.1f}%" if ret is not None else "—"
    if no_offer:
        base = _first_str(row.get("ret_base")) or i18n.t("capital.ipo.detail.first_day")
        ret_txt = f"{_esc(base)} {ret_txt}"
    ret_html = (
        f'<span style="font-family:{mono};font-size:12.5px;font-weight:700;'
        f'color:{ret_color};font-variant-numeric:tabular-nums;">{ret_txt}</span>'
    )
    chips = []
    if broke:
        chips.append(
            f'<span style="font-family:{mono};font-size:10px;color:{T.DOWN_DEEP};'
            f'background:{T.DOWN_TINT};border:1px solid {T.DOWN};border-radius:2px;'
            f'padding:1px 6px;">{i18n.t("capital.ipo.detail.broke_chip")}</span>'
        )
    else:
        chips.append(
            f'<span style="font-family:{mono};font-size:10px;color:{T.UP_DEEP};'
            f'background:{T.UP_TINT};border:1px solid {T.UP};border-radius:2px;'
            f'padding:1px 6px;">{i18n.t("capital.ipo.detail.up_chip")}</span>'
        )
    if is_susp:
        chips.append(
            f'<span style="font-family:{mono};font-size:10px;color:{T.INK_3};'
            f'background:{T.PAPER_BAND};border:1px solid {T.INK_4};border-radius:2px;'
            f'padding:1px 6px;">{i18n.t("capital.ipo.detail.suspended_chip")}</span>'
        )
    badge_html = (
        f'<span style="display:flex;align-items:center;gap:8px;justify-content:flex-end;">'
        f'{ret_html}{"".join(chips)}</span>'
    )

    caret = (
        f'<span class="ipo-acc-caret"><svg width="10" height="10" viewBox="0 0 10 10">'
        f'<path d="M3 1.5 L7 5 L3 8.5" fill="none" stroke="{T.INK_3}" '
        f'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"></path>'
        f'</svg></span>'
    )
    return (
        f'<summary class="ipo-acc-sum" style="display:grid;'
        f'grid-template-columns:18px 300px 1fr auto;gap:14px;align-items:center;'
        f'padding:13px 14px;border-bottom:1px solid {T.PAPER_RULE};">'
        f'{caret}{name_html}{intel_html}{badge_html}</summary>'
    )


def _detail_body(row, pipeline, bd, pipeline_total, bd_total,
                 disclosed, disclosed_sum_m, is_18a, has_archive) -> str:
    left = _archive_card(row, bd, bd_total, disclosed, disclosed_sum_m, is_18a, has_archive)
    if not has_archive:
        # 零档案: 只渲左栏基本信息(通栏),右栏 + 授权大数卡不出现
        inner = (
            f'<div style="display:grid;grid-template-columns:1fr;gap:0;'
            f'border-left:1px solid {T.PAPER_RULE};">{left}</div>'
        )
    else:
        right = _ladder_and_bd(pipeline, bd, pipeline_total, bd_total)
        inner = (
            f'<div style="display:grid;grid-template-columns:320px 1fr;gap:0;'
            f'border-left:1px solid {T.PAPER_RULE};">{left}{right}</div>'
        )
    return (
        f'<div style="padding:0 0 0 17px;border-bottom:1px solid {T.PAPER_RULE};'
        f'background:{T.PAPER};">{inner}</div>'
    )


# ── 左栏: 档案卡 ────────────────────────────────────────────────────────────
def _kv(label: str, value_html: str) -> str:
    return (
        f'<div><div style="font-family:{T.FONT_MONO};font-size:10px;'
        f'letter-spacing:.1em;color:{T.INK_3};">{label}</div>'
        f'<div style="margin-top:3px;">{value_html}</div></div>'
    )


def _archive_card(row, bd, bd_total, disclosed, disclosed_sum_m,
                  is_18a, has_archive) -> str:
    mono = T.FONT_MONO
    border_r = f"border-right:1px solid {T.PAPER_EDGE};" if has_archive else ""
    kv_cells = []

    ipo_date = _first_str(row.get("ipo_date"))
    if ipo_date:
        kv_cells.append(_kv(
            i18n.t("capital.ipo.detail.listing_date"),
            f'<span style="font-family:{mono};font-size:14px;font-weight:600;'
            f'color:{T.INK};">{_esc(ipo_date)}</span>'))

    ret = _num(row.get("ret_pct"))
    if ret is not None:
        up = ret >= 0
        base = ""
        if _first_str(row.get("no_offer")).lower() in ("true", "1", "yes"):
            b = _first_str(row.get("ret_base")) or i18n.t("capital.ipo.detail.first_day")
            base = f'{_esc(b)} '
        kv_cells.append(_kv(
            i18n.t("capital.ipo.detail.ret_since"),
            f'<span style="font-family:{mono};font-size:14px;font-weight:700;'
            f'color:{T.UP if up else T.DOWN};font-variant-numeric:tabular-nums;">'
            f'{base}{ret:+.1f}%</span>'))

    offer = _num(row.get("offer_price_hkd"))
    close = _num(row.get("close"))
    if offer is not None and close is not None:
        kv_cells.append(_kv(
            i18n.t("capital.ipo.detail.offer_to_cur"),
            f'<span style="font-family:{mono};font-size:14px;font-weight:600;'
            f'color:{T.INK};font-variant-numeric:tabular-nums;">'
            f'{offer:.2f} → {close:.2f}</span>'))

    lmc = _num(row.get("listing_mktcap_yi"))
    cmc = _num(row.get("cur_mktcap_yi"))
    if lmc is not None and cmc is not None:
        kv_cells.append(_kv(
            i18n.t("capital.ipo.detail.val_to_mc"),
            f'<span style="font-family:{mono};font-size:14px;font-weight:600;'
            f'color:{T.INK};font-variant-numeric:tabular-nums;">'
            f'{lmc:.1f} → {cmc:.1f}亿</span>'))

    turn = _num(row.get("avg_turnover_usdm"))
    if turn is not None:
        kv_cells.append(_kv(
            i18n.t("capital.ipo.detail.avg_turnover"),
            f'<span style="font-family:{mono};font-size:14px;font-weight:600;'
            f'color:{T.INK};font-variant-numeric:tabular-nums;">${turn:.1f}M</span>'))

    sub_sector = _first_str(row.get("sub_sector"))
    if sub_sector:
        sec_txt = _esc(sub_sector) + (" · 18A" if is_18a else "")
        kv_cells.append(_kv(
            i18n.t("capital.ipo.detail.sector"),
            f'<span style="font-size:13px;font-weight:600;color:{T.INK};">{sec_txt}</span>'))

    founding = _num(row.get("founding_year"))
    if founding is not None:
        kv_cells.append(_kv(
            i18n.t("capital.ipo.detail.founded"),
            f'<span style="font-family:{mono};font-size:14px;font-weight:600;'
            f'color:{T.INK};">{int(founding)}</span>'))

    # 有档案 = 左栏 320px 内 2 列紧凑 KV(参考稿);零档案通栏 = 横向紧凑格,
    # 每格上限 220px,不随整行宽度均分拉伸(否则左右两列隔半屏空洞)。
    kv_grid = (
        "grid-template-columns:1fr 1fr;gap:12px 16px;" if has_archive
        else "grid-template-columns:repeat(auto-fit,minmax(150px,220px));gap:14px 48px;"
    )
    basic = (
        f'<div style="font-family:{mono};font-size:10px;letter-spacing:.1em;'
        f'color:{T.INK_3};">{i18n.t("capital.ipo.detail.basic")}</div>'
        f'<div style="display:grid;{kv_grid}'
        f'margin-top:10px;">{"".join(kv_cells)}</div>'
    )

    bd_card = _disclosed_bignum(bd, bd_total, disclosed, disclosed_sum_m) if bd_total > 0 else ""
    partners = _partner_graph(bd) if bd_total > 0 else ""
    footer = (
        f'<div style="font-family:{mono};font-size:10px;color:{T.INK_4};'
        f'margin-top:16px;">{i18n.t("capital.ipo.detail.footer")}</div>'
    )
    return (
        f'<div style="padding:20px 24px 22px;{border_r}">'
        f'{basic}{bd_card}{partners}{footer}</div>'
    )


def _disclosed_bignum(bd, bd_total, disclosed, disclosed_sum_m) -> str:
    mono = T.FONT_MONO
    ge1b = sum(1 for d in disclosed if (_num(d.get("value_usd_m")) or 0) >= 1000)
    if disclosed:
        big = _fmt_deal_sum(disclosed_sum_m)
        meta = i18n.t("capital.ipo.detail.ge_1b").format(n=bd_total, m=ge1b)
        # 分段条: 披露前 5 笔按金额,teal 深→浅
        top5 = sorted(disclosed, key=lambda d: -(_num(d.get("value_usd_m")) or 0))[:5]
        shades = [T.UP_DEEP, T.UP, T.UP, "#5a9aa1", "#a8c8cb"]
        bars = "".join(
            f'<span style="flex:{int(_num(d.get("value_usd_m")) or 0)};'
            f'background:{shades[min(i, 4)]};"></span>'
            for i, d in enumerate(top5)
        )
        bar_html = (
            f'<div style="margin-top:10px;height:6px;display:flex;gap:2px;">{bars}</div>'
        )
        legend_txt = " ｜ ".join(
            f'{_esc(_first_str(d.get("partner")) or "—")} '
            f'{(_num(d.get("value_usd_m")) or 0) / 1000:.2f}'
            for d in top5
        )
        legend_html = (
            f'<div style="font-family:{mono};font-size:10px;color:{T.INK_4};'
            f'margin-top:5px;">{legend_txt}</div>'
        )
    else:
        big = i18n.t("capital.ipo.detail.undisclosed_n").format(n=bd_total)
        meta = ""
        bar_html = ""
        legend_html = ""
    meta_html = (
        f'<div style="font-family:{mono};font-size:10.5px;color:{T.INK_3};'
        f'margin-top:7px;">{meta}</div>' if meta else ""
    )
    return (
        f'<div style="margin-top:18px;padding:14px 16px;background:rgba(255,255,255,0.55);'
        f'border:1px solid {T.PAPER_EDGE};">'
        f'<div style="font-family:{mono};font-size:10px;letter-spacing:.1em;'
        f'color:{T.INK_3};">{i18n.t("capital.ipo.detail.disclosed_total")}</div>'
        f'<div style="font-family:{mono};font-size:30px;font-weight:700;'
        f'letter-spacing:-0.02em;margin-top:5px;line-height:1;color:{T.INK};'
        f'font-variant-numeric:tabular-nums;">{big}</div>'
        f'{meta_html}{bar_html}{legend_html}</div>'
    )


def _partner_graph(bd) -> str:
    mono = T.FONT_MONO
    # 去重保序 + 计数
    counts: dict[str, int] = {}
    order: list[str] = []
    for d in bd:
        p = _first_str(d.get("partner"))
        if not p:
            continue
        if p not in counts:
            counts[p] = 0
            order.append(p)
        counts[p] += 1
    if not order:
        return ""
    chips = []
    for p in order[:8]:
        label = _esc(p) + (f" ×{counts[p]}" if counts[p] > 1 else "")
        chips.append(
            f'<span style="font-size:11px;font-weight:600;border:1px solid {T.PAPER_EDGE};'
            f'border-radius:2px;padding:2px 8px;background:rgba(255,255,255,0.5);'
            f'color:{T.INK};">{label}</span>'
        )
    return (
        f'<div style="margin-top:16px;">'
        f'<div style="font-family:{mono};font-size:10px;letter-spacing:.1em;'
        f'color:{T.INK_3};">{i18n.t("capital.ipo.detail.partners")}</div>'
        f'<div style="display:flex;flex-wrap:wrap;gap:5px;margin-top:8px;">'
        f'{"".join(chips)}</div></div>'
    )


# ── 右栏: 管线阶梯 + BD 按年 ────────────────────────────────────────────────
def _rib_head(title: str, meta: str, mt: str = "0") -> str:
    return (
        f'<div style="display:flex;align-items:baseline;gap:9px;margin-top:{mt};">'
        f'<span style="width:3px;height:13px;background:{T.CMSI_RED};'
        f'align-self:center;"></span>'
        f'<span style="font-size:14px;font-weight:700;color:{T.INK};">{title}</span>'
        f'<span style="font-family:{T.FONT_MONO};font-size:11px;color:{T.INK_3};">'
        f'{meta}</span></div>'
    )


def _ladder_and_bd(pipeline, bd, pipeline_total, bd_total) -> str:
    return (
        f'<div style="padding:20px 26px 22px;">'
        f'{_pipeline_ladder(pipeline, pipeline_total)}'
        f'{_bd_by_year(bd, bd_total)}</div>'
    )


def _pipeline_ladder(pipeline, pipeline_total) -> str:
    mono = T.FONT_MONO
    # 按 phase 分组
    groups: dict[str, list[dict]] = {}
    for d in pipeline:
        ph = _first_str(d.get("phase")) or _first_str(d.get("phase_cn")) or "临床前"
        groups.setdefault(ph, []).append(d)
    ordered = sorted(groups.items(), key=lambda kv: _PHASE_RANK.get(kv[0], 99))

    rows_html = []
    shown = 0
    for phase, drugs in ordered:
        if shown >= _LADDER_MAX:
            break
        take = drugs[: max(0, _LADDER_MAX - shown)]
        if not take:
            break
        shown += len(take)
        bg, bl, tc = _phase_tile_style(phase)
        tile = (
            f'<div style="display:flex;flex-direction:column;justify-content:center;'
            f'padding:10px 12px;background:{bg};border-left:3px solid {bl};">'
            f'<span style="font-family:{mono};font-size:11px;font-weight:700;'
            f'color:{tc};">{_esc(phase)}</span>'
            f'<span style="font-family:{mono};font-size:10px;color:{T.INK_3};'
            f'margin-top:2px;">{len(drugs)} 条</span></div>'
        )
        chips = []
        for d in take:
            name = _esc(_first_str(d.get("name")) or "—")
            target = _first_str(d.get("target"))
            tgt_txt = "—" if (not target or target.lower() == "not available") else _esc(target)
            dis = _disease_short(_first_str(d.get("disease")))
            dis_html = (
                f'<span style="font-size:11px;color:{T.INK_3};">{_esc(dis)}</span>'
                if dis else ""
            )
            chips.append(
                f'<span style="display:inline-flex;align-items:baseline;gap:7px;'
                f'border:1px solid {T.PAPER_EDGE};background:rgba(255,255,255,0.6);'
                f'padding:6px 12px;">'
                f'<span style="font-size:13px;font-weight:700;color:{T.INK};">{name}</span>'
                f'<span style="font-family:{mono};font-size:10.5px;color:{T.INK_3};">'
                f'{tgt_txt}</span>{dis_html}</span>'
            )
        chip_wrap = (
            f'<div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;'
            f'padding:8px 0;">{"".join(chips)}</div>'
        )
        rows_html.append(tile + chip_wrap)

    rest = pipeline_total - shown
    tail = (
        f'<div style="font-family:{mono};font-size:10.5px;color:{T.INK_4};'
        f'margin-top:6px;">'
        f'{i18n.t("capital.ipo.detail.rest_pipeline").format(n=rest)}</div>'
        if rest > 0 else ""
    )
    meta = i18n.t("capital.ipo.detail.pipeline_meta").format(n=pipeline_total, k=shown)
    grid = (
        f'<div style="display:grid;grid-template-columns:110px 1fr;gap:10px;'
        f'align-items:stretch;margin-top:12px;">{"".join(rows_html)}</div>'
    )
    return (
        f'{_rib_head(i18n.t("capital.ipo.detail.ladder"), meta)}'
        f'{grid}{tail}'
    )


def _bd_by_year(bd, bd_total) -> str:
    mono = T.FONT_MONO
    if not bd:
        return ""
    # 按年倒序分组
    years: dict[str, list[dict]] = {}
    for d in bd:
        y = _first_str(d.get("date"))[:4] or "—"
        years.setdefault(y, []).append(d)
    ordered = sorted(years.items(), key=lambda kv: kv[0], reverse=True)

    rows = []
    for i, (year, deals) in enumerate(ordered):
        disc = [d for d in deals if _num(d.get("value_usd_m"))]
        subtotal = sum(_num(d.get("value_usd_m")) for d in disc)
        if disc:
            cnt_txt = f'{len(deals)} 笔 · {_fmt_deal_sum(subtotal)}'
        else:
            cnt_txt = f'{len(deals)} 笔'
        chips = []
        for d in deals:
            partner = _esc(_first_str(d.get("partner")) or "—")
            asset = _esc(_first_str(d.get("asset")))
            val = _fmt_deal_value(d.get("value_usd_m"))
            asset_html = f' · {asset}' if asset else ""
            if val:
                chips.append(
                    f'<span style="font-size:11.5px;border:1px solid {T.PAPER_EDGE};'
                    f'background:rgba(255,255,255,0.55);padding:3px 9px;color:{T.INK};">'
                    f'<b>{partner}</b>{asset_html} · '
                    f'<span style="font-family:{mono};font-weight:700;'
                    f'font-variant-numeric:tabular-nums;">{val}</span></span>'
                )
            else:
                chips.append(
                    f'<span style="font-size:11.5px;border:1px dashed {T.PAPER_EDGE};'
                    f'padding:3px 9px;color:{T.INK_3};">'
                    f'<b style="color:{T.INK_2};">{partner}</b>{asset_html} · '
                    f'{i18n.t("capital.ipo.detail.undisclosed")}</span>'
                )
        border = T.PAPER_EDGE if i == len(ordered) - 1 else T.PAPER_RULE
        rows.append(
            f'<div style="display:grid;grid-template-columns:70px 110px 1fr;gap:14px;'
            f'padding:10px 2px;border-bottom:1px solid {border};align-items:start;">'
            f'<span style="font-family:{mono};font-size:13px;font-weight:700;'
            f'color:{T.INK};">{_esc(year)}</span>'
            f'<span style="font-family:{mono};font-size:11px;color:{T.INK_3};'
            f'padding-top:2px;font-variant-numeric:tabular-nums;">{cnt_txt}</span>'
            f'<span style="display:flex;flex-wrap:wrap;gap:6px;">{"".join(chips)}</span>'
            f'</div>'
        )
    meta = i18n.t("capital.ipo.detail.bd_meta").format(k=len(bd), n=bd_total)
    return (
        f'{_rib_head(i18n.t("capital.ipo.detail.bd_by_year"), meta, mt="22px")}'
        f'<div style="margin-top:10px;border-top:1px solid {T.PAPER_EDGE};">'
        f'{"".join(rows)}</div>'
    )
