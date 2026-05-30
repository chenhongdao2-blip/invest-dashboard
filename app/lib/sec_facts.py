"""SEC company-facts selection & query logic (read-only over data/snapshots.db).

Reads sec_company / sec_kpi_map populated by jobs/fetch_sec_facts.py. Individual
XBRL facts are NOT stored in a flat table (that bloated the committed DB to
600MB+); instead the raw companyfacts JSON lives gzip'd in sec_company.payload_gzip
and is parsed on demand per company by _load_facts() (st.cache_data → parsed once
per ticker per session).

Industry-agnostic: KPI cards are driven by sec_kpi_map with a `domain` layer
(NULL = universal, else per-domain overlay), and each KPI carries a us-gaap +
ifrs-full concept fallback chain so foreign filers (which report under ifrs-full)
don't blank out.

DB reads go through db.query() (mode=ro). Cached functions are language-agnostic
— never call i18n.t() inside a cached function.
"""

from __future__ import annotations

import gzip
import json

import pandas as pd
import streamlit as st

from lib import db

_FACT_COLS = [
    "taxonomy", "concept", "label", "unit", "value", "value_text",
    "start_date", "end_date", "instant", "fy", "fp", "form", "filed", "accession", "frame",
]

# Common us-gaap / ifrs-full XBRL concepts → sell-side Chinese names. Keyed by the
# bare concept (taxonomy-agnostic; collisions across us-gaap/ifrs are rare and the
# CN term is the same anyway). Used to add a 中文名 column to the fact browser in
# Chinese mode. Unknown concepts fall back to "" (raw XBRL tag stays visible).
_CONCEPT_CN: dict[str, str] = {
    # ── income statement ──
    "Revenues": "营业收入",
    "Revenue": "营业收入",
    "RevenueFromContractWithCustomerExcludingAssessedTax": "营业收入(不含税)",
    "RevenueFromContractWithCustomerIncludingAssessedTax": "营业收入(含税)",
    "SalesRevenueNet": "营业收入(净额)",
    "CostOfRevenue": "营业成本",
    "CostOfGoodsAndServicesSold": "营业成本",
    "GrossProfit": "毛利润",
    "OperatingExpenses": "营业费用",
    "ResearchAndDevelopmentExpense": "研发费用",
    "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost": "研发费用(不含外购在研)",
    "SellingGeneralAndAdministrativeExpense": "销售及管理费用",
    "GeneralAndAdministrativeExpense": "管理费用",
    "SellingAndMarketingExpense": "销售费用",
    "OperatingIncomeLoss": "营业利润",
    "ProfitLossFromOperatingActivities": "营业利润",
    "NetIncomeLoss": "归母净利润",
    "ProfitLoss": "净利润",
    "ProfitLossAttributableToOwnersOfParent": "归母净利润",
    "IncomeTaxExpenseBenefit": "所得税费用",
    "InterestExpense": "利息费用",
    "EarningsPerShareBasic": "基本每股收益",
    "EarningsPerShareDiluted": "稀释每股收益",
    "BasicEarningsLossPerShare": "基本每股收益",
    "DilutedEarningsLossPerShare": "稀释每股收益",
    "WeightedAverageNumberOfSharesOutstandingBasic": "加权平均股本(基本)",
    "WeightedAverageNumberOfDilutedSharesOutstanding": "加权平均股本(稀释)",
    # ── balance sheet ──
    "Assets": "总资产",
    "AssetsCurrent": "流动资产",
    "CashAndCashEquivalentsAtCarryingValue": "现金及现金等价物",
    "CashAndCashEquivalents": "现金及现金等价物",
    "ShortTermInvestments": "短期投资",
    "MarketableSecuritiesCurrent": "流动性可售证券",
    "AccountsReceivableNetCurrent": "应收账款净额",
    "InventoryNet": "存货净额",
    "Goodwill": "商誉",
    "IntangibleAssetsNetExcludingGoodwill": "无形资产(不含商誉)",
    "PropertyPlantAndEquipmentNet": "固定资产净额",
    "Liabilities": "总负债",
    "LiabilitiesCurrent": "流动负债",
    "AccountsPayableCurrent": "应付账款",
    "LongTermDebt": "长期债务",
    "LongTermDebtNoncurrent": "长期债务(非流动)",
    "StockholdersEquity": "股东权益",
    "Equity": "股东权益",
    "EquityAttributableToOwnersOfParent": "归母股东权益",
    "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest": "股东权益(含少数股东)",
    "RetainedEarningsAccumulatedDeficit": "留存收益/累计亏损",
    "CommonStockSharesOutstanding": "流通普通股数",
    # ── cash flow ──
    "NetCashProvidedByUsedInOperatingActivities": "经营活动现金流净额",
    "NetCashProvidedByUsedInInvestingActivities": "投资活动现金流净额",
    "NetCashProvidedByUsedInFinancingActivities": "筹资活动现金流净额",
    "PaymentsToAcquirePropertyPlantAndEquipment": "资本开支(购建固定资产)",
    "ShareBasedCompensation": "股份支付",
    "DepreciationDepletionAndAmortization": "折旧及摊销",
    "DividendsCommonStock": "普通股股息",
    # ── dei ──
    "EntityCommonStockSharesOutstanding": "流通普通股数(dei)",
}


