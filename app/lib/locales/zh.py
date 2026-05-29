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
        "**累计收益图**\n"
        "- **买入持有（实线）**：选股日等权建仓后持有——已交付客户的口径。\n"
        "- **月度再平衡（虚线，可选）**：每月将权重重置为等权——可复制策略的口径。\n"
        "- **基准（灰色虚线）**：XBI 或 3110.HK。\n"
        "- **10–90 分位区间**：中间 80% 持仓的分布带；区间越宽，个股分化越大。\n\n"
        "**指标** — **超额收益 (pp)** = 组合收益减基准收益（百分点）。"
        "**评分** = 选股时模型给出的分数（若有）。"
    ),

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
