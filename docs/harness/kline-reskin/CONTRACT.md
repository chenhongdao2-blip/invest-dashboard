# CONTRACT — K线行情 FT-salmon glass 1:1 重实现 · Ticker Drill 整页 (harness · code mode)

Status: **FROZEN 2026-07-03** — George 批准 plan(含 D1-D5 + O2-O4 默认值)后冻结。
Design source of truth: Claude Design 项目 26a29f87 `K线行情.dc.html`(DesignSync get_file 2026-07-03 拉取);
规格提取与实现方案存 `~/.claude/plans/use-the-claude-design-mcp-curried-wilkes.md`。
Builder↔Evaluator 协商记录见文末附录 N。

## §0 已钉定开放项

| id | 钉定 | 依据 |
|---|---|---|
| O1 跌色 | **#c8102e**(蜡烛/量柱/跌字/chip 底,仅本页新皮;`theme.DOWN="#cc0000"` 全局 token 不动) | George D5 2026-07-03 |
| O2 字体 | 自托管 `app/static/fonts/space-grotesk-var.woff2`(OFL,循 Inter 先例);iframe srcdoc 也注入 @font-face | George 批 plan 默认值 |
| O3 时段文案 | 按交易所映射真实时段(HK 09:30—16:00 / US 09:30—16:00 ET / A股 09:30—15:00 UTC+8);缺映射回退「EOD 收盘」 | 同上(D1 语义改真延伸) |
| O4 列表模式 | 共享 底色+双 wash+页头语言;quote_table 本身不动 | 同上 |

## §1 宏观 spec(Planner)

`K线行情.dc.html`(FT-salmon glass)1:1 还原到 Ticker Drill:行情终端 iframe 整层换肤 + 整页(masthead/各区块)统一新设计语言。数据全真(EOD yfinance/DB),无任何 mock 行为。渲染纪律不变:st.iframe srcdoc + 自托管 echarts + mountEChart(echarts_boot.MOUNT_JS)。新皮 CSS **页面局部注入**(6_Ticker_Drill 内),禁进 theme._CSS 全局。

## §2 验收清单(35 条,逐项独立 PASS/FAIL;方法代号见 §3)

### P — 页面级(Streamlit DOM)

| id | 断言 | 方法 |
|---|---|---|
| P1 | 页身底色 `#fff1e5`(stApp/stAppViewContainer computed background) | JS |
| P2 | 页级双 radial 洗:computed backgroundImage 含 `radial-gradient(900px 520px at 10% -8%, rgba(200, 16, 46, 0.09)` 与 `radial-gradient(820px 520px at 94% 4%, rgba(13, 118, 128, 0.1)` 两段 | JS |
| P3 | 页头 masthead:红竖条 **5×44px #c8102e** + 股名 **30px/700** + 代码 chip(mono,border `#e4d2bd`)同排 | JS+SS |
| P4 | 页头底 rule `2px solid #1a1a1a` | JS |
| P5 | 页头副行 mono 12.5px:`日K线 · MA5/MA10/MA20 · 成交量 · <O3 时段>` | JS+SS |
| P6 | EOD 状态块:青呼吸点 `#0d7680` + animation 周期 1.5s 无限;文案 `EOD 数据 · 截至 YYYY-MM-DD`(真 as-of);可含真实时钟;**全页零** `tick interval` 字样、零 暂停/重置按钮 | JS+GR+SS |
| P7 | 标题字 Space Grotesk 自托管相对路径 + **iframe srcdoc 内 @font-face 存在**(修字体注入 bug);数字 JetBrains Mono;全 repo 零 `fonts.googleapis.com|fonts.gstatic.com` | JS+GR |
| P8a-f | 六区块玻璃配方统一(=T3 四值断言:bg `rgba(255,255,255,0.55)`、`blur(14px)`、`border-top:3px solid #1a1a1a`、`border-radius:0`,且 `box-shadow:none`):a KPI带 / b consensus_house / c 多空看板 / d memo bar / e stat strips / f expander 面 | JS |
| P9 | 新皮零泄漏他页:Sector Heatmap + Strategy Picks 抽查无 wash/新卡皮;theme._CSS 零本次新增规则 | RM+GR |
| P10 | zh/en 双语等价(pages_zh/pages_en parity 保持);零新增 emoji | RM+GR |

### T — 终端 iframe(srcdoc)

