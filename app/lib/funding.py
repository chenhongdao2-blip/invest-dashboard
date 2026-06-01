"""ED-Funding capital-markets data layer (P0a — reads JSON copied into repo).

Source: ~/yuqing-system/healthcare/ed-funding (CMSI HC monthly funding tracker),
artifacts COPIED into data/external/ at ingest time (NEVER live-read ~/yuqing-system
from the app — Streamlit Cloud has no access to that filesystem; same failure mode
as the killed live-yfinance Cloud-staleness bug).

Two source files:
- data/external/funding_aggregate.json  — 6 monthly series × 12 months (trailing-12M
  rolling window). The `医疗行业投融资总金额` series is USD **bn**; the 5 sub-series
  are USD **mn**. This module NORMALIZES everything to USD mn for cross-series math
  and keeps each series' native display unit (bn for total, mn for sub-series) so a
  chart never mixes scales by 1000x.
- data/external/funding_mnc_balance_2026Q1.json — 18 MNC balance sheets (12 with
  us-gaap cash; 6 null = NVS/AZN/SNY/NVO/PHG 20-F ADRs + GEHC cash null).

Reliability: the aggregate is MEDIUM (curated PitchBook-style export); the MNC sheet
is HIGH (SEC XBRL via edgartools). Surfaced via funding.SOURCE_TIER.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
AGG_PATH = REPO_ROOT / "data" / "external" / "funding_aggregate.json"            # legacy monthly (PitchBook, retired from page)
MNC_PATH = REPO_ROOT / "data" / "external" / "funding_mnc_balance_2026Q1.json"
PUBLIC_PATH = REPO_ROOT / "data" / "external" / "funding_public_q1_2026.json"    # Option-2 quarterly public-source interim
MNC_DEALS_PATH = REPO_ROOT / "data" / "external" / "mnc_ma_deals.csv"            # Pharma MNC M&A deal-level (from MNCs basket xlsx)
MNC_DEALS_META = REPO_ROOT / "data" / "external" / "mnc_ma_deals_meta.json"

# Source-tier labels (research-data.md). The aggregate is a curated monthly export
# (MEDIUM); the MNC balance sheet is SEC XBRL (HIGH).
SOURCE_TIER = {"aggregate": "MEDIUM", "mnc": "HIGH"}
SOURCE_NOTE = {
    "aggregate": "yuqing/ED-Funding 月度 aggregate (PitchBook 式策划口径)",
    "mnc": "SEC EDGAR 10-Q / 20-F XBRL (edgartools)",
}
MNC_AS_OF = "2026Q1"

# Series registry. `json_key` is the EXACT key in funding_aggregate.json.
# `unit` is the series' NATIVE display unit; `bucket` groups for M&A-vs-VC split;
# `domain` groups for the 3-col sub-sector sparkline grid.
SERIES = [
    {"id": "hc_total",   "json_key": "医疗行业投融资总金额", "unit": "bn", "bucket": "total",  "domain": None},
    {"id": "pharma_ma",  "json_key": "药M&A",              "unit": "mn", "bucket": "ma",     "domain": "pharma"},
    {"id": "pharma_vc",  "json_key": "药VC&IPO",           "unit": "mn", "bucket": "vc_ipo", "domain": "pharma"},
    {"id": "device_ma",  "json_key": "器械M&A",            "unit": "mn", "bucket": "ma",     "domain": "device"},
    {"id": "device_vc",  "json_key": "器械VC&IPO",         "unit": "mn", "bucket": "vc_ipo", "domain": "device"},
    {"id": "digital_vc", "json_key": "数字医疗VC&IPO",      "unit": "mn", "bucket": "vc_ipo", "domain": "digital"},
]
_BY_ID = {s["id"]: s for s in SERIES}


def _to_period_ts(label: str) -> pd.Timestamp:
    """'2025 Apr' → Timestamp(2025-04-01). Robust to stray whitespace."""
    return pd.to_datetime(str(label).strip(), format="%Y %b")


@st.cache_data(ttl=600)
def load_aggregate() -> pd.DataFrame:
    """Long-format tidy frame of the 6 monthly series.

    Columns: series_id, period (Timestamp, month-start), period_label (raw '2025 Apr'),
             capital_mn (ALWAYS USD mn — hc_total ×1000 from bn), deal_count,
             unit (native display unit 'bn'|'mn').
    All values normalized to USD mn in `capital_mn` so buckets/charts share one scale;
    `unit` carries the native unit for per-series display.
    """
    with AGG_PATH.open(encoding="utf-8") as f:
        raw = json.load(f)
    rows = []
    for spec in SERIES:
        block = raw.get(spec["json_key"])
        if not block or len(block) < 2:
            continue
        for r in block[1:]:  # row[0] is the header
            label, capital, count = r[0], r[1], r[2]
            cap_mn = float(capital) * (1000.0 if spec["unit"] == "bn" else 1.0)
            rows.append({
                "series_id": spec["id"],
                "period": _to_period_ts(label),
                "period_label": str(label).strip(),
                "capital_mn": cap_mn,
                "deal_count": int(count) if count is not None else None,
                "unit": spec["unit"],
            })
    df = pd.DataFrame(rows).sort_values(["series_id", "period"]).reset_index(drop=True)
    return df


def series_frame(agg: pd.DataFrame, series_id: str) -> pd.DataFrame:
    """One series as a period-indexed frame (capital_mn + deal_count), ascending."""
    sub = agg[agg["series_id"] == series_id].sort_values("period")
    return sub.set_index("period")[["capital_mn", "deal_count", "period_label"]]


def native_capital(series_id: str, capital_mn: float) -> float:
    """Convert the normalized USD-mn value back to the series' native unit for display
    (hc_total → bn; everyone else stays mn)."""
    return capital_mn / 1000.0 if _BY_ID[series_id]["unit"] == "bn" else capital_mn


def latest_period_label(agg: pd.DataFrame) -> str:
    """Raw label of the most recent month (e.g. '2026 Mar') — the page's (截至) stamp."""
    return agg.sort_values("period")["period_label"].iloc[-1]


