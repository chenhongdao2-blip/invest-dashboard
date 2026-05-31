---
status: ACTIVE
created_at: 2026-05-30T22:30:00+08:00
updated_at: 2026-05-30T22:30:00+08:00
project_root: /Users/gcc/invest-dashboard
mission: Ticker Drill 个股详情页重构已 ship (commit 45783ff, origin==local)。完成态快照 + backlog（TEM 基准未定 / 云端待 Reboot 验证 / 可选设计债）。
---
# HANDOFF — Ticker Drill 个股详情页重构（完成态快照）

> 自包含交接包。接棒人只读此文件即可动手，不需要对话历史。

## 1. 任务 Mission
重做 invest-dashboard 的「个股详情页」(`app/pages/6_🔍_Ticker_Drill.py`)：金融内容（区域/行业基准、SEC 财务趋势）+ 视觉（editorial、字号阶梯、图表美化）。源起：financial-strategist + designer 两 agent 讨论 → `/cccg`(Codex+GLM) 评审。**已全部 ship 到 main（commit 45783ff）**。

## 2. 进度快照
- ✅ **P0** Header 5 KPI 卡（最新价·市值 **本币+USD 双列** / YTD 染色 / 20日成交额）+ 共识小字（仅供参考）+ Variant 三栏（内部观点/市场一致/预期差，GLM 合规护栏：无覆盖隐藏）
- ✅ **P1+P1.5** 相对强弱图：绝对价单线 → rebased=100；**个股本币**(`get_close_series`)；共同交易日 anchor（非个股自身起点）；**区域/行业基准路由**（见 §3）；中文图例
- ✅ **P2** SEC 财务趋势（**US-only**）：Revenue/R&D/Cash 三趋势(自适应 bn/mn)+YoY+biotech 现金跑道；非美股 graceful fallback（IFRS/CAS 无 SEC 申报）
- ✅ memo editorial 重做（▎研究备忘 + 评级/目标价 hairline 条 + sector chips + eyebrow 摘要/投资逻辑）；合规 banner 双语改写（去「已剥离」黑化感、去内部路径）
- ✅ 字号 type scale（KPI 数字 38px / 原生 `st.metric` 30px / 标签保持小）；图表 spline+渐变+末点强调+隐藏 modebar
- ✅ benchmark 数据全进 committed `data/snapshots.db`（HSHCI/IGV/XHS/^NDX/^SP500-352020/512170）→ **离线/云端可跑**
- 🟡 **TEM (Tempus AI)** 基准未定——现仍错走 `hc_ai → 软件(IGV)+纳指`。用户说「你定」但没给方向。待决：cxo→XLV（与 ILMN/IDXX 一致，**我倾向这个**）还是 biotech→XBI
- ⚪ 可选设计债：chip 系统全面化（coverage/strategy badge 仍是 markdown 反引号）、section 标题统一

