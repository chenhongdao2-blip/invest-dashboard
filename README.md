# invest-dashboard

> Multi-domain sell-side investment dashboard. Healthcare v1, AI 与其它 domain 后续扩展。

**Live**: TBD (Streamlit Community Cloud URL)
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

## Roadmap

- **P0 (Week 1)**: Home + Sector Heatmap + CMSI Coverage + Strategy Picks + Valuation Scanner + Ticker Drill
- **P1 (Week 2-4)**: Multiple Z-score (需 60 天数据)、Earnings drift tracker、YTD decomp
- **P2 (Backlog)**: Earnings calendar、Insider trades、Cross-membership comparison
