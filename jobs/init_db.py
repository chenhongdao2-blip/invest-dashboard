"""Initialize SQLite schema for invest-dashboard.

Idempotent — safe to run multiple times.

Usage:
    python jobs/init_db.py
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "snapshots.db"

SCHEMA = """
-- Daily prices (auto-grown by fetch_eod.py)
-- Local-currency close + USD-converted close (M1 audit fix)
CREATE TABLE IF NOT EXISTS prices_daily (
    ticker        TEXT NOT NULL,
    date          TEXT NOT NULL,        -- YYYY-MM-DD
    open          REAL,
    high          REAL,
    low           REAL,
    close         REAL,                  -- local ccy
    adj_close     REAL,                  -- local ccy
    volume        INTEGER,
    currency      TEXT,                  -- USD / HKD / JPY / KRW / EUR / CNY / GBP / CHF
    close_usd     REAL,                  -- M1: USD-converted close
    adj_close_usd REAL,                  -- M1: USD-converted adj_close
    PRIMARY KEY (ticker, date)
);
CREATE INDEX IF NOT EXISTS idx_prices_date ON prices_daily(date);

-- Multiple snapshot 时序 (core value: 自累积 → 90d 后可做 Z-score)
CREATE TABLE IF NOT EXISTS multiples_daily (
    ticker            TEXT NOT NULL,
    date              TEXT NOT NULL,
    market_cap_usd    REAL,
    mcap_tier         TEXT,                -- M11: mega/large/mid/small/micro
    trailing_pe       REAL,
    forward_pe        REAL,
    trailing_eps      REAL,
    forward_eps       REAL,
    ev_ebitda         REAL,
    ev_sales          REAL,
    fcf_yield         REAL,
    peg               REAL,
    pb                REAL,
    ytd_return        REAL,
    last_price        REAL,                -- local ccy
    last_price_usd    REAL,                -- M1: USD-converted last price
    currency          TEXT,                -- 来自 yfinance.info
    PRIMARY KEY (ticker, date)
);
CREATE INDEX IF NOT EXISTS idx_mult_date ON multiples_daily(date);

-- Universe membership (many-to-many for cross-sector tickers like ISRG / HCA)
CREATE TABLE IF NOT EXISTS universe_member (
    domain    TEXT NOT NULL,
    sector    TEXT NOT NULL,
    ticker    TEXT NOT NULL,
    name_cn   TEXT,
    name_en   TEXT,
    region    TEXT,
    note      TEXT,
    PRIMARY KEY (domain, sector, ticker)
);
CREATE INDEX IF NOT EXISTS idx_um_ticker ON universe_member(ticker);
CREATE INDEX IF NOT EXISTS idx_um_domain_sector ON universe_member(domain, sector);

-- Meta key/value
CREATE TABLE IF NOT EXISTS meta (
    key         TEXT PRIMARY KEY,
    value       TEXT,
    updated_at  TEXT
);

-- Benchmark index closes (cron-fetched; home page reads this, NOT live yfinance —
-- live calls from Streamlit Cloud get rate-limited by Yahoo, esp. ^HSI).
CREATE TABLE IF NOT EXISTS benchmarks_daily (
    ticker TEXT NOT NULL,
    date   TEXT NOT NULL,
    close  REAL,
    PRIMARY KEY (ticker, date)
);
CREATE INDEX IF NOT EXISTS idx_bench_date ON benchmarks_daily(date);

-- 申万行业指数周线 (RRG 板块轮动用)。iFind-only (MCP 在本地父会话，cron 抓不到)，
-- 故走 committed seed CSV → jobs/load_sw_industry.py 入库，与 HSHCI 同模式。
-- 频率=周 (W-FRI)；close=指数点位 native CNY；turnover_rate=周换手率% (拥挤度 Tier A)。
CREATE TABLE IF NOT EXISTS sw_industry_daily (
    ticker        TEXT NOT NULL,
    name_cn       TEXT,
    market        TEXT,            -- a_share | hk (美股走 benchmarks_daily)
    date          TEXT NOT NULL,
    close         REAL,
    turnover_rate REAL,
    PRIMARY KEY (ticker, date)
);
CREATE INDEX IF NOT EXISTS idx_sw_industry_date ON sw_industry_daily(date);

