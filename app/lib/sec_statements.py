"""三大报表摘要 (Financial Statements summary) — shared by both SEC Facts pages.

Builds an Excel-model-style matrix (years as columns, line items as rows) from
SEC XBRL company facts, with a curated line-item set + per-line tag fallback
chains (different filers tag the same line differently). Periods run old→new
(left→old, right→new) per user preference.

Annual mode keys periods by fiscal-year-end year (int). Quarterly mode keys by
"YYYYQn" (str) derived from end_date + fp. YoY in quarterly mode compares the
same quarter one year earlier (4 periods back); CAGR is annual-only.

Annual derived-metrics table also appends a peer-median comparison block for the
latest available year (consumes sf.peer_medians).

Design source: docs/plans/sec-page-redesign.md §2. Offline: reads only the
cached DB via sec_facts; no network.
"""

from __future__ import annotations

import pandas as pd

from lib import format as fmt
from lib import sec_facts as sf
from lib import theme
from lib import ui


# ── value formatter (unit-aware; mirrors the pages' _fmt_val) ──
def _fmt_val(v, unit: str) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    unit = unit or ""
    if "shares" in unit and "/" in unit:          # USD/shares → EPS (per-share)
        return f"${v:,.2f}"
    if unit == "USD" or unit.startswith("USD"):
        return fmt.fmt_money_b(v)
    if "shares" in unit:                          # raw share counts
        return fmt.fmt_money_b(v).lstrip("$")
    return f"{v:,.2f}"


# ── line-item config: key, cn, en, unit, tags (priority), [compute] ──
# compute=(key_a, op, key_b) used only when no tag returns data.
_USD = "USD"
_EPS = "USD/shares"
_SH = "shares"

INCOME_ROWS = [
    {"key": "revenue", "cn": "营业收入", "en": "Revenue", "unit": _USD,
     "tags": ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues",
              "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueNet",
              # ifrs-full equivalents (foreign filers: TSM/ASX/AZN/NVS/GSK…)
              "Revenue", "RevenueFromContractsWithCustomers"]},
    {"key": "cogs", "cn": "营业成本", "en": "Cost of Revenue", "unit": _USD,
     "tags": ["CostOfGoodsAndServicesSold", "CostOfRevenue", "CostOfGoodsSold", "CostOfServices",
              # ifrs-full
              "CostOfSales"]},
    {"key": "gross_profit", "cn": "毛利润", "en": "Gross Profit", "unit": _USD,
     "tags": ["GrossProfit"], "compute": ("revenue", "-", "cogs")},
    {"key": "rnd", "cn": "研发费用", "en": "R&D Expense", "unit": _USD,
     "tags": ["ResearchAndDevelopmentExpense"]},
    {"key": "sga", "cn": "销售及管理费用", "en": "SG&A", "unit": _USD,
     "tags": ["SellingGeneralAndAdministrativeExpense", "GeneralAndAdministrativeExpense"]},
    {"key": "opex", "cn": "营业费用合计", "en": "Total Operating Expenses", "unit": _USD,
     "tags": ["OperatingExpenses", "CostsAndExpenses"]},
    {"key": "operating_income", "cn": "营业利润", "en": "Operating Income", "unit": _USD,
     "tags": ["OperatingIncomeLoss",
              # ifrs-full
              "ProfitLossFromOperatingActivities"]},
    {"key": "interest", "cn": "利息费用", "en": "Interest Expense", "unit": _USD,
     "tags": ["InterestExpense", "InterestExpenseNonoperating", "InterestIncomeExpenseNet"]},
    {"key": "pretax", "cn": "税前利润", "en": "Pretax Income", "unit": _USD,
     "tags": ["IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
              "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments"]},
    {"key": "tax", "cn": "所得税费用", "en": "Income Tax Expense", "unit": _USD,
     "tags": ["IncomeTaxExpenseBenefit"]},
    {"key": "net_income", "cn": "净利润", "en": "Net Income", "unit": _USD,
     "tags": ["NetIncomeLoss", "ProfitLoss", "NetIncomeLossAvailableToCommonStockholdersBasic",
              # ifrs-full (ProfitLoss already covers most IFRS filers; add
              # owner-attributable variant as a fallback)
              "ProfitLossAttributableToOwnersOfParent"]},
    {"key": "eps_basic", "cn": "基本每股收益", "en": "Basic EPS", "unit": _EPS,
     "tags": ["EarningsPerShareBasic"]},
    {"key": "eps_diluted", "cn": "稀释每股收益", "en": "Diluted EPS", "unit": _EPS,
     "tags": ["EarningsPerShareDiluted"]},
    {"key": "shares_diluted", "cn": "稀释加权平均股本", "en": "Diluted Wtd Avg Shares", "unit": _SH,
     "tags": ["WeightedAverageNumberOfDilutedSharesOutstanding", "WeightedAverageNumberOfSharesOutstandingBasic"]},
]

