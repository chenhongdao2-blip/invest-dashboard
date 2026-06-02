"""中文 locale — Phase 2（Home + 5 个 healthcare 页 + 共享组件）。

由 lib.i18n 与 zh.py（Phase 1）合并。术语沿用 zh.py 头部锁定表。
onboarding 正文多数沿用源页既有中文（精修），EN 侧为其翻译。
中文措辞经 GLM 决策定稿。
"""

STRINGS = {
    # ── 共享：侧边栏搜索 ──
    "sidebar.find_ticker": "🔍 查找标的",
    "sidebar.jump_label": "跳转到个股详情",
    "sidebar.select_placeholder": "— 选择 —",
    "sidebar.selected_info": "📍 **{bbg}** — 打开 *个股详情* 页查看完整资料。",

    # ── 共享：通用表头 ──
    "common.col.name": "名称",
    "common.col.last": "最新价",
    "common.col.ticker": "代码",
    "common.col.1d": "1日 %",
    "common.col.5d": "5日 %",
    "common.col.1m": "1月 %",
    "common.col.3m": "3月 %",
    "common.col.6m": "6月 %",
    "common.col.vs_spx": "相对标普 pp",
    "common.col.ytd": "年初至今 %",
    "common.col.mcap_b": "市值（十亿美元 $B）",
    "common.col.trail_pe": "静态 P/E",
    "common.col.fwd_pe": "动态 P/E",
    "common.col.ev_ebitda": "EV/EBITDA",
    "common.col.ev_sales": "EV/Sales",
    "common.col.fcf_yld": "自由现金流收益率",
    "common.col.pb": "P/B",
    "common.warn.fetch_fail": "实时获取失败（yfinance）——检查网络/代理。",

    # ── Home panels ──
    "home.panel.broad_market": "市场总览",
    "home.panel.sp500_sector": "标普500 子行业表现",
    "home.panel.healthcare": "医疗健康基准",
    "home.panel.ai": "AI 基准（预留）",
    "home.panel.empty": "数据预留，敬请期待",
    "home.panel.sp500_caption": "11 个 GICS 一级行业（SPDR Select Sector ETF 代理）+ 标普500 大盘对照",
    "home.sub.benchmarks": "基准",

    # ── Home ──
    "home.title": "行情中枢",
    "home.metric.latest_snapshot": "最新快照",
    "home.metric.last_fetch": "最后获取（UTC）",
    "home.metric.universe": "股票池数量",
    "home.section.benchmarks": "基准指数",
    "home.section.movers": "涨跌榜 · 1日",
    "home.section.movers_meta": "覆盖板块内",
    "home.movers.gainers": "涨幅前 10",
    "home.movers.drags": "跌幅前 10",
    "home.movers.empty": "暂无价格数据——运行 `jobs/fetch_eod.py --backfill-days 180`。",
    "home.section.universe": "股票池覆盖",
    "home.col.domain": "领域",
    "home.col.sector": "板块",
    "home.col.tickers": "标的数",
    "home.caveat.data": (
        "**数据口径**：估值倍数取自 **yfinance**，仅含静态 P/E 与 12 个月动态 P/E。"
        "多年期一致预期（25E / 26E / 27E）**不在本看板范围内**。"
        "本看板定位为快速目视扫描工具；精确一致预期请以 Bloomberg / FactSet 终端为准。"
    ),

    # ── CMSI Coverage ──
    "cov.title": "CMSI 覆盖名单",
    "cov.caption": "28 只官方覆盖名单——港股 15 / 美股 10 / A 股 3。最新数据：{date}",
    "cov.col.vs_hsi": "恒指超额（年初至今）",
    "cov.col.tp_upside": "目标价空间 %",
    "cov.col.reco": "评级",
    "cov.col.n_analysts": "分析师数",
    "cov.col.cross": "跨板块",
    "cov.onboarding.title": "如何阅读本页",
    "cov.onboarding.body": (
        "**官方覆盖名单**：招商证券国际（CMSI）医疗健康覆盖名单，含港股、美股及 A 股。\n\n"
        "**字段说明**\n"
        "- **跨板块**：若标的同属多个板块股票池（如信达属于 Biotech + Pharma），此处显示对应标签。\n"
        "- **市值（美元）**：统一换算为美元，便于跨地域比较。\n"
        "- **动态 P/E**：yfinance 提供的 12 个月动态 P/E。\n"
        "- **自由现金流收益率**：越高通常代表现金流越稳健。\n\n"
        "**排序**：默认按市值降序。"
    ),
    "cov.caption.tags": (
        "BIO = Biotech · PHAR = Pharma · AI = HC+AI · MED = Medtech · HOSP = Hospital Care · "
        "MC = Managed Care · CXO = CXO。跨板块标签表示该标的同时存在于其他板块股票池（自动去重）。"
    ),
    "cov.caption.source": (
        "覆盖名单来源：`config/universes/cmsi_coverage_hc.yml`（{n} 只）。"
        "默认按市值降序，名称中文优先。"
    ),

    # ── Healthcare overview ──
    "hc.title": "医疗健康",
    "hc.caption_fallback": "医疗健康领域总览——7 个细分板块。",
    "hc.section.summary": "板块汇总",
    "hc.section.summary_meta": "各板块平均收益",
    "hc.section.benchmark": "领域基准及同业",
    "hc.section.benchmark_meta": "XLV · XBI · XPH · IXJ · IHF · IHI",
    "hc.section.movers": "各板块涨跌前 3 · 1日",
    "hc.col.sector": "板块",
    "hc.col.tickers": "标的数",
    "hc.col.benchmark": "基准",
    "hc.col.1d_avg": "1日 % 均值",
    "hc.col.5d_avg": "5日 % 均值",
    "hc.col.1m_avg": "1月 % 均值",
    "hc.col.ytd_avg": "年初至今 % 均值",
    "hc.movers.gainers": "涨幅前 3 · 1日",
    "hc.movers.drags": "跌幅前 3 · 1日",
    "hc.summary.empty": "暂无板块数据——需回补。",
    # ── 相对表现（Jonah：HSHCI vs 恒生/恒科 · NBI vs 纳指 · 标普医疗 vs 标普）──
    "hc.rs.section": "相对表现",
    "hc.rs.section_meta": "去年 8 月以来 · rebased=100",
    "hc.rs.hk.title": "恒生医疗保健 vs 恒生 vs 恒生科技",
    "hc.rs.nbi.title": "纳斯达克生物科技 (NBI) vs 纳斯达克综合",
    "hc.rs.sphc.title": "标普 500 医疗保健 vs 标普 500",
    "hc.rs.ylabel": "rebased（起点 = 100）",
    "hc.rs.caption": "锚定 {anchor}（去年 8 月）· {detail}。来源：{src}，截至 {asof}。",
    "hc.rs.read": (
        "港股医疗独熊（较恒指 −22.4pp），主因**中国医疗特有风险**（流动性虹吸 / 集采 VBP / "
        "医保谈判），而非全球医疗 de-rating——佐证：NBI 与纳指基本持平，全球生科未同步走弱。"
        "美股大医疗 −9.3pp 则属药价（IRA/PBM）与 managed-care 赔付压力的板块 de-rating。"
    ),
    "hc.rs.lag": "{hero}较{peer} 跑输 {pp}pp",
    "hc.rs.lead": "{hero}较{peer} 跑赢 {pp}pp",
    "hc.rs.flat": "{hero}与{peer} 基本持平",
    "hc.rs.empty": "暂无指数对比数据——请运行 jobs/build_hc_overview_data.py 回补。",
    # ── 机构持仓 · 离岸中国基金对 healthcare 超配/低配 ──
    "hc.pos.section": "机构持仓 · 离岸中国基金对医疗的超配/低配",
    "hc.pos.section_meta": "12 只离岸中国股票型基金 · vs 各自基准 · 截至 2026-03-31",
    "hc.pos.chart.title": "医疗板块偏离度（基金权重 − 基准权重）",
    "hc.pos.chart.xlabel": "相对基准的偏离（百分点）",
    "hc.pos.legend": "🟢 青＝超配 (OW)　🔴 红＝低配 (UW)　·　此处颜色表**仓位倾斜**，非当日涨跌",
    # 纯计数 headline — 永远有效, 不含方向/AUM倾斜/写死数字(无数据时也安全)。
    "hc.pos.verdict": (
        "**结论**：按基金只数接近中性——{n_ow} 超配 / {n_uw} 低配 / {n_neu} 中性"
        "（另 {n_na} 只未披露 HC 权重）。"
    ),
    # 方向性倾斜 — 页面仅在 data_available(有真实 AUM 支撑) 时渲染。
    "hc.pos.verdict_tilt": (
        "**按 AUM 加权为小幅净低配（{aum_pp}pp）**——最大的一只（3.3bn）坚定低配 −3.8pp，"
        "第二大的一只反而小幅超配 +1.1pp；真正的超配信仰集中在更小的几只户口（最高 +6.7pp）。"
    ),
    "hc.pos.read": (
        "大户仍在加速减仓（最深者一年减 −3.4 ~ −3.8pp），与港股医疗同期较恒指跑输 −22pp "
        "形成「机构去化 + 估值杀」共振；个别中小户开始向中性补仓，是逆向资金的试探，但拐点未到。"
        "研判偏 **contrarian**——分步跟踪筹码见底，不抢左侧。"
    ),
    "hc.pos.col.fund": "基金",
    "hc.pos.col.aum": "规模 (USD)",
    "hc.pos.col.bm": "基准",
    "hc.pos.col.fund_hc": "基金 HC%",
    "hc.pos.col.bm_hc": "基准 HC%",
    "hc.pos.col.dev": "偏离",
    "hc.pos.col.stance": "超/低配",
    "hc.pos.col.chg": "较去年 Δ",
    "hc.read.eyebrow": "研判",
    "hc.pos.stance.OW": "超配",
    "hc.pos.stance.UW": "低配",
    "hc.pos.stance.Neutral": "中性",
    "hc.pos.stance.SlightlyOW": "略超配",
    "hc.pos.stance.NA": "未披露",
    "hc.pos.source": "来源：",
    "hc.pos.note_ai": "解读由金融策略 / 医药研究 Agent 基于上表数据生成；不含也不采信任何评级 / 目标价。",
    "hc.pos.empty": "暂无基金持仓数据——请运行 jobs/build_hc_overview_data.py 回补。",
    "hc.onboarding.title": "如何阅读本页",
    "hc.onboarding.body": (
        "**板块汇总**：展示医疗健康 7 个细分板块的平均涨跌幅。\n"
        "- **标的数**：该板块包含的股票数量。\n"
        "- **基准**：该板块对应的行业指数（如 XBI 对应 Biotech）。\n\n"
        "**领域基准**：XLV（Healthcare）及其主要细分行业 ETF 的表现。\n\n"
        "**各板块涨跌**：每个板块内当日表现最好和最差的 3 只个股。"
    ),

    # ── Sector Heatmap ──
    "heat.title": "板块热力图",
    "heat.caption": "各板块横截面快照。倍数来自 yfinance——仅静态 + 12 个月动态。",
    "heat.filter.header": "筛选",
    "heat.filter.min_mcap": "市值下限（十亿美元 B）",
    "heat.filter.min_mcap_help": "过滤掉小市值标的，避免拉偏均值。",
    "heat.filter.sort_by": "排序依据",
    "heat.filter.sort_help": "默认按市值降序。",
    "heat.agg.expander": "{sector} 汇总（均值 / 中位数 / 加权）",
    "heat.agg.metric": "指标",
    "heat.onboarding.title": "如何阅读本页",
    "heat.onboarding.body": (
        "**倍数与收益**\n"
        "- **配色图例**：收益率绿涨红跌；估值倍数（P/E、EV/EBITDA）绿低红高（绿=便宜）；"
        "自由现金流收益率绿高红低。\n"
        "- **选项卡**：上方选项卡快速切换 7 个细分板块。\n\n"
        "**筛选** — **最小市值**：过滤掉极小市值标的，避免其极端估值拉偏板块均值。\n\n"
        "**汇总**：展开下方「板块汇总」可看该板块的均值与中位数。"
    ),

    "heat.caption.legend": "**配色图例**：收益率绿涨红跌；估值倍数（P/E、EV/EBITDA）绿低红高（绿=便宜）；自由现金流收益率绿高红低。代码采用 **彭博格式**（2269 HK / 4587 JP / 300760 CH）。最新数据：**{date}**",
    "heat.caption.filter_note": "通过侧边栏排序/筛选。当小市值标的拉偏板块均值时（如 4587 JP $904M vs GILD $166B），市值下限筛选很有用。",

    # ── Valuation Scanner ──
    "scan.title": "估值扫描器",
    "scan.caption": (
        "横截面扫描——寻找低估值且近期动量为正的标的。板块内 P/E 分位 + 年初至今/5日 筛选。最新：{date}"
    ),
    "scan.presets.header": "预设",
    "scan.presets.deep_value": "深度价值",
    "scan.presets.recovery": "困境反转",
    "scan.presets.reset": "重置全部筛选",
    "scan.filters.header": "筛选",
    "scan.filters.sector": "板块",
    "scan.filters.min_mcap": "市值下限（十亿美元 B）",
    "scan.filters.pe_pct": "P/E 分位阈值",
    "scan.filters.pe_pct_help": "只显示动态 P/E 在板块内分位 ≤ 此阈值的候选。",
    "scan.filters.pe_metric": "P/E 类型",
    "scan.filters.ytd_range": "年初至今收益区间（%）",
    "scan.filters.min_5d": "5日收益下限（%）",
    "scan.metric.universe": "扫描标的数",
    "scan.metric.candidates": "候选数",
    "scan.metric.median_mcap": "市值中位数（十亿美元 B）",
    "scan.metric.median_ytd": "年初至今中位数",
    "scan.col.pe_pctile": "板块 P/E 分位",
    "scan.warn.no_sector": "请在侧边栏至少选择 1 个板块。",
    "scan.warn.no_candidates": (
        "无候选匹配当前筛选。请放宽条件（降低最小市值 / 提高 P/E 阈值 / 拓宽年初至今区间）。"
    ),
    "scan.onboarding.title": "如何阅读本页",
    "scan.onboarding.body": (
        "**板块 P/E 分位**：该股动态（或静态）P/E 在所属板块内的分位。\n"
        "- `0%–25%` = 板块内最便宜的四分之一。\n"
        "- 典型卖方框架：低倍数 + 正动量 → 可能的重估候选。\n\n"
        "**年初至今 %**：年初至今总回报。负年初至今 + 低 P/E 可能是「坠落天使」；"
        "正年初至今 + 低 P/E 可能是「价值 + 动量」。\n\n"
        "**5日 %**：最近 5 个交易日动量；默认筛选 ≥ −10% 排除崩盘中标的。\n\n"
        "**EV/EBITDA**：互补倍数（避免一次性项目扭曲 EPS 的误判）。\n\n"
        "**自由现金流收益率**：自由现金流 / 市值；越高 = 现金生成能力越强。\n\n"
        "**预设** — **深度价值**：板块内极低估（15% 分位）的大市值标的。"
        "**困境反转**：已从底部回升（5日 % > 5%）的低估标的。"
    ),
    "scan.caption.method": (
        "**方法论**：所选板块内横截面比较。负 P/E 不纳入分位排名。最新快照：{date}。"
        "板块归属为多对多。"
    ),

    # ── Ticker Drill ──
    "drill.title": "个股详情",
    "drill.caption": "单只标的深度剖析——wiki memo（若有）+ 价格图 + 估值倍数 + 跨板块标签。",
    "drill.choose": "选择标的",
    "drill.pick_prompt": "从侧边栏或上方下拉框选择一只标的。",
    "drill.badge.coverage": "CMSI 覆盖",
    "drill.badge.pick": "入选：{names}",
    "drill.metric.last_local": "最新价",
    "drill.metric.last": "最新价",
    "drill.metric.mcap": "市值",
    "drill.metric.fwd_pe": "动态 P/E",
    "drill.metric.tp_upside": "目标价空间",
    "drill.metric.ytd": "年初至今",
    "drill.metric.adv": "20日成交额",
    "drill.kpi.ytd_foot": "{ccy} · 本币口径",
    "drill.kpi.adv_foot": "{ccy} · 流动性",
    "drill.consensus_line": "市场一致目标价 {tp}（较现价 {upside}）· {n} 分析师 · 第三方一致预期，仅供参考",
    "drill.analysts": "分析师",
    "drill.kpi.pe_foot": "静态 {pe}",
    "drill.kpi.tp_foot": "一致目标价 {tp}",
    "drill.kpi.tp_none": "无一致目标价",
    # ── Variant block (House vs Consensus) ──
    "drill.variant.title": "预期差 · 内部观点 vs 市场一致",
    "drill.variant.house": "内部观点 · CMS HK",
    "drill.variant.consensus": "市场一致预期 · 仅供参考",
    "drill.variant.gap": "预期差 · VARIANT",
    "drill.variant.tp_foot": "目标价 {tp}",
    "drill.variant.cons_foot": "目标价 {tp} · {n} 分析师",
    "drill.variant.gap_foot": "较最新价",
    "drill.variant.disclaimer": (
        "市场一致预期来自 Yahoo Finance 第三方聚合（覆盖分析师有限，港股 18A 标的口径"
        "可能失真），仅供参考、不代表 CMS HK 观点，亦不构成投资建议。内部观点引自 wiki "
        "memo，与第三方预期口径不同，请勿对外分发。"
    ),
    "drill.reco.strong_buy": "强烈买入",
    "drill.reco.buy": "买入",
    "drill.reco.hold": "持有",
    "drill.reco.sell": "卖出",
    "drill.reco.strong_sell": "强烈卖出",
    "drill.consensus_tp": "一致目标价：**{tp}**（较最新 {upside}）{analysts}",
    "drill.no_mults": "无估值快照——该标的可能仅为选股池标的（不在主获取池）。",
    "drill.section.price": "价格 · 美元归一",
    "drill.section.rs": "相对强弱 · vs 板块基准",
    "drill.rs.title": "{bbg} · 相对强弱（基准日 = 100）",
    "drill.rs.caption": (
        "{date} 归一为 100。对照基准：{benches}。个股与基准均按上市地本币（{ccy}）"
        "同币种对照，rebase 比较相对走势，无汇率扰动。"
    ),
    "drill.rs.fallback": "无重叠的板块基准数据，回退显示美元绝对收盘价。",
    "drill.ret_windows": "区间收益率",
    "drill.col.window": "区间",
    "drill.col.return": "收益 %",
    "drill.latest_mults": "最新估值倍数（yfinance）",
    "drill.col.metric": "指标",
    "drill.col.value": "数值",
    "drill.ext.expander": "扩展基本面（yfinance.info 实时——点击获取）",
    "drill.ext.fetch": "实时获取",
    "drill.ext.fetch_help": "调用 yfinance.info；结果缓存 1 小时。",
    "drill.ext.hint": (
        "点击 *实时获取* 从 yfinance.info 拉取 EBITDA / 利润率 / 股本 / 业务简介。"
        "默认不获取，以保证页面在 Streamlit Cloud 上的加载速度（冷启动访问跳过实时调用）。"
    ),
    "drill.ext.empty": "yfinance.info 返回为空——网络问题、限流，或标的已退市。",
    "drill.ext.biz_summary": "公司业务简介",
    "drill.ext.f.ebitda": "EBITDA（TTM）",
    "drill.ext.f.total_cash": "现金及等价物总额",
    "drill.ext.f.total_debt": "总有息负债",
    "drill.ext.f.total_rev": "营业收入（TTM）",
    "drill.ext.f.rev_growth": "营收同比增速",
    "drill.ext.f.gross_margin": "毛利率",
    "drill.ext.f.op_margin": "营业利润率",
    "drill.ext.f.profit_margin": "净利率",
    "drill.ext.f.roe": "净资产收益率（ROE）",
    "drill.ext.f.peg": "PEG",
    "drill.ext.f.div_yield": "股息率",
    "drill.ext.f.beta": "Beta",
    "drill.ext.f.shares_out": "总股本",
    "drill.ext.f.float_shares": "流通股本",
    "drill.ext.col.metric": "指标",
    "drill.ext.col.value": "数值",
    "drill.ext.biz_summary_note": "以下为 yfinance 英文原文（公司未提供中文官方简介）。",
    # wiki memo block
    "drill.wiki.none": (
        "该标的暂无 LLM Wiki memo。在 `~/Documents/LLM Wiki/Wiki/` 下放一个 "
        "`companies/*.md` 文件即可在此展示投资逻辑。"
    ),
    "drill.wiki.memo_title": "研究备忘",
    "drill.wiki.banner_public": (
        "公开研究摘要 · 呈现投资逻辑与公开信息框架。具体评级、目标价及完整测算"
        "以 CMS HK 正式研究报告为准。本材料仅供参考，不构成任何投资建议或要约。"
    ),
    "drill.wiki.rating": "评级",
    "drill.wiki.tp": "目标价",
    "drill.wiki.updated": "更新于",
    "drill.wiki.sectors": "Wiki 板块",
    "drill.wiki.summary": "摘要",
    "drill.wiki.thesis": "投资逻辑",
    "drill.wiki.sources": "来源",
    "drill.wiki.source_file": "源文件",
    # warnings / empty states
    "drill.warn.no_price": "snapshots.db 中无价格历史——该标的需要回补数据。",
    "drill.warn.price_nan": "价格序列全为空值。",
    "drill.warn.no_return": "无收益数据。",
    "drill.warn.no_mult_snap": "无估值倍数快照。",
    "drill.no_sector": "该标的不在任何已配置的板块股票池中。",
    "drill.chart.title": "{bbg} · {ccy} 收盘价（{n} 个观测）",
    # multiples panel labels
    "drill.mult.trailing_pe": "静态市盈率",
    "drill.mult.forward_pe": "动态市盈率",
    "drill.mult.ev_ebitda": "EV/EBITDA",
    "drill.mult.ev_sales": "EV/销售额",
    "drill.mult.pb": "市净率",
    "drill.mult.fcf_yield": "自由现金流收益率",
    # ── SEC financial trends (US-only) ──
    "drill.sec.section": "财务趋势 · SEC",
    "drill.sec.na": (
        "本标的无 SEC 申报（SEC XBRL 为美股 US-GAAP 口径专属）。港股 18A 采用 IFRS、"
        "A 股采用企业会计准则，财务请见本地 / Wind 财报。"
    ),
    "drill.sec.revenue": "营业收入",
    "drill.sec.rnd": "研发费用",
    "drill.sec.cash": "现金及等价物",
    "drill.sec.no_concept": "无此科目数据",
    "drill.sec.latest": "最新 {val}（{date}）",
    "drill.sec.runway": "现金跑道 ≈ {years} 年（现金+短投 ÷ 年度研发，截至 {date}，粗略估算）",
    "drill.sec.source": "来源：SEC XBRL · 最新申报 {filed} · 仅美股口径",
    "drill.membership": "所属板块",
    "drill.onboarding.title": "如何阅读本页",
    "drill.onboarding.body": (
        "**Memo 来源**：若 `~/Documents/LLM Wiki/Wiki/companies/<ticker>-*.md` 存在，"
        "本页顶部渲染其 Summary / Thesis / Rating / TP / 核心投资逻辑 / 催化剂 / 风险点。"
        "Memo 在 wiki 端撰写，本页只读、不回写。\n\n"
        "**价格**：来自 `snapshots.db` 的美元归一收盘（每日 cron；数据始于约 2025-12-01）。\n\n"
        "**估值倍数**：仅 yfinance 静态 + 12 个月动态。多年期预测（25E/26E/27E）不在范围。\n\n"
        "**扩展基本面**：yfinance.info 实时获取，缓存 1 小时。「—」表示该字段未提供。\n\n"
        "**深链**：可通过 `?ticker=LLY` URL 参数直接跳到该票。"
    ),

    # ── 行情总表 ──
    "market.title": "行情总表",
    "market.caption": "全股票池行情一览——覆盖全部 {n} 只标的（跨所有行业）。最新：{date}",
    "market.filters.domain": "领域",
    "market.filters.sector": "板块",
    "market.filters.region": "地区",
    "market.metric.universe": "股票池规模",
    "market.metric.shown": "当前行数",
    "market.section.table": "行情与估值倍数",
    "market.col.sector": "板块",
    "market.col.region": "地区",
    "market.dl.quotes": "⬇ 下载行情表（CSV）",
    "market.dl.master": "⬇ 下载证券主表（CSV）",
    "market.dl.master_help": "完整 universe_member 表——代码 / 名称 / 领域 / 板块 / 地区。",
    "market.onboarding.title": "如何阅读本页",
    "market.onboarding.body": (
        "**范围**：看板股票池内全部标的、所有行业——一页扫全市场。\n\n"
        "**价格 / 倍数**：来自 `snapshots.db`（每日 cron），与其他页同源。\n\n"
        "**下载**：*行情表* = 当前筛选后所见行；*证券主表* = 股票池名册本身，便于同步进你自己的工具。"
    ),

    # ── SEC 财报数据 ──
    "sec.title": "SEC 财报数据",
    "sec.caption": "美股标的的 SEC XBRL 申报（us-gaap / ifrs-full）。来源：data.sec.gov。",
    "sec.choose": "选择一只美股标的",
    "sec.pick_prompt": "在上方选择标的以加载其 SEC 财报数据。",
    "sec.warn.non_us": "**{ticker}** 不在美股池内——SEC 财报数据仅覆盖美股申报人。",
    "sec.warn.no_xbrl": "**{ticker}** 未向 SEC 申报 XBRL 数据（多为 OTC 一级 ADR），无数据可显示。",
    "sec.warn.not_fetched": "**{ticker}** 的 SEC 数据尚未缓存。请运行 `jobs/fetch_sec_facts.py` 或等待每周刷新。",
    "sec.badge.fetched": "缓存于 {fetched}",
    "sec.badge.latest_filed": "最新申报 {filed}",
    "sec.badge.taxonomy": "会计准则：{tax}",
    "sec.period.annual": "年度（FY）",
    "sec.period.quarterly": "季度",
    "sec.period.label": "期间口径",
    "sec.section.kpi": "核心财报指标",
    "sec.kpi.na": "—",
    "sec.kpi.fallback": "回退概念",
    "sec.kpi.trace": "来源：{concept} · {form} · FY{fy} {fp} · 期末 {end} · 申报 {filed} · {accn}",
    "sec.section.timeseries": "概念时间序列",
    "sec.ts.pick": "概念",
    "sec.ts.freq": "频率",
    "sec.ts.yoy": "同比 %",
    "sec.ts.qoq": "环比 %",
    "sec.ts.empty": "该概念在所选频率下无时间序列。",
    "sec.section.browser": "全量财报数据",
    "sec.browser.search": "筛选概念 / 标签",
    "sec.browser.form": "申报表",
    "sec.browser.taxonomy": "会计准则",
    "sec.browser.shown": "显示 {shown} / 共 {total} 条",
    "sec.browser.dl": "⬇ 下载筛选结果（CSV）",
    "sec.col.concept": "概念",
    "sec.col.concept_cn": "中文名",
    "sec.col.taxonomy": "准则",
    "sec.col.unit": "单位",
    "sec.col.value": "数值",
    "sec.col.start": "起始",
    "sec.col.end": "截止",
    "sec.col.form": "申报表",
    "sec.col.fy": "财年",
    "sec.col.fp": "财季",
    "sec.col.filed": "申报日",
    "sec.section.comp": "可比表导出",
    "sec.comp.pick_tickers": "选择对比标的",
    "sec.comp.pick_kpis": "指标（最新年度）",
    "sec.comp.dl": "⬇ 下载可比表（CSV）",
    "sec.comp.hint": "各标的取最新年度财年值。FY End 列标示不同申报人的期间差异。",
    "sec.col.fy_end": "财年截止",
    "sec.onboarding.title": "如何阅读本页",
    "sec.onboarding.body": (
        "**来源**：SEC Company Facts API（完整 XBRL）。仅美股标的——港股 / A 股 / "
        "OTC-ADR 申报人不在 SEC，会相应标注。\n\n"
        "**会计准则**：美国本土申报人用 `us-gaap`；外国申报人（如阿斯利康、诺华）"
        "用 `ifrs-full`。KPI 卡在两套准则间回退，外国标的不会空白。\n\n"
        "**KPI 卡**：每张显示最新申报值并附完整来源溯源（概念 / 申报表 / 期间 / 申报日）。"
        "*回退概念* 徽标表示由非主概念提供数值（如概念迁移）。\n\n"
        "**刷新**：缓存于 `snapshots.db`，由 GitHub Actions 每周自动刷新——无需手动抓取。"
    ),

    # ── AI 域页面（a1–a5）——以 domain='ai' 镜像 healthcare 各页 ──
    "ai.cov.title": "AI 全景标的",
    "ai.cov.caption": "AI 算力 / 半导体产业链全景——L1–L6 共 135 标的（美 / 日 / 韩 / A股）。最新数据：{date}",
    "ai.cov.col.vs_sox": "vs SOX 年初至今",
    "ai.cov.caption.source": "展示 {n} 只 AI 标的，跨 6 个产业链层级。AI 暂无 CMSI 覆盖名单——此处为完整跟踪股票池。",
    "ai.cov.onboarding.title": "如何阅读本页",
    "ai.cov.onboarding.body": (
        "**AI 全景标的** 是本看板跟踪的 AI 算力 / 半导体产业链全景——AI 暂无 CMSI 覆盖名单，"
        "故本页呈现全部标的（135 只），按 6 个产业链层级分组（L1 设备 → L6 服务器）。\n\n"
        "**vs SOX 年初至今** = 该标的年初至今涨跌幅减去 ^SOX（费城半导体指数）年初至今——"
        "AI 域主基准，替代以港股为中心的医疗覆盖页所用的恒指。\n\n"
        "**默认**：按市值降序、中文名优先。价格 / 倍数来自 `snapshots.db`（每日 cron）。"
    ),
    "ai.ov.title": "AI 总览",
    "ai.heat.title": "AI 板块热力图",
    "ai.scan.title": "AI 估值扫描器",
    "ai.sec.title": "AI · SEC 财报数据",
    "ai.sec.caption": "美股 AI 标的的 SEC XBRL 申报（us-gaap / ifrs-full）。来源：data.sec.gov。",
    "ai.section.benchmark": "域基准（^SOX）与同业",

    # ── Healthcare · Capital Markets 投融资（P0a aggregate tracker）──
    "capital.page.title": "投融资",
    "capital.page.caption": "全球医疗健康资本市场——BD/许可、并购、VC/IPO 月度资金流追踪（医药 / 器械 / 数字医疗）。",
    "capital.page.asof": "数据截至 {date}（滚动 12 月窗口）",
    "capital.cadence_note": (
        "口径：aggregate 资金流为**月度**策划数据（MEDIUM 可靠性），逐数字标来源与截至月；"
        "MNC 资产负债为 SEC XBRL（HIGH）。本页只搬 deal 事实数字，**不含任何卖方评级**。"
    ),
    # KPI strip
    "capital.kpi.ttm": "滚动12月总投融资额",
    "capital.kpi.ttm_foot": "窗口 {first} → {last}",
    "capital.kpi.latest": "最新月投融资额",
    "capital.kpi.latest_foot": "{month} · 环比 {mom}",
    "capital.kpi.deals": "最新月总成交笔数",
    "capital.kpi.deals_foot": "{month} · 全窗口累计 {ttm:,} 笔",
    "capital.kpi.chinaout": "China-OUT 最大单",
    "capital.kpi.chinaout_foot": "头条 $15.2B → 真实现金 $950M（B3·恒瑞-BMS）",
    # Trend section
    "capital.section.trend": "资金流趋势",
    "capital.section.trend_meta": "柱=投融资额 · 线=成交笔数",
    "capital.segments.pick": "选择序列",
    "capital.chart.capital": "投融资额",
    "capital.chart.deals": "成交笔数",
    "capital.series.hc_total": "总投融资额",
    "capital.series.pharma_ma": "药 M&A",
    "capital.series.pharma_vc": "药 VC&IPO",
    "capital.series.device_ma": "器械 M&A",
    "capital.series.device_vc": "器械 VC&IPO",
    "capital.series.digital_vc": "数字医疗 VC&IPO",
    "capital.unit.bn": "十亿美元",
    "capital.unit.mn": "百万美元",
    # Sub-sector sparkline grid
    "capital.section.segments": "细分板块走势",
    "capital.section.segments_meta": "近 12 月投融资额（USD mn）",
    "capital.domain.pharma": "医药（M&A + VC&IPO）",
    "capital.domain.device": "器械（M&A + VC&IPO）",
    "capital.domain.digital": "数字医疗（仅 VC&IPO）",
    "capital.domain.digital_foot": "注：数字医疗仅追踪 VC&IPO，无独立 M&A 序列。",
    "capital.reconcile_note": (
        "⚠️ 口径说明：5 个细分序列之和 **不等于**「总投融资额」——后者覆盖更广的 universe。"
        "细分图仅反映所追踪的 5 个子板块（USD mn），勿读作总额的 100% 拆分。"
    ),
    # China-OUT
    "capital.section.chinaout": "China-OUT 主线",
    "capital.chinaout.eyebrow": "中国出海许可制度性拐点",
    "capital.chinaout.body": (
        "中国 license 已从「零星出海事件」变成 MNC 标准 pipeline 补给渠道。"
        "**NextPharma 2025-01→09 Top 25 deals 中，中国 OUT 占 13/25 = 52%**"
        "（来源: NextPharma 720 deals，截至 2025-09-04），2026 Q2 比例进一步上升。\n\n"
        "**4-5 月中国 OUT 已知合计 $19.3B**（恒瑞-BMS $15.2B + Insilico-Lilly $2.75B + "
        "海思科-AbbVie $745M + Amoytop-Aligos $445M + Huahui-BeOne $120M）——"
        "仅 BMS-恒瑞一单已超 2025 全年多个月份的全行业 BD 总值。\n\n"
        "⚠️ **合规口径**：恒瑞头条 $15.2B 含 $14.25B contingent milestones，"
        "真实 structured cash 仅 $950M（B3 拆解）。下游估值须按 upfront / milestone 拆开建模，"
        "不得用头条值直接加总。"
    ),
    # MNC dry-powder
    "capital.section.mnc": "MNC 资产负债 · 干火药",
    "capital.section.mnc_meta": "2026Q1 · SEC XBRL（HIGH）",
    "capital.mnc.col.company": "公司",
    "capital.mnc.col.cash": "现金 $bn",
    "capital.mnc.col.debt": "总债务 $bn",
    "capital.mnc.col.net": "净现金 $bn",
    "capital.mnc.col.form": "申报表",
    "capital.mnc.col.date": "申报日",
    "capital.mnc.note": (
        "6 家标「—」为无 us-gaap 现金披露（NVS/AZN/SNY/NVO/PHG 为 20-F ADR，GEHC 现金字段缺）——"
        "**非零**，勿读作无现金。另：us-gaap 现金口径不含短期投资，PFE/MRK 等现金或被低估。"
    ),
    # Methodology + disclaimer
    "capital.method_expander": "方法论与来源（B1-B7 cross-check）",
    "capital.method_body": (
        "**数据源分层（research-data.md）**：aggregate 月度资金流 = MEDIUM（策划口径，PitchBook 式）；"
        "MNC 资产负债 = HIGH（SEC EDGAR 10-Q/20-F XBRL）。\n\n"
        "**B3 拆解纪律**：任何头条 deal 金额须可拆到 upfront + milestone + structured/CVR；"
        "sum-check 不过标 confidence=MEDIUM。\n\n"
        "**B6 不对称源**：A股/HK 单源（HKEX/cninfo）可 HIGH；US private deal 需 3 源。\n\n"
        "**单位归一**：总额原始为 USD bn、子序列为 USD mn，loader 已统一归一以防图表混标。"
    ),
    "capital.disclaimer": (
        "本页为研究台多源 cross-check 数据底稿，非投资建议。头条 deal 金额按 B3 可拆解为真实现金；"
        "MEDIUM 源仅取数字事实，**不采纳任何卖方评级**。数字均标（来源, 截至）。"
    ),

    # ── Capital Markets · Q1 2026 公开源季度快照（Option-2，替代月度 PitchBook）──
    "capital.q.asof": "最新完整季度 Q1 2026 · 季度颗粒（非月度）",
    "capital.q.freshness": (
        "📅 **数据节奏**：公开源均为**季度**口径——最新完整季度 **Q1 2026**（Jan-Mar）。"
        "Q2 2026（4-6月）报告 ~7 月中才出，在那之前 4/5 月只有 deal-level 不完整 tally。"
        "原 PitchBook 月度颗粒已**无法复现**（免费源无月度）。"
    ),
    "capital.q.cadence_note": (
        "口径：全部数字来自**公开已发布**报告（JPMorgan / DealForma / Rock Health / Galen Growth / "
        "CB Insights / Renaissance / Bain），逐项带来源 URL + 发布日 + 口径标签 + HIGH/MEDIUM tier。"
        "多源交叉验证 + 对抗式核源。**不采纳任何卖方评级**。"
    ),
    # KPI（4 张,各自口径不同,不可相加）
    "capital.q.kpi.ma": "生物药 M&A",
    "capital.q.kpi.ma_foot": "Q1'26 · upfront 现金口径 · JPM+DealForma 收敛 ±$0.1B · 25-32 笔",
    "capital.q.kpi.lic": "生物药许可",
    "capital.q.kpi.lic_foot": "Q1'26 · announced biobucks · upfront 仅 ~6%（milestone 为主）",
    "capital.q.kpi.vc": "生物药风投",
    "capital.q.kpi.vc_foot": "Q1'26 · 同比 −20%（vs $8.6B）· 全球 · 许可正替代 VC",
    "capital.q.kpi.dh": "数字医疗 VC（全球）",
    "capital.q.kpi.dh_foot": "Q1'26 · 全球 216 笔 · 美国子集 $4.0B(Rock) · Galen+CB 收敛 4%",
    # Scorecard
    "capital.q.section.scorecard": "Q1 2026 分段记分卡",
    "capital.q.section.scorecard_meta": "每行带口径 / 地域 / tier / 来源",
    "capital.q.col.segment": "分段",
    "capital.q.col.value": "Q1'26 $B",
    "capital.q.col.count": "笔数",
    "capital.q.col.prior": "Q1'25 $B",
    "capital.q.col.yoy": "同比 %",
    "capital.q.col.measure": "口径",
    "capital.q.col.geo": "地域",
    "capital.q.col.tier": "可靠性",
    "capital.q.col.source": "来源",
    # 分段名
    "capital.seg.biopharma_ma": "生物药 M&A",
    "capital.seg.biopharma_licensing": "生物药许可（BD）",
    "capital.seg.biopharma_venture": "生物药风投",
    "capital.seg.digital_health_vc_us": "数字医疗 VC（美国）",
    "capital.seg.digital_health_vc_global": "数字医疗 VC（全球）",
    "capital.seg.us_biotech_ipo": "美股 biotech IPO",
    "capital.seg.medtech_ma": "器械 M&A",
    # 口径标签
    "capital.measure.upfront_cash": "首付现金",
    "capital.measure.incl_contingents": "含或有(CVR)",
    "capital.measure.announced_biobucks": "公布总额",
    "capital.measure.raised": "募集额",
    "capital.measure.proceeds": "募资额",
    "capital.measure.disclosed_value": "披露金额",
    # 地域 badge
    "capital.geo.global": "全球",
    "capital.geo.us": "美国",
    # YoY 图
    "capital.q.section.yoy": "风投 / VC 同比",
    "capital.q.section.yoy_meta": "仅同量级、有同比的分段（避免混口径）",
    # Medtech 注
    "capital.q.section.medtech": "器械 M&A（缺口）",
    "capital.q.medtech_note": (
        "⚠️ 免费公开源**无器械 M&A 季度序列**。唯一可引是 Bain **FY2025 不完整年**（1-11月）"
        "**~$80B**（经 MedTech Dive 转引,MEDIUM,笔数未披露），超过前三年总和、H2≈2×H1。"
        "**按 partial-FY 单点标注,不当季度柱**。器械占 Q1'26 全行业 M&A 31%(8 季新高,Biotechgate)。"
        "大单:BSX-Penumbra $14.5B(H1'26 close)、Abbott-Exact Sciences $23B。"
    ),
    # FY baselines
    "capital.q.section.baselines": "FY2025 基准（趋势背景）",
    "capital.q.baselines.col.metric": "指标",
    "capital.q.baselines.col.value": "FY2025 $B",
    "capital.q.baselines.col.count": "笔数",
    "capital.q.baselines.col.source": "来源",
    # China-OUT 重定位(partial-Q2,围栏)
    "capital.q.chinaout_wall": (
        "⚠️ 以下为 **4-5 月 deal-level 不完整 tally**（非完整季度 aggregate，LOW/部分披露）——"
        "与上方 Q1'26 公开季度数字**口径不同,勿混读**。保留因对你 China-OUT 主线有信息价值。"
    ),
    # 方法论(公开源)
    "capital.q.method_body": (
        "**数据源（全部公开已发布，逐项 URL 见下）**：\n\n"
        "- 生物药 M&A / 许可 / 风投 / IPO：JPMorgan Q1 2026 Biopharma 报告、DealForma、Renaissance、BioPharma Dive\n"
        "- 数字医疗 VC：Rock Health（美国）、Galen Growth（全球）、CB Insights（全球）\n"
        "- 器械 M&A：Bain（经 MedTech Dive）— FY2025 不完整年\n\n"
        "**口径纪律**：M&A 区分 upfront 现金 vs 含 contingent；许可是 announced biobucks（upfront 仅 ~6%）；"
        "数字医疗美国(Rock)与全球(Galen/CB)分列不相加。**不同口径不可加总。**\n\n"
        "**时效**：Q2 2026 报告 ~7 月中出,计划届时刷新。"
    ),

    # ── Pharma MNC M&A（deal-level，MNCs basket xlsx / mnc-deal-scanner）──
    "mnc_ma.page.asof": "13 家药企 MNC · 历史并购",
    "mnc_ma.intro": "13 家全球药企 MNC 的历史并购全集——deal-level，可按公司 / 治疗领域 / 年份切。数据来自 MNCs basket（mnc-deal-scanner skill 维护）。",
    "mnc_ma.source_note": "来源：MNCs basket summary（{source}）。金额含已披露(Actual)与合理估算(Estimated)；deal-level 多源 cross-check。**不含任何卖方评级**。",
    "mnc_ma.kpi.total": "历史并购总额",
    "mnc_ma.kpi.total_foot": "{n} 笔 · {ymin}-{ymax} · 13 家药企 MNC",
    "mnc_ma.kpi.deals": "并购笔数",
    "mnc_ma.kpi.deals_foot": "已披露 {actual} · 估算 {est}",
    "mnc_ma.kpi.top": "最活跃买家",
    "mnc_ma.kpi.top_foot": "{company} · {n} 笔",
    "mnc_ma.kpi.biggest": "史上最大单",
    "mnc_ma.kpi.biggest_foot": "{acq} 收 {tgt} · {year}",
    "mnc_ma.section.league": "各药企并购总额",
    "mnc_ma.section.league_meta": "谁最爱买（USD bn，累计）",
    "mnc_ma.section.ta": "按治疗领域",
    "mnc_ma.section.ta_meta": "并购金额分布（USD bn）",
    "mnc_ma.section.timeline": "并购历年走势",
    "mnc_ma.section.timeline_meta": "各年并购总额（USD bn）",
    "mnc_ma.section.top": "史上最大并购 TOP 20",
    "mnc_ma.section.table": "并购明细",
    "mnc_ma.section.table_meta": "可按公司筛选",
    "mnc_ma.chart.by_company": "各药企历史并购总额",
    "mnc_ma.chart.by_ta": "并购金额 · 按治疗领域",
    "mnc_ma.chart.by_year": "历年并购总额",
    "mnc_ma.col.ticker": "公司",
    "mnc_ma.col.company": "收购方",
    "mnc_ma.col.target": "标的",
    "mnc_ma.col.year": "年月",
    "mnc_ma.col.size": "金额 $B",
    "mnc_ma.col.ta": "治疗领域",
    "mnc_ma.col.basis": "口径",
    "mnc_ma.filter.company": "筛选公司",
    "mnc_ma.filter.all": "全部",
    "mnc_ma.basis.Actual": "已披露",
    "mnc_ma.basis.Estimated": "估算",
    "mnc_ma.disclaimer": "本页为药企并购历史数据底稿，非投资建议。金额含估算项（已标注口径）；deal 事实数字，不采纳卖方评级。",
    # 2026 YTD M&A（置顶）
    "mnc_ma.section.ytd": "2026 年至今并购",
    "mnc_ma.section.ytd_meta": "今年真收购（M&A，不含 BD/合作）",
    "mnc_ma.ytd.count": "2026 M&A 笔数",
    "mnc_ma.ytd.count_foot": "合计 ${value:.1f}B · 仅真收购",
    "mnc_ma.ytd.total": "2026 M&A 总额",
    "mnc_ma.ytd.total_foot": "{n} 笔 · 不含 BD/合作",
    "mnc_ma.ytd.biggest": "今年最大收购",
    "mnc_ma.ytd.biggest_foot": "{acq} 收 {tgt}",
    "mnc_ma.ytd.bd_count": "2026 BD/合作",
    "mnc_ma.ytd.bd_foot": "不计入 M&A · 详见 BD tab",
    "mnc_ma.ytd.bd_note": "⚠️ M&A = 真收购(控制权转移);BD = license/option/合作(无控制权转移)。恒瑞-BMS $15.2B 是 13-program 战略合作,属 **BD 不是 M&A**——见下方「BD/合作」区。",
    # M&A-only 强调
    "mnc_ma.ma_only": "（仅真收购 M&A，BD/合作单列）",
    # BD 区
    "mnc_ma.section.bd": "BD / 合作",
    "mnc_ma.section.bd_meta": "授权交易（首付 / 里程碑 / 总对价）· 来自 ED Funding 报告 + 2026",
    "mnc_ma.col.type": "类型",
    "mnc_ma.bd.col.licensor": "授权方",
    "mnc_ma.bd.col.licensee": "被授权方",
    "mnc_ma.bd.col.asset": "药物/技术",
    "mnc_ma.bd.col.phase": "阶段",
    "mnc_ma.bd.col.region": "区域",
    "mnc_ma.bd.col.date": "时间",
    "mnc_ma.bd.sources": "2026 BD 来源（点击打开）：",
    "mnc_ma.section.sources": "数据来源",
    "mnc_ma.sources_note": "deal 官方公告发布于各药企 IR / newsroom，点击打开核对：",
    "mnc_ma.col.total": "总额 $B",
    "mnc_ma.col.upfront": "首付 $B",
    "mnc_ma.col.milestone": "里程碑 $B",
    "mnc_ma.ytd.sources": "2026 M&A 来源（点击打开公告）：",
    "mnc_ma.col.src": "来源",
    # ── M&A / BD tabs + BD insight layer ──
    "capital.tab.ma": "M&A · 并购",
    "capital.tab.bd": "BD · 许可合作",
    "capital.def": "M&A = 控制权转让（收购/合并）；BD = 授权 / 期权 / 合作（无控制权转让）。",
    "capital.bd.section.ytd": "2026 YTD BD",
    "capital.bd.section.ytd_meta": "本年至今授权交易（截至 2026-05，部分期）",
    "capital.bd.ytd.total": "2026 潜在总额",
    "capital.bd.ytd.total_foot": "含里程碑 · {n} 笔",
    "capital.bd.ytd.upfront": "2026 首付款",
    "capital.bd.ytd.upfront_foot": "已确认现金部分",
    "capital.bd.ytd.count": "2026 交易数",
    "capital.bd.ytd.count_foot": "2025 全年 {y} 笔",
    "capital.bd.ytd.biggest": "最大单笔",
    "capital.bd.ytd.biggest_foot": "{lor} → {lee}",
    "capital.bd.contingent": "⚠️ 里程碑为或有付款，不代表已确认收入；总额含未披露 / 部分披露条款。",
    "capital.bd.section.league": "BD League · 全量 2025–2026",
    "capital.bd.section.league_meta": "授权交易经济学 · 单一来源 bd_deals.csv（99 笔）",
    "capital.bd.kpi.total": "BD 交易总额",
    "capital.bd.kpi.total_foot": "含里程碑 · Σ首付 ${u:.1f}B vs Σ里程碑 ${m:.1f}B",
    "capital.bd.kpi.upfront_ratio": "首付占比（中位）",
    "capital.bd.kpi.upfront_ratio_foot": "首付/总额中位数 · ~5% = 95% 押在里程碑",
    "capital.bd.kpi.china": "中国授出占比",
    "capital.bd.kpi.china_foot": "按金额 · 中国药企授权方 ${b:.0f}B",
    "capital.bd.kpi.topmnc": "最活跃 MNC 买方",
    "capital.bd.kpi.topmnc_foot": "{name} · {n} 笔",
    "capital.bd.section.bylicensee": "BD League · 按被授权方（MNC 买方）",
    "capital.bd.section.bylicensee_meta": "按交易笔数 · MNC 引进胃口（非金额——里程碑会膨胀）",
    "capital.bd.chart.licensee": "MNC 买方榜（按 BD 交易笔数）",
    "capital.bd.section.byta": "按疾病领域分布",
    "capital.bd.section.byta_meta": "按潜在总额（含里程碑）· 与 M&A 按 TA 同轴可比",
    "capital.bd.chart.ta": "BD 交易额（按疾病领域）",
    "capital.bd.section.byphase": "MNC 介入阶段分布",
    "capital.bd.section.byphase_meta": "按交易笔数 · MNC 往上游伸多深（M&A 给不出）",
    "capital.bd.chart.phase": "MNC 介入阶段（按笔数）",
    "capital.bd.section.byyear": "年度走势",
    "capital.bd.chart.year": "BD 交易笔数（按年）",
    "capital.bd.note.year": "柱高 = 交易笔数；2026 为 YTD（截至 2026-05），里程碑膨胀不宜直接跨年比金额。",
    "capital.bd.section.top": "TOP 20 BD 交易",
    "capital.bd.section.table": "全部 BD 交易（筛选）",
    "capital.bd.note.league": "* MNC 买方榜已剔除被授权方为 NewCo/小 biotech 或方向特殊（MNC 往外授）的交易，使榜单代表真实 MNC 引进；计数图与下方明细表仍含全部 99 笔。1 笔里程碑＞总额的数据异常行（Evaxion→默克）已从金额口径剔除。",
    "capital.bd.unit.deals": "笔数",
    "capital.bd.filter.licensee": "按被授权方（MNC）筛选",
    "capital.bd.filter.licensor": "按授权方筛选",
    "capital.bd.filter.all": "全部",
}
