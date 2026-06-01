---
status: ACTIVE
created_at: 2026-06-01T12:16:58+08:00
updated_at: 2026-06-01T12:16:58+08:00
project_root: /Users/gcc/invest-dashboard
mission: 一批 local-first 未提交改动（上一棒「港股IPO打新」接入 + 本 session 4 组 UI/数据微调）待 George 本地验收，说「可以 ship」后 commit+push。⚠️ data/snapshots.db 是 git-tracked，必须连库一起提交，否则新数据不上 Cloud。
---
# HANDOFF — invest-dashboard 一批本地改动待 ship（IPO batch + 4 组 UI/数据修）

> 自包含交接包。接棒人只读此文件即可动手，不需要对话历史/git log。
> ⚠️ 全部改动是 **local-first 未提交**。核心待办 = 「George 说『可以 ship』→ commit+push」。**没说之前不许 commit/push**（项目硬约束）。

## 1. 任务 Mission
invest-dashboard（Streamlit 多行业看板，medical 是第一个 domain）现有一大堆 uncommitted 改动堆在 `main` 上，分两层：
- **上一棒遗留（已本地完成、未 push）**：Strategy Picks 第 4 个策略「港股IPO打新」(18 只评分×首日后测) + 个股热力图 v2 bento。
- **本 session 叠加的 4 组微调**（见 §2）：中英 i18n 漏字修复、Market Overview 加上证综指、IPO 卡口径改中位数、基准表 3M 列格式化。

George 的工作方式：**本地起 app 眼验** → 满意才 ship。app 现在跑在 `localhost:8501`（后台 streamlit，仍 alive）。

## 2. 进度快照

### 本 session 完成的 4 组改动（全部 ✅ 本地验证过，无 🟡 半成品）
- ✅ **中英 i18n 漏字修复**：英文模式下漏中文的三处 —
  - `app/lib/locales/pages_en.py` + `pages_zh.py`：`home.title` 原本两边都是双语 `"Market Hub 行情中枢"` → EN 改 `"Market Hub"`、ZH 改 `"行情中枢"`（其它 title 都是单语，就这条破例）。
  - `app/lib/heatmap.py`：bento 原是「中文为主+英文小注」固定双语版式，没接语言开关。改成按 `prefer_cn` 单语渲染——masthead 标题、domain head（`医疗`/`HEALTHCARE` 二选一）、block head、图例 `跌/涨`→`Down/Up`、`中位`→`Median`、`席`→空、`_DOMAIN_EN` 的 `"AI · 人工智能"`→`"AI"`。`_render_block(b, cn)` / `_render_domain(d, cn)` 加了 `cn` 参数。
  - `app/home.py:211` 基准面板脚注硬编码中文 → 加 `i18n.get_lang()=="zh"` 三元分支。
  - 验证：合成数据跑 `render_bento_html` 两种语言，EN 可见文案零 CJK（剩一条 CSS 注释里的中文，不渲染）。
- ✅ **Market Overview 加 A 股**：原 3 卡(S&P500/NASDAQ100/恒生) → 现 **4 卡**，A 股只加 **上证综指 `000001.SS`**。
  - 改了 4 处 sync point：`app/lib/benchmarks.py`（`_META` + `PANELS["broad_market"]`）、`jobs/fetch_eod.py`（`BENCHMARK_TICKERS`，cron 用）、`app/lib/i18n.py`（`_BENCH_ZH` 加「上证综指」）。
  - `app/lib/theme.py` `kpi_strip()`：>4 卡时改 `repeat(auto-fit,minmax(190px,1fr))` 自动换行，防大字号点位被挤裂；≤4 卡仍单行不变。
  - **本地 DB 已灌数**：`data/snapshots.db` 的 `benchmarks_daily` 加了 `000001.SS` 242 个交易日（yfinance period=1y，proxy 7897）。
