# CONTRACT — Reskin Wave-2 · 六区块 1:1 报纸精修 (harness · code mode)

Status: **FROZEN 2026-07-03** — George 拍板 §0 齐备，**无 FREEZE-BLOCKER**。
Branch: `feat/kline-reskin`。Design source of truth: Claude Design 项目 26a29f87 六张 `.dc.html`（DesignSync 2026-07-03 拉取）；
token 级规格 = `docs/harness/reskin-wave2/specs/{ipo-1a,hub,treemap,sector-overview,strategy-hero,strategy-banner}.md`；
现状基线 = `docs/harness/reskin-wave2/current-state.md`。冲突归一记录见文末附录 N。
Wave-1 契约（`docs/harness/kline-reskin/CONTRACT.md`）**对 Ticker Drill 继续全量有效**，本契约不改废它任何一条。

## §0 已钉定决策（George 2026-07-03 拍板，Builder/Evaluator/Auditor 均不得翻案）

| id | 钉定 | 依据 / 效力 |
|---|---|---|
| D1 | **IPO = 1a 报纸精修**（hover-dock 版），且**六区块全做**（IPO-1a / HUB / TMAP / SOVR / HERO / BANR） | George 2026-07-03 |
| D2 | **跌色 #c8102e 页级豁免扩展到 wave-2 全部 reskin 表面**（与 wave-1 D5 同理）：六区块新皮内 跌/亏/破发/最差 一律 `#c8102e`（tint 同步 rgb 200,16,46）；`theme.DOWN="#cc0000"` 全局 token **不动**；未 reskin 页面照旧 #cc0000。**Auditor 勿报**「跌色偏离 theme.DOWN」。specs 中 hub/sector 的跌色 FLAG 由本条一揽子裁决（附录 N-1） | George 2026-07-03 |
| D3 | **pulse/LIVE 呼吸点：KEEP visual + 语义改真 wording**（per wave-1 D1 模式）：设计画了呼吸点的位置一律保留视觉（cmsiPulse 1.5s 属入场级装饰，允许），但标签措辞必须诚实口径 —— `EOD / BACKTEST / 截至真日期 / DAILY` 类；**零** 「实时跟踪 · TRACKING」「TRACKING LIVE」等假实时字样、零假 tick `setInterval`、零 clock-mock。specs 中 hub「徽标继续不做」与 banner「维持删除」的默认值被本条覆盖（附录 N-2） | George 2026-07-03 |
| D4 | **字体已自托管**：`theme.FONT_FACE_CSS` 三族（Space Grotesk / JetBrains Mono / Inter），零 Google Fonts CDN；display 栈用 `theme.FONT_DISPLAY`，**全站 `FONT_STACK` 不换**（theme.py:83-84 明令），各区块显式设字族 | wave-1 O2 既成 |
| D5 | **GLASS_CARD_CSS / page_radial_wash（theme.py，wave-1 B1）= 可复用壳原语**：Ticker Drill 之外需要 wash/玻璃 的页面**必须复用它们**——wash 一律 `theme.page_radial_wash(1240)` 页级调用（勿在模块里重造双 radial）；玻璃 = 复用**配方值族**（rgba 白 + blur14 + 白边 + accent 顶/左边）以 inline style 或页级 `<style>` 实现；**禁把 `GLASS_CARD_CSS` 选择器扩类**（那组是 Ticker-Drill 专用 DOM），**禁向 `theme._CSS` 全局新增任何玻璃/wash 规则**（页级注入，NOT global）。注意各区块配方参数按各自 spec 断言（附录 N-8） | George 2026-07-03 |

## §1 宏观 spec（Planner）

六个区块按 George 批准的 Claude Design 新模板 1:1 重实现（token 级），数据全真零 mock：
① IPO tab（Strategy Picks 第 4 tab）整体重实现为 1a 报纸精修（KPI 三卡 + 分档表现 + 排行表 & hover 盘中 dock 单 iframe）——新 lib `app/lib/ipo_stage.py`；
② 行情中枢 Hub 指数瓦片 strip 玻璃化精修（`app/lib/market_hub_tiles.py`）；
③ 个股热力图 Treemap 原位精修（`app/lib/heatmap_treemap.py`）；
④ 板块总览 masthead + 基准表 + 涨跌榜 精修（`app/lib/sector_overview.py`，**双页共用**）；
⑤ 策略表现 Hero tearsheet 玻璃化（`app/lib/strategy_hero.py`）；
⑥ 策略开场 Banner 精修（`app/lib/strategy_banner.py`）。
渲染纪律不变（current-state「RENDERING-MECHANISM MAP」为准）：iframe 者仍 iframe、markdown 者仍 markdown、echarts 者必 `mountEChart`、小图面必 inline SVG。新皮 CSS 一律页面/模块局部注入。
**CRITICAL 数据完整性（贯穿全 §2）：零捏造曲线/路径/数值** —— 所有序列接真 loader（IPO dock = 真盘中路径 only，无路径出「盘中路径未采集」空态；hero/banner 曲线 = `compute_strategy_returns`；hub 瓦片 = 真 spark closes；treemap = `build_domain_bento` payload；sector = 真期间收益/spark）；**零硬编码 demo 字面量**（各 spec 点名清单，如 n=20 / +384% / -4.6% 快照数字 → 一律 live-computed 流入）。

## §2 验收清单（86 条，逐项独立 PASS/FAIL；方法代号见 §3）

### IPO — 港股IPO打新 1a（`app/lib/ipo_stage.py` + `4_Strategy_Picks.py::render_ipo_strategy` 重写）

