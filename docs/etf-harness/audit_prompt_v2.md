You are an independent CROSS-MODEL auditor in a three-power build harness. You did NOT write this code. Audit read-only; propose fixes, do not edit.

## What was built (v2 redesign)
The ETF feature was redesigned. v1 (a bespoke expander-list page) was REJECTED by the user, who wants
ETFs shown **like stocks**: 表现 (performance) / 动能 (momentum) / 热力图 (heatmap). The chosen approach
**promotes the 10 healthcare ETFs to first-class instruments**: they are loaded into the shared price DB
(`data/snapshots.db` → `universe_member` domain='etf' + `prices_daily`) via `config/domains/etf.yml` +
`config/universes/etf_*.yml`, so the EXISTING stock components render them with no new analytics code.

Files to audit:
- `config/domains/etf.yml` + `config/universes/etf_*.yml` — new universe (6 sub-sectors, 10 ETFs).
- `app/pages/e1_etf_overview.py` — 表现 table (db.compute_returns over domain='etf') + 成分股 tab
  (reuses lib/etf_panel holdings).
- `app/pages/e2_etf_heatmap.py` — reuses lib/heatmap.build_domain_bento("etf", ...).
- `app/pages/e3_etf_rotation.py` — reuses lib/rrg (RRG, ETFs vs XLV benchmark).
- `app/lib/heatmap.py` — added 6 `etf_*` sub-sector display names + `etf` domain label.
- `app/streamlit_app.py` — new top-level "ETF 专栏" nav group; removed the old hc_etf page.
- `app/lib/locales/pages_{en,zh}.py` — new `etf.*` keys.
- `jobs/build_etf_panel.py` — unchanged (still bakes holdings CSV the 成分股 tab reads).

Use `git diff` / `git status` to see the full change set.

## Audit on three axes
1. **Conformance** — does it deliver 表现/动能/热力图 "like stocks", with holdings preserved as a tab?
2. **Consistency** — sub-sector ids (`etf_*`) consistent across etf.yml ↔ universe files ↔
   heatmap._SECTOR_CN/_EN ↔ e1's local _SUB maps? i18n `etf.*` keys present in BOTH locales and used?
3. **Correctness** — focus on these (this is a sell-side tool; wrong numbers/regressions are costly):
   - **No regression to the shared price DB / existing pages**: adding domain='etf' to universe_member +
     editing the shared `lib/heatmap.py` must not change HC/AI heatmaps, home, or the nightly fetch_eod
     behavior. Reason about whether any existing query that does NOT filter by domain could now sweep in
     ETFs unintentionally (e.g. `all_tickers()`, a domain-less heatmap, top_movers without domain).
   - **Heatmap on ETFs**: mcap is None for ETFs (yf.info gives no ETF market cap) — confirm
     `build_domain_bento` / `_pick_tiles` degrade safely (no anchor) and don't crash or mis-rank.
   - **RRG benchmark**: e3 uses XLV as benchmark and excludes XLV from the plotted set — verify XLV isn't
     plotted against itself, and that the MIN_DAYS history filter is sound for ~273 sessions.
   - **Deep-link safety**: e1 builds `/Ticker_Drill?ticker=...` — URL-encoded? null-safe?
   - **表现 table**: returns come from db.compute_returns (live DB); AUM from the baked CSV — is the join
     by ticker correct, and does a missing AUM degrade to "—" not 0 or crash?
   - **i18n**: any `etf.*` / `hc_etf.*` key used in a page but missing from a locale (would render the raw key)?

## Output
Single verdict: APPROVE / APPROVE-WITH-NITS / REJECT. Then findings: severity (CRITICAL/MAJOR/MINOR/NIT),
file:line, what's wrong, proposed fix. Be skeptical — your value is catching what same-model build+eval
missed (last round you caught 3 real bugs). If nothing material, say so plainly.