BALANCE_ROWS = [
    {"key": "cash", "cn": "现金及现金等价物", "en": "Cash & Equivalents", "unit": _USD,
     "tags": ["CashAndCashEquivalentsAtCarryingValue",
              "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"]},
    {"key": "sti", "cn": "短期投资", "en": "Short-term Investments", "unit": _USD,
     "tags": ["ShortTermInvestments", "MarketableSecuritiesCurrent"]},
    {"key": "ar", "cn": "应收账款净额", "en": "Accounts Receivable, Net", "unit": _USD,
     "tags": ["AccountsReceivableNetCurrent", "ReceivablesNetCurrent"]},
    {"key": "inventory", "cn": "存货", "en": "Inventory", "unit": _USD,
     "tags": ["InventoryNet", "InventoryFinishedGoodsNetOfReserves"]},
    {"key": "current_assets", "cn": "流动资产合计", "en": "Total Current Assets", "unit": _USD,
     "tags": ["AssetsCurrent"]},
    {"key": "ppe", "cn": "固定资产净额", "en": "PP&E, Net", "unit": _USD,
     "tags": ["PropertyPlantAndEquipmentNet"]},
    {"key": "goodwill", "cn": "商誉", "en": "Goodwill", "unit": _USD,
     "tags": ["Goodwill"]},
    {"key": "intangibles", "cn": "无形资产", "en": "Intangible Assets", "unit": _USD,
     "tags": ["IntangibleAssetsNetExcludingGoodwill", "FiniteLivedIntangibleAssetsNet"]},
    {"key": "total_assets", "cn": "总资产", "en": "Total Assets", "unit": _USD,
     "tags": ["Assets"]},  # ifrs-full also tags total assets as "Assets"
    {"key": "ap", "cn": "应付账款", "en": "Accounts Payable", "unit": _USD,
     "tags": ["AccountsPayableCurrent", "AccountsPayableAndAccruedLiabilitiesCurrent"]},
    {"key": "current_liabilities", "cn": "流动负债合计", "en": "Total Current Liabilities", "unit": _USD,
     "tags": ["LiabilitiesCurrent"]},
    {"key": "lt_debt", "cn": "长期借款", "en": "Long-term Debt", "unit": _USD,
     "tags": ["LongTermDebtNoncurrent", "LongTermDebt", "LongTermDebtAndCapitalLeaseObligations"]},
    {"key": "total_liabilities", "cn": "总负债", "en": "Total Liabilities", "unit": _USD,
     "tags": ["Liabilities"]},  # ifrs-full also tags total liabilities as "Liabilities"
    {"key": "equity", "cn": "股东权益合计", "en": "Total Stockholders' Equity", "unit": _USD,
     "tags": ["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
              # ifrs-full
              "Equity", "EquityAttributableToOwnersOfParent"]},
    {"key": "shares_out", "cn": "流通股本", "en": "Shares Outstanding", "unit": _SH,
     "tags": ["CommonStockSharesOutstanding", "CommonStockSharesIssued", "EntityCommonStockSharesOutstanding"]},
]

