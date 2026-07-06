# WAVE-3 CONTRACT（冻结 2026-07-05）— 眼验反馈三连修

> 冻结自三轮磁盘博弈：`contract-draft-builder.md`（Builder v1，26 项）→ `contract-critique-evaluator.md`
> （Evaluator：ACCEPT 15 / HARDEN 12 / REJECT 1 / MISSING 7）→ `contract-response-builder.md`
> （Builder round-2：全收 + 2 项机制加固 + 合并清单 C01-C44）。
> 唯一 DISPUTED（C43 / GBL-1）由 Planner 裁决，见 C43 条目。协商细节与判据 rationale 以上述三文件为准；
> **本文件 = Evaluator 打分唯一锚**。基线 HEAD `154a36c`，分支 `feat/kline-reskin`。

## 验收方法代号

- **RM** — 重启 :8599（`bash docs/harness/kline-reskin/init.sh`，lib 改动后强制）/ py_compile / AppTest
- **JS** — claude-in-chrome 真机：computed-style / DOM 断言 / 真点击 / 真滚动（**运行时行为项的唯一 PASS 依据**）
- **GR** — grep 源码电池（macOS 用 `grep -E`，禁 `-P`）
- **PS** — `_build_html` / helper 纯字符串探针（**仅廉价静态门，不得替代真机**——wave-1 echarts 静态探针假阳性前车之鉴）
- **SS** — 截图旁证

**纪律**：凡「运行时行为」（排序/滚动/hover/语言真切/dock 可视）PASS 唯一依据 = 真机 JS；合成事件（dispatchEvent 捷径）不作为可视性判据——必须真滚到底 + 真 rect。

## §0 不动面（NT1-7，Builder 承诺、Evaluator 抽查）

| id | 冻结项 |
|---|---|
| NT1 | wave-2 §0 D1-D5（#c8102e 页级跌色豁免 / D3 呼吸点语义诚实 / 自托管字体 / D5 玻璃壳原语 / theme.DOWN 不动） |
| NT2 | BANR1-12 逐条；尤其 BANR2（toggle 只换皮不换 `?lang=` 机制）、BANR4（dek 14/1.65/#4a4a4a/max-880 + 包装器 `4_Strategy_Picks.py:146-149` 四行字节不动）、BANR7/8/9 |
| NT3 | IPO1-15 数字级：d1 DECIMAL ×100 仅一次 / code str 前导零 / None-NaN 诚实 `—` / pending rank `—` 沉底 / 末笔 NaN 整路径丢弃（ipo_stage.py:455-466）/ 终点=首日收盘锚 / 零伪造路径 / 零 MOCK / 零 demo 字面量 |
| NT4 | `theme._CSS` 零新增规则；F1 新皮走 i18n 模块内 inline HTML，不进 theme._CSS |
| NT5 | `load_ipo`/`load_ipo_intraday`/`compute_strategy_returns` 签名不动；排序只动展示顺序、禁碰数值计算 |
| NT6 | `sector_overview.masthead`（Healthcare/AI 板块小节头）不在本 wave 范围 |
| NT7 | 自包含 srcdoc HTML / 无外部 JS 库 / 改 lib 必重启 :8599 |

## §1 验收项 C01-C44

### F1-toggle（中英模块全站统一）
| # | 断言 | 方法 | PASS 判据 |
|---|---|---|---|
| C01 | `i18n.lang_toggle_html()` 返双锚 `<a href="?...lang=zh\|en" target="_self">` + 段 CSS(mono 11px/600/.08em/p5-12) + 容器 border 1px #d4c4b0 radius3 | PS(zh/en 两态) | 双锚在 + CSS token 齐 |
| C02 | active 段 bg#c8102e 字#fff1e5 / inactive transparent 字#8a8580，随 `get_lang()`；无 state 走 zh 不崩 | PS(两态+空 state) | 三态配色正确 |
| C03 | 三页(8_SEC_Facts/e2_etf_heatmap/2_Healthcare)真机描边锚点在；旧钮清零 | JS+GR | 三页 `a[href*="lang=en"]` 在 + `grep st.button app/lib/i18n.py`=0 + `grep -rn _lang_btn app/`(排 .omc)=0 + `.st-key-_lang_btn`==0 |
| C04 | 真机点非策略页 lang 段 → 整页切语（等 reload 完再断） | JS+SS | 该页已知 t() 串由中变英、回切还原 |
| C05 | banner toggle == 页 toggle 同一 helper 产物：两处 `<a>` computed(font-size/weight/letter-spacing/padding/background/color) 逐字段等 + 容器 border/radius 达标（BANR2 不回归） | JS | 计算样式全等 |
| C06 | qp 读取单源仅 i18n.py（init_lang 内） | GR | `grep -En "query_params.get\(.lang" app/` 命中仅 i18n.py 1 处 + `grep _qp_lang app/pages/4_Strategy_Picks.py`=0 |
| C07 | 19 调用点零改动 + `render_lang_toggle` 无必填参 | GR+PS | 19 处全裸调（含 model_drill.py:28）+ 签名无必填参 |
| C08 | py_compile + AppTest(5_Valuation_Scanner/8_SEC_Facts/home/4_Strategy_Picks × zh/en) | RM | 各跑完无 raw key / TypeError / import 环 / rerun 上限 |
| C09 | **[HIGH]** lang toggle 保 sibling query params：`8_SEC_Facts?ticker=<票>` 与 `model_drill?ticker=<票>` 切语言不丢票 | JS | URL 含 `ticker=<票>` 与 `lang=en` 且页面仍锁该票（详情不重置） |
| C10 | **[声明]** anchor 整页 reload 抹非 lang widget 态 = BANR2 既有机制、George 已接受的行为，非回归 | 契约明文+SS(e2 一例旁证) | 声明在本条 + 旁证归档 |