def concept_cn(concept: str) -> str:
    """Chinese name for a known XBRL concept, else '' (raw tag stays visible)."""
    return _CONCEPT_CN.get(concept, "")


@st.cache_data(ttl=300)
def _load_facts(ticker: str) -> pd.DataFrame:
    """Parse a company's gzip'd companyfacts JSON into a flat fact DataFrame.

    Columns match the old sec_fact schema so downstream logic is unchanged.
    Cached per ticker — decompress+parse (~1MB JSON → ~20k rows) runs once.
    Returns an empty (typed) frame if the payload is missing/unparseable.
    """
    df0 = db.query(
        "SELECT payload_gzip FROM sec_company WHERE ticker = ? AND sec_status = 'ok'",
        (ticker,),
    )
    if df0.empty or df0.iloc[0]["payload_gzip"] is None:
        return pd.DataFrame(columns=_FACT_COLS)
    try:
        cf = json.loads(gzip.decompress(df0.iloc[0]["payload_gzip"]))
    except (OSError, ValueError, TypeError):
        return pd.DataFrame(columns=_FACT_COLS)

    rows: list[tuple] = []
    for taxonomy, concepts in (cf.get("facts") or {}).items():
        for concept, cdata in concepts.items():
            label = cdata.get("label")
            for unit, items in (cdata.get("units") or {}).items():
                for it in items:
                    end = it.get("end")
                    if not end:
                        continue
                    start = it.get("start") or ""
                    val = it.get("val")
                    is_num = isinstance(val, (int, float))
                    rows.append((
                        taxonomy, concept, label, unit,
                        float(val) if is_num else None,
                        None if is_num else (None if val is None else str(val)),
                        start, end, 0 if start else 1,
                        it.get("fy"), it.get("fp"), it.get("form"),
                        it.get("filed"), it.get("accn", ""), it.get("frame", "") or "",
                    ))
    if not rows:
        return pd.DataFrame(columns=_FACT_COLS)
    return pd.DataFrame(rows, columns=_FACT_COLS)

# Form families
_ANNUAL_FORMS = ("10-K", "10-K/A", "20-F", "20-F/A", "40-F", "40-F/A")
_AMEND_SUFFIX = "/A"


# ──────────────────────────────────────────────────────────────────────────
# KPI map
# ──────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=600)
def kpis_for_domain(domain: str | None) -> list[dict]:
    """KPIs to show for a ticker's domain: universal (domain IS NULL) + overlay.

    Returns list of dicts ordered by display_order. concepts is parsed to a list
    of "taxonomy:concept" strings (priority order).
    """
    df = db.query(
        """SELECT kpi_key, display_order, domain, label_en, label_cn,
                  concepts_json, period_type, unit_hint
           FROM sec_kpi_map
           WHERE domain IS NULL OR domain = ?
           ORDER BY display_order""",
        (domain or "",),
    )
    out: list[dict] = []
    for _, r in df.iterrows():
        out.append({
            "kpi_key": r["kpi_key"],
            "display_order": int(r["display_order"]),
            "domain": r["domain"],
            "label_en": r["label_en"],
            "label_cn": r["label_cn"],
            "concepts": json.loads(r["concepts_json"]),
            "period_type": r["period_type"],
            "unit_hint": r["unit_hint"],
        })
    return out


@st.cache_data(ttl=600)
def _kpi_row(kpi_key: str) -> dict | None:
    df = db.query(
        "SELECT kpi_key, label_en, label_cn, concepts_json, period_type, unit_hint "
        "FROM sec_kpi_map WHERE kpi_key = ?",
        (kpi_key,),
    )
    if df.empty:
        return None
    r = df.iloc[0]
    return {
        "kpi_key": r["kpi_key"], "label_en": r["label_en"], "label_cn": r["label_cn"],
        "concepts": json.loads(r["concepts_json"]),
        "period_type": r["period_type"], "unit_hint": r["unit_hint"],
    }


# ──────────────────────────────────────────────────────────────────────────
# Company status / pool
# ──────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def company_status(ticker: str) -> dict | None:
    """sec_company row for a ticker (None if never attempted)."""
    df = db.query(
        """SELECT ticker, cik, cik10, entity_name, taxonomy_primary, sec_status,
                  fetched_at, latest_filed, facts_count, last_error
           FROM sec_company WHERE ticker = ?""",
        (ticker,),
    )
    return None if df.empty else df.iloc[0].to_dict()


