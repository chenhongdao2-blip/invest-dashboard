# Multi-Domain Investment Dashboard — Implementation Plan

> **Codename**: `invest-dashboard`（首期 Healthcare，预留 AI / 其他 domain）
> **Plan author**: consult-mode session with George Chen, 2026-05-28
> **Target ship**: 1 周内 P0 上线，后续 P1/P2 增量

---

## Context

George（CMSI HK sell-side healthcare analyst）想做一个**云端自托管、零运维、$0/月**的投资 dashboard，把分散的几类股票表现可视化：

1. **板块横切**（首期 Healthcare 7 板块：Biotech / Hospital Care / HC+AI / Managed Care / Medtech / CXO & Life sciences / Pharma，未来加 AI 等大类）
2. **CMSI 自己 cover 的股票**
3. **自家选股策略 picks**（v4 biotech / v5 biotech / HK 高股息）

诉求不止"5D/30D return 行情看板"那种 standard view —— 还要**估值 multiple insight**（P/E / EV/EBITDA / FCF Yield / PEG / P/B）+ 时间序列累积，3 个月后能做 Z-score outlier detection。

**关键约束**：
- George 的 Mac 可能关机/断网，所以 data ingestion 必须跑在云端（不是本地 launchd）
- 完全免费部署（GitHub Actions + Streamlit Community Cloud）
- Public URL 无 auth（用户已确认不需要 password gate）
- 数据精度容忍：yfinance 的 trailing P/E + 12M forward 够用，**不追求 Bloomberg-grade multi-year 25E/26E/27E**（那部分留在他手工维护的 Excel）

---

## Final Design Summary

### Stack（$0/月）

| 层 | 选型 | 理由 |
|---|---|---|
| Cron / 数据拉取 | GitHub Actions schedule（cloud-side）| Mac 可关机 |
| 数据源 | yfinance 统一 US + HK + JP + KR | 已验证；strategy-weekly 复用 pattern |
| 存储 | SQLite，commit 进 repo | 自然 audit trail；数据量小 ~1.6MB/年/150 tickers |
| 前端 | Streamlit（`st.navigation` multi-page）| 写 financial dashboard 极快 |
| Hosting | Streamlit Community Cloud | Free，public URL，自动 redeploy on push |
| Picks 数据 | 复用 `~/ic-foundry/ledger.db`（read-only SQL）| 不重建 |

### 顶层架构（multi-domain ready）

```
invest-dashboard.streamlit.app
│
├── 🏠 Home  (跨 domain 总览：今日 top mover / drag)
│
├── 🏥 Healthcare  (v1)
│   ├── 🏠 Domain Overview
│   ├── 🔥 Sector Heatmap (7 板块)
│   ├── 💎 CMSI Coverage
│   ├── 🧬 Strategy Picks
│   ├── 💰 Valuation Scanner
│   └── 🔍 Ticker Drill
│
├── 🤖 AI  (v2, 同样 structure, 后期加)
│
└── ⚙️ About (注明 yfinance 数据精度 caveat)
```

**配置驱动**：每个 domain 一个 YAML，sectors / benchmarks / coverage / strategies 全配置。新增 domain = 加 YAML + ticker list，不动代码。

---

## Repo Structure（greenfield，需创建）