### F2-pitch（strategy.pitch B 口径）
| # | 断言 | 方法 | PASS 判据 |
|---|---|---|---|
| C11 | zh.pitch **字符级 == canonical**（见下 §2 pin，含全角标点/三 `**` 锚/段间 `\n\n`）；旧文案消失 | PS+GR | `grep 这是什么 app/lib/locales/zh.py`=0 + 逐字符相等 |
| C12 | zh 态策略页 dek：`<b style="color:#1a1a1a;">`×3 + `<br><br>`≥1 | JS | 三墨色粗体 + 段隔在 |
| C13 | en.pitch 恰 3 个 `**` 锚（Methodology / logged…day it is selected / real cumulative return…since selection）+ `\n\n`；zh/en `t()` ≠ key 自身 | PS | 3 锚齐 + 段隔 + 非 raw key |
| C14 | en 态 dek 同 C12（镜像） | JS | 三墨色粗体 + 段隔在 |
| C15 | BANR4 不回归：dek `<p>` computed 14px/1.65/#4a4a4a/max-880；包装器 146-149 四行字节未改 | JS+GR diff | computed 达标 + 字节不变 |

### F3-ipo-rank（列排序 + dock 重设计）
| # | 断言 | 方法 | PASS 判据 |
|---|---|---|---|
| C16 | **[HIGH]** iframe 定高 + 结构零溢出：body `height:100vh;flex-col;overflow:hidden`，masthead/KPI/tier/footer `flex:none`，`.rank-grid` `flex:1;min-height:0`，`.rank-scroll` 唯一滚动源 | GR+JS | `grep "max(2400" app/lib/ipo_stage.py`=0 + 常量 `_FIXED_H` 在 + 真机 `scrollHeight ≤ _FIXED_H+2` + `.footer` rect.bottom ≤ _FIXED_H |
| C17 | **[HIGH]** 末行 hover dock 可视（缺陷 b 核心）：真滚到底三步——①`.rank-scroll` scrollTop=scrollHeight 后末行(第 n) rect 落在容器可视带；②hover 末行；③dock 内容切为末行股名+涨幅 且 dock rect ∈ [0,_FIXED_H] | JS+SS | 末行可达 + dock 载荷==末行股 + dock 全在视口 |
| C18 | **[HIGH]** `.rank-scroll` overflow-y:auto + thead `position:sticky;top:0`（真滚到底后 `\|thead.top − container.top\| < 2px`）+ `.dock` position:static | JS(computed+真滚) | 三 computed 达标 + 表头真钉住 |
| C19 | 点「首日涨幅」th：desc（首行=最高首日 listed）→ 再点 asc（首行=最低首日 listed）+ ▲/▼ 指示器切换 | JS(真点击) | 两向首行正确 + 指示器随向 |
| C20 | 换列初始方向：name asc / score desc / list_date desc | JS(逐列点击) | 各列首行符合初始方向 |
| C21 | **[HIGH]** pending 沉底四向：(i)score↓ (ii)score↑ (iii)name↑ (iv)date↓ 每种下所有 pending 行 DOM index > 所有 listed 行；listed-空日期行居 listed 组末（pending 沉底优先级更高） | JS(四向) | 四向全沉 + 空日期边缘正确 |
| C22 | `#` 列 = 评分档原始名次（身份锚，排序不重编号；pending 恒 `—`） | JS | 按首日涨幅排序后位移行 `#` ≠ 必然 "01" |
| C23 | 数值零篡改（NT5）：排序前后同 code 行 评分/首日涨幅/tier 文本恒等；d1 仍 ×100 一次 | JS(diff 同 code) | 逐单元格恒等 |
| C24 | NT3 逐条不回归 | PS(现 5 self-test case 全 PASS)+GR | 零命中电池（Math.random/genData/MOCK/硬编字面量） |
| C25 | self-test exit 0 + 新 Case6-9（TIER_ORDER 注入 / 8 列 data-key / 排序+沉底 JS 标识 / 默认序&DEFAULT_CODE 不变）+ py_compile + AppTest；**初始态（未点击）tbody 行数据序 == 评分降序 == wave-2 现状**（thead 新 chrome 允许，行数据序不得变）；排序类 PASS 唯一依据=真机 C17-C21/C27 | RM+JS | 退出 0 + 初始序断言过 |
| C26 | **[HIGH]** 注入 `TIER_COLORS`/`TIER_ORDER` 与 py `_TIER_COLORS`(L30-36)/`_TIER_ORDER`(L37) 单源一致 | JS+PS | 注入值逐项相等 |
| C27 | **[HIGH]** 排序后 hover→dock 零 stale：重排须重绑 mouseenter + `activeCode=null` 复位 | JS | 排序后 ≥2 个不同行 hover，dock 名/涨幅逐一命中所 hover 行单元格 |
| C28 | `.rank-scroll` 滚动条纸皮调和（定制 ::-webkit-scrollbar） | JS(computed) | 宽 ≤10px + thumb INK_3 系半透 + track 透明 |
| C29 | 「申购档」列排序 = TIER_ORDER 序（重点申购+→…→不申购）+ 未知档沉 listed 组末 + pending 仍全沉 | JS(点击) | tier 序==TIER_ORDER + 边缘正确 |

