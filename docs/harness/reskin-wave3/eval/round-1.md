# WAVE-3 ROUND-1 独立验收（Evaluator）

- 分支 `feat/kline-reskin`，基线 HEAD `154a36c`（Builder 改动全在**工作树未提交**，`git diff 154a36c` = wave-3 全量 diff，7 文件）
- 锚 = `CONTRACT.md` C01-C44 + NT1-7 + §2 canonical；不采信 Builder self_checks
- 验收顺序遵行 C44：GR/PS 静态 → C42 重启冒烟 → C43 差分门 → 真机 JS → SS
- 服务器：`init.sh` 重启 :8599，四页 GET 200（home/Healthcare/Strategy_Picks/AI_Overview），真机在此实例跑

## 全局 verdict

| | 结果 |
|---|---|
| 总项 | 42（C01-C44，其中 C35=C15、C40=C26 双列一次执行）|
| PASS | **40** |
| FAIL | **2 — C04 / C09（同一根因）** |
| Feature 翻绿 | **F2 ✅ / F3 ✅ / F4 ✅**；**F1 ❌（C09[HIGH]+C04 挡）** |
| browser_needed | 否（claude-in-chrome 全程可用，真机判据均已跑）|

**一句话**：F2/F3/F4 三个 feature 全绿、可放行到 Stage 4；F1 卡在一个 **[HIGH] 真机回归**——`init_lang()` 的 `st.rerun()` 使**任何子页带 `?lang=en` 加载即弹回 home**，`?ticker=` 详情锁丢失（C09 失败），子页 lang 段点击也随之弹回（C04 失败）。修复点单一且明确（见下）。

---

## FAIL 清单（带 critique + 精确代码位置）

### ❌ C09 [HIGH] — lang toggle 到 EN 使子页弹回 home，详情锁丢失

**判据**：URL 含 ticker + lang=en **且页面仍锁该票（详情不重置）**。
**实测**：URL 侧 PASS（ticker + lang=en 都在），但**页面弹回 home、详情锁丢失** → 判据后半 FAIL。

**证据（真机，可复现，非 flakiness）**：
| 导航（直接 GET，= `<a target=_self>` 点击的等价语义）| 落地 pathname | 结果 |
|---|---|---|
| `/Model_Drill?ticker=VEEV&lang=zh` | `/Model_Drill` | VEEV 锁住 ✅（对照）|
| `/SEC_Facts?ticker=NVDA&lang=zh` | `/SEC_Facts` | 停留 ✅（对照）|
| `/Model_Drill?ticker=VEEV&lang=en` | **`/`** | 弹回 home，VEEV 丢 ❌（复现 2×）|
| `/Sector_Heatmap?lang=en`（无 ticker）| **`/`** | 弹回 home ❌（排除 ticker 相关）|
| SEC 页真点 EN 段 | **`/?…lang=en`** | 弹回 home（en）❌ |

**根因（代码级确证）**：`app/lib/i18n.py:47-50`
```python
qp_lang = st.query_params.get("lang")
if qp_lang in ("zh", "en") and qp_lang != st.session_state["lang"]:
    st.session_state["lang"] = qp_lang
    st.rerun()          # ← 元凶：L50
```
- `lang=zh`（==DEFAULT）不进 rerun 分支 → 停留；`lang=en`（≠default）进分支 → `st.rerun()`。**唯一差异就是这句 rerun。**
- 在 `st.navigation` 下，子页**首帧** `st.rerun()` 把 app 复位到默认页（home）。
- **是 wave-3 回归**：基线 `init_lang()` 不读 qp、不 rerun（qp→session 同步旧在各页 `_qp_lang` 块，仅 4_Strategy 有，且页级 toggle 是 `st.button` 的**页内 rerun 不改 URL**，不弹页）。F1 把同步搬进 `init_lang()`+`st.rerun()` 才引入弹回。
- C43 AppTest 矩阵测不到（无 URL 路由），所以静态/差分全绿也漏这条——正是契约把 C09 钉为真机 JS 的原因。

**修复方向**：删掉 `st.rerun()`（L50）。`init_lang()` 在每页顶、任何 `t()` 之前调用，`st.session_state["lang"]=qp_lang` 后**本帧**所有 `t()` 已读到新语言，锚点自身已带 lang，rerun 冗余且有害。删后需复验：①无半语言渲染（init_lang 仍首位）②toggle active 段本帧即反映新 lang（`get_lang()` 读已更新的 session_state，OK）③子页带 `?lang=en` 不再弹页、`?ticker=` 仍锁。

### ❌ C04 — 点非策略页 lang 段整页切语（同根因 co-symptom）

**判据**：点非策略页 lang 段 → 整页切语，该页 t() 串由中变英、回切还原。
**实测**：home（也是非策略页）toggle en/zh **在原页切换 OK**（`/?lang=en`→Market Hub，`/?lang=zh`→行情中枢）；但 **SEC/Model_Drill/Sector_Heatmap 等子页点 EN 段 → 弹回 home**（C09 同根因），"该页"不保留 → 该页 t() 串无法在原页验证。
**结论**：子页 in-place 切语不成立 → FAIL。修 C09（删 rerun）即连带修复。

