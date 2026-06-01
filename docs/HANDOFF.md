---
status: ACTIVE
created_at: 2026-06-01T15:50:00+08:00
updated_at: 2026-06-01T15:50:00+08:00
project_root: /Users/gcc/invest-dashboard
mission: invest-dashboard「投融资」页(药企 MNC M&A + BD/合作 + IPO + 余额表)已建成并 ship 上云(commit 0bffeac)。以后维护靠 docs/funding-pipeline.md 管道 + 每周 SessionStart 自动检测 hook。本交接是「已交付状态 + 维护机制」快照,非半成品。
---
# HANDOFF — invest-dashboard 投融资页(已 ship)+ 数据刷新机制

> 自包含交接包。接棒人只读此文件即可动手,不需要对话历史。
> ⚠️ 本 session 的工作**已全部 commit + push 上云**(`0bffeac`),工作区干净。这不是待 ship 的半成品。

## 1. 任务 Mission
把 George 的「ED CN Funding」月报数据搬上 invest-dashboard,做成 Healthcare 栏目下的「投融资」页(`/HC_Capital_Markets`)。核心:**药企 MNC M&A 历史**(deal-level)+ **BD/合作**(授权交易)+ MNC 余额表 + IPO。已 ship。以后**每周/每月按管道刷新**。

## 2. 进度快照(全部 ✅,无半成品)
- ✅ **投融资页** `app/pages/9_HC_Capital_Markets.py`:
  - **2026 YTD M&A 置顶**:KPI + B3 三段(总额/首付/里程碑)+ 每行来源 ↗ 链接
  - **历史 M&A**(真收购):league 条 / 治疗领域 / 历年 / TOP20 / 可筛明细
  - **BD/合作**:报告 TABLE 59 格式(授权方→被授权方,药物在中间,首付/里程碑/总对价),99 笔(68 报告2025 + 31 web 2026),来源 ↗ 进表
  - MNC 干火药表(SEC XBRL)
- ✅ **数据**(`data/external/`):`mnc_ma_deals.csv`(430 笔, M&A 391/BD 39)、`bd_deals.csv`(99)、`funding_mnc_balance_2026Q1.json`、`mnc_2026_deals.json`、`bd_licensing_report.csv`;另有 `funding_aggregate.json` + `funding_public_q1_2026.json`(**月度/季度方案的数据,页面已不用,留给将来 PharmCube**)
- ✅ **分类全 biotech-verified**:M&A vs BD、B3 三段、cross-check 三轮核
- ✅ **Strategy Picks**:`ipo_picks.csv` 加 天辰生物-B(1779,5.4)+ 大金重工(1081,5.7),pending
- ✅ **全量数据刷新到 2026-06-01**:价格/multiples/benchmarks/SEC(fail=0)/peer-median/CN基准/wiki(164)
- ✅ **刷新管道** `docs/funding-pipeline.md`(6 步 runbook)
- ✅ **每周自动检测** `.claude/hooks/funding-staleness.mjs` + `.claude/settings.json`(SessionStart,>7天提示)+ `data/external/.last_refresh`(marker=今天)

**环境状态**:branch `main` / 工作区干净(仅 gitignored 的 .bak/cov_/stray db)/ 已 push `0bffeac` / Cloud 自动部署 / 本地 `localhost:8501` 后台运行中。
repro:`uv run --with-requirements requirements.txt streamlit run app/streamlit_app.py --server.headless true --server.port 8501`
**相关文件**:`app/pages/9_HC_Capital_Markets.py`、`app/lib/funding.py`、`app/lib/charts.py`(ranked_hbar/year_bar/funding_yoy_bar/capital_dual_axis_chart)、`app/lib/ui.py`(render_html_table 加了 `link_cols`)、`app/lib/i18n.py`(ta_name 双语)、`app/lib/locales/pages_{zh,en}.py`(capital.*/mnc_ma.* 键)、`data/external/*`、`docs/funding-pipeline.md`