| id | 断言 | 方法 |
|---|---|---|
| IPO1 | masthead：border-bottom 2px #1a1a1a pb16；左 = 红条 5×48 #c8102e + 「港股 IPO 打新」30px/700 + chip「CMSI 棱镜六因子 v6.7 · 策略后测」（mono 13/600 #8a8580，border 1px #e4d2bd，p 3-9）；副行 mono 11/.08em #8a8580 含「样本 n={N}」动态值 | JS+SS |
| IPO2 | masthead 右：红呼吸点 8px #c8102e（pulseDot 1.5s：50% opacity .35 + scale .82）+「BACKTEST · 后测」mono 10/.16em UPPER #c8102e/600；下行 mono 11 #8a8580「截至 {真 as-of} · {真来源}」——D3 合规（BACKTEST=诚实口径）；零假实时字样 | JS+SS+GR |
| IPO3 | KPI 三卡：grid 3 等分 gap14；玻璃 rgba(255,255,255,.55)+blur(14px)+border 1px rgba(255,255,255,.7)；顶边 3px：样本=#1a1a1a / 最高=#0d7680 / 最差=#c8102e；label mono 10/.12em UPPER → 值 mono 48px/700 -0.02em（色随卡）→ 脚注 mono 11；**design 的 hover translateY+shadow 已裁：零 box-shadow、零 hover 位移** | JS |
| IPO4 | KPI 数据全 live：样本卡值 = `load_ipo()` 全量 n（当前 54），脚注「已上市 X · 待上市 Y」动态；最高/最差从 listed `day1_ret` 实算（idxmax/idxmin，脚注 = 名+档）；**零 n=20 旧快照、零硬编码 384/56.9 字面量**（数值必须由数据流入） | JS+GR+RM |
| IPO5 | 分档表现节：节标 = 红条 4×16 + mono 12/.16em UPPER「分档表现 · TIER PERFORMANCE」+ 灰副注；玻璃容器（rgba .5/blur14/白边，无顶边）内表格 grid `150px 70px 1fr 110px 90px` gap12；表头 mono 10/.1em UPPER #8a8580 底线 1.5px #1a1a1a；行线 1px #eadbc8；脚注读法行 mono 10.5 | JS |
| IPO6 | 分档数据实算：5 档固定序（重点申购+/重点申购/推荐申购/谨慎申购/不申购）从 listed 实算 只数/中位/收涨率/破发；中位条形 轨 160×8 rgba(26,26,26,.06)、填充按 \|中位\|/max 归一、涨青跌红；破发 0=#8a8580 / >0=#c8102e | JS+RM |
| IPO7 | 档位色系 5 色：重点申购+ #a00d25 / 重点申购 #c8102e / 推荐申购 #0d7680 / 谨慎申购 #a06d1f / 不申购 #6b6560；chip = 同色字 + 1px 同色边 + bg rgba(色,.07~.08) | JS |
| IPO8 | 排行表 + 走势 dock 在**同一个 `st.iframe` srcdoc 内**（单 iframe 自包含，跨 iframe 无法 hover 联动）；外层 grid `1fr 400px` gap20；节标「评分排行 · SCORE RANKING」+ 副注含 hover 提示 | JS+GR |
| IPO9 | 左表 = **全 54 行按评分降序**（固定序，无排序 toggle）；7 个 design 列轨 `36px 56px 140px 56px 104px 1fr 92px`（#/代码/名称/评分/申购档/子板块/首日涨幅右对齐）照断 + **附加「上市日期」列必须存在**（George 2026-07-03 点名，design 未画；轨宽/位置 Builder 定，mono 右对齐）；rank mono 12 #8a8580 补零两位（pending 无 rank「—」）；名称 13.5/700；评分 mono 13/700；档 chip 9.5px；首日 mono 13/700 涨青跌红、pending 首日列「—」 | JS+RM |
| IPO10 | hover 交互：mouseenter 任一行 → 右 dock 切换为该股（无需点击）；**默认选中 rank 1** 常驻；hover/选中行 bg rgba(200,16,46,.06) | JS+SS |
| IPO11 | dock：`position:sticky; top:16px`；玻璃加强 rgba(255,255,255,.6)+blur(16px)+白边 .75+顶边 3px #1a1a1a，p20-22；头行 = 名 19/700 + code chip + 档 chip 右浮；涨幅 mono 38/700 色随向；副注 mono 10/.08em「首日盘中 · 相对发行价 % · 终点 = 首日收盘」；SVG 356×200 = 3 横网格 #eadbc8 + 0% 盈亏虚线（#8a8580 dash 4-4 op.65 + mono 9 标签）+ area fill 线色 α.10 + path stroke-width 2 + 终点 circle r4；底行 border-t #eadbc8 mono 11「区间高 {max} · 区间低 {min} · {来源}」 | JS+SS |
| IPO12 | **盘中路径数据完整性（CRITICAL）**：有路径票（`load_ipo_intraday()`，当前 20 codes）→ 真实 5min 路径，终点口径 = 首日收盘（沿现 `pct=(closes*(1+d1)/last-1)*100` 等价换算）；无路径票（新补录/pending）→ dock 显示「盘中路径未采集 · 仅首日收盘」空态或首日收盘平线；**零 Math.random/genData/正弦抖动伪造路径**（design 的 genData 仅演示，禁移植） | JS+GR+RM |
| IPO13 | 页脚注框：border 1px #e4d2bd + bg rgba(255,255,255,.4) p12-18 mono 10.5/1.7 #8a8580，后测口径提示 +「仅供内部研究回测,不构成投资或申购建议」；零 MOCK 字样 | JS+GR |
| IPO14 | **superseded 清理**（§4-S1，Auditor 勿报缺失）：现小图墙（`charts.ipo_intraday_facets` Plotly 于 IPO tab 的调用）、按评分/按首日双排序 toggle（`ipo_rank_sort` segmented_control）、`render_html_table` 版排行表 → 全部移除，被 1a dock 取代；`listed.empty` 早退守卫（现 L598-602）保留等价保护（无 listed 时 KPI/分档/dock 不渲或空态） | GR+RM |
| IPO15 | 工程：`day1_ret` DECIMAL ×100 仅一次、`code` 保持 str（前导零）；`app/lib/ipo_stage.py` py_compile clean；4_Strategy_Picks AppTest 无异常；`load_ipo/load_ipo_intraday` 数据管道签名不动 | RM |

### HUB — 行情中枢指数瓦片（`app/lib/market_hub_tiles.py` + home.py masthead 区）

