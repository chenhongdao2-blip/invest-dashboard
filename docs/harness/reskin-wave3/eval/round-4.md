# WAVE-3 ROUND-4 定向复验（Evaluator）— C45 dock 双宽度眼验

- 触发：C45(CONTRACT §2.5,George 眼验修正案)—— dock 恒不压 footer + 图表按容器实测尺寸绘制。Builder 落 dock 有界 flex 列 + buildSVG(w,h) 两步测量渲染(仅 ipo_stage.py,自测 44 + node --check)。
- 范围(team-lead 指派):重启冒烟 → 自测 44 → **真机双宽度**(默认宽 + resize 窄宽) → 溅射(sort/hover/C17/console)。

## Round-4 verdict:**C45 ❌ REJECT（打回 Builder）** —— dock 结构有界达标,但「按容器实测尺寸绘制」机制失效,图表被裁 125px、0% 轴标签不可见

> 我验收时 ipo_stage.py 自测 = **44 断言**(含 Case13)——已锚最终树。

### 判据拆解(默认宽,真机 iframe 1062px)
| C45 子判据 | 结果 | 证据 |
|---|---|---|
| `dock.bottom ≤ footer.top`(严格不重叠) | ✅ PASS | dock.bottom=1002 ≤ footer.top=1026(24px 间隙);overflow:hidden 夹住 dock —— **George 原始「dock 压 footer」已修** |
| dock 脚注(区间高/低行)可见 | ✅ PASS | "区间高 +433.7% · 区间低 +343.3% · 来源…" flex:none 恒显 |
| **图表无文本变形 / SVG 不被裁 + 0% 标签可视** | ❌ **FAIL** | 见下 |

### ❌ 核心缺陷:SVG 恒画 280 fallback,在 155px chart cell 被裁 125px
**真机实测(默认宽,4 个 charted 行全中)**:

| code | chart cell clientHeight | svg height 属性 | overflow(裁切) | 0% 标签可视 |
|---|---|---|---|---|
| 1879 | 155 | **280** | **+125px** | ❌ 否 |
| 7666 | 155 | 280 | +125px | ❌ |
| 7688 | 155 | 280 | +125px | ❌ |
| 3310 | 155 | 280 | +125px | ❌ |

`all_280:true / any_clipped:true` —— **每一个 charted 行的 SVG 都画成 280(fallback 值),而真实 chart cell 只有 155px,底部 125px(含 0% 基准线标签)被 `.dock-chart overflow:hidden` 裁掉**。zero_label_bottom=1051 > chart_bottom=949 → 0% 轴标签落在可视区外。

### 根因(先审 diff 后定位)
`.dock` = `align-self:start`(内容定高)+ `.dock-chart` = `flex:1 1 auto; min-height:0`(ipo_stage.py:135-138)。两步渲染(showDock 395-414):
1. step1 插空骨架 `<div class="dock-chart"></div>`;
2. step2 读 `chartEl.clientHeight` → **在 align-self:start 的内容定高容器里,空的 flex:1/min-height:0 子元素塌成 0**(flex-grow 无自由空间可分)→ `chRaw=0` → 走 `else 280` fallback(L412)→ `buildSVG(...,cw,280)`。
3. SVG(280)插入后,dock 的 `max-height:100%` 把 dock 夹到 grid track(minmax(0,1fr)),chart cell 被压到 155,SVG 溢出 125px 被 overflow:hidden 裁。

即 C45 承诺的「按容器**实测**尺寸绘制」未兑现 —— 实测恒为 0,恒退化到 280 fallback。**self-test Case13 静态查 token 存在(`clientHeight`/`buildSVG(w,h)`/`[140,340]`)全 PASS,但查不到运行时 clientHeight=0→fallback 的实际行为**(同 wave-1 echarts 静态探针假阳性陷阱:静态 token 在 ≠ 运行时正确)。

### 双宽度说明(诚实降级)
`resize_window` 在本环境**不改 rendered viewport**(parent `innerWidth` 恒 1512,iframe 恒 1062,窄宽 rect 与默认宽逐字节相同)→ 真窄宽未能复现。但缺陷 **width-independent**(fallback 恒触发,与宽度无关),**默认宽即裁**,窄宽(cell 更小)只会更糟。C45 primary(dock≤footer)由 `max-height:100%+overflow:hidden` 结构保证,任意宽度成立。

### 溅射面(未回归,供 Builder 定位 scope)
- self-test **44 PASS**(含 Case13);重启 :8599 四页 200。
- sort ▼ 首 +384.0%(max) / hover 2 异行无 stale / C17 末行(宝盖新材)dock 不压 footer+可视 / **无 console JS 错**。
- dock 重构**只坏了图表尺寸**,排序/hover/dock 联动/末行可视全过。

## 打回 Builder — 修法方向
测量被 `align-self:start` 空骨架 defeat,fallback 280 在正常态就超真实 cell(155)。选项:
- **(a) 推荐:buildSVG 输出 `width:100%;height:100%` + viewBox**(纯 CSS 缩放,SVG 恒贴合 .dock-chart cell,零 clientHeight 测量、零竞态)——最稳。
- (b) `requestAnimationFrame` 内测量(等 max-height clamp 解析后再画)。
- (c) 去掉 `.dock align-self:start` 让 dock 撑满 grid track,给 chart 稳定可测高。
- (d) 插 SVG 后二次测量 settled cell,超则 rescale。
- **验收补强**:Case13 需从「静态 token 在」升级为「渲染后断言 `svg.getBoundingClientRect().height ≤ .dock-chart.clientHeight + 2`」(运行时,非静态),否则同类假阳性会再漏。

## 影响
- **C45 FAIL → wave-3 未达 ship gate**(C45 是 [HIGH·George 眼验] 项)。
- F3 原列项(C16-C29/C37-C40 + Codex C1/C2/M3/KPI 残留)**仍绿未回归**;F1/F2/F4 不受影响(本修仅 ipo_stage.py)。
- 断路器:C45 是 Stage-5 眼验增补项,新缺陷,需打回再修;非原 max-3-cycle 内。
