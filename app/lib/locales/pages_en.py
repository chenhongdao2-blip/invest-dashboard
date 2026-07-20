"""English locale — Phase 2 (Home + 5 healthcare pages + shared components).

Merged with en.py (Phase 1 strategy keys) by lib.i18n. Kept separate so Phase 1
stays untouched and per-page wiring can proceed without locale-file contention.
Onboarding bodies are translations of the (originally Chinese) in-page help text.
"""

STRINGS = {
    # ── Sector Rotation (RRG) ──
    "rot.title": "Sector Rotation · RRG",
    "rot.caption": "Relative-rotation map — each sector's relative strength × momentum vs its market benchmark. An internal attention map, not a timing signal.",
    "rot.ctrl.header": "RRG controls",
    "rot.ctrl.tail": "Tail length (weeks)",
    "rot.ctrl.tail_help": "Weeks of trajectory drawn behind each sector dot.",
    "rot.ctrl.thr": "Overheat threshold (z)",
    "rot.ctrl.thr_help": "A Leading sector is flagged [HOT] when its crowding z-score exceeds this.",
    "rot.tab.a": "A-share · SW/CSI",
    "rot.tab.hk": "HK · HSCI",
    "rot.note.hk": "HK crowding = sector turnover-rate z-score (iFind weekly). Sectors = 11 Hang Seng Composite Industry indices vs HSI.",
    "rot.empty.hk": "No HK sector data — run jobs/load_sw_industry.py.",
    "rot.tab.us": "US · GICS",
    "rot.note.a": "A-share crowding = sector turnover-rate z-score (iFind weekly). Sectors = standard Shenwan Level-1 31 industries vs CSI 300.",
    "rot.note.us": "US crowding = price-extension z (close vs 200-DMA) — an overbought proxy, not true turnover/breadth (v2). Sectors = 11 GICS SPDR ETFs vs S&P 500.",
    "rot.empty.a": "No A-share sector data — run jobs/load_sw_industry.py.",
    "rot.empty.us": "No US benchmark data — run jobs/fetch_eod.py.",
    "rot.tab.drill": "US · Stock drill",
    "rot.drill.domain": "Domain",
    "rot.drill.sector": "Sector",
    "rot.drill.topn": "Show top",
    "rot.drill.topn_help": "Plot the top-N constituents by 20-day turnover (liquidity); the synthetic sector index still uses all constituents.",
    "rot.drill.empty": "Not enough constituent price history to drill this sector.",
    "rot.drill.trunc": "Showing top {shown}/{total} constituents by liquidity (composite uses all {total}).",
    "rot.drill.short": "{n} more constituent(s) excluded for insufficient price history (< ~22 weeks); they join automatically once backfilled.",
    "rot.note.drill": "Stock drill: constituents vs an **equal-weight synthetic sector index** (not the market), answering \"who leads/lags inside the sector\". Crowding = single-stock price-extension z (close vs 50-DMA, short-window overbought proxy). ⚠️ Single-stock prices span only ~9 months (prices_daily), so effective RRG history is short — read as intra-sector structure only.",
    "rot.tab.xmkt": "Cross-market · USD",
    "rot.xmkt.markets": "Markets",
    "rot.xmkt.pern": "Sectors / market",
    "rot.xmkt.pern_help": "Plot the top-N most-deviated sectors (distance from origin) per market to avoid clutter.",
    "rot.xmkt.pick": "Select at least one market.",
    "rot.xmkt.empty": "Missing cross-market data — run jobs/fetch_fx_world.py (URTH/FX) and jobs/load_sw_industry.py (SW/HS).",
    "rot.xmkt.panel_frozen": "↑ Incl. FX (USD overlay)  /  ↓ FX-stripped (local-driven, FX frozen at start) — a sector's shift between the two = its FX beta (guardrail ③).",
    "rot.note.xmkt": "Cross-market: A/HK/US sectors converted to USD vs MSCI World (URTH, developed markets). Color = market; URTH is a developed-markets yardstick for global relative strength only. ⚠️ A/HK use SW/HS weekly seeds (~52w); US uses GICS ETF daily — slightly different cadence. Crowding (guardrail ②) lives in the single-market tabs.",
    "rot.onboard.title": "How to read the RRG",
    "rot.onboard.body": (
        "**Four quadrants, clockwise:** Improving (weak but recovering) → Leading (strong & improving) "
        "→ Weakening (strong but fading) → Lagging (weak & deteriorating).\n\n"
        "- **X = RS-Ratio** (relative strength vs benchmark); **Y = RS-Momentum** (its rate of change). Origin = 100/100.\n"
        "- **Dot** = sector now; **tail** = recent weekly trajectory.\n"
        "- **Red ring [HOT]** = Leading **and** crowded — guardrail ② flags the danger zone RRG itself can't see (positioning).\n"
        "- **Regime banner** = guardrail ① — tactical vs strategic qualification from the cycle backdrop.\n\n"
        "**First principle:** RRG describes the relative state that has *already happened* (high-confidence fact), "
        "not future direction (no predictive power). It answers \"how far along,\" not \"up next?\""
    ),

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
    # hub.tbl.* — Market Hub tables (market_hub_tables iframe, zip5 design)
    "hub.tbl.sp.title": "S&P 500 Sector Performance",
    "hub.tbl.sp.sub": "11 GICS level-1 sectors (SPDR Select Sector ETF proxies) · ranked by YTD by default · click headers to sort",
    "hub.tbl.hc.title": "Healthcare · Benchmarks",
    "hub.tbl.hc.sub": "Healthcare benchmark ETFs · vs S&P = YTD excess · click headers to sort",
    "hub.tbl.movers.title": "Top Movers · 1D",
    "hub.tbl.movers.sub": "Healthcare coverage pool · ranked by 1D move · prices in local currency",

    "cov.title": "CMSI Coverage",
    "cov.caption": "28-ticker official cover list — HK 15 / US 10 / CN A-share 3. Latest data: {date}",
    # cov.tbl.* — Coverage glass-card table (coverage_table iframe, zip5 design)
    "cov.tbl.tab.hk": "HK",
    "cov.tbl.tab.us": "US",
    "cov.tbl.tab.cn": "CN",
    "cov.tbl.tab.all": "ALL",
    "cov.tbl.bench.own": "Own benchmark",
    "cov.tbl.cover": "COVERAGE",
    "cov.tbl.mcap_total": "TOTAL MCAP",
    "cov.tbl.ytd_med": "YTD MEDIAN",
    "cov.tbl.bench_prefix": "",
    "cov.tbl.beat_label": "Beat ",
    "cov.tbl.unit_names": "names",
    "cov.tbl.median": "Coverage median",
    "cov.tbl.grp_ret": "RETURNS %",
    "cov.tbl.grp_exc_prefix": "vs ",
    "cov.tbl.grp_val": "VALUATION ×",
    "cov.tbl.col.t": "Ticker",
    "cov.tbl.col.n": "Name",
    "cov.tbl.col.mcap": "Mcap $B",
    "cov.tbl.col.ytd": "YTD",
    "cov.tbl.col.m1": "1M",
    "cov.tbl.col.d5": "5D",
    "cov.tbl.col.d1": "1D",
    "cov.tbl.col.exc_prefix": "",
    "cov.tbl.col.exc": "Excess",
    "cov.tbl.col.exc_suffix": "",
    "cov.tbl.col.peS": "Trail P/E",
    "cov.tbl.col.peF": "Fwd P/E",
    "cov.tbl.col.evE": "EV/EBITDA",
    "cov.tbl.footnote": (
        "Mcap in USD bn; returns are USD total return (incl. FX); multiples from the yfinance "
        "snapshot (as of {date}); negative/zero multiples shown as NM; Excess = stock YTD − "
        "market benchmark YTD (pp). Names with a model carry a red ● badge."
    ),
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
    "hc.section.benchmark": "Domain Benchmark & Peers",
    "hc.section.benchmark_meta": "XLV · XBI · XPH · IXJ · IHF · IHI",
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
    # ── Relative performance (Jonah: HSHCI vs HSI/HSTECH · NBI vs Nasdaq · S&P HC vs S&P) ──
    "hc.rs.section": "Relative Performance",
    "hc.rs.section_meta": "5 index pairs · re-anchored within window",
    "hc.rs.win.meta": "REBASED = 100 · common trading days inner-joined · each card has its own window toggle (top-right); switching re-anchors at the window's first day",
    "hc.rs.kicker.hk": "01 · HK LENS · HANG SENG",
    "hc.rs.kicker.msci": "02 · MSCI CHINA · ETF PROXY",
    "hc.rs.kicker.nbi": "03 · US BIOTECH",
    "hc.rs.kicker.sphc": "04 · S&P HEALTH CARE",
    "hc.rs.kicker.aibio": "05 · BIOTECH VS AI HARDWARE",
    "hc.rs.footnote": (
        "Basis: within each panel, all series are inner-joined on common trading days and "
        "re-anchored to 100 at the selected window's first day; the pp badge = the red hero "
        "line's cumulative excess vs that peer within the window (hero − peer, rebased points). "
        "5D = last 5 common sessions; 1M / 6M by calendar lookback."
    ),
    "hc.rs.hk.title": "Hang Seng Healthcare vs Hang Seng vs Hang Seng TECH",
    "hc.rs.msci.title": "MSCI China Health Care vs MSCI China (ETF proxy: KURE / MCHI)",
    "hc.rs.msci.src": "yfinance · ETF proxy (total return · USD)",
    # GLOSSARY structured card (zip4 design; replaces the old hc_indices_note prose)
    "hc.rs.gl.eyebrow": "GLOSSARY",
    "hc.rs.gl.title": "Two China-healthcare indices — how they differ",
    "hc.rs.gl.sub_right": "Panels 01 / 02 above",
    "hc.rs.gl.comp_label": "COMP",
    "hc.rs.gl.feat_label": "TRAIT",
    "hc.rs.gl.how_label": "HOW TO USE",
    "hc.rs.gl.note_right": "They diverge — a basis difference, not a data error",
    "hc.rs.gl.badge1": "HSHCI",
    "hc.rs.gl.name1": "Hang Seng Healthcare",
    "hc.rs.gl.tag1": "HK-healthcare beta",
    "hc.rs.gl.chip1a": "Purely offshore · no A-shares",
    "hc.rs.gl.chip1b": "HKD · price index · ex-dividend",
    "hc.rs.gl.comp1": "HK-listed healthcare: innovative pharma / biotech / devices / services",
    "hc.rs.gl.feat1": "Biotech-heavy, volatile",
    "hc.rs.gl.badge2": "MSCI · KURE",
    "hc.rs.gl.name2": "MSCI China Health Care",
    "hc.rs.gl.tag2": "All-China healthcare beta",
    "hc.rs.gl.chip2a": "A-shares + H-shares + ADRs",
    "hc.rs.gl.chip2b": "USD ETF · total return",
    "hc.rs.gl.comp2": "KURE tracks MSCI China All Shares Health Care, incl. A-share giants like Hengrui & Mindray",
    "hc.rs.gl.feat2": "Broader basis; A-share inclusion dampens the HK biotech swings",
    "hc.rs.gl.how1": (
        'For the <b>HK-healthcare de-positioning / biotech</b> story → use <span style="font-family:'
        "'JetBrains Mono',monospace;font-size:11px;font-weight:700;color:#c8102e;\">HSHCI</span>"
    ),
    "hc.rs.gl.how2": (
        'For <b>all-China healthcare beta</b> → use <span style="font-family:'
        "'JetBrains Mono',monospace;font-size:11px;font-weight:700;color:#1a1a1a;\">MSCI (KURE)</span>"
    ),
    "hc.rs.nbi.title": "Nasdaq Biotech (NBI) · S&P Biotech (XBI) vs Nasdaq Composite",
    "hc.rs.sphc.title": "S&P 500 Health Care vs S&P 500",
    "hc.rs.aibio.title": "Biotech (NBI large-cap · XBI equal-weight) vs AI Hardware (PHLX Semis, SOX)",
    "hc.rs.aibio.note": (
        "**How to read it.**　The two hottest themes on one anchor (last Aug): **red = biotech** "
        "(solid NBI, market-cap-weighted large-cap / red-dashed XBI, S&P Biotech equal-weight = the "
        "SMID-cap breadth read), **teal = AI hardware** (^SOX, PHLX Semiconductor).　"
        "**① The NBI–XBI gap** = large- vs small/mid-cap biotech: XBI leading = broad SMID-cap "
        "participation (M&A / small-cap squeeze); XBI lagging = gains concentrated in the megacaps, "
        "weak breadth.　**② the biotech-vs-AI scissor** = the relative rotation between "
        "the two themes — when AI hardware leads for long, biotech tends to get starved of flow; a "
        "converging / reversing scissor often flags a risk-appetite or rate-expectations shift.　"
        "All three same-basis rebased — beta only, no single-name alpha."
    ),
    "hc.rs.ylabel": "Rebased (start = 100)",
    "hc.rs.read": (
        "HK healthcare is the lone bear (−22.4pp vs HSI), driven by **China-specific risk** "
        "(HK liquidity drain / VBP procurement / NRDL price cuts) — not a global healthcare "
        "de-rating: NBI tracked the Nasdaq, so global biotech didn't weaken in step. US "
        "large-cap healthcare's −9.3pp is the drug-pricing (IRA/PBM) + managed-care MLR de-rating."
    ),
    "hc.rs.lag": "{hero} lagged {peer} by {pp}pp",
    "hc.rs.lead": "{hero} led {peer} by {pp}pp",
    "hc.rs.flat": "{hero} ≈ flat vs {peer}",
    "hc.rs.empty": "No index-comparison data — run jobs/build_hc_overview_data.py to backfill.",
    # HSHCI full-cycle path (−70% → doubled → pullback)
    "hc.rs.hshci.kicker": "06 · HK LENS · FULL CYCLE",
    "hc.rs.hshci.chip": "Monthly close · absolute level",
    "hc.rs.hshci.src": "iFind monthly close (latest daily endpoint)",
    "hc.rs.hshci.vs_peak": "vs peak",
    "hc.rs.hshci.vs_start": "vs start",
    "hc.rs.hshci.title": "Hang Seng Healthcare: full cycle since Jul 2021 (index level)",
    "hc.rs.hshci.ylabel": "Index level",
    "hc.rs.hshci.ann.start": "High {c:,.0f}",
    "hc.rs.hshci.ann.trough": "Trough {c:,.0f} ({p:+.0%})",
    "hc.rs.hshci.ann.peak": "Rebound {c:,.0f} ({p:+.0%})",
    "hc.rs.hshci.ann.now": "Now {c:,.0f} ({p:+.0%})",
    "hc.rs.hshci.caption": (
        "Full path: {start_d} high {start_c:,.0f} → {trough_d} trough {trough_c:,.0f} "
        "({trough_pct:+.0%} from high) → {peak_d} rebound {peak_c:,.0f} ({peak_pct:+.0%} off the low) "
        "→ {now_d} {now_c:,.0f} ({now_peak:+.0%} vs peak; {now_start:+.0%} vs start). "
        "Source: iFind monthly close, as of {asof}."
    ),
    # ── Japan Healthcare (region universe: hc_japan.yml, 40 names) ──
    "hc.jp.section": "Japan Healthcare",
    "hc.jp.section_meta": "40 names · iFind watchlist (May 2026) · returns in USD",
    "hc.jp.sub.pharma": "Pharma",
    "hc.jp.sub.medtech": "Medtech",
    "hc.jp.sub.diagnostics": "Diagnostics & Testing",
    "hc.jp.sub.distribution": "Distribution & Services",
    "hc.jp.col.subsector": "Subsector",
    "hc.jp.chart.title": "Japan HC composite vs TOPIX vs Nikkei 225 (USD)",
    "hc.jp.hero": "Japan HC composite (40 names, cap-weighted)",
    "hc.jp.bench.topix": "TOPIX (1305.T ETF proxy)",
    "hc.jp.bench.n225": "Nikkei 225",
    "hc.jp.kicker": "JAPAN HC · USD BASIS",
    "hc.jp.caption": (
        "Composite = market-cap-weighted across 40 names (weights = May-2026 mcap snapshot, "
        "normalized at the composite's base date, independent of the selected window); "
        "all three series in USD (FX included; FX largely cancels in the relative "
        "spread); TOPIX proxied by the 1305.T ETF. Window re-anchoring and the pp badges "
        "follow the Relative Performance section above. Source: yfinance EOD cron, "
        "as of {asof}."
    ),
    "hc.jp.detail": "All 40 names (by subsector · USD)",
    "hc.jp.read": (
        "Read Japan healthcare **by pricing currency**, not by the return column: "
        "Daiichi Sankyo (ADC: Enhertu/Datroway), Eisai (Leqembi) and the medtech trio "
        "(Terumo/HOYA/Olympus) are **globally-priced assets** — revenue mostly in "
        "USD/EUR, so a weak yen is a tailwind. The distributors (Medipal/Alfresa/"
        "Suzuken/Toho) and generics (Sawai/Towa) are **domestically-priced assets** — "
        "squeezed by biennial drug-price revisions and payer tightening, with a weak "
        "yen inflating their import costs. The composite-vs-TOPIX spread strips market "
        "beta (both legs in USD, so FX largely cancels) and answers \"is Japan "
        "healthcare beating its own market\"; for single names, go back to the "
        "layering above."
    ),
    "hc.jp.note_delisted": (
        "Two names from the original 42-name list removed on going-private delistings: "
        "HOGY MEDICAL (3593, Carlyle TOB, delisted May 2026) and Hisamitsu (4530, MBO)."
    ),
    "hc.jp.empty": "No Japan universe on file — run jobs/load_universe.py to backfill.",
    # ── Institutional positioning · offshore China funds' OW/UW on healthcare ──
    "hc.pos.section": "Institutional Positioning · Offshore China Funds' OW/UW on Healthcare",
    "hc.pos.section_meta": "12 offshore China-equity funds · vs own benchmark · as of 31 Mar 2026",
    "hc.pos.chart.title": "Healthcare deviation (fund weight − benchmark weight)",
    "hc.pos.chart.xlabel": "Deviation from benchmark (pp)",
    "hc.pos.legend": "🟢 teal = OW　🔴 red = UW　·　color shows **positioning tilt**, not a daily price move",
    # Counts-only headline — always valid, no direction/AUM-tilt/frozen numbers (safe with no data).
    "hc.pos.verdict": (
        "**Verdict**: near-neutral by fund count — {n_ow} OW / {n_uw} UW / {n_neu} Neutral "
        "({n_na} undisclosed)."
    ),
    # Directional tilt — page renders this ONLY when data_available (real AUM backs it).
    "hc.pos.verdict_tilt": (
        "On an **AUM-weighted basis, a modest net underweight ({aum_pp}pp)** — the largest "
        "fund (3.3bn) is firmly UW at −3.8pp, while the 2nd-largest sits marginally OW "
        "(+1.1pp); the real OW conviction is in smaller mandates (up to +6.7pp)."
    ),
    "hc.pos.read": (
        "Big money is still cutting, and accelerating (the deepest −3.4 to −3.8pp over the "
        "year) — resonating with HK healthcare's −22pp lag vs HSI into a 'de-positioning + "
        "valuation kill.' A few smaller funds are creeping back toward neutral — a contrarian "
        "probe, not the turn. Stance: **contrarian, scaled-in** — track the chip bottom, "
        "don't catch the falling knife."
    ),
    "hc.pos.col.fund": "Fund",
    "hc.pos.col.aum": "AUM (USD)",
    "hc.pos.col.bm": "Benchmark",
    "hc.pos.col.fund_hc": "Fund HC%",
    "hc.pos.col.bm_hc": "BM HC%",
    "hc.pos.col.dev": "Deviation",
    "hc.pos.col.stance": "OW/UW",
    "hc.pos.col.chg": "Δ vs last yr",
    "hc.read.eyebrow": "TAKEAWAY",
    "hc.pos.stance.OW": "OW",
    "hc.pos.stance.UW": "UW",
    "hc.pos.stance.Neutral": "Neutral",
    "hc.pos.stance.SlightlyOW": "Slightly OW",
    "hc.pos.stance.NA": "N/A",
    "hc.pos.source": "Source: ",
    "hc.pos.note_ai": "Read generated by finance / pharma research Agents from the table above; no rating or target price is shown or relied upon.",
    "hc.pos.empty": "No fund-positioning data — run jobs/build_hc_overview_data.py to backfill.",
    # ── US HC-dedicated funds 13F · consensus holdings + QoQ moves ──
    "hc.f13.section": "US Healthcare Funds 13F · Consensus Holdings & Quarterly Moves",
    "hc.f13.section_meta": "12 US HC-dedicated funds · SEC EDGAR 13F-HR · US-listed longs only",
    "hc.f13.verdict": (
        "**Verdict**: across {n_funds} funds (~${aum}bn combined 13F value, period {period}), "
        "the highest-consensus holding is **{top}** ({top_n} funds hold it); "
        "the hottest new buy this quarter is **{hot}** ({hot_n} funds initiated together)."
    ),
    "hc.f13.consensus_h": "**Consensus holdings matrix** (top-15 consensus names × holders; cell = that fund's position, $M)",
    "hc.f13.consensus_note": "Column headers: 6M closes + move since quarter end; cell color = that fund's own QoQ move in the name; 13F excludes shorts and non-US lines.",
    "hc.f13.mx.holder": "Holder",
    "hc.f13.mx.total": "Total",
    "hc.f13.mx.unch": "unmarked = unchanged",
    "hc.f13.newbuys_h": "**Hottest new buys this quarter** (multiple funds initiating together)",
    "hc.f13.exits_h": "**Crowded exits this quarter** (multiple funds selling out together)",
    "hc.f13.perfund_h": "**Per-fund detail** (top-15 holdings + that fund's QoQ moves)",
    "hc.f13.legend": "🟢 teal = NEW/ADD　🔴 red = TRIM/EXIT　·　color shows **quarterly repositioning**, not a daily price move",
    "hc.f13.read": (
        "13F shows **US-long positioning as of the report date** (up to 45 days stale). The alpha "
        "sits in two places: ① multi-fund same-quarter NEW buys = a smart-money convergence signal "
        "worth checking pipeline + catalysts name by name; ② crowded exits are usually failed "
        "readouts / take-outs / de-crowding — triage each. Consensus holdings are crowded by "
        "construction — treat this as a map of specialist attention, not a buy list."
    ),
    "hc.f13.source": "Source: SEC EDGAR 13F-HR (public filings, up to 45 days after quarter end) · auto-fetched by jobs/fetch_13f_hc_funds.py",
    "hc.f13.empty": "No 13F data — run jobs/fetch_13f_hc_funds.py to backfill.",
    "hc.f13.none": "Nothing recorded this quarter.",
    "hc.f13.positions": "positions",
    "hc.f13.col.name": "Name",
    "hc.f13.col.n_funds": "Held by",
    "hc.f13.col.value": "Combined value",
    "hc.f13.col.new": "New",
    "hc.f13.col.add": "Add",
    "hc.f13.col.trim": "Trim",
    "hc.f13.col.n_exits": "Exits",
    "hc.f13.col.funds": "Funds",
    "hc.f13.col.spark": "6M trend",
    "hc.f13.col.since_qend": "Since Q-end",
    "hc.f13.col.weight": "Weight",
    "hc.f13.col.qoq": "QoQ",
    "hc.f13.col.chg": "Shares Δ%",
    "hc.f13.qoq.NEW": "NEW",
    "hc.f13.qoq.ADD": "ADD",
    "hc.f13.qoq.TRIM": "TRIM",
    "hc.f13.qoq.UNCH": "UNCH",
    "hc.f13.prices_note": (
        "Trend & Since-Q-end use closes as of {asof} (yfinance), anchored at the 13F report "
        "date {period} — i.e. market action **after** the funds' snapshot, to gauge how much "
        "of the signal is already priced in."
    ),
    # --- Headcount change (hirers vs cutters) ---
    "hc.hc.section": "Headcount Change · China Innovative-Pharma Hirers vs Cutters",
    "hc.hc.section_meta": "12 China innovative-pharma / biotech · FY2024 → FY2025 · group total employees",
    "hc.hc.chart.title": "Headcount change (FY2024 → FY2025)",
    "hc.hc.chart.xlabel": "Headcount change (people)",
    "hc.hc.legend": "🟢 teal = hiring　🔴 red = cutting　·　color shows **headcount move**, not a daily price move",
    "hc.hc.verdict": (
        "**Bottom line**: of 12, {n_hire} hiring / {n_cut} cutting, net {net:+,} people. "
        "Biggest hirer {top_hire_name} ({top_hire_delta:+,}), biggest cutter {top_cut_name} ({top_cut_delta:+,})."
    ),
    "hc.hc.read": (
        "Unlike Western big pharma's 2025 layoffs (Sanofi / Novo / Pfizer each shedding thousands), "
        "China innovative pharma is **still hiring in 10 of 12 names** — the commercial-ramp biotechs "
        "(Innovent +33%, Akeso +24%, Keymed +17%) are expanding fastest, consistent with a launch-cycle, "
        "not a retrenchment. The two cutters are the traditional large caps (Sino Biopharm, CSPC), "
        "trimming legacy generics / sales headcount mid-transition — a different story from the biotech build-out. "
        "Read: **headcount is a leading signal of operating posture** — where hiring concentrates is where "
        "management's ramp conviction sits."
    ),
    "hc.hc.col.company": "Company",
    "hc.hc.col.ticker": "Ticker",
    "hc.hc.col.fy24": "FY2024",
    "hc.hc.col.fy25": "FY2025",
    "hc.hc.col.delta": "Change",
    "hc.hc.col.pct": "Change %",
    "hc.hc.source": (
        "Source: HKEX annual results announcements / annual-report 'Employees & Remuneration', "
        "company ESG reports, iFind; basis = group total employees (FY year-end)."
    ),
    "hc.hc.empty": "No headcount data — run jobs/cn_pharma_headcount_2025.py to backfill.",
    "hc.dl.xlsx": "⬇ Download this section (Excel)",
    "hc.stale.warn": "⚠ This section's data is {days} days old (as of {asof}). Re-bake per docs/healthcare-data-pipeline.md.",
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
    # Legacy Styler-table keys — still consumed by a3_ai_heatmap (AI heatmap not migrated)
    "heat.filter.sort_by": "Sort by",
    "heat.filter.sort_help": "Defaults to market cap descending.",
    "heat.agg.expander": "{sector} aggregates (mean / median / weighted)",
    "heat.agg.metric": "Metric",
    "heat.caption.legend": "**Color legend**: returns green-up / red-down; multiples (P/E, EV/EBITDA) green-cheap / red-rich; FCF yield green-high / red-low. Ticker in **Bloomberg style** (2269 HK / 4587 JP / 300760 CH). Latest data: **{date}**",
    "heat.empty": "No cross-section data — run jobs/fetch_eod to backfill.",
    "heat.tbl.cover": "COVERAGE",
    "heat.tbl.mcap_total": "TOTAL MCAP",
    "heat.tbl.ytd_med": "YTD MEDIAN",
    "heat.tbl.breadth": "YTD BREADTH",
    "heat.tbl.up": "up",
    "heat.tbl.dn": "down",
    "heat.tbl.unit_names": "names",
    "heat.tbl.median": "Sector median",
    "heat.tbl.grp_ret": "RETURNS %",
    "heat.tbl.grp_val": "VALUATION ×",
    "heat.tbl.grp_cf": "CASH FLOW",
    "heat.tbl.col.t": "Ticker",
    "heat.tbl.col.n": "Name",
    "heat.tbl.col.mcap": "Mcap $B",
    "heat.tbl.col.ytd": "YTD",
    "heat.tbl.col.m1": "1M",
    "heat.tbl.col.d5": "5D",
    "heat.tbl.col.d1": "1D",
    "heat.tbl.col.peS": "Trail P/E",
    "heat.tbl.col.peF": "Fwd P/E",
    "heat.tbl.col.fcf": "FCF Yld",
    # Region filter chips (in-table client-side multi-select; all off = full set)
    "heat.tbl.region.US": "US",
    "heat.tbl.region.HK": "HK",
    "heat.tbl.region.CN": "A-share",
    "heat.tbl.region.JP": "Japan",
    "heat.tbl.region.KR": "Korea",
    "heat.tbl.sum.title": "Sector Summary",
    "heat.tbl.sum.sub": "Equal-weight avg returns · {n} names · click a row to switch the sector below",
    "heat.tbl.heat.title": "Sector Heatmap",
    "heat.tbl.heat.sub": "Single-name cross-section · multiples from yfinance (trailing + 12M fwd) · click headers to sort",
    "heat.tbl.sum.col.sector": "Sector",
    "heat.tbl.sum.col.n": "Names",
    "heat.tbl.sum.col.dist": "YTD dist",
    "heat.tbl.sum.col.bench": "BM",
    "heat.tbl.footnote_dyn": "Sector summary is equal-weighted; the YTD bar is scaled to the column's max magnitude (±{max}%).",
    "heat.tbl.footnote": (
        'Color legend: return cells deepen with within-column magnitude '
        '(<span style="color:#0d7680;font-weight:600;">teal up</span> / '
        '<span style="color:#c8102e;font-weight:600;">red down</span>); valuation multiples '
        'tinted by within-column percentile (teal = cheap / red = rich, NM excluded); FCF yield '
        'teal-high / red-low. Mcap bar is √-scaled. Click a column header to sort; the '
        '"Sector median" row is the current sector\'s column median. Latest snapshot: {date}.'
    ),
    "heat.onboarding.title": "How to read this page",
    # heat.tbl.* forked keys (new iframe card only); heat.onboarding.body /
    # heat.caption.filter_note keep the LEGACY text — a3_ai_heatmap still consumes them.
    "heat.tbl.onboarding.body": (
        "**Multiples & returns**\n"
        "- **Color legend**: return cells teal-up / red-down (deepen with within-column "
        "magnitude); multiples tinted by within-column percentile (teal = cheap / red = rich, "
        "NM excluded); FCF yield teal-high / red-low.\n"
        "- **Tabs**: switch across the 7 sub-sectors inside the table (instant, no rerun).\n"
        "- **Sorting**: click a column header; click again to reverse. NM always sinks.\n\n"
        "**Filters** — **Min market cap** (sidebar): drop tiny names whose extreme multiples "
        "skew the sector median."
    ),
    "heat.tbl.filter_note": "Set a min market cap in the sidebar — useful when small caps distort the sector median (e.g. 4587 JP $904M vs GILD $166B).",
    "heat.onboarding.body": (
        "**Multiples & returns**\n"
        "- **Color legend**: returns green-up / red-down; multiples (P/E, EV/EBITDA) "
        "green-cheap / red-rich; FCF yield green-high / red-low.\n"
        "- **Tabs**: piano-key through the sub-sectors.\n\n"
        "**Filters** — **Min market cap**: drop tiny names whose extreme multiples skew the "
        "sector mean.\n\n"
        "**Aggregates**: expand 'Sector aggregates' for the sector's mean and median."
    ),
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
    "drill.term.meta_line": "Daily K · MA5 / MA10 / MA20 · Volume · {hours}",
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
    "market.filters.sector_help": "Show only tickers in these industries/sub-sectors (default: all).",
    "market.empty": "No tickers match the current filters.",
    "market.click_hint": "👆 Click \"Open ↗\" in a row → stock detail in a new tab; or use the picker above → same-tab detail.",
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
    "capital.tab.ipo": "IPO · Tracker",
    "capital.def": "M&A = change of control (acquisition/merger); BD = license / option / collaboration (no change of control).",
    "capital.ipo.empty": "No IPO tracker data yet — run jobs/build_hk_ipo_tracker.py locally (needs the Wind terminal + Futu OpenD).",
    "capital.ipo.asof": "HK healthcare IPOs since 2025-04 (恒瑞 window) · as of {asof} · source Wind+Futu, daily-refreshed via cloud yfinance",
    "capital.ipo.methodology": "Definitions: return = offer → latest close; break-issue = current < offer. Aggregates exclude no-offer (introduction listings), suspended (frozen price), and names with <20 trading sessions.",
    "capital.ipo.kpi.total": "IPOs",
    "capital.ipo.kpi.total_foot": "{w} with offer · {s} suspended",
    "capital.ipo.kpi.broke": "Break-issue (clean)",
    "capital.ipo.kpi.broke_foot": "{n}/{d} below offer · full sample {fn}",
    "capital.ipo.kpi.big": "≥HK$10bn count",
    "capital.ipo.kpi.big_foot": "Large+mid cap (institutional zone)",
    "capital.ipo.kpi.top": "Top gainer",
    "capital.ipo.kpi.top_foot": "{name}",
    "capital.ipo.kpi.median": "Median return",
    "capital.ipo.kpi.median_foot": "clean n={n}",
    "capital.ipo.section.bymkt": "Break-issue × market-cap tier",
    "capital.ipo.section.bymkt_meta": "The conclusion · larger cap = less break (monotonic)",
    "capital.ipo.chart.bymkt": "Break-issue rate (by market-cap tier)",
    "capital.ipo.note.bymkt": "Large ≥HK$30bn (恒瑞 only) / Mid HK$10-30bn / Small <HK$10bn. Break rate rises monotonically small→large = larger caps win institutional endorsement and resist breaking issue.",
    "capital.ipo.section.scatter": "Return × market cap",
    "capital.ipo.section.scatter_meta": "One dot per IPO · y=0 = break line · log market-cap axis",
    "capital.ipo.chart.scatter": "Return since offer vs current market cap",
    "capital.ipo.section.byliq": "Break-issue × liquidity",
    "capital.ipo.section.byliq_meta": "Secondary · liquidity tier = Wind 20-session avg turnover",
    "capital.ipo.chart.byliq": "Break-issue rate (by liquidity tier)",
    "capital.ipo.note.byliq": "Caveat: liquidity→break is non-monotonic, small-n (some buckets n<5), and Wind/Futu source choice flips it → descriptive only; market-cap tier is the clean signal.",
    "capital.ipo.unit.break": "Break rate %",
    "capital.ipo.section.table": "Full roster (filterable)",
    "capital.ipo.filter.mkt": "Cap tier",
    "capital.ipo.filter.water": "Water",
    "capital.ipo.filter.tag": "Type",
    "capital.ipo.filter.all": "All",
    "capital.ipo.filter.above": "Above water",
    "capital.ipo.filter.below": "Broke issue",
    "capital.ipo.filter.ai": "AI pharma",
    "capital.ipo.sort.label": "Sort",
    "capital.ipo.sort.ret_desc": "Return high→low",
    "capital.ipo.sort.ret_asc": "Return low→high",
    "capital.ipo.sort.mktcap_desc": "Mkt cap large→small",
    "capital.ipo.sort.date_desc": "Listed newest→oldest",
    "capital.ipo.sort.pipeline_desc": "Pipeline most→least",
    "capital.ipo.sort.bd_desc": "Disclosed BD high→low",
    "capital.ipo.col.name": "Name",
    "capital.ipo.col.date": "Listed",
    "capital.ipo.col.offer": "Offer",
    "capital.ipo.col.close": "Last",
    "capital.ipo.col.ret": "Return%",
    "capital.ipo.col.mktcap": "Mkt cap (亿)",
    "capital.ipo.col.mkttier": "Cap tier",
    "capital.ipo.col.turnover": "Avg turnover (M$)",
    "capital.ipo.col.liqtier": "Liquidity",
    "capital.ipo.col.broke": "Broke",
    "capital.ipo.col.flag": "Flag",
    "capital.ipo.col.founded": "Founded",

    # ── IPO detail expander ──
    "capital.ipo.detail.title": "Company Details",
    "capital.ipo.detail.basic": "Basic Info",
    "capital.ipo.detail.founded": "Founded",
    "capital.ipo.detail.sector": "Sector",
    "capital.ipo.detail.listing_mc": "Listing valuation",
    "capital.ipo.detail.pipeline": "Pipeline",
    "capital.ipo.detail.pipeline_loading": "Loading pipeline data...",
    "capital.ipo.detail.pipeline_empty": "No pipeline data available",
    "capital.ipo.detail.pipeline_error": "Pipeline query failed",
    "capital.ipo.detail.bd": "BD Deals",
    "capital.ipo.detail.bd_loading": "Loading BD deals...",
    "capital.ipo.detail.bd_empty": "No BD deals on record",
    "capital.ipo.detail.bd_error": "BD query failed",
    "capital.ipo.detail.product": "Product",
    "capital.ipo.detail.indication": "Indication",
    "capital.ipo.detail.phase": "Phase",
    "capital.ipo.detail.partner": "Partner",
    "capital.ipo.detail.deal_value": "Deal value",
    "capital.ipo.detail.deal_date": "Date",
    # ── Ledger × ladder redesign (scheme 2a) ──
    "capital.ipo.detail.section_title": "Company Details · Full Roster",
    "capital.ipo.detail.section_meta": "PharmCube prebuilt · Pipeline + BD · click a row to expand",
    "capital.ipo.detail.disclosed": "Disclosed",
    "capital.ipo.detail.no_archive": "No pipeline / BD archive · basic info only",
    "capital.ipo.detail.up_chip": "Above",
    "capital.ipo.detail.broke_chip": "Broke",
    "capital.ipo.detail.suspended_chip": "Halted",
    "capital.ipo.detail.first_day": "1st day",
    "capital.ipo.detail.listing_date": "Listing date",
    "capital.ipo.detail.ret_since": "Since IPO",
    "capital.ipo.detail.offer_to_cur": "Offer → Current",
    "capital.ipo.detail.val_to_mc": "Valuation → Mkt cap",
    "capital.ipo.detail.avg_turnover": "Avg turnover",
    "capital.ipo.detail.disclosed_total": "Out-licensing · Disclosed total",
    "capital.ipo.detail.ge_1b": "{n} deals · {m} ≥ $1B · upfront+milestones",
    "capital.ipo.detail.undisclosed_n": "{n} deals · value undisclosed",
    "capital.ipo.detail.partners": "Partner map",
    "capital.ipo.detail.footer": "Source PharmCube · prebuilt · zero runtime query · missing fields auto-hidden",
    "capital.ipo.detail.ladder": "Core pipeline · Phase ladder",
    "capital.ipo.detail.pipeline_meta": "{n} total · top {k} on ladder",
    "capital.ipo.detail.rest_pipeline": "{n} more, mostly preclinical / Phase I",
    "capital.ipo.detail.bd_by_year": "Out-licensing · By year",
    "capital.ipo.detail.bd_meta": "showing {k} / {n}",
    "capital.ipo.detail.undisclosed": "Undisclosed",

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
    # Out-licensing structure: License-out / Co-Co / NewCo
    "capital.bd.col.structure": "Structure",
    "capital.bd.struct.licenseout": "License-out",
    "capital.bd.struct.coco": "Co-Co",
    "capital.bd.struct.newco": "NewCo",
    "capital.bd.section.bystructure": "By Out-licensing Structure (License-out / Co-Co / NewCo)",
    "capital.bd.section.bystructure_meta": "by deal count · License-out vs Co-Co (co-develop + co-commercialize) vs NewCo (assets into a new co + equity)",
    "capital.bd.chart.structure": "Out-licensing Structure (deal count)",
    "capital.bd.note.structure": (
        "License-out {lo} · Co-Co {coco} · NewCo {newco}. "
        "Co-Co = co-development + co-commercialization with cost/profit split (e.g. Innovent × Takeda, IBI363); "
        "NewCo = assets dropped into a newly-formed company, licensor takes equity for upside (e.g. Harbour × Solstice, Keymed × Ouro)."
    ),
    "capital.bd.filter.structure": "Filter by Structure",
    # ── HC ETF 专栏 (hc_etf.*) ──
    "hc_etf.title": "Healthcare ETFs",
    "hc_etf.caption": "{n} US-listed healthcare ETFs · profile + total-return windows · holdings expand inline · data as of {date}",
    "hc_etf.empty": "ETF data not built yet — run jobs/build_etf_panel.py.",
    "hc_etf.filter.subsector": "Sub-sector",
    "hc_etf.filter.all": "All",
    "hc_etf.subsector.Broad": "Broad healthcare",
    "hc_etf.subsector.Biotech": "Biotech",
    "hc_etf.subsector.Pharma": "Pharma",
    "hc_etf.subsector.Devices": "Medical devices",
    "hc_etf.subsector.Providers": "Providers / payers",
    "hc_etf.subsector.Genomics": "Genomics / thematic",
    "hc_etf.subsector.Other": "Other",
    "hc_etf.col.rank": "#",
    "hc_etf.col.symbol": "Ticker",
    "hc_etf.col.name": "Holding",
    "hc_etf.col.weight": "Weight",
    "hc_etf.holdings_title": "Top holdings",
    "hc_etf.coverage": "Top {n} weighted = {cov}% of fund",
    "hc_etf.tail_more": "+{n} more constituents (symbol-only): {syms}",
    "hc_etf.tail_more_trunc": "+{n} more constituents (symbol-only) — first {shown}: {syms} …",
    "hc_etf.kpi.price": "Price",
    "hc_etf.kpi.ytd": "YTD",
    "hc_etf.kpi.y1": "1Y",
    "hc_etf.kpi.y3": "3Y",
    "hc_etf.kpi.vol": "Vol",
    "hc_etf.kpi.maxdd": "Max DD",
    "hc_etf.kpi.expense": "Expense",
    "hc_etf.kpi.aum": "AUM",
    "hc_etf.provenance": "Source: {src} · as of {date}",
    # ── ETF 专栏 v2 (etf.*) — ETFs as first-class instruments ──
    "etf.title": "Healthcare ETFs",
    "etf.caption": "US healthcare ETFs as first-class instruments — performance · heatmap · momentum, just like stocks · data as of {date}",
    "etf.empty": "ETF data not loaded — run jobs/load_universe.py + fetch_eod.py.",
    "etf.tab.perf": "Performance 表现",
    "etf.tab.holdings": "Holdings 成分股",
    "etf.col.name": "Name",
    "etf.col.sub": "Sub-sector",
    "etf.col.last": "Last",
    "etf.col.aum": "AUM",
    "etf.col.detail": "Detail",
    "etf.col.m1": "1M",
    "etf.col.ytd": "YTD",
    "etf.col.d5": "5D",
    "etf.card.holdings": "Top 5 holdings",
    "etf.card.expand": "All {n} holdings",
    "etf.click_hint": "Click a row's ↗ to open the ETF in Ticker Drill (new tab).",
    "etf.provenance": "Source: {src} · as of {date}",
    "etf.holdings.pick": "ETF",
    "etf.heat.title": "ETF Heatmap",
    "etf.heat.caption": "ETFs grouped by sub-sector, colored by return (teal up / red down) · as of {date}",
    "etf.heat.window": "Window",
    "etf.rot.title": "ETF Momentum Rotation (RRG)",
    "etf.rot.caption": "Each ETF rotates against the broad-HC benchmark (XLV) — Leading / Weakening / Lagging / Improving.",
    "etf.rot.thin": "Too few ETFs with enough history for a rotation graph.",
    "etf.rot.note": "Benchmark = {bench} (broad healthcare). Weekly RS-Ratio / RS-Momentum.",
}
