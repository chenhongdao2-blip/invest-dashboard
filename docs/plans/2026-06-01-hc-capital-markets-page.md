# Plan — Healthcare「Capital Markets 投融资」页 (ED-Funding tracker 上看板)

> 研究产出 (ultracode 4-lens workflow + 对抗式 critic, 2026-06-01)。源数据 = `~/yuqing-system/healthcare/ed-funding/`。目标 = invest-dashboard `Healthcare 医疗健康` 栏目加一行。
> Status: 待 George 拍板。**未动任何代码**。

## 0. 一句话

把 George 每月手写的「ED CN XM26 Funding」月报变成看板里一个 **双语、可月度刷新** 的 `Capital Markets 投融资` 页:trailing-12M 资金流 tracker (6 序列, 美元 vs 交易数) + B3-可拆解的 Top-Deals 榜 (头条 $15.2B → 真实现金 $950M 视觉化) + China-OUT 制度性拐点 banner + MNC 干火药表 (SEC HIGH 源)。每个数字带 (来源, 截至) + HIGH/MEDIUM/LOW tier,**不搬任何卖方评级**。

## 1. 数据真相 (critic 实测 3 个源文件后的结论)

### ✅ 已验证、现在就能上 (纯 aggregate JSON, 全在磁盘)
- 6 条月度序列 × 12 月 (2025-04→2026-03): 总投融资额 / 药 M&A / 药 VC&IPO / 器械 M&A / 器械 VC&IPO / 数字医疗 VC&IPO,每条带 capital + deal count
- 派生: MoM% / TTM 总额 / M&A-vs-VC bucket / 子板块占比 / avg deal size
- China-OUT banner 事实: $19.3B (4-5月合计, 已逐笔核对 15.2+2.75+0.745+0.445+0.120=19.26) + 52% (NextPharma, 截至 2025-09-04)
- **单位陷阱 (必修)**: 总额是 USD **bn**,5 个子序列是 USD **mn** → loader 必须 ×1000 归一,否则器械面板错标 1000 倍

### ⚠️ critic 抓到的硬伤 (上线前必处理)
| # | 问题 | 严重度 | 修法 |
|---|---|---|---|
| G1 | KPI「12M 成交 1,579 笔」**是错的** — 1,579 是最新月 (2026-03) 值,不是 12M 总和 (真 TTM ≈ 21,586) | 🔴 high | 卡片改标「最新月成交 (2026-03) 1,579」或算真 12M 和,二选一,窗口写明 |
| G2 | Top-Deals 榜的招牌功能「每行都有 头条$ + 真实现金$」**只对 2-3 个 deal 成立** — 磁盘上只有 海思科 / Gilead-Tubulis / 恒瑞(lump $950M) 有拆分;其余 6+ 笔(Amoytop/Insilico/Huahui/Sun-Organon/Kelonia/BSX/Kailera)磁盘无拆分 | 🔴 high | 真实现金列只填已披露的,其余明标「n/a — 头条值未拆分披露」,**不臆造**;榜重新定位为「B3 在恒瑞旗舰 + 2 个干净对照上演示」,decomposition bar 只画有真拆分的 2-3 笔 |
| G3 | 恒瑞 `$600M+$175M+$175M=$950M, 15x` 三行拆解 **不在任何磁盘源文件** (grep 零命中),只存在于 synthesis block (引 HKEX/Cardiff) | 🔴 high | 渲染前先把它转录进 `funding_deals.csv` 并带自己的 (来源: HKEX 1276 公告, 截至 2026-05-12) 戳;若 George 指不出 HKEX 原文行,只显示「$15.2B 头条 → $950M structured (aggregate)」不编内部 split |
| G4 | 3-col「药/器械/数字医疗」sparkline 网格映射到 5 序列别扭 (数字医疗只有 VC&IPO 无 M&A) | 🟡 med | 改 5 面板,或保留 3 域但脚注「数字医疗 = 仅 VC&IPO」 |
| G5 | MNC 余额表 critic **没读到** JSON (不在给的 3 个路径),18 ticker/12 有现金/6 null 未独立验证 | 🟡 med | George 上线前眼验 `mnc_balance_sheet_2026Q1.json`;6 个 null (NVS/AZN/SNY/NVO ADR+PHG+GEHC) 标「无 us-gaap 现金」非 0;补 README 脚注 (us-gaap 现金不含短投→PFE/MRK 低估) |
| G6 | 5 子序列之和 ≠ 总额 (2025-04: 30.6bn vs 44.49bn, 口径不同) | 🟡 med | 图副标题硬编码「5 个追踪子板块 (USD mn),不等于更广的总额 universe」,不留作「以后再定措辞」 |
| G7 | 评级洗白风险: draft 第 34 行有 8 个「增持」(LLY/NVS/BMY/VEEV/3692/1801/2162/2256),这些 ticker 会作为 licensor/acquirer 出现 | 🟡 med | 代码级断言:任何渲染 cell 不得含「增持/买入/Overweight/Buy」;deal 只搬事实数字 |

