"""个股热力图 v2 — Ranked Bento Grid (replaces the v1 go.Treemap).

WHY a bento grid, not a treemap (design provenance: docs/prototypes/heatmap_v2.html,
4-way /cccg review 2026-06-01):
  v1 encoded tile AREA = |return|, which let one outlier (OCS -23.4%) eat the canvas
  and crushed every other name into illegible sub-1% slivers. v2 DECOUPLES the channels:
    - COLOR  = signed return (diverging teal-up / red-down, neutral cream, sat cap ±12%)
               — reuses charts._diverging_color EXACTLY (project-LOCKED: teal up / red down).
    - SIZE   = a uniform cell. Tile size means NOTHING; the slot COUNT per sub-sector
               (allocated by rank) is what encodes "where the action is".

ALLOCATION (per domain, ranked independently so a hot AI day never starves Healthcare):
  1. Rank sub-sectors by MEDIAN member return over the window (outlier-robust; mean would
     let two JP names spike pharma above its 4-of-7-red reality). Tie-break: %-up desc,
     valid count desc, sector id asc — deterministic, reproducible across refreshes.
  2. Slots = min(SLOT_SCHEDULE[rank], valid_member_count). Best book ~15 tiles, laggards 3-5.
  3. Within a sub-sector ("anchored movers"): force-include the top `min(3, slots//4)`
     members by market cap (bellwethers stay visible session-to-session), then fill the
     rest by descending |return| (the movers). Display sorted by signed return desc
     (greens lead, reds trail) so each lane reads like a thermometer.
     NB the anchor count keys off SHOWN slots (slots//4), NOT raw member count — this
     resolves the prototype's doc/impl mismatch flagged by Codex in the /cccg review.

COLOR CONVENTION (George's call, /cccg BLOCKER from GLM): the whole dashboard is LOCKED
to teal-up / red-down (港美股惯例). A-share readers trained on 红涨绿跌 can misread, so the
board carries a bold convention banner instead of flipping (flipping one chart would break
site-wide consistency + the locked invariant).

Rendered as a self-contained HTML doc inside an iframe via st.iframe — the same pattern
ui.render_html_table uses (st.markdown strips <script>; st.dataframe is a dark canvas).
Window/domain toggles live in Streamlit (st.segmented_control re-runs Python), so the
iframe is pure server-rendered HTML with ZERO client JS and ZERO CDN (China-network safe).
"""
from __future__ import annotations

from html import escape as _esc

import pandas as pd

from lib import db, theme
from lib.charts import _diverging_color

# Slot budget by sub-sector rank (rank 0 = hottest). Length 13 covers HC(7)+AI(6).
# Monotone non-increasing: best book ~15 tiles, cold books 3.
SLOT_SCHEDULE = [15, 12, 10, 8, 7, 6, 5, 5, 4, 4, 3, 3, 3]

# Saturation + (former) size cap, in ±%. Mirrors charts._diverging_color default.
CAP = 12.0

WIN_TO_COL = {"1D": "1d_%", "5D": "5d_%", "1M": "1m_%"}

# Defensive mcap column resolution (snapshot schema name varies).
_MCAP_CANDIDATES = (
    "market_cap_usd", "mcap_usd", "marketcap_usd",
    "market_cap", "marketcap", "mktcap_usd", "mktcap",
)

# Sub-sector display names (raw id -> cn / en). Mirrors i18n._SECTOR_*; inlined here so
# this module stays import-light and the iframe doc is fully self-contained.
_SECTOR_CN = {
    "biotech": "生物科技", "pharma": "制药", "medtech": "医疗器械",
    "cxo": "CXO与生命科学", "hc_ai": "医疗+AI", "hospital_care": "医院服务",
    "managed_care": "管理式医疗",
    "ai_equip": "半导体设备材料", "ai_chip": "芯片设计", "ai_memory": "存储芯片",
    "ai_foundry": "代工封测", "ai_interconnect": "光互联/PCB", "ai_server": "服务器/温控/电源",
    "etf_broad": "广基医疗", "etf_biotech": "生物科技", "etf_pharma": "制药",
    "etf_devices": "医疗器械", "etf_providers": "医疗服务", "etf_genomics": "基因/主题",
}
_SECTOR_EN = {
    "biotech": "Biotech", "pharma": "Pharma", "medtech": "MedTech",
    "cxo": "CXO & Life Sci", "hc_ai": "Healthcare AI", "hospital_care": "Hospital Care",
    "managed_care": "Managed Care",
    "ai_equip": "Semi Equip & Materials", "ai_chip": "Chip Design", "ai_memory": "Memory",
    "ai_foundry": "Foundry & OSAT", "ai_interconnect": "Interconnect", "ai_server": "Server/Power",
    "etf_broad": "Broad HC", "etf_biotech": "Biotech", "etf_pharma": "Pharma",
    "etf_devices": "MedDevices", "etf_providers": "Providers", "etf_genomics": "Genomics",
}
_DOMAIN_CN = {"healthcare": "医疗", "ai": "AI", "etf": "ETF"}
_DOMAIN_EN = {"healthcare": "HEALTHCARE", "ai": "AI", "etf": "ETF"}