def window_label(agg: pd.DataFrame) -> tuple[str, str]:
    """(first, last) raw month labels of the trailing window, e.g. ('2025 Apr','2026 Mar')."""
    s = agg.sort_values("period")["period_label"]
    return s.iloc[0], s.iloc[-1]


def kpis(agg: pd.DataFrame) -> dict:
    """Headline KPI bundle for the strip. All windows explicitly labeled (fixes the
    'latest-month vs TTM' mislabel risk): TTM = sum over the 12-month window; latest
    = most recent single month.

    Returns:
      ttm_total_bn        trailing-12M total HC capital (USD bn)
      latest_total_bn     latest-month HC capital (USD bn)
      latest_total_mom    latest-month MoM % (vs prior month)
      latest_deals        latest-MONTH total deal count (NOT a 12M sum)
      ttm_deals           trailing-12M total deal count (sum)
      ma_share_latest     latest-month M&A bucket as % of (M&A + VC/IPO) buckets
      ma_mn_latest        latest-month M&A bucket capital (USD mn)
      vc_mn_latest        latest-month VC/IPO bucket capital (USD mn)
    """
    total = series_frame(agg, "hc_total")
    ttm_total_bn = native_capital("hc_total", total["capital_mn"].sum())
    latest_total_bn = native_capital("hc_total", total["capital_mn"].iloc[-1])
    prev_total = total["capital_mn"].iloc[-2] if len(total) >= 2 else None
    latest_total_mom = (
        (total["capital_mn"].iloc[-1] - prev_total) / prev_total * 100.0
        if prev_total else None
    )
    latest_deals = int(total["deal_count"].iloc[-1])
    ttm_deals = int(total["deal_count"].sum())

    # M&A vs VC/IPO buckets (latest month), normalized USD mn.
    def _bucket_latest(bucket: str) -> float:
        ids = [s["id"] for s in SERIES if s["bucket"] == bucket]
        return float(sum(series_frame(agg, sid)["capital_mn"].iloc[-1] for sid in ids))

    ma_mn = _bucket_latest("ma")
    vc_mn = _bucket_latest("vc_ipo")
    denom = ma_mn + vc_mn
    ma_share = (ma_mn / denom * 100.0) if denom else None

    return {
        "ttm_total_bn": ttm_total_bn,
        "latest_total_bn": latest_total_bn,
        "latest_total_mom": latest_total_mom,
        "latest_deals": latest_deals,
        "ttm_deals": ttm_deals,
        "ma_share_latest": ma_share,
        "ma_mn_latest": ma_mn,
        "vc_mn_latest": vc_mn,
    }