```
~/invest-dashboard/                     # 新 repo
├── .github/
│   └── workflows/
│       ├── fetch_eod.yml               # cron: 每日 EOD 跑 yfinance
│       └── deploy_streamlit.yml        # push 时自动让 Streamlit Cloud 知道
├── config/
│   ├── domains/
│   │   ├── healthcare.yml              # 板块列表 + benchmark + 元信息
│   │   └── ai.yml                      # 占位
│   └── universes/
│       ├── hc_biotech.yml              # 15 tickers
│       ├── hc_hospital_care.yml        # 10 tickers
│       ├── hc_ai.yml                   # 12 tickers
│       ├── hc_managed_care.yml         # 10 tickers
│       ├── hc_medtech.yml              # 13 tickers
│       ├── hc_cxo.yml                  # 14 tickers
│       ├── hc_pharma.yml               # 16 tickers
│       └── cmsi_coverage_hc.yml        # CMSI HC cover list
├── data/
│   └── snapshots.db                    # SQLite，commit
├── jobs/
│   ├── fetch_eod.py                    # Daily 跑 yfinance.info + prices
│   ├── load_universe.py                # 读 YAML → universe_member table
│   └── sync_picks.py                   # 从远端 ic-foundry ledger 同步（看 trade-off）
├── app/
│   ├── streamlit_app.py                # Home page
│   ├── pages/
│   │   ├── 1_🏥_Healthcare.py
│   │   ├── 2_🔥_Sector_Heatmap.py
│   │   ├── 3_💎_CMSI_Coverage.py
│   │   ├── 4_🧬_Strategy_Picks.py
│   │   ├── 5_💰_Valuation_Scanner.py
│   │   └── 6_🔍_Ticker_Drill.py
│   └── lib/
│       ├── db.py                       # SQLite reader
│       ├── universe.py                 # 读 config YAML
│       ├── format.py                   # 数字 / 颜色 formatter
│       └── charts.py                   # Plotly 共用图表
├── requirements.txt                    # streamlit, yfinance, pandas, plotly, pyyaml
├── .streamlit/
│   └── config.toml                     # theme (dark + 红绿)
└── README.md
```

---

## Critical Files & Patterns to Reuse

### From `~/strategy-weekly/weekly_perf.py`（**直接 crib**）

```python
# yfinance 批量 download pattern, lines 74-102
# 已处理 US/HK/JP/KR ticker normalization
# 复制进 jobs/fetch_eod.py 的核心 fetch loop
```

### From `~/ic-foundry/ledger.db`（**只读取**）

```sql
SELECT ticker, source_skill, date_added, price_at_decision
FROM picks_v2
WHERE status = 'active' AND source_skill IN ('catalyst-monitor', 'us-biotech', 'hk-high-div')
```

**Trade-off — picks 数据流**:
- **Option A**：dashboard repo 不持有 ledger.db，每次 GitHub Actions 跑时通过 user 提前同步好的副本（最简单：把 ledger.db 也 commit 进 dashboard repo 的 `data/external/`，定期手动 sync）。
- **Option B**：每天 GitHub Actions 起一个 task 通过某种 secret 拉远端 ledger（复杂，不推荐）。
- **推荐**：A —— 每周 George 手工 `cp ~/ic-foundry/ledger.db ~/invest-dashboard/data/external/`，commit，push。或写一个 `make sync-ledger` 一键命令。

---

## SQLite Schema（`data/snapshots.db`）

```sql
-- 价格历史（已有数据 + 自累积）
CREATE TABLE prices_daily (
    ticker TEXT NOT NULL,
    date TEXT NOT NULL,           -- YYYY-MM-DD
    open REAL, high REAL, low REAL, close REAL,
    adj_close REAL,
    volume INTEGER,
    currency TEXT,                 -- USD / HKD / JPY / KRW
    PRIMARY KEY (ticker, date)
);
CREATE INDEX idx_prices_date ON prices_daily(date);

-- Multiple 时序快照（dashboard 价值核心：自累积）
CREATE TABLE multiples_daily (
    ticker TEXT NOT NULL,
    date TEXT NOT NULL,
    market_cap_usd REAL,           -- 统一 USD
    trailing_pe REAL,
    forward_pe REAL,               -- yfinance 12M forward
    trailing_eps REAL,
    forward_eps REAL,
    ev_ebitda REAL,
    ev_sales REAL,
    fcf_yield REAL,
    peg REAL,
    pb REAL,
    ytd_return REAL,
    PRIMARY KEY (ticker, date)
);
CREATE INDEX idx_mult_date ON multiples_daily(date);

-- Universe membership (many-to-many for cross-membership)
CREATE TABLE universe_member (
    domain TEXT NOT NULL,          -- 'healthcare' / 'ai' / ...
    sector TEXT NOT NULL,          -- 'biotech' / 'hospital_care' / ...
    ticker TEXT NOT NULL,
    name_cn TEXT,
    name_en TEXT,
    region TEXT,                   -- 'US' / 'HK' / 'JP' / 'KR'
    PRIMARY KEY (domain, sector, ticker)
);

-- 元信息
CREATE TABLE meta (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT
);
```

