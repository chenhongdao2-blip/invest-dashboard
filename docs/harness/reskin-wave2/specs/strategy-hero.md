# SPEC — 策略表现 Hero · reskin wave-2

> 源: DesignSync 26a29f87 `策略表现 Hero.dc.html`(NEW,2026-07-03 拉取)+ `旧版备份/策略表现 Hero.dc.html`(OLD=现行实现蓝本,2026-06-30 快照,附录 §G)。
> 目标 = Strategy Picks(`app/pages/4_Strategy_Picks.py`)顶部 tearsheet hero(`app/lib/strategy_hero.py` render/#eq;render_compare_chart/#cmp 设计稿未画,保持现状)。
> 通用底座同 kline-reskin:#fff1e5 + Space Grotesk/JetBrains Mono(自托管)+ 玻璃卡直角。
> **单一方案,无多变体,无需 George 选版**(NEW 稿=OLD 的玻璃化+mono 化精修,布局骨架未动)。

## A. NEW 规格(token 级)

### A1. 页面级(iframe body / 页面 chrome)
1. **渐变洗层**(玻璃糊感的垫底,必须有):wrapper `position:relative; overflow:hidden` + absolute inset:0 双 radial —— 左上红 `radial-gradient(900px 520px at 10% -8%, rgba(200,16,46,.09), transparent 60%)` + 右上青 `radial-gradient(820px 520px at 94% 4%, rgba(13,118,128,.10), transparent 60%)`;内容层 `position:relative` 压其上。字体 body='Space Grotesk','PingFang SC','Noto Sans SC';`font-feature-settings:'tnum','ss01'`
2. **页头**(页面层,非 hero iframe):border-b 2px #1a1a1a pb14,flex **center** gap14:**左置红竖条 5×36 #c8102e**(flex:none,r1)+ H1 32px/36 /700 -0.01em「AI Agent 选股 · 策略表现」;右浮 mono 11/.1em UPPER #8a8580「QUANTAMENTAL · 量化基本面」。(OLD 的 H1 尾缀小红条改为左置大红条 = wave-2 masthead 惯例)
3. **策略 tabs / 版本 pills**:设计稿为静态装饰(tabs 加了 mono 字族;pills 同 OLD)——现实现 = `st.tabs` + 页面层版本切换,**不移植假 tabs**(见 §D)
4. **「蓝色释义框 → 编辑部 Note」节**:与 OLD 逐字节相同,已落地为 `theme.note_block()`,勿再移植

### A2. HERO TEARSHEET 卡(本次改造主体)
- **玻璃卡**(直角):`bg rgba(255,255,255,.55)` + `backdrop-filter blur(14px)`(+-webkit-)+ `border 1px rgba(255,255,255,.7)` + **`border-top 3px #c8102e`**(标准 wave-2 玻璃配方,同 ipo-1a);内部 grid `340px 1fr`
- **左栏**(p26-28,flex-col):在玻璃上再加一层白纱 `bg rgba(255,255,255,.35)` + overflow:hidden + relative;**border-right 1px #e4d2bd**(OLD 为 #ebd9c8,加深一档)
  - 顶行:呼吸点 8px **teal #0d7680**(cmsiPulse 1.5s:opacity .35 + scale .82)+ mono 10/.16em UPPER #0d7680/600「持续跟踪 · TRACKING LIVE」(措辞违站规,见 §E)
  - 策略名 20px/600 mt14;副行 mono 11 #8a8580 /.02em mt4「AI AGENT · 自 {pick_date} 建仓」
  - 底部块(margin-top:auto pt28):label **mono** 10/.12em UPPER #8a8580/600「累计收益 · CUMULATIVE」→ 巨号 **mono 56px/60 /700 -0.03em** teal tabular-nums lining-nums mt6(count-up)→ 脚注行 flex gap18 **mt16**:基准(label mono 10/.1em UPPER #8a8580/600「基准 {code}」→ 值 **mono 17px**/600 #4a4a4a tabular mt2)‖(border-l 1px **#e4d2bd** pl18)超额(label mono 10 UPPER **#c8102e**/600「超额 α · ALPHA」→ 值 **mono 17px**/700 teal)
- **右栏**(p18-18-8 relative):角标 abs top18 left22 z2 **mono** 10/.12em UPPER #8a8580/600「净值曲线 · rebased 起点 = 100」;echarts 容器 100%×**300**
- **KPI 7 格带**(grid repeat(7,1fr) border-t 1px #d4c4b0;格 p14-16 border-r 1px #ebd9c8):label **mono 10**/.12em UPPER #8a8580/600 → 值 **mono 17px**/600 tabular mt8。色:选股日/持有天数/夏普/基准=墨 #1a1a1a;胜率=teal #0d7680;**MDD=#c8102e**(OLD 为 #cc0000,见 §E 裁决);持仓数/胜率带灰小分母 11px/500 #8a8580(「/ 评分池 34」「/ 20」——live 用真分母);基准格带副行 10px #8a8580(非 mono)「恒生高股息 30」
- **provenance 行**(卡外 mt8):mono 11 #8a8580 /.02em(live 换真 provenance,见 §D)

### A3. ECharts 净值曲线(#eq)— 与 OLD 逐参数相同,仅 legend 字体换
- canvas;animationDuration **1900ms** cubicOut(draw-in);grid l44 r58 t52 b28
- legend top16 right8 roundRect 18×2 gap18,text 11px #4a4a4a **fontFamily 'Space Grotesk'**(唯一 JS 改动)
- 策略线 #c8102e w2.2 smooth 无 symbol + area LinearGradient rgba(200,16,46,.14→.01) + endLabel「策略 {值}」mono 11/700 红 z3;基准线 #8a8580 w1.5 dashed + endLabel「基准 {值}」mono 11 灰 z2
- x 轴 category boundaryGap:false,axisLine #1a1a1a w1,label mono 10 #8a8580 interval 20,无 splitLine;y 轴 value scale 无轴线,label mono 10,splitLine #ebd9c8
- tooltip:axis + dashed 十字 #b8b1a8;墨底 #1a1a1a 奶字 #fff1e5 mono 11 p8-12;行=marker+系列名+净值+`(+x.x%)` 折算收益

### A4. 动效
- 数字 count-up:rAF **1500ms easeOutCubic**,巨号/基准/α/KPI 全部 0→目标(MDD 补负号、sharpe 2dp)——**保留**,这是真数据的入场动画,不是 mock(§D)
- 曲线 draw-in 1900ms;呼吸点 cmsiPulse 1.5s infinite
- cmsiSweep keyframe 定义了但**未用于任何元素**——勿凭空补

### A5. NEW token 表
| token | 值 | theme 映射 |
|---|---|---|
| 纸底 | #fff1e5 | t.PAPER |
| 玻璃卡 | rgba(255,255,255,.55)+blur14+白边 .7+顶边 3px 红 | 新 CSS(参照 stock_header 玻璃配方) |
| 左栏白纱 | rgba(255,255,255,.35) | 新 CSS |
| 墨/次墨/灰/浅灰 | #1a1a1a / #4a4a4a / #8a8580 / #b8b1a8 | t.INK / INK_2 / INK_3 / INK_4 |
| 分隔线 | 外 #d4c4b0 · 内 #ebd9c8 · 左栏竖线 #e4d2bd | t.PAPER_* 对应 token,勿写死 hex |
| 招商红 | #c8102e | t.CMSI_RED |
| 涨 teal | #0d7680 | t.UP |
| 洗层 | 红 .09 / 青 .10 双 radial | 新 CSS |
| 字体 | Space Grotesk + JetBrains Mono(设计走 Google CDN) | 自托管 t.FONT_FACE_CSS(§E) |

## B. NEW vs OLD delta(设计稿间)

| # | 项 | OLD(=现行蓝本) | NEW |
|---|---|---|---|
| 1 | 正文字体 | Inter(400-800) | **Space Grotesk**(400-700);echarts legend 同步换 |
| 2 | 页面洗层 | 无 | **双 radial 渐变洗**(红左上/青右上)+ overflow hidden |
| 3 | 页头红条 | H1 尾缀 4×24 内联 | **左置 5×36**,flex center gap14 |
| 4 | hero 卡 | 平面:border #d4c4b0 + bg #fff1e5 | **玻璃**:rgba .55 + blur14 + 白边 .7 + **红顶边 3px** |
| 5 | 左栏 | 无底色;border-r #ebd9c8 | +白纱 rgba .35;border-r/内竖线 **#e4d2bd** |
| 6 | 巨号 | 60px/62,无 mono | **56px/60 JetBrains Mono** |
| 7 | 脚注值/KPI 值 | 18px,无 mono | **17px mono** |
| 8 | label 族 | 累计收益/KPI label 9-10px 非 mono | 全部 **mono 化**,KPI label 9→**10px** |
| 9 | MDD 色 | #cc0000 | **#c8102e** |
| 10 | tabs 字族 | 无 mono | mono |
| 11 | 其余 | 布局骨架/呼吸点/pills/chip/note-box/provenance 文案/全部 JS 数据与 echarts 参数 | **逐字节相同**(仅 legend 字体) |

## C. NEW vs 现有实现 delta(改造 to-do,`app/lib/strategy_hero.py`)

现实现 = OLD 的 live-data 忠实翻译(current-state.md §5),故 to-do ≈ §B 映射到代码:

| # | to-do | 落点 |
|---|---|---|
| 1 | `.hero` 卡玻璃化:玻璃配方 + 红顶边 3px(替换现平面 border/bg) | `_CSS` `.hero` |
| 2 | iframe body 加双 radial 洗层(玻璃 blur 的垫底;stock_header 已有同款先例) | `_CSS` body/wrapper |
| 3 | `.hero-left` 加白纱 rgba(255,255,255,.35) + 竖线换 t.PAPER_EDGE(#e4d2bd) | `_CSS` |
| 4 | 巨号 `.big-num` 60→**56px/60** + mono;`.bf-v`/KPI 值 18→**17px** + mono;label 全 mono、KPI label →10px | `_CSS` |
| 5 | echarts legend fontFamily → Space Grotesk(经 json.dumps 的 FONT 变量,勿内联) | `render()` data/JS |
| 6 | 字体栈:iframe 用自托管 Space Grotesk 主导栈(t.FONT_FACE_CSS/FONT_STACK 已随 kline-reskin 升级) | `_CSS.format(FONT=…)` |
| 7 | 页头左置红条(masthead 惯例)属**页面层**(theme.page_header/4_Strategy_Picks),不进本模块 | 页面层,单独小改 |
| 8 | **不动**:mountEChart 契约、count-up data-count 协议、符号染色 `_cum_col/_alpha_col`、json.dumps 字体注入、height 470/#eq 290、`@media 860px` 折行断点、L224-229 渲染 gate、render_compare_chart(#cmp)整体 | — |

## D. MOCK-not-to-port(NEW 稿仍带,一律不移植)

- **`genCurve()` 伪随机净值路径**(102 天、终值 118.7/106.2 钉死)→ **禁移植**;live 曲线 = `strategy.compute_strategy_returns`(portfolio rebased=100)+ `_bench_norm`,由 4_Strategy_Picks L232-245 传入(现状已如此,勿回退)
- **count-up 动效本身保留**——它是真数据的入场动画;禁的是 count-up **目标值**用设计稿硬编数(+18.7%/+6.2%/+12.5pp/20/102/14/-6.3/1.84),live 全实算传参
- 「MOCK 数据(演示)」provenance 片段、「策略 · 提案」chip + demo 说明行 → 删/换真 provenance(`as_of`/`source` 参数)
- 静态 tabs 四 span + version pills 三 span → 现实现 = `st.tabs` + 页面层版本切换(HD v1/v2 双轨),不做 iframe 假 tabs
- 「蓝色释义框」before/after 演示整节 → 已落地 `theme.note_block()`,勿再移植
- 基准钉死 3466.HK/恒生高股息 30、评分池 34、「/ 20」分母 → live 按策略 book 传参(`bench_code/bench_sub/pool/n_total`)
- echarts 未加载 setInterval 100ms 轮询兜底 → 由 mountEChart 契约取代,勿抄回

## E. 站规 overrides(违 design 处,不随 NEW 稿翻案)

- Google Fonts CDN + echarts CDN → **自托管**(`theme.FONT_FACE_CSS` / `ECHARTS_SRC="app/static/echarts.min.js"` **相对路径**,Cloud 前缀坑 INVARIANT)
- echarts 启动必走 **mountEChart 契约**(`echarts_boot.MOUNT_JS`:轮询 lib+非 0 宽、getInstanceByDom 复用、ResizeObserver)
- **「TRACKING LIVE」假实时禁用**(数据 EOD,George 早拍「无假实时 tick/LIVE」):呼吸点可留,措辞改「持续跟踪 · EOD」类(IPO 稿同例=留点改词)
- 巨号/α **按符号染色**(负=红):NEW 稿仍硬编 teal,照样 override(现实现 `_cum_col/_alpha_col` 已修,勿回退)
- **MDD 色微裁决**:NEW 稿 #c8102e(招商红)vs 现实现 t.DOWN(#cc0000,全站「亏损=DOWN」信号色)。默认**照设计取 t.CMSI_RED**;若 Auditor 判信号一致性优先则回 t.DOWN——两者均为红族、不违「红只在 eyebrow/章节/跌」
- NEW 稿无 box-shadow/hover lift(纯 blur 玻璃)→ 无需裁;若实现时手痒加 shadow = 违站规
- 涨 teal #0d7680 / 跌红,单一招商红,无 emoji,tabular-nums,直角——照旧
- theme token 全走 `t.*`(CMSI_RED/PAPER/INK*/UP/DOWN/PAPER_RULE/PAPER_EDGE…),不写死 hex

## F. 现有实现契约(改动时勿破;详见 current-state.md §5)

- `render()`(hero+KPI,#eq,st.iframe h470)与 `render_compare_chart()`(#cmp,h460,v1/v2 对比线)两入口;仅 `4_Strategy_Picks.py` 调用(L232-245 / L485-490),无 spillover
- render 有渲染 gate(L224-229:曲线非空 + len≥10 + sharpe 非退化 + bench 尾非 NaN)——玻璃化不得绕过
- count-up = `[data-count]` 协议 rAF 1500ms easeOutCubic,MDD 强制补负号、sharpe 2dp
- FONT_STACK 必须 `json.dumps` 进 JS(含单引号,内联会炸,注释 L72-75)
- `#eq` CSS 高 290px 固定 + `html,body{height:100%}` + `@media (max-width:860px)` hero-grid 1col/KPI 3col 断点必须保留
- 数据由页面层喂(compute_strategy_returns 单源),hero 不自己抓数

## G. 附录 — OLD 基线 verbatim(=`旧版备份/`,2026-06-30 快照,审计对照用)

### G1. 布局
1. 页头:border-b 2px #1a1a1a pb14:H1 32px/36 /700 + **尾缀红条 4×24**(ml6);右浮 mono 11 UPPER「QUANTAMENTAL · 量化基本面」;下行墨底 chip「策略 · 提案」+ 灰 demo 说明
2. tabs(静态,非 mono)+ 版本 pills(激活红底 mono 12/600;非激活 #f9e6d4 + border #d4c4b0)
3. hero 卡:**平面** border 1px #d4c4b0 bg #fff1e5,grid `340px 1fr`;左栏 p26-28 border-r #ebd9c8:teal 呼吸点+「持续跟踪 · TRACKING LIVE」、策略名 20px/600、巨号 **60px/62 /700(非 mono)** teal、脚注基准 18px/600 #4a4a4a ‖ α label 红 + 值 18px/700 teal(divider #ebd9c8);右栏角标(非 mono)+ echarts 100%×300
4. KPI 7 格:label **9px 非 mono** → 值 **18px 非 mono**;MDD **#cc0000**;余同 NEW
5. provenance 行 + 「蓝色释义框」节(theme.note_block 蓝本):同 NEW
6. 字体 **Inter**(Google CDN)+ JetBrains Mono;echarts CDN 5.5.0;无洗层
7. JS:genCurve mock + count-up 1500ms + echarts option 同 §A3(legend 'Inter')