**环境状态**：branch `main` / 工作树 clean（仅 demos/、docs/HANDOFF.md、根 `snapshots.db`、docs/handoffs/* 这些**预存在的无关 untracked**）/ origin==local（45783ff 已 push）/ 本地服务可能仍在跑：`lsof -ti:8521`。
**repro 本地**：`uv run --python 3.12 --with-requirements requirements.txt streamlit run app/streamlit_app.py --server.port 8521 --server.headless true`
**验证手法**（本 session 一直用，非自述）：`streamlit.testing.v1.AppTest` headless 跑 page，断言 caption/markdown + 0 异常。
**相关文件**：`app/pages/6_🔍_Ticker_Drill.py`（主）、`app/lib/{theme,charts,benchmarks,i18n,db,sec_facts}.py`、`app/lib/locales/pages_{zh,en}.py`、`jobs/{fetch_eod,fetch_cn_benchmarks}.py`、`config/universes/hc_biotech.yml`、`data/external/hk_cn_benchmarks_seed.csv`、`docs/plans/ticker-drill-uplift.md`。

## 3. 关键决策
- **基准按上市地路由**（用户+GLM）：港股→恒生医疗保健 HSHCI + 恒指 (HKD)；A股→中证医疗 512170 (CNY)；美股 biotech→XBI / pharma→标普500医药 `^SP500-352020`(非等权 XPH) / medtech→IHI / hospital→XHS / managed→IHF / hc_ai→IGV+纳指 / cxo→XLV。**个股+基准同币种**消除汇率噪音。
- **HSHCI 走 iFind seed**（`jobs/fetch_cn_benchmarks.py` 读 `data/external/hk_cn_benchmarks_seed.csv`）——yfinance 无纯恒生医疗指数，且 iFind 是本地 MCP、**美国 cron runner 够不到**。512170/IGV/XHS/^NDX/^SP500-352020 是 yfinance 原生，已加进 `jobs/fetch_eod.py` 的 `BENCHMARK_TICKERS`（cron 自动维护）。
- **per-ticker benchmark 覆盖表** `_BENCH_OVERRIDE`（页面顶部）治「sector 标签对、benchmark 该例外」：OMCL→IHI(器械)、HQY→XLV(医疗金融)、HIMS→XLV(消费医疗)、RPRX→标普500医药(特许权金融)。**不动 universe 分类**。
- **RXRX→biotech**：直接加 biotech 标签（双写 `hc_biotech.yml` + DB），因它真属 biotech（影响选股/筛选，非仅 benchmark）。区别于上面 4 个用覆盖表。
- **SEC 选概念取「最新数据优先」**（`sec_facts.kpi_timeseries`）：原「历史最长」会选中弃用旧概念渲染 2017 旧数据（已修）。
- **字号阶梯非一刀切**：editorial `.cmsi-kpi-num`=38px（Ticker Drill 大高亮），原生 `st.metric`=30px（其它页装日期不截断）。**两者是不同组件，分别控制**。
- 用户确认保留：**AMGN→pharma**、**HCM/ONC→XBI**（中国 biotech ADR）。

## 4. 失败的尝试
- iFind 把「标普500医药」理解成 S35.GI **等权重**医疗保健（不要，等权正是要避开的）→ 改用 yfinance `^SP500-352020` (S&P 500 Pharmaceuticals 子行业)。
- yfinance 抓纯指数无效：`^HSHCI`/`^HSNHC`/`000913.SS`/`399989.SZ` 只返回 1 行 → 指数用 ETF 代理或 iFind seed。
- `/cccg` 的 **Gemini lane 被国内 geo-block**（`User location is not supported`）→ 评审实为 3-way(Claude+Codex+GLM)。
- AppTest 检查 CSS class 不可靠：注入的 `<style>` 含 `.cmsi-xxx{}` 字样 → 恒 True。必须查渲染出的 `class="cmsi-xxx"` div 计数。

## 5. 下一步
1. **云端 Reboot 验证**（最优先）：本次加了多个新函数（`mini_trend_chart`/`relative_strength_chart`/`close_series`/`adv_20d`/`kpi_timeseries`/`memo_meta_bar`/`eyebrow`/`chips`）。Streamlit Cloud git pull 后热重载会用 `sys.modules` 缓存旧 lib 跑新 page → 报假错（`AttributeError: ... has no attribute ...`）。**Manage app → ⋮ → Reboot app** 清缓存，再眼验云端。
2. **TEM 基准定夺**：用户给方向后，加进 `_BENCH_OVERRIDE`（建议 `["XLV"]`，与基因/诊断同类 ILMN/IDXX 一致）。
3. 可选：设计债——chip 系统全面化（coverage/strategy badge）、section 标题统一；或用户的 Claude Design mockup（Variant 用背景色区隔）进一步精修。

## 6. 陷阱与约束
- **本地优先 ship gate**：所有 UI/功能改动先本地 `streamlit run` 给 URL 眼验，用户明说「ship/push」才 commit+push。本次已获明确 push 指令。
- **改 lib 函数签名/加新函数后云端必 Reboot**（见 §5.1，本项目最大的坑）。
- **macOS**：`grep -E` 不用 `-P`；`date` 不支持 `%3N`；无 `timeout` 命令。**中国网络**：yfinance/SEC 走代理 `http://127.0.0.1:7897`。
- **离线要求**：网站在用户关机/无网时也要能跑——runtime 只读 committed `snapshots.db`，iFind 仅在「灌种子那一刻」用。新功能不得引入 runtime 实时网络依赖。
- **内部 LLM Wiki**（`~/Documents/LLM Wiki/`）是**不常驻的同步盘**，本 session 期间掉线过 → app 自动回退 repo 公开脱敏版（`data/wiki/companies/`，32 文件，无评级/TP，合规如此）。memo 新格式两种状态都正常。
- 别碰：`demos/`、`docs/HANDOFF.md`(本档外)、`docs/handoffs/*`、根目录 stray `snapshots.db`（真 DB 是 `data/snapshots.db`）——这些是预存在/无关文件，本次未提交。
- 页面文件名含 emoji（`6_🔍_*.py`）**不改名**，只改内容。

## 7. 打开的问题
- TEM 基准方向（见 §5.2）。
- hc_ai 桶里是否还有其它该挪的（用户已逐个 review，确认纯软件 VEEV/DOCS/CRM 保持软件）。
- 云端 Reboot 后是否一切正常（用户需亲验，我无 Streamlit Cloud 访问权）。

## ⚠️ 低置信度决策点（接棒人请核对）
- **TEM 我倾向 XLV 但用户未拍板**——别擅自加，等用户给字。
- 我没亲验云端（无访问权）；「离线/双币种/基准路由」全靠本地 AppTest 验证，**云端 Reboot 后请实际点开 1530.HK(港股本币)/BIIB(SEC趋势)/RXRX(XBI) 复核**。
- 内部 wiki 掉线是否永久未知——若它回来，Variant 三栏 + memo 评级/目标价条会自动出现（这是预期行为，非 bug）。

<!-- HANDOFF-END -->