---

## GitHub Actions Workflow

### `.github/workflows/fetch_eod.yml`

```yaml
name: Fetch EOD data
on:
  schedule:
    # US 收盘 16:00 ET ≈ 21:00 UTC (DST) / 22:00 UTC (winter)
    # 跑 22:30 UTC 保证两个时段都已收盘
    - cron: '30 22 * * 1-5'
    # HK 收盘 16:00 HKT = 08:00 UTC; 跑 09:00 UTC
    - cron: '0 9 * * 1-5'
  workflow_dispatch:               # 允许手动触发

jobs:
  fetch:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -r requirements.txt
      - run: python jobs/fetch_eod.py
      - name: Commit data
        run: |
          git config user.email "bot@github.com"
          git config user.name "data-bot"
          git add data/snapshots.db
          git diff-index --quiet HEAD || git commit -m "data: EOD snapshot $(date -u +%Y-%m-%d)"
          git push
```

**Notes**:
- GitHub Actions cron 不支持夏令时，所以跑得稍微保守一点
- 用 `[skip ci]` 在 commit message 避免触发自身循环（虽然没注册其他 workflow）
- Free tier 每月 2000 min，每次 fetch 估计 < 3min，每天 2 次 × 22 工作日 ≈ 132 min/月，富富有余

### `.github/workflows/deploy_streamlit.yml`（其实不需要）

Streamlit Cloud 自动 listen GitHub repo push，不需要 deploy yml。可以删除这条。

---

## P0 View Specs（首期 6 个页面）

### 1. 🏠 Home
- 今日（最近 SQLite 数据日）跨 domain top 5 涨幅 + top 5 跌幅
- 4 个 benchmark 表：XBI / XPH / IXJ / XLV 当日 + 1W + 1M + YTD
- Banner: data updated YYYY-MM-DD HH:MM UTC

### 2. 🏥 Healthcare Domain Overview
- 7 板块的 1D / 5D / 1M / YTD avg return summary table
- vs domain benchmark XLV alpha
- "板块今天哪些股票涨/跌最大" hover

### 3. 🔥 Sector Heatmap（**核心视图**）
- Dropdown 切板块（7 选 1）
- 表格：Ticker | Name | Mkt Cap | YTD% | 1M% | 5D% | 1D% | Trailing P/E | Fwd P/E | EV/EBITDA | FCF Yield | PB
- **每列独立红绿渐变染色**（mimicking 图 4-10 的视觉效果）
- 表底 sector aggregates：mean / median / weighted-by-mktcap

### 4. 💎 CMSI Coverage
- 单一长表：Ticker | Name | Sector | Region | YTD% | Multiples …
- 标注 cross-sector 股票（图标）
- Coverage list **来源用户提供**（gap，见 Open Questions）

### 5. 🧬 Strategy Picks
- 3 个 tab: v4 biotech / v5 biotech / HK 高股息
- 每个 tab：
  - Since-inception 累计回报曲线（picks 等权 vs benchmark）
  - Top 5 / Bottom 5 ranking table（沿用 strategy-weekly Excel 风格）
  - 每只股的 contribution
- 数据源：`ic-foundry/ledger.db` 的 picks_v2 + `multiples_daily`

### 6. 💰 Valuation Scanner
- 条件 filter：
  - Sector 多选
  - 当前 trailing P/E 在板块内 < X% 分位
  - YTD return > Y%
  - 最小 mkt cap
- 输出 candidate list + 简单解读
- 注明 "P/E 分位是 cross-sectional，时序 Z-score 等 P1 上线"

### 7. 🔍 Ticker Drill（个股详情）
- 5Y 复权价格图
- Trailing P/E 时序图（自上线后逐日累积）
- 基本面卡片：Mkt cap / EBITDA margin / Cash / Debt / Sales (24A/25E from yfinance)
- 该股最新 sector group（cross-membership 列出全部）
- 如果在 picks 里，标"v4/v5/高股息 pick"
- 注明 "本页 multiple 来自 yfinance，与 Bloomberg consensus 有出入"

