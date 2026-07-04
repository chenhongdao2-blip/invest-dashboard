# SPEC — 行情中枢 Hub · 新版精修(wave-2)

> 源: DesignSync 26a29f87 `行情中枢 Hub.dc.html`(新版,主循环 2026-07-03 代拉落盘);旧版 = `旧版备份/行情中枢 Hub.dc.html`,内容从 2026-06-30 transcript 的 get_file 结果恢复(当时 root 路径即现旧版,byte 完整含 `</html>` 结尾,`truncated:false`)。
> 目标 = home.py 行情中枢首屏:页级 masthead(theme.page_header 区)+「市场总览」指数瓦片 strip(lib/market_hub_tiles.py)。
> **单一设计,无多变体,无需 George 选版。** 新旧两版 DOM 结构逐行同构,delta 是「精修层」:字体/氛围/玻璃/mono 化,不是重排版。

## 布局(自上而下,新版 token 逐值)

0. **页级氛围层**(新增):外层 wrapper `position:relative;overflow:hidden;bg #fff1e5;color #1a1a1a;font 'Space Grotesk','PingFang SC','Noto Sans SC';padding 32px 0 70px;font-feature 'tnum','ss01'`;其上盖一层 absolute inset:0 双 radial 水彩:`radial-gradient(900px 520px at 10% -8%, rgba(200,16,46,.09), transparent 60%), radial-gradient(820px 520px at 94% 4%, rgba(13,118,128,.10), transparent 60%)`(左上红晕 + 右上青晕)。内容容器 `max-width 1240px;margin 0 auto;padding 0 36px`(旧 1280 → 新 **1240**;Streamlit 页宽全局控,此条 advisory)
1. **masthead**(flex align-end space-between gap20;border-bottom 2px #1a1a1a;pb 14):
   - 左 = flex gap14:**红条 5×44 #c8102e radius 1px**(旧版是 h1 尾随 4×24 红点,新版改左侧通栏条)+ 竖排两行:h1「行情中枢」**30px/34px/700 -0.01em #1a1a1a**(旧 32/36)→ 下行 **mono kicker**(新增)`CMSI · MARKET HUB · 四大指数总览` JetBrains Mono 11px/.08em #8a8580 mt5
   - 右 = 呼吸点 8×8 圆 **#0d7680** anim `cmsiPulse 1.5s ease-in-out infinite`(50%: opacity .35 + scale .82)+「实时跟踪 · TRACKING」mono 10/.16em UPPER #0d7680/600;下行 mono 11 #8a8580「EOD 2026-06-29 · 08:42 HKT」——**⚠ TRACKING 徽标 George 已拍板去掉(EOD/cron 非实时),设计残留,勿回归**;右侧降级为纯 EOD 时间戳行(live 值)
2. **eyebrow 节标**(flex baseline gap10;margin 24 0 12):红 tick 4×16 #c8102e + 标题改 **mono 双语 smallcaps**:`市场总览 · Market Overview` JetBrains Mono **12px/.16em UPPER #1a1a1a/600**(旧 = sans 13px/600 纯中文)+ 副注 12px #8a8580「四大指数 · 30 日走势 + 52 周区间」+ 右浮 mono 10/.1em UPPER #8a8580 渲染器标签(设计写 ECHARTS;实现为 SVG → 标签与实情一致写 `SVG`)
3. **指数瓦片 strip**(设计=内嵌 iframe 268px,#row 248px;现实现=单 st.iframe srcdoc,同):
   - 内层画布 bg(新增):`radial-gradient(700px 320px at 8% -20%, rgba(200,16,46,.09), transparent 60%), radial-gradient(700px 320px at 94% -10%, rgba(13,118,128,.10), transparent 60%), #fff1e5`(给玻璃提供可 blur 的底)
   - **#row 玻璃容器**(headline delta):`display:flex;border:1px solid rgba(255,255,255,.7);border-top:3px solid #1a1a1a;background:rgba(255,255,255,.55);backdrop-filter:blur(14px);height:248px`;末瓦片去右边框(旧 = 实心 #fff1e5 + 1px #d4c4b0 边、无顶墨条、无玻璃)
   - 瓦片 ×4(flex:1;p 18 20;border-right 1px #ebd9c8;min-width 0),内部自上而下:
     a. 头行 flex space-between:指数名 11px/.06em/600 #8a8580 + 红 tick 4×12 #c8102e
     b. 现价:**JetBrains Mono 32px/38px/700 -0.02em #1a1a1a tabular-nums mt8**(旧 = Inter 34/40/600 —— 数字全面 mono 化)
     c. 当日涨跌:mono 13/700 mt2,涨 #0d7680 / 跌 **#c8102e**(旧 #cc0000;见站规裁定)
     d. sparkline 46px 高 mt8:设计 = echarts line width1.8 smooth,area 渐变 涨 rgba(13,118,128,.22)→.01 / 跌 rgba(200,16,46,.20)→.01,anim 900ms cubicOut;**实现保持内联 SVG**(protected 决策,见站规)
     e. 52 周区间 bar mt6:轨 3px #ebd9c8;teal #0d7680 填充至 pos%;墨标 2×9 #1a1a1a @pos(top -3);下行 flex-between mono 9px #b8b1a8「52W {lo}」/「{hi}」mt5
     f. 情境行 mt8:mono 10/.04em UPPER #8a8580「1M {±x.x%} · YTD {±x.x%}」,值按符号染色(涨 #0d7680/跌 #c8102e→站规裁定)
4. **脚注**:mono 11 #8a8580 mt8「SOURCE: Yahoo Finance cron EOD · 截至 {date} · 仅供参考」(设计含「MOCK 走势(演示)」字样,live 删)

## NEW-vs-OLD delta 表(驱动 build)

| # | 区块 | 旧版(现代码基线) | 新版 | build 动作 |
|---|------|------|------|------|
| 1 | 字体 | Inter 主字 | **Space Grotesk** 主字(mono 不变) | strip/masthead 换 theme.FONT_DISPLAY(自托管已有);全站 FONT_STACK 不动 |
| 2 | 页级氛围 | 无 | 外层+内层各一组**双 radial 红/青水彩**(token 见布局 0/3) | 新增;页级层需 st.markdown 注 .stApp,或降级只做 strip iframe 内层版(见交互注) |
| 3 | masthead 左 | h1 32px + 尾随红点 4×24 | 红条 **5×44 r1** 前置 + h1 30px + **mono kicker「CMSI · MARKET HUB · 四大指数总览」** | home.py page_header 区改造(或 home 专属 header 变体);kicker 文案 live 化 |
| 4 | eyebrow 标题 | sans 13/600「市场总览」 | **mono 12/.16em UPPER 双语「市场总览 · Market Overview」** | market_hub_tiles eyebrow CSS 改 |
| 5 | 瓦片容器 | 实心 #fff1e5 + 1px #d4c4b0 | **玻璃 rgba(255,255,255,.55) + blur14 + 白边 .7 + 顶边 3px 墨** | #row/.grid 换玻璃配方(与 kline/ipo wave 同族) |
| 6 | 现价字 | Inter 34/40/600 | **mono 32/38/700** | .tval 改 FONT_MONO + 缩 2px 加粗 |
| 7 | 跌色 | #cc0000(=theme.DOWN) | **#c8102e 全面**(chg/spark/1M/YTD) | ⚠ 站规冲突,默认**保 #cc0000**,见站规节 |
| 8 | 容器宽 | 1280 | 1240 | advisory,Streamlit 全局宽不由本块控 |
| — | 瓦片内部结构/间距/tick/52W bar/脚注 | 同 | 同(逐值无变) | 不动 |
| — | TRACKING 呼吸徽标 | 有(George 拍板已删) | 设计仍有 | **继续不做**,右侧只留 EOD 时间戳 |

**现代码 v2 增量的处置**(旧设计之外、George 已验收的自加项,新设计既未画也未否定 → **全部保留**,Auditor 勿报 diff):市场速读 dek(真实 N涨M跌+领涨领跌)、现价 count-up、瓦片 staggered fade-rise、SVG spark draw-in、prefers-reduced-motion 降级、中英 i18n 双语、52W 窗口 <330d 不标注护栏、缺数占位保高度。

## 交互

- 无 hover/点击交互;纯展示 strip。动效 = 入场一次性(现 v2 的 draw-in/rise/count-up 保留),**不做**任何暗示实时的循环动画(cmsiPulse 随 TRACKING 一起不做)。
- 玻璃 blur 要有底可 blur:内层画布必须带水彩层(布局 3 内层 bg),否则 blur(14px) 对纯色底不可见。
- 页级水彩(布局 0)如注 .stApp 成本/风险高(全局 CSS 污染其他页),可接受降级 = 仅 strip iframe 内实现内层水彩;masthead 区水彩舍弃。标注给 George:降级不影响玻璃观感主体。
- strip 仍 = 单 st.iframe 自包含 srcdoc(现架构不变)。

## 数据接真(design MOCK → live)

- `indices()` 硬编码 4 组快照(7,354.02/-0.05 等)= MOCK → live `bm.fetch_benchmarks()` broad_market(^GSPC/^NDX/^HSI/000001.SS),home.py 已接好,复用现 `_tiles` 组装。
- `curve(n,end,seed)` 种子伪随机游走 sparkline = MOCK → live `bm.close_series()` 近 30 真实收盘(现 `_spark()`)。**禁止移植伪随机曲线**。
- echarts CDN `cdn.jsdelivr.net/npm/echarts@5.5.0` = 设计便利 → **不引 CDN**(国内网络站规)。spark 渲染**维持内联 SVG**:protected 决策(grid 0 宽 echarts.init 竞态 + 全站 sparkline 统一 SVG,见 market_hub_tiles.py 头注);若未来非要 echarts,必须走自托管 `app/static/echarts.min.js` + echarts_boot.mountEChart,本轮不动。
- 「实时跟踪 · TRACKING」+ cmsiPulse = 假实时暗示 → 已拍板删除,live 右侧 = `EOD {latest} · {fetch_utc}` 真值。
- 「EOD 2026-06-29 · 08:42 HKT」硬编码 → `db.latest_snapshot_date()` + `db.last_fetch_utc()`。
- 脚注「MOCK 走势(演示)」→ 现 foot 文案(来源 Yahoo Finance cron EOD · 截至 {latest} · 仅供参考,中英随 i18n)。
- 右上「ECHARTS」标签 → 与真实渲染器一致写 `SVG`(现状),不虚标。

## 站规覆盖(违 design 处)

- 字体 Google Fonts CDN(Space Grotesk + JetBrains Mono)→ 自托管 theme.FONT_FACE_CSS(三族已含,Space Grotesk = FONT_DISPLAY,勿换全站 FONT_STACK)。
- **跌色**:设计把跌统一成品牌红 #c8102e;站规 = 涨青 #0d7680 / 跌 #cc0000(theme.DOWN,与品牌红语义分离)。默认**保 #cc0000**;若 George 想要设计的品牌红跌,需显式页面豁免——标注「需 George 裁:跌色 #cc0000 vs #c8102e」,未裁前按站规。
- TRACKING 呼吸徽标 → 站规级既有拍板(EOD 数据不装实时),不随新版回归。
- radius:红条 r1、呼吸点 50%(8px 圆=4px 实效)均 ≤4 ✓;无 box-shadow ✓(设计本身无 hover 阴影);无 emoji ✓。
- 玻璃 backdrop-filter blur14 = wave-2 全站玻璃配方同族,合规。