| id | 断言 | 方法 |
|---|---|---|
| HUB1 | masthead 左：红条 5×44 #c8102e radius1 + h1「行情中枢」30px/34/700 -0.01em + **mono kicker**「CMSI · MARKET HUB · 四大指数总览」11px/.08em #8a8580 mt5 | JS+SS |
| HUB2 | masthead 右（D3 裁决，附录 N-2）：呼吸点 8px #0d7680 cmsiPulse 1.5s **保留** + 标签改诚实口径（如「EOD · 收盘」mono 10/.16em UPPER #0d7680/600）；下行 = `EOD {db.latest_snapshot_date()} · {db.last_fetch_utc()}` 真值；**零「实时跟踪/TRACKING/LIVE」字样、零硬编码 2026-06-29/08:42** | JS+GR |
| HUB3 | eyebrow 节标：红 tick 4×16 + mono 双语「市场总览 · Market Overview」JetBrains Mono 12/.16em UPPER #1a1a1a/600 + 副注 12px #8a8580 + 右浮渲染器标签 mono 10/.1em UPPER = **`SVG`**（与实情一致，零 `ECHARTS` 虚标） | JS+GR |
| HUB4 | #row 玻璃容器：border 1px rgba(255,255,255,.7) + **border-top 3px #1a1a1a** + bg rgba(255,255,255,.55) + backdrop-filter blur(14px)，高 248px；末瓦片去右边框 | JS |
| HUB5 | strip srcdoc 内层水彩垫底（玻璃可 blur 前置条件）：`radial-gradient(700px 320px at 8% -20%, rgba(200,16,46,.09)…) + radial-gradient(700px 320px at 94% -10%, rgba(13,118,128,.10)…) + #fff1e5`；页级 masthead wash 允许降级舍弃（spec 交互注） | JS |
| HUB6 | 瓦片 ×4（flex:1 p18-20 border-right 1px #ebd9c8）：头行 指数名 11/.06em/600 #8a8580 + 红 tick 4×12；现价 **mono 32px/38/700 -0.02em tabular**（替 Inter 34/40/600）；当日涨跌 mono 13/700 涨 #0d7680 / 跌 **#c8102e**（D2） | JS |
| HUB7 | sparkline：46px 高**内联 SVG**（protected，禁换 echarts —— 0 宽竞态守卫）；数据 = `bm.close_series()` 近 30 真实收盘；**零 `curve(n,end,seed)` 伪随机移植、零 echarts CDN 引入** | JS+GR |
| HUB8 | 52W 区间：轨 3px #ebd9c8 + teal #0d7680 填充至 pos% + 墨标 2×9 #1a1a1a @pos(top -3) + 下行 mono 9 #b8b1a8「52W {lo}」/「{hi}」；**<330d 窗口不标 52W 护栏保留** | JS+RM |
| HUB9 | 情境行：mono 10/.04em UPPER #8a8580「1M {±x.x%} · YTD {±x.x%}」，值符号染色 涨 #0d7680 / 跌 #c8102e | JS |
| HUB10 | **v2 增量全保留**（§4-K，Auditor 勿报 diff）：市场速读 dek（真 N涨M跌+领涨领跌）、现价 count-up、瓦片 staggered fade-rise、SVG draw-in、prefers-reduced-motion 降级、中英 i18n、缺数占位保高度 | JS+RM |
| HUB11 | 脚注真 provenance：「SOURCE: Yahoo Finance cron EOD · 截至 {真date} · 仅供参考」（随 i18n）；**零「MOCK 走势(演示)」** | JS+GR |
| HUB12 | 数据管道/签名不变：`bm.fetch_benchmarks()` broad_market 4 指数 + 现 `_tiles`/`_spark`/`_range52` 组装；`render_index_tiles(tiles,*,as_of,prefer_cn,height)` 兼容（home.py:285 唯一调用点，可加带默认值新参） | RM |

### TMAP — 个股热力图 Treemap（`app/lib/heatmap_treemap.py`）

| id | 断言 | 方法 |
|---|---|---|
| TMAP1 | 页壳：#fff1e5 + `theme.FONT_DISPLAY` 栈 + `font-feature-settings:'tnum','ss01'` + **`color-scheme:light` 保留**（现码已有，勿丢）+ 双 radial 洗层（900×520 at 10% -8% 红 .09 / 820×520 at 94% 4% 青 .10，absolute inset 0） | JS |
| TMAP2 | masthead：红条 5×44 r1 + H1 26px/700 -0.01em「个股热力图 · Market Map」+ CMSI chip（mono 10/700，#fff1e5 字 on #c8102e 底，p2-7 ls .06em）；副行 mono 11/.06em #8a8580 =「面积 = 市值 · 颜色 = **{win}** 涨跌方向与幅度 · 子行业分块」，win 随 1D/5D/1M 段控动态（零写死 1D） | JS+SS |
| TMAP3 | 渐变图例（新元素）：条 190×12 border 1px #d4c4b0，`linear-gradient(to right,#a30000,#d23b3b,#efe2cf,#2f8a8f,#0a5a62)`（与 `_ramp` 五锚点严格同源）；两端字 11/700 跌=#a30000/涨=#0a5a62；刻度行 mono 9/600「-12%」「0」「+12%」（与 CAP=12 同步——若 CAP 改，刻度必须联动） | JS |
| TMAP4 | 惯例 banner：bg #f9e6d4 + border-left 3px #c8102e p7-12；结构化加粗「本图配色(港美股惯例)」+ 青绿=涨 #0a5a62 / 红=跌 #a30000 +「与 A 股相反」提示 + 右侧 hover 提示；**零 ⚠ 字符**（NEW 删，现码的一并删） | JS+GR |
| TMAP5 | 域条（新元素）：bg #f9e6d4 border-left 3px #c8102e p8-13；域名 16/700（cn/en 按 prefer_cn）+ 右浮 mono 11/700「中位 {median:+.1f}% · {n_total} 标的」= payload 真值实算 | JS+RM |
| TMAP6 | 多域竖叠（home「全部」模式）：masthead+图例+banner **页级元素只出一次**（首张或独立 header 块）；域条+画布+脚注 per-domain；单域 = 完整结构一张。**Auditor 勿报「第二张缺 masthead」** | JS+SS |
| TMAP7 | echarts **不变项**（勿动，回归即 FAIL）：`_ramp` 7-stop 色带原值、CAP ±12、字色阈值 \|ret\|≥5→cream、series 骨架（treemap/roam:false/nodeClick:false/breadcrumb 隐/visualDimension:0/label inside mono 12/700 `name\n±x.x%`）、levels（L0 gap3 border0 #f9e6d4 + upperLabel on；L1 gap1 border1 #fff1e5）、animation 900ms cubicOut | EO |
| TMAP8 | tooltip（改）：bg/border #1a1a1a、padding [8,12]、mono 11 #fff1e5；三行 = name 13/700 /「{win} {±r.toFixed(1)}%」ret 染色 **涨 #9cc4c2 / 跌 #eaa9a9** /「市值 ${x}B」#b8b1a8（CN「市值」/EN「mcap」随 prefer_cn；**/1e9 换算保留**，design mock 直用 B 值不 port） | EO+SS |
| TMAP9 | upperLabel（改）：h26、#1a1a1a、700/13、padding [0,6]、fontFamily **'Space Grotesk'**（替 'Inter'） | EO |
| TMAP10 | 启动纪律：经 `mountEChart('m',…)`（echarts_boot.MOUNT_JS）；**零 `go()/setTimeout` 轮询、零裸 `echarts.init`**；`_ECHARTS_SRC` 相对路径 `app/static/echarts.min.js` 无前导斜杠；`<script>` 拆 token 机制（`chr(60)+"scr"+"ipt"`）保留于新增脚本 | GR+EO |
| TMAP11 | **payload 形状不可改**：`build_domain_bento` / `_payload_to_treemap` 输入形状不动（payload 同喂 `e2_etf_heatmap.py:52` 旧 bento）；公共签名 `render_treemap_html(payload,*,window_label,as_of,prefer_cn,height=720)->(doc,h)` 兼容（home.py:178 唯一调用点） | RM+GR |
| TMAP12 | srcdoc `html,body{height:100%}` + `#m` 显式 px 高（canvas 塌 0 契约）；缺 mcap tile 中位兜底保留（0 面积消失防护）；画布高按设计 ~700（home 多域 600 / 单域 720 现逻辑等比可维持） | JS+RM |
| TMAP13 | 脚注：mono 11 #8a8580「SOURCE: {source} · 市值 USD · 截至 {真as_of} · 面积=市值 / 颜色={win} 涨跌」；**零「MOCK 数据(演示)」** | JS+GR |
| TMAP14 | 数据真值（CRITICAL）：全部 tiles/sectors 来自 `build_domain_bento` 真 payload；**零 design `data()` 7 块硬编移植、零 DCLogic/frameRef/buildDoc 双层 srcdoc 机制移植**（保持单层 st.iframe） | GR+RM |

