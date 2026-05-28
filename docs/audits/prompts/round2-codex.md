Second-round audit of invest-dashboard D4 + D5 work. Previous audit (commit `251c6de`) addressed Codex/Gemini/GLM round-1 findings. This is post-D4+D5 follow-up.

**Repo (public)**: https://github.com/chenhongdao2-blip/invest-dashboard

**Recent commits**:
- `251c6de` (round-1 audit fixes — pre-format strings, USD prices, exp backoff, etc)
- `2863c72` (**D4 Strategy Picks page** — v4/v5 biotech + HK 高股息)
- `9e1179e` (**D5 CMSI Coverage + Valuation Scanner**)

**D4 architecture** (new files):
- `app/lib/strategy.py`: loads picks from `data/external/picks.db` (ic-foundry copy, `catalyst-monitor` source), `data/external/v4_picks.csv` (27 picks 2026-04-22), `data/external/hd_picks.csv` (34 picks 2026-03-20). Live yfinance fetch via `fetch_picks_closes` with `@st.cache_data(ttl=3600)`. `compute_strategy_returns` builds since-inception cumulative + per-window perf.
- `app/pages/4_🧬_Strategy_Picks.py`: 3 tabs (v4/v5/HD). Header metrics (Portfolio / Bench / Alpha pp). Plotly chart with individual + portfolio + benchmark overlay. Top/Bottom 5 ranking + expandable full table.

**D5 architecture** (new files):
- `app/pages/3_💎_CMSI_Coverage.py`: 4 region tabs (HK 15 / US 10 / CN 3 / All 28). Per ticker shows: BBG, name_cn, name_en, region, mcap_tier, cross-sector emoji tags (🧬💊🤖⚕️🏥🩺🧪), mcap, multi-window returns, multiples.
- `app/pages/5_💰_Valuation_Scanner.py`: Sidebar filters (sectors multi / min mcap / sector P/E percentile threshold / fwd vs trailing / YTD range / 5D min). Computes `sector_pe_percentile()` (multi-sector ticker uses cheapest sector ranking; negative P/E excluded).

**Audit angle (architecture / correctness / risk)**:

1. **D4 Strategy returns calculation correctness** — `app/lib/strategy.py:compute_strategy_returns()`:
   - Equal-weight portfolio = `normed.mean(axis=1, skipna=True)`. Is this correct semantics for "equal-weight equity-curve"? Specifically: when a single ticker has NaN on day X (e.g., trading halt), should the portfolio that day be: (a) mean of available, (b) NaN, (c) carry-forward previous value?
   - Current behavior: (a) mean of available — biased upward when missing-data tickers tend to be losers
   - Compare to weekly_perf.py's approach. Aligned?

2. **D4 picks.db on Streamlit Cloud (B1 follow-through)** — picks.db is now in repo `data/external/`. But:
   - `.db-shm` and `.db-wal` files also got committed (WAL/SHM SQLite journals)
   - These are session-specific and shouldn't be in repo. Issue?

3. **D5 Scanner percentile logic** — `sector_pe_percentile()`:
   - "Multi-sector ticker uses cheapest sector ranking" — does this bias toward stocks in cheap-but-large sectors?
   - Negative P/E exclusion: correct for biotech, but a stock with -5x P/E (i.e., barely positive earnings yet) gets dropped while same stock at +500x P/E gets ranked. Is this binary cliff a problem?
   - `pct_threshold ≤ 25` with positive-P/E only: how many actually positive P/E stocks in biotech sector (16)? If only ~8, then 25% = 2 stocks max from biotech. Is the percentile math meaningful with such small N?

4. **D4 live yfinance fetch performance** — `fetch_picks_closes()` fetches v4 + v5 + HD picks live (27+40+34 = ~100 tickers + benchmarks). With 1h cache:
   - First page load: ~15-30s cold
   - Streamlit Cloud free tier has 1GB memory limit — does caching 100-ticker 200-day daily closes (~3000 KB) fit in cache?
   - What happens on Streamlit Cloud sleep/wake? Cache invalidated each wake.

5. **Regression check** — verify these fixes from round-1 audit still hold in D4/D5 pages:
   - M7 NaN render → "—" not "None"
   - M10 name_cn priority + mcap desc default sort
   - n2 Bloomberg ticker style ("2269 HK" not "2269.HK")
   - m4 dark theme
   - B4 global search sidebar reused on every page

6. **GitHub Actions cron** — does it still pass with the new schema and new data/external/ committed files? `.github/workflows/fetch_eod.yml` references `data/snapshots.db` only — does `data/external/picks.db` need separate sync?

7. **Picks.db sync workflow** — README says `cp ~/ic-foundry/ledger.db data/external/picks.db && git add && git commit` weekly. But user hasn't set up automation. Is this fragile?

8. **Data quality** — Strategy Picks page showed:
   - v4 portfolio +1.04%, XBI -2.08%, Alpha +3.12pp (user email screenshot showed +4.61pp on 2026-05-26)
   - Discrepancy: 2-day gap (5/26 → 5/28) + possibly different ticker count handling. Is this acceptable?

9. **What's the biggest BLOCKER/MAJOR risk for D7 deploy with current state?**

Output: severity-tagged [BLOCKER] / [MAJOR] / [MINOR] / [NIT] action items with file:line refs.
