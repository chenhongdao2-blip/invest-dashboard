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
    "common.col.ytd": "年初至今 %",
    "common.col.mcap_b": "市值（十亿美元 $B）",
    "common.col.trail_pe": "静态 P/E",
    "common.col.fwd_pe": "动态 P/E",
    "common.col.ev_ebitda": "EV/EBITDA",
    "common.col.ev_sales": "EV/Sales",
    "common.col.fcf_yld": "自由现金流收益率",
    "common.col.pb": "P/B",
    "common.warn.fetch_fail": "实时获取失败（yfinance）——检查网络/代理。",

    # ── Home ──
    "home.title": "多领域投资看板",
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
        "**数据口径**：估值倍数来自 **yfinance**（静态 P/E + 12 个月动态 P/E）。"
        "多年期预测（25E / 26E / 27E）需 Bloomberg / FactSet，**不在本看板范围**。"
        "本看板用于快速目视扫描；精确一致预期请以你的 Excel 对照表为准。"
    ),
    "home.caveat.repo": (
        "仓库：[github.com/chenhongdao2-blip/invest-dashboard]"
        "(https://github.com/chenhongdao2-blip/invest-dashboard) · "
        "数据：SQLite 随仓库提交 · 自动更新：GitHub Actions 定时（美股 22:30 UTC + 港股 09:00 UTC）"
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
    "hc.section.benchmark": "领域基准（XLV）及同业",
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
    "drill.metric.last_local": "最新价（本币）",
    "drill.metric.last": "最新价",
    "drill.metric.mcap": "市值",
    "drill.metric.fwd_pe": "动态 P/E",
    "drill.consensus_tp": "一致目标价：**{tp}**（较最新 {upside}）{analysts}",
    "drill.no_mults": "无估值快照——该标的可能仅为选股池标的（不在主获取池）。",
    "drill.section.price": "价格 · 美元归一",
    "drill.ret_windows": "区间收益率",
    "drill.col.window": "区间",
    "drill.col.return": "收益 %",
    "drill.latest_mults": "最新估值倍数（yfinance）",
    "drill.col.metric": "指标",
    "drill.col.value": "数值",
    "drill.ext.expander": "扩展基本面（yfinance.info 实时——点击获取）",
    "drill.ext.fetch": "实时获取",
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
}