| id | 断言 | 方法 |
|---|---|---|
| T1 | `html,body{height:100%}`、`color-scheme:light`、底 `#fff1e5` | JS |
| T2 | iframe 内双 radial 洗同 P2 参数 | JS |
| T3 | 玻璃卡配方(图卡+右侧全部卡):四值断言同 P8,**且删除现行 pcard box-shadow(原 :219)** | JS |
| T4 | 主栅格 `grid-template-columns: 1fr 340px; gap: 26px` | JS |
| T5 | Last Price 卡:eyebrow mono 11px/.16em;价格 **46px/700 mono**,涨 `#0d7680`/跌 `#c8102e` 动态;币种后缀 | JS+SS |
| T6 | change 行:带符号绝对值 + pct chip,chip 底 `rgba(13,118,128,.12)`(涨)/`rgba(200,16,46,.10)`(跌) | JS |
| T7 | OHLC 卡四行:高=`#0d7680`、低=`#c8102e`、开/收=墨 | JS |
| T8 | 指标卡 only-available(D3):振幅(必)/ 量比=当日量÷前5日均量,标「量比(5日)」诚实口径 / 换手率=当日量÷股本(缺股本不渲)/ PE(mults forward→trailing,缺不渲);格数 4→3→2 退化;**零 2.69/1.34/28.4 演示字面量** | JS+GR |
| T9 | iframe 内零按钮、零假 tick setInterval(数据不被定时器改动;真实挂钟白名单) | GR+JS |
| T10 | 页脚注 = `配色(港美股惯例):青 = 涨 · 红 = 跌(与 A 股红涨绿跌相反)` + 真 provenance(yfinance·复权·截至日);**零 MOCK 字样** | SS+GR |
| T11 | 页模式图容器 560px;modal 模式按 height 参数缩放不裁切 slider | JS+EO |

### C — echarts option(contentWindow getOption 探针)

