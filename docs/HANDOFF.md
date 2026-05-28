---
status: ACTIVE
created_at: 2026-05-28T15:30:00+08:00
updated_at: 2026-05-28T15:30:00+08:00
project_root: /Users/gcc/invest-dashboard
mission: 完成 invest-dashboard 剩余 D6 Ticker Drill + D7 Streamlit Cloud 部署；并清理已知的 Sector Heatmap / Healthcare 页面 sort bug 残留。
---
# HANDOFF — invest-dashboard D6 + D7 收尾

> 自包含交接包。接棒人只读此文件即可动手，不需要对话历史。
> 项目 repo（public）：https://github.com/chenhongdao2-blip/invest-dashboard

## 1. 任务 Mission

George Chen (CMSI HK healthcare analyst) 的多 domain 卖方 dashboard。Healthcare v1 已经 ship 5/7 pages（D1-D5 完成），剩 **D6 Ticker Drill 个股详情页** 和 **D7 Streamlit Community Cloud 部署**。还需要把同一类 sort bug（Streamlit Styler pre-format string 导致 header click sort 按字符串排序）从 Sector Heatmap / Healthcare overview 等页面也清掉——只在 CMSI Coverage 修了，其他几个 page 同源漏洞还在。

## 2. 进度快照

**已完成（all pushed to origin/main）**:
- ✅ D1: Repo bootstrap + 8 universe YAML + SQLite schema → commit `7f71a91`
- ✅ D2: `jobs/fetch_eod.py` 完整 yfinance 抓取 + GitHub Actions cron + 180-day backfill → `3157451`
- ✅ D3: Streamlit Home + Healthcare overview + Sector Heatmap → `17f2f17`
- ✅ Audit Round 1 fixes（Codex/Gemini/GLM 三 advisor）→ `251c6de`
- ✅ D4: Strategy Picks (v4/v5 biotech + HK 高股息) → `2863c72`
- ✅ D5: CMSI Coverage + Valuation Scanner → `9e1179e`
- ✅ Audit Round 2 fixes（B1 picks.db IP scrub / m1 .gitignore WAL / page rename CMSI #1 / M11 min mcap $1.5B / M2 ffill / M14 3M/6M return / m2/m3 Scanner caveat / m8 TP upside via yfinance.info / M5 sync_ledger.sh）→ `16a190a`
- ✅ Sort numeric bug fix on CMSI Coverage（column_config approach）→ `f6d8e4b`
- ✅ docs/ 整合：plans + audits + screenshots → `b146260`

**未开始**:
- ⚪ D6: Ticker Drill 个股详情页 (`app/pages/6_🔍_Ticker_Drill.py`)
- ⚪ D7: Streamlit Community Cloud 部署 + public URL
- ⚪ Sort bug 系统性 fix（仅 CMSI Coverage 修了；Sector Heatmap / Healthcare overview / Strategy Picks ranking 表 / Scanner 还在用旧 Styler pre-format string 模式）
- ⚪ Streamlit 1050px viewport 限制：CMSI Coverage 默认 15/17 列可见，缺 Reco / N analysts / Cross；可用 Fullscreen 但建议永久解决（drop 一些低价值列）

**进行中**:
- 🟡 无（最近 commit `b146260` 已落，working tree clean）

**环境状态**：
- branch `main`，无未提交改动
- 最新本地 build：手动运行 `streamlit run` ok，3 个 page 验证过
- 数据 backfill：180-day 已落 SQLite，2025-12-01 → 2026-05-28，4301 prices + 106 multiples + 28 CMSI cover
- repro 命令：`cd ~/invest-dashboard && uv run --with streamlit --with yfinance --with pandas --with plotly --with pyyaml --with numpy streamlit run app/streamlit_app.py --server.port 8517`

**相关文件**：
- `app/pages/1_💎_CMSI_Coverage.py` — sort bug 已修，column_config + width="small"。**模板，可参考给其他 page 用**
- `app/pages/3_🔥_Sector_Heatmap.py` — sort bug 还在（pre-format string）。**最高优先级修**
- `app/pages/2_🏥_Healthcare.py` — 同上
- `app/pages/5_💰_Valuation_Scanner.py` — 同上
- `app/pages/4_🧬_Strategy_Picks.py` — Top/Bottom 5 ranking 表也是 pre-format string
- `app/lib/ui.py` — `sidebar_search` + `onboarding_expander`（Gemini auto-fix 创建，所有 page 已用）
- `app/lib/charts.py` — `cumulative_return_chart(show_individual, dispersion band)`（Gemini auto-fix）
- `app/lib/db.py` — `compute_returns` 含 3M/6M/1Y / `get_close_series_usd` / `latest_multiples`
- `app/lib/strategy.py` — load_v4 / load_v5（CSV not picks.db）/ load_hd / `fetch_picks_closes` cached 1h
- `jobs/fetch_eod.py` — yfinance 批量 + FX normalize + m8 fields (target_price_mean / recommendation_mean / n_analysts) + exp backoff
- `jobs/init_db.py` — schema CREATE TABLE 不含 m8 字段（用 ALTER TABLE ADD COLUMN 加），但 idempotent
- `scripts/sync_ledger.sh` — 每周手工同步 ic-foundry → v5_picks.csv，**未实测**
- `data/external/picks.db` — **不再 commit**（IP leak fix）；改用 `v5_picks.csv` (40 picks, 3 cols)
- `.gitignore` — `data/external/*.db / *-shm / *-wal` excluded
- `docs/plans/modular-toasting-spindle.md` — D1-D7 完整 plan
- `docs/audits/round1/` + `docs/audits/round2/` — 6 个 advisor 报告（Codex/Gemini/GLM × 2 rounds）
- `docs/audits/prompts/` — 我发给 advisor 的 prompt（接棒人可仿写）
- `docs/screenshots/` — 关键 visual milestones

