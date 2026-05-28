# codex advisor artifact

- Provider: codex
- Exit code: 0
- Created at: 2026-05-28T03:38:37.323Z

## Original task

Audit this multi-domain sell-side investment dashboard against the plan.

**Repo (public)**: https://github.com/chenhongdao2-blip/invest-dashboard
**Three commits**: `7f71a91` (D1 bootstrap), `3157451` (D2 fetcher), `17f2f17` (D3 Streamlit pages)

**Plan goal**: 1-week ship of Healthcare dashboard with 6 P0 views; will extend to AI domain later.

**Stack**:
- GitHub Actions cron (22:30 UTC for US close + 09:00 UTC for HK close)
- yfinance batch download + `.info` multiples
- SQLite committed to repo (4 tables: prices_daily / multiples_daily / universe_member / meta)
- Streamlit Cloud free tier, public no-auth
- FX normalization to USD (HKD/JPY/KRW/CNY/EUR/GBP/CHF)

**Done in D1-D3**:
- 97 universe tickers (7 healthcare sectors + 28 CMSI HK cover, cross-membership via many-to-many `universe_member`)
- 60-day price backfill: 4301 rows × 106 unique tickers
- 106/106 multiples snapshots (0 fail)
- Streamlit Home (8 benchmarks + top movers + universe summary)
- Healthcare domain overview (7-sector summary table + per-sector top-3 expanders)
- Sector Heatmap (dropdown + heatmap with diverging colors for returns + low-good gradient for P/E)

**Pending (D4-D7)**:
- D4 Strategy Picks: read `~/ic-foundry/ledger.db` picks_v2 table (v4/v5 biotech + HK 高股息)
- D5 CMSI Coverage page + Valuation Scanner (sector-internal P/E percentile filter)
- D6 Ticker Drill (5Y price + multiple time series + fundamentals card)
- D7 Deploy to Streamlit Community Cloud

**Audit angle (architecture / correctness / risk)**:

1. **Schema vs plan** — Look at `jobs/init_db.py`. Plan listed 4 tables. Are they all defined correctly? Any column missing for downstream needs?

2. **fetch_eod.py robustness** — Look at `jobs/fetch_eod.py`:
   - Rate limit handling sufficient (`SLEEP_BETWEEN_INFO = 0.2`, batch size 40)?
   - FX edge cases: I use `if sym.startswith("USD")` for "USDxxx=X" pairs to invert; otherwise treat as direct. Correct?
   - Negative multiples (e.g. forward P/E for unprofitable biotech) → I render "neg" via `fmt_ratio`. Acceptable?
   - `--backfill-days` arg uses `max(args.backfill_days, 5)` to ensure at least 5-day window. Reasonable?
   - What happens if yfinance returns partial batch failure (some tickers in batch fail)? My current code uses `try/except` per ticker — sufficient?

3. **Cron schedule** — `.github/workflows/fetch_eod.yml` runs at `30 22 * * 1-5` (US close) and `0 9 * * 1-5` (HK close). GitHub Actions cron doesn't observe DST. Does 22:30 UTC correctly cover both EST (UTC-5) and EDT (UTC-4) close times (21:00 UTC vs 20:00 UTC)? Should I move earlier?

4. **SQLite commit growth** — Plan estimates ~1.6MB/year for 150 tickers. With 106 tickers × daily commits × multi-year, will the repo become unwieldy? At what point should I migrate to Parquet snapshots or external SQLite (Turso/Supabase)?

5. **Public repo with price data** — Repo is public on GitHub. Price data is freely available elsewhere (Yahoo Finance public). But the **CMSI cover list** + **strategy picks** could be considered IP. User confirmed acceptable (cover list in research distribution is semi-public). Flag if you see a real leak risk I missed.

6. **compute_returns ragged-tail fix** — `app/lib/db.py:compute_returns()` iterates each ticker's own `dropna()` series for last/prev close. This fixes the original bug where JP markets close before US, leaving US tickers with NaN on the latest date. Edge cases I might have missed?

7. **GitHub Actions write permission** — I set `permissions: contents: write` so the bot can `git push` the data commit. Is this the right scope, or should I use a fine-grained PAT?

8. **What's the biggest BLOCKER/MAJOR risk that could break the dashboard after Streamlit Cloud deploy?**

Output: severity-tagged [BLOCKER] / [MAJOR] / [MINOR] / [NIT] actionable items with file:line references. No fluff. Be ruthless — this is pre-deploy review.

## Final prompt

Audit this multi-domain sell-side investment dashboard against the plan.

**Repo (public)**: https://github.com/chenhongdao2-blip/invest-dashboard
**Three commits**: `7f71a91` (D1 bootstrap), `3157451` (D2 fetcher), `17f2f17` (D3 Streamlit pages)

**Plan goal**: 1-week ship of Healthcare dashboard with 6 P0 views; will extend to AI domain later.

**Stack**:
- GitHub Actions cron (22:30 UTC for US close + 09:00 UTC for HK close)
- yfinance batch download + `.info` multiples
- SQLite committed to repo (4 tables: prices_daily / multiples_daily / universe_member / meta)
- Streamlit Cloud free tier, public no-auth
- FX normalization to USD (HKD/JPY/KRW/CNY/EUR/GBP/CHF)

**Done in D1-D3**:
- 97 universe tickers (7 healthcare sectors + 28 CMSI HK cover, cross-membership via many-to-many `universe_member`)
- 60-day price backfill: 4301 rows × 106 unique tickers
- 106/106 multiples snapshots (0 fail)
- Streamlit Home (8 benchmarks + top movers + universe summary)
- Healthcare domain overview (7-sector summary table + per-sector top-3 expanders)
- Sector Heatmap (dropdown + heatmap with diverging colors for returns + low-good gradient for P/E)

**Pending (D4-D7)**:
- D4 Strategy Picks: read `~/ic-foundry/ledger.db` picks_v2 table (v4/v5 biotech + HK 高股息)
- D5 CMSI Coverage page + Valuation Scanner (sector-internal P/E percentile filter)
- D6 Ticker Drill (5Y price + multiple time series + fundamentals card)
- D7 Deploy to Streamlit Community Cloud

**Audit angle (architecture / correctness / risk)**:

1. **Schema vs plan** — Look at `jobs/init_db.py`. Plan listed 4 tables. Are they all defined correctly? Any column missing for downstream needs?

2. **fetch_eod.py robustness** — Look at `jobs/fetch_eod.py`:
   - Rate limit handling sufficient (`SLEEP_BETWEEN_INFO = 0.2`, batch size 40)?
   - FX edge cases: I use `if sym.startswith("USD")` for "USDxxx=X" pairs to invert; otherwise treat as direct. Correct?
   - Negative multiples (e.g. forward P/E for unprofitable biotech) → I render "neg" via `fmt_ratio`. Acceptable?
   - `--backfill-days` arg uses `max(args.backfill_days, 5)` to ensure at least 5-day window. Reasonable?
   - What happens if yfinance returns partial batch failure (some tickers in batch fail)? My current code uses `try/except` per ticker — sufficient?

3. **Cron schedule** — `.github/workflows/fetch_eod.yml` runs at `30 22 * * 1-5` (US close) and `0 9 * * 1-5` (HK close). GitHub Actions cron doesn't observe DST. Does 22:30 UTC correctly cover both EST (UTC-5) and EDT (UTC-4) close times (21:00 UTC vs 20:00 UTC)? Should I move earlier?

4. **SQLite commit growth** — Plan estimates ~1.6MB/year for 150 tickers. With 106 tickers × daily commits × multi-year, will the repo become unwieldy? At what point should I migrate to Parquet snapshots or external SQLite (Turso/Supabase)?

5. **Public repo with price data** — Repo is public on GitHub. Price data is freely available elsewhere (Yahoo Finance public). But the **CMSI cover list** + **strategy picks** could be considered IP. User confirmed acceptable (cover list in research distribution is semi-public). Flag if you see a real leak risk I missed.

6. **compute_returns ragged-tail fix** — `app/lib/db.py:compute_returns()` iterates each ticker's own `dropna()` series for last/prev close. This fixes the original bug where JP markets close before US, leaving US tickers with NaN on the latest date. Edge cases I might have missed?

7. **GitHub Actions write permission** — I set `permissions: contents: write` so the bot can `git push` the data commit. Is this the right scope, or should I use a fine-grained PAT?

8. **What's the biggest BLOCKER/MAJOR risk that could break the dashboard after Streamlit Cloud deploy?**

Output: severity-tagged [BLOCKER] / [MAJOR] / [MINOR] / [NIT] actionable items with file:line references. No fluff. Be ruthless — this is pre-deploy review.

## Raw output