# ── data layer ────────────────────────────────────────────────────────────

def _mcap_col(mult: pd.DataFrame) -> str:
    for c in _MCAP_CANDIDATES:
        if not mult.empty and c in mult.columns:
            return c
    return ""


def _domain_sectors(domain_id: str) -> list[str]:
    df = db.query(
        "SELECT DISTINCT sector FROM universe_member "
        "WHERE domain = ? AND sector != '_coverage' ORDER BY sector",
        (domain_id,),
    )
    return df["sector"].tolist() if not df.empty else []


_ALL_KEY = "__all__"


def build_domain_bento(domain_id: str, window_col: str, prefer_cn: bool, *,
                       single_block: bool = False, single_cn: str | None = None,
                       single_en: str | None = None) -> dict | None:
    """Assemble one domain's ranked-bento payload, or None if the domain has no data.

    Returns: {id, cn, en, median, n_total, sectors: [block, ...]} where each block is
    {id, cn, en, median, pct_up, n_valid, n_members, n_shown, rank, tiles:[{tk,ret,mcap,name}]}
    sorted by rank (hottest first). Sectors with zero valid returns are dropped.

    single_block=True collapses ALL of the domain's members into ONE basket (one block)
    instead of per-sub-sector blocks — "one industry, one basket" (e.g. the ETF column,
    where the 6 HC sub-sectors are all 医药 and a single basket reads cleaner). The block
    label falls back to single_cn/single_en (else the domain label). Default False leaves
    the stock heatmaps' per-sub-sector grouping unchanged.
    """
    sectors = _domain_sectors(domain_id)
    if not sectors:
        return None

    # First-wins sector assignment (a ticker in two sectors is counted once).
    # single_block routes every member into one synthetic basket key.
    sector_of: dict[str, str] = {}
    members_count: dict[str, int] = {}
    for sec in sectors:
        m = db.sector_tickers(domain_id, sec)
        if m.empty:
            continue
        tgt = _ALL_KEY if single_block else sec
        cnt = 0
        for t in m["ticker"].tolist():
            if t not in sector_of:
                sector_of[t] = tgt
                cnt += 1
        members_count[tgt] = members_count.get(tgt, 0) + cnt
    tickers = tuple(sector_of.keys())
    if not tickers:
        return None

    closes = db.get_close_series_usd(tickers)
    rets = db.compute_returns(closes)
    if rets.empty or window_col not in rets.columns:
        return None
    mult = db.latest_multiples(tickers)
    mc = _mcap_col(mult)
    names = db.ticker_to_name(prefer_cn=prefer_cn)

    ret_s = pd.to_numeric(rets[window_col], errors="coerce")
    mcap_s = pd.to_numeric(mult[mc], errors="coerce") if mc else pd.Series(dtype=float)

    # Per-ticker record (valid = has a return).
    recs: dict[str, list[dict]] = {}
    all_valid_rets: list[float] = []
    for t, sec in sector_of.items():
        r = ret_s.get(t)
        if r is None or pd.isna(r):
            continue
        m = mcap_s.get(t) if not mcap_s.empty else None
        recs.setdefault(sec, []).append({
            "tk": t,
            "ret": float(r),
            "mcap": (None if (m is None or pd.isna(m)) else float(m)),
            "name": names.get(t, t),
        })
        all_valid_rets.append(float(r))

    if not recs:
        return None

    # Rank sub-sectors by median return (tie-break: %up desc, count desc, id asc).
    ranked = []
    for sec, items in recs.items():
        vals = [x["ret"] for x in items]
        med = float(pd.Series(vals).median())
        pct_up = sum(1 for v in vals if v > 0) / len(vals)
        ranked.append((sec, med, pct_up, len(vals), items))
    ranked.sort(key=lambda r: (-r[1], -r[2], -r[3], r[0]))

    blocks = []
    for rank, (sec, med, pct_up, n_valid, items) in enumerate(ranked):
        # single basket shows every member (no per-rank slot cap).
        slots = n_valid if single_block else min(
            SLOT_SCHEDULE[rank] if rank < len(SLOT_SCHEDULE) else SLOT_SCHEDULE[-1], n_valid)
        tiles = _pick_tiles(items, slots)
        is_all = sec == _ALL_KEY
        blocks.append({
            "id": sec,
            "cn": (single_cn or _DOMAIN_CN.get(domain_id, domain_id)) if is_all else _SECTOR_CN.get(sec, sec),
            "en": (single_en or _DOMAIN_EN.get(domain_id, domain_id.upper())) if is_all else _SECTOR_EN.get(sec, sec),
            "median": med,
            "pct_up": pct_up,
            "n_valid": n_valid,
            "n_members": members_count.get(sec, n_valid),
            "n_shown": len(tiles),
            "rank": rank + 1,
            "tiles": tiles,
        })

    return {
        "id": domain_id,
        "cn": _DOMAIN_CN.get(domain_id, domain_id),
        "en": _DOMAIN_EN.get(domain_id, domain_id.upper()),
        "median": float(pd.Series(all_valid_rets).median()) if all_valid_rets else None,
        "n_total": len(all_valid_rets),
        "sectors": blocks,
    }


