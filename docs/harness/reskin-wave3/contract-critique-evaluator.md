# CONTRACT CRITIQUE — Evaluator 反驳 (wave-3 · 眼验反馈三连修)

> 角色：Evaluator-negotiator。本文 = 对 `contract-draft-builder.md` 逐项裁决 + 补漏，供冻结 `CONTRACT.md` 参照。
> 立场：我是之后真机验收 Builder 产物的人。此处磨硬判据 = 不给 Builder 留松测口子。
> 方法代号沿用 Builder §0：RM / JS(真机 computed-style·DOM) / GR / SS / PS(纯字符串探针)。
> **PS 纪律（wave-1 血的教训）**：PS 只证「串被 emit」，不证「行为对」。凡缺陷本质是**运行时行为**
> （排序生效 / dock 可视 / hover 联动 / 语言真切换）的项，**PS 一律不得作为唯一 PASS 依据**，
> 必升级 :8599 真机（重启后 computed-style / 实际点击后 DOM 顺序 / 滚动到位后 rect）。
> 参见 memory `echarts-candlestick-tooltip-params-trap`（静态探针假阳性害 Codex 误诊的前车）。

## 裁决统计

| 裁决 | 数 | 说明 |
|---|---|---|
| ACCEPT | 15 | 判据已测得到真行为，method 恰当，冻结 |
| HARDEN | 12 | 判据方向对但**方法可假阳性 / 魔数脆 / 覆盖不足**，给更硬替代判据 |
| REJECT | 1 | 判据物理上测不到真行为（选择器恒空）→ 换 method |
| MISSING | 7 | Builder 漏掉的边缘/交互，补新验收项 |

已核事实（真代码抽查，非采信 Builder 自述）：
- **19 调用点确证**：`grep -rn render_lang_toggle()` = 18 pages + home.py:39 = 19，**含隐页 `model_drill.py:28`**（Builder §1 枚举文字漏列 model_drill，但 F1-T7 的 grep 覆盖它，总数对）。
- **旧钮实锤**：i18n.py:258 `st.button(_LABELS[other], key="_lang_btn", use_container_width=True)`。**Streamlit 不把 `key` 渲成 DOM `key=` 属性**（渲成容器 class `.st-key-_lang_btn`）——F1-T3 的选择器 `button[key="_lang_btn"]` **恒选空**（见 REJECT）。
- **qp 交叉污染实锤**：`?ticker=` 被 8_SEC_Facts.py:67 / a5_ai_sec.py:72 / model_drill.py:43 读；6_Ticker_Drill.py:235 `st.query_params.clear()`。裸 `<a href="?lang=en">` 会**整串替换** query → 冲掉 `?ticker=`（见 F1-M1）。
- **F3 iframe 定高实锤**：`render()` L650 `iframe_h = max(2400, 900+len(picks)*33)`；`st.iframe(doc, height=iframe_h)`（真 API，ui.py:525-528 注 Streamlit 1.58+ 自识 HTML）。手算 5 档满内容高 ≈**1246px** > Builder 提案 1180（见 F3-T1）。
- **strategy.pitch 位置确证**：zh.py:20-25 / en.py:17-25；旧文案 zh 首句 `**这是什么** — 一个展示 **AI Agent 选股**实际表现的平台`。
- **page_header DOM 确证**：theme.py:1061-1062 产 `<div class="cmsi-page-hero"><h1 class="ttl">{title}<span class="bar"></span></h1>`；home.py:46-49 调用块 = 待删；HUB masthead home.py:243 = `<div ...>行情中枢</div>`（第二处同题）。`.cmsi-page-hero` CSS(theme.py:749-789) 被他页 page_header 复用 → **不得删 CSS，只删 home 调用**（Builder 正确）。

---

## §1 F1-toggle 裁决

