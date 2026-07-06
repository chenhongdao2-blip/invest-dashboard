# WAVE-3 ROUND-3 定向复验（Evaluator）— Codex 6 findings 修复面

- 触发：Codex 异模型终审 REJECT 6 findings(2C/2M/2m,`eval/AUDIT_codex_round1.log` 尾部);Builder 全修。
- 改动面：`ipo_stage.py`(_json_for_script 五 blob `<`→< 转义 + JS `esc()` 全插值 + d1 非有限→None→JS `—`) / `i18n.py`(_cur_qp get_all + _lang_href doseq 多值 qp + m6 窄化注释) / `en.py`(docstring 补 supersession)。
- 范围(team-lead 指派):重启冒烟 → 静态(self-test + C01/C02 PS + _json_for_script 挂点) → 真机溅射面(IPO 渲染/排序/hover/dock + C09 after M4 + dek) → C43 快查。

## ⚠️ 范围增量(2026-07-06)——最终工作树锚定 self-test = **43 断言**

Codex round-2 判 **M3 残留 NOT-FIXED**:KPI `idxmax` 全-NA 抛 ValueError + 分档统计 nan 漏渲。Builder 再落一版 **仅 ipo_stage.py**(i18n.py/en.py 此后未再动——已 grep 佐证:get_all/doseq 仍在、en Supersession 仍在)。修法:day1_ret 算术切 `df_fin`(有限子集,L457 `_d1_num.notna() & abs()!=inf`),KPI/tier 守卫改 `n_fin>0`(L465/489),**样本计数口径不动**(n_total/n_listed/n_pending + "已上市 X" 仍走 df_listed);self-test 扩 39→**43**(新 Case12)。

**本 Evaluator 已在最终树(43 断言)重锚 F3/ipo 面**:
- self-test **43 PASS**(Case12 四断言:all-NaN listed 不抛 idxmax / 无 literal 'nan' / KPI+tier 空态 / 样本计数不变「已上市 2·待上市 0」)。
- 重启 :8599 后真机 IPO tab **最终态复核**:KPI 三卡 **零变化**(54 / +384.0% 曦智科技·重点申购+ / -56.9% 华健未来-B·谨慎申购,foot 已上市38·待上市16);分档中位全有限 `[+276.5,+80.0,+49.2,+44.2,+93.4]%` **无 nan 泄漏**;54 行渲染正常、**零 u003c 泄漏**;C19 排序(desc▼首+384.0%=max)/ C27 hover(商米科技命中)/ C17 末行 dock(宝盖新材·真滚·dock∈视口) 全过;**无 console JS 错**。正常数据 df_fin≡df_listed → KPI/分档零变化,符合预期。
- 分档「只数」= 进档有限行数(与 median/green_rate 分母一致)——Codex r3 NIT,**Planner 裁决维持**(计数与统计口径一致优先,2026-07-06),非缺陷。

**各项验收工作树状态钉桩**(git diff --stat 佐证:自六修态起仅 ipo_stage.py 再动):
| 项 | 依赖文件 | 验收工作树 | 状态 |
|---|---|---|---|
| C16-C29 / C37-C40 / C1 / C2 / M3(含 KPI 残留) | ipo_stage.py | **最终树(43 断言)** | ✅ 本节重锚 |
| C01-C10 / C36 / M4 / m6 | i18n.py | 六修态(此后未动) | ✅ 仍效 |
| C11-C15 / m5(dek) | en.py / zh.py / 4_Strategy | 六修态(此后未动) | ✅ 仍效 |
| C30-C34 | home.py | round-1(此后未动) | ✅ 仍效 |

## Round-3 verdict:**Codex 6 findings + M3-KPI 残留 全修复确证(final tree, self-test=43),4/4 feature 维持全绿,零回归 → 可交 George 眼验**

