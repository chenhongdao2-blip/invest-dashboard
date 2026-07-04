# SPEC — 板块总览 · 报纸精修(wave-2)

> 源: `板块总览 美化.dc.html`(NEW,主循环 2026-07-03 拉取,scratchpad `sector_new.html`;与 Design 项目 26a29f87 线上版核对一致)。
> **基线 = 现有代码** `app/lib/sector_overview.py`(benchmark_table L102 / movers L165,纯 st.markdown + inline SVG,**非 iframe**)+ `docs/harness/reskin-wave2/current-state.md` §4。
> 通用底座同 kline-reskin/ipo-1a:#fff1e5 + Space Grotesk/JetBrains Mono(自托管)+ 玻璃卡直角。
> **单方案设计,无 #1a/#1b 变体 → 无版式「需 George 选版」**;仅 1 个 token 级 FLAG(见站规 §跌色)。
> ⚠️ **SPILLOVER**:本模块是 wave-2 唯一双页共用件(`pages/2_Healthcare.py:152/521` + `pages/a2_ai_overview.py:136/157`),改一处两页齐变,**验收必须两页都过**。

## 布局(自上而下,NEW token 级)

0. **页底座**:bg #fff1e5,字族 'Space Grotesk','PingFang SC','Noto Sans SC';padding 30px 0 70px;`font-feature-settings:'tnum','ss01'`;内容 max-width **1240px** + 左右 36px;外层 `position:relative;overflow:hidden` + **双径向渐变洗底层**(absolute inset 0):`radial-gradient(900px 520px at 10% -8%, rgba(200,16,46,.09), transparent 60%), radial-gradient(820px 520px at 94% 4%, rgba(13,118,128,.10), transparent 60%)`——玻璃卡的糊感垫底,必须有。**现成复用:`theme.page_radial_wash(max_width_px=1240)`(theme.py:1022-1042,kline-reskin 已引入,双 wash 参数与本设计一致)**,页级调用即可,勿在模块里重造。
1. **masthead**(flex 两端对齐 align-end gap24,border-bottom **2px #1a1a1a**,pb16):
   - 左 = 红条 **5×48** #c8102e(radius 1px)+ 标题 **30px/700/-0.01em**「板块总览 · 医疗健康」+ chip(mono 13/600 #8a8580,border 1px #e4d2bd = PAPER_EDGE_SOFT,padding 3px 9px)「HEALTHCARE」;副行 mono 11/.08em #8a8580 mt6「基准 ETF 分档表现 × 涨跌榜 · 30 日趋势 · 相对标普超额」。
   - 右(右对齐)= **青呼吸点** 8px 圆 **#0d7680**(`@keyframes pulseDot` 1.5s ease-in-out infinite;50% = opacity .35 + scale .82)+「EOD · 收盘」mono 10/.16em UPPER #0d7680/600;下行 mt5 mono 11 #8a8580「截至 {asof} · {source}」。
   - 注意:呼吸点是**青色 + EOD 标签**(≠ ipo-1a 的红 BACKTEST 点)——语义 = 收盘快照,不装 LIVE,合 George「无假实时」拍板,保留。勿复用 theme 里孤儿 `.cmsi-live-dot`(current-state §6:该 CSS 已无 DOM 挂点,红色语义也不对),按本设计新做青点。
2. **基准节标**(m 22px 0 10px,flex gap10):红条 **4×16** #c8102e + mono **12/.16em UPPER** #1a1a1a/600「基准 · Benchmark ETF」;右浮(margin-left:auto)色阶图例 =「跌」10px **#c8102e**/600 + 渐变条 120×9(border 1px #d4c4b0,`linear-gradient(to right,#c8102e,#f7d9d9,#fff1e5,#d9e8e6,#0d7680)`)+「涨」10px #0d7680/600 + mono 9 #8a8580「期间收益色阶」。
3. **基准表**:玻璃容器(**rgba(255,255,255,.5) + blur14 + border 1px rgba(255,255,255,.7)**,padding **2px 16px 8px**,overflow hidden,直角,**无顶边 accent**——注意与 `theme.GLASS_CARD_CSS` 配方不同:那个是 rgba .55 + border-top 3px INK,本页设计**没有**墨色顶边,勿直接套)。表 13px tabular-nums:
   - 列:Ticker / 名称 / 趋势 30D / 1日 / 5日 / 1月 / 3月 / YTD / 相对标普 PP(末列居中题)。
   - **th**:bg **transparent**,mono 10/.08em UPPER **#8a8580**/600,padding 9px 12px,**border-bottom 1.5px solid #1a1a1a**;**无任何竖分隔线**。
   - td:h46,padding 0 12px,border-bottom 1px **#ebd9c8**;**行 hover `rgba(26,26,26,.045)`**(需 `<style>` 规则,现代码无 hover)。
   - Ticker mono 12/700 #1a1a1a/.04em;名称 500 #1a1a1a。
   - sparkline:SVG viewBox 110×28(显示 110×26,preserveAspectRatio none),polyline stroke-width 1.5 non-scaling + 终点 circle r2.2;色 = 末值≥首值 ? #0d7680 : **#c8102e**。几何与现 `_spark_svg`(L62)完全一致,只换跌色。
   - 期间格:右对齐,`▲ +x.x%`/`▼ x.x%`/`· x.x%`,字色 #0d7680 / **#c8102e** / #8a8580(0 档),权重 600;底 tint = `rgba(13,118,128|200,16,46, α)`,α = min(|v|/25,1)×0.16,|v|<0.05 → transparent。公式与现 `_tint`/`_pct_cell`(L43/L51)一致,只换跌 rgb(204,0,0 → 200,16,46)。
   - 相对标普格:轨 flex-1 h14 **#f4ead9** + 50% 处 1px 中线 #d4c4b0 + 填充(top/bottom 2px inset)自中线外伸,宽 = min(|v|/25,1)×50%(≥0 → left:50%,<0 → right:50%),色青/红;值 mono 12/700 w54 右「▲ +x.x」/「▼ x.x」。与现 `_rel_bar`(L86)一致,只换跌色。
   - 表下来源行:mono 11 #8a8580 mt8(现 `source=` 参数照旧)。
4. **涨跌榜**:节标(m 34px 0 4px)= 红条 4×16 + mono 12/.16em UPPER「涨跌榜 · Movers」+ 12px #8a8580「1 日涨跌幅前 10」;grid **1fr 1fr gap20 mt14**:
   - 列头(mb8)= 竖条 3×13(涨青/跌红)+ mono **11/700/.1em** 双语「涨幅前 10 · GAINERS」#0d7680 /「跌幅前 10 · LOSERS」**#c8102e**。
   - 玻璃容器(同 §3 配方,无 padding);行 = flex gap12,padding 10px 14px,border-bottom 1px #ebd9c8:tk mono 12/700 w64 → 名称 13px flex ellipsis → last mono 12 #4a4a4a w60 右 → 动量条(轨 **84×16**,涨 `rgba(13,118,128,.10)`/跌 `rgba(200,16,46,.08)`;填充 top/bottom 2px,涨锚 left:0 / 跌锚 right:0,宽 = min(|d1|/22,1)×100%)→ d1 mono 13/700 w58 右「▲ +x.x%」/「▼ -x.x%」(设计带负号;现代码 `abs()` 去号,见 delta)。

## NEW 设计 vs 现有代码 delta 表

现实现 = `app/lib/sector_overview.py`(纯 st.markdown,按 current-state.md §4 校过);masthead 一栏基线在调用页。

| 部件 | 现有代码 | NEW 设计 | 改动位 |
|------|------|------|------|
| 页头 | 页级 `theme.section_header()`(2_Healthcare.py:124 / a2_ai_overview.py:~106),无 masthead | **完整 broadsheet masthead**:border-bottom 2px 墨 + 红条 5×48 + 30px 标题 + domain chip + 副行 + 青 EOD 呼吸点 + dateline | **全新增块**(新函数,双页各自传参) |
| 页底 | 平 PAPER;无 wash | 1240px + 双径向渐变洗 + overflow hidden | 页级调 `theme.page_radial_wash(1240)`(现成) |
| 字体 | FONT_STACK = Inter 系(theme.py:78) | 标题/正文 **Space Grotesk**(mono 不变) | 随 wave-2 全站字族切换 |
| 表容器 | `border:1px solid PAPER_EDGE`(L136) | **玻璃卡** rgba .5/blur14/白边 .7,p 2px 16px 8px,无顶边 | 换容器;≠ GLASS_CARD_CSS 配方 |
| 表头 th | bg PAPER_BAND #f2dfce + 字 CMSI_RED + 底线 1px CMSI_RED + 首末列竖线(L108-116) | **透明底 + mono #8a8580 字 + 墨 1.5px 底线 + 零竖线** | `benchmark_table` th 生成器 |
| 行 hover | **无**(纯 inline style,无 hover 规则) | rgba(26,26,26,.045) | 需注入 `<style>` 块(带 class) |
| 跌色 | `t.DOWN` **#cc0000**;tint rgb 204,0,0(L47);movers 轨 #f6ecec | **#c8102e** 全部件;tint rgb 200,16,46;轨 rgba(200,16,46,.08) | 见站规 FLAG |
| 涨轨底 | #eef2ec 实色(L144) | rgba(13,118,128,.10) | `_mover_row` |
| 节标 | 无「基准」节标(页级 section_header 代管);movers 头 = 3×15 红条 + 14px 中文「涨跌榜 · {window}」(L174-178) | 4×16 红条 + mono 12/.16em UPPER 双语(基准 · Benchmark ETF / 涨跌榜 · Movers)+ 色阶图例右浮 | 节标进模块;图例为**新增**元素 |
| movers 列头 | 12px/.04em「涨幅前 10」「跌幅前 10」(L167-170) | mono 11/700/.1em「… · GAINERS / LOSERS」 | `movers.col()` |
| movers d1 | `{gly}{abs(d1):.1f}%` → 「▼ 16.0%」(L161) | `▼ -16.0%`(带负号) | 微调格式(跟设计) |
| 呼吸点/dateline | 无 | 青 EOD pulse + 截至/来源(masthead 右) | 新增,`@keyframes` 注入 |
| **不变** | sparkline 几何(110×28/1.5/r2.2)、行高 46、行线 #ebd9c8、rel 条几何(h14/#f4ead9/中线/cap 25→50%)、期间格 glyph+tint 公式(cap 25→α.16、死区 .05)、mover 行宽(64/flex/60/84/58)与 cap 22、UP #0d7680、列清单与列序、`rows/gainers/losers` 数据契约 | 同左 | **勿动**;公共 API 签名可保持 |

## MOCK 行为(不移植)

- `spark(end, seed)` 伪随机游走 30D 路径——现实现已用真实收盘(`bm.close_series()` tail 30),**保持真数据**。
- `renderVals()` 硬编 6 ETF 行 + 4 涨/4 跌——live = 页面各自数据(Healthcare focus = XLV/XBI/XPH/IXJ/IHF/IHI;AI = ^SOX/SMH/AIQ/512480.SS/515880.SS/442580.KS;movers 全域 top-10)。design 第 6 行 **IGV「美国科技软件」出现在医疗 mock 是错位**,勿照抄行清单。
- 脚注「… · MOCK 走势(演示)」→ 真 provenance(现 `source=` 参数已接 `db.latest_snapshot_date()`,沿用)。
- 「截至 2026-06-29 · Yahoo Finance」硬编 → masthead dateline 用真实 as-of + 真 source(AI 页来源不同,参数化)。
- design movers 每侧只画 4 行(hint-placeholder-count=4)但题写「前 10」→ live 照现状出 10 行。
- Google Fonts CDN `<link>` → 不移植(见站规)。

## 站规覆盖(违 design 处 / 集成约束)

- **字体 CDN → 自托管**:theme.FONT_FACE_CSS(theme.py:160)已含所需字族(国内 CDN 挂,kline-reskin 同款处理)。
- **跌色 FLAG(需 George 拍板)**:NEW 把跌红从 t.DOWN **#cc0000** 全面换成 brand **#c8102e**,与 wave-2 ipo-1a 口径一致(青 #0d7680 涨/红 #c8102e 跌);但 theme.py:58 注释明确 DOWN=#cc0000「signal-red, distinct from brand」,且本模块双页共用。**建议**:按 design 走 #c8102e,以模块内常量或 theme 新 token 实现,**勿全局改 t.DOWN**(避免牵连未 reskin 页面);全站是否迁移由 George 定。teal=涨/红=跌语义(cross-cutting INVARIANT #1)不动。
- **masthead 参数化**:design 按医疗页画(「板块总览 · 医疗健康」/HEALTHCARE/该副行),但模块双 domain 共用(memory: multi-industry not healthcare-only)→ 标题/chip/副行/dateline 来源全参数化;沿用现模块「caller 传预本地化字符串」的 i18n 模式(current-state §0 风格 b),或补 locales key——movers 列头等中文硬编的双语化随本次一并处理(现状「不完全双语」是已知短板)。
- **呼吸点保留**:青点 +「EOD · 收盘」= 明示收盘快照,不违「无假实时 tick」拍板;en 版「EOD · CLOSE」。
- **无 box-shadow**:NEW 全页无 shadow(只 backdrop-filter + 白边),无需裁剪;本页也无 hover-lift(对照 ipo-1a KPI hover 被裁的情况)。
- **实现载体不迁 iframe**:NEW 无 JS 行为(纯静态 + CSS hover/keyframes),现 st.markdown 方案继续成立(cross-cutting INVARIANT #4:小图面必须 inline SVG,勿换 echarts);`@keyframes pulseDot`、`tr:hover`、`backdrop-filter` 经 `<style>` 块注入。**玻璃糊感前置条件**:容器底下必须有径向渐变洗 → 页级 `theme.page_radial_wash(1240)`,否则 blur 无物可糊。
- **表保持 DOM**(不进 canvas)——现注释「可排序」诉求不变;NEW 未引入排序交互,不新增。
- **双页回归验收**:Healthcare 与 AI overview 两页都要真机眼验(唯一多页模块,current-state spillover 表)。
