# WAVE-3 ROUND-5 定向复验（Evaluator）— C45 第二修终验

- 触发：round-4 打回 C45(图表恒画 280 fallback、155px cell 裁 125px、0% 标签不可见,根因 `.dock align-self:start` 使空骨架 clientHeight=0)。Builder 第二修(仅 ipo_stage.py):`.dock align-self:stretch` 根治测量 + SVG `viewBox`/`width:height:100%`/`preserveAspectRatio="xMidYMax meet"` 兜底。
- 我验收时 self-test = **44 断言**(Case13 升级版)。

## Round-5 verdict:**C45 ✅ PASS（静态+结构+真机三证齐全）** —— 真机探针 team-lead 代跑(George 本机 Chrome,:8599 最终树)回值,四门全过

> 诚实边界:round-4 教训=「静态 token 在 ≠ 运行时正确」,故不单凭静态翻绿;真机核心断言由 team-lead 代跑(evaluator 因第二 Chrome 连入被工具禁自选浏览器),判决权在 evaluator,据回传原始值裁决。

### 真机裁决（team-lead 代跑,探针逐字用 round-5-browser-probes.md）
| 探针 | 关键回值 | 结果 |
|---|---|---|
| A 默认宽(iframe_w=1062) | 5 charted 行(1879/7666/7688/3310/3296)**每行** svg_not_taller_than_cell/svg_bottom_within_cell/zero_label_within_cell/endpoint_within_cell **全 true**;`all_no_clip:true`;`dock_le_footer:true`(1002≤1026);`dock_foot_visible:true`(区间高+15.5%·低+9.1%);`dock_fills_track:true`(dock_h=369==scroll_h=369 对称双栏) | ✅ |
| B 窄宽模拟(iframe.style.width=900px,已恢复) | 1879:narrow_svg_within_cell/narrow_zero_visible/narrow_dock_le_footer **全 true** | ✅ |
| C 溅射面 | sort ▼ 首+384.0% / hoverA·hoverB true(无 stale)/ c17_dock_le_footer·c17_last_has_dock true | ✅ |
| console | onlyErrors 零命中 | ✅ |

**对照 round-4**:round-4=svg_h 280/cell 155/overflow 125px/zero_label_visible **false**/all_280:true → round-5=全 charted 行 svg≤cell、0% 完整可视、all_no_clip:true。**裁切已修,两层防御(stretch 根治测量 + meet 物理不可裁)真机生效;dock 撑满行轨 369==369 完美对称无空洞。**

### C45 终裁：**PASS**。四门(A all_no_clip + B narrow 不裁 + C 溅射 + console 零错)全过。

### ⏭ C46（新增 §2.5,待验）
George 眼验又提:策略页 hero 净值图 endLabel 被画布右缘裁切(`strategy_hero.py` grid.right=58 不够,修 58→96)。Builder 修复中,**未落地/实例未重启 → 本轮不验**。C46 落地重启后做轻量真机核(endLabel 全字符可见)+ 确认 C45 面未受影响(strategy_hero≠ipo_stage 不同文件,理论零溅射),写 round-6(或补本文)。**wave-3 ship gate 需 C45(已过)+ C46(待)俱绿。**

## 修复核验（先审 diff）—— 两层防御,任一层独立成立即不裁

### 层 1:`.dock align-self:stretch` 根治测量（ipo_stage.py:140）
round-4 根因:`align-self:start` → dock 内容定高 → 空 `.dock-chart`(flex:1/min-height:0)塌成 0 → step2 测 `clientHeight=0` → 恒退 280 fallback。
改 `align-self:stretch` → dock 撑满 grid 行轨(`minmax(0,1fr)`)→ `.dock-chart` 首帧即有真实高 → `chartEl.clientHeight>0` → `buildSVG` 拿到正确 h。**测量不再恒 0。**

### 层 2:SVG `meet` 缩放兜底（ipo_stage.py:268）—— 物理不可裁
```
<svg viewBox="0 0 W H" preserveAspectRatio="xMidYMax meet"
     style="width:100%;height:100%;display:block">
```
- svg 元素 = `.dock-chart` cell 的 100%×100%(即恒等于 cell rect)。
- `meet` = viewBox 内容**统一缩放到完整落入**元素框(不足则 letterbox),`xMidYMax`=水平居中、**垂直贴底**(0% 基准线在 viewBox 底 y≈H → 贴 YMax → 恒可视)。
- **数学性质**:meet 保证整个 viewBox(含 0% 标签、终点圆点)恒 ⊆ 元素框 → svg 内容永不越界 → `overflow:hidden` 永无可裁之物。**即使层 1 测量仍错(h=fallback),svg 元素仍=cell 尺寸、内容仍 meet-缩放贴合 → 不裁。**

