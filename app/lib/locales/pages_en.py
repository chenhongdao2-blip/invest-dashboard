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
    "common.col.ytd": "YTD %",
    "common.col.mcap_b": "Mcap USD ($B)",
    "common.col.trail_pe": "Trail P/E",
    "common.col.fwd_pe": "Fwd P/E",
    "common.col.ev_ebitda": "EV/EBITDA",
    "common.col.ev_sales": "EV/Sales",
    "common.col.fcf_yld": "FCF Yld",
    "common.col.pb": "P/B",
    "common.warn.fetch_fail": "Live fetch failed (yfinance) — check network/proxy.",

    # ── Home ──
    "home.title": "Multi-Domain Investment Dashboard",
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
        "**Data caveat**: valuation multiples are from **yfinance** (trailing P/E + 12M "
        "forward P/E). Multi-year forward (25E / 26E / 27E) needs Bloomberg / FactSet and "
        "is **out of scope**. Use this for a quick visual scan; rely on your manual Excel "
        "comp tables for precise consensus."
    ),
    "home.caveat.repo": (
        "Repo: [github.com/chenhongdao2-blip/invest-dashboard]"
        "(https://github.com/chenhongdao2-blip/invest-dashboard) · "
        "Data: SQLite committed in repo · Auto-update: GitHub Actions cron (22:30 UTC US + 09:00 UTC HK)"
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
    "drill.metric.last_local": "Last (local)",
    "drill.metric.last": "Last",
    "drill.metric.mcap": "Market cap",
    "drill.metric.fwd_pe": "Fwd P/E",
    "drill.consensus_tp": "Consensus TP: **{tp}** ({upside} vs last){analysts}",
    "drill.no_mults": "No multiples snapshot — ticker may be picks-only (not in main fetch universe).",
    "drill.section.price": "Price · USD-normalized",
    "drill.ret_windows": "Return windows",
    "drill.col.window": "Window",
    "drill.col.return": "Return %",
    "drill.latest_mults": "Latest multiples (yfinance)",
    "drill.col.metric": "Metric",
    "drill.col.value": "Value",
    "drill.ext.expander": "Extended fundamentals (live yfinance.info — click to fetch)",
    "drill.ext.fetch": "Fetch live",
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
}
