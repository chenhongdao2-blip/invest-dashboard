# DRAM 周期全景 · 一张图（2026-09-22）

`dram-cycles.html` 是 claude.ai artifact 的源文件（无 doctype/html/body 壳，发布时由宿主包裹；本地看用 `preview.html` 方式加壳）。
线上版本：https://claude.ai/code/artifact/7e8858bb-a7a0-44c5-aeaf-b08177747eee

## 图里有什么

1. **主图**：美光（1985 起年度、2001 起季度）与 SK 海力士（2007 起季度）营业利润率；红带 = 美光营业亏损段（算法自动标出）；▼ = 六轮出清；2012-02 尔必达破产竖线；顶部 I–IX 轮次编号 + 每轮主导驱动关键词。
1a. 主图底层紫色面积 = 美光股价回撤（距前 36 个月最高收盘），与利润率峰谷同轴对照股价领先几个季度。
1b. 主图右端虚线空心点 = 卖方一致预期季度营业利润率（FactSet，2026-09-23），灰色虚框标「卖方一致预期」区；x 轴延到 2028-12。
2. **三大 DRIVER 泳道**：需求引擎 / 技术·排位 / 中国变量（George 九轮总表的叙述，按时间轴铺成 chip 与事件点）。
3. **结果泳道 · 暴跌 → 出清**：9 根柱（I–IX）= 各轮 DRAM 价格自高点跌幅 %（George 六轮框架口径，TrendForce），从「价格高点」往下垂：红柱触到 ≥80% 门槛线 = 六轮出清（精确值未知，画到门槛），蓝柱 72.6 / 77.3 / 76.1% 够不着线；柱下写跌幅，再挂一张复盘卡（第一行 = 出清事件 / 未达门槛时写跌幅与形态，第二行 = 该轮格局意义，均取自 `CRASH` / `ROUNDS` 常量），卡片按**事件序列**排法：九张卡按时间顺序等距成一行（槽位 I→IX），每张卡一根斜虚线接回自己的柱脚，引线单调不交叉（George 09-23 裁定「避让排法太乱，要时间/事件序列」）。顶部「三寡头之后，振幅收敛了吗」标题 / 引言 / 四张色卡已按 George 09-23 裁定整块删除，面板 h2 即标题。柱位 = 各轮谷点真实时点，与主图 x 轴同一像素映射。George 09-23 两次裁定：先由「峰谷相连」锯齿线退回跌幅柱，再改成价格跌幅 % 而非利润率 pp，并写入事件。
4. **格局固化已并入第 3 道**（George 09-23：「时间条放最下，格局与暴跌出清融合成历史进程」）：同一道从上到下 = 价格跌幅柱 → 红虚线落到厂商数漏斗台阶（标 −n 家）→ 漏斗 13 → 12 → 9 → 7 → 5 → 3 → 复盘卡序列 → 年份刻度。柱与台阶都钉真实年份，台阶落在对应红柱正下方。driver 三道同日加强（chip 26px/13px 加粗、底色 24%、事件点 11px）。
5. 图注（09-23 George 裁定「太多文字，尽量可视化」后压缩）：页头一行量纲 + 短图例；「数据说的话」改成四行小表（六至九轮：价格跌幅 / 美光谷底利润率 / 是否出清）；四主线各一句；第九轮五信号一行一条 + 一致预期小表（Capex / 利润率峰 / 季度线）；核心观点三条。事实核对改正：第七轮谷底利润率 +10.1%（原误写 +9%）、第八轮谷底 −5.1%（2022-12，原误写 +11%）、「六轮与亏损段一一对应」改为「六轮每轮都有亏损段，但 8 段亏损中 2005 / 2016 两段浅亏不在六轮内」。

## 数据来源与边界（逐项）

