---
status: ACTIVE
created_at: 2026-05-31T17:00:00+08:00
updated_at: 2026-05-31T17:00:00+08:00
project_root: /Users/gcc/invest-dashboard
mission: 投研看板「Market Hub 行情中枢」一次大改造——首页重构 + AI 全域 universe 接入 + 侧栏严肃化 + 全个股 wiki 接通。全部本地完成+验证，但一律未 commit（local-first ship gate，待 George 说「可以 ship」一次性提交+云端 Reboot）。
---
# HANDOFF — Market Hub 行情中枢 大改造（完成态，待 ship）

> 自包含交接包。接棒人只读此文件即可动手，不需要对话历史。
> ⚠️ **本 session 改动巨大且一律未 commit**（last commit `45783ff` = session 开始）。核心待办是「George 眼验 → 说『可以 ship』→ 一次性 commit+push+云端 Reboot」。

## 1. 任务 Mission
George（CMSI 卖方分析师）一长程 session 把医疗投研看板扩成**多领域平台**：① 首页重构（标普子行业表 + 分域折叠）② 接入 **AI 全域 universe**（135 个 AI/半导体个股，仿 healthcare 域）③ 侧栏严肃化 ④ 全个股 wiki 接通。全部本地做完+机器验证，**未提交**——等 George 拍「可以 ship」。

## 2. 进度快照
- ✅ **首页重构**（`app/home.py`）：市场总览 KPI 卡×3（^GSPC/^NDX/^HSI）→ **标普500子行业 hero 表**（11 GICS SPDR ETF + ^GSPC 末行 ref，列 1D/5D/1M/3M/YTD/vs-SPX，染色 heatmap，^GSPC 斜体对照行）→ 医疗健康基准表 → AI 基准表 → Top Movers（domain 分域：HC movers / AI movers）。三域用 **st.expander 折叠 + CSS 重塑成 section 风格**。chip variant + `subsection()` + 删所有 st.divider + 表脚来源 caption（已去配色图例那句）。
- ✅ **AI 全域 universe**：`domain='ai'`，**135 标的 / 6 sector**（L1-L6：`ai_equip/ai_chip/ai_memory/ai_foundry/ai_interconnect/ai_server`）。`config/domains/ai.yml` + 6 个 `config/universes/ai_*.yml`。`.SH→.SS` 已归一化。prices+multiples 全抓（隔离脚本），47 个 US AI 名 SEC facts 已抓。i18n 6 sector 中英名 + AI benchmark 中文名。Ticker Drill `_route_benchmarks` 加 AI 分支（A股→512480/159819、日→2644.T、韩→091160、美→^SOX/SMH、港→3191）+ `_local_ccy` 支持 .KQ。
- ✅ **AI 5 页 domain 化**（`app/pages/a1-a5_ai_*.py`）：a1 全 universe(135, vs-SOX) / a2 overview / a3 heatmap / a4 valuation / a5 SEC。**自包含复用 db domain-ready helper，未改 HC 页（零回归）**。
- ✅ **AI 基准面板**（首页）：11 跨市场 AI benchmark（^SOX/SMH/AIQ/2644.T/091160/442580 HBM/512480/515880/159819/588200/3191.HK，ai-researcher 评审定）。已 backfill 进 benchmarks_daily。
- ✅ **侧栏严肃化**：去 emoji（8 页 `git mv` 去文件名 emoji + AI 页 `icon=` 删）+ nav 字体 Inter + 三大类 **Global/Healthcare/AI 红纵肋**（`stNavSectionHeader` border-left）+ 隐藏「View more/less」钮。
- ✅ **wiki 接通**：`wiki.py` 加 `Wiki/AI/companies` **递归**根（rglob）；`export_wiki_public.py` 扩展含 AI + HC源缺失不 bail。`data/wiki/companies` **32→196**（HC 32 脱敏 + AI 164 脱敏）。所有个股详情页（含 AI）现有 wiki。
- ✅ **改名**：首页 → **「Market Hub 行情中枢」**（主标题 home.title 中英 locale + 侧栏落地页项 title，双语常驻格式）。
- ✅ **cccg 验收**（对照 healthcare）：无 BLOCKER；修了 a4 KeyError（return 列 guard）+ a1 侧栏 Coverage→Universe + a5 SEC Company Facts。
- 🟡 **expand_more bug**（`app/lib/theme.py:281-282`）：刚 hide `stNavSectionHeader` 折叠箭头(`stIconMaterial` display:none) + `pointer-events:none`。**未经 George 眼验确认是否真消失**——上一次 hide `stSidebarNavViewButton` 修错了元素。
- ⚪ **commit/push**（全部未做，待 ship gate）。