### F4-home-dedup（首页双标题）
| # | 断言 | 方法 | PASS 判据 |
|---|---|---|---|
| C30 | 单标题：`[data-testid="stMain"]` 内「行情中枢」计数==1（HUB masthead）+ `.cmsi-page-hero`==0 | JS+SS | 计数正确 |
| C31 | fetch 时间折入 masthead 时间戳行（zh/en 双语分支都带）；fetch_utc=None 降级 `—` 不崩 | JS+PS | 时间戳行含 latest + fetch_utc[:16] 两段 |
| C32 | `grep page_header app/home.py`=0 + py_compile + home AppTest 无异常无 raw key | GR+RM | 全过 |
| C33 | 删后顶部无空白遗留：主内容区首个可见块==HUB masthead + 无空壳 stMarkdown；范围守卫 `sector_overview.masthead` 未碰（NT6）；home.py diff 仅两处（删 page_header + 改时间戳行） | JS+SS+GR | 三判据全过 |
| C34 | `home.title` locale parity：zh/en 同去或同留（无单语言孤儿，守 GRD3） | GR | parity 成立 |

### 回归电池 + 全局
| # | 断言 | 方法 | PASS 判据 |
|---|---|---|---|
| C35 | R-1 BANR4 dek+包装器不回归（=C15，双列一次执行） | GR diff+JS | 同 C15 |
| C36 | R-2 BANR2 banner toggle computed（active #c8102e/#fff1e5 + 容器 1px#d4c4b0 r3 + 段 mono11/600/.08em/p5-12） | JS | 全达标 |
| C37 | R-3 IPO9 8 列结构 + `padStart(2,'0')` + pending rank `—` | JS+PS | 全在 |
| C38 | R-4 IPO12 盘中锚（CRITICAL）：Case5 endpoint 100.0 + Case4 无 pts + 零 Math.random/genData | PS+GR | 全过 |
| C39 | R-5 IPO4 KPI live（+384.0%/-56.9% 实算，零硬编字面量） | PS+GR | 全过 |
| C40 | R-6 IPO7 五档色单源（=C26；五色 a00d25/c8102e/0d7680/a06d1f/6b6560） | JS+PS | 全过 |
| C41 | R-7 BANR7 α chip 符号染色 + 大号 mono32 tabular | JS | ≥0 青/青底，<0 红/红底 |
| C42 | R-8 GRD7 重启冒烟（**所有真机验收的前置门**）：init.sh 重启 → home/Strategy/Healthcare/AI 200 + echarts 连刷 3× 出图 | RM | 全过后才开始 JS 项 |
| C43 | **[HIGH · Planner 已裁决]** GBL-1 全量 smoke = **差分门**：同一脚本（`apptest_matrix.py`）在基线 `154a36c`（干净 worktree + 本地数据镜像）与改后各跑 19 页+home × zh/en。PASS = ①矩阵逐页逐态 diff **零新增异常**（预存在数据层异常以基线实证豁免、逐条记入 eval）② 全矩阵零 raw i18n key ③ 零 rerun 上限 ④ 零 i18n/toggle 路径 TypeError | RM(差分) | 四判据同时成立；豁免必须有基线证据，Evaluator 执行 diff，Builder 不得自报白名单 |
| C44 | GBL-2 验收顺序：GR/PS 静态 → C42 重启冒烟 → 真机 JS → SS；4_Strategy_Picks.py 仅 F1 一方改写（F2 只碰 locales），C35 diff 审兜底 | 流程+GR | 顺序遵行 |

