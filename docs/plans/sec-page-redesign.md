# 个股 SEC 财务数据页 — 重设计规格 (SEC Facts Page Redesign Spec)

> 适用页面：`app/pages/8_SEC_Facts.py`（医疗域 HC）与 `app/pages/a5_ai_sec.py`（AI 域），结构相同，本规格两页通用（domain 作参数）。
> 数据层：`app/lib/sec_facts.py`（命名空间 `sf`），DB `data/snapshots.db` 表 `sec_company`（每公司一行，gzip JSON payload）+ `sec_kpi_map`。
> 运行时只读已 commit 的 DB，**禁止实时网络依赖**。
> 复用组件：`theme.py` / `ui.py` / `charts.py` / `i18n.py`。
> 配色锁：UP=teal 涨 / DOWN=red 跌（国际惯例）；CMSI_RED 仅做品牌/小标题红肋。
>
> 状态：设计 pass，**未改生产代码**。Concept tag 凡无法对 live DB 校验者标 `待校验`。

---

## 0. 设计原则（卖方审美 4 条）

1. **以"会计师/建模师"的眼睛排版**：三大报表用"年份做列、科目做行"的矩阵，跟 Excel 财务模型同构，分析师扫一眼就能读懂结构、抓趋势。
2. **信息密度收敛**：默认只展示策展后的规范科目（每表 8–15 行），两万行原始 XBRL 收进折叠器备查。"全"不等于"有用"。
3. **双语术语规范**：中文必须是规范会计/卖方用语（见 §6 词典）；长尾冷门 XBRL 标签保留英文，不生造。
4. **留白与层级**：每段一个 `theme.section_header`（红肋小标题）+ 一句"为什么看它"导语；段间留白拉开；表格右对齐数字、sticky 行头。

---

## 1. 页面信息架构（段落顺序与取舍）

选股控件（ticker selectbox）置顶，全页围绕单只美股。建议顺序：

| 段 | 标题（中/英） | 一句话："分析师为什么看它" |
|----|--------------|--------------------------|
| 选股 | 选择标的 / Select Ticker | 锁定个股，下面所有数据随之刷新；显示 taxonomy（us-gaap / ifrs-full）+ 最新 filing 时间戳。 |
| ① | 核心财报指标 / Key Financials (KPIs) | domain-aware KPI 卡片，3 秒拿到这家公司的规模/盈利/现金画像。 |
| ② | **三大报表摘要** / Financial Statements | **本次重点**。利润表/资产负债表/现金流量表三张矩阵表（年列×科目行+YoY/CAGR），看趋势、看结构、看质量——取代原"两万行平铺表"。 |
| ③ | 概念时间序列 / Concept Time Series | 任选一个 XBRL 概念深挖单指标的历史走势（年度/季度），看拐点与同比。 |
| ④ | 可比公司表 / Comparison Table | 多股×KPI 横向对标，导出 CSV，做 comps。 |
| ⑤（折叠） | 高级：全量 XBRL 浏览器 / Advanced: Raw XBRL Browser | 25,699 行原始事实，搜索/筛选/CSV，供溯源与冷门概念兜底——默认收起。 |

**取舍说明**：
- 原 ③"全量表"从主视图**降级**为 ⑤ 折叠器（George 已拍板）。
- KPI（①）保留，但其"为何取此值"溯源表继续折叠，不占主视觉。
- ②（三大表）从无到有，成为页面价值核心；②应排在概念时序（③）之前——分析师先看完整报表结构，再下钻单概念。

---

## 2. 三大报表摘要 — 详细规格（核心）

### 2.1 通用机制

**取数函数**：对每个行项的 concept tag 调
`sf.concept_timeseries(ticker, tax, concept, unit="USD", freq="annual")`
返回列 `end_date / value / fy / fp / form / unit / yoy`。
- **tax**：先试 `us-gaap`；该 ticker 若 us-gaap 无任何命中则切 `ifrs-full`（用 §2.5 的 ifrs 等价 tag）。一个页面只用一种 taxonomy（按 §1 选股段已探明的 taxonomy）。
- **fallback 链**：每个行项给"主 tag + 备选 tags（按优先级）"。取数逻辑：依次尝试 tag，第一个返回非空时序的即采用，并记录"实际命中 tag"（供 ⑤ 溯源/调试）。
- **unit**：金额行项 `unit="USD"`；每股行项 `unit="USD/shares"`；股数行项 `unit="shares"`。
- **freq**：摘要默认 `annual`（年报 10-K / 20-F）。提供"年度/季度"切换（同 §5 radio 修复）。季度时 IS/CF 用单季 duration，BS 用季末 instant。