**环境状态**：branch `main`；**一律未提交**（last commit `45783ff`，session 开始那个）；AppTest 全绿（home + 5 AI 页 + Ticker Drill NVDA/688256/LLY + HC 回归 2/3/5/8 全 0 异常）；DB 已备份 `data/snapshots.db.bak-20260531`；本地服务跑在 :8521。
**repro**：`uv run --python 3.12 --with-requirements requirements.txt streamlit run app/streamlit_app.py --server.port 8521 --server.headless true`
**改动规模**（`git diff --stat`）：14 tracked 文件 +548/−138；`data/snapshots.db` 17.9→31.3MB；8 页改名；新增 6 AI config + ai.yml + 5 AI 页 + ~196 `data/wiki/companies/*.md`（均 untracked，ship 时 `git add`）。
**相关文件**：`app/home.py`、`app/lib/{benchmarks,i18n,ui,wiki,theme,db}.py`、`app/lib/locales/pages_{zh,en}.py`、`app/pages/6_Ticker_Drill.py`、`app/pages/a1-a5_ai_*.py`、`app/streamlit_app.py`、`config/domains/ai.yml`、`config/universes/ai_*.yml`、`jobs/{fetch_eod,export_wiki_public}.py`、`data/snapshots.db`、`data/wiki/companies/`。

## 3. 关键决策
- AI sector = 产业链 **L1-L6**（L7 云/应用 + 未上市不纳入，与 wiki 建页范围一致）。
- AI 5 页 **自包含复用 domain-ready helper，不改 HC 页**（HC 是生产域含 audit 修复，零回归优先）——而非共享函数重构。
- AI 数据用**隔离 fetch 脚本** `/tmp/fetch_ai.py`（复用 fetch_eod 函数，无阈值中断），避免脏数据顶破 fetch_eod 阈值连累 healthcare 那批。
- wiki「更新一遍」= **接通 + 同步脱敏镜像**（AI 164 页本就新鲜，缺的是接线），**非逐家重生成研究正文**。
- benchmark 列采纳分析师集 `1D/5D/1M/3M/YTD/vs-SPX`（砍 6M/12M，6M 与 YTD 共线）。
- 涨跌配色锁 **teal 涨 / red 跌**（国际惯例，不开红涨绿跌）。
- 三域用 expander + CSS 重塑成 section 风格（George 要可折叠但保持 section 字体/纵肋，非 expander 默认小字）。

## 4. 失败的尝试
- hide `stSidebarNavViewButton`（「View more/less」钮）**不是** expand_more 真凶 → 真凶是 `stNavSectionHeader` 自带的可折叠箭头（onClick + `:material/expand_more:`）。已改打这个。
- `export_wiki_public.py` 初版在 `Wiki/companies` 缺失时 early-exit bail（HC 同步盘掉线）→ 已修：HC 源缺失不 bail、仍处理 AI、不清空已有镜像。
- ticker `ON`（ON Semiconductor）YAML 无引号被解析成 bool True → 存成 `'1'` → 已加引号 `"ON"` + 删 DB 脏行。
- `4185.T`（JSR）已被 JIC 私有化退市、yfinance 无数据 → 已从 ai_equip.yml 剔除（135 = 136−1）。
- `/cccg` 三路全成功（Codex+Gemini+GLM，含 Gemini 这次没 geo-block）。

