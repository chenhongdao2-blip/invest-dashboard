# CONTRACT RESPONSE — Builder round-2 回应 (wave-3)

> 对 `contract-critique-evaluator.md`(ACCEPT 15 / HARDEN 12 / REJECT 1 / MISSING 7) 逐条表态。
> 结论词：**ACCEPT**(采纳进方案) / **COUNTER**(给理由 + 替代判据) / **ACCEPT+**(采纳判据并加固机制)。
> 已核 Evaluator 关键事实(非采信自述)：`st.query_params.get("ticker")` 实读于 8_SEC_Facts:67 / a5_ai_sec:72 / model_drill:43；
> 6_Ticker_Drill:235 `st.query_params.clear()` 仅在「返回列表」按钮回调(与 lang toggle 无关)；Streamlit widget `key` 渲成 `.st-key-<key>` class 非 DOM `key=` 属性。
> **总表态：REJECT 1 全收 · HARDEN 12 全收(2 项加固机制) · MISSING 7 全收。DISPUTED = 1（GBL-1 范围，见 §7）。**

---

## §1 F1-toggle 回应

**ACCEPT（Evaluator ACCEPT 项，无异议冻结）**：F1-T1 / F1-T2（补：`get_lang()` 无 state 走 `DEFAULT_LANG="zh"`，helper 不崩于无 state）/ F1-T4（补：点击=整页 reload，断言前 `wait` 至新标题出现/networkidle）/ F1-T6（钉 `grep -n _qp_lang app/pages/4_Strategy_Picks.py`=0）/ F1-T7。

**HARDEN 回应**：
- **F1-T3 → ACCEPT**：删「`button[key="_lang_btn"]`」子句（承认恒空、假阴性）。旧钮清零改三判据：①三页真机 `a[href^="?"][href*="lang=en"]` 非空；②GR 源码 `grep -n "st.button" app/lib/i18n.py`=0 **且** `grep -rn "_lang_btn" app/`=0（排 .omc/）；③DOM 兜底 `document.querySelectorAll('.st-key-_lang_btn').length===0`。
- **F1-T5 → ACCEPT**：弃 outerHTML 字节相等（承认过脆）。改比对两处 `<a>` 段的 `getAttribute('href')`(经 M1 后含 sibling qp，比对 lang 段一致性) + `getComputedStyle`(font-size/weight/letter-spacing/padding/background/color) 逐字段等；容器只断 computed `border`(1px rgb(212,196,176)) + `border-radius:3px`。
- **F1-T8 → ACCEPT**：4 页样本换成触发全路径的页：**5_Valuation_Scanner**(init_lang 双调 :37/:87)+**8_SEC_Facts**(qp 隐页)+home+4_Strategy_Picks；断 zh/en 各跑完无 raw key/TypeError/import 环 **且未触 rerun 上限**（rerun 环即在此暴露）。全量网移交 GBL-1。

**REJECT 回应**：
- **F1-T3 子句「无 button[key=]」→ ACCEPT REJECT**：Streamlit `key` 不渲 DOM `key=` 属性，选择器恒返 null=假阴性。已并入上条 T3 三判据（源码 GR 承担旧钮清零）。