CASHFLOW_ROWS = [
    {"key": "ocf", "cn": "经营活动现金流净额", "en": "Net Cash from Operations", "unit": _USD,
     "tags": ["NetCashProvidedByUsedInOperatingActivities",
              "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations",
              # ifrs-full
              "CashFlowsFromUsedInOperatingActivities"]},
    {"key": "da", "cn": "折旧及摊销", "en": "Depreciation & Amortization", "unit": _USD,
     "tags": ["DepreciationDepletionAndAmortization", "DepreciationAmortizationAndAccretionNet",
              "DepreciationAndAmortization"]},
    {"key": "sbc", "cn": "股权激励费用", "en": "Stock-based Compensation", "unit": _USD,
     "tags": ["ShareBasedCompensation", "AllocatedShareBasedCompensationExpense"]},
    {"key": "icf", "cn": "投资活动现金流净额", "en": "Net Cash from Investing", "unit": _USD,
     "tags": ["NetCashProvidedByUsedInInvestingActivities",
              "NetCashProvidedByUsedInInvestingActivitiesContinuingOperations"]},
    {"key": "capex", "cn": "资本开支", "en": "Capital Expenditures", "unit": _USD,
     "tags": ["PaymentsToAcquirePropertyPlantAndEquipment", "PaymentsToAcquireProductiveAssets",
              # ifrs-full (capex tag varies across IFRS filers; try the common ones)
              "PurchaseOfPropertyPlantAndEquipment",
              "PurchaseOfPropertyPlantAndEquipmentIntangibleAssetsAndInvestmentProperty"]},
    {"key": "fcf", "cn": "自由现金流", "en": "Free Cash Flow", "unit": _USD,
     "tags": [], "compute": ("ocf", "-", "capex")},
    {"key": "fcf2", "cn": "融资活动现金流净额", "en": "Net Cash from Financing", "unit": _USD,
     "tags": ["NetCashProvidedByUsedInFinancingActivities",
              "NetCashProvidedByUsedInFinancingActivitiesContinuingOperations"]},
    {"key": "buyback", "cn": "股票回购", "en": "Share Repurchases", "unit": _USD,
     "tags": ["PaymentsForRepurchaseOfCommonStock"]},
    {"key": "dividends", "cn": "现金分红", "en": "Dividends Paid", "unit": _USD,
     "tags": ["PaymentsOfDividendsCommonStock", "PaymentsOfDividends"]},
    {"key": "debt_issued", "cn": "债务发行", "en": "Debt Issued", "unit": _USD,
     "tags": ["ProceedsFromIssuanceOfLongTermDebt", "ProceedsFromIssuanceOfDebt"]},
    {"key": "debt_repaid", "cn": "债务偿还", "en": "Debt Repaid", "unit": _USD,
     "tags": ["RepaymentsOfLongTermDebt", "RepaymentsOfDebt"]},
    {"key": "net_change_cash", "cn": "现金净增加额", "en": "Net Change in Cash", "unit": _USD,
     "tags": ["CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect",
              "CashAndCashEquivalentsPeriodIncreaseDecrease"]},
]


# ── period keying ──
# Annual:    period key = int(end_date[:4])                e.g. 2023
# Quarterly: period key = "YYYYQn" (str) from end_date+fp  e.g. "2024Q1"
_MONTH_TO_Q = {3: 1, 6: 2, 9: 3, 12: 4}