## §2 F2 canonical 文本（pin，字符级）

**zh `strategy.pitch`**（两段，`\n\n` 分隔；`>` 为本文档排版不入值）：

> **方法论** — 本页跟踪一套量化基本面（Quantamental）选股体系的实盘表现：以临床试验读出、FDA 审批进度、财报披露与公司治理事件为输入，按多维度评分筛选入池。**持仓自入选之日起登记在册**，业绩以原始记录为准复盘，盈亏均客观呈现。
>
> 下方三个策略展示**自选股日起的真实累计收益 vs 基准**（非回测美化）。

**en `strategy.pitch`**：

> **Methodology** — this page tracks the live performance of a quantamental stock-selection system: it ingests clinical-trial readouts, FDA review milestones, earnings disclosures and governance events, then scores and screens names into the pool across multiple dimensions. **Every holding is logged on the record from the day it is selected**, and performance is reviewed against that original record — wins and losses shown alike.
>
> The three strategies below show **real cumulative return vs benchmark since selection** (not a polished backtest).

## §2.5 Stage-5 眼验修正案（George 直接反馈，Planner 增补 2026-07-06）

| # | 断言 | 方法 | PASS 判据 |
|---|---|---|---|
| C45 | **[HIGH · George 眼验]** dock 恒不压 footer：dock 改有界 flex 列（`max-height:100%`，头部/脚注 flex:none，图表区 flex:1 收缩、按容器实测尺寸绘制），结构上不可能溢出排行区 | JS(真机**双宽度**：默认宽 + resize 到 ~1000px 窄宽) | 两宽度下 `dock.getBoundingClientRect().bottom ≤ .footer.getBoundingClientRect().top`（严格不重叠）+ dock 脚注（区间高/低行）可见 + 图表无文本变形 |

> 背景：C17 在 evaluator 视口宽度下通过，但窄窗口 tier/masthead 换行增高挤压排行区，dock 内 SVG 固定高不收缩 → 溢出盖 footer（George 截图实证）。C45 把判据从「单视口 rect」加硬为「双宽度 + 结构有界」。

| # | 断言 | 方法 | PASS 判据 |
|---|---|---|---|
| C46 | **[George 眼验]** 策略页 hero 净值曲线终点标签（`策略 XX.X` / `基准 XX.X`）不被画布右缘裁切：`strategy_hero.py` hero 图 `grid.right` 从 58 扩到足够容纳最宽标签（`策略 100.0+` 11px mono bold + distance），同文件第二张对比图按同口径复核 | JS(真机：endLabel 文本完整渲出，末字符 rect ≤ 画布右缘) + SS | 两曲线终点标签全字符可见；plot 区左移量不破 HERO 既有验收观感（George 终裁） |

> C46 备注：grid.right=58 若为 wave-2 设计包冻结值，本条为 George ship-gate 直接反馈，**优先级高于装饰性冻结值**——契约据此修订，evaluator 在 eval 中记录该 delta。

## §3 角色与循环纪律

- Builder（Workflow 4 路并行，F1={i18n.py, strategy_banner.py, 4_Strategy_Picks.py} / F2={locales/zh.py, en.py} / F3={ipo_stage.py} / F4={home.py}，文件互不相交）**物理禁碰**：`CONTRACT.md` / `feature_list.json` / `eval/` / `apptest_matrix.py` / baseline 产物。
- Evaluator 独立 context，按本契约逐条打分，写 `eval/round-N.md`，翻 `feature_list.json` passes；失败项带 critique + 代码位置退回。
- 断路器：max 3 轮；连续 1 轮 0 新通过 → 停下回报 George。
- Stage 4 = Codex read-only 异模型终审 wave-3 diff。
- Ship gate：George 眼验 + 明说可以 ship 才 commit（PR-based，禁直推 main）。