**MISSING 回应**：
- **F1-M1 [HIGH，站级回归] → ACCEPT，采方案(a)**。**这是我 round-1 的实漏，Evaluator 对。** 实现细节写死：
  - `lang_toggle_html()` 渲染时读**当前** `st.query_params`，把现有参数并进 href、仅覆盖 `lang`：
    ```python
    from urllib.parse import urlencode
    def _cur_qp() -> dict:
        try:
            return {k: v for k, v in st.query_params.to_dict().items()}
        except Exception:
            return {}          # 裸 import/无 run-context → 空(PS 测走此支)
    def _lang_href(code_lang: str) -> str:
        return "?" + urlencode({**_cur_qp(), "lang": code_lang})
    ```
    → SEC 页 `?ticker=NVDA` 点 EN 段 = `?ticker=NVDA&lang=en`（ticker 保活）；无 sibling 参数页 = `?lang=en`（退化，与现 banner 一致）。
  - **6_Ticker_Drill 行为**：其 `?ticker=` 深链读在 :211-216；lang toggle 保 ticker → 切语言**不掉出详情模式**（stay in drill）。返回列表的 `query_params.clear()`(:235) 是独立按钮，与 toggle 无交叉，行为不变。
  - **helper 不再是纯函数**（依赖 st.query_params 运行时）：F1-T1/T2 PS 测在无 run-context 下 `_cur_qp()` 返空 → href=`?lang=<x>`，段结构/配色断言仍成立（sibling 保活归 F1-M1 真机）。
  - **验收(真机)**：`8_SEC_Facts?ticker=<已知票>` → 点 lang 段 → URL 含 `ticker=<票>&lang=en` **且**页面仍锁该票（`st.query_params.get("ticker")` 未丢、详情不重置）。补一路 `model_drill?ticker=<票>` 同断。PASS = 两页切语言后 ticker 保活。
- **F1-M2 [MED] → ACCEPT（书面声明）**：契约加明文——「lang toggle = `<a target=_self>` 整页 reload（沿 BANR2 机制，George 已接受）；非 lang 的 widget 态(筛选/selectbox)随 reload 重置，属**已接受行为非回归**」。真机旁证 1 例(e2_etf_heatmap 设一筛选→切 lang→态重置→归入接受)。附 M2 尾注：活 session 内跨页切换靠 session_state 存活，仅「reload」才回默认(低危，声明带一句)。

---

## §2 F2-pitch 回应

**ACCEPT**：F2-T2 / F2-T4（补强：F1 改 4_Strategy_Picks.py 时 GR diff 锁死 146-149 包装器 4 行字节不变，确保未误伤）。

**HARDEN 回应**：
- **F2-T1 → ACCEPT，并 pin 定稿 canonical 串**（消歧：SPEC F2 的 `>` 是文档 blockquote 排版，**不入** locale 值）。zh.py `strategy.pitch` 目标值逐字 =（两段，`\n\n` 分隔）：
  > 段1：`**方法论** — 本页跟踪一套量化基本面（Quantamental）选股体系的实盘表现：以临床试验读出、FDA 审批进度、财报披露与公司治理事件为输入，按多维度评分筛选入池。**持仓自入选之日起登记在册**，业绩以原始记录为准复盘，盈亏均客观呈现。`
  > 段2：`下方三个策略展示**自选股日起的真实累计收益 vs 基准**（非回测美化）。`
  - 判据①旧串 GR：`grep -n "这是什么" app/lib/locales/zh.py`=0（去星号稳定锚）。
  - 判据②zh.pitch **字符级等于上方 canonical**（含全角顿号「、」/括号「（Quantamental）」/破折号「 — 」/三 `**…**` 锚/段间 `\n\n`），除 markdown 标记外零字差。PS 断字符串相等。
- **F2-T3 → ACCEPT**：en 收紧为**恰 3 个** `**…**` 锚 + `\n\n`。en canonical 提案（镜像三锚，financially professional）：
  > `**Methodology** — this page tracks the live performance of a quantamental stock-selection system: it ingests clinical-trial readouts, FDA review milestones, earnings disclosures and governance events, then scores and screens names into the pool across multiple dimensions. **Every holding is logged on the record from the day it is selected**, and performance is reviewed against that original record — wins and losses shown alike.\n\nThe three strategies below show **real cumulative return vs benchmark since selection** (not a polished backtest).`
  - PASS = en 恰 3 `**` 锚(Methodology / logged … from the day it is selected / real cumulative return vs benchmark since selection) + `\n\n` 在 + zh/en `t('strategy.pitch')` 均 ≠ key 自身。

**MISSING 回应**：
- **F2-M1 [LOW] → ACCEPT**：补 en 态 :8599 策略页 dek `<p>` innerHTML 含 **3 个** `<b style="color:#1a1a1a;">` + ≥1 `<br><br>`（镜像 T2 于 en）。PASS = en dek 三墨色粗体 + 段隔在。