def domain_series_mn(agg: pd.DataFrame, domain: str) -> pd.Series:
    """Sum the sub-series of a domain into one USD-mn capital path (period-indexed).

    pharma = 药M&A + 药VC&IPO; device = 器械M&A + 器械VC&IPO;
    digital = 数字医疗VC&IPO ONLY (no M&A series tracked — caller must footnote, G4).
    """
    ids = [s["id"] for s in SERIES if s["domain"] == domain]
    frames = [series_frame(agg, sid)["capital_mn"].rename(sid) for sid in ids]
    if not frames:
        return pd.Series(dtype=float)
    wide = pd.concat(frames, axis=1)
    return wide.sum(axis=1)


@st.cache_data(ttl=600)
def load_mnc() -> pd.DataFrame:
    """MNC balance sheets (18 rows). Adds net_cash_bn = cash_bn − debt_total_bn.

    Rows with null cash (NVS/AZN/SNY/NVO/PHG 20-F ADRs + GEHC) keep NaN — the caller
    MUST flag them as 'no us-gaap cash' (NOT zero). net_cash_bn is NaN when cash is
    null so they never sort as if they had zero cash.
    """
    with MNC_PATH.open(encoding="utf-8") as f:
        rows = json.load(f)
    df = pd.DataFrame(rows)
    df["net_cash_bn"] = df["cash_bn"] - df["debt_total_bn"]
    return df


# ── Option-2 public-source quarterly interim (funding_public_q1_2026.json) ──
# Replaces the unavailable PitchBook monthly aggregate with publicly-cited,
# multi-source, adversarially-verified quarterly figures. Every row carries a
# measure (upfront-cash / incl-contingents / announced / raised / proceeds),
# a geography, a source tier, and a real URL.

# Scorecard order + which figure index is the headline anchor per segment.
_PUBLIC_ORDER = [
    "biopharma_ma", "biopharma_licensing", "biopharma_venture",
    "digital_health_vc_us", "digital_health_vc_global", "us_biotech_ipo", "medtech_ma",
]


@st.cache_data(ttl=600)
def load_public() -> dict:
    with PUBLIC_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def public_meta() -> dict:
    return load_public()["_meta"]


def public_scorecard() -> list[dict]:
    """One headline row per tracked segment (the anchor figure), with YoY where
    available. Plain dicts with stable keys; the page localizes labels.

    keys: seg_id, period, value_bn, count, measure, geo, tier, source, url,
          prior_bn, yoy_pct, partial (bool)
    """
    segs = load_public()["segments"]
    rows: list[dict] = []
    for sid in _PUBLIC_ORDER:
        seg = segs.get(sid)
        if not seg:
            continue
        fig = seg["figures"][0]                      # headline anchor = first figure
        yoy = seg.get("yoy") or {}
        rows.append({
            "seg_id": sid,
            "period": seg["period"],
            "value_bn": fig.get("value_usd_bn"),
            "count": fig.get("deal_count"),
            "measure": fig["measure"],
            "geo": seg["geography"],
            "tier": fig["tier"],
            "source": fig["source"],
            "url": fig.get("url", ""),
            "prior_bn": yoy.get("value_usd_bn"),
            "yoy_pct": yoy.get("yoy_pct"),
            "partial": "PARTIAL" in str(seg["period"]).upper(),
        })
    return rows


def public_all_citations() -> list[dict]:
    """Every figure (all measures, all sources) flattened for the methodology
    citation list. keys: seg_id, measure, value_bn, count, tier, source, url."""
    segs = load_public()["segments"]
    out: list[dict] = []
    for sid in _PUBLIC_ORDER:
        seg = segs.get(sid)
        if not seg:
            continue
        for fig in seg["figures"]:
            out.append({
                "seg_id": sid, "measure": fig["measure"],
                "value_bn": fig.get("value_usd_bn"), "count": fig.get("deal_count"),
                "tier": fig["tier"], "source": fig["source"], "url": fig.get("url", ""),
            })
    return out