---

## Phase 计划

### P0 — Week 1（target ship: 2026-06-04）

| Day | 任务 | Owner |
|---|---|---|
| D1 | 创建 repo `~/invest-dashboard/`，写 README + skeleton | claude |
| D1 | SQLite schema 初始化 + 7 个 universe YAML（用户提供 ticker list 后填）| claude |
| D2 | `jobs/fetch_eod.py` — 从 universe YAML 读 ticker，yfinance 批量拉，落 SQLite | claude |
| D2 | GitHub Actions yml + 本地手动跑一次 backfill 历史价格 | claude |
| D3 | Streamlit app skeleton: Home + Sector Heatmap | claude |
| D4 | Strategy Picks page（接 ic-foundry ledger）| claude |
| D5 | CMSI Coverage + Valuation Scanner | claude |
| D6 | Ticker Drill page | claude |
| D7 | Deploy 到 Streamlit Cloud，测试 public URL，写 README | claude |

### P1 — Week 2-4（数据积累期）

- Multiple Z-score view（需要 ≥ 60 天数据，约 6 月底可上）
- Sector-relative Z-score
- Earnings drift tracker（forwardEps 30D 变化）
- YTD return decomposition (multiple expansion vs EPS growth)
- AI domain skeleton（复用 healthcare pattern）

### P2 — Backlog（视后续需求）

- Earnings calendar overlay
- Insider trades view
- Cross-membership 性能对比（ISRG 在 HC+AI vs Medtech）
- 给团队 / 客户的高级 view（如果决定走付费/private）

---

## Open Questions & Blockers

### B1: Universe ticker list（**P0 blocker**）

我没有找到那个 **2025-11-06 dated 7-sector Excel**（图 4-10 来源）。需要用户：
- 要么把那个 Excel 路径告诉我 → 我自动提取 ticker list
- 要么手动 fork 出 7 个 YAML（每个 sector ~10-16 个 ticker，5 分钟工作）

**已知 ticker list（从图 4-10 OCR 提取）**：

```yaml
# hc_biotech.yml (15 + 1 = 16 from picture, 但实际 14 ticker 因为有重复)
tickers:
  - GILD, VRTX, REGN, ARGX, ALNY, BNTX, BIIB, ONC, MRNA, RPRX, GMAB, NBIX, INCY, BMRN, RVMD, 4587.T

# hc_hospital_care.yml (10)
tickers: [HCA, THC, UHS, DVA, EHC, CHE, ENSG, SEM, OPCH, ACHC]

# ... (7 个总共 ~80-90 unique tickers)
```

可以从图 OCR 出 first cut，再让用户 confirm。

### B2: CMSI Coverage list

用户图片 memory 提到 `~/Desktop/香港股票信息表信息.xlsx`，recon 没找到。可能在：
- iCloud Drive 远程
- 重命名了
- 在 OneDrive / 内网

用户提供路径或 ticker list 才能填 `cmsi_coverage_hc.yml`。

### B3: SQLite commit 还是外存？

P0 推荐**commit 进 repo**（简单 + audit trail）。但 6 个月后 commit history 体积会涨。如果体积成问题，迁移方案：
- 改用 Parquet daily snapshot（更省）
- 改用 Turso / Supabase（外部 hosted SQLite，仍 free tier）

P0 不解决，标注 follow-up。

### B4: 港股 yfinance 数据精度

yfinance 港股复权处理不如 Futu 精确，但 dashboard 这种 use case **够用**。
- 已知 caveat：dividend/split adjustment 可能略糙
- George 的严肃 backtest（eval-ledger / strategy-weekly）继续用 Futu，**不动**
- Dashboard 是另一条独立数据通路

---

## Verification（如何测试 end-to-end）

### Bootstrap test（本地）
```bash
cd ~/invest-dashboard
# 1. 初始化 schema
python jobs/init_db.py
# 2. 加载 universe
python jobs/load_universe.py
# 3. Fetch 历史 30 天
python jobs/fetch_eod.py --backfill-days=30
# 4. 启动 Streamlit
streamlit run app/streamlit_app.py
# → 浏览器自动打开 localhost:8501
```

