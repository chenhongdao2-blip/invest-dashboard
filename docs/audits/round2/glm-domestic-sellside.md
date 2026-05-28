# GLM 5.1 — mode: review
> 20260528-145113 | input=2232 output=1258 cached=0

## System
```
你是 senior reviewer for 投研 + 国内 SDK / 中文 code / 中文 docs。任务：对下面的 output 做 balanced critical review。重点视角：1. 中文 phrasing / 卖方研报口径 2. 中文 SDK / 国内 ops 3. 国内 framework: 集采/医保谈判/CSRC/NMPA 4. 跨域盲点 5. 数字 fidelity。输出 [BLOCKER]/[MAJOR]/[MINOR]/[NIT] 严重性 + 具体 evidence，中文简洁。
```
## Prompt
```
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
   - 34 个 ticker 几乎都不是医药 (3968 招商银行 / 0300 美的 / 1088 中国神华 / 6690 海尔 / 3998 波司登...[truncated]
```

## Response
作为覆盖“投研+国内二级/A股港股”的 Senior Reviewer，以下是对本轮更新的 Cross-domain Audit 审查意见。总体而言，工具框架已成型，但在**卖方核心定价逻辑、港股/生物科技特色指标、以及绝对收益对账**上存在硬伤。

### [BLOCKER] 

**1. “高股息”策略核心指标完全缺失，逻辑自相矛盾**
*   **Evidence**: HK高股息策略的核心 Alpha 来自 Dividend Yield (股息率) 和 Payout Ratio (派息比率)。当前 D4 HD Tab 仅有 Price Return (价差收益)，完全没体现高股息策略的真正底色。
*   **Ops/Phrasing**: 卖方研报口径中，高股息模型必须拆分为 **股息收益 + 资本利得**。yfinance 完全支持 `dividendYield` 抓取。缺失该字段，该 Tab 在投研框架下毫无存在价值，必须补充 `div_yield` 指标。

**2. P/E百分位算法违背国内/港股卖方真实定价逻辑**
*   **Evidence**: D5 Scanner 仅用 Cross-sectional (截面) 的 Sector P/E ≤25% 定义为 "cheap"。
*   **Framework**: 国内卖方/基金经理极少看截面 P/E 分位，核心是 **Time-series P/E Band (过去5年/10年估值分位)**。此外，港股 18A/Biotech 大量亏损公司根本无 P/E，强算分位会引入巨大偏差；卖方标准做法是 Biotech 看 **Peak Sales / PEG / EV/Sales**，医院/传统药企看 **EV/EBITDA**。当前算法是纯 Quant 外行的“半成品”。

### [MAJOR]

**3. v4/v5 Portfolio Alpha 回溯数据出现严重漂移**
*   **Evidence**: Email (05-26) 显示 v4 Alpha +4.61pp，Dashboard (05-28) 显示 +3.12pp。2个交易日缩窄 1.49pp 不符合常态。
*   **Ops**: 卖方 Backtest 的铁律是 **Lock-in Pick Date** 的 composition。如果每日用 `yfinance` 重抓实时价格算历史回溯，会引入严重的 Look-ahead bias (幸存者偏差) 和成分股变动。必须固化 Base Date 的基准点位。

**4. 最小市值 默认 $5B 对国内/港股严重失真**
*   **Evidence**: 默认 $5B 过滤掉了 90% 以上的港股 18A 创新药公司，甚至连 D4 “建发国际(1908.HK)” 等 HD 标的都被扫掉。
*   **Framework**: A股/港股卖方覆盖中证1000/国证2000或恒生综合小型股时，门槛通常在 **$1B ~ $2B**。建议默认值下调至 $1.5B 或 $2B，否则 Scanner 对港股 Biotech 毫无实用性。

**5. 跨时区 Equal-weight 组合测算不够严谨**
*   **Evidence**: US/HK/CN 跨时区收盘价格直接做 Equal-weight 算日度 return。
*   **Sell-side Ops**: 真正的卖方多空/组合基准测算需对齐时间轴（例如 T-1 的 US 收盘对应 T 日 HK/A 收盘，或统一转换为周度/月度频率）。日度跨时区直接平均会产生 false alpha noise。

**6. 跨行业 Emoji 伪标签，缺乏 Alpha 增值**
*   **Evidence**: 🤖HC+AI 等标签仅覆盖极少数票（如讯飞医疗），信达、药明等主力票无 Cross-tag。
*   **Framework**: 国内医药卖方看 CMSI 不看这套 Emoji。真正要加的维度是：**集采暴露度**、**医保谈判进度**、**18A/18C 标签**、**港股通持仓比例变化 (南向资金净流入)**。这些才是 A/H 股定价核心。

**7. 跨周期 Return 框架过短**
*   **Evidence**: 只有 1D/5D/1M/YTD。
*   **Ops**: 卖方基本面框架必备 **3M / 6M / 1Y / 3Y**。特别是 HD 高股息策略，常看 1M vs 5D spread 找 mean-reversion 买点。周期太短无法看长线 Momentum。

### [MINOR]

**8. CMSI Coverage 缺卖方核心篮子指标**
*   **Evidence**: 缺 YTD vs HSI / HSCEI (恒指/国指) 的相对收益；缺 Brokers Consensus Rating (一致预期评级 Buy/Hold/Sell 分布)；缺 Target Price Upside %。
*   **Ops**: 国内买方每天早会看 CMSI 变动，这三个是外发 Morning Note 的核心标配，缺少会让买方客户觉得工具“不专业”。

**9. “How to read” Expander 定位尴尬**
*   **Evidence**: Expander 默认折叠。
*   **Ops**: 留着可以，但在 UI 上建议做 Tiered access：Senior PM 看不到（隐藏），Junior Analyst 默认展开。目前的文案语气偏“教学”，不够“Toolbox”。

### [NIT]

**10. 币种显示混乱隐患**
*   **Evidence**: HK 高股息 Portfolio 底层是 HKD，Benchmark (3110.HK) 也是 HKD。
*   **Ops**: Dashboard 统一转 USD 是好意，但在显示 HD 标的回报时，需在 Tooltip 或小字标注 "Local Currency (HKD) Return"，否则港股资深交易员会对数字缺乏体感。