```text
**Findings**

[BLOCKER] D4 Strategy Picks will not work on Streamlit Cloud if it reads `~/ic-foundry/ledger.db`. Streamlit Cloud will not have that home-directory DB, and the current app only opens repo-local `data/snapshots.db` read-only at `app/lib/db.py:11-17`. Action: export `picks_v2` into the committed dashboard DB, a private artifact, or an external DB reachable via Streamlit secrets. Do not build D4 against `~`.

[MAJOR] FX normalization is not actually implemented for prices. `prices_daily` stores only local `close` / `adj_close` plus `currency` at `jobs/init_db.py:19-29`; `fetch_eod.py` fetches FX at `jobs/fetch_eod.py:265-266` but only uses currency labels when writing prices at `jobs/fetch_eod.py:284-287`. Action: add `fx_to_usd`, `close_usd`, `adj_close_usd` or compute a USD view. For multiples, also store `currency` and `last_price_usd`; `last_price` is local while `market_cap_usd` is USD at `jobs/fetch_eod.py:221-241`.

[MAJOR] Displayed YTD is currently false with only a 60-calendar-day backfill. `compute_returns()` anchors YTD to the first available close in the current year at `app/lib/db.py:121-127`, but the DB starts `2026-03-30`, so “YTD” is really “since Mar 30”. Action: backfill from Jan 1 at minimum whenever YTD is displayed, or label it as since-first-available.

[MAJOR] `60d_%` will be mostly/all NaN after a 60-calendar-day backfill. `ret_back(60)` requires 61 valid trading closes at `app/lib/db.py:113-119` and `app/lib/db.py:135`; `--backfill-days 60` gives roughly 40-45 trading rows. Action: use ~90 calendar days for 60 trading days, or redefine as calendar-day return using date lookup.

[MAJOR] yfinance `.info` rate-limit handling is too optimistic for unattended cron. `SLEEP_BETWEEN_INFO = 0.2` at `jobs/fetch_eod.py:37-39` plus only two attempts at `jobs/fetch_eod.py:203-214` can silently produce stale/missing multiples; the job still exits success at `jobs/fetch_eod.py:293-311`. Action: exponential backoff, jitter, longer sleep, and fail the workflow if failures exceed a threshold.

[MAJOR] SQLite-in-git growth is underestimated because every daily commit stores another binary DB version in Git history. Current DB is already 640KB for 60 days; even with packing, page churn can make history grow much faster than the “1.6MB/year” working-file estimate. Action: acceptable for MVP, but plan migration before multi-year/multi-domain use. Trigger point: working DB >50-100MB or `.git` pack >200-500MB. Prefer external SQLite/Turso/Supabase or partitioned Parquet snapshots.

[MAJOR] Public IP leak risk is real in comments, even if the ticker list is acceptable. `config/universes/cmsi_coverage_hc.yml:1-3` explicitly says “CMSI internal coverage table” and names provenance. Strategy picks will be much more sensitive than coverage. Action: remove internal-source comments from public repo; keep strategy picks private or publish only derived/non-actionable labels.

[MINOR] FX pair inversion logic is correct for your listed pairs. `USDHKD=X`, `USDJPY=X`, `USDKRW=X`, `USDCNY=X`, `USDCHF=X` should invert; `EURUSD=X` and `GBPUSD=X` should not. Current `sym.startswith("USD")` logic at `jobs/fetch_eod.py:122-127` is fine. Action: add a unit test/table-driven assertion so this does not regress.

[MINOR] FX failure fallback is dangerous. If `yf.download()` fails, all currencies default to `1.0` at `jobs/fetch_eod.py:103-108`, which can make HKD/JPY/KRW market caps wildly wrong. Action: fail the job on FX failure, or reuse last good FX rates from DB instead of defaulting to 1.0.

[MINOR] Partial price batch failure is handled enough to preserve successful tickers, but missing tickers are swallowed. `fetch_prices_batch()` extracts per-ticker frames at `jobs/fetch_eod.py:160-168`, but logs no missing symbols and the workflow still succeeds. Action: log `set(batch) - set(result)` and fail if missing count crosses a threshold.

[MINOR] `fmt_ratio()` rendering negative P/E as `neg` is acceptable for biotech scanning at `app/lib/format.py:45-50`. The heatmap correctly skips coloring negative multiples at `app/lib/format.py:123-126`. Action: for scanner filters, exclude negative P/E from percentile math or bucket as “NM/neg”, not cheap.

[MINOR] `--backfill-days` minimum 5-day window is reasonable for daily cron repair at `jobs/fetch_eod.py:258-260`. It will recover short gaps. It is not enough for return windows or YTD, so treat it as operational repair only.

[MINOR] Cron timing is safe. `22:30 UTC` is after both EDT close `20:00 UTC` and EST close `21:00 UTC`; moving earlier risks winter incompleteness. `09:00 UTC` is after HK close. Keep `.github/workflows/fetch_eod.yml:4-9` as-is unless yfinance finalization latency proves lower and you explicitly split US summer/winter schedules.

[MINOR] `permissions: contents: write` is the right GitHub Actions scope for pushing the DB with `GITHUB_TOKEN` at `.github/workflows/fetch_eod.yml:17-18` and `.github/workflows/fetch_eod.yml:46-55`. A fine-grained PAT is not better unless branch protection blocks the bot or you need cross-repo writes.

[NIT] `prices_to_rows()` uses `r.get("Adj Close") or r.get("Close")` at `jobs/fetch_eod.py:181`; `NaN` is truthy, so it may not fall back to close. Action: use explicit `pd.notna()` fallback.

**Biggest Risk**

The biggest deploy-breaking risk is D4: a Streamlit Cloud app cannot read `~/ic-foundry/ledger.db`. The biggest correctness risk in current D1-D3 views is false YTD/60D due to insufficient history.

Verification: `python3 -m compileall jobs app` passes.


OpenAI Codex v0.130.0
--------
workdir: /Users/gcc/invest-dashboard
model: gpt-5.5
provider: openai
approval: never
sandbox: danger-full-access
reasoning effort: medium
reasoning summaries: none
session id: 019e6ca7-aeeb-7982-a22f-43b44e4bfa7c
--------
user
Audit this multi-domain sell-side investment dashboard against the plan.

**Repo (public)**: https://github.com/chenhongdao2-blip/invest-dashboard
**Three commits**: `7f71a91` (D1 bootstrap), `3157451` (D2 fetcher), `17f2f17` (D3 Streamlit pages)

**Plan goal**: 1-week ship of Healthcare dashboard with 6 P0 views; will extend to AI domain later.

**Stack**:
- GitHub Actions cron (22:30 UTC for US close + 09:00 UTC for HK close)
- yfinance batch download + `.info` multiples
- SQLite committed to repo (4 tables: prices_daily / multiples_daily / universe_member / meta)
- Streamlit Cloud free tier, public no-auth
- FX normalization to USD (HKD/JPY/KRW/CNY/EUR/GBP/CHF)

**Done in D1-D3**:
- 97 universe tickers (7 healthcare sectors + 28 CMSI HK cover, cross-membership via many-to-many `universe_member`)
- 60-day price backfill: 4301 rows × 106 unique tickers
- 106/106 multiples snapshots (0 fail)
- Streamlit Home (8 benchmarks + top movers + universe summary)
- Healthcare domain overview (7-sector summary table + per-sector top-3 expanders)
- Sector Heatmap (dropdown + heatmap with diverging colors for returns + low-good gradient for P/E)

**Pending (D4-D7)**:
- D4 Strategy Picks: read `~/ic-foundry/ledger.db` picks_v2 table (v4/v5 biotech + HK 高股息)
- D5 CMSI Coverage page + Valuation Scanner (sector-internal P/E percentile filter)
- D6 Ticker Drill (5Y price + multiple time series + fundamentals card)
- D7 Deploy to Streamlit Community Cloud

**Audit angle (architecture / correctness / risk)**:

1. **Schema vs plan** — Look at `jobs/init_db.py`. Plan listed 4 tables. Are they all defined correctly? Any column missing for downstream needs?

2. **fetch_eod.py robustness** — Look at `jobs/fetch_eod.py`:
   - Rate limit handling sufficient (`SLEEP_BETWEEN_INFO = 0.2`, batch size 40)?
   - FX edge cases: I use `if sym.startswith("USD")` for "USDxxx=X" pairs to invert; otherwise treat as direct. Correct?
   - Negative multiples (e.g. forward P/E for unprofitable biotech) → I render "neg" via `fmt_ratio`. Acceptable?
   - `--backfill-days` arg uses `max(args.backfill_days, 5)` to ensure at least 5-day window. Reasonable?
   - What happens if yfinance returns partial batch failure (some tickers in batch fail)? My current code uses `try/except` per ticker — sufficient?

3. **Cron schedule** — `.github/workflows/fetch_eod.yml` runs at `30 22 * * 1-5` (US close) and `0 9 * * 1-5` (HK close). GitHub Actions cron doesn't observe DST. Does 22:30 UTC correctly cover both EST (UTC-5) and EDT (UTC-4) close times (21:00 UTC vs 20:00 UTC)? Should I move earlier?

4. **SQLite commit growth** — Plan estimates ~1.6MB/year for 150 tickers. With 106 tickers × daily commits × multi-year, will the repo become unwieldy? At what point should I migrate to Parquet snapshots or external SQLite (Turso/Supabase)?

5. **Public repo with price data** — Repo is public on GitHub. Price data is freely available elsewhere (Yahoo Finance public). But the **CMSI cover list** + **strategy picks** could be considered IP. User confirmed acceptable (cover list in research distribution is semi-public). Flag if you see a real leak risk I missed.

6. **compute_returns ragged-tail fix** — `app/lib/db.py:compute_returns()` iterates each ticker's own `dropna()` series for last/prev close. This fixes the original bug where JP markets close before US, leaving US tickers with NaN on the latest date. Edge cases I might have missed?

7. **GitHub Actions write permission** — I set `permissions: contents: write` so the bot can `git push` the data commit. Is this the right scope, or should I use a fine-grained PAT?

8. **What's the biggest BLOCKER/MAJOR risk that could break the dashboard after Streamlit Cloud deploy?**

Output: severity-tagged [BLOCKER] / [MAJOR] / [MINOR] / [NIT] actionable items with file:line references. No fluff. Be ruthless — this is pre-deploy review.
codex
I’ll audit this as a code review against the plan: first pin the repo state and relevant files, then inspect schema, fetcher, workflow, and app return logic with line references.
exec
/bin/zsh -lc 'rg --files' in /Users/gcc/invest-dashboard
 succeeded in 0ms:
data/snapshots.db
jobs/init_db.py
jobs/fetch_eod.py
jobs/load_universe.py
README.md
requirements.txt
config/universes/cmsi_coverage_hc.yml
config/universes/hc_cxo.yml
config/universes/hc_ai.yml
config/universes/hc_biotech.yml
config/universes/hc_hospital_care.yml
config/universes/hc_pharma.yml
config/universes/hc_managed_care.yml
config/universes/hc_medtech.yml
config/domains/healthcare.yml
app/streamlit_app.py
app/lib/benchmarks.py
app/lib/format.py
app/lib/__init__.py
app/lib/charts.py
app/lib/db.py
app/pages/1_🏥_Healthcare.py
app/pages/2_🔥_Sector_Heatmap.py

exec
/bin/zsh -lc 'git show --stat --oneline 7f71a91 3157451 17f2f17' in /Users/gcc/invest-dashboard
 succeeded in 0ms:
7f71a91 init: invest-dashboard repo bootstrap (D1)
 .github/workflows/fetch_eod.yml       |  53 ++++++++++++++++
 .gitignore                            |  27 ++++++++
 .streamlit/config.toml                |  14 ++++
 README.md                             |  74 ++++++++++++++++++++++
 app/lib/__init__.py                   |   0
 app/lib/db.py                         |  45 +++++++++++++
 app/streamlit_app.py                  |  54 ++++++++++++++++
 config/domains/healthcare.yml         |  49 ++++++++++++++
 config/universes/cmsi_coverage_hc.yml |  24 +++++++
 config/universes/hc_ai.yml            |  31 +++++++++
 config/universes/hc_biotech.yml       |  38 +++++++++++
 config/universes/hc_cxo.yml           |  33 ++++++++++
 config/universes/hc_hospital_care.yml |  25 ++++++++
 config/universes/hc_managed_care.yml  |  26 ++++++++
 config/universes/hc_medtech.yml       |  31 +++++++++
 config/universes/hc_pharma.yml        |  37 +++++++++++
 data/snapshots.db                     | Bin 0 -> 53248 bytes
 jobs/fetch_eod.py                     |  66 +++++++++++++++++++
 jobs/init_db.py                       |  94 +++++++++++++++++++++++++++
 jobs/load_universe.py                 | 116 ++++++++++++++++++++++++++++++++++
 requirements.txt                      |   6 ++
 21 files changed, 843 insertions(+)
3157451 feat(D2): full yfinance fetcher + cron + CMSI coverage list
 .github/workflows/fetch_eod.yml       |   3 +
 config/universes/cmsi_coverage_hc.yml | 127 ++++++++++++--
 data/snapshots.db                     | Bin 53248 -> 593920 bytes
 jobs/fetch_eod.py                     | 308 +++++++++++++++++++++++++++++++---
 4 files changed, 400 insertions(+), 38 deletions(-)
17f2f17 feat(D3): Streamlit Home + Healthcare overview + Sector Heatmap
 app/lib/benchmarks.py                            |  78 +++++++++++
 app/lib/charts.py                                |  89 ++++++++++++
 app/lib/db.py                                    | 153 +++++++++++++++++++--
 app/lib/format.py                                | 133 ++++++++++++++++++
 "app/pages/1_\360\237\217\245_Healthcare.py"     | 130 ++++++++++++++++++
 "app/pages/2_\360\237\224\245_Sector_Heatmap.py" | 167 +++++++++++++++++++++++
 app/streamlit_app.py                             | 124 +++++++++++++----
 7 files changed, 837 insertions(+), 37 deletions(-)

exec
/bin/zsh -lc 'git status --short && git rev-parse --show-toplevel && git log --oneline -5' in /Users/gcc/invest-dashboard
 succeeded in 0ms:
/Users/gcc/invest-dashboard
17f2f17 feat(D3): Streamlit Home + Healthcare overview + Sector Heatmap
3157451 feat(D2): full yfinance fetcher + cron + CMSI coverage list
7f71a91 init: invest-dashboard repo bootstrap (D1)

codex
I have the requested commits locally and the worktree appears clean from the first check. I’m reading the schema, fetch path, workflow, and app data helpers now so the findings are tied to exact behavior rather than the README.
exec
/bin/zsh -lc 'nl -ba jobs/init_db.py' in /Users/gcc/invest-dashboard
exec
/bin/zsh -lc 'nl -ba jobs/fetch_eod.py' in /Users/gcc/invest-dashboard
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
    19	CREATE TABLE IF NOT EXISTS prices_daily (
    20	    ticker     TEXT NOT NULL,
    21	    date       TEXT NOT NULL,        -- YYYY-MM-DD
    22	    open       REAL,
    23	    high       REAL,
    24	    low        REAL,
    25	    close      REAL,
    26	    adj_close  REAL,
    27	    volume     INTEGER,
    28	    currency   TEXT,                  -- USD / HKD / JPY / KRW / EUR
    29	    PRIMARY KEY (ticker, date)
    30	);
    31	CREATE INDEX IF NOT EXISTS idx_prices_date ON prices_daily(date);
    32	
    33	-- Multiple snapshot 时序 (core value: 自累积 → 90d 后可做 Z-score)
    34	CREATE TABLE IF NOT EXISTS multiples_daily (
    35	    ticker            TEXT NOT NULL,
    36	    date              TEXT NOT NULL,
    37	    market_cap_usd    REAL,
    38	    trailing_pe       REAL,
    39	    forward_pe        REAL,
    40	    trailing_eps      REAL,
    41	    forward_eps       REAL,
    42	    ev_ebitda         REAL,
    43	    ev_sales          REAL,
    44	    fcf_yield         REAL,
    45	    peg               REAL,
    46	    pb                REAL,
    47	    ytd_return        REAL,
    48	    last_price        REAL,
    49	    PRIMARY KEY (ticker, date)
    50	);
    51	CREATE INDEX IF NOT EXISTS idx_mult_date ON multiples_daily(date);
    52	
    53	-- Universe membership (many-to-many for cross-sector tickers like ISRG / HCA)
    54	CREATE TABLE IF NOT EXISTS universe_member (
    55	    domain    TEXT NOT NULL,
    56	    sector    TEXT NOT NULL,
    57	    ticker    TEXT NOT NULL,
    58	    name_cn   TEXT,
    59	    name_en   TEXT,
    60	    region    TEXT,
    61	    note      TEXT,
    62	    PRIMARY KEY (domain, sector, ticker)
    63	);
    64	CREATE INDEX IF NOT EXISTS idx_um_ticker ON universe_member(ticker);
    65	CREATE INDEX IF NOT EXISTS idx_um_domain_sector ON universe_member(domain, sector);
    66	
    67	-- Meta key/value
    68	CREATE TABLE IF NOT EXISTS meta (
    69	    key         TEXT PRIMARY KEY,
    70	    value       TEXT,
    71	    updated_at  TEXT
    72	);
    73	"""
    74	
    75	
    76	def main() -> None:
    77	    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    78	    conn = sqlite3.connect(DB_PATH)
    79	    try:
    80	        conn.executescript(SCHEMA)
    81	        conn.commit()
    82	        # Sanity log
    83	        cur = conn.execute(
    84	            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    85	        )
    86	        tables = [row[0] for row in cur.fetchall()]
    87	        print(f"[init_db] DB at: {DB_PATH}")
    88	        print(f"[init_db] Tables: {tables}")
    89	    finally:
    90	        conn.close()
    91	
    92	
    93	if __name__ == "__main__":
    94	    main()

 succeeded in 0ms:
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
    38	SLEEP_BETWEEN_INFO = 0.2          # seconds between .info calls (rate limit)
    39	
    40	
    41	# ----- args -----
    42	def parse_args() -> argparse.Namespace:
    43	    p = argparse.ArgumentParser()
    44	    p.add_argument("--backfill-days", type=int, default=0,
    45	                   help="Days of historical price to backfill (0 = today only).")
    46	    p.add_argument("--skip-multiples", action="store_true",
    47	                   help="Skip yfinance.info multiples fetch (faster, prices only).")
    48	    p.add_argument("--limit", type=int, default=0,
    49	                   help="Process only first N tickers (debug).")
    50	    return p.parse_args()
    51	
    52	
    53	# ----- DB helpers -----
    54	def get_tickers(conn: sqlite3.Connection, limit: int = 0) -> list[str]:
    55	    q = "SELECT DISTINCT ticker FROM universe_member ORDER BY ticker"
    56	    if limit > 0:
    57	        q += f" LIMIT {limit}"
    58	    return [row[0] for row in conn.execute(q).fetchall()]
    59	
    60	
    61	def upsert_prices(conn: sqlite3.Connection, rows: list[tuple]) -> int:
    62	    if not rows:
    63	        return 0
    64	    conn.executemany(
    65	        """INSERT OR REPLACE INTO prices_daily
    66	           (ticker, date, open, high, low, close, adj_close, volume, currency)
    67	           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
    68	        rows,
    69	    )
    70	    return len(rows)
    71	
    72	
    73	def upsert_multiples(conn: sqlite3.Connection, rows: list[tuple]) -> int:
    74	    if not rows:
    75	        return 0
    76	    conn.executemany(
    77	        """INSERT OR REPLACE INTO multiples_daily
    78	           (ticker, date, market_cap_usd, trailing_pe, forward_pe,
    79	            trailing_eps, forward_eps, ev_ebitda, ev_sales, fcf_yield,
    80	            peg, pb, ytd_return, last_price)
    81	           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
    82	        rows,
    83	    )
    84	    return len(rows)
    85	
    86	
    87	def set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    88	    conn.execute(
    89	        "INSERT OR REPLACE INTO meta (key, value, updated_at) VALUES (?, ?, ?)",
    90	        (key, value, datetime.now(timezone.utc).isoformat(timespec="seconds")),
    91	    )
    92	
    93	
    94	# ----- FX rate snapshot -----
    95	def fetch_fx_rates() -> dict[str, float]:
    96	    """Get current USD-conversion factors. {ccy → ccy/USD multiplier}.
    97	
    98	    Example: USDHKD=X close = 7.8 → 1 HKD = 1/7.8 USD.
    99	    Output: {"HKD": 1/7.8, "JPY": 1/152, ...} so price * factor[ccy] = USD.
   100	    """
   101	    rates: dict[str, float] = {"USD": 1.0}
   102	    symbols = [pair for pair in FX_PAIRS.values() if pair is not None]
   103	    try:
   104	        d = yf.download(symbols, period="5d", auto_adjust=True,
   105	                        progress=False, threads=True, group_by="ticker")
   106	    except Exception as e:
   107	        print(f"[fx] download failed: {e}; defaulting all FX to 1.0")
   108	        return {ccy: 1.0 for ccy in FX_PAIRS}
   109	
   110	    for ccy, sym in FX_PAIRS.items():
   111	        if sym is None:
   112	            continue
   113	        try:
   114	            if isinstance(d.columns, pd.MultiIndex):
   115	                ser = d[(sym, "Close")].dropna()
   116	            else:
   117	                ser = d["Close"].dropna()
   118	            if ser.empty:
   119	                rates[ccy] = 1.0
   120	                continue
   121	            last = float(ser.iloc[-1])
   122	            # USDXXX=X means how many XXX per 1 USD
   123	            # XXXUSD=X means how many USD per 1 XXX
   124	            if sym.startswith("USD"):
   125	                rates[ccy] = 1.0 / last
   126	            else:
   127	                rates[ccy] = last
   128	        except Exception:
   129	            rates[ccy] = 1.0
   130	    print(f"[fx] rates → USD: { {k: round(v, 5) for k, v in rates.items()} }")
   131	    return rates
   132	
   133	
   134	# ----- price batch fetch -----
   135	def fetch_prices_batch(tickers: list[str], start: str, end: str) -> dict[str, pd.DataFrame]:
   136	    """Return {ticker → DataFrame[Open, High, Low, Close, Volume]} indexed by date."""
   137	    out: dict[str, pd.DataFrame] = {}
   138	    # We always batch; yfinance handles single ticker in MultiIndex too with group_by='ticker'.
   139	    try:
   140	        d = yf.download(
   141	            tickers, start=start, end=end,
   142	            auto_adjust=False,   # keep both close and adj_close
   143	            progress=False, threads=True, group_by="ticker",
   144	        )
   145	    except Exception as e:
   146	        print(f"[prices] batch download failed: {e}")
   147	        return out
   148	
   149	    if d.empty:
   150	        return out
   151	
   152	    # Handle single-ticker DataFrame vs multi-ticker MultiIndex
   153	    if len(tickers) == 1:
   154	        t = tickers[0]
   155	        if isinstance(d.columns, pd.MultiIndex):
   156	            d.columns = d.columns.droplevel(1)
   157	        out[t] = d
   158	        return out
   159	
   160	    for t in tickers:
   161	        try:
   162	            if t in d.columns.get_level_values(0):
   163	                sub = d[t].dropna(how="all")
   164	                if not sub.empty:
   165	                    out[t] = sub
   166	        except Exception:
   167	            pass
   168	    return out
   169	
   170	
   171	def prices_to_rows(ticker: str, df: pd.DataFrame, currency: str) -> list[tuple]:
   172	    rows = []
   173	    for ts, r in df.iterrows():
   174	        d = ts.date().isoformat() if hasattr(ts, "date") else str(ts)[:10]
   175	        rows.append((
   176	            ticker, d,
   177	            _safe_float(r.get("Open")),
   178	            _safe_float(r.get("High")),
   179	            _safe_float(r.get("Low")),
   180	            _safe_float(r.get("Close")),
   181	            _safe_float(r.get("Adj Close") or r.get("Close")),
   182	            _safe_int(r.get("Volume")),
   183	            currency,
   184	        ))
   185	    return rows
   186	
   187	
   188	def _safe_float(v) -> float | None:
   189	    try:
   190	        if v is None or pd.isna(v):
   191	            return None
   192	        return float(v)
   193	    except Exception:
   194	        return None
   195	
   196	
   197	def _safe_int(v) -> int | None:
   198	    f = _safe_float(v)
   199	    return int(f) if f is not None else None
   200	
   201	
   202	# ----- multiples fetch (.info) -----
   203	def fetch_info_for(ticker: str) -> dict | None:
   204	    """Single-ticker .info fetch with retry."""
   205	    for attempt in range(2):
   206	        try:
   207	            t = yf.Ticker(ticker)
   208	            info = t.info or {}
   209	            if info and (info.get("marketCap") or info.get("regularMarketPrice")):
   210	                return info
   211	        except Exception as e:
   212	            print(f"[info] {ticker} attempt {attempt + 1} fail: {e}")
   213	        time.sleep(0.5)
   214	    return None
   215	
   216	
   217	def info_to_multiple_row(
   218	    ticker: str, info: dict, snapshot_date: str, fx: dict[str, float]
   219	) -> tuple | None:
   220	    """Convert yfinance.info dict → multiples_daily row tuple."""
   221	    ccy = (info.get("currency") or info.get("financialCurrency") or "USD").upper()
   222	    fx_to_usd = fx.get(ccy, 1.0)
   223	    mcap_local = _safe_float(info.get("marketCap"))
   224	    mcap_usd = mcap_local * fx_to_usd if mcap_local is not None else None
   225	
   226	    return (
   227	        ticker,
   228	        snapshot_date,
   229	        mcap_usd,
   230	        _safe_float(info.get("trailingPE")),
   231	        _safe_float(info.get("forwardPE")),
   232	        _safe_float(info.get("trailingEps")),
   233	        _safe_float(info.get("forwardEps")),
   234	        _safe_float(info.get("enterpriseToEbitda")),
   235	        _safe_float(info.get("enterpriseToRevenue")),
   236	        _safe_float(info.get("freeCashflow") and mcap_local
   237	                    and info.get("freeCashflow") / mcap_local),
   238	        _safe_float(info.get("pegRatio") or info.get("trailingPegRatio")),
   239	        _safe_float(info.get("priceToBook")),
   240	        _safe_float(info.get("ytdReturn")),         # may be None for individual stocks
   241	        _safe_float(info.get("regularMarketPrice") or info.get("currentPrice")),
   242	    )
   243	
   244	
   245	# ----- main -----
   246	def main() -> None:
   247	    args = parse_args()
   248	
   249	    if not DB_PATH.exists():
   250	        raise SystemExit(f"DB not found at {DB_PATH}. Run init_db.py first.")
   251	
   252	    conn = sqlite3.connect(DB_PATH)
   253	    tickers = get_tickers(conn, limit=args.limit)
   254	    if not tickers:
   255	        print("[fetch_eod] No tickers — run load_universe.py first.")
   256	        return
   257	
   258	    today = date.today()
   259	    end = (today + timedelta(days=1)).isoformat()    # exclusive in yfinance
   260	    start = (today - timedelta(days=max(args.backfill_days, 5))).isoformat()
   261	    snapshot_date = today.isoformat()
   262	
   263	    print(f"[fetch_eod] tickers={len(tickers)} | start={start} | end={end}")
   264	
   265	    # 1. FX rates
   266	    fx = fetch_fx_rates()
   267	
   268	    # 2. Build ticker → currency lookup from universe_member.region
   269	    region_to_ccy = {
   270	        "US": "USD", "HK": "HKD", "JP": "JPY",
   271	        "KR": "KRW", "CN": "CNY", "EU": "EUR", "UK": "GBP", "CH": "CHF",
   272	    }
   273	    ccy_map: dict[str, str] = {}
   274	    cur = conn.execute("SELECT ticker, region FROM universe_member")
   275	    for t, r in cur.fetchall():
   276	        ccy_map[t] = region_to_ccy.get(r, "USD")
   277	
   278	    # 3. Batch fetch prices
   279	    total_prices = 0
   280	    for i in range(0, len(tickers), BATCH_SIZE):
   281	        batch = tickers[i:i + BATCH_SIZE]
   282	        print(f"[prices] batch {i // BATCH_SIZE + 1}/{(len(tickers) + BATCH_SIZE - 1) // BATCH_SIZE} ({len(batch)} tickers)")
   283	        result = fetch_prices_batch(batch, start=start, end=end)
   284	        for t, df in result.items():
   285	            ccy = ccy_map.get(t, "USD")
   286	            rows = prices_to_rows(t, df, ccy)
   287	            total_prices += upsert_prices(conn, rows)
   288	        conn.commit()
   289	        time.sleep(0.5)
   290	    print(f"[prices] total upserted rows: {total_prices}")
   291	
   292	    # 4. Multiples (.info)  — slower, one by one
   293	    if not args.skip_multiples:
   294	        total_mult = 0
   295	        ok = 0
   296	        fail = 0
   297	        for idx, t in enumerate(tickers, 1):
   298	            info = fetch_info_for(t)
   299	            if not info:
   300	                fail += 1
   301	                continue
   302	            row = info_to_multiple_row(t, info, snapshot_date, fx)
   303	            if row:
   304	                total_mult += upsert_multiples(conn, [row])
   305	                ok += 1
   306	            if idx % 20 == 0:
   307	                conn.commit()
   308	                print(f"[mult] progress {idx}/{len(tickers)} (ok={ok}, fail={fail})")
   309	            time.sleep(SLEEP_BETWEEN_INFO)
   310	        conn.commit()
   311	        print(f"[mult] done. ok={ok} fail={fail} rows={total_mult}")
   312	    else:
   313	        print("[mult] skipped (--skip-multiples)")
   314	
   315	    # 5. Meta
   316	    set_meta(conn, "last_fetch_utc", datetime.now(timezone.utc).isoformat(timespec="seconds"))
   317	    set_meta(conn, "last_snapshot_date", snapshot_date)
   318	    conn.commit()
   319	    conn.close()
   320	    print(f"[fetch_eod] done. snapshot_date={snapshot_date}")
   321	
   322	
   323	if __name__ == "__main__":
   324	    main()

exec
/bin/zsh -lc 'nl -ba app/lib/db.py' in /Users/gcc/invest-dashboard
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
    66	def ticker_to_name() -> dict[str, str]:
    67	    """Use English name if available, else Chinese, else ticker."""
    68	    df = query(
    69	        "SELECT ticker, "
    70	        "  COALESCE(name_en, name_cn, ticker) AS display_name "
    71	        "FROM universe_member GROUP BY ticker"
    72	    )
    73	    return dict(zip(df["ticker"], df["display_name"]))
    74	
    75	
    76	# ---------- prices & returns ----------
    77	@st.cache_data(ttl=300)
    78	def get_close_series(tickers: tuple[str, ...]) -> pd.DataFrame:
    79	    """Wide-format close prices: index=date, columns=ticker. Tuple for cache."""
    80	    if not tickers:
    81	        return pd.DataFrame()
    82	    placeholders = ",".join("?" * len(tickers))
    83	    df = query(
    84	        f"SELECT ticker, date, close FROM prices_daily "
    85	        f"WHERE ticker IN ({placeholders}) ORDER BY date",
    86	        tuple(tickers),
    87	    )
    88	    if df.empty:
    89	        return pd.DataFrame()
    90	    df["date"] = pd.to_datetime(df["date"])
    91	    return df.pivot(index="date", columns="ticker", values="close").sort_index()
    92	
    93	
    94	def compute_returns(closes: pd.DataFrame) -> pd.DataFrame:
    95	    """Per-ticker return windows. Each ticker uses its OWN last valid close —
    96	    avoids ragged-tail bug across markets (JP closes earlier than US).
    97	    Output index=ticker, columns=[last, 1d_%, 5d_%, 1m_%, ytd_%, 60d_%]."""
    98	    if closes.empty:
    99	        return pd.DataFrame()
   100	
   101	    closes = closes.sort_index()
   102	    out: dict[str, dict[str, float | None]] = {}
   103	
   104	    NAN = float("nan")
   105	    for ticker in closes.columns:
   106	        ser = closes[ticker].dropna()
   107	        if ser.empty:
   108	            out[ticker] = {k: NAN for k in ("last", "1d_%", "5d_%", "1m_%", "ytd_%", "60d_%")}
   109	            continue
   110	
   111	        last = float(ser.iloc[-1])
   112	
   113	        def ret_back(n: int) -> float:
   114	            if len(ser) <= n:
   115	                return NAN
   116	            prev = ser.iloc[-n - 1]
   117	            if pd.isna(prev) or prev == 0:
   118	                return NAN
   119	            return float((ser.iloc[-1] / prev - 1) * 100)
   120	
   121	        # YTD: first close in current year (use each ticker's own anchor)
   122	        year = ser.index.max().year
   123	        this_year = ser[ser.index >= pd.Timestamp(f"{year}-01-01")]
   124	        if not this_year.empty and this_year.iloc[0] != 0:
   125	            ytd = float((ser.iloc[-1] / this_year.iloc[0] - 1) * 100)
   126	        else:
   127	            ytd = NAN
   128	
   129	        out[ticker] = {
   130	            "last": last,
   131	            "1d_%": ret_back(1),
   132	            "5d_%": ret_back(5),
   133	            "1m_%": ret_back(21),
   134	            "ytd_%": ytd,
   135	            "60d_%": ret_back(60),
   136	        }
   137	
   138	    return pd.DataFrame.from_dict(out, orient="index")
   139	
   140	
   141	# ---------- multiples ----------
   142	@st.cache_data(ttl=300)
   143	def latest_multiples(tickers: tuple[str, ...]) -> pd.DataFrame:
   144	    """Latest multiples_daily snapshot per ticker."""
   145	    if not tickers:
   146	        return pd.DataFrame()
   147	    placeholders = ",".join("?" * len(tickers))
   148	    df = query(
   149	        f"""
   150	        SELECT m.* FROM multiples_daily m
   151	        INNER JOIN (
   152	          SELECT ticker, MAX(date) AS max_date
   153	          FROM multiples_daily
   154	          WHERE ticker IN ({placeholders})
   155	          GROUP BY ticker
   156	        ) latest
   157	        ON m.ticker = latest.ticker AND m.date = latest.max_date
   158	        """,
   159	        tuple(tickers),
   160	    )
   161	    if df.empty:
   162	        return df
   163	    return df.set_index("ticker")
   164	
   165	
   166	# ---------- top movers ----------
   167	@st.cache_data(ttl=300)
   168	def top_movers(n: int = 10) -> tuple[pd.DataFrame, pd.DataFrame]:
   169	    """Top n gainers and losers by 1-day return across all universe tickers."""
   170	    tickers = tuple(all_tickers())
   171	    closes = get_close_series(tickers)
   172	    rets = compute_returns(closes)
   173	    if rets.empty:
   174	        return pd.DataFrame(), pd.DataFrame()
   175	    name_map = ticker_to_name()
   176	    rets["name"] = rets.index.map(name_map)
   177	    rets = rets[["name", "last", "1d_%", "5d_%", "1m_%", "ytd_%"]]
   178	    gainers = rets.sort_values("1d_%", ascending=False).head(n)
   179	    losers = rets.sort_values("1d_%", ascending=True).head(n)
   180	    return gainers, losers

exec
/bin/zsh -lc 'nl -ba .github/workflows/fetch_eod.yml' in /Users/gcc/invest-dashboard
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
/bin/zsh -lc 'nl -ba jobs/load_universe.py' in /Users/gcc/invest-dashboard
exec
/bin/zsh -lc 'nl -ba app/streamlit_app.py' in /Users/gcc/invest-dashboard
 succeeded in 0ms:
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

 succeeded in 0ms:
     1	"""invest-dashboard — Home page."""
     2	
     3	from __future__ import annotations
     4	
     5	import pandas as pd
     6	import streamlit as st
     7	
     8	from lib import benchmarks as bm
     9	from lib import db
    10	from lib import format as fmt
    11	
    12	st.set_page_config(
    13	    page_title="invest-dashboard",
    14	    page_icon="📊",
    15	    layout="wide",
    16	    initial_sidebar_state="expanded",
    17	)
    18	
    19	# --- Header ---
    20	st.title("📊 Multi-Domain Investment Dashboard")
    21	st.caption(
    22	    "Sell-side healthcare coverage · v1 (P0) · data via yfinance · "
    23	    "build: `streamlit_app.py` · plan: `~/.claude/plans/modular-toasting-spindle.md`"
    24	)
    25	
    26	latest = db.latest_snapshot_date()
    27	fetch_utc = db.last_fetch_utc()
    28	col1, col2, col3 = st.columns([2, 2, 3])
    29	col1.metric("📅 Latest snapshot", latest or "—")
    30	col2.metric("🕒 Last fetch (UTC)", fetch_utc[:16] if fetch_utc else "—")
    31	n_tickers = len(db.all_tickers())
    32	col3.metric("🌐 Universe tickers", f"{n_tickers}")
    33	
    34	st.divider()
    35	
    36	# --- Benchmarks ---
    37	st.subheader("📐 Benchmarks")
    38	bench_df = bm.fetch_benchmarks()
    39	if not bench_df.empty:
    40	    show = bench_df.copy()
    41	    # Build a display DataFrame with formatted strings + bg gradient on raw values
    42	    display_cols = ["name", "last", "1d_%", "5d_%", "1m_%", "ytd_%"]
    43	    show = show[display_cols].rename(columns={
    44	        "name": "Name", "last": "Last",
    45	        "1d_%": "1D %", "5d_%": "5D %", "1m_%": "1M %", "ytd_%": "YTD %",
    46	    })
    47	    styler = (
    48	        show.style
    49	        .format({
    50	            "Last": fmt.fmt_num,
    51	            "1D %": fmt.fmt_pct,
    52	            "5D %": fmt.fmt_pct,
    53	            "1M %": fmt.fmt_pct,
    54	            "YTD %": fmt.fmt_pct,
    55	        }, na_rep="—")
    56	        .apply(fmt.style_pct_column, subset=["1D %", "5D %", "1M %", "YTD %"])
    57	    )
    58	    st.dataframe(styler, use_container_width=True)
    59	else:
    60	    st.warning("Benchmark fetch failed (yfinance live, check network).")
    61	
    62	st.divider()
    63	
    64	# --- Top movers ---
    65	st.subheader("🏆 Today's Top Movers (across all 7 healthcare sectors)")
    66	gainers, losers = db.top_movers(n=10)
    67	if gainers.empty:
    68	    st.info("No price data — run `jobs/fetch_eod.py --backfill-days 30`.")
    69	else:
    70	    movers_col1, movers_col2 = st.columns(2)
    71	    pct_cols = ["1d_%", "5d_%", "1m_%", "ytd_%"]
    72	    rename_map = {"name": "Name", "last": "Last",
    73	                  "1d_%": "1D %", "5d_%": "5D %", "1m_%": "1M %", "ytd_%": "YTD %"}
    74	
    75	    with movers_col1:
    76	        st.markdown("##### 🟢 Top 10 Gainers")
    77	        g = gainers.rename(columns=rename_map)
    78	        styler = (
    79	            g.style
    80	            .format({"Last": fmt.fmt_num, "1D %": fmt.fmt_pct,
    81	                     "5D %": fmt.fmt_pct, "1M %": fmt.fmt_pct, "YTD %": fmt.fmt_pct},
    82	                    na_rep="—")
    83	            .apply(fmt.style_pct_column, subset=["1D %", "5D %", "1M %", "YTD %"])
    84	        )
    85	        st.dataframe(styler, use_container_width=True)
    86	
    87	    with movers_col2:
    88	        st.markdown("##### 🔴 Top 10 Drags")
    89	        l = losers.rename(columns=rename_map)
    90	        styler = (
    91	            l.style
    92	            .format({"Last": fmt.fmt_num, "1D %": fmt.fmt_pct,
    93	                     "5D %": fmt.fmt_pct, "1M %": fmt.fmt_pct, "YTD %": fmt.fmt_pct},
    94	                    na_rep="—")
    95	            .apply(fmt.style_pct_column, subset=["1D %", "5D %", "1M %", "YTD %"])
    96	        )
    97	        st.dataframe(styler, use_container_width=True)
    98	
    99	st.divider()
   100	
   101	# --- Universe ---
   102	st.subheader("🌐 Universe Coverage")
   103	uni = db.universe_summary()
   104	if not uni.empty:
   105	    st.dataframe(uni.rename(columns={"domain": "Domain", "sector": "Sector", "n": "Tickers"}),
   106	                 use_container_width=True, hide_index=True)
   107	else:
   108	    st.warning("universe_member empty — run `jobs/load_universe.py`")
   109	
   110	# --- Footer ---
   111	st.divider()
   112	st.caption(
   113	    "⚠️ **Data caveat**: valuation multiples are from **yfinance** "
   114	    "(trailing P/E + 12M forward P/E). Multi-year forward (25E / 26E / 27E) "
   115	    "requires Bloomberg / FactSet and is **not in scope**. "
   116	    "Use this dashboard for quick visual scan; refer to your manual Excel comp tables for precise consensus."
   117	)
   118	st.caption(
   119	    f"Repo: [github.com/chenhongdao2-blip/invest-dashboard](https://github.com/chenhongdao2-blip/invest-dashboard) · "
   120	    f"Data: SQLite committed in repo · "
   121	    f"Auto-update: GitHub Actions cron (22:30 UTC US + 09:00 UTC HK)"
   122	)

exec
/bin/zsh -lc 'nl -ba "app/pages/1_🏥_Healthcare.py"' in /Users/gcc/invest-dashboard
exec
/bin/zsh -lc 'nl -ba "app/pages/2_🔥_Sector_Heatmap.py"' in /Users/gcc/invest-dashboard
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
    14	st.set_page_config(page_title="Healthcare · invest-dashboard", page_icon="🏥", layout="wide")
    15	
    16	REPO_ROOT = Path(__file__).resolve().parent.parent.parent
    17	DOMAIN_CFG = REPO_ROOT / "config" / "domains" / "healthcare.yml"
    18	
    19	
    20	@st.cache_data(ttl=600)
    21	def load_domain_cfg() -> dict:
    22	    with DOMAIN_CFG.open() as f:
    23	        return yaml.safe_load(f)
    24	
    25	
    26	cfg = load_domain_cfg()
    27	st.title(f"{cfg.get('emoji', '🏥')} {cfg['name']}")
    28	st.caption(cfg.get("description", "").strip())
    29	
    30	# --- 7 sector aggregate summary ---
    31	st.subheader("📊 Sector summary (mean returns per sector)")
    32	
    33	rows = []
    34	all_returns_by_sector: dict[str, pd.DataFrame] = {}
    35	for sec in cfg["sectors"]:
    36	    uni = db.sector_tickers("healthcare", sec["id"])
    37	    tickers = tuple(uni["ticker"].tolist())
    38	    if not tickers:
    39	        continue
    40	    closes = db.get_close_series(tickers)
    41	    rets = db.compute_returns(closes)
    42	    if rets.empty:
    43	        continue
    44	    all_returns_by_sector[sec["id"]] = rets
    45	    rows.append({
    46	        "Sector": sec["name"],
    47	        "Tickers": len(tickers),
    48	        "1D % avg": rets["1d_%"].mean(),
    49	        "5D % avg": rets["5d_%"].mean(),
    50	        "1M % avg": rets["1m_%"].mean(),
    51	        "YTD % avg": rets["ytd_%"].mean(),
    52	        "Benchmark": sec.get("benchmark", "—"),
    53	    })
    54	
    55	if not rows:
    56	    st.warning("No sector data — backfill needed.")
    57	else:
    58	    summary = pd.DataFrame(rows)
    59	    pct_cols = ["1D % avg", "5D % avg", "1M % avg", "YTD % avg"]
    60	    styler = (
    61	        summary.style
    62	        .format({c: fmt.fmt_pct for c in pct_cols}, na_rep="—")
    63	        .apply(fmt.style_pct_column, subset=pct_cols)
    64	    )
    65	    st.dataframe(styler, use_container_width=True, hide_index=True)
    66	
    67	st.divider()
    68	
    69	# --- Domain benchmark snapshot ---
    70	st.subheader("📐 Domain benchmark (XLV) & peers")
    71	bench_df = bm.fetch_benchmarks()
    72	if not bench_df.empty:
    73	    focus = ["XLV", "XBI", "XPH", "IXJ", "IHF", "IHI"]
    74	    sub = bench_df.loc[bench_df.index.intersection(focus)].copy()
    75	    sub = sub.rename(columns={
    76	        "name": "Name", "last": "Last",
    77	        "1d_%": "1D %", "5d_%": "5D %", "1m_%": "1M %", "ytd_%": "YTD %",
    78	    })
    79	    styler = (
    80	        sub.style
    81	        .format({"Last": fmt.fmt_num, "1D %": fmt.fmt_pct,
    82	                 "5D %": fmt.fmt_pct, "1M %": fmt.fmt_pct, "YTD %": fmt.fmt_pct},
    83	                na_rep="—")
    84	        .apply(fmt.style_pct_column, subset=["1D %", "5D %", "1M %", "YTD %"])
    85	    )
    86	    st.dataframe(styler, use_container_width=True)
    87	
    88	st.divider()
    89	
    90	# --- Per-sector top 3 movers / drags ---
    91	st.subheader("🎯 Per-sector top 3 movers / drags (1D)")
    92	
    93	name_map = db.ticker_to_name()
    94	for sec in cfg["sectors"]:
    95	    rets = all_returns_by_sector.get(sec["id"])
    96	    if rets is None or rets.empty:
    97	        continue
    98	    with st.expander(f"**{sec['name']}**  ({len(rets)} tickers)"):
    99	        rets = rets.copy()
   100	        rets["name"] = rets.index.map(name_map)
   101	        rets = rets[["name", "last", "1d_%", "5d_%", "1m_%", "ytd_%"]]
   102	        rets.index.name = "Ticker"
   103	
   104	        c1, c2 = st.columns(2)
   105	        gainers = rets.sort_values("1d_%", ascending=False).head(3)
   106	        drags = rets.sort_values("1d_%", ascending=True).head(3)
   107	        with c1:
   108	            st.markdown("🟢 Top 3 gainers (1D)")
   109	            styler = (
   110	                gainers.rename(columns={"name": "Name", "last": "Last",
   111	                                        "1d_%": "1D %", "5d_%": "5D %",
   112	                                        "1m_%": "1M %", "ytd_%": "YTD %"}).style
   113	                .format({"Last": fmt.fmt_num, "1D %": fmt.fmt_pct,
   114	                         "5D %": fmt.fmt_pct, "1M %": fmt.fmt_pct, "YTD %": fmt.fmt_pct},
   115	                        na_rep="—")
   116	                .apply(fmt.style_pct_column, subset=["1D %", "5D %", "1M %", "YTD %"])
   117	            )
   118	            st.dataframe(styler, use_container_width=True)
   119	        with c2:
   120	            st.markdown("🔴 Top 3 drags (1D)")
   121	            styler = (
   122	                drags.rename(columns={"name": "Name", "last": "Last",
   123	                                      "1d_%": "1D %", "5d_%": "5D %",
   124	                                      "1m_%": "1M %", "ytd_%": "YTD %"}).style
   125	                .format({"Last": fmt.fmt_num, "1D %": fmt.fmt_pct,
   126	                         "5D %": fmt.fmt_pct, "1M %": fmt.fmt_pct, "YTD %": fmt.fmt_pct},
   127	                        na_rep="—")
   128	                .apply(fmt.style_pct_column, subset=["1D %", "5D %", "1M %", "YTD %"])
   129	            )
   130	            st.dataframe(styler, use_container_width=True)

 succeeded in 0ms:
     1	"""Sector Heatmap — multiples + returns per sector with color gradient."""
     2	
     3	from __future__ import annotations
     4	
     5	import pandas as pd
     6	import streamlit as st
     7	import yaml
     8	from pathlib import Path
     9	
    10	from lib import db
    11	from lib import format as fmt
    12	
    13	st.set_page_config(page_title="Sector Heatmap · invest-dashboard", page_icon="🔥", layout="wide")
    14	
    15	REPO_ROOT = Path(__file__).resolve().parent.parent.parent
    16	DOMAIN_CFG = REPO_ROOT / "config" / "domains" / "healthcare.yml"
    17	
    18	
    19	@st.cache_data(ttl=600)
    20	def load_domain_cfg() -> dict:
    21	    with DOMAIN_CFG.open() as f:
    22	        return yaml.safe_load(f)
    23	
    24	
    25	cfg = load_domain_cfg()
    26	
    27	st.title("🔥 Sector Heatmap")
    28	st.caption("Cross-sectional snapshot per sector. Multiples from yfinance — trailing + 12M forward only.")
    29	
    30	# --- Sector picker ---
    31	sector_options = [(sec["id"], sec["name"]) for sec in cfg["sectors"]]
    32	default_idx = next((i for i, s in enumerate(sector_options) if s[0] == "biotech"), 0)
    33	selected = st.selectbox(
    34	    "Pick sector",
    35	    options=[s[0] for s in sector_options],
    36	    format_func=lambda x: next(s[1] for s in sector_options if s[0] == x),
    37	    index=default_idx,
    38	)
    39	
    40	# --- Load ---
    41	uni = db.sector_tickers("healthcare", selected)
    42	tickers = tuple(uni["ticker"].tolist())
    43	if not tickers:
    44	    st.warning("No tickers in this sector — check config/universes/")
    45	    st.stop()
    46	
    47	closes = db.get_close_series(tickers)
    48	rets = db.compute_returns(closes)
    49	mults = db.latest_multiples(tickers)
    50	name_map = db.ticker_to_name()
    51	
    52	# Merge: returns + multiples
    53	merged = rets.copy() if not rets.empty else pd.DataFrame(index=list(tickers))
    54	merged["Name"] = pd.Series(name_map).reindex(merged.index)
    55	merged = merged.join(mults[["market_cap_usd", "trailing_pe", "forward_pe",
    56	                             "ev_ebitda", "ev_sales", "fcf_yield", "pb"]],
    57	                     how="left")
    58	
    59	# Region annotation
    60	region_map = uni.set_index("ticker")["region"].to_dict()
    61	merged["Region"] = pd.Series(region_map).reindex(merged.index)
    62	
    63	# Reorder columns
    64	display = merged[["Name", "Region", "market_cap_usd",
    65	                  "ytd_%", "1m_%", "5d_%", "1d_%",
    66	                  "trailing_pe", "forward_pe", "ev_ebitda", "ev_sales",
    67	                  "fcf_yield", "pb"]].copy()
    68	display.columns = ["Name", "Region", "Mcap USD",
    69	                    "YTD %", "1M %", "5D %", "1D %",
    70	                    "Trail P/E", "Fwd P/E", "EV/EBITDA", "EV/Sales",
    71	                    "FCF Yld", "P/B"]
    72	display.index.name = "Ticker"
    73	
    74	# Sort by YTD desc by default
    75	display = display.sort_values("YTD %", ascending=False, na_position="last")
    76	
    77	# --- Heatmap styling ---
    78	pct_cols = ["YTD %", "1M %", "5D %", "1D %"]
    79	low_good_cols = ["Trail P/E", "Fwd P/E", "EV/EBITDA", "EV/Sales", "P/B"]
    80	high_good_cols = ["FCF Yld"]
    81	
    82	styler = display.style.format({
    83	    "Mcap USD": fmt.fmt_money_b,
    84	    "YTD %": fmt.fmt_pct,
    85	    "1M %": fmt.fmt_pct,
    86	    "5D %": fmt.fmt_pct,
    87	    "1D %": fmt.fmt_pct,
    88	    "Trail P/E": fmt.fmt_ratio,
    89	    "Fwd P/E": fmt.fmt_ratio,
    90	    "EV/EBITDA": fmt.fmt_ratio,
    91	    "EV/Sales": fmt.fmt_ratio,
    92	    "FCF Yld": fmt.fmt_pct_decimal,
    93	    "P/B": fmt.fmt_ratio,
    94	}, na_rep="—")
    95	
    96	# Color gradient for return columns
    97	styler = styler.apply(fmt.background_gradient_diverging, subset=pct_cols)
    98	
    99	# Lower-is-better for multiples (P/E etc.)
   100	for col in low_good_cols:
   101	    styler = styler.apply(fmt.background_gradient_low_good, subset=[col])
   102	
   103	# Higher-is-better for FCF Yield (reverse colors)
   104	for col in high_good_cols:
   105	    styler = styler.apply(
   106	        lambda s: fmt.background_gradient_low_good(s, low_color="#dc2626", high_color="#16a34a"),
   107	        subset=[col],
   108	    )
   109	
   110	st.dataframe(styler, use_container_width=True, height=600)
   111	
   112	# --- Sector aggregates ---
   113	st.subheader("📊 Sector aggregates")
   114	
   115	agg_rows = {}
   116	for col in ["YTD %", "1M %", "5D %", "1D %", "Trail P/E", "Fwd P/E",
   117	            "EV/EBITDA", "EV/Sales", "FCF Yld", "P/B"]:
   118	    s = display[col]
   119	    s_clean = s.dropna()
   120	    agg_rows[col] = {
   121	        "Mean": s_clean.mean() if not s_clean.empty else None,
   122	        "Median": s_clean.median() if not s_clean.empty else None,
   123	        "Min": s_clean.min() if not s_clean.empty else None,
   124	        "Max": s_clean.max() if not s_clean.empty else None,
   125	    }
   126	# Mkt-cap weighted average for multiples
   127	mcap_w = display["Mcap USD"].fillna(0)
   128	if mcap_w.sum() > 0:
   129	    weights = mcap_w / mcap_w.sum()
   130	    for col in ["Trail P/E", "Fwd P/E", "EV/EBITDA", "EV/Sales", "FCF Yld", "P/B"]:
   131	        valid = display[col].notna()
   132	        if valid.any():
   133	            w = weights[valid] / weights[valid].sum()
   134	            wm = (display.loc[valid, col] * w).sum()
   135	            agg_rows[col]["Wgt avg"] = wm
   136	
   137	agg = pd.DataFrame(agg_rows).T
   138	agg = agg[["Mean", "Median", "Min", "Max"] + (["Wgt avg"] if "Wgt avg" in agg.columns else [])]
   139	
   140	def _fmt_cell(col_label: str, v) -> str:
   141	    if v is None or (isinstance(v, float) and pd.isna(v)):
   142	        return "—"
   143	    if "%" in col_label:
   144	        return f"{v:+.2f}%"
   145	    if col_label in ["FCF Yld"]:
   146	        return f"{v * 100:+.2f}%"
   147	    return f"{v:.1f}x"
   148	
   149	# Build fresh string DataFrame to avoid pandas 2.x dtype coercion error
   150	agg_str = {
   151	    idx: {col: _fmt_cell(idx, agg.at[idx, col]) for col in agg.columns}
   152	    for idx in agg.index
   153	}
   154	agg_fmt = pd.DataFrame.from_dict(agg_str, orient="index")
   155	
   156	st.dataframe(agg_fmt, use_container_width=True)
   157	
   158	# --- caveats ---
   159	st.caption(
   160	    "🎨 **Color legend**: Returns (YTD/1M/5D/1D) green=up, red=down. "
   161	    "Multiples (P/E, EV/EBITDA): green=lower=cheaper, red=higher=expensive. "
   162	    "FCF Yield: green=higher=better."
   163	)
   164	st.caption(
   165	    f"Sector: **{next(s['name'] for s in cfg['sectors'] if s['id'] == selected)}** "
   166	    f"({len(display)} tickers) · Latest data: {db.latest_snapshot_date()}"
   167	)

exec
/bin/zsh -lc 'nl -ba app/lib/format.py' in /Users/gcc/invest-dashboard
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
    66	def color_pct(v) -> str:
    67	    """Return CSS color string for a percentage value."""
    68	    if v is None or (isinstance(v, float) and pd.isna(v)):
    69	        return f"color: {NEUTRAL}"
    70	    if v > 0:
    71	        return f"color: {GREEN}; font-weight: 600"
    72	    if v < 0:
    73	        return f"color: {RED}; font-weight: 600"
    74	    return f"color: {NEUTRAL}"
    75	
    76	
    77	def style_pct_column(s: pd.Series) -> list[str]:
    78	    """For DataFrame.style.apply: color each cell red/green."""
    79	    return [color_pct(v) for v in s]
    80	
    81	
    82	def background_gradient_diverging(
    83	    s: pd.Series,
    84	    mid: float = 0,
    85	    pos_color: str = "#16a34a",
    86	    neg_color: str = "#dc2626",
    87	    intensity: float = 0.35,
    88	) -> list[str]:
    89	    """Diverging color background for numeric Series. Intensity 0-1 (alpha)."""
    90	    out = []
    91	    s_clean = s.dropna()
    92	    if s_clean.empty:
    93	        return [""] * len(s)
    94	    max_abs = max(abs(s_clean.min() - mid), abs(s_clean.max() - mid)) or 1
    95	    for v in s:
    96	        if pd.isna(v):
    97	            out.append("")
    98	            continue
    99	        if v >= mid:
   100	            ratio = min(abs(v - mid) / max_abs, 1.0) * intensity
   101	            color = pos_color
   102	        else:
   103	            ratio = min(abs(v - mid) / max_abs, 1.0) * intensity
   104	            color = neg_color
   105	        out.append(f"background-color: {color}{int(ratio * 255):02x}")
   106	    return out
   107	
   108	
   109	def background_gradient_low_good(
   110	    s: pd.Series,
   111	    low_color: str = "#16a34a",
   112	    high_color: str = "#dc2626",
   113	    intensity: float = 0.30,
   114	) -> list[str]:
   115	    """For ratios where lower is better (P/E, EV/EBITDA). Green = low, Red = high."""
   116	    out = []
   117	    s_clean = s.dropna()
   118	    if s_clean.empty or len(s_clean) < 2:
   119	        return [""] * len(s)
   120	    lo, hi = s_clean.min(), s_clean.max()
   121	    if hi == lo:
   122	        return [""] * len(s)
   123	    for v in s:
   124	        if pd.isna(v) or v < 0:    # negative ratios = neg earnings, skip
   125	            out.append("")
   126	            continue
   127	        ratio_lo = (hi - v) / (hi - lo) * intensity   # closer to low = greener
   128	        ratio_hi = (v - lo) / (hi - lo) * intensity
   129	        if ratio_lo >= ratio_hi:
   130	            out.append(f"background-color: {low_color}{int(ratio_lo * 255):02x}")
   131	        else:
   132	            out.append(f"background-color: {high_color}{int(ratio_hi * 255):02x}")
   133	    return out

codex
The main structural risk is starting to look less like the four-table schema and more like deploy/runtime assumptions: the app reads local committed SQLite, while Actions mutates it later. I’m checking the actual DB contents and dependency/runtime details before ranking that.
exec
/bin/zsh -lc 'nl -ba requirements.txt' in /Users/gcc/invest-dashboard
 succeeded in 0ms:
     1	streamlit>=1.36
     2	yfinance>=0.2.43
     3	pandas>=2.2
     4	pyyaml>=6.0
     5	plotly>=5.22
     6	numpy>=1.26

exec
/bin/zsh -lc "find .streamlit -maxdepth 2 -type f -print -exec nl -ba {} \\;" in /Users/gcc/invest-dashboard
 succeeded in 0ms:
.streamlit/config.toml
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
/bin/zsh -lc "sqlite3 data/snapshots.db '.schema'" in /Users/gcc/invest-dashboard
 succeeded in 0ms:
CREATE TABLE prices_daily (
    ticker     TEXT NOT NULL,
    date       TEXT NOT NULL,        -- YYYY-MM-DD
    open       REAL,
    high       REAL,
    low        REAL,
    close      REAL,
    adj_close  REAL,
    volume     INTEGER,
    currency   TEXT,                  -- USD / HKD / JPY / KRW / EUR
    PRIMARY KEY (ticker, date)
);
CREATE INDEX idx_prices_date ON prices_daily(date);
CREATE TABLE multiples_daily (
    ticker            TEXT NOT NULL,
    date              TEXT NOT NULL,
    market_cap_usd    REAL,
    trailing_pe       REAL,
    forward_pe        REAL,
    trailing_eps      REAL,
    forward_eps       REAL,
    ev_ebitda         REAL,
    ev_sales          REAL,
    fcf_yield         REAL,
    peg               REAL,
    pb                REAL,
    ytd_return        REAL,
    last_price        REAL,
    PRIMARY KEY (ticker, date)
);
CREATE INDEX idx_mult_date ON multiples_daily(date);
CREATE TABLE universe_member (
    domain    TEXT NOT NULL,
    sector    TEXT NOT NULL,
    ticker    TEXT NOT NULL,
    name_cn   TEXT,
    name_en   TEXT,
    region    TEXT,
    note      TEXT,
    PRIMARY KEY (domain, sector, ticker)
);
CREATE INDEX idx_um_ticker ON universe_member(ticker);
CREATE INDEX idx_um_domain_sector ON universe_member(domain, sector);
CREATE TABLE meta (
    key         TEXT PRIMARY KEY,
    value       TEXT,
    updated_at  TEXT
);

exec
/bin/zsh -lc 'sqlite3 data/snapshots.db "select currency,count(*) from prices_daily group by currency order by currency; select region,count(distinct ticker) from universe_member group by region order by region; select ticker,count(distinct currency) c, group_concat(distinct currency) from prices_daily group by ticker having c>1 limit 20;"' in /Users/gcc/invest-dashboard
exec
/bin/zsh -lc "sqlite3 data/snapshots.db \"select 'prices', count(*), count(distinct ticker), min(date), max(date) from prices_daily union all select 'multiples', count(*), count(distinct ticker), min(date), max(date) from multiples_daily union all select 'universe', count(*), count(distinct ticker), min(domain||':'||sector), max(domain||':'||sector) from universe_member;\"" in /Users/gcc/invest-dashboard
 succeeded in 0ms:
CNY|120
HKD|624
JPY|400
KRW|41
USD|3116
CN|3
HK|16
JP|10
KR|1
US|76

 succeeded in 0ms:
prices|4301|106|2026-03-30|2026-05-28
multiples|106|106|2026-05-28|2026-05-28
universe|120|106|healthcare:_coverage|healthcare:pharma

codex
A concrete correctness gap is confirmed: FX is fetched, but price rows remain local currency and only `market_cap_usd` is converted. I’m also checking whether that leaks into current views or just blocks later scanner/drill-down work.
exec
/bin/zsh -lc 'sqlite3 data/snapshots.db "select ticker, date, close, adj_close, currency from prices_daily where currency!='"'USD' order by ticker,date limit 10; select ticker, market_cap_usd, last_price from multiples_daily where ticker in (select distinct ticker from prices_daily where currency"'!='"'USD') order by ticker limit 10;\"" in /Users/gcc/invest-dashboard
 succeeded in 0ms:
1093.HK|2026-03-30|9.27999973297119|9.27999973297119|HKD
1093.HK|2026-03-31|9.10000038146973|9.10000038146973|HKD
1093.HK|2026-04-01|9.61999988555908|9.61999988555908|HKD
1093.HK|2026-04-02|9.71000003814697|9.71000003814697|HKD
1093.HK|2026-04-08|9.3100004196167|9.3100004196167|HKD
1093.HK|2026-04-09|9.10999965667725|9.10999965667725|HKD
1093.HK|2026-04-10|9.26000022888184|9.26000022888184|HKD
1093.HK|2026-04-13|9.0|9.0|HKD
1093.HK|2026-04-14|9.15999984741211|9.15999984741211|HKD
1093.HK|2026-04-15|9.4399995803833|9.4399995803833|HKD
1093.HK|10193892307.461|7.0
1177.HK|11045319686.1298|4.85
1530.HK|5676944165.37352|17.78
1681.HK|1511208888.68801|14.07
1801.HK|17120414123.9596|77.3
207940.KS|42178192884.6914|1373000.0
2162.HK|2215526257.29646|58.9
2256.HK|850658917.154004|10.04
2269.HK|17100185052.8295|32.4
2359.HK|47126225664.4843|123.7

exec
/bin/zsh -lc 'nl -ba app/lib/benchmarks.py' in /Users/gcc/invest-dashboard
exec
/bin/zsh -lc 'nl -ba app/lib/charts.py' in /Users/gcc/invest-dashboard
 succeeded in 0ms:
     1	"""Live benchmark data via yfinance (cached 30 min).
     2	
     3	Benchmarks are NOT in our SQLite universe — fetched on demand.
     4	"""
     5	
     6	from __future__ import annotations
     7	
     8	from datetime import date, datetime, timedelta, timezone
     9	
    10	import pandas as pd
    11	import streamlit as st
    12	import yfinance as yf
    13	
    14	BENCHMARKS = {
    15	    "XLV":   "Health Care Select Sector",
    16	    "XBI":   "S&P Biotech",
    17	    "XPH":   "S&P Pharmaceuticals",
    18	    "IXJ":   "iShares Global Healthcare",
    19	    "IHF":   "US Healthcare Providers",
    20	    "IHI":   "US Medical Devices",
    21	    "^HSI":  "Hang Seng Index",
    22	    "^GSPC": "S&P 500",
    23	}
    24	
    25	
    26	@st.cache_data(ttl=1800, show_spinner="Fetching benchmarks…")
    27	def fetch_benchmarks() -> pd.DataFrame:
    28	    """Return a tidy DataFrame: index=ticker, columns=[name, last, 1d, 5d, 1m, ytd]."""
    29	    tickers = list(BENCHMARKS.keys())
    30	    today = date.today()
    31	    start = (today - timedelta(days=180)).isoformat()
    32	    end = (today + timedelta(days=1)).isoformat()
    33	    try:
    34	        d = yf.download(
    35	            tickers, start=start, end=end,
    36	            auto_adjust=True, progress=False, threads=True, group_by="ticker",
    37	        )
    38	    except Exception as e:
    39	        return pd.DataFrame()
    40	
    41	    rows = []
    42	    for t in tickers:
    43	        try:
    44	            if t in d.columns.get_level_values(0):
    45	                ser = d[t]["Close"].dropna().sort_index()
    46	            else:
    47	                ser = pd.Series(dtype=float)
    48	            if ser.empty:
    49	                rows.append({"ticker": t, "name": BENCHMARKS[t]})
    50	                continue
    51	            last = float(ser.iloc[-1])
    52	
    53	            def ret(n: int) -> float | None:
    54	                if len(ser) < n + 1:
    55	                    return None
    56	                return float((ser.iloc[-1] / ser.iloc[-n - 1] - 1) * 100)
    57	
    58	            # YTD
    59	            ytd = None
    60	            this_year_start = pd.Timestamp(f"{today.year}-01-01")
    61	            ytd_ser = ser[ser.index >= this_year_start]
    62	            if not ytd_ser.empty:
    63	                ytd = float((ser.iloc[-1] / ytd_ser.iloc[0] - 1) * 100)
    64	
    65	            rows.append({
    66	                "ticker": t,
    67	                "name": BENCHMARKS[t],
    68	                "last": last,
    69	                "1d_%": ret(1),
    70	                "5d_%": ret(5),
    71	                "1m_%": ret(21),
    72	                "ytd_%": ytd,
    73	            })
    74	        except Exception:
    75	            rows.append({"ticker": t, "name": BENCHMARKS[t]})
    76	
    77	    df = pd.DataFrame(rows).set_index("ticker")
    78	    return df

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

exec
/bin/zsh -lc 'python -m compileall jobs app' in /Users/gcc/invest-dashboard
 exited 127 in 0ms:
zsh:1: command not found: python

exec
/bin/zsh -lc 'sqlite3 data/snapshots.db "select ticker, count(*) n, min(date), max(date) from prices_daily group by ticker having n<5 order by n, ticker limit 20; select ticker from universe_member where ticker not in (select distinct ticker from prices_daily) order by ticker limit 20; select ticker from universe_member where ticker not in (select distinct ticker from multiples_daily) order by ticker limit 20;"' in /Users/gcc/invest-dashboard
 succeeded in 0ms:
exec
/bin/zsh -lc 'sqlite3 data/snapshots.db "select m.ticker, u.region, m.last_price, m.market_cap_usd, p.currency, p.close from multiples_daily m join (select ticker, max(date) maxd from prices_daily group by ticker) lp on m.ticker=lp.ticker join prices_daily p on p.ticker=lp.ticker and p.date=lp.maxd join universe_member u on u.ticker=m.ticker where u.region!='"'US' group by m.ticker order by m.ticker limit 20;\"" in /Users/gcc/invest-dashboard
 succeeded in 0ms:
1093.HK|HK|7.0|10193892307.461|HKD|7.01999998092651
1177.HK|HK|4.85|11045319686.1298|HKD|4.84999990463257
1530.HK|HK|17.78|5676944165.37352|HKD|17.7800006866455
1681.HK|HK|14.07|1511208888.68801|HKD|14.0699996948242
1801.HK|HK|77.3|17120414123.9596|HKD|77.3000030517578
207940.KS|KR|1373000.0|42178192884.6914|KRW|1373000.0
2162.HK|HK|58.9|2215526257.29646|HKD|58.7999992370605
2256.HK|HK|10.04|850658917.154004|HKD|10.0500001907349
2269.HK|HK|32.4|17100185052.8295|HKD|32.3600006103516
2359.HK|HK|123.7|47126225664.4843|HKD|123.699996948242
2413.T|JP|1379.5|5770323036.54004|JPY|1379.5
2506.HK|HK|83.25|1284877981.68033|HKD|83.25
2616.HK|HK|7.72|1575353165.61104|HKD|7.71999979019165
2666.HK|HK|5.22|1342467160.94189|HKD|5.21999979019165
300760.SZ|CN|149.3|26691659887.1504|CNY|149.309997558594
300832.SZ|CN|47.45|5497413427.79593|CNY|47.4799995422363
3320.HK|HK|4.66|3738080527.43644|HKD|4.65999984741211
3692.HK|HK|32.18|24911504893.5675|HKD|32.1800003051758
4151.T|JP|2474.0|8116685177.23855|JPY|2474.0
4502.T|JP|5144.0|50931495131.5767|JPY|5144.0

exec
/bin/zsh -lc 'git status --short' in /Users/gcc/invest-dashboard
 succeeded in 0ms:
exec
/bin/zsh -lc 'python3 -m compileall jobs app' in /Users/gcc/invest-dashboard
 succeeded in 0ms:
Listing 'jobs'...
Compiling 'jobs/fetch_eod.py'...
Compiling 'jobs/init_db.py'...
Compiling 'jobs/load_universe.py'...
Listing 'app'...
Listing 'app/lib'...
Compiling 'app/lib/__init__.py'...
Compiling 'app/lib/benchmarks.py'...
Compiling 'app/lib/charts.py'...
Compiling 'app/lib/db.py'...
Compiling 'app/lib/format.py'...
Listing 'app/pages'...
Compiling 'app/pages/1_🏥_Healthcare.py'...
Compiling 'app/pages/2_🔥_Sector_Heatmap.py'...
Compiling 'app/streamlit_app.py'...

exec
/bin/zsh -lc 'nl -ba config/domains/healthcare.yml' in /Users/gcc/invest-dashboard
 succeeded in 0ms:
     1	# Healthcare domain config
     2	name: Healthcare
     3	emoji: 🏥
     4	description: |
     5	  Sell-side healthcare coverage across 7 sub-sectors.
     6	  Includes US / HK / JP / KR / EU-listed tickers.
     7	
     8	# 板块列表（按 universe YAML 命名）
     9	sectors:
    10	  - id: biotech
    11	    name: Biotech
    12	    universe_file: hc_biotech.yml
    13	    benchmark: XBI            # SPDR S&P Biotech ETF
    14	  - id: hospital_care
    15	    name: Hospital Care
    16	    universe_file: hc_hospital_care.yml
    17	    benchmark: XLV            # Health Care Select Sector SPDR
    18	  - id: hc_ai
    19	    name: Healthcare + AI
    20	    universe_file: hc_ai.yml
    21	    benchmark: XLV
    22	  - id: managed_care
    23	    name: Managed Care
    24	    universe_file: hc_managed_care.yml
    25	    benchmark: IHF            # iShares US Healthcare Providers
    26	  - id: medtech
    27	    name: Medtech
    28	    universe_file: hc_medtech.yml
    29	    benchmark: IHI            # iShares US Medical Devices
    30	  - id: cxo
    31	    name: CXO & Life Sciences
    32	    universe_file: hc_cxo.yml
    33	    benchmark: XLV
    34	  - id: pharma
    35	    name: Pharma
    36	    universe_file: hc_pharma.yml
    37	    benchmark: XPH            # SPDR S&P Pharmaceuticals
    38	
    39	# Domain-level benchmarks
    40	benchmarks:
    41	  primary: XLV
    42	  secondary:
    43	    - XBI                     # Biotech
    44	    - XPH                     # Pharma
    45	    - IXJ                     # iShares Global Healthcare
    46	
    47	# CMSI 自己 cover list
    48	coverage:
    49	  universe_file: cmsi_coverage_hc.yml

exec
/bin/zsh -lc "nl -ba config/universes/cmsi_coverage_hc.yml | sed -n '1,80p'" in /Users/gcc/invest-dashboard
 succeeded in 0ms:
     1	# CMSI HK Healthcare Coverage List — 28 tickers
     2	# Source: CMSI internal coverage table (HK + US + 3 CN A-share)
     3	# Provided by George 2026-05-28
     4	# Note: 部分 ticker 与 sector universe cross-membership（dashboard 自动 dedup）
     5	sector_id: cmsi_coverage_hc
     6	domain: healthcare
     7	
     8	tickers:
     9	  # HK Listed
    10	  - ticker: 1093.HK
    11	    name_cn: 石药集团
    12	    name_en: CSPC Pharmaceutical
    13	    region: HK
    14	  - ticker: 1177.HK
    15	    name_cn: 中国生物制药
    16	    name_en: Sino Biopharm
    17	    region: HK
    18	  - ticker: 1530.HK
    19	    name_cn: 三生制药
    20	    name_en: 3SBio
    21	    region: HK
    22	  - ticker: 1681.HK
    23	    name_cn: 康臣药业
    24	    name_en: Consun Pharma
    25	    region: HK
    26	  - ticker: 1801.HK
    27	    name_cn: 信达生物
    28	    name_en: Innovent Bio
    29	    region: HK
    30	  - ticker: 2162.HK
    31	    name_cn: 康诺亚
    32	    name_en: Keymed Biosciences
    33	    region: HK
    34	  - ticker: 2256.HK
    35	    name_cn: 和誉
    36	    name_en: Abbisko
    37	    region: HK
    38	  - ticker: 2269.HK
    39	    name_cn: 药明生物
    40	    name_en: WuXi Biologics
    41	    region: HK
    42	  - ticker: 2359.HK
    43	    name_cn: 药明康德
    44	    name_en: WuXi AppTec
    45	    region: HK
    46	  - ticker: 2506.HK
    47	    name_cn: 讯飞医疗
    48	    name_en: Xunfei Healthcare Tech
    49	    region: HK
    50	  - ticker: 2616.HK
    51	    name_cn: 基石药业
    52	    name_en: CStone Pharmaceuticals
    53	    region: HK
    54	  - ticker: 2666.HK
    55	    name_cn: 环球医疗
    56	    name_en: Universal Medical
    57	    region: HK
    58	  - ticker: 3320.HK
    59	    name_cn: 华润医药
    60	    name_en: CR Pharm
    61	    region: HK
    62	  - ticker: 3692.HK
    63	    name_cn: 翰森制药
    64	    name_en: Hansoh Pharma
    65	    region: HK
    66	  - ticker: 9995.HK
    67	    name_cn: 荣昌生物
    68	    name_en: Remegen
    69	    region: HK
    70	
    71	  # US Listed
    72	  - ticker: ALNY
    73	    name_cn: 艾拉伦制药
    74	    name_en: Alnylam
    75	    region: US
    76	  - ticker: BSX
    77	    name_cn: 波士顿科学
    78	    name_en: Boston Scientific
    79	    region: US
    80	  - ticker: GPCR

exec
/bin/zsh -lc 'du -h data/snapshots.db && git count-objects -vH' in /Users/gcc/invest-dashboard
 succeeded in 0ms:
640K	data/snapshots.db
count: 60
size: 448.00 KiB
in-pack: 0
packs: 0
size-pack: 0 bytes
prune-packable: 0
garbage: 0
size-garbage: 0 bytes

exec
/bin/zsh -lc 'sqlite3 data/snapshots.db "select max(length(note)), count(*) from universe_member where note is not null and note!='"''; select ticker, note from universe_member where note is not null and note"'!='"'' limit 10;\"" in /Users/gcc/invest-dashboard
 succeeded in 0ms:
|0

codex
**Findings**

[BLOCKER] D4 Strategy Picks will not work on Streamlit Cloud if it reads `~/ic-foundry/ledger.db`. Streamlit Cloud will not have that home-directory DB, and the current app only opens repo-local `data/snapshots.db` read-only at `app/lib/db.py:11-17`. Action: export `picks_v2` into the committed dashboard DB, a private artifact, or an external DB reachable via Streamlit secrets. Do not build D4 against `~`.

[MAJOR] FX normalization is not actually implemented for prices. `prices_daily` stores only local `close` / `adj_close` plus `currency` at `jobs/init_db.py:19-29`; `fetch_eod.py` fetches FX at `jobs/fetch_eod.py:265-266` but only uses currency labels when writing prices at `jobs/fetch_eod.py:284-287`. Action: add `fx_to_usd`, `close_usd`, `adj_close_usd` or compute a USD view. For multiples, also store `currency` and `last_price_usd`; `last_price` is local while `market_cap_usd` is USD at `jobs/fetch_eod.py:221-241`.

[MAJOR] Displayed YTD is currently false with only a 60-calendar-day backfill. `compute_returns()` anchors YTD to the first available close in the current year at `app/lib/db.py:121-127`, but the DB starts `2026-03-30`, so “YTD” is really “since Mar 30”. Action: backfill from Jan 1 at minimum whenever YTD is displayed, or label it as since-first-available.

[MAJOR] `60d_%` will be mostly/all NaN after a 60-calendar-day backfill. `ret_back(60)` requires 61 valid trading closes at `app/lib/db.py:113-119` and `app/lib/db.py:135`; `--backfill-days 60` gives roughly 40-45 trading rows. Action: use ~90 calendar days for 60 trading days, or redefine as calendar-day return using date lookup.

[MAJOR] yfinance `.info` rate-limit handling is too optimistic for unattended cron. `SLEEP_BETWEEN_INFO = 0.2` at `jobs/fetch_eod.py:37-39` plus only two attempts at `jobs/fetch_eod.py:203-214` can silently produce stale/missing multiples; the job still exits success at `jobs/fetch_eod.py:293-311`. Action: exponential backoff, jitter, longer sleep, and fail the workflow if failures exceed a threshold.

[MAJOR] SQLite-in-git growth is underestimated because every daily commit stores another binary DB version in Git history. Current DB is already 640KB for 60 days; even with packing, page churn can make history grow much faster than the “1.6MB/year” working-file estimate. Action: acceptable for MVP, but plan migration before multi-year/multi-domain use. Trigger point: working DB >50-100MB or `.git` pack >200-500MB. Prefer external SQLite/Turso/Supabase or partitioned Parquet snapshots.

[MAJOR] Public IP leak risk is real in comments, even if the ticker list is acceptable. `config/universes/cmsi_coverage_hc.yml:1-3` explicitly says “CMSI internal coverage table” and names provenance. Strategy picks will be much more sensitive than coverage. Action: remove internal-source comments from public repo; keep strategy picks private or publish only derived/non-actionable labels.

[MINOR] FX pair inversion logic is correct for your listed pairs. `USDHKD=X`, `USDJPY=X`, `USDKRW=X`, `USDCNY=X`, `USDCHF=X` should invert; `EURUSD=X` and `GBPUSD=X` should not. Current `sym.startswith("USD")` logic at `jobs/fetch_eod.py:122-127` is fine. Action: add a unit test/table-driven assertion so this does not regress.

[MINOR] FX failure fallback is dangerous. If `yf.download()` fails, all currencies default to `1.0` at `jobs/fetch_eod.py:103-108`, which can make HKD/JPY/KRW market caps wildly wrong. Action: fail the job on FX failure, or reuse last good FX rates from DB instead of defaulting to 1.0.

[MINOR] Partial price batch failure is handled enough to preserve successful tickers, but missing tickers are swallowed. `fetch_prices_batch()` extracts per-ticker frames at `jobs/fetch_eod.py:160-168`, but logs no missing symbols and the workflow still succeeds. Action: log `set(batch) - set(result)` and fail if missing count crosses a threshold.

[MINOR] `fmt_ratio()` rendering negative P/E as `neg` is acceptable for biotech scanning at `app/lib/format.py:45-50`. The heatmap correctly skips coloring negative multiples at `app/lib/format.py:123-126`. Action: for scanner filters, exclude negative P/E from percentile math or bucket as “NM/neg”, not cheap.

[MINOR] `--backfill-days` minimum 5-day window is reasonable for daily cron repair at `jobs/fetch_eod.py:258-260`. It will recover short gaps. It is not enough for return windows or YTD, so treat it as operational repair only.

[MINOR] Cron timing is safe. `22:30 UTC` is after both EDT close `20:00 UTC` and EST close `21:00 UTC`; moving earlier risks winter incompleteness. `09:00 UTC` is after HK close. Keep `.github/workflows/fetch_eod.yml:4-9` as-is unless yfinance finalization latency proves lower and you explicitly split US summer/winter schedules.

[MINOR] `permissions: contents: write` is the right GitHub Actions scope for pushing the DB with `GITHUB_TOKEN` at `.github/workflows/fetch_eod.yml:17-18` and `.github/workflows/fetch_eod.yml:46-55`. A fine-grained PAT is not better unless branch protection blocks the bot or you need cross-repo writes.

[NIT] `prices_to_rows()` uses `r.get("Adj Close") or r.get("Close")` at `jobs/fetch_eod.py:181`; `NaN` is truthy, so it may not fall back to close. Action: use explicit `pd.notna()` fallback.

**Biggest Risk**

The biggest deploy-breaking risk is D4: a Streamlit Cloud app cannot read `~/ic-foundry/ledger.db`. The biggest correctness risk in current D1-D3 views is false YTD/60D due to insufficient history.

Verification: `python3 -m compileall jobs app` passes.
tokens used
74,375

```

## Concise summary

Provider completed successfully. Review the raw output for details.

## Action items

- Review the response and extract decisions you want to apply.
- Capture follow-up implementation tasks if needed.
