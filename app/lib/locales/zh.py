"""中文 locale — Strategy Picks 页（Phase 1）。

术语锁定（GLM 审计要求，全站一致）：
  rebalance=再平衡 / turnover(版本换仓)=调仓（两者严禁混用）/ dividend yield=股息率 /
  equal-weight=等权 / since-inception=建仓至今 / buy & hold=买入持有 /
  universe=股票池 / catalyst=催化事件（非"催化剂"）。
策略说明文案溯源自 CMS HK 白皮书（us-biotech 投资人简版 / high-dividend methodology.md）。
中文措辞经 GLM 决策定稿（glm-review-20260529-160642）：采纳卖方口径精修（顿号 / 括号% /
成交额 / 储备及未分配利润 / Line B 互斥 / "目标"非"考核" / 透明度说明 / 后视偏差）；
**保留**"AI 主观研判"事实表述（白皮书原文口径，未按 GLM 软化为"研究员研判"）。
2026-07-05 George 拍板 B 口径（Quantamental）重写 strategy.pitch，supersede 原 GLM 定稿该 key。
"""

STRINGS = {
    # ── page chrome ──
    "strategy.page.title": "AI Agent 选股 · 策略表现",
    "strategy.page.caption": (
        "让 AI 像分析师一样读数据、按多维度打分选股，全程留痕、事后复盘——这种融合"
        "数据算力与基本面逻辑（业内称「量化基本面 / Quantamental」）的方式，是本平台的核心引擎。"
    ),
    "strategy.pitch": (
        "**方法论** — 本页跟踪一套量化基本面（Quantamental）选股体系的实盘表现："
        "以临床试验读出、FDA 审批进度、财报披露与公司治理事件为输入，按多维度评分筛选入池。"
        "**持仓自入选之日起登记在册**，业绩以原始记录为准复盘，盈亏均客观呈现。\n\n"
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
    "strategy.metric.totalreturn_note": "组合与基准均为**复权总回报**（含息 · 毛股息按除息日再投 · 未计红利税）；除息日股价机械下跌已由复权抵消，apples-to-apples。",
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
    "common.provenance": "来源: {src} · 截至 {asof}",
    "strategy.metric.holdings_foot": "等权 · 评分池 {n} 只",
    "strategy.metric.holdings_foot_weighted": "评分定权 · 约 {cash:.0f}% 现金缓冲",
    "strategy.col.since": "建仓至今 %",
    "strategy.col.contrib": "收益贡献 %",
    "strategy.col.spark": "30日走势",
    "strategy.col.rank": "排名",
    "strategy.holdings.title": "Top 20 持仓（按评分排名 · 等权）",
    "strategy.holdings.all": "全部 {n} 只评分股票池（按评分排名；前 20 为组合持仓）",
    "strategy.metric.holdings_help": "本组合由评分前 20 名等权建仓；当期评分股票池共 {n} 只。",
    "strategy.metric.holdings_help_weighted": (
        "本组合 = 20 只按质量评分定权建仓 + 约 {cash:.0f}% 现金缓冲；"
        "表中权重为建仓权重，买入持有曲线随价格自然漂移。"
    ),
    "strategy.holdings.title_weighted": "Top 20 持仓（按评分排名 · 评分定权 + 现金缓冲）",
    "strategy.col.weight": "权重 %",
    "strategy.col.bucket": "收益来源",
    "strategy.col.runrate": "股息率 %",
    "strategy.hd.bucket.rate": "利率溢价",
    "strategy.hd.bucket.nonrate": "非利率",

    # ── HD version group (v1/v2 frozen history / v3 current / 三代 compare) ──
    "strategy.hd.version.toggle": "组合版本",
    "strategy.hd.version.v3": "v3 · 2026-07-07（当前）",
    "strategy.hd.version.v2": "v2 · 2026-06-11（历史）",
    "strategy.hd.version.v1": "v1 · 2026-03-20（历史）",
    "strategy.hd.version.compare": "三代对比（v1 / v2 / v3）",
    "strategy.hd.version.v1_note": (
        "历史版本：v1 为 2026-03-20 发布的正式组合（34 只评分池 · Top 20 等权），"
        "曲线持续跟踪、成分不再调整；2026-06-11 起的新建仓见 v2。"
    ),
    "strategy.hd.compare.title": "高股息 v1 / v2 / v3 · 净值对比（各自建仓日 = 100）",
    "strategy.hd.compare.v1_line": "v1 组合（等权，2026-03-20 起）",
    "strategy.hd.compare.v2_line": "v2 组合（评分定权 + 现金缓冲，2026-06-11 起）",
    "strategy.hd.compare.v3_line": "v3 组合（Wind 单一源评分定权 + 现金缓冲，2026-07-07 起）",
    "strategy.hd.compare.rebal_label": "v3 建仓 2026-07-07",
    "strategy.hd.compare.note": (
        "口径：三条曲线各自以建仓日收盘 = 100 独立计算（三个独立组合，"
        "非同一净值的接续）；基准锚定 v1 建仓日。v1 / v2 历史完整保留，"
        "不因 v3 上线而截断或重述（三代演进）。"
    ),
    "strategy.hd.compare.metric.v1": "v1 建仓至今",
    "strategy.hd.compare.metric.v2": "v2 建仓至今",
    "strategy.hd.compare.metric.v3": "v3 建仓至今",
    "strategy.hd.diff.title": "换仓明细（v1 Top-20 组合 → v2）",
    "strategy.hd.diff.kept": "留任 {n} 只",
    "strategy.hd.diff.added": "新进 {n} 只",
    "strategy.hd.diff.removed": "剔除 {n} 只",
    "strategy.hd.diff.col.v1w": "v1 权重 %",
    "strategy.hd.diff.col.v2w": "v2 权重 %",
    "strategy.hd.diff.col.sector": "行业",
    "strategy.hd.diff.note": (
        "换仓明细由两版持仓 CSV 自动计算（不手工填写）。对比基准为 v1 的 "
        "Top-20 净值组合（等权、每只 5.0%），34 只评分池中排名 20 以后者"
        "不在 v1 组合内；v2 权重为 2026-06-11 建仓权重。"
    ),
    "strategy.hd.v2.cash_note": (
        "组合含约 {cash:.0f}% 现金缓冲（策略设计，非误差）；净值按现金 0 收益的"
        "保守口径计算，不计利息收入。"
    ),

    # ── Biotech version group (v4/v5 frozen history / v6 current / 三代 compare) ──
    "strategy.biotech.version.toggle": "组合版本",
    "strategy.biotech.version.v6": "7月调仓 · 2026-07-08（当前）",
    "strategy.biotech.version.v5": "夏季调仓 · 2026-05-15（历史）",
    "strategy.biotech.version.v4": "春季建仓 · 2026-04-22（历史）",
    "strategy.biotech.version.compare": "三代对比（v4 / v5 / v6）",
    "strategy.biotech.version.v4_note": (
        "历史版本：v4 为 2026-04-22 的春季建仓（回看验证版），曲线持续跟踪、"
        "成分不再调整；后续调仓见「夏季调仓」（v5）与「7月调仓」（v6）。"
    ),
    "strategy.biotech.version.v6_pending": (
        "**7月调仓（v6）即将上线** — 选股结果与建仓权重正在最终确认，数据录入后"
        "本页将自建仓日（2026-07-08）起跟踪真实净值 vs XBI。当前可查看「春季建仓」"
        "（v4）与「夏季调仓」（v5）两版历史表现。"
    ),
    "strategy.biotech.compare.title": "生物科技 v4 / v5 / v6 · 净值对比（各自建仓日 = 100）",
    "strategy.biotech.compare.v4_line": "v4 组合（春季建仓，2026-04-22 起）",
    "strategy.biotech.compare.v5_line": "v5 组合（夏季调仓，2026-05-15 起）",
    "strategy.biotech.compare.v6_line": "v6 组合（7月调仓，2026-07-08 起）",
    "strategy.biotech.compare.rebal_label": "v6 建仓 2026-07-08",
    "strategy.biotech.compare.note": (
        "口径：各条曲线以建仓日收盘 = 100 独立计算（独立组合，非同一净值的接续）；"
        "基准锚定 v4 建仓日。v4 / v5 历史完整保留，不因 v6 上线而截断或重述（三代演进）。"
        "v6 数据录入后自动加入对比。"
    ),
    "strategy.biotech.compare.metric.v4": "v4 建仓至今",
    "strategy.biotech.compare.metric.v5": "v5 建仓至今",
    "strategy.biotech.compare.metric.v6": "v6 建仓至今",

    # ── absolute-amount hero block (初始资金 → 当前净值) ──
    "strategy.hero.initial_capital": "初始资金",
    "strategy.hero.current_nav": "当前净值",
    "strategy.hero.nav_gain": "累计盈亏",

    # ── chained-account (跟随换仓的真实账户净值,只在对比 tab) ──
    "strategy.chain.section_title": "接续账户净值 · 跟随换仓（同一笔本金一路持有）",
    "strategy.chain.independent_section_title": "各版独立净值 · 各自建仓日 = 100（评判单版选股）",
    "strategy.chain.kpi.initial": "初始资金",
    "strategy.chain.kpi.current": "当前净值",
    "strategy.chain.kpi.cumulative": "累计收益",
    "strategy.chain.kpi.alpha": "超额 α",
    "strategy.chain.acct_line": "接续账户（跟随换仓）",
    "strategy.chain.rebal_marker": "换仓",
    "strategy.chain.note": (
        "口径:假设建仓日投入 {cur} {cap} 于最早版本,每逢新版建仓日整体换仓——"
        "前一版终值滚入下一版作起始本金,链成一条真实账户净值(虚线标注为换仓日)。"
        "回答「我从头一路跟到今天剩多少」;与下方「各版独立=100」口径互补,后者回答"
        "「每一版选股本身好不好」。基准为同一基准自最早建仓日买入持有(不换仓)作同期对照。"
    ),
    "strategy.col.ticker": "代码",
    "strategy.metric.delta_vs_bh": "{bp:+.0f} bp vs 买入持有",
    "strategy.onboarding.title": "如何阅读本页",

    # ── methodology footnotes ──
    "strategy.method.equal_weight": (
        "**方法论** — 生物科技与高股息 v1：按评分排名取 **Top 20 等权**建仓；"
        "高股息 v2：**质量评分定权 + 约 12% 现金缓冲**（现金按 0 收益保守计）。"
        "自建仓日起的两条曲线：**买入持有**：成立时按建仓权重买入后持有（权重随价格漂移）。"
        "**月度再平衡**：每月初将权重重置回建仓权重（等权组合即重置等权）。"
        "基准：生物科技用 XBI；港股高股息用 3466.HK（恒生高股息30），另列恒生指数作大盘参照。"
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

    # ── Model Drill（分析师模型可视化）──
    "model.title": "分析师模型",
    "model.intro": "读取分析师 Excel 模型，把收入拆解 / 利润率 / 未来预测 + DCF 做成可视化——补足财报 GAAP「拆解不够细」的缺口。数字为分析师 view，与 GAAP 申报分轨标注；预测(FYxxE)半透明、不裸展示。",
    "model.none_any": "当前环境暂无分析师模型数据。",
    "model.pick": "选择公司",
    "model.no_model": "{ticker} 暂无分析师模型。",
    "model.fallback_link": "→ 去个股详情 / SEC 财报",
    "model.as_of": "模型: {ver} · 来源: {src}",
    "model.tp": "目标价 (DCF)",
    "model.dcf_sub": "WACC {wacc} · 永续 {tg}",
    "model.price": "现价",
    "model.as_of_date": "截至 {d}",
    "model.model_ref": "模型基准价 {p}（{ver}）；上行空间已按最新现价重算",
    "model.upside": "隐含空间",
    "model.upside_sub": "目标价 vs 现价",
    "model.rating": "评级",
    "model.wiki_tp": "Wiki 目标价",
    "model.freq": "口径",
    "model.freq_year": "年度",
    "model.freq_quarter": "季度",
    "model.sec.revenue": "① 收入拆解",
    "model.revenue_cap": "**teal 深浅=战略分部**（深=主分部 R&D、浅=Commercial）、**斜纹=专业服务**（满色=订阅）；柱顶 = 主分部(R&D)占总收入比重。实色=已实际，半透明+虚线=分析师预测(FYxxE)。单位 $十亿。各分部占 DCF 企业价值(EV)的比重见 ③ 价值地图。来源: 分析师模型 Segment Summary。",
    "model.sec.margin": "② 利润率（GAAP vs 非GAAP）",
    "model.margin_cap": "灰虚线=GAAP，实色=非GAAP。SaaS 的 GAAP 被股权激励(SBC)压低，非GAAP 才是卖方定价口径；**展开下方桥图**拆 GAAP→非GAAP 的差(主因 SBC)。",
    "model.bridge_expand": "▸ 展开 GAAP → 非GAAP 桥(主因股权激励 SBC)",
    "model.sec.forecast": "③ 未来预测 + DCF",
    "model.ev_title": "DCF 企业价值分部构成 (NPV)",
    "model.sec.r40": "④ 估值矩阵 · Rule of 40",
    "model.r40_cap": "横轴 = Rule of 40（营收增速 + FCF Margin），纵轴 = EV/Sales。空心点 = SaaS/AI 软件可比公司（{n} 只），红点 = 当前标的；虚线 = 两轴均值，点线 = Rule of 40 = 40「优秀线」。数据来自每日快照（截至 {d}，随行情动态更新）。来源: yfinance（LOW，仅作相对定位）。",
    "model.r40_none": "暂无可比公司快照数据 — 请先运行 jobs/fetch_eod.py 抓取 software 组。",
    "model.scenario": "分析师情景注释",
    "model.sec.wiki": "④ 研究观点 (LLM Wiki)",
    "model.wiki_full": "展开完整 Wiki",
    "model.see_thesis": "→ 完整研究观点见「个股详情」",
    "model.disclaimer": "数据来自分析师模型 {src}（分析师 view，非财报口径；FYxxE 为估算）。目标价/DCF 为单一模型 base case，仅供内部研究，不构成投资建议。",
    "model.public_desensitized": "📋 公开脱敏版：目标价 / DCF 估值结论已移除，预测与比率保留；完整估值仅本地内部版可见。",
    # ── ⑤ 分析师比率（SEC 给不出的除法/倍数/预测）──
    "model.sec.ratios": "⑤ 分析师比率",
    "model.ratios_cap": (
        "SEC 只给原子（应收/营收/净利/权益），给不出除法、倍数与预测。本面板是分析师模型的"
        "增量价值：凡需股价/EV 的倍数、需预测的 FYxxE、或需口径选择的（非GAAP/周转天数/ROIC/"
        "现金转化）——SEC 结构性没有。数字为分析师 view，含预测，与 GAAP 申报分轨。"
    ),
    "model.ratios_tag": "分析师 view（含预测）",
    "model.ratios_annual_only": "仅年度口径",
    "model.ratios_annual_only_tip": "季度未年化/口径不可比",
    "model.ratios_q_note": "比率默认年度口径；季度仅展示利润率/Billings/客户数等口径可比项。",
    "model.ratios_metric_col": "指标",
    # 分组标题
    "model.ratios.g.valuation": "估值倍数",
    "model.ratios.g.profitability": "盈利与回报",
    "model.ratios.g.efficiency": "效率与营运资本",
    "model.ratios.g.cash": "现金与 Billings",
    "model.ratios.g.operational": "经营指标",

    # ── IPO 打新策略（静态截面后测；与时间序列策略结构不同）──
    "strategy.name.ipo": "港股IPO打新",
    "strategy.ipo.tab.intro": (
        "**港股打新策略后测** — 用 CMSI 棱镜六因子模型（v6.7）对近期港股新股打分分档，回看评分与"
        "首日表现的关系。顶部 3 张卡看规模与首日区间（样本数 / 最高 / 最差）；下方**「分档表现」表**"
        "按申购档从高到低列出只数、中位首日、收涨率、破发，一眼看出**评分越高是不是越好**。核心"
        "读数:**评分擅长判方向（打不打、规避破发），不擅长测涨幅（涨多少）**——分档表里中间几档"
        "拉不开就是证据。再往下:小图看每只首日盘中路径，双榜可按评分或首日涨幅排序。"
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
    "strategy.ipo.rank.pending_short": "待上市",
    # 排名表列
    "strategy.ipo.col.rank": "排名",
    "strategy.ipo.col.code": "代码",
    "strategy.ipo.col.name": "名称",
    "strategy.ipo.col.list_date": "上市日期",
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
    "strategy.name.v4_biotech": "美国生物科技选股",
    "strategy.name.v5_biotech": "美国生物科技选股 · 夏季调仓",
    "strategy.name.v6_biotech": "美国生物科技选股 · 7月调仓",
    "strategy.name.hk_hd": "港股高股息选股",
    "strategy.name.hk_hd_v2": "港股高股息 v2 · 标准建仓",
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
        "**基准** — 3466.HK（恒生高股息30 ETF），另列恒生指数作大盘参照。\n\n"
        "**投资哲学** — 巴菲特（股东导向 / 护城河）、芒格（高 ROE）、"
        "马克斯（第二层思考 / 风险控制）、格雷厄姆（安全边际）。"
    ),
    "strategy.hd.v2.method": (
        "**版本定位** — v2 为 2026-06-11 标准建仓的正式组合（20 只，非等权），"
        "与 v1（2026-03-20，34 只评分池 · Top 20 等权）独立核算；v1 历史曲线完整保留。\n\n"
        "**构建方式** — 本组合由 AI 原生端到端投研引擎产出：定量筛选、定性评分、"
        "组合构建全流程由 Agent 执行，机器校验、独立审核、全程留痕，"
        "实现从选股到建仓的全自动化（详见 2026-06-10 报告"
        "《从 Vibe Coding 到 Agentic Engineering》）。\n\n"
        "**四条组合规则** —\n"
        "1. **高仓位收息**：约 88% 建仓 + 约 12% 现金缓冲，现金用于应对调仓与极端波动"
        "（净值按现金 0 收益的保守口径计算）。\n"
        "2. **质量评分定权重**：沿用「愿意分 / 分得出 / 分得久」质量评分框架，评分越高权重越高。\n"
        "3. **收益来源结构锚定**：利率溢价桶约 55% : 非利率桶约 45%。第一性原理——高股息"
        "收益的本质是**利率风险溢价**：银行吃信用利差、公用事业（燃气 / 电力）吃久期折现；"
        "非利率桶（消费 / 能源 / 交通 / 博彩 / 医药）的分红由自身现金流驱动，"
        "对冲组合的利率敏感度。\n"
        "4. **集中度约束**：单一标的权重 ≤10%，行业适度分散。\n\n"
        "**股息率口径** — 表中股息率为建仓时点的年化 run-rate（截至 2026-06-11）。\n\n"
        "**基准** — 3466.HK（恒生高股息30 ETF），另列恒生指数作大盘参照；与 v1 一致。"
    ),
    "strategy.hd.v3.method": (
        "**版本定位** — v3 为 2026-07-07 生效的正式换仓组合（20 只，非等权），"
        "数据日 2026-07-06；与 v1（2026-03-20）、v2（2026-06-11）独立核算，"
        "三代曲线完整保留（三代演进）。\n\n"
        "**数据源升级** — v3 起财务 / 行情 / 估值取数切换为 **Wind 单一源**（此前 iFind / 聚源 产线停用），"
        "例外补源为港交所业绩公告（纯港股现金流量表 + 派息率边界终核）。\n\n"
        "**构建方式** — 定量六闸筛选、垂直分析师 Agent 定性评分、组合构建全流程由 AI 原生投研引擎产出，"
        "三权分立契约校验、异模型独立审核、全程留痕；名单经人工逐票复核后生效。\n\n"
        "**四条组合规则** —\n"
        "1. **高仓位收息**：约 88% 建仓 + 约 12% 现金缓冲（净值按现金 0 收益的保守口径计算）。\n"
        "2. **质量评分定权重**：沿用「愿意分 / 分得出 / 分得久」质量评分框架，评分越高权重越高。\n"
        "3. **收益来源结构锚定**：利率溢价桶与非利率桶分散。第一性原理——高股息"
        "收益的本质是**利率风险溢价**：银行吃信用利差、公用事业（电力）吃久期折现；"
        "非利率桶（消费 / 工业 / 能源）的分红由自身现金流驱动，对冲组合的利率敏感度。\n"
        "4. **集中度约束**：单一标的权重 ≤10%，行业适度分散。\n\n"
        "**股息率口径** — 表中股息率为建仓时点的清洁年化 run-rate（截至 2026-07-06）。\n\n"
        "**基准** — 3466.HK（恒生高股息30 ETF），另列恒生指数作大盘参照；与 v1 / v2 一致。"
    ),
}
