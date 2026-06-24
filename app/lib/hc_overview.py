"""Loaders for the Healthcare page's institutional-positioning + relative-performance
section. Reads the two committed CSVs baked by jobs/build_hc_overview_data.py
(cloud can't fetch iFind/yfinance live), so the page stays self-contained.

- hc_index_comparison.csv      : rebased-comparison source series (3 panels)
- china_fund_hc_positioning.csv: 12 funds' HC over/underweight vs benchmark
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_EXT = REPO_ROOT / "data" / "external"
IDX_PATH = _EXT / "hc_index_comparison.csv"
# HSHCI long-history monthly close (2021.7→now), baked by jobs/hshci_history.py —
# the "−70% → 翻倍 → 回调" full-cycle context line for the relative-performance section.
HSHCI_HIST_PATH = _EXT / "hshci_history_monthly.csv"
# Fund positioning: the FULL file (real fund names) is gitignored / local-only; the
# committed file is ANONYMISED (Fund 1–12) and is the only one that reaches Cloud.
# The loaders prefer the full file when it exists, else fall back to the public one —
# so local shows real names, Cloud shows Fund 1–12, with no per-environment branching.
POS_PATH_FULL = _EXT / "china_fund_hc_positioning_full.csv"
POS_PATH = _EXT / "china_fund_hc_positioning.csv"
POS_SRC_PATH_FULL = _EXT / "china_fund_hc_positioning_source_full.txt"
POS_SRC_PATH = _EXT / "china_fund_hc_positioning_source.txt"
# Headcount FY2024→FY2025 for 12 China innovative-pharma names (扩招 vs 收缩).
# Committed CSV baked by jobs/cn_pharma_headcount_2025.py from 年报公告 / ESG / iFind.
HC_PATH = _EXT / "cn_pharma_headcount.csv"

# Panel layout: (panel_id, hero_series_id, [peer_series_ids]). A series may recur
# across panels (^NBI / XBI in both nbi + ai_bio) — the baked CSV carries one row-set
# per (series, panel), so panel_series() slices cleanly. The hero is the CMSI-red
# emphasis line; peers default to muted grey unless the page passes peer_styles.
PANELS = [
    ("hk",     "HSHCI.HK",  ["HSI.HK", "HSTECH.HK"]),
    ("msci",   "KURE",      ["MCHI"]),       # MSCI 口径 ETF 代理 — 全中国医疗 vs 全中国宽基
    ("nbi",    "^NBI",      ["^IXIC", "XBI"]),  # +XBI 等权生科(SMID breadth) vs ^NBI 大盘
    ("sphc",   "^SP500-35", ["^GSPC"]),
    # 跨板块主题对比：生物科技(NBI 大盘 + XBI 等权) vs AI 硬件(^SOX 费城半导体)。
    ("ai_bio", "^NBI",      ["XBI", "^SOX"]),
]


def _resolve(*candidates: Path) -> tuple[str, float]:
    """Pick the first existing path (preference order) and snapshot its mtime.

    Returns (path_str, mtime) where path_str == "" when none exists. Both values are
    HASHED ARGUMENTS into the cached readers below, so the @st.cache_data key tracks
    BOTH the chosen path (full-vs-anon selection) AND the file's mtime — fixing the
    zero-arg cache trap where neither was in the key (cache-key-omits-input-state).
    Streamlit keys cache_data on (module, qualname, source_text) + hashed args ONLY
    (see lib/db.py:20-25); filesystem state is invisible unless passed as an arg.
    Resolution runs OUTSIDE any cache, so it re-evaluates on every render and an
    in-place rebuild (new mtime) or a freshly-landed full file (new path) invalidates.
    """
    for p in candidates:
        if p.exists():
            return str(p), p.stat().st_mtime
    return "", 0.0


@st.cache_data(ttl=3600)
def _read_index_comparison(path_str: str, mtime: float) -> pd.DataFrame:
    if not path_str:
        return pd.DataFrame()
    return pd.read_csv(path_str, parse_dates=["date"])


def load_index_comparison() -> pd.DataFrame:
    """date-indexed long frame: date, series_id, name_en, name_cn, panel, close, source."""
    path_str, mtime = _resolve(IDX_PATH)
    return _read_index_comparison(path_str, mtime)


@st.cache_data(ttl=3600)
def _read_hshci_history(path_str: str, mtime: float) -> pd.DataFrame:
    if not path_str:
        return pd.DataFrame()
    return pd.read_csv(path_str, parse_dates=["date"])


def load_hshci_history() -> pd.DataFrame:
    """HSHCI monthly close 2021.7→now (committed CSV). Path+mtime outside cache."""
    path_str, mtime = _resolve(HSHCI_HIST_PATH)
    return _read_hshci_history(path_str, mtime)


def hshci_milestones(df: pd.DataFrame) -> dict:
    """start / trough / recovery-peak(after trough) / now — all computed from data.

    Returns {start, trough, peak, now} where each is a dict with date/close and the
    relevant pct (trough vs start, peak vs trough, now vs peak & vs start). Drives
    both the chart annotations and the bilingual caption — never hardcoded prose.
    """
    if df.empty:
        return {}
    d = df.sort_values("date").reset_index(drop=True)
    c = d["close"]
    i_tr = int(c.idxmin())
    i_pk = int(c.iloc[i_tr:].idxmax())
    i_now = len(d) - 1
    s, t, p, n = c.iloc[0], c.iloc[i_tr], c.iloc[i_pk], c.iloc[i_now]
    fmt = lambda i: d["date"].iloc[i].strftime("%Y-%m")
    return {
        "start": {"date": fmt(0), "close": float(s)},
        "trough": {"date": fmt(i_tr), "close": float(t), "pct_start": float(t / s - 1)},
        "peak": {"date": fmt(i_pk), "close": float(p), "pct_trough": float(p / t - 1)},
        "now": {"date": fmt(i_now), "close": float(n),
                "pct_peak": float(n / p - 1), "pct_start": float(n / s - 1)},
    }


def panel_series(df: pd.DataFrame, panel: str) -> dict[str, pd.Series]:
    """{series_id: close series indexed by date} for one panel."""
    sub = df[df["panel"] == panel]
    return {sid: g.set_index("date")["close"].sort_index() for sid, g in sub.groupby("series_id")}


def series_name(df: pd.DataFrame, series_id: str, *, prefer_cn: bool) -> str:
    row = df[df["series_id"] == series_id]
    if row.empty:
        return series_id
    return str(row.iloc[0]["name_cn" if prefer_cn else "name_en"])


@st.cache_data(ttl=3600)
def _read_fund_positioning(path_str: str, mtime: float) -> pd.DataFrame:
    if not path_str:
        return pd.DataFrame()
    df = pd.read_csv(path_str)
    # The builder writes the literal sentinel "N/A" into ow_uw_2026 for the one fund
    # that discloses no HC weight. pandas' DEFAULT na_values
    # includes "N/A", so read_csv silently coerces that token to float NaN — which
    # then (1) makes positioning_verdict's `== "N/A"` branch dead code (the fund is
    # dropped from the count, so the tally no longer sums to the universe), and
    # (2) makes the page's str(s).strip() stance lookup miss every key and fall
    # through to the Neutral fallback (mislabelling an undisclosed fund "中性").
    # Restore the sentinel at the loader boundary so the undisclosed fund is both
    # counted as N/A and routed to the dedicated NA stance key.
    if "ow_uw_2026" in df.columns:
        df["ow_uw_2026"] = df["ow_uw_2026"].where(df["ow_uw_2026"].notna(), "N/A")
    return df


def load_fund_positioning() -> pd.DataFrame:
    # Prefer the local full (real-names) file, else the committed anon one. Path +
    # mtime are resolved OUTSIDE the cache and passed in, so a full file landing
    # mid-process (path change) or an in-place rebuild (mtime change) invalidates.
    path_str, mtime = _resolve(POS_PATH_FULL, POS_PATH)
    return _read_fund_positioning(path_str, mtime)


@st.cache_data(ttl=3600)
def _read_positioning_source(path_str: str, mtime: float) -> str:
    if not path_str:
        return ""
    return Path(path_str).read_text(encoding="utf-8").strip()


def positioning_source() -> str:
    path_str, mtime = _resolve(POS_SRC_PATH_FULL, POS_SRC_PATH)
    return _read_positioning_source(path_str, mtime)


def positioning_verdict(df: pd.DataFrame) -> dict:
    """Counts + AUM-weighted tilt sign. AUM weighting parses the '3.3bn'/'995mn' strings.

    Returns {n_ow, n_uw, n_neu, n_na, aum_wt_dev, tilt} where tilt ∈ {OW, UW, ~flat}.
    aum_wt_dev is the AUM-weighted mean of deviation_2026 over funds WITH data — the
    "real money" tilt that the headline verdict rests on.

    When data_available, also emits the extremal figures the verdict narrates, all
    computed from the data (never hardcoded prose): largest_aum_dev / largest_aum_label
    (top-AUM fund), second_aum_dev (2nd-largest, if any), max_ow_dev (peak overweight).
    """
    if df.empty:
        return {}
    ow_uw = df["ow_uw_2026"].astype(str)
    # contains() on BOTH OW and UW (symmetric): "Slightly OW"/"Slightly UW" must each
    # land in their lean. Exact =="UW" silently dropped "Slightly UW" while n_ow's
    # contains() caught "Slightly OW" — an asymmetry that understated the underweight
    # tally and broke the {n_ow}/{n_uw}/{n_neu}/{n_na} partition of the universe.
    n_ow = ow_uw.str.contains("OW", na=False).sum()
    n_uw = ow_uw.str.contains("UW", na=False).sum()
    n_neu = ow_uw.str.contains("Neutral", na=False).sum()
    n_na = (ow_uw == "N/A").sum()

    have = df.dropna(subset=["deviation_2026"]).copy()
    have["_aum"] = have["aum_2026"].map(_parse_aum)
    have = have.dropna(subset=["_aum"])

    counts = {"n_ow": int(n_ow), "n_uw": int(n_uw), "n_neu": int(n_neu), "n_na": int(n_na)}

    # No fund has BOTH a parseable AUM and a non-NaN deviation → zero real-money
    # signal. Emit an explicit no-data sentinel instead of a silent NaN: omit the
    # aum_wt_dev key entirely (so the caller's `.get("aum_wt_dev", 0.0)` default
    # fires and never formats a NaN into a finite-looking "+X.Xpp"), and refuse to
    # advertise a "~flat" tilt that no money backs. `data_available` lets the
    # caller branch on the no-data case explicitly.
    denom = float(have["_aum"].sum()) if not have.empty else 0.0
    if have.empty or denom <= 0:
        # No parseable AUM behind any non-NaN deviation (empty) OR a zero / non-positive
        # AUM denominator → no real-money signal. Same no-data sentinel as the empty
        # case: OMIT aum_wt_dev (so the caller's .get(...,0.0) default fires and never
        # formats a NaN into a finite-looking "+X.Xpp"), and refuse a "~flat" tilt that
        # zero money backs. A non-empty `have` whose AUMs all parse to 0.0 lands here too.
        return {**counts, "data_available": False, "tilt": "n/a"}

    aum_wt_dev = float((have["deviation_2026"] * have["_aum"]).sum() / denom)
    tilt = "OW" if aum_wt_dev > 0.002 else "UW" if aum_wt_dev < -0.002 else "~flat"

    # Emit the extremal/largest-fund figures the verdict narrates, computed FROM the
    # data (data-narrative-coupling fix). The verdict_tilt template previously froze
    # these as English prose ('largest fund 3.3bn ... -3.8pp', '2nd-largest +1.1pp',
    # 'up to +6.7pp'); when build_hc_overview_data.py re-bakes a new quarter those
    # literals silently diverge from the diverging-bar chart on the same screen.
    # Surfacing them here lets the template be parameterised instead of hardcoded.
    ranked = have.sort_values("_aum", ascending=False).reset_index(drop=True)
    extremes: dict = {
        "largest_aum_dev": float(ranked.loc[0, "deviation_2026"]),
        "largest_aum_label": str(ranked.loc[0, "aum_2026"]),
        "max_ow_dev": float(ranked["deviation_2026"].max()),
    }
    if len(ranked) > 1:
        extremes["second_aum_dev"] = float(ranked.loc[1, "deviation_2026"])

    return {**counts, "data_available": True, "aum_wt_dev": aum_wt_dev, "tilt": tilt, **extremes}


@st.cache_data(ttl=3600)
def _read_headcount(path_str: str, mtime: float) -> pd.DataFrame:
    if not path_str:
        return pd.DataFrame()
    return pd.read_csv(path_str)


def load_headcount() -> pd.DataFrame:
    """12 China innovative-pharma names' FY2024→FY2025 headcount (committed CSV).

    Path + mtime resolved OUTSIDE the cache so an in-place re-bake invalidates.
    """
    path_str, mtime = _resolve(HC_PATH)
    return _read_headcount(path_str, mtime)


def headcount_verdict(df: pd.DataFrame) -> dict:
    """Counts + net + the extremal hirer/cutter the headline narrates — all from data.

    Returns {n_hire, n_cut, n_flat, net, top_hire_name, top_hire_delta,
    top_cut_name, top_cut_delta, asof}. Hire = delta>0, cut = delta<0.
    """
    if df.empty:
        return {}
    d = df.dropna(subset=["delta"]).copy()
    d["delta"] = pd.to_numeric(d["delta"], errors="coerce")
    d = d.dropna(subset=["delta"])
    n_hire = int((d["delta"] > 0).sum())
    n_cut = int((d["delta"] < 0).sum())
    n_flat = int((d["delta"] == 0).sum())
    top_h = d.loc[d["delta"].idxmax()]
    top_c = d.loc[d["delta"].idxmin()]
    return {
        "n_hire": n_hire, "n_cut": n_cut, "n_flat": n_flat,
        "net": int(d["delta"].sum()),
        "top_hire_name_cn": str(top_h["name_cn"]), "top_hire_name_en": str(top_h["name_en"]),
        "top_hire_delta": int(top_h["delta"]),
        "top_cut_name_cn": str(top_c["name_cn"]), "top_cut_name_en": str(top_c["name_en"]),
        "top_cut_delta": int(top_c["delta"]),
        "asof": str(d["asof"].iloc[0]) if "asof" in d.columns and len(d) else "",
    }


# --- Japan Healthcare 区域 universe（「日本医药」section） -----------------------
# Universe = config/universes/hc_japan.yml（42 支，jobs/_gen_jp_seed.py 从 iFind 自选
# 清单生成）。subsector 分组只活在 yml（不进 DB）——这里读 yml 是分组的单一数据源；
# 价格走 prices_daily（EOD cron 日刷，JPY→USD 已转）。
JP_UNIVERSE_PATH = REPO_ROOT / "config" / "universes" / "hc_japan.yml"
JP_SUBSECTOR_ORDER = ["pharma", "medtech", "diagnostics", "distribution"]


@st.cache_data(ttl=3600)
def _read_jp_universe(path_str: str, mtime: float) -> pd.DataFrame:
    if not path_str:
        return pd.DataFrame()
    import yaml
    with open(path_str, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    df = pd.DataFrame(data.get("tickers") or [])
    # keep yml order (mcap-desc within subsector) but expose a stable sort key
    df["_sub_rank"] = df["subsector"].map({s: i for i, s in enumerate(JP_SUBSECTOR_ORDER)})
    return df


def jp_universe() -> pd.DataFrame:
    """ticker / name_cn / name_en / subsector / note — path+mtime outside cache."""
    path_str, mtime = _resolve(JP_UNIVERSE_PATH)
    return _read_jp_universe(path_str, mtime)


def jp_composite(closes: pd.DataFrame, weights: pd.Series | None = None,
                 min_coverage: float = 0.9) -> pd.Series | None:
    """市值加权「日本医药专栏指数」：USD close panel → 锚日归一 100 → 按权重平均。

    `weights` = ticker-indexed 市值快照（hc_japan.yml `mcap_bn_jpy`，2026/05/26）。
    股本不变时「锚日市值权重 × 归一价格」= 标准市值加权指数（George 2026-06-10
    指定，替换最初的等权口径）。weights 缺失/全零时回退等权。
    锚 = 首个覆盖率 ≥ min_coverage 的交易日（per-ticker ffill 后）；锚日仍缺数的
    ticker 整条剔除（记在 .attrs['dropped']，caption 可披露）。
    """
    if closes is None or closes.empty:
        return None
    panel = closes.sort_index().ffill()
    coverage = panel.notna().mean(axis=1)
    ok = coverage[coverage >= min_coverage]
    if ok.empty:
        return None
    anchor = ok.index[0]
    base = panel.loc[anchor]
    keep = base.dropna().index
    normalized = panel.loc[anchor:, keep].div(base[keep]) * 100.0
    w = weights.reindex(keep).fillna(0.0) if weights is not None else None
    if w is not None and float(w.sum()) > 0:
        comp = normalized.mul(w, axis=1).sum(axis=1) / float(w.sum())
    else:
        comp = normalized.mean(axis=1)
    comp.attrs["anchor"] = anchor
    comp.attrs["dropped"] = sorted(set(panel.columns) - set(keep))
    return comp


@st.cache_data(ttl=300)
def jp_benchmarks_usd() -> dict[str, pd.Series]:
    """{'1305.T': TOPIX-ETF USD 序列, '^N225': 日经 USD 序列}。

    benchmarks_daily 存 NATIVE 报价（两者 JPY）；÷ 同表的 JPY=X（USDJPY）序列换 USD，
    与 prices_daily 的 close_usd 同口径。JPY=X 缺数日 ffill（汇率日频连续，假日沿用）。
    TOPIX 代理 = 1305.T（大和）：1306.T 2026-03-30 10:1 拆股 Yahoo 未复权，序列废。
    """
    from lib import db
    raw = db.query(
        "SELECT ticker, date, close FROM benchmarks_daily "
        "WHERE ticker IN ('1305.T', '^N225', 'JPY=X') ORDER BY date"
    )
    if raw.empty:
        return {}
    raw["date"] = pd.to_datetime(raw["date"])
    panel = raw.pivot(index="date", columns="ticker", values="close").sort_index()
    if "JPY=X" not in panel.columns:
        return {}
    jpy = panel["JPY=X"].ffill()
    out: dict[str, pd.Series] = {}
    for t in ("1305.T", "^N225"):
        if t in panel.columns:
            ser = (panel[t] / jpy).dropna()
            if not ser.empty:
                out[t] = ser
    return out


def _parse_aum(s) -> float | None:
    """'3.3bn' → 3300, '995mn' → 995, '2,609mn' → 2609 (USD mn). None if unparseable."""
    if s is None:
        return None
    t = str(s).strip().lower().replace(",", "").replace("~", "").replace("usd", "").strip()
    try:
        if t.endswith("bn"):
            return float(t[:-2]) * 1000.0
        if t.endswith("mn"):
            return float(t[:-2])
        return float(t)
    except ValueError:
        return None
