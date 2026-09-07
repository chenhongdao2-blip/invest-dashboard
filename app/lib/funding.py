"""ED-Funding capital-markets data layer — MNC balance sheets, M&A deals, BD deals.

Source: ~/yuqing-system/healthcare/ed-funding (CMSI HC funding tracker) plus the
MNCs basket xlsx, artifacts COPIED into data/external/ at ingest time (NEVER
live-read ~/yuqing-system from the app — Streamlit Cloud has no access to that
filesystem; same failure mode as the killed live-yfinance Cloud-staleness bug).

Live source files:
- data/external/funding_mnc_balance_2026Q1.json — 18 MNC balance sheets (12 with
  us-gaap cash; 6 null = NVS/AZN/SNY/NVO/PHG 20-F ADRs + GEHC cash null).
- data/external/mnc_ma_deals.csv (+ _meta.json) — Pharma MNC M&A, deal level.
- data/external/mnc_ma_rumors.json — rumours, isolated (never summed into totals).
- data/external/bd_deals.csv — report-format BD / licensing deals.

Reliability: the MNC balance sheet is HIGH (SEC XBRL via edgartools); the deal
tables are MEDIUM (curated exports).

Retired (R3 audit §7): the monthly PitchBook-style `funding_aggregate.json` layer
and the `funding_public_q1_2026.json` Option-2 quarterly interim were both dropped
from 9_HC_Capital_Markets long ago; their 14 reader functions had zero call sites
and were deleted. Restore from git history if either dataset comes back.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MNC_PATH = REPO_ROOT / "data" / "external" / "funding_mnc_balance_2026Q1.json"
MNC_DEALS_PATH = REPO_ROOT / "data" / "external" / "mnc_ma_deals.csv"            # Pharma MNC M&A deal-level (from MNCs basket xlsx)
MNC_DEALS_META = REPO_ROOT / "data" / "external" / "mnc_ma_deals_meta.json"

MNC_AS_OF = "2026Q1"


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


# ── Pharma MNC M&A deal-level (mnc_ma_deals.csv) ───────────────────────────
# Deal-level acquisitions across global pharma/biotech buyers, 1986-2026. Original
# 13-MNC basket (mnc-deal-scanner skill) expanded 2026-06 to add active buyers
# (GILD/BIIB/UCB/MRK.DE…). M&A rows are sourced via web/deal-tracker (Fierce,
# BioPharma Dive, BioBucks) — PharmCube drugDeal carries NO corporate M&A, only BD.
# Columns: ticker, company, target,
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
    # 2026 universe expansion — additional global biopharma buyers active in M&A.
    "GILD": "https://www.gilead.com/news/press-releases",
    "BIIB": "https://investors.biogen.com/news-releases",
    "UCB": "https://www.ucb.com/stories-media/Press-Releases",
    "MRK.DE": "https://www.merckgroup.com/en/news.html",  # Merck KGaA (Darmstadt) — NOT Merck & Co
    # 2026-08 FactSet 增强新增买家 (17 -> 20)
    "VRTX": "https://investors.vrtx.com/press-releases",
    "BAYN": "https://www.bayer.com/en/news-stories",
    "4568-JP": "https://www.daiichisankyo.com/media/press_release/",  # 第一三共 (本表仅剥离方向)
}


MNC_RUMORS_PATH = REPO_ROOT / "data" / "external" / "mnc_ma_rumors.json"  # 传闻隔离, 不计入总额

BD_DEALS_PATH = REPO_ROOT / "data" / "external" / "bd_deals.csv"   # report-format BD/licensing (2025 from ED report TABLE 59 + 2026)


@st.cache_data(ttl=600)
def load_mnc_deals() -> pd.DataFrame:
    """全量交易表。含 2026-08 FactSet 增强列：announce_date / close_date / lag_days /
    date_basis / direction / fs_tv_mn / fs_status / fs_ev_ebitda / fs_ev_sales /
    fs_deal_id / flag。

    ⚠ `date` 列语义不一致（2026 行=宣布日，历史行=交割日，已用 Celgene 实证）。
    需要明确语义时一律读 announce_date / close_date，勿用 `date`。
    ⚠ `direction`：buy=该 MNC 作为买方；sell=剥离。所有"谁最爱买"类聚合
    必须先过 buy_side()，否则剥离会被算成收购。"""
    df = pd.read_csv(MNC_DEALS_PATH)
    df["year"] = df["year"].astype(int)
    for c in ("announce_date", "close_date", "date_basis", "direction",
              "fs_status", "fs_deal_id", "flag"):
        if c not in df.columns:
            df[c] = ""
    for c in ("lag_days", "fs_tv_mn", "fs_ev_ebitda", "fs_ev_sales"):
        if c not in df.columns:
            df[c] = pd.NA
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["direction"] = df["direction"].fillna("buy").replace("", "buy")
    return df


def buy_side(df: pd.DataFrame) -> pd.DataFrame:
    """仅买方交易。剔除剥离（direction=='sell'），避免污染"谁最爱买"口径。"""
    if "direction" not in df.columns:
        return df
    return df[df["direction"].fillna("buy") != "sell"]


@st.cache_data(ttl=600)
def load_mnc_rumors() -> list[dict]:
    """传闻 / 已取消交易 — 隔离展示，绝不计入 M&A 总额或笔数。"""
    if not MNC_RUMORS_PATH.exists():
        return []
    with MNC_RUMORS_PATH.open(encoding="utf-8") as f:
        return json.load(f).get("deals", [])


def mnc_close_lag(df: pd.DataFrame, year: int | None = None) -> pd.DataFrame:
    """announce -> close 时滞。仅保留真实有间隔的行：FactSet 在交割日未知时
    会用宣布日填充 close_date，lag==0 并非"当天交割"，直接统计会把中位数腰斩。"""
    d = df[df["lag_days"].notna() & (df["lag_days"] > 0)]
    if year is not None:
        d = d[d["year"] == year]
    cols = [c for c in ("ticker", "company", "target", "announce_date",
                        "close_date", "lag_days", "fs_status") if c in d.columns]
    return d[cols].sort_values("lag_days", ascending=False)


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
    g = (buy_side(df).groupby(["ticker", "company"])
           .agg(n=("target", "size"), total_bn=("deal_size_mn", lambda x: x.sum() / 1000.0))
           .reset_index().sort_values("total_bn", ascending=False))
    return g


def mnc_by_ta(df: pd.DataFrame) -> pd.DataFrame:
    """By therapeutic-area bucket: ta_group → n, total USD bn. Desc by total."""
    g = (buy_side(df).groupby("ta_group")
           .agg(n=("target", "size"), total_bn=("deal_size_mn", lambda x: x.sum() / 1000.0))
           .reset_index().sort_values("total_bn", ascending=False))
    return g


def mnc_by_year(df: pd.DataFrame) -> pd.DataFrame:
    """By completion year: year → n, total USD bn. Ascending year, gap-filled."""
    g = (buy_side(df).groupby("year")
           .agg(n=("target", "size"), total_bn=("deal_size_mn", lambda x: x.sum() / 1000.0))
           .reset_index())
    full = pd.DataFrame({"year": range(int(g["year"].min()), int(g["year"].max()) + 1)})
    g = full.merge(g, on="year", how="left").fillna({"n": 0, "total_bn": 0.0})
    g["n"] = g["n"].astype(int)
    return g


def mnc_top_deals(df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    return buy_side(df).nlargest(n, "deal_size_mn").copy()


# ── BD / licensing insight layer (bd_deals.csv = the 99-row canonical BD set) ──
# bd_deals.csv is the SINGLE source for BD insight. Do NOT union the 39 BD rows in
# mnc_ma_deals.csv — 28 overlap by value → double-count (biotech-researcher verified).
# The raw `ta` (45 free-text strings) and `phase` (20) must be canonicalized before
# any group-by, else Oncology splits across 肿瘤/Oncology/实体瘤 and undercounts ~2×.
# Canon TA maps to the M&A ta_group taxonomy (i18n._TA_ZH) so the M&A-by-TA and
# BD-by-TA charts share one axis.

BD_TA_CANON = {
    # already-canonical English (2026 rows already use ta_group)
    "Oncology": "Oncology", "Immunology": "Immunology",
    "Cardiovascular/Metabolic": "Cardiovascular/Metabolic", "CNS/Neurology": "CNS/Neurology",
    "Gene/Cell Therapy": "Gene/Cell Therapy", "Vaccines": "Vaccines",
    "Rare Disease": "Rare Disease", "IO/CNS": "Oncology", "Other": "Other",
    # Oncology
    "肿瘤": "Oncology", "癌症": "Oncology", "实体瘤": "Oncology", "前列腺癌": "Oncology",
    "慢阻塞肺病/肿瘤": "Oncology", "多发性骨髓瘤": "Oncology", "肿瘤 / 自免": "Oncology",
    "肿瘤/自免": "Oncology", "免疫/肿瘤/代谢": "Oncology",
    # Immunology & autoimmune
    "自免": "Immunology", "自免疾病": "Immunology", "免疫介导疾病": "Immunology",
    "炎症": "Immunology", "炎症(未指明)": "Immunology",
    # Cardiovascular / metabolic / obesity
    "代谢": "Cardiovascular/Metabolic", "代谢/CVD": "Cardiovascular/Metabolic",
    "代谢/肥胖": "Cardiovascular/Metabolic", "代谢 / 肥胖": "Cardiovascular/Metabolic",
    "代谢，肥胖": "Cardiovascular/Metabolic", "肥胖": "Cardiovascular/Metabolic",
    "肥胖/2型糖尿病": "Cardiovascular/Metabolic", "血脂调控": "Cardiovascular/Metabolic",
    "肥厚型心肌病 HCM": "Cardiovascular/Metabolic",
    # CNS / neurology
    "中枢神经": "CNS/Neurology", "神经科": "CNS/Neurology", "神经系统疾病": "CNS/Neurology",
    "神经退行性疾病": "CNS/Neurology", "多发性硬化症": "CNS/Neurology",
    "癫痫 Epilepsy": "CNS/Neurology", "肌萎缩侧索硬化症": "CNS/Neurology",
    # Rare disease
    "罕见病": "Rare Disease", "罕见血液/肾脏疾病": "Rare Disease", "遗传病": "Rare Disease",
    # Respiratory / vaccines-ID / other
    "呼吸系统疾病": "Respiratory", "传染病/细菌感染": "Vaccines", "未知": "Other",
}

BD_PHASE_CANON = {
    "临床前": "Preclinical/Discovery", "先导筛选": "Preclinical/Discovery",
    "发现阶段": "Preclinical/Discovery", "IND": "Preclinical/Discovery",
    "IND 递交": "Preclinical/Discovery", "申报临床": "Preclinical/Discovery",
    "IND/Ⅰ期": "Phase I", "Ⅰ期": "Phase I", "Ⅰ/Ⅱ期": "Phase I", "I/II期临床": "Phase I",
    "Ⅱ期": "Phase II", "Ⅱ期临床": "Phase II", "Ⅱb期": "Phase II", "Ⅱ/Ⅲ期": "Phase II",
    "Ⅲ期": "Phase III", "III期临床": "Phase III", "Phase 3": "Phase III",
    "批准上市": "Approved/Filed", "未披露": "Undisclosed", "—": "Undisclosed",
}
BD_PHASE_ORDER = ["Preclinical/Discovery", "Phase I", "Phase II", "Phase III",
                  "Approved/Filed", "Undisclosed"]

# Licensees that are NOT genuine global-MNC inbound buyers (NewCo / small biotech) or
# a reversed-direction deal (an MNC out-licensing) — biotech-flagged. Excluded ONLY
# from the "MNC buyer league" + KPI so that ranking stays clean; still counted in
# deal-count charts and the full detail table. (George: 稳妥+留痕)
BD_LEAGUE_EXCLUDE = {
    "Vor BioPharma", "Verdiva Bio", "Zenas BioPharma", "Radiance Bio", "Radiance",
    "Sidera Bio", "Kalexo Bio", "Alfasigma",
}


def bd_canon_ta(s) -> str:
    return BD_TA_CANON.get(str(s).strip(), "Other")


def bd_canon_phase(s) -> str:
    return BD_PHASE_CANON.get(str(s).strip(), "Undisclosed")


@st.cache_data(ttl=600)
def load_bd_enriched() -> pd.DataFrame:
    """bd_deals.csv (99) + canonical/flag columns. All 99 rows retained; the flags
    decide which aggregation includes a row.

    Added columns:
      ta_canon      free-text ta → M&A ta_group bucket (bd_canon_ta)
      phase_canon   free-text phase → ordered stage (bd_canon_phase)
      is_china_out  licensor name contains CJK → Chinese biotech out-licensing
      mnc_buyer_ok  licensee is a real global-MNC inbound buyer (not in BD_LEAGUE_EXCLUDE)
      value_ok      total>0 AND milestone<=total — drops the data-impossible Evaxion row
                    (ms 1184 > total 600) and the total=0 option/collab rows from $-math
    """
    import re

    df = load_bd_report().copy()
    # Out-licensing structure (License-out / Co-Co / NewCo). Default-fill so the page
    # never KeyErrors if an older CSV (pre-structure-column) is loaded.
    if "structure" not in df.columns:
        df["structure"] = "License-out"
    df["structure"] = df["structure"].fillna("License-out").astype(str)
    df["ta_canon"] = df["ta"].map(bd_canon_ta)
    df["phase_canon"] = df["phase"].map(bd_canon_phase)
    up = pd.to_numeric(df["upfront_musd"], errors="coerce")
    ms = pd.to_numeric(df["milestone_musd"], errors="coerce")
    tot = pd.to_numeric(df["total_musd"], errors="coerce")
    df["upfront_musd"], df["milestone_musd"], df["total_musd"] = up, ms, tot
    cjk = re.compile(r"[一-鿿]")
    df["is_china_out"] = df["licensor"].astype(str).map(lambda s: bool(cjk.search(s)))
    df["mnc_buyer_ok"] = ~df["licensee"].astype(str).str.strip().isin(BD_LEAGUE_EXCLUDE)
    df["value_ok"] = tot.notna() & (tot > 0) & (ms.isna() | (ms <= tot))
    return df


def bd_by_licensee(df: pd.DataFrame, top: int = 12) -> pd.DataFrame:
    """MNC buyer league (mnc_buyer_ok only). Ranked by DEAL COUNT — BD headline value
    is milestone-inflated, so one $18.5B deal must not crown a one-deal buyer."""
    sub = df[df["mnc_buyer_ok"]]
    g = (sub.groupby("licensee")
           .agg(n=("asset", "size"), total_bn=("total_musd", lambda x: x.sum() / 1000.0))
           .reset_index().sort_values("n", ascending=False).head(top))
    return g


def bd_by_ta(df: pd.DataFrame) -> pd.DataFrame:
    """By canonical TA, value-weighted (value_ok rows only). Desc by USD bn."""
    sub = df[df["value_ok"]]
    g = (sub.groupby("ta_canon")
           .agg(n=("asset", "size"), total_bn=("total_musd", lambda x: x.sum() / 1000.0))
           .reset_index().sort_values("total_bn", ascending=False))
    return g


def bd_by_phase(df: pd.DataFrame) -> pd.DataFrame:
    """Deal COUNT per canonical phase, ordered Preclinical→Approved→Undisclosed
    (the depth-of-reach view: how early MNCs reach into Chinese pipeline)."""
    g = (df.groupby("phase_canon").agg(n=("asset", "size"))
           .reindex(BD_PHASE_ORDER).fillna(0))
    g["n"] = g["n"].astype(int)
    return g.reset_index()


def bd_by_year(df: pd.DataFrame) -> pd.DataFrame:
    """Deal COUNT per year (value is milestone-inflated; count avoids cross-year distortion)."""
    return (df.groupby("year").agg(n=("asset", "size"))
              .reset_index().sort_values("year"))


# Out-licensing structures, ordered traditional → equity-heavy. Co-Co (co-develop +
# co-commercialize, profit-share) and NewCo (assets dropped into a new co, licensor
# takes equity) are the two "升级" models vs a plain License-out.
BD_STRUCTURE_ORDER = ["License-out", "Co-Co", "NewCo"]


def bd_by_structure(df: pd.DataFrame) -> pd.DataFrame:
    """Deal COUNT (all rows) + announced VALUE (USD bn, value_ok rows only) per
    out-licensing structure, ordered License-out → Co-Co → NewCo. Value is a
    milestone-inflated ceiling, so the headline read should lead with count."""
    n = df.groupby("structure").size()
    v = df[df["value_ok"]].groupby("structure")["total_musd"].sum() / 1000.0
    g = (pd.DataFrame({"n": n, "total_bn": v})
         .reindex(BD_STRUCTURE_ORDER).fillna({"n": 0, "total_bn": 0.0}))
    g["n"] = g["n"].astype(int)
    return g.reset_index().rename(columns={"index": "structure"})


def bd_kpis(df: pd.DataFrame) -> dict:
    """Headline BD KPI bundle. All $-figures use value_ok rows only (excludes total=0
    options + the Evaxion data error). Milestones are CONTINGENT — total is an announced
    ceiling, never realized cash; the page label MUST say 含里程碑/incl. milestones.

    Keys: total_bn, upfront_bn, milestone_bn, med_upfront_pct, china_pct, china_bn,
          biggest (Series|None), top_mnc (Series|None), n_all, n_2025, n_2026.
    """
    val = df[df["value_ok"]]
    total_bn = float(val["total_musd"].sum()) / 1000.0
    ratio = (val["upfront_musd"] / val["total_musd"]).dropna()
    china_bn = float(val[val["is_china_out"]]["total_musd"].sum()) / 1000.0
    lg = bd_by_licensee(df, top=1)
    return {
        "total_bn": total_bn,
        "upfront_bn": float(val["upfront_musd"].sum()) / 1000.0,
        "milestone_bn": float(val["milestone_musd"].sum()) / 1000.0,
        "med_upfront_pct": float(ratio.median()) * 100.0 if len(ratio) else None,
        "china_bn": china_bn,
        "china_pct": china_bn / total_bn * 100.0 if total_bn else None,
        "biggest": val.nlargest(1, "total_musd").iloc[0] if len(val) else None,
        "top_mnc": lg.iloc[0] if len(lg) else None,
        "n_all": len(df),
        "n_2025": int((df["year"] == 2025).sum()),
        "n_2026": int((df["year"] == 2026).sum()),
    }