-- Company profile from yfinance.info (cron-fetched; Ticker Drill extended
-- fundamentals reads this, NOT live .info — Yahoo blocks live .info from cloud IPs).
-- Columns mirror yfinance.info field names so the page can use info.get('ebitda') etc.
CREATE TABLE IF NOT EXISTS company_profile (
    ticker                TEXT PRIMARY KEY,
    fetched_at            TEXT,
    ebitda                REAL,
    totalCash             REAL,
    totalDebt             REAL,
    totalRevenue          REAL,
    revenueGrowth         REAL,
    freeCashflow          REAL,
    grossMargins          REAL,
    operatingMargins      REAL,
    profitMargins         REAL,
    returnOnEquity        REAL,
    trailingPegRatio      REAL,
    dividendYield         REAL,
    beta                  REAL,
    sharesOutstanding     REAL,
    floatShares           REAL,
    longBusinessSummary   TEXT
);

-- Chinese translation of company_profile.longBusinessSummary. SEPARATE table so the
-- daily fetch_eod INSERT OR REPLACE on company_profile never wipes translations.
-- en_hash = sha256 of the English text at translation time → detects staleness when
-- the cron refreshes the English summary (mismatch → page falls back to English).
-- Populated locally by jobs/translate_profiles.py (needs GLM key + proxy; NOT run on
-- the US Actions runner).
CREATE TABLE IF NOT EXISTS profile_cn (
    ticker        TEXT PRIMARY KEY,
    en_hash       TEXT,
    summary_cn    TEXT,
    translated_at TEXT
);

-- ── SEC Company Facts (auto-grown by fetch_sec_facts.py) ──
-- ticker→CIK mapping + fetch status + raw snapshot (audit/re-parse)
CREATE TABLE IF NOT EXISTS sec_company (
    ticker           TEXT PRIMARY KEY,     -- joins universe_member.ticker (region='US')
    cik              INTEGER,
    cik10            TEXT,                  -- zero-padded for API path
    entity_name      TEXT,
    taxonomy_primary TEXT,                  -- 'us-gaap' | 'ifrs-full' | NULL
    sec_status       TEXT NOT NULL,         -- 'ok' | 'no_xbrl' | 'not_mapped' | 'failed'
    fetched_at       TEXT,
    latest_filed     TEXT,
    facts_count      INTEGER,
    last_error       TEXT,
    payload_gzip     BLOB                   -- raw companyfacts JSON (gzip), audit/re-parse
);

-- NOTE: individual XBRL facts are NOT exploded into a flat table — at ~20k
-- facts × ~75 companies that bloated the committed DB to 600MB+ (GitHub rejects
-- >100MB). Instead the raw companyfacts JSON is stored gzip'd in
-- sec_company.payload_gzip (~14MB total) and parsed on demand per company by
-- app/lib/sec_facts.py (st.cache_data). Single source of truth, tiny on disk.

