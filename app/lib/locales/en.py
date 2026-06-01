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
        "This dashboard tracks opportunities along two strategy lines:\n"
        "- **(1) Catalyst-driven** — clinical readouts, FDA / NMPA approval milestones, "
        "earnings and governance events around biotech names, capturing the re-rating around "
        "the event; the first three tabs show real since-inception returns vs benchmark.\n"
        "- **(2) Multi-factor IPO subscription** — a six-factor model (free-float scarcity, "
        "cornerstone roster, sector momentum, subscription multiple, valuation, fundamentals) "
        "that scores and tiers HK new listings to quantify day-1 subscription odds; the last "
        "tab is a static cross-section backtest.\n\n"
        "Both lines share one data discipline: every figure carries a source and timestamp, "
        "sell-side consensus is kept separate from our own view, and conclusions are "
        "actionable. More industry domains will be added over time."
    ),

    # ── IPO subscription strategy (static cross-section backtest) ──
    "strategy.name.ipo": "HK IPO Subscription",
    "strategy.ipo.tab.intro": (
        "**HK IPO Subscription Backtest** — scores and tiers recent HK new listings via the "
        "CMSI Prism six-factor model (v6.7) and revisits how score relates to day-1 performance. "
        "The 3 cards up top show scale and the day-1 range (sample / best / worst); the "
        "**by-tier table** below lists, from top tier to bottom, the count, median day-1, up-rate "
        "and breaks — so you can see at a glance **whether a higher score actually does better**. "
        "Key read: **the score is good at direction (subscribe or not, avoiding breaks), not at "
        "magnitude (how much it pops)** — the middle tiers barely separating is the evidence. "
        "Further down: mini-charts show each name's intraday path, and the dual leaderboard sorts "
        "by score or by day-1 return."
    ),
    # KPI
    "strategy.ipo.kpi.sample": "Sample",
    "strategy.ipo.kpi.sample_delta": "{listed} listed / {pending} pending",
    "strategy.ipo.kpi.max": "Top day-1",
    "strategy.ipo.kpi.max_delta": "{name}",
    "strategy.ipo.kpi.worst": "Worst day-1",
    "strategy.ipo.kpi.worst_delta": "{name}",
    # By-tier staircase table (replaces the contrast cards — reads "does higher score = better?")
    "strategy.ipo.tier.title": "By-tier performance — does a higher score do better?",
    "strategy.ipo.tier.col.tier": "Tier",
    "strategy.ipo.tier.col.n": "n",
    "strategy.ipo.tier.col.med": "Median d1",
    "strategy.ipo.tier.col.win": "Up rate",
    "strategy.ipo.tier.col.brk": "Broke",
    "strategy.ipo.tier.note": (
        "Read top-to-bottom: the model nails the **extremes** (Strong-Buy+ best / Avoid broke) "
        "but the middle tiers (Strong-Buy / Subscribe / Cautious) barely separate — the score is "
        "useful for **direction (whether to subscribe), not for ranking magnitude**. Tiers are "
        "small (n=17 total); pending more listings. Internal research backtest; not subscription advice."
    ),
    # scatter
    "strategy.ipo.scatter.title": "Score × Day-1 Return (n={n} listed)",
    "strategy.ipo.scatter.x": "Six-factor score",
    "strategy.ipo.scatter.y": "Day-1 return %",
    "strategy.ipo.scatter.trend": "OLS trend",
    "strategy.ipo.scatter.rho": "Spearman ρ = {rho:.2f} (p={p}, not significant)",
    "strategy.ipo.scatter.hover": "{name} ({code}) · score {score:.1f} · day-1 {ret:+.0f}% · {tier}",
    "strategy.ipo.scatter.caption": (
        "This is an ADMISSION FILTER, not a MAGNITUDE predictor — a high score locks in the "
        "*win-rate* (avoiding breaks), not the *payoff*: score is only weakly, non-significantly "
        "related to day-1 magnitude (Spearman ρ = 0.13, p = 0.62). Dots are coloured by "
        "subscription tier; a **red ring marks day-1 breakers** (e.g. UISEE, a Subscribe-tier "
        "name, still closed −4.6%). The trend line is a mean-level reference only (dashed; wide CI)."
    ),
    # intraday small-multiples
    "strategy.ipo.intraday.title": "Listing-day intraday path (% vs offer; ends at the day-1 close)",
    "strategy.ipo.intraday.caption": (
        "Y-axis is **% vs the offer price**, so each line **ends exactly at the day-1 close "
        "return shown in its mini-title**; the dashed line = offer price (0% breakeven). Most "
        "day-1 gains are locked in at the opening auction, so high-open names trade nearly flat "
        "intraday (e.g. Lightelligence is ~+384% by 09:35 and stays there), while names like "
        "Top NC keep climbing post-open. Line color keys off the day-1 close sign (teal up / red down)."
    ),
    "strategy.ipo.intraday.mini_title": "{name} {ret:+.0f}%",
    "strategy.ipo.intraday.hover": "{time} · {path:+.1f}% vs offer",
    # dual leaderboard
    "strategy.ipo.rank.toggle": "Sort by",
    "strategy.ipo.rank.by_score": "By score",
    "strategy.ipo.rank.by_ret": "By day-1 return",
    "strategy.ipo.rank.pending": "Pending ({date})",
    # rank table columns
    "strategy.ipo.col.rank": "Rank",
    "strategy.ipo.col.code": "Code",
    "strategy.ipo.col.name": "Name",
    "strategy.ipo.col.score": "Score",
    "strategy.ipo.col.tier": "Subscription Tier",
    "strategy.ipo.col.sub_sector": "Sub-sector",
    "strategy.ipo.col.day1_ret": "Day-1 Return",
    "strategy.ipo.col.source": "Source",
    # methodology
    "strategy.ipo.method_expander": "How this strategy works · Six-factor scoring v6.7",
    "strategy.ipo.method": (
        "**HK IPO Six-Factor Scoring Framework (CMSI Prism Subscription Card · v6.7)**\n\n"
        "Each new listing is weighted-scored across six dimensions (max 10; v6.7 reweighting) and "
        "mapped to a four-tier subscription call. **This is distinct from the biotech-catalyst "
        "framework's clinical / FDA / earnings / governance dimensions** — IPO scoring assesses "
        "listing-day pricing dynamics and supply-demand, not long-run fundamentals.\n\n"
        "| # | Factor | What it measures (v6.7) |\n"
        "|---|---|---|\n"
        "| ① | Free-float scarcity (FF master switch) | Tighter float = sharper contest; v6.7 uses a **piecewise curve** (steep bonus <5% / flattened 6–12% / stepped penalty >15%) and reads the **absolute free-float HK$**, not just the percentage |\n"
        "| ② | Cornerstone / institutional backing | Cornerstone quality tier (A/B/C) × share of offering + intl-placement oversubscription + sovereign anchor capital + sponsor win-rate |\n"
        "| ③ | Sector scarcity / momentum | Scarce theme (photonic-AI, AI-drug discovery) + sector sentiment + **secondary anchor** (peer 30-day break rate) |\n"
        "| ④ | Public-offer subscription multiple | Retail oversubscription (bucketed); **downweighted in v6.7** — in a universal-pop regime everyone is >1000×, so the single factor's discrimination is flattened by β |\n"
        "| ⑤ | Valuation reasonableness | v6.6+ uses **floor logic**: an inverted primary valuation (pre-IPO multiple too high) caps the total score, rather than simple weighting |\n"
        "| ⑥ | Fundamentals & financial quality | Revenue growth, margins, cash, path-to-profit; weakly related to day-1, used mainly for the holding period |\n\n"
        "**Four tiers:**\n"
        "- Score ≥ 7.5 → **Strong Buy+**\n"
        "- 6.0 – 7.4 → **Subscribe**\n"
        "- 5.0 – 5.9 → **Cautious**\n"
        "- < 5.0 → **Avoid**\n\n"
        "**Backtest read (n=17 listed):** as an **admission filter** the score has marginal value "
        "— the Subscribe tier (≥6.0) broke issue on day 1 in **9.1%** of cases vs **16.7%** for "
        "the Cautious/Avoid tiers (full sample 11.8%). But it has almost no power over the "
        "*magnitude* of day-1 returns (Spearman ρ=0.13, p≈0.61; the two biggest winners — "
        "DeepZero +266% / SUNMI +241% — both sit in the <6.0 tier): **the score is a filter for "
        "\"whether to subscribe / avoid breaks,\" not a predictor of \"how much it pops.\"**\n\n"
        "**Where day-1 alpha comes from (alpha attribution, vetted by a 4-way /cccg debate):** "
        "day-1 moves are driven mainly by **primary-market microstructure** — A/H discount "
        "(secondary listings anchored to the A-share price; Mabwell closed +0.6%, near-bottom), "
        "**absolute free-float** (scarcer = easier squeeze), and the **intl-placement × deal-size** "
        "balance. The company-quality score should **move off the day-1 card and serve the holding "
        "period instead**. This rests on n=17 in a single universal-pop regime — "
        "**hypothesis-generating, not validated** — pending confirmation at n≥30."
    ),
    "strategy.ipo.caveat": (
        "Day-1 figures are a snapshot frozen on the listing date and do not update with later "
        "trading; this page is a strategy backtest, not a live-monitoring tool. Intraday "
        "mini-charts are plotted as % vs the offer price, so each line ends exactly at its "
        "labelled day-1 close return. With only 17 listed names, conclusions are sensitive to "
        "small-sample and right-tail outliers and do not constitute investment advice."
    ),
    "strategy.ipo.source": (
        "Source: CMSI Prism backtest card / Futu day-1 close / iFind pricing. Day-1 figures are a "
        "frozen snapshot and do not update with subsequent trading. With ~18 names the tier "
        "win-rates need more samples to confirm; past performance does not indicate future "
        "results — internal quant research only, not investment or subscription advice."
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
