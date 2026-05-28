# Streamlit Community Cloud — invest-dashboard runbook

## 0. Pre-flight (already in repo)

- [x] `requirements.txt` — pinned dep ranges (streamlit / yfinance / pandas / plotly / pyyaml / numpy). yfinance must be `>=1.4,<2` (1.4.0 shipped May 2026; older `<0.3` caps lock the cloud onto an EOL minor).
- [x] `runtime.txt` → `python-3.12` (informational only; **Streamlit Community Cloud does NOT read `runtime.txt`** — Python version is selected in the Cloud UI Advanced settings. The file is kept for `uv` / `pyenv` parity)
- [x] `.python-version` → `3.12` (uv / pyenv pin for local dev)
- [x] `.streamlit/config.toml` — dark theme + headless + xsrf protection
- [x] `app/streamlit_app.py` — main entry (Streamlit auto-discovers `app/pages/*`)
- [x] `data/snapshots.db` committed (Streamlit Cloud has no writable persistent disk; SQLite-in-git is the storage)
- [x] `data/external/v5_picks.csv` + `v4_picks.csv` + `hd_picks.csv` committed
- [x] Raw `picks.db` is **gitignored** (IP scrub — see `.gitignore`)

## 1. Deploy (one-time)

1. Sign in at https://share.streamlit.io with the GitHub account that owns `chenhongdao2-blip/invest-dashboard`.
2. **New app** → pick:
   - Repository: `chenhongdao2-blip/invest-dashboard`
   - Branch: `main`
   - Main file path: `app/streamlit_app.py`
   - App URL (optional): `cmsi-invest-dashboard` → resulting URL `https://cmsi-invest-dashboard.streamlit.app`
   - **Advanced settings → Python version**: pick **3.12** explicitly (Community Cloud no longer reads `runtime.txt`; whatever Streamlit defaults to changes over time — pin it in the UI). [Streamlit docs reference](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy#optional-configure-secrets-and-python-version).
3. Click **Deploy**. First build takes ~2-3 minutes (uv install + cold cache).
4. Once it boots, copy the public URL and paste it into `README.md` `Live: ...` line (replace `TBD`).

## 2. Page slug check (emoji concern from HANDOFF §⚠️)

The page filenames use emoji (e.g. `6_🔍_Ticker_Drill.py`). Streamlit Cloud Unicode-encodes the slug, so the URL becomes `/Ticker_Drill` (emoji stripped, spaces → `_`). Hit each of these post-deploy:

```
/                       — Home
/CMSI_Coverage
/Healthcare
/Sector_Heatmap
/Strategy_Picks
/Valuation_Scanner
/Ticker_Drill
/Ticker_Drill?ticker=LLY     # deep-link smoke test
```

If any returns 404 (rare — only on very old Streamlit versions), rename the file dropping emoji + leading number (e.g. `Ticker_Drill.py`) and re-deploy.

## 3. Cron → redeploy chain

GitHub Actions runs `jobs/fetch_eod.py` twice daily (22:30 UTC + 09:00 UTC) and commits the updated `data/snapshots.db` to `main`. Streamlit Cloud watches the branch and auto-redeploys within ~1 minute of the push.

Verify after first cron tick:

```bash
gh run list --workflow=cron.yml --limit 3   # check latest GH Actions run
git log --oneline -1                         # bot commit pushed?
curl -sS https://<your-url>.streamlit.app/_stcore/health   # redeploy completed?
```

## 4. LLM Wiki memos (Ticker Drill)

`app/lib/wiki.py` resolves memos under `~/Documents/LLM Wiki/Wiki/companies/`. On Streamlit Cloud that path does not exist, so the Ticker Drill page silently falls back to "no memo" mode — price + multiples + cross-sector tags still render.

To surface memos in the cloud build:

1. Curate a sanitized subset of wiki files (no internal IP / unreleased thesis) under `data/wiki/companies/`.
2. In `app/lib/wiki.py`, change `WIKI_ROOT` to:
   ```python
   WIKI_ROOT = Path(__file__).resolve().parent.parent.parent / "data" / "wiki" / "companies"
   ```
3. Commit and push. Out of v1 scope — flagged for future iteration.

## 5. Secrets (none yet)

No third-party API keys in this stack. yfinance is unauthenticated. If you later add Tushare / AKShare / OpenAI:

- Drop into `Settings → Secrets` on the Streamlit Cloud app dashboard. Available in code as `st.secrets["KEY"]`.
- **Never** commit `.streamlit/secrets.toml` (already in `.gitignore`).

## 6. Roll back

Streamlit Cloud always serves the latest commit on the configured branch. To roll back:

```bash
git revert <bad-sha>
git push origin main
```

Within ~1 minute the previous good build is live again. No way to pin to a specific commit on the free tier.

## 7. Cost / quota

- Streamlit Community Cloud free tier: **unlimited public apps**, 1 GB RAM per app, sleeps after 7 days of no traffic (wakes on next visit, ~10 s cold start).
- GitHub Actions free tier: 2000 minutes/month for public repos. Two crons × ~30 s each × 30 days = ~30 minutes/month. **Plenty of headroom.**

## 8. Smoke test checklist post-deploy

- [ ] Home page renders, "Latest snapshot" matches the latest cron run
- [ ] CMSI Coverage table sorts numerically (header click on Mcap → desc → asc)
- [ ] Sector Heatmap tabs all 7 sectors, color gradient visible on returns
- [ ] Strategy Picks 3 tabs render charts; benchmark overlay visible
- [ ] Valuation Scanner Deep Value preset returns candidates
- [ ] Ticker Drill `?ticker=LLY` deep-link loads the LLY price chart
- [ ] Ticker Drill on `1093.HK` (would have a wiki memo locally) shows "No LLM Wiki memo for this ticker" — expected on cloud