def _period_key(end_date, fp, freq: str):
    """Return the period key for a row, or None if it can't be derived."""
    ed = str(end_date) if end_date is not None else ""
    if len(ed) < 4 or not ed[:4].isdigit():
        return None
    year = int(ed[:4])
    if freq != "quarterly":
        return year
    # quarterly: derive quarter from fp, falling back to end_date month
    q = None
    fps = str(fp).strip().upper() if fp is not None else ""
    if fps in ("Q1", "Q2", "Q3", "Q4"):
        q = int(fps[1])
    elif fps == "FY":
        q = 4
    if q is None:
        try:
            mo = int(ed[5:7])
        except (ValueError, IndexError):
            mo = 0
        q = _MONTH_TO_Q.get(mo)
    if q is None:
        return None
    return f"{year}Q{q}"


def _period_label(period, freq: str) -> str:
    """Column header label. Annual: '2023'. Quarterly: '24Q1'."""
    if freq != "quarterly":
        return str(period)
    s = str(period)            # "YYYYQn"
    if "Q" in s:
        yr, q = s.split("Q", 1)
        return f"{yr[-2:]}Qn".replace("Qn", f"Q{q}")
    return s


def _period_sort_key(period, freq: str):
    """Chronological sort key (handles both int years and 'YYYYQn' strings)."""
    if freq != "quarterly":
        return (int(period), 0)
    s = str(period)
    if "Q" in s:
        yr, q = s.split("Q", 1)
        try:
            return (int(yr), int(q))
        except ValueError:
            return (0, 0)
    return (0, 0)


# ── series extraction ──
def _row_series(ticker: str, tax: str, tags: list[str], unit: str, freq: str) -> dict:
    """First non-empty tag → {period_key: value}. period_key per _period_key()."""
    for tag in tags:
        ts = sf.concept_timeseries(ticker, tax, tag, unit, freq)
        if ts is None or ts.empty:
            continue
        out: dict = {}
        for _, row in ts.iterrows():
            pk = _period_key(row.get("end_date"), row.get("fp"), freq)
            if pk is None:
                continue
            val = row.get("value")
            if pd.notna(val):
                out[pk] = float(val)
        if out:
            return out
    return {}


def _section_series(ticker: str, tax: str, rows: list[dict], freq: str,
                    monetary_unit: str | None = None) -> dict:
    """Per-key {period: value} for a section of rows, reusing _row_series.

    monetary_unit: when given (e.g. "TWD"), monetary rows (unit == _USD) are
    fetched in THAT currency instead of forcing USD. This is what makes the
    peer-median build currency-agnostic: foreign IFRS filers (TSM/ASX report in
    TWD, GSK in GBP) report monetary facts only in their local currency, so a
    hardcoded USD filter returns nothing. The 6 derived metrics are RATIOS
    (numerator/denominator in the SAME currency) → unitless → comparable across
    filers with no FX conversion. Non-monetary rows (shares/EPS) are unaffected.
    """
    by_key: dict = {}
    for r in rows:
        unit = r["unit"]
        if monetary_unit and unit == _USD:
            unit = monetary_unit
        by_key[r["key"]] = _row_series(ticker, tax, r["tags"], unit, freq)
    # compute rows (when tag chain returned nothing)
    for r in rows:
        if by_key.get(r["key"]) or "compute" not in r:
            continue
        a, op, b = r["compute"]
        sa, sb = by_key.get(a, {}), by_key.get(b, {})
        prds = set(sa) & set(sb)
        by_key[r["key"]] = {p: (sa[p] - sb[p] if op == "-" else sa[p] + sb[p]) for p in prds}
    return by_key


# Units that are NOT a reporting currency (skip when detecting dominant currency).
_NON_CCY_UNIT_PAT = "pure|shares|employee|option|/|-|warrant|item|segment|year|day|rate|pct|percent"