@st.cache_data(ttl=300)
def us_pool() -> pd.DataFrame:
    """US tickers in the universe joined with their SEC fetch status (one row/ticker)."""
    return db.query(
        """SELECT um.ticker,
                  MAX(um.name_cn) AS name_cn, MAX(um.name_en) AS name_en,
                  MAX(um.domain)  AS domain,
                  c.sec_status, c.taxonomy_primary, c.fetched_at,
                  c.latest_filed, c.facts_count
           FROM universe_member um
           LEFT JOIN sec_company c ON c.ticker = um.ticker
           WHERE um.region = 'US'
           GROUP BY um.ticker
           ORDER BY um.ticker"""
    )


# ──────────────────────────────────────────────────────────────────────────
# Fact selection
# ──────────────────────────────────────────────────────────────────────────
def _facts(ticker: str, taxonomy: str, concept: str, unit: str | None) -> pd.DataFrame:
    """Facts for one (taxonomy, concept[, unit]) — filtered from the parsed payload."""
    df = _load_facts(ticker)
    if df.empty:
        return df
    m = (df["taxonomy"] == taxonomy) & (df["concept"] == concept)
    if unit:
        m &= df["unit"] == unit
    return df[m]


def _filter_period(df: pd.DataFrame, period_type: str, period: str) -> pd.DataFrame:
    """period ∈ {'annual','quarterly'}; period_type ∈ {'duration','instant'}."""
    if df.empty:
        return df
    d = df.copy()
    if period_type == "duration":
        d = d[d["start_date"].astype(str) != ""]
        span = (pd.to_datetime(d["end_date"]) - pd.to_datetime(d["start_date"])).dt.days
        if period == "annual":
            sel = (d["fp"] == "FY") | (span >= 350)
        else:  # quarterly
            sel = span <= 100
        d = d[sel]
    else:  # instant (balance-sheet point-in-time)
        d = d[d["start_date"].astype(str) == ""]
        if period == "annual":
            ann = d[d["form"].isin(_ANNUAL_FORMS)]
            if not ann.empty:
                d = ann
    return d


def _rank(df: pd.DataFrame) -> pd.DataFrame:
    """Latest fiscal period first; within a period, most-recently-filed (amendment) wins."""
    if df.empty:
        return df
    return df.sort_values(["end_date", "filed"], ascending=[False, False])


def pick_kpi_fact(ticker: str, kpi_key: str, period: str = "annual") -> dict | None:
    """Best fact for a KPI card across the taxonomy:concept fallback chain.

    Collects the best (latest) fact from EVERY concept in the chain, then picks the
    globally most-recent period. This auto-handles us-gaap concept migrations (e.g.
    LLY moved ResearchAndDevelopmentExpense → ...ExcludingAcquiredInProcessCost): a
    "first concept with any data" rule would lock onto the stale predecessor.

    Ranking: latest end_date wins; tie → lower fallback_rank (canonical concept)
    → most-recently filed. fallback_rank 0 = primary concept; is_fallback flags
    that a non-primary concept supplied the value (surface a badge in the UI).
    """
    kpi = _kpi_row(kpi_key)
    if not kpi:
        return None
    candidates: list[tuple] = []  # (end_date, rank, filed, row)
    for rank, taxconcept in enumerate(kpi["concepts"]):
        tax, _, concept = taxconcept.partition(":")
        df = _facts(ticker, tax, concept, kpi["unit_hint"])
        df = _filter_period(df, kpi["period_type"], period)
        df = _rank(df)
        if df.empty:
            continue
        r = df.iloc[0]
        candidates.append((str(r["end_date"]), rank, str(r["filed"] or ""), r))
    if not candidates:
        return None
    # latest end_date, then canonical concept (lower rank), then latest filed
    candidates.sort(key=lambda c: (c[0], -c[1], c[2]), reverse=True)
    end_date, rank, _, r = candidates[0]
    return {
        "kpi_key": kpi_key,
        "value": None if pd.isna(r["value"]) else float(r["value"]),
        "taxonomy": r["taxonomy"], "concept": r["concept"], "label": r["label"],
        "unit": r["unit"], "form": r["form"],
        "fy": None if pd.isna(r["fy"]) else int(r["fy"]), "fp": r["fp"],
        "start_date": r["start_date"], "end_date": r["end_date"],
        "filed": r["filed"], "accession": r["accession"],
        "fallback_rank": rank, "is_fallback": rank > 0,
    }


