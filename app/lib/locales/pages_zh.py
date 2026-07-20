"""中文 locale — Phase 2（Home + 5 个 healthcare 页 + 共享组件）。

由 lib.i18n 与 zh.py（Phase 1）合并。术语沿用 zh.py 头部锁定表。
onboarding 正文多数沿用源页既有中文（精修），EN 侧为其翻译。
中文措辞经 GLM 决策定稿。
"""

STRINGS = {
    # ── 板块轮动 (RRG) ──
    "rot.title": "板块轮动 · 相对轮动图 RRG",
    "rot.caption": "相对轮动地图——各板块相对市场基准的「相对强弱×动量」投影。是市场内部的注意力地图，不是择时信号。",
    "rot.ctrl.header": "RRG 参数",
    "rot.ctrl.tail": "尾巴长度（周）",
    "rot.ctrl.tail_help": "每个板块点后画几周的轨迹尾巴。",
    "rot.ctrl.thr": "过热阈值（z）",
    "rot.ctrl.thr_help": "Leading 板块的拥挤度 z-score 超过此值时标记 [过热]。",
    "rot.tab.a": "A股 · 申万/中证",
    "rot.tab.hk": "港股 · 恒生行业",
    "rot.note.hk": "港股拥挤度 = 板块换手率 z-score（iFind 周线）。板块 = 11 个恒生综合行业指数 vs 恒生指数。",
    "rot.empty.hk": "无港股板块数据——请跑 jobs/load_sw_industry.py。",
    "rot.tab.us": "美股 · GICS",
    "rot.note.a": "A股拥挤度 = 板块换手率 z-score（iFind 周线）。板块 = 标准申万一级 31 行业 vs 沪深300。",
    "rot.note.us": "美股拥挤度 = 价格拉伸 z（收盘 vs 200日均线）——超买代理，非真换手/breadth（v2）。板块 = 11 个 GICS SPDR ETF vs 标普500。",
    "rot.empty.a": "无 A 股板块数据——请跑 jobs/load_sw_industry.py。",
    "rot.empty.us": "无美股基准数据——请跑 jobs/fetch_eod.py。",
    "rot.tab.drill": "美股 · 个股下沉",
    "rot.drill.domain": "领域",
    "rot.drill.sector": "板块",
    "rot.drill.topn": "显示数量",
    "rot.drill.topn_help": "按 20 日成交额（流动性）取前 N 只成分股绘制；合成板块指数仍用全部成分股。",
    "rot.drill.empty": "该板块无足够成分股价格数据可下沉。",
    "rot.drill.trunc": "已按流动性显示前 {shown}/{total} 只成分（合成指数用全部 {total} 只）。",
    "rot.drill.short": "另有 {n} 只成分因价格历史不足（< 约 22 周）暂不参与，数据补全后自动纳入。",
    "rot.note.drill": "个股下沉：成分股 vs **等权合成板块指数**（不是市场基准），回答「谁在板块内部领跑/掉队」。拥挤度 = 个股价格拉伸 z（收盘 vs 50 日均线，短窗超买代理）。⚠️ 个股价格仅约 9 个月历史（prices_daily），有效 RRG 周数偏短，仅作板块内部结构参考。",
    "rot.tab.xmkt": "跨市场 · USD 同框",
    "rot.xmkt.markets": "纳入市场",
    "rot.xmkt.pern": "每市场板块数",
    "rot.xmkt.pern_help": "每个市场按偏离度（离原点远近）取前 N 个板块绘制，避免 53 个板块挤爆画布。",
    "rot.xmkt.pick": "请至少选择一个市场。",
    "rot.xmkt.empty": "缺跨市场数据——请跑 jobs/fetch_fx_world.py（URTH/FX）与 jobs/load_sw_industry.py（申万/恒生）。",
    "rot.xmkt.panel_frozen": "↑ 含汇率（USD 同框）　／　↓ 汇率剥离（板块本币驱动，汇率冻结期初）——同一板块两图间的位移 = 该板块的汇率 beta（护栏③）。",
    "rot.note.xmkt": "跨市场：A/港/美板块统一换算 USD vs MSCI World（URTH，发达市场）。颜色 = 市场，仅以 URTH 作全球相对强弱标尺。⚠️ A/港板块为申万/恒生周线 seed（~52 周），美股为 GICS ETF 日线，口径略有差异；拥挤度（护栏②）见各单市场 tab。",
    "rot.onboard.title": "RRG 怎么读",
    "rot.onboard.body": (
        "**四象限顺时针演进：**改善（弱但反弹）→ 领先（强且改善）→ 转弱（强但动量衰减）→ 滞后（弱且转弱）。\n\n"
        "- **横轴 = RS-Ratio**（相对基准的强弱）；**纵轴 = RS-Momentum**（其变化率）。原点 = 100/100。\n"
        "- **点** = 板块当前位置；**尾巴** = 近期周度轨迹。\n"
        "- **红圈 [过热]** = Leading **且**拥挤——护栏②标出 RRG 自己看不到的危险区（筹码结构）。\n"
        "- **级别水印** = 护栏①——根据周期母框架判定战术 vs 战略资格。\n\n"
        "**第一性原则：**RRG 描述的是*已经发生*的相对状态（高置信事实），不预测方向（无预测力）。"
        "它回答\"走到哪一步了\"，不回答\"下一步涨不涨\"。"
    ),

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
    # hub.tbl.* — Market Hub 三块表（market_hub_tables iframe，zip5 设计）
    "hub.tbl.sp.title": "标普 500 子行业表现",
    "hub.tbl.sp.sub": "11 个 GICS 一级行业（SPDR Select Sector ETF 代理）· 默认按 YTD 排名 · 点击列头排序",
    "hub.tbl.hc.title": "医疗健康 · 基准",
    "hub.tbl.hc.sub": "医疗健康基准 ETF · 相对标普 = YTD 超额 · 点击列头排序",
    "hub.tbl.movers.title": "涨跌榜 · 1 日",
    "hub.tbl.movers.sub": "医疗健康覆盖池 · 按 1 日涨跌排序 · 价格为当地币种",

    "cov.title": "CMSI 覆盖名单",
    "cov.caption": "28 只官方覆盖名单——港股 15 / 美股 10 / A 股 3。最新数据：{date}",
    # cov.tbl.* — Coverage 玻璃卡片表（coverage_table iframe，zip5 设计）
    "cov.tbl.tab.hk": "HK",
    "cov.tbl.tab.us": "US",
    "cov.tbl.tab.cn": "CN",
    "cov.tbl.tab.all": "ALL",
    "cov.tbl.bench.own": "各自基准",
    "cov.tbl.cover": "覆盖",
    "cov.tbl.mcap_total": "总市值",
    "cov.tbl.ytd_med": "YTD 中位",
    "cov.tbl.bench_prefix": "",
    "cov.tbl.beat_label": "跑赢 ",
    "cov.tbl.unit_names": "只",
    "cov.tbl.median": "覆盖中位数",
    "cov.tbl.grp_ret": "回报 RETURNS %",
    "cov.tbl.grp_exc_prefix": "相对",
    "cov.tbl.grp_val": "估值 VALUATION ×",
    "cov.tbl.col.t": "代码",
    "cov.tbl.col.n": "名称",
    "cov.tbl.col.mcap": "市值 十亿$",
    "cov.tbl.col.ytd": "年初至今",
    "cov.tbl.col.m1": "1月",
    "cov.tbl.col.d5": "5日",
    "cov.tbl.col.d1": "1日",
    "cov.tbl.col.exc_prefix": "",
    "cov.tbl.col.exc": "基准超额",
    "cov.tbl.col.exc_suffix": "",
    "cov.tbl.col.peS": "静态P/E",
    "cov.tbl.col.peF": "动态P/E",
    "cov.tbl.col.evE": "EV/EBITDA",
    "cov.tbl.footnote": (
        "市值以 USD 十亿计；回报为 USD 总收益（含汇率）；估值来自 yfinance 快照（截至 {date}）；"
        "负/零倍数标 NM；基准超额＝个股 YTD − 本市场基准 YTD（pp）。有模型的标的名称后以 ● 标注。"
    ),
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
    "hc.rs.section_meta": "五组指数对比 · 窗口内重锚定",
    "hc.rs.win.meta": "REBASED = 100 · 共同交易日内联 · 每张卡片右上角独立切窗，切换即以窗口首日重锚定",
    "hc.rs.kicker.hk": "01 · 港股口径 · HK LENS",
    "hc.rs.kicker.msci": "02 · MSCI 中国口径 · ETF PROXY",
    "hc.rs.kicker.nbi": "03 · 美股生科 · US BIOTECH",
    "hc.rs.kicker.sphc": "04 · 美股医疗 · S&P HC",
    "hc.rs.kicker.aibio": "05 · 跨主题 · BIOTECH VS AI HARDWARE",
    "hc.rs.footnote": (
        "口径：各面板内所有序列按共同交易日内联，在当前窗口首日重锚定为 100；"
        "pp 徽章 = 红色主线相对该对照线的窗口内累计超额（主线 − 对照线，rebased 点数）。"
        "5D = 近 5 个共同交易日；1M / 6M 按日历回溯。"
    ),
    "hc.rs.hk.title": "恒生医疗保健 vs 恒生 vs 恒生科技",
    "hc.rs.msci.title": "MSCI 中国医疗保健 vs MSCI 中国（ETF 代理：KURE / MCHI）",
    "hc.rs.msci.src": "yfinance · ETF 代理（含息·USD）",
    # 释义 GLOSSARY 结构化卡（zip4 设计；旧 hc_indices_note 长段落已被替换）
    "hc.rs.gl.eyebrow": "释义 · GLOSSARY",
    "hc.rs.gl.title": "两个医疗指数怎么区分？",
    "hc.rs.gl.sub_right": "对应上方面板 01 / 02",
    "hc.rs.gl.comp_label": "成分",
    "hc.rs.gl.feat_label": "特征",
    "hc.rs.gl.how_label": "怎么用",
    "hc.rs.gl.note_right": "二者会分叉，属口径差异而非数据错误",
    "hc.rs.gl.badge1": "HSHCI",
    "hc.rs.gl.name1": "恒生医疗保健",
    "hc.rs.gl.tag1": "港股医疗 beta",
    "hc.rs.gl.chip1a": "纯离岸 · 不含 A 股",
    "hc.rs.gl.chip1b": "港元 · 价格指数 · 不含息",
    "hc.rs.gl.comp1": "香港上市医疗股：创新药 / Biotech / 器械 / 医疗服务",
    "hc.rs.gl.feat1": "Biotech 权重高、波动大",
    "hc.rs.gl.badge2": "MSCI · KURE",
    "hc.rs.gl.name2": "MSCI 中国医疗",
    "hc.rs.gl.tag2": "全中国医疗 beta",
    "hc.rs.gl.chip2a": "A 股 + H 股 + ADR",
    "hc.rs.gl.chip2b": "美元 ETF · 含息",
    "hc.rs.gl.comp2": "KURE 跟踪 MSCI China All Shares Health Care，含恒瑞医药、迈瑞医疗等 A 股大票",
    "hc.rs.gl.feat2": "口径更宽，A 股纳入摊薄了港股 Biotech 的极端波动",
    "hc.rs.gl.how1": (
        '讲<b>港股医疗去仓位 / Biotech</b> → 用 <span style="font-family:\'JetBrains Mono\','
        'monospace;font-size:11px;font-weight:700;color:#c8102e;">HSHCI</span>'
    ),
    "hc.rs.gl.how2": (
        '讲<b>全中国医疗 beta</b> → 用 <span style="font-family:\'JetBrains Mono\','
        'monospace;font-size:11px;font-weight:700;color:#1a1a1a;">MSCI（KURE）</span>'
    ),
    "hc.rs.nbi.title": "纳指生科 NBI · 标普生科 XBI vs 纳斯达克综合",
    "hc.rs.sphc.title": "标普 500 医疗保健 vs 标普 500",
    "hc.rs.aibio.title": "生物科技（NBI 大盘 · XBI 等权）vs AI 硬件（费城半导体 SOX）",
    "hc.rs.aibio.note": (
        "**怎么读这张图？**　把两大热门主题放在同一锚点（去年 8 月）同框：**红＝生物科技**"
        "（实线 NBI 大盘·市值加权 / 红虚线 XBI 标普生科·等权，代表中小盘 breadth），"
        "**青＝AI 硬件**（^SOX 费城半导体指数）。　"
        "**① NBI 与 XBI 的缺口** ＝ 大盘 vs 中小盘生科的强弱：XBI 领先 ＝ 中小盘普涨、breadth 强"
        "（并购 / 小票逼空驱动）；XBI 落后 ＝ 涨幅集中在大票、breadth 弱。　"
        "**② 生科红线与 AI 青线的剪刀差** ＝ 资金在两大主题间的相对轮动——AI 硬件长期领跑时生科多被虹吸，"
        "剪刀差收敛 / 反转常是风险偏好或利率预期切换的信号。　"
        "三条线同口径 rebased，仅看 beta，不含个股 alpha。"
    ),
    "hc.rs.ylabel": "rebased（起点 = 100）",
    "hc.rs.read": (
        "港股医疗独熊（较恒指 −22.4pp），主因**中国医疗特有风险**（流动性虹吸 / 集采 VBP / "
        "医保谈判），而非全球医疗 de-rating——佐证：NBI 与纳指基本持平，全球生科未同步走弱。"
        "美股大医疗 −9.3pp 则属药价（IRA/PBM）与 managed-care 赔付压力的板块 de-rating。"
    ),
    "hc.rs.lag": "{hero}较{peer} 跑输 {pp}pp",
    "hc.rs.lead": "{hero}较{peer} 跑赢 {pp}pp",
    "hc.rs.flat": "{hero}与{peer} 基本持平",
    "hc.rs.empty": "暂无指数对比数据——请运行 jobs/build_hc_overview_data.py 回补。",
    # HSHCI 长周期完整轨迹（−70% → 翻倍 → 回调）
    "hc.rs.hshci.kicker": "06 · 港股口径 · FULL CYCLE",
    "hc.rs.hshci.chip": "月收盘 · 绝对点位",
    "hc.rs.hshci.src": "iFind 指数月收盘（末点日频）",
    "hc.rs.hshci.vs_peak": "较峰",
    "hc.rs.hshci.vs_start": "较起点",
    "hc.rs.hshci.title": "恒生医疗保健指数：2021.7 以来完整轨迹（绝对点位）",
    "hc.rs.hshci.ylabel": "指数点位",
    "hc.rs.hshci.ann.start": "高位 {c:,.0f}",
    "hc.rs.hshci.ann.trough": "见底 {c:,.0f} ({p:+.0%})",
    "hc.rs.hshci.ann.peak": "反弹 {c:,.0f} ({p:+.0%})",
    "hc.rs.hshci.ann.now": "今 {c:,.0f} ({p:+.0%})",
    "hc.rs.hshci.caption": (
        "完整轨迹：{start_d} 高位 {start_c:,.0f} → {trough_d} 见底 {trough_c:,.0f}"
        "（自高位 {trough_pct:+.0%}）→ {peak_d} 反弹 {peak_c:,.0f}（较底 {peak_pct:+.0%}）"
        "→ {now_d} {now_c:,.0f}（较峰 {now_peak:+.0%}；较起点仍 {now_start:+.0%}）。"
        "来源：iFind 指数月收盘，截至 {asof}。"
    ),
    # ── 日本医药（区域 universe：hc_japan.yml，40 支）──
    "hc.jp.section": "日本医药 · Japan Healthcare",
    "hc.jp.section_meta": "40 支 · iFind 自选清单 (2026/05) · 收益 USD 口径",
    "hc.jp.sub.pharma": "制药",
    "hc.jp.sub.medtech": "医疗器械",
    "hc.jp.sub.diagnostics": "诊断·检测",
    "hc.jp.sub.distribution": "流通·服务",
    "hc.jp.col.subsector": "子板块",
    "hc.jp.chart.title": "日本医药专栏指数 vs TOPIX vs 日经 225（USD）",
    "hc.jp.hero": "日本医药专栏指数（40 支市值加权）",
    "hc.jp.bench.topix": "TOPIX（1305.T ETF 代理）",
    "hc.jp.bench.n225": "日经 225",
    "hc.jp.kicker": "日本医药 · JAPAN HC · USD 口径",
    "hc.jp.caption": (
        "专栏指数＝40 支市值加权（权重＝2026/05 市值快照，于指数基期归一，与所选窗口无关）；"
        "三条序列均为 USD 口径（含汇率，相对差值已大致互抵汇率项）；TOPIX 用 1305.T ETF 代理。"
        "窗口重锚定与 pp 徽章口径同上方「相对表现」版块。来源：yfinance EOD cron，截至 {asof}。"
    ),
    "hc.jp.detail": "40 支明细（按子板块 · USD 口径）",
    "hc.jp.read": (
        "日本医药的正确读法是**按定价货币分层**，而非按涨跌排序：第一三共（ADC：Enhertu/"
        "Datroway）、卫材（Leqembi）与器械三杰（泰尔茂/HOYA/奥林巴斯）是**全球定价资产**"
        "——收入以美元/欧元为主，弱日元是顺风；流通四社（Medipal/阿弗瑞萨/铃谦/东邦）与"
        "仿制药（泽井/东和）是**本土定价资产**——吃药价两年一调与医保收缩的逆风，弱日元"
        "还抬高其进口成本。专栏指数 vs TOPIX 的差值剔除了大盘 beta（同为 USD 口径，汇率项"
        "大致互抵），适合回答「日本医疗相对自身市场强弱」；判断个股请回到上表分层。"
    ),
    "hc.jp.note_delisted": (
        "原 42 支清单中 2 支因私有化退市剔除：HOGY MEDICAL（3593，凯雷 TOB，2026-05 退市）、"
        "久光制药（4530，MBO 非公开化）。"
    ),
    "hc.jp.empty": "暂无日本医药 universe——请运行 jobs/load_universe.py 回补。",
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
    # ── 美国医疗专业基金 13F · 共识持仓 + 季度变动 ──
    "hc.f13.section": "美国医疗专业基金 13F · 共识持仓与季度调仓",
    "hc.f13.section_meta": "12 家美国 HC 专业基金 · SEC EDGAR 13F-HR · 仅美股多头",
    "hc.f13.verdict": (
        "**结论**：{n_funds} 家基金（合计 13F 市值 ~${aum}bn，报告期 {period}）"
        "共识度最高的持仓是 **{top}**（{top_n} 家共同持有）；"
        "本季最热新建仓 **{hot}**（{hot_n} 家同季新买入）。"
    ),
    "hc.f13.consensus_h": "**共识持仓矩阵**（Top 15 共识标的 × 持有基金，格子＝该基金持仓市值 $M）",
    "hc.f13.consensus_note": "列头走势为 6 个月收盘 + 季末以来涨跌；格子颜色＝该基金对该标的的季度动向；13F 不含空头与非美股持仓。",
    "hc.f13.mx.holder": "机构",
    "hc.f13.mx.total": "合计",
    "hc.f13.mx.unch": "无标记＝持平",
    "hc.f13.newbuys_h": "**本季最热新建仓**（多家同季首次买入）",
    "hc.f13.exits_h": "**本季集体清仓**（多家同季全数卖出）",
    "hc.f13.perfund_h": "**分基金明细**（Top 15 持仓 + 该基金季度动向）",
    "hc.f13.legend": "🟢 青＝新建/加仓　🔴 红＝减仓/清仓　·　此处颜色表**季度调仓方向**，非当日涨跌",
    "hc.f13.read": (
        "13F 反映的是**报告期时点的美股多头仓位**（滞后最多 45 天），alpha 主要看两点："
        "①「多家同季新建仓」= smart money 共振信号，值得逐一过管线与催化剂；"
        "②「集体清仓」多为数据读出失败 / 被收购退市 / 拥挤度出清，需逐票分辨性质。"
        "共识持仓本身即高拥挤——更适合作专业投资者关注度的地图，而非直接买入清单。"
    ),
    "hc.f13.source": "来源：SEC EDGAR 13F-HR（公开申报，滞后季末最多 45 天）· jobs/fetch_13f_hc_funds.py 自动抓取",
    "hc.f13.empty": "暂无 13F 数据——请运行 jobs/fetch_13f_hc_funds.py 回补。",
    "hc.f13.none": "本季无记录。",
    "hc.f13.positions": "只持仓",
    "hc.f13.col.name": "标的",
    "hc.f13.col.n_funds": "持有家数",
    "hc.f13.col.value": "合计市值",
    "hc.f13.col.new": "新建",
    "hc.f13.col.add": "加仓",
    "hc.f13.col.trim": "减仓",
    "hc.f13.col.n_exits": "清仓家数",
    "hc.f13.col.funds": "基金",
    "hc.f13.col.spark": "6个月走势",
    "hc.f13.col.since_qend": "季末以来",
    "hc.f13.col.weight": "组合权重",
    "hc.f13.col.qoq": "季度动向",
    "hc.f13.col.chg": "持股数 Δ%",
    "hc.f13.qoq.NEW": "新建",
    "hc.f13.qoq.ADD": "加仓",
    "hc.f13.qoq.TRIM": "减仓",
    "hc.f13.qoq.UNCH": "持平",
    "hc.f13.prices_note": (
        "走势与「季末以来」涨跌以 {asof} 收盘计（yfinance），锚定 13F 报告期 {period}——"
        "即基金持仓快照**之后**的市场表现，用于判断信号是否已被 price in。"
    ),
    # --- 员工人数变化（扩招 vs 收缩）---
    "hc.hc.section": "员工人数变化 · 中国创新药企扩招 vs 收缩",
    "hc.hc.section_meta": "12 家中国创新药 / biotech · FY2024 → FY2025 · 集团合并在职员工",
    "hc.hc.chart.title": "员工人数变化（FY2024 → FY2025）",
    "hc.hc.chart.xlabel": "员工人数变化（人）",
    "hc.hc.legend": "🟢 青＝扩招　🔴 红＝收缩　·　此处颜色表**人力增减**，非当日涨跌",
    "hc.hc.verdict": (
        "**结论**：12 家中 {n_hire} 家扩招 / {n_cut} 家收缩，净 {net:+,} 人。"
        "最猛扩招 {top_hire_name}（{top_hire_delta:+,} 人），最大收缩 {top_cut_name}（{top_cut_delta:+,} 人）。"
    ),
    "hc.hc.read": (
        "与西方大药企 2025 年普遍裁员（Sanofi / Novo / Pfizer 各减数千）相反，国产创新药 "
        "**10/12 仍在扩招**——商业化放量的 biotech（信达 +33%、康方 +24%、康诺亚 +17%）扩得最猛，"
        "印证国产创新药仍处放量周期而非收缩周期。两家收缩的都是传统大票（中生、石药），"
        "属成熟仿制 + 转型期的产线 / 销售队伍优化，与 biotech 扩张是两种叙事。"
        "研判：**人力是经营姿态的领先信号**——扩招最集中处，即管理层放量信心所在。"
    ),
    "hc.hc.col.company": "公司",
    "hc.hc.col.ticker": "代码",
    "hc.hc.col.fy24": "FY2024",
    "hc.hc.col.fy25": "FY2025",
    "hc.hc.col.delta": "变化",
    "hc.hc.col.pct": "变化%",
    "hc.hc.source": (
        "来源：港交所年度业绩公告 / 年报「雇员及薪酬」段、公司 ESG 报告、iFind；"
        "口径＝集团合并在职员工总数（FY 年末）。"
    ),
    "hc.hc.empty": "暂无员工人数数据——请运行 jobs/cn_pharma_headcount_2025.py 回补。",
    "hc.dl.xlsx": "⬇ 下载本节数据 (Excel)",
    "hc.stale.warn": "⚠ 本节数据已 {days} 天未更新（截至 {asof}）。按 docs/healthcare-data-pipeline.md 回补。",
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
    # 旧 Styler 版 keys —— a3_ai_heatmap 仍在用（AI 域热力图未迁移新卡片）
    "heat.filter.sort_by": "排序依据",
    "heat.filter.sort_help": "默认按市值降序。",
    "heat.agg.expander": "{sector} 汇总（均值 / 中位数 / 加权）",
    "heat.agg.metric": "指标",
    "heat.caption.legend": "**配色图例**：收益率绿涨红跌；估值倍数（P/E、EV/EBITDA）绿低红高（绿=便宜）；自由现金流收益率绿高红低。代码采用 **彭博格式**（2269 HK / 4587 JP / 300760 CH）。最新数据：**{date}**",
    "heat.empty": "暂无横截面数据——请运行 jobs/fetch_eod 回补。",
    "heat.tbl.cover": "覆盖",
    "heat.tbl.mcap_total": "总市值",
    "heat.tbl.ytd_med": "YTD 中位",
    "heat.tbl.breadth": "YTD 广度",
    "heat.tbl.up": "涨",
    "heat.tbl.dn": "跌",
    "heat.tbl.unit_names": "家",
    "heat.tbl.median": "板块中位数",
    "heat.tbl.grp_ret": "回报 RETURNS %",
    "heat.tbl.grp_val": "估值 VALUATION ×",
    "heat.tbl.grp_cf": "现金流",
    "heat.tbl.col.t": "代码",
    "heat.tbl.col.n": "名称",
    "heat.tbl.col.mcap": "市值 十亿$",
    "heat.tbl.col.ytd": "年初至今",
    "heat.tbl.col.m1": "1月",
    "heat.tbl.col.d5": "5日",
    "heat.tbl.col.d1": "1日",
    "heat.tbl.col.peS": "静态P/E",
    "heat.tbl.col.peF": "动态P/E",
    "heat.tbl.col.fcf": "FCF收益",
    # 地区过滤 chips（表内客户端多选；全部点灭 = 全集）
    "heat.tbl.region.US": "美股",
    "heat.tbl.region.HK": "H股",
    "heat.tbl.region.CN": "A股",
    "heat.tbl.region.JP": "日股",
    "heat.tbl.region.KR": "韩股",
    "heat.tbl.sum.title": "板块汇总",
    "heat.tbl.sum.sub": "等权平均收益 · 共 {n} 标的 · 点击行切换下方板块",
    "heat.tbl.heat.title": "板块热力图",
    "heat.tbl.heat.sub": "个股横截面 · 倍数来自 yfinance（静态 + 12M 动态）· 点击列头排序",
    "heat.tbl.sum.col.sector": "板块",
    "heat.tbl.sum.col.n": "标的",
    "heat.tbl.sum.col.dist": "YTD 分布",
    "heat.tbl.sum.col.bench": "基准",
    "heat.tbl.footnote_dyn": "板块汇总为等权平均，YTD 分布条以列内最大幅度（±{max}%）为满刻度。",
    "heat.tbl.footnote": (
        '配色图例：回报列按列内幅度加深（<span style="color:#0d7680;font-weight:600;">青涨</span>'
        ' / <span style="color:#c8102e;font-weight:600;">红跌</span>）；估值倍数按列内分位'
        '（青 = 便宜 / 红 = 贵，NM 不参与）；FCF 收益青高红低。市值条为 √ 刻度。'
        '点击列头排序；「中位数」行为当前板块列中位。最新快照：{date}。'
    ),
    "heat.onboarding.title": "如何阅读本页",
    # heat.tbl.* 分叉键（新 iframe 卡片专用）；heat.onboarding.body / heat.caption.filter_note
    # 保持旧文案不动 —— a3_ai_heatmap（未迁移）仍在消费，语义与旧 Styler 表对应。
    "heat.tbl.onboarding.body": (
        "**倍数与收益**\n"
        "- **配色图例**：回报列青涨红跌（按列内幅度加深）；估值倍数按列内分位染色"
        "（青=便宜 / 红=贵，NM 不参与）；FCF 收益青高红低。\n"
        "- **选项卡**：表内上方 tabs 快速切换 7 个细分板块（即时，无刷新）。\n"
        "- **排序**：点击列头即按该列排序，再点反转；NM 恒沉底。\n\n"
        "**筛选** — **最小市值**（侧边栏）：过滤掉极小市值标的，避免其极端估值拉偏板块中位。"
    ),
    "heat.tbl.filter_note": "侧边栏可设市值下限。当小市值标的拉偏板块中位时（如 4587 JP $904M vs GILD $166B），该筛选很有用。",
    "heat.onboarding.body": (
        "**倍数与收益**\n"
        "- **配色图例**：收益率绿涨红跌；估值倍数（P/E、EV/EBITDA）绿低红高（绿=便宜）；"
        "自由现金流收益率绿高红低。\n"
        "- **选项卡**：上方选项卡快速切换细分板块。\n\n"
        "**筛选** — **最小市值**：过滤掉极小市值标的，避免其极端估值拉偏板块均值。\n\n"
        "**汇总**：展开下方「板块汇总」可看该板块的均值与中位数。"
    ),
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
    "drill.term.meta_line": "日K线 · MA5 / MA10 / MA20 · 成交量 · {hours}",
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
    "market.filters.sector_help": "选后只显示属于这些行业/子行业的标的（默认全显）。",
    "market.empty": "没有符合当前筛选的标的。",
    "market.click_hint": "👆 点行内「详情 ↗」→ 新标签打开个股；或用上方选股框 → 同标签进详情。",
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
    "capital.tab.ipo": "IPO · 打新追踪",
    "capital.def": "M&A = 控制权转让（收购/合并）；BD = 授权 / 期权 / 合作（无控制权转让）。",
    "capital.ipo.empty": "暂无 IPO 追踪数据 — 先在本地运行 jobs/build_hk_ipo_tracker.py（需 Wind 终端 + Futu OpenD）。",
    "capital.ipo.asof": "港股医疗 IPO 自 2025-04（恒瑞窗口）· 数据截至 {asof} · 来源 Wind+Futu，云端 yfinance 每日刷新",
    "capital.ipo.methodology": "口径：涨幅 = 发行价→最新收盘；破发 = 现价 < 发行价。聚合统计已剔除无招股价（介绍上市）、停牌（冻结价）、上市未满 20 交易日者。",
    "capital.ipo.kpi.total": "IPO 总数",
    "capital.ipo.kpi.total_foot": "{w} 家有招股价 · {s} 家停牌",
    "capital.ipo.kpi.broke": "破发率（已清洗）",
    "capital.ipo.kpi.broke_foot": "{n}/{d} 跌破发行价 · 全样本 {fn}",
    "capital.ipo.kpi.big": "≥100亿 家数",
    "capital.ipo.kpi.big_foot": "大+中市值（机构偏好区）",
    "capital.ipo.kpi.top": "最大涨幅",
    "capital.ipo.kpi.top_foot": "{name}",
    "capital.ipo.kpi.median": "中位涨幅",
    "capital.ipo.kpi.median_foot": "已清洗 {n} 家",
    "capital.ipo.section.bymkt": "破发率 × 市值分层",
    "capital.ipo.section.bymkt_meta": "结论层 · 市值越大越不破发（单调）",
    "capital.ipo.chart.bymkt": "破发率（按市值分层）",
    "capital.ipo.note.bymkt": "大 ≥300亿（仅恒瑞）/ 中 100-300亿 / 小 <100亿。大→中→小 破发率单调上升 = 大市值更受机构认可、抗破发。",
    "capital.ipo.section.scatter": "涨幅 × 市值散点",
    "capital.ipo.section.scatter_meta": "每点一只 IPO · y=0 为破发线 · log 市值轴",
    "capital.ipo.chart.scatter": "自发行价涨幅 vs 现市值",
    "capital.ipo.section.byliq": "破发率 × 流动性",
    "capital.ipo.section.byliq_meta": "次要 · 流动性档 = Wind 20 日均成交额",
    "capital.ipo.chart.byliq": "破发率（按流动性档）",
    "capital.ipo.note.byliq": "注意：流动性→破发非单调、样本小（部分档 n<5）、Wind/Futu 口径会翻转结论 → 仅描述性；市值分层才是干净信号。",
    "capital.ipo.unit.break": "破发率 %",
    "capital.ipo.section.table": "全名单（可筛选）",
    "capital.ipo.filter.mkt": "市值档",
    "capital.ipo.filter.water": "水位",
    "capital.ipo.filter.tag": "类型",
    "capital.ipo.filter.all": "全部",
    "capital.ipo.filter.above": "水上（未破发）",
    "capital.ipo.filter.below": "破发",
    "capital.ipo.filter.ai": "AI 制药",
    "capital.ipo.sort.label": "排序",
    "capital.ipo.sort.ret_desc": "涨幅 高→低",
    "capital.ipo.sort.ret_asc": "涨幅 低→高",
    "capital.ipo.sort.mktcap_desc": "市值 大→小",
    "capital.ipo.sort.date_desc": "上市日 新→旧",
    "capital.ipo.sort.pipeline_desc": "管线数 多→少",
    "capital.ipo.sort.bd_desc": "已披露 BD 高→低",
    "capital.ipo.col.name": "名称",
    "capital.ipo.col.date": "上市日",
    "capital.ipo.col.offer": "发行价",
    "capital.ipo.col.close": "现价",
    "capital.ipo.col.ret": "涨幅%",
    "capital.ipo.col.mktcap": "现市值(亿)",
    "capital.ipo.col.mkttier": "市值档",
    "capital.ipo.col.turnover": "日均成交(M$)",
    "capital.ipo.col.liqtier": "流动性档",
    "capital.ipo.col.broke": "破发",
    "capital.ipo.col.flag": "标记",
    "capital.ipo.col.founded": "成立",

    # ── IPO detail expander ──
    "capital.ipo.detail.title": "公司详情",
    "capital.ipo.detail.basic": "基本信息",
    "capital.ipo.detail.founded": "成立年份",
    "capital.ipo.detail.sector": "业务分类",
    "capital.ipo.detail.listing_mc": "上市时估值",
    "capital.ipo.detail.pipeline": "核心管线",
    "capital.ipo.detail.pipeline_loading": "正在查询管线信息...",
    "capital.ipo.detail.pipeline_empty": "暂无管线数据",
    "capital.ipo.detail.pipeline_error": "管线查询失败",
    "capital.ipo.detail.bd": "授权交易",
    "capital.ipo.detail.bd_loading": "正在查询BD交易...",
    "capital.ipo.detail.bd_empty": "暂无BD交易记录",
    "capital.ipo.detail.bd_error": "BD查询失败",
    "capital.ipo.detail.product": "产品",
    "capital.ipo.detail.indication": "适应症",
    "capital.ipo.detail.phase": "临床阶段",
    "capital.ipo.detail.partner": "合作方",
    "capital.ipo.detail.deal_value": "交易总额",
    "capital.ipo.detail.deal_date": "交易日期",
    # ── 总账×阶梯 重做（方案 2a）──
    "capital.ipo.detail.section_title": "公司详情 · 全名单档案",
    "capital.ipo.detail.section_meta": "PharmCube 预构建 · 管线 + 授权交易 · 点击行展开",
    "capital.ipo.detail.disclosed": "已披露",
    "capital.ipo.detail.no_archive": "无管线 / BD 档案 · 仅基本信息",
    "capital.ipo.detail.up_chip": "水上",
    "capital.ipo.detail.broke_chip": "破发",
    "capital.ipo.detail.suspended_chip": "停牌",
    "capital.ipo.detail.first_day": "上市首日",
    "capital.ipo.detail.listing_date": "上市日期",
    "capital.ipo.detail.ret_since": "发行至今",
    "capital.ipo.detail.offer_to_cur": "发行价 → 现价",
    "capital.ipo.detail.val_to_mc": "估值 → 市值",
    "capital.ipo.detail.avg_turnover": "日均成交",
    "capital.ipo.detail.disclosed_total": "对外授权 · 已披露总额",
    "capital.ipo.detail.ge_1b": "{n} 笔 · {m} 笔 ≥ $1B · 首付+里程碑",
    "capital.ipo.detail.undisclosed_n": "{n} 笔 · 金额未披露",
    "capital.ipo.detail.partners": "合作方图谱",
    "capital.ipo.detail.footer": "数据源 PharmCube · 预构建 · 运行时零查询 · 缺失字段自动隐藏",
    "capital.ipo.detail.ladder": "核心管线 · 阶段梯队",
    "capital.ipo.detail.pipeline_meta": "共 {n} 条 · 前沿 {k} 条入梯",
    "capital.ipo.detail.rest_pipeline": "其余 {n} 条以临床前 / I期为主",
    "capital.ipo.detail.bd_by_year": "授权交易 · 按年",
    "capital.ipo.detail.bd_meta": "展示 {k} / {n} 笔",
    "capital.ipo.detail.undisclosed": "未披露",

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
    # 出海模式区分：传统授权 / Co-Co / NewCo
    "capital.bd.col.structure": "结构",
    "capital.bd.struct.licenseout": "传统授权",
    "capital.bd.struct.coco": "Co-Co",
    "capital.bd.struct.newco": "NewCo",
    "capital.bd.section.bystructure": "按出海模式（授权 / Co-Co / NewCo）",
    "capital.bd.section.bystructure_meta": "按交易笔数 · 传统授权 vs Co-Co（共研+共商业化）vs NewCo（资产装新公司+换股权）",
    "capital.bd.chart.structure": "出海模式分布（按笔数）",
    "capital.bd.note.structure": (
        "传统授权 {lo} 笔 · Co-Co {coco} 笔 · NewCo {newco} 笔。"
        "Co-Co＝共同开发 + 联合商业化、按比例分摊成本/分享利润（如信达×武田 IBI363）；"
        "NewCo＝把资产装入新设公司、授权方换取股权分享上行（如和铂×Solstice、康诺亚×Ouro）。"
    ),
    "capital.bd.filter.structure": "按出海模式筛选",
    # ── HC ETF 专栏 (hc_etf.*) ──
    "hc_etf.title": "医疗健康 ETF 专栏",
    "hc_etf.caption": "{n} 支美股医疗 ETF · 概况 + 总回报区间 · 成分股就地展开 · 数据截至 {date}",
    "hc_etf.empty": "ETF 数据尚未生成 —— 请先运行 jobs/build_etf_panel.py。",
    "hc_etf.filter.subsector": "细分赛道",
    "hc_etf.filter.all": "全部",
    "hc_etf.subsector.Broad": "广基医疗",
    "hc_etf.subsector.Biotech": "生物科技",
    "hc_etf.subsector.Pharma": "制药",
    "hc_etf.subsector.Devices": "医疗器械",
    "hc_etf.subsector.Providers": "医疗服务 / 支付方",
    "hc_etf.subsector.Genomics": "基因 / 主题",
    "hc_etf.subsector.Other": "其他",
    "hc_etf.col.rank": "#",
    "hc_etf.col.symbol": "代码",
    "hc_etf.col.name": "成分股",
    "hc_etf.col.weight": "权重",
    "hc_etf.holdings_title": "主要成分股",
    "hc_etf.coverage": "前 {n} 大权重 = 基金的 {cov}%",
    "hc_etf.tail_more": "另有 {n} 支成分股(仅代码):{syms}",
    "hc_etf.tail_more_trunc": "另有 {n} 支成分股(仅代码)—— 前 {shown} 支:{syms} …",
    "hc_etf.kpi.price": "价格",
    "hc_etf.kpi.ytd": "年初至今",
    "hc_etf.kpi.y1": "一年",
    "hc_etf.kpi.y3": "三年",
    "hc_etf.kpi.vol": "波动率",
    "hc_etf.kpi.maxdd": "最大回撤",
    "hc_etf.kpi.expense": "费率",
    "hc_etf.kpi.aum": "规模",
    "hc_etf.provenance": "来源:{src} · 截至 {date}",
    # ── ETF 专栏 v2 (etf.*) — ETF 当作一等标的 ──
    "etf.title": "医疗健康 ETF 专栏",
    "etf.caption": "把美股医疗 ETF 当作一等标的 —— 表现 · 热力图 · 动能,跟个股一样 · 数据截至 {date}",
    "etf.empty": "ETF 数据未加载 —— 请先跑 jobs/load_universe.py + fetch_eod.py。",
    "etf.tab.perf": "表现",
    "etf.tab.holdings": "成分股",
    "etf.col.name": "名称",
    "etf.col.sub": "子赛道",
    "etf.col.last": "最新价",
    "etf.col.aum": "规模",
    "etf.col.detail": "详情",
    "etf.col.m1": "1月",
    "etf.col.ytd": "今年",
    "etf.col.d5": "5日",
    "etf.card.holdings": "前5大持仓",
    "etf.card.expand": "展开 · 全部 {n} 只成分股",
    "etf.click_hint": "点击行尾 ↗ 在 Ticker Drill 打开该 ETF(新标签)。",
    "etf.provenance": "来源:{src} · 截至 {date}",
    "etf.holdings.pick": "选择 ETF",
    "etf.heat.title": "ETF 热力图",
    "etf.heat.caption": "ETF 按子赛道分组,按涨跌着色(青绿涨/红跌) · 截至 {date}",
    "etf.heat.window": "窗口",
    "etf.rot.title": "ETF 动能轮动 (RRG)",
    "etf.rot.caption": "每支 ETF 相对广基医疗基准(XLV)轮动 —— 领先 / 转弱 / 落后 / 改善。",
    "etf.rot.thin": "历史足够的 ETF 太少,无法绘制轮动图。",
    "etf.rot.note": "基准 = {bench}(广基医疗)。周频 RS-Ratio / RS-Momentum。",
}
