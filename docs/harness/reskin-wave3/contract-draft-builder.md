# CONTRACT DRAFT — Builder 提案 (wave-3 · 眼验反馈三连修)

> 角色：Builder-negotiator。本文 = 实现方案 + 可测试验收项**提案**，供 Evaluator 反驳博弈。
> 分支 `feat/kline-reskin`；基线 HEAD `154a36c`（wave-2 全绿 85/85 + wave-1 11/11）。
> Builder 物理碰不到 `CONTRACT.md` / `feature_list.json` / `eval/`（SPEC §全局约束 4）。
> 验收方法代号沿用 wave-2 §3：**RM**(改 lib 必 kill+relaunch :8599 / py_compile / AppTest)、
> **JS**(claude-in-chrome computed-style 主判定门)、**GR**(grep 电池零命中)、
> **SS**(截图旁证)、**PS**(=本 wave 新增：`_build_html`/自测**纯字符串探针**，py 层静态断言，无浏览器)。

---

## §0 不动面声明（Builder 承诺不回归；Evaluator 应抽查）

| id | 冻结项 | 依据 |
|---|---|---|
| NT1 | wave-2 §0 D1-D5 全部（跌色 #c8102e 页级豁免 / D3 呼吸点语义诚实 / 自托管字体 / D5 玻璃壳原语 / theme.DOWN 不动） | wave-2 CONTRACT §0 |
| NT2 | **BANR1-12 逐条**——尤其 BANR2(中/EN 切换只换皮不换交互，`?lang=` 真锚点 + query_params 机制保留)、BANR3(青呼吸点 EOD 跟踪)、BANR4(dek 包样式 14/1.65/#4a4a4a/max-880 + `**`→`<b>` 墨、`\n\n`→`<br><br>`；包装器 `4_Strategy_Picks.py:146-149` **不动**)、BANR7/8/9(曲线/盈亏点/IPO 卡数据接真) | wave-2 CONTRACT §2 BANR |
| NT3 | **IPO1-IPO15 数字级修复逐条**——d1 DECIMAL ×100 仅一次 / code 保持 str 前导零 / None-NaN 诚实渲染 `—` / pending rank `—` + 待上市沉底 / 盘中路径末笔 NaN 整路径丢弃(ipo_stage.py:455-466) / 终点口径=首日收盘锚(IPO12) / 零 `Math.random·genData·正弦` 伪造路径 / 零 MOCK / 零 demo 字面量(2.69/384 硬编) | wave-2 CONTRACT §2 IPO + Codex 终审 7 findings(HEAD c8bb06e/9d198e2) |
| NT4 | `theme._CSS` **零本次新增规则**（GRD6 同款）；`GLASS_CARD_CSS` 选择器不扩类；F1 新皮**不进 theme._CSS**，走 i18n 模块内 inline HTML | wave-2 GRD6 |
| NT5 | `load_ipo` / `load_ipo_intraday` 数据管道签名不动；`strategy.compute_strategy_returns` 单源不动；排序**只动展示顺序，禁碰数值计算**(SPEC F3) | SPEC F3 |
| NT6 | Healthcare/AI 页 `sector_overview.masthead` 板块小节头**不在本 wave 范围**（SPEC F4 已核）；不触碰 | SPEC F4 |
| NT7 | 现实约束：自包含 srcdoc HTML、无外部 JS 库、macOS grep 无 `-P`(用 `grep -E`)、改 lib 必重启 :8599 | SPEC 全局约束 2 |

---

## §1 F1-toggle — 中英切换全站统一

### 现状核实（已抽查）
- 旧钮：`i18n.render_lang_toggle()` (i18n.py:241-260) = `st.columns((9,1)) + st.button` 实心红钮，点击翻 `session_state["lang"]` + `st.rerun()`。**19 调用点**全部无参调用（`i18n.render_lang_toggle()`）：home.py:39 + 18 个 pages/*.py（grep 实证：a1-a5 / e1-e3 / 1/2/3/3b/5/6/7/8/9_*）。
- 新钮：`strategy_banner.live_title()` 内 `seg()` (strategy_banner.py:222-239) = `<a href="?lang=zh|en" target="_self">` 描边分段，mono 11/600/.08em、p5-12、active bg=`t.CMSI_RED` 字=`t.PAPER`、inactive transparent+`t.INK_3`、外框 1px `t.PAPER_EDGE` radius3。
- query-param→state 读取**仅** 4_Strategy_Picks.py:41-44 一处（散、非中心化）。
- `init_lang()` 已在**每页顶部 + hub(streamlit_app.py:36)**调用（19 页 + hub 全覆盖）。
- 导入安全实证：`theme.py` 不 import i18n（无环）；i18n.py 现未 import theme（F1 将新增 `from lib import theme`，单向安全）。

### 实现方案
1. **新增纯 helper** `i18n.lang_toggle_html() -> str`：返回描边分段控件 HTML 字符串，**逐字节复刻 BANR2 现 seg() 产物**（同 CSS token），active 态由 `get_lang()` 内部判定（不再靠外部传 `lang='中'/'EN'`）。i18n.py 顶部加 `from lib import theme` 取 `CMSI_RED/PAPER/INK_3/PAPER_EDGE/FONT_MONO`。
2. **重写** `render_lang_toggle()`：删 `st.button`+`st.columns`，改 `st.markdown(<flex justify-content:flex-end 容器> + lang_toggle_html(), unsafe_allow_html=True)`，右上角定位。签名收敛为 `render_lang_toggle() -> None`（19 调用点全无参 → **零调用点改动**）。
3. **中心化 query-param sync 进 `init_lang()`**：`init_lang()` 内 seed 后追加——读 `st.query_params.get("lang")`，若 ∈{zh,en} 且 ≠ 现 `session_state["lang"]` → 置位 + `st.rerun()`（**保留 st.rerun，与 BANR2「机制保留」一致**）。因 init_lang 每页顶 + hub 均调用 = 唯一 choke point，覆盖含策略页（策略页 toggle 在 banner 内、不走 render_lang_toggle）。
4. **策略页去重**：删 4_Strategy_Picks.py:41-44 局部 qp 块（中心化后为死码；SPEC「single source」要求）。
5. **banner 收敛防发散**：`strategy_banner.live_title()` 的 `seg()` 内联块替换为 `i18n.lang_toggle_html()`（banner + 全站共用同一 helper）。live_title 的 `lang=` 形参保留兼容（仅控是否显示 toggle：None=不显示；非 None=显示，active 态由 helper 内部 get_lang 定，不再依赖传入的 '中'/'EN'）。调用页 4_Strategy_Picks.py:145 传 `lang=(...)` 维持真值即可。
6. **theme._CSS 425 注释**：旧注释「Covers the top-bar language toggle (a single st.button)」现失真——仅改注释文字（说明 toggle 已迁锚点），**不删/不增 CSS 规则**（stButton 规则其他钮仍用）。

### 验收项提案（F1-T*）
| id | 断言 | 方法 |
|---|---|---|
| F1-T1 | `i18n.lang_toggle_html()` 返回串含 `<a href="?lang=zh" target="_self"` 与 `<a href="?lang=en" target="_self"`；容器 `border:1px solid #d4c4b0`(PAPER_EDGE) + `border-radius:3px`；段样式含 `font-size:11px`+`font-weight:600`+`letter-spacing:.08em`+`padding:5px 12px` | PS(py import i18n；zh/en 两态各调一次断串) |
| F1-T2 | active 段 `background:#c8102e`(CMSI_RED) 且 `color:#fff1e5`(PAPER)；inactive 段 `background:transparent` 且 `color:#8a8580`(INK_3)——lang=zh 时「中」active、「EN」inactive；lang=en 反之 | PS(切 session_state["lang"] 两态断色) |
| F1-T3 | 任一非策略页(取 3 页：`8_SEC_Facts`/`e2_etf_heatmap`/`2_Healthcare`)真机 DOM 存在描边分段锚点(`a[href="?lang=en"]`)，且**无** `button[key="_lang_btn"]`(旧实心钮已消失) | JS(真机 querySelector) |
| F1-T4 | 真机点非策略页 `中` 段(zh 态点 en 段) → URL 加 `?lang=en` → 页面整体切英文(取该页一个已知 t() 串，如 SEC 页标题断言由中变英)；再点回 zh 段还原 | JS(click + 断标题文本 + SS 旁证) |
| F1-T5 | 策略页 banner 内 toggle 与非策略页 toggle **同一 helper 产物**：两处锚点的 outerHTML 结构一致(容器 class/style + 两 `<a>` href/style 逐字段等)；banner 视觉 BANR2 不回归(active bg #c8102e、容器 border #d4c4b0 radius3) | JS(策略页 + 一非策略页各取 toggle outerHTML 比对) |
| F1-T6 | 单源实证：`grep -En "query_params.get\(.lang.|st.query_params\[.lang.\]" app/` 命中**仅** `i18n.py`(init_lang 内)一处；4_Strategy_Picks.py 局部 qp 块已删 | GR |
| F1-T7 | 零调用点改动实证：`grep -rn "render_lang_toggle()" app/pages app/home.py` 19 处仍全无参；`render_lang_toggle` 签名无必填参 | GR+PS |
| F1-T8 | 工程：i18n.py + strategy_banner.py + 4_Strategy_Picks.py + home.py py_compile clean；AppTest(home/4_Strategy_Picks/2_Healthcare/a2_ai_overview 四页)zh/en 两态各渲一遍无 raw key、无 TypeError、无 import 环 | RM |

---

## §2 F2-pitch — strategy.pitch 换 B 口径

### 实现方案
- `zh.py:20-25` `strategy.pitch` → George 定稿逐字（SPEC F2 原文）：两段，粗体锚点 `**方法论**` / `**持仓自入选之日起登记在册**` / `**自选股日起的真实累计收益 vs 基准**`，段间 `\n\n`。保留 `**…**` markdown（BANR4 包装器消费）。
- `en.py:17-25` 镜像改写：financially professional，语义/粗体结构对齐（`**Methodology**` / `**logged on the record from the day of selection**` / `**real cumulative return vs benchmark since selection**`），非逐词直译。
- `zh.py` docstring 追一行备注：本次 supersede 旧 pitch(B 口径 George 拍板 2026-07-05)。
- **不动**：BANR4 包装器 `4_Strategy_Picks.py:146-149`(`re.sub` `**`→`<b>` + `\n\n`→`<br><br>`)。

### 验收项提案（F2-T*）
| id | 断言 | 方法 |
|---|---|---|
| F2-T1 | zh 态渲染后 pitch 段含定稿关键短语「本页跟踪一套量化基本面（Quantamental）选股体系的实盘表现」与「持仓自入选之日起登记在册」与「自选股日起的真实累计收益 vs 基准」；**旧文案「这是什么 — 一个展示 AI Agent 选股实际表现的平台」消失** | JS(策略页 zh 态断 dek 文本)+GR(旧串零命中) |
| F2-T2 | 粗体锚点保留：渲染 DOM 里 dek `<p>` 内含 `<b style="color:#1a1a1a;">方法论</b>` 等(BANR4 包装器把 `**`→墨色 `<b>`)；段落分隔 `<br><br>` 存在(≥1 处) | JS(断 innerHTML 含 `<b` + `<br><br>`) |
| F2-T3 | en 态镜像：pitch 英文含 `**`-粗体结构(≥2 处 `**`)、语义对齐(方法论/登记在册/真实收益 vs 基准三要点均在)；zh/en 均非空、无 raw key `strategy.pitch` | JS(en 态断)+PS(t('strategy.pitch') 两 lang 非 key 自身) |
| F2-T4 | BANR4 契约不回归：dek `<p>` 样式仍 `font-size:14px`+`line-height:1.65`+`color:#4a4a4a`+`max-width:880px`；包装器 4_Strategy_Picks.py:146-149 逐字未改 | JS+GR(diff 该 4 行) |

---

## §3 F3-ipo-rank — 排行表列排序 + 图表 dock 重设计

### 现状根因（已核实 ipo_stage.py）
- `.rank-grid{grid-template-columns:1fr 400px}`(L105)、`.dock{position:sticky;top:16px}`(L122)、thead 8 列(L584-596)、`buildRankRows()`(L234-261)、`showDock()`(L265-303)、`render()` `iframe_h=max(2400,900+n*33)`(L650)。
- **dock 失效根因**：iframe 高 = 全内容高(≈2682px@54 行) → 滚动发生在**父 Streamlit 页**、iframe 文档自身不滚 → `position:sticky` 永不触发 → hover 第 29 名时右侧大图在视口外。

### 缺陷 b（dock）修复方案 —— 「iframe 定高 + 左表内滚」（SPEC 推荐向，Builder 采纳并锁死参数）
根本机制：**让滚动回到 iframe 文档内部**。
1. `render()` iframe 高度**改定高**：`iframe_h = 1180`（固定；masthead≈150 + KPI≈150 + tier 区≈变 + rank 区定高 ≈ 视口友好）。公式提案：`iframe_h = _FIXED_H`，`_FIXED_H = 1180`（常量，非 `max(2400, 900+n*33)`）；n 增大不再拉高 iframe（表内滚吸收）。
2. `.rank-grid` 保持 `1fr 400px` + `align-items:start`。
3. 左表列外套滚动容器 `.rank-scroll{max-height:560px;overflow-y:auto}`（560 = rank 区可视高，容 ~16 行，其余内滚）；thead 用 `position:sticky;top:0` 钉在滚动容器内(表头随内滚常驻)。
4. `.dock` 去 `position:sticky` → **`position:static`**（iframe 已定高、dock 恒在视口内，无需 sticky）；dock 与左表 `align-items:start` 顶对齐。保留玻璃加强 rgba(.6)/blur16/白边.75/顶边 3px #1a1a1a、p20-22（IPO11 视觉不回归）。
5. hover 最后一行(第 54 名)：因表在 `.rank-scroll` 内滚、dock 在右恒可视 → hover 任意行(含内滚到底的末行)右图恒在视口。**这是缺陷 b 的验收核心**。

> 备选(未采纳)：整页 `position:fixed` dock —— srcdoc iframe 内 fixed 相对 iframe viewport，可行但 400px 宽度/left 需硬算易脆，且与 grid 语义打架。定高+内滚更稳、参数少。

### 缺陷 a（排序）修复方案 —— thead 点击排序
JS 侧新增排序状态机（**只重排 DOM 行，零碰数值计算**，NT5）：
1. **注入** `const TIER_ORDER = <json _TIER_ORDER>`（tier 排序依据；现 py 已有 `_TIER_ORDER`，L37）。
2. thead `<th>` 加 `data-key`（`rank`/`code`/`name`/`score`/`tier`/`sub_sector`/`list_date`/`d1_pct`）+ `cursor:pointer` + `role`。
3. 状态 `var sortKey='score', sortDir='desc'`（**默认序 = 评分降序，与现状一致**，初载不变）。
4. 点击某列 th：
   - 同列再点 → `sortDir` 翻转(asc↔desc)。
   - 换列 → `sortKey=新列`，`sortDir=` 该列**初始方向**：数值列(`score`/`d1_pct`/`rank`)=`desc`，文本列(`code`/`name`/`sub_sector`)=`asc`，日期列(`list_date`)=`desc`(新上市在前)，档位列(`tier`)=`asc`(按 TIER_ORDER 序，重点申购+ 在前)。
5. **pending 沉底铁律**（NT3）：无论何列何向，`pending===true` 行**恒排在 listed 行之后**（先按 pending 分组，组内再按 sortKey/sortDir）。pending 组内部按 score 降序稳定兜底。
6. **缺数兜底**：`d1_pct===null`(pending) / `list_date===''` 排序时视为最末（与 pending 沉底叠加，双保险）。tier 用 `TIER_ORDER.indexOf(tier)`，未知档 → 末位。
7. **`#` 列语义**：恒显**评分档原始 rank**（`r.rank`，pending=`—`），**排序不重编号**——即按别的列排序后，每行仍带其评分名次(身份稳定，可读「第 3 名评分的股按首日涨幅排到了第 1 行」)。
8. **排序指示器**：active 列 th 追加 `▲`(asc)/`▼`(desc)（mono，#1a1a1a）；非 active 列无指示器。
9. 重排后 `buildRankRows()` 复用现渲染(d1 ×100 / None `—` / pending `—` 全走现分支，NT3)；重排后**保持 hover→dock 联动**(重新绑 mouseenter)、默认选中仍 rank 1(即 score 最高 listed 股，非「当前首行」——身份锚定 DEFAULT_CODE 不变)。

### `__main__` 自测扩展（PS，禁回归现 5 case）
现自测 5 case(基础/all-pending/nan-close/last-NaN/mid-NaN)**全保留**，新增：
- Case 6：`_build_html` 产物含 `const TIER_ORDER =` 且值含 `重点申购+`。
- Case 7：thead 每列带 `data-key`（断 8 个 key 串均在 html）。
- Case 8：JS 含排序函数标识(如 `function sortRows(` / `sortKey`) 与 pending 沉底逻辑标识(如 `a.pending`/`pending ? 1`)。
- Case 9：默认序断言——ROWS JSON 首元素 = 评分最高股(现基础 case 应为 code "1234" score 8.5)，`DEFAULT_CODE` = "1234"（排序默认态不变）。

### 验收项提案（F3-T*）
| id | 断言 | 方法 |
|---|---|---|
| F3-T1 | iframe 定高：`render()` 高度为常量(不随 n 变)；`grep -n "max(2400" app/lib/ipo_stage.py` 零命中(旧公式已删)；新常量 `_FIXED_H`/固定值存在 | GR+PS |
| F3-T2 | dock 恒可视(缺陷 b 核心)：真机 54 行数据下，JS 对**末行**(第 54)`dispatchEvent(mouseenter)` → dock 头行名称/涨幅切为末行股，且 dock `getBoundingClientRect()` 顶/底均落在 iframe 可视高(0..iframe_h)内(未被推出视口) | JS(mouseenter 末行 + 断 dock rect + SS 旁证) |
| F3-T3 | 左表内滚：`.rank-scroll` computed `overflow-y:auto` + `max-height` 有限值；thead `position:sticky;top:0`(内滚时表头常驻)；`.dock` computed `position:static`(非 sticky) | JS(getComputedStyle) |
| F3-T4 | 排序可用(缺陷 a)：点「首日涨幅」th → 行按 d1_pct 降序(首行 = 最高首日 listed 股)；再点同列 → 升序(首行 = 最低首日 listed 股，但仍在 pending 之前)；active th 出现 `▼`/`▲` 指示器 | JS(click th + 断首行 code + 断指示器字符) |
| F3-T5 | 换列初始方向：点「名称」th → 文本 asc(首行名称字典序最小 listed)；点「评分」th → 数值 desc(首行 score 最高)；点「上市日期」th → 日期 desc(最新上市在前) | JS(逐列 click + 断首行) |
| F3-T6 | **pending 沉底铁律**：任一列任一向排序后，所有 `status≠listed` 行恒在 listed 行之后(DOM 顺序)；pending 行 `#` 列显 `—`、首日列显 `—` | JS(取全行 pending flag 序 + 断分组)+PS(rank null 现契约) |
| F3-T7 | `#` 列语义：按「首日涨幅」排序后，各行 `#` 仍显其评分档原始名次(非 1..N 重编号)——取排序后首行，其 `#` = 该股评分 rank 而非 "01" | JS(排序后断首行 # 文本 ≠ 必然 01) |
| F3-T8 | 数值零篡改(NT5)：排序前后同一 code 行的 评分/首日涨幅/tier 文本恒等(排序只重排不改值)；d1 仍 ×100 一次(取一已知 code 断 %值) | JS(排序前后 diff 同 code 单元格) |
| F3-T9 | NT3 逐条不回归：None/NaN 渲 `—`、末笔 NaN 路径丢弃、终点=首日收盘锚、零 `Math.random·genData`、零 MOCK/demo 字面量 | PS(现 5 self-test case 全 PASS)+GR |
| F3-T10 | 自测扩展：`python -m app.lib.ipo_stage`(经 `.venv/bin/python`，PYTHONPATH=app 或 `-m` 形式)退出码 0，新增 Case 6-9 全 PASS；`ipo_stage.py` py_compile clean；4_Strategy_Picks AppTest 无异常 | RM |

---

## §4 F4-home-dedup — 首页双标题去重

### 实现方案
- **删** home.py:45-49（`theme.page_header(i18n.t("home.title"), meta=...)` 整块）——旧标题「行情中枢」与 HUB masthead(L237-256)同题叠加。
- **保 fetch 时间**：HUB masthead 时间戳行(现 L252 `EOD {latest} HKT`)折入 fetch_utc——改为 `EOD {latest} · 取数 {fetch_utc[:16] if fetch_utc else '—'} HKT`（zh）/ `EOD {latest} · fetch {fetch_utc[:16]} HKT`（en，随 `_zh_hub`）。`latest`/`fetch_utc` 变量已在 L42-43 就绪，删 page_header 不影响其定义。
- **不动**：HUB masthead 主体(红条/标题/kicker/呼吸点)、`home.title` locale key（其他页可能引用——需 grep 确认；若仅 home 引用可留 key 不删，避免 GRD3 parity 噪音）。

### 验收项提案（F4-T*）
| id | 断言 | 方法 |
|---|---|---|
| F4-T1 | 单标题：首页 DOM 中「行情中枢」仅出现**一次**(HUB masthead)；旧 `cmsi-page-hero`/`page_header` 产物(class `ttl` 含「行情中枢」)消失 | JS(querySelectorAll 计数)+SS |
| F4-T2 | fetch 时间不丢：HUB masthead 时间戳行含 `latest` 快照日**且**含 `fetch_utc[:16]` 值(取数时间)；`fetch_utc` 为空时降级 `—`(不崩) | JS(断时间戳行文本含两段)+PS(fetch_utc=None 分支) |
| F4-T3 | 删净：`grep -n "page_header" app/home.py` 零命中；home.py py_compile clean；home AppTest 无异常、无 raw key | GR+RM |
| F4-T4 | 范围守卫：`sector_overview.masthead`(Healthcare/AI 板块小节头)未被触碰(NT6)；home.py diff 仅落在删 page_header + 改 masthead 时间戳行两处 | GR(diff 审) |

---

## §5 全局 / 现实约束回声（SPEC 全局约束）
1. PR-based 禁直推 main；最终 ship gate = George 眼验；commit 待授权（local-first ship gate）。
2. 改 lib(i18n/strategy_banner/ipo_stage/home)后验收**必重启 :8599**(`bash docs/harness/kline-reskin/init.sh`)——热进程缓存 lib(memory 实锤 `streamlit-cloud-reboot-after-lib-change`)。
3. wave-1(11/11)+wave-2(85/85)不回归；Evaluator 抽查回归面：BANR2/3/4/7/8/9、IPO10-14、GRD1-7。
4. F1-F4 文件互不相交（Workflow 4 路并行安全）：F1={i18n.py, strategy_banner.py, 4_Strategy_Picks.py(删 qp 块+banner 调用参)}、F2={locales/zh.py, en.py}、F3={ipo_stage.py}、F4={home.py}。**交叠点**：4_Strategy_Picks.py 被 F1(删 qp 块 L41-44 + banner lang 参)与 F2(无关，仅改 locale)共享——F2 不碰该文件，仅 F1 改；无真冲突。
5. 成本断路器：max 3 轮；连续 1 轮 0 新通过 → 停回报 George。

---

## §6 Builder 预判 Evaluator 会打的点（先应答，压缩博弈轮次）
- **P1「F1 折进 init_lang 会不会 rerun 环」**：不会。guard=`qp∈{zh,en} and qp≠session_state`；首次 sync 后 session_state==qp，后续 init_lang 调用(含同页多次、hub+page 双调)全 no-op。已在 F1-T8 AppTest 双态覆盖。
- **P2「lang_toggle_html 复刻 BANR2 是否逐字节」**：F1-T1/T2/T5 锁死 CSS token(border #d4c4b0 radius3 / mono 11/600/.08em / p5-12 / active #c8102e+#fff1e5)；banner 与页面共用同一 helper 产物(F1-T5 outerHTML 比对)确保零发散。
- **P3「i18n→theme import 是否成环」**：已实证 theme.py 不 import i18n（单向安全）；F1-T8 AppTest import 环即崩可兜。
- **P4「F3 dock 定高 1180 是否武断」**：1180 为提案初值，Evaluator/真机可调；**验收判据是 F3-T2(末行 hover dock 在视口内)行为，非高度魔数**——高度只要满足「表内滚 + dock 恒可视」即通过，具体值 Builder 真机微调。
- **P5「排序改了会不会碰 IPO12 数值」**：F3-T8 断排序前后同 code 数值恒等 + F3-T9 现 5 self-test 全绿双证；排序纯 DOM 重排(sortRows 只 reorder ROWS 副本→重渲)，`_build_html` 的 pts/d1 计算路径一字未动。
- **P6「# 列不重编号是否反直觉」**：提案锁「# = 评分档原始名次(身份锚)」，理由=让用户看「高评分股在别的维度排到哪」——若 George/Evaluator 要「# = 当前显示序」，改动仅 buildRankRows 一行(用 idx+1 替 r.rank)，留作可翻案项。

---

（完 · Builder 提案 v1；等待 Evaluator `contract-critique-evaluator.md` 反驳）