## 3. 关键决策

- **picks.db raw 不入 repo**（B1 Codex audit BLOCKER）— ic-foundry 完整 ledger 含 thesis/conviction/postmortem JSON IP。改用 `data/external/v5_picks.csv` (ticker + pick_date + price_at_decision)，每周 `scripts/sync_ledger.sh` 重生成。
- **Live yfinance for strategy picks**（不进 main universe）— v4/v5/HD 的 ~100 个 ticker 不污染 daily cron fetch；通过 `lib/strategy.fetch_picks_closes` 1h cached。
- **column_config + numeric DataFrame** 解决 sort bug（CMSI Coverage 只）— 保 numeric 由 Streamlit NumberColumn 显示 format。**Styler 仍用 background_gradient 染色但不 format**。pre-format string 死路（sort 按字符串）。
- **CMSI Coverage 移到 page #1**（Round 1+2 Gemini audit）— sell-side analyst 早会先看自己 cover。Sidebar 顺序：CMSI / Healthcare / Sector Heatmap / Strategy Picks / Valuation Scanner.
- **min mcap default $1.5B** Scanner（M11 GLM）— $5B 过滤 90% HK 18A，不够接地气。
- **GitHub Actions cron**（22:30 UTC + 09:00 UTC）— 不 observe DST，跑得稍后保证两个时段都已收盘。
- **Public repo + 无 password gate** — user 确认 cover list 在 distribution list 已半公开；真 IP 是观点不是名单。
- **不做 25E/26E/27E multi-year forward** — Bloomberg/FactSet 独有，留 user Excel；dashboard 用 yfinance trailing P/E + 12M forward。

## 4. 失败的尝试

- **`st.dataframe(styler)` + Styler.format(formatter, na_rep="—")** — 渲染时 Streamlit canvas widget 静默 drop trailing columns (17 cols 只渲染 11-13)，且 NaN 显示 "None" 而非 "—"。**不要再走这条路**。已切到 numeric DataFrame + column_config.
- **`use_container_width=True` 默认列宽** — 17 cols 在 1050px viewport 只挤进 13。加 `width="small"` 才挤进 15。建议永久 drop 低价值列（Reco / N analysts / Cross）保 15 主列。
- **Gemini YOLO 自动 rename pages** — Gemini round 2 试图用 emoji 文件名 rename 失败几次，最终成功但 git 检测为 delete + add 而非 rename（git 内部用 `--find-renames` heuristic 自动识别，OK）。
- **`merged["tp_upside_%"] = pd.NA` scalar broadcast** — Pandas 2.x 接受，OK，但 column dtype 变 object；不影响 column_config 显示但 sort 行为微妙。

## 5. 下一步

1. **修 sort bug 到其他 4 个 page**（D5 完成后唯一遗留质量问题）：
   - `app/pages/3_🔥_Sector_Heatmap.py`：模仿 `1_💎_CMSI_Coverage.py` 的 column_config 模式，把所有 sector 的 7 个 tab 内 dataframe 改成 numeric + NumberColumn format
   - `app/pages/2_🏥_Healthcare.py`：sector summary 表 + per-sector top 3 expanders
   - `app/pages/5_💰_Valuation_Scanner.py`：candidates 输出表
   - `app/pages/4_🧬_Strategy_Picks.py`：Top 5 / Worst 5 ranking 表
   - 公共 helper：可考虑把 column_config 生成 + Styler.background_gradient apply 抽到 `lib/ui.py:render_styled_table(df, pct_cols, mult_cols, ...)`，复用 5 page

2. **写 D6 Ticker Drill page**（`app/pages/6_🔍_Ticker_Drill.py`）：
   - Sidebar `ui.sidebar_search` 已 session_state 持久化 → 用 `st.session_state.global_ticker` 拿 ticker
   - 内容（per plan）：5Y 复权价格 Plotly 图、Trailing P/E 时序图（数据自上线后逐日累积）、基本面 card (Mcap / EBITDA / Cash / Debt / Sales 24A/25E from yfinance.info 已有字段)、cross-membership sector 标签、如果在 picks 里 badge "v4/v5/HD pick"、caveat note
   - 数据：复用 `lib/db.get_close_series_usd` + `lib/db.latest_multiples`，必要时 live yfinance.info fetch 补漏

