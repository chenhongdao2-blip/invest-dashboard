You are an independent CROSS-MODEL auditor in a three-power build harness. You did NOT write this code. Audit it read-only; propose fixes but do not edit.

## What was built
A new "ETF 专栏" feature for a Streamlit investment dashboard (healthcare ETFs, each row expands to show constituent holdings). Files to audit:
- `jobs/build_etf_panel.py` — bakes 3 data files by shelling out to an external etf-data MCP CLI.
- `data/external/etf_hc_universe.csv`, `etf_hc_holdings.csv`, `etf_hc_meta.json` — the baked data.
- `app/lib/etf_panel.py` — the loader (pure reader).
- `app/pages/10_HC_ETF.py` — the page.
- `app/streamlit_app.py` — nav registration (one st.Page added under Healthcare).
- `app/lib/locales/pages_en.py` / `pages_zh.py` — `hc_etf.*` keys (search for "hc_etf").
- `tests/test_etf_panel.py` — the acceptance gate (authored independently; do NOT treat as ground truth, audit it too).

The frozen contract is `docs/etf-harness/ACCEPTANCE.md`. Read it first.

## Audit on three axes
1. **Conformance** — does the implementation meet every criterion A–G in ACCEPTANCE.md?
2. **Consistency** — is it internally consistent (loader interface vs page usage vs tests vs data schema)?
3. **Correctness** — logic bugs, especially in these high-risk spots (this is a sell-side investment tool — wrong numbers pollute decisions):
   - **Weight formatting**: weights must render as a plain non-signed percent (e.g. "16.4%") with a data bar — NOT sign-colored teal/red like a return. Verify `render_html_table` is called with weight in `bar_cols`/`extra_formats`, NOT `pct_cols`.
   - **Null-tail handling**: the symbol-only tail must keep `weight_pct`/`name` as NULL/NaN — an unknown weight must NEVER be coerced to 0.0 (zero would lie about the holding). Check the job, the loader, and the CSV.
   - **Deep-link safety**: holding tickers deep-link to `/Ticker_Drill?ticker=<SYM>`. Verify a null/blank symbol (it occurs — IBB has a weighted row with no symbol) does NOT produce `ticker=nan`, and that the symbol is URL/HTML-safe.
   - **Coverage number**: `meta.weight_sum_pct_by_etf` is used as the "top-25 = X% of fund" note. Confirm it equals the sum of the persisted weighted rows (internal consistency), not a separately-reported upstream field.
   - **Cache correctness**: the loader uses `st.cache_data` keyed on (path, mtime). Reason about whether a missing file returns empty AND whether a re-bake busts the cache.
   - **Empty-safety / no-crash**: loaders and page must degrade (empty df / warning), never throw, on missing files.

## Output
Give a single verdict: **APPROVE**, **APPROVE-WITH-NITS**, or **REJECT**.
Then a findings list, each: severity (CRITICAL / MAJOR / MINOR / NIT), file:line, what's wrong, and the proposed fix. Be concrete and skeptical — your value is catching what the same-model builder and evaluator both missed. If you find nothing material, say so plainly.
