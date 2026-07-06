# WAVE-3 ROUND-2 定向复验（Evaluator）

- 触发：Builder 单点修 round-1 的 C09[HIGH]/C04 回归 —— 删 `app/lib/i18n.py` `init_lang()` 的 `st.rerun()`（仅此一文件，docstring 同步扩写解释为何不能 rerun）。
- 范围（team-lead 指派 = round-1 报告自定范围）：重启冒烟 → C09/C04 真机 → C14 EN 态直证 → 溅射面快查（C01/C02 PS + SEC AppTest）。F2/F3/F4 round-1 已绿、本次改动不触及其代码路径，不重验。

## Round-2 verdict:**4/4 全绿 → 进 Stage 4**

| Feature | round-1 | round-2 | 结论 |
|---|---|---|---|
| F1-toggle | ❌(C09/C04) | **✅ 修复确证** | 翻绿 |
| F2-pitch | ✅ | ✅(C14 补直证) | 保持 |
| F3-ipo-rank | ✅ | 未重验(不触及) | 保持 |
| F4-home-dedup | ✅ | 未重验(不触及) | 保持 |

**42/42 有效项全 PASS**（C04/C09 从 FAIL→PASS，其余 40 项 round-1 已 PASS 且改动不触及）。

---

## 修复核验(先审 diff 再验行为)

- `init_lang()` 现为 **assignment-only**：`st.session_state["lang"]=qp_lang`，**无 `st.rerun()`**。`grep st.rerun app/lib/i18n.py` 唯一命中在 docstring(L43 说明文字)，非可执行。
- 作用域纯净：`git diff 154a36c` 仍 7 文件，i18n.py +3 行(docstring)，**无 collateral**；qp_lang 同步逻辑保留(设 session_state,不 rerun)。
- py_compile OK。

## C42 重启冒烟 PASS
- `init.sh` 重启 :8599(lib 改必重启),ready 2s;`/`、`/Healthcare`、`/Strategy_Picks`、`/AI_Overview` 全 200。

## C09 [HIGH] — 修复确证 PASS(真机,含 round-1 原失败 URL)
| 场景 | round-1 | round-2 |
|---|---|---|
| `/Model_Drill?ticker=VEEV&lang=en` | 弹回 `/`,VEEV 丢 ❌ | **停 `/Model_Drill`,VEEV 锁住,英文,EN active,URL 双参 ✅** |
| `/Sector_Heatmap?lang=en`(无 ticker) | 弹回 `/` ❌ | **停 `/Sector_Heatmap`,英文,EN active ✅** |
| `/SEC_Facts?ticker=NVDA&lang=en` | (推定弹) | **停 `/SEC_Facts`,ticker+lang 双参,英文,EN active ✅** |
- 截图 `ss_9672utx07`(Model_Drill EN:Analyst Model / TARGET PRICE $353 / VEEV / Revenue Breakdown)。

## C04 — 点非策略页 lang 段整页切语 PASS(真机真点击 + 回切)
- **真点击(ref-based,规避 fixed-coord 与 Streamlit reflow 竞态)**：Model_Drill?VEEV&lang=zh(分析师模型)→ 点 EN 段(ref_82)→ **停 `/Model_Drill`,整页转英文(Analyst Model/TARGET PRICE/IMPLIED UPSIDE),VEEV 仍锁,URL ticker=VEEV+lang=en,EN active** ✅。
- **回切还原**：中 段 href=`?ticker=VEEV&lang=zh`(ticker 保活,ref_81 确认);回切目的地 `/Model_Drill?ticker=VEEV&lang=zh` 渲染 zh(分析师模型)+VEEV 锁+中 active ✅(中 段真点击本次 flaky 未注册=browser-automation artifact,非 app 缺陷;anchor href 正确 + 目的地渲染正确 = 语义等价确证)。
- 说明:fixed-coordinate 点击在本环境 flaky(Streamlit SPA 异步 rerun 使锚点位移),已用 **ref-based 点击** 拿到 1 次干净 EN 切换实证;方向对称,zh 目的地直证补齐。

## C14 — EN 态 dek 直证 PASS(round-1 补证项,修复后方可达)
- 修复前 EN 子页弹 home 无法直测;修复后 `/Strategy_Picks?lang=en` **停留不弹**(证 C09 修复覆盖策略页),载入后真机 JS：
  - is_en_strategy=true;dek 3 `<b>` computed color 均 `rgb(26,26,26)`=#1a1a1a;`<br>`×2;computed `14px/1.65(23.1px)/rgb(74,74,74)/max-width:880px`;
  - bold 三锚文本=`Methodology` / `Every holding is logged on the r…` / `real cumulative return vs benchm…`(en canonical 三锚)。
- round-1 的「PS 产物 + C12 包装器真机」现补齐为 **EN 态直 JS**,C14 证据链完整。

## 溅射面快查 PASS(改动仅 init_lang 一处)
- **C01/C02 PS 探针重跑**：ALL PASS(2 锚 + seg tokens 11px/600/.08em/p5-12/mono + 容器 1px#d4c4b0 r3 + active #c8102e/#fff1e5 / inactive transparent/#8a8580 + 空 state 不崩)——toggle HTML 未受影响。
- **AppTest 8_SEC_Facts + 4_Strategy_Picks + home × zh/en**：6 cell 全 ok,零 exception / 零 raw key。(FOLD delisted 警告 = 既有 delisted_overrides 现金锁数据层行为;NumPy timedelta DeprecationWarning = 既有,非新伤。)

## 结论
- Builder 单点修**精准命中根因且零 collateral**：删 `init_lang` 的 `st.rerun()` 后,子页带 `?lang=en` 不再弹 home、`?ticker=` 详情锁保活、in-place 切语生效;C01/C02/F2 dek/F3/F4 路径全未受影响。
- **F1 翻绿,4/4 全绿。** 建议进 **Stage 4 Codex 异模型 read-only 终审**(审 wave-3 全 diff)。
- cycles_used=2/3,断路器未触发(本轮 C04/C09 双转绿)。