**矩阵构建**（建议新增 helper，§7 P0 落地）：
```
build_statement_matrix(ticker, tax, rows, freq, periods=6) -> DataFrame
# rows: 见 §2.3–2.5 的行项清单 (cn_label, en_label, primary, fallbacks, is_instant)
# 返回：index = 科目中文/英文标签（随 lang），columns = 财年 (FY2021..FY2026)
#       + 末列 "YoY" 或 "CAGR"；值已按 _fmt_val(v, unit) 格式化或保留原值交给 ui 格式化
```

**布局**：
- 三张表分别用 `theme.section_header` 子标题（利润表/资产负债表/现金流量表）+ `ui.render_html_table`。
- **列**：最近 4–6 个财年（annual 优先），**新→旧从左到右**（最新财年在最左，符合卖方研报习惯）或旧→新（与 Excel 一致）——**采用旧→新（左旧右新）**，与衍生指标 CAGR/趋势阅读方向一致。
- **行**：§2.3–2.5 规范科目，按报表自然顺序（不按字母排序）。
- **末列**：`YoY%`（最近一年 vs 前一年，`pct_cols` 染色 teal/red）或对全周期给 `CAGR%`。建议**两列都给**：倒数第二列 `YoY%`（最近年），最后一列 `CAGR%`（首末年复合增速）。
- **缺失值**：显示 `—`（em dash），不显示 0 / NaN / None。某行项全周期皆空则**整行隐藏**（避免空行噪音），并在表脚注 caption 标"部分科目该公司未披露"。
- **金额规范**：用 `money_b_cols`（→ $56.4B / $1.2M 自适应）；每股用 `mult_cols` 或预格式化 `$X.XX` 走 `right_text_cols`；股数走 `right_text_cols` 预格式化（千分位）。
- index_label：第一列表头写"科目 / Line Item"。

### 2.2 衍生指标（盈利能力/成长性/现金质量）

在三张表下方加一个小的"衍生指标"区块（`theme.section_header` + 一张 `ui.render_html_table`，年列×指标行，`pct_cols` 染色）：

| 中文 | English | 公式 | 取数来源 |
|------|---------|------|---------|
| 毛利率 | Gross Margin | GrossProfit / Revenues | IS 两行相除（缺 GrossProfit 时 = (Revenues − CostOfRevenue)/Revenues） |
| 营业利润率 | Operating Margin | OperatingIncomeLoss / Revenues | IS |
| 净利率 | Net Margin | NetIncomeLoss / Revenues | IS |
| 营收 CAGR | Revenue CAGR | (Rev_末 / Rev_首)^(1/(n−1)) − 1 | IS Revenues 时序 |
| 自由现金流 FCF | Free Cash Flow | 经营活动现金流净额 − 资本开支 | CF：NetCashProvidedByUsedInOperatingActivities − PaymentsToAcquirePropertyPlantAndEquipment |
| FCF 利润率 | FCF Margin | FCF / Revenues | CF + IS |
| ROE | Return on Equity | NetIncomeLoss / StockholdersEquity | IS + BS（期末权益；可选两期均值） |
| 资产负债率 | Debt-to-Assets | Liabilities / Assets | BS |

> 衍生指标全部由前面已取的行项时序**就地计算**，不额外打 DB。某分子/分母缺失则该单元格 `—`。

### 2.3 利润表 (Income Statement)　行项清单（duration / 区间值）