### ACCEPT
- **F1-T1**（lang_toggle_html 返回串含双锚点 + CSS token）：ACCEPT。测的是**纯 helper 的字符串契约**，PS 恰当（真渲染归 T3/T4/T5）。
- **F1-T2**（active/inactive 配色随 lang）：ACCEPT。纯 helper 分支逻辑，PS 恰当。冻结时补一条：`get_lang()` 在无 session_state 时走 `DEFAULT_LANG="zh"` → 首屏「中」active，别让 helper 崩在无 state 态。
- **F1-T4**（真机点击切语言）：ACCEPT。真机 click + 断标题字变。**补执行细节**：锚点点击 = 整页 reload，断言前须等重连（`wait` 至新标题出现或 networkidle），否则读到旧帧假阴性。
- **F1-T6**（qp 单源仅 i18n.py）：ACCEPT。GR 恰当。附加已含「4_Strategy_Picks.py:41-44 局部块删净」——冻结时钉：`grep -n _qp_lang app/pages/4_Strategy_Picks.py` 零命中。
- **F1-T7**（19 调用点零改 + 无必填参）：ACCEPT。GR 覆盖 model_drill 隐页。PASS = `grep -rn "render_lang_toggle()" app/pages app/home.py` = 19 且全裸调用 + `render_lang_toggle` 签名无必填参。

### HARDEN
- **F1-T3**（真机描边锚点存在 + 旧钮消失）：**HARDEN**。正向断言（`a[href="?lang=en"]` 存在于 3 页）保留。**旧钮消失子句 `button[key="_lang_btn"]` 物理测不到**（见 REJECT）→ 换：
  1. 正向 JS：取 `8_SEC_Facts / e2_etf_heatmap / 2_Healthcare` 三页真机，`document.querySelector('a[href="?lang=en"]')` 非空；
  2. 旧钮清零走 **GR 源码**：`grep -n "st.button" app/lib/i18n.py` = 0 **且** `grep -rn '_lang_btn' app/` = 0；
  3. DOM 兜底：`document.querySelectorAll('.st-key-_lang_btn').length === 0`（正确选择器，非 `button[key=...]`）。
  PASS = 三页锚点均在 + i18n.py 零 st.button + 全站零 `_lang_btn`。