- ✅ **IPO 卡口径改中位数**（`app/pages/4_Strategy_Picks.py` 第 3 张 KPI 卡）：George 要求「对外口径改中位，撤掉均值 +113%」。
  - 卡从「已上市平均首日 +113.2%（中位 +86.6%）」→「**已上市中位首日 +86.6%**，副文案『区间 −5% ~ +384%』」。
  - locale key `strategy.ipo.kpi.avg`/`avg_delta` → 改名 `med`/`med_delta`（zh.py + en.py 同步）；intro「平均/中位」→「中位」；note 去「平均/Mean」措辞、保留右尾极值说明。
  - 代码：删 `avg_ret=...mean()`，加 `lo_ret=...min()`，卡值 `med_ret`、副文案 `lo/hi`。对外两个 headline：**中位 +86.6% · 收涨率 88.2%**。
- ✅ **基准表 3M 列格式化修复**：`领域基准(XLV)及同业` 表里 3M 列显示原始浮点 `-6.3143…`、表头 `3M_%`。真因：`fetch_benchmarks()` 出 `3m_%` 列，但页面 rename/pct_cols 漏了它 → 掉进 text 列直接打印。
  - 修 `app/pages/2_Healthcare.py` + `app/pages/a2_ai_overview.py`（同一 bug）：rename 加 `"3m_%":"3M %"`、pct_cols 加 `"3M %"` → 走和别的列一样的箭头+1位小数+%+配色。`3M %` label 已在 `common_cols()` 定义好（en `3M %` / zh `3月 %`）。movers 表不受影响（它们显式只 select 1d/5d/1m/ytd）。

### 上一棒遗留（已本地完成，**非本 session 产出**，presumed-ready 但接棒人 ship 前应抽验）
- ⚪/✅ Strategy Picks「港股IPO打新」第 4 策略：`render_ipo_strategy()`（散点+盘中小图+双榜+方法论+免责），数据 `data/external/ipo_picks.csv`(18 行) + `ipo_day1_intraday.csv`。已过 /cccg 4-way。
- ⚪/✅ 个股热力图 v2 bento（`app/lib/heatmap.py` 大改 + `app/lib/charts.py` `_diverging_color` 等）。
- 这两块对应大 diff：`charts.py +192`、`strategy.py +32`、`4_Strategy_Picks.py +268`、`en.py/zh.py` 大段 IPO 文案——**这些行不是本 session 写的**，本 session 只在 4_Strategy_Picks.py / 两个 locale 里做了上面那一小撮 median 改动。

**环境状态**：branch `main` / 17 个 tracked 文件未提交（含 `data/snapshots.db` Bin 改动）/ 全部 `py_compile` 通过 / app 在 `localhost:8501` 后台运行中。
repro：`uv run --with-requirements requirements.txt streamlit run app/streamlit_app.py --server.headless true --server.port 8501`
**相关文件**：`app/lib/benchmarks.py`、`jobs/fetch_eod.py`、`app/lib/i18n.py`、`app/lib/heatmap.py`、`app/lib/theme.py`、`app/home.py`、`app/lib/locales/{pages_en,pages_zh,en,zh}.py`、`app/pages/{2_Healthcare,4_Strategy_Picks,a2_ai_overview}.py`、`data/snapshots.db`

## 3. 关键决策
- **A 股只留上证综指**：George 先说「沪深300/上证/创业板都要」，又先后撤掉创业板、再撤沪深300，最终只剩 `000001.SS`。沪深300 的 242 行 DB 数据已删干净，代码 4 处 sync 全回退。
- **IPO 用中位不用均值**：均值 +113% 被曦智 +384% 等右尾极值拉高失真，中位 +86.6% 才是中枢——这正是 George 要的对外口径。
- **3M 按 home 页约定格式化（不是删列）**：首页基准表本就显示 `1D/5D/1M/3M/YTD` 格式化的 3M，Healthcare/AI 页只是漏接，补齐即对齐全站约定。
- **kpi_strip 用 auto-fit 而非固定列数**：5+ 卡固定 `repeat(n,1fr)` 会把 38px 点位挤裂；auto-fit 换行更稳，且不回归 ≤4 卡的页面。
- **DB 连代码一起 ship**：`data/snapshots.db` 是 git-tracked（不是 gitignore），新指数要上 Cloud 必须把库一起 commit；否则 Cloud 上「上证综指」卡显示「—」直到下次 cron。