## 3. 关键决策
- **M&A vs BD 必须分清**(George 反复强调):M&A=控制权转移;BD=license/option/合作。**恒瑞-BMS $15.2B 是 BD(13-program 战略合作)不是 M&A**——这是判定锚点。
- **BD 用报告 TABLE 59 格式**:George 要「按 funding 报告呈现方式」,从 `ED CN 11M25 Funding.docx` 第 59 张表直抓(授权方/被授权方/药物/首付/里程碑/总对价)。
- **deal 数据 biotech-researcher 多轮核**:用 markdown scanner → structurer(不强制 schema),抓出真错(荃信首付里程碑写反、Orna $1065→$700 虚高、4笔M&A混入BD、Saniona TA「电线」)。
- **公司名清洗**:中文统一(石药集团/信达生物/荣昌生物),去资产描述/ticker/（中国）。
- **来源进表格**:`ui.render_html_table` 加 `link_cols` 渲染 iframe 内可点 ↗(escape 限制的 workaround)。
- **月度 aggregate / 季度 public-source 方案放弃**:PitchBook 没了 + 季度颗粒太粗 + 口径漂移;改 deal-level M&A/BD。数据留库待 PharmCube 接月度。

## 4. 失败的尝试(别重走)
- **强制 schema 的 workflow agent 会集体 StructuredOutput 失败**(过度研究后忘了调输出工具)→ 改 **markdown scanner + 单个 structurer**。
- **并发跑 fetch_eod + fetch_sec_facts 撞 SQLite db 锁**(单写)→ 必须**顺序跑**。
- **Streamlit Cloud 不能 live-read `~/yuqing-system` 或 `~/Downloads`**(无文件系统)→ 数据必须 copy 进 repo。
- **render_html_table 默认 escape HTML**,cell 放不了 `<a>` → 用 `link_cols` 在 iframe 内渲染。

## 5. 下一步(≤3)
1. **下次刷新**:开 cc 若 hook 提示 deal 数据 stale → 按 `docs/funding-pipeline.md` 跑(扫deal→分类→biotech核→merge→刷各层→眼验→上云)。
2. **PitchBook 替代**:接 PharmCube `investEvent` MCP 做 event-level 月度 aggregate(Option 1),复活月度资金流视图。
3. **IPO 回填**:天辰/大金 06-05 上市后,把 `ipo_picks.csv` 的 day1_ret / day1_close 填上、status→listed。

## 6. 陷阱与约束
- **local-first ship gate**:改动须 George 本地眼验、明说「可以 ship / 上云」才 commit+push。
- **SQLite 单写**:刷新脚本顺序跑,别并发。
- **垃圾别提交**:`.gitignore` 已挡 `/snapshots.db`(0字节stray)、`data/snapshots.db.bak-*`、`cov_*.txt/json`。别 `git add` 它们。
- **snapshots.db 是 git-tracked**:连库提交才上 Cloud;价格/SEC 已有 GitHub Action cron 每日自刷。
- **投资人面纪律**:每数字带源、M&A/BD 分清、不采纳卖方评级、值冲突要人拍板(biotech 核出过一堆错)。
- macOS:`grep -E` 不用 `-P`;`date` 无 `%3N`;中国代理 `http://127.0.0.1:7897`。

## 7. 打开的问题
- **PitchBook 已不可用**:月度 aggregate 暂无源,Option 1(PharmCube)未接。
- **bd_deals 2025 那 68 笔来自 11M25 报告**:George 出新一版 ED Funding 报告时需重抽 TABLE 59 覆盖。
- **funding_aggregate.json / funding_public_q1_2026.json 留库未用**:接 PharmCube 后才复用,否则可删。

## ⚠️ 低置信度决策点(接棒人请核对)
- **BD `bd_deals.csv` 99 笔的 2025 部分**:从 docx TABLE 59 抓 + biotech 核了 corrections,但报告原表本身的个别数字未逐笔回原始公告(biotech 核了 top ranks)。引用前大额的最好再抽验。
- **AbelZeta / West Pharma 被从 BD 删除**(biotech 判 M&A):它们没有同时加进 M&A 数据集(M&A 集是 13-MNC basket,这俩算 rights/facility 收购,边界)。若要完整,需确认归属。
- **`mnc_ma_deals.csv` 2026 行的 ta_group** 是从 free-text `ta` 关键词分桶推的,个别可能不准。

<!-- HANDOFF-END -->