| id | 断言 | 方法 |
|---|---|---|
| C1 | 蜡烛 `color:#0d7680, borderColor:#0d7680, color0:#c8102e, borderColor0:#c8102e` | EO |
| C2 | MA5 `#e0963c` / MA10 `#b8b1a8` / MA20 `#1a1a1a` | EO |
| C3 | 三 MA `width:1`、`smooth:true`、`symbol:'none'` | EO |
| C4 | legend 左上、mono、fontSize 11 | EO |
| C5 | tooltip `backgroundColor:#1a1a1a`、text `#fff1e5`、cross 虚线 `#b8b1a8`;formatter 出 开/收/低/高 | EO+SS |
| C6 | 双 grid = 设计绝对值 44/320/400/110 ÷ 560 的 **% 值**(≈ top 7.9%/h 57.1% + top 71.4%/h 19.6%),modal 480px 仍成比例 | EO |
| C7 | y 轴 `position:'right'`;splitLine=theme.PAPER_RULE(#ebd9c8,≈设计 #eadbc8,token 单一真相源);x 轴线 `#d4c4b0` | EO |
| C8 | dataZoom inside + slider(`bottom:6,height:14`),filler `rgba(200,16,46,.12)`、handle `#c8102e`、border `#d4c4b0` | EO |
| C9 | 量柱 `rgba(13,118,128,.5)` / `rgba(200,16,46,.5)` 按当日阴阳 | EO |
| C10 | series 名集合恰为 `{日K, MA5, MA10, MA20, Vol}`,零基准 series(D2) | EO |
| C11 | 经 `mountEChart('kc',…)` 挂载;`__echartsRO` ResizeObserver 在;零裸 `echarts.init` | EO+GR |

### G — 工程守卫与回归

| id | 断言 | 方法 |
|---|---|---|
| G1 | `py_compile` 全改动 .py clean | RM |
| G2 | AppTest:Ticker Drill `000977.SZ` + `000660.KS` + 一只美股 无异常 | RM |
| G3 | `init.sh` 重启 :8599 → HTTP 200;详情页连刷 3× 每次蜡烛出图 | RM |
| G4 | grep 电池(§3-GR 10 条)零命中 | GR |
| G5 | bench 通道全删:`_terminal_bench_overlay` + 调用点/caption + `bench_overlay` 参数及 option/tooltip 分支;repo 零 `bench_overlay|benchName` 引用 | GR |
| G6 | `kline_picker` modal(home.py:190 入口,show_header=True)新皮渲出不崩(accepted spillover) | RM+SS |
| G7 | 无 OHLCV 票 plotly RS 回退仍工作(`_route_benchmarks` 保留) | RM |
| G8 | 列表模式按 O4:壳新皮、quote_table 功能不变 | RM |
| G9 | 1440×900 定视口截图 vs 设计稿并排 gestalt 一致(旁证;判定以 JS/EO 为准) | SS |

## §3 验收方法(Stage 2 · 独立 Evaluator · 真机)

- **RM**:`docs/harness/kline-reskin/init.sh`;改 lib 后必须 kill+relaunch(热进程缓存);AppTest/py_compile 走 `.venv/bin/python`。
- **JS**:claude-in-chrome `javascript_tool`。srcdoc iframe 同源:`var f=[...document.querySelectorAll('iframe')].find(f=>(f.srcdoc||'').includes('id="kc"')); var d=f.contentDocument;` → `getComputedStyle`。断言用 rgb() 归一形。
- **EO**:`f.contentWindow.echarts.getInstanceByDom(f.contentDocument.getElementById('kc')).getOption()`。
- **SS**:参照 = Claude Design 画布截图(首选)或 DesignSync 源剥壳本地渲;实现 = Browser :8599 定视口 1440×900。截图为旁证,颜色/尺寸判定一律 JS/EO。
- **GR 电池(零命中,白名单注明)**:① `echarts.init(` 除 echarts_boot.MOUNT_JS ② `fonts.googleapis.com|fonts.gstatic.com` ③ `src="/app/static|url('/app/static` 绝对路径 ④ `setInterval` 于 candlestick_terminal/6_Ticker_Drill(stock_header 真挂钟白名单一处)⑤ `bench_overlay|_terminal_bench_overlay|benchName` 全 repo ⑥ `MOCK`(app/ UI 串)⑦ `2\.69|1\.34|28\.4` 演示字面量(改动文件)⑧ `box-shadow`(新皮 CSS 域)⑨ emoji(新增 UI 串)⑩ `border-radius:\s*([5-9]|\d{2,})px`(新皮域)。

## §4 SUPERSEDED INVARIANTS(对 docs/harness/echarts-race/CONTRACT.md 的显式改废;Auditor 勿报 regression)

| 旧 INVARIANT | 本契约处置 | 依据 |
|---|---|---|
| MA 金/青石蓝/黛紫 不变 | 改 #e0963c/#b8b1a8/#1a1a1a | George D-1:1 授权 2026-07-03 |
| benchmark 虚线叠加语义不变 | 全通道删除(G5/C10) | George D2 |
| option 语义不变 | 外观值有意变更(C5-C9);底线=数据序列真实零捏造 | 本任务即换肤 |
| 跌 red #cc0000 不变 | 本页新皮 #c8102e(全局 token 不动) | George D5 |

**仍有效,照核**:mountEChart 零裸 init / 自托管 echarts 相对路径 / 涨 teal #0d7680 + 页脚惯例注 / 无假 tick 无 mock / 无 emoji / 无 box-shadow / radius≤4(卡=0)/ tabular-nums / color-scheme light / srcdoc height:100% / PR-based 不直推 main / 签名对不上先停下问。

## §5 Evaluator 独立协议

独立 context(未写过本任务代码),**零 app 代码编辑权**;只写 `eval/round-N.md`、翻 `feature_list.json` passes 位(唯一有权者)、证据存档 `evidence/`。失败报告 = 验收项 id + 期望 vs 实测 + file:line + 证据路径。断路器:**max_cycles=4**,同项 3 连败停机上报 George。

## §6 Codex Auditor(read-only 异模型)

token 机械比对(§2 表逐 hex/px 对最终 HTML/option)/ option 语义(series 恰五件套零捏造)/ 无造假(D1 落实、T8 真判非硬编码)/ INVARIANT 按 §4 核 / GR 电池独立复跑 / 契约外漂移上报。`node --check` 渲染后 srcdoc HTML。

---

## 附录 N · Builder↔Evaluator 协商记录(Stage 0.5)

双侧由独立 context 的两个 Plan agent 分别产出(实现侧=Builder 视角 2026-07-03 / 契约侧=Evaluator 视角 2026-07-03),冲突由 orchestrator 归一、George 拍板:

| 冲突点 | Builder 侧 | Evaluator 侧 | 归一 |
|---|---|---|---|
| 跌色 | #cc0000 语义 token | O1 默认 #c8102e | **George D5:#c8102e**(页级豁免) |
| grid 尺寸 | % 制(modal 480px 兼容) | px 制照设计 | **% 制**(C6 按比例断言;绝对值仅 560px 页模式下等价) |
| 量比可得性 | 可算(5日均量口径) | 需盘中数据,疑不可得 | **可算**,标「量比(5日)」诚实口径(T8) |
| G5 bench 处置 | 全删(死代码烂) | 全删 vs 留参待议 | **全删**(G5) |
| 字体注入 | 发现 iframe 缺 @font-face bug | 未覆盖 | **P7 扩展**:断言 srcdoc 内 @font-face 存在 |
| 时钟 setInterval | 真挂钟允许 | 全禁 setInterval | **白名单一处**(stock_header 真挂钟;GR④) |