### Cron test（手动触发 GitHub Actions）
1. Push 到 GitHub
2. Actions tab → "Fetch EOD data" → "Run workflow"
3. 等待 2-3 min
4. 检查 `data/snapshots.db` 有今日 commit
5. Streamlit Cloud auto-redeploy → public URL refresh

### Data correctness spot-check
- Random pick 3 ticker（一只 US、一只 HK、一只 JP）
- 对比 yahoo finance 网页显示的 trailing P/E 和我们 SQLite 数字
- 误差 < 5% 算 pass（yfinance 数据有 1-2h delay 很正常）

### Strategy Picks 验收
- 用 strategy-weekly Markdown report (`~/SecondBrain/eval/strategy-weekly-2026-05-26.md`) 当 ground truth
- Dashboard 的 v5 biotech since-inception return 应该跟 markdown 数字一致

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| yfinance rate limit 在 GitHub Actions | Low | High | 加 retry + exponential backoff；分批 fetch（每 50 ticker 一组）|
| SQLite commit conflict（两个 workflow 同时跑）| Low | Medium | GitHub Actions 的 cron 不会并发；用 `concurrency` group |
| Streamlit Cloud free tier 限流 | Low | Low | 1 个 app 免费，且只有自己访问，不会触发限流 |
| Forward P/E 字段在某些 HK / JP ticker 不返回 | Medium | Low | UI 显示 "—"；不阻断其他列 |
| Public URL 被搜索引擎抓 | Low | Low | 加 `robots.txt`；URL 不要在公开渠道分享 |

---

## What this plan does NOT do

- ❌ 不做 multi-year forward P/E（25E/26E/27E）— 留 George 的手工 Excel
- ❌ 不做真"实时" tick 数据 — EOD daily 是足够的
- ❌ 不做团队登录 / RBAC — 用户已确认 public 无 auth
- ❌ 不做 mobile-first 优化 — Streamlit 默认 layout 在 desktop 用，mobile 凑合（P2 优化）
- ❌ 不做 alert / push notification — 那是另一个 workflow（FDA Catalyst Monitor 已经在做）

---

## Critical files to create

| 文件 | 作用 |
|---|---|
| `~/invest-dashboard/jobs/fetch_eod.py` | **核心数据 fetcher**，crib pattern from `strategy-weekly/weekly_perf.py:74-102` |
| `~/invest-dashboard/app/streamlit_app.py` + `pages/*.py` | Streamlit 多页面入口 |
| `~/invest-dashboard/config/universes/*.yml` | 7 个板块 + CMSI cover list **需要用户提供 ticker list 或 confirm OCR 提取的 first cut** |
| `~/invest-dashboard/.github/workflows/fetch_eod.yml` | 云端 cron job |
| `~/invest-dashboard/requirements.txt` | streamlit, yfinance, pandas, plotly, pyyaml, sqlalchemy(optional) |

---

## Decision log（记录关键 trade-off）

1. **yfinance over Bloomberg**：精度让步给免费 + cloud-deployable
2. **Streamlit over Next.js**：1 周 ship vs 3-4 周
3. **Public no-auth over private**：用户确认；真正 IP 不在 cover list 本身
4. **SQLite over Postgres**：简单，commit 进 repo，audit trail
5. **GitHub Actions over self-hosted cron**：Mac 关机不影响
6. **不复用 ic-foundry ledger 的 schema 扩展**：dashboard 是 read-only consumer，不重塑 ledger
7. **Multi-domain ready from day 1**：YAML config-driven，未来加 AI domain 不动代码

---

## Next session 启动检查清单

1. 用户 confirm plan ✅
2. 用户提供 7 sector ticker list（或 confirm OCR first cut）
3. 用户提供 CMSI HK coverage list
4. 创建 `~/invest-dashboard/` git repo + 推 GitHub
5. 启用 Streamlit Community Cloud account（free）
6. 开始 D1 任务