| Codex finding | 严重度 | 修复确证 |
|---|---|---|
| C1 `</script>` breakout (ipo:557) | CRITICAL | ✅ `_json_for_script` 5 blob 全 `<`→<;self-test Case11 过;真机 rendered HTML 无 `u003c` 泄漏(转义回 `<` 正确) |
| C2 innerHTML 未转义 (ipo:260) | CRITICAL | ✅ `esc()`(&<>"')挂满 buildRankRows(code/name×2/chip tier/sub_sector/listDate) + showDock(name/codeChip/chip/source);真机 53 CJK 名 + 54 chip 正常渲染,零可见变化 |
| M3 listed NaN d1 非诚实 `—` (ipo:502) | MAJOR | ✅ `_finite()` py 兜 None/NaN/inf/非数 + `hasD1()` JS;Case10 过;真机 16 pending 显 `—`、零 `NaN%` |
| M4 qp 多值不通用 (i18n:60) | MAJOR | ✅ `get_all`+`doseq=True`;真机 `?foo=a&foo=b` 双值全保 + 单值 `ticker=NVDA` 干净(无 `%5B['..']` list-repr);C09 after-M4 仍过 |
| m5 en.py docstring 陈旧 | MINOR | ✅ 补「2026-07-05 George wave-3 F2 supersession」note,provenance 明示 |
| m6 _cur_qp 宽 except | MINOR | ✅ 保留 bare except 但补注释说明(bare-import 探针路径 no-context 异常类型跨 Streamlit 版本不稳,只丢 offline 探针 sibling params,live page 不受影响) |

---

## 先审 diff 后验行为(先证修复不是自述)

### 静态(自己跑,不信 self_checks)
- **ipo self-test 39 断言全 PASS**(`PYTHONPATH=app .venv/bin/python -m lib.ipo_stage`),含:
  - Case10:`no literal 'NaN' in html` + `non-finite listed d1_pct == null, row stays listed → renders '—'`
  - Case11/C1:`no raw '</script><img' breakout` + `exactly one legit </script>` + `data '<' escaped to <`
  - Case11/C2:`esc(` markers 全在(r.name/r.code/r.sub_sector/row.name/row.source)
- **`esc()` 定义完整**:`&<>"'` 五字符 HTML 转义(ipo:160-164);数值/hex 色受控不转。
- **`_json_for_script` 挂 5 blob**:rank/intraday/tier_color/tier_order/default(ipo:598-602);`grep _json_for_script(`=6(5 调用+1 def)。
- **`_finite`** try/except 兜 TypeError/ValueError(float(None)/非数不抛)。
- **i18n `_cur_qp`** = `{k: get_all(k) for k in keys()}`;`_lang_href` = `urlencode({**_cur_qp(),'lang':[code]}, doseq=True)`。
- **C01/C02 PS 探针重跑 ALL PASS**(M4 改 href 生成未破两态锚点/配色/容器)。
- **C42**:init.sh 重启 :8599(ipo/i18n lib 必重启),ready 2s,四页 200。

### 真机溅射面(修复触及的渲染路径)
- **IPO 排行表正常**(真数据 54 行):row0=魔门塔(6880)/8.7,53 CJK 名完好(样本 魔门塔/曦智科技/芯碁微装),54 tier chip,16 pending 显 `—`,**`NaN%`=false**,**泄漏 `u003c`=false**(esc/转义对正常数据零可见变化)。
- **无 console JS 错误**(且 54 行全渲染+排序+dock 可用 = 脚本无 load-time 语法错,比 console 更强的证据)。
- **C19 排序**:d1 desc ▼ 首 +384.0%(max)/ asc ▲ 首 -56.9%(min)。
- **C27 hover**:2 异行 dock 逐一命中。
- **C17 末行 dock**:真滚到底,末行 宝盖新材 可视,dock 载荷=末行名,dock ∈ 视口。
- **C09 after M4**:`/SEC_Facts?ticker=NVDA&lang=en` 停 `/SEC_Facts`、ticker+lang 双参、英文;EN anchor href 干净(ticker=NVDA,无 list-repr);**M4 多值**:`?foo=a&foo=b` 经 toggle 后双值全保(getAll=[a,b])。
- **策略 dek**:en.py 仅 docstring(STRINGS 不变,运行时零影响);4_Strategy × zh/en AppTest ok 覆盖 dek 渲染。

### C43 快查(6 cell 无新伤)
- 8_SEC_Facts + 2_Healthcare + 4_Strategy_Picks × zh/en:**6/6 ok**,零 exception / 零 raw key。(NumPy timedelta DeprecationWarning + FOLD delisted = 既有噪声。)

## 结论
- Builder 对 Codex 6 findings **逐条精准修复,零 collateral、零回归**:安全面(C1 script breakout / C2 innerHTML XSS)已封,诚实面(M3 NaN→`—`)已补,通用面(M4 qp 多值)已泛化,文档面(m5/m6)已澄清。
- **F1/F2/F3/F4 维持全绿**;esc()/转义对正常渲染零可见变化(真机确证)。
- 本 Evaluator 侧判定 **wave-3 全绿、可交 George 眼验**;Codex 复审(team-lead 并行跑)两路都绿即 ship。
- cycles_used=3/3(Codex-fix 复验计入本轮);断路器:本轮 6 findings 全修确证,非空过。