### SOVR — 板块总览（`app/lib/sector_overview.py`；⚠ 双页共用，**每项两页都核**）

| id | 断言 | 方法 |
|---|---|---|
| SOVR1 | **双页 spillover 验收**：`2_Healthcare.py`（focus XLV/XBI/XPH/IXJ/IHF/IHI）与 `a2_ai_overview.py`（^SOX/SMH/AIQ/512480.SS/515880.SS/442580.KS）两页均渲染新皮，SOVR2-14 逐项两页各自 PASS；真机眼验两页 | RM+SS |
| SOVR2 | masthead（新增块）：border-b 2px #1a1a1a pb16 + 红条 5×48 r1 + 标题 30px/700 -0.01em + domain chip（mono 13/600 #8a8580 border 1px #e4d2bd p3-9）+ 副行 mono 11/.08em；**标题/chip/副行/来源全参数化**（医疗≠AI，零 hardcode HEALTHCARE —— memory: multi-industry） | JS+RM |
| SOVR3 | masthead 右：青呼吸点 8px #0d7680 pulseDot 1.5s +「EOD · 收盘」mono 10/.16em UPPER #0d7680/600（en「EOD · CLOSE」）+ 下行 mono 11「截至 {真asof} · {真source}」；**新做青点，不复用 theme 孤儿 `.cmsi-live-dot`**（红色语义不对）；D3 合规 | JS+GR |
| SOVR4 | 页级 wash：两调用页各自 `theme.page_radial_wash(1240)`（D5：复用现成 theme.py:1022，勿模块内重造）；玻璃 blur 有垫底 | JS+GR |
| SOVR5 | 基准节标 + 色阶图例：红条 4×16 + mono 12/.16em UPPER「基准 · Benchmark ETF」；右浮图例 =「跌」10px #c8102e/600 + 渐变条 120×9（border 1px #d4c4b0，`linear-gradient(to right,#c8102e,#f7d9d9,#fff1e5,#d9e8e6,#0d7680)`）+「涨」#0d7680 + mono 9 #8a8580「期间收益色阶」 | JS |
| SOVR6 | 基准表玻璃容器：**rgba(255,255,255,.5)** + blur(14px) + border 1px rgba(255,255,255,.7)，padding 2px 16px 8px，直角，**无顶边 accent**（本节配方 ≠ GLASS_CARD_CSS，勿套那组类/顶墨条） | JS |
| SOVR7 | th 重构：**透明底**（替 PAPER_BAND）+ mono 10/.08em UPPER #8a8580/600（替红字）+ padding 9-12 + **border-bottom 1.5px solid #1a1a1a**（替红线）+ **零竖分隔线**（替首末列竖线） | JS |
| SOVR8 | 行态：td h46 padding 0-12 border-bottom 1px #ebd9c8；**行 hover `rgba(26,26,26,.045)`** 经 `<style>` 类规则注入（现纯 inline 无 hover → 新增）；Ticker mono 12/700 .04em；名称 500 | JS |
| SOVR9 | 几何不变 + 仅跌色换（D2）：sparkline SVG 110×28/stroke1.5 non-scaling/终点 r2.2、`_tint` cap25→α≤.16/死区 .05、期间格 `▲/▼/·` 权重 600、rel 条 h14/#f4ead9/中线 #d4c4b0/cap25→50%/值 mono 12/700 w54 —— 公式全同现码，**跌侧一律 #c8102e / tint rgb(200,16,46)**（0 档 #8a8580 照旧） | JS |
| SOVR10 | movers：节标 红条 4×16 + mono 12/.16em UPPER「涨跌榜 · Movers」+ 副注；列头 竖条 3×13 + **mono 11/700/.1em 双语**「涨幅前 10 · GAINERS」#0d7680 /「跌幅前 10 · LOSERS」#c8102e；玻璃容器同 SOVR6 配方无 padding；行宽 64/flex/60/84/58 + cap22 不变；轨 涨 rgba(13,118,128,.10) / 跌 rgba(200,16,46,.08)；d1 **带负号**「▼ -x.x%」（替现 `abs()` 去号） | JS |
| SOVR11 | 数据真值：`rows/gainers/losers` 数据契约不变（caller 真数据：`bm.fetch_benchmarks`/`close_series` tail30/rel_sp=YTD−^GSPC）；movers 每侧出 **10** 行（非 design 4 行 placeholder）；**零照抄 design 行清单（IGV 错位）、零 `spark(end,seed)` 伪随机、零 MOCK 脚注** | RM+GR |
| SOVR12 | 渲染载体不迁：纯 `st.markdown(unsafe_allow_html)` **非 iframe**；表保持真 `<table>` DOM；小图 inline SVG **禁 echarts**（横切 INVARIANT 4）；`@keyframes pulseDot`/hover/backdrop-filter 经 `<style>` 块注入 | GR+RM |
| SOVR13 | 跌色 page-scope 实现纪律：#c8102e 以模块/页级常量实现（先例 candlestick `_DOWN=theme.CMSI_RED`）；`theme.DOWN` 全局不动 | GR+JS |
| SOVR14 | i18n：新增双语（movers 列头/节标/EOD 标签等）zh/en 成对；caller 预本地化模式（style b）保持或补 locales key，**parity 不破**、EN 态无 raw key/残留单语硬编回归 | RM+GR |

