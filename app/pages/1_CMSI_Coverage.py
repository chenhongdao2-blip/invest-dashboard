"""CMSI Coverage — 覆盖名单玻璃卡片表（coverage_table iframe 版）.

设计源（1:1 移植）：claude.ai/design 「CMSI 覆盖名单 美化.dc.html」.
data layer 与旧版完全兼容（db.sector_tickers / compute_returns / latest_multiples）.

变更摘要（vs 旧 D5 实现）:
- st.tabs + ui.render_html_table → coverage_table.render_coverage iframe
  （客户端 JS 切换市场 tab + 列排序，无 rerun）
- 拆除 sort selectbox（in-table sort 已覆盖）
- 保留 onboarding expander（expanded=True）+ sidebar search
- 新增「超额 vs 本市场基准」列（exc）：各市场股票对各自基准 YTD 做差
- i18n labels 走 i18n.t("cov.tbl.*")（缺 key → 返 key 字符串，不崩）
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import benchmarks as bm
from lib import coverage_table
from lib import db
from lib import i18n
from lib import model_view
from lib import theme
from lib import ui
from lib import section_header

st.set_page_config(
    page_title="CMSI Coverage · invest-dashboard",
    page_icon="💎",
    layout="wide",
)

# --- Sidebar ---
with st.sidebar:
    ui.sidebar_search(key_prefix="cmsi")

i18n.init_lang()
i18n.render_lang_toggle()

section_header.cover(i18n.t("cov.title"), "CMSI · COVERAGE",
                     rail=section_header.RAIL_HC, prefer_cn=i18n.get_lang() == "zh")
theme.page_radial_wash(1300)

prefer_cn = i18n.get_lang() == "zh"

# ---------------------------------------------------------------------------
# 1. Universe 加载
# ---------------------------------------------------------------------------
cmsi = db.sector_tickers("healthcare", "_coverage")
if cmsi.empty:
    st.warning("No CMSI coverage data — check config/universes/cmsi_coverage_hc.yml")
    st.stop()

tickers = tuple(cmsi["ticker"].tolist())
cmsi_idx = cmsi.set_index("ticker")

# Caption counts are derived from the loaded universe, never hardcoded — the
# 28/15/10 literals went stale the moment a name was added to the yml.
_reg = cmsi["region"].value_counts()
st.caption(i18n.t("cov.caption",
                  n=len(cmsi), hk=int(_reg.get("HK", 0)),
                  us=int(_reg.get("US", 0)), cn=int(_reg.get("CN", 0)),
                  date=(db.latest_snapshot_date() or "—")))

# ---------------------------------------------------------------------------
# 2. 数据层：回报 + 倍数 + 基准
# ---------------------------------------------------------------------------
closes = db.get_close_series_usd(tickers)
rets = db.compute_returns(closes)
mults = db.latest_multiples(tickers)

bench_df = bm.fetch_benchmarks()

def _bench_ytd(symbol: str) -> float | None:
    if bench_df.empty or symbol not in bench_df.index:
        return None
    v = bench_df.loc[symbol, "ytd_%"]
    return float(v) if pd.notna(v) else None

hk_ytd  = _bench_ytd("^HSI")
us_ytd  = _bench_ytd("^GSPC")
cn_ytd  = _bench_ytd("000001.SS")

# ---------------------------------------------------------------------------
# 3. 逐 ticker 行构建（匹配 coverage_table.render_coverage 的 rows schema）
# ---------------------------------------------------------------------------
# region → benchmark ytd 映射
_REGION_BENCH: dict[str, float | None] = {
    "HK": hk_ytd,
    "US": us_ytd,
    "CN": cn_ytd,
}

rows_all: list[dict] = []
for tk in tickers:
    ri = rets.loc[tk] if (not rets.empty and tk in rets.index) else pd.Series(dtype=float)
    mi = mults.loc[tk] if (not mults.empty and tk in mults.index) else pd.Series(dtype=float)
    region = str(cmsi_idx.loc[tk, "region"]) if tk in cmsi_idx.index else "HK"

    mcap_raw = mi.get("market_cap_usd")
    mcap_b = (float(mcap_raw) / 1e9) if (mcap_raw is not None and pd.notna(mcap_raw)) else None

    ytd = ri.get("ytd_%")
    ytd = float(ytd) if (ytd is not None and pd.notna(ytd)) else None

    # 超额 = 该股 ytd − 本市场基准 ytd（换算成 pp）
    bm_ytd = _REGION_BENCH.get(region)
    exc: float | None = None
    if ytd is not None and bm_ytd is not None:
        exc = ytd - bm_ytd

    def _f(col: str) -> float | None:
        v = ri.get(col) if col in ("1m_%", "5d_%", "1d_%") else mi.get(col)
        return float(v) if (v is not None and pd.notna(v)) else None

    name = (cmsi_idx.loc[tk, "name_cn"] if prefer_cn else cmsi_idx.loc[tk, "name_en"]) \
           if tk in cmsi_idx.index else tk

    rows_all.append({
        "t":     tk,
        "n":     str(name) if name and str(name) not in ("nan", "None") else tk,
        "model": model_view.has_model(tk),
        "region": region,
        "mcap":  mcap_b,
        "ytd":   ytd,
        "m1":    _f("1m_%"),
        "d5":    _f("5d_%"),
        "d1":    _f("1d_%"),
        "exc":   exc,
        "peS":   _f("trailing_pe"),
        "peF":   _f("forward_pe"),
        "evE":   _f("ev_ebitda"),
    })

# ---------------------------------------------------------------------------
# 4. 组装 tabs_payload（HK / US / CN / ALL）
# ---------------------------------------------------------------------------
MARKET_ORDER = [
    ("HK", i18n.t("cov.tbl.tab.hk"),  "^HSI",       "恒指" if prefer_cn else "HSI",    hk_ytd),
    ("US", i18n.t("cov.tbl.tab.us"),  "^GSPC",      "标普" if prefer_cn else "S&P500", us_ytd),
    ("CN", i18n.t("cov.tbl.tab.cn"),  "000001.SS",  "上证" if prefer_cn else "SSE",    cn_ytd),
]

tabs_payload: list[dict] = []
for region, tab_lbl, _sym, bench_lbl, b_ytd in MARKET_ORDER:
    region_rows = [r for r in rows_all if r["region"] == region]
    if not region_rows:
        continue
    tabs_payload.append({
        "id":          region,
        "label":       tab_lbl,
        "count":       len(region_rows),
        "bench_label": bench_lbl,
        "bench_ytd":   b_ytd,
        "rows":        [{k: v for k, v in r.items() if k != "region"} for r in region_rows],
    })

# ALL tab：各股保留各自 exc（already computed per-market）；bench_ytd=None
all_rows = [{k: v for k, v in r.items() if k != "region"} for r in rows_all]
tabs_payload.append({
    "id":          "ALL",
    "label":       i18n.t("cov.tbl.tab.all"),
    "count":       len(all_rows),
    "bench_label": i18n.t("cov.tbl.bench.own"),   # "各自基准"
    "bench_ytd":   None,
    "rows":        all_rows,
})

# ---------------------------------------------------------------------------
# 5. Labels（i18n，缺 key 退回 key 字符串）
# ---------------------------------------------------------------------------
labels = {
    # 摘要条
    "cover":       i18n.t("cov.tbl.cover"),
    "mcap_total":  i18n.t("cov.tbl.mcap_total"),
    "ytd_med":     i18n.t("cov.tbl.ytd_med"),
    "bench_prefix": i18n.t("cov.tbl.bench_prefix"),
    "beat_label":  i18n.t("cov.tbl.beat_label"),
    "unit_names":  i18n.t("cov.tbl.unit_names"),
    "median":      i18n.t("cov.tbl.median"),
    # 组头带
    "grp_ret":       i18n.t("cov.tbl.grp_ret"),
    "grp_exc_prefix": i18n.t("cov.tbl.grp_exc_prefix"),
    "grp_val":       i18n.t("cov.tbl.grp_val"),
    # 列标题
    "cols": {
        "t":          i18n.t("cov.tbl.col.t"),
        "n":          i18n.t("cov.tbl.col.n"),
        "mcap":       i18n.t("cov.tbl.col.mcap"),
        "ytd":        i18n.t("cov.tbl.col.ytd"),
        "m1":         i18n.t("cov.tbl.col.m1"),
        "d5":         i18n.t("cov.tbl.col.d5"),
        "d1":         i18n.t("cov.tbl.col.d1"),
        # exc 列：前缀 + tab bench_label + 后缀（JS 侧动态拼）
        "exc_prefix": i18n.t("cov.tbl.col.exc_prefix"),
        "exc":        i18n.t("cov.tbl.col.exc"),   # fallback 静态 label
        "exc_suffix": i18n.t("cov.tbl.col.exc_suffix"),
        "peS":        i18n.t("cov.tbl.col.peS"),
        "peF":        i18n.t("cov.tbl.col.peF"),
        "evE":        i18n.t("cov.tbl.col.evE"),
    },
    # 脚注
    "footnote": i18n.t("cov.tbl.footnote", date=(db.latest_snapshot_date() or "—")),
    "brand":    "CMSI · COVERAGE",
}

# ---------------------------------------------------------------------------
# 6. 渲染 iframe
# ---------------------------------------------------------------------------
if not tabs_payload:
    st.warning("No rows to display.")
else:
    _doc, _h = coverage_table.render_coverage(tabs_payload, labels=labels, height=780)
    st.iframe(_doc, height=_h)

# ---------------------------------------------------------------------------
# 7. Onboarding（不折叠，George 要求）
# ---------------------------------------------------------------------------
with st.expander(i18n.t("cov.onboarding.title"), expanded=True):
    st.markdown(i18n.t("cov.onboarding.body"))
