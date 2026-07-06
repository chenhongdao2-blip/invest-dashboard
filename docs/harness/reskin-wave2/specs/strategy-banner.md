# SPEC — 策略开场 Banner · 精修(reskin wave-2)

> 源: DesignSync 26a29f87 `策略开场 Banner.dc.html`(NEW,2026-07-03 拉取;单方案无 1a/1b 变体,无需选版)。
> 目标 = `app/lib/strategy_banner.py`(live_title / overview_strip / dual_track)+ 调用页 `app/pages/4_Strategy_Picks.py:112-137` 的皮肤升级。
> OLD 基线 = 现有实现(非旧版设计稿),delta 表按「NEW 设计 vs 现有代码」;现状详查 `docs/harness/reskin-wave2/current-state.md` §6。
> 通用底座同 kline-reskin:#fff1e5 + Space Grotesk/JetBrains Mono(自托管,theme.FONT_DISPLAY/FONT_MONO)+ 玻璃卡直角。

## 布局(自上而下,NEW 设计 token 级)

1. **页面壳**:`#fff1e5` + 双径向微光(红 900×520 at 10%/-8% rgba(200,16,46,.09) + 青 820×520 at 94%/4% rgba(13,118,128,.10))+ 内容 1240px/padding 0 36px + `font-feature-settings:'tnum','ss01'`。**实现 = 调 `theme.page_radial_wash(1240)`**(theme.py:1022,几何逐值相同,勿重写);页字体 design 全页 Space Grotesk → 站规:**只把 banner 各块显式设 `theme.FONT_DISPLAY`**,不动全局 FONT_STACK(theme.py:83-84 注释明令)。
2. **masthead**(flex space-between align-end,border-bottom 2px #1a1a1a,pb14):左 = 红条 5×34 #c8102e radius1 + H1 32px/36 700 -0.01em(FONT_DISPLAY)。右(gap18):
   - **中/EN 切换**:容器 border 1px #d4c4b0 radius3 overflow hidden;段 mono 11/600/.08em padding 5-12;active bg #c8102e 字 #fff1e5,inactive 透明字 #8a8580。与现 `live_title` seg 逐值一致 → **只换皮不换交互**:保留 `<a href="?lang=zh|en" target="_self">` 真锚点 + 调用页 `st.query_params`→`session_state` 现机制。
   - **TRACKING 徽标**(⚠️ 见 FLAG):青呼吸点 8px #0d7680(cmsiPulse 1.5s:opacity .35 + scale .82)+「实时跟踪 · TRACKING」mono 10/.16em UPPER #0d7680/600;下行 mono 11 #8a8580「更新 {as_of} HKT」mt5。
3. **导语 dek**:14px/1.65 #4a4a4a max-width 880 mt16,关键短语 `<b style="color:#1a1a1a">`(设计 mock 文案 = 缩短版;**文案以现 i18n `strategy.pitch` 双语对为准**,只升级排版,勿用 mock 中文回退双语覆盖)。
4. **速览带节标**(margin 26 0 12):红条 4×16 + mono 12/.16em UPPERCASE #1a1a1a/600「策略速览 · Strategy Snapshot」+ 灰副注 12px #8a8580「自选股日起的真实累计收益 vs 基准(非回测美化)」+ **右浮 counter chip** `margin-left:auto` mono 10/.1em UPPER #8a8580「{N} STRATEGIES」(动态 = len(items),design mock 固定 3)。
5. **三卡速览带**:grid 3 等分,**玻璃配方**(rgba(255,255,255,.55) + blur14 + border 1px rgba(255,255,255,.7) + **border-top 3px #1a1a1a**,同 GLASS_CARD_CSS/ipo-1a KPI 卡);卡间隔 border-right 1px #ebd9c8;卡内 padding 18-20。无 hover 态、无 box-shadow(design 本身没有,不需裁)。
   - **curve 卡 ×2**(生科 5.0 / 港股高股息):头行 = 名 14/600 ink + 右浮「基准 {code}」mono 10 #8a8580;副行 mono 11 #8a8580 mt2「自 {pick_date} · {n} 票」;数值行 mt14 = 大号累计 **mono 32px/36 700 -0.02em tabular**(⚠️ 现实现是 sans 34px → 改 FONT_MONO 32px)+ α chip mono 12/700 padding 2-7 radius2(**沿现 sign-color INVARIANT**:α≥0 青字 bg rgba(13,118,128,.12) / α<0 红字红底,design mock 只画了正例,勿回退 AUDIT-2026-06-30 D1 修复);SVG 280×64(h58 mt12):策略红实线 #c8102e w2 + 渐变面积(#c8102e .16→.01,gradient id 每卡唯一沿现 `"sp_"+hash`)+ 基准灰虚线 #b8b1a8 1.4 dash3-3 + 终点红点 r2.6,双序列共 min/max 对齐(= 现 `_spark_pair`,几何不变);**盈亏点带** mt11 gap3(5px 圆点,盈 #0d7680 / 亏 **#c8102e**,title tooltip「每点 = 一只持仓」);底行 mt10 mono 11 #8a8580「基准 {b}%」左 /「胜率 {w}/{t} · {d}D」右。
   - **IPO 卡**:头行名 + 右浮「六因子 v6.7」mono 10;副行「静态截面 · {n} 样本」;大号中位 mono 32 青 + 「中位首日」11 #8a8580;三行分布条 mt18 gap7(标签 mono 10 w30 + 轨 h8 #ebd9c8 + 填充青/红 **#c8102e** + 值 mono 11/700 w48 右对齐;负值条 anchor `right:50%`);底行 mono 11「已上市 {listed} / 待上市 {pending}」。
6. **双轨导览**:节标同 4(margin 30 0 12,无副注)「如何阅读本页 · 两条策略线」;grid 2 gap16;卡 = **玻璃**(rgba(255,255,255,.5) + blur14 + 白边 .7)+ **border-left 3px #c8102e** padding 18-22;序号 mono 15/700 #c8102e + 标题 15/700 ink(baseline gap9);正文 13/1.65 #4a4a4a mt10,重点 `<b>` ink。
7. **页脚数据纪律条**:mt14 padding 11-16 bg #f9e6d4 12.5px #4a4a4a + 红 tick 3×14 —— **与现实现逐值相同,不动**。

## NEW vs 现有实现 delta(改哪里)

| 区域 | 现有(strategy_banner.py) | NEW 设计 | 动作 |
|---|---|---|---|
| 页面壳 | 无径向微光、全局 Inter | 双径向微光 + Space Grotesk | 调用页加 `theme.page_radial_wash(1240)`;banner 块字体 FONT_DISPLAY |
| masthead 右侧 | 仅 中/EN + 时间戳(TRACKING 已按 George 拍板删) | 恢复 呼吸点+TRACKING 徽标 | ⚠️ FLAG,默认不恢复(见下) |
| 节标(速览/双轨) | 13px sans 600 无字距 | mono 12 UPPER .16em + EN 副题 + 「N STRATEGIES」chip | 换 mono 节标 + 动态 counter |
| 速览带容器 | 实底 PAPER + 1px PAPER_EDGE | 玻璃 rgba .55/blur14/白边 + 顶边 3px INK | 换玻璃配方(inline style,勿借 GLASS_CARD_CSS 类名——那组选择器是 Ticker-Drill 专用) |
| 大号数字 | sans(FONT_STACK)34px | **JetBrains Mono 32px** | 换 FONT_MONO + 32px |
| 亏/跌色(dots、IPO 最差条) | `t.DOWN` #cc0000 | **#c8102e** | 页级换 #c8102e(先例 = candlestick_terminal `_DOWN = theme.CMSI_RED`,CONTRACT O1 page-scope;全局 DOWN token 不动) |
| 盈亏点带数据 | wins/total 伪随机洗牌(`_dots` seed) | design 同为 genDots mock | **升级接真**:调用页 `normed.iloc[-1] > 100` 已有逐持仓真值 → 传逐持仓 sign 列表(按 rank 或收益排序,确定性),`_dots` 只画不造 |
| IPO 最差条宽 | 硬编 2% | mock 2%(worst -4.6% 旧样本) | 按 `max(2, min(|lo|/hi*100, 100))` 归一(对齐中位条公式;live worst -56.9% 时约 15%) |
| 双轨卡 | 实底 + PAPER_EDGE 边 | 玻璃 + 保留红左边 3px | 换玻璃配方 |
| 中/EN、导语、页脚条 | 已与设计逐值一致/仅排版微调 | — | 不动交互;dek 排版按 §3 |

> 参考:NEW vs 旧版设计稿(旧版备份/)的 diff 本身也只有:Inter→Space Grotesk、加径向微光、节标 mono UPPER 化、实底→玻璃、大号数字 mono 32、亏色 #cc0000→#c8102e —— 与上表一致,确认 delta 提取无遗漏。

## MOCK 不移植(design 演示层)

- `curve(n,end,vol,seed)` / `pair(...)` 假净值曲线、`genDots(total,wins,seed)` 假盈亏点 —— **禁移植**;曲线 = `compute_strategy_returns` portfolio + bench rebased=100(现 `_overview_curve_card` 已接),点带 = 真实逐持仓盈亏(上表),IPO 分布 = `load_ipo()` 实算。
- mock 数字全部过期:n=40/20 票、+24.3%/+18.7%、IPO「20 样本/已上市 20/待上市 0/最差 -4.6%」→ live 54 行(38 listed/16 pending),median/hi/lo 实算(现 `_overview_ipo_card` 已接,勿被 mock 数字带偏)。
- 「更新 2026-06-29 16:08 HKT」→ live `_as_of`(现已动态)。
- `sc-for` / `hint-placeholder-count` / `DCLogic` = Claude Design DSL,非可移植代码。
- Google Fonts CDN `<link>`(国内 blocked)→ 自托管 `theme.FONT_FACE_CSS`(已含 Space Grotesk 三族)。
- dek 缩短版中文 mock 文案 → 保留现 i18n `strategy.pitch` 双语对。

## 站规覆盖(违 design / 越 design 处)

- **TRACKING 徽标冲突(唯一需拍板项)**:design(新旧两版都)画了「实时跟踪 · TRACKING」呼吸点;但现实现已按 George 拍板删除(数据 EOD/cron 非实时,docstring strategy_banner.py:47-49)。**默认 = 维持删除,只保留「更新 {as_of} HKT」时间戳**;若 George 要恢复,改文案为非实时口径(如「EOD 跟踪 · DAILY」)再上呼吸点 —— `.cmsi-live-dot` + `@keyframes cmsiPulse` 已在 theme 全局 _CSS(theme.py:741-746,现为孤儿 CSS),DOM 元素补回即可,纯 st.markdown 可动画。**FLAG 需 George 拍板**。
- **渲染机制不变**:banner 无 JS 交互/无 count-up → 维持纯 `st.markdown(unsafe_allow_html)`,**不迁 iframe**;小图维持 inline SVG **禁 echarts**(0 宽竞态站规,current-state.md 横切 INVARIANT 4)。
- **玻璃/微光页级作用域**:kline-reskin CONTRACT P9 明令玻璃与径向微光不得泄漏到别页 —— Strategy Picks 属 wave-2 显式 opt-in 页,radial wash 用 `theme.page_radial_wash()`(页级注入),玻璃写 inline style,**不把 GLASS_CARD_CSS 选择器扩类**。
- **sign-color INVARIANT**:大号累计 + α chip 必须按符号取色(负 = 红,#c8102e 本页口径);design mock 全正例,不代表可硬编青。
- **跌色 page-scope**:#c8102e 只在本页 reskin 表面用作亏/跌;`theme.DOWN`(#cc0000)全局不动(candlestick O1 同例)。
- **无 box-shadow / 无 hover 位移**:design 本身干净,实现勿自加。
- **i18n**:节标「策略速览 · Strategy Snapshot」双语合一按 design;卡内中文硬编字段(「基准/胜率/静态截面/已上市」)现状即硬编 CN —— 维持现状不倒退,若顺手改用 `i18n.t` 需 zh/en 成对新增 key。
