# codex advisor artifact

- Provider: codex
- Exit code: 0
- Created at: 2026-05-28T06:53:31.000Z

## Original task

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

## Final prompt

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

## Raw output

```text
Second-round audit result: no code changes made. I found one deploy-level blocker and several major correctness/operational risks.

**Findings**

[BLOCKER] Raw `picks.db` is committed to a public repo, but D4 only needs a small derived extract.
[file](/Users/gcc/invest-dashboard/app/lib/strategy.py:43) reads only `ticker`, `price_at_decision`, and `date_added` from `picks_v2`, but the committed SQLite file also contains extra tables (`calibration_alerts`, `schema_meta`, `universe_snapshots_index`). For a public repo, replace [picks.db](/Users/gcc/invest-dashboard/data/external/picks.db) with a derived CSV/JSON/minimal SQLite export. If any data is sensitive, removing the file in a future commit is not enough; purge repo history.

[MAJOR] D4 portfolio return math is not aligned with `weekly_perf.py`.
[file](/Users/gcc/invest-dashboard/app/lib/strategy.py:147) anchors every ticker to the first global row after pick date, then [line 150](/Users/gcc/invest-dashboard/app/lib/strategy.py:150) averages available normalized series with `skipna=True`. `weekly_perf.py` computes per-ticker since returns and then averages those returns. These match only if every ticker has the same first and latest valid date. Action: either report `perf["Since %"].mean()` for email parity, or explicitly document the page as a daily equal-weight equity curve with different semantics.

[MAJOR] Missing prices are currently dropped from portfolio weight.
[file](/Users/gcc/invest-dashboard/app/lib/strategy.py:150) means a halted/missing ticker is removed from that day’s average. That can overstate returns if missing names are weak. For an equal-weight equity curve, carry forward each constituent after its first valid price (`ffill`) and show constituent coverage by date; for strict data quality, mark the portfolio NaN when coverage is incomplete.

[MAJOR] Chart and metric can diverge after future fixes.
[file](/Users/gcc/invest-dashboard/app/pages/4_🧬_Strategy_Picks.py:76) computes `portfolio`, but [charts.py](/Users/gcc/invest-dashboard/app/lib/charts.py:69) recomputes `base`, `norm`, and [portfolio](/Users/gcc/invest-dashboard/app/lib/charts.py:71). Once return logic is fixed in one place, the other can silently disagree. Action: pass `normed`/`portfolio` into the chart instead of recomputing.

[MAJOR] D4 cold load fetches all strategy tabs, not only the visible tab.
[file](/Users/gcc/invest-dashboard/app/pages/4_🧬_Strategy_Picks.py:219) creates tabs, then [line 222](/Users/gcc/invest-dashboard/app/pages/4_🧬_Strategy_Picks.py:222) renders every strategy, each calling [live yfinance](/Users/gcc/invest-dashboard/app/pages/4_🧬_Strategy_Picks.py:65). Memory is fine for ~100 tickers x ~200 daily closes, but Streamlit Cloud sleep/wake will invalidate cache and make the first page load slow/unreliable. Action: precompute closes into `snapshots.db` or lazy-select one strategy.

[MAJOR] `picks.db` sync is documented but not implemented.
[README](/Users/gcc/invest-dashboard/README.md:95) says copy and commit periodically, and [line 99](/Users/gcc/invest-dashboard/README.md:99) references `make sync-ledger`, but there is no `Makefile`. The GitHub cron only commits [snapshots.db](/Users/gcc/invest-dashboard/.github/workflows/fetch_eod.yml:50). Action: add a real sync script/Make target and preferably export a minimal derived artifact.

[MAJOR] B4 “global search on every page” is still incomplete in committed pages.
D4/D5/CMSI/Home have search, but Healthcare has no sidebar search near [page setup](/Users/gcc/invest-dashboard/app/pages/2_🏥_Healthcare.py:33), and Sector Heatmap’s sidebar starts with filters only at [line 39](/Users/gcc/invest-dashboard/app/pages/3_🔥_Sector_Heatmap.py:39). Action: use shared `ui.sidebar_search()` on every page.

[MINOR] SQLite WAL/SHM files should not be tracked.
`data/external/picks.db-wal` and `data/external/picks.db-shm` are tracked. Add `*.db-wal` / `*.db-shm` to [.gitignore](/Users/gcc/invest-dashboard/.gitignore:1) and remove them from git.

[MINOR] Scanner percentile is useful directionally, but small-N ranks are coarse and mislabeled.
[file](/Users/gcc/invest-dashboard/app/pages/5_💰_Valuation_Scanner.py:142) uses `rank(pct=True) * 100`, so the cheapest stock is `100/N`, not `0`, despite the docstring at [line 128](/Users/gcc/invest-dashboard/app/pages/5_💰_Valuation_Scanner.py:128). Current positive forward P/E counts are biotech 13, hc_ai 11, hospital/managed care 10, etc.; a 25% threshold means only 2-4 names per sector. Action: show `rank/N`, `N positive`, and/or use `(rank - 1) / (N - 1) * 100`.

[MINOR] Negative P/E exclusion is defensible, but should be surfaced.
[file](/Users/gcc/invest-dashboard/app/pages/5_💰_Valuation_Scanner.py:139) drops non-positive P/E. That is correct for P/E ranking, especially biotech, but loss-making names become invisible while high positive P/E names remain rankable. Action: show an “excluded: negative/NA P/E” count and add EV/Sales or cash/runway mode for biotech.

**Regression Check**

M7, M10, n2, and dark theme look preserved: formatting helpers return `"—"` for NaN, CMSI sorts by market cap desc and prefers Chinese names, Bloomberg ticker formatting is used, and dark theme is configured. B4 is the only regression still incomplete.

Verification run: `python3 -m compileall app jobs` passed; `jobs/init_db.py` and `jobs/load_universe.py` ran successfully. I did not run live `fetch_eod.py` or live D4 yfinance fetch.


OpenAI Codex v0.130.0
--------
workdir: /Users/gcc/invest-dashboard
model: gpt-5.5
provider: openai
approval: never
sandbox: danger-full-access
reasoning effort: medium
reasoning summaries: none
session id: 019e6d59-0c30-7e50-8483-830442c039e6
--------
user
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
codex
I’ll audit from the local repo state and compare the D4/D5 code against the specific risk list. I’ll start by reading the relevant files, workflow, and recent diffs, then I’ll run lightweight checks where possible.
exec
/bin/zsh -lc 'rg -n "def compute_strategy_returns|def fetch_picks_closes|sector_pe_percentile|global search|search|None|name_cn|Bloomberg|BBG|sort|dark|theme|snapshots.db|picks.db" app .github README* data -S' in /Users/gcc/invest-dashboard
exec
/bin/zsh -lc 'rg --files' in /Users/gcc/invest-dashboard
 succeeded in 0ms:
data/external/v4_picks.csv
data/external/hd_picks.csv
data/external/picks.db
data/external/picks.db-wal
data/external/picks.db-shm
data/snapshots.db
jobs/init_db.py
jobs/fetch_eod.py
jobs/load_universe.py
README.md
config/universes/cmsi_coverage_hc.yml
config/universes/hc_cxo.yml
config/universes/hc_ai.yml
config/universes/hc_biotech.yml
config/universes/hc_hospital_care.yml
config/universes/hc_pharma.yml
config/universes/hc_managed_care.yml
config/universes/hc_medtech.yml
config/domains/healthcare.yml
requirements.txt
app/pages/1_🏥_Healthcare.py
app/pages/5_💰_Valuation_Scanner.py
app/pages/3_💎_CMSI_Coverage.py
app/pages/2_🔥_Sector_Heatmap.py
app/pages/4_🧬_Strategy_Picks.py
app/lib/benchmarks.py
app/lib/format.py
app/lib/strategy.py
app/lib/__init__.py
app/lib/charts.py
app/lib/db.py
app/streamlit_app.py

 succeeded in 0ms:
.github/workflows/fetch_eod.yml:50:          git add data/snapshots.db
README.md:23:**与 Bloomberg / FactSet 的 consensus multi-year forward (25E/26E/27E) 有出入**。如需精确分年度 forward，请参考 George 手工维护的 Excel sector comp table。
README.md:34:│   ├── snapshots.db       # 价格 + multiple 时序 (auto-grown)
README.md:81:`data/snapshots.db` is committed daily. With binary churn in git pack, growth is faster
README.md:95:- **Scheme A** (recommended): `cp ~/ic-foundry/ledger.db data/external/picks.db` and commit periodically
app/pages/1_🏥_Healthcare.py:15:def _render_pct_table(df: pd.DataFrame, pct_cols: list[str], num_cols: list[str] | None = None) -> None:
app/pages/1_🏥_Healthcare.py:103:    if rets is None or rets.empty:
app/pages/1_🏥_Healthcare.py:115:        gainers = rets.sort_values("1d_%", ascending=False).head(3).rename(columns=rename_map)
app/pages/1_🏥_Healthcare.py:116:        drags = rets.sort_values("1d_%", ascending=True).head(3).rename(columns=rename_map)
app/pages/1_🏥_Healthcare.py:117:        # n2: Bloomberg ticker style
app/pages/4_🧬_Strategy_Picks.py:6:- Data: data/external/picks.db (v5) + data/external/v4_picks.csv + data/external/hd_picks.csv
app/pages/4_🧬_Strategy_Picks.py:26:# Sidebar global search (B4 audit, on every page)
app/pages/4_🧬_Strategy_Picks.py:31:        options=[""] + sorted(db.all_tickers()),
app/pages/4_🧬_Strategy_Picks.py:33:        key="strategy_search",
app/pages/4_🧬_Strategy_Picks.py:45:def render_strategy(strat_id: str) -> None:
app/pages/4_🧬_Strategy_Picks.py:93:        bench_last = (bench_norm.iloc[-1] - 100) if not bench_norm.empty else None
app/pages/4_🧬_Strategy_Picks.py:94:        alpha = (port_last - bench_last) if bench_last is not None else None
app/pages/4_🧬_Strategy_Picks.py:99:            delta=None,
app/pages/4_🧬_Strategy_Picks.py:103:            f"{bench_last:+.2f}%" if bench_last is not None else "—",
app/pages/4_🧬_Strategy_Picks.py:104:            delta=None,
app/pages/4_🧬_Strategy_Picks.py:108:            f"{alpha:+.2f}pp" if alpha is not None else "—",
app/pages/4_🧬_Strategy_Picks.py:147:    perf_sorted = perf.sort_values("Since %", ascending=False, na_position="last")
app/pages/4_🧬_Strategy_Picks.py:148:    perf_sorted.index = [fmt.fmt_ticker_bbg(t) for t in perf_sorted.index]
app/pages/4_🧬_Strategy_Picks.py:152:    cols_to_show = [c for c in front_cols if c in perf_sorted.columns]
app/pages/4_🧬_Strategy_Picks.py:153:    perf_display = perf_sorted[cols_to_show].rename(columns={"name": "Name"})
app/pages/4_🧬_Strategy_Picks.py:188:    with st.expander(f"📋 All {len(perf_display)} picks (sorted by since-inception)"):
app/pages/4_🧬_Strategy_Picks.py:216:    "Picks source: v4/v5 from `data/external/picks.db` + `v4_picks.csv` · HK 高股息 from `hd_picks.csv` · "
app/pages/4_🧬_Strategy_Picks.py:217:    "Sync via `cp ~/ic-foundry/ledger.db data/external/picks.db && git add && git commit` weekly."
app/pages/5_💰_Valuation_Scanner.py:39:# --- Sidebar global search ---
app/pages/5_💰_Valuation_Scanner.py:44:        options=[""] + sorted(db.all_tickers()),
app/pages/5_💰_Valuation_Scanner.py:46:        key="scanner_search",
app/pages/5_💰_Valuation_Scanner.py:114:def sector_pe_percentile(_mults_df: pd.DataFrame, _sector_map: dict[str, list[str]], pe_col: str) -> pd.Series:
app/pages/5_💰_Valuation_Scanner.py:139:pe_pct = sector_pe_percentile(mults, all_tickers_by_sec, pe_metric)
app/pages/5_💰_Valuation_Scanner.py:151:candidates = candidates.sort_values("pe_percentile", ascending=True)
app/pages/5_💰_Valuation_Scanner.py:169:disp["BBG"] = [fmt.fmt_ticker_bbg(t) for t in disp.index]
app/pages/3_💎_CMSI_Coverage.py:6:- Defaults: name_cn first, mcap desc (M10 audit)
app/pages/3_💎_CMSI_Coverage.py:26:# --- Sidebar global search ---
app/pages/3_💎_CMSI_Coverage.py:31:        options=[""] + sorted(db.all_tickers()),
app/pages/3_💎_CMSI_Coverage.py:33:        key="cmsi_search",
app/pages/3_💎_CMSI_Coverage.py:76:merged["name_cn"] = cmsi.set_index("ticker")["name_cn"]
app/pages/3_💎_CMSI_Coverage.py:79:merged["BBG"] = [fmt.fmt_ticker_bbg(t) for t in merged.index]
app/pages/3_💎_CMSI_Coverage.py:102:# --- Default sort: mcap desc (M10 audit) ---
app/pages/3_💎_CMSI_Coverage.py:103:merged = merged.sort_values("market_cap_usd", ascending=False, na_position="last")
app/pages/3_💎_CMSI_Coverage.py:110:def render_region(df: pd.DataFrame) -> None:
app/pages/3_💎_CMSI_Coverage.py:117:    disp["BBG"] = df["BBG"]
app/pages/3_💎_CMSI_Coverage.py:118:    disp["Name (CN)"] = df["name_cn"].fillna("—")
app/streamlit_app.py:5:- M10: name_cn priority
app/streamlit_app.py:6:- B4: global ticker search in sidebar (stub for D6 Ticker Drill)
app/streamlit_app.py:7:- n2: Bloomberg ticker style display
app/streamlit_app.py:26:# --- B4 audit: global ticker search ---
app/streamlit_app.py:32:        options=[""] + sorted(all_t),
app/streamlit_app.py:57:def _render_pct_table(df: pd.DataFrame, pct_cols: list[str], num_cols: list[str] | None = None) -> None:
app/streamlit_app.py:103:        # n2: rewrite index to Bloomberg style
app/streamlit_app.py:129:    "requires Bloomberg / FactSet and is **not in scope**. "
app/lib/benchmarks.py:45:                ser = d[t]["Close"].dropna().sort_index()
app/lib/benchmarks.py:53:            def ret(n: int) -> float | None:
app/lib/benchmarks.py:55:                    return None
app/lib/benchmarks.py:59:            ytd = None
app/lib/charts.py:9:PLOT_TEMPLATE = "plotly_dark"
app/lib/charts.py:20:    benchmark: pd.Series | None = None,
app/lib/charts.py:33:    if benchmark is not None and not benchmark.empty:
app/lib/charts.py:53:    pick_date: str | None = None,
app/lib/charts.py:60:    closes = closes.sort_index()
app/pages/2_🔥_Sector_Heatmap.py:6:- M10: default sort by market cap desc; name_cn priority (中文卖方习惯).
app/pages/2_🔥_Sector_Heatmap.py:46:    sort_col = st.selectbox(
app/pages/2_🔥_Sector_Heatmap.py:54:def render_sector(sec: dict) -> None:
app/pages/2_🔥_Sector_Heatmap.py:84:    # M10 audit: default sort by market cap desc
app/pages/2_🔥_Sector_Heatmap.py:85:    sort_map = {
app/pages/2_🔥_Sector_Heatmap.py:92:    sort_field = sort_map.get(sort_col, "market_cap_usd")
app/pages/2_🔥_Sector_Heatmap.py:93:    ascending = "P/E" in sort_col   # cheaper first for P/E
app/pages/2_🔥_Sector_Heatmap.py:94:    if sort_field in merged.columns:
app/pages/2_🔥_Sector_Heatmap.py:95:        merged = merged.sort_values(sort_field, ascending=ascending, na_position="last")
app/pages/2_🔥_Sector_Heatmap.py:103:    display_str["BBG"] = merged["Ticker_bbg"]
app/pages/2_🔥_Sector_Heatmap.py:159:                "Mean": fmt.fmt_pct(s.mean() if not s.empty else None),
app/pages/2_🔥_Sector_Heatmap.py:160:                "Median": fmt.fmt_pct(s.median() if not s.empty else None),
app/pages/2_🔥_Sector_Heatmap.py:161:                "Min": fmt.fmt_pct(s.min() if not s.empty else None),
app/pages/2_🔥_Sector_Heatmap.py:162:                "Max": fmt.fmt_pct(s.max() if not s.empty else None),
app/pages/2_🔥_Sector_Heatmap.py:168:                "Mean": fmt_fn(s.mean() if not s.empty else None),
app/pages/2_🔥_Sector_Heatmap.py:169:                "Median": fmt_fn(s.median() if not s.empty else None),
app/pages/2_🔥_Sector_Heatmap.py:170:                "Min": fmt_fn(s.min() if not s.empty else None),
app/pages/2_🔥_Sector_Heatmap.py:171:                "Max": fmt_fn(s.max() if not s.empty else None),
app/pages/2_🔥_Sector_Heatmap.py:189:    "Ticker shown in **Bloomberg style** (2269 HK / 4587 JP / 300760 CH). "
app/lib/format.py:14:    if v is None:
app/lib/format.py:67:    """n2 audit fix: Bloomberg ticker style '2269 HK' instead of '2269.HK'.
app/lib/format.py:71:      .T  → JP (Tokyo, Bloomberg uses JP not T)
app/lib/format.py:72:      .SS → CH (Shanghai, Bloomberg uses CH)
app/lib/format.py:73:      .SZ → CH (Shenzhen, Bloomberg uses CH)
app/lib/format.py:85:    if v is None or (isinstance(v, float) and pd.isna(v)):
app/lib/db.py:12:DB_PATH = REPO_ROOT / "data" / "snapshots.db"
app/lib/db.py:20:def query(sql: str, params: tuple | list | dict | None = None) -> pd.DataFrame:
app/lib/db.py:30:def latest_snapshot_date() -> str | None:
app/lib/db.py:32:    return df["d"].iloc[0] if not df.empty else None
app/lib/db.py:36:def last_fetch_utc() -> str | None:
app/lib/db.py:38:    return df["value"].iloc[0] if not df.empty else None
app/lib/db.py:58:        "SELECT ticker, name_cn, name_en, region "
app/lib/db.py:71:        col_expr = "COALESCE(name_cn, name_en, ticker)"
app/lib/db.py:73:        col_expr = "COALESCE(name_en, name_cn, ticker)"
app/lib/db.py:96:    return df.pivot(index="date", columns="ticker", values="close").sort_index()
app/lib/db.py:106:    closes = closes.sort_index()
app/lib/db.py:107:    out: dict[str, dict[str, float | None]] = {}
app/lib/db.py:188:    return df.pivot(index="date", columns="ticker", values="close_usd").sort_index()
app/lib/db.py:203:    gainers = rets.sort_values("1d_%", ascending=False).head(n)
app/lib/db.py:204:    losers = rets.sort_values("1d_%", ascending=True).head(n)
app/lib/strategy.py:5:- v5 biotech (2026-05-15, 40 picks, XBI benchmark)   — picks.db (catalyst-monitor)
app/lib/strategy.py:24:PICKS_DB = DATA_EXT / "picks.db"
app/lib/strategy.py:38:    """v5 biotech: from picks.db, source_skill='catalyst-monitor'."""
app/lib/strategy.py:52:    df["score"] = None
app/lib/strategy.py:95:def fetch_picks_closes(yf_syms: tuple[str, ...], start: str) -> pd.DataFrame:
app/lib/strategy.py:126:    return pd.DataFrame(out).sort_index()
app/lib/strategy.py:129:def compute_strategy_returns(
app/lib/strategy.py:142:    closes = closes.sort_index()

exec
/bin/zsh -lc 'git status --short && git log --oneline -5' in /Users/gcc/invest-dashboard
 succeeded in 0ms:
9e1179e feat(D5): CMSI Coverage + Valuation Scanner pages
2863c72 feat(D4): Strategy Picks page — v4/v5 biotech + HK 高股息
251c6de feat(audit): apply Codex/Gemini/GLM audit fixes (D1-D3 polish)
17f2f17 feat(D3): Streamlit Home + Healthcare overview + Sector Heatmap
3157451 feat(D2): full yfinance fetcher + cron + CMSI coverage list

codex
The repo is at `9e1179e` and includes the WAL/SHM files under `data/external`, so I’ll treat this as the post-D5 state. I’m drilling into the return math, scanner percentile implementation, and workflow/data sync assumptions now.
exec
/bin/zsh -lc "nl -ba app/lib/strategy.py | sed -n '1,240p'" in /Users/gcc/invest-dashboard
 succeeded in 0ms:
     1	"""Strategy picks data layer — reads from data/external/.
     2	
     3	Strategies tracked:
     4	- v4 biotech (2026-04-22, 27 picks, XBI benchmark) — CSV
     5	- v5 biotech (2026-05-15, 40 picks, XBI benchmark)   — picks.db (catalyst-monitor)
     6	- HK 高股息 (2026-03-20, 34 picks, 3110.HK benchmark) — CSV
     7	
     8	Prices fetched live via yfinance, cached 1 hour.
     9	"""
    10	
    11	from __future__ import annotations
    12	
    13	import sqlite3
    14	from datetime import date, datetime, timedelta
    15	from pathlib import Path
    16	
    17	import pandas as pd
    18	import streamlit as st
    19	import yfinance as yf
    20	
    21	REPO_ROOT = Path(__file__).resolve().parent.parent.parent
    22	DATA_EXT = REPO_ROOT / "data" / "external"
    23	
    24	PICKS_DB = DATA_EXT / "picks.db"
    25	V4_CSV = DATA_EXT / "v4_picks.csv"
    26	HD_CSV = DATA_EXT / "hd_picks.csv"
    27	
    28	
    29	@st.cache_data(ttl=900)
    30	def load_v4() -> pd.DataFrame:
    31	    if not V4_CSV.exists():
    32	        return pd.DataFrame()
    33	    return pd.read_csv(V4_CSV)
    34	
    35	
    36	@st.cache_data(ttl=900)
    37	def load_v5() -> pd.DataFrame:
    38	    """v5 biotech: from picks.db, source_skill='catalyst-monitor'."""
    39	    if not PICKS_DB.exists():
    40	        return pd.DataFrame()
    41	    conn = sqlite3.connect(f"file:{PICKS_DB}?mode=ro", uri=True)
    42	    try:
    43	        df = pd.read_sql(
    44	            "SELECT ticker, MAX(price_at_decision) AS price_at_decision, "
    45	            "MIN(date_added) AS pick_date "
    46	            "FROM picks_v2 WHERE source_skill='catalyst-monitor' GROUP BY ticker",
    47	            conn,
    48	        )
    49	    finally:
    50	        conn.close()
    51	    df["name"] = df["ticker"]
    52	    df["score"] = None
    53	    df["benchmark"] = "XBI"
    54	    df["yf_sym"] = df["ticker"]
    55	    df["pick_date"] = "2026-05-15"
    56	    return df[["ticker", "name", "score", "pick_date", "benchmark", "yf_sym", "price_at_decision"]]
    57	
    58	
    59	@st.cache_data(ttl=900)
    60	def load_hd() -> pd.DataFrame:
    61	    if not HD_CSV.exists():
    62	        return pd.DataFrame()
    63	    return pd.read_csv(HD_CSV)
    64	
    65	
    66	STRATEGIES = {
    67	    "v4_biotech": {
    68	        "name": "🧬 v4 biotech",
    69	        "emoji": "🧬",
    70	        "loader": load_v4,
    71	        "pick_date": "2026-04-22",
    72	        "benchmark": "XBI",
    73	        "benchmark_name": "SPDR S&P Biotech",
    74	    },
    75	    "v5_biotech": {
    76	        "name": "🧬 v5 biotech",
    77	        "emoji": "🧬",
    78	        "loader": load_v5,
    79	        "pick_date": "2026-05-15",
    80	        "benchmark": "XBI",
    81	        "benchmark_name": "SPDR S&P Biotech",
    82	    },
    83	    "hk_hd": {
    84	        "name": "💰 HK 高股息",
    85	        "emoji": "💰",
    86	        "loader": load_hd,
    87	        "pick_date": "2026-03-20",
    88	        "benchmark": "3110.HK",
    89	        "benchmark_name": "Premia 沪深港高股息低波动",
    90	    },
    91	}
    92	
    93	
    94	@st.cache_data(ttl=3600, show_spinner="Fetching picks prices…")
    95	def fetch_picks_closes(yf_syms: tuple[str, ...], start: str) -> pd.DataFrame:
    96	    """Wide-format close DataFrame for picks. Live yfinance, cached 1h."""
    97	    if not yf_syms:
    98	        return pd.DataFrame()
    99	    end = (date.today() + timedelta(days=1)).isoformat()
   100	    try:
   101	        d = yf.download(
   102	            list(yf_syms), start=start, end=end,
   103	            auto_adjust=True, progress=False, threads=True, group_by="ticker",
   104	        )
   105	    except Exception as e:
   106	        st.warning(f"Live fetch failed: {e}")
   107	        return pd.DataFrame()
   108	    if d.empty:
   109	        return pd.DataFrame()
   110	
   111	    if len(yf_syms) == 1:
   112	        sym = yf_syms[0]
   113	        if isinstance(d.columns, pd.MultiIndex):
   114	            d.columns = d.columns.droplevel(1)
   115	        if "Close" in d.columns:
   116	            return pd.DataFrame({sym: d["Close"]}).dropna(how="all")
   117	        return pd.DataFrame()
   118	
   119	    out = {}
   120	    for sym in yf_syms:
   121	        try:
   122	            if sym in d.columns.get_level_values(0):
   123	                out[sym] = d[sym]["Close"].dropna()
   124	        except Exception:
   125	            pass
   126	    return pd.DataFrame(out).sort_index()
   127	
   128	
   129	def compute_strategy_returns(
   130	    closes: pd.DataFrame, pick_date: str
   131	) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
   132	    """Compute since-inception cumulative return (indexed=100) for each ticker
   133	    + equal-weight portfolio + per-window returns table.
   134	
   135	    Returns:
   136	      - normed: wide DataFrame indexed=100 from pick_date
   137	      - portfolio: equal-weight portfolio cumulative (Series)
   138	      - perf_table: per-ticker returns for windows
   139	    """
   140	    if closes.empty:
   141	        return pd.DataFrame(), pd.Series(dtype=float), pd.DataFrame()
   142	    closes = closes.sort_index()
   143	    anchor_ts = pd.Timestamp(pick_date)
   144	    sub = closes[closes.index >= anchor_ts]
   145	    if sub.empty:
   146	        return pd.DataFrame(), pd.Series(dtype=float), pd.DataFrame()
   147	    base = sub.iloc[0]
   148	    normed = (sub / base) * 100
   149	    # Equal-weight portfolio: mean across tickers each day
   150	    portfolio = normed.mean(axis=1, skipna=True)
   151	
   152	    # Per-window returns
   153	    rows = []
   154	    NAN = float("nan")
   155	    for ticker in closes.columns:
   156	        ser = closes[ticker].dropna()
   157	        if ser.empty:
   158	            continue
   159	        last = float(ser.iloc[-1])
   160	        after_pick = ser[ser.index >= anchor_ts]
   161	        since = float((last / after_pick.iloc[0] - 1) * 100) if not after_pick.empty else NAN
   162	
   163	        def ret_back(n: int) -> float:
   164	            if len(ser) <= n:
   165	                return NAN
   166	            prev = ser.iloc[-n - 1]
   167	            if pd.isna(prev) or prev == 0:
   168	                return NAN
   169	            return float((last / prev - 1) * 100)
   170	
   171	        rows.append({
   172	            "Ticker": ticker,
   173	            "Last": last,
   174	            "1D %": ret_back(1),
   175	            "5D %": ret_back(5),
   176	            "15D %": ret_back(15),
   177	            "30D %": ret_back(30),
   178	            "Since %": since,
   179	        })
   180	    perf = pd.DataFrame(rows).set_index("Ticker") if rows else pd.DataFrame()
   181	    return normed, portfolio, perf

exec
/bin/zsh -lc "nl -ba app/pages/4_🧬_Strategy_Picks.py | sed -n '1,260p'" in /Users/gcc/invest-dashboard
 succeeded in 0ms:
     1	"""Strategy Picks — v4/v5 biotech + HK 高股息 since-inception perf vs benchmark.
     2	
     3	D4 implementation:
     4	- 3 tabs (one per strategy)
     5	- For each: cumulative return chart (portfolio vs benchmark) + per-pick ranking table
     6	- Data: data/external/picks.db (v5) + data/external/v4_picks.csv + data/external/hd_picks.csv
     7	- Price fetch: yfinance live, cached 1h (picks tickers not in main universe by design)
     8	"""
     9	
    10	from __future__ import annotations
    11	
    12	import pandas as pd
    13	import streamlit as st
    14	
    15	from lib import db
    16	from lib import format as fmt
    17	from lib import strategy as strat
    18	from lib import charts
    19	
    20	st.set_page_config(
    21	    page_title="Strategy Picks · invest-dashboard",
    22	    page_icon="🧬",
    23	    layout="wide",
    24	)
    25	
    26	# Sidebar global search (B4 audit, on every page)
    27	with st.sidebar:
    28	    st.subheader("🔍 Find ticker")
    29	    pick = st.selectbox(
    30	        "Jump to ticker drill",
    31	        options=[""] + sorted(db.all_tickers()),
    32	        format_func=lambda x: fmt.fmt_ticker_bbg(x) if x else "— select —",
    33	        key="strategy_search",
    34	    )
    35	    if pick:
    36	        st.info(f"📍 {fmt.fmt_ticker_bbg(pick)} — Ticker Drill (D6) coming soon.")
    37	
    38	st.title("🧬 Strategy Picks Performance")
    39	st.caption(
    40	    "v4 / v5 biotech + HK 高股息 since-inception cumulative returns vs benchmark. "
    41	    "Data source: ic-foundry ledger.db + scoring Excel, picks fetched live via yfinance."
    42	)
    43	
    44	
    45	def render_strategy(strat_id: str) -> None:
    46	    cfg = strat.STRATEGIES[strat_id]
    47	    picks = cfg["loader"]()
    48	    if picks.empty:
    49	        st.warning(f"No picks for {cfg['name']} — check data/external/")
    50	        return
    51	
    52	    pick_date = cfg["pick_date"]
    53	    bench_sym = cfg["benchmark"]
    54	    bench_name = cfg["benchmark_name"]
    55	
    56	    # --- Header metrics ---
    57	    n_picks = len(picks)
    58	    days_since = (pd.Timestamp.now().normalize() - pd.Timestamp(pick_date)).days
    59	    c1, c2, c3, c4 = st.columns(4)
    60	    c1.metric("📅 Pick date", pick_date)
    61	    c2.metric("📊 # picks", n_picks)
    62	    c3.metric("📆 Days since", days_since)
    63	    c4.metric("📐 Benchmark", bench_sym)
    64	
    65	    # --- Fetch prices ---
    66	    yf_syms = tuple(picks["yf_sym"].dropna().unique().tolist())
    67	    # Fetch from pick_date - 10 days for benchmark anchor
    68	    earliest = (pd.Timestamp(pick_date) - pd.Timedelta(days=10)).date().isoformat()
    69	    closes = strat.fetch_picks_closes(yf_syms + (bench_sym,), start=earliest)
    70	
    71	    if closes.empty:
    72	        st.error("Live price fetch failed. Check network/yfinance.")
    73	        return
    74	
    75	    # Separate benchmark
    76	    bench_close = closes[bench_sym] if bench_sym in closes.columns else pd.Series(dtype=float)
    77	    picks_closes = closes.drop(columns=[bench_sym], errors="ignore")
    78	
    79	    # --- Compute returns ---
    80	    normed, portfolio, perf = strat.compute_strategy_returns(picks_closes, pick_date)
    81	
    82	    # Benchmark norm to 100 at pick_date anchor
    83	    bench_norm = pd.Series(dtype=float)
    84	    if not bench_close.empty:
    85	        anchor_ts = pd.Timestamp(pick_date)
    86	        bench_sub = bench_close[bench_close.index >= anchor_ts].dropna()
    87	        if not bench_sub.empty:
    88	            bench_norm = (bench_sub / bench_sub.iloc[0]) * 100
    89	
    90	    # --- Summary metrics ---
    91	    if not portfolio.empty:
    92	        port_last = portfolio.iloc[-1] - 100
    93	        bench_last = (bench_norm.iloc[-1] - 100) if not bench_norm.empty else None
    94	        alpha = (port_last - bench_last) if bench_last is not None else None
    95	        c1, c2, c3 = st.columns(3)
    96	        c1.metric(
    97	            "📈 Portfolio since-inception",
    98	            f"{port_last:+.2f}%",
    99	            delta=None,
   100	        )
   101	        c2.metric(
   102	            f"📐 Benchmark ({bench_sym})",
   103	            f"{bench_last:+.2f}%" if bench_last is not None else "—",
   104	            delta=None,
   105	        )
   106	        c3.metric(
   107	            "🎯 Alpha (pp)",
   108	            f"{alpha:+.2f}pp" if alpha is not None else "—",
   109	            delta=f"{'outperform' if alpha and alpha > 0 else 'underperform' if alpha else 'tied'}",
   110	            delta_color="normal" if alpha and alpha > 0 else "inverse" if alpha else "off",
   111	        )
   112	
   113	    # --- Cumulative return chart ---
   114	    if not portfolio.empty:
   115	        # Build a 2-column DataFrame: portfolio + benchmark
   116	        chart_df = pd.DataFrame({"Portfolio (equal-weight)": portfolio})
   117	        if not bench_norm.empty:
   118	            chart_df[f"{bench_sym} (benchmark)"] = bench_norm
   119	        chart_df = chart_df.dropna(how="all")
   120	
   121	        fig = charts.cumulative_return_chart(
   122	            picks_closes[picks_closes.index >= pd.Timestamp(pick_date)],
   123	            title=f"{cfg['name']} — Indexed return since {pick_date}",
   124	            pick_date=pick_date,
   125	        )
   126	        # Add benchmark overlay
   127	        import plotly.graph_objects as go
   128	        if not bench_norm.empty:
   129	            fig.add_trace(go.Scatter(
   130	                x=bench_norm.index, y=bench_norm.values,
   131	                mode="lines", name=f"{bench_sym} ({bench_name})",
   132	                line=dict(width=3, color="#a78bfa", dash="dash"),
   133	            ))
   134	        st.plotly_chart(fig, use_container_width=True)
   135	
   136	    # --- Top/Bottom ranking table ---
   137	    if perf.empty:
   138	        st.warning("No per-ticker performance data.")
   139	        return
   140	
   141	    # Merge in name + score from picks
   142	    picks_meta = picks.set_index("yf_sym")[["name"]] if "yf_sym" in picks.columns else pd.DataFrame()
   143	    if "score" in picks.columns and not picks.empty:
   144	        picks_meta["Pick Score"] = picks.set_index("yf_sym")["score"]
   145	    perf = perf.join(picks_meta, how="left")
   146	
   147	    perf_sorted = perf.sort_values("Since %", ascending=False, na_position="last")
   148	    perf_sorted.index = [fmt.fmt_ticker_bbg(t) for t in perf_sorted.index]
   149	
   150	    # Re-order columns
   151	    front_cols = ["name", "Pick Score", "Last", "1D %", "5D %", "15D %", "30D %", "Since %"]
   152	    cols_to_show = [c for c in front_cols if c in perf_sorted.columns]
   153	    perf_display = perf_sorted[cols_to_show].rename(columns={"name": "Name"})
   154	
   155	    c_top, c_bot = st.columns(2)
   156	    with c_top:
   157	        st.markdown(f"##### 🟢 Top {min(5, len(perf_display))} (since-inception)")
   158	        top5 = perf_display.head(5)
   159	        styler = (
   160	            top5.style
   161	            .format({
   162	                "Last": fmt.fmt_num,
   163	                "Pick Score": "{:.2f}",
   164	                "1D %": fmt.fmt_pct, "5D %": fmt.fmt_pct,
   165	                "15D %": fmt.fmt_pct, "30D %": fmt.fmt_pct, "Since %": fmt.fmt_pct,
   166	            }, na_rep="—")
   167	            .apply(fmt.style_pct_column,
   168	                   subset=[c for c in ["1D %", "5D %", "15D %", "30D %", "Since %"] if c in top5.columns])
   169	        )
   170	        st.dataframe(styler, use_container_width=True)
   171	    with c_bot:
   172	        st.markdown(f"##### 🔴 Bottom {min(5, len(perf_display))} (since-inception)")
   173	        bot5 = perf_display.tail(5).iloc[::-1]
   174	        styler = (
   175	            bot5.style
   176	            .format({
   177	                "Last": fmt.fmt_num,
   178	                "Pick Score": "{:.2f}",
   179	                "1D %": fmt.fmt_pct, "5D %": fmt.fmt_pct,
   180	                "15D %": fmt.fmt_pct, "30D %": fmt.fmt_pct, "Since %": fmt.fmt_pct,
   181	            }, na_rep="—")
   182	            .apply(fmt.style_pct_column,
   183	                   subset=[c for c in ["1D %", "5D %", "15D %", "30D %", "Since %"] if c in bot5.columns])
   184	        )
   185	        st.dataframe(styler, use_container_width=True)
   186	
   187	    # --- Full table (expandable) ---
   188	    with st.expander(f"📋 All {len(perf_display)} picks (sorted by since-inception)"):
   189	        styler = (
   190	            perf_display.style
   191	            .format({
   192	                "Last": fmt.fmt_num,
   193	                "Pick Score": "{:.2f}",
   194	                "1D %": fmt.fmt_pct, "5D %": fmt.fmt_pct,
   195	                "15D %": fmt.fmt_pct, "30D %": fmt.fmt_pct, "Since %": fmt.fmt_pct,
   196	            }, na_rep="—")
   197	            .apply(fmt.style_pct_column,
   198	                   subset=[c for c in ["1D %", "5D %", "15D %", "30D %", "Since %"] if c in perf_display.columns])
   199	        )
   200	        st.dataframe(styler, use_container_width=True, height=500)
   201	
   202	
   203	# --- M8 audit: tabs > dropdown ---
   204	strategy_tabs = st.tabs([strat.STRATEGIES[sid]["name"] for sid in strat.STRATEGIES])
   205	for tab, sid in zip(strategy_tabs, strat.STRATEGIES.keys()):
   206	    with tab:
   207	        render_strategy(sid)
   208	
   209	st.divider()
   210	st.caption(
   211	    "📊 **Methodology**: Equal-weight portfolio cumulative return from pick date. "
   212	    "All prices via yfinance (auto-adjusted for splits/dividends). "
   213	    "Benchmark: XBI for biotech, 3110.HK for HK 高股息."
   214	)
   215	st.caption(
   216	    "Picks source: v4/v5 from `data/external/picks.db` + `v4_picks.csv` · HK 高股息 from `hd_picks.csv` · "
   217	    "Sync via `cp ~/ic-foundry/ledger.db data/external/picks.db && git add && git commit` weekly."
   218	)

exec
/bin/zsh -lc "nl -ba app/pages/5_💰_Valuation_Scanner.py | sed -n '1,260p'" in /Users/gcc/invest-dashboard
 succeeded in 0ms:
     1	"""Valuation Scanner — find outlier candidates with cheap multiples + positive momentum.
     2	
     3	D5 implementation:
     4	- Filters: sector multi-select, min mcap, P/E percentile, YTD return range
     5	- Output: candidate list with sector-relative P/E rank + Z-score (if enough data)
     6	- Multi-criteria: combine cheap-on-multiple + recovering-momentum signal
     7	"""
     8	
     9	from __future__ import annotations
    10	
    11	from pathlib import Path
    12	
    13	import numpy as np
    14	import pandas as pd
    15	import streamlit as st
    16	import yaml
    17	
    18	from lib import db
    19	from lib import format as fmt
    20	
    21	st.set_page_config(
    22	    page_title="Valuation Scanner · invest-dashboard",
    23	    page_icon="💰",
    24	    layout="wide",
    25	)
    26	
    27	REPO_ROOT = Path(__file__).resolve().parent.parent.parent
    28	DOMAIN_CFG = REPO_ROOT / "config" / "domains" / "healthcare.yml"
    29	
    30	
    31	@st.cache_data(ttl=600)
    32	def load_domain_cfg() -> dict:
    33	    with DOMAIN_CFG.open() as f:
    34	        return yaml.safe_load(f)
    35	
    36	
    37	cfg = load_domain_cfg()
    38	
    39	# --- Sidebar global search ---
    40	with st.sidebar:
    41	    st.subheader("🔍 Find ticker")
    42	    pick = st.selectbox(
    43	        "Jump to ticker drill",
    44	        options=[""] + sorted(db.all_tickers()),
    45	        format_func=lambda x: fmt.fmt_ticker_bbg(x) if x else "— select —",
    46	        key="scanner_search",
    47	    )
    48	    if pick:
    49	        st.info(f"📍 {fmt.fmt_ticker_bbg(pick)} — Ticker Drill (D6) coming soon.")
    50	
    51	    st.divider()
    52	    st.subheader("📊 Filters")
    53	
    54	    sector_options = [(sec["id"], sec["name"]) for sec in cfg["sectors"]]
    55	    selected_sectors = st.multiselect(
    56	        "Sector",
    57	        options=[s[0] for s in sector_options],
    58	        default=[s[0] for s in sector_options],
    59	        format_func=lambda x: next(s[1] for s in sector_options if s[0] == x),
    60	    )
    61	
    62	    min_mcap_b = st.slider("Min market cap (USD B)", 0.0, 50.0, 5.0, 0.5)
    63	    pct_threshold = st.slider(
    64	        "P/E percentile threshold (within sector)",
    65	        0, 100, 25,
    66	        help="只显示 fwd P/E 在板块内分位 ≤ 此阈值的候选（25 = bottom quartile = cheap）"
    67	    )
    68	    pe_metric = st.selectbox("P/E metric", ["forward_pe", "trailing_pe"], index=0)
    69	    ytd_min, ytd_max = st.slider("YTD return range (%)", -100, 200, (-50, 100), 5)
    70	    min_5d = st.slider("Min 5D return (%)", -30, 30, -10, 1,
    71	                       help="recent momentum filter（正值过滤暴跌反弹候选）")
    72	
    73	
    74	# --- Build candidate universe ---
    75	st.title("💰 Valuation Scanner")
    76	st.caption(
    77	    "Cross-sectional scan — find cheap-on-multiple stocks with positive recent momentum. "
    78	    "Sector-internal P/E percentile + YTD/5D filter. Latest: " + (db.latest_snapshot_date() or "—")
    79	)
    80	
    81	if not selected_sectors:
    82	    st.warning("Select at least 1 sector in sidebar.")
    83	    st.stop()
    84	
    85	# Collect all tickers across selected sectors
    86	all_tickers_by_sec: dict[str, list[str]] = {}
    87	for sid in selected_sectors:
    88	    tlist = db.sector_tickers("healthcare", sid)["ticker"].tolist()
    89	    for t in tlist:
    90	        all_tickers_by_sec.setdefault(t, []).append(sid)
    91	
    92	all_t = tuple(all_tickers_by_sec.keys())
    93	if not all_t:
    94	    st.warning("No tickers in selected sectors.")
    95	    st.stop()
    96	
    97	# Returns + multiples
    98	closes = db.get_close_series_usd(all_t)
    99	rets = db.compute_returns(closes)
   100	mults = db.latest_multiples(all_t)
   101	name_map = db.ticker_to_name(prefer_cn=True)
   102	
   103	# Merge
   104	merged = rets.copy() if not rets.empty else pd.DataFrame(index=list(all_t))
   105	if not mults.empty:
   106	    for c in ["market_cap_usd", "mcap_tier", "trailing_pe", "forward_pe",
   107	              "ev_ebitda", "ev_sales", "fcf_yield", "pb"]:
   108	        if c in mults.columns:
   109	            merged[c] = mults[c]
   110	
   111	# Sector-internal P/E percentile
   112	# For each ticker, compute its P/E rank within its first sector
   113	@st.cache_data(ttl=300)
   114	def sector_pe_percentile(_mults_df: pd.DataFrame, _sector_map: dict[str, list[str]], pe_col: str) -> pd.Series:
   115	    """For each ticker, rank P/E within its sector (excluding NaN and negative).
   116	    Returns percentile [0,100] where 0 = cheapest."""
   117	    result = {}
   118	    # Group tickers by sector
   119	    sector_tickers: dict[str, list[str]] = {}
   120	    for t, secs in _sector_map.items():
   121	        for s in secs:
   122	            sector_tickers.setdefault(s, []).append(t)
   123	
   124	    for sec, t_list in sector_tickers.items():
   125	        in_sec = _mults_df.loc[_mults_df.index.intersection(t_list), pe_col].copy()
   126	        # exclude non-positive (neg earnings) for percentile calc
   127	        in_sec = in_sec[in_sec > 0].dropna()
   128	        if in_sec.empty:
   129	            continue
   130	        ranks = in_sec.rank(pct=True) * 100
   131	        for t in t_list:
   132	            if t in ranks.index:
   133	                # Keep min percentile across sectors (cheapest sector ranking wins)
   134	                if t not in result or ranks[t] < result[t]:
   135	                    result[t] = float(ranks[t])
   136	    return pd.Series(result, name="pe_percentile")
   137	
   138	
   139	pe_pct = sector_pe_percentile(mults, all_tickers_by_sec, pe_metric)
   140	merged["pe_percentile"] = pe_pct
   141	
   142	# Apply filters
   143	candidates = merged.copy()
   144	candidates = candidates[candidates["market_cap_usd"] >= min_mcap_b * 1e9]
   145	candidates = candidates[candidates["pe_percentile"] <= pct_threshold]
   146	candidates = candidates[candidates["pe_percentile"].notna()]
   147	candidates = candidates[(candidates["ytd_%"] >= ytd_min) & (candidates["ytd_%"] <= ytd_max)]
   148	candidates = candidates[candidates["5d_%"] >= min_5d]
   149	
   150	# Sort by P/E percentile ascending (cheapest first)
   151	candidates = candidates.sort_values("pe_percentile", ascending=True)
   152	
   153	# --- Result summary ---
   154	col1, col2, col3, col4 = st.columns(4)
   155	col1.metric("🌐 Universe scanned", f"{len(all_t)}")
   156	col2.metric("✅ Candidates", f"{len(candidates)}")
   157	col3.metric("📐 Median Mcap (USD B)",
   158	            f"${candidates['market_cap_usd'].median()/1e9:.1f}B" if not candidates.empty else "—")
   159	col4.metric("📈 Median YTD", fmt.fmt_pct(candidates['ytd_%'].median()) if not candidates.empty else "—")
   160	
   161	if candidates.empty:
   162	    st.warning(
   163	        "🤷 No candidates match filters. Loosen criteria (lower min mcap / higher P/E threshold / widen YTD range)."
   164	    )
   165	    st.stop()
   166	
   167	# Build display
   168	disp = pd.DataFrame(index=candidates.index)
   169	disp["BBG"] = [fmt.fmt_ticker_bbg(t) for t in disp.index]
   170	disp["Name"] = [name_map.get(t, t) for t in disp.index]
   171	disp["Sectors"] = [", ".join(all_tickers_by_sec.get(t, [])) for t in disp.index]
   172	disp["Tier"] = candidates.get("mcap_tier", pd.Series(index=candidates.index)).fillna("—")
   173	disp["Mcap USD"] = candidates["market_cap_usd"].apply(fmt.fmt_money_b)
   174	disp[f"{pe_metric.replace('_', ' ').title()}"] = candidates[pe_metric].apply(fmt.fmt_ratio)
   175	disp["Sector P/E %ile"] = candidates["pe_percentile"].apply(lambda v: f"{v:.0f}%" if pd.notna(v) else "—")
   176	disp["YTD %"] = candidates["ytd_%"].apply(fmt.fmt_pct)
   177	disp["1M %"] = candidates["1m_%"].apply(fmt.fmt_pct)
   178	disp["5D %"] = candidates["5d_%"].apply(fmt.fmt_pct)
   179	disp["EV/EBITDA"] = candidates["ev_ebitda"].apply(fmt.fmt_ratio)
   180	disp["FCF Yld"] = candidates["fcf_yield"].apply(fmt.fmt_pct_decimal)
   181	disp.index.name = "Ticker"
   182	
   183	# Color gradients
   184	styler = disp.style
   185	for col, num in [("YTD %", candidates["ytd_%"]), ("1M %", candidates["1m_%"]),
   186	                 ("5D %", candidates["5d_%"])]:
   187	    styler = styler.apply(
   188	        lambda _s, n=num: fmt.background_gradient_diverging(n),
   189	        subset=[col],
   190	    )
   191	# Lower better
   192	styler = styler.apply(
   193	    lambda _s: fmt.background_gradient_low_good(candidates[pe_metric]),
   194	    subset=[f"{pe_metric.replace('_', ' ').title()}"],
   195	)
   196	styler = styler.apply(
   197	    lambda _s: fmt.background_gradient_low_good(candidates["ev_ebitda"]),
   198	    subset=["EV/EBITDA"],
   199	)
   200	# Higher better
   201	styler = styler.apply(
   202	    lambda _s: fmt.background_gradient_low_good(
   203	        candidates["fcf_yield"], low_color="#dc2626", high_color="#16a34a"
   204	    ),
   205	    subset=["FCF Yld"],
   206	)
   207	# Sector P/E percentile column — low percentile = cheap = green
   208	styler = styler.apply(
   209	    lambda _s: fmt.background_gradient_low_good(candidates["pe_percentile"]),
   210	    subset=["Sector P/E %ile"],
   211	)
   212	
   213	st.dataframe(styler, use_container_width=True, height=560)
   214	
   215	# --- Interpretation hints ---
   216	with st.expander("📖 How to read this scan"):
   217	    st.markdown("""
   218	**Sector P/E %ile**：当前股票的 forward (or trailing) P/E 在所属板块内的分位。
   219	- `0%-25%` = cheapest quartile within sector
   220	- 一般 sell-side framework: 看 cheap multiple + 正面 momentum 一起 → 可能 re-rating 候选
   221	
   222	**YTD %**: 年至今总回报。负 YTD + 低 P/E 可能是 "fallen angel" 候选。
   223	正 YTD + 低 P/E 可能是 "value with momentum"。
   224	
   225	**5D %**: 最近 5 个交易日 momentum。Filter 默认 ≥ -10% 排除崩盘中候选。
   226	
   227	**EV/EBITDA**: complementary multiple，避免单看 P/E 误判（EPS 被一次性项目影响）。
   228	
   229	**FCF Yield**: free cash flow / market cap. 高 = 现金生成能力强 = 好。
   230	
   231	**注意**：
   232	- 板块 P/E 中位数受小市值标的扭曲 (4587 JP 在 Biotech 拉低均值)，min mcap filter 可缓解
   233	- 负 P/E (亏损) 不参与 percentile rank（排除 biotech 烧钱期标的）
   234	- Multi-sector ticker (e.g. ISRG ∈ hc_ai + medtech) 用最 cheap 的板块 percentile
   235	""")
   236	
   237	st.divider()
   238	st.caption(
   239	    "🎯 **Methodology**: Cross-sectional within selected sectors. Negative P/E excluded from percentile rank. "
   240	    "Latest snapshot: " + (db.latest_snapshot_date() or "—") + ". "
   241	    "Sector membership: many-to-many (ISRG ∈ hc_ai + medtech 等)."
   242	)

exec
/bin/zsh -lc "nl -ba app/pages/3_💎_CMSI_Coverage.py | sed -n '1,220p'" in /Users/gcc/invest-dashboard
 succeeded in 0ms:
     1	"""CMSI Coverage — 28 ticker cover list with full multiples + cross-sector tags.
     2	
     3	D5 implementation:
     4	- Region tabs (HK / US / CN-A)
     5	- Per region: full table with multiples + return windows + cross-sector membership
     6	- Defaults: name_cn first, mcap desc (M10 audit)
     7	"""
     8	
     9	from __future__ import annotations
    10	
    11	from pathlib import Path
    12	
    13	import pandas as pd
    14	import streamlit as st
    15	import yaml
    16	
    17	from lib import db
    18	from lib import format as fmt
    19	
    20	st.set_page_config(
    21	    page_title="CMSI Coverage · invest-dashboard",
    22	    page_icon="💎",
    23	    layout="wide",
    24	)
    25	
    26	# --- Sidebar global search ---
    27	with st.sidebar:
    28	    st.subheader("🔍 Find ticker")
    29	    pick = st.selectbox(
    30	        "Jump to ticker drill",
    31	        options=[""] + sorted(db.all_tickers()),
    32	        format_func=lambda x: fmt.fmt_ticker_bbg(x) if x else "— select —",
    33	        key="cmsi_search",
    34	    )
    35	    if pick:
    36	        st.info(f"📍 {fmt.fmt_ticker_bbg(pick)} — Ticker Drill (D6) coming soon.")
    37	
    38	st.title("💎 CMSI Healthcare Coverage")
    39	st.caption("28 ticker official cover list — HK 15 / US 10 / CN A-share 3. Latest data: " + (db.latest_snapshot_date() or "—"))
    40	
    41	
    42	# --- Load CMSI Coverage tickers ---
    43	cmsi = db.sector_tickers("healthcare", "_coverage")
    44	if cmsi.empty:
    45	    st.warning("No CMSI coverage data — check config/universes/cmsi_coverage_hc.yml")
    46	    st.stop()
    47	
    48	tickers = tuple(cmsi["ticker"].tolist())
    49	
    50	# --- Compute returns + multiples for all CMSI tickers ---
    51	closes = db.get_close_series_usd(tickers)
    52	rets = db.compute_returns(closes)
    53	mults = db.latest_multiples(tickers)
    54	
    55	# --- Find cross-sector membership ---
    56	# Query all sectors each ticker belongs to (excluding _coverage)
    57	@st.cache_data(ttl=300)
    58	def cross_membership(_tickers: tuple[str, ...]) -> dict[str, list[str]]:
    59	    placeholders = ",".join("?" * len(_tickers))
    60	    df = db.query(
    61	        f"SELECT ticker, sector FROM universe_member "
    62	        f"WHERE ticker IN ({placeholders}) AND sector != '_coverage' "
    63	        f"ORDER BY ticker, sector",
    64	        tuple(_tickers),
    65	    )
    66	    out: dict[str, list[str]] = {}
    67	    for _, row in df.iterrows():
    68	        out.setdefault(row["ticker"], []).append(row["sector"])
    69	    return out
    70	
    71	
    72	cross = cross_membership(tickers)
    73	
    74	# --- Merge into display DataFrame ---
    75	merged = rets.copy() if not rets.empty else pd.DataFrame(index=list(tickers))
    76	merged["name_cn"] = cmsi.set_index("ticker")["name_cn"]
    77	merged["name_en"] = cmsi.set_index("ticker")["name_en"]
    78	merged["region"] = cmsi.set_index("ticker")["region"]
    79	merged["BBG"] = [fmt.fmt_ticker_bbg(t) for t in merged.index]
    80	if not mults.empty:
    81	    for c in ["market_cap_usd", "mcap_tier", "trailing_pe", "forward_pe",
    82	              "ev_ebitda", "ev_sales", "fcf_yield", "pb"]:
    83	        if c in mults.columns:
    84	            merged[c] = mults[c]
    85	
    86	# Cross-sector tags: convert to icons
    87	def _cross_tag(ticker: str) -> str:
    88	    sectors = cross.get(ticker, [])
    89	    if not sectors:
    90	        return ""
    91	    # 简短 emoji mapping
    92	    icons = {
    93	        "biotech": "🧬", "pharma": "💊", "hc_ai": "🤖",
    94	        "medtech": "⚕️", "hospital_care": "🏥",
    95	        "managed_care": "🩺", "cxo": "🧪",
    96	    }
    97	    return " ".join(icons.get(s, f"[{s}]") for s in sectors)
    98	
    99	
   100	merged["Cross-Sector"] = [_cross_tag(t) for t in merged.index]
   101	
   102	# --- Default sort: mcap desc (M10 audit) ---
   103	merged = merged.sort_values("market_cap_usd", ascending=False, na_position="last")
   104	
   105	# --- Region tabs ---
   106	regions = ["HK", "US", "CN", "All"]
   107	tabs = st.tabs([f"{r} ({sum(merged['region']==r) if r != 'All' else len(merged)})" for r in regions])
   108	
   109	
   110	def render_region(df: pd.DataFrame) -> None:
   111	    if df.empty:
   112	        st.info("No tickers in this region.")
   113	        return
   114	
   115	    # Build display string DataFrame (M7 audit pattern)
   116	    disp = pd.DataFrame(index=df.index)
   117	    disp["BBG"] = df["BBG"]
   118	    disp["Name (CN)"] = df["name_cn"].fillna("—")
   119	    disp["Name (EN)"] = df["name_en"].fillna("—")
   120	    disp["Region"] = df["region"]
   121	    disp["Tier"] = df.get("mcap_tier", pd.Series(index=df.index)).fillna("—")
   122	    disp["Cross"] = df["Cross-Sector"]
   123	    disp["Mcap USD"] = df["market_cap_usd"].apply(fmt.fmt_money_b)
   124	    disp["YTD %"] = df["ytd_%"].apply(fmt.fmt_pct)
   125	    disp["1M %"] = df["1m_%"].apply(fmt.fmt_pct)
   126	    disp["5D %"] = df["5d_%"].apply(fmt.fmt_pct)
   127	    disp["1D %"] = df["1d_%"].apply(fmt.fmt_pct)
   128	    disp["Trail P/E"] = df["trailing_pe"].apply(fmt.fmt_ratio)
   129	    disp["Fwd P/E"] = df["forward_pe"].apply(fmt.fmt_ratio)
   130	    disp["EV/EBITDA"] = df["ev_ebitda"].apply(fmt.fmt_ratio)
   131	    disp["FCF Yld"] = df["fcf_yield"].apply(fmt.fmt_pct_decimal)
   132	    disp["P/B"] = df["pb"].apply(fmt.fmt_ratio)
   133	    disp.index.name = "Ticker"
   134	
   135	    pct_cols = ["YTD %", "1M %", "5D %", "1D %"]
   136	    mult_cols = ["Trail P/E", "Fwd P/E", "EV/EBITDA", "P/B"]
   137	
   138	    styler = disp.style
   139	    for col in pct_cols:
   140	        num = df["ytd_%" if "YTD" in col else ("1m_%" if "1M" in col else ("5d_%" if "5D" in col else "1d_%"))]
   141	        styler = styler.apply(
   142	            lambda _s, n=num: fmt.background_gradient_diverging(n),
   143	            subset=[col],
   144	        )
   145	    for col in mult_cols:
   146	        num_field = {"Trail P/E": "trailing_pe", "Fwd P/E": "forward_pe",
   147	                     "EV/EBITDA": "ev_ebitda", "P/B": "pb"}[col]
   148	        styler = styler.apply(
   149	            lambda _s, n=df[num_field]: fmt.background_gradient_low_good(n),
   150	            subset=[col],
   151	        )
   152	    styler = styler.apply(
   153	        lambda _s: fmt.background_gradient_low_good(df["fcf_yield"], low_color="#dc2626", high_color="#16a34a"),
   154	        subset=["FCF Yld"],
   155	    )
   156	
   157	    st.dataframe(styler, use_container_width=True, height=560)
   158	
   159	
   160	for tab, region in zip(tabs, regions):
   161	    with tab:
   162	        if region == "All":
   163	            render_region(merged)
   164	        else:
   165	            render_region(merged[merged["region"] == region])
   166	
   167	st.divider()
   168	st.caption(
   169	    "🧬 = Biotech · 💊 = Pharma · 🤖 = HC+AI · ⚕️ = Medtech · 🏥 = Hospital Care · 🩺 = Managed Care · 🧪 = CXO. "
   170	    "Cross-sector tags 表示 ticker 同时存在于其他 sector universe（dedup 自动）。"
   171	)
   172	st.caption(
   173	    f"📊 Cover list source: `config/universes/cmsi_coverage_hc.yml` ({len(merged)} tickers). "
   174	    "默认按 market cap 降序，名字优先中文 (M10 audit)。"
   175	)

exec
/bin/zsh -lc "nl -ba app/lib/charts.py | sed -n '1,180p'" in /Users/gcc/invest-dashboard
exec
/bin/zsh -lc "nl -ba app/lib/db.py | sed -n '1,260p'" in /Users/gcc/invest-dashboard
 succeeded in 0ms:
     1	"""Plotly chart helpers."""
     2	
     3	from __future__ import annotations
     4	
     5	import pandas as pd
     6	import plotly.graph_objects as go
     7	
     8	
     9	PLOT_TEMPLATE = "plotly_dark"
    10	PRIMARY = "#22c55e"
    11	SECONDARY = "#06b6d4"
    12	BENCH_LINE = "#a78bfa"
    13	GRID = "#334155"
    14	
    15	
    16	def price_line_chart(
    17	    df: pd.DataFrame,
    18	    title: str = "",
    19	    ylabel: str = "Close",
    20	    benchmark: pd.Series | None = None,
    21	    benchmark_name: str = "",
    22	) -> go.Figure:
    23	    """Single-series price line.
    24	    df: wide DataFrame with date index, one (or more) ticker columns.
    25	    """
    26	    fig = go.Figure()
    27	    for col in df.columns:
    28	        fig.add_trace(go.Scatter(
    29	            x=df.index, y=df[col],
    30	            mode="lines", name=col,
    31	            line=dict(width=2),
    32	        ))
    33	    if benchmark is not None and not benchmark.empty:
    34	        fig.add_trace(go.Scatter(
    35	            x=benchmark.index, y=benchmark.values,
    36	            mode="lines", name=benchmark_name or "Benchmark",
    37	            line=dict(width=1.5, color=BENCH_LINE, dash="dot"),
    38	        ))
    39	    fig.update_layout(
    40	        template=PLOT_TEMPLATE,
    41	        title=title,
    42	        yaxis_title=ylabel,
    43	        height=380,
    44	        margin=dict(l=10, r=10, t=40, b=10),
    45	        legend=dict(orientation="h", yanchor="bottom", y=1.0),
    46	    )
    47	    return fig
    48	
    49	
    50	def cumulative_return_chart(
    51	    closes: pd.DataFrame,
    52	    title: str = "",
    53	    pick_date: str | None = None,
    54	) -> go.Figure:
    55	    """Index series to pick_date (or first date) = 100.
    56	    Each ticker shown as a translucent line, plus equal-weighted portfolio in bold.
    57	    """
    58	    if closes.empty:
    59	        return go.Figure()
    60	    closes = closes.sort_index()
    61	    if pick_date:
    62	        anchor_ts = pd.Timestamp(pick_date)
    63	        closes = closes[closes.index >= anchor_ts]
    64	        if closes.empty:
    65	            return go.Figure()
    66	    base = closes.iloc[0]
    67	    norm = (closes / base) * 100
    68	    portfolio = norm.mean(axis=1)
    69	    fig = go.Figure()
    70	    for col in norm.columns:
    71	        fig.add_trace(go.Scatter(
    72	            x=norm.index, y=norm[col],
    73	            mode="lines", name=col,
    74	            line=dict(width=1), opacity=0.35,
    75	            showlegend=False, hoverinfo="x+y+name",
    76	        ))
    77	    fig.add_trace(go.Scatter(
    78	        x=portfolio.index, y=portfolio.values,
    79	        mode="lines", name="Equal-weight portfolio",
    80	        line=dict(width=3, color=PRIMARY),
    81	    ))
    82	    fig.update_layout(
    83	        template=PLOT_TEMPLATE,
    84	        title=title,
    85	        yaxis_title="Indexed (start=100)",
    86	        height=420,
    87	        margin=dict(l=10, r=10, t=40, b=10),
    88	    )
    89	    return fig

 succeeded in 0ms:
     1	"""SQLite read helpers for Streamlit pages."""
     2	
     3	from __future__ import annotations
     4	
     5	import sqlite3
     6	from pathlib import Path
     7	
     8	import pandas as pd
     9	import streamlit as st
    10	
    11	REPO_ROOT = Path(__file__).resolve().parent.parent.parent
    12	DB_PATH = REPO_ROOT / "data" / "snapshots.db"
    13	
    14	
    15	def connect() -> sqlite3.Connection:
    16	    """Read-only connection."""
    17	    return sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    18	
    19	
    20	def query(sql: str, params: tuple | list | dict | None = None) -> pd.DataFrame:
    21	    conn = connect()
    22	    try:
    23	        return pd.read_sql_query(sql, conn, params=params or ())
    24	    finally:
    25	        conn.close()
    26	
    27	
    28	# ---------- metadata ----------
    29	@st.cache_data(ttl=300)
    30	def latest_snapshot_date() -> str | None:
    31	    df = query("SELECT MAX(date) AS d FROM multiples_daily")
    32	    return df["d"].iloc[0] if not df.empty else None
    33	
    34	
    35	@st.cache_data(ttl=300)
    36	def last_fetch_utc() -> str | None:
    37	    df = query("SELECT value FROM meta WHERE key = 'last_fetch_utc'")
    38	    return df["value"].iloc[0] if not df.empty else None
    39	
    40	
    41	@st.cache_data(ttl=300)
    42	def universe_summary() -> pd.DataFrame:
    43	    return query(
    44	        "SELECT domain, sector, COUNT(*) AS n FROM universe_member "
    45	        "WHERE sector != '_coverage' GROUP BY domain, sector ORDER BY domain, sector"
    46	    )
    47	
    48	
    49	# ---------- universe ----------
    50	@st.cache_data(ttl=300)
    51	def all_tickers() -> list[str]:
    52	    return query("SELECT DISTINCT ticker FROM universe_member")["ticker"].tolist()
    53	
    54	
    55	@st.cache_data(ttl=300)
    56	def sector_tickers(domain: str, sector: str) -> pd.DataFrame:
    57	    return query(
    58	        "SELECT ticker, name_cn, name_en, region "
    59	        "FROM universe_member WHERE domain = ? AND sector = ? "
    60	        "ORDER BY ticker",
    61	        (domain, sector),
    62	    )
    63	
    64	
    65	@st.cache_data(ttl=300)
    66	def ticker_to_name(prefer_cn: bool = True) -> dict[str, str]:
    67	    """Resolve display name. M10 audit fix: default to Chinese first (中文卖方 习惯).
    68	
    69	    Set prefer_cn=False to fall back to English-first."""
    70	    if prefer_cn:
    71	        col_expr = "COALESCE(name_cn, name_en, ticker)"
    72	    else:
    73	        col_expr = "COALESCE(name_en, name_cn, ticker)"
    74	    df = query(
    75	        f"SELECT ticker, {col_expr} AS display_name "
    76	        "FROM universe_member GROUP BY ticker"
    77	    )
    78	    return dict(zip(df["ticker"], df["display_name"]))
    79	
    80	
    81	# ---------- prices & returns ----------
    82	@st.cache_data(ttl=300)
    83	def get_close_series(tickers: tuple[str, ...]) -> pd.DataFrame:
    84	    """Wide-format close prices: index=date, columns=ticker. Tuple for cache."""
    85	    if not tickers:
    86	        return pd.DataFrame()
    87	    placeholders = ",".join("?" * len(tickers))
    88	    df = query(
    89	        f"SELECT ticker, date, close FROM prices_daily "
    90	        f"WHERE ticker IN ({placeholders}) ORDER BY date",
    91	        tuple(tickers),
    92	    )
    93	    if df.empty:
    94	        return pd.DataFrame()
    95	    df["date"] = pd.to_datetime(df["date"])
    96	    return df.pivot(index="date", columns="ticker", values="close").sort_index()
    97	
    98	
    99	def compute_returns(closes: pd.DataFrame) -> pd.DataFrame:
   100	    """Per-ticker return windows. Each ticker uses its OWN last valid close —
   101	    avoids ragged-tail bug across markets (JP closes earlier than US).
   102	    Output index=ticker, columns=[last, 1d_%, 5d_%, 1m_%, ytd_%, 60d_%]."""
   103	    if closes.empty:
   104	        return pd.DataFrame()
   105	
   106	    closes = closes.sort_index()
   107	    out: dict[str, dict[str, float | None]] = {}
   108	
   109	    NAN = float("nan")
   110	    for ticker in closes.columns:
   111	        ser = closes[ticker].dropna()
   112	        if ser.empty:
   113	            out[ticker] = {k: NAN for k in ("last", "1d_%", "5d_%", "1m_%", "ytd_%", "60d_%")}
   114	            continue
   115	
   116	        last = float(ser.iloc[-1])
   117	
   118	        def ret_back(n: int) -> float:
   119	            if len(ser) <= n:
   120	                return NAN
   121	            prev = ser.iloc[-n - 1]
   122	            if pd.isna(prev) or prev == 0:
   123	                return NAN
   124	            return float((ser.iloc[-1] / prev - 1) * 100)
   125	
   126	        # YTD: first close in current year (use each ticker's own anchor)
   127	        year = ser.index.max().year
   128	        this_year = ser[ser.index >= pd.Timestamp(f"{year}-01-01")]
   129	        if not this_year.empty and this_year.iloc[0] != 0:
   130	            ytd = float((ser.iloc[-1] / this_year.iloc[0] - 1) * 100)
   131	        else:
   132	            ytd = NAN
   133	
   134	        out[ticker] = {
   135	            "last": last,
   136	            "1d_%": ret_back(1),
   137	            "5d_%": ret_back(5),
   138	            "1m_%": ret_back(21),
   139	            "ytd_%": ytd,
   140	            "60d_%": ret_back(60),
   141	        }
   142	
   143	    return pd.DataFrame.from_dict(out, orient="index")
   144	
   145	
   146	# ---------- multiples ----------
   147	@st.cache_data(ttl=300)
   148	def latest_multiples(tickers: tuple[str, ...]) -> pd.DataFrame:
   149	    """Latest multiples_daily snapshot per ticker. Includes M1 close_usd + M11 mcap_tier."""
   150	    if not tickers:
   151	        return pd.DataFrame()
   152	    placeholders = ",".join("?" * len(tickers))
   153	    df = query(
   154	        f"""
   155	        SELECT m.* FROM multiples_daily m
   156	        INNER JOIN (
   157	          SELECT ticker, MAX(date) AS max_date
   158	          FROM multiples_daily
   159	          WHERE ticker IN ({placeholders})
   160	          GROUP BY ticker
   161	        ) latest
   162	        ON m.ticker = latest.ticker AND m.date = latest.max_date
   163	        """,
   164	        tuple(tickers),
   165	    )
   166	    if df.empty:
   167	        return df
   168	    return df.set_index("ticker")
   169	
   170	
   171	@st.cache_data(ttl=300)
   172	def get_close_series_usd(tickers: tuple[str, ...]) -> pd.DataFrame:
   173	    """M1 audit fix: USD-converted close series (so cross-region returns are comparable).
   174	
   175	    Falls back to local close × FX if close_usd is null (legacy rows pre-M1 fix).
   176	    """
   177	    if not tickers:
   178	        return pd.DataFrame()
   179	    placeholders = ",".join("?" * len(tickers))
   180	    df = query(
   181	        f"SELECT ticker, date, COALESCE(close_usd, close) AS close_usd "
   182	        f"FROM prices_daily WHERE ticker IN ({placeholders}) ORDER BY date",
   183	        tuple(tickers),
   184	    )
   185	    if df.empty:
   186	        return pd.DataFrame()
   187	    df["date"] = pd.to_datetime(df["date"])
   188	    return df.pivot(index="date", columns="ticker", values="close_usd").sort_index()
   189	
   190	
   191	# ---------- top movers ----------
   192	@st.cache_data(ttl=300)
   193	def top_movers(n: int = 10) -> tuple[pd.DataFrame, pd.DataFrame]:
   194	    """Top n gainers and losers by 1-day return across all universe tickers."""
   195	    tickers = tuple(all_tickers())
   196	    closes = get_close_series(tickers)
   197	    rets = compute_returns(closes)
   198	    if rets.empty:
   199	        return pd.DataFrame(), pd.DataFrame()
   200	    name_map = ticker_to_name()
   201	    rets["name"] = rets.index.map(name_map)
   202	    rets = rets[["name", "last", "1d_%", "5d_%", "1m_%", "ytd_%"]]
   203	    gainers = rets.sort_values("1d_%", ascending=False).head(n)
   204	    losers = rets.sort_values("1d_%", ascending=True).head(n)
   205	    return gainers, losers

exec
/bin/zsh -lc "nl -ba app/lib/format.py | sed -n '1,160p'" in /Users/gcc/invest-dashboard
 succeeded in 0ms:
     1	"""Number / color formatters for dashboard tables."""
     2	
     3	from __future__ import annotations
     4	
     5	import pandas as pd
     6	
     7	# Colors
     8	GREEN = "#22c55e"
     9	RED = "#ef4444"
    10	NEUTRAL = "#94a3b8"
    11	
    12	
    13	def _is_na(v) -> bool:
    14	    if v is None:
    15	        return True
    16	    if isinstance(v, float) and pd.isna(v):
    17	        return True
    18	    return False
    19	
    20	
    21	def fmt_pct(v, decimals: int = 2) -> str:
    22	    if _is_na(v):
    23	        return "—"
    24	    return f"{v:+.{decimals}f}%"
    25	
    26	
    27	def fmt_pct_decimal(v, decimals: int = 2) -> str:
    28	    """For values already in decimal form (0.05 = 5%)."""
    29	    if _is_na(v):
    30	        return "—"
    31	    return f"{v * 100:+.{decimals}f}%"
    32	
    33	
    34	def fmt_money_b(v) -> str:
    35	    """USD billions / millions."""
    36	    if _is_na(v):
    37	        return "—"
    38	    if abs(v) >= 1e9:
    39	        return f"${v / 1e9:.1f}B"
    40	    if abs(v) >= 1e6:
    41	        return f"${v / 1e6:.0f}M"
    42	    return f"${v:.0f}"
    43	
    44	
    45	def fmt_ratio(v, decimals: int = 1) -> str:
    46	    if _is_na(v):
    47	        return "—"
    48	    if v < 0:
    49	        return "neg"
    50	    return f"{v:.{decimals}f}x"
    51	
    52	
    53	def fmt_price(v, decimals: int = 2) -> str:
    54	    if _is_na(v):
    55	        return "—"
    56	    return f"{v:,.{decimals}f}"
    57	
    58	
    59	def fmt_num(v, decimals: int = 2) -> str:
    60	    """Plain number, e.g. for benchmark Last price."""
    61	    if _is_na(v):
    62	        return "—"
    63	    return f"{v:,.{decimals}f}"
    64	
    65	
    66	def fmt_ticker_bbg(ticker: str) -> str:
    67	    """n2 audit fix: Bloomberg ticker style '2269 HK' instead of '2269.HK'.
    68	
    69	    Suffix mapping:
    70	      .HK → HK (Hong Kong)
    71	      .T  → JP (Tokyo, Bloomberg uses JP not T)
    72	      .SS → CH (Shanghai, Bloomberg uses CH)
    73	      .SZ → CH (Shenzhen, Bloomberg uses CH)
    74	      .KS → KS (Korea)
    75	    """
    76	    if not ticker or "." not in ticker:
    77	        return ticker
    78	    code, suffix = ticker.split(".", 1)
    79	    mapping = {"HK": "HK", "T": "JP", "SS": "CH", "SZ": "CH", "KS": "KS"}
    80	    return f"{code} {mapping.get(suffix, suffix)}"
    81	
    82	
    83	def color_pct(v) -> str:
    84	    """Return CSS color string for a percentage value."""
    85	    if v is None or (isinstance(v, float) and pd.isna(v)):
    86	        return f"color: {NEUTRAL}"
    87	    if v > 0:
    88	        return f"color: {GREEN}; font-weight: 600"
    89	    if v < 0:
    90	        return f"color: {RED}; font-weight: 600"
    91	    return f"color: {NEUTRAL}"
    92	
    93	
    94	def style_pct_column(s: pd.Series) -> list[str]:
    95	    """For DataFrame.style.apply: color each cell red/green."""
    96	    return [color_pct(v) for v in s]
    97	
    98	
    99	def background_gradient_diverging(
   100	    s: pd.Series,
   101	    mid: float = 0,
   102	    pos_color: str = "#16a34a",
   103	    neg_color: str = "#dc2626",
   104	    intensity: float = 0.35,
   105	) -> list[str]:
   106	    """Diverging color background for numeric Series. Intensity 0-1 (alpha)."""
   107	    out = []
   108	    s_clean = s.dropna()
   109	    if s_clean.empty:
   110	        return [""] * len(s)
   111	    max_abs = max(abs(s_clean.min() - mid), abs(s_clean.max() - mid)) or 1
   112	    for v in s:
   113	        if pd.isna(v):
   114	            out.append("")
   115	            continue
   116	        if v >= mid:
   117	            ratio = min(abs(v - mid) / max_abs, 1.0) * intensity
   118	            color = pos_color
   119	        else:
   120	            ratio = min(abs(v - mid) / max_abs, 1.0) * intensity
   121	            color = neg_color
   122	        out.append(f"background-color: {color}{int(ratio * 255):02x}")
   123	    return out
   124	
   125	
   126	def background_gradient_low_good(
   127	    s: pd.Series,
   128	    low_color: str = "#16a34a",
   129	    high_color: str = "#dc2626",
   130	    intensity: float = 0.30,
   131	) -> list[str]:
   132	    """For ratios where lower is better (P/E, EV/EBITDA). Green = low, Red = high."""
   133	    out = []
   134	    s_clean = s.dropna()
   135	    if s_clean.empty or len(s_clean) < 2:
   136	        return [""] * len(s)
   137	    lo, hi = s_clean.min(), s_clean.max()
   138	    if hi == lo:
   139	        return [""] * len(s)
   140	    for v in s:
   141	        if pd.isna(v) or v < 0:    # negative ratios = neg earnings, skip
   142	            out.append("")
   143	            continue
   144	        ratio_lo = (hi - v) / (hi - lo) * intensity   # closer to low = greener
   145	        ratio_hi = (v - lo) / (hi - lo) * intensity
   146	        if ratio_lo >= ratio_hi:
   147	            out.append(f"background-color: {low_color}{int(ratio_lo * 255):02x}")
   148	        else:
   149	            out.append(f"background-color: {high_color}{int(ratio_hi * 255):02x}")
   150	    return out

exec
/bin/zsh -lc "nl -ba .github/workflows/fetch_eod.yml | sed -n '1,140p'" in /Users/gcc/invest-dashboard
 succeeded in 0ms:
     1	name: Fetch EOD data
     2	
     3	on:
     4	  schedule:
     5	    # US 收盘 16:00 ET. EDT = UTC-4 → 20:00 UTC; EST = UTC-5 → 21:00 UTC.
     6	    # 跑 22:30 UTC 兼容夏冬时
     7	    - cron: '30 22 * * 1-5'
     8	    # HK 收盘 16:00 HKT = 08:00 UTC. 跑 09:00 UTC.
     9	    - cron: '0 9 * * 1-5'
    10	  workflow_dispatch:               # 允许手动从 Actions tab 触发
    11	    inputs:
    12	      backfill_days:
    13	        description: 'Backfill historical days (0 = today only)'
    14	        required: false
    15	        default: '0'
    16	
    17	permissions:
    18	  contents: write                  # 允许 bot push 数据 commit
    19	
    20	jobs:
    21	  fetch:
    22	    runs-on: ubuntu-latest
    23	    concurrency:
    24	      group: fetch-eod
    25	      cancel-in-progress: false
    26	    steps:
    27	      - uses: actions/checkout@v4
    28	
    29	      - uses: actions/setup-python@v5
    30	        with:
    31	          python-version: '3.12'
    32	          cache: 'pip'
    33	
    34	      - name: Install deps
    35	        run: pip install -r requirements.txt
    36	
    37	      - name: Init schema (idempotent)
    38	        run: python jobs/init_db.py
    39	
    40	      - name: Load universe
    41	        run: python jobs/load_universe.py
    42	
    43	      - name: Fetch EOD data
    44	        run: python jobs/fetch_eod.py --backfill-days "${{ github.event.inputs.backfill_days || '0' }}"
    45	
    46	      - name: Commit data
    47	        run: |
    48	          git config user.email "data-bot@github.com"
    49	          git config user.name "data-bot"
    50	          git add data/snapshots.db
    51	          if git diff-index --quiet HEAD; then
    52	            echo "No data changes to commit"
    53	          else
    54	            git commit -m "data: EOD snapshot $(date -u +%Y-%m-%d) [skip ci]"
    55	            git push
    56	          fi

exec
/bin/zsh -lc "nl -ba README.md | sed -n '70,115p'" in /Users/gcc/invest-dashboard
 succeeded in 0ms:
    70	## Roadmap
    71	
    72	- **P0 (Week 1)**: Home + Sector Heatmap + CMSI Coverage + Strategy Picks + Valuation Scanner + Ticker Drill
    73	- **P1 (Week 2-4)**: Multiple Z-score (需 60 天数据)、Earnings drift tracker、YTD decomp
    74	- **P2 (Backlog)**: Earnings calendar、Insider trades、Cross-membership comparison
    75	- **P1 deferred from audit**: 港股通 / 北向资金（中资 healthcare sell-side 核心指标，yfinance 无，需 AKShare / Tushare 集成）
    76	
    77	## Operational notes
    78	
    79	### SQLite-in-git growth (M5 audit fix)
    80	
    81	`data/snapshots.db` is committed daily. With binary churn in git pack, growth is faster
    82	than working-file size suggests. Migration trigger points:
    83	
    84	- Working DB > **50MB** → consider partitioned Parquet snapshots
    85	- `.git/pack` > **200MB** → migrate to external SQLite (Turso/Supabase free tier)
    86	- Multi-year history (3+ years) → mandatory migration
    87	
    88	Current state: ~640KB DB after 60-day backfill of 106 tickers → ~4MB/yr projected.
    89	
    90	### Data path for D4 Strategy Picks (B1 audit)
    91	
    92	`ic-foundry/ledger.db` lives in `~/ic-foundry/` on George's Mac — **NOT accessible**
    93	from Streamlit Cloud. For D4 deployment:
    94	
    95	- **Scheme A** (recommended): `cp ~/ic-foundry/ledger.db data/external/picks.db` and commit periodically
    96	- **Scheme B**: extract picks_v2 to a derived JSON in repo (less sensitive than raw ledger)
    97	- **Scheme C**: external DB via Streamlit secrets (Turso / Supabase)
    98	
    99	Default: Scheme A — sync via `make sync-ledger`.
   100	
   101	### China network proxy (国内 dev)
   102	
   103	When running locally in China for yfinance:
   104	```bash
   105	export HTTP_PROXY=http://127.0.0.1:7897
   106	export HTTPS_PROXY=http://127.0.0.1:7897
   107	```
   108	GitHub Actions runs on Microsoft cloud — proxy NOT needed for scheduled fetches.
   109	
   110	### Known yfinance gotchas
   111	
   112	- **BGNE → ONC rename**: BeOne Medicines (ONC) historical data may not include pre-rename
   113	  ticker (BGNE). For YTD anchored at Jan 1 2026, ONC has continuous data — safe.
   114	- **Hong Kong stocks**: 复权 precision略糙 vs Futu OpenAPI. Severe backtest 用 Futu (eval-ledger).
   115	  Dashboard daily quick scan 用 yfinance 够。

exec
/bin/zsh -lc "rg -n \"weekly_perf|equal-weight|mean\\(|ffill|portfolio|cumulative\" -S . /Users/gcc/ic-foundry 2>/dev/null" in /Users/gcc/invest-dashboard
 succeeded in 0ms:
/Users/gcc/ic-foundry/runs/2026-05-15-m1-via-engines.log.legacy:15:09:10:34  Step 2: Portfolio PnL reproduction — 7 stocks 2026-03-20 → 2026-05-13
/Users/gcc/ic-foundry/runs/2026-05-15-m1-via-engines.log.legacy:26:09:10:43    Portfolio total: -0.0181 (M1 ref -0.0181, delta 0.0000) PASS
/Users/gcc/ic-foundry/runs/2026-05-15-m1-via-engines.log.legacy:34:09:10:43    Portfolio PnL reproduction  : PASS
/Users/gcc/ic-foundry/runs/2026-05-15-m1-via-engines.log.legacy:50:09:53:25  Step 2: Portfolio PnL reproduction — 7 stocks 2026-03-20 → 2026-05-13
/Users/gcc/ic-foundry/runs/2026-05-15-m1-via-engines.log.legacy:61:09:53:29    Portfolio total: -0.0181 (M1 ref -0.0181, delta 0.0000) PASS
/Users/gcc/ic-foundry/runs/2026-05-15-m1-via-engines.log.legacy:69:09:53:29    Portfolio PnL reproduction  : PASS
./jobs/fetch_eod.py:3:Pattern crib from ~/strategy-weekly/weekly_perf.py:74-102 (yfinance batch).
./app/pages/1_🏥_Healthcare.py:67:        "1D % avg": rets["1d_%"].mean(),
./app/pages/1_🏥_Healthcare.py:68:        "5D % avg": rets["5d_%"].mean(),
./app/pages/1_🏥_Healthcare.py:69:        "1M % avg": rets["1m_%"].mean(),
./app/pages/1_🏥_Healthcare.py:70:        "YTD % avg": rets["ytd_%"].mean(),
./app/pages/2_🔥_Sector_Heatmap.py:159:                "Mean": fmt.fmt_pct(s.mean() if not s.empty else None),
./app/pages/2_🔥_Sector_Heatmap.py:168:                "Mean": fmt_fn(s.mean() if not s.empty else None),
./app/lib/strategy.py:132:    """Compute since-inception cumulative return (indexed=100) for each ticker
./app/lib/strategy.py:133:    + equal-weight portfolio + per-window returns table.
./app/lib/strategy.py:137:      - portfolio: equal-weight portfolio cumulative (Series)
./app/lib/strategy.py:149:    # Equal-weight portfolio: mean across tickers each day
./app/lib/strategy.py:150:    portfolio = normed.mean(axis=1, skipna=True)
./app/lib/strategy.py:181:    return normed, portfolio, perf
./app/lib/charts.py:50:def cumulative_return_chart(
./app/lib/charts.py:56:    Each ticker shown as a translucent line, plus equal-weighted portfolio in bold.
./app/lib/charts.py:68:    portfolio = norm.mean(axis=1)
./app/lib/charts.py:78:        x=portfolio.index, y=portfolio.values,
./app/lib/charts.py:79:        mode="lines", name="Equal-weight portfolio",
./app/pages/4_🧬_Strategy_Picks.py:5:- For each: cumulative return chart (portfolio vs benchmark) + per-pick ranking table
./app/pages/4_🧬_Strategy_Picks.py:40:    "v4 / v5 biotech + HK 高股息 since-inception cumulative returns vs benchmark. "
./app/pages/4_🧬_Strategy_Picks.py:80:    normed, portfolio, perf = strat.compute_strategy_returns(picks_closes, pick_date)
./app/pages/4_🧬_Strategy_Picks.py:91:    if not portfolio.empty:
./app/pages/4_🧬_Strategy_Picks.py:92:        port_last = portfolio.iloc[-1] - 100
./app/pages/4_🧬_Strategy_Picks.py:97:            "📈 Portfolio since-inception",
./app/pages/4_🧬_Strategy_Picks.py:113:    # --- Cumulative return chart ---
./app/pages/4_🧬_Strategy_Picks.py:114:    if not portfolio.empty:
./app/pages/4_🧬_Strategy_Picks.py:115:        # Build a 2-column DataFrame: portfolio + benchmark
./app/pages/4_🧬_Strategy_Picks.py:116:        chart_df = pd.DataFrame({"Portfolio (equal-weight)": portfolio})
./app/pages/4_🧬_Strategy_Picks.py:121:        fig = charts.cumulative_return_chart(
./app/pages/4_🧬_Strategy_Picks.py:211:    "📊 **Methodology**: Equal-weight portfolio cumulative return from pick date. "

exec
/bin/zsh -lc 'du -h data/external/picks.db data/external/picks.db-wal data/external/picks.db-shm data/snapshots.db .git/objects/pack/* 2>/dev/null' in /Users/gcc/invest-dashboard
 exited 1 in 0ms:
zsh:1: no matches found: .git/objects/pack/*

exec
/bin/zsh -lc 'git ls-files data/external .gitignore && (test -f .gitignore && nl -ba .gitignore || true)' in /Users/gcc/invest-dashboard
 succeeded in 0ms:
.gitignore
data/external/hd_picks.csv
data/external/picks.db
data/external/picks.db-shm
data/external/picks.db-wal
data/external/v4_picks.csv
     1	# Python
     2	__pycache__/
     3	*.py[cod]
     4	*.egg-info/
     5	.venv/
     6	venv/
     7	.pytest_cache/
     8	
     9	# IDE
    10	.vscode/
    11	.idea/
    12	.DS_Store
    13	
    14	# Streamlit secrets (keep local, not commit)
    15	.streamlit/secrets.toml
    16	
    17	# logs / scratch
    18	*.log
    19	.scratch/
    20	tmp/
    21	
    22	# uv
    23	.uv-cache/
    24	
    25	# OMC plugin auto-state (do not commit)
    26	.omc/
    27	.claude/

exec
/bin/zsh -lc "sqlite3 data/snapshots.db \"select count(*) from universe_member; select count(distinct ticker) from universe_member; select sector, count(distinct ticker) from universe_member where domain='healthcare' and sector"'!='"'_coverage' group by sector order by sector; select count(*) from multiples_daily where date=(select max(date) from multiples_daily);\"" in /Users/gcc/invest-dashboard
 succeeded in 0ms:
120
106
biotech|16
cxo|14
hc_ai|13
hospital_care|10
managed_care|10
medtech|13
pharma|16
106

exec
/bin/zsh -lc "sqlite3 data/external/picks.db '.tables' && sqlite3 data/external/picks.db \"select count(*), min(date_added), max(date_added) from picks_v2 where source_skill='catalyst-monitor';\" && sqlite3 data/external/picks.db \"select count(distinct ticker) from picks_v2 where source_skill='catalyst-monitor';\"" in /Users/gcc/invest-dashboard
 succeeded in 0ms:
calibration_alerts        schema_meta             
picks_v2                  universe_snapshots_index
60|2026-05-15|2026-05-15
40

exec
/bin/zsh -lc "rg -n \"mean\\(|ffill|dropna|portfolio|equal|cum|return\" /Users/gcc/strategy-weekly/weekly_perf.py /Users/gcc/strategy-weekly -S 2>/dev/null" in /Users/gcc/invest-dashboard
 succeeded in 0ms:
/Users/gcc/strategy-weekly/weekly_perf.py:5:Pulls 5 return windows (1D / 5D / 15D / 30D / Since-Inception) for each strategy
/Users/gcc/strategy-weekly/weekly_perf.py:35:V4_XLSX = HOME / "Documents/LLM Wiki/RAW/us-biotech-screening-v4/03_scoring_v4.xlsx"
/Users/gcc/strategy-weekly/weekly_perf.py:53:    return df
/Users/gcc/strategy-weekly/weekly_perf.py:63:    return df[["ticker","name","score","pick_date","yf_sym"]]
/Users/gcc/strategy-weekly/weekly_perf.py:69:    def hk_yf(t): code, suf = t.split("."); return f"{int(code):04d}.{suf}"
/Users/gcc/strategy-weekly/weekly_perf.py:72:    return df
/Users/gcc/strategy-weekly/weekly_perf.py:76:    """Return dict: symbol -> close series (date-indexed, dropna)."""
/Users/gcc/strategy-weekly/weekly_perf.py:88:            out[s] = d["Close"].dropna() if "Close" in d.columns else None
/Users/gcc/strategy-weekly/weekly_perf.py:95:                    out[s] = d[(s, "Close")].dropna()
/Users/gcc/strategy-weekly/weekly_perf.py:97:                    out[s] = d[s]["Close"].dropna()
/Users/gcc/strategy-weekly/weekly_perf.py:102:    return out
/Users/gcc/strategy-weekly/weekly_perf.py:104:def window_return(series: pd.Series, days_back: int) -> float | None:
/Users/gcc/strategy-weekly/weekly_perf.py:105:    """Trailing N trading-day return — uses last close vs close N bars earlier.
/Users/gcc/strategy-weekly/weekly_perf.py:108:        return None
/Users/gcc/strategy-weekly/weekly_perf.py:112:    return float((last/prev - 1) * 100)
/Users/gcc/strategy-weekly/weekly_perf.py:114:def inception_return(series: pd.Series, pick_date: str) -> float | None:
/Users/gcc/strategy-weekly/weekly_perf.py:115:    if series is None or series.empty: return None
/Users/gcc/strategy-weekly/weekly_perf.py:118:    if after.empty: return None
/Users/gcc/strategy-weekly/weekly_perf.py:119:    return float((series.iloc[-1] / after.iloc[0] - 1) * 100)
/Users/gcc/strategy-weekly/weekly_perf.py:135:                row[f"{w}_%"] = window_return(ser, n)
/Users/gcc/strategy-weekly/weekly_perf.py:136:            row["since_%"] = inception_return(ser, pick_date)
/Users/gcc/strategy-weekly/weekly_perf.py:138:    return pd.DataFrame(rows)
/Users/gcc/strategy-weekly/weekly_perf.py:140:def benchmark_returns(bench_sym: str, pick_date: str) -> dict[str, float|None]:
/Users/gcc/strategy-weekly/weekly_perf.py:145:    for w,n in WINDOWS: res[w] = window_return(ser, n)
/Users/gcc/strategy-weekly/weekly_perf.py:146:    res["since"] = inception_return(ser, pick_date)
/Users/gcc/strategy-weekly/weekly_perf.py:147:    return res
/Users/gcc/strategy-weekly/weekly_perf.py:243:    # Footer: portfolio means + benchmark
/Users/gcc/strategy-weekly/weekly_perf.py:245:    H(ws.cell(row=foot,column=1,value="📊 Portfolio")); ws.merge_cells(start_row=foot,start_column=1,end_row=foot,end_column=2)
/Users/gcc/strategy-weekly/weekly_perf.py:255:        v = df[col].dropna().mean()
/Users/gcc/strategy-weekly/weekly_perf.py:271:        p = df[col].dropna().mean()
/Users/gcc/strategy-weekly/weekly_perf.py:280:    if v is None or pd.isna(v): return "—"
/Users/gcc/strategy-weekly/weekly_perf.py:281:    return f"{v:+.2f}%"
/Users/gcc/strategy-weekly/weekly_perf.py:284:    """Return inline CSS for a return cell, color-coded."""
/Users/gcc/strategy-weekly/weekly_perf.py:286:        return "color:#9ca3af;background:#f9fafb;"
/Users/gcc/strategy-weekly/weekly_perf.py:287:    if v >= 5:    return "color:#065f46;background:#a7f3d0;font-weight:700;"
/Users/gcc/strategy-weekly/weekly_perf.py:288:    if v >= 2:    return "color:#065f46;background:#d1fae5;font-weight:600;"
/Users/gcc/strategy-weekly/weekly_perf.py:289:    if v >= 0:    return "color:#065f46;background:#ecfdf5;"
/Users/gcc/strategy-weekly/weekly_perf.py:290:    if v >= -2:   return "color:#7f1d1d;background:#fef2f2;"
/Users/gcc/strategy-weekly/weekly_perf.py:291:    if v >= -5:   return "color:#7f1d1d;background:#fee2e2;font-weight:600;"
/Users/gcc/strategy-weekly/weekly_perf.py:292:    return "color:#7f1d1d;background:#fecaca;font-weight:700;"
/Users/gcc/strategy-weekly/weekly_perf.py:295:    if alpha is None or pd.isna(alpha): return ("—", "color:#9ca3af;background:#f3f4f6;")
/Users/gcc/strategy-weekly/weekly_perf.py:296:    if alpha >= 5:  return (f"+{alpha:.2f}pp", "color:#fff;background:#15803d;font-weight:700;")
/Users/gcc/strategy-weekly/weekly_perf.py:297:    if alpha >= 2:  return (f"+{alpha:.2f}pp", "color:#fff;background:#22c55e;font-weight:600;")
/Users/gcc/strategy-weekly/weekly_perf.py:298:    if alpha >= 0:  return (f"+{alpha:.2f}pp", "color:#065f46;background:#bbf7d0;")
/Users/gcc/strategy-weekly/weekly_perf.py:299:    if alpha >= -2: return (f"{alpha:.2f}pp",   "color:#7c2d12;background:#fed7aa;")
/Users/gcc/strategy-weekly/weekly_perf.py:300:    return (f"{alpha:.2f}pp", "color:#fff;background:#dc2626;font-weight:700;")
/Users/gcc/strategy-weekly/weekly_perf.py:320:    head += '<div style="padding:24px 32px;"><h2 style="margin:0 0 12px 0;font-size:18px;color:#1f2937;">📊 Portfolio summary (mean returns)</h2>'
/Users/gcc/strategy-weekly/weekly_perf.py:405:  <div style="color:#9ca3af;margin-top:10px;font-size:10px;">"—" 表示该 window 持有天数不足；returns are unadjusted close-to-close, excluding dividends and transaction costs.</div>
/Users/gcc/strategy-weekly/weekly_perf.py:409:    return head
/Users/gcc/strategy-weekly/weekly_perf.py:421:    return cfg
/Users/gcc/strategy-weekly/weekly_perf.py:430:        return False
/Users/gcc/strategy-weekly/weekly_perf.py:454:            return True
/Users/gcc/strategy-weekly/weekly_perf.py:460:    return False
/Users/gcc/strategy-weekly/weekly_perf.py:474:    xbi_v4 = benchmark_returns("XBI", "2026-04-22")
/Users/gcc/strategy-weekly/weekly_perf.py:475:    xbi_v5 = benchmark_returns("XBI", "2026-05-15")
/Users/gcc/strategy-weekly/weekly_perf.py:476:    bm_3110 = benchmark_returns("3110.HK", "2026-03-20")
/Users/gcc/strategy-weekly/weekly_perf.py:478:    def mean_(s, col): return float(s[col].dropna().mean()) if s[col].notna().any() else None
/Users/gcc/strategy-weekly/weekly_perf.py:488:        return {"label":label, "pick_date":pick_date, "n":n, "bench_name":bench_name, "rows":rs}
/Users/gcc/strategy-weekly/weekly_perf.py:516:            def f(v): return f"{v:+.2f}%" if v is not None else "—"
/Users/gcc/strategy-weekly/weekly_perf.py:542:            def f(v): return f"{v:+6.2f}%" if v is not None else "    —"
/Users/gcc/strategy-weekly/weekly_perf.py:545:    return 0
/Users/gcc/strategy-weekly/runs/weekly_2026-05-26.html:12:<div style="padding:24px 32px;"><h2 style="margin:0 0 12px 0;font-size:18px;color:#1f2937;">📊 Portfolio summary (mean returns)</h2><table style="width:100%;border-collapse:collapse;font-size:13px;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;"><thead><tr style="background:#1f4e79;color:#fff;"><th style="padding:10px 8px;text-align:center;font-weight:600;font-size:12px;border-right:1px solid rgba(255,255,255,0.15);">策略</th><th style="padding:10px 8px;text-align:center;font-weight:600;font-size:12px;border-right:1px solid rgba(255,255,255,0.15);">Pick</th><th style="padding:10px 8px;text-align:center;font-weight:600;font-size:12px;border-right:1px solid rgba(255,255,255,0.15);">N</th><th style="padding:10px 8px;text-align:center;font-weight:600;font-size:12px;border-right:1px solid rgba(255,255,255,0.15);">1D</th><th style="padding:10px 8px;text-align:center;font-weight:600;font-size:12px;border-right:1px solid rgba(255,255,255,0.15);">5D</th><th style="padding:10px 8px;text-align:center;font-weight:600;font-size:12px;border-right:1px solid rgba(255,255,255,0.15);">15D</th><th style="padding:10px 8px;text-align:center;font-weight:600;font-size:12px;border-right:1px solid rgba(255,255,255,0.15);">30D</th><th style="padding:10px 8px;text-align:center;font-weight:600;font-size:12px;border-right:1px solid rgba(255,255,255,0.15);">Since</th><th style="padding:10px 8px;text-align:center;font-weight:600;font-size:12px;border-right:1px solid rgba(255,255,255,0.15);">Benchmark</th><th style="padding:10px 8px;text-align:center;font-weight:600;font-size:12px;border-right:1px solid rgba(255,255,255,0.15);">Since Alpha</th></tr></thead><tbody><tr style="background:#ffffff;border-bottom:1px solid #e5e7eb;"><td style="padding:10px 8px;font-weight:600;border-right:1px solid #e5e7eb;">v4 biotech</td><td style="padding:10px 8px;text-align:center;color:#6b7280;font-size:12px;border-right:1px solid #e5e7eb;">2026-04-22</td><td style="padding:10px 8px;text-align:center;border-right:1px solid #e5e7eb;">27</td><td style="padding:10px 8px;text-align:right;border-right:1px solid #e5e7eb;color:#7f1d1d;background:#fef2f2;">-0.79%</td><td style="padding:10px 8px;text-align:right;border-right:1px solid #e5e7eb;color:#065f46;background:#ecfdf5;">+1.13%</td><td style="padding:10px 8px;text-align:right;border-right:1px solid #e5e7eb;color:#065f46;background:#d1fae5;font-weight:600;">+3.31%</td><td style="padding:10px 8px;text-align:right;border-right:1px solid #e5e7eb;color:#9ca3af;background:#f9fafb;">—</td><td style="padding:10px 8px;text-align:right;border-right:1px solid #e5e7eb;color:#065f46;background:#ecfdf5;">+0.50%</td><td style="padding:10px 8px;text-align:center;font-size:12px;color:#1e40af;font-weight:600;border-right:1px solid #e5e7eb;">XBI</td><td style="padding:10px 8px;text-align:center;color:#fff;background:#22c55e;font-weight:600;border-radius:4px;">+4.61pp</td></tr><tr style="background:#fafbfc;border-bottom:1px solid #e5e7eb;"><td style="padding:10px 8px;font-weight:600;border-right:1px solid #e5e7eb;">v5 biotech</td><td style="padding:10px 8px;text-align:center;color:#6b7280;font-size:12px;border-right:1px solid #e5e7eb;">2026-05-15</td><td style="padding:10px 8px;text-align:center;border-right:1px solid #e5e7eb;">40</td><td style="padding:10px 8px;text-align:right;border-right:1px solid #e5e7eb;color:#7f1d1d;background:#fef2f2;">-1.08%</td><td style="padding:10px 8px;text-align:right;border-right:1px solid #e5e7eb;color:#065f46;background:#ecfdf5;">+0.03%</td><td style="padding:10px 8px;text-align:right;border-right:1px solid #e5e7eb;color:#9ca3af;background:#f9fafb;">—</td><td style="padding:10px 8px;text-align:right;border-right:1px solid #e5e7eb;color:#9ca3af;background:#f9fafb;">—</td><td style="padding:10px 8px;text-align:right;border-right:1px solid #e5e7eb;color:#065f46;background:#ecfdf5;">+0.03%</td><td style="padding:10px 8px;text-align:center;font-size:12px;color:#1e40af;font-weight:600;border-right:1px solid #e5e7eb;">XBI</td><td style="padding:10px 8px;text-align:center;color:#7c2d12;background:#fed7aa;border-radius:4px;">-0.71pp</td></tr><tr style="background:#ffffff;border-bottom:1px solid #e5e7eb;"><td style="padding:10px 8px;font-weight:600;border-right:1px solid #e5e7eb;">HK 高股息</td><td style="padding:10px 8px;text-align:center;color:#6b7280;font-size:12px;border-right:1px solid #e5e7eb;">2026-03-20</td><td style="padding:10px 8px;text-align:center;border-right:1px solid #e5e7eb;">34</td><td style="padding:10px 8px;text-align:right;border-right:1px solid #e5e7eb;color:#7f1d1d;background:#fef2f2;">-0.08%</td><td style="padding:10px 8px;text-align:right;border-right:1px solid #e5e7eb;color:#7f1d1d;background:#fef2f2;">-1.57%</td><td style="padding:10px 8px;text-align:right;border-right:1px solid #e5e7eb;color:#7f1d1d;background:#fee2e2;font-weight:600;">-2.30%</td><td style="padding:10px 8px;text-align:right;border-right:1px solid #e5e7eb;color:#7f1d1d;background:#fee2e2;font-weight:600;">-2.82%</td><td style="padding:10px 8px;text-align:right;border-right:1px solid #e5e7eb;color:#7f1d1d;background:#fef2f2;">-1.30%</td><td style="padding:10px 8px;text-align:center;font-size:12px;color:#1e40af;font-weight:600;border-right:1px solid #e5e7eb;">3110.HK</td><td style="padding:10px 8px;text-align:center;color:#065f46;background:#bbf7d0;border-radius:4px;">+0.82pp</td></tr></tbody></table></div><div style="padding:0 32px 24px 32px;"><h2 style="margin:0 0 12px 0;font-size:18px;color:#1f2937;">🎯 Alpha vs benchmark (by window)</h2><table style="width:100%;border-collapse:collapse;font-size:13px;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;"><thead><tr style="background:#1f4e79;color:#fff;"><th style="padding:10px 8px;text-align:center;font-weight:600;font-size:12px;border-right:1px solid rgba(255,255,255,0.15);">Strategy</th><th style="padding:10px 8px;text-align:center;font-weight:600;font-size:12px;border-right:1px solid rgba(255,255,255,0.15);">1D</th><th style="padding:10px 8px;text-align:center;font-weight:600;font-size:12px;border-right:1px solid rgba(255,255,255,0.15);">5D</th><th style="padding:10px 8px;text-align:center;font-weight:600;font-size:12px;border-right:1px solid rgba(255,255,255,0.15);">15D</th><th style="padding:10px 8px;text-align:center;font-weight:600;font-size:12px;border-right:1px solid rgba(255,255,255,0.15);">30D</th><th style="padding:10px 8px;text-align:center;font-weight:600;font-size:12px;border-right:1px solid rgba(255,255,255,0.15);">Since-Inception</th></tr></thead><tbody><tr style="background:#ffffff;border-bottom:1px solid #e5e7eb;"><td style="padding:10px 8px;font-weight:600;border-right:1px solid #e5e7eb;">v4 biotech <span style="color:#9ca3af;font-weight:400;font-size:11px;">vs XBI</span></td><td style="padding:10px 8px;text-align:center;color:#065f46;background:#bbf7d0;border-right:1px solid #e5e7eb;">+0.05pp</td><td style="padding:10px 8px;text-align:center;color:#065f46;background:#bbf7d0;border-right:1px solid #e5e7eb;">+0.39pp</td><td style="padding:10px 8px;text-align:center;color:#fff;background:#22c55e;font-weight:600;border-right:1px solid #e5e7eb;">+2.36pp</td><td style="padding:10px 8px;text-align:center;color:#9ca3af;background:#f3f4f6;border-right:1px solid #e5e7eb;">—</td><td style="padding:10px 8px;text-align:center;color:#fff;background:#22c55e;font-weight:600;border-right:1px solid #e5e7eb;">+4.61pp</td></tr><tr style="background:#fafbfc;border-bottom:1px solid #e5e7eb;"><td style="padding:10px 8px;font-weight:600;border-right:1px solid #e5e7eb;">v5 biotech <span style="color:#9ca3af;font-weight:400;font-size:11px;">vs XBI</span></td><td style="padding:10px 8px;text-align:center;color:#7c2d12;background:#fed7aa;border-right:1px solid #e5e7eb;">-0.24pp</td><td style="padding:10px 8px;text-align:center;color:#7c2d12;background:#fed7aa;border-right:1px solid #e5e7eb;">-0.71pp</td><td style="padding:10px 8px;text-align:center;color:#9ca3af;background:#f3f4f6;border-right:1px solid #e5e7eb;">—</td><td style="padding:10px 8px;text-align:center;color:#9ca3af;background:#f3f4f6;border-right:1px solid #e5e7eb;">—</td><td style="padding:10px 8px;text-align:center;color:#7c2d12;background:#fed7aa;border-right:1px solid #e5e7eb;">-0.71pp</td></tr><tr style="background:#ffffff;border-bottom:1px solid #e5e7eb;"><td style="padding:10px 8px;font-weight:600;border-right:1px solid #e5e7eb;">HK 高股息 <span style="color:#9ca3af;font-weight:400;font-size:11px;">vs 3110.HK</span></td><td style="padding:10px 8px;text-align:center;color:#7c2d12;background:#fed7aa;border-right:1px solid #e5e7eb;">-0.20pp</td><td style="padding:10px 8px;text-align:center;color:#7c2d12;background:#fed7aa;border-right:1px solid #e5e7eb;">-0.89pp</td><td style="padding:10px 8px;text-align:center;color:#7c2d12;background:#fed7aa;border-right:1px solid #e5e7eb;">-0.30pp</td><td style="padding:10px 8px;text-align:center;color:#7c2d12;background:#fed7aa;border-right:1px solid #e5e7eb;">-0.94pp</td><td style="padding:10px 8px;text-align:center;color:#065f46;background:#bbf7d0;border-right:1px solid #e5e7eb;">+0.82pp</td></tr></tbody></table></div><div style="padding:0 32px 24px 32px;"><h2 style="margin:0 0 12px 0;font-size:18px;color:#1f2937;">🧬 v4 biotech <span style="font-size:12px;color:#6b7280;font-weight:400;">pick 2026-04-22 · n=27 · since-inception ranking</span></h2><table style="width:100%;border-collapse:collapse;font-size:12px;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;"><thead><tr style="background:#1f4e79;color:#fff;"><th style="padding:8px;text-align:center;font-weight:600;font-size:11px;border-right:1px solid rgba(255,255,255,0.15);">#</th><th style="padding:8px;text-align:center;font-weight:600;font-size:11px;border-right:1px solid rgba(255,255,255,0.15);">Ticker</th><th style="padding:8px;text-align:center;font-weight:600;font-size:11px;border-right:1px solid rgba(255,255,255,0.15);">Name</th><th style="padding:8px;text-align:center;font-weight:600;font-size:11px;border-right:1px solid rgba(255,255,255,0.15);">1D</th><th style="padding:8px;text-align:center;font-weight:600;font-size:11px;border-right:1px solid rgba(255,255,255,0.15);">5D</th><th style="padding:8px;text-align:center;font-weight:600;font-size:11px;border-right:1px solid rgba(255,255,255,0.15);">15D</th><th style="padding:8px;text-align:center;font-weight:600;font-size:11px;border-right:1px solid rgba(255,255,255,0.15);">30D</th><th style="padding:8px;text-align:center;font-weight:600;font-size:11px;border-right:1px solid rgba(255,255,255,0.15);">Since</th></tr></thead><tbody><tr><td colspan="8" style="padding:6px 10px;background:#ecfdf5;color:#065f46;font-weight:600;font-size:11px;letter-spacing:0.5px;">▲ TOP 5 (since-inception 表现最好)</td></tr><tr style="background:#ffffff;border-bottom:1px solid #f3f4f6;"><td style="padding:6px 8px;text-align:center;color:#9ca3af;border-right:1px solid #e5e7eb;">1</td><td style="padding:6px 8px;text-align:center;font-weight:600;border-right:1px solid #e5e7eb;">CORT</td><td style="padding:6px 8px;font-size:11px;border-right:1px solid #e5e7eb;">Corcept Therapeutics</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#ecfdf5;border-right:1px solid #e5e7eb;font-size:11px;">+0.89%</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#a7f3d0;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">+6.83%</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#a7f3d0;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">+17.11%</td><td style="padding:6px 8px;text-align:right;color:#9ca3af;background:#f9fafb;border-right:1px solid #e5e7eb;font-size:11px;">—</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#a7f3d0;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">+29.31%</td></tr><tr style="background:#fafbfc;border-bottom:1px solid #f3f4f6;"><td style="padding:6px 8px;text-align:center;color:#9ca3af;border-right:1px solid #e5e7eb;">2</td><td style="padding:6px 8px;text-align:center;font-weight:600;border-right:1px solid #e5e7eb;">JAZZ</td><td style="padding:6px 8px;font-size:11px;border-right:1px solid #e5e7eb;">Jazz Pharmaceuticals</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#ecfdf5;border-right:1px solid #e5e7eb;font-size:11px;">+0.18%</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#d1fae5;font-weight:600;border-right:1px solid #e5e7eb;font-size:11px;">+4.83%</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#a7f3d0;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">+18.31%</td><td style="padding:6px 8px;text-align:right;color:#9ca3af;background:#f9fafb;border-right:1px solid #e5e7eb;font-size:11px;">—</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#a7f3d0;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">+18.49%</td></tr><tr style="background:#ffffff;border-bottom:1px solid #f3f4f6;"><td style="padding:6px 8px;text-align:center;color:#9ca3af;border-right:1px solid #e5e7eb;">3</td><td style="padding:6px 8px;text-align:center;font-weight:600;border-right:1px solid #e5e7eb;">CYTK</td><td style="padding:6px 8px;font-size:11px;border-right:1px solid #e5e7eb;">Cytokinetics</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fef2f2;border-right:1px solid #e5e7eb;font-size:11px;">-1.43%</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#ecfdf5;border-right:1px solid #e5e7eb;font-size:11px;">+1.44%</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#a7f3d0;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">+21.45%</td><td style="padding:6px 8px;text-align:right;color:#9ca3af;background:#f9fafb;border-right:1px solid #e5e7eb;font-size:11px;">—</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#a7f3d0;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">+16.14%</td></tr><tr style="background:#fafbfc;border-bottom:1px solid #f3f4f6;"><td style="padding:6px 8px;text-align:center;color:#9ca3af;border-right:1px solid #e5e7eb;">4</td><td style="padding:6px 8px;text-align:center;font-weight:600;border-right:1px solid #e5e7eb;">IMVT</td><td style="padding:6px 8px;font-size:11px;border-right:1px solid #e5e7eb;">Immunovant</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#ecfdf5;border-right:1px solid #e5e7eb;font-size:11px;">+0.06%</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#a7f3d0;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">+24.23%</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#a7f3d0;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">+25.92%</td><td style="padding:6px 8px;text-align:right;color:#9ca3af;background:#f9fafb;border-right:1px solid #e5e7eb;font-size:11px;">—</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#a7f3d0;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">+15.80%</td></tr><tr style="background:#ffffff;border-bottom:1px solid #f3f4f6;"><td style="padding:6px 8px;text-align:center;color:#9ca3af;border-right:1px solid #e5e7eb;">5</td><td style="padding:6px 8px;text-align:center;font-weight:600;border-right:1px solid #e5e7eb;">CELC</td><td style="padding:6px 8px;font-size:11px;border-right:1px solid #e5e7eb;">Celcuity</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fee2e2;font-weight:600;border-right:1px solid #e5e7eb;font-size:11px;">-3.02%</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#ecfdf5;border-right:1px solid #e5e7eb;font-size:11px;">+0.40%</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#a7f3d0;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">+10.01%</td><td style="padding:6px 8px;text-align:right;color:#9ca3af;background:#f9fafb;border-right:1px solid #e5e7eb;font-size:11px;">—</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#a7f3d0;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">+12.91%</td></tr><tr><td colspan="8" style="padding:6px 10px;background:#fef2f2;color:#7f1d1d;font-weight:600;font-size:11px;letter-spacing:0.5px;">▼ BOTTOM 5 (since-inception 表现最差)</td></tr><tr style="background:#ffffff;border-bottom:1px solid #f3f4f6;"><td style="padding:6px 8px;text-align:center;color:#9ca3af;border-right:1px solid #e5e7eb;">23</td><td style="padding:6px 8px;text-align:center;font-weight:600;border-right:1px solid #e5e7eb;">TNGX</td><td style="padding:6px 8px;font-size:11px;border-right:1px solid #e5e7eb;">Tango Therapeutics</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fecaca;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">-6.38%</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fef2f2;border-right:1px solid #e5e7eb;font-size:11px;">-1.56%</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fee2e2;font-weight:600;border-right:1px solid #e5e7eb;font-size:11px;">-3.53%</td><td style="padding:6px 8px;text-align:right;color:#9ca3af;background:#f9fafb;border-right:1px solid #e5e7eb;font-size:11px;">—</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fecaca;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">-24.87%</td></tr><tr style="background:#fafbfc;border-bottom:1px solid #f3f4f6;"><td style="padding:6px 8px;text-align:center;color:#9ca3af;border-right:1px solid #e5e7eb;">24</td><td style="padding:6px 8px;text-align:center;font-weight:600;border-right:1px solid #e5e7eb;">GPCR</td><td style="padding:6px 8px;font-size:11px;border-right:1px solid #e5e7eb;">Structure Therapeutics</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#ecfdf5;border-right:1px solid #e5e7eb;font-size:11px;">+1.03%</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#ecfdf5;border-right:1px solid #e5e7eb;font-size:11px;">+1.29%</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fecaca;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">-7.15%</td><td style="padding:6px 8px;text-align:right;color:#9ca3af;background:#f9fafb;border-right:1px solid #e5e7eb;font-size:11px;">—</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fecaca;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">-15.72%</td></tr><tr style="background:#ffffff;border-bottom:1px solid #f3f4f6;"><td style="padding:6px 8px;text-align:center;color:#9ca3af;border-right:1px solid #e5e7eb;">25</td><td style="padding:6px 8px;text-align:center;font-weight:600;border-right:1px solid #e5e7eb;">BNTX</td><td style="padding:6px 8px;font-size:11px;border-right:1px solid #e5e7eb;">BioNTech (ADR)</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#ecfdf5;border-right:1px solid #e5e7eb;font-size:11px;">+1.33%</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#d1fae5;font-weight:600;border-right:1px solid #e5e7eb;font-size:11px;">+2.89%</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fecaca;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">-5.54%</td><td style="padding:6px 8px;text-align:right;color:#9ca3af;background:#f9fafb;border-right:1px solid #e5e7eb;font-size:11px;">—</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fecaca;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">-15.16%</td></tr><tr style="background:#fafbfc;border-bottom:1px solid #f3f4f6;"><td style="padding:6px 8px;text-align:center;color:#9ca3af;border-right:1px solid #e5e7eb;">26</td><td style="padding:6px 8px;text-align:center;font-weight:600;border-right:1px solid #e5e7eb;">ALMS</td><td style="padding:6px 8px;font-size:11px;border-right:1px solid #e5e7eb;">Alumis</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fef2f2;border-right:1px solid #e5e7eb;font-size:11px;">-0.68%</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fee2e2;font-weight:600;border-right:1px solid #e5e7eb;font-size:11px;">-3.72%</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fecaca;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">-12.55%</td><td style="padding:6px 8px;text-align:right;color:#9ca3af;background:#f9fafb;border-right:1px solid #e5e7eb;font-size:11px;">—</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fecaca;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">-14.95%</td></tr><tr style="background:#ffffff;border-bottom:1px solid #f3f4f6;"><td style="padding:6px 8px;text-align:center;color:#9ca3af;border-right:1px solid #e5e7eb;">27</td><td style="padding:6px 8px;text-align:center;font-weight:600;border-right:1px solid #e5e7eb;">REGN</td><td style="padding:6px 8px;font-size:11px;border-right:1px solid #e5e7eb;">Regeneron Pharmaceuticals</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fef2f2;border-right:1px solid #e5e7eb;font-size:11px;">-0.58%</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fecaca;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">-8.50%</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fecaca;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">-8.92%</td><td style="padding:6px 8px;text-align:right;color:#9ca3af;background:#f9fafb;border-right:1px solid #e5e7eb;font-size:11px;">—</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fecaca;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">-14.43%</td></tr></tbody></table></div><div style="padding:0 32px 24px 32px;"><h2 style="margin:0 0 12px 0;font-size:18px;color:#1f2937;">🧬 v5 biotech <span style="font-size:12px;color:#6b7280;font-weight:400;">pick 2026-05-15 · n=40 · since-inception ranking</span></h2><table style="width:100%;border-collapse:collapse;font-size:12px;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;"><thead><tr style="background:#1f4e79;color:#fff;"><th style="padding:8px;text-align:center;font-weight:600;font-size:11px;border-right:1px solid rgba(255,255,255,0.15);">#</th><th style="padding:8px;text-align:center;font-weight:600;font-size:11px;border-right:1px solid rgba(255,255,255,0.15);">Ticker</th><th style="padding:8px;text-align:center;font-weight:600;font-size:11px;border-right:1px solid rgba(255,255,255,0.15);">Name</th><th style="padding:8px;text-align:center;font-weight:600;font-size:11px;border-right:1px solid rgba(255,255,255,0.15);">1D</th><th style="padding:8px;text-align:center;font-weight:600;font-size:11px;border-right:1px solid rgba(255,255,255,0.15);">5D</th><th style="padding:8px;text-align:center;font-weight:600;font-size:11px;border-right:1px solid rgba(255,255,255,0.15);">15D</th><th style="padding:8px;text-align:center;font-weight:600;font-size:11px;border-right:1px solid rgba(255,255,255,0.15);">30D</th><th style="padding:8px;text-align:center;font-weight:600;font-size:11px;border-right:1px solid rgba(255,255,255,0.15);">Since</th></tr></thead><tbody><tr><td colspan="8" style="padding:6px 10px;background:#ecfdf5;color:#065f46;font-weight:600;font-size:11px;letter-spacing:0.5px;">▲ TOP 5 (since-inception 表现最好)</td></tr><tr style="background:#ffffff;border-bottom:1px solid #f3f4f6;"><td style="padding:6px 8px;text-align:center;color:#9ca3af;border-right:1px solid #e5e7eb;">1</td><td style="padding:6px 8px;text-align:center;font-weight:600;border-right:1px solid #e5e7eb;">CORT</td><td style="padding:6px 8px;font-size:11px;border-right:1px solid #e5e7eb;">CORT</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#ecfdf5;border-right:1px solid #e5e7eb;font-size:11px;">+0.89%</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#a7f3d0;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">+6.83%</td><td style="padding:6px 8px;text-align:right;color:#9ca3af;background:#f9fafb;border-right:1px solid #e5e7eb;font-size:11px;">—</td><td style="padding:6px 8px;text-align:right;color:#9ca3af;background:#f9fafb;border-right:1px solid #e5e7eb;font-size:11px;">—</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#a7f3d0;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">+6.83%</td></tr><tr style="background:#fafbfc;border-bottom:1px solid #f3f4f6;"><td style="padding:6px 8px;text-align:center;color:#9ca3af;border-right:1px solid #e5e7eb;">2</td><td style="padding:6px 8px;text-align:center;font-weight:600;border-right:1px solid #e5e7eb;">ONC</td><td style="padding:6px 8px;font-size:11px;border-right:1px solid #e5e7eb;">ONC</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#ecfdf5;border-right:1px solid #e5e7eb;font-size:11px;">+0.20%</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#a7f3d0;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">+5.79%</td><td style="padding:6px 8px;text-align:right;color:#9ca3af;background:#f9fafb;border-right:1px solid #e5e7eb;font-size:11px;">—</td><td style="padding:6px 8px;text-align:right;color:#9ca3af;background:#f9fafb;border-right:1px solid #e5e7eb;font-size:11px;">—</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#a7f3d0;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">+5.79%</td></tr><tr style="background:#ffffff;border-bottom:1px solid #f3f4f6;"><td style="padding:6px 8px;text-align:center;color:#9ca3af;border-right:1px solid #e5e7eb;">3</td><td style="padding:6px 8px;text-align:center;font-weight:600;border-right:1px solid #e5e7eb;">JAZZ</td><td style="padding:6px 8px;font-size:11px;border-right:1px solid #e5e7eb;">JAZZ</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#ecfdf5;border-right:1px solid #e5e7eb;font-size:11px;">+0.18%</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#d1fae5;font-weight:600;border-right:1px solid #e5e7eb;font-size:11px;">+4.83%</td><td style="padding:6px 8px;text-align:right;color:#9ca3af;background:#f9fafb;border-right:1px solid #e5e7eb;font-size:11px;">—</td><td style="padding:6px 8px;text-align:right;color:#9ca3af;background:#f9fafb;border-right:1px solid #e5e7eb;font-size:11px;">—</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#d1fae5;font-weight:600;border-right:1px solid #e5e7eb;font-size:11px;">+4.83%</td></tr><tr style="background:#fafbfc;border-bottom:1px solid #f3f4f6;"><td style="padding:6px 8px;text-align:center;color:#9ca3af;border-right:1px solid #e5e7eb;">4</td><td style="padding:6px 8px;text-align:center;font-weight:600;border-right:1px solid #e5e7eb;">BMRN</td><td style="padding:6px 8px;font-size:11px;border-right:1px solid #e5e7eb;">BMRN</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fef2f2;border-right:1px solid #e5e7eb;font-size:11px;">-0.02%</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#d1fae5;font-weight:600;border-right:1px solid #e5e7eb;font-size:11px;">+4.40%</td><td style="padding:6px 8px;text-align:right;color:#9ca3af;background:#f9fafb;border-right:1px solid #e5e7eb;font-size:11px;">—</td><td style="padding:6px 8px;text-align:right;color:#9ca3af;background:#f9fafb;border-right:1px solid #e5e7eb;font-size:11px;">—</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#d1fae5;font-weight:600;border-right:1px solid #e5e7eb;font-size:11px;">+4.40%</td></tr><tr style="background:#ffffff;border-bottom:1px solid #f3f4f6;"><td style="padding:6px 8px;text-align:center;color:#9ca3af;border-right:1px solid #e5e7eb;">5</td><td style="padding:6px 8px;text-align:center;font-weight:600;border-right:1px solid #e5e7eb;">TVTX</td><td style="padding:6px 8px;font-size:11px;border-right:1px solid #e5e7eb;">TVTX</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fef2f2;border-right:1px solid #e5e7eb;font-size:11px;">-0.69%</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#d1fae5;font-weight:600;border-right:1px solid #e5e7eb;font-size:11px;">+4.32%</td><td style="padding:6px 8px;text-align:right;color:#9ca3af;background:#f9fafb;border-right:1px solid #e5e7eb;font-size:11px;">—</td><td style="padding:6px 8px;text-align:right;color:#9ca3af;background:#f9fafb;border-right:1px solid #e5e7eb;font-size:11px;">—</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#d1fae5;font-weight:600;border-right:1px solid #e5e7eb;font-size:11px;">+4.32%</td></tr><tr><td colspan="8" style="padding:6px 10px;background:#fef2f2;color:#7f1d1d;font-weight:600;font-size:11px;letter-spacing:0.5px;">▼ BOTTOM 5 (since-inception 表现最差)</td></tr><tr style="background:#ffffff;border-bottom:1px solid #f3f4f6;"><td style="padding:6px 8px;text-align:center;color:#9ca3af;border-right:1px solid #e5e7eb;">36</td><td style="padding:6px 8px;text-align:center;font-weight:600;border-right:1px solid #e5e7eb;">FOLD</td><td style="padding:6px 8px;font-size:11px;border-right:1px solid #e5e7eb;">FOLD</td><td style="padding:6px 8px;text-align:right;color:#9ca3af;background:#f9fafb;border-right:1px solid #e5e7eb;font-size:11px;">—</td><td style="padding:6px 8px;text-align:right;color:#9ca3af;background:#f9fafb;border-right:1px solid #e5e7eb;font-size:11px;">—</td><td style="padding:6px 8px;text-align:right;color:#9ca3af;background:#f9fafb;border-right:1px solid #e5e7eb;font-size:11px;">—</td><td style="padding:6px 8px;text-align:right;color:#9ca3af;background:#f9fafb;border-right:1px solid #e5e7eb;font-size:11px;">—</td><td style="padding:6px 8px;text-align:right;color:#9ca3af;background:#f9fafb;border-right:1px solid #e5e7eb;font-size:11px;">—</td></tr><tr style="background:#fafbfc;border-bottom:1px solid #f3f4f6;"><td style="padding:6px 8px;text-align:center;color:#9ca3af;border-right:1px solid #e5e7eb;">37</td><td style="padding:6px 8px;text-align:center;font-weight:600;border-right:1px solid #e5e7eb;">TLX</td><td style="padding:6px 8px;font-size:11px;border-right:1px solid #e5e7eb;">TLX</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fecaca;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">-7.79%</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fecaca;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">-10.32%</td><td style="padding:6px 8px;text-align:right;color:#9ca3af;background:#f9fafb;border-right:1px solid #e5e7eb;font-size:11px;">—</td><td style="padding:6px 8px;text-align:right;color:#9ca3af;background:#f9fafb;border-right:1px solid #e5e7eb;font-size:11px;">—</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fecaca;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">-10.32%</td></tr><tr style="background:#ffffff;border-bottom:1px solid #f3f4f6;"><td style="padding:6px 8px;text-align:center;color:#9ca3af;border-right:1px solid #e5e7eb;">38</td><td style="padding:6px 8px;text-align:center;font-weight:600;border-right:1px solid #e5e7eb;">REGN</td><td style="padding:6px 8px;font-size:11px;border-right:1px solid #e5e7eb;">REGN</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fef2f2;border-right:1px solid #e5e7eb;font-size:11px;">-0.58%</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fecaca;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">-8.50%</td><td style="padding:6px 8px;text-align:right;color:#9ca3af;background:#f9fafb;border-right:1px solid #e5e7eb;font-size:11px;">—</td><td style="padding:6px 8px;text-align:right;color:#9ca3af;background:#f9fafb;border-right:1px solid #e5e7eb;font-size:11px;">—</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fecaca;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">-8.50%</td></tr><tr style="background:#fafbfc;border-bottom:1px solid #f3f4f6;"><td style="padding:6px 8px;text-align:center;color:#9ca3af;border-right:1px solid #e5e7eb;">39</td><td style="padding:6px 8px;text-align:center;font-weight:600;border-right:1px solid #e5e7eb;">RARE</td><td style="padding:6px 8px;font-size:11px;border-right:1px solid #e5e7eb;">RARE</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fef2f2;border-right:1px solid #e5e7eb;font-size:11px;">-1.35%</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fecaca;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">-6.44%</td><td style="padding:6px 8px;text-align:right;color:#9ca3af;background:#f9fafb;border-right:1px solid #e5e7eb;font-size:11px;">—</td><td style="padding:6px 8px;text-align:right;color:#9ca3af;background:#f9fafb;border-right:1px solid #e5e7eb;font-size:11px;">—</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fecaca;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">-6.44%</td></tr><tr style="background:#ffffff;border-bottom:1px solid #f3f4f6;"><td style="padding:6px 8px;text-align:center;color:#9ca3af;border-right:1px solid #e5e7eb;">40</td><td style="padding:6px 8px;text-align:center;font-weight:600;border-right:1px solid #e5e7eb;">MRNA</td><td style="padding:6px 8px;font-size:11px;border-right:1px solid #e5e7eb;">MRNA</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fef2f2;border-right:1px solid #e5e7eb;font-size:11px;">-0.80%</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fee2e2;font-weight:600;border-right:1px solid #e5e7eb;font-size:11px;">-4.40%</td><td style="padding:6px 8px;text-align:right;color:#9ca3af;background:#f9fafb;border-right:1px solid #e5e7eb;font-size:11px;">—</td><td style="padding:6px 8px;text-align:right;color:#9ca3af;background:#f9fafb;border-right:1px solid #e5e7eb;font-size:11px;">—</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fee2e2;font-weight:600;border-right:1px solid #e5e7eb;font-size:11px;">-4.40%</td></tr></tbody></table></div><div style="padding:0 32px 24px 32px;"><h2 style="margin:0 0 12px 0;font-size:18px;color:#1f2937;">💰 HK 高股息 <span style="font-size:12px;color:#6b7280;font-weight:400;">pick 2026-03-20 · n=34 · since-inception ranking</span></h2><table style="width:100%;border-collapse:collapse;font-size:12px;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;"><thead><tr style="background:#1f4e79;color:#fff;"><th style="padding:8px;text-align:center;font-weight:600;font-size:11px;border-right:1px solid rgba(255,255,255,0.15);">#</th><th style="padding:8px;text-align:center;font-weight:600;font-size:11px;border-right:1px solid rgba(255,255,255,0.15);">Ticker</th><th style="padding:8px;text-align:center;font-weight:600;font-size:11px;border-right:1px solid rgba(255,255,255,0.15);">Name</th><th style="padding:8px;text-align:center;font-weight:600;font-size:11px;border-right:1px solid rgba(255,255,255,0.15);">1D</th><th style="padding:8px;text-align:center;font-weight:600;font-size:11px;border-right:1px solid rgba(255,255,255,0.15);">5D</th><th style="padding:8px;text-align:center;font-weight:600;font-size:11px;border-right:1px solid rgba(255,255,255,0.15);">15D</th><th style="padding:8px;text-align:center;font-weight:600;font-size:11px;border-right:1px solid rgba(255,255,255,0.15);">30D</th><th style="padding:8px;text-align:center;font-weight:600;font-size:11px;border-right:1px solid rgba(255,255,255,0.15);">Since</th></tr></thead><tbody><tr><td colspan="8" style="padding:6px 10px;background:#ecfdf5;color:#065f46;font-weight:600;font-size:11px;letter-spacing:0.5px;">▲ TOP 5 (since-inception 表现最好)</td></tr><tr style="background:#ffffff;border-bottom:1px solid #f3f4f6;"><td style="padding:6px 8px;text-align:center;color:#9ca3af;border-right:1px solid #e5e7eb;">1</td><td style="padding:6px 8px;text-align:center;font-weight:600;border-right:1px solid #e5e7eb;">1908.HK</td><td style="padding:6px 8px;font-size:11px;border-right:1px solid #e5e7eb;">建发国际集团</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#ecfdf5;border-right:1px solid #e5e7eb;font-size:11px;">+0.38%</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fee2e2;font-weight:600;border-right:1px solid #e5e7eb;font-size:11px;">-2.86%</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#a7f3d0;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">+6.41%</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#a7f3d0;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">+16.61%</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#a7f3d0;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">+22.05%</td></tr><tr style="background:#fafbfc;border-bottom:1px solid #f3f4f6;"><td style="padding:6px 8px;text-align:center;color:#9ca3af;border-right:1px solid #e5e7eb;">2</td><td style="padding:6px 8px;text-align:center;font-weight:600;border-right:1px solid #e5e7eb;">2388.HK</td><td style="padding:6px 8px;font-size:11px;border-right:1px solid #e5e7eb;">中银香港</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#ecfdf5;border-right:1px solid #e5e7eb;font-size:11px;">+0.87%</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#a7f3d0;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">+5.33%</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#a7f3d0;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">+7.81%</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#a7f3d0;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">+9.37%</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#a7f3d0;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">+17.86%</td></tr><tr style="background:#ffffff;border-bottom:1px solid #f3f4f6;"><td style="padding:6px 8px;text-align:center;color:#9ca3af;border-right:1px solid #e5e7eb;">3</td><td style="padding:6px 8px;text-align:center;font-weight:600;border-right:1px solid #e5e7eb;">3988.HK</td><td style="padding:6px 8px;font-size:11px;border-right:1px solid #e5e7eb;">中国银行</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fef2f2;border-right:1px solid #e5e7eb;font-size:11px;">-0.19%</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#ecfdf5;border-right:1px solid #e5e7eb;font-size:11px;">+0.19%</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#d1fae5;font-weight:600;border-right:1px solid #e5e7eb;font-size:11px;">+2.55%</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#d1fae5;font-weight:600;border-right:1px solid #e5e7eb;font-size:11px;">+3.57%</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#a7f3d0;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">+11.06%</td></tr><tr style="background:#fafbfc;border-bottom:1px solid #f3f4f6;"><td style="padding:6px 8px;text-align:center;color:#9ca3af;border-right:1px solid #e5e7eb;">4</td><td style="padding:6px 8px;text-align:center;font-weight:600;border-right:1px solid #e5e7eb;">0939.HK</td><td style="padding:6px 8px;font-size:11px;border-right:1px solid #e5e7eb;">建设银行</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fef2f2;border-right:1px solid #e5e7eb;font-size:11px;">-0.11%</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#ecfdf5;border-right:1px solid #e5e7eb;font-size:11px;">+0.00%</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fef2f2;border-right:1px solid #e5e7eb;font-size:11px;">-0.90%</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#d1fae5;font-weight:600;border-right:1px solid #e5e7eb;font-size:11px;">+3.67%</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#a7f3d0;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">+8.42%</td></tr><tr style="background:#ffffff;border-bottom:1px solid #f3f4f6;"><td style="padding:6px 8px;text-align:center;color:#9ca3af;border-right:1px solid #e5e7eb;">5</td><td style="padding:6px 8px;text-align:center;font-weight:600;border-right:1px solid #e5e7eb;">1288.HK</td><td style="padding:6px 8px;font-size:11px;border-right:1px solid #e5e7eb;">农业银行</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fee2e2;font-weight:600;border-right:1px solid #e5e7eb;font-size:11px;">-2.20%</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fee2e2;font-weight:600;border-right:1px solid #e5e7eb;font-size:11px;">-4.61%</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fee2e2;font-weight:600;border-right:1px solid #e5e7eb;font-size:11px;">-2.53%</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#ecfdf5;border-right:1px solid #e5e7eb;font-size:11px;">+0.00%</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#a7f3d0;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">+7.82%</td></tr><tr><td colspan="8" style="padding:6px 10px;background:#fef2f2;color:#7f1d1d;font-weight:600;font-size:11px;letter-spacing:0.5px;">▼ BOTTOM 5 (since-inception 表现最差)</td></tr><tr style="background:#ffffff;border-bottom:1px solid #f3f4f6;"><td style="padding:6px 8px;text-align:center;color:#9ca3af;border-right:1px solid #e5e7eb;">30</td><td style="padding:6px 8px;text-align:center;font-weight:600;border-right:1px solid #e5e7eb;">1066.HK</td><td style="padding:6px 8px;font-size:11px;border-right:1px solid #e5e7eb;">威高股份</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fef2f2;border-right:1px solid #e5e7eb;font-size:11px;">-0.57%</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#ecfdf5;border-right:1px solid #e5e7eb;font-size:11px;">+0.29%</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fef2f2;border-right:1px solid #e5e7eb;font-size:11px;">-0.57%</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fecaca;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">-6.99%</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fecaca;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">-24.12%</td></tr><tr style="background:#fafbfc;border-bottom:1px solid #f3f4f6;"><td style="padding:6px 8px;text-align:center;color:#9ca3af;border-right:1px solid #e5e7eb;">31</td><td style="padding:6px 8px;text-align:center;font-weight:600;border-right:1px solid #e5e7eb;">6862.HK</td><td style="padding:6px 8px;font-size:11px;border-right:1px solid #e5e7eb;">海底捞</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fef2f2;border-right:1px solid #e5e7eb;font-size:11px;">-1.93%</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fecaca;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">-11.09%</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fecaca;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">-12.14%</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fecaca;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">-16.04%</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fecaca;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">-20.06%</td></tr><tr style="background:#ffffff;border-bottom:1px solid #f3f4f6;"><td style="padding:6px 8px;text-align:center;color:#9ca3af;border-right:1px solid #e5e7eb;">32</td><td style="padding:6px 8px;text-align:center;font-weight:600;border-right:1px solid #e5e7eb;">6690.HK</td><td style="padding:6px 8px;font-size:11px;border-right:1px solid #e5e7eb;">海尔智家</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fef2f2;border-right:1px solid #e5e7eb;font-size:11px;">-0.35%</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fee2e2;font-weight:600;border-right:1px solid #e5e7eb;font-size:11px;">-3.26%</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fecaca;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">-9.09%</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fee2e2;font-weight:600;border-right:1px solid #e5e7eb;font-size:11px;">-4.55%</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fecaca;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">-18.27%</td></tr><tr style="background:#fafbfc;border-bottom:1px solid #f3f4f6;"><td style="padding:6px 8px;text-align:center;color:#9ca3af;border-right:1px solid #e5e7eb;">33</td><td style="padding:6px 8px;text-align:center;font-weight:600;border-right:1px solid #e5e7eb;">3933.HK</td><td style="padding:6px 8px;font-size:11px;border-right:1px solid #e5e7eb;">联邦制药</td><td style="padding:6px 8px;text-align:right;color:#065f46;background:#ecfdf5;border-right:1px solid #e5e7eb;font-size:11px;">+0.89%</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fef2f2;border-right:1px solid #e5e7eb;font-size:11px;">-0.11%</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fee2e2;font-weight:600;border-right:1px solid #e5e7eb;font-size:11px;">-4.64%</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fecaca;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">-10.41%</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fecaca;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">-13.74%</td></tr><tr style="background:#ffffff;border-bottom:1px solid #f3f4f6;"><td style="padding:6px 8px;text-align:center;color:#9ca3af;border-right:1px solid #e5e7eb;">34</td><td style="padding:6px 8px;text-align:center;font-weight:600;border-right:1px solid #e5e7eb;">1044.HK</td><td style="padding:6px 8px;font-size:11px;border-right:1px solid #e5e7eb;">恒安国际</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fef2f2;border-right:1px solid #e5e7eb;font-size:11px;">-0.40%</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fee2e2;font-weight:600;border-right:1px solid #e5e7eb;font-size:11px;">-4.78%</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fecaca;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">-8.31%</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fecaca;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">-12.35%</td><td style="padding:6px 8px;text-align:right;color:#7f1d1d;background:#fecaca;font-weight:700;border-right:1px solid #e5e7eb;font-size:11px;">-9.79%</td></tr></tbody></table></div>
/Users/gcc/strategy-weekly/runs/weekly_2026-05-26.html:17:  <div style="color:#9ca3af;margin-top:10px;font-size:10px;">"—" 表示该 window 持有天数不足；returns are unadjusted close-to-close, excluding dividends and transaction costs.</div>
/Users/gcc/strategy-weekly/weekly_perf.py:5:Pulls 5 return windows (1D / 5D / 15D / 30D / Since-Inception) for each strategy
/Users/gcc/strategy-weekly/weekly_perf.py:35:V4_XLSX = HOME / "Documents/LLM Wiki/RAW/us-biotech-screening-v4/03_scoring_v4.xlsx"
/Users/gcc/strategy-weekly/weekly_perf.py:53:    return df
/Users/gcc/strategy-weekly/weekly_perf.py:63:    return df[["ticker","name","score","pick_date","yf_sym"]]
/Users/gcc/strategy-weekly/weekly_perf.py:69:    def hk_yf(t): code, suf = t.split("."); return f"{int(code):04d}.{suf}"
/Users/gcc/strategy-weekly/weekly_perf.py:72:    return df
/Users/gcc/strategy-weekly/weekly_perf.py:76:    """Return dict: symbol -> close series (date-indexed, dropna)."""
/Users/gcc/strategy-weekly/weekly_perf.py:88:            out[s] = d["Close"].dropna() if "Close" in d.columns else None
/Users/gcc/strategy-weekly/weekly_perf.py:95:                    out[s] = d[(s, "Close")].dropna()
/Users/gcc/strategy-weekly/weekly_perf.py:97:                    out[s] = d[s]["Close"].dropna()
/Users/gcc/strategy-weekly/weekly_perf.py:102:    return out
/Users/gcc/strategy-weekly/weekly_perf.py:104:def window_return(series: pd.Series, days_back: int) -> float | None:
/Users/gcc/strategy-weekly/weekly_perf.py:105:    """Trailing N trading-day return — uses last close vs close N bars earlier.
/Users/gcc/strategy-weekly/weekly_perf.py:108:        return None
/Users/gcc/strategy-weekly/weekly_perf.py:112:    return float((last/prev - 1) * 100)
/Users/gcc/strategy-weekly/weekly_perf.py:114:def inception_return(series: pd.Series, pick_date: str) -> float | None:
/Users/gcc/strategy-weekly/weekly_perf.py:115:    if series is None or series.empty: return None
/Users/gcc/strategy-weekly/weekly_perf.py:118:    if after.empty: return None
/Users/gcc/strategy-weekly/weekly_perf.py:119:    return float((series.iloc[-1] / after.iloc[0] - 1) * 100)
/Users/gcc/strategy-weekly/weekly_perf.py:135:                row[f"{w}_%"] = window_return(ser, n)
/Users/gcc/strategy-weekly/weekly_perf.py:136:            row["since_%"] = inception_return(ser, pick_date)
/Users/gcc/strategy-weekly/weekly_perf.py:138:    return pd.DataFrame(rows)
/Users/gcc/strategy-weekly/weekly_perf.py:140:def benchmark_returns(bench_sym: str, pick_date: str) -> dict[str, float|None]:
/Users/gcc/strategy-weekly/weekly_perf.py:145:    for w,n in WINDOWS: res[w] = window_return(ser, n)
/Users/gcc/strategy-weekly/weekly_perf.py:146:    res["since"] = inception_return(ser, pick_date)
/Users/gcc/strategy-weekly/weekly_perf.py:147:    return res
/Users/gcc/strategy-weekly/weekly_perf.py:243:    # Footer: portfolio means + benchmark
/Users/gcc/strategy-weekly/weekly_perf.py:245:    H(ws.cell(row=foot,column=1,value="📊 Portfolio")); ws.merge_cells(start_row=foot,start_column=1,end_row=foot,end_column=2)
/Users/gcc/strategy-weekly/weekly_perf.py:255:        v = df[col].dropna().mean()
/Users/gcc/strategy-weekly/weekly_perf.py:271:        p = df[col].dropna().mean()
/Users/gcc/strategy-weekly/weekly_perf.py:280:    if v is None or pd.isna(v): return "—"
/Users/gcc/strategy-weekly/weekly_perf.py:281:    return f"{v:+.2f}%"
/Users/gcc/strategy-weekly/weekly_perf.py:284:    """Return inline CSS for a return cell, color-coded."""
/Users/gcc/strategy-weekly/weekly_perf.py:286:        return "color:#9ca3af;background:#f9fafb;"
/Users/gcc/strategy-weekly/weekly_perf.py:287:    if v >= 5:    return "color:#065f46;background:#a7f3d0;font-weight:700;"
/Users/gcc/strategy-weekly/weekly_perf.py:288:    if v >= 2:    return "color:#065f46;background:#d1fae5;font-weight:600;"
/Users/gcc/strategy-weekly/weekly_perf.py:289:    if v >= 0:    return "color:#065f46;background:#ecfdf5;"
/Users/gcc/strategy-weekly/weekly_perf.py:290:    if v >= -2:   return "color:#7f1d1d;background:#fef2f2;"
/Users/gcc/strategy-weekly/weekly_perf.py:291:    if v >= -5:   return "color:#7f1d1d;background:#fee2e2;font-weight:600;"
/Users/gcc/strategy-weekly/weekly_perf.py:292:    return "color:#7f1d1d;background:#fecaca;font-weight:700;"
/Users/gcc/strategy-weekly/weekly_perf.py:295:    if alpha is None or pd.isna(alpha): return ("—", "color:#9ca3af;background:#f3f4f6;")
/Users/gcc/strategy-weekly/weekly_perf.py:296:    if alpha >= 5:  return (f"+{alpha:.2f}pp", "color:#fff;background:#15803d;font-weight:700;")
/Users/gcc/strategy-weekly/weekly_perf.py:297:    if alpha >= 2:  return (f"+{alpha:.2f}pp", "color:#fff;background:#22c55e;font-weight:600;")
/Users/gcc/strategy-weekly/weekly_perf.py:298:    if alpha >= 0:  return (f"+{alpha:.2f}pp", "color:#065f46;background:#bbf7d0;")
/Users/gcc/strategy-weekly/weekly_perf.py:299:    if alpha >= -2: return (f"{alpha:.2f}pp",   "color:#7c2d12;background:#fed7aa;")
/Users/gcc/strategy-weekly/weekly_perf.py:300:    return (f"{alpha:.2f}pp", "color:#fff;background:#dc2626;font-weight:700;")
/Users/gcc/strategy-weekly/weekly_perf.py:320:    head += '<div style="padding:24px 32px;"><h2 style="margin:0 0 12px 0;font-size:18px;color:#1f2937;">📊 Portfolio summary (mean returns)</h2>'
/Users/gcc/strategy-weekly/weekly_perf.py:405:  <div style="color:#9ca3af;margin-top:10px;font-size:10px;">"—" 表示该 window 持有天数不足；returns are unadjusted close-to-close, excluding dividends and transaction costs.</div>
/Users/gcc/strategy-weekly/weekly_perf.py:409:    return head
/Users/gcc/strategy-weekly/weekly_perf.py:421:    return cfg
/Users/gcc/strategy-weekly/weekly_perf.py:430:        return False
/Users/gcc/strategy-weekly/weekly_perf.py:454:            return True
/Users/gcc/strategy-weekly/weekly_perf.py:460:    return False
/Users/gcc/strategy-weekly/weekly_perf.py:474:    xbi_v4 = benchmark_returns("XBI", "2026-04-22")
/Users/gcc/strategy-weekly/weekly_perf.py:475:    xbi_v5 = benchmark_returns("XBI", "2026-05-15")
/Users/gcc/strategy-weekly/weekly_perf.py:476:    bm_3110 = benchmark_returns("3110.HK", "2026-03-20")
/Users/gcc/strategy-weekly/weekly_perf.py:478:    def mean_(s, col): return float(s[col].dropna().mean()) if s[col].notna().any() else None
/Users/gcc/strategy-weekly/weekly_perf.py:488:        return {"label":label, "pick_date":pick_date, "n":n, "bench_name":bench_name, "rows":rs}
/Users/gcc/strategy-weekly/weekly_perf.py:516:            def f(v): return f"{v:+.2f}%" if v is not None else "—"
/Users/gcc/strategy-weekly/weekly_perf.py:542:            def f(v): return f"{v:+6.2f}%" if v is not None else "    —"
/Users/gcc/strategy-weekly/weekly_perf.py:545:    return 0
/Users/gcc/strategy-weekly/docs/HANDOFF.md:55:- `~/Documents/LLM Wiki/RAW/us-biotech-screening-v4/03_scoring_v4.xlsx` — v4 picks 数据源
/Users/gcc/strategy-weekly/docs/HANDOFF.md:56:- `~/Documents/LLM Wiki/RAW/us-biotech-screening-2026-04/01_universe.xlsx` — 584-ticker universe（Final_Universe sheet）
/Users/gcc/strategy-weekly/docs/HANDOFF.md:66:- **window_return 用 trailing N trading bars，不用 today−N calendar days**：避免 yfinance 当日数据未 settle 时算出 1D=0% 的假象（第一版踩过坑，已修）。
/Users/gcc/strategy-weekly/docs/HANDOFF.md:76:- **biotech_universe.py f-string 嵌套引号 SyntaxError**：`f'{r["ret_%"]:+.1f}%'` 在 Python 3.12 下 escape 不生效；改成 helper `def fmt_row(r): return f"{r['ticker']} {r['ret_%']:+.1f}%"` 绕开。
/Users/gcc/strategy-weekly/scripts/biotech_universe.py:23:SRC = Path.home()/"Documents/LLM Wiki/RAW/us-biotech-screening-2026-04/01_universe.xlsx"
/Users/gcc/strategy-weekly/scripts/biotech_universe.py:33:tickers = uni['ticker'].dropna().astype(str).tolist()
/Users/gcc/strategy-weekly/scripts/biotech_universe.py:47:                sub = d[t][['Open','High','Low','Close','Volume']].dropna(how='all')
/Users/gcc/strategy-weekly/scripts/biotech_universe.py:49:                sub = d[t][['Open','High','Low','Close','Volume']].dropna(how='all')
/Users/gcc/strategy-weekly/scripts/biotech_universe.py:80:        avgv  = float(d['Volume'].mean())
/Users/gcc/strategy-weekly/scripts/biotech_universe.py:81:        avgp  = float(d['Close'].mean())
/Users/gcc/strategy-weekly/scripts/biotech_universe.py:130:    cols  = ['Rank','Ticker','Company','MCap mn$','Px 04-20','Px Now','Return %','High','Low','Avg Vol (sh)','Avg $Vol (mn)']
/Users/gcc/strategy-weekly/scripts/biotech_universe.py:167:write_sheet(wb.create_sheet("📊 Universe (sorted by return)"), perf,
/Users/gcc/strategy-weekly/scripts/biotech_universe.py:169:            f"N={len(perf)} tickers · source: CMSI Biotech Sheet (2026-04 vintage) · today {TODAY.isoformat()} · sort: return desc")
/Users/gcc/strategy-weekly/scripts/biotech_universe.py:173:bot30 = perf.dropna(subset=['ret_%']).tail(30).iloc[::-1].reset_index(drop=True); bot30['rank']=range(1,len(bot30)+1)
/Users/gcc/strategy-weekly/scripts/biotech_universe.py:175:            "Top 30 winners 自 2026-04-20", f"按 return % 排序前 30 名 · today {TODAY.isoformat()}")
/Users/gcc/strategy-weekly/scripts/biotech_universe.py:177:            "Bottom 30 losers 自 2026-04-20", f"按 return % 排序倒数 30 名（剔除无数据）· today {TODAY.isoformat()}")
/Users/gcc/strategy-weekly/scripts/biotech_universe.py:188:valid = perf['ret_%'].dropna()
/Users/gcc/strategy-weekly/scripts/biotech_universe.py:193:    ("Universe 均值",        valid.mean(), '+0.00"%"'),
/Users/gcc/strategy-weekly/scripts/biotech_universe.py:195:    ("胜率 (>0)",            (valid>0).mean()*100, '0.0"%"'),
/Users/gcc/strategy-weekly/scripts/biotech_universe.py:198:    ("Avg 日均成交额 (mn$)",  perf['avg_dollar_vol_mn'].dropna().mean(), '#,##0.0'),
/Users/gcc/strategy-weekly/scripts/biotech_universe.py:199:    ("Median 日均成交额 (mn$)", perf['avg_dollar_vol_mn'].dropna().median(), '#,##0.0'),
/Users/gcc/strategy-weekly/scripts/biotech_universe.py:216:c = cov.cell(row=foot,column=2,value="📈 Return % 分布 (10 个 bucket)")
/Users/gcc/strategy-weekly/scripts/biotech_universe.py:240:print(f"\nN={len(perf)}  valid={len(valid)}  mean={valid.mean():+.2f}%  median={valid.median():+.2f}%  hit_rate={(valid>0).mean()*100:.1f}%")
/Users/gcc/strategy-weekly/scripts/biotech_universe.py:242:    return f"{r['ticker']} {r['ret_%']:+.1f}%"
/Users/gcc/strategy-weekly/scripts/biotech_universe.py:244:print("Bot 5: " + ", ".join(fmt_row(r) for _,r in perf.dropna(subset=['ret_%']).tail(5).iterrows()))

exec
/bin/zsh -lc 'du -h data/external/picks.db data/external/picks.db-wal data/external/picks.db-shm data/snapshots.db 2>/dev/null; find .git/objects -type f -maxdepth 3 -print0 | xargs -0 du -ch 2>/dev/null | tail -n 5' in /Users/gcc/invest-dashboard
 succeeded in 0ms:
136K	data/external/picks.db
  0B	data/external/picks.db-wal
 32K	data/external/picks.db-shm
2.1M	data/snapshots.db
4.0K	.git/objects/8c/28f21891a82a1a088771ee7d6371a278005b35
4.0K	.git/objects/47/e1513ccb785c2464093c72e2ff94f11d32e0e9
4.0K	.git/objects/7f/71a9180e9f4abf2e987cd96fbbf1a8a2ac8896
4.0K	.git/objects/25/1c6de5ab7a234f5f836a94db30370d36e74525
1.2M	total

exec
/bin/zsh -lc "python - <<'PY'
import pandas as pd
from app.lib.strategy import compute_strategy_returns
idx=pd.to_datetime(['2026-01-01','2026-01-02','2026-01-03'])
closes=pd.DataFrame({'A':[100,90,80],'B':[100,None,100]}, index=idx)
print(compute_strategy_returns(closes,'2026-01-01')[1])
PY" in /Users/gcc/invest-dashboard
exec
/bin/zsh -lc "sqlite3 data/snapshots.db \"with latest as (select * from multiples_daily where date=(select max(date) from multiples_daily)), sector_members as (select sector, ticker from universe_member where domain='healthcare' and sector"'!='"'_coverage'), vals as (select sm.sector, sm.ticker, l.forward_pe from sector_members sm left join latest l on l.ticker=sm.ticker) select sector, count(*) as n_total, sum(case when forward_pe > 0 then 1 else 0 end) as n_pos, min(case when forward_pe > 0 then forward_pe end), max(case when forward_pe > 0 then forward_pe end) from vals group by sector order by sector;\"" in /Users/gcc/invest-dashboard
 exited 127 in 0ms:
zsh:1: command not found: python

 succeeded in 0ms:
biotech|16|13|8.133123|31.386364
cxo|14|14|10.501492|33.361122
hc_ai|13|11|11.673097|230.88046
hospital_care|10|10|6.0563784|20.644436
managed_care|10|10|6.0563784|19.784998
medtech|13|13|10.9810295|45.95172
pharma|16|16|9.238241|87.53649

codex
A key mismatch is emerging: `weekly_perf.py` reports portfolio summary as the mean of per-ticker returns, while the D4 page reports the last point of a daily mean equity curve. Those are equivalent only when every ticker has both the same anchor and same latest valid date.
exec
/bin/zsh -lc "sed -n '232,282p' /Users/gcc/strategy-weekly/weekly_perf.py && sed -n '468,484p' /Users/gcc/strategy-weekly/weekly_perf.py" in /Users/gcc/invest-dashboard
 succeeded in 0ms:
            elif src=="score": B(c,fmt='0.00',align="center")
            else: B(c,fmt='+0.00"%"',align="right",bold=(src=="since_%"))
            c.fill=PatternFill("solid",fgColor=bg)

    # color scale on each window col
    for col_letter in "DEFGH":
        ws.conditional_formatting.add(f"{col_letter}6:{col_letter}{5+len(df)}", ColorScaleRule(
            start_type='num',start_value=-20,start_color=RED_BG,
            mid_type='num',mid_value=0,mid_color="FFFFFF",
            end_type='num',end_value=20,end_color=GREEN_BG))

    # Footer: portfolio means + benchmark
    foot = 5 + len(df) + 2
    H(ws.cell(row=foot,column=1,value="📊 Portfolio")); ws.merge_cells(start_row=foot,start_column=1,end_row=foot,end_column=2)
    H(ws.cell(row=foot,column=3,value="Score"))
    for j,w in enumerate(["1D %","5D %","15D %","30D %","Since %"]):
        H(ws.cell(row=foot,column=4+j,value=w))

    # mean row
    rr=foot+1; ws.row_dimensions[rr].height=22
    c=ws.cell(row=rr,column=1,value="组合均值"); B(c,align="center",bold=True); ws.merge_cells(start_row=rr,start_column=1,end_row=rr,end_column=2)
    c=ws.cell(row=rr,column=3,value=None); B(c,align="center")
    for j,col in enumerate(["1D_%","5D_%","15D_%","30D_%","since_%"]):
        v = df[col].dropna().mean()
        c=ws.cell(row=rr,column=4+j,value=v if pd.notna(v) else None); B(c,fmt='+0.00"%"',align="right",bold=True)

    # benchmark row
    rr+=1; ws.row_dimensions[rr].height=22
    c=ws.cell(row=rr,column=1,value=f"{bench_sym} 基准"); B(c,align="center",bold=True,color=NAVY); ws.merge_cells(start_row=rr,start_column=1,end_row=rr,end_column=2)
    c=ws.cell(row=rr,column=3,value=None); B(c,align="center")
    for j,key in enumerate(["1D","5D","15D","30D","since"]):
        v = bench.get(key)
        c=ws.cell(row=rr,column=4+j,value=v if v is not None else None); B(c,fmt='+0.00"%"',align="right",bold=True,color=NAVY)

    # alpha row
    rr+=1; ws.row_dimensions[rr].height=22
    c=ws.cell(row=rr,column=1,value="Alpha (组合 − 基准)"); B(c,align="center",bold=True); ws.merge_cells(start_row=rr,start_column=1,end_row=rr,end_column=2)
    c=ws.cell(row=rr,column=3,value=None); B(c,align="center")
    for j,(col,key) in enumerate(zip(["1D_%","5D_%","15D_%","30D_%","since_%"],["1D","5D","15D","30D","since"])):
        p = df[col].dropna().mean()
        b = bench.get(key)
        alpha = (p - b) if (pd.notna(p) and b is not None) else None
        c=ws.cell(row=rr,column=4+j,value=alpha); B(c,fmt='+0.00"%"',align="right",bold=True)

    ws.sheet_view.zoomScale=110

# ============ HTML report ============
def fmt_pct(v):
    if v is None or pd.isna(v): return "—"
    return f"{v:+.2f}%"

    print("  fetching prices (batch yfinance)...", file=sys.stderr)
    v4_perf = strategy_table(v4_df, "2026-04-22")
    v5_perf = strategy_table(v5_df, "2026-05-15")
    hd_perf = strategy_table(hd_df, "2026-03-20")

    print("  fetching benchmarks...", file=sys.stderr)
    xbi_v4 = benchmark_returns("XBI", "2026-04-22")
    xbi_v5 = benchmark_returns("XBI", "2026-05-15")
    bm_3110 = benchmark_returns("3110.HK", "2026-03-20")

    def mean_(s, col): return float(s[col].dropna().mean()) if s[col].notna().any() else None
    def rows_for(df, bench, label, pick_date, n, bench_name):
        rs = []
        for win,_ in WINDOWS:
            port = mean_(df, f"{win}_%"); ben = bench.get(win)
            alpha = (port - ben) if (port is not None and ben is not None) else None
            rs.append((win, port, ben, alpha))

exec
/bin/zsh -lc "git show --stat --oneline 251c6de..HEAD && git show --name-only --oneline 9e1179e | sed -n '1,80p'" in /Users/gcc/invest-dashboard
 succeeded in 0ms:
9e1179e feat(D5): CMSI Coverage + Valuation Scanner pages
 "app/pages/3_\360\237\222\216_CMSI_Coverage.py"    | 175 +++++++++++++++
 .../pages/5_\360\237\222\260_Valuation_Scanner.py" | 242 +++++++++++++++++++++
 2 files changed, 417 insertions(+)
2863c72 feat(D4): Strategy Picks page — v4/v5 biotech + HK 高股息
 app/lib/strategy.py                              | 181 +++++++++++++++++++
 "app/pages/4_\360\237\247\254_Strategy_Picks.py" | 218 +++++++++++++++++++++++
 data/external/hd_picks.csv                       |  35 ++++
 data/external/picks.db                           | Bin 0 -> 139264 bytes
 data/external/picks.db-shm                       | Bin 0 -> 32768 bytes
 data/external/picks.db-wal                       |   0
 data/external/v4_picks.csv                       |  28 +++
 7 files changed, 462 insertions(+)
9e1179e feat(D5): CMSI Coverage + Valuation Scanner pages
"app/pages/3_\360\237\222\216_CMSI_Coverage.py"
"app/pages/5_\360\237\222\260_Valuation_Scanner.py"

exec
/bin/zsh -lc 'python3 -m compileall app jobs' in /Users/gcc/invest-dashboard
 succeeded in 0ms:
Listing 'app'...
Listing 'app/.streamlit'...
Listing 'app/lib'...
Compiling 'app/lib/charts.py'...
Compiling 'app/lib/db.py'...
Compiling 'app/lib/format.py'...
Compiling 'app/lib/strategy.py'...
Compiling 'app/lib/ui.py'...
Listing 'app/pages'...
Compiling 'app/pages/1_🏥_Healthcare.py'...
Compiling 'app/pages/2_🔥_Sector_Heatmap.py'...
Compiling 'app/pages/3_💎_CMSI_Coverage.py'...
Compiling 'app/pages/4_🧬_Strategy_Picks.py'...
Compiling 'app/pages/5_💰_Valuation_Scanner.py'...
Compiling 'app/streamlit_app.py'...
Listing 'jobs'...
Compiling 'jobs/fetch_eod.py'...
Compiling 'jobs/init_db.py'...

exec
/bin/zsh -lc "python3 - <<'PY'
import pandas as pd
idx=pd.to_datetime(['2026-01-01','2026-01-02','2026-01-03'])
closes=pd.DataFrame({'A':[100,90,80],'B':[100,None,100]}, index=idx)
sub=closes[closes.index >= pd.Timestamp('2026-01-01')]
normed=(sub/sub.iloc[0])*100
print('normed')
print(normed)
print('current portfolio')
print(normed.mean(axis=1, skipna=True))
print('ffill portfolio')
print(normed.ffill().mean(axis=1))
print('strict portfolio')
print(normed.mean(axis=1, skipna=False))
print('per-ticker mean since')
print(((closes.ffill().iloc[-1]/sub.iloc[0]-1)*100).mean())
PY" in /Users/gcc/invest-dashboard
 succeeded in 565ms:
normed
                A      B
2026-01-01  100.0  100.0
2026-01-02   90.0    NaN
2026-01-03   80.0  100.0
current portfolio
2026-01-01    100.0
2026-01-02     90.0
2026-01-03     90.0
dtype: float64
ffill portfolio
2026-01-01    100.0
2026-01-02     95.0
2026-01-03     90.0
dtype: float64
strict portfolio
2026-01-01    100.0
2026-01-02      NaN
2026-01-03     90.0
dtype: float64
per-ticker mean since
-9.999999999999998

exec
/bin/zsh -lc "sed -n '1,80p' requirements.txt; find app -maxdepth 2 -type f -print | sort" in /Users/gcc/invest-dashboard
exec
/bin/zsh -lc "nl -ba app/pages/1_🏥_Healthcare.py | sed -n '1,150p'; nl -ba app/pages/2_🔥_Sector_Heatmap.py | sed -n '1,130p'; nl -ba app/streamlit_app.py | sed -n '1,80p'" in /Users/gcc/invest-dashboard
 succeeded in 0ms:
streamlit>=1.36
yfinance>=0.2.43
pandas>=2.2
pyyaml>=6.0
plotly>=5.22
numpy>=1.26
app/.streamlit/config.toml
app/__pycache__/streamlit_app.cpython-314.pyc
app/lib/__init__.py
app/lib/benchmarks.py
app/lib/charts.py
app/lib/db.py
app/lib/format.py
app/lib/strategy.py
app/lib/ui.py
app/pages/1_🏥_Healthcare.py
app/pages/2_🔥_Sector_Heatmap.py
app/pages/3_💎_CMSI_Coverage.py
app/pages/4_🧬_Strategy_Picks.py
app/pages/5_💰_Valuation_Scanner.py
app/streamlit_app.py

 succeeded in 0ms:
     1	"""Healthcare domain overview — 7 sub-sectors summary."""
     2	
     3	from __future__ import annotations
     4	
     5	import pandas as pd
     6	import streamlit as st
     7	import yaml
     8	from pathlib import Path
     9	
    10	from lib import benchmarks as bm
    11	from lib import db
    12	from lib import format as fmt
    13	
    14	
    15	def _render_pct_table(df: pd.DataFrame, pct_cols: list[str], num_cols: list[str] | None = None) -> None:
    16	    """Pre-format strings + Styler color-only (M7 audit fix)."""
    17	    display_str = pd.DataFrame(index=df.index)
    18	    for c in df.columns:
    19	        if c in pct_cols:
    20	            display_str[c] = df[c].apply(fmt.fmt_pct)
    21	        elif num_cols and c in num_cols:
    22	            display_str[c] = df[c].apply(fmt.fmt_num)
    23	        else:
    24	            display_str[c] = df[c]
    25	    styler = display_str.style
    26	    for c in pct_cols:
    27	        styler = styler.apply(
    28	            lambda _s, n=df[c]: fmt.background_gradient_diverging(n),
    29	            subset=[c],
    30	        )
    31	    st.dataframe(styler, use_container_width=True)
    32	
    33	st.set_page_config(page_title="Healthcare · invest-dashboard", page_icon="🏥", layout="wide")
    34	
    35	REPO_ROOT = Path(__file__).resolve().parent.parent.parent
    36	DOMAIN_CFG = REPO_ROOT / "config" / "domains" / "healthcare.yml"
    37	
    38	
    39	@st.cache_data(ttl=600)
    40	def load_domain_cfg() -> dict:
    41	    with DOMAIN_CFG.open() as f:
    42	        return yaml.safe_load(f)
    43	
    44	
    45	cfg = load_domain_cfg()
    46	st.title(f"{cfg.get('emoji', '🏥')} {cfg['name']}")
    47	st.caption(cfg.get("description", "").strip())
    48	
    49	# --- 7 sector aggregate summary ---
    50	st.subheader("📊 Sector summary (mean returns per sector)")
    51	
    52	rows = []
    53	all_returns_by_sector: dict[str, pd.DataFrame] = {}
    54	for sec in cfg["sectors"]:
    55	    uni = db.sector_tickers("healthcare", sec["id"])
    56	    tickers = tuple(uni["ticker"].tolist())
    57	    if not tickers:
    58	        continue
    59	    closes = db.get_close_series_usd(tickers)   # M1 audit: USD-converted
    60	    rets = db.compute_returns(closes)
    61	    if rets.empty:
    62	        continue
    63	    all_returns_by_sector[sec["id"]] = rets
    64	    rows.append({
    65	        "Sector": sec["name"],
    66	        "Tickers": len(tickers),
    67	        "1D % avg": rets["1d_%"].mean(),
    68	        "5D % avg": rets["5d_%"].mean(),
    69	        "1M % avg": rets["1m_%"].mean(),
    70	        "YTD % avg": rets["ytd_%"].mean(),
    71	        "Benchmark": sec.get("benchmark", "—"),
    72	    })
    73	
    74	if not rows:
    75	    st.warning("No sector data — backfill needed.")
    76	else:
    77	    summary = pd.DataFrame(rows).set_index("Sector")
    78	    pct_cols = ["1D % avg", "5D % avg", "1M % avg", "YTD % avg"]
    79	    _render_pct_table(summary, pct_cols=pct_cols)
    80	
    81	st.divider()
    82	
    83	# --- Domain benchmark snapshot ---
    84	st.subheader("📐 Domain benchmark (XLV) & peers")
    85	bench_df = bm.fetch_benchmarks()
    86	if not bench_df.empty:
    87	    focus = ["XLV", "XBI", "XPH", "IXJ", "IHF", "IHI"]
    88	    sub = bench_df.loc[bench_df.index.intersection(focus)].copy()
    89	    sub = sub.rename(columns={
    90	        "name": "Name", "last": "Last",
    91	        "1d_%": "1D %", "5d_%": "5D %", "1m_%": "1M %", "ytd_%": "YTD %",
    92	    })
    93	    _render_pct_table(sub, pct_cols=["1D %", "5D %", "1M %", "YTD %"], num_cols=["Last"])
    94	
    95	st.divider()
    96	
    97	# --- Per-sector top 3 movers / drags ---
    98	st.subheader("🎯 Per-sector top 3 movers / drags (1D)")
    99	
   100	name_map = db.ticker_to_name(prefer_cn=True)   # M10 audit
   101	for sec in cfg["sectors"]:
   102	    rets = all_returns_by_sector.get(sec["id"])
   103	    if rets is None or rets.empty:
   104	        continue
   105	    with st.expander(f"**{sec['name']}**  ({len(rets)} tickers)"):
   106	        rets = rets.copy()
   107	        rets["name"] = rets.index.map(name_map)
   108	        rets = rets[["name", "last", "1d_%", "5d_%", "1m_%", "ytd_%"]]
   109	        rets.index.name = "Ticker"
   110	
   111	        rename_map = {"name": "Name", "last": "Last",
   112	                      "1d_%": "1D %", "5d_%": "5D %",
   113	                      "1m_%": "1M %", "ytd_%": "YTD %"}
   114	        c1, c2 = st.columns(2)
   115	        gainers = rets.sort_values("1d_%", ascending=False).head(3).rename(columns=rename_map)
   116	        drags = rets.sort_values("1d_%", ascending=True).head(3).rename(columns=rename_map)
   117	        # n2: Bloomberg ticker style
   118	        gainers.index = [fmt.fmt_ticker_bbg(t) for t in gainers.index]
   119	        drags.index = [fmt.fmt_ticker_bbg(t) for t in drags.index]
   120	        with c1:
   121	            st.markdown("🟢 Top 3 gainers (1D)")
   122	            _render_pct_table(gainers, pct_cols=["1D %", "5D %", "1M %", "YTD %"], num_cols=["Last"])
   123	        with c2:
   124	            st.markdown("🔴 Top 3 drags (1D)")
   125	            _render_pct_table(drags, pct_cols=["1D %", "5D %", "1M %", "YTD %"], num_cols=["Last"])
     1	"""Sector Heatmap — multiples + returns per sector with color gradient.
     2	
     3	Audit fixes applied:
     4	- M7: pre-format string DataFrame for display; Styler computes background from numeric.
     5	- M8: st.tabs instead of dropdown (analyst can piano-key through 7 sectors).
     6	- M10: default sort by market cap desc; name_cn priority (中文卖方习惯).
     7	- M1: use USD-converted close series for fair cross-region return comparison.
     8	- M11: mcap_tier shown as badge; sidebar min-mcap filter.
     9	"""
    10	
    11	from __future__ import annotations
    12	
    13	from pathlib import Path
    14	
    15	import pandas as pd
    16	import streamlit as st
    17	import yaml
    18	
    19	from lib import db
    20	from lib import format as fmt
    21	
    22	st.set_page_config(page_title="Sector Heatmap · invest-dashboard", page_icon="🔥", layout="wide")
    23	
    24	REPO_ROOT = Path(__file__).resolve().parent.parent.parent
    25	DOMAIN_CFG = REPO_ROOT / "config" / "domains" / "healthcare.yml"
    26	
    27	
    28	@st.cache_data(ttl=600)
    29	def load_domain_cfg() -> dict:
    30	    with DOMAIN_CFG.open() as f:
    31	        return yaml.safe_load(f)
    32	
    33	
    34	cfg = load_domain_cfg()
    35	
    36	st.title("🔥 Sector Heatmap")
    37	st.caption("Cross-sectional snapshot per sector. Multiples from yfinance — trailing + 12M forward only.")
    38	
    39	# --- Sidebar filter (M11 audit) ---
    40	with st.sidebar:
    41	    st.subheader("Filter")
    42	    min_mcap_b = st.slider(
    43	        "Min market cap (USD B)", 0.0, 50.0, 0.0, 0.5,
    44	        help="过滤掉小市值标的避免均值扭曲（GLM audit M11: 4587.T $904M 拉低 biotech 均值）"
    45	    )
    46	    sort_col = st.selectbox(
    47	        "Sort by",
    48	        ["Mcap USD", "YTD %", "1M %", "Trail P/E", "Fwd P/E"],
    49	        index=0,
    50	        help="默认按市值降序（M10 audit: 中文卖方习惯）"
    51	    )
    52	
    53	
    54	def render_sector(sec: dict) -> None:
    55	    uni = db.sector_tickers("healthcare", sec["id"])
    56	    tickers = tuple(uni["ticker"].tolist())
    57	    if not tickers:
    58	        st.warning(f"No tickers in sector {sec['name']}")
    59	        return
    60	
    61	    # M1: use USD-converted close series
    62	    closes = db.get_close_series_usd(tickers)
    63	    rets = db.compute_returns(closes)
    64	    mults = db.latest_multiples(tickers)
    65	    name_map = db.ticker_to_name(prefer_cn=True)   # M10 audit
    66	    region_map = uni.set_index("ticker")["region"].to_dict()
    67	
    68	    # --- Merge numeric DataFrame (for gradient calc) ---
    69	    merged = rets.copy() if not rets.empty else pd.DataFrame(index=list(tickers))
    70	    if not mults.empty:
    71	        for col in ["market_cap_usd", "mcap_tier", "trailing_pe", "forward_pe",
    72	                    "ev_ebitda", "ev_sales", "fcf_yield", "pb"]:
    73	            if col in mults.columns:
    74	                merged[col] = mults[col]
    75	    merged["Name"] = pd.Series(name_map).reindex(merged.index)
    76	    merged["Region"] = pd.Series(region_map).reindex(merged.index)
    77	    merged["Ticker_bbg"] = [fmt.fmt_ticker_bbg(t) for t in merged.index]   # n2 audit
    78	
    79	    # M11 audit: filter by min_mcap (in B)
    80	    if min_mcap_b > 0:
    81	        mcap_filter = merged["market_cap_usd"] >= (min_mcap_b * 1e9)
    82	        merged = merged[mcap_filter]
    83	
    84	    # M10 audit: default sort by market cap desc
    85	    sort_map = {
    86	        "Mcap USD": "market_cap_usd",
    87	        "YTD %": "ytd_%",
    88	        "1M %": "1m_%",
    89	        "Trail P/E": "trailing_pe",
    90	        "Fwd P/E": "forward_pe",
    91	    }
    92	    sort_field = sort_map.get(sort_col, "market_cap_usd")
    93	    ascending = "P/E" in sort_col   # cheaper first for P/E
    94	    if sort_field in merged.columns:
    95	        merged = merged.sort_values(sort_field, ascending=ascending, na_position="last")
    96	
    97	    if merged.empty:
    98	        st.info(f"No tickers in {sec['name']} after min-mcap filter (>= ${min_mcap_b:.1f}B)")
    99	        return
   100	
   101	    # --- Build STRING display DataFrame (M7 audit) ---
   102	    display_str = pd.DataFrame(index=merged.index)
   103	    display_str["BBG"] = merged["Ticker_bbg"]
   104	    display_str["Name"] = merged["Name"].fillna(merged.index.to_series())
   105	    display_str["Tier"] = merged.get("mcap_tier", pd.Series(index=merged.index)).fillna("—")
   106	    display_str["Mcap USD"] = merged["market_cap_usd"].apply(fmt.fmt_money_b)
   107	    display_str["YTD %"] = merged["ytd_%"].apply(fmt.fmt_pct)
   108	    display_str["1M %"] = merged["1m_%"].apply(fmt.fmt_pct)
   109	    display_str["5D %"] = merged["5d_%"].apply(fmt.fmt_pct)
   110	    display_str["1D %"] = merged["1d_%"].apply(fmt.fmt_pct)
   111	    display_str["Trail P/E"] = merged["trailing_pe"].apply(fmt.fmt_ratio)
   112	    display_str["Fwd P/E"] = merged["forward_pe"].apply(fmt.fmt_ratio)
   113	    display_str["EV/EBITDA"] = merged["ev_ebitda"].apply(fmt.fmt_ratio)
   114	    display_str["EV/Sales"] = merged["ev_sales"].apply(fmt.fmt_ratio)
   115	    display_str["FCF Yld"] = merged["fcf_yield"].apply(fmt.fmt_pct_decimal)
   116	    display_str["P/B"] = merged["pb"].apply(fmt.fmt_ratio)
   117	    display_str.index.name = "Ticker"
   118	
   119	    # --- Apply colors via Styler using NUMERIC values from `merged` ---
   120	    pct_cols = ["YTD %", "1M %", "5D %", "1D %"]
   121	    low_good_cols = ["Trail P/E", "Fwd P/E", "EV/EBITDA", "EV/Sales", "P/B"]
   122	    high_good_cols = ["FCF Yld"]
   123	
   124	    pct_num_map = {"YTD %": "ytd_%", "1M %": "1m_%", "5D %": "5d_%", "1D %": "1d_%"}
   125	    mult_num_map = {"Trail P/E": "trailing_pe", "Fwd P/E": "forward_pe",
   126	                    "EV/EBITDA": "ev_ebitda", "EV/Sales": "ev_sales", "P/B": "pb",
   127	                    "FCF Yld": "fcf_yield"}
   128	
   129	    styler = display_str.style
   130	    for col in pct_cols:
     1	"""invest-dashboard — Home page.
     2	
     3	Audit fixes:
     4	- M7: pre-format strings + Styler color-only
     5	- M10: name_cn priority
     6	- B4: global ticker search in sidebar (stub for D6 Ticker Drill)
     7	- n2: Bloomberg ticker style display
     8	"""
     9	
    10	from __future__ import annotations
    11	
    12	import pandas as pd
    13	import streamlit as st
    14	
    15	from lib import benchmarks as bm
    16	from lib import db
    17	from lib import format as fmt
    18	
    19	st.set_page_config(
    20	    page_title="invest-dashboard",
    21	    page_icon="📊",
    22	    layout="wide",
    23	    initial_sidebar_state="expanded",
    24	)
    25	
    26	# --- B4 audit: global ticker search ---
    27	with st.sidebar:
    28	    st.subheader("🔍 Find ticker")
    29	    all_t = db.all_tickers()
    30	    pick = st.selectbox(
    31	        "Jump to ticker drill",
    32	        options=[""] + sorted(all_t),
    33	        format_func=lambda x: fmt.fmt_ticker_bbg(x) if x else "— select —",
    34	    )
    35	    if pick:
    36	        st.info(f"📍 Selected: **{fmt.fmt_ticker_bbg(pick)}** — Ticker Drill page coming D6.")
    37	        # st.switch_page("pages/6_🔍_Ticker_Drill.py")   # uncomment when D6 ships
    38	
    39	# --- Header ---
    40	st.title("📊 Multi-Domain Investment Dashboard")
    41	st.caption(
    42	    "Sell-side healthcare coverage · v1 (P0) · data via yfinance · "
    43	    "build: `streamlit_app.py` · plan: `~/.claude/plans/modular-toasting-spindle.md`"
    44	)
    45	
    46	latest = db.latest_snapshot_date()
    47	fetch_utc = db.last_fetch_utc()
    48	col1, col2, col3 = st.columns([2, 2, 3])
    49	col1.metric("📅 Latest snapshot", latest or "—")
    50	col2.metric("🕒 Last fetch (UTC)", fetch_utc[:16] if fetch_utc else "—")
    51	n_tickers = len(db.all_tickers())
    52	col3.metric("🌐 Universe tickers", f"{n_tickers}")
    53	
    54	st.divider()
    55	
    56	
    57	def _render_pct_table(df: pd.DataFrame, pct_cols: list[str], num_cols: list[str] | None = None) -> None:
    58	    """Render a DataFrame with formatted strings + colored pct columns."""
    59	    display_str = pd.DataFrame(index=df.index)
    60	    for c in df.columns:
    61	        if c in pct_cols:
    62	            display_str[c] = df[c].apply(fmt.fmt_pct)
    63	        elif num_cols and c in num_cols:
    64	            display_str[c] = df[c].apply(fmt.fmt_num)
    65	        else:
    66	            display_str[c] = df[c]
    67	    styler = display_str.style
    68	    for c in pct_cols:
    69	        styler = styler.apply(
    70	            lambda _s, n=df[c]: fmt.background_gradient_diverging(n),
    71	            subset=[c],
    72	        )
    73	    st.dataframe(styler, use_container_width=True)
    74	
    75	
    76	# --- Benchmarks ---
    77	st.subheader("📐 Benchmarks")
    78	bench_df = bm.fetch_benchmarks()
    79	if not bench_df.empty:
    80	    show = bench_df[["name", "last", "1d_%", "5d_%", "1m_%", "ytd_%"]].rename(columns={

exec
/bin/zsh -lc "nl -ba app/lib/ui.py | sed -n '1,180p'; rg -n \"Find ticker|Jump to ticker drill|st.sidebar\" app -S" in /Users/gcc/invest-dashboard
 succeeded in 0ms:
     1	"""Shared Streamlit UI components."""
     2	
     3	from __future__ import annotations
     4	
     5	import streamlit as st
     6	from lib import db
     7	from lib import format as fmt
     8	
     9	def sidebar_search(key_prefix: str = ""):
    10	    """Unified sidebar ticker search with session state persistence."""
    11	    st.subheader("🔍 Find ticker")
    12	    
    13	    # Initialize session state if not present
    14	    if "global_ticker" not in st.session_state:
    15	        st.session_state.global_ticker = ""
    16	
    17	    all_t = sorted(db.all_tickers())
    18	    
    19	    # We use a temporary key for the selectbox and then sync with session_state
    20	    # to avoid the "Duplicate Key" or "Value not in options" issues during page switches.
    21	    current_index = 0
    22	    if st.session_state.global_ticker in all_t:
    23	        current_index = all_t.index(st.session_state.global_ticker) + 1
    24	
    25	    pick = st.selectbox(
    26	        "Jump to ticker drill",
    27	        options=[""] + all_t,
    28	        index=current_index,
    29	        format_func=lambda x: fmt.fmt_ticker_bbg(x) if x else "— select —",
    30	        key=f"{key_prefix}_search_box",
    31	    )
    32	    
    33	    if pick != st.session_state.global_ticker:
    34	        st.session_state.global_ticker = pick
    35	        # st.rerun() # Optional: force immediate update if needed
    36	
    37	    if st.session_state.global_ticker:
    38	        st.info(f"📍 **{fmt.fmt_ticker_bbg(st.session_state.global_ticker)}** — Ticker Drill (D6) coming soon.")
    39	
    40	def onboarding_expander(page_name: str, markdown_text: str):
    41	    """Consistent onboarding expander across pages."""
    42	    with st.expander(f"📖 How to read this {page_name}"):
    43	        st.markdown(markdown_text)
app/streamlit_app.py:27:with st.sidebar:
app/streamlit_app.py:28:    st.subheader("🔍 Find ticker")
app/streamlit_app.py:31:        "Jump to ticker drill",
app/pages/5_💰_Valuation_Scanner.py:40:with st.sidebar:
app/pages/5_💰_Valuation_Scanner.py:41:    st.subheader("🔍 Find ticker")
app/pages/5_💰_Valuation_Scanner.py:43:        "Jump to ticker drill",
app/pages/3_💎_CMSI_Coverage.py:27:with st.sidebar:
app/pages/3_💎_CMSI_Coverage.py:28:    st.subheader("🔍 Find ticker")
app/pages/3_💎_CMSI_Coverage.py:30:        "Jump to ticker drill",
app/lib/ui.py:11:    st.subheader("🔍 Find ticker")
app/lib/ui.py:26:        "Jump to ticker drill",
app/pages/2_🔥_Sector_Heatmap.py:40:with st.sidebar:
app/pages/4_🧬_Strategy_Picks.py:28:with st.sidebar:

exec
/bin/zsh -lc "nl -ba app/.streamlit/config.toml | sed -n '1,80p'" in /Users/gcc/invest-dashboard
 succeeded in 0ms:
     1	[theme]
     2	base = "dark"
     3	primaryColor = "#22c55e"          # green for gains
     4	backgroundColor = "#0f172a"       # dark slate
     5	secondaryBackgroundColor = "#1e293b"
     6	textColor = "#f1f5f9"
     7	font = "monospace"
     8	
     9	[server]
    10	headless = true
    11	runOnSave = true
    12	
    13	[browser]
    14	gatherUsageStats = false

exec
/bin/zsh -lc "git status --short --ignored | sed -n '1,80p'; git ls-files app/lib/ui.py app/.streamlit/config.toml" in /Users/gcc/invest-dashboard
 succeeded in 0ms:
 M app/lib/charts.py
 M "app/pages/4_\360\237\247\254_Strategy_Picks.py"
 M "app/pages/5_\360\237\222\260_Valuation_Scanner.py"
?? app/lib/ui.py
!! .omc/
!! app/__pycache__/
!! app/lib/__pycache__/
!! app/pages/__pycache__/
!! jobs/__pycache__/
app/.streamlit/config.toml

exec
/bin/zsh -lc "git ls-files '*.pyc' app/__pycache__ app/lib/__pycache__ app/pages/__pycache__" in /Users/gcc/invest-dashboard
 succeeded in 0ms:
codex
There are local edits on top of `9e1179e` in `app/lib/charts.py`, Strategy Picks, Scanner, plus an untracked `app/lib/ui.py`. I’m not changing them; I’m using the current working tree for line references because that’s what would deploy if committed now.
exec
/bin/zsh -lc 'git diff --stat' in /Users/gcc/invest-dashboard
exec
/bin/zsh -lc "git diff -- app/lib/charts.py app/pages/4_🧬_Strategy_Picks.py app/pages/5_💰_Valuation_Scanner.py | sed -n '1,260p'" in /Users/gcc/invest-dashboard
 succeeded in 0ms:
 app/lib/charts.py                                  | 46 +++++++++++++----
 "app/pages/4_\360\237\247\254_Strategy_Picks.py"   | 39 +++++++++-----
 .../pages/5_\360\237\222\260_Valuation_Scanner.py" | 59 +++++++++++++---------
 3 files changed, 99 insertions(+), 45 deletions(-)

 succeeded in 0ms:
diff --git a/app/lib/charts.py b/app/lib/charts.py
index 391afcf..168fc2f 100644
--- a/app/lib/charts.py
+++ b/app/lib/charts.py
@@ -51,9 +51,11 @@ def cumulative_return_chart(
     closes: pd.DataFrame,
     title: str = "",
     pick_date: str | None = None,
+    show_individual: bool = False,
 ) -> go.Figure:
     """Index series to pick_date (or first date) = 100.
-    Each ticker shown as a translucent line, plus equal-weighted portfolio in bold.
+    Shows equal-weighted portfolio in bold, plus a 10-90th percentile shaded band
+    for dispersion. Individual lines optional.
     """
     if closes.empty:
         return go.Figure()
@@ -63,27 +65,51 @@ def cumulative_return_chart(
         closes = closes[closes.index >= anchor_ts]
         if closes.empty:
             return go.Figure()
+
     base = closes.iloc[0]
     norm = (closes / base) * 100
     portfolio = norm.mean(axis=1)
+
     fig = go.Figure()
-    for col in norm.columns:
-        fig.add_trace(go.Scatter(
-            x=norm.index, y=norm[col],
-            mode="lines", name=col,
-            line=dict(width=1), opacity=0.35,
-            showlegend=False, hoverinfo="x+y+name",
-        ))
+
+    # --- Dispersion Band (10th - 90th percentile) ---
+    p10 = norm.quantile(0.1, axis=1)
+    p90 = norm.quantile(0.9, axis=1)
+
+    fig.add_trace(go.Scatter(
+        x=p90.index.tolist() + p90.index[::-1].tolist(),
+        y=p90.values.tolist() + p10.values[::-1].tolist(),
+        fill="toself",
+        fillcolor="rgba(34, 197, 94, 0.15)",  # Translucent green
+        line=dict(color="rgba(255,255,255,0)"),
+        hoverinfo="skip",
+        showlegend=True,
+        name="10th–90th %ile Range",
+    ))
+
+    # --- Individual Lines (Optional) ---
+    if show_individual:
+        for col in norm.columns:
+            fig.add_trace(go.Scatter(
+                x=norm.index, y=norm[col],
+                mode="lines", name=col,
+                line=dict(width=1), opacity=0.25,
+                showlegend=False, hoverinfo="x+y+name",
+            ))
+
+    # --- Portfolio Line ---
     fig.add_trace(go.Scatter(
         x=portfolio.index, y=portfolio.values,
-        mode="lines", name="Equal-weight portfolio",
+        mode="lines", name="Equal-weight Portfolio",
         line=dict(width=3, color=PRIMARY),
     ))
+
     fig.update_layout(
         template=PLOT_TEMPLATE,
         title=title,
         yaxis_title="Indexed (start=100)",
-        height=420,
+        height=450,
         margin=dict(l=10, r=10, t=40, b=10),
+        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
     )
     return fig
diff --git "a/app/pages/4_\360\237\247\254_Strategy_Picks.py" "b/app/pages/4_\360\237\247\254_Strategy_Picks.py"
index 5c8110b..806ccdf 100644
--- "a/app/pages/4_\360\237\247\254_Strategy_Picks.py"
+++ "b/app/pages/4_\360\237\247\254_Strategy_Picks.py"
@@ -16,6 +16,7 @@ from lib import db
 from lib import format as fmt
 from lib import strategy as strat
 from lib import charts
+from lib import ui
 
 st.set_page_config(
     page_title="Strategy Picks · invest-dashboard",
@@ -23,17 +24,12 @@ st.set_page_config(
     layout="wide",
 )
 
-# Sidebar global search (B4 audit, on every page)
+# Sidebar global search
 with st.sidebar:
-    st.subheader("🔍 Find ticker")
-    pick = st.selectbox(
-        "Jump to ticker drill",
-        options=[""] + sorted(db.all_tickers()),
-        format_func=lambda x: fmt.fmt_ticker_bbg(x) if x else "— select —",
-        key="strategy_search",
-    )
-    if pick:
-        st.info(f"📍 {fmt.fmt_ticker_bbg(pick)} — Ticker Drill (D6) coming soon.")
+    ui.sidebar_search(key_prefix="strategy")
+    st.divider()
+    st.subheader("⚙️ Chart Settings")
+    show_lines = st.checkbox("Show individual ticker lines", value=False, help="Display translucent lines for every ticker in the portfolio.")
 
 st.title("🧬 Strategy Picks Performance")
 st.caption(
@@ -122,6 +118,7 @@ def render_strategy(strat_id: str) -> None:
             picks_closes[picks_closes.index >= pd.Timestamp(pick_date)],
             title=f"{cfg['name']} — Indexed return since {pick_date}",
             pick_date=pick_date,
+            show_individual=show_lines,
         )
         # Add benchmark overlay
         import plotly.graph_objects as go
@@ -133,7 +130,7 @@ def render_strategy(strat_id: str) -> None:
             ))
         st.plotly_chart(fig, use_container_width=True)
 
-    # --- Top/Bottom ranking table ---
+    # --- Top/Worst ranking table ---
     if perf.empty:
         st.warning("No per-ticker performance data.")
         return
@@ -169,7 +166,7 @@ def render_strategy(strat_id: str) -> None:
         )
         st.dataframe(styler, use_container_width=True)
     with c_bot:
-        st.markdown(f"##### 🔴 Bottom {min(5, len(perf_display))} (since-inception)")
+        st.markdown(f"##### 🔴 Worst {min(5, len(perf_display))} (since-inception)")
         bot5 = perf_display.tail(5).iloc[::-1]
         styler = (
             bot5.style
@@ -200,6 +197,24 @@ def render_strategy(strat_id: str) -> None:
         st.dataframe(styler, use_container_width=True, height=500)
 
 
+# --- Onboarding expander ---
+ui.onboarding_expander("Strategy Page", """
+**Cumulative Return Chart**: 
+- **Portfolio (Equal-weight)**: 每只票在 Pick Date 初始权重相同，展示其后的复合回报（Indexed=100）。
+- **Benchmark**: 比较基准（如 XBI 或 3110.HK）的同步表现。
+- **10th–90th %ile Range**: 阴影区域展示了组合内 80% 标的的表现分布。如果阴影很宽，说明个股分化巨大。
+- **Individual Lines**: 可在侧边栏开启，查看每只具体股票的轨迹。
+
+**Metrics**:
+- **Alpha (pp)**: 组合回报减去基准回报的百分点差。
+- **Pick Score**: 如果来自 catalyst-monitor，显示其当时的量化评分。
+
+**Sorting**:
+- **Top 5**: 累计回报最高的 5 只票。
+- **Worst 5**: 累计回报最低的 5 只票（Worst first）。
+""")
+
+
 # --- M8 audit: tabs > dropdown ---
 strategy_tabs = st.tabs([strat.STRATEGIES[sid]["name"] for sid in strat.STRATEGIES])
 for tab, sid in zip(strategy_tabs, strat.STRATEGIES.keys()):
diff --git "a/app/pages/5_\360\237\222\260_Valuation_Scanner.py" "b/app/pages/5_\360\237\222\260_Valuation_Scanner.py"
index eb22091..cfcfbaf 100644
--- "a/app/pages/5_\360\237\222\260_Valuation_Scanner.py"
+++ "b/app/pages/5_\360\237\222\260_Valuation_Scanner.py"
@@ -17,6 +17,7 @@ import yaml
 
 from lib import db
 from lib import format as fmt
+from lib import ui
 
 st.set_page_config(
     page_title="Valuation Scanner · invest-dashboard",
@@ -27,48 +28,59 @@ st.set_page_config(
 REPO_ROOT = Path(__file__).resolve().parent.parent.parent
 DOMAIN_CFG = REPO_ROOT / "config" / "domains" / "healthcare.yml"
 
-
 @st.cache_data(ttl=600)
 def load_domain_cfg() -> dict:
     with DOMAIN_CFG.open() as f:
         return yaml.safe_load(f)
 
-
 cfg = load_domain_cfg()
+sector_options = [(sec["id"], sec["name"]) for sec in cfg["sectors"]]
+all_sector_ids = [s[0] for s in sector_options]
 
-# --- Sidebar global search ---
+# --- Sidebar global search + Filters ---
 with st.sidebar:
-    st.subheader("🔍 Find ticker")
-    pick = st.selectbox(
-        "Jump to ticker drill",
-        options=[""] + sorted(db.all_tickers()),
-        format_func=lambda x: fmt.fmt_ticker_bbg(x) if x else "— select —",
-        key="scanner_search",
-    )
-    if pick:
-        st.info(f"📍 {fmt.fmt_ticker_bbg(pick)} — Ticker Drill (D6) coming soon.")
+    ui.sidebar_search(key_prefix="scanner")
+    st.divider()
+    
+    st.subheader("🎯 Presets")
+    c1, c2 = st.columns(2)
+    if c1.button("💎 Deep Value", use_container_width=True):
+        st.session_state["scan_pe_pct"] = 15
+        st.session_state["scan_mcap"] = 5.0
+        st.session_state["scan_ytd"] = (-100, 20)
+        st.session_state["scan_5d"] = -30
+    if c2.button("🚀 Recovery", use_container_width=True):
+        st.session_state["scan_pe_pct"] = 30
+        st.session_state["scan_mcap"] = 2.0
+        st.session_state["scan_ytd"] = (-100, 0)
+        st.session_state["scan_5d"] = 5
+    if st.button("🔄 Reset all filters", use_container_width=True):
+        for k in ["scan_pe_pct", "scan_mcap", "scan_ytd", "scan_5d", "scan_sectors"]:
+            if k in st.session_state: del st.session_state[k]
+        st.rerun()
 
     st.divider()
     st.subheader("📊 Filters")
 
-    sector_options = [(sec["id"], sec["name"]) for sec in cfg["sectors"]]
     selected_sectors = st.multiselect(
         "Sector",
-        options=[s[0] for s in sector_options],
-        default=[s[0] for s in sector_options],
+        options=all_sector_ids,
+        default=all_sector_ids,
         format_func=lambda x: next(s[1] for s in sector_options if s[0] == x),
+        key="scan_sectors"
     )
 
-    min_mcap_b = st.slider("Min market cap (USD B)", 0.0, 50.0, 5.0, 0.5)
+    min_mcap_b = st.slider("Min market cap (USD B)", 0.0, 50.0, 5.0, 0.5, key="scan_mcap")
     pct_threshold = st.slider(
-        "P/E percentile threshold (within sector)",
+        "P/E percentile threshold",
         0, 100, 25,
-        help="只显示 fwd P/E 在板块内分位 ≤ 此阈值的候选（25 = bottom quartile = cheap）"
+        help="只显示 fwd P/E 在板块内分位 ≤ 此阈值的候选",
+        key="scan_pe_pct"
     )
     pe_metric = st.selectbox("P/E metric", ["forward_pe", "trailing_pe"], index=0)
-    ytd_min, ytd_max = st.slider("YTD return range (%)", -100, 200, (-50, 100), 5)
-    min_5d = st.slider("Min 5D return (%)", -30, 30, -10, 1,
-                       help="recent momentum filter（正值过滤暴跌反弹候选）")
+    ytd_range = st.slider("YTD return range (%)", -100, 200, (-50, 100), 5, key="scan_ytd")
+    ytd_min, ytd_max = ytd_range
+    min_5d = st.slider("Min 5D return (%)", -30, 30, -10, 1, key="scan_5d")
 
 
 # --- Build candidate universe ---
@@ -168,8 +180,8 @@ if candidates.empty:
 disp = pd.DataFrame(index=candidates.index)
 disp["BBG"] = [fmt.fmt_ticker_bbg(t) for t in disp.index]

exec
/bin/zsh -lc "git show HEAD:app/pages/4_🧬_Strategy_Picks.py | nl -ba | sed -n '108,138p'; git show HEAD:app/lib/charts.py | nl -ba | sed -n '50,90p'" in /Users/gcc/invest-dashboard
 succeeded in 0ms:
   108	            f"{alpha:+.2f}pp" if alpha is not None else "—",
   109	            delta=f"{'outperform' if alpha and alpha > 0 else 'underperform' if alpha else 'tied'}",
   110	            delta_color="normal" if alpha and alpha > 0 else "inverse" if alpha else "off",
   111	        )
   112	
   113	    # --- Cumulative return chart ---
   114	    if not portfolio.empty:
   115	        # Build a 2-column DataFrame: portfolio + benchmark
   116	        chart_df = pd.DataFrame({"Portfolio (equal-weight)": portfolio})
   117	        if not bench_norm.empty:
   118	            chart_df[f"{bench_sym} (benchmark)"] = bench_norm
   119	        chart_df = chart_df.dropna(how="all")
   120	
   121	        fig = charts.cumulative_return_chart(
   122	            picks_closes[picks_closes.index >= pd.Timestamp(pick_date)],
   123	            title=f"{cfg['name']} — Indexed return since {pick_date}",
   124	            pick_date=pick_date,
   125	        )
   126	        # Add benchmark overlay
   127	        import plotly.graph_objects as go
   128	        if not bench_norm.empty:
   129	            fig.add_trace(go.Scatter(
   130	                x=bench_norm.index, y=bench_norm.values,
   131	                mode="lines", name=f"{bench_sym} ({bench_name})",
   132	                line=dict(width=3, color="#a78bfa", dash="dash"),
   133	            ))
   134	        st.plotly_chart(fig, use_container_width=True)
   135	
   136	    # --- Top/Bottom ranking table ---
   137	    if perf.empty:
   138	        st.warning("No per-ticker performance data.")
    50	def cumulative_return_chart(
    51	    closes: pd.DataFrame,
    52	    title: str = "",
    53	    pick_date: str | None = None,
    54	) -> go.Figure:
    55	    """Index series to pick_date (or first date) = 100.
    56	    Each ticker shown as a translucent line, plus equal-weighted portfolio in bold.
    57	    """
    58	    if closes.empty:
    59	        return go.Figure()
    60	    closes = closes.sort_index()
    61	    if pick_date:
    62	        anchor_ts = pd.Timestamp(pick_date)
    63	        closes = closes[closes.index >= anchor_ts]
    64	        if closes.empty:
    65	            return go.Figure()
    66	    base = closes.iloc[0]
    67	    norm = (closes / base) * 100
    68	    portfolio = norm.mean(axis=1)
    69	    fig = go.Figure()
    70	    for col in norm.columns:
    71	        fig.add_trace(go.Scatter(
    72	            x=norm.index, y=norm[col],
    73	            mode="lines", name=col,
    74	            line=dict(width=1), opacity=0.35,
    75	            showlegend=False, hoverinfo="x+y+name",
    76	        ))
    77	    fig.add_trace(go.Scatter(
    78	        x=portfolio.index, y=portfolio.values,
    79	        mode="lines", name="Equal-weight portfolio",
    80	        line=dict(width=3, color=PRIMARY),
    81	    ))
    82	    fig.update_layout(
    83	        template=PLOT_TEMPLATE,
    84	        title=title,
    85	        yaxis_title="Indexed (start=100)",
    86	        height=420,
    87	        margin=dict(l=10, r=10, t=40, b=10),
    88	    )
    89	    return fig

exec
/bin/zsh -lc "nl -ba jobs/init_db.py | sed -n '1,260p'; nl -ba jobs/load_universe.py | sed -n '1,240p'; nl -ba jobs/fetch_eod.py | sed -n '1,280p'" in /Users/gcc/invest-dashboard
 succeeded in 0ms:
     1	"""Initialize SQLite schema for invest-dashboard.
     2	
     3	Idempotent — safe to run multiple times.
     4	
     5	Usage:
     6	    python jobs/init_db.py
     7	"""
     8	
     9	from __future__ import annotations
    10	
    11	import sqlite3
    12	from pathlib import Path
    13	
    14	REPO_ROOT = Path(__file__).resolve().parent.parent
    15	DB_PATH = REPO_ROOT / "data" / "snapshots.db"
    16	
    17	SCHEMA = """
    18	-- Daily prices (auto-grown by fetch_eod.py)
    19	-- Local-currency close + USD-converted close (M1 audit fix)
    20	CREATE TABLE IF NOT EXISTS prices_daily (
    21	    ticker        TEXT NOT NULL,
    22	    date          TEXT NOT NULL,        -- YYYY-MM-DD
    23	    open          REAL,
    24	    high          REAL,
    25	    low           REAL,
    26	    close         REAL,                  -- local ccy
    27	    adj_close     REAL,                  -- local ccy
    28	    volume        INTEGER,
    29	    currency      TEXT,                  -- USD / HKD / JPY / KRW / EUR / CNY / GBP / CHF
    30	    close_usd     REAL,                  -- M1: USD-converted close
    31	    adj_close_usd REAL,                  -- M1: USD-converted adj_close
    32	    PRIMARY KEY (ticker, date)
    33	);
    34	CREATE INDEX IF NOT EXISTS idx_prices_date ON prices_daily(date);
    35	
    36	-- Multiple snapshot 时序 (core value: 自累积 → 90d 后可做 Z-score)
    37	CREATE TABLE IF NOT EXISTS multiples_daily (
    38	    ticker            TEXT NOT NULL,
    39	    date              TEXT NOT NULL,
    40	    market_cap_usd    REAL,
    41	    mcap_tier         TEXT,                -- M11: mega/large/mid/small/micro
    42	    trailing_pe       REAL,
    43	    forward_pe        REAL,
    44	    trailing_eps      REAL,
    45	    forward_eps       REAL,
    46	    ev_ebitda         REAL,
    47	    ev_sales          REAL,
    48	    fcf_yield         REAL,
    49	    peg               REAL,
    50	    pb                REAL,
    51	    ytd_return        REAL,
    52	    last_price        REAL,                -- local ccy
    53	    last_price_usd    REAL,                -- M1: USD-converted last price
    54	    currency          TEXT,                -- 来自 yfinance.info
    55	    PRIMARY KEY (ticker, date)
    56	);
    57	CREATE INDEX IF NOT EXISTS idx_mult_date ON multiples_daily(date);
    58	
    59	-- Universe membership (many-to-many for cross-sector tickers like ISRG / HCA)
    60	CREATE TABLE IF NOT EXISTS universe_member (
    61	    domain    TEXT NOT NULL,
    62	    sector    TEXT NOT NULL,
    63	    ticker    TEXT NOT NULL,
    64	    name_cn   TEXT,
    65	    name_en   TEXT,
    66	    region    TEXT,
    67	    note      TEXT,
    68	    PRIMARY KEY (domain, sector, ticker)
    69	);
    70	CREATE INDEX IF NOT EXISTS idx_um_ticker ON universe_member(ticker);
    71	CREATE INDEX IF NOT EXISTS idx_um_domain_sector ON universe_member(domain, sector);
    72	
    73	-- Meta key/value
    74	CREATE TABLE IF NOT EXISTS meta (
    75	    key         TEXT PRIMARY KEY,
    76	    value       TEXT,
    77	    updated_at  TEXT
    78	);
    79	"""
    80	
    81	
    82	def main() -> None:
    83	    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    84	    conn = sqlite3.connect(DB_PATH)
    85	    try:
    86	        conn.executescript(SCHEMA)
    87	        conn.commit()
    88	        # Sanity log
    89	        cur = conn.execute(
    90	            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    91	        )
    92	        tables = [row[0] for row in cur.fetchall()]
    93	        print(f"[init_db] DB at: {DB_PATH}")
    94	        print(f"[init_db] Tables: {tables}")
    95	    finally:
    96	        conn.close()
    97	
    98	
    99	if __name__ == "__main__":
   100	    main()
     1	"""Load universe YAML files into the universe_member table.
     2	
     3	Idempotent — uses INSERT OR REPLACE.
     4	
     5	Usage:
     6	    python jobs/load_universe.py
     7	"""
     8	
     9	from __future__ import annotations
    10	
    11	import sqlite3
    12	from pathlib import Path
    13	
    14	import yaml
    15	
    16	REPO_ROOT = Path(__file__).resolve().parent.parent
    17	DB_PATH = REPO_ROOT / "data" / "snapshots.db"
    18	DOMAINS_DIR = REPO_ROOT / "config" / "domains"
    19	UNIVERSES_DIR = REPO_ROOT / "config" / "universes"
    20	
    21	
    22	def load_domains() -> list[dict]:
    23	    """Read all domain YAMLs."""
    24	    domains = []
    25	    for p in sorted(DOMAINS_DIR.glob("*.yml")):
    26	        with p.open() as f:
    27	            data = yaml.safe_load(f)
    28	        data["_file"] = p.name
    29	        data["_domain_id"] = p.stem      # e.g. "healthcare"
    30	        domains.append(data)
    31	    return domains
    32	
    33	
    34	def load_universe_file(filename: str) -> dict:
    35	    """Read a single universe YAML by filename."""
    36	    path = UNIVERSES_DIR / filename
    37	    with path.open() as f:
    38	        return yaml.safe_load(f)
    39	
    40	
    41	def upsert_members(conn: sqlite3.Connection, domain_id: str,
    42	                   sector_id: str, tickers: list[dict]) -> int:
    43	    """Insert/replace universe_member rows. Returns row count."""
    44	    rows = []
    45	    for entry in tickers:
    46	        rows.append((
    47	            domain_id,
    48	            sector_id,
    49	            entry["ticker"],
    50	            entry.get("name_cn"),
    51	            entry.get("name_en"),
    52	            entry.get("region"),
    53	            entry.get("note"),
    54	        ))
    55	    conn.executemany(
    56	        """
    57	        INSERT OR REPLACE INTO universe_member
    58	            (domain, sector, ticker, name_cn, name_en, region, note)
    59	        VALUES (?, ?, ?, ?, ?, ?, ?)
    60	        """,
    61	        rows,
    62	    )
    63	    return len(rows)
    64	
    65	
    66	def main() -> None:
    67	    if not DB_PATH.exists():
    68	        raise SystemExit(
    69	            f"DB not found at {DB_PATH}. Run jobs/init_db.py first."
    70	        )
    71	
    72	    conn = sqlite3.connect(DB_PATH)
    73	    try:
    74	        total = 0
    75	        for domain in load_domains():
    76	            domain_id = domain["_domain_id"]
    77	            sectors = domain.get("sectors") or []
    78	            for sector in sectors:
    79	                uni = load_universe_file(sector["universe_file"])
    80	                n = upsert_members(
    81	                    conn,
    82	                    domain_id,
    83	                    sector["id"],
    84	                    uni.get("tickers") or [],
    85	                )
    86	                total += n
    87	                print(f"[load_universe] {domain_id} / {sector['id']}: {n} tickers")
    88	            # Coverage list (CMSI)
    89	            cov = domain.get("coverage")
    90	            if cov:
    91	                uni = load_universe_file(cov["universe_file"])
    92	                # 用 sector="_coverage" 标识 cover list（不是 sector）
    93	                n = upsert_members(
    94	                    conn,
    95	                    domain_id,
    96	                    "_coverage",
    97	                    uni.get("tickers") or [],
    98	                )
    99	                total += n
   100	                print(f"[load_universe] {domain_id} / _coverage: {n} tickers")
   101	        conn.commit()
   102	        # Summary
   103	        cur = conn.execute(
   104	            "SELECT domain, sector, COUNT(*) FROM universe_member "
   105	            "GROUP BY domain, sector ORDER BY domain, sector"
   106	        )
   107	        print(f"\n[load_universe] Total upserted: {total}")
   108	        print("\n[load_universe] universe_member rows by (domain, sector):")
   109	        for row in cur.fetchall():
   110	            print(f"  {row[0]:>14s} / {row[1]:<16s} {row[2]:>3d}")
   111	    finally:
   112	        conn.close()
   113	
   114	
   115	if __name__ == "__main__":
   116	    main()
     1	"""Fetch EOD price + multiple snapshot for all tickers in universe_member.
     2	
     3	Pattern crib from ~/strategy-weekly/weekly_perf.py:74-102 (yfinance batch).
     4	
     5	Usage:
     6	    python jobs/fetch_eod.py                       # today's EOD only
     7	    python jobs/fetch_eod.py --backfill-days 30    # 30-day historical backfill
     8	    python jobs/fetch_eod.py --skip-multiples      # prices only
     9	"""
    10	
    11	from __future__ import annotations
    12	
    13	import argparse
    14	import sqlite3
    15	import time
    16	from datetime import date, datetime, timedelta, timezone
    17	from pathlib import Path
    18	
    19	import pandas as pd
    20	import yfinance as yf
    21	
    22	REPO_ROOT = Path(__file__).resolve().parent.parent
    23	DB_PATH = REPO_ROOT / "data" / "snapshots.db"
    24	
    25	# FX 转 USD（local ccy → USD）
    26	FX_PAIRS = {
    27	    "USD": None,                  # no conversion
    28	    "HKD": "USDHKD=X",
    29	    "JPY": "USDJPY=X",
    30	    "KRW": "USDKRW=X",
    31	    "CNY": "USDCNY=X",
    32	    "EUR": "EURUSD=X",            # inverse pair (we divide differently)
    33	    "GBP": "GBPUSD=X",            # inverse pair
    34	    "CHF": "USDCHF=X",
    35	}
    36	
    37	BATCH_SIZE = 40                   # yfinance batch download size
    38	SLEEP_BETWEEN_INFO = 0.4          # seconds between .info calls (rate limit, M4 doubled)
    39	INFO_MAX_RETRY = 4                # M4: max retries per ticker
    40	INFO_BACKOFF_BASE = 1.5           # M4: exp backoff multiplier
    41	INFO_FAIL_THRESHOLD = 0.20        # M4: fail workflow if >20% .info calls fail
    42	
    43	
    44	def cap_tier(mcap_usd: float | None) -> str | None:
    45	    """M11: classify market cap into tier."""
    46	    if mcap_usd is None or pd.isna(mcap_usd):
    47	        return None
    48	    if mcap_usd >= 200e9:
    49	        return "mega"
    50	    if mcap_usd >= 50e9:
    51	        return "large"
    52	    if mcap_usd >= 10e9:
    53	        return "mid"
    54	    if mcap_usd >= 2e9:
    55	        return "small"
    56	    return "micro"
    57	
    58	
    59	# ----- args -----
    60	def parse_args() -> argparse.Namespace:
    61	    p = argparse.ArgumentParser()
    62	    p.add_argument("--backfill-days", type=int, default=0,
    63	                   help="Days of historical price to backfill (0 = today only).")
    64	    p.add_argument("--skip-multiples", action="store_true",
    65	                   help="Skip yfinance.info multiples fetch (faster, prices only).")
    66	    p.add_argument("--limit", type=int, default=0,
    67	                   help="Process only first N tickers (debug).")
    68	    return p.parse_args()
    69	
    70	
    71	# ----- DB helpers -----
    72	def get_tickers(conn: sqlite3.Connection, limit: int = 0) -> list[str]:
    73	    q = "SELECT DISTINCT ticker FROM universe_member ORDER BY ticker"
    74	    if limit > 0:
    75	        q += f" LIMIT {limit}"
    76	    return [row[0] for row in conn.execute(q).fetchall()]
    77	
    78	
    79	def upsert_prices(conn: sqlite3.Connection, rows: list[tuple]) -> int:
    80	    if not rows:
    81	        return 0
    82	    conn.executemany(
    83	        """INSERT OR REPLACE INTO prices_daily
    84	           (ticker, date, open, high, low, close, adj_close, volume, currency,
    85	            close_usd, adj_close_usd)
    86	           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
    87	        rows,
    88	    )
    89	    return len(rows)
    90	
    91	
    92	def upsert_multiples(conn: sqlite3.Connection, rows: list[tuple]) -> int:
    93	    if not rows:
    94	        return 0
    95	    conn.executemany(
    96	        """INSERT OR REPLACE INTO multiples_daily
    97	           (ticker, date, market_cap_usd, mcap_tier, trailing_pe, forward_pe,
    98	            trailing_eps, forward_eps, ev_ebitda, ev_sales, fcf_yield,
    99	            peg, pb, ytd_return, last_price, last_price_usd, currency)
   100	           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
   101	        rows,
   102	    )
   103	    return len(rows)
   104	
   105	
   106	def set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
   107	    conn.execute(
   108	        "INSERT OR REPLACE INTO meta (key, value, updated_at) VALUES (?, ?, ?)",
   109	        (key, value, datetime.now(timezone.utc).isoformat(timespec="seconds")),
   110	    )
   111	
   112	
   113	# ----- FX rate snapshot -----
   114	def fetch_fx_rates(prev_rates: dict[str, float] | None = None) -> dict[str, float]:
   115	    """Get current USD-conversion factors. {ccy → ccy/USD multiplier}.
   116	
   117	    M1/m1 audit fix: fail-fast — if FX 数据失败，**raise**，不 silently default to 1.0
   118	    (which made HKD/JPY/KRW market caps wildly wrong). Optionally reuse `prev_rates`.
   119	
   120	    Example: USDHKD=X close = 7.8 → 1 HKD = 1/7.8 USD.
   121	    """
   122	    rates: dict[str, float] = {"USD": 1.0}
   123	    symbols = [pair for pair in FX_PAIRS.values() if pair is not None]
   124	    try:
   125	        d = yf.download(symbols, period="5d", auto_adjust=True,
   126	                        progress=False, threads=True, group_by="ticker")
   127	    except Exception as e:
   128	        if prev_rates:
   129	            print(f"[fx] download failed: {e}; reusing previous rates")
   130	            return prev_rates
   131	        raise RuntimeError(f"FX fetch failed and no previous rates available: {e}")
   132	
   133	    if d.empty:
   134	        if prev_rates:
   135	            print("[fx] empty result; reusing previous rates")
   136	            return prev_rates
   137	        raise RuntimeError("FX fetch returned empty data")
   138	
   139	    missing: list[str] = []
   140	    for ccy, sym in FX_PAIRS.items():
   141	        if sym is None:
   142	            continue
   143	        try:
   144	            if isinstance(d.columns, pd.MultiIndex):
   145	                ser = d[(sym, "Close")].dropna()
   146	            else:
   147	                ser = d["Close"].dropna()
   148	            if ser.empty:
   149	                missing.append(ccy)
   150	                continue
   151	            last = float(ser.iloc[-1])
   152	            # USDXXX=X means how many XXX per 1 USD → invert
   153	            # XXXUSD=X means how many USD per 1 XXX → direct
   154	            if sym.startswith("USD"):
   155	                rates[ccy] = 1.0 / last
   156	            else:
   157	                rates[ccy] = last
   158	        except Exception as e:
   159	            missing.append(f"{ccy}({e})")
   160	
   161	    if missing:
   162	        if prev_rates:
   163	            print(f"[fx] missing pairs {missing}; backfilling from previous rates")
   164	            for ccy in missing:
   165	                base = ccy.split("(")[0]
   166	                if base in prev_rates:
   167	                    rates[base] = prev_rates[base]
   168	        else:
   169	            raise RuntimeError(f"FX missing pairs: {missing}")
   170	    print(f"[fx] rates → USD: { {k: round(v, 5) for k, v in rates.items()} }")
   171	    return rates
   172	
   173	
   174	def last_good_fx(conn: sqlite3.Connection) -> dict[str, float] | None:
   175	    """Recover the most recent FX snapshot from meta table."""
   176	    cur = conn.execute(
   177	        "SELECT value FROM meta WHERE key = 'last_fx_rates'"
   178	    ).fetchone()
   179	    if not cur:
   180	        return None
   181	    try:
   182	        import json
   183	        return json.loads(cur[0])
   184	    except Exception:
   185	        return None
   186	
   187	
   188	# ----- price batch fetch -----
   189	def fetch_prices_batch(tickers: list[str], start: str, end: str) -> dict[str, pd.DataFrame]:
   190	    """Return {ticker → DataFrame[Open, High, Low, Close, Volume]} indexed by date."""
   191	    out: dict[str, pd.DataFrame] = {}
   192	    # We always batch; yfinance handles single ticker in MultiIndex too with group_by='ticker'.
   193	    try:
   194	        d = yf.download(
   195	            tickers, start=start, end=end,
   196	            auto_adjust=False,   # keep both close and adj_close
   197	            progress=False, threads=True, group_by="ticker",
   198	        )
   199	    except Exception as e:
   200	        print(f"[prices] batch download failed: {e}")
   201	        return out
   202	
   203	    if d.empty:
   204	        return out
   205	
   206	    # Handle single-ticker DataFrame vs multi-ticker MultiIndex
   207	    if len(tickers) == 1:
   208	        t = tickers[0]
   209	        if isinstance(d.columns, pd.MultiIndex):
   210	            d.columns = d.columns.droplevel(1)
   211	        out[t] = d
   212	        return out
   213	
   214	    for t in tickers:
   215	        try:
   216	            if t in d.columns.get_level_values(0):
   217	                sub = d[t].dropna(how="all")
   218	                if not sub.empty:
   219	                    out[t] = sub
   220	        except Exception:
   221	            pass
   222	    return out
   223	
   224	
   225	def prices_to_rows(
   226	    ticker: str, df: pd.DataFrame, currency: str, fx_to_usd: float = 1.0
   227	) -> list[tuple]:
   228	    """Convert price DataFrame to upsert rows. Includes USD-converted close/adj_close."""
   229	    rows = []
   230	    for ts, r in df.iterrows():
   231	        d = ts.date().isoformat() if hasattr(ts, "date") else str(ts)[:10]
   232	        adj_raw = r.get("Adj Close")
   233	        close_raw = r.get("Close")
   234	        # Explicit NaN-safe fallback (NaN is truthy in `or`, so don't use `or`)
   235	        adj = _safe_float(adj_raw) if not pd.isna(adj_raw) else _safe_float(close_raw)
   236	        close = _safe_float(close_raw)
   237	        close_usd = close * fx_to_usd if close is not None else None
   238	        adj_usd = adj * fx_to_usd if adj is not None else None
   239	        rows.append((
   240	            ticker, d,
   241	            _safe_float(r.get("Open")),
   242	            _safe_float(r.get("High")),
   243	            _safe_float(r.get("Low")),
   244	            close,
   245	            adj,
   246	            _safe_int(r.get("Volume")),
   247	            currency,
   248	            close_usd,
   249	            adj_usd,
   250	        ))
   251	    return rows
   252	
   253	
   254	def _safe_float(v) -> float | None:
   255	    try:
   256	        if v is None or pd.isna(v):
   257	            return None
   258	        return float(v)
   259	    except Exception:
   260	        return None
   261	
   262	
   263	def _safe_int(v) -> int | None:
   264	    f = _safe_float(v)
   265	    return int(f) if f is not None else None
   266	
   267	
   268	# ----- multiples fetch (.info) -----
   269	def fetch_info_for(ticker: str) -> dict | None:
   270	    """Single-ticker .info fetch with exponential backoff + jitter (M4)."""
   271	    import random
   272	    for attempt in range(INFO_MAX_RETRY):
   273	        try:
   274	            t = yf.Ticker(ticker)
   275	            info = t.info or {}
   276	            if info and (info.get("marketCap") or info.get("regularMarketPrice")):
   277	                return info
   278	            # Sparse / no useful fields — treat as fail and retry
   279	        except Exception as e:
   280	            print(f"[info] {ticker} attempt {attempt + 1}/{INFO_MAX_RETRY} fail: {e}")

exec
/bin/zsh -lc 'python3 jobs/init_db.py && python3 jobs/load_universe.py' in /Users/gcc/invest-dashboard
 succeeded in 0ms:
[init_db] DB at: /Users/gcc/invest-dashboard/data/snapshots.db
[init_db] Tables: ['meta', 'multiples_daily', 'prices_daily', 'universe_member']
[load_universe] healthcare / biotech: 16 tickers
[load_universe] healthcare / hospital_care: 10 tickers
[load_universe] healthcare / hc_ai: 13 tickers
[load_universe] healthcare / managed_care: 10 tickers
[load_universe] healthcare / medtech: 13 tickers
[load_universe] healthcare / cxo: 14 tickers
[load_universe] healthcare / pharma: 16 tickers
[load_universe] healthcare / _coverage: 28 tickers

[load_universe] Total upserted: 120

[load_universe] universe_member rows by (domain, sector):
      healthcare / _coverage         28
      healthcare / biotech           16
      healthcare / cxo               14
      healthcare / hc_ai             13
      healthcare / hospital_care     10
      healthcare / managed_care      10
      healthcare / medtech           13
      healthcare / pharma            16

exec
/bin/zsh -lc "python3 - <<'PY'
import sqlite3, pandas as pd
from pathlib import Path
conn=sqlite3.connect('data/snapshots.db')
latest=pd.read_sql(\"select max(date) d from multiples_daily\", conn)['d'][0]
q='''with latest as (select * from multiples_daily where date=(select max(date) from multiples_daily)), sector_members as (select sector, ticker from universe_member where domain='healthcare' and sector"'!='"'_coverage'), vals as (select sm.sector, sm.ticker, l.forward_pe from sector_members sm left join latest l on l.ticker=sm.ticker), pos as (select * from vals where forward_pe > 0) select sector, count(*) n_pos, cast(count(*)*0.25 as real) threshold_count, group_concat(ticker || ':' || printf('%.1f', forward_pe), ', ') from (select sector,ticker,forward_pe, percent_rank() over(partition by sector order by forward_pe) pr from pos) group by sector order by sector;'''
print('latest', latest)
print(pd.read_sql(q, conn).to_string(index=False))
conn.close()
PY" in /Users/gcc/invest-dashboard
 succeeded in 305ms:
latest 2026-05-28
       sector  n_pos  threshold_count                                                                                                                 group_concat(ticker || ':' || printf('%.1f', forward_pe), ', ')
      biotech     13             3.25                                     BMRN:8.1, RPRX:9.6, 4587.T:9.9, INCY:10.7, REGN:11.7, BIIB:11.9, NBIX:12.3, GILD:13.9, GMAB:14.6, VRTX:20.4, ALNY:21.3, ARGX:22.3, ONC:31.4
          cxo     14             3.50                             ICLR:10.5, IQV:11.7, LH:13.3, CRL:13.4, TMO:16.7, A:17.7, DHR:19.0, WAT:20.8, MTD:21.3, LZAGY:21.8, MEDP:23.1, ILMN:25.3, 207940.KS:28.0, IDXX:33.4
        hc_ai     11             2.75                                                   IQV:11.7, CRM:11.8, DOCS:12.7, 6618.HK:13.5, VEEV:16.0, HQY:16.2, 2413.T:19.2, HIMS:19.6, OMCL:19.6, ISRG:35.5, 2506.HK:230.9
hospital_care     10             2.50                                                                            UHS:6.1, THC:10.2, OPCH:10.5, DVA:11.3, HCA:11.8, SEM:12.0, ACHC:13.9, EHC:15.9, CHE:16.3, ENSG:20.6
 managed_care     10             2.50                                                                                 UHS:6.1, CI:8.5, THC:10.2, CVS:11.0, HCA:11.8, CNC:13.2, ELV:13.4, UNH:18.4, MOH:19.4, HUM:19.8
      medtech     13             3.25                                      BDX:11.0, GEHC:11.9, MDT:12.5, 6869.T:13.0, BSX:13.4, ABT:14.1, ALC:16.7, RMD:16.9, SYK:18.3, 4543.T:23.7, EW:25.7, ISRG:35.5, 7747.T:46.0
       pharma     16             4.00 PFE:9.2, GSK:9.9, MRK:12.6, NVO:13.3, ABBV:13.3, AMGN:14.3, NVS:15.2, RHHBY:16.3, 4151.T:17.8, JNJ:18.2, 4568.T:18.7, AZN:23.1, LLY:24.4, 4519.T:32.9, 4502.T:36.6, 4506.T:87.5

exec
/bin/zsh -lc 'git status --short' in /Users/gcc/invest-dashboard
 succeeded in 0ms:
 M app/lib/charts.py
 D "app/pages/1_\360\237\217\245_Healthcare.py"
 D "app/pages/2_\360\237\224\245_Sector_Heatmap.py"
 D "app/pages/3_\360\237\222\216_CMSI_Coverage.py"
 M "app/pages/4_\360\237\247\254_Strategy_Picks.py"
 M "app/pages/5_\360\237\222\260_Valuation_Scanner.py"
 M app/streamlit_app.py
 M data/snapshots.db
?? app/lib/ui.py
?? "app/pages/1_\360\237\222\216_CMSI_Coverage.py"
?? "app/pages/2_\360\237\217\245_Healthcare.py"
?? "app/pages/3_\360\237\224\245_Sector_Heatmap.py"

exec
/bin/zsh -lc 'git diff -- data/snapshots.db --stat; git diff --name-only' in /Users/gcc/invest-dashboard
 succeeded in 0ms:
diff --git a/data/snapshots.db b/data/snapshots.db
index 0e87056..184b4a9 100644
Binary files a/data/snapshots.db and b/data/snapshots.db differ
app/lib/charts.py
"app/pages/1_\360\237\217\245_Healthcare.py"
"app/pages/2_\360\237\224\245_Sector_Heatmap.py"
"app/pages/3_\360\237\222\216_CMSI_Coverage.py"
"app/pages/4_\360\237\247\254_Strategy_Picks.py"
"app/pages/5_\360\237\222\260_Valuation_Scanner.py"
app/streamlit_app.py
data/snapshots.db

codex
Running the idempotent schema/universe check touched `data/snapshots.db`; I’ll avoid treating that as a finding and will exclude it from audit conclusions. The page renumbering/local edits appear unrelated to the three commits under review, so I’ll keep findings tied to D4/D5 behavior and call out where the working tree differs.
exec
/bin/zsh -lc 'find app/pages -maxdepth 1 -type f -print | sort | nl -ba' in /Users/gcc/invest-dashboard
 succeeded in 0ms:
     1	app/pages/1_💎_CMSI_Coverage.py
     2	app/pages/2_🏥_Healthcare.py
     3	app/pages/3_🔥_Sector_Heatmap.py
     4	app/pages/4_🧬_Strategy_Picks.py
     5	app/pages/5_💰_Valuation_Scanner.py

exec
/bin/zsh -lc "git diff -- app/streamlit_app.py | sed -n '1,180p'; git diff --name-status" in /Users/gcc/invest-dashboard
 succeeded in 0ms:
diff --git a/app/streamlit_app.py b/app/streamlit_app.py
index ae78866..01c4634 100644
--- a/app/streamlit_app.py
+++ b/app/streamlit_app.py
@@ -15,6 +15,7 @@ import streamlit as st
 from lib import benchmarks as bm
 from lib import db
 from lib import format as fmt
+from lib import ui
 
 st.set_page_config(
     page_title="invest-dashboard",
@@ -23,18 +24,9 @@ st.set_page_config(
     initial_sidebar_state="expanded",
 )
 
-# --- B4 audit: global ticker search ---
+# --- Unified sidebar search ---
 with st.sidebar:
-    st.subheader("🔍 Find ticker")
-    all_t = db.all_tickers()
-    pick = st.selectbox(
-        "Jump to ticker drill",
-        options=[""] + sorted(all_t),
-        format_func=lambda x: fmt.fmt_ticker_bbg(x) if x else "— select —",
-    )
-    if pick:
-        st.info(f"📍 Selected: **{fmt.fmt_ticker_bbg(pick)}** — Ticker Drill page coming D6.")
-        # st.switch_page("pages/6_🔍_Ticker_Drill.py")   # uncomment when D6 ships
+    ui.sidebar_search(key_prefix="home")
 
 # --- Header ---
 st.title("📊 Multi-Domain Investment Dashboard")
M	app/lib/charts.py
D	"app/pages/1_\360\237\217\245_Healthcare.py"
D	"app/pages/2_\360\237\224\245_Sector_Heatmap.py"
D	"app/pages/3_\360\237\222\216_CMSI_Coverage.py"
M	"app/pages/4_\360\237\247\254_Strategy_Picks.py"
M	"app/pages/5_\360\237\222\260_Valuation_Scanner.py"
M	app/streamlit_app.py

exec
/bin/zsh -lc 'git restore data/snapshots.db && git status --short' in /Users/gcc/invest-dashboard
 succeeded in 0ms:
 M app/lib/charts.py
 D "app/pages/1_\360\237\217\245_Healthcare.py"
 D "app/pages/2_\360\237\224\245_Sector_Heatmap.py"
 D "app/pages/3_\360\237\222\216_CMSI_Coverage.py"
 M "app/pages/4_\360\237\247\254_Strategy_Picks.py"
 M "app/pages/5_\360\237\222\260_Valuation_Scanner.py"
 M app/streamlit_app.py
?? app/lib/ui.py
?? "app/pages/1_\360\237\222\216_CMSI_Coverage.py"
?? "app/pages/2_\360\237\217\245_Healthcare.py"
?? "app/pages/3_\360\237\224\245_Sector_Heatmap.py"

exec
/bin/zsh -lc "nl -ba app/pages/5_💰_Valuation_Scanner.py | sed -n '112,170p'; nl -ba app/pages/4_🧬_Strategy_Picks.py | sed -n '64,135p'; nl -ba app/lib/charts.py | sed -n '60,118p'; nl -ba app/lib/strategy.py | sed -n '94,181p'" in /Users/gcc/invest-dashboard
 succeeded in 0ms:
   112	mults = db.latest_multiples(all_t)
   113	name_map = db.ticker_to_name(prefer_cn=True)
   114	
   115	# Merge
   116	merged = rets.copy() if not rets.empty else pd.DataFrame(index=list(all_t))
   117	if not mults.empty:
   118	    for c in ["market_cap_usd", "mcap_tier", "trailing_pe", "forward_pe",
   119	              "ev_ebitda", "ev_sales", "fcf_yield", "pb"]:
   120	        if c in mults.columns:
   121	            merged[c] = mults[c]
   122	
   123	# Sector-internal P/E percentile
   124	# For each ticker, compute its P/E rank within its first sector
   125	@st.cache_data(ttl=300)
   126	def sector_pe_percentile(_mults_df: pd.DataFrame, _sector_map: dict[str, list[str]], pe_col: str) -> pd.Series:
   127	    """For each ticker, rank P/E within its sector (excluding NaN and negative).
   128	    Returns percentile [0,100] where 0 = cheapest."""
   129	    result = {}
   130	    # Group tickers by sector
   131	    sector_tickers: dict[str, list[str]] = {}
   132	    for t, secs in _sector_map.items():
   133	        for s in secs:
   134	            sector_tickers.setdefault(s, []).append(t)
   135	
   136	    for sec, t_list in sector_tickers.items():
   137	        in_sec = _mults_df.loc[_mults_df.index.intersection(t_list), pe_col].copy()
   138	        # exclude non-positive (neg earnings) for percentile calc
   139	        in_sec = in_sec[in_sec > 0].dropna()
   140	        if in_sec.empty:
   141	            continue
   142	        ranks = in_sec.rank(pct=True) * 100
   143	        for t in t_list:
   144	            if t in ranks.index:
   145	                # Keep min percentile across sectors (cheapest sector ranking wins)
   146	                if t not in result or ranks[t] < result[t]:
   147	                    result[t] = float(ranks[t])
   148	    return pd.Series(result, name="pe_percentile")
   149	
   150	
   151	pe_pct = sector_pe_percentile(mults, all_tickers_by_sec, pe_metric)
   152	merged["pe_percentile"] = pe_pct
   153	
   154	# Apply filters
   155	candidates = merged.copy()
   156	candidates = candidates[candidates["market_cap_usd"] >= min_mcap_b * 1e9]
   157	candidates = candidates[candidates["pe_percentile"] <= pct_threshold]
   158	candidates = candidates[candidates["pe_percentile"].notna()]
   159	candidates = candidates[(candidates["ytd_%"] >= ytd_min) & (candidates["ytd_%"] <= ytd_max)]
   160	candidates = candidates[candidates["5d_%"] >= min_5d]
   161	
   162	# Sort by P/E percentile ascending (cheapest first)
   163	candidates = candidates.sort_values("pe_percentile", ascending=True)
   164	
   165	# --- Result summary ---
   166	col1, col2, col3, col4 = st.columns(4)
   167	col1.metric("🌐 Universe scanned", f"{len(all_t)}")
   168	col2.metric("✅ Candidates", f"{len(candidates)}")
   169	col3.metric("📐 Median Mcap (USD B)",
   170	            f"${candidates['market_cap_usd'].median()/1e9:.1f}B" if not candidates.empty else "—")
    64	    earliest = (pd.Timestamp(pick_date) - pd.Timedelta(days=10)).date().isoformat()
    65	    closes = strat.fetch_picks_closes(yf_syms + (bench_sym,), start=earliest)
    66	
    67	    if closes.empty:
    68	        st.error("Live price fetch failed. Check network/yfinance.")
    69	        return
    70	
    71	    # Separate benchmark
    72	    bench_close = closes[bench_sym] if bench_sym in closes.columns else pd.Series(dtype=float)
    73	    picks_closes = closes.drop(columns=[bench_sym], errors="ignore")
    74	
    75	    # --- Compute returns ---
    76	    normed, portfolio, perf = strat.compute_strategy_returns(picks_closes, pick_date)
    77	
    78	    # Benchmark norm to 100 at pick_date anchor
    79	    bench_norm = pd.Series(dtype=float)
    80	    if not bench_close.empty:
    81	        anchor_ts = pd.Timestamp(pick_date)
    82	        bench_sub = bench_close[bench_close.index >= anchor_ts].dropna()
    83	        if not bench_sub.empty:
    84	            bench_norm = (bench_sub / bench_sub.iloc[0]) * 100
    85	
    86	    # --- Summary metrics ---
    87	    if not portfolio.empty:
    88	        port_last = portfolio.iloc[-1] - 100
    89	        bench_last = (bench_norm.iloc[-1] - 100) if not bench_norm.empty else None
    90	        alpha = (port_last - bench_last) if bench_last is not None else None
    91	        c1, c2, c3 = st.columns(3)
    92	        c1.metric(
    93	            "📈 Portfolio since-inception",
    94	            f"{port_last:+.2f}%",
    95	            delta=None,
    96	        )
    97	        c2.metric(
    98	            f"📐 Benchmark ({bench_sym})",
    99	            f"{bench_last:+.2f}%" if bench_last is not None else "—",
   100	            delta=None,
   101	        )
   102	        c3.metric(
   103	            "🎯 Alpha (pp)",
   104	            f"{alpha:+.2f}pp" if alpha is not None else "—",
   105	            delta=f"{'outperform' if alpha and alpha > 0 else 'underperform' if alpha else 'tied'}",
   106	            delta_color="normal" if alpha and alpha > 0 else "inverse" if alpha else "off",
   107	        )
   108	
   109	    # --- Cumulative return chart ---
   110	    if not portfolio.empty:
   111	        # Build a 2-column DataFrame: portfolio + benchmark
   112	        chart_df = pd.DataFrame({"Portfolio (equal-weight)": portfolio})
   113	        if not bench_norm.empty:
   114	            chart_df[f"{bench_sym} (benchmark)"] = bench_norm
   115	        chart_df = chart_df.dropna(how="all")
   116	
   117	        fig = charts.cumulative_return_chart(
   118	            picks_closes[picks_closes.index >= pd.Timestamp(pick_date)],
   119	            title=f"{cfg['name']} — Indexed return since {pick_date}",
   120	            pick_date=pick_date,
   121	            show_individual=show_lines,
   122	        )
   123	        # Add benchmark overlay
   124	        import plotly.graph_objects as go
   125	        if not bench_norm.empty:
   126	            fig.add_trace(go.Scatter(
   127	                x=bench_norm.index, y=bench_norm.values,
   128	                mode="lines", name=f"{bench_sym} ({bench_name})",
   129	                line=dict(width=3, color="#a78bfa", dash="dash"),
   130	            ))
   131	        st.plotly_chart(fig, use_container_width=True)
   132	
   133	    # --- Top/Worst ranking table ---
   134	    if perf.empty:
   135	        st.warning("No per-ticker performance data.")
    60	    if closes.empty:
    61	        return go.Figure()
    62	    closes = closes.sort_index()
    63	    if pick_date:
    64	        anchor_ts = pd.Timestamp(pick_date)
    65	        closes = closes[closes.index >= anchor_ts]
    66	        if closes.empty:
    67	            return go.Figure()
    68	
    69	    base = closes.iloc[0]
    70	    norm = (closes / base) * 100
    71	    portfolio = norm.mean(axis=1)
    72	
    73	    fig = go.Figure()
    74	
    75	    # --- Dispersion Band (10th - 90th percentile) ---
    76	    p10 = norm.quantile(0.1, axis=1)
    77	    p90 = norm.quantile(0.9, axis=1)
    78	
    79	    fig.add_trace(go.Scatter(
    80	        x=p90.index.tolist() + p90.index[::-1].tolist(),
    81	        y=p90.values.tolist() + p10.values[::-1].tolist(),
    82	        fill="toself",
    83	        fillcolor="rgba(34, 197, 94, 0.15)",  # Translucent green
    84	        line=dict(color="rgba(255,255,255,0)"),
    85	        hoverinfo="skip",
    86	        showlegend=True,
    87	        name="10th–90th %ile Range",
    88	    ))
    89	
    90	    # --- Individual Lines (Optional) ---
    91	    if show_individual:
    92	        for col in norm.columns:
    93	            fig.add_trace(go.Scatter(
    94	                x=norm.index, y=norm[col],
    95	                mode="lines", name=col,
    96	                line=dict(width=1), opacity=0.25,
    97	                showlegend=False, hoverinfo="x+y+name",
    98	            ))
    99	
   100	    # --- Portfolio Line ---
   101	    fig.add_trace(go.Scatter(
   102	        x=portfolio.index, y=portfolio.values,
   103	        mode="lines", name="Equal-weight Portfolio",
   104	        line=dict(width=3, color=PRIMARY),
   105	    ))
   106	
   107	    fig.update_layout(
   108	        template=PLOT_TEMPLATE,
   109	        title=title,
   110	        yaxis_title="Indexed (start=100)",
   111	        height=450,
   112	        margin=dict(l=10, r=10, t=40, b=10),
   113	        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
   114	    )
   115	    return fig
    94	@st.cache_data(ttl=3600, show_spinner="Fetching picks prices…")
    95	def fetch_picks_closes(yf_syms: tuple[str, ...], start: str) -> pd.DataFrame:
    96	    """Wide-format close DataFrame for picks. Live yfinance, cached 1h."""
    97	    if not yf_syms:
    98	        return pd.DataFrame()
    99	    end = (date.today() + timedelta(days=1)).isoformat()
   100	    try:
   101	        d = yf.download(
   102	            list(yf_syms), start=start, end=end,
   103	            auto_adjust=True, progress=False, threads=True, group_by="ticker",
   104	        )
   105	    except Exception as e:
   106	        st.warning(f"Live fetch failed: {e}")
   107	        return pd.DataFrame()
   108	    if d.empty:
   109	        return pd.DataFrame()
   110	
   111	    if len(yf_syms) == 1:
   112	        sym = yf_syms[0]
   113	        if isinstance(d.columns, pd.MultiIndex):
   114	            d.columns = d.columns.droplevel(1)
   115	        if "Close" in d.columns:
   116	            return pd.DataFrame({sym: d["Close"]}).dropna(how="all")
   117	        return pd.DataFrame()
   118	
   119	    out = {}
   120	    for sym in yf_syms:
   121	        try:
   122	            if sym in d.columns.get_level_values(0):
   123	                out[sym] = d[sym]["Close"].dropna()
   124	        except Exception:
   125	            pass
   126	    return pd.DataFrame(out).sort_index()
   127	
   128	
   129	def compute_strategy_returns(
   130	    closes: pd.DataFrame, pick_date: str
   131	) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
   132	    """Compute since-inception cumulative return (indexed=100) for each ticker
   133	    + equal-weight portfolio + per-window returns table.
   134	
   135	    Returns:
   136	      - normed: wide DataFrame indexed=100 from pick_date
   137	      - portfolio: equal-weight portfolio cumulative (Series)
   138	      - perf_table: per-ticker returns for windows
   139	    """
   140	    if closes.empty:
   141	        return pd.DataFrame(), pd.Series(dtype=float), pd.DataFrame()
   142	    closes = closes.sort_index()
   143	    anchor_ts = pd.Timestamp(pick_date)
   144	    sub = closes[closes.index >= anchor_ts]
   145	    if sub.empty:
   146	        return pd.DataFrame(), pd.Series(dtype=float), pd.DataFrame()
   147	    base = sub.iloc[0]
   148	    normed = (sub / base) * 100
   149	    # Equal-weight portfolio: mean across tickers each day
   150	    portfolio = normed.mean(axis=1, skipna=True)
   151	
   152	    # Per-window returns
   153	    rows = []
   154	    NAN = float("nan")
   155	    for ticker in closes.columns:
   156	        ser = closes[ticker].dropna()
   157	        if ser.empty:
   158	            continue
   159	        last = float(ser.iloc[-1])
   160	        after_pick = ser[ser.index >= anchor_ts]
   161	        since = float((last / after_pick.iloc[0] - 1) * 100) if not after_pick.empty else NAN
   162	
   163	        def ret_back(n: int) -> float:
   164	            if len(ser) <= n:
   165	                return NAN
   166	            prev = ser.iloc[-n - 1]
   167	            if pd.isna(prev) or prev == 0:
   168	                return NAN
   169	            return float((last / prev - 1) * 100)
   170	
   171	        rows.append({
   172	            "Ticker": ticker,
   173	            "Last": last,
   174	            "1D %": ret_back(1),
   175	            "5D %": ret_back(5),
   176	            "15D %": ret_back(15),
   177	            "30D %": ret_back(30),
   178	            "Since %": since,
   179	        })
   180	    perf = pd.DataFrame(rows).set_index("Ticker") if rows else pd.DataFrame()
   181	    return normed, portfolio, perf

exec
/bin/zsh -lc "git show HEAD:app/pages/5_💰_Valuation_Scanner.py | nl -ba | sed -n '112,150p'; git show HEAD:app/lib/strategy.py | nl -ba | sed -n '94,181p'" in /Users/gcc/invest-dashboard
 succeeded in 0ms:
   112	# For each ticker, compute its P/E rank within its first sector
   113	@st.cache_data(ttl=300)
   114	def sector_pe_percentile(_mults_df: pd.DataFrame, _sector_map: dict[str, list[str]], pe_col: str) -> pd.Series:
   115	    """For each ticker, rank P/E within its sector (excluding NaN and negative).
   116	    Returns percentile [0,100] where 0 = cheapest."""
   117	    result = {}
   118	    # Group tickers by sector
   119	    sector_tickers: dict[str, list[str]] = {}
   120	    for t, secs in _sector_map.items():
   121	        for s in secs:
   122	            sector_tickers.setdefault(s, []).append(t)
   123	
   124	    for sec, t_list in sector_tickers.items():
   125	        in_sec = _mults_df.loc[_mults_df.index.intersection(t_list), pe_col].copy()
   126	        # exclude non-positive (neg earnings) for percentile calc
   127	        in_sec = in_sec[in_sec > 0].dropna()
   128	        if in_sec.empty:
   129	            continue
   130	        ranks = in_sec.rank(pct=True) * 100
   131	        for t in t_list:
   132	            if t in ranks.index:
   133	                # Keep min percentile across sectors (cheapest sector ranking wins)
   134	                if t not in result or ranks[t] < result[t]:
   135	                    result[t] = float(ranks[t])
   136	    return pd.Series(result, name="pe_percentile")
   137	
   138	
   139	pe_pct = sector_pe_percentile(mults, all_tickers_by_sec, pe_metric)
   140	merged["pe_percentile"] = pe_pct
   141	
   142	# Apply filters
   143	candidates = merged.copy()
   144	candidates = candidates[candidates["market_cap_usd"] >= min_mcap_b * 1e9]
   145	candidates = candidates[candidates["pe_percentile"] <= pct_threshold]
   146	candidates = candidates[candidates["pe_percentile"].notna()]
   147	candidates = candidates[(candidates["ytd_%"] >= ytd_min) & (candidates["ytd_%"] <= ytd_max)]
   148	candidates = candidates[candidates["5d_%"] >= min_5d]
   149	
   150	# Sort by P/E percentile ascending (cheapest first)
    94	@st.cache_data(ttl=3600, show_spinner="Fetching picks prices…")
    95	def fetch_picks_closes(yf_syms: tuple[str, ...], start: str) -> pd.DataFrame:
    96	    """Wide-format close DataFrame for picks. Live yfinance, cached 1h."""
    97	    if not yf_syms:
    98	        return pd.DataFrame()
    99	    end = (date.today() + timedelta(days=1)).isoformat()
   100	    try:
   101	        d = yf.download(
   102	            list(yf_syms), start=start, end=end,
   103	            auto_adjust=True, progress=False, threads=True, group_by="ticker",
   104	        )
   105	    except Exception as e:
   106	        st.warning(f"Live fetch failed: {e}")
   107	        return pd.DataFrame()
   108	    if d.empty:
   109	        return pd.DataFrame()
   110	
   111	    if len(yf_syms) == 1:
   112	        sym = yf_syms[0]
   113	        if isinstance(d.columns, pd.MultiIndex):
   114	            d.columns = d.columns.droplevel(1)
   115	        if "Close" in d.columns:
   116	            return pd.DataFrame({sym: d["Close"]}).dropna(how="all")
   117	        return pd.DataFrame()
   118	
   119	    out = {}
   120	    for sym in yf_syms:
   121	        try:
   122	            if sym in d.columns.get_level_values(0):
   123	                out[sym] = d[sym]["Close"].dropna()
   124	        except Exception:
   125	            pass
   126	    return pd.DataFrame(out).sort_index()
   127	
   128	
   129	def compute_strategy_returns(
   130	    closes: pd.DataFrame, pick_date: str
   131	) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
   132	    """Compute since-inception cumulative return (indexed=100) for each ticker
   133	    + equal-weight portfolio + per-window returns table.
   134	
   135	    Returns:
   136	      - normed: wide DataFrame indexed=100 from pick_date
   137	      - portfolio: equal-weight portfolio cumulative (Series)
   138	      - perf_table: per-ticker returns for windows
   139	    """
   140	    if closes.empty:
   141	        return pd.DataFrame(), pd.Series(dtype=float), pd.DataFrame()
   142	    closes = closes.sort_index()
   143	    anchor_ts = pd.Timestamp(pick_date)
   144	    sub = closes[closes.index >= anchor_ts]
   145	    if sub.empty:
   146	        return pd.DataFrame(), pd.Series(dtype=float), pd.DataFrame()
   147	    base = sub.iloc[0]
   148	    normed = (sub / base) * 100
   149	    # Equal-weight portfolio: mean across tickers each day
   150	    portfolio = normed.mean(axis=1, skipna=True)
   151	
   152	    # Per-window returns
   153	    rows = []
   154	    NAN = float("nan")
   155	    for ticker in closes.columns:
   156	        ser = closes[ticker].dropna()
   157	        if ser.empty:
   158	            continue
   159	        last = float(ser.iloc[-1])
   160	        after_pick = ser[ser.index >= anchor_ts]
   161	        since = float((last / after_pick.iloc[0] - 1) * 100) if not after_pick.empty else NAN
   162	
   163	        def ret_back(n: int) -> float:
   164	            if len(ser) <= n:
   165	                return NAN
   166	            prev = ser.iloc[-n - 1]
   167	            if pd.isna(prev) or prev == 0:
   168	                return NAN
   169	            return float((last / prev - 1) * 100)
   170	
   171	        rows.append({
   172	            "Ticker": ticker,
   173	            "Last": last,
   174	            "1D %": ret_back(1),
   175	            "5D %": ret_back(5),
   176	            "15D %": ret_back(15),
   177	            "30D %": ret_back(30),
   178	            "Since %": since,
   179	        })
   180	    perf = pd.DataFrame(rows).set_index("Ticker") if rows else pd.DataFrame()
   181	    return normed, portfolio, perf

exec
/bin/zsh -lc "git show HEAD:app/pages/3_💎_CMSI_Coverage.py | nl -ba | sed -n '26,132p'; git show HEAD:app/pages/2_🔥_Sector_Heatmap.py | nl -ba | sed -n '36,52p'" in /Users/gcc/invest-dashboard
 succeeded in 0ms:
    26	# --- Sidebar global search ---
    27	with st.sidebar:
    28	    st.subheader("🔍 Find ticker")
    29	    pick = st.selectbox(
    30	        "Jump to ticker drill",
    31	        options=[""] + sorted(db.all_tickers()),
    32	        format_func=lambda x: fmt.fmt_ticker_bbg(x) if x else "— select —",
    33	        key="cmsi_search",
    34	    )
    35	    if pick:
    36	        st.info(f"📍 {fmt.fmt_ticker_bbg(pick)} — Ticker Drill (D6) coming soon.")
    37	
    38	st.title("💎 CMSI Healthcare Coverage")
    39	st.caption("28 ticker official cover list — HK 15 / US 10 / CN A-share 3. Latest data: " + (db.latest_snapshot_date() or "—"))
    40	
    41	
    42	# --- Load CMSI Coverage tickers ---
    43	cmsi = db.sector_tickers("healthcare", "_coverage")
    44	if cmsi.empty:
    45	    st.warning("No CMSI coverage data — check config/universes/cmsi_coverage_hc.yml")
    46	    st.stop()
    47	
    48	tickers = tuple(cmsi["ticker"].tolist())
    49	
    50	# --- Compute returns + multiples for all CMSI tickers ---
    51	closes = db.get_close_series_usd(tickers)
    52	rets = db.compute_returns(closes)
    53	mults = db.latest_multiples(tickers)
    54	
    55	# --- Find cross-sector membership ---
    56	# Query all sectors each ticker belongs to (excluding _coverage)
    57	@st.cache_data(ttl=300)
    58	def cross_membership(_tickers: tuple[str, ...]) -> dict[str, list[str]]:
    59	    placeholders = ",".join("?" * len(_tickers))
    60	    df = db.query(
    61	        f"SELECT ticker, sector FROM universe_member "
    62	        f"WHERE ticker IN ({placeholders}) AND sector != '_coverage' "
    63	        f"ORDER BY ticker, sector",
    64	        tuple(_tickers),
    65	    )
    66	    out: dict[str, list[str]] = {}
    67	    for _, row in df.iterrows():
    68	        out.setdefault(row["ticker"], []).append(row["sector"])
    69	    return out
    70	
    71	
    72	cross = cross_membership(tickers)
    73	
    74	# --- Merge into display DataFrame ---
    75	merged = rets.copy() if not rets.empty else pd.DataFrame(index=list(tickers))
    76	merged["name_cn"] = cmsi.set_index("ticker")["name_cn"]
    77	merged["name_en"] = cmsi.set_index("ticker")["name_en"]
    78	merged["region"] = cmsi.set_index("ticker")["region"]
    79	merged["BBG"] = [fmt.fmt_ticker_bbg(t) for t in merged.index]
    80	if not mults.empty:
    81	    for c in ["market_cap_usd", "mcap_tier", "trailing_pe", "forward_pe",
    82	              "ev_ebitda", "ev_sales", "fcf_yield", "pb"]:
    83	        if c in mults.columns:
    84	            merged[c] = mults[c]
    85	
    86	# Cross-sector tags: convert to icons
    87	def _cross_tag(ticker: str) -> str:
    88	    sectors = cross.get(ticker, [])
    89	    if not sectors:
    90	        return ""
    91	    # 简短 emoji mapping
    92	    icons = {
    93	        "biotech": "🧬", "pharma": "💊", "hc_ai": "🤖",
    94	        "medtech": "⚕️", "hospital_care": "🏥",
    95	        "managed_care": "🩺", "cxo": "🧪",
    96	    }
    97	    return " ".join(icons.get(s, f"[{s}]") for s in sectors)
    98	
    99	
   100	merged["Cross-Sector"] = [_cross_tag(t) for t in merged.index]
   101	
   102	# --- Default sort: mcap desc (M10 audit) ---
   103	merged = merged.sort_values("market_cap_usd", ascending=False, na_position="last")
   104	
   105	# --- Region tabs ---
   106	regions = ["HK", "US", "CN", "All"]
   107	tabs = st.tabs([f"{r} ({sum(merged['region']==r) if r != 'All' else len(merged)})" for r in regions])
   108	
   109	
   110	def render_region(df: pd.DataFrame) -> None:
   111	    if df.empty:
   112	        st.info("No tickers in this region.")
   113	        return
   114	
   115	    # Build display string DataFrame (M7 audit pattern)
   116	    disp = pd.DataFrame(index=df.index)
   117	    disp["BBG"] = df["BBG"]
   118	    disp["Name (CN)"] = df["name_cn"].fillna("—")
   119	    disp["Name (EN)"] = df["name_en"].fillna("—")
   120	    disp["Region"] = df["region"]
   121	    disp["Tier"] = df.get("mcap_tier", pd.Series(index=df.index)).fillna("—")
   122	    disp["Cross"] = df["Cross-Sector"]
   123	    disp["Mcap USD"] = df["market_cap_usd"].apply(fmt.fmt_money_b)
   124	    disp["YTD %"] = df["ytd_%"].apply(fmt.fmt_pct)
   125	    disp["1M %"] = df["1m_%"].apply(fmt.fmt_pct)
   126	    disp["5D %"] = df["5d_%"].apply(fmt.fmt_pct)
   127	    disp["1D %"] = df["1d_%"].apply(fmt.fmt_pct)
   128	    disp["Trail P/E"] = df["trailing_pe"].apply(fmt.fmt_ratio)
   129	    disp["Fwd P/E"] = df["forward_pe"].apply(fmt.fmt_ratio)
   130	    disp["EV/EBITDA"] = df["ev_ebitda"].apply(fmt.fmt_ratio)
   131	    disp["FCF Yld"] = df["fcf_yield"].apply(fmt.fmt_pct_decimal)
   132	    disp["P/B"] = df["pb"].apply(fmt.fmt_ratio)
    36	st.title("🔥 Sector Heatmap")
    37	st.caption("Cross-sectional snapshot per sector. Multiples from yfinance — trailing + 12M forward only.")
    38	
    39	# --- Sidebar filter (M11 audit) ---
    40	with st.sidebar:
    41	    st.subheader("Filter")
    42	    min_mcap_b = st.slider(
    43	        "Min market cap (USD B)", 0.0, 50.0, 0.0, 0.5,
    44	        help="过滤掉小市值标的避免均值扭曲（GLM audit M11: 4587.T $904M 拉低 biotech 均值）"
    45	    )
    46	    sort_col = st.selectbox(
    47	        "Sort by",
    48	        ["Mcap USD", "YTD %", "1M %", "Trail P/E", "Fwd P/E"],
    49	        index=0,
    50	        help="默认按市值降序（M10 audit: 中文卖方习惯）"
    51	    )
    52	

exec
/bin/zsh -lc "nl -ba app/pages/1_💎_CMSI_Coverage.py | sed -n '1,80p'; nl -ba app/pages/2_🏥_Healthcare.py | sed -n '1,80p'; nl -ba app/pages/3_🔥_Sector_Heatmap.py | sed -n '1,80p'" in /Users/gcc/invest-dashboard
 succeeded in 0ms:
     1	"""CMSI Coverage — 28 ticker cover list with full multiples + cross-sector tags.
     2	
     3	D5 implementation:
     4	- Region tabs (HK / US / CN-A)
     5	- Per region: full table with multiples + return windows + cross-sector membership
     6	- Defaults: name_cn first, mcap desc (M10 audit)
     7	"""
     8	
     9	from __future__ import annotations
    10	
    11	from pathlib import Path
    12	
    13	import pandas as pd
    14	import streamlit as st
    15	import yaml
    16	
    17	from lib import db
    18	from lib import format as fmt
    19	from lib import ui
    20	
    21	st.set_page_config(
    22	    page_title="CMSI Coverage · invest-dashboard",
    23	    page_icon="💎",
    24	    layout="wide",
    25	)
    26	
    27	# --- Sidebar global search ---
    28	with st.sidebar:
    29	    ui.sidebar_search(key_prefix="cmsi")
    30	
    31	st.title("💎 CMSI Healthcare Coverage")
    32	st.caption("28 ticker official cover list — HK 15 / US 10 / CN A-share 3. Latest data: " + (db.latest_snapshot_date() or "—"))
    33	
    34	
    35	# --- Load CMSI Coverage tickers ---
    36	cmsi = db.sector_tickers("healthcare", "_coverage")
    37	if cmsi.empty:
    38	    st.warning("No CMSI coverage data — check config/universes/cmsi_coverage_hc.yml")
    39	    st.stop()
    40	
    41	tickers = tuple(cmsi["ticker"].tolist())
    42	
    43	# --- Compute returns + multiples for all CMSI tickers ---
    44	closes = db.get_close_series_usd(tickers)
    45	rets = db.compute_returns(closes)
    46	mults = db.latest_multiples(tickers)
    47	
    48	# --- Find cross-sector membership ---
    49	# Query all sectors each ticker belongs to (excluding _coverage)
    50	@st.cache_data(ttl=300)
    51	def cross_membership(_tickers: tuple[str, ...]) -> dict[str, list[str]]:
    52	    placeholders = ",".join("?" * len(_tickers))
    53	    df = db.query(
    54	        f"SELECT ticker, sector FROM universe_member "
    55	        f"WHERE ticker IN ({placeholders}) AND sector != '_coverage' "
    56	        f"ORDER BY ticker, sector",
    57	        tuple(_tickers),
    58	    )
    59	    out: dict[str, list[str]] = {}
    60	    for _, row in df.iterrows():
    61	        out.setdefault(row["ticker"], []).append(row["sector"])
    62	    return out
    63	
    64	
    65	cross = cross_membership(tickers)
    66	
    67	# --- Merge into display DataFrame ---
    68	merged = rets.copy() if not rets.empty else pd.DataFrame(index=list(tickers))
    69	merged["name_cn"] = cmsi.set_index("ticker")["name_cn"]
    70	merged["name_en"] = cmsi.set_index("ticker")["name_en"]
    71	merged["region"] = cmsi.set_index("ticker")["region"]
    72	merged["BBG"] = [fmt.fmt_ticker_bbg(t) for t in merged.index]
    73	if not mults.empty:
    74	    for c in ["market_cap_usd", "mcap_tier", "trailing_pe", "forward_pe",
    75	              "ev_ebitda", "ev_sales", "fcf_yield", "pb"]:
    76	        if c in mults.columns:
    77	            merged[c] = mults[c]
    78	
    79	# Cross-sector tags: convert to icons
    80	def _cross_tag(ticker: str) -> str:
     1	"""Healthcare domain overview — 7 sub-sectors summary."""
     2	
     3	from __future__ import annotations
     4	
     5	import pandas as pd
     6	import streamlit as st
     7	import yaml
     8	from pathlib import Path
     9	
    10	from lib import benchmarks as bm
    11	from lib import db
    12	from lib import format as fmt
    13	
    14	
    15	def _render_pct_table(df: pd.DataFrame, pct_cols: list[str], num_cols: list[str] | None = None) -> None:
    16	    """Pre-format strings + Styler color-only (M7 audit fix)."""
    17	    display_str = pd.DataFrame(index=df.index)
    18	    for c in df.columns:
    19	        if c in pct_cols:
    20	            display_str[c] = df[c].apply(fmt.fmt_pct)
    21	        elif num_cols and c in num_cols:
    22	            display_str[c] = df[c].apply(fmt.fmt_num)
    23	        else:
    24	            display_str[c] = df[c]
    25	    styler = display_str.style
    26	    for c in pct_cols:
    27	        styler = styler.apply(
    28	            lambda _s, n=df[c]: fmt.background_gradient_diverging(n),
    29	            subset=[c],
    30	        )
    31	    st.dataframe(styler, use_container_width=True)
    32	
    33	st.set_page_config(page_title="Healthcare · invest-dashboard", page_icon="🏥", layout="wide")
    34	
    35	REPO_ROOT = Path(__file__).resolve().parent.parent.parent
    36	DOMAIN_CFG = REPO_ROOT / "config" / "domains" / "healthcare.yml"
    37	
    38	
    39	@st.cache_data(ttl=600)
    40	def load_domain_cfg() -> dict:
    41	    with DOMAIN_CFG.open() as f:
    42	        return yaml.safe_load(f)
    43	
    44	
    45	cfg = load_domain_cfg()
    46	st.title(f"{cfg.get('emoji', '🏥')} {cfg['name']}")
    47	st.caption(cfg.get("description", "").strip())
    48	
    49	# --- 7 sector aggregate summary ---
    50	st.subheader("📊 Sector summary (mean returns per sector)")
    51	
    52	rows = []
    53	all_returns_by_sector: dict[str, pd.DataFrame] = {}
    54	for sec in cfg["sectors"]:
    55	    uni = db.sector_tickers("healthcare", sec["id"])
    56	    tickers = tuple(uni["ticker"].tolist())
    57	    if not tickers:
    58	        continue
    59	    closes = db.get_close_series_usd(tickers)   # M1 audit: USD-converted
    60	    rets = db.compute_returns(closes)
    61	    if rets.empty:
    62	        continue
    63	    all_returns_by_sector[sec["id"]] = rets
    64	    rows.append({
    65	        "Sector": sec["name"],
    66	        "Tickers": len(tickers),
    67	        "1D % avg": rets["1d_%"].mean(),
    68	        "5D % avg": rets["5d_%"].mean(),
    69	        "1M % avg": rets["1m_%"].mean(),
    70	        "YTD % avg": rets["ytd_%"].mean(),
    71	        "Benchmark": sec.get("benchmark", "—"),
    72	    })
    73	
    74	if not rows:
    75	    st.warning("No sector data — backfill needed.")
    76	else:
    77	    summary = pd.DataFrame(rows).set_index("Sector")
    78	    pct_cols = ["1D % avg", "5D % avg", "1M % avg", "YTD % avg"]
    79	    _render_pct_table(summary, pct_cols=pct_cols)
    80	
     1	"""Sector Heatmap — multiples + returns per sector with color gradient.
     2	
     3	Audit fixes applied:
     4	- M7: pre-format string DataFrame for display; Styler computes background from numeric.
     5	- M8: st.tabs instead of dropdown (analyst can piano-key through 7 sectors).
     6	- M10: default sort by market cap desc; name_cn priority (中文卖方习惯).
     7	- M1: use USD-converted close series for fair cross-region return comparison.
     8	- M11: mcap_tier shown as badge; sidebar min-mcap filter.
     9	"""
    10	
    11	from __future__ import annotations
    12	
    13	from pathlib import Path
    14	
    15	import pandas as pd
    16	import streamlit as st
    17	import yaml
    18	
    19	from lib import db
    20	from lib import format as fmt
    21	
    22	st.set_page_config(page_title="Sector Heatmap · invest-dashboard", page_icon="🔥", layout="wide")
    23	
    24	REPO_ROOT = Path(__file__).resolve().parent.parent.parent
    25	DOMAIN_CFG = REPO_ROOT / "config" / "domains" / "healthcare.yml"
    26	
    27	
    28	@st.cache_data(ttl=600)
    29	def load_domain_cfg() -> dict:
    30	    with DOMAIN_CFG.open() as f:
    31	        return yaml.safe_load(f)
    32	
    33	
    34	cfg = load_domain_cfg()
    35	
    36	st.title("🔥 Sector Heatmap")
    37	st.caption("Cross-sectional snapshot per sector. Multiples from yfinance — trailing + 12M forward only.")
    38	
    39	# --- Sidebar filter (M11 audit) ---
    40	with st.sidebar:
    41	    st.subheader("Filter")
    42	    min_mcap_b = st.slider(
    43	        "Min market cap (USD B)", 0.0, 50.0, 0.0, 0.5,
    44	        help="过滤掉小市值标的避免均值扭曲（GLM audit M11: 4587.T $904M 拉低 biotech 均值）"
    45	    )
    46	    sort_col = st.selectbox(
    47	        "Sort by",
    48	        ["Mcap USD", "YTD %", "1M %", "Trail P/E", "Fwd P/E"],
    49	        index=0,
    50	        help="默认按市值降序（M10 audit: 中文卖方习惯）"
    51	    )
    52	
    53	
    54	def render_sector(sec: dict) -> None:
    55	    uni = db.sector_tickers("healthcare", sec["id"])
    56	    tickers = tuple(uni["ticker"].tolist())
    57	    if not tickers:
    58	        st.warning(f"No tickers in sector {sec['name']}")
    59	        return
    60	
    61	    # M1: use USD-converted close series
    62	    closes = db.get_close_series_usd(tickers)
    63	    rets = db.compute_returns(closes)
    64	    mults = db.latest_multiples(tickers)
    65	    name_map = db.ticker_to_name(prefer_cn=True)   # M10 audit
    66	    region_map = uni.set_index("ticker")["region"].to_dict()
    67	
    68	    # --- Merge numeric DataFrame (for gradient calc) ---
    69	    merged = rets.copy() if not rets.empty else pd.DataFrame(index=list(tickers))
    70	    if not mults.empty:
    71	        for col in ["market_cap_usd", "mcap_tier", "trailing_pe", "forward_pe",
    72	                    "ev_ebitda", "ev_sales", "fcf_yield", "pb"]:
    73	            if col in mults.columns:
    74	                merged[col] = mults[col]
    75	    merged["Name"] = pd.Series(name_map).reindex(merged.index)
    76	    merged["Region"] = pd.Series(region_map).reindex(merged.index)
    77	    merged["Ticker_bbg"] = [fmt.fmt_ticker_bbg(t) for t in merged.index]   # n2 audit
    78	
    79	    # M11 audit: filter by min_mcap (in B)
    80	    if min_mcap_b > 0:

exec
/bin/zsh -lc "rg -n \"ui\\.sidebar_search|Find ticker|Jump to ticker drill\" app/streamlit_app.py app/pages app/lib/ui.py -S" in /Users/gcc/invest-dashboard
 succeeded in 0ms:
app/pages/5_💰_Valuation_Scanner.py:42:    ui.sidebar_search(key_prefix="scanner")
app/lib/ui.py:11:    st.subheader("🔍 Find ticker")
app/lib/ui.py:26:        "Jump to ticker drill",
app/streamlit_app.py:29:    ui.sidebar_search(key_prefix="home")
app/pages/1_💎_CMSI_Coverage.py:29:    ui.sidebar_search(key_prefix="cmsi")
app/pages/4_🧬_Strategy_Picks.py:29:    ui.sidebar_search(key_prefix="strategy")

exec
/bin/zsh -lc "nl -ba app/pages/4_🧬_Strategy_Picks.py | sed -n '214,235p'; git show HEAD:app/pages/4_🧬_Strategy_Picks.py | nl -ba | sed -n '203,218p'" in /Users/gcc/invest-dashboard
 succeeded in 0ms:
   214	- **Worst 5**: 累计回报最低的 5 只票（Worst first）。
   215	""")
   216	
   217	
   218	# --- M8 audit: tabs > dropdown ---
   219	strategy_tabs = st.tabs([strat.STRATEGIES[sid]["name"] for sid in strat.STRATEGIES])
   220	for tab, sid in zip(strategy_tabs, strat.STRATEGIES.keys()):
   221	    with tab:
   222	        render_strategy(sid)
   223	
   224	st.divider()
   225	st.caption(
   226	    "📊 **Methodology**: Equal-weight portfolio cumulative return from pick date. "
   227	    "All prices via yfinance (auto-adjusted for splits/dividends). "
   228	    "Benchmark: XBI for biotech, 3110.HK for HK 高股息."
   229	)
   230	st.caption(
   231	    "Picks source: v4/v5 from `data/external/picks.db` + `v4_picks.csv` · HK 高股息 from `hd_picks.csv` · "
   232	    "Sync via `cp ~/ic-foundry/ledger.db data/external/picks.db && git add && git commit` weekly."
   233	)
   203	# --- M8 audit: tabs > dropdown ---
   204	strategy_tabs = st.tabs([strat.STRATEGIES[sid]["name"] for sid in strat.STRATEGIES])
   205	for tab, sid in zip(strategy_tabs, strat.STRATEGIES.keys()):
   206	    with tab:
   207	        render_strategy(sid)
   208	
   209	st.divider()
   210	st.caption(
   211	    "📊 **Methodology**: Equal-weight portfolio cumulative return from pick date. "
   212	    "All prices via yfinance (auto-adjusted for splits/dividends). "
   213	    "Benchmark: XBI for biotech, 3110.HK for HK 高股息."
   214	)
   215	st.caption(
   216	    "Picks source: v4/v5 from `data/external/picks.db` + `v4_picks.csv` · HK 高股息 from `hd_picks.csv` · "
   217	    "Sync via `cp ~/ic-foundry/ledger.db data/external/picks.db && git add && git commit` weekly."
   218	)

exec
/bin/zsh -lc "nl -ba app/pages/5_💰_Valuation_Scanner.py | sed -n '216,255p'; git show HEAD:app/pages/5_💰_Valuation_Scanner.py | nl -ba | sed -n '216,242p'" in /Users/gcc/invest-dashboard
 succeeded in 0ms:
   216	        candidates["fcf_yield"], low_color="#dc2626", high_color="#16a34a"
   217	    ),
   218	    subset=["FCF Yld"],
   219	)
   220	# Sector P/E percentile column — low percentile = cheap = green
   221	styler = styler.apply(
   222	    lambda _s: fmt.background_gradient_low_good(candidates["pe_percentile"]),
   223	    subset=["Sector P/E %ile"],
   224	)
   225	
   226	st.dataframe(styler, use_container_width=True, height=560)
   227	
   228	# --- Interpretation hints ---
   229	ui.onboarding_expander("Valuation Scanner", """
   230	**Sector P/E %ile**：当前股票的 forward (or trailing) P/E 在所属板块内的分位。
   231	- `0%-25%` = cheapest quartile within sector
   232	- 一般 sell-side framework: 看 cheap multiple + 正面 momentum 一起 → 可能 re-rating 候选
   233	
   234	**YTD %**: 年至今总回报。负 YTD + 低 P/E 可能是 "fallen angel" 候选。
   235	正 YTD + 低 P/E 可能是 "value with momentum"。
   236	
   237	**5D %**: 最近 5 个交易日 momentum。Filter 默认 ≥ -10% 排除崩盘中候选。
   238	
   239	**EV/EBITDA**: complementary multiple，避免单看 P/E 误判（EPS 被一次性项目影响）。
   240	
   241	**FCF Yield**: free cash flow / market cap. 高 = 现金生成能力强 = 好。
   242	
   243	**Presets**:
   244	- **Deep Value**: 寻找板块内极低估 (15%ile) 的大市值标的。
   245	- **Recovery**: 寻找已经开始从底部回升 (5D % > 5%) 的低估标的。
   246	""")
   247	
   248	st.divider()
   249	st.caption(
   250	    "🎯 **Methodology**: Cross-sectional within selected sectors. Negative P/E excluded from percentile rank. "
   251	    "Latest snapshot: " + (db.latest_snapshot_date() or "—") + ". "
   252	    "Sector membership: many-to-many (ISRG ∈ hc_ai + medtech 等)."
   253	)
   216	with st.expander("📖 How to read this scan"):
   217	    st.markdown("""
   218	**Sector P/E %ile**：当前股票的 forward (or trailing) P/E 在所属板块内的分位。
   219	- `0%-25%` = cheapest quartile within sector
   220	- 一般 sell-side framework: 看 cheap multiple + 正面 momentum 一起 → 可能 re-rating 候选
   221	
   222	**YTD %**: 年至今总回报。负 YTD + 低 P/E 可能是 "fallen angel" 候选。
   223	正 YTD + 低 P/E 可能是 "value with momentum"。
   224	
   225	**5D %**: 最近 5 个交易日 momentum。Filter 默认 ≥ -10% 排除崩盘中候选。
   226	
   227	**EV/EBITDA**: complementary multiple，避免单看 P/E 误判（EPS 被一次性项目影响）。
   228	
   229	**FCF Yield**: free cash flow / market cap. 高 = 现金生成能力强 = 好。
   230	
   231	**注意**：
   232	- 板块 P/E 中位数受小市值标的扭曲 (4587 JP 在 Biotech 拉低均值)，min mcap filter 可缓解
   233	- 负 P/E (亏损) 不参与 percentile rank（排除 biotech 烧钱期标的）
   234	- Multi-sector ticker (e.g. ISRG ∈ hc_ai + medtech) 用最 cheap 的板块 percentile
   235	""")
   236	
   237	st.divider()
   238	st.caption(
   239	    "🎯 **Methodology**: Cross-sectional within selected sectors. Negative P/E excluded from percentile rank. "
   240	    "Latest snapshot: " + (db.latest_snapshot_date() or "—") + ". "
   241	    "Sector membership: many-to-many (ISRG ∈ hc_ai + medtech 等)."
   242	)

exec
/bin/zsh -lc "test -f Makefile && nl -ba Makefile | sed -n '1,160p' || echo 'no Makefile'; rg -n \"sync-ledger|picks.db|ledger.db\" -S ." in /Users/gcc/invest-dashboard
 succeeded in 0ms:
no Makefile
./app/pages/4_🧬_Strategy_Picks.py:6:- Data: data/external/picks.db (v5) + data/external/v4_picks.csv + data/external/hd_picks.csv
./app/pages/4_🧬_Strategy_Picks.py:37:    "Data source: ic-foundry ledger.db + scoring Excel, picks fetched live via yfinance."
./app/pages/4_🧬_Strategy_Picks.py:231:    "Picks source: v4/v5 from `data/external/picks.db` + `v4_picks.csv` · HK 高股息 from `hd_picks.csv` · "
./app/pages/4_🧬_Strategy_Picks.py:232:    "Sync via `cp ~/ic-foundry/ledger.db data/external/picks.db && git add && git commit` weekly."
./README.md:18:| Picks 数据 | 复用 `~/ic-foundry/ledger.db`，sync 进 `data/external/` |
./README.md:92:`ic-foundry/ledger.db` lives in `~/ic-foundry/` on George's Mac — **NOT accessible**
./README.md:95:- **Scheme A** (recommended): `cp ~/ic-foundry/ledger.db data/external/picks.db` and commit periodically
./README.md:99:Default: Scheme A — sync via `make sync-ledger`.
./app/lib/strategy.py:5:- v5 biotech (2026-05-15, 40 picks, XBI benchmark)   — picks.db (catalyst-monitor)
./app/lib/strategy.py:24:PICKS_DB = DATA_EXT / "picks.db"
./app/lib/strategy.py:38:    """v5 biotech: from picks.db, source_skill='catalyst-monitor'."""
./app/lib/strategy.py:39:    if not PICKS_DB.exists():
./app/lib/strategy.py:41:    conn = sqlite3.connect(f"file:{PICKS_DB}?mode=ro", uri=True)

exec
/bin/zsh -lc "git ls-files data/external/picks.db-wal data/external/picks.db-shm data/external/picks.db; nl -ba .gitignore | sed -n '1,40p'; nl -ba README.md | sed -n '90,100p'" in /Users/gcc/invest-dashboard
 succeeded in 0ms:
data/external/picks.db
data/external/picks.db-shm
data/external/picks.db-wal
     1	# Python
     2	__pycache__/
     3	*.py[cod]
     4	*.egg-info/
     5	.venv/
     6	venv/
     7	.pytest_cache/
     8	
     9	# IDE
    10	.vscode/
    11	.idea/
    12	.DS_Store
    13	
    14	# Streamlit secrets (keep local, not commit)
    15	.streamlit/secrets.toml
    16	
    17	# logs / scratch
    18	*.log
    19	.scratch/
    20	tmp/
    21	
    22	# uv
    23	.uv-cache/
    24	
    25	# OMC plugin auto-state (do not commit)
    26	.omc/
    27	.claude/
    90	### Data path for D4 Strategy Picks (B1 audit)
    91	
    92	`ic-foundry/ledger.db` lives in `~/ic-foundry/` on George's Mac — **NOT accessible**
    93	from Streamlit Cloud. For D4 deployment:
    94	
    95	- **Scheme A** (recommended): `cp ~/ic-foundry/ledger.db data/external/picks.db` and commit periodically
    96	- **Scheme B**: extract picks_v2 to a derived JSON in repo (less sensitive than raw ledger)
    97	- **Scheme C**: external DB via Streamlit secrets (Turso / Supabase)
    98	
    99	Default: Scheme A — sync via `make sync-ledger`.
   100	

codex
Second-round audit result: no code changes made. I found one deploy-level blocker and several major correctness/operational risks.

**Findings**

[BLOCKER] Raw `picks.db` is committed to a public repo, but D4 only needs a small derived extract.
[file](/Users/gcc/invest-dashboard/app/lib/strategy.py:43) reads only `ticker`, `price_at_decision`, and `date_added` from `picks_v2`, but the committed SQLite file also contains extra tables (`calibration_alerts`, `schema_meta`, `universe_snapshots_index`). For a public repo, replace [picks.db](/Users/gcc/invest-dashboard/data/external/picks.db) with a derived CSV/JSON/minimal SQLite export. If any data is sensitive, removing the file in a future commit is not enough; purge repo history.

[MAJOR] D4 portfolio return math is not aligned with `weekly_perf.py`.
[file](/Users/gcc/invest-dashboard/app/lib/strategy.py:147) anchors every ticker to the first global row after pick date, then [line 150](/Users/gcc/invest-dashboard/app/lib/strategy.py:150) averages available normalized series with `skipna=True`. `weekly_perf.py` computes per-ticker since returns and then averages those returns. These match only if every ticker has the same first and latest valid date. Action: either report `perf["Since %"].mean()` for email parity, or explicitly document the page as a daily equal-weight equity curve with different semantics.

[MAJOR] Missing prices are currently dropped from portfolio weight.
[file](/Users/gcc/invest-dashboard/app/lib/strategy.py:150) means a halted/missing ticker is removed from that day’s average. That can overstate returns if missing names are weak. For an equal-weight equity curve, carry forward each constituent after its first valid price (`ffill`) and show constituent coverage by date; for strict data quality, mark the portfolio NaN when coverage is incomplete.

[MAJOR] Chart and metric can diverge after future fixes.
[file](/Users/gcc/invest-dashboard/app/pages/4_🧬_Strategy_Picks.py:76) computes `portfolio`, but [charts.py](/Users/gcc/invest-dashboard/app/lib/charts.py:69) recomputes `base`, `norm`, and [portfolio](/Users/gcc/invest-dashboard/app/lib/charts.py:71). Once return logic is fixed in one place, the other can silently disagree. Action: pass `normed`/`portfolio` into the chart instead of recomputing.

[MAJOR] D4 cold load fetches all strategy tabs, not only the visible tab.
[file](/Users/gcc/invest-dashboard/app/pages/4_🧬_Strategy_Picks.py:219) creates tabs, then [line 222](/Users/gcc/invest-dashboard/app/pages/4_🧬_Strategy_Picks.py:222) renders every strategy, each calling [live yfinance](/Users/gcc/invest-dashboard/app/pages/4_🧬_Strategy_Picks.py:65). Memory is fine for ~100 tickers x ~200 daily closes, but Streamlit Cloud sleep/wake will invalidate cache and make the first page load slow/unreliable. Action: precompute closes into `snapshots.db` or lazy-select one strategy.

[MAJOR] `picks.db` sync is documented but not implemented.
[README](/Users/gcc/invest-dashboard/README.md:95) says copy and commit periodically, and [line 99](/Users/gcc/invest-dashboard/README.md:99) references `make sync-ledger`, but there is no `Makefile`. The GitHub cron only commits [snapshots.db](/Users/gcc/invest-dashboard/.github/workflows/fetch_eod.yml:50). Action: add a real sync script/Make target and preferably export a minimal derived artifact.

[MAJOR] B4 “global search on every page” is still incomplete in committed pages.
D4/D5/CMSI/Home have search, but Healthcare has no sidebar search near [page setup](/Users/gcc/invest-dashboard/app/pages/2_🏥_Healthcare.py:33), and Sector Heatmap’s sidebar starts with filters only at [line 39](/Users/gcc/invest-dashboard/app/pages/3_🔥_Sector_Heatmap.py:39). Action: use shared `ui.sidebar_search()` on every page.

[MINOR] SQLite WAL/SHM files should not be tracked.
`data/external/picks.db-wal` and `data/external/picks.db-shm` are tracked. Add `*.db-wal` / `*.db-shm` to [.gitignore](/Users/gcc/invest-dashboard/.gitignore:1) and remove them from git.

[MINOR] Scanner percentile is useful directionally, but small-N ranks are coarse and mislabeled.
[file](/Users/gcc/invest-dashboard/app/pages/5_💰_Valuation_Scanner.py:142) uses `rank(pct=True) * 100`, so the cheapest stock is `100/N`, not `0`, despite the docstring at [line 128](/Users/gcc/invest-dashboard/app/pages/5_💰_Valuation_Scanner.py:128). Current positive forward P/E counts are biotech 13, hc_ai 11, hospital/managed care 10, etc.; a 25% threshold means only 2-4 names per sector. Action: show `rank/N`, `N positive`, and/or use `(rank - 1) / (N - 1) * 100`.

[MINOR] Negative P/E exclusion is defensible, but should be surfaced.
[file](/Users/gcc/invest-dashboard/app/pages/5_💰_Valuation_Scanner.py:139) drops non-positive P/E. That is correct for P/E ranking, especially biotech, but loss-making names become invisible while high positive P/E names remain rankable. Action: show an “excluded: negative/NA P/E” count and add EV/Sales or cash/runway mode for biotech.

**Regression Check**

M7, M10, n2, and dark theme look preserved: formatting helpers return `"—"` for NaN, CMSI sorts by market cap desc and prefers Chinese names, Bloomberg ticker formatting is used, and dark theme is configured. B4 is the only regression still incomplete.

Verification run: `python3 -m compileall app jobs` passed; `jobs/init_db.py` and `jobs/load_universe.py` ran successfully. I did not run live `fetch_eod.py` or live D4 yfinance fetch.
tokens used
137,850

```

## Concise summary

Provider completed successfully. Review the raw output for details.

## Action items

- Review the response and extract decisions you want to apply.
- Capture follow-up implementation tasks if needed.
