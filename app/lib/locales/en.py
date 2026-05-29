"""English locale — Strategy Picks page (Phase 1). Other pages land in Phase 2.

Source of truth for keys; zh.py mirrors these exactly. Strategy methodology copy
is sourced from the CMS HK whitepapers (us-biotech v5.2 投资人简版 / high-dividend
methodology.md) — not invented. EN strategy copy gets a /ccg polish pass; CN copy
gets a GLM decision pass (per user instruction).
"""

STRINGS = {
    # ── page chrome ──
    "strategy.page.title": "AI-Agent Stock Picks · Performance",
    "strategy.page.caption": (
        "The agent reads data like an analyst, scores names across dimensions, and logs "
        "every decision for honest post-hoc review — a blend of data-scale and fundamental "
        "logic the industry calls quantamental (quant + fundamental)."
    ),
    "strategy.pitch": (
        "**What this is** — a live showcase of **AI-agent stock-picking**. The agent acts "
        "as an analyst: it reads clinical trials, FDA timelines, financials and governance, "
        "scores names across several dimensions, and builds the portfolio — and **every pick "
        "is logged the day it's chosen**, so months later we review against the original "
        "record, hits and misses alike.\n\n"
        "The three strategies below show **real since-inception returns vs benchmark** — not "
        "a polished backtest."
    ),
    "common.lang_label": "Language",

    # ── sidebar ──
    "strategy.sidebar.chart_settings": "Chart settings",
    "strategy.sidebar.show_individual": "Show individual ticker lines",
    "strategy.sidebar.show_individual_help": "Faint line for every holding — shows dispersion.",
    "strategy.sidebar.show_rebalanced": "Show monthly-rebalanced line",
    "strategy.sidebar.show_rebalanced_help": (
        "Overlay a dashed curve: equal weight RESET monthly (vs the solid buy-&-hold "
        "line whose weights drift). The gap shows how much weight-drift contributed."
    ),

    # ── header metrics ──
    "strategy.metric.pick_date": "Pick date",
    "strategy.metric.n_picks": "# picks",
    "strategy.metric.days_since": "Days held",
    "strategy.metric.benchmark": "Benchmark",
    "strategy.metric.port_bh": "Portfolio · buy & hold",
    "strategy.metric.port_rebal": "Portfolio · monthly rebal.",
    "strategy.metric.benchmark_ret": "Benchmark · {sym}",
    "strategy.metric.alpha": "Alpha (pp)",
    "strategy.delta.outperform": "outperform",
    "strategy.delta.underperform": "underperform",
    "strategy.delta.tied": "tied",

    # ── chart ──
    "strategy.chart.title": "{name} — indexed return since {date}",
    "strategy.chart.line.portfolio": "Top 20 (buy & hold)",
    "strategy.chart.line.rebalanced": "Top 20 (monthly rebalance)",
    "strategy.chart.line.band": "10th–90th %ile range",
    "strategy.chart.line.benchmark": "{sym} ({name})",
    "strategy.chart.y": "Indexed (start = 100)",

    # ── ranking tables ──
    "strategy.rank.top": "Top {n} (since entry)",
    "strategy.rank.worst": "Worst {n} (since entry)",
    "strategy.rank.all": "All {n} picks (sorted by since-entry)",
    "strategy.col.name": "Name",
    "strategy.col.score": "Pick score",
    "strategy.col.last": "Last",
    "strategy.col.since": "Since entry %",
    "strategy.col.rank": "Rank",
    "strategy.holdings.title": "Top 20 holdings (by score rank · equal-weight)",
    "strategy.holdings.all": "All {n} scored (by score rank; top 20 = portfolio)",
    "strategy.metric.holdings_help": "Portfolio = top 20 by score, equal-weight; scored universe = {n}.",
    "strategy.col.ticker": "Ticker",
    "strategy.metric.delta_vs_bh": "{bp:+.0f} bp vs buy & hold",
    "strategy.onboarding.title": "How to read this page",

    # ── methodology footnotes ──
    "strategy.method.equal_weight": (
        "**Methodology** — Portfolio = **top 20 by score, equal-weight**, from the pick date. Two curves: "
        "**Buy & hold**: equal weight at inception, then held (weights drift with price). "
        "**Monthly rebalance**: weights reset to equal at each month start. "
        "Benchmark: XBI for biotech, 3110.HK for HK high-dividend."
    ),
    "strategy.method.total_return": (
        "Portfolio and benchmark both use yfinance auto-adjusted closes "
        "(splits **and** dividends reinvested — i.e. total-return basis), so the "
        "comparison is like-for-like."
    ),
    "strategy.method.source": (
        "Picks produced by the AI-agent scoring system (synced weekly); prices fetched live "
        "via yfinance."
    ),

    # ── onboarding ──
    "strategy.onboarding.name": "Strategy page",
    "strategy.onboarding.body": (
        "**Cumulative return chart**\n"
        "- **Buy & hold (solid)**: equal weight at the pick date, then held — the curve "
        "that already shipped to clients.\n"
        "- **Monthly rebalance (dashed, optional)**: equal weight reset every month — the "
        "reproducible-strategy view.\n"
        "- **Benchmark (grey dashed)**: XBI or 3110.HK.\n"
        "- **10th–90th %ile band**: spread of the 80% middle of holdings; a wide band "
        "means big single-name dispersion.\n\n"
        "**Metrics** — **Alpha (pp)** = portfolio return minus benchmark, in percentage "
        "points. **Pick score** = the model's score at selection, where available."
    ),

    # ── strategy methodology (sourced) ──
    "strategy.method_expander": "How this strategy works",
    "strategy.name.v4_biotech": "US Biotech AI Picks 4.0",
    "strategy.name.v5_biotech": "US Biotech AI Picks 5.0",
    "strategy.name.hk_hd": "HK High-Dividend Picks",
    "strategy.v4.tag": "Lookback build",
    "strategy.v5.tag": "catalyst-monitor",
    "strategy.v4.method": (
        "**Universe** — full-market US biotech scan.\n\n"
        "**Selection** — names with a clinical / FDA catalyst in the next 12 months, scored on "
        "5 dimensions: Pipeline & clinical (40%) / Catalyst (25%) / M&A & strategic value (20%) / "
        "Financials & cash (10%) / Risk (5%).\n\n"
        "**This build · look-back validation** — 4.0 applies the framework to a historical window and "
        "checks the ranking against real subsequent moves. Over 24 trading days the basket beat XBI by "
        "~570bps with a 75% hit rate, and the model showed a **strong top-of-list (Top 5) edge** while "
        "mid-list ranking added little — a finding that directly drove the 5.0 upgrade.\n\n"
        "**Benchmark** — XBI (broad biotech ETF).\n\n"
        "⚠️ **Disclosure** — short look-back window, small sample; directional only, not indicative of "
        "future performance."
    ),
    "strategy.v5.method": (
        "**Universe** — full-market US biotech scan, split by market cap: Line A (≥ $30B large-cap, "
        "benchmarked to beat XBI) / Line B ($1B–<$30B mid/small-cap, targeting 10x).\n\n"
        "**Selection** — same 5-dimension scoring (Pipeline 40% / Catalyst 25% / M&A 20% / Financials "
        "10% / Risk 5%), but 5.0 **refines** it over 4.0: the catalyst dimension adds an *expectations "
        "gap* (the spread between market consensus on a trial\u2019s probability of success and "
        "the model\u2019s own estimate) and dynamically incorporates live market signals (flows + technicals).\n\n"
        "**This build · current forward version** — 5.0 is the latest live pick set (mid/small-cap Line B), "
        "now entering forward testing. Names selected in **both 4.0 and 5.0 (e.g. ARWR, CYTK, GMAB, JAZZ, "
        "BMRN) form the model\u2019s highest-conviction core basket**.\n\n"
        "**Benchmark** — XBI.\n\n"
        "⚠️ **Disclosure** — early-stage, small sample; ~60% of the score is AI subjective judgment (with a "
        "prudent haircut for potential hindsight bias). The next stage upgrades some manually-entered "
        "pipeline data to automated authoritative-source pulls + evidence checks; until that and a full "
        "forward test complete, output is **not investable-grade**."
    ),
    "strategy.biotech.method": (
        "**Universe** — full-market US biotech scan.\n\n"
        "**Selection** — names with a clinical / FDA catalyst in the next 12 months, "
        "scored on 5 dimensions:\n"
        "- Pipeline · clinical **40%** · Catalyst · events **25%** · M&A · strategic value "
        "**20%** · Financials · cash **10%** · Risk **5%**\n\n"
        "**Market-cap lines** — Line A (cap ≥ $30B): large-cap beta-enhancement, "
        "benchmarked to beat **XBI**. Line B ($1B–<$30B): mid/small-cap alpha, targeting "
        "10x. XBI is the benchmark as the broad biotech ETF proxy for Line A.\n\n"
        "**Rebalancing** — a new version (full re-pick) ships roughly monthly "
        "(4.0 → 5.0); within a version, positions are not adjusted.\n\n"
        "⚠️ **Honest caveats** — early-stage, small sample; ~60% of the score is AI subjective "
        "judgment (with a prudent haircut for potential hindsight bias). Until the next-stage data-automation upgrade + full "
        "forward test complete, output is **not investable-grade**."
    ),
    "strategy.hd.method": (
        "**Universe** — full HK market (~2,500) → quantitative pre-screen → ~34 candidates.\n\n"
        "**Hard filters** — 3-month avg turnover > HK$50m · dividend yield (TTM) > 5% · "
        "ROE > 7% · payout ratio 30–80% · cash buffer (reserves + retained earnings) / "
        "net profit > 3 · free cash flow > total dividends. (Financials & property exempt "
        "from the cash-flow test.)\n\n"
        "**Score (100 pts)** — Governance 55 (*willing to pay*) + Financial quality 25 "
        "(*able to pay*) + Moat 20 (*able to keep paying*).\n\n"
        "**Grades** — ≥80 excellent (core holding) · 60–79 good · 40–59 fair · <40 cut. "
        "(e.g. China Merchants Bank = 87, excellent.)\n\n"
        "**Bottom line** — current static dividend yield is **not** a scoring input "
        "(guards against cyclical-peak fake-high-yield).\n\n"
        "**Benchmark** — 3110.HK (Premia CSI Caixin China Bedrock Economy / HK high-"
        "dividend low-volatility).\n\n"
        "**Philosophy** — Buffett (shareholder-oriented mgmt / moat) · Munger (high ROE) · "
        "Marks (second-level thinking / risk control) · Graham (margin of safety)."
    ),
}