即 round-4 的失效模式(测量→fallback→固定高溢出)被层 2 从原理上消除:现在 svg 尺寸由 CSS/SVG 定(跟随 cell),**与 JS 测量解耦**。

### self-test 44 PASS（Case13 升级)
`PASS [Case13/C45]: dock stretch-fills row + measured buildSVG(w,h) + [140,340] clamp + no-clip meet svg all present`。buildSVG 仍含 0% text(L242)+ 终点 circle(L259),重构未丢元素。node 语法门过(Builder 声明)。
⚠️ 但 Case13 仍是**静态 token 在**级别(查 `align-self:stretch`/`meet`/`viewBox` 字符串存在),**未含渲染后 rect 断言**——同 round-4 假阳性面。**建议 Builder 把 Case13 升级为渲染后运行时断言**(`svg.getBoundingClientRect().height ≤ .dock-chart.clientHeight+2`),否则下次同类回归静态仍漏。真机由本轮探针补。

## 真机 ⚠️ browser_needed
本会话中途**第二个 Chrome 连入**,`tabs_context_mcp` 报「Multiple browsers connected, none selected」。工具硬规则:任何浏览器动作前必须 AskUserQuestion 列出所有浏览器让用户选,**禁 evaluator 自选**(可能操作错误用户的 Chrome)。evaluator 作为后台子 agent 无法解析此选择 → 真机断言交主循环代跑。
- **探针清单**(可直接执行,原始返回值回传裁决):`eval/round-5-browser-probes.md`
  - 探针 A:默认宽逐 charted 行 → `all_no_clip`(svg 高≤cell/底缘≤cell/0% 标签完整落 cell)+ `dock≤footer` + `dock_foot_visible` + `dock_fills_track`(撑满行轨、与左表对称)。
  - 探针 B:窄宽模拟(iframe.style.width=900px,测完恢复)→ narrow 不裁 + 0% 可视 + dock≤footer。
  - 探针 C:C17 末行 + sort ▼ + hover 换行 + console 零错。
  - George 眼验:dock 撑满行轨玻璃视觉正常/无诡异空洞、图表折线+终点+0% 完整无 meet 畸形。
- **裁决门**:探针 A `all_no_clip:true` + B narrow 不裁 + C 溅射全过 + console 零错 → C45 PASS,F3 记入终态。若探针 A 出现任何 `svg_bottom_within_cell:false` 或 `zero_label_within_cell:false` → 仍裁,再打回(带测量值)。

## 结构论证兜底（若真机彻底不可得）
team-lead task#3 授权:窄宽真机不可复现时依赖结构论证。**meet 缩放物理不可裁**(viewBox ⊆ 元素框是 SVG 规范保证)+ align-self:stretch 令 cell 首帧有真高 —— 两层任一独立保证不裁,与宽度无关。故即便真机完全不可得,C45 的「不裁」结论有 SVG 规范级结构证据支撑(强于 round-4 前的纯静态)。但 dock 撑满行轨的**视觉**面(空洞/letterbox 畸形)仍建议 George 眼过。

## 溅射面（未回归,静态+前轮真机)
sort/hover/dock 联动逻辑(_JS_LOGIC 的 sortRows/showDock/hasD1)本修未动;dock 重构只改 CSS + buildSVG 出参。前轮(round-3b)已真机确证 sort/hover/C17/无 console 错;本修不触及该 JS 路径 → 逻辑面不回归(真机 rect 面待探针 C 确认)。F1/F2/F4 不受影响(仅 ipo_stage.py)。

## 结论
- C45 **静态+结构 PASS**,证据强度已达 SVG 规范级(meet 不可裁);**真机核心断言 browser_needed**,探针已备,交 team-lead 代跑 → 绿则 C45 终态 PASS、wave-3 达 ship gate(待 George 眼验 dock 视觉)。
- **本轮不擅自翻 C45 全绿**(守 round-4 教训:静态≠运行时);待真机探针 A/B/C 回值裁决。
