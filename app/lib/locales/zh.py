"""中文 locale — Strategy Picks 页（Phase 1）。

术语锁定（GLM 审计要求，全站一致）：
  rebalance=再平衡 / turnover(版本换仓)=调仓（两者严禁混用）/ dividend yield=股息率 /
  equal-weight=等权 / since-inception=建仓至今 / buy & hold=买入持有 /
  universe=股票池 / catalyst=催化事件（非"催化剂"）。
策略说明文案溯源自 CMS HK 白皮书（us-biotech 投资人简版 / high-dividend methodology.md）。
中文措辞经 GLM 决策定稿（glm-review-20260529-160642）：采纳卖方口径精修（顿号 / 括号% /
成交额 / 储备及未分配利润 / Line B 互斥 / "目标"非"考核" / 透明度说明 / 后视偏差）；
**保留**"AI 主观研判"事实表述（白皮书原文口径，未按 GLM 软化为"研究员研判"）。
"""

STRINGS = {
    # ── page chrome ──
    "strategy.page.title": "AI Agent 选股 · 策略表现",
    "strategy.page.caption": (
        "让 AI 像分析师一样读数据、按多维度打分选股，全程留痕、事后复盘——这种融合"
        "数据算力与基本面逻辑（业内称「量化基本面 / Quantamental」）的方式，是本平台的核心引擎。"
    ),
    "strategy.pitch": (
        "**这是什么** — 一个展示 **AI Agent 选股**实际表现的平台。我们让 AI 扮演分析师："
        "自动追踪并阅读临床试验数据、FDA 审批进度、财报披露与公司治理事件，按多个维度量化打分，挑出股票池——"
        "**每一只票在选出当天就被登记在册**，几个月后对着原始记录复盘，盈亏均客观呈现。\n\n"
        "下方三个策略展示**自选股日起的真实累计收益 vs 基准**（非回测美化）。"
    ),
    "common.lang_label": "语言",

    # ── sidebar ──
    "strategy.sidebar.chart_settings": "图表设置",
    "strategy.sidebar.show_individual": "显示个股曲线",
    "strategy.sidebar.show_individual_help": "为每只持仓画一条淡线，展示分化程度。",
    "strategy.sidebar.show_rebalanced": "显示月度再平衡曲线",
    "strategy.sidebar.show_rebalanced_help": (
        "叠加一条虚线：每月将权重重置为等权（对比实线「买入持有」——其权重随价格漂移）。"
        "两线之差即权重漂移的贡献。"
    ),

    # ── header metrics ──
    "strategy.metric.pick_date": "选股日",
    "strategy.metric.n_picks": "持仓数",
    "strategy.metric.days_since": "持有天数",
    "strategy.metric.benchmark": "基准",
    "strategy.metric.port_bh": "组合 · 买入持有",
    "strategy.metric.port_rebal": "组合 · 月度再平衡",
    "strategy.metric.benchmark_ret": "基准 · {sym}",
    "strategy.metric.alpha": "超额收益 (pp)",
    "strategy.delta.outperform": "跑赢",
    "strategy.delta.underperform": "跑输",
    "strategy.delta.tied": "持平",

    # ── chart ──
    "strategy.chart.title": "{name} — 建仓至今归一收益（{date} 起）",
    "strategy.chart.line.portfolio": "Top 20 组合（买入持有）",
    "strategy.chart.line.rebalanced": "Top 20 组合（月度再平衡）",
    "strategy.chart.line.band": "10–90 分位区间",
    "strategy.chart.line.benchmark": "{sym}（{name}）",
    "strategy.chart.y": "归一（起点 = 100）",

    # ── ranking tables ──
    "strategy.rank.top": "前 {n} 名（建仓至今）",
    "strategy.rank.worst": "后 {n} 名（建仓至今）",
    "strategy.rank.all": "全部 {n} 只（按建仓至今排序）",
    "strategy.col.name": "名称",
    "strategy.col.score": "评分",
    "strategy.col.last": "最新价",
    "strategy.col.since": "建仓至今 %",
    "strategy.col.rank": "排名",
    "strategy.holdings.title": "Top 20 持仓（按评分排名 · 等权）",
    "strategy.holdings.all": "全部 {n} 只评分股票池（按评分排名；前 20 为组合持仓）",
    "strategy.metric.holdings_help": "本组合由评分前 20 名等权建仓；当期评分股票池共 {n} 只。",
    "strategy.col.ticker": "代码",
    "strategy.metric.delta_vs_bh": "{bp:+.0f} bp vs 买入持有",
    "strategy.onboarding.title": "如何阅读本页",

    # ── methodology footnotes ──
    "strategy.method.equal_weight": (
        "**方法论** — 组合 = 按评分排名取 **Top 20 等权**建仓，自选股日起的两条曲线："
        "**买入持有**：成立时等权建仓后持有（权重随价格漂移）。"
        "**月度再平衡**：每月初将权重重置为等权。"
        "基准：生物科技用 XBI，港股高股息用 3110.HK。"
    ),
    "strategy.method.total_return": (
        "组合与基准均采用 yfinance 复权收盘价（已回补拆股**与**分红，即总收益口径），"
        "因此为同口径对比。"
    ),
    "strategy.method.source": (
        "选股结果由 AI Agent 评分系统产出（每周同步）；股票价格经 yfinance 实时获取。"
    ),

    # ── onboarding ──
    "strategy.onboarding.name": "策略页",
    "strategy.onboarding.body": (
        "本看板沿两条策略线追踪机会：\n"
        "- **① 催化剂驱动** — 围绕生物科技的临床读出、FDA / NMPA 审批节点、财报与公司治理事件，"
        "捕捉事件前后的价值重估；前三个标签页展示自选股日起的真实累计收益 vs 基准。\n"
        "- **② 新股打新多维评分** — 以六因子模型（流通盘稀缺度、基石阵容、板块景气、认购倍数、"
        "估值、基本面）为港股新股打分分档，量化首日申购胜率；末标签页为静态截面后测。\n\n"
        "两条线共用同一套数据纪律：数字标来源与时效、卖方一致预期与自有观点分离、结论可操作。"
        "后续将扩展至更多行业 domain。"
    ),

    # ── IPO 打新策略（静态截面后测；与时间序列策略结构不同）──
    "strategy.name.ipo": "港股IPO打新",
    "strategy.ipo.tab.intro": (
        "**港股打新策略后测** — 用 CMSI 棱镜六因子模型（v6.7）对近期港股新股打分分档，回看评分与"
        "首日表现的关系。下方 KPI 卡用**分档破发率对照**与**评分-涨幅排序力（ρ）**呈现这套评分的"
        "真实价值与能力边界（随样本更新），而非用「普涨 regime 下的中位涨幅／收涨率」把市场红利"
        "显示成评分功劳。核心读数:**评分擅长判方向（打不打、规避破发），不擅长测涨幅（涨多少）**"
        "——评分与首日涨幅仅弱相关（见散点右上角 Spearman ρ）。下方散点看评分 × 首日，小图看每只"
        "盘中路径，双榜可按评分或首日涨幅排序。"
    ),
    # KPI
    "strategy.ipo.kpi.sample": "样本数",
    "strategy.ipo.kpi.sample_delta": "已上市 {listed} / 待上市 {pending}",
    "strategy.ipo.kpi.max": "最高首日",
    "strategy.ipo.kpi.max_delta": "{name}",
    "strategy.ipo.kpi.worst": "最差首日",
    "strategy.ipo.kpi.worst_delta": "{name}",
    # 分档阶梯表（替代原对比卡 — 直读"评分越高越好吗"）
    "strategy.ipo.tier.title": "分档表现 — 评分越高越好吗？",
    "strategy.ipo.tier.col.tier": "申购档",
    "strategy.ipo.tier.col.n": "只数",
    "strategy.ipo.tier.col.med": "中位首日",
    "strategy.ipo.tier.col.win": "收涨率",
    "strategy.ipo.tier.col.brk": "破发",
    "strategy.ipo.tier.note": (
        "按申购档从高到低读：模型挑得出**最好（重点申购+）和最差（不申购，破发）**，"
        "但中间三档（重点 / 推荐 / 谨慎）首日拉不开——**评分判方向（打不打）有用，"
        "排不出涨幅大小**。各档样本少（共 n=17），结论待更多新股验证。本页为内部研究回测，不构成申购建议。"
    ),
    # 散点图
    "strategy.ipo.scatter.title": "评分 × 首日涨幅（n={n} 已上市）",
    "strategy.ipo.scatter.x": "六因子评分",
    "strategy.ipo.scatter.y": "首日涨幅 %",
    "strategy.ipo.scatter.trend": "OLS 趋势线",
    "strategy.ipo.scatter.rho": "Spearman ρ = {rho:.2f}（p={p}，不显著）",
    "strategy.ipo.scatter.hover": "{name}（{code}） · 评分 {score:.1f} · 首日 {ret:+.0f}% · {tier}",
    "strategy.ipo.scatter.caption": (
        "本评分体系是【准入过滤模型】而非【涨幅预测模型】——高分锁定的是「胜率」（规避破发），"
        "而非「赔率」（预测涨幅）：评分与首日涨幅强弱仅弱相关且不显著（Spearman ρ = 0.13，p = 0.62）。"
        "点色按申购档位着色，**红圈标记首日破发个股**（如馭勢虽列推荐档仍首日 −4.6%）。"
        "趋势线仅作均值层面参考（虚线、置信区间宽）。"
    ),
    # 盘中走势小图
    "strategy.ipo.intraday.title": "首日盘中走势（相对发行价 %，终点 = 首日收盘涨幅）",
    "strategy.ipo.intraday.caption": (
        "纵轴为 **相对发行价的涨幅 %**，每条线的 **终点即小图标题的首日收盘涨幅**；"
        "虚线 = 发行价（0% 盈亏线）。多数新股首日涨幅在开盘集合竞价已定格，故高开股盘中近乎横走"
        "（如曦智 09:35 即约 +384%、全日横盘），拓璞等则在开盘后继续上行。线色按首日收盘正负着色"
        "（青绿收涨 / 红色收跌）。"
    ),
    "strategy.ipo.intraday.mini_title": "{name} {ret:+.0f}%",
    "strategy.ipo.intraday.hover": "{time} · 相对发行价 {path:+.1f}%",
    # 双排名
    "strategy.ipo.rank.toggle": "排序方式",
    "strategy.ipo.rank.by_score": "按评分",
    "strategy.ipo.rank.by_ret": "按首日涨幅",
    "strategy.ipo.rank.pending": "待上市 ({date})",
    # 排名表列
    "strategy.ipo.col.rank": "排名",
    "strategy.ipo.col.code": "代码",
    "strategy.ipo.col.name": "名称",
    "strategy.ipo.col.score": "评分",
    "strategy.ipo.col.tier": "申购档位",
    "strategy.ipo.col.sub_sector": "子板块",
    "strategy.ipo.col.day1_ret": "首日涨幅",
    "strategy.ipo.col.source": "数据来源",
    # 方法论
    "strategy.ipo.method_expander": "打新策略方法论 · 六因子评分 v6.7",
    "strategy.ipo.method": (
        "**港股 IPO 六因子评分体系（CMSI 棱镜打新卡 · v6.7）**\n\n"
        "本策略以六个维度对每只新股加权打分（满分 10 分，v6.7 权重再平衡），据此分四档给出申购"
        "建议。**与生物科技催化剂策略的临床 / FDA / 财报 / 治理维度无关**——打新评估的是"
        "「上市定价博弈与首日供需」，不是企业长期基本面。\n\n"
        "| # | 因子 | 评估内容（v6.7） |\n"
        "|---|---|---|\n"
        "| ① | 流通盘稀缺度（FF 主开关） | 货越少越紧；v6.7 改**分段曲线**：<5% 陡峭加分 / 6–12% 压平 / >15% 阶梯扣分，并看**绝对自由流通盘金额**而非仅百分比 |\n"
        "| ② | 基石阵容 / 机构背书 | 基石质量分级（A/B/C）× 占发售比 + 国际配售超购 + 头部主权资金 + 保荐人护航胜率 |\n"
        "| ③ | 行业稀缺性 / 板块景气 | 稀缺赛道（如光子 AI、AI 制药）+ 当期板块情绪 + **二级锚**（同业 30 天破发率）|\n"
        "| ④ | 公开发售认购倍数 | 散户超额认购（分桶）；v6.7 **降权**——普涨里人人超购千倍，单因子区分度被 β 压平 |\n"
        "| ⑤ | 估值合理性 | v6.6+ 改 **floor logic**：一级估值倒挂（pre-IPO 倍数过高）触发总分上限封顶，而非简单加权 |\n"
        "| ⑥ | 公司基本面与财务质量 | 收入增速、毛利、现金与盈利路径；对首日相关性弱，主用于持有期 |\n\n"
        "**四档阈值：**\n"
        "- 评分 ≥ 7.5 → **重点申购+**\n"
        "- 6.0 – 7.4 → **推荐申购**\n"
        "- 5.0 – 5.9 → **谨慎申购**\n"
        "- < 5.0 → **不申购**\n\n"
        "**后测读数（n=17 已上市）：** 评分作为**准入过滤器**有边际价值——推荐档（≥6.0）首日"
        "破发率 **9.1%** vs 谨慎 / 不申购档 **16.7%**（全样本 11.8%）。但评分对首日**涨幅大小**"
        "近乎无排序力（Spearman ρ=0.13，p≈0.61；两个最大赢家深演 +266% / 商米 +241% 反落在 "
        "<6.0 档）——**评分是「要不要打／规避破发」的过滤器，不是「能涨多少」的预测器**。\n\n"
        "**首日 alpha 来自哪里（alpha 归因复盘，已过 /cccg 四方对抗）：** 首日涨跌主要由**一级"
        "市场微结构**驱动——A/H 折价（二次上市被 A 股价格锚死，迈威 +0.6% 垫底）、**绝对自由"
        "流通盘**（货越少越易挤兑）、**国配 × 盘子**供需。公司质量评分应**迁出首日、改用于持有"
        "期**。该结论基于 n=17 单一普涨 regime，属**假设生成（非已验证）**，待 n≥30 验证。"
    ),
    "strategy.ipo.caveat": (
        "首日表现为上市当日定格快照，一经记录不随后续行情更新；本页为策略后测（backtest），"
        "非实时盯盘工具。盘中走势小图按【相对发行价 %】绘制，每条线终点即该股首日收盘涨幅。"
        "样本仅 17 只已上市新股，统计结论受小样本与右尾异常值影响，不构成投资建议。"
    ),
    "strategy.ipo.source": "来源：CMSI 棱镜后测卡 / futu 首日收盘 / iFind 定价。首日表现为定格快照，不随后续行情更新。当前回测样本约 18 只，档位胜率特征尚需更多样本校验；过往业绩不代表未来表现，本页仅供内部量化研究参考，不构成投资或申购建议。",

    # ── strategy methodology (sourced) ──
    "strategy.method_expander": "策略方法论",
    "strategy.name.v4_biotech": "美国生物科技选股 4.0",
    "strategy.name.v5_biotech": "美国生物科技选股 5.0",
    "strategy.name.hk_hd": "港股高股息选股",
    "strategy.v4.tag": "回看版",
    "strategy.v5.tag": "catalyst-monitor",
    "strategy.v4.method": (
        "**股票池** — 全市场美股生物科技扫描。\n\n"
        "**选股逻辑** — 筛选未来 12 个月具临床 / FDA 催化事件的标的，按 5 大维度打分："
        "管线与临床（40%）/ 催化事件（25%）/ 并购与战略价值（20%）/ 财务与现金（10%）/ 风险（5%）。\n\n"
        "**本版定位 · 回看验证版** — 4.0 把选股框架套到历史区间，用真实后续走势检验「排序准不准」。"
        "24 个交易日回看：组合相对 XBI 跑赢约 +570bps、胜率 75%；并发现模型 **头部（Top 5）选股能力强**，"
        "中段排序区分度有限——这一发现直接促成了 5.0 的迭代升级。\n\n"
        "**基准** — XBI（宽基生物科技 ETF）。\n\n"
        "⚠️ **透明度说明** — 回看窗口短、样本小，仅供方向性参考，不代表未来表现。"
    ),
    "strategy.v5.method": (
        "**股票池** — 全市场美股生物科技扫描，按市值分线：Line A（≥ $30B 大盘，目标跑赢 XBI）/ "
        "Line B（$1B – <$30B 中小盘，追求 10 倍回报）。\n\n"
        "**选股逻辑** — 同为 5 维打分（管线 40% / 催化事件 25% / 并购 20% / 财务 10% / 风险 5%），"
        "5.0 在 4.0 基础上**细化评分**：催化事件维度引入「预期差」分析（评估市场对临床成功概率的共识，与 AI 测算的实际概率之间的落差），并结合实时市场交易信号（资金面与技术面）动态修正。\n\n"
        "**本版定位 · 当前前瞻版** — 5.0 是最新一版实际选股（中小盘 Line B），正进入实盘前瞻测试。"
        "在 4.0 / 5.0 两版中**反复入选的标的（如 ARWR、CYTK、GMAB、JAZZ、BMRN）视为当前模型信心评分最高的核心标的池**。\n\n"
        "**基准** — XBI。\n\n"
        "⚠️ **透明度说明** — 早期阶段、样本量仍小；评分约 60% 权重来自 AI 主观研判（已对潜在后视偏差做审慎处理）。"
        "下一阶段正把部分人工录入的管线数据升级为权威源自动抓取 + 证据校验；在该升级与完整前瞻测试完成前，"
        "输出**不构成可投级别**建议。"
    ),
    "strategy.biotech.method": (
        "**股票池** — 全市场美股生物科技扫描。\n\n"
        "**选股逻辑** — 筛选未来 12 个月具临床 / FDA 催化事件的标的，按 5 大维度打分：\n"
        "- 管线与临床（**40%**）/ 催化事件（**25%**）/ 并购与战略价值（**20%**）/ "
        "财务与现金（**10%**）/ 风险（**5%**）\n\n"
        "**市值分线** — Line A（市值 ≥ $30B）：大盘 Beta 增强，目标为跑赢 **XBI**；"
        "Line B（$1B – <$30B）：中小盘 Alpha，追求 10 倍回报。XBI 作为基准，对应 Line A 的宽基生物科技 ETF。\n\n"
        "**更新** — 大致每月推出新版本（整体重新选股，4.0 → 5.0）；版本内不调仓。\n\n"
        "⚠️ **透明度说明** — 策略运行时间较短、当前为早期小样本；评分约 60% 权重来自 AI 主观研判"
        "（已对潜在后视偏差进行审慎折价处理）。在下一阶段数据自动化升级 + 完整前瞻测试完成前，"
        "输出**不构成可投级别**建议。"
    ),
    "strategy.hd.method": (
        "**股票池** — 港股全市场（约 2,500 只）→ 定量初筛 → 约 34 只候选。\n\n"
        "**硬性筛选** — 近 3 月日均成交额 > 5,000 万港元 · 股息率（TTM）> 5% · ROE > 7% · "
        "派息率 30–80% · 财务安全垫（储备及未分配利润）/ 净利润 > 3 · 自由现金流 > 股息支出总额。"
        "（金融、地产豁免现金流检验。）\n\n"
        "**评分（100 分制）** — 公司治理 55（*愿意分*）+ 财务质量 25（*分得出*）+ 行业护城河 20（*分得久*）。\n\n"
        "**评级** — ≥80 优秀（核心配置）· 60–79 良好 · 40–59 一般 · <40 剔除。"
        "（如招商银行 = 87，优秀级。）\n\n"
        "**底线** — 当前静态股息率**不作**评分依据（防周期高点的伪高息）。\n\n"
        "**基准** — 3110.HK（Premia 沪深港高股息低波动）。\n\n"
        "**投资哲学** — 巴菲特（股东导向 / 护城河）、芒格（高 ROE）、"
        "马克斯（第二层思考 / 风险控制）、格雷厄姆（安全边际）。"
    ),
}