def dominant_monetary_unit(ticker: str, tax: str) -> str | None:
    """Most common reporting CURRENCY unit for a ticker under one taxonomy.

    Inspects all_facts: among that taxonomy's monetary facts (excluding pure /
    shares / per-share / fx-pair / count units), returns the most frequent unit
    (e.g. 'TWD' for TSM, 'GBP' for GSK, 'USD' for a domestic filer or AZN/NVS).
    Returns None if no monetary unit can be determined (caller falls back to USD).
    Used by the peer-median build to fetch each peer's ratios in its OWN currency.
    """
    af = sf.all_facts(ticker)
    if af is None or af.empty or "unit" not in af.columns:
        return None
    sub = af
    if "taxonomy" in af.columns:
        tsub = af[af["taxonomy"] == tax]
        if not tsub.empty:
            sub = tsub
    u = sub["unit"].astype(str)
    mon = sub[~u.str.contains(_NON_CCY_UNIT_PAT, case=False, regex=True, na=False)]
    if mon.empty:
        return None
    vc = mon["unit"].astype(str).value_counts()
    return None if vc.empty else str(vc.index[0])


def _yoy(ordered: list) -> float | None:
    """YoY across adjacent positions in the ordered period list (annual mode)."""
    v = [x for x in ordered if x is not None]
    if len(v) < 2 or not v[-2]:
        return None
    return (v[-1] - v[-2]) / abs(v[-2]) * 100


def _yoy_quarterly(series: dict, periods: list) -> float | None:
    """Quarterly YoY: latest available period vs the same quarter 1 year prior."""
    # walk newest→oldest, find a period with both itself and its -4Q counterpart
    for p in reversed(periods):
        cur = series.get(p)
        if cur is None:
            continue
        s = str(p)
        if "Q" not in s:
            continue
        yr, q = s.split("Q", 1)
        try:
            prior = f"{int(yr) - 1}Q{int(q)}"
        except ValueError:
            continue
        prev = series.get(prior)
        if prev is not None and prev != 0:
            return (cur - prev) / abs(prev) * 100
        # -4Q counterpart missing for THIS quarter → fall through to the next-newest
        # quarter instead of killing the whole column (bug fix: was `return None`).
        continue
    return None


def _cagr(series: dict, periods: list) -> float | None:
    """Annual-only CAGR across the period span."""
    pts = [(p, series[p]) for p in periods if series.get(p) is not None]
    if len(pts) < 2:
        return None
    (p0, v0), (p1, v1) = pts[0], pts[-1]
    n = int(p1) - int(p0)
    if n <= 0 or v0 is None or v1 is None or v0 <= 0 or v1 <= 0:
        return None
    return ((v1 / v0) ** (1 / n) - 1) * 100


def _collect_periods(maps: list, freq: str, periods: int) -> list:
    """Union of all period keys across maps, chronological, last `periods` kept."""
    allp = {p for m in maps for s in m.values() for p in s}
    if not allp:
        return []
    ordered = sorted(allp, key=lambda p: _period_sort_key(p, freq))
    return ordered[-periods:]


def _matrix_df(rows: list[dict], by_key: dict, periods: list, freq: str,
               prefer_cn: bool, yoy_l: str, cagr_l: str) -> pd.DataFrame:
    recs, idx = [], []
    is_q = freq == "quarterly"
    for r in rows:
        s = by_key.get(r["key"], {})
        if not s:                              # hide all-empty rows
            continue
        idx.append(r["cn"] if prefer_cn else r["en"])
        rec = {_period_label(p, freq): (_fmt_val(s.get(p), r["unit"]) if s.get(p) is not None else "—")
               for p in periods}
        ordered = [s.get(p) for p in periods]
        rec[yoy_l] = _yoy_quarterly(s, periods) if is_q else _yoy(ordered)
        if not is_q:
            rec[cagr_l] = _cagr(s, periods)
        recs.append(rec)
    if not recs:
        return pd.DataFrame()
    return pd.DataFrame(recs, index=pd.Index(idx))


def _render_one(title: str, rows: list[dict], by_key: dict, periods: list, freq: str,
                prefer_cn: bool, yoy_l: str, cagr_l: str) -> bool:
    df = _matrix_df(rows, by_key, periods, freq, prefer_cn, yoy_l, cagr_l)
    if df.empty:
        return False
    is_q = freq == "quarterly"
    labels = [_period_label(p, freq) for p in periods]
    pct = [yoy_l] if is_q else [yoy_l, cagr_l]
    theme.section_header(title)
    ui.render_html_table(
        df,
        right_text_cols=labels,
        pct_cols=pct,
        index_label=("科目" if prefer_cn else "Line Item"),
        height=560,
    )
    return True


