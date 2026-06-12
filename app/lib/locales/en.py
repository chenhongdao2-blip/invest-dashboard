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
    "strategy.metric.totalreturn_note": "Portfolio and benchmark are both **total return** (dividends included, gross, reinvested at ex-date; withholding tax not deducted); ex-dividend price drops are offset by the adjustment — apples-to-apples.",
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
    "common.provenance": "Source: {src} · as of {asof}",
    "strategy.metric.holdings_foot": "equal-weight · {n} scored",
    "strategy.metric.holdings_foot_weighted": "score-weighted · ~{cash:.0f}% cash buffer",
    "strategy.col.since": "Since entry %",
    "strategy.col.contrib": "Contrib %",
    "strategy.col.spark": "30D trend",
    "strategy.col.rank": "Rank",
    "strategy.holdings.title": "Top 20 holdings (by score rank · equal-weight)",
    "strategy.holdings.all": "All {n} scored (by score rank; top 20 = portfolio)",
    "strategy.metric.holdings_help": "Portfolio = top 20 by score, equal-weight; scored universe = {n}.",
    "strategy.metric.holdings_help_weighted": (
        "Portfolio = 20 names, quality-score-set weights, plus ~{cash:.0f}% cash buffer; "
        "weights shown are at-build and drift with price on the buy & hold curve."
    ),
    "strategy.holdings.title_weighted": "Top 20 holdings (by score rank · score-weighted + cash buffer)",
    "strategy.col.weight": "Weight %",
    "strategy.col.bucket": "Return source",
    "strategy.col.runrate": "Div yield %",
    "strategy.hd.bucket.rate": "Rate premium",
    "strategy.hd.bucket.nonrate": "Non-rate",

    # ── HD version group (v1 frozen history / v2 current / compare) ──
    "strategy.hd.version.toggle": "Portfolio version",
    "strategy.hd.version.v2": "v2 · 2026-06-11 (current)",
    "strategy.hd.version.v1": "v1 · 2026-03-20 (history)",
    "strategy.hd.version.compare": "v1 vs v2 compare",
    "strategy.hd.version.v1_note": (
        "Historical version: v1 is the official portfolio published 2026-03-20 "
        "(34-name scored universe · top 20 equal-weight). Its curve keeps running "
        "and constituents are frozen; the new book from 2026-06-11 is v2."
    ),
    "strategy.hd.compare.title": "High-dividend v1 vs v2 · NAV compare (each inception = 100)",
    "strategy.hd.compare.v1_line": "v1 (equal-weight, from 2026-03-20)",
    "strategy.hd.compare.v2_line": "v2 (score-weighted + cash buffer, from 2026-06-11)",
    "strategy.hd.compare.rebal_label": "v2 build 2026-06-11",
    "strategy.hd.compare.note": (
        "Basis: each curve is indexed to 100 at its own inception close — two "
        "independent books, not one chained NAV. Benchmark anchored at the v1 "
        "inception. v1 history is fully preserved, never truncated or restated."
    ),
    "strategy.hd.compare.metric.v1": "v1 since inception",
    "strategy.hd.compare.metric.v2": "v2 since inception",
    "strategy.hd.diff.title": "Rebalance detail (v1 top-20 book → v2)",
    "strategy.hd.diff.kept": "Kept ({n})",
    "strategy.hd.diff.added": "Added ({n})",
    "strategy.hd.diff.removed": "Removed ({n})",
    "strategy.hd.diff.col.v1w": "v1 weight %",
    "strategy.hd.diff.col.v2w": "v2 weight %",
    "strategy.hd.diff.col.sector": "Sector",
    "strategy.hd.diff.note": (
        "Computed automatically from the two holdings CSVs (never hand-filled). "
        "Comparison base is the v1 top-20 NAV book (equal-weight, 5.0% each); names "
        "ranked below 20 in the 34-name scored universe were not in the v1 book. "
        "v2 weights are at-build, 2026-06-11."
    ),
    "strategy.hd.v2.cash_note": (
        "The book carries a ~{cash:.0f}% cash buffer by design (not an error); the "
        "NAV treats cash at zero return — a conservative basis with no interest "
        "income credited."
    ),
    "strategy.col.ticker": "Ticker",
    "strategy.metric.delta_vs_bh": "{bp:+.0f} bp vs buy & hold",
    "strategy.onboarding.title": "How to read this page",

    # ── methodology footnotes ──
    "strategy.method.equal_weight": (
        "**Methodology** — Biotech & high-dividend v1: **top 20 by score, equal-weight**. "
        "High-dividend v2: **quality-score-set weights + ~12% cash buffer** (cash at zero "
        "return, conservative). Two curves from the pick date: "
        "**Buy & hold**: at-build weights at inception, then held (weights drift with price). "
        "**Monthly rebalance**: weights reset to the at-build book at each month start. "
        "Benchmark: XBI for biotech; HK high-dividend uses 3466.HK (Hang Seng High "
        "Dividend 30), with the Hang Seng Index as a broad-market reference."
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
    # ── Model Drill (analyst-model visualization) ──
    "model.title": "Analyst Model",
    "model.intro": "Reads the analyst's Excel model and visualizes revenue breakdown / margins / forecast + DCF — the detail the GAAP filing page can't show. Figures are analyst view, tracked apart from GAAP; forecasts (FYxxE) are translucent, never bare.",
    "model.none_any": "No analyst-model data in this environment yet.",
    "model.pick": "Company",
    "model.no_model": "No analyst model for {ticker}.",
    "model.fallback_link": "→ Ticker Drill / SEC Facts",
    "model.as_of": "Model: {ver} · source: {src}",
    "model.tp": "Target Price (DCF)",
    "model.dcf_sub": "WACC {wacc} · TG {tg}",
    "model.price": "Current",
    "model.as_of_date": "as of {d}",
    "model.model_ref": "Model base price {p} ({ver}); upside recomputed vs latest close",
    "model.upside": "Implied upside",
    "model.upside_sub": "target vs current",
    "model.rating": "Rating",
    "model.wiki_tp": "Wiki TP",
    "model.freq": "Periodicity",
    "model.freq_year": "Annual",
    "model.freq_quarter": "Quarterly",
    "model.sec.revenue": "① Revenue Breakdown",
    "model.revenue_cap": "**Teal depth = strategic segment** (deep = lead R&D, light = Commercial), **hatch = professional services** (solid = subscription); top label = lead segment's share of revenue. Solid = actual, translucent + dashed = analyst forecast (FYxxE). Units $bn. Each segment's share of DCF enterprise value is in the ③ value map. Source: analyst model Segment Summary.",
    "model.sec.margin": "② Margins (GAAP vs non-GAAP)",
    "model.margin_cap": "Grey dashed = GAAP, solid = non-GAAP. SaaS GAAP is depressed by SBC; non-GAAP is the sell-side pricing basis — **expand the bridge below** to decompose the gap (mostly SBC).",
    "model.bridge_expand": "▸ Expand GAAP → Non-GAAP bridge (mostly stock-based comp)",
    "model.sec.forecast": "③ Forecast + DCF",
    "model.ev_title": "DCF Enterprise Value by segment (NPV)",
    "model.sec.r40": "④ Valuation Matrix · Rule of 40",
    "model.r40_cap": "X = Rule of 40 (revenue growth + FCF margin), Y = EV/Sales. Hollow points = SaaS/AI software comps ({n}), red = current name; dashed = per-axis means, dotted = the Rule-of-40 = 40 line. Live from the daily snapshot (as of {d}, moves with the market). Source: yfinance (LOW — relative positioning only).",
    "model.r40_none": "No comp snapshot data yet — run jobs/fetch_eod.py for the software group first.",
    "model.scenario": "Analyst scenario notes",
    "model.sec.wiki": "④ Research View (LLM Wiki)",
    "model.wiki_full": "Expand full Wiki",
    "model.see_thesis": "→ Full research view on Ticker Drill",
    "model.disclaimer": "Data from analyst model {src} (analyst view, not filing basis; FYxxE are estimates). TP/DCF is a single-model base case — internal research only, not investment advice.",
    "model.public_desensitized": "📋 Public desensitized view — price target / DCF valuation removed; forecasts & ratios retained. Full valuation is internal/local only.",
    # ── ⑤ Analyst ratios (the divisions/multiples/forecasts SEC can't give) ──
    "model.sec.ratios": "⑤ Analyst Ratios",
    "model.ratios_cap": (
        "SEC gives only the atoms (receivables/revenue/net income/equity) — not the "
        "divisions, multiples or forecasts. This panel is the analyst model's incremental "
        "value: any multiple needing price/EV, any forecast FYxxE, or any basis choice "
        "(non-GAAP / turnover days / ROIC / cash conversion) is structurally absent from "
        "SEC. Figures are analyst view, incl. forecast, tracked apart from GAAP filings."
    ),
    "model.ratios_tag": "Analyst view (incl. forecast)",
    "model.ratios_annual_only": "annual only",
    "model.ratios_annual_only_tip": "not annualized / basis not comparable quarterly",
    "model.ratios_q_note": "Ratios default to the annual basis; quarterly shows only basis-comparable items (margins / Billings / customers).",
    "model.ratios_metric_col": "Metric",
    # group titles
    "model.ratios.g.valuation": "Valuation multiples",
    "model.ratios.g.profitability": "Profitability & returns",
    "model.ratios.g.efficiency": "Efficiency & working capital",
    "model.ratios.g.cash": "Cash & billings",
    "model.ratios.g.operational": "Operational",

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
    "strategy.name.hk_hd_v2": "HK High-Dividend v2 · Standard Build",
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
        "**Benchmark** — 3466.HK (Hang Seng High Dividend 30 ETF), with the Hang Seng "
        "Index shown as a broad-market reference.\n\n"
        "**Philosophy** — Buffett (shareholder-oriented mgmt / moat) · Munger (high ROE) · "
        "Marks (second-level thinking / risk control) · Graham (margin of safety)."
    ),
    "strategy.hd.v2.method": (
        "**This build** — v2 is the official standard build of 2026-06-11 (20 names, "
        "non-equal weights), run as a separate book from v1 (2026-03-20, 34-name "
        "scored universe · top 20 equal-weight); the v1 curve is fully preserved.\n\n"
        "**How it is built** — the portfolio is produced by an AI-native end-to-end "
        "research engine: quantitative screening, qualitative scoring and portfolio "
        "construction are all executed by Agents, with machine validation, independent "
        "review and full audit trails — fully automated from stock selection to "
        "portfolio build (see our 2026-06-10 report *From Vibe Coding to Agentic "
        "Engineering*).\n\n"
        "**Four portfolio rules** —\n"
        "1. **High deployment for income**: ~88% invested + ~12% cash buffer for "
        "rebalancing and tail volatility (NAV treats cash at zero return, conservative).\n"
        "2. **Quality score sets weights**: the *willing / able / durable to pay* quality "
        "framework carries over; higher score → higher weight.\n"
        "3. **Return-source structure anchored**: rate-premium bucket ~55% : non-rate "
        "~45%. First principles — high-dividend return is fundamentally a **rate risk "
        "premium**: banks earn the credit spread, utilities (gas / power) earn duration "
        "discounting; the non-rate bucket (consumer / energy / transport / gaming / "
        "healthcare) pays out of its own cash flow, hedging the book's rate sensitivity.\n"
        "4. **Concentration limit**: single name ≤10%, sectors reasonably diversified.\n\n"
        "**Yield basis** — yields shown are the annualized run-rate at build (as of "
        "2026-06-11).\n\n"
        "**Benchmark** — 3466.HK (Hang Seng High Dividend 30 ETF), with the Hang Seng "
        "Index shown as a broad-market reference; same as v1."
    ),
}
