"""English locale — Phase 2 (Home + 5 healthcare pages + shared components).

Merged with en.py (Phase 1 strategy keys) by lib.i18n. Kept separate so Phase 1
stays untouched and per-page wiring can proceed without locale-file contention.
Onboarding bodies are translations of the (originally Chinese) in-page help text.
"""

STRINGS = {
    # ── shared: sidebar search (lib.ui.sidebar_search) ──
    "sidebar.find_ticker": "🔍 Find ticker",
    "sidebar.jump_label": "Jump to ticker drill",
    "sidebar.select_placeholder": "— select —",
    "sidebar.selected_info": "📍 **{bbg}** — open the *Ticker Drill* page for the full profile.",

    # ── shared: common table columns ──
    "common.col.name": "Name",
    "common.col.last": "Last",
    "common.col.ticker": "Ticker",
    "common.col.1d": "1D %",
    "common.col.5d": "5D %",
    "common.col.1m": "1M %",
    "common.col.3m": "3M %",
    "common.col.6m": "6M %",
    "common.col.vs_spx": "vs SPX",
    "common.col.ytd": "YTD %",
    "common.col.mcap_b": "Mcap USD ($B)",
    "common.col.trail_pe": "Trail P/E",
    "common.col.fwd_pe": "Fwd P/E",
    "common.col.ev_ebitda": "EV/EBITDA",
    "common.col.ev_sales": "EV/Sales",
    "common.col.fcf_yld": "FCF Yld",
    "common.col.pb": "P/B",
    "common.warn.fetch_fail": "Live fetch failed (yfinance) — check network/proxy.",

    # ── Home panels ──
    "home.panel.broad_market": "Market Overview",
    "home.panel.sp500_sector": "S&P 500 Sectors",
    "home.panel.healthcare": "Healthcare Benchmarks",
    "home.panel.ai": "AI Benchmarks (soon)",
    "home.panel.empty": "Coming soon",
    "home.panel.sp500_caption": "11 GICS sectors (SPDR Select Sector ETF proxies) + S&P 500 reference",
    "home.sub.benchmarks": "Benchmarks",

    # ── Home ──
    "home.title": "Market Hub",
    "home.metric.latest_snapshot": "Latest snapshot",
    "home.metric.last_fetch": "Last fetch (UTC)",
    "home.metric.universe": "Universe tickers",
    "home.section.benchmarks": "Benchmarks",
    "home.section.movers": "Top Movers · 1D",
    "home.section.movers_meta": "ACROSS COVERED SECTORS",
    "home.movers.gainers": "Top 10 Gainers",
    "home.movers.drags": "Top 10 Drags",
    "home.movers.empty": "No price data — run `jobs/fetch_eod.py --backfill-days 180`.",
    "home.section.universe": "Universe Coverage",
    "home.col.domain": "Domain",
    "home.col.sector": "Sector",
    "home.col.tickers": "Tickers",
    "home.caveat.data": (
        "**Data caveat**: valuation multiples come from **yfinance** — trailing P/E and "
        "12M forward P/E only. Multi-year consensus (25E / 26E / 27E) is **out of scope** "
        "here. Treat this board as a quick visual scan; defer to your Bloomberg / FactSet "
        "terminal for precise consensus."
    ),

    # ── CMSI Coverage ──
    "cov.title": "CMSI Coverage",
    "cov.caption": "28-ticker official cover list — HK 15 / US 10 / CN A-share 3. Latest data: {date}",
    "cov.col.vs_hsi": "vs HSI YTD",
    "cov.col.tp_upside": "TP Upside %",
    "cov.col.reco": "Reco",
    "cov.col.n_analysts": "N analysts",
    "cov.col.cross": "Cross",
    "cov.onboarding.title": "How to read this page",
    "cov.onboarding.body": (
        "**Official coverage list**: CMSI Healthcare coverage — HK, US and CN A-shares.\n\n"
        "**Columns**\n"
        "- **Cross**: cross-sector tags. A name in several sector universes (e.g. Innovent in "
        "Biotech + Pharma) shows the corresponding tags.\n"
        "- **Mcap USD**: market cap in USD for cross-region comparison.\n"
        "- **Fwd P/E**: yfinance 12M forward P/E.\n"
        "- **FCF Yield**: free-cash-flow yield; higher usually = steadier cash flow.\n\n"
        "**Sorting**: defaults to market cap descending."
    ),
    "cov.caption.tags": (
        "BIO = Biotech · PHAR = Pharma · AI = HC+AI · MED = Medtech · HOSP = Hospital Care · "
        "MC = Managed Care · CXO = CXO. Cross-sector tags mean the ticker also sits in other "
        "sector universes (auto-deduped)."
    ),
    "cov.caption.source": (
        "Cover list source: `config/universes/cmsi_coverage_hc.yml` ({n} tickers). "
        "Default sort market cap desc; name CN-first."
    ),

    # ── Healthcare overview ──
    "hc.title": "Healthcare",
    "hc.caption_fallback": "Healthcare domain overview — 7 sub-sectors.",
    "hc.section.summary": "Sector Summary",
    "hc.section.summary_meta": "MEAN RETURNS PER SECTOR",
    "hc.section.benchmark": "Domain Benchmark (XLV) & Peers",
    "hc.section.movers": "Per-Sector Top 3 Movers / Drags · 1D",
    "hc.col.sector": "Sector",
    "hc.col.tickers": "Tickers",
    "hc.col.benchmark": "Benchmark",
    "hc.col.1d_avg": "1D % avg",
    "hc.col.5d_avg": "5D % avg",
    "hc.col.1m_avg": "1M % avg",
    "hc.col.ytd_avg": "YTD % avg",
    "hc.movers.gainers": "Top 3 gainers · 1D",
    "hc.movers.drags": "Top 3 drags · 1D",
    "hc.summary.empty": "No sector data — backfill needed.",
    "hc.onboarding.title": "How to read this page",
    "hc.onboarding.body": (
        "**Sector summary**: mean return across the 7 healthcare sub-sectors.\n"
        "- **Tickers**: number of names in the sector.\n"
        "- **Benchmark**: the sector's reference index (e.g. XBI for Biotech).\n\n"
        "**Domain benchmarks**: XLV (Healthcare) and its main sub-industry ETFs.\n\n"
        "**Per-sector movers**: each sector's best/worst 3 names on the day."
    ),

    # ── Sector Heatmap ──
    "heat.title": "Sector Heatmap",
    "heat.caption": "Cross-sectional snapshot per sector. Multiples from yfinance — trailing + 12M forward only.",
    "heat.filter.header": "Filter",
    "heat.filter.min_mcap": "Min market cap (USD B)",
    "heat.filter.min_mcap_help": "Filter out small caps so they don't distort the mean.",
    "heat.filter.sort_by": "Sort by",
    "heat.filter.sort_help": "Defaults to market cap descending.",
    "heat.agg.expander": "{sector} aggregates (mean / median / weighted)",
    "heat.agg.metric": "Metric",
    "heat.onboarding.title": "How to read this page",
    "heat.onboarding.body": (
        "**Multiples & returns**\n"
        "- **Color legend**: returns green-up / red-down; multiples (P/E, EV/EBITDA) "
        "green-cheap / red-rich; FCF yield green-high / red-low.\n"
        "- **Tabs**: piano-key through the 7 sub-sectors.\n\n"
        "**Filters** — **Min market cap**: drop tiny names whose extreme multiples skew the "
        "sector mean.\n\n"
        "**Aggregates**: expand 'Sector aggregates' for the sector's mean and median."
    ),

    "heat.caption.legend": "**Color legend**: returns green-up / red-down; multiples (P/E, EV/EBITDA) green-cheap / red-rich; FCF yield green-high / red-low. Ticker in **Bloomberg style** (2269 HK / 4587 JP / 300760 CH). Latest data: **{date}**",
    "heat.caption.filter_note": "Sort/filter via the sidebar. The min-market-cap filter helps when small caps distort sector means (e.g. 4587 JP $904M vs GILD $166B).",

    # ── Valuation Scanner ──
    "scan.title": "Valuation Scanner",
    "scan.caption": (
        "Cross-sectional scan — cheap-on-multiple names with positive recent momentum. "
        "Sector-internal P/E percentile + YTD/5D filter. Latest: {date}"
    ),
    "scan.presets.header": "Presets",
    "scan.presets.deep_value": "Deep Value",
    "scan.presets.recovery": "Recovery",
    "scan.presets.reset": "Reset all filters",
    "scan.filters.header": "Filters",
    "scan.filters.sector": "Sector",
    "scan.filters.min_mcap": "Min market cap (USD B)",
    "scan.filters.pe_pct": "P/E percentile threshold",
    "scan.filters.pe_pct_help": "Show only candidates whose fwd P/E sits at/below this sector percentile.",
    "scan.filters.pe_metric": "P/E metric",
    "scan.filters.ytd_range": "YTD return range (%)",
    "scan.filters.min_5d": "Min 5D return (%)",
    "scan.metric.universe": "Universe scanned",
    "scan.metric.candidates": "Candidates",
    "scan.metric.median_mcap": "Median Mcap (USD B)",
    "scan.metric.median_ytd": "Median YTD",
    "scan.col.pe_pctile": "Sector P/E %ile",
    "scan.warn.no_sector": "Select at least 1 sector in the sidebar.",
    "scan.warn.no_candidates": (
        "No candidates match filters. Loosen criteria (lower min mcap / higher P/E threshold / "
        "widen YTD range)."
    ),
    "scan.onboarding.title": "How to read this page",
    "scan.onboarding.body": (
        "**Sector P/E %ile**: the stock's forward (or trailing) P/E rank within its sector.\n"
        "- `0%–25%` = cheapest quartile in-sector.\n"
        "- Typical sell-side framing: cheap multiple + positive momentum → possible re-rating.\n\n"
        "**YTD %**: year-to-date total return. Negative YTD + low P/E = possible 'fallen angel'; "
        "positive YTD + low P/E = 'value with momentum'.\n\n"
        "**5D %**: last-5-day momentum; default filter ≥ −10% drops names mid-crash.\n\n"
        "**EV/EBITDA**: complementary multiple (guards against one-off EPS distortions).\n\n"
        "**FCF Yield**: free cash flow / market cap; higher = stronger cash generation.\n\n"
        "**Presets** — **Deep Value**: deeply cheap (15%ile) large caps. "
        "**Recovery**: cheap names already turning up (5D % > 5%)."
    ),
    "scan.caption.method": (
        "**Methodology**: cross-sectional within selected sectors. Negative P/E excluded from "
        "percentile rank. Latest snapshot: {date}. Sector membership is many-to-many."
    ),

    # ── Ticker Drill ──
    "drill.title": "Ticker Drill",
    "drill.caption": "Single-ticker deep dive — wiki memo (if any) + price chart + multiples + cross-sector tags.",
    "drill.choose": "Choose ticker",
    "drill.pick_prompt": "Pick a ticker from the sidebar or the selectbox above.",
    "drill.badge.coverage": "CMSI Coverage",
    "drill.badge.pick": "Pick: {names}",
    "drill.metric.last_local": "Last",
    "drill.metric.last": "Last",
    "drill.metric.mcap": "Market cap",
    "drill.metric.fwd_pe": "Fwd P/E",
    "drill.metric.tp_upside": "TP Upside",
    "drill.metric.ytd": "YTD Return",
    "drill.metric.adv": "20D Turnover",
    "drill.kpi.ytd_foot": "{ccy} · local",
    "drill.kpi.adv_foot": "{ccy} · liquidity",
    "drill.consensus_line": "Consensus TP {tp} ({upside} vs last) · {n} analysts · third-party estimate, reference only",
    "drill.analysts": "analysts",
    "drill.kpi.pe_foot": "TRAIL {pe}",
    "drill.kpi.tp_foot": "Consensus TP {tp}",
    "drill.kpi.tp_none": "No consensus TP",
    # ── Variant block (House vs Consensus) ──
    "drill.variant.title": "Variant · House vs Consensus",
    "drill.variant.house": "House View · CMS HK",
    "drill.variant.consensus": "Consensus · Reference Only",
    "drill.variant.gap": "Variant Gap",
    "drill.variant.tp_foot": "TP {tp}",
    "drill.variant.cons_foot": "TP {tp} · {n} analysts",
    "drill.variant.gap_foot": "vs last price",
    "drill.variant.disclaimer": (
        "Consensus is a third-party Yahoo Finance aggregate (limited analyst "
        "coverage; may be unreliable for HK 18A names) — reference only, not a "
        "CMS HK view, and not investment advice. House view is from the wiki memo "
        "and uses a different methodology; do not distribute externally."
    ),
    "drill.reco.strong_buy": "Strong Buy",
    "drill.reco.buy": "Buy",
    "drill.reco.hold": "Hold",
    "drill.reco.sell": "Sell",
    "drill.reco.strong_sell": "Strong Sell",
    "drill.consensus_tp": "Consensus TP: **{tp}** ({upside} vs last){analysts}",
    "drill.no_mults": "No multiples snapshot — ticker may be picks-only (not in main fetch universe).",
    "drill.section.price": "Price · USD-normalized",
    "drill.section.rs": "Relative Strength · vs Sector",
    "drill.rs.title": "{bbg} · Relative Strength (rebased = 100)",
    "drill.rs.caption": (
        "Rebased to 100 on {date}. Benchmarks: {benches}. Stock and benchmarks are "
        "all in the listing currency ({ccy}) — same-currency comparison, no FX distortion."
    ),
    "drill.rs.fallback": "No overlapping sector-benchmark data — falling back to the absolute USD close.",
    "drill.ret_windows": "Return windows",
    "drill.col.window": "Window",
    "drill.col.return": "Return %",
    "drill.latest_mults": "Latest multiples (yfinance)",
    "drill.col.metric": "Metric",
    "drill.col.value": "Value",
    "drill.ext.expander": "Extended fundamentals (live yfinance.info — click to fetch)",
    "drill.ext.fetch": "Fetch live",
    "drill.ext.fetch_help": "Calls yfinance.info; result cached 1 hour.",
    "drill.ext.hint": (
        "Click *Fetch live* to pull EBITDA / margins / shares / business summary "
        "from yfinance.info. Avoided by default to keep the page snappy on "
        "Streamlit Cloud (cold-start visits skip the live call)."
    ),
    "drill.ext.empty": "yfinance.info returned empty — network issue, rate limit, or ticker delisted.",
    "drill.ext.biz_summary": "Business summary",
    "drill.ext.f.ebitda": "EBITDA (TTM)",
    "drill.ext.f.total_cash": "Total cash",
    "drill.ext.f.total_debt": "Total debt",
    "drill.ext.f.total_rev": "Total revenue (TTM)",
    "drill.ext.f.rev_growth": "Revenue growth (YoY)",
    "drill.ext.f.gross_margin": "Gross margin",
    "drill.ext.f.op_margin": "Operating margin",
    "drill.ext.f.profit_margin": "Profit margin",
    "drill.ext.f.roe": "Return on equity",
    "drill.ext.f.peg": "PEG ratio",
    "drill.ext.f.div_yield": "Dividend yield",
    "drill.ext.f.beta": "Beta",
    "drill.ext.f.shares_out": "Shares outstanding",
    "drill.ext.f.float_shares": "Float shares",
    "drill.ext.col.metric": "Metric",
    "drill.ext.col.value": "Value",
    "drill.ext.biz_summary_note": "yfinance English source text (no official Chinese profile provided).",
    # wiki memo block
    "drill.wiki.none": (
        "No LLM Wiki memo for this ticker. Drop a `companies/*.md` file in "
        "`~/Documents/LLM Wiki/Wiki/` to surface a thesis here."
    ),
    "drill.wiki.memo_title": "Research memo",
    "drill.wiki.banner_public": (
        "Public research summary · investment thesis and publicly available "
        "information. For ratings, target prices and full estimates, please refer "
        "to the formal CMS HK research report. For reference only; not investment "
        "advice or an offer."
    ),
    "drill.wiki.rating": "Rating",
    "drill.wiki.tp": "TP",
    "drill.wiki.updated": "Updated",
    "drill.wiki.sectors": "Wiki sectors",
    "drill.wiki.summary": "Summary",
    "drill.wiki.thesis": "Thesis",
    "drill.wiki.sources": "Sources",
    "drill.wiki.source_file": "Source file",
    # warnings / empty states
    "drill.warn.no_price": "No price history in snapshots.db — backfill needed for this ticker.",
    "drill.warn.price_nan": "Price series all-NaN.",
    "drill.warn.no_return": "No return data.",
    "drill.warn.no_mult_snap": "No multiples snapshot.",
    "drill.no_sector": "Ticker is not in any configured sector universe.",
    "drill.chart.title": "{bbg} · {ccy} close ({n} obs)",
    # multiples panel labels
    "drill.mult.trailing_pe": "Trailing P/E",
    "drill.mult.forward_pe": "Forward P/E",
    "drill.mult.ev_ebitda": "EV/EBITDA",
    "drill.mult.ev_sales": "EV/Sales",
    "drill.mult.pb": "P/B",
    "drill.mult.fcf_yield": "FCF Yield",
    # ── SEC financial trends (US-only) ──
    "drill.sec.section": "Financial Trends · SEC",
    "drill.sec.na": (
        "No SEC filing for this name (SEC XBRL is US-GAAP only). HK 18A reports "
        "under IFRS and A-shares under PRC GAAP — see local / Wind financials."
    ),
    "drill.sec.revenue": "Revenue",
    "drill.sec.rnd": "R&D",
    "drill.sec.cash": "Cash & equivalents",
    "drill.sec.no_concept": "No data",
    "drill.sec.latest": "Latest {val} ({date})",
    "drill.sec.runway": "Cash runway ≈ {years} yr ((cash + ST investments) ÷ annual R&D, as of {date}, rough)",
    "drill.sec.source": "Source: SEC XBRL · latest filing {filed} · US filers only",
    "drill.membership": "Universe membership",
    "drill.onboarding.title": "How to read this page",
    "drill.onboarding.body": (
        "**Memo source**: if `~/Documents/LLM Wiki/Wiki/companies/<ticker>-*.md` exists, the top "
        "of this page renders its Summary / Thesis / Rating / TP / catalysts / risks. The memo is "
        "authored on the wiki side; this page is read-only.\n\n"
        "**Price**: USD-converted close from `snapshots.db` (daily cron; data starts ~2025-12-01).\n\n"
        "**Multiples**: yfinance trailing + 12M forward only. Multi-year forward (25E/26E/27E) is "
        "out of scope.\n\n"
        "**Extended fundamentals**: live yfinance.info, cached 1h. '—' = field not provided.\n\n"
        "**Deep-link**: jump straight to a name via the `?ticker=LLY` URL param."
    ),

    # ── Market Data (full-universe quote table) ──
    "market.title": "Market Data",
    "market.caption": "Full-universe quote table — all {n} tickers across every domain. Latest: {date}",
    "market.filters.domain": "Domain",
    "market.filters.sector": "Sector",
    "market.filters.region": "Region",
    "market.metric.universe": "Universe size",
    "market.metric.shown": "Rows shown",
    "market.section.table": "Quotes & Multiples",
    "market.col.sector": "Sector",
    "market.col.region": "Region",
    "market.dl.quotes": "⬇ Download quote table (CSV)",
    "market.dl.master": "⬇ Download security master (CSV)",
    "market.dl.master_help": "The full universe_member table — ticker / name / domain / sector / region.",
    "market.onboarding.title": "How to read this page",
    "market.onboarding.body": (
        "**Scope**: every ticker in the dashboard universe, all domains — a single-page market scan.\n\n"
        "**Prices / multiples**: from `snapshots.db` (daily cron). Same source as the other pages.\n\n"
        "**Downloads**: *quote table* = the rows you see now (post-filter); *security master* = "
        "the universe roster itself, for syncing into your own tools."
    ),

    # ── SEC Company Facts ──
    "sec.title": "SEC Company Facts",
    "sec.caption": "SEC XBRL filings (us-gaap / ifrs-full) for US-listed names. Source: data.sec.gov.",
    "sec.choose": "Choose a US-listed ticker",
    "sec.pick_prompt": "Pick a ticker above to load its SEC company facts.",
    "sec.warn.non_us": "**{ticker}** is not in the US-listed pool — SEC company facts cover US filers only.",
    "sec.warn.no_xbrl": "**{ticker}** files no SEC XBRL facts (likely an OTC Level-I ADR). Nothing to show.",
    "sec.warn.not_fetched": "No SEC facts cached for **{ticker}** yet. Run `jobs/fetch_sec_facts.py` or wait for the weekly refresh.",
    "sec.badge.fetched": "Cached {fetched}",
    "sec.badge.latest_filed": "Latest filing {filed}",
    "sec.badge.taxonomy": "Taxonomy: {tax}",
    "sec.period.annual": "Annual (FY)",
    "sec.period.quarterly": "Quarterly",
    "sec.period.label": "Period basis",
    "sec.section.kpi": "Key Company Facts",
    "sec.kpi.na": "—",
    "sec.kpi.fallback": "fallback concept",
    "sec.kpi.trace": "Source: {concept} · {form} · FY{fy} {fp} · period end {end} · filed {filed} · {accn}",
    "sec.section.timeseries": "Concept Time-Series",
    "sec.ts.pick": "Concept",
    "sec.ts.freq": "Frequency",
    "sec.ts.yoy": "YoY %",
    "sec.ts.qoq": "QoQ %",
    "sec.ts.empty": "No time-series for this concept at the chosen frequency.",
    "sec.section.browser": "All Company Facts",
    "sec.browser.search": "Filter concept / label",
    "sec.browser.form": "Form",
    "sec.browser.taxonomy": "Taxonomy",
    "sec.browser.shown": "{shown} shown / {total} facts",
    "sec.browser.dl": "⬇ Download filtered facts (CSV)",
    "sec.col.concept": "Concept",
    "sec.col.concept_cn": "中文名",
    "sec.col.taxonomy": "Taxonomy",
    "sec.col.unit": "Unit",
    "sec.col.value": "Value",
    "sec.col.start": "Start",
    "sec.col.end": "End",
    "sec.col.form": "Form",
    "sec.col.fy": "FY",
    "sec.col.fp": "Period",
    "sec.col.filed": "Filed",
    "sec.section.comp": "Comp Table Export",
    "sec.comp.pick_tickers": "Tickers to compare",
    "sec.comp.pick_kpis": "Metrics (latest annual)",
    "sec.comp.dl": "⬇ Download comp table (CSV)",
    "sec.comp.hint": "Latest annual fiscal-year value per ticker. FY-end column flags period mismatch across filers.",
    "sec.col.fy_end": "FY End",
    "sec.onboarding.title": "How to read this page",
    "sec.onboarding.body": (
        "**Source**: SEC Company Facts API (full XBRL). US-listed names only — HK / A-share / "
        "OTC-ADR filers aren't in SEC and are flagged accordingly.\n\n"
        "**Taxonomy**: US domestic filers report under `us-gaap`; foreign filers (e.g. AstraZeneca, "
        "Novartis) report under `ifrs-full`. KPI cards fall back across both so foreign names don't blank out.\n\n"
        "**KPI cards**: each shows the latest reported value with a full source trace (concept / form / "
        "period / filing). A *fallback concept* badge means a non-primary tag supplied the number "
        "(e.g. concept migrations).\n\n"
        "**Refresh**: cached in `snapshots.db`, refreshed weekly by GitHub Actions — no manual fetch needed."
    ),

    # ── AI domain pages (a1–a5) — mirror healthcare pages with domain='ai' ──
    "ai.cov.title": "AI Universe",
    "ai.cov.caption": "Full AI supply-chain universe — 135 names across L1–L6 (US / JP / KR / CN-A). Latest data: {date}",
    "ai.cov.col.vs_sox": "vs SOX YTD",
    "ai.cov.caption.source": "Showing {n} AI names across 6 supply-chain layers. No CMSI cover list for AI yet — this is the full tracked universe.",
    "ai.cov.onboarding.title": "How to read this page",
    "ai.cov.onboarding.body": (
        "**AI Universe** is the full AI-compute / semiconductor supply chain tracked here — there is no CMSI "
        "cover list for AI yet, so this page surfaces every name (135) grouped by the 6 supply-chain layers "
        "(L1 equipment → L6 server).\n\n"
        "**vs SOX YTD** = the name's YTD return minus the ^SOX (Philadelphia Semiconductor Index) YTD — the "
        "AI-domain primary benchmark, replacing HSI used on the HK-centric Healthcare coverage page.\n\n"
        "**Defaults**: market-cap descending, Chinese name first. Prices / multiples from `snapshots.db` (daily cron)."
    ),
    "ai.ov.title": "AI Overview",
    "ai.heat.title": "AI Sector Heatmap",
    "ai.scan.title": "AI Valuation Scanner",
    "ai.sec.title": "AI · SEC Company Facts",
    "ai.sec.caption": "SEC XBRL filings (us-gaap / ifrs-full) for US-listed AI names. Source: data.sec.gov.",
    "ai.section.benchmark": "Domain Benchmark (^SOX) & Peers",

    # ── Healthcare · Capital Markets (P0a aggregate tracker) ──
    "capital.page.title": "Capital Markets",
    "capital.page.caption": "Global healthcare capital markets — monthly BD/licensing, M&A and VC/IPO flow tracker (pharma / medtech / digital health).",
    "capital.page.asof": "Data as of {date} (trailing-12M window)",
    "capital.cadence_note": (
        "Scope: the aggregate flow data is a **monthly** curated export (MEDIUM reliability), every figure tagged with source + as-of month; "
        "MNC balance sheets are SEC XBRL (HIGH). This page carries deal facts only — **no sell-side ratings**."
    ),
    # KPI strip
    "capital.kpi.ttm": "Trailing-12M Total Funding",
    "capital.kpi.ttm_foot": "Window {first} → {last}",
    "capital.kpi.latest": "Latest-Month Funding",
    "capital.kpi.latest_foot": "{month} · MoM {mom}",
    "capital.kpi.deals": "Latest-Month Deal Count",
    "capital.kpi.deals_foot": "{month} · {ttm:,} over full window",
    "capital.kpi.chinaout": "China-OUT Top Deal",
    "capital.kpi.chinaout_foot": "Headline $15.2B → real cash $950M (B3 · Hengrui-BMS)",
    # Trend section
    "capital.section.trend": "Capital Flow Trend",
    "capital.section.trend_meta": "Bars = capital · Line = deal count",
    "capital.segments.pick": "Select series",
    "capital.chart.capital": "Capital Invested",
    "capital.chart.deals": "Deal Count",
    "capital.series.hc_total": "Total Funding",
    "capital.series.pharma_ma": "Pharma M&A",
    "capital.series.pharma_vc": "Pharma VC&IPO",
    "capital.series.device_ma": "Device M&A",
    "capital.series.device_vc": "Device VC&IPO",
    "capital.series.digital_vc": "Digital-Health VC&IPO",
    "capital.unit.bn": "USD bn",
    "capital.unit.mn": "USD mn",
    # Sub-sector sparkline grid
    "capital.section.segments": "Sub-Sector Trends",
    "capital.section.segments_meta": "Last 12 months, capital invested (USD mn)",
    "capital.domain.pharma": "Pharma (M&A + VC&IPO)",
    "capital.domain.device": "Medtech (M&A + VC&IPO)",
    "capital.domain.digital": "Digital Health (VC&IPO only)",
    "capital.domain.digital_foot": "Note: digital health tracks VC&IPO only — no separate M&A series.",
    "capital.reconcile_note": (
        "⚠️ Scope note: the 5 sub-series do **NOT** sum to Total Funding — the total covers a broader universe. "
        "The sub-sector view shows only the 5 tracked segments (USD mn); do not read it as a 100% breakdown of the total."
    ),
    # China-OUT
    "capital.section.chinaout": "China-OUT Theme",
    "capital.chinaout.eyebrow": "China licensing — a structural regime shift",
    "capital.chinaout.body": (
        "China licensing has shifted from one-off out-licensing headlines into a standing MNC pipeline-sourcing channel. "
        "**Of NextPharma's Top 25 deals (Jan–Sep 2025), China-OUT accounts for 13/25 = 52%** "
        "(source: NextPharma 720 deals, as of 2025-09-04), and the share rose further into Q2 2026.\n\n"
        "**Known China-OUT total for Apr–May = $19.3B** (Hengrui-BMS $15.2B + Insilico-Lilly $2.75B + "
        "Haisco-AbbVie $745M + Amoytop-Aligos $445M + Huahui-BeOne $120M) — the single BMS-Hengrui deal "
        "alone exceeds whole-industry BD totals for several months of 2025.\n\n"
        "⚠️ **Compliance**: Hengrui's $15.2B headline includes $14.25B contingent milestones; real structured "
        "cash is only $950M (B3 decomposition). Downstream valuation must model upfront / milestone separately "
        "— never sum the headline figure directly."
    ),
    # MNC dry-powder
    "capital.section.mnc": "MNC Balance Sheets · Dry Powder",
    "capital.section.mnc_meta": "2026Q1 · SEC XBRL (HIGH)",
    "capital.mnc.col.company": "Company",
    "capital.mnc.col.cash": "Cash $bn",
    "capital.mnc.col.debt": "Total Debt $bn",
    "capital.mnc.col.net": "Net Cash $bn",
    "capital.mnc.col.form": "Form",
    "capital.mnc.col.date": "Filed",
    "capital.mnc.note": (
        "6 rows show \"—\" for no us-gaap cash disclosure (NVS/AZN/SNY/NVO/PHG are 20-F ADRs; GEHC cash field missing) — "
        "this is **not zero**, do not read as no cash. Also: the us-gaap cash concept excludes short-term investments, "
        "so PFE/MRK and others may be understated."
    ),
    # Methodology + disclaimer
    "capital.method_expander": "Methodology & Sources (B1-B7 cross-check)",
    "capital.method_body": (
        "**Source tiers (research-data.md)**: aggregate monthly flow = MEDIUM (curated, PitchBook-style); "
        "MNC balance sheets = HIGH (SEC EDGAR 10-Q/20-F XBRL).\n\n"
        "**B3 decomposition**: any headline deal size must decompose to upfront + milestone + structured/CVR; "
        "failing sum-check flags confidence = MEDIUM.\n\n"
        "**B6 asymmetric sourcing**: A-share/HK single-source (HKEX/cninfo) can be HIGH; US-private deals need 3 sources.\n\n"
        "**Unit normalization**: the total series is native USD bn while sub-series are USD mn — the loader normalizes "
        "everything so charts never mix scales."
    ),
    "capital.disclaimer": (
        "This page is a research-desk multi-source cross-check, not investment advice. Headline deal sizes decompose to "
        "real cash per B3; MEDIUM sources contribute factual figures only — **no sell-side rating is adopted**. Every "
        "figure carries (source, as-of)."
    ),

    # ── Capital Markets · Q1 2026 public-source quarterly snapshot (Option-2) ──
    "capital.q.asof": "Freshest complete quarter Q1 2026 · quarterly (not monthly)",
    "capital.q.freshness": (
        "📅 **Cadence**: public sources are **quarterly** — freshest complete quarter is **Q1 2026** (Jan–Mar). "
        "Q2 2026 (Apr–Jun) reports land ~mid-July; until then Apr/May are partial deal-level tallies only. "
        "The old PitchBook **monthly** cadence **cannot be reproduced** (no free monthly source)."
    ),
    "capital.q.cadence_note": (
        "Scope: every figure is from a **publicly-published** report (JPMorgan / DealForma / Rock Health / Galen Growth / "
        "CB Insights / Renaissance / Bain), each carrying a source URL + publication date + measure tag + HIGH/MEDIUM tier. "
        "Multi-source cross-checked + adversarially verified. **No sell-side rating adopted.**"
    ),
    "capital.q.kpi.ma": "Biopharma M&A",
    "capital.q.kpi.ma_foot": "Q1'26 · upfront-cash measure · JPM+DealForma converge ±$0.1B · 25-32 deals",
    "capital.q.kpi.lic": "Biopharma Licensing",
    "capital.q.kpi.lic_foot": "Q1'26 · announced biobucks · upfront only ~6% (milestone-heavy)",
    "capital.q.kpi.vc": "Biopharma Venture",
    "capital.q.kpi.vc_foot": "Q1'26 · −20% YoY (vs $8.6B) · global · licensing substituting for VC",
    "capital.q.kpi.dh": "Digital-Health VC (global)",
    "capital.q.kpi.dh_foot": "Q1'26 · global 216 deals · US subset $4.0B (Rock) · Galen+CB converge 4%",
    "capital.q.section.scorecard": "Q1 2026 Segment Scorecard",
    "capital.q.section.scorecard_meta": "each row tagged measure / geography / tier / source",
    "capital.q.col.segment": "Segment",
    "capital.q.col.value": "Q1'26 $B",
    "capital.q.col.count": "Deals",
    "capital.q.col.prior": "Q1'25 $B",
    "capital.q.col.yoy": "YoY %",
    "capital.q.col.measure": "Measure",
    "capital.q.col.geo": "Geo",
    "capital.q.col.tier": "Tier",
    "capital.q.col.source": "Source",
    "capital.seg.biopharma_ma": "Biopharma M&A",
    "capital.seg.biopharma_licensing": "Biopharma Licensing (BD)",
    "capital.seg.biopharma_venture": "Biopharma Venture",
    "capital.seg.digital_health_vc_us": "Digital-Health VC (US)",
    "capital.seg.digital_health_vc_global": "Digital-Health VC (global)",
    "capital.seg.us_biotech_ipo": "US Biotech IPO",
    "capital.seg.medtech_ma": "Medtech M&A",
    "capital.measure.upfront_cash": "upfront cash",
    "capital.measure.incl_contingents": "incl. CVR",
    "capital.measure.announced_biobucks": "announced",
    "capital.measure.raised": "raised",
    "capital.measure.proceeds": "proceeds",
    "capital.measure.disclosed_value": "disclosed",
    "capital.geo.global": "Global",
    "capital.geo.us": "US",
    "capital.q.section.yoy": "Venture / VC YoY",
    "capital.q.section.yoy_meta": "only same-magnitude segments with a YoY comparator (avoids mixing measures)",
    "capital.q.section.medtech": "Medtech M&A (gap)",
    "capital.q.medtech_note": (
        "⚠️ Free public sources have **no quarterly medtech-M&A series**. The only citable figure is Bain's "
        "**FY2025 partial-year** (Jan–Nov) **~$80B** (via MedTech Dive, MEDIUM, deal count undisclosed) — surpassing "
        "the prior three years combined, H2 ≈ 2× H1. **Shown as a single partial-FY annotation, not quarterly bars.** "
        "Medtech = 31% of all-industry M&A in Q1'26 (8-quarter high, Biotechgate). Large deals: BSX-Penumbra $14.5B "
        "(H1'26 close), Abbott-Exact Sciences $23B."
    ),
    "capital.q.section.baselines": "FY2025 Baselines (trend context)",
    "capital.q.baselines.col.metric": "Metric",
    "capital.q.baselines.col.value": "FY2025 $B",
    "capital.q.baselines.col.count": "Deals",
    "capital.q.baselines.col.source": "Source",
    "capital.q.chinaout_wall": (
        "⚠️ Below = **Apr–May deal-level partial tally** (NOT a complete-quarter aggregate; LOW / partial disclosure) — "
        "a **different basis** from the Q1'26 public quarterly figures above, do not read together. Kept for its "
        "information value on your China-OUT theme."
    ),
    "capital.q.method_body": (
        "**Sources (all publicly published; per-figure URLs below)**:\n\n"
        "- Biopharma M&A / licensing / venture / IPO: JPMorgan Q1 2026 Biopharma report, DealForma, Renaissance, BioPharma Dive\n"
        "- Digital-health VC: Rock Health (US), Galen Growth (global), CB Insights (global)\n"
        "- Medtech M&A: Bain (via MedTech Dive) — FY2025 partial-year\n\n"
        "**Measure discipline**: M&A separates upfront-cash vs incl-contingents; licensing is announced biobucks "
        "(upfront only ~6%); digital-health US (Rock) and global (Galen/CB) are listed separately, never added. "
        "**Different measures are non-additive.**\n\n"
        "**Freshness**: Q2 2026 reports land ~mid-July; refresh planned then."
    ),

    # ── Pharma MNC M&A (deal-level, MNCs basket xlsx / mnc-deal-scanner) ──
    "mnc_ma.page.asof": "13 pharma MNCs · M&A history",
    "mnc_ma.intro": "The full M&A history of 13 global pharma MNCs — deal-level, sliceable by company / therapeutic area / year. Data from the MNCs basket (maintained by the mnc-deal-scanner skill).",
    "mnc_ma.source_note": "Source: MNCs basket summary ({source}). Values include disclosed (Actual) and reasonable estimates (Estimated); deal-level cross-checked. **No sell-side rating.**",
    "mnc_ma.kpi.total": "Total M&A (lifetime)",
    "mnc_ma.kpi.total_foot": "{n} deals · {ymin}-{ymax} · 13 pharma MNCs",
    "mnc_ma.kpi.deals": "Deal Count",
    "mnc_ma.kpi.deals_foot": "disclosed {actual} · estimated {est}",
    "mnc_ma.kpi.top": "Most Acquisitive",
    "mnc_ma.kpi.top_foot": "{company} · {n} deals",
    "mnc_ma.kpi.biggest": "Largest Ever",
    "mnc_ma.kpi.biggest_foot": "{acq} acq. {tgt} · {year}",
    "mnc_ma.section.league": "M&A by Acquirer",
    "mnc_ma.section.league_meta": "who buys most (USD bn, cumulative)",
    "mnc_ma.section.ta": "By Therapeutic Area",
    "mnc_ma.section.ta_meta": "M&A value distribution (USD bn)",
    "mnc_ma.section.timeline": "M&A Over Time",
    "mnc_ma.section.timeline_meta": "M&A value per year (USD bn)",
    "mnc_ma.section.top": "Largest Deals Ever · Top 20",
    "mnc_ma.section.table": "Deal Detail",
    "mnc_ma.section.table_meta": "filter by company",
    "mnc_ma.chart.by_company": "Lifetime M&A by pharma MNC",
    "mnc_ma.chart.by_ta": "M&A value by therapeutic area",
    "mnc_ma.chart.by_year": "M&A value per year",
    "mnc_ma.col.ticker": "Co.",
    "mnc_ma.col.company": "Acquirer",
    "mnc_ma.col.target": "Target",
    "mnc_ma.col.year": "Date",
    "mnc_ma.col.size": "Size $B",
    "mnc_ma.col.ta": "Therapeutic Area",
    "mnc_ma.col.basis": "Basis",
    "mnc_ma.filter.company": "Filter company",
    "mnc_ma.filter.all": "All",
    "mnc_ma.basis.Actual": "Disclosed",
    "mnc_ma.basis.Estimated": "Estimated",
    "mnc_ma.disclaimer": "This page is an M&A-history dataset, not investment advice. Values include estimates (basis tagged); deal facts only, no sell-side rating adopted.",
    # 2026 YTD M&A (top)
    "mnc_ma.section.ytd": "2026 YTD M&A",
    "mnc_ma.section.ytd_meta": "this year's true acquisitions (M&A, excl. BD/partnerships)",
    "mnc_ma.ytd.count": "2026 M&A Deals",
    "mnc_ma.ytd.count_foot": "${value:.1f}B total · acquisitions only",
    "mnc_ma.ytd.total": "2026 M&A Value",
    "mnc_ma.ytd.total_foot": "{n} deals · excl. BD/partnerships",
    "mnc_ma.ytd.biggest": "Largest 2026 Acquisition",
    "mnc_ma.ytd.biggest_foot": "{acq} acq. {tgt}",
    "mnc_ma.ytd.bd_count": "2026 BD/Partnerships",
    "mnc_ma.ytd.bd_foot": "NOT M&A · see the BD tab",
    "mnc_ma.ytd.bd_note": "⚠️ M&A = true acquisition (change of control); BD = license/option/collaboration (no change of control). The Hengrui-BMS $15.2B is a 13-program strategic COLLABORATION — it is **BD, not M&A** — see the BD/Partnerships section below.",
    "mnc_ma.ma_only": "(true acquisitions only; BD/partnerships listed separately)",
    "mnc_ma.section.bd": "BD / Partnerships",
    "mnc_ma.section.bd_meta": "licensing deals (upfront / milestone / total) · from the ED Funding report + 2026",
    "mnc_ma.col.type": "Type",
    "mnc_ma.bd.col.licensor": "Licensor",
    "mnc_ma.bd.col.licensee": "Licensee",
    "mnc_ma.bd.col.asset": "Asset / Tech",
    "mnc_ma.bd.col.phase": "Phase",
    "mnc_ma.bd.col.region": "Region",
    "mnc_ma.bd.col.date": "Date",
    "mnc_ma.bd.sources": "2026 BD sources (click to open):",
    "mnc_ma.section.sources": "Sources",
    "mnc_ma.sources_note": "Deals are officially announced on each MNC's IR / newsroom — click to open and verify:",
    "mnc_ma.col.total": "Total $B",
    "mnc_ma.col.upfront": "Upfront $B",
    "mnc_ma.col.milestone": "Milestone $B",
    "mnc_ma.ytd.sources": "2026 M&A sources (click to open the press release):",
    "mnc_ma.col.src": "Source",
    # ── M&A / BD tabs + BD insight layer ──
    "capital.tab.ma": "M&A · Acquisitions",
    "capital.tab.bd": "BD · Licensing",
    "capital.def": "M&A = change of control (acquisition/merger); BD = license / option / collaboration (no change of control).",
    "capital.bd.section.ytd": "2026 YTD BD",
    "capital.bd.section.ytd_meta": "year-to-date licensing deals (through 2026-05, partial period)",
    "capital.bd.ytd.total": "2026 Potential Total",
    "capital.bd.ytd.total_foot": "incl. milestones · {n} deals",
    "capital.bd.ytd.upfront": "2026 Upfront",
    "capital.bd.ytd.upfront_foot": "committed cash portion",
    "capital.bd.ytd.count": "2026 Deals",
    "capital.bd.ytd.count_foot": "2025 full-year: {y}",
    "capital.bd.ytd.biggest": "Biggest Single",
    "capital.bd.ytd.biggest_foot": "{lor} → {lee}",
    "capital.bd.contingent": "⚠️ Milestones are contingent, not recognized revenue; totals include undisclosed / partially-disclosed terms.",
    "capital.bd.section.league": "BD League · full 2025–2026",
    "capital.bd.section.league_meta": "licensing economics · single source bd_deals.csv (99 deals)",
    "capital.bd.kpi.total": "Total BD Value",
    "capital.bd.kpi.total_foot": "incl. milestones · Σupfront ${u:.1f}B vs Σmilestone ${m:.1f}B",
    "capital.bd.kpi.upfront_ratio": "Upfront Ratio (median)",
    "capital.bd.kpi.upfront_ratio_foot": "upfront/total median · ~5% = 95% on milestones",
    "capital.bd.kpi.china": "China Out-Licensing",
    "capital.bd.kpi.china_foot": "by value · CN-biotech licensors ${b:.0f}B",
    "capital.bd.kpi.topmnc": "Most-Active MNC Buyer",
    "capital.bd.kpi.topmnc_foot": "{name} · {n} deals",
    "capital.bd.section.bylicensee": "BD League · by Licensee (MNC buyer)",
    "capital.bd.section.bylicensee_meta": "by deal count · MNC in-licensing appetite (not value — milestones inflate it)",
    "capital.bd.chart.licensee": "MNC Buyers by BD Deal Count",
    "capital.bd.section.byta": "by Therapeutic Area",
    "capital.bd.section.byta_meta": "by potential total (incl. milestones) · same axis as M&A-by-TA",
    "capital.bd.chart.ta": "BD Value by Therapeutic Area",
    "capital.bd.section.byphase": "How Early MNCs Reach In",
    "capital.bd.section.byphase_meta": "by deal count · upstream depth (M&A cannot show this)",
    "capital.bd.chart.phase": "MNC Entry by Phase (deal count)",
    "capital.bd.section.byyear": "Yearly Trend",
    "capital.bd.chart.year": "BD Deal Count by Year",
    "capital.bd.note.year": "Bar = deal count; 2026 is YTD (through 2026-05); milestone-inflated value is not comparable across years.",
    "capital.bd.section.top": "TOP 20 BD Deals",
    "capital.bd.section.table": "All BD Deals (filter)",
    "capital.bd.note.league": "* The MNC-buyer league excludes deals whose licensee is a NewCo/small biotech or whose direction is atypical (an MNC out-licensing), so the ranking reflects genuine MNC in-licensing; count charts and the detail table below still include all 99. One data-anomaly row (milestone > total, Evaxion→Merck) is dropped from value math.",
    "capital.bd.unit.deals": "# deals",
    "capital.bd.filter.licensee": "Filter by Licensee (MNC)",
    "capital.bd.filter.licensor": "Filter by Licensor",
    "capital.bd.filter.all": "All",
}