3. **D7 Streamlit Cloud 部署**：
   - https://share.streamlit.io 注册 + 连 GitHub repo
   - Specify "Main file path: `app/streamlit_app.py`"
   - Public URL 自动生成（free tier）
   - Test post-deploy：跑通至少 1 个 cron cycle 看 GitHub Actions push commit + Streamlit Cloud auto-redeploy 链条没问题
   - Update `README.md` 顶部加 live URL badge

## 6. 陷阱与约束

- **`.omc/` 和 `.claude/`** 在 `.gitignore`，不能 commit（含 session state / artifacts）
- **`data/external/*.db`** 也 ignored — 不要回提 ic-foundry ledger 副本（IP）
- **macOS shell**：用 `grep -E`，不用 `grep -P`（用户 CLAUDE.md hard rule）
- **HK proxy**：用户在 China 本地跑 yfinance 需 `HTTP_PROXY=http://127.0.0.1:7897`；但 GitHub Actions 在 Microsoft cloud 跑，无需 proxy
- **不要 rename "invest-dashboard"** 也不要去 emoji（用户 round 2 decision: 保持原样）
- **CRM (Salesforce) 留在 hc_ai sector**（用户决定，GLM 反对但 user 否决）
- **`Adj Close or Close` NaN truthy** 已修 → 用 explicit `pd.notna()` check（`jobs/fetch_eod.py:prices_to_rows`），别 regress
- **strategy-weekly Excel 落盘 `/Users/gcc/Desktop/strategy_weekly_*.xlsx`** 是另一个 launchd job，跟 dashboard 不冲突
- **不要 commit raw `data/external/picks.db`** — IP leak（已设 .gitignore）

## 7. 打开的问题

- **P1 deferred audit 项目**（GLM Round 1+2 提的）：
  - 港股通 / 北向资金（中资 sell-side daily 核心指标），需要选 AKShare / Tushare / HKEX scraper
  - Time-series 5Y P/E band（vs current cross-sectional percentile）
  - 集采/医保谈判 policy calendar overlay
  - Consensus rating / TP upside（m8 已部分加 TP upside，缺 broker count breakdown）
  - 3M / 6M / 1Y return 已在 `compute_returns` 加但 UI 还没用
- **CMSI cover list 是 partial subset 还是 full CMSI**：GLM Round 1 指出缺 18A 核心（康方 9926 / 再鼎 9688 / 和铂 6994 / 恒瑞 600276）。User 决策 "暂时不要管"。
- **Mobile / responsive** — Streamlit 默认 desktop。Round 1 Gemini 提了，P2.

## ⚠️ 低置信度决策点（接棒人请核对）

> 以下几点我注意力可能记偏，磁盘真值优先。请核对：

1. **Sort bug 在 Sector Heatmap 上是否真的没修** — 我在 round 2 后期 refactor 了 CMSI Coverage 用 numeric + column_config，但**没动** Sector Heatmap。请直接打开 `app/pages/3_🔥_Sector_Heatmap.py` 看是否还在用 `df["YTD %"].apply(fmt.fmt_pct)` 把数字预格式化成 string + Styler.format — 是的话同样的 sort bug 一定存在，需要 fix。
2. **m8 列 ALTER TABLE 添加是否所有 ticker 都有数据** — re-fetch run 时所有 106 ticker .info 都 ok=106 fail=0，所以应该全有。但如果某 ticker 在再 fetch 时 yfinance.info 临时失败，可能 NULL。
3. **Streamlit Cloud + GitHub Actions push 链条** — 我没实测端到端 round-trip。GitHub Actions yml 里 `permissions: contents: write` 应该 OK，但部署后第一个 cron 跑完没 verify push 触发 Streamlit redeploy。
4. **scripts/sync_ledger.sh 未实测** — 写了但没跑过。Run 一次确认 `uv run python` heredoc 在 bash 里能正确 substitute `$LEDGER` 和 `$OUT` env vars（应该 OK 因为是双引号 heredoc，但 verify）。
5. **page rename 后 Streamlit Cloud 是否正确路由** — 本地 rename 后 URL slug 跟着文件名变。Streamlit Cloud 同步 GitHub repo 时同样应该 OK，但 page slug 含 emoji（`1_💎_CMSI_Coverage.py`）可能导致 deploy 时编码问题——若 Cloud 部署后 URL 404 / 404 / 404，可能要给 page 文件名去掉 emoji 加纯 ASCII slug。
6. **lib/ui.py global_ticker session_state** — Gemini auto-fix 写的，page 切换时持久。但若用户 hard-reload，session_state 丢失。这是 Streamlit 设计、非 bug，但 D6 Ticker Drill 实现要考虑 fallback。

<!-- HANDOFF-END -->