| # | 中文标签 | English | 主用 us-gaap concept | 备选 fallback（优先级降序） | ifrs-full 等价 | instant? |
|---|---------|---------|---------------------|---------------------------|----------------|----------|
| 1 | 营业收入 | Revenue | `RevenueFromContractWithCustomerExcludingAssessedTax` | `Revenues`, `RevenueFromContractWithCustomerIncludingAssessedTax`, `SalesRevenueNet` | `Revenue` | 否 |
| 2 | 营业成本 | Cost of Revenue | `CostOfGoodsAndServicesSold` | `CostOfRevenue`, `CostOfGoodsSold`, `CostOfServices` | `CostOfSales` | 否 |
| 3 | 毛利润 | Gross Profit | `GrossProfit` | （缺则 = 行1 − 行2 计算） | `GrossProfit` | 否 |
| 4 | 研发费用 | R&D Expense | `ResearchAndDevelopmentExpense` | — | `ResearchAndDevelopmentExpense`（待校验） | 否 |
| 5 | 销售及管理费用 | SG&A | `SellingGeneralAndAdministrativeExpense` | `GeneralAndAdministrativeExpense`+`SellingAndMarketingExpense`（分项相加） | — | 否 |
| 6 | 营业费用合计 | Total Operating Expenses | `OperatingExpenses` | `CostsAndExpenses` | — | 否 |
| 7 | 营业利润 | Operating Income | `OperatingIncomeLoss` | — | `ProfitLossFromOperatingActivities` | 否 |
| 8 | 利息费用 | Interest Expense | `InterestExpense` | `InterestExpenseNonoperating`, `InterestIncomeExpenseNet` | `FinanceCosts` | 否 |
| 9 | 税前利润 | Pretax Income | `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` | `IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments` | `ProfitLossBeforeTax` | 否 |
| 10 | 所得税费用 | Income Tax Expense | `IncomeTaxExpenseBenefit` | — | `IncomeTaxExpenseContinuingOperations`（待校验） | 否 |
| 11 | 净利润 | Net Income | `NetIncomeLoss` | `ProfitLoss`, `NetIncomeLossAvailableToCommonStockholdersBasic` | `ProfitLoss` | 否 |
| 12 | 基本每股收益 | Basic EPS | `EarningsPerShareBasic` | — | `BasicEarningsLossPerShare` | 否 |
| 13 | 稀释每股收益 | Diluted EPS | `EarningsPerShareDiluted` | — | `DilutedEarningsLossPerShare` | 否 |
| 14 | 稀释加权平均股本 | Diluted Weighted Avg Shares | `WeightedAverageNumberOfDilutedSharesOutstanding` | `WeightedAverageNumberOfSharesOutstandingBasic` | — | 否 |

### 2.4 资产负债表 (Balance Sheet)　行项清单（instant / 时点值）

| # | 中文标签 | English | 主用 us-gaap concept | 备选 fallback | ifrs-full 等价 | instant? |
|---|---------|---------|---------------------|--------------|----------------|----------|
| 1 | 现金及现金等价物 | Cash & Equivalents | `CashAndCashEquivalentsAtCarryingValue` | `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents` | `CashAndCashEquivalents` | 是 |
| 2 | 短期投资 | Short-term Investments | `ShortTermInvestments` | `MarketableSecuritiesCurrent` | — | 是 |
| 3 | 应收账款净额 | Accounts Receivable, Net | `AccountsReceivableNetCurrent` | `ReceivablesNetCurrent` | `TradeAndOtherCurrentReceivables` | 是 |
| 4 | 存货 | Inventory | `InventoryNet` | `InventoryFinishedGoodsNetOfReserves` | `Inventories` | 是 |
| 5 | 流动资产合计 | Total Current Assets | `AssetsCurrent` | — | `CurrentAssets` | 是 |
| 6 | 固定资产净额 | Property, Plant & Equipment, Net | `PropertyPlantAndEquipmentNet` | — | `PropertyPlantAndEquipment` | 是 |
| 7 | 商誉 | Goodwill | `Goodwill` | — | `Goodwill` | 是 |
| 8 | 无形资产 | Intangible Assets | `IntangibleAssetsNetExcludingGoodwill` | `FiniteLivedIntangibleAssetsNet` | `IntangibleAssetsOtherThanGoodwill` | 是 |
| 9 | 总资产 | Total Assets | `Assets` | — | `Assets` | 是 |
| 10 | 应付账款 | Accounts Payable | `AccountsPayableCurrent` | `AccountsPayableAndAccruedLiabilitiesCurrent` | `TradeAndOtherCurrentPayables` | 是 |
| 11 | 流动负债合计 | Total Current Liabilities | `LiabilitiesCurrent` | — | `CurrentLiabilities` | 是 |
| 12 | 长期借款 | Long-term Debt | `LongTermDebtNoncurrent` | `LongTermDebt`, `LongTermDebtAndCapitalLeaseObligations` | `NoncurrentBorrowings`（待校验） | 是 |
| 13 | 总负债 | Total Liabilities | `Liabilities` | `LiabilitiesAndStockholdersEquity`−`StockholdersEquity`（计算兜底） | `Liabilities` | 是 |
| 14 | 股东权益合计 | Total Stockholders' Equity | `StockholdersEquity` | `StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest` | `Equity` | 是 |
| 15 | 流通股本 | Shares Outstanding | `CommonStockSharesOutstanding` | `CommonStockSharesIssued`, `EntityCommonStockSharesOutstanding`(dei) | — | 是 |

