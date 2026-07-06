# SPEC — 个股热力图 · Treemap 精修(wave-2)

> 源: DesignSync 26a29f87 `热力图 Treemap.dc.html`(2026-07-03 拉取,主会话转存 scratchpad/treemap_new.html,9379B)。**单版设计,无 #1a/#1b 变体,无需 George 选版**。
> 目标 = home Market Hub 热力图原位升级:`app/lib/heatmap_treemap.py::render_treemap_html`(唯一调用点 `app/home.py:178`,per-domain 循环 st.iframe)。
> OLD 基线(主循环拍板 2026-07-03):`旧版备份/热力图 Treemap.dc.html` **不再拉取**。OLD = 现码 `app/lib/heatmap_treemap.py`(wave-1 落地代码/07 的落地版)+ 现状勘察 `docs/harness/reskin-wave2/current-state.md` §3(签名/payload 形状/调用点/INVARIANTs 已落盘,本 spec 直接引用)。delta 表 = NEW 设计 vs 现码。
> 通用底座同 kline/ipo-1a:#fff1e5 + Space Grotesk/JetBrains Mono(自托管)+ 直角。

## 布局(单 st.iframe srcdoc 内,自上而下)

1. **页壳**:cream #fff1e5,字族 display=Space Grotesk 栈(theme.FONT_DISPLAY),`font-feature-settings:'tnum','ss01'`,`color-scheme:light`;**双 radial gradient 洗层**(absolute inset 0):`radial-gradient(900px 520px at 10% -8%, rgba(200,16,46,.09), transparent 60%), radial-gradient(820px 520px at 94% 4%, rgba(13,118,128,.10), transparent 60%)`;内容容器 max-width 1240 居中 + 左右 padding 36(嵌 Streamlit 主栏时可视宽度已受限,max-width 允许按容器实况裁,gradient 洗层保留)
2. **masthead**(border-bottom 2px #1a1a1a,pb 12;flex space-between align-start gap 20 wrap):
   - 左:红条 5×44 #c8102e(radius 1)+ 同行 gap10:H1 26px/700 ls -0.01em #1a1a1a「个股热力图 · Market Map」+ **CMSI chip**(mono 10/700,#fff1e5 字 on #c8102e 底,p 2-7,ls .06em);副行 mono 11 ls .06em #8a8580 mt5:「面积 = 市值 · 颜色 = {win} 涨跌方向与幅度 · 子行业分块」(design 写死 1D → live 随 window 段控 1D/5D/1M)
   - 右(**渐变图例**,新元素,text-right):label 10/600 #4a4a4a mb4「颜色 = 涨跌方向与幅度」;渐变条 190×12,border 1px #d4c4b0,`linear-gradient(to right,#a30000,#d23b3b,#efe2cf,#2f8a8f,#0a5a62)`(= _ramp 五锚点,红→米→青,与 ramp 严格同源),两端字 11/700:跌=#a30000 / 涨=#0a5a62,gap6;刻度行 width190 mono 9/600 #8a8580 两端+中:「-12%」「0」「+12%」(±CAP=12 同步)
3. **惯例 banner**(margin 10 0 4,p 7-12,bg #f9e6d4,border-left 3px #c8102e,11.5px #4a4a4a,flex gap8):「**本图配色(港美股惯例):**」b #1a1a1a;「青绿 = 涨」#0a5a62/700 · 「红 = 跌」#a30000/700;「**(与 A 股红涨绿跌相反,请注意)**」b #1a1a1a;右侧 margin-left:auto 10.5px #8a8580「面积 = 市值(龙头最大) · hover 看名称/市值」。**无 ⚠ 前缀**(NEW 删;现码的 ⚠ 字符一并删)
4. **域条**(新元素;flex baseline gap11,bg #f9e6d4,border-left 3px #c8102e,p 8-13,margin 12 0 2):域名 16/700 #1a1a1a(如「医疗 Healthcare」= payload cn/en 双语并排或按 prefer_cn,见数据节);右 margin-left:auto mono 11/700 #4a4a4a「中位 {median:+.1f}% · {n_total} 标的」(中位/标的数从 masthead 右侧迁到此)
5. **treemap 画布**:高 700px(design iframe height:700;现码 #m = height-90。live 取 height 参数下的 ~700,多域竖叠模式可维持现 600/720 逻辑等比)
6. **来源脚注**:mono 11 #8a8580 ls .02em mt6:「SOURCE: {source} · 市值 USD · 截至 {as_of} · 面积=市值 / 颜色={win} 涨跌」(design 的「MOCK 数据(演示)」删)

## ECharts option(token 级;不变项显式声明防回归)

- **不变(勿动)**:_ramp 色带(up: 0→#efe2cf/.35→#9cc4c2/.7→#2f8a8f/1→#0a5a62;dn: .35→#eaa9a9/.7→#d23b3b/1→#a30000)、CAP ±12、字色阈值(|ret|≥5 → cream #fff1e5,否则 ink)、series 骨架(treemap,roam:false,nodeClick:false,breadcrumb 隐,visualDimension:0,label inside mono 12/700 lh15 `name\n±x.x%`)、levels(L0 gap3 border0 底色 #f9e6d4 + upperLabel on;L1 gap1 border1 #fff1e5 + upperLabel off)、animation 900ms cubicOut
- **tooltip(改)**:bg/border #1a1a1a,padding [8,12],mono 11 #fff1e5;三行:①name 13/700 mb3;②「{win} **{±r.toFixed(1)}%**」——**ret 染色:涨 #9cc4c2 / 跌 #eaa9a9**(NEW;现码无 win label、ret 不染色);③「市值 ${x}B」#b8b1a8(CN「市值」/EN「mcap」随 prefer_cn;**换算保留现码 /1e9**,design mock 直用 B 值不 port)
- **upperLabel(改)**:h26,#1a1a1a,700/13,padding [0,6],**fontFamily 'Space Grotesk'**(现码 'Inter' → 换)

## NEW vs OLD(现码)delta 表

| 项 | OLD(现码 heatmap_treemap.py) | NEW(热力图 Treemap.dc.html) |
|---|---|---|
| masthead | 18px 标题 + window/as-of 11px 内联,右侧中位字符串 | 红条 5×44 + H1 26/700 + CMSI 红 chip + mono 副行 |
| 涨跌图例 | 无 | 190×12 五段渐变条 + 跌/涨端字 + -12/0/+12 刻度 |
| 惯例 banner | 「⚠ 本图配色…」单段 | 去 ⚠;加粗结构化;右侧补「hover 看名称/市值」提示 |
| 域名/中位位置 | 域名拼进标题(个股热力图 · {dom});中位在 masthead 右 | 独立域条(#f9e6d4 红左边):域名 16/700 + 中位+标的数右浮 |
| 页壳 | 无氛围层 | 双 radial gradient 洗层(红左上/青右上)+ max-width 1240 |
| tooltip | name/ret(无色)/mcap$B | +「{win}」label;ret 涨#9cc4c2 跌#eaa9a9 染色;「市值」中文 label |
| upperLabel 字体 | Inter | Space Grotesk |
| 画布高 | height-90(默认 630) | 700 |
| 色 ramp/CAP/字色阈值/levels/label/启动 | — | **无变化,原样保留** |

## MOCK 行为(不 port)与 honest-real 替换

| design MOCK | 替换 |
|---|---|
| `data()` 写死 7 块(管理式医疗/CXO/制药/生物科技/器械/医院/Japan)+ 手填 mcap($B)/ret | 保留现码 `_payload_to_treemap(build_domain_bento(...))` 真值管道:mcap=USD(缺市值中位兜底逻辑保留),tooltip /1e9 换算保留 |
| 「中位 +1.3% · 67 标的」写死 | payload `median` / `n_total` 实算 |
| 「截至 2026-06-29 · MOCK 数据(演示)」 | 真 as_of(home.py 传 latest)+ 真 source;「MOCK 数据(演示)」整段删 |
| `DCLogic` 组件 / `frameRef` / `buildDoc()` 双层 srcdoc | 不 port(Design 画布宿主机制);保持单层 `st.iframe(doc)` 自包含 |
| `function go(){...setTimeout(go,60)}` 轮询启动 | **禁**;必须走 `echarts_boot.MOUNT_JS` 的 `mountEChart('m', ...)`(0 宽竞态契约,现码已是,勿回退) |
| echarts jsdelivr CDN | 自托管 `app/static/echarts.min.js`,**相对路径无前导斜杠**(Cloud `/~/+/` 前缀契约,勿回退绝对路径) |
| design 写死中文单语 | 保留现码 prefer_cn 双语(EN 文案沿现码口径:标题 Single-Stock Map、Median/names、teal up/red down…),NEW 新增元素(图例 label/域条/脚注)补对应 EN |

**落地适配决策(design 未画,契约声明)**:home「全部」模式 = healthcare+ai 两张竖叠。masthead+图例+banner 属**页级元素只出一次**(第一张 iframe 或独立 header 块),域条+画布+脚注 per-domain 重复;单域模式 = 完整结构一张。Auditor 勿以「第二张没有 masthead」报违。

**落地硬约束(current-state.md §3 钉死,违即回滚)**:
- **payload 形状不可改**:`build_domain_bento` payload 同时喂旧 bento 渲染器(`app/pages/e2_etf_heatmap.py:52`)——本次只改渲染层(`render_treemap_html` 内部),payload/`_payload_to_treemap` 输入形状动了会外溢 ETF 页
- srcdoc 必须保 `html,body{height:100%}` + `#m` 显式 px 高(canvas 塌 0 契约);缺 mcap 的 tile 中位兜底(0 面积消失)保留
- `<script>` tag 用 `chr(60)+"scr"+"ipt"` 拆token(躲 build-time validator)——现码机制保留,新增脚本同法
- 公共签名 `render_treemap_html(payload, *, window_label, as_of, prefer_cn, height=720) -> (doc, h)` 保持兼容(home.py:178 唯一调用点;可加默认值新参,不破位置/语义)

## 站规 overrides(违 design 处)

- Google Fonts CDN(Space Grotesk/JetBrains Mono)→ 自托管 `theme.FONT_FACE_CSS`(三族已含);display 栈用 `theme.FONT_DISPLAY`
- box-shadow:设计本身无,✓ 无需裁;radius:仅红条 radius 1(≤4 ✓),其余直角
- emoji:设计无 ✓;**现码惯例 banner 的「⚠」字符按 NEW 删除**
- teal 涨 #0d7680 系 / red 跌不翻 ✓(memory:banner 化解 A 股误读 —— banner 保留且加强)
- `color-scheme:light` 保留在 srcdoc(现码已有,design 无此声明,live 必须保留)