- **F1-T5**（banner toggle == 页 toggle 同 helper 产物）：**HARDEN**。整容器 outerHTML 逐字节相等**过脆**——banner 外层可能多套 flex/gap 包裹使容器串不同，却不代表控件发散。换：比对**两处 `<a>` 段**的 `getAttribute('href')` + `getComputedStyle`(font-size/font-weight/letter-spacing/padding/background/color) 逐字段相等；容器只断 computed `border`(1px #d4c4b0 折算 rgb) + `border-radius:3px`。PASS = 两 `<a>`(中/EN 各)计算样式全等 + 容器边框/圆角达标。
- **F1-T8**（py_compile + AppTest 4 页 zh/en）：**HARDEN**。中心化 qp-sync 进 `init_lang()` 后，`init_lang` **每页多次被调**（实测 5_Valuation_Scanner.py 显式调 2 次 :37/:87，且 render_lang_toggle 内部 i18n.py:253 再调一次）+ hub(streamlit_app.py:36) 先调。新 `st.rerun()` 若 guard 不严 = rerun 环。4 页样本须换成**能触发这些路径的页**：
  - 必含 **5_Valuation_Scanner**（init_lang 双调）+ **model_drill 或 8_SEC_Facts**（qp 隐页）+ home + 4_Strategy_Picks；
  - AppTest 断言：zh/en 两态各渲一遍**跑完**（无 raw key、无 TypeError、无 import 环）**且未触 Streamlit rerun 上限**（rerun 环即在此暴露）。

### REJECT
- **F1-T3 子句「无 `button[key="_lang_btn"]`」**：**REJECT（method 恒真）**。Streamlit 不把 widget `key` 渲成 HTML `key=` 属性，故 `document.querySelector('button[key="_lang_btn"]')` **无论旧钮在不在都返 null** → 该断言恒 PASS，**检测不到旧钮残留回归**（假阴性）。裁决：删此子句，旧钮清零改由 F1-T3 HARDEN 的**源码 GR**（i18n.py 零 st.button）承担；若坚持 DOM，唯一有效选择器是 `.st-key-_lang_btn`。

### MISSING（Builder 全漏）
- **F1-M1 [HIGH] — 裸 `?lang=` 锚点冲掉 sibling `?ticker=`**：新 helper 产 `<a href="?lang=en">`（裸 query），点击**整串替换** URL query。在读 `?ticker=` 的页（8_SEC_Facts:67 / a5_ai_sec:72 / model_drill:43），toggle 语言 = **丢掉 ticker → 页面重置到默认标的**。旧 `st.button+st.rerun` 不动 URL、不丢 ticker → 这是**站级行为回归**（策略页无他 qp 才侥幸没暴）。Builder 契约零处理。
  验收项（真机）：`8_SEC_Facts?ticker=<已知票>` → 点 lang 段 → 断言页面仍锁该票（url 含 `ticker=<票>&lang=en` 或页面 ticker 未变）。
  PASS 二选一，Builder 定：(a) helper **保留现有 qp**（`?ticker=NVDA&lang=en`，读 `st.query_params` 拼回）——推荐；(b) 契约**显式声明** toggle 会丢 ticker 且 George 接受（书面）。默认 (a)。
- **F1-M2 [MED] — 站级 reload 抹 widget 状态**：19 页从 `st.button+st.rerun`（保 session_state/控件态）改为 anchor+整页 reload（新 session，除 `?lang=` 恢复外 session_state 全清）= **切语言即丢筛选/下拉/选择态**（e2_etf_heatmap 筛选、各页 selectbox）。George 已在策略页接受 BANR2 此机制，但**站级铺开须显式声明范围**，否则后续会被当回归打回。
  验收项：契约加一条明文「lang toggle = 整页 reload，非 lang 的 widget 态随之重置（沿 BANR2 机制，George 接受）」；真机旁证 1 例（e2 设一筛选 → 切 lang → 记录态重置 → 确认属接受）。附：6_Ticker_Drill:235 `st.query_params.clear()` 只清 URL 不清活 session 的 session_state，故**活 session 内**切页 lang 靠 session_state 存活；仅「clear 后硬 reload」才回默认（低危，M2 声明里带一句即可）。

**F1 小计**：ACCEPT 5 · HARDEN 3 · REJECT 1 · MISSING 2

---

## §2 F2-pitch 裁决

### ACCEPT
- **F2-T2**（粗体锚点 → 墨色 `<b>` + `<br><br>`）：ACCEPT。真机断 BANR4 包装器对新文案的产物（`<b style="color:#1a1a1a;">` + `<br><br>`），JS on live DOM，恰当。
- **F2-T4**（BANR4 dek 样式不回归 + 包装器 4 行未改）：ACCEPT。computed-style(14px/1.65/#4a4a4a/max-880) + GR diff 4_Strategy_Picks.py:146-149 逐字。**冻结强调**：F1 与 F2 都碰 4_Strategy_Picks.py（F1 删 qp 块+改 banner lang 参，F2 不碰此文件）——须确保 F1 的改动**未误伤** 146-149 包装器（GR diff 锁死该 4 行字节不变）。

### HARDEN
- **F2-T1**（新短语在 / 旧文案消失）：**HARDEN**。两处收紧：
  1. **旧串 GR 用无 `**` 子串**：旧文案带 markdown 星号（`**这是什么** — …`），grep 整句易漏 → 钉 `grep -n "这是什么" app/lib/locales/zh.py` = 0（去掉星号的稳定锚）。
  2. **George 要求「逐字执行」→ 必字节级对定稿**，非「含关键短语」。加断言：zh.py `strategy.pitch` 值 == SPEC F2 定稿两段**逐字**（含全角顿号/括号「（Quantamental）」/破折号「—」/`**…**` 三锚 `方法论`·`持仓自入选之日起登记在册`·`自选股日起的真实累计收益 vs 基准`/段间 `\n\n`）。
  PASS = 旧串零命中 + zh.pitch 字符级等于定稿（除 `**`/`\n\n` 标记外无一字差）。
- **F2-T3**（en 镜像粗体 + 语义对齐）：**HARDEN**。「≥2 处 `**`」太松，SPEC 要求**镜像 3 个粗体锚**。收紧：en `strategy.pitch` 恰含 **3 个** `**…**` 且语义映射 zh 三锚（Methodology / logged … from the day of selection / real cumulative return vs benchmark since selection）+ 段间 `\n\n` 存在。PASS = en 三粗体锚齐 + `\n\n` 在 + zh/en 两态 `t('strategy.pitch')` 均 ≠ key 自身（非 raw key）。

### MISSING
- **F2-M1 [LOW] — en 态 dek live DOM 未验**：F2-T2 只断**zh 态**策略页 dek。en 态经同一 BANR4 包装器渲染的 `<b>`/`<br><br>` **无真机断言**。补：en 态 :8599 策略页 dek `<p>` innerHTML 含 3 个 `<b style="color:#1a1a1a;">` + ≥1 `<br><br>`（镜像 T2 于 en）。PASS = en dek 三墨色粗体 + 段隔在。

**F2 小计**：ACCEPT 2 · HARDEN 2 · MISSING 1

---

## §3 F3-ipo-rank 裁决（重头）

### ACCEPT
- **F3-T4**（点首日涨幅 desc→asc + 指示器）：ACCEPT。真机 click th + 断首行 code + 断 `▼`/`▲`。**补交叉**：desc 与 asc 两结果均须 pending 沉底（并入 T6 断言，勿只测 listed 首行）。
- **F3-T5**（换列初始方向 name asc / score desc / date desc）：ACCEPT。覆盖初始方向状态机三列。**tier 列初始方向另立**（见 F3-M4）。
- **F3-T7**（# 列 = 评分档原始名次，非 1..N 重编号）：ACCEPT。取排序后确实位移的行断 `#` ≠ `01`，恰当。
- **F3-T8**（排序前后同 code 数值恒等 + d1 ×100 一次）：ACCEPT。强反篡改门，NT5 核心。真机 diff 同 code 单元格。
- **F3-T9**（NT3 逐条不回归 + 现 5 self-test）：ACCEPT。PS(5 case)+GR，与 T10 联动。

### HARDEN
- **F3-T1 [HIGH]**（iframe 定高，max(2400 删）：**HARDEN**。`_FIXED_H=1180` 是**脆魔数**——手算满内容（body pad 24 + masthead≈113 + KPI≈152 + tier 5 档≈265 + rank-sec 32 + rank-scroll 560 + footer 68 + pad 32）≈**1246px** > 1180 → **footer 及 rank 区底被截 / iframe body 自身出第二滚动条**（双滚动条）。tier 档数可变（2~5 档）使高度浮动，定值必顾此失彼。判据必须**锁行为不锁数字**：
  1. GR：`grep -n "max(2400" app/lib/ipo_stage.py` = 0 + 常量存在（保留）；
  2. **反溢出（新，核心）**：真机 iframe 文档内 `document.documentElement.scrollHeight <= <iframe height> + 2`——**body 不溢出 iframe，唯一滚动来自 `.rank-scroll`**（无 iframe 级第二滚动条）；
  3. **footer 全见**：`.footer` `getBoundingClientRect().bottom <= <iframe height>`。
  PASS = 三者同时。高度取值 Builder 真机定（可能须 >1180 或改为「固定前段 + rank-scroll + footer」测量式），但**不满足 2+3 即 FAIL**，不接受「1180 够用」的口头。
- **F3-T2 [HIGH]**（末行 hover → dock 可视）：**HARDEN**。`dispatchEvent(mouseenter)` 是**合成事件捷径**——不管末行是否真滚得到、是否可见，handler 都触发 → 可**假阳性**（正是缺陷 b 要防的「滚不到/看不到」被绕过；wave-1 静态探针同型陷阱）。且 dock 现 `position:static` 恒不动 →「dock 在视口」近乎恒真，**非载荷断言**。重写为真机三步：
  1. 把 `.rank-scroll` 滚到底（`el.scrollTop = el.scrollHeight`），断第 54 行 rect 落在滚动容器可视带内（真到得了末行）；
  2. hover 末行（合成或真 hover 皆可，但须在步骤 1 之后）；
  3. **载荷断言**：`#dock-content` 文本切为末行股名+涨幅（dock 内容真联动）**且** dock `getBoundingClientRect()` 顶/底 ∈ [0, iframe_h]（未被推出/截断）。
  PASS = dock 内容 == 末行股 + dock rect 全在 iframe 视口 + 步骤 1 证明末行可达。
- **F3-T3 [HIGH]**（rank-scroll overflow + thead sticky + dock static）：**HARDEN**。computed `position:sticky` **必要不充分**（祖先 overflow/transform 会静默破坏 sticky）。补真滚证明：将 `.rank-scroll` 滚到底后，`thead` `getBoundingClientRect().top` ≈ 滚动容器 `top`（表头钉住没随内容滚走）。PASS = computed(`.rank-scroll` overflow-y:auto + max-height 有限 / thead position:sticky top:0 / `.dock` position:static) **且** 滚到底后 `|thead.top − scrollContainer.top| < 2px`。
- **F3-T6 [HIGH]**（pending 沉底铁律）：**HARDEN**。「任一列任一向」须**列举执行**，不能一句带过（升/降两向都要断，SPEC 明令）。判据展开为四断言：(i) score desc、(ii) score asc、(iii) name asc、(iv) list_date desc——**每种**下「全部 status≠listed 行的 DOM index > 全部 listed 行的 DOM index」。并补**混排边缘**：**listed 但 list_date=='' 的行**在 date 排序下须留在 **listed 组末尾（仍在 pending 之上）**，不得与 pending 一起沉底（pending 沉底优先级 > 空日期沉底）。PASS = 四向 pending 全沉 + listed-空日期行位于 listed 组内末位。
- **F3-T10**（self-test exit 0 + 新 Case 6-9 + py_compile + AppTest）：**HARDEN**。Case 6-9 全是 `_build_html` 产物上的 **PS 字符串探针**（"含 `function sortRows(`"/"data-key 在"/"`a.pending` 在"）——**只证串被 emit，不证排序真的排、pending 真的沉、hover 真的联动**（wave-1 假阳性同型）。裁决：Case 6-9 作**廉价静态门保留**，但契约须明文：**F3 的排序/沉底/联动/dock 可视 PASS 唯一依据是真机 T4/T5/T6/F3-M1**，PS Case 不得替代。另补一条真机初始态回归：**未点击前** tbody 行序 == 评分降序，且**与 wave-2 现状行序字节一致**（thead 新增 data-key/cursor/指示器位 = 允许的新 chrome，但**行数据序不得变**）。

### MISSING（Builder 漏，含 task 点名项）
- **F3-M1 [HIGH] — 排序后 hover→dock 联动无验收项**（task 明确点名）：现 `buildRankRows` 用闭包 `tr.addEventListener('mouseenter', ()=>showDock(r.code))`，且 `showDock` 有 `if(code===activeCode) return` 早退。排序若**重排 <tr> 而闭包捕获旧 `r`** 或 **重渲后 activeCode 未复位** → hover 第 k 行显示**错/旧**股。Builder 零验收项。补真机：sort 首日涨幅 desc → hover 新首行 → `#dock-content` 股名 == 该行名称单元格；再 hover 新的末位 listed 行 → dock 正确切换。PASS = ≥2 个排序后不同行，dock 名/涨幅逐一命中所 hover 行的单元格（无 stale）。
- **F3-M3 [MED] — `.rank-scroll` 滚动条在 FT-salmon 纸皮下无约束**（task 点名）：新内滚容器在 `#fff1e5` 奶纸面引入可见滚动条，默认 OS 滚动条（深灰/系统蓝）在纸皮上突兀。契约须裁：(a) `.rank-scroll::-webkit-scrollbar` 定制（细、thumb=INK_3 半透、track 透明）与纸皮调和；或 (b) 显式接受默认滚动条。PASS = 选 (a) 则 computed 断 scrollbar 宽≤10px + thumb 色属纸皮色板；选 (b) 则契约书面接受 + SS 旁证 George 认。
- **F3-M4 [MED] — tier 列排序初始方向 + 未知档末位**：Builder rule 4/6 定义「点申购档 th → 按 TIER_ORDER asc（重点申购+ 在前），未知档→末位」，但 F3-T5 只测 name/score/date，**tier 列无验收**。补真机：点「申购档」th → 行按 `TIER_ORDER`（重点申购+ → 重点申购 → 推荐申购 → 谨慎申购 → 不申购）排、未知 tier 沉 listed 组末、pending 仍全沉。PASS = tier 序 == TIER_ORDER + 未知档末 + pending 沉底。

**F3 小计**：ACCEPT 5 · HARDEN 5 · MISSING 3

---

## §4 F4-home-dedup 裁决

### ACCEPT
- **F4-T1**（单标题 / 旧 cmsi-page-hero 消失）：ACCEPT。querySelectorAll 计数 + `.cmsi-page-hero` 零。**小收紧**：断言限定主内容区（`section.main` 或 `[data-testid="stMain"]`）内「行情中枢」出现 **== 1** 且 `document.querySelectorAll('.cmsi-page-hero').length === 0`（home 页）。
- **F4-T2**（fetch 时间不丢）：ACCEPT。masthead 时间戳行含 `latest` + `fetch_utc[:16]` 两段，且 `fetch_utc=None` 降级 `—` 分支（PS 覆盖 None 分支恰当）。冻结钉：改后 home.py:252 那行 zh/en 双语（`_zh_hub` 分支）都带 fetch 段。
- **F4-T3**（page_header grep 零 + py_compile + AppTest）：ACCEPT。GR+RM 恰当。

### HARDEN
- **F4-T4**（范围守卫 + diff 仅两处）：**HARDEN**。补 task 点名的「删除后顶部无空白遗留」：page_header 原产 `<div class="cmsi-page-hero">`，删后须证**无空容器/无双顶边距**残留于 HUB masthead 之上。加断言：home 主内容区**首个可见块 == HUB masthead**（其上无空 `stMarkdown`/无 `.cmsi-page-hero` 空壳）；SS 旁证顶部无空白带。范围守卫保留：`sector_overview.masthead` 未触碰（NT6）+ home.py diff 仅落「删 45-49 + 改 masthead 时间戳行」两处（GR diff 审）。PASS = 首块=masthead + 无空壳 + diff 两处。

### MISSING
- **F4-M1 [LOW] — home.title locale key 孤儿 / GRD3 parity**：删 page_header 后 `home.title` 可能零 t() 引用。补：`grep -rn "home.title" app/` 若仅剩 locale 定义（零调用），则该 key **zh/en 同去或同留**（不得单边留 → 破 GRD3 parity）。PASS = home.title 要么两 locale 都留、要么都删；不出现单语言孤儿。

**F4 小计**：ACCEPT 3 · HARDEN 1 · MISSING 1

---

## §5 回归面抽查清单（Evaluator 强制电池，NT2/NT3 具体化到数字级）

Builder §0 NT2/NT3 泛列「逐条不回归」。以下 **8 条数字级**是我 round-1 真机必抽（挑跨 F1-F4 改动面最可能溅到的）：

| # | 抽查项 | 判据（数字级）| 方法 | 为什么这条（溅射源）|
|---|---|---|---|---|
| R-1 | **BANR4 dek + 包装器** | 4_Strategy_Picks.py:146-149 `re.sub **→<b> + \n\n→<br><br>` 逐字未改；dek `<p>` computed 14px/1.65/#4a4a4a/max-880 | GR diff+JS | F1 与 F2 都碰策略页/pitch，最易误伤 |
| R-2 | **BANR2 banner toggle** | 描边分段 active bg `#c8102e` + 字 `#fff1e5`；容器 border 1px `#d4c4b0` radius3；段 mono 11/600/.08em p5-12 | JS computed | F1 把 seg() 抽成共享 helper，重构即回归风险最高 |
| R-3 | **IPO9 排行表结构** | 8 列 thead（#/代码/名称/评分/申购档/子板块/上市日期/首日涨幅）齐；rank `padStart(2,'0')`；pending rank `—` | JS+PS | F3 给 th 加 data-key/指示器，勿丢列/勿改 padStart |
| R-4 | **IPO12 盘中锚（CRITICAL）** | 终点 = day1_ret×100（Case5 endpoint 100.0）；末笔 NaN → 整路径丢弃（Case4 无 pts）；零 Math.random/genData | PS(5case)+GR | F3 动排序**禁碰数值计算路径** L440-470 |
| R-5 | **IPO4 KPI live** | 最高 `+384.0%` / 最差 `-56.9%`（合成 case）实算；零硬编 384/56.9/2.69 字面量 | PS+GR | F3 self-test 须保 |
| R-6 | **IPO7 五档色** | 重点申购+ `#a00d25` / 重点申购 `#c8102e` / 推荐申购 `#0d7680` / 谨慎申购 `#a06d1f` / 不申购 `#6b6560`；注入 JS 的 TIER_COLORS 与 py `_TIER_COLORS`(L30-36) 一致 | JS+PS | F3 把 TIER_ORDER/COLORS 注入 JS，须与 py 单源一致 |
| R-7 | **BANR7 curve 卡** | α chip 符号染色不回退（≥0 青/青底、<0 红/红底）；大号累计 mono 32px tabular | JS computed | F1 改策略页顶（banner 调用），抽查未溅到卡 |
| R-8 | **GRD7 真机冒烟** | init.sh 重启 :8599 → home / Strategy / Healthcare / AI overview HTTP 200；echarts 面（treemap `#m` + hero `#eq`）连刷 3× 每次出图（0 宽竞态回归探针）| RM | 改 4 个 lib（i18n/banner/ipo_stage/home）必重启，热进程缓存 |

> memory `streamlit-cloud-reboot-after-lib-change` 实锤：改 lib 签名/locale key 后**必 Reboot**（本地 kill+relaunch :8599），rerun 清不掉热进程缓存 → 否则新 page 撞旧 lib 崩（raw key/TypeError）。R-8 是所有 lib 改动的前置门。

---

## §6 全局 HARDEN（GBL）

- **GBL-1 [HIGH] — AppTest 覆盖面 4 页 → 全页 smoke**：F1 改 `render_lang_toggle`+`init_lang` = **每一页都跑的共享路径**；只测 4 页（F1-T8/GRD4）网眼太大。冻结须加：AppTest **遍历全部 19 页 + hub**（zh/en 两态）做无崩/无 raw key/无 rerun 环 smoke（可脚本化 `for p in pages: AppTest(p).run()`），至少一次全量。这是 F1 站级改动的**唯一足量回归网**。PASS = 19 页×2 态全 run 完，零 raw key、零 TypeError、零 rerun 上限。
- **GBL-2 [记录] — 验收顺序**：GRD1-4 静态电池 → R-8 重启冒烟 → 逐区块真机 JS → 最后 SS。Builder 三路并行（F1={i18n/banner/4_Strategy}, F2={locales}, F3={ipo_stage}, F4={home}）文件不相交，但 **4_Strategy_Picks.py 被 F1 独占改**（F2 只改 locale 不碰它）——冻结时确认无二方同写该文件（R-1 diff 审兜底）。

---

## §7 冻结前给 Builder 的最重要 5 条（改这些，round-1 才有的过）

1. **F1-M1（HIGH）**：裸 `<a href="?lang=en">` 冲掉 sibling `?ticker=` → SEC/ai_sec/model_drill 切语言丢标的。helper 须保留现有 qp（`?ticker=X&lang=en`）或书面声明接受。**这是站级行为回归，非皮肤问题。**
2. **F3-T1+F3-M2（HIGH）**：定高 1180 手算会截 footer（满内容≈1246px）→ 双滚动条。判据锁**行为**（iframe body 不溢出 + footer bottom≤iframe_h），不锁魔数；高度真机测量式定。
3. **F3-M1（HIGH）**：排序后 hover→dock 联动**零验收项**（task 点名）。补真机：排序后 hover 第 k 行 → dock 显示第 k 行股（无 stale）。
4. **F3-T2/T3（HIGH）**：`dispatchEvent` + 纯 computed-style 假阳性风险（wave-1 陷阱）。dock 可视与 thead sticky 必须**真滚到底**后再断 rect/位置，不接受合成事件捷径。
5. **F1-T3/REJECT**：`button[key="_lang_btn"]` 选择器恒选空、测不到旧钮回归。旧钮清零改由**源码 GR**（i18n.py 零 st.button + 全站零 `_lang_btn`）证明。

（完 · Evaluator 反驳 v1；待 Builder 回应或 Planner 冻结 CONTRACT.md）