### 2.5 现金流量表 (Cash Flow Statement)　行项清单（duration / 区间值）

| # | 中文标签 | English | 主用 us-gaap concept | 备选 fallback | ifrs-full 等价 | instant? |
|---|---------|---------|---------------------|--------------|----------------|----------|
| 1 | 经营活动现金流净额 | Net Cash from Operating Activities | `NetCashProvidedByUsedInOperatingActivities` | `NetCashProvidedByUsedInOperatingActivitiesContinuingOperations` | `CashFlowsFromUsedInOperatingActivities` | 否 |
| 2 | 折旧及摊销 | Depreciation & Amortization | `DepreciationDepletionAndAmortization` | `DepreciationAmortizationAndAccretionNet`, `DepreciationAndAmortization` | `DepreciationAndAmortisationExpense` | 否 |
| 3 | 股权激励费用 | Stock-based Compensation | `ShareBasedCompensation` | `AllocatedShareBasedCompensationExpense` | — | 否 |
| 4 | 营运资本变动 | Change in Working Capital | `IncreaseDecreaseInOperatingCapital` | （分项：应收/存货/应付变动之和） | — | 否 |
| 5 | 投资活动现金流净额 | Net Cash from Investing Activities | `NetCashProvidedByUsedInInvestingActivities` | `NetCashProvidedByUsedInInvestingActivitiesContinuingOperations` | `CashFlowsFromUsedInInvestingActivities` | 否 |
| 6 | 资本开支 | Capital Expenditures | `PaymentsToAcquirePropertyPlantAndEquipment` | `PaymentsToAcquireProductiveAssets`, `PaymentsForCapitalImprovements` | `PurchaseOfPropertyPlantAndEquipment`（待校验） | 否 |
| 7 | 融资活动现金流净额 | Net Cash from Financing Activities | `NetCashProvidedByUsedInFinancingActivities` | `NetCashProvidedByUsedInFinancingActivitiesContinuingOperations` | `CashFlowsFromUsedInFinancingActivities` | 否 |
| 8 | 股票回购 | Share Repurchases | `PaymentsForRepurchaseOfCommonStock` | — | — | 否 |
| 9 | 现金分红 | Dividends Paid | `PaymentsOfDividendsCommonStock` | `PaymentsOfDividends` | `DividendsPaidClassifiedAsFinancingActivities`（待校验） | 否 |
| 10 | 债务发行 | Debt Issued | `ProceedsFromIssuanceOfLongTermDebt` | `ProceedsFromIssuanceOfDebt` | — | 否 |
| 11 | 债务偿还 | Debt Repaid | `RepaymentsOfLongTermDebt` | `RepaymentsOfDebt` | — | 否 |
| 12 | 现金净增加额 | Net Change in Cash | `CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect` | `CashAndCashEquivalentsPeriodIncreaseDecrease` | — | 否 |
| 13 | 自由现金流（衍生） | Free Cash Flow (derived) | 行1 − 行6 | — | — | 否 |

> ⚠️ 所有 ifrs-full 等价 tag 标"待校验"者，需在 P1 阶段用持有 IFRS 报表的 ADR（如医疗域 NVS/AZN/NVO；AI 域如 TSM/ASML/SK Hynix 若有 SEC facts）实测命中再定稿。

---

## 3. ⑤ 原始全量 XBRL 浏览器（折叠备查）

- 包进 `st.expander("高级：全量 XBRL 数据 / Advanced: Raw XBRL Browser", expanded=False)`。
- 数据源：`sf.all_facts(ticker)`（约 25,699 行，列 concept/taxonomy/unit/value/fy/fp/form/end_date/start_date/filed/accession/instant/label）。
- **保留能力**：
  1. **搜索**：`st.text_input("搜索概念 / Search concept")` → 对 `concept` + `label` 做大小写不敏感 `contains` 过滤。
  2. **筛选**：`taxonomy`（us-gaap/ifrs-full/dei）、`form`（10-K/10-Q/...）、`fp`（FY/Q1..Q4）三个 `st.multiselect`。
  3. **CSV 导出**：`st.download_button` 导当前过滤结果（保留原始未格式化数值）。