def public_yoy_segments() -> list[dict]:
    """Segments with a clean Q1'25→Q1'26 comparator AND similar magnitude
    (the venture / VC family, $3-9B) — safe to chart on one grouped bar without
    the magnitude/measure-mixing trap. keys: seg_id, cur_bn, prior_bn."""
    out: list[dict] = []
    for r in public_scorecard():
        if r["seg_id"] in ("biopharma_venture", "digital_health_vc_us", "digital_health_vc_global") \
           and r["value_bn"] is not None and r["prior_bn"] is not None:
            out.append({"seg_id": r["seg_id"], "cur_bn": r["value_bn"], "prior_bn": r["prior_bn"]})
    return out


def fy_baselines() -> list[dict]:
    return load_public().get("fy2025_baselines", [])


# ── Pharma MNC M&A deal-level (mnc_ma_deals.csv) ───────────────────────────
# 398 deals across 13 pharma MNCs, 1986-2026, ~$1.5T. Source = the MNCs basket
# xlsx maintained by the mnc-deal-scanner skill. Columns: ticker, company, target,
# date, year, deal_size_mn, ta_group (canonical TA bucket), specialty, size_basis
# (Actual/Estimated), note.

# Each MNC's IR / newsroom — where these deals are officially announced. Used for
# the page's clickable Sources section (deal press releases live under these).
MNC_IR_URL = {
    "PFE": "https://www.pfizer.com/news/announcements",
    "MRK": "https://www.merck.com/media/news/",
    "LLY": "https://investor.lilly.com/news-releases",
    "JNJ": "https://www.investor.jnj.com/news/",
    "ABBV": "https://news.abbvie.com/",
    "BMY": "https://news.bms.com/",
    "AMGN": "https://www.amgen.com/newsroom/press-releases",
    "AZN": "https://www.astrazeneca.com/media-centre/press-releases.html",
    "GSK": "https://www.gsk.com/en-gb/media/press-releases/",
    "NVS": "https://www.novartis.com/news/media-releases",
    "SNY": "https://www.sanofi.com/en/media-room/press-releases",
    "ROG": "https://www.roche.com/media/releases",
    "NVO": "https://www.novonordisk.com/news-and-media/latest-news.html",
}


BD_DEALS_PATH = REPO_ROOT / "data" / "external" / "bd_deals.csv"   # report-format BD/licensing (2025 from ED report TABLE 59 + 2026)


@st.cache_data(ttl=600)
def load_mnc_deals() -> pd.DataFrame:
    df = pd.read_csv(MNC_DEALS_PATH)
    df["year"] = df["year"].astype(int)
    return df


@st.cache_data(ttl=600)
def load_bd_report() -> pd.DataFrame:
    """BD / licensing in the ED Funding report's own format: licensor → licensee,
    asset, MoA, TA, phase, region, upfront / milestone / total (USD mn), date.
    2025 rows = report TABLE 59; 2026 rows = biotech-verified MNC BD."""
    return pd.read_csv(BD_DEALS_PATH)


def mnc_ma_meta() -> dict:
    with MNC_DEALS_META.open(encoding="utf-8") as f:
        return json.load(f)


def mnc_by_company(df: pd.DataFrame) -> pd.DataFrame:
    """Per-MNC league: ticker → company, n deals, total USD bn. Desc by total."""
    g = (df.groupby(["ticker", "company"])
           .agg(n=("target", "size"), total_bn=("deal_size_mn", lambda x: x.sum() / 1000.0))
           .reset_index().sort_values("total_bn", ascending=False))
    return g


def mnc_by_ta(df: pd.DataFrame) -> pd.DataFrame:
    """By therapeutic-area bucket: ta_group → n, total USD bn. Desc by total."""
    g = (df.groupby("ta_group")
           .agg(n=("target", "size"), total_bn=("deal_size_mn", lambda x: x.sum() / 1000.0))
           .reset_index().sort_values("total_bn", ascending=False))
    return g


def mnc_by_year(df: pd.DataFrame) -> pd.DataFrame:
    """By completion year: year → n, total USD bn. Ascending year, gap-filled."""
    g = (df.groupby("year")
           .agg(n=("target", "size"), total_bn=("deal_size_mn", lambda x: x.sum() / 1000.0))
           .reset_index())
    full = pd.DataFrame({"year": range(int(g["year"].min()), int(g["year"].max()) + 1)})
    g = full.merge(g, on="year", how="left").fillna({"n": 0, "total_bn": 0.0})
    g["n"] = g["n"].astype(int)
    return g


def mnc_top_deals(df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    return df.nlargest(n, "deal_size_mn").copy()

