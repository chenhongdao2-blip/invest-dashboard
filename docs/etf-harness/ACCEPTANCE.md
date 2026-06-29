# ACCEPTANCE — ETF 专栏 v1 (Healthcare)

Status: **SEED** (Planner draft). To be hardened by the independent Evaluator, then **FROZEN**.
Once frozen, the Builder may not weaken any criterion and may not edit `tests/test_etf_panel.py`.

Macro spec: `~/.claude/plans/etf-etf-linear-rain.md`.

## Artifacts under test
- `data/external/etf_hc_universe.csv`, `etf_hc_holdings.csv`, `etf_hc_meta.json` (baked, frozen)
- `app/lib/etf_panel.py` (loader)
- `app/pages/10_HC_ETF.py` (page)
- `app/streamlit_app.py` (nav registration)
- `app/lib/locales/pages_en.py`, `pages_zh.py` (`hc_etf.*` keys)

## Criteria (gate = `tests/test_etf_panel.py` for A,B,E,G; real-machine for C,D,F)

**A. Data integrity (baked files)**
- A1 `etf_hc_universe.csv` has exactly the curated rows (10 in v1), columns per spec, `domain`=="healthcare".
- A2 Each ETF's `ret_1y` is finite and within a sane band; `aum`>0; `expense_ratio` in (0,1).
- A3 `etf_hc_holdings.csv`: for each ETF the weighted rows (rank not null) sum to ≈ `meta.weight_sum_pct_by_etf[ticker]` (±0.5pp).
- A4 Tail rows (rank null) have `weight_pct` empty (NOT 0) and `name` empty — "unknown ≠ zero".
- A5 XLV top holding == LLY with weight ≈16.4% (±0.3); XLV weighted rows ≈ top-25.

**B. Loader contract (`app/lib/etf_panel.py`)**
- B1 `load_etf_universe()` → DataFrame, 10 rows, expected columns.
- B2 `load_etf_holdings()` → DataFrame, includes weighted + tail rows.
- B3 `holdings_for(load_etf_holdings(), "XLV")` → `(weighted_df, tail_symbols)`; weighted_df ≤25 rows all weight-not-null & rank-sorted; tail_symbols is a list[str] of the null-rank symbols.
- B4 Missing data file → loaders return **empty DataFrame** (no exception). `etf_meta()` → {} if absent.
- B5 No `weight_pct==0.0` rows fabricated for tail (loader must preserve None/NaN).

**C. Page render — real machine (Streamlit running)**
- C1 App boots; "Healthcare 医疗健康 → HC ETFs" page reachable, no exception in logs.
- C2 Each ETF renders an `st.expander`; opening one shows the holdings as an FT HTML table (iframe, **not** a black `st.dataframe` canvas).
- C3 Weight column shows an in-cell data bar; weight is a plain non-signed "%.1f%%" (NOT teal/red sign-colored).
- C4 Caption shows `meta.as_of`.

**D. Deep-link — real machine**
- D1 A holding row exposes a `↗` link to `/Ticker_Drill?ticker=<SYM>`; clicking opens Ticker Drill (new tab) resolved to that symbol.

**E. Tail + coverage**
- E1 For an equal-weight ETF (XBI), the page shows a "+N more constituents: …" line listing tail symbols.
- E2 A coverage note shows top-25 weight sum (e.g. "top 25 = 30.5% of fund") sourced from meta.

**F. Empty-safe / no regression**
- F1 Renaming `etf_hc_universe.csv` aside → page shows a graceful notice, does not crash the app.
- F2 All other nav pages still import/run; nav still `expanded=True`; no new errors on Home / Ticker Drill / Capital Markets.

**G. i18n**
- G1 `hc_etf.title`, `hc_etf.caption`, column labels, `hc_etf.tail_more` exist in BOTH `pages_en.py` and `pages_zh.py`.
- G2 Page renders with no missing-key fallback (`i18n.t` returns no `⟨key⟩`-style miss) in EN and 中文.

## Out of scope (do not test/build in v1)
Per-constituent live quotes/sparklines; non-HC domains; live price overlay / auto holdings refresh; per-ETF options panel.