- 表格用 `st.dataframe`（原始全量保留交互排序即可，无需暖色 HTML——这是工程兜底视图，不是展示视图）；默认只显示前 N=500 行 + 提示"用搜索/筛选缩小范围或导出 CSV"。
- caption：标"原始 SEC XBRL 事实，未策展；用于溯源与冷门概念查询"。

---

## 4. ③ 概念时间序列 — 最终形态

- 选概念：`st.selectbox`，选项 = §6 词典覆盖的常用概念优先置顶（显示"中文名 (en_tag)"），其余长尾概念排后（显示英文 tag）。中文模式 label 走 `sf.concept_cn(concept)`，无则回退英文 tag。
- 周期切换：年度/季度 segmented（见 §5）。
- 取数：`sf.concept_timeseries(ticker, tax, concept, unit, freq)`。
- **图表**（`charts.price_line_chart`）：
  - **标题修复 (反馈 b)**：中文模式 = `concept_cn(concept)`（无则英文 tag）；英文模式 = 该概念的可读 label（`all_facts` 的 `label` 列，无则 tag）。**绝不**直接把 `ContractWithCustomerLiabilityRevenueRecognized` 这种裸 tag 当标题。
  - **去冗余图例**：单系列时 `showlegend=False`（`charts.price_line_chart` 增 `show_legend` 参数，默认按系列数判断：≤1 系列不显示图例）。
  - **轴**：Y 轴保持 USD(mn) 缩放（金额 / 1e6，ylabel="USD (mn)"；每股则 ylabel="USD/share"，股数 ylabel="Shares (mn)"）。X 轴 = end_date。
  - 字号遵循 INVARIANTS：X tick ≥11pt、Y label ≥12pt、title ≥14pt。
- **表**（`ui.render_concept_table`）：保持暖色；中文模式表头/概念名用 `concept_cn`；YoY/QoQ 列 `pct_cols` 染 teal/red。

---

## 5. 周期 radio 可见性修复（反馈 a）

**问题**：当前 `st.radio` 的"年度/季度"文字标签对比度过低（截图只见深色●/绿色○圆点，文字几乎不可见），是主题 CSS 把 radio label 文字颜色压到接近背景色。

**方案（按优先级，实现时二选一）**：

- **首选 — 换 `st.segmented_control`**（Streamlit ≥1.40 原生 segmented 按钮）：
  ```
  freq_label = st.segmented_control(
      i18n.t("period"), options=[i18n.t("annual"), i18n.t("quarterly")],
      default=i18n.t("annual"), selection_mode="single")
  ```
  segmented 是高对比药丸按钮，选中态用 CMSI_RED 描边/填充，未选中态 INK 文字 on PAPER，文字必然可见。在 `theme.py` 增 segmented 的 CSS：选中 `background:CMSI_RED;color:PAPER`，未选中 `color:INK;border:1px solid INK@30%`。
- **备选 — 修 radio CSS**：在 `theme.py` 注入
  ```css
  div[role="radiogroup"] label p { color: var(--ink) !important; font-size: 0.95rem !important; font-weight: 500; }
  div[role="radiogroup"] label { gap: 0.4rem; }
  ```
  强制 radio 文字 = INK 墨色、≥0.95rem，并加圆点与文字间距。

> 推荐 segmented_control：既修可见性又提升卖方审美（药丸切换比 radio 更现代）。注意全页其它周期切换处统一替换，保持一致。

---

## 6. 策展概念→中文词典（数据交付物）

> 直接合并进 `sf._CONCEPT_CN`（或新建 `app/lib/sec_concept_cn.py` 单独维护后 import）。
> 覆盖：三大表全部行项 + 全 KPI + 常见科目。标准会计/卖方中文术语。长尾冷门 tag 不在此表者运行时回退英文。
> 共 **~155 条**。

