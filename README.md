# invest-dashboard

> Multi-domain sell-side investment dashboard. Healthcare v1, AI 与其它 domain 后续扩展。

**Live**: [agentmental-research.streamlit.app](https://agentmental-research.streamlit.app) ([deploy notes](docs/deploy/streamlit-cloud.md))
**Cost**: $0/月（GitHub Actions cron + Streamlit Cloud free tier）
**Author**: George Chen (CMSI HK Healthcare)
**Plan**: see `~/.claude/plans/modular-toasting-spindle.md`

## Stack

| Layer | Choice |
|---|---|
| Cron / data fetch | GitHub Actions schedule（cloud-side，Mac 可关机）|
| Data source | yfinance (US + HK + JP + KR + EU 统一) |
| Storage | SQLite (commit 进 repo, 自然 audit trail) |
| Frontend | Streamlit + `st.navigation` multi-page |
| Picks 数据 | 复用 `~/ic-foundry/ledger.db`，sync 进 `data/external/` |

## Data caveat

本 dashboard 估值 multiple 数据来自 **yfinance**，包括 trailing P/E 和 12-month forward P/E。
**与 Bloomberg / FactSet 的 consensus multi-year forward (25E/26E/27E) 有出入**。如需精确分年度 forward，请参考 George 手工维护的 Excel sector comp table。

## 目录结构

```
.
├── .github/workflows/      # GitHub Actions cron
├── config/
│   ├── domains/           # Domain 元数据 (healthcare.yml, ai.yml)
│   └── universes/         # Sector ticker list YAMLs
├── data/
│   ├── snapshots.db       # 价格 + multiple 时序 (auto-grown)
│   └── external/          # ic-foundry ledger 副本
├── jobs/
│   ├── init_db.py         # 初始化 SQLite schema
│   ├── load_universe.py   # YAML → universe_member table
│   └── fetch_eod.py       # 每日 yfinance EOD fetch
└── app/
    ├── streamlit_app.py   # Home
    ├── pages/             # 多页面
    └── lib/               # 共用工具
```

## Quick start (本地)

```bash
# 1. Init schema
uv run --with pyyaml --with pandas python jobs/init_db.py

# 2. Load universes
uv run --with pyyaml --with pandas python jobs/load_universe.py

# 3. Fetch 历史 30 天 backfill
uv run --with yfinance --with pandas --with pyyaml python jobs/fetch_eod.py --backfill-days 30

# 4. 启动 Streamlit
uv run --with streamlit --with plotly --with pyyaml --with pandas streamlit run app/streamlit_app.py
```

## 添加新 Ticker / 板块 / Domain

1. 新 ticker：编辑对应 `config/universes/*.yml`，追加 ticker
2. 新板块：创建新 YAML，更新对应 `config/domains/<domain>.yml` 的 sectors 列表
3. 新 domain：创建 `config/domains/<new>.yml`，加 universe YAMLs，前端 `app/pages/` 加新页面

无需改 schema 或核心代码。

## 📂 Project layout (IDE-friendly)

```
invest-dashboard/
├── app/              Streamlit pages + lib helpers
├── config/           Domain & universe YAMLs
├── data/             SQLite snapshots + external CSVs
├── jobs/             Cron-driven data fetcher
├── scripts/          Helper scripts (sync_ledger.sh etc.)
├── .github/          GitHub Actions cron workflow
└── docs/             ⭐ Plans / audits / screenshots — see docs/README.md
```

**Quick links**: [Plan](docs/plans/modular-toasting-spindle.md) · [Round 1 audit](docs/audits/round1/) · [Round 2 audit](docs/audits/round2/) · [Screenshots](docs/screenshots/)

## Pages (D1–D7)

| Page | What | Wiki integration |
|---|---|---|
| Home | Benchmarks + top movers + universe summary | — |
| 💎 CMSI Coverage | 28-ticker cover list, full multiples, cross-sector tags | — |
| 🏥 Healthcare | 7 sub-sector summary + per-sector top movers | — |
| 🔥 Sector Heatmap | 7 sector tabs, color-graded multiples + returns | — |
| 🧬 Strategy Picks | v4 / v5 biotech + HK 高股息, since-inception perf vs benchmark | — |
| 💰 Valuation Scanner | Cross-sectional P/E percentile filter, deep-value & recovery presets | — |
| 🔍 Ticker Drill | Single-ticker deep dive (price + multiples + cross-sector tags) | **Renders LLM Wiki memo** (Summary / Thesis / Rating / TP / Catalysts / Risks) if `~/Documents/LLM Wiki/Wiki/companies/<ticker>-*.md` exists |

> **Wiki + Cloud caveat**: LLM Wiki lives on George's Mac and is **not** copied to Streamlit Cloud. On the deployed instance the Ticker Drill page falls back to price + multiples only; wiki memos render only when running locally. To surface memos in the cloud version, copy a sanitized subset under `data/wiki/companies/` and point `app/lib/wiki.py:WIKI_ROOT` at it — out of scope for v1.

## Deployment

| Step | What |
|---|---|
| 1. Sign in | https://share.streamlit.io — connect GitHub account |
| 2. New app | Repo `chenhongdao2-blip/invest-dashboard`, branch `main`, main file `app/streamlit_app.py` |
| 3. Python | Pinned via `runtime.txt` → 3.12 |
| 4. Deps | `requirements.txt` (streamlit / yfinance / pandas / plotly / pyyaml / numpy) |
| 5. Config | `.streamlit/config.toml` ships dark theme + headless mode |
| 6. Verify | Page slug emoji ok (e.g. `/Ticker_Drill`), URL drilldown via `?ticker=LLY` |

Cron updates land via GitHub Actions push → Streamlit Cloud auto-redeploy. See [docs/deploy/streamlit-cloud.md](docs/deploy/streamlit-cloud.md) for the end-to-end check.

## Roadmap

- **P0 (Week 1)**: Home + Sector Heatmap + CMSI Coverage + Strategy Picks + Valuation Scanner + Ticker Drill
- **P1 (Week 2-4)**: Multiple Z-score (需 60 天数据)、Earnings drift tracker、YTD decomp
- **P2 (Backlog)**: Earnings calendar、Insider trades、Cross-membership comparison
- **P1 deferred from audit**: 港股通 / 北向资金（中资 healthcare sell-side 核心指标，yfinance 无，需 AKShare / Tushare 集成）

## Operational notes

### SQLite-in-git growth (M5 audit fix)

`data/snapshots.db` is committed daily. With binary churn in git pack, growth is faster
than working-file size suggests. Migration trigger points:

- Working DB > **50MB** → consider partitioned Parquet snapshots
- `.git/pack` > **200MB** → migrate to external SQLite (Turso/Supabase free tier)
- Multi-year history (3+ years) → mandatory migration

Current state: ~640KB DB after 60-day backfill of 106 tickers → ~4MB/yr projected.

### Data path for D4 Strategy Picks (B1 audit)

`ic-foundry/ledger.db` lives in `~/ic-foundry/` on George's Mac — **NOT accessible**
from Streamlit Cloud. For D4 deployment:

- **Scheme A** (recommended): `cp ~/ic-foundry/ledger.db data/external/picks.db` and commit periodically
- **Scheme B**: extract picks_v2 to a derived JSON in repo (less sensitive than raw ledger)
- **Scheme C**: external DB via Streamlit secrets (Turso / Supabase)

Default: Scheme A — sync via `make sync-ledger`.

### China network proxy (国内 dev)

When running locally in China for yfinance:
```bash
export HTTP_PROXY=http://127.0.0.1:7897
export HTTPS_PROXY=http://127.0.0.1:7897
```
GitHub Actions runs on Microsoft cloud — proxy NOT needed for scheduled fetches.

### Known yfinance gotchas

- **BGNE → ONC rename**: BeOne Medicines (ONC) historical data may not include pre-rename
  ticker (BGNE). For YTD anchored at Jan 1 2026, ONC has continuous data — safe.
- **Hong Kong stocks**: 复权 precision略糙 vs Futu OpenAPI. Severe backtest 用 Futu (eval-ledger).
  Dashboard daily quick scan 用 yfinance 够。
- **CN A-share**: Use `.SS` (Shanghai) and `.SZ` (Shenzhen) suffix, not `.SH`.