---

## §3 F3-ipo-rank 回应（重头）

**ACCEPT**：F3-T4（补：desc/asc 两向均并 pending 沉底断言→并入 T6）/ F3-T5（tier 列初始方向另立→M4）/ F3-T7 / F3-T8 / F3-T9。

**HARDEN 回应**：
- **F3-T1 [HIGH] → ACCEPT 判据 + COUNTER 机制（加固，去魔数脆性）**。承认定值 1180 会截 footer（满内容≈1246）。**但我不采「继续调大魔数」——改用结构性零溢出布局**，让 Evaluator 的反溢出判据**由构造保证**：
  - iframe body：`height:100vh; display:flex; flex-direction:column; overflow:hidden`。
  - masthead / KPI / tier 区 / 节标 / **footer** = `flex:none`（自然高，footer 恒为 body 末子、恒可视）。
  - `.rank-grid`：`flex:1; min-height:0`（吸收剩余高，tier 档数 2~5 变动由此消化）。
  - `.rank-scroll`(左表)：`overflow-y:auto`（**唯一滚动源**，随 flex-1 区自适应高）；`.dock`：`position:static; align-self:start`。
  - iframe 高度 = 固定 `_FIXED_H`（提案初值 **1120**，真机微调）——因 `overflow:hidden`+flex 布局，body 结构上不溢出、footer 结构上可视，**判据 2/3 不依赖魔数精确**（任何 ≥~950 的值都满足，仅影响 rank 区可视高度）。
  - **判据（同 Evaluator，全收）**：①GR `grep -n "max(2400" app/lib/ipo_stage.py`=0 + 常量存在；②真机 `document.documentElement.scrollHeight <= _FIXED_H + 2`（body 不溢出、无 iframe 级第二滚动条）；③真机 `.footer` `getBoundingClientRect().bottom <= _FIXED_H`。PASS = 三者同时；不满足 2+3 即 FAIL（我不做「1180 够用」口头担保）。
  - 注：Evaluator §7.2 引「F3-M2」但 §3 未定义 M2 —— 该 double-scrollbar 隐患即本条 T1 判据②所覆盖，视为编号笔误，无独立缺口。
- **F3-T2 [HIGH] → ACCEPT（弃合成事件捷径）**。真机三步：①`.rank-scroll` 滚到底(`el.scrollTop=el.scrollHeight`)，断第 54 行 `getBoundingClientRect()` 落在滚动容器可视带内(真到得了末行)；②滚到底后 hover 末行；③**载荷断言**：`#dock-content` 文本切为末行股名+涨幅 **且** dock rect 顶/底 ∈ [0, _FIXED_H]。PASS = dock 内容==末行股 + dock rect 全在视口 + 步骤①证末行可达。（dock 现 `position:static`——由 flex 布局恒在右侧可视，不再靠 sticky。）
- **F3-T3 [HIGH] → ACCEPT**：computed 断(`.rank-scroll` overflow-y:auto + max/flex 有限高 / thead position:sticky top:0 / `.dock` position:static) **且**滚到底后 `|thead.getBoundingClientRect().top − scrollContainer.top| < 2px`（表头真钉住）。
- **F3-T6 [HIGH] → ACCEPT（四向列举 + 空日期边缘）**：四断言 (i)score desc (ii)score asc (iii)name asc (iv)list_date desc——每种下「所有 status≠listed 行 DOM index > 所有 listed 行 DOM index」。补边缘：**listed 但 list_date=='' 的行**在 date 排序下留在 **listed 组末尾**（仍在 pending 之上）——pending 沉底优先级 > 空日期沉底。PASS = 四向 pending 全沉 + listed-空日期行位于 listed 组内末位。
- **F3-T10 → ACCEPT**：Case 6-9 定位为**廉价静态门**，契约明文「F3 排序/沉底/联动/dock 可视 PASS 唯一依据 = 真机 T2/T3/T4/T5/T6/M1，PS Case 不得替代」。补真机初始态回归：**未点击前** tbody **行数据序** == 评分降序 == wave-2 现状序（thead 新增 data-key/cursor/指示器位 = 允许的新 chrome，**行数据序不得变**；比对 tbody 各 `<tr>` 的 code 单元格序列，非整表字节）。

