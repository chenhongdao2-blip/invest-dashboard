# SPEC — 港股IPO打新 · 1a 报纸精修(George 拍板 2026-07-03)

> 源: DesignSync 26a29f87 `港股IPO打新 美化.dc.html` #1a(2026-07-03 拉取)。目标 = Strategy Picks 第 4 tab(render_ipo_strategy)整体重实现。
> 通用底座同 kline-reskin:#fff1e5 + Space Grotesk/JetBrains Mono(自托管)+ 玻璃卡直角。

## 布局(自上而下)
1. **masthead**(border-bottom 2px #1a1a1a, pb 16):左=红条 5×48 #c8102e + 「港股 IPO 打新」30px/700 + chip「CMSI 棱镜六因子 v6.7 · 策略后测」(mono 13/600 #8a8580 border #e4d2bd p3-9);副行 mono 11/.08em #8a8580「评分档 × 首日表现 · 样本 n={N} · 评分擅长判方向,不擅长测涨幅」。右=红呼吸点 8px #c8102e(pulseDot 1.5s:opacity .35 + scale .82)+「BACKTEST · 后测」mono 10/.16em UPPER #c8102e/600;下行 mono 11 #8a8580「截至 {date} · CMSI / futu / iFind」
2. **KPI 三卡** grid 3 等分 gap14 mt22,玻璃配方(rgba .55/blur14/白边),顶边 3px:样本=墨 #1a1a1a、最高首日=青 #0d7680、最差首日=红 #c8102e。内部:label mono 10/.12em UPPER #8a8580/600 → 值 mono 48px/700 -0.02em(色随卡)→ 脚注 mono 11 #8a8580(样本卡=「已上市 X · 待上市 Y」;best/worst=「{名} · {档}」)。design 有 hover translateY+shadow(style-hover)——**违站规 no box-shadow,裁掉 hover 态**
3. **分档表现节**:节标(红条 4×16 + mono 12/.16em UPPER「分档表现 · TIER PERFORMANCE」+ 灰副注「评分越高越好吗?—— 两端拉得开,中间三档拉不开」);玻璃容器(rgba .5/blur14/白边,无顶边)内表格 grid `150px 70px 1fr 110px 90px` gap12:表头 mono 10/.1em UPPER #8a8580,底线 1.5px #1a1a1a;行 border-b 1px #eadbc8:档位 chip(见色系)/只数 mono 13/600/中位首日=条形(轨 160×8 rgba(26,26,26,.06),填充按 |中位|/max 比例,色=涨青跌红)+值 mono 13/700 同色/收涨率 mono 13/600 #4a4a4a/破发 mono 13/700(0=灰 #8a8580,>0=红 #c8102e);脚注 mono 10.5 #8a8580 读法行
4. **评分排行 + 走势台**:节标同上「评分排行 · SCORE RANKING」+ 副注「hover 任意行 → 右侧浮出该股首日盘中大图」;grid `1fr 400px` gap20:
   - 左表玻璃容器:grid `36px 56px 140px 56px 104px 1fr 92px`(#/代码/名称/评分/申购档/子板块/首日涨幅右对齐);表头同上;行 p7 border-b #eadbc8,hover bg rgba(200,16,46,.06)(选中行常驻同色);rank mono 12 #8a8580 补零两位;名称 13.5/700;评分 mono 13/700;档 chip 9.5px;首日 mono 13/700 涨青跌红
   - 右 dock **sticky top16**:玻璃加强(rgba .6/blur16/白边 .75/顶边 3px 墨)p20-22:头行=名 19/700 + code chip + 档 chip(右浮);涨幅 mono 38/700 色随向;副注 mono 10/.08em「首日盘中 · 相对发行价 % · 终点 = 首日收盘」;**SVG 356×200**:3 条横网格 #eadbc8 + 0% 盈亏线(#8a8580 dashed 4-4 op.65 + 标签 mono 9)+ area fill(线色 α.10)+ path(线色 stroke-width 2)+ 终点 circle r4;底行(border-t #eadbc8)mono 11 #8a8580:区间高 {max} · 区间低 {min} · {来源}
5. **页脚注框**:border 1px #e4d2bd + bg rgba(255,255,255,.4) p12-18 mono 10.5/1.7 #8a8580:「提示 · 后测口径 — 首日表现为上市当日定档快照,不随后续行情更新;本页为策略后测(backtest),非实时盯盘工具。…仅供内部研究回测,不构成投资或申购建议。」

## 档位色系(design 内嵌 tierColors)
重点申购+ `#a00d25` / 重点申购 `#c8102e` / 推荐申购 `#0d7680` / 谨慎申购 `#a06d1f` / 不申购 `#6b6560`;chip = color 字 + 1px 同色边 + bg rgba(color,.07~.08)。涨跌:青 #0d7680 涨 / 红 #c8102e 跌(colorScheme 默认青涨红跌;flat=#8a8580)

## 交互(必须单 iframe 自包含实现)
hover 排行任一行 → 右 dock 切换为该股(mouseenter,无点击);默认选中 rank 1。表+dock 必须同一 st.iframe srcdoc 内(跨 iframe 无法 hover 联动)。曲线 = 纯 SVG path(design 用 Catmull-Rom 平滑),无需 echarts。

## 数据接真(design MOCK → live)
- design n=20 是旧快照;live = load_ipo() 54 行(listed 38/pending 16),KPI 样本卡 = 54 + 「已上市 38 · 待上市 16」动态;best/worst 从 listed day1_ret 实算(曦智 +384% / 华健未来-B -56.9% 按现数据)
- 分档表现 5 行从 listed 实算(中位/收涨率/破发数,按档位含重点申购+ 分档);条形按 |中位|/max 归一
- 排行表 = 全 54 行按评分降序(pending 行:涨幅列 「—」、名称不拖日期、**保留 2026-07-03 新增的上市日期列**——George 当日点名要的,design 未画但保留为附加列,契约标注)
- 盘中路径:`load_ipo_intraday()`(ipo_day1_intraday.csv,仅早期 ~17 只有 5min 路径)。有路径→真实路径 SVG;无路径(新补录 18 只/pending)→ dock 显示「盘中路径未采集 · 仅首日收盘」+ 首日收盘平线或空态;**禁止用 mock 正弦抖动伪造路径**(design 的 genData/抖动仅演示)
- 来源列/来源字段用 CSV source 列真值;截至日期用数据实际 as-of
- **superseded 现有功能**(契约声明,Auditor 勿报):现小图墙(intraday small-multiples)、按评分/按首日排序 toggle、render_html_table 版排行表 → 全部被 1a 设计取代(dock hover 即大图;表固定评分序)

## 站规覆盖(违 design 处)
- KPI 卡 hover translateY + box-shadow → 裁(no box-shadow 站规)
- 字体 Google Fonts CDN → 自托管(theme.FONT_FACE_CSS 已含三族)
- MOCK 数据/演示脚注 → 真数据 + 真 provenance