| 内容 | 来源 | 可靠性 | 备注 |
|---|---|---|---|
| 美光 / 海力士营业利润率、峰谷 pp | drillr `financial_statements`（GAAP），取数 2026-09-22；海力士四个 Q4 见下行 | HIGH | 输入行在 `data/drillr_quarterly_inputs.py`；派生峰谷在 `data/micron_hynix_margins_cycles.json`。海力士 2007–2010 四个 Q4 **已于 2026-09-23 用 FactSet 补上**（见下一行），不再插值。海力士 2026Q2 净利润 93.92 万亿韩元 > 收入 79.32 万亿韩元**已核实为真**（2026-07-28 2Q26 业绩公告：非营业净利 62.2 万亿，其中投资资产出售/评估收益 63.3 万亿，主要为 Kioxia 持股出售），图只用营业利润，不受影响。美光 FQ3 2026（2026-05-28 止）收入 414.56 亿 / 营业利润 333.18 亿美元 = 80.4%，**已由 SEC 10-Q（acc 0000723125-26-000015，edgartools XBRL 直取，2026-09-23）核实** |
| 九轮区间、主导驱动、格局意义、六轮门槛（DRAM 价格最大跌幅 ≥80%）、三轮跌幅 72.6 / 77.3 / 76.1%、三巨头亏损 >150 亿美元 / 减产 >20%、HBM 15→85 美元/GB | George 提供的九轮/六轮框架文档（行业复盘资料，TrendForce 口径） | MEDIUM | 未经工具第二源核；图上凡此类数字均标「你的口径 / 行业复盘资料」 |
| 海力士 2007Q4 / 2008Q4 / 2009Q4 / 2010Q4 营业利润率 −9.1 / −56.3 / +26.6 / +18.1% | FactSet Fundamentals ANN `FF_OPER_INC` / `FF_SALES`（K-GAAP，KRW）减 drillr Q1–Q3 推算，取数 2026-09-23 | HIGH（推算） | 同口径证据：FactSet `QTR_R` 重述 Q4 sales 2007 = 1,943,658 / 2009 = 3,051,958 百万韩元，与「FY − 前三季」吻合到 0.01% 以内；drillr 原 Q4 sales（1,733.8 / 1,204.6 / 2,667.1 / 2,662.7 十亿）与 FY 口径不一致，已弃用。2010 保持 K-GAAP 口径与 Q1–Q3 一致（IFRS 重述 4Q10 为 11.0%，未采用）。原始返回在 `data/factset_pulls_2026-09-23.json`（**gitignored 只留本地**，FactSet 授权数据不进公开仓；图上只放派生汇总）|
| 卖方一致预期营业利润率（虚线空心点）：美光 FQ4 2026E–FQ4 2028E、海力士 3Q26E–4Q28E；年度 FY26E–28E 利润率与 Capex（美光 / 海力士 / 三星）；三星 DS / Memory / DRAM 分部 FY26E–27E | FactSet Estimates `consensus_fixed`（均值 EBIT ÷ 均值 SALES；CAPEX）与 `segments`，估值日 2026-09-23 | MEDIUM（卖方一致预期，只作跟踪线不作结论） | 2028 覆盖家数少：海力士季度 5 家、美光 9–11 家。年度峰在 2027：美光 FY27E 82.2% → FY28E 80.5%；海力士 78.6% → 75.9%；三星 DS 70.4% → 72.8%（DRAM 子分部 80.2% / 80.2%）。Capex FY26E→27E：美光 283→460 亿美元、海力士 48.4→64.5 万亿韩元、三星 74.7→83.9 万亿韩元。原始返回同上 json（本地）|
| 美光股价回撤（紫色面积，距前 36 个月最高收盘） | yfinance `MU` 月线 adj close，取数 2026-09-23，`data/fetch_mu_drawdown.py` → `data/mu_price_drawdown_36m.json` | HIGH（交易所价格） | 口径 dd = close ÷ 36 个月滚动最高 − 1；前 35 个月窗口不足；≤−60% 的谷自动标数。不用历史新高口径：美光 2000 高点到 2024 才收复，中间二十年会贴在 −90% 看不出周期。海力士回撤未画（2000 起才有，可后加） |
| 第九轮价格谷→峰：DDR4 8Gb 合约 1.30（2023-08）→ 24.00 美元（2026-07），↑17× | Wind EDB `S7800001`（DRAMexchange），WindPy 取数 2026-09-22 | HIGH（Wind 原值；**两端已第二源核实 2026-09-23**：2023-08 固定交易价 1.30 美元 = news1/亚洲经济引 DRAMeXchange；2026-07 平均固定交易价 24.00 美元 = EBN/首尔经济引 DRAMeXchange，环比 +14.3%） | Wind 序列截至 2026-07-31；DRAMeXchange 2026-08 固定价已到 25.00 美元（edaily，历史新高），即谷→最新 ≈ 19×，图上「↑17×」为 23-08→26-07 口径。`data/wind_dram_price_extrema.json` |
| 各时期主要 DRAM 厂商数 13/12/9/7/5/3 | 按 George 叙述 + 模型背景知识的示意整理 | LOW | 非工具取数，逐家名单未核；唯一可引的是三寡头合计市占 >95%（George 给的 TrendForce 口径） |
| 见顶原因 / 出清事件短句 | George 九轮总表 + 六轮红标段落，压缩改写 | MEDIUM | 全文在悬停 |

