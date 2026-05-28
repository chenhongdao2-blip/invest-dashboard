第二轮 4-way audit — 重点审 D4 (Strategy Picks) + D5 (CMSI Coverage + Valuation Scanner)，找**中文卖方 / 国内投研** 盲点。

**Repo public**: https://github.com/chenhongdao2-blip/invest-dashboard
**Recent commits**:
- `251c6de` (Round-1 audit fixes — name_cn 优先 / Bloomberg ticker / dark theme / etc)
- `2863c72` (**D4 Strategy Picks**)
- `9e1179e` (**D5 CMSI Coverage + Valuation Scanner**)

**D4 Strategy Picks 实现**：
- 3 tabs: v4 biotech (27 picks 2026-04-22) / v5 biotech (40 picks 2026-05-15 from ic-foundry catalyst-monitor) / **HK 高股息 (34 picks 2026-03-20)**
- 每 tab: Portfolio / Benchmark / Alpha (pp) 三个 metric + Plotly 累计回报图 + Top/Bottom 5 ranking
- v4 verified: Portfolio +1.04%, XBI -2.08%, Alpha +3.12pp outperform
- **HK 高股息 picks**：包含 3968.HK 招商银行 / 0300.HK 美的集团 / 1088.HK 中国神华 / 6690.HK 海尔智家 / 3998.HK 波司登 等 34 个 ticker，几乎都是金融/能源/消费板块（**不是医药**）
- Benchmark: 3110.HK Premia 沪深港高股息低波动

**D5 CMSI Coverage 实现**：
- 4 region tabs: HK (15) / US (10) / CN A-share (3) / All (28)
- HK tab 默认 mcap desc 排序: 药明康德 $47.2B → 翰森 $24.9B → 信达 $17.1B → 药明生物 $17.1B → 中生制药 $11B → 石药 $10B → 荣昌 $6.1B → 三生 $5.6B → 华润 $3.7B → 康诺亚 $2.2B → 基石 $1.6B → 康臣 $1.5B → 讯飞医疗 $1.4B → 环球医疗 $1.3B → 和誉 $830M
- Cross-sector emoji tag (🧬biotech / 💊pharma / 🤖hc+ai / ⚕️medtech / 🏥hospital / 🩺managed / 🧪cxo)

**D5 Valuation Scanner 实现**：
- Sidebar 过滤: sector multi-select / min mcap (default $5B) / Sector P/E percentile threshold (default ≤25%) / forward vs trailing P/E / YTD range / Min 5D return
- 算法: sector-internal P/E percentile (multi-sector ticker 用 cheapest sector ranking; 负 P/E 不参与分位 ranking)
- Default 输出: 87 universe → 16 candidates
- Top: PFE (9.2x, 6%, YTD +4%), ICLR (10.5x, 7%, YTD -37% recovery), BDX, BMRN, IQV (hc_ai+cxo cross), UHS (hospital+managed), GSK, GEHC, RPRX (+38% YTD biotech 强势!), CRM (hc_ai), MRK (mega cap quality), CI, THC, LH, MDT, NVO

**审查角度（重点找 sell-side / 国内 盲点）**：

1. **HK 高股息 strategy 在 Healthcare dashboard 的存在性合理吗？**
   - 34 个 ticker 几乎都不是医药 (3968 招商银行 / 0300 美的 / 1088 中国神华 / 6690 海尔 / 3998 波司登 / 1288 农业银行 / 0939 建设银行 / 1908 建发国际 etc)
   - Dashboard 标题是 "Multi-Domain Investment Dashboard" + "Sell-side healthcare coverage"
   - HK 高股息 与 healthcare 关联薄弱，是否该单独 domain？
   - 但: George's strategy-weekly 一直把 HK 高股息 跟 v4/v5 biotech 一起 mail
   
2. **D4 Strategy returns 算法**：
   - Equal-weight portfolio = 当天 available tickers 的平均 normed price
   - 港股 + JP 股 + US 股各自时区不同，equal-weight 跨时区算 portfolio return — 卖方 backtest 标准做法吗？
   - HK 高股息 portfolio 是 HKD-based，benchmark 也是 HKD。但 dashboard 现在统一显示 USD-converted？混乱吗？