## 2. 页面设计 (设计 lens, 对齐现有视觉系统)

- **命名**: `Capital Markets 投融资`, url_path `HC_Capital_Markets`, 文件 `app/pages/9_HC_Capital_Markets.py` (接 1-8 HC 序列;注: 设计 lens 的 9_ 对, pipeline lens 的 `6_HC_Funding` 撞 6_Ticker_Drill,作废)
- **位置**: `Healthcare 医疗健康` 组**最后**一个 (收尾的自上而下宏观/资金流 tab,接在 SEC Facts 后)
- **布局** (复用 Strategy Picks IPO 那套 pattern):
  0. init_lang + toggle **首位** (ship-gate #3 单语渲染) + as-of 戳
  1. KPI strip (4 张 cmsi-kpi HTML 卡, **非** st.metric): 12M 总额 $138.4bn+MoM / 成交笔数(见 G1) / 最大子板块占比 / China-OUT 合规卡 (同卡显 头条$15.2B + 真实现金$950M)
  2. **招牌图**: `capital_dual_axis_chart` (新) — 柱=Capital(左轴 teal) + 线=Deal Count(右轴),segmented_control 选序列,单位从序列头读
  3. 子板块对比: 复用 `charts.mini_trend_chart` 3-col 网格 (零新代码, 见 G4)
  4. Top-Deals 榜: `ui.render_html_table`,头条$ 与 真实现金$ **两列分开** (G2/G3 约束)
  5. China-OUT 主线: `deal_decomposition_bar` (新) 水平堆叠拆 upfront/milestone,只画有真拆分的 (G2)
  6. MNC 干火药表: `ui.render_html_table` (G5)
  7. 方法论 expander (B1-B7 verbatim) + 免责
- **新 chart helper**: `capital_dual_axis_chart` + `deal_decomposition_bar` (+ 可选 `mnc_balance_bar`);其余全复用 charts.py/theme.py 现成件
- **i18n**: `capital.*` 命名空间, 注册进 pages_zh.py + pages_en.py;6 个原始序列 key 保持中文在数据层,只翻显示 label

## 3. 数据层 + 更新机制 (pipeline lens, 已解分歧)

- **Aggregate 6 序列** → snapshots.db 新表 `funding_monthly` (long format, 仿 benchmarks_daily, 全归一 USD mn, 带 source_tier/as_of/ingested_at);**MVP 先直读 JSON** (copy 进 data/external/) 几天上线,P1 再换 DB read 同 query 路径不返工
- **Deals** → MVP 用手维护 `data/external/funding_deals.csv` (照 ipo_picks.csv 模式, 含 name_cn/en + B3 列 + sum_check + source_tier + status);full 版才升级到 typed DB 表 + adapter drop file
- **MNC** → v1 直读现有 2026Q1 JSON (单快照,表即可)
- **绝不** 让 Streamlit 在 Cloud 上 live-read `~/yuqing-system` (Cloud 无文件系统访问,同 live-yfinance 旧 bug);ingest 时 copy/转录进 repo
- **更新节奏 — 诚实两轨,非静默 cron**:
  - Track A (6 序列): 纯 JSON→SQLite 秒级可脚本,**但**上游 yuqing aggregate JSON 本身得先刷 (PitchBook 式手动导出 = 真瓶颈)
  - Track B (deals): **本质人工** — mnc-deal-scanner 是 chat-native MCP 链,只能在交互 Claude session 跑,且故意把「apply? yes/no」卡在人手上 (合规: $15.2B 头条必须人验成 $950M 真现金才上投资人面)
  - 现实终态 ≈ 5 分钟/月: 刷 aggregate + (手改 CSV 或跑 scanner 载 drop file) + `git commit 'data: funding refresh YYYY-MM [skip ci]'`
  - 看板的活是**让 staleness 可见** (last-refresh + 「>30d 待更新」banner),不是假装自动化

## 4. 分阶段

| Phase | 内容 | 估时 |
|---|---|---|
| **P0a** ✅ critic 放行 | Aggregate tracker (funding.py 直读 JSON + dual-axis 图 + KPI strip + sparkline + China-OUT banner事实 + 单位归一)。纯磁盘数据,干净可上 | 1-1.5 天 |
| **P0b** ⏸ critic HOLD | Top-Deals 榜 + 拆解 bar。**门槛 = 先解 G2/G3 数据真相** (逐 deal 拆分+源戳, 或重定位为「恒瑞旗舰+对照」)。effort 真成本在合规级转录+逐行验源,非渲染码 | 1-1.5 天 (数据转录为主) |
| **P1** | DB 毕业: init_funding_tables + load_funding.py (仿 fetch_eod) + funding.py 改读 DB + staleness banner + runbook | 1-1.5 天 |
| **P2** | Deal 自动化 (adapter drop→typed 表) + 外部 tier-tagged 指标 (YoY/US91%/upfront6%) + 2025Q3 MNC baseline 做趋势 + 可选 IPO CSV | 2-3 天 + ~5min/月 |

## 5. critic 最终判定

> **CONDITIONAL GO** — P0a (aggregate tracker) 立即放行,真实/单位正确/纯磁盘数据。P0b (deal 榜) HOLD,直到 B3 数据可用性如实解决:repo 可读文件只有 2-3 个 deal 有真拆分,恒瑞 `$600/$175/$175→$950M` 锚点零磁盘命中。要么逐行转录带源戳 (多数真实现金列诚实写 n/a),要么把榜重定位为「恒瑞旗舰+干净对照」。修好那一列的数据真相,其余 plan 成立。

## 6. 决策记录 (George, 2026-06-01)

- ✅ **D1 P0 拆分**: 同意。先上 P0a aggregate tracker,P0b deal 榜等数据源齐再上。
- ✅ **D3 恒瑞拆解**: **只显 `$15.2B → $950M (aggregate)`**,不渲染 $600/$175/$175 内部 split (避免凭空造数,G3 关闭)。
- 🔵 **D2 Deal 表源 → 推荐 CSV** (George 在问;我的建议见下,理由绑定 2-day cadence)。
- ✅ **Cadence 改 2-day** (原 monthly): George「既然放到网上了,每两天一次」。**但需按数据层拆**(见下,待 George 确认口径):
  - **Aggregate 6 序列**: 本质月度粒度,每 2 天刷=同样数字+新时间戳(假新鲜)。→ 真实做法:月度更新 (新月 JSON 落盘时),banner 标「数据截至 YYYY-MM 月度」
  - **Deal 表 + China-OUT**: 真有每几天的新 BD/M&A 流 → 2-day cadence 在这层有意义 (CSV 每 2 天更),page 显新 deal
  - 含义: **deal 层 = 2-day (CSV), aggregate 层 = monthly (其真粒度), 各带各的 截至戳**
- ⏳ **D4 合规口径** (待定): 投资人面显不显 $15.2B 头条? 设计假设 头条+真现金并排。评级**强制全剥**(已定铁律)。
- ✅ **D5 刷新 ownership → 我(Claude)负责**,机制 = **SessionStart hook 自动检测** (George: 「我打开 dashboard / 在这文件夹开 cc 时自动检测刷新」)。详见 §7。
- ⏳ **D6 HC-only vs 多域** (待定): url 已 namespace `HC_Capital_Markets` 防撞,默认 HC 专属。

## 7. 自动刷新机制 (D5, SessionStart hook)

**做得到。** 确认:项目级无 hook(我加),全局已有 SessionStart hook(handoff-detect.mjs)证明机制可用,iFind news MCP 已连通。

**设计**:
1. **检测**(project SessionStart hook, 仅 `source=startup` 不在 resume/compact 触发,避免每次 resume 都扫):读 last-refresh 戳(`data/external/.funding_last_refresh` 或 snapshots.db meta key)→ 算 staleness → ≥2 天则注入 `<system-reminder>`「📊 funding deal 数据 N 天未刷 → 触发 2-day refresh」。hook 是 shell/node,**不能调 MCP**,只负责检测+发信号。
2. **执行**(我接信号后):exa + iFind news(+ pharmcube 若活)扫最近 HC BD/M&A → B6 cross-check → 更新 `funding_deals.csv` → 报新增几条。
3. **合规融进刷新**(D3 已同意「待核」):**HIGH/MEDIUM 才上投资人面;LOW/单源进「待核」lane**(不当事实渲染)→ 你异步复核。这样 auto-push 也不会把未验证 deal 糊上 Cloud。
4. **aggregate 层不在此触发**(月度粒度,monthly 单独刷)。

**⏳ 待 George 拍板(碰 ship-gate 铁律)**: 刷新要到 Cloud 必须 commit+push,但你的规矩是「George 说可以 ship 才 push」。要真自动就得 auto-push。
→ **提议**: `funding_deals.csv` 这类**纯数据刷新预授权 auto-commit+push**(不含代码改动),但每次我**报清推了什么 + 待核几条**,你可异步 revert/纠正;**代码改动仍走老 ship-gate**(你眼验说「可以 ship」)。确认这个口径?

**排序**: 此 hook 等 **P0b(页面+CSV)活了、deal 数据上了 Cloud** 再挂——现在还没 CSV 可刷。先 P0a → P0b → 挂 auto-refresh hook。

## 8. 刷新编排器 — 开 cc 自动刷所有 stale 数据层 (George: 「不限于医药 BD」)

### 关键发现: 刷新早已分两类,编排器补 cron 补不了的那类
| 类别 | 机制 | 内容 | 开 cc 要做啥 |
|---|---|---|---|
| **Cloud cron (已有)** | GitHub Actions (`fetch_eod.yml` / `fetch_sec_facts.yml`),**无 MCP** | 价格/multiples/benchmarks/profile (`fetch_eod.py`) + SEC facts (`fetch_sec_facts.py`)。自动提交 snapshots.db | **不用刷**,编排器只读其 freshness 报状态 |
| **缺口: MCP-依赖,cron 跑不了** | 需本地 session + MCP | iFind CN benchmarks (`fetch_cn_benchmarks.py` 注释明说「cron can't reach iFind」) / 医药 BD deals (exa/iFind news/pharmcube) / funding aggregate / news | ✅ **这正是开-cc-orchestrator 该 own 的** |

→ 分工清楚: **cloud cron = 市场数据 (yfinance/edgar 无 MCP);开 cc = MCP 数据 (iFind/exa/pharmcube/news)**。George 的直觉对,编排器专攻 cron 物理上做不到的。

### 设计
- **manifest** (registry, 仿 yuqing `sources.yaml`): 每源声明 `{id, cadence, mechanism: cron|local_session|mcp_sweep, staleness_key (meta/marker), action, cost, auto|gated}`。已有 freshness 戳可复用: `last_fetch_utc` / `last_snapshot_date` / `last_sec_fetch_utc`。
- **SessionStart hook (仅检测)**: `source=startup` 时读 manifest + meta → 注入**一张 freshness 表**(谁 fresh / 谁 stale / 我该刷啥)。hook 是 shell/node,**不调 MCP**,只检测+发信号。
- **我 (执行)**: cheap/local 秒级 → inline 刷;expensive (BD 全扫+cross-check) → `run_in_background` **不卡你当前任务**,完成再报;full `fetch_eod` **不在本地跑** (那是 GA 的活,慢+rate limit)。
- **cost-aware 铁律**: 开 cc 不能卡几分钟等刷新;重活后台跑 + 完成通知。

### 首批 lane
1. 医药 BD/deals (原始需求, 2-day cadence, mcp_sweep)
2. **iFind CN benchmarks (现成缺口, easy win** — cron 本就跑不了的,顺手纳管)
3. funding aggregate (monthly, 上游 JSON 落盘时)
4. 未来按需注册更多 lane

### push 口径 (D5 附属, RESOLVED)
GitHub Actions **早已自动提交 snapshots.db 数据**(你说的 `[skip ci]` data commits)→ **数据刷新 auto-commit+push 与现状一致,预授权**;**代码改动仍走 ship-gate**(你眼验说「可以 ship」)。一致,无新增风险。

### 排序
编排器是 **P0b 之后的独立基建**。先把 funding 页做活 → 再建 orchestrator (lane 1=BD, lane 2=iFind bench)。不让基建卡住建页。

### D2 建议: 用 CSV,不等 scanner 管道 (理由)
2-day cadence 直接判了这题 —— 全量 mnc-deal-scanner 一次 ~150-200 MCP queries + 每次人手合规 gate;每 2 天跑 = ~2-3k queries/月 + 你一月坐 15 次 loop,不现实。CSV 天然贴合 2-day 节奏 (你日常本就在看这些 deal,落地时 drop 新行)。scanner 留作**月度深扫 backstop (P2)**。
附带好处: 2-day 频繁提交下,deal 放 `data/external/funding_deals.csv` (tiny diff) 比进 snapshots.db (49MB blob 每 2 天重提交=仓库膨胀加速) 干净 —— 这也顺带定了 deal 数据层选 CSV 而非 DB 表。