# Derived-ratio definitions, in the FIXED order the backend peer_medians keys use:
# [gross_margin, operating_margin, net_margin, fcf_margin, roe, debt_to_assets]
_DERIVED_METRIC_KEYS = [
    "gross_margin", "operating_margin", "net_margin", "fcf_margin", "roe", "debt_to_assets",
]


def _derived_metrics(inc, bal, cf, periods: list):
    """Return ordered list of (cn, en, metric_key, {period: pct}). Order is fixed
    to align with sf.peer_medians metric keys."""
    rev = inc.get("revenue", {})

    def ratio(num_key, num_map, den_key, den_map):
        out = {}
        for p in periods:
            n, d = num_map.get(num_key, {}).get(p), den_map.get(den_key, {}).get(p)
            out[p] = (n / d * 100) if (n is not None and d not in (None, 0)) else None
        return out

    def margin(num_key, src):
        out = {}
        for p in periods:
            n, d = src.get(num_key, {}).get(p), rev.get(p)
            out[p] = (n / d * 100) if (n is not None and d not in (None, 0)) else None
        return out

    fcf_m = {}
    for p in periods:
        f, d = cf.get("fcf", {}).get(p), rev.get(p)
        fcf_m[p] = (f / d * 100) if (f is not None and d not in (None, 0)) else None

    return [
        ("毛利率", "Gross Margin", "gross_margin", margin("gross_profit", inc)),
        ("营业利润率", "Operating Margin", "operating_margin", margin("operating_income", inc)),
        ("净利率", "Net Margin", "net_margin", margin("net_income", inc)),
        ("自由现金流利润率", "FCF Margin", "fcf_margin", fcf_m),
        ("净资产收益率(ROE)", "ROE", "roe", ratio("net_income", inc, "equity", bal)),
        ("资产负债率", "Debt-to-Assets", "debt_to_assets", ratio("total_liabilities", bal, "total_assets", bal)),
    ]


def _derived_df(inc, bal, cf, periods: list, freq: str, prefer_cn: bool) -> pd.DataFrame:
    metrics = _derived_metrics(inc, bal, cf, periods)
    recs, idx = [], []
    for cn, en, _mk, vals in metrics:
        if not any(v is not None for v in vals.values()):
            continue
        idx.append(cn if prefer_cn else en)
        recs.append({_period_label(p, freq): vals.get(p) for p in periods})
    if not recs:
        return pd.DataFrame()
    return pd.DataFrame(recs, index=pd.Index(idx))


# Minimum peer count for a peer-median to be shown (DECISION 2). Below this the
# median is dominated by self / 1-2 names → misleading; we suppress it.
_MIN_PEER_N = 3


def _peer_median_for_year(peer_series: dict, year: int):
    """Lookup a peer value for an int year, tolerating int- or str-keyed maps."""
    if not peer_series:
        return None
    if year in peer_series:
        return peer_series[year]
    if str(year) in peer_series:
        return peer_series[str(year)]
    return None