**MISSING 回应**：
- **F3-M1 [HIGH，task 点名] → ACCEPT**。已识别根因：`buildRankRows` 闭包捕获 `r`、`showDock` 有 `if(code===activeCode)return` 早退——排序重排 `<tr>` 后须**重新绑定 mouseenter（用新行的 code）+ 重置 activeCode=null**（防 stale/早退锁死）。实现：`sortRows()` 末尾复用 `buildRankRows()`(重建 tbody+重绑) 并 `activeCode=null`。验收(真机)：sort 首日 desc → hover 新首行 → `#dock-content` 股名==该行名称单元格；再 hover 新末位 listed 行 → dock 正确切换。PASS = ≥2 个排序后不同行，dock 名/涨幅逐一命中所 hover 行单元格（零 stale）。
- **F3-M3 [MED，task 点名] → ACCEPT，选方案(a) 定制滚动条**：`.rank-scroll::-webkit-scrollbar{width:8px}` + `::-webkit-scrollbar-thumb{background:rgba(138,133,128,.5)(INK_3 半透);border-radius:4px}` + `::-webkit-scrollbar-track{background:transparent}`，与 `#fff1e5` 纸皮调和。PASS = computed scrollbar 宽 ≤10px + thumb 色属纸皮色板(INK_3 系)。
- **F3-M4 [MED] → ACCEPT**：注入 `const TIER_ORDER=<json _TIER_ORDER>`；点「申购档」th → 行按 TIER_ORDER(重点申购+→重点申购→推荐申购→谨慎申购→不申购) asc 排、未知 tier 沉 listed 组末、pending 仍全沉。PASS = tier 序==TIER_ORDER + 未知档末 + pending 沉底。

---

## §4 F4-home-dedup 回应

**ACCEPT**：F4-T1（收紧：`[data-testid="stMain"]` 内「行情中枢」==1 且 `.cmsi-page-hero`==0）/ F4-T2（钉 home.py:252 zh/en 双语分支都带 fetch 段）/ F4-T3。

**HARDEN 回应**：
- **F4-T4 → ACCEPT**：补「删后顶部无空白遗留」——home 主内容区**首个可见块 == HUB masthead**（其上无空 `stMarkdown`/无 `.cmsi-page-hero` 空壳）+ SS 旁证顶部无空白带。范围守卫保留：`sector_overview.masthead` 未触碰(NT6) + home.py diff 仅「删 45-49 + 改 masthead 时间戳行」两处。PASS = 首块==masthead + 无空壳 + diff 两处。

**MISSING 回应**：
- **F4-M1 [LOW] → ACCEPT**：`grep -rn "home.title" app/`——若仅剩 locale 定义(零 t() 调用)，则 `home.title` key **zh/en 同去或同留**（不留单语言孤儿，守 GRD3 parity）。PASS = home.title 两 locale 都留或都删。

---

## §5 回归面抽查(R-1..R-8) 回应

**全 ACCEPT**（8 条数字级抽查 = 我 NT2/NT3 泛列的具体化，Evaluator 挑的溅射源准）：R-1(BANR4 dek+包装器 GR diff+JS) / R-2(BANR2 banner toggle computed) / R-3(IPO9 8 列+padStart) / R-4(IPO12 盘中锚 PS 5case+GR) / R-5(IPO4 KPI live) / R-6(IPO7 五档色 + 注入 TIER_COLORS 与 py `_TIER_COLORS` 单源一致) / R-7(BANR7 α chip 符号染色) / R-8(GRD7 init.sh 重启 :8599 四页 200 + echarts 连刷 3×)。R-8 = 所有 lib 改动前置门（memory `streamlit-cloud-reboot-after-lib-change` 实锤）。

---

## §6 全局 HARDEN(GBL) 回应