```python
_CONCEPT_CN = {
    # ===== 利润表 Income Statement =====
    "Revenues": "营业收入",
    "RevenueFromContractWithCustomerExcludingAssessedTax": "营业收入",
    "RevenueFromContractWithCustomerIncludingAssessedTax": "营业收入(含税)",
    "SalesRevenueNet": "营业收入净额",
    "SalesRevenueGoodsNet": "商品销售收入",
    "SalesRevenueServicesNet": "服务收入",
    "CostOfRevenue": "营业成本",
    "CostOfGoodsAndServicesSold": "营业成本",
    "CostOfGoodsSold": "销货成本",
    "CostOfServices": "服务成本",
    "GrossProfit": "毛利润",
    "OperatingExpenses": "营业费用合计",
    "CostsAndExpenses": "成本及费用合计",
    "ResearchAndDevelopmentExpense": "研发费用",
    "SellingGeneralAndAdministrativeExpense": "销售及管理费用",
    "GeneralAndAdministrativeExpense": "管理费用",
    "SellingAndMarketingExpense": "销售费用",
    "SellingExpense": "销售费用",
    "MarketingAndAdvertisingExpense": "营销及广告费用",
    "AmortizationOfIntangibleAssets": "无形资产摊销",
    "RestructuringCharges": "重组费用",
    "OperatingIncomeLoss": "营业利润",
    "NonoperatingIncomeExpense": "营业外净收支",
    "InterestExpense": "利息费用",
    "InterestExpenseNonoperating": "利息费用",
    "InterestIncomeExpenseNet": "利息净收支",
    "InvestmentIncomeInterest": "利息收入",
    "OtherNonoperatingIncomeExpense": "其他营业外收支",
    "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest": "税前利润",
    "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments": "税前利润",
    "IncomeTaxExpenseBenefit": "所得税费用",
    "IncomeLossFromContinuingOperations": "持续经营利润",
    "IncomeLossFromDiscontinuedOperationsNetOfTax": "终止经营损益(税后)",
    "NetIncomeLoss": "净利润",
    "ProfitLoss": "净利润",
    "NetIncomeLossAvailableToCommonStockholdersBasic": "归属普通股东净利润",
    "NetIncomeLossAttributableToNoncontrollingInterest": "少数股东损益",
    "EarningsPerShareBasic": "基本每股收益",
    "EarningsPerShareDiluted": "稀释每股收益",
    "WeightedAverageNumberOfSharesOutstandingBasic": "基本加权平均股本",
    "WeightedAverageNumberOfDilutedSharesOutstanding": "稀释加权平均股本",
    "ComprehensiveIncomeNetOfTax": "综合收益(税后)",
    "ShareBasedCompensation": "股权激励费用",
    "AllocatedShareBasedCompensationExpense": "股权激励费用",

    # ===== 资产负债表 Balance Sheet =====
    "Assets": "总资产",
    "AssetsCurrent": "流动资产合计",
    "AssetsNoncurrent": "非流动资产合计",
    "CashAndCashEquivalentsAtCarryingValue": "现金及现金等价物",
    "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents": "现金及受限现金",
    "ShortTermInvestments": "短期投资",
    "MarketableSecuritiesCurrent": "可供出售金融资产(流动)",
    "LongTermInvestments": "长期投资",
    "AccountsReceivableNetCurrent": "应收账款净额",
    "ReceivablesNetCurrent": "应收款项净额",
    "InventoryNet": "存货净额",
    "PrepaidExpenseAndOtherAssetsCurrent": "预付费用及其他流动资产",
    "OtherAssetsCurrent": "其他流动资产",
    "PropertyPlantAndEquipmentNet": "固定资产净额",
    "PropertyPlantAndEquipmentGross": "固定资产原值",
    "OperatingLeaseRightOfUseAsset": "经营租赁使用权资产",
    "Goodwill": "商誉",
    "IntangibleAssetsNetExcludingGoodwill": "无形资产净额",
    "FiniteLivedIntangibleAssetsNet": "有限寿命无形资产净额",
    "DeferredIncomeTaxAssetsNet": "递延所得税资产",
    "OtherAssetsNoncurrent": "其他非流动资产",
    "Liabilities": "总负债",
    "LiabilitiesCurrent": "流动负债合计",
    "LiabilitiesNoncurrent": "非流动负债合计",
    "LiabilitiesAndStockholdersEquity": "负债及股东权益合计",
    "AccountsPayableCurrent": "应付账款",
    "AccountsPayableAndAccruedLiabilitiesCurrent": "应付账款及应计负债",
    "AccruedLiabilitiesCurrent": "应计负债",
    "EmployeeRelatedLiabilitiesCurrent": "应付职工薪酬",
    "ContractWithCustomerLiabilityCurrent": "合同负债(流动)",
    "DeferredRevenueCurrent": "递延收入(流动)",
    "ShortTermBorrowings": "短期借款",
    "LongTermDebtCurrent": "一年内到期长期借款",
    "LongTermDebtNoncurrent": "长期借款",
    "LongTermDebt": "长期借款",
    "OperatingLeaseLiabilityNoncurrent": "经营租赁负债(非流动)",
    "DeferredIncomeTaxLiabilitiesNet": "递延所得税负债",
    "OtherLiabilitiesNoncurrent": "其他非流动负债",
    "CommitmentsAndContingencies": "承诺及或有事项",
    "StockholdersEquity": "股东权益合计",
    "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest": "股东权益合计(含少数股东)",
    "CommonStockValue": "普通股股本",
    "AdditionalPaidInCapital": "资本公积",
    "RetainedEarningsAccumulatedDeficit": "未分配利润(累计亏损)",
    "AccumulatedOtherComprehensiveIncomeLossNetOfTax": "累计其他综合收益",
    "TreasuryStockValue": "库存股",
    "MinorityInterest": "少数股东权益",
    "CommonStockSharesOutstanding": "流通股本",
    "CommonStockSharesIssued": "已发行股本",
    "CommonStockSharesAuthorized": "授权股本",

    # ===== 现金流量表 Cash Flow Statement =====
    "NetCashProvidedByUsedInOperatingActivities": "经营活动现金流净额",
    "NetCashProvidedByUsedInOperatingActivitiesContinuingOperations": "经营活动现金流净额",
    "NetCashProvidedByUsedInInvestingActivities": "投资活动现金流净额",
    "NetCashProvidedByUsedInInvestingActivitiesContinuingOperations": "投资活动现金流净额",
    "NetCashProvidedByUsedInFinancingActivities": "融资活动现金流净额",
    "NetCashProvidedByUsedInFinancingActivitiesContinuingOperations": "融资活动现金流净额",
    "DepreciationDepletionAndAmortization": "折旧及摊销",
    "DepreciationAmortizationAndAccretionNet": "折旧摊销及增值净额",
    "DepreciationAndAmortization": "折旧及摊销",
    "Depreciation": "折旧",
    "IncreaseDecreaseInAccountsReceivable": "应收账款变动",
    "IncreaseDecreaseInInventories": "存货变动",
    "IncreaseDecreaseInAccountsPayable": "应付账款变动",
    "IncreaseDecreaseInOperatingCapital": "营运资本变动",
    "DeferredIncomeTaxExpenseBenefit": "递延所得税变动",
    "PaymentsToAcquirePropertyPlantAndEquipment": "购建固定资产支出",
    "PaymentsToAcquireProductiveAssets": "购建生产性资产支出",
    "PaymentsToAcquireBusinessesNetOfCashAcquired": "收购支出(净)",
    "PaymentsToAcquireInvestments": "购买投资支出",
    "ProceedsFromSaleMaturityAndCollectionsOfInvestments": "投资收回",
    "PaymentsForRepurchaseOfCommonStock": "股票回购",
    "PaymentsOfDividendsCommonStock": "现金分红",
    "PaymentsOfDividends": "现金分红",
    "ProceedsFromIssuanceOfLongTermDebt": "长期债务发行",
    "ProceedsFromIssuanceOfDebt": "债务发行",
    "RepaymentsOfLongTermDebt": "长期债务偿还",
    "RepaymentsOfDebt": "债务偿还",
    "ProceedsFromIssuanceOfCommonStock": "股票发行募资",
    "EffectOfExchangeRateOnCashAndCashEquivalents": "汇率变动对现金影响",
    "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalentsPeriodIncreaseDecreaseIncludingExchangeRateEffect": "现金净增加额",
    "CashAndCashEquivalentsPeriodIncreaseDecrease": "现金净增加额",

    # ===== KPI / 常用衍生与比率 =====
    "GrossMargin": "毛利率",
    "OperatingMargin": "营业利润率",
    "NetMargin": "净利率",
    "FreeCashFlow": "自由现金流",
    "FreeCashFlowMargin": "自由现金流利润率",
    "ReturnOnEquity": "净资产收益率(ROE)",
    "ReturnOnAssets": "总资产收益率(ROA)",
    "DebtToEquity": "产权比率",
    "DebtToAssets": "资产负债率",
    "CurrentRatio": "流动比率",
    "RevenueCAGR": "营收复合增速",
    "CapitalExpenditures": "资本开支",
    "EBITDA": "息税折旧摊销前利润",
    "EBIT": "息税前利润",

    # ===== 行业常见科目（半导体/AI/科技 与 医疗）=====
    "ContractWithCustomerLiabilityRevenueRecognized": "合同负债转收入",
    "ContractWithCustomerLiability": "合同负债",
    "ContractWithCustomerAssetNetCurrent": "合同资产(流动)",
    "RevenueRemainingPerformanceObligation": "未履约履约义务(在手订单)",
    "DeferredRevenueNoncurrent": "递延收入(非流动)",
    "InventoryFinishedGoodsNetOfReserves": "产成品存货净额",
    "InventoryWorkInProcessNetOfReserves": "在产品存货净额",
    "InventoryRawMaterialsNetOfReserves": "原材料存货净额",
    "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost": "研发费用(不含在研收购)",
    "CapitalizedComputerSoftwareNet": "资本化软件净额",
    "ContractResearchAndDevelopmentExpense": "受托研发费用",
    "CollaborativeArrangementRevenue": "合作研发收入",
    "LicenseAndServicesRevenue": "授权及服务收入",
    "RoyaltyRevenue": "特许权使用费收入",
    "ProductMember": "产品收入",
    "ServiceMember": "服务收入",

    # ===== dei / 元数据 =====
    "EntityCommonStockSharesOutstanding": "流通股本",
    "EntityPublicFloat": "公众持股市值",
}
```