---

## PASS 清单（分 feature，附证据摘录）

### F1-toggle（C01-C10 + C36 + C43/C44）— 除 C04/C09 外全 PASS
- **C01** PASS（PS）：`lang_toggle_html()` 双 `<a target=_self>` + seg mono/11px/600/.08em(0.88px)/pad5px12px + 容器 `border:1px solid #d4c4b0` `radius:3px`（`theme.PAPER_EDGE=#d4c4b0` 已核）。
- **C02** PASS（PS 三态）：active `#c8102e/#fff1e5`、inactive `transparent/#8a8580`，随 `get_lang()`；无 session 裸调不崩、默认 zh。
- **C03** PASS（JS+GR）：ETF_Heatmap/Healthcare/SEC_Facts 均 2 锚 + `lang=en` 在；`grep st.button app/lib/i18n.py`=0、`_lang_btn`=0、`.st-key-_lang_btn`=0（真机 old_button=0）。
- **C05** PASS（JS）：banner 锚 computed（Strategy 页）vs 页级锚 computed（ETF_Heatmap 页）**逐字段全等**——中 active `#c8102e/#fff1e5`、EN `transparent/#8a8580`、11px/600/0.88px/pad5px12px/mono、容器 `1px #d4c4b0` r3。同源 `lang_toggle_html()`（strategy_banner.py:228 `toggle=i18n.lang_toggle_html()`）不发散。
- **C06** PASS（GR）：`query_params.get(.lang` 全 app/ 仅 `i18n.py:47` 1 处；`_qp_lang` 在 4_Strategy=0（diff 确认删除旧 5 行块）。
- **C07** PASS（GR）：`render_lang_toggle` 19 处裸调（含 `model_drill.py:28`），签名默认参 `anchor_cols=(9.0,1.0)` 无必填。
- **C08** PASS（RM）：7 文件 py_compile OK；C43 矩阵 5_Valuation/8_SEC/home/4_Strategy × zh/en 全 ok，零 raw key/TypeError/rerun 上限。
- **C10** PASS：声明在契约本条 + SS 旁证（ETF_Heatmap 截图 `ss_76193ckkn`，中/EN 段渲染）。⚠️ 注：C09 修复后此 anchor-reload 行为应回归为"仅抹 widget 态"而非"弹页"。
- **C36** PASS（JS）：banner toggle computed 全达标（同 C05 数值）。
- **C43** PASS（差分门）：40 cell diff 零新增异常/零新增 raw key（`sec.gov` 域名误报两侧同在抵消）/零新增 crash/TIMEOUT/零 rerun 命中。round1 落 `round1-apptest.json`。
- **C44** PASS：GR/PS→C42→C43→JS→SS 顺序遵行；`4_Strategy_Picks.py` 仅 F1 改（删 `_qp_lang` 5 行，diff 唯一 hunk）、F2 只碰 locales；C35 diff 审兜底。

### F2-pitch（C11-C15 + C35）— 全 PASS ✅
- **C11** PASS（PS+GR）：zh.pitch **字符级 == canonical**（从 CONTRACT §2 blockquote 直解析比对，len=165 全等）；`grep 这是什么 zh.py`=0；3 个 `**` 锚 + `\n\n`。
- **C12** PASS（JS 真机）：zh 态 dek `<b>`×3 computed color 均 `rgb(26,26,26)`=#1a1a1a + `<br>`×2。
- **C13** PASS（PS）：en.pitch 恰 3 `**` 锚（Methodology / …day it is selected / …since selection）+ `\n\n`；zh/en `t()` ≠ key。
- **C14** PASS（JS 包装器 + PS en-dek 产物）：复现 page code 142-144 于 en.pitch → 3 `<b style="color:#1a1a1a;">` + `<br><br>`；wrapper computed（14px/1.65/#4a4a4a/880）已由 C12 同页真机确证（语言无关同一代码路径）。*备注：EN 态直接真机渲染被 C09 弹回阻断，故 en dek 以「PS 产物断言 + C12 包装器真机」双证；C09 修好后 round-2 可补一次 EN 态直 JS 作 belt-and-suspenders。*
- **C15/C35** PASS（JS+GR diff）：dek `<p>` computed `14px/1.65/rgb(74,74,74)/max-width:880px`；`4_Strategy_Picks.py` diff 唯一 hunk=删 `_qp_lang`，BANR4 包装器 146-149 **不在 diff**=字节未改。