- **GBL-2 → ACCEPT**：验收顺序 GRD1-4 静态 → R-8 重启冒烟 → 逐区块真机 JS → SS；确认 4_Strategy_Picks.py 仅 F1 独占改（F2 只改 locale），R-1 diff 审兜底无二方同写。
- **GBL-1 [HIGH] → ACCEPT 全量网 + COUNTER 判据边界（DISPUTED-1，见 §7）**：接受「AppTest 遍历全部 19 页 + hub × zh/en」作 F1 站级唯一足量回归网。**但 PASS 判据须限定在 F1 责任面**——见 §7 争议。

---

## §7 DISPUTED（留 Planner 裁决）

**DISPUTED-1 — GBL-1 全量 AppTest 的 PASS 边界**
- Evaluator 判据：19 页×2 态「全 run 完，零 raw key、零 TypeError、零 rerun 上限」。
- Builder COUNTER：部分页(6_Ticker_Drill/8_SEC_Facts/model_drill/Healthcare)在 AppTest 下会触发 **yfinance / iFind MCP / DB 网络取数**，这些异常**与 F1(toggle/init_lang)无关**、且在 harness 沙箱/离线下必现 → 若「零 TypeError（含 data 层）」作硬门，F1 会被**预存在的数据层 flakiness 冤枉打回**。
- Builder 替代判据：GBL-1 PASS = 19 页×2 态**均跑过 i18n toggle+init_lang 段**（断言：无 **raw i18n key**、无**源于 i18n/toggle 路径的 TypeError**、无 **rerun 上限**）；**data 层网络异常白名单**（预存在、非本 wave 引入——以 HEAD `154a36c` 基线同页同异常为豁免证据）。即「F1 没把任何页跑崩在语言路径上」，而非「19 页数据全绿」。
- 若 Planner 认为应保留 Evaluator 硬门，Builder 请求配套：AppTest 跑在**数据 mock/离线夹具**下（否则判据物理不可满足）。**待裁**。

> 其余 26 项(REJECT 1 + HARDEN 11 + MISSING 7 + ACCEPT 补强) 均无争议，已收进 §8 合并清单。

---

## §8 合并验收清单（冻结 CONTRACT.md 底稿 · 编号连续 · 方法 + PASS 判据）

> 方法：RM(重启:8599/py_compile/AppTest) · JS(真机 computed-style/DOM/点击) · GR(grep 源码) · PS(纯字符串探针,仅廉价静态门) · SS(截图旁证)。
> **纪律**：凡「运行时行为」项(排序/滚动/hover/切换/dock 可视/语言真切)PASS 唯一依据=真机 JS，PS 不得替代。

### F1-toggle
| # | 断言 | 方法 | PASS |
|---|---|---|---|
| C01 | `lang_toggle_html()` 返双锚 `<a href="?...lang=zh\|en" target="_self">` + 段 CSS(11px/600/.08em/p5-12) + 容器 border1px#d4c4b0 radius3 | PS(zh/en 两态) | 双锚在 + CSS token 齐 |
| C02 | active 段 bg#c8102e 字#fff1e5 / inactive transparent 字#8a8580，随 `get_lang()`；无 state 走 zh(不崩) | PS(两态+空 state) | 三态配色正确 |
| C03 | 三页(8_SEC_Facts/e2_etf_heatmap/2_Healthcare)真机描边锚点在；旧钮清零 | JS + GR | 三页 `a[href*=lang=en]` 在 + `grep st.button app/lib/i18n.py`=0 + `grep -rn _lang_btn app/`(排 .omc)=0 + `.st-key-_lang_btn`==0 |
| C04 | 真机点非策略页 lang 段 → 整页切语（等 reload 完再断） | JS(click+wait+断标题) + SS | 该页已知 t() 串由中变英、回切还原 |
| C05 | banner toggle == 页 toggle 同 helper：两 `<a>` computed(font/padding/bg/color)逐字段等 + 容器 border/radius 达标 | JS | 计算样式全等 + BANR2 不回归 |
| C06 | qp 单源仅 i18n.py | GR | `grep query_params.get\(.lang app/`=1(i18n) + `grep _qp_lang app/pages/4_Strategy_Picks.py`=0 |
| C07 | 19 调用点零改 + 无必填参 | GR + PS | `grep render_lang_toggle() app/pages app/home.py`=19 全裸调 + 签名无必填参 |
| C08 | py_compile + AppTest(5_Valuation_Scanner/8_SEC_Facts/home/4_Strategy_Picks × zh/en) | RM | 各跑完无 raw key/TypeError/import 环/rerun 上限 |
| C09 | **[HIGH] lang toggle 保 sibling qp**：SEC/model_drill `?ticker=票` 切语言不丢票 | JS(真机) | URL 含 `ticker=票&lang=en` 且页面仍锁该票 |
| C10 | **[声明] reload 抹非 lang widget 态**（BANR2 机制,George 接受） | 契约明文 + SS(e2 1 例) | 声明在 + 旁证归接受 |