def _peer_compare_df(inc, bal, cf, periods: list, prefer_cn: bool, ticker: str, domain: str):
    """Annual-only peer-median comparison for the LATEST available year per metric.

    DECISION 2 (n<3 guard): a metric's peer-median / vs-peer cells are shown ONLY
    when that metric+year has >=3 disclosing peers; otherwise both render as "—"
    (the self value still shows). The per-metric n is surfaced in the caption.

    Returns (df, sector_used, n_peers, n_by_metric) or (None, ...) if no peer
    data at all. n_by_metric maps the displayed row label → the peer n that
    backed it (or 0 when suppressed/absent), for the caption.
    """
    pm = sf.peer_medians(ticker, domain)
    if not pm or not pm.get("metrics"):
        return None, None, None, None
    pm_metrics = pm.get("metrics", {})
    pm_ns = pm.get("ns", {})
    sector_used = pm.get("sector_used")
    n_peers = pm.get("n_peers")

    metrics = _derived_metrics(inc, bal, cf, periods)
    self_l = "本股(最新)" if prefer_cn else "Self (latest)"
    peer_l = "同业中位" if prefer_cn else "Peer Median"
    delta_l = "vs同业(差)" if prefer_cn else "vs Peer (Δ)"
    yr_l = "年度" if prefer_cn else "Year"

    recs, idx = [], []
    n_by_metric: dict[str, int] = {}
    for cn, en, mkey, vals in metrics:
        # latest available year for THIS metric on the self series
        self_years = sorted((p for p, v in vals.items() if v is not None),
                            key=lambda p: _period_sort_key(p, "annual"))
        if not self_years:
            continue
        latest = self_years[-1]
        self_v = vals.get(latest)
        yint = int(latest)
        peer_v = _peer_median_for_year(pm_metrics.get(mkey, {}), yint)
        # peer sample size for this metric+year (0 if unknown)
        n_here = _peer_median_for_year(pm_ns.get(mkey, {}), yint)
        n_here = int(n_here) if n_here is not None else 0
        # n<3 guard: suppress thin/self-dominated medians
        if n_here < _MIN_PEER_N:
            peer_v = None
        if self_v is None and peer_v is None:
            continue
        label = cn if prefer_cn else en
        idx.append(label)
        delta = (self_v - peer_v) if (self_v is not None and peer_v is not None) else None
        recs.append({
            yr_l: str(yint),
            self_l: self_v,
            peer_l: peer_v,
            delta_l: delta,
        })
        n_by_metric[label] = n_here
    if not recs:
        return None, sector_used, n_peers, None
    df = pd.DataFrame(recs, index=pd.Index(idx))
    return df, sector_used, n_peers, n_by_metric