### F3-ipo-rank（C16-C29 + C37-C40）— 全 PASS ✅（真机 54 行真数据：38 listed / 16 pending）
- **C16** PASS：`grep max(2400`=0，`_FIXED_H=1120`；真机 body `flex-col/overflow:hidden/height1120`，`scrollHeight=1120`≤1122，`.footer` bottom=1088≤1120，mh/kpi/tier/footer flex-grow0、rank-section flex1、grid min-height0。
- **C17** PASS（真滚+真 rect，缺陷 b 核心）：`.rank-scroll.scrollTop=scrollHeight`（2436+369=2805=scrollHeight），末行 宝盖新材(8090) rect 939-1003 落容器带 634-1002；hover 末行 → dock 载荷=宝盖新材+"—"（pending 诚实）；dock rect 634-936 ∈[0,1120]。
- **C18** PASS：`.rank-scroll` overflow-y:auto、thead `sticky top:0`（真滚到底后 thead.top=634=container.top，|Δ|<2px）、`.dock` position:static。
- **C19** PASS（真点击）：首日涨幅 desc→首行 +384.0%（max）▼；再点 asc→首行 -56.9%（min）▲。
- **C20** PASS：初始方向 name asc(▲)/score desc(▼)/list_date desc(▼) 各列首行符合。
- **C21** PASS（四向）：score↓/score↑/name↑/date↓ 每向所有 pending DOM index > 所有 listed。
- **C22** PASS：row0=pending（6880,score8.7,rank"—"），首个 listed rank="02"≠"01" → `#` 为评分档身份锚，排序不重编号。
- **C23** PASS（diff 同 code）：排序前后全 54 code 的 评分/首日涨幅/tier 逐一恒等，tamper=0。
- **C24** PASS（GR/PS）：`Math.random|genData`=0；self-test no MOCK/no 2.69。
- **C25** PASS（RM+JS）：self-test exit 0 + Case6-9 全 PASS；初始未点击 tbody 数据序单调 score-desc（全 54 行）。
- **C26** PASS（JS+PS）：5 tier chip computed color 全等单源 `#a00d25/#c8102e/#0d7680/#a06d1f/#6b6560`；Case6 注入 TIER_ORDER==py。
- **C27** PASS（JS）：排序后 hover 3 个异行（剂泰科技-P +169.0%/云英谷 +91.7%/英派药业-B +76.0%）dock 逐一命中；回 hover 首行 dock 更新，零 stale。
- **C28** PASS：`::-webkit-scrollbar{width:8px}` + thumb `rgba(138,133,128,.5)`(INK_3 半透) + track transparent。
- **C29** PASS（点击）：申购档序==TIER_ORDER[重点申购+→…→不申购]、pending 全沉。
- **C37** PASS：8 列 data-key 齐、pending rank/d1 全"—"、listed rank padStart 2 位。
- **C38** PASS：Case5 endpoint 100.0 + Case4 无 pts + 零 random。
- **C39** PASS：KPI live +384.0%/-56.9% 实算（真机截图确证）。
- **C40** PASS：=C26 五档色单源。

### F4-home-dedup（C30-C34）— 全 PASS ✅
- **C30** PASS（JS）：`[data-testid=stMain]` 内「行情中枢」计数=1（HUB masthead）、`.cmsi-page-hero`=0。
- **C31** PASS（PS+JS）：时间戳行折入 masthead，zh/en 双分支带 `fetch_utc[:16]`，`fetch_utc=None`→"—"；真机 home 显 "EOD 2026-07-02 · fetch 2026-07-02T23:41 HKT"。
- **C32** PASS（GR+RM）：`grep page_header home.py`=0 + py_compile + home AppTest ok 无 raw key。
- **C33** PASS（JS+GR）：empty-shell markdown=0、masthead 为首个内容块（顶栏 toggle→隐形 home-CSS style→masthead）；home.py diff **恰两 hunk**（删 page_header + 改时间戳行），`sector_overview.masthead` 未碰（NT6）。
- **C34** PASS（GR）：`home.title` zh(行情中枢)+en(Market Hub) 双在，parity 成立。

### 全局门
- **C42** PASS：init.sh 重启 :8599，home/Healthcare/Strategy_Picks/AI_Overview 全 200；多次加载 home（market-hub tiles + treemap echarts）与 strategy（sparkline SVG）均出图。

## §0 不动面抽查（NT1-7）
- **NT4** ✅：`app/lib/theme.py` **零 diff**（`git diff 154a36c` 无此文件）；F1 新皮走 i18n 模块 inline HTML。
- **NT2/BANR4** ✅：4_Strategy 包装器 146-149 字节未改（diff 确认）。
- **NT5** ✅：C23 数值零篡改；排序只动展示序。
- **NT6** ✅：home.py diff 未碰 sector_overview.masthead。
- **NT3/NT7** ✅：ipo self-test 全绿（无 MOCK/demo 字面量/末笔 NaN 整路丢弃）、srcdoc 自包含无外部 JS。

## 退回 Builder（仅 F1）
单点修复：删 `app/lib/i18n.py:50` 的 `st.rerun()`（保留 L48-49 的 session_state 赋值）。修后 round-2 定向复验 C09/C04（子页 `?lang=en` 不弹页 + `?ticker=` 仍锁 + 子页 in-place 切语）+ 补 C14 EN 态直 JS。F2/F3/F4 已绿，无需重验（除非 F1 修改触及共享 i18n 影响 t() 路径——`init_lang` 删 rerun 不改 `t()`，F2 dek 不受影响）。