# ──────────────────────────────────────────────────────────────────────────
# Concept time-series (with QoQ / YoY)
# ──────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def concept_timeseries(
    ticker: str, taxonomy: str, concept: str, unit: str | None, freq: str = "quarterly"
) -> pd.DataFrame:
    """Time-series of one concept across filings, deduped to one value per period end.

    freq ∈ {'annual','quarterly'}. Adds qoq/yoy pct columns:
      - quarterly: qoq = vs prior period, yoy = vs 4 periods ago
      - annual:    yoy = vs prior period (qoq omitted)
    """
    df = _facts(ticker, taxonomy, concept, unit)
    if df.empty:
        return df
    # A concept is either a flow (duration) or a stock (instant). Decide by the
    # majority of rows rather than guessing from row 0 (payload order is arbitrary).
    period_type = "instant" if (df["instant"] == 1).mean() >= 0.5 else "duration"
    df = _filter_period(df, period_type, freq)
    if df.empty:
        return df
    # one value per end_date: keep most-recently-filed (amendment supersedes)
    df = df.sort_values(["end_date", "filed"], ascending=[True, False])
    df = df.drop_duplicates(subset=["end_date"], keep="first").reset_index(drop=True)
    df = df[["end_date", "value", "fy", "fp", "form", "unit"]].copy()
    df["yoy"] = df["value"].pct_change(4 if freq == "quarterly" else 1) * 100
    if freq == "quarterly":
        df["qoq"] = df["value"].pct_change(1) * 100
    return df


@st.cache_data(ttl=300)
def kpi_timeseries(ticker: str, kpi_key: str, freq: str = "annual") -> tuple[pd.DataFrame, str]:
    """Time-series for a KPI, choosing the concept in its fallback chain with the
    LONGEST history (most distinct period-ends) so concept migrations don't truncate
    the trend. Returns (df[end_date,value,yoy(,qoq)], concept). Empty df if no data.

    SEC / US-GAAP data only — reads the committed snapshots.db (works offline)."""
    kpi = _kpi_row(kpi_key)
    if not kpi:
        return pd.DataFrame(), ""
    # Prefer the concept whose data is MOST RECENT (latest end_date), then longest.
    # A "most period-ends" rule wrongly picks a DEPRECATED concept: e.g. revenue's
    # 'Revenues' (heavily used pre-2018, many old period-ends) would beat the current
    # 'RevenueFromContractWithCustomer…' and render a stale 2017 series.
    best = pd.DataFrame()
    best_concept = ""
    best_key: tuple[str, int] | None = None
    for taxconcept in kpi["concepts"]:
        tax, _, concept = taxconcept.partition(":")
        ts = concept_timeseries(ticker, tax, concept, kpi["unit_hint"], freq=freq)
        tsv = ts.dropna(subset=["value"]) if not ts.empty else ts
        if tsv.empty:
            continue
        key = (str(tsv["end_date"].max()), len(tsv))
        if best_key is None or key > best_key:
            best, best_concept, best_key = ts, concept, key
    return best, best_concept


# ──────────────────────────────────────────────────────────────────────────
# Full fact browser
# ──────────────────────────────────────────────────────────────────────────
def all_facts(ticker: str) -> pd.DataFrame:
    """All facts for a ticker (drives the filterable browser table)."""
    df = _load_facts(ticker)
    if df.empty:
        return df
    return df.sort_values(["filed", "concept"], ascending=[False, True]).reset_index(drop=True)


# ──────────────────────────────────────────────────────────────────────────
# Comp table (multi-ticker × KPI, latest annual per ticker)
# ──────────────────────────────────────────────────────────────────────────
def comp_table(tickers: list[str], kpi_keys: list[str], lang: str = "en") -> pd.DataFrame:
    """Multi-ticker comparable table: rows = tickers, cols = KPIs (latest annual).

    Period ends differ across filers, so a 'FY End' column is included for honesty.
    Values are returned numeric (formatting is the caller's job). lang picks label.
    """
    label_field = "label_cn" if lang == "zh" else "label_en"
    kmeta = {k["kpi_key"]: k for k in (_kpi_row(k) or {} for k in kpi_keys) if k}
    cols = [kmeta[k][label_field] for k in kpi_keys if k in kmeta]
    out_rows: list[dict] = []
    for t in tickers:
        row: dict = {"Ticker": t}
        ends: list[str] = []
        for k in kpi_keys:
            if k not in kmeta:
                continue
            f = pick_kpi_fact(t, k, period="annual")
            row[kmeta[k][label_field]] = None if f is None else f["value"]
            if f and f.get("end_date"):
                ends.append(f["end_date"])
        row["FY End"] = max(ends) if ends else None
        out_rows.append(row)
    return pd.DataFrame(out_rows, columns=["Ticker", *cols, "FY End"])