def statements_section(ticker: str, tax: str, prefer_cn: bool, *,
                       freq: str = "annual", periods: int = 6, domain=None) -> None:
    """Render the 3-statement summary + derived-metrics block for one ticker.

    freq: "annual" (default) or "quarterly". Quarterly shows '24Q1'-style headers,
    YoY vs the same quarter one year prior, and omits CAGR.
    domain: when given (annual mode only), append a peer-median comparison block
    to the derived-metrics table via sf.peer_medians(ticker, domain).
    """
    tax = tax or "us-gaap"
    freq = "quarterly" if freq == "quarterly" else "annual"
    is_q = freq == "quarterly"
    # quarterly default span is 8 quarters unless the caller overrides periods
    if is_q and periods == 6:
        periods = 8
    yoy_l = "同比%" if prefer_cn else "YoY%"
    cagr_l = "复合增速" if prefer_cn else "CAGR"

    inc = _section_series(ticker, tax, INCOME_ROWS, freq)
    bal = _section_series(ticker, tax, BALANCE_ROWS, freq)
    cf = _section_series(ticker, tax, CASHFLOW_ROWS, freq)
    prds = _collect_periods([inc, bal, cf], freq, periods)

    if not prds:
        import streamlit as st
        st.caption("该标的暂无可用的结构化报表数据。" if prefer_cn
                else "No structured statement data available for this ticker.")
        return

    any_rendered = False
    any_rendered |= _render_one("利润表" if prefer_cn else "Income Statement",
                                INCOME_ROWS, inc, prds, freq, prefer_cn, yoy_l, cagr_l)
    any_rendered |= _render_one("资产负债表" if prefer_cn else "Balance Sheet",
                                BALANCE_ROWS, bal, prds, freq, prefer_cn, yoy_l, cagr_l)
    any_rendered |= _render_one("现金流量表" if prefer_cn else "Cash Flow Statement",
                                CASHFLOW_ROWS, cf, prds, freq, prefer_cn, yoy_l, cagr_l)

    dm = _derived_df(inc, bal, cf, prds, freq, prefer_cn)
    if not dm.empty:
        theme.section_header("衍生指标" if prefer_cn else "Derived Metrics")
        ui.render_html_table(
            dm,
            pct_cols=[_period_label(p, freq) for p in prds],
            index_label=("指标" if prefer_cn else "Metric"),
            height=320,
        )

    # ── peer-median comparison (ANNUAL mode only) ──
    if not is_q and domain:
        try:
            pdf, sector_used, n_peers, n_by_metric = _peer_compare_df(
                inc, bal, cf, prds, prefer_cn, ticker, domain)
        except Exception:
            pdf, sector_used, n_peers, n_by_metric = None, None, None, None
        if pdf is not None and not pdf.empty:
            self_l = "本股(最新)" if prefer_cn else "Self (latest)"
            peer_l = "同业中位" if prefer_cn else "Peer Median"
            delta_l = "vs同业(差)" if prefer_cn else "vs Peer (Δ)"
            yr_l = "年度" if prefer_cn else "Year"
            theme.section_header("同业对标" if prefer_cn else "Peer Comparison")
            ui.render_html_table(
                pdf,
                pct_cols=[self_l, peer_l, delta_l],
                text_cols=[yr_l],
                index_label=("指标" if prefer_cn else "Metric"),
                height=300,
            )
            import streamlit as st
            cap_sector = sector_used or "—"
            # per-metric sample sizes for transparency; flag the n<3 guard.
            n_by_metric = n_by_metric or {}
            n_parts = ", ".join(f"{lbl}={n}" for lbl, n in n_by_metric.items()) or "—"
            any_thin = any(n < _MIN_PEER_N for n in n_by_metric.values())
            thin_note_cn = (f" 部分指标同业数<{_MIN_PEER_N}（样本不足，同业中位以 — 表示）。"
                            if any_thin else "")
            thin_note_en = (f" Metrics with <{_MIN_PEER_N} peers are suppressed (shown as —)."
                            if any_thin else "")
            st.caption(
                (f"同业 = 同 domain（{domain}）下与本股共享行业的美股（含 IFRS 申报、按比率口径可比，已排除 _coverage 总览）；"
                 f"行业：{cap_sector}；同业数(峰值)：{n_peers}；各指标同业数：{n_parts}。"
                 f"中位数已忽略缺披露同业；取各指标本股最新可得年度对比。{thin_note_cn}")
                if prefer_cn else
                (f"Peers = US names sharing a real sector with this ticker in domain '{domain}' "
                 f"(incl. IFRS filers — ratios are currency-agnostic; '_coverage' overlay excluded). "
                 f"Sector: {cap_sector}; n_peers (peak): {n_peers}; per-metric n: {n_parts}. "
                 f"Median ignores peers lacking disclosure; compared at each metric's latest available "
                 f"year for this ticker.{thin_note_en}")
            )

    import streamlit as st
    if is_q:
        st.caption(
            ("单位自适应 $B/$M；季度口径(利润表/现金流为单季,资产负债为季末时点);"
             "同比为去年同季;缺披露科目以 — 表示并隐藏全空行。准则：" + tax)
            if prefer_cn else
            ("Amounts auto-scaled $B/$M; quarterly (IS/CF single-quarter, BS quarter-end); "
             "YoY vs same quarter prior year; undisclosed lines shown as — (all-empty rows hidden). "
             "Taxonomy: " + tax)
        )
    else:
        st.caption(
            ("单位自适应 $B/$M；缺披露科目以 — 表示并隐藏全空行。准则：" + tax)
            if prefer_cn else
            ("Amounts auto-scaled $B/$M; undisclosed lines shown as — (all-empty rows hidden). Taxonomy: " + tax)
        )