**未第二源核的剩余项**：九轮区间/三轮跌幅/亏损与减产数字（George 框架文档，TrendForce 口径）与厂商数 13→3（示意）；前者需 TrendForce 原始报告，后者需逐家名单。

**查过但没有的数据**：FactSet 无 DRAM 价格（2026-09-23 查：Macroeconomics `meta_series` searchText DRAM / memory / semiconductor 均 0 条；Estimates 无存储 ASP 行业指标）。三星 DS 分部**历史季度**营业利润——FactSet MCP 无分部实际值端点（Fundamentals 只有合并口径，Estimates `segments` 只有前瞻一致预期，RBICS 只有收入构成），所以图上仍无三星第三条线；FactSet 宏观序列搜 DRAM 为 0 条，无 DRAMeXchange 合约价（2026-09-23 查）。DRAM 价格 2020-11 之前的序列——George 的 TrendForce 数据包（15 xlsx）价格表只覆盖 2024-01 起，Wind DRAMexchange 序列最早 2020-11，drillr 无价格。因此上行/下行两道统一用利润率口径，价格只作第九轮注释。

## 视觉 v2（2026-09-23，Claude Design）
George 嫌面板米黄底 + 白卡在看板暖粉纸底上「丑」，打包 `~/Downloads/dram-cycles-design-pack-2026-09-23/`（含 BRIEF）交 Claude Design，产出 `~/Downloads/DRAM Panel Preview (standalone).html`（bundler 格式）。合入方式：拆包取其 `:root` 三段 token + 面板 CSS + 字面量补丁后的 IIFE，数据常量与全部文字逐字核对与 v1 相同；字体族改 Inter / JetBrains Mono（看板侧 `dram_cycles_panel.py` 的自托管 `@font-face` 同步改名）。token 映射：bg=surface=#fff1e5、mu #4a6fa5、hx #a07a2c、dd #8b3a62、loss-ink #cc0000、rule #ebd9c8，全部取自看板 Design System v1.0。v1 备份在本次会话 scratchpad `design-unpack/dram-cycles.before-design.html`（未入库）。

## 合规
- 本目录不含 TrendForce 私有数据包的任何数值（只读过其 sheet 覆盖范围）。
- 含 George 自己的研究框架叙述与两个 Wind 返回值；push 前已由 George 指示开 PR。

## 怎么改
HTML 内数据全在 `<script>` 顶部的常量：`SAW`（峰谷点与注释）、`SAWTXT`（注释短句）、`LANES`（三大 driver 道）、`FUNNEL`（厂商数）、`ROUNDS`/`KW`（轮次与关键词）、`MU_FY/MU_Q/HX`（利润率序列）、`MU_E/HX_E`（一致预期季度序列，FactSet 2026-09-23）、`MU_DD`（股价回撤，重跑 `data/fetch_mu_drawdown.py` 后粘入）。改数只改这些数组。