## 4. 失败的尝试（别重走）
- **恒生科技 `^HSTECH` / ChiNext `399006.SZ`/`399102.SZ` 在 yfinance 上不可用**：恒生科技 404；创业板系列只返回当天 1 个 tick（无历史）。所以 Market Overview 没法加这两个（会显示空/半空卡）。HK 第二指数若以后要加，只有 `^HSCE`(国企指数) 在 yfinance 可靠；George 本轮选择不加 HK 第二指数。
- 单 ticker `yf.download(t)['Close']` 在新版 yfinance 会因 MultiIndex 列报 TypeError——探活要用 `group_by='ticker'` 批量取再 `d[t]['Close']`。

## 5. 下一步
1. **George 在 `localhost:8501` 眼验**：首页 Market Overview（4 卡含上证综指 + 切中英验 i18n）、Strategy Picks 的 IPO median 卡、Overview 页 3M 列格式。
2. George 说「可以 ship」后 → **一次性 commit 代码+locale+DB**（17 个 tracked 文件，含 `data/snapshots.db`），再 push。建议拆 1~2 个语义 commit：①本 session 4 组微调 ②上一棒 IPO/heatmap batch（如尚未单独提交）。
3. push 前确认 untracked 里哪些要入库（见 §7）。

## 6. 陷阱与约束
- **local-first ship gate（硬约束）**：改动必须 George 本地眼验、明说「可以 ship」才 commit/push。没说就只留在工作区。
- **`data/snapshots.db` 是 git-tracked**：ship 时务必连库提交，否则 Cloud 数据不更新。改库前已建备份 `data/snapshots.db.bak-add-ashare-20260601-115025`。
- **侧栏导航标题刻意双语**（`streamlit_app.py:39` 注释「by user request」）——`Market Hub 行情中枢` 等是故意的，**不要**当 i18n bug 去「修」。
- **个股页内部合规免责声明**（`6_Ticker_Drill.py:402`）是刻意中文（挂在中文 wiki memo 上），wiki memo 章节名（催化剂/风险点）是中文研报**数据**——都不是 i18n chrome 漏字，别动。
- macOS：用 `grep -E`，不用 `grep -P`；`date` 无 `%3N`（毫秒）；`timeout` 不存在。中国网络代理 `http://127.0.0.1:7897`。
- 改库/批量删前必先备份（已遵守）。

## 7. 打开的问题
- **untracked 哪些要入库**：`data/external/ipo_picks.csv` + `ipo_day1_intraday.csv`（IPO 策略依赖，**很可能要入库**）；`docs/ipo-*.md`（分析产出）；`docs/prototypes/heatmap_v2_realdata.html`。**不该入库**的：`cov_err.txt`、`cov_out.json`（疑似临时调试产物）、根目录 `snapshots.db`（0 字节 stray，可删）、一堆 `data/snapshots.db.bak-*`（备份，本地留即可）。ship 前请 George 确认清单。
- 是否真的要把 50MB `data/snapshots.db` 反复 commit 进 git（仓库膨胀）——长期可考虑 LFS 或改 cron-only，但**本轮按现状（tracked）走**，别擅自改方案。

## ⚠️ 低置信度决策点（接棒人请核对）
- **§2「上一棒遗留」那几行（charts.py/strategy.py/4_Strategy_Picks.py 大 diff）我没逐行读**——本 session 没碰这些，是从 git diff 推断为上一棒产物。ship 前若要拆 commit，请 `git diff` 实看归属，别把它们算成本 session 的改动。
- IPO median 卡副文案我**自作主张**填了「区间 −5% ~ +384%」补分布上下界；George 没明确要这个，可能想留空或换措辞——请优先确认这一处。
- 备份文件名时间戳 `20260601-115025` 是凭 ls 记的，落库前以 `ls data/*.bak-add-ashare-*` 实查为准。

<!-- HANDOFF-END -->