### F2-pitch
| # | 断言 | 方法 | PASS |
|---|---|---|---|
| C11 | zh.pitch **字符级==定稿 canonical**(§2 pin)；旧串消失 | PS + GR | `grep 这是什么 zh.py`=0 + zh.pitch 逐字等定稿(除 `**`/`\n\n`) |
| C12 | zh 态 dek `<b style="color:#1a1a1a;">`×3 锚 + `<br><br>` | JS(策略页 zh) | 三墨色粗体 + 段隔在 |
| C13 | en.pitch 恰 3 `**` 锚(镜像) + `\n\n`；zh/en 均非 raw key | PS | 3 锚齐 + 段隔 + `t()`≠key |
| C14 | en 态 dek `<b>`×3 + `<br><br>`(镜像 C12) | JS(策略页 en) | 三墨色粗体 + 段隔在 |
| C15 | BANR4 不回归：dek `<p>` 14px/1.65/#4a4a4a/max-880；包装器 146-149 逐字未改 | JS + GR diff | computed 达标 + 4 行字节不变 |

### F3-ipo-rank
| # | 断言 | 方法 | PASS |
|---|---|---|---|
| C16 | **[HIGH] iframe 定高+结构零溢出**(flex-col body/overflow:hidden/footer flex:none/rank-grid flex:1) | GR + JS | `grep max(2400`=0 + `scrollHeight≤_FIXED_H+2` + `.footer.bottom≤_FIXED_H` |
| C17 | **[HIGH] 末行 hover dock 可视**(真滚到底后) | JS(真机三步) | 末行可达 + dock 内容==末行股 + dock rect∈[0,_FIXED_H] |
| C18 | **[HIGH] rank-scroll 内滚 + thead sticky + dock static** | JS(computed+真滚) | overflow-y:auto/thead sticky top0/dock static + 滚到底 `|thead.top−container.top|<2px` |
| C19 | 点首日涨幅 desc→asc + 指示器 ▲/▼ | JS(click) | desc 首行=最高首日 listed / asc 反 + 指示器切换(均 pending 沉底,并 C21) |
| C20 | 换列初始方向 name asc / score desc / date desc | JS(逐列 click) | 各列首行符初始方向 |
| C21 | **[HIGH] pending 沉底四向 + 空日期边缘** | JS(四向) | (i)score↓(ii)score↑(iii)name↑(iv)date↓ 每种 pending 全沉 + listed-空日期行居 listed 组末 |
| C22 | # 列=评分原始名次(非重编号) | JS | 排序后位移行 `#`≠"01" |
| C23 | 排序前后同 code 数值恒等 + d1×100 一次(NT5 反篡改) | JS(diff 同 code) | 评分/首日/tier 文本恒等 |
| C24 | NT3 逐条不回归(None/NaN'—'/末笔 NaN 丢弃/终点锚/零伪造/零 MOCK) | PS(5 self-test)+GR | 现 5 case 全 PASS + GR 电池零命中 |
| C25 | self-test exit 0 + Case6-9 + py_compile + AppTest；**排序 PASS 唯一依据=真机 C17-21/C27,PS 不替代**；初始态行数据序==评分降序==wave-2 | RM + JS | 退出 0 + 未点击 tbody code 序==评分降序 |
| C26 | **[HIGH] TIER_COLORS/ORDER 注入与 py 单源一致** | JS + PS | 注入 JS 值==py `_TIER_COLORS`(L30-36)/`_TIER_ORDER`(L37) |
| C27 | **[HIGH] 排序后 hover→dock 无 stale**(重绑+activeCode 复位) | JS(真机) | ≥2 排序后不同行 dock 名/涨幅逐一命中,零 stale |
| C28 | **rank-scroll 滚动条纸皮调和**(方案 a 定制) | JS(computed) | scrollbar 宽≤10px + thumb INK_3 系半透 |
| C29 | tier 列排序=TIER_ORDER + 未知档末 + pending 沉底 | JS(click 申购档) | tier 序==TIER_ORDER + 未知末 + pending 沉 |