def _pick_tiles(items: list[dict], slots: int) -> list[dict]:
    """Anchored-movers selection: force-include top min(3, slots//4) by mcap, fill the
    rest by descending |return|, then return sorted by signed return desc."""
    if slots <= 0 or not items:
        return []
    n_anchor = min(3, slots // 4)
    chosen: dict[str, dict] = {}
    if n_anchor > 0:
        with_mcap = [x for x in items if x["mcap"] is not None and x["mcap"] > 0]
        with_mcap.sort(key=lambda x: x["mcap"], reverse=True)
        for x in with_mcap[:n_anchor]:
            x["anchor"] = True
            chosen[x["tk"]] = x
    # Fill remaining by |return| desc.
    movers = sorted((x for x in items if x["tk"] not in chosen),
                    key=lambda x: abs(x["ret"]), reverse=True)
    for x in movers:
        if len(chosen) >= slots:
            break
        x.setdefault("anchor", False)
        chosen[x["tk"]] = x
    return sorted(chosen.values(), key=lambda x: x["ret"], reverse=True)


# ── render layer ──────────────────────────────────────────────────────────

def _fmt_pct(v) -> str:
    return "—" if v is None or pd.isna(v) else f"{float(v):+.1f}%"


def _fmt_mcap(v) -> str:
    if v is None or pd.isna(v):
        return "—"
    v = float(v)
    if v >= 1e12:
        return f"${v / 1e12:.1f}T"
    if v >= 1e9:
        return f"${v / 1e9:.1f}B"
    if v >= 1e6:
        return f"${v / 1e6:.1f}M"
    return f"${v:,.0f}"


def _text_on(pct: float) -> str:
    """Cream text on deep tiles (sat ≥ 0.55 ≈ |ret| ≥ 6.6%), else ink — matches prototype."""
    if pct is None or pd.isna(pct):
        return theme.INK
    return theme.PAPER if min(abs(float(pct)) / CAP, 1.0) >= 0.55 else theme.INK


def _short_tk(tk: str) -> tuple[str, str]:
    """Return (display, css-size-class). Keep semantic suffix (.KS/.HK) — shrink, never
    ellipsis (Gemini /cccg note). Class drives a smaller font for long tickers."""
    if len(tk) >= 9:
        return tk, "tk-xs"
    if len(tk) >= 7:
        return tk, "tk-sm"
    return tk, ""


def _bento_css() -> str:
    t = theme
    return f"""
    :root {{ color-scheme: light; }}
    * {{ box-sizing:border-box; margin:0; padding:0; }}
    html,body {{ background:{t.PAPER}; color:{t.INK}; font-family:{t.FONT_STACK};
      -webkit-font-smoothing:antialiased; font-feature-settings:'tnum','ss01'; }}
    body {{ padding:4px 2px 14px; }}

    .masthead {{ display:flex; justify-content:space-between; align-items:flex-start;
      gap:20px; flex-wrap:wrap; border-bottom:2px solid {t.INK}; padding-bottom:10px; }}
    .mast-left h1 {{ font-size:19px; font-weight:700; letter-spacing:-.2px; line-height:1.1; }}
    .mast-left h1 .en {{ font-size:13px; font-weight:600; color:{t.INK_2}; margin-left:7px; }}
    .mast-left .cmsi-tag {{ display:inline-block; font-size:9px; font-weight:700; color:#fff;
      background:{t.CMSI_RED}; padding:2px 6px; border-radius:2px; letter-spacing:.6px;
      vertical-align:middle; margin-left:6px; }}
    .mast-left .sub {{ font-size:11px; color:{t.INK_3}; margin-top:4px; }}

    .legend {{ min-width:250px; }}
    .legend .lg-title {{ font-size:10px; font-weight:600; color:{t.INK_2}; margin-bottom:4px; text-align:right; }}
    .lg-bar-wrap {{ display:flex; align-items:center; gap:6px; justify-content:flex-end; }}
    .lg-end {{ font-size:11px; font-weight:700; white-space:nowrap; }}
    .lg-bar {{ width:190px; height:13px; border:1px solid {t.PAPER_EDGE}; border-radius:2px;
      background:linear-gradient(to right, {t.DOWN} 0%, {t.PAPER_BAND} 50%, {t.UP} 100%); }}
    .lg-ticks {{ display:flex; justify-content:space-between; width:190px; margin:3px 0 0 auto;
      font-family:{t.FONT_MONO}; font-size:9px; font-weight:600; color:{t.INK_3}; }}

    /* color-convention banner — George's /cccg decision (港美股惯例, A股相反) */
    .conv {{ display:flex; align-items:center; gap:8px; margin:9px 0 2px; padding:6px 11px;
      background:{t.PAPER_DEEP}; border-left:3px solid {t.CMSI_RED}; border-radius:0 3px 3px 0;
      font-size:11.5px; color:{t.INK_2}; }}
    .conv b {{ font-weight:700; }}
    .conv .up {{ color:{t.UP_DEEP}; font-weight:700; }}
    .conv .dn {{ color:{t.DOWN_DEEP}; font-weight:700; }}
    .conv .sz {{ color:{t.INK_3}; margin-left:auto; font-size:10.5px; }}

    .domain {{ margin-top:16px; }}
    .domain-head {{ display:flex; align-items:baseline; gap:11px; background:{t.PAPER_DEEP};
      border-left:3px solid {t.CMSI_RED}; padding:8px 13px; margin-bottom:9px; border-radius:0 3px 3px 0; }}
    .domain-head .dh-title {{ font-size:16px; font-weight:700; color:{t.INK}; letter-spacing:-.2px; }}
    .domain-head .dh-en {{ font-size:10px; font-weight:600; color:{t.INK_3}; letter-spacing:1px; text-transform:uppercase; }}
    .domain-head .dh-agg {{ margin-left:auto; font-family:{t.FONT_MONO}; font-size:11px; font-weight:700; color:{t.INK_2}; }}
    .domain-head .ill {{ font-family:{t.FONT_STACK}; font-size:9px; font-weight:700; color:{t.CMSI_RED};
      background:{t.CMSI_RED_TINT}; padding:1px 5px; border-radius:2px; margin-left:6px; }}

    .block {{ display:flex; gap:12px; margin-bottom:9px; align-items:stretch; }}
    .block-head {{ flex:0 0 168px; background:{t.PAPER_DEEP}; border:1px solid {t.PAPER_RULE};
      border-radius:4px; padding:8px 11px; display:flex; flex-direction:column; justify-content:center; gap:2px; }}
    .block-head .bh-cn {{ font-size:13.5px; font-weight:700; color:{t.INK}; line-height:1.15; }}
    .block-head .bh-en {{ font-size:10px; font-weight:500; color:{t.INK_3}; }}
    .badge {{ display:inline-flex; align-items:center; gap:5px; margin-top:5px; padding:2px 8px;
      border-radius:11px; border:1px solid {t.PAPER_EDGE}; align-self:flex-start; }}
    .badge .arr {{ font-size:11px; font-weight:700; line-height:1; }}
    .badge .b-pct {{ font-family:{t.FONT_MONO}; font-size:12.5px; font-weight:700; }}
    .badge .b-ctx {{ font-size:9.5px; color:{t.INK_3}; font-weight:600; white-space:nowrap; }}

    .lane {{ flex:1; display:flex; flex-wrap:wrap; gap:4px; align-content:flex-start;
      background:{t.PAPER_BAND}; border-radius:4px; padding:5px; border:1px solid {t.PAPER_RULE}; }}
    .tile {{ flex:0 0 auto; width:70px; height:44px; border-radius:3px; border:1px solid {t.PAPER};
      display:flex; flex-direction:column; justify-content:center; align-items:center; gap:1px;
      overflow:hidden; }}
    .tile.flat {{ border:1px solid {t.PAPER_EDGE}; }}        /* 0% tile keeps physicality (Gemini) */
    .tile.anchor {{ box-shadow:inset 0 2px 0 {t.CMSI_RED}; }} /* bellwether marker (Gemini) */
    .tile .t-tk {{ font-size:12.5px; font-weight:700; line-height:1; letter-spacing:-.2px; }}
    .tile .t-tk.tk-sm {{ font-size:11px; }}
    .tile .t-tk.tk-xs {{ font-size:9.5px; }}
    .tile .t-pct {{ font-family:{t.FONT_MONO}; font-size:11.5px; font-weight:700; line-height:1.05; }}

    .footnote {{ margin-top:18px; border-top:1px solid {t.PAPER_RULE}; padding-top:10px;
      font-size:10.5px; color:{t.INK_3}; line-height:1.55; }}
    .footnote b {{ color:{t.INK_2}; }}
    .footnote code {{ font-family:{t.FONT_MONO}; font-size:9.5px; background:{t.PAPER_DEEP};
      padding:1px 4px; border-radius:2px; }}

    @media (max-width:680px) {{ .block-head {{ flex:0 0 120px; }} .tile {{ width:62px; }} }}
    """


def _render_block(b: dict, cn: bool) -> str:
    badge_color = _diverging_color(b["median"], cap=CAP)
    arr = "▲" if b["median"] >= 0 else "▼"
    arr_color = theme.UP_DEEP if b["median"] >= 0 else theme.DOWN_DEEP
    more = ""
    if b["n_shown"] < b["n_members"]:
        more = f" · {b['n_members'] - b['n_shown']}+"
    seat = "席" if cn else ""
    badge = (
        f'<span class="badge" style="background:{badge_color}">'
        f'<span class="arr" style="color:{arr_color}">{arr}</span>'
        f'<span class="b-pct" style="color:{_text_on(b["median"])}">{_fmt_pct(b["median"])}</span>'
        f'<span class="b-ctx">#{b["rank"]} · {b["n_shown"]}/{b["n_members"]}{seat}{more}</span>'
        f'</span>'
    )
    head = (
        f'<div class="block-head">'
        f'<span class="bh-cn">{_esc(b["cn"] if cn else b["en"])}</span>'
        f'{badge}</div>'
    )
    tiles = []
    for x in b["tiles"]:
        ret = x["ret"]
        fill = _diverging_color(ret, cap=CAP)
        txt = _text_on(ret)
        disp, szcls = _short_tk(x["tk"])
        cls = "tile"
        if abs(ret) < 0.4:
            cls += " flat"
        if x.get("anchor"):
            cls += " anchor"
        title = f'{_esc(str(x["name"]))} ({_esc(x["tk"])}) · {_fmt_pct(ret)} · mcap {_fmt_mcap(x["mcap"])}'
        tiles.append(
            f'<div class="{cls}" style="background:{fill}" title="{title}">'
            f'<span class="t-tk {szcls}" style="color:{txt}">{_esc(disp)}</span>'
            f'<span class="t-pct" style="color:{txt}">{_fmt_pct(ret)}</span></div>'
        )
    lane = f'<div class="lane">{"".join(tiles)}</div>'
    return f'<div class="block">{head}{lane}</div>'


def _render_domain(d: dict, cn: bool) -> str:
    agg = _fmt_pct(d["median"]) if d["median"] is not None else "—"
    ill_txt = "示意" if cn else "illustrative"
    ill = f'<span class="ill">{ill_txt}</span>' if d.get("illustrative") else ""
    med_lbl = "中位" if cn else "Median"
    head = (
        f'<div class="domain-head">'
        f'<span class="dh-title">{_esc(d["cn"] if cn else d["en"])}</span>'
        f'<span class="dh-agg">{med_lbl} {agg}{ill}</span></div>'
    )
    blocks = "".join(_render_block(b, cn) for b in d["sectors"])
    return f'<div class="domain">{head}{blocks}</div>'


def _estimate_height(domains: list[dict], *, tiles_per_row: int = 11) -> int:
    """Conservative iframe height so content is not clipped (slight overshoot is fine)."""
    import math
    h = 56 + 40 + 30  # masthead + convention banner + footnote-ish base
    for d in domains:
        h += 46  # domain head + margin
        for b in d["sectors"]:
            rows = max(1, math.ceil(b["n_shown"] / tiles_per_row))
            h += max(70, rows * 48 + 12) + 9  # block (header floor or lane) + gap
    return int(h)


def render_bento_html(domains: list[dict], *, prefer_cn: bool, window_label: str,
                      as_of: str | None) -> tuple[str, int]:
    """Build the self-contained HTML doc + an iframe height. `domains` is a list of
    build_domain_bento() payloads (already filtered to non-None)."""
    t = theme
    title = "个股热力图" if prefer_cn else "Single-Stock Heatmap"
    sub = ("子行业按中位涨跌排序分配席位 · 最热的子行业分到最多席位"
           if prefer_cn else
           "Slots by sub-sector median-return rank — hottest books get the most tiles")
    legend = (
        f'<div class="legend"><div class="lg-title">'
        f'{"颜色 = 涨跌方向与幅度" if prefer_cn else "Color = direction &amp; magnitude"}</div>'
        f'<div class="lg-bar-wrap"><span class="lg-end" style="color:{t.DOWN_DEEP}">{"跌" if prefer_cn else "Down"}</span>'
        f'<div class="lg-bar"></div><span class="lg-end" style="color:{t.UP_DEEP}">{"涨" if prefer_cn else "Up"}</span></div>'
        f'<div class="lg-ticks"><span>-12%</span><span>0</span><span>+12%</span></div></div>'
    )
    # George's /cccg decision: keep teal-up/red-down, add a loud convention banner.
    conv = (
        f'<div class="conv">⚠ <b>本图配色（港美股惯例）：</b>'
        f'<span class="up">青绿 = 涨</span> · <span class="dn">红 = 跌</span>'
        f'<b>（与 A 股红涨绿跌相反，请注意）</b>'
        f'<span class="sz">块大小 = 排名席位（非涨幅） · 顶部红条 = 子行业市值龙头（锚定常驻）</span></div>'
        if prefer_cn else
        f'<div class="conv">⚠ <b>Color (HK/US convention):</b> '
        f'<span class="up">teal = up</span> · <span class="dn">red = down</span>'
        f'<span class="sz">tile size = rank slot, not move size · red cap = sub-sector mcap bellwether (pinned)</span></div>'
    )
    boards = "".join(_render_domain(d, prefer_cn) for d in domains)
    foot = (
        f'<div class="footnote"><b>方法.</b> 子行业按窗口内成员收益<b>中位数</b>排序（抗异常值）→ '
        f'席位 <code>[15,12,10,8,7,6,5…]</code> 按名次分配，<code>slots=min(席位,有效成员)</code> → '
        f'组内强制纳入市值前列「压舱石」(顶部红条标记)，其余按 |涨跌| 选领涨/领跌，块内带符号降序。'
        f'市值仅 hover 显示。{"截至 " + as_of if as_of else ""}</div>'
        if prefer_cn else
        f'<div class="footnote"><b>Method.</b> Sub-sectors ranked by member-return <b>median</b> → '
        f'slots <code>[15,12,10,8,7,6,5…]</code> by rank → anchor top-mcap bellwethers (red cap) + '
        f'fill by |return|. Size = rank slot, not move. {"As of " + as_of if as_of else ""}</div>'
    )
    body = (
        f'<header class="masthead"><div class="mast-left">'
        f'<h1>{title}<span class="cmsi-tag">CMSI</span></h1>'
        f'<div class="sub">{sub} · {window_label}</div></div>{legend}</header>'
        f'{conv}{boards}{foot}'
    )
    doc = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<style>{_bento_css()}</style></head><body>{body}</body></html>"
    )
    return doc, _estimate_height(domains)