### HERO — 策略表现 Hero（`app/lib/strategy_hero.py::render` + 页面层页头）

| id | 断言 | 方法 |
|---|---|---|
| HERO1 | hero 卡玻璃：bg rgba(255,255,255,.55) + blur(14px)(+-webkit-) + border 1px rgba(255,255,255,.7) + **border-top 3px #c8102e**；直角；零 box-shadow；grid `340px 1fr` 保持 | JS |
| HERO2 | iframe srcdoc：双 radial 洗层（红 .09 左上 / 青 .10 右上）+ overflow hidden 垫底；**自托管 @font-face 在 srcdoc 内存在**（wave-1 P7 同款）、body 用 Space Grotesk 主导栈 + tnum/ss01 | JS+GR |
| HERO3 | 左栏：白纱 bg rgba(255,255,255,.35) + border-right 1px **#e4d2bd**（加深一档）；顶行 teal 呼吸点 8px cmsiPulse 保留 + 措辞诚实（如「持续跟踪 · EOD」；**零「TRACKING LIVE」**——D3） | JS+GR |
| HERO4 | 巨号：**mono 56px/60/700 -0.03em** tabular lining（替 60/62 非 mono）；label「累计收益 · CUMULATIVE」mono 10/.12em UPPER；**符号染色不回退**（`_cum_col`：负=红） | JS+RM |
| HERO5 | 脚注行 mt16：基准 label mono 10/.1em UPPER「基准 {code}」→ 值 **mono 17px/600** #4a4a4a；竖 divider 1px #e4d2bd pl18；α label mono 10 UPPER **#c8102e**「超额 α · ALPHA」→ 值 **mono 17px/700** 符号染色（`_alpha_col`） | JS |
| HERO6 | KPI 7 格：grid repeat(7,1fr) border-t 1px #d4c4b0、格 p14-16 border-r 1px #ebd9c8；label **mono 10**/.12em UPPER → 值 **mono 17/600** tabular mt8；胜率=#0d7680、**MDD=#c8102e**（D2/spec E 裁决取 CMSI_RED）、余=墨；灰分母「/ 评分池 {pool}」「/ {n_total}」**live 真分母**；基准格副行 10px 非 mono | JS+RM |
| HERO7 | echarts `#eq` option：策略线 #c8102e w2.2 smooth 无 symbol + area LinearGradient rgba(200,16,46,.14→.01) + endLabel「策略 {值}」mono 11/700；基准线 #8a8580 w1.5 dashed + endLabel；legend top16 right8 roundRect 18×2、text 11px #4a4a4a **fontFamily 'Space Grotesk'**（唯一 JS 改动）；grid l44 r58 t52 b28；animationDuration 1900ms cubicOut | EO |
| HERO8 | 轴/tooltip：x category boundaryGap:false + axisLine #1a1a1a w1 + label mono 10 #8a8580 interval 20 无 splitLine；y value scale 无轴线 + splitLine #ebd9c8；tooltip axis + 虚线 **line 指针** #b8b1a8(设计稿源 `axisPointer.type:'line'`——原契约误写"十字",R1 裁决修正 2026-07-05,Auditor 按 line 核)+ 墨底 #1a1a1a 奶字 mono 11 p8-12 + 行含 `(+x.x%)` 折算收益 | EO |
| HERO9 | **曲线/数字真值（CRITICAL）**：曲线 = `compute_strategy_returns`（portfolio rebased=100）+ `_bench_norm` 页面层传入（4_Strategy_Picks L232-245 管道不回退）；count-up 目标值全 live；**零 `genCurve` 伪随机、零 118.7/106.2/+18.7/+6.2/+12.5/-6.3/1.84/102 等 mock 字面量硬编** | GR+RM |
| HERO10 | 渲染 gate 保留（现 L224-229 等价）：曲线非空 + len≥10 + sharpe 非退化 + bench 尾非 NaN 才渲 —— 玻璃化不得绕过 gate | RM+GR |
| HERO11 | 契约不动项：mountEChart('eq') + 零裸 init、`[data-count]` count-up 协议 1500ms easeOutCubic + MDD 强制负号 + sharpe 2dp、FONT 经 `json.dumps` 注入（勿内联单引号）、iframe height 470 + `#eq` 290px（spec §C8 钉 290，见附录 N-6）+ `html,body{height:100%}`、`@media 860px` 断点、**`render_compare_chart`(#cmp) 整体不动** | GR+EO+RM |
| HERO12 | 页面层页头：左置红条 **5×36** r1 + H1 32/36/700 -0.01em（替尾缀 4×24）+ 右浮 mono 11/.1em UPPER「QUANTAMENTAL · 量化基本面」；卡外 provenance 行 mono 11 真值；**零 MOCK/「策略 · 提案」demo chip 残留**；不做 iframe 假 tabs（保持 st.tabs） | JS+GR | **[R2 裁决 2026-07-05:作废——此项系 hero 设计稿「上下文框」与 banner 设计稿对同一页头的重复描绘;banner 版(语言钮+TRACKING,BANR1/2)为功能实现版已落地。QUANTAMENTAL 装饰标不实现;Auditor 勿报缺失。George 眼验可翻案]**

### BANR — 策略开场 Banner（`app/lib/strategy_banner.py` + 4_Strategy_Picks 调用区）

| id | 断言 | 方法 |
|---|---|---|
| BANR1 | 页面壳：调用页 `theme.page_radial_wash(1240)`（D5 复用；Strategy Picks = wave-2 显式 opt-in 页）；banner 各块显式 `theme.FONT_DISPLAY`（全局 FONT_STACK 不动） | JS+GR |
| BANR2 | masthead：红条 5×34 #c8102e r1 + H1 32px/36/700 -0.01em；中/EN 切换**只换皮不换交互**：容器 border 1px #d4c4b0 radius3、段 mono 11/600/.08em p5-12、active bg #c8102e 字 #fff1e5；`<a href="?lang=zh\|en" target="_self">` 真锚点 + `st.query_params` 机制保留 | JS+RM |
| BANR3 | 呼吸点徽标（D3 裁决，附录 N-2）：**恢复**青点 8px #0d7680 cmsiPulse + 诚实措辞（如「EOD 跟踪 · DAILY」mono 10/.16em UPPER；**零「实时跟踪 · TRACKING」**）+ 下行「更新 {真as_of} HKT」mt5；实现可复用 theme 孤儿 `.cmsi-live-dot`（theme.py:741，需校色为 teal）补回 DOM，或模块 `<style>`——若动 theme._CSS 仅限调整/清理该既有块，零新增规则 | JS+GR |
| BANR4 | dek：14px/1.65 #4a4a4a max-width 880 mt16 + 关键短语 `<b>` 墨；文案 = 现 i18n `strategy.pitch` 双语对（**零 design 缩短版 mock 文案覆盖**） | JS+RM |
| BANR5 | 速览节标：红条 4×16 + mono 12/.16em UPPER「策略速览 · Strategy Snapshot」+ 灰副注 + **右浮 counter chip** mono 10/.1em UPPER「{N} STRATEGIES」动态 = len(items)（零固定 3） | JS |
| BANR6 | 三卡玻璃：rgba(255,255,255,.55)+blur14+白边 .7+**顶边 3px #1a1a1a**，卡间 border-right 1px #ebd9c8，卡内 p18-20；inline style 实现（**不扩 GLASS_CARD_CSS 类**——D5）；零 hover 态/零 box-shadow | JS+GR |
| BANR7 | curve 卡 ×2：头行 名 14/600 + 右浮「基准 {code}」mono 10；副行 mono 11「自 {pick_date} · {n} 票」；大号累计 **mono 32px/36/700 -0.02em tabular**（替 sans 34）符号染色；α chip mono 12/700 p2-7 r2 **符号染色不回退**（AUDIT-2026-06-30 D1：α≥0 青/青底、<0 红/红底）；SVG 280×64 `_spark_pair` 几何不变（红实线 w2 + 渐变面积 .16→.01 + 灰虚线 1.4 dash3-3 + 终点 r2.6 + 双序列共 min/max）+ **gradient id 每卡唯一**；曲线数据 = `compute_strategy_returns` 现管道（`_overview_curve_card`），**零 `curve()/pair()` mock** | JS+RM+GR |
| BANR8 | **盈亏点带接真（CRITICAL 升级）**：逐持仓真 sign 列表（调用页 `normed.iloc[-1]>100` 逐持仓真值，按 rank 或收益确定性排序）传入替 `_dots` 伪随机洗牌——`_dots` 只画不造；点 5px gap3、盈 #0d7680 / 亏 #c8102e、title tooltip「每点 = 一只持仓」 | JS+RM+GR |
| BANR9 | IPO 卡：头行 名 + 右浮「六因子 v6.7」mono 10；副行「静态截面 · {n} 样本」；大号中位 mono 32 青 +「中位首日」11；三行分布条（标签 mono 10 w30 + 轨 h8 #ebd9c8 + 填充青/红 #c8102e + 值 mono 11/700 w48 右；负值条 anchor right:50%）；**最差条宽归一 `max(2, min(|lo|/hi×100, 100))`**（替硬编 2%）；底行「已上市 {listed} / 待上市 {pending}」live（零 mock 20/0/-4.6） | JS+RM |
| BANR10 | 双轨导览：节标同 BANR5 无副注；卡玻璃 rgba(255,255,255,.5)+blur14+白边 .7 + **border-left 3px #c8102e** p18-22；序号 mono 15/700 #c8102e + 标题 15/700 baseline gap9；正文 13/1.65 #4a4a4a | JS |
| BANR11 | 页脚数据纪律条：mt14 p11-16 bg #f9e6d4 12.5px #4a4a4a + 红 tick 3×14 —— **与现实现逐值相同，不动** | JS |
| BANR12 | 渲染载体/边界：纯 `st.markdown` **不迁 iframe**；小图 inline SVG **禁 echarts**；跌色 #c8102e page-scope（D2，theme.DOWN 不动）；卡内既有中文硬编字段维持现状不倒退，若改 `i18n.t` 需 zh/en 成对 | GR+RM |

### GRD — 横切守卫与回归（W7）

| id | 断言 | 方法 |
|---|---|---|
| GRD1 | **grep 电池零命中**（白名单注明，清单见 §3-GR）：CDN 字体 / 裸 echarts.init / 绝对 static 路径 / 伪造序列函数 / MOCK UI 串 / spec 点名 demo 字面量 | GR |
| GRD2 | 新皮 CSS 域：零 box-shadow、border-radius ≤4px、零 emoji（新增 UI 串）、tabular-nums 数字面 | GR |
| GRD3 | i18n parity：locales zh/en（含 pages_zh/pages_en）新增 key 成对；zh/en 两态各渲染一遍无 raw key、无 TypeError | RM+GR |
| GRD4 | `py_compile` 全改动 .py clean；AppTest：home / 4_Strategy_Picks / 2_Healthcare / a2_ai_overview 四页无异常 | RM |
| GRD5 | **零泄漏 spot-check（wave-1 P9 同款）**：未触页抽查 **SEC Facts + Capital Markets(HK IPO tracker) + e2_etf_heatmap** —— 无 wash/玻璃新皮泄漏、ETF bento 页照旧渲染（payload 共享回归探针）。（附录 N-3：brief 例举 Healthcare 已改——Healthcare 是 wave-2 opt-in 页） | RM+GR+SS |
| GRD6 | theme 边界（D5）：`theme._CSS` 零本次新增玻璃/wash 规则（允许清理/校色既有 `.cmsi-live-dot` 孤儿块）；`GLASS_CARD_CSS` 选择器不扩类；新页 wash 全部经 `theme.page_radial_wash()` 页级调用 | GR |
| GRD7 | 真机冒烟：init.sh 重启 :8599 → home / Strategy Picks / Healthcare / AI overview HTTP 200；echarts 面（treemap `#m` + hero `#eq`）**连刷 3× 每次出图**（0 宽竞态回归探针） | RM |

## §3 验收方法（Stage 2 · 独立 Evaluator · 真机）

- **RM**（run-machine）：沿用 `docs/harness/kline-reskin/init.sh` 起 :8599（或复制为 `reskin-wave2/init.sh`）；**改 lib 后必须 kill+relaunch**（Streamlit 热进程缓存 lib 模块，memory 实锤）；AppTest/py_compile 走 `.venv/bin/python`。
- **JS**（computed-style，主判定门）：claude-in-chrome `javascript_tool`。srcdoc iframe 同源取法：`var f=[...document.querySelectorAll('iframe')].find(f=>(f.srcdoc||'').includes(MARKER)); var d=f.contentDocument;` → `getComputedStyle`；MARKER per 模块（IPO dock 容器 id / hub `#row` / treemap `id="m"` / hero `id="eq"`）。SOVR/BANR 为 st.markdown 直出 → 直接查页面 DOM。断言色值用 rgb() 归一形。
  **IPO hover-dock 交互验收**：JS 对第 N 行 `dispatchEvent(new MouseEvent('mouseenter',{bubbles:true}))` → 断言 dock 头行名称/涨幅切换为该股；初载断言 dock = rank 1；辅以 claude-in-chrome 真 hover 截图旁证。
- **EO**（echarts getOption）：`f.contentWindow.echarts.getInstanceByDom(f.contentDocument.getElementById(ID)).getOption()`，ID ∈ {m, eq}；断言 series/tooltip/label 参数。hub/sector/banner 小图无 echarts → 无 EO 项（若 Builder 违规引入 echarts 即 FAIL HUB7/SOVR12/BANR12）。
- **SS**（screenshot 旁证）：参照 = Claude Design 画布截图 / DesignSync 源剥壳本地渲；实现 = :8599 定视口 1440×900。gestalt 一致性旁证；**颜色/尺寸判定一律以 JS/EO 为准**。
- **GR 电池（零命中；白名单注明）**：
  ① `fonts.googleapis.com|fonts.gstatic.com` 全 repo；
  ② `echarts.init(` 除 `echarts_boot.MOUNT_JS` 定义处；
  ③ `src="/app/static|url('/app/static` 绝对路径（Cloud `/~/+/` 前缀契约）；
  ④ **伪造序列**：`Math.random|genData\(|genCurve\(|genDots\(|curve\(n,|seed` 于本次新增/改动的 srcdoc JS（`ipo_stage/market_hub_tiles/heatmap_treemap/strategy_hero/sector_overview/strategy_banner`；Python 侧确定性 hash 用途须逐个白名单注明，如 gradient id 的 `hash(name)`）；
  ⑤ `MOCK`（app/ 下 UI 字符串）；
  ⑥ **demo 字面量电池**（改动文件，spec 点名清单）：IPO `n=20` 样本快照 / hub `7354\.02|7,354` 等 4 组硬编快照 / treemap 7 块手填 mcap/ret / sector 6 行 renderVals + IGV / hero `118\.7|106\.2|18\.7|6\.2|12\.5|1\.84|-6\.3` / banner `24\.3|4\.6`（数字必须由 loader 流入，正则按最终 diff 调整、命中需给出「非 demo」证明）；
  ⑦ `setInterval`（六模块新皮域；无白名单——wave-2 无真挂钟需求）；
  ⑧ `box-shadow`（新皮 CSS 域）；⑨ emoji + `⚠`（新增 UI 串 + treemap banner）；⑩ `border-radius:\s*([5-9]|\d{2,})px`（新皮域）；
  ⑪ 假实时字样：`实时跟踪|TRACKING LIVE|LIVE ·`（六模块 UI 串；「BACKTEST/EOD/DAILY/持续跟踪 · EOD」白名单）；
  ⑫ `bench_overlay|_terminal_bench_overlay` 全 repo 仍零（wave-1 G5 不回潮）。
- **判定纪律**：每项独立 PASS/FAIL，failure 报告 = 验收项 id + 期望 vs 实测 + file:line + 证据路径（`eval/` 下截图/JS 输出/grep 输出）。

## §4 SUPERSEDED / KEPT invariants（Auditor 按此核，勿把改废当 regression）

### S — 本契约显式改废（George 授权 2026-07-03）

| # | 旧特性/旧约束 | 处置 | 依据 |
|---|---|---|---|
| S1 | IPO tab 盘中小图墙（Plotly `ipo_intraday_facets`）+ 按评分/按首日双排序 toggle（`ipo_rank_sort`）+ `render_html_table` 版排行表 | **全部移除**，被 1a hover-dock 取代（dock hover 即大图；表固定评分序）；`charts.ipo_intraday_facets` 函数本体若无他处引用可留可删（死代码清理 Builder 裁量，删则 grep 证明零引用） | George 2026-07-03（IPO14） |
| S2 | hub「TRACKING 徽标已拍板去掉、勿回归」（spec hub §布局 1 / delta 表末行） | **收窄**：呼吸点视觉回归 + 措辞改真（「EOD · 收盘」类）；被禁的是假实时**措辞/语义**而非圆点本身 | §0 D3（后出拍板胜） |
| S3 | banner「TRACKING 已删维持、默认不恢复」FLAG（spec banner 站规 §1） | 同 S2：恢复 dot + 诚实措辞（BANR3） | §0 D3 |
| S4 | 跌色 #cc0000 于 wave-2 六表面（hub delta#7 / sector FLAG 的「默认保 #cc0000」） | wave-2 reskin 表面一律 **#c8102e**；全局 token 不动 | §0 D2 |
| S5 | 六区块旧 masthead/节标/容器样式（sector th 红字红线、hub Inter 34px、hero 平面卡等 current-state 基线细节） | 被各 spec 新 token 取代——**外观 diff ≠ regression**，按 §2 断言核 | D1（本任务即换肤） |
| S6 | treemap 惯例 banner 的「⚠」前缀字符 | 删除（NEW 设计 + 站规 emoji/警示字符收紧） | spec treemap |

### K — 仍有效，照核（回归即 FAIL）

- **mountEChart 强制**：所有 echarts 面（treemap `#m`、hero `#eq`/`#cmp`）经 `echarts_boot.MOUNT_JS`，零裸 init、ResizeObserver 在；hub sparks 当前 SVG——**若任何区块未来改 echarts-based，同样必须走 mountEChart**，本轮不改。
- 自托管 echarts / 字体 **相对路径**无前导斜杠（Cloud 前缀）；srcdoc `html,body{height:100%}` + 容器显式 px 高。
- **teal #0d7680 = 涨 / 红 = 跌** 语义（HK-US），惯例 banner 保留且加强；A 股误读护栏不删。
- 符号染色 INVARIANT：策略 cum/α/MDD 等自身盈亏必须按符号取色（负=红），design mock 全正例不构成硬编 teal 授权。
- IPO `day1_ret` = DECIMAL（×100 一次于 render）；`code` str 前导零。
- `build_domain_bento` payload 形状（ETF 页共享）；`render_index_tiles`/`render_treemap_html`/`benchmark_table`/`movers`/`overview_strip`/`render` 公共签名兼容（可加带默认值新参，不破位置/语义）。
- 多小图面（hub/sector/banner）**inline SVG 禁 echarts**（0 宽竞态）；sector/banner **不迁 iframe**。
- hero 渲染 gate（L224-229 等价）、count-up `[data-count]` 协议、`json.dumps` 字体注入、`@media 860px` 断点、`render_compare_chart` 不动。
- banner 中/EN 真锚点交互、gradient id 唯一、`load_ipo` 缓存/dtype 管道。
- i18n zh/en parity；无 emoji；无 box-shadow；radius ≤4；tabular-nums；color-scheme:light（有此声明的 srcdoc 保留）。
- **wave-1 契约对 Ticker Drill 全量有效**（P1-P10/T/C/G 不受本契约影响）；PR-based 流程不直推 main；签名/规格对不上先停下问，不硬凑。

## §5 Evaluator 独立协议

- Evaluator = **独立 context**（未写过本任务任何代码），**零 app 代码编辑权**；只写 `docs/harness/reskin-wave2/eval/round-N.md`、证据存 `eval/`（或 `eval/evidence/`）。
- **唯一有权翻 `feature_list.json` 的 `passes` 位者**；每翻一位必须挂真机证据（JS/EO 输出、截图、grep 输出、AppTest log），无证据的 PASS 无效。
- 失败报告格式：验收项 id + 期望（契约原文）vs 实测 + file:line + 证据路径；Builder 只凭报告修复，不得改契约/改验收方法。
- 断路器：**max_cycles=4**；**同一验收项 3 连败 → 停机上报 George**（附卡点分析），不无限烧。
- 验收顺序建议：先 GRD1-4（静态电池，秒杀低级违约）→ 再 RM 冒烟 → 再逐区块 JS/EO → 最后 SS 旁证。

## §6 Codex Auditor scope（read-only 异模型终审）

`codex exec --sandbox read-only`，物理零改权。审：
1. **token 机械比对**：§2 各表逐 hex/px/字重 对最终渲出 HTML（srcdoc 落盘后 `node --check` + 文本比对）与 echarts option；
2. **数据无造假**：IPO dock 路径逐点对 `ipo_day1_intraday.csv`；无路径票确实空态非伪线；hero/banner 曲线首尾值对 `compute_strategy_returns` 复算；hub spark 对 `close_series`；treemap tiles 对 payload；KPI/分档/分布数字对 CSV 实算——**抽查各 ≥2 例**；
3. **GR 电池独立复跑**（§3 全 12 条 + 白名单核真）；
4. **INVARIANT 按 §4 核**：S 表内改废项**勿报** regression（含 D2 跌色、D3 徽标、S1 小图墙移除）；K 表逐条核；
5. **spillover/泄漏**：SOVR 两页 + GRD5 三个未触页 + e2_etf_heatmap payload 回归；
6. 契约外漂移（改了契约没写的公共面）→ 上报，不自行裁决。

---

## 附录 N · 协商与冲突归一记录（Evaluator-side assembler，2026-07-03）

六份 spec 由独立 extractor agents 产出（Builder 侧视角内嵌于各 delta 表）；本契约装配时发现并归一以下冲突。**FREEZE-BLOCKER：无。**

| # | 冲突 | 双方 | 归一 |
|---|---|---|---|
| N-1 | 跌色 #cc0000 vs #c8102e：hub delta#7「默认保 #cc0000 需 George 裁」、sector 站规 FLAG、banner/hero 已按 page-scope 写 | specs 间口径不一 | **§0 D2 一揽子裁决**：wave-2 全 reskin 表面 #c8102e，全局 token 不动。specs 的 FLAG 全部关闭 |
| N-2 | 呼吸点/TRACKING：hub spec「徽标已拍板去掉勿回归」、banner spec「默认维持删除，FLAG 需拍板」 vs §0 D3「KEEP visual + 语义改真」 | 旧拍板 vs 新拍板 | **D3 胜**（2026-07-03 后出且显式覆盖 wave-2）：dot 视觉回归、措辞诚实（EOD/BACKTEST/DAILY）、假实时字样仍禁（GR⑪ 兜底）。旧拍板的真意（不装实时）被措辞约束完整继承 |
| N-3 | 零泄漏抽查页集：brief 例举「Healthcare/SEC Facts」，但 Healthcare 是 wave-2 opt-in 页（sector_overview 双页 spillover + page_radial_wash） | brief vs current-state 事实 | 抽查集改为 **SEC Facts + Capital Markets + e2_etf_heatmap**（GRD5）；Healthcare 转入 SOVR1 正面验收 |
| N-4 | IPO 排行表列数：design 7 列 grid vs George 2026-07-03 点名保留「上市日期」附加列 | design vs 拍板 | **8 列**：7 个 design 列 token 照断，附加列位置/轨宽 Builder 定（IPO9 契约钉住，Auditor 勿报「多一列」） |
| N-5 | 样本数字：`load_ipo` docstring「18 rows」stale（实际 54 = 38 listed + 16 pending，且会继续增长） | current-state ⚠ | 验收断言**动态**（= len 实算），不断言 54/38/16 字面量；Builder 顺手修 stale docstring 允许、不列硬项 |
| N-6 | hero `#eq` 高：spec §A2 写「echarts 容器 100%×300」（design token）vs 同 spec §C8「不动 #eq 290」 | spec 内部矛盾 | **290 胜**（§C/§F 现契约 + iframe height 470 预算既定）；10px 差不构成违约 |
| N-7 | treemap 画布高：design 700 vs home 多域 600 / 单域 720 现逻辑 | design vs 调用现实 | 保留 home 高度逻辑（TMAP12「~700 等价带」）；spec 本身已授权此适配 |
| N-8 | 玻璃配方参数不一：hub/banner 速览/ipo KPI = rgba .55 + 顶边 3px；sector 表 = rgba .5 无顶边；ipo dock = rgba .6/blur16；hero = .55 + 红顶边 | 各 design 有意分层 | **按各 spec 的 token 分别断言**，不强行统一四值；D5 的「复用」指 wash 函数 + 配方族纪律（页级注入、不进全局），非单一配方值 |
| N-9 | sector movers d1 格式：design 带负号「▼ -16.0%」vs 现码 `abs()` 去号 | design vs 现码 | 跟 design（SOVR10）——负号消歧义优于视觉洁癖 |
| N-10 | GR④ 伪随机电池误伤风险：banner gradient id 用 `hash(name)`（确定性、非序列伪造） | 电池 vs 合法用法 | 电池限定「新增/改动 srcdoc JS 的序列生成」，Python 确定性 hash 用途逐个白名单（§3-GR④ 已注明） |