## 5. 下一步
1. **George 眼验**：① 收起侧栏确认旋转的 expand_more 真没了（最关键，未验证）② 标题/侧栏首项「Market Hub 行情中枢」③ 三大类纵肋 + 侧栏所有项正常 ④ AI 个股（NVDA/688256）详情页有 wiki。
2. George 说「**可以 ship**」→ `git add` 全部（含 8 renames、AI configs/pages、`data/wiki/companies` 196 文件、`data/snapshots.db`）→ commit + push → **提醒云端 Streamlit Cloud Manage app → Reboot**（清 sys.modules + cache_data，改了 lib 签名）。
3. （可选）cccg MINOR backlog（见 §7）。

## 6. 陷阱与约束
- **local-first ship gate**：George 明说「可以 ship」才 commit/push（硬规则，见 auto-memory `local-first-ship-gate`）。
- **改 lib 签名后云端必 Reboot**（sys.modules + cache_data 缓存旧 df → 假错）。
- **HC 内部 wiki（`~/Documents/LLM Wiki/Wiki/companies`）当前掉线**（不常驻同步盘）→ HC 个股暂走 `data/wiki` 镜像 32 页；盘回来后重跑 `export_wiki_public.py` 补 HC 内部页（AI 在 `Wiki/AI/companies` 164 页，在线）。
- **中国网络**：yfinance 走 `HTTPS_PROXY=http://127.0.0.1:7897`；SEC 走 `SEC_PROXY=http://127.0.0.1:7897`。`grep -E` 不用 `-P`。
- **离线**：runtime 只读 committed `data/snapshots.db`；新功能不得引入实时网络依赖。
- **别动**：根目录 stray `snapshots.db`（0 字节，真 DB 是 `data/snapshots.db`）、`demos/`、`docs/handoffs/*`。
- load_universe 是纯追加（INSERT OR REPLACE，无 DELETE）→ 安全；写 DB 前已备份。
- 页面文件已**去 emoji 改名**（`6_Ticker_Drill.py` 等），url_path 不变 deep-link 不断。

## 7. 打开的问题
- **expand_more 修复是否真生效**（§2 🟡，未眼验）——若仍漏，箭头可能非 `stIconMaterial`，换选择器（如 `stNavSectionHeader > *:last-child`）。
- **「wiki 更新一遍」是否要逐家重生成研究正文**？本次只做接通+同步；若要 241 家现取数重写正文是另一大工程，需单开。
- **TEM (Tempus AI) benchmark** 仍未定（最早 backlog，现 hc_ai→IGV+纳指，倾向 XLV）。
- **cccg MINOR backlog**（不阻断 ship）：① 515880(中证通信) 稀释 CPO beta → 表注标明或换算力 ETF ② 「芯片设计」→国内口径「Fabless」③ HBM/先进封装显性标签 ④ a2 概览描述取自 ai.yml 中文 description、**EN 模式不翻**（i18n gap）⑤ 港股 AI 链单薄（可加中芯 02878.HK/ASMPT 01975.HK）。
- `data/wiki/companies` 196 文件 git 追踪状态：当前全 `??`，ship 时确认 `.gitignore` 不排除、`git add`。

## ⚠️ 低置信度决策点（接棒人请核对）
- **expand_more 修复未经 George 眼验**（最可能未验证）——他上一条说「我点还是会有一个旋转的 expand home 没有改好」是针对**上一版**（hide View 钮）；最新版（hide stNavSectionHeader 箭头）他还没看。
- **首页名最终是「Market Hub 行情中枢」**（George 最后定的；中途曾试「全域投研台」「Research Hub 投研中枢」，均被否/改）。
- AI 数据里若见极端单日涨幅（如 DELL +32.8%）——是 yfinance 该日真实收盘算出（非 pipeline bug），本环境数据如此。

<!-- HANDOFF-END -->