3. **CMSI Coverage cross-sector emoji 设计**：
   - 28 ticker 中只有 2506.HK (讯飞医疗) 有 🤖 tag
   - 信达/翰森/中生制药/石药/药明 这些**都没有 cross-tag** 因为它们没在 sector universe 里
   - 这导致 emoji column 90% 是空的 — 对 CMSI cover 数据没增值
   - 国内卖方常用的 cross 维度：港股通持仓比例 / 北向资金净流入 / 集采暴露 / 18A 18C 标签 — 这些是不是更有 alpha?

4. **D5 Scanner 算法的 sell-side validity**：
   - **Sector P/E percentile threshold ≤25** 作为 "cheap" — 中国/港股 sell-side 卖方更常用：
     (a) **过去 5 年 P/E band 分位** (time-series): 比 cross-sectional 更有意义 — 一家公司 P/E 12x 在自己历史下 30 percentile vs 板块 30 percentile 含义完全不同
     (b) **PEG** (P/E / EPS growth): 卖方 valuation framework 必备，dashboard 已经有 PEG 字段但 Scanner 没用
     (c) **EV/EBITDA** vs **EV/Sales** — 不同板块习惯不同：Biotech 用 EV/Sales (亏损公司); Hospital 用 EV/EBITDA
   - 现在 Scanner 只用了 sector P/E percentile + 简单 multi-window return filter — 这是"半成品"框架

5. **Min mcap default $5B 是 sell-side 默认值吗**？
   - 美股 sell-side: > $5B ≈ small-cap+ (合理)
   - 港股 sell-side: > HK$30B ≈ HK$32亿 ≈ USD$4B (Borderline)
   - 港股 biotech/innovative drug 普遍小盘，HK 18A 公司平均 $1-3B mcap。默认 $5B 把 90% HK biotech 都过滤掉
   - HD picks 34 个里很多都 < $5B (1088 中国神华 大；1908 建发国际 ≈ $1.5B 港股 — 被过滤)
   - 国内 sell-side 默认设 $1B 或 $2B 更接地气

6. **"高股息" framework 完全缺失**：
   - HK 高股息 strategy 的核心指标是 **dividend yield + payout ratio + dividend coverage**
   - Dashboard 完全没有 dividend yield 字段（yfinance.info 有 `dividendYield` / `trailingAnnualDividendYield`）
   - Strategy Picks 的 HD tab 只看 price return，**完全没体现 strategy 的核心论点**（高股息）
   - 应该在 multiples_daily 加 `div_yield` 字段 + HD tab 加 dividend column

7. **D4 v4/v5 biotech 跟 strategy-weekly mail 数字对账**：
   - User email (2026-05-26) 显示 v4 since Alpha +4.61pp
   - Dashboard (2026-05-28) 显示 +3.12pp
   - 2 个交易日缩窄 1.49pp 合理吗？
   - 卖方 backtest 真实做法应该 lock-in pick_date 的 portfolio composition + 不重 fetch yfinance（避免 survivorship bias / look-ahead bias）

8. **Multi-window return 缺**：
   - Dashboard 各页都显示 1D / 5D / 1M / YTD
   - 卖方还看 **3M / 6M / 1Y / 3Y / 5Y** — 长期 momentum vs 短期 mean reversion 区分必要
   - HD 高股息 跨周期 reversion 用 1M-5D spread (-2 sigma) 是常见技巧 — dashboard 缺

9. **"How to read this scan" expander on Scanner**：
   - 中文卖方 senior 不需要这种 hand-holding 注释，反而显得 dashboard 是"教学用"不是"工具用"
   - 但 Junior analyst onboarding 有价值
   - 建议 expander 默认 collapsed (现在就是) — OK

10. **D5 Coverage 缺关键卖方字段**：
    - **YTD performance vs HSI / HSCEI** (港股 cover 必看，因为 HK 个股表现高度依赖大盘)
    - **Brokers consensus rating** (buy/hold/sell 分布) — 用户原 Excel 有，dashboard 缺
    - **Target price upside %** — sell-side daily 看的核心字段

请用 [BLOCKER] / [MAJOR] / [MINOR] / [NIT] 标注，中文输出，简洁不和稀泥。