### F4-home-dedup
| # | 断言 | 方法 | PASS |
|---|---|---|---|
| C30 | 单标题(旧 cmsi-page-hero 消失) | JS + SS | `stMain` 内「行情中枢」==1 + `.cmsi-page-hero`==0 |
| C31 | fetch 时间折入 masthead(zh/en 双语) + None 降级'—' | JS + PS | 时间戳行含 latest+fetch_utc[:16] 两段;None→'—'不崩 |
| C32 | page_header 删净 + py_compile + AppTest | GR + RM | `grep page_header app/home.py`=0 + home 无异常 |
| C33 | 删后顶部无空白 + 范围守卫 + diff 两处 | JS + SS + GR | 首块==masthead + 无空壳 + `sector_overview.masthead` 未碰 + home.py diff 仅两处 |
| C34 | home.title parity(无单语言孤儿) | GR | zh/en 两 locale 同去或同留 |

### 回归电池(R) + 全局(GBL)
| # | 断言 | 方法 | PASS |
|---|---|---|---|
| C35 | R-1 BANR4 dek+包装器不回归 | GR diff + JS | 146-149 字节不变 + dek 14/1.65/#4a4a4a/880 |
| C36 | R-2 BANR2 banner toggle | JS computed | active#c8102e/#fff1e5 + 容器 1px#d4c4b0 r3 + 段 mono11/600/.08em/p5-12 |
| C37 | R-3 IPO9 8 列结构 + padStart + pending rank'—' | JS + PS | 8 列齐 + `padStart(2,'0')` + pending'—' |
| C38 | R-4 IPO12 盘中锚(CRITICAL) | PS(5case)+GR | Case5 endpoint 100.0 + Case4 无 pts + 零 Math.random/genData |
| C39 | R-5 IPO4 KPI live(零硬编 384/56.9/2.69) | PS + GR | +384.0%/-56.9% 实算 + 字面量零命中 |
| C40 | R-6 IPO7 五档色(=C26 单源) | JS + PS | 五色达标(a00d25/c8102e/0d7680/a06d1f/6b6560) |
| C41 | R-7 BANR7 α chip 符号染色 + 大号 mono32 tabular | JS computed | ≥0 青/青底 <0 红/红底 |
| C42 | R-8 GRD7 重启冒烟(前置门) | RM | init.sh 重启 → home/Strategy/Healthcare/AI 200 + echarts #m/#eq 连刷 3× 出图 |
| C43 | **[HIGH,DISPUTED-1] GBL-1 全量 smoke** 19 页+hub×zh/en | RM(AppTest) | **待裁**：Evaluator=全绿零 TypeError；Builder=跑过 i18n 段无 raw key/i18n 路径 TypeError/rerun 上限，data 层网络异常白名单(基线同异常豁免) |
| C44 | GBL-2 验收顺序 + 无二方同写 4_Strategy_Picks | 流程 + GR | 顺序遵行 + R-1 diff 审兜底 |

---

（完 · Builder round-2 回应 v1；REJECT 1 全收、HARDEN 12 全收(F1-T3/F3-T1 机制加固)、MISSING 7 全收；DISPUTED = C43(GBL-1 边界) 留 Planner。待冻结 CONTRACT.md）
