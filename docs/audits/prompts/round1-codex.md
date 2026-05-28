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