> 说明：以上中文均为规范会计/卖方术语。若 live DB 校验后发现某 tag 实际不存在或语义有出入，按 §2 fallback 与实测调整；新增长尾 tag 沿用同风格补入。

---

## 7. 分阶段实现 checklist（P0/P1/P2）

### P0 — 三大报表摘要 + 词典（本期核心，本地眼验）
- [ ] 新建/扩充 `_CONCEPT_CN`（§6 ~155 条），中文模式概念翻译全线生效（图标题/时序表/全量表 label）。
- [ ] 在 `sec_facts.py` 加 `STATEMENT_ROWS`（§2.3–2.5 三表行项配置：cn/en/primary/fallbacks/ifrs/is_instant）。
- [ ] 加 helper `build_statement_matrix(ticker, tax, rows, freq, periods)`（fallback 链命中 + 年列×科目行矩阵 + 缺失整行隐藏 + 末列 YoY/CAGR）。
- [ ] 页面 ②段：三张 `ui.render_html_table`（IS/BS/CF），暖色、money_b/right_text 格式、`—` 缺失、sticky 行头。
- [ ] 衍生指标小表（§2.2）。
- [ ] 本地眼验 AMKR（半导体 us-gaap）+ 一只医疗股，确认行项命中率与数值正确。
- [ ] ③段原始全量表降级为 ⑤ `st.expander`（搜索/筛选/CSV 保留）。