-- KPI map — industry-agnostic layered; dual-taxonomy fallback chain.
-- domain IS NULL => universal (all industries); else per-domain overlay.
-- Drives SEC page KPI cards + comp-table columns. Seeded by seed_kpi_map().
CREATE TABLE IF NOT EXISTS sec_kpi_map (
    kpi_key       TEXT PRIMARY KEY,
    display_order INTEGER NOT NULL,
    domain        TEXT,                      -- NULL=universal; 'healthcare'/'ai'/...=overlay
    label_en      TEXT NOT NULL,
    label_cn      TEXT NOT NULL,
    concepts_json TEXT NOT NULL,             -- JSON ["us-gaap:X","ifrs-full:Y",...] by priority
    period_type   TEXT NOT NULL,             -- 'instant' | 'duration'
    unit_hint     TEXT
);
"""


# ── SEC KPI map seed (industry-agnostic) ──
# (kpi_key, display_order, domain, label_en, label_cn, [concept fallbacks], period_type, unit_hint)
# domain=None => universal (every industry); domain='healthcare' => HC overlay.
# Concept fallbacks span us-gaap AND ifrs-full so foreign filers (NVS/AZN/BNTX...) don't blank out.
SEED_KPIS: list[tuple] = [
    # ── universal layer (domain=None) — applies to ANY industry ──
    ("revenue", 10, None, "Revenue", "营业收入",
     ["us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax",
      "us-gaap:Revenues", "us-gaap:SalesRevenueNet", "ifrs-full:Revenue"],
     "duration", "USD"),
    ("gross_profit", 20, None, "Gross Profit", "毛利润",
     ["us-gaap:GrossProfit", "ifrs-full:GrossProfit"], "duration", "USD"),
    ("operating_income", 30, None, "Operating Income", "营业利润",
     ["us-gaap:OperatingIncomeLoss", "ifrs-full:ProfitLossFromOperatingActivities"],
     "duration", "USD"),
    ("net_income", 40, None, "Net Income", "归母净利润",
     ["us-gaap:NetIncomeLoss",
      "ifrs-full:ProfitLossAttributableToOwnersOfParent", "ifrs-full:ProfitLoss"],
     "duration", "USD"),
    ("eps_diluted", 50, None, "Diluted EPS", "稀释每股收益",
     ["us-gaap:EarningsPerShareDiluted", "ifrs-full:DilutedEarningsLossPerShare"],
     "duration", "USD/shares"),
    ("assets", 60, None, "Total Assets", "总资产",
     ["us-gaap:Assets", "ifrs-full:Assets"], "instant", "USD"),
    ("equity", 70, None, "Stockholders Equity", "股东权益",
     ["us-gaap:StockholdersEquity",
      "ifrs-full:EquityAttributableToOwnersOfParent", "ifrs-full:Equity"],
     "instant", "USD"),
    ("cash", 80, None, "Cash & Equivalents", "现金及现金等价物",
     ["us-gaap:CashAndCashEquivalentsAtCarryingValue",
      "ifrs-full:CashAndCashEquivalents"], "instant", "USD"),
    # ── healthcare overlay (domain='healthcare') — only shown for HC tickers ──
    ("rnd", 90, "healthcare", "R&D Expense", "研发费用",
     ["us-gaap:ResearchAndDevelopmentExpense",
      "us-gaap:ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost",
      "ifrs-full:ResearchAndDevelopmentExpense"], "duration", "USD"),
    ("sga", 100, "healthcare", "SG&A Expense", "销售及管理费用",
     ["us-gaap:SellingGeneralAndAdministrativeExpense",
      "us-gaap:GeneralAndAdministrativeExpense",
      "ifrs-full:SellingGeneralAndAdministrativeExpense"], "duration", "USD"),
    ("short_term_investments", 110, "healthcare", "Short-Term Investments", "短期投资",
     ["us-gaap:ShortTermInvestments", "us-gaap:MarketableSecuritiesCurrent",
      "ifrs-full:CurrentInvestments"], "instant", "USD"),
    ("sbc", 120, "healthcare", "Stock-Based Comp", "股份支付",
     ["us-gaap:ShareBasedCompensation",
      "us-gaap:AllocatedShareBasedCompensationExpense"], "duration", "USD"),
]


def seed_kpi_map(conn: sqlite3.Connection) -> int:
    """Idempotent canonical seed of sec_kpi_map (INSERT OR REPLACE by kpi_key)."""
    import json

    rows = [
        (k, order, domain, en, cn, json.dumps(concepts, ensure_ascii=False), period, unit)
        for (k, order, domain, en, cn, concepts, period, unit) in SEED_KPIS
    ]
    conn.executemany(
        """INSERT OR REPLACE INTO sec_kpi_map
           (kpi_key, display_order, domain, label_en, label_cn,
            concepts_json, period_type, unit_hint)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )
    return len(rows)


def _safe_alter(conn: sqlite3.Connection, sql: str) -> None:
    """ALTER TABLE ADD COLUMN — ignore 'duplicate column name' errors."""
    try:
        conn.execute(sql)
    except sqlite3.OperationalError as e:
        if "duplicate column" not in str(e).lower():
            raise


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(SCHEMA)
        # m8 audit: idempotent column adds for existing DBs (no destructive migration)
        _safe_alter(conn, "ALTER TABLE multiples_daily ADD COLUMN target_price_mean REAL")
        _safe_alter(conn, "ALTER TABLE multiples_daily ADD COLUMN recommendation_mean REAL")
        _safe_alter(conn, "ALTER TABLE multiples_daily ADD COLUMN n_analysts INTEGER")
        _safe_alter(conn, "ALTER TABLE sw_industry_daily ADD COLUMN market TEXT")
        n_kpi = seed_kpi_map(conn)
        conn.commit()
        print(f"[init_db] seeded sec_kpi_map: {n_kpi} rows")
        # Sanity log
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cur.fetchall()]
        print(f"[init_db] DB at: {DB_PATH}")
        print(f"[init_db] Tables: {tables}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