### P1 — 概念时序 + 周期可见性 + 视觉收口
- [ ] 概念时序图标题改 `concept_cn`/可读 label（反馈 b），单系列去图例（`charts.price_line_chart` 加 `show_legend`）。
- [ ] 周期切换换 `st.segmented_control` + theme CSS（反馈 a），全页统一。
- [ ] 概念 selectbox：词典常用概念置顶、显示中文名。
- [ ] section_header 红肋 + 导语 + 段间留白，整页视觉层级收口（反馈 d）。
- [ ] i18n：新增 keys（period/annual/quarterly/income_statement/balance_sheet/cash_flow/derived_metrics/raw_browser/yoy/cagr...）补 `pages_zh.py` + `pages_en.py`。
- [ ] ifrs-full 等价 tag 用一只 IFRS ADR 实测校验，定稿"待校验"项。

### P2 — 增强（可后置）
- [ ] 三大表支持"年度/季度"切换（季度 BS 用季末 instant、IS/CF 用单季 duration）。
- [ ] 衍生指标趋势 sparkline / 迷你折线。
- [ ] 可比表（④）联动：把当前个股三大表某行一键加入 comps。
- [ ] 缺失行项的 fallback 命中诊断折叠器（显示每行实际命中哪个 tag，便于维护词典/行项配置）。

---

## 8. 实现注意（约束复述）
- 运行时只读已 commit 的 `data/snapshots.db`，**不引入实时网络**。
- 两个页面（`8_SEC_Facts.py` HC / `a5_ai_sec.py` AI）共用同一套 §2/§4 逻辑，建议抽到 `sec_facts.py` 或新 render helper，domain 作参数，避免两份漂移。
- 涨跌染色锁 teal 涨 / red 跌；图表字号遵循 skills INVARIANTS（X tick ≥11pt / Y label ≥12pt / title ≥14pt）。
- 改动须本地眼验，George 明确"可以 ship"后才 commit/push。
