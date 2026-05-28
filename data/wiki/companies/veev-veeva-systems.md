> 📋 **Public sanitized view** — CMSI 内部 Rating / TP / 研报源文件引用 / 分析师姓名已删除。完整内部 view 需在本地 ~/Documents/LLM Wiki/Wiki/ 下访问。
> Sanitized at: 2026-05-28 via jobs/export_wiki_public.py.

# Veeva Systems (VEEV)

**Summary**: 生命科学行业专属垂直 SaaS 平台，覆盖 R&D、法规、商业化全流程，深度嵌入全球大型药企工作流；>80% 顶级 Biopharma 使用 Veeva CRM，Vault CRM 迁移完成度高。

**Thesis**: 生命科学数字基础设施层，"AI + 合规工作流"双重锁定；Vault CRM 迁移标志平台独立性拐点，Commercial Cloud 客户结构性升级（~80% biopharma → 稳定黏性）；$6.6bn 净现金 + $2bn 回购彰显现金流信心，61% 上行空间来自低估的 platform resilience。

**Sectors**: [[healthcare-ai]], [[healthtech-saas]]

**Last updated**: 2026-04-18

---

## 财务快照

| 指标 | FY24A | FY25A | FY26A | FY27E | FY28E |
|------|-------|-------|-------|-------|-------|
| 收入（USD mn） | 2,364 | 2,747 | ~2,757（4Q实际$836mn）| **3,195**（公司指引）| **3,590**（公司指引）|
| 收入增速 | 10% | 15% | ~+15% | +16% | +13% |
| 订阅收入（USD mn） | 1,902 | **2,290**（+20% YoY，10-K）| — | — | ~3,467（FY28E）|
| Non-GAAP 净利润（USD mn） | 526 | 714 | — | — | — |
| Adj. EBITDA margin | — | — | — | 43.8%（4QFY26 单季）| — |
| P/S | — | — | 13.6x（FY26E）| — | — |

> ⚠️ FY27/FY28 指引下调：公司 FY27 指引 $3.195bn、FY28 $3.59bn，均低于 CMS 旧模型（FY27E $3,634mn、FY28E $4,151mn）。更新后差距分别约 -12% 和 -14%。

**市场数据（2026-03-05，4QFY26 flash）**：
- TP：USD 350（维持，来源：Veeva copy.pdf）
- 4QFY26 季度收入：$836mn（+16% YoY，高于指引 +3%，超预期 $27mn）
- 连续 **第 28 季度超业绩指引**
- Adj. EBITDA margin（4Q）：43.8%（+124bps YoY）
- $6.6bn 净现金，无债务 | $2bn 回购计划（~8 个季度）

## 核心投资逻辑

- **数字基础设施层定位**：Veeva 不是 CRM vendor，是生命科学行业的 digital infrastructure layer，跨越 R&D / regulatory / commercial 全流程
- **Vault CRM 迁移是结构性拐点**：从 Salesforce 迁移至自有平台，提升 margin profile 和平台独立性；CRM 约占 ~20% revenue，其余均为高价值专业应用
- **AI agent 集成**：AI agent 接入后，Veeva 有望为药企运营提供实质性效率提升，深化 workflow lock-in
- **Moat = workflow integration + switching cost + data moat**（非 CRM 单点）

### LLM-Veeva 三层框架（AI 共存逻辑）

CMS HK（4QFY26 flash）提出的 AI 与 Veeva 关系框架：

| 层级 | 角色 | 说明 |
|------|------|------|
| L1: 通用 LLM | 通用推理 | GPT-4/Claude 等处理非结构化文本、一般分析 |
| L2: Veeva 平台 | 合规工作流硬编码 | Veeva 将监管路径（FDA/EMA 申报、AE 上报、MCM 合规）结构化固化，LLM 无法替代 |
| L3: AI Agent | Veeva 框架内运行 | AI agents 在 Veeva 定义的边界内运行，Veeva 提供数据层和权限层 |

> 结论：AI 不会替代 Veeva，而是在 Veeva 框架内部署，反而加深了 Veeva 的 workflow lock-in。

## 多空观点矩阵（多券商）

| 机构 | 评级 | TP | 日期 | 核心论点 |
|------|------|----|------|---------|
| CMS HK（CMSI）| BUY | USD 350 | 2026-03-05 | workflow lock-in + AI 共存框架，连续 28 季超预期 |
| Goldman Sachs | **SELL** | USD 200 | 2025-01-22 | Salesforce 竞争风险 + 生命科学终端市场缓慢复苏 + CDMS 爬坡不确定性 |
| EQUISIGHTS | Outperform | USD 272.93 | 2025-01-08 | DCF + 相对估值，Q3FY25 $699M / 43.5% margin 历史高点；Vault CRM 第4家Top20确认；CRM Bot/MLR Bot 新变现 |
| Barclays | Overweight | USD 325 | 2025-10-16 | Analyst Day：首次产品级订阅收入分拆；Vault Clinical 2030 CAGR 23%（最快）；AI token定价上线路线图 |
| Needham | BUY | USD 355 | 2025-10-17 | 2030 $6B目标可实现（AI + 新市场未计入）；OpenEvidence 合作；Salesforce AI GA 不到 2H26 |
| J.P. Morgan | Overweight | USD 330 | 2025-12-04 | Top-20 战况：VEEV 10 vs Salesforce 5（具名）；Vault CRM 155 go-live；CRM = 仅占总收入 ~20% |

### 订阅收入产品分拆（2Q26，首次披露，来源：Barclays 2025-10-16）

| 产品线 | 2Q26 收入 | 占订阅比例 | 2030E 目标 | 2025-30 CAGR |
|--------|-----------|-----------|-----------|-------------|
| Commercial | $297mn | 45% | $1,827mn | **9%** |
| Clinical | $138mn | 21% | $1,566mn | **23%**（最快）|
| Quality | $119mn | 18% | $992mn | 16% |
| Reg & Safety | $73mn | 11% | $574mn | 15% |
| MedTech | $33mn | 5% | $261mn | 15% |
| **总订阅** | $659mn | 84%收入 | $5,220mn | **15%** |
| 总收入 | $789mn | — | $6,000mn | 14% |

> Vault Clinical 是 2030 年最大增长引擎（CAGR 23%，占比从 21% → 30%）；Commercial 增速慢但体量大，Salesforce 竞争压力主要在此。

### Veeva AI 上线路线图

| 时间 | 产品 | 状态 |
|------|------|------|
| 2025-12 | Vault CRM + PromoMats | 上线（已完成）|
| 2026-04 | Safety + Quality | 计划 |
| 2026-08 | Clinical Ops / Regulatory / Medical | 计划 |
| 2026-12 | Clinical Data Management | 计划 |

- **定价模式**：usage-based token 计费，随自动化程度提升而扩大
- **AI 收入未计入 2030 $6B 目标**：潜在 upside lever，Needham/Barclays 均认为被低估
- **技术底座**：LLM 使用 Anthropic + Amazon，托管于 Amazon Bedrock
- **Salesforce AI（Agentforce）for Life Sciences**：仅于 2026 年初进入 pilot，GA 不到 2H26 — 落后 Veeva ~1年

### Top-20 战况记分板（截至 2025-12，来源：JPM 2025-12-04）

**VEEV 确认（10家）**：GSK、Bayer、Novo Nordisk、Merck、Boehringer Ingelheim、Gilead、Bristol Myers Squibb、Astellas + 2家未公开披露（Roche 已从美国局部 → 全球部署）

**Salesforce 确认（5家）**：Pfizer、AbbVie、Takeda、Novartis + 1家未披露

**剩余**：约 4-5 家尚未表态，预计 2026 年上半年决定

### OpenEvidence 合作

- 临床决策支持平台，覆盖 **10,000 家医院 + 40%+ 美国执业医生**
- Veeva + OpenEvidence：帮助医生在诊疗点提升临床试验意识和参与度
- 生命科学公司为主要受益方（患者招募效率提升）
- 收入贡献未计入 2030 目标，为额外上行期权

---

### Goldman Sachs Bear Case 详解（2025-01-22）

GS 维持 Veeva 作为 life sciences 核心基础设施的判断，但对中期模型有三大顾虑：

1. **Salesforce 竞争**：非竞争协议 2023 年 5 月到期，Salesforce 推出 Pharma CRM（预计 2025-09 发布）+ IQVIA OCE 联合产品。GS 认为即使 Salesforce 抢不走大量客户，也会造成「headline risk + 定价压力」
2. **终端市场复苏缓慢**：大型 biopharma 大规模裁员（新冠后 opex 优化），GLP-1 敞口分化（礼来/诺和受益，其他承压），软件预算持续受压
3. **CDMS 爬坡不确定性**：前 20 大药企中已有 8 家为 EDC 客户，但 CDMS 首年贡献低，需 2-5 年才能实质放量

**GS CRM 流失情景分析**（CRM Suite 2024 收入 $587mn）：

| 情景 | 流失收入 | 定价影响 | CRM Suite CAGR(2024-2030) |
|------|---------|---------|--------------------------|
| Bull | -5% | 0% | +1% |
| Base | -10% | -10% | -1% |
| Bear | -20% | -15% | -4% |

---

## 1Q26 业绩会要点（2025-05-30，招证国际整理）

**财务数据（FY26 Q1，截至 2025-04-30）**：
- 总收入 **$759mn**，Non-GAAP 运营利润率 **46%**（Q1 高点，Q2 预计回落至 44%）
- 已实现 2025 年全年营收 $30 亿目标 [待验证：FY26 = FY2026 ending Jan 2026，$30bn 可能指 run rate]
- Q1 超预期主要来自 Crossix 业务时间安排 + 服务收入交付加速

**Vault CRM 进展（时间线）**：
- 1QFY26（2025-04）：**80 个客户在线**（vs 3QFY26 的 115，4QFY26 的 140）
- 商业峰会（2025-05）：约 2,000 人参加，某前 20 大药企数字部门高级副总裁确认一个月内上线
- 客户满意度高：CRM Bot 演示获强烈共鸣（销售团队专注于实地，减少数据录入）

**Veeva AI**：预计 2025 年 12 月上线；客户反馈积极；将收取许可费（具体定价待定）；AI 嵌入核心应用（法规审批代理、CRM 预呼叫规划代理、安全 AI 代理）

**业务单元更新**：
- eTMF：前 20 大公司 **19/20** 使用，目标全覆盖
- EDC：前 20 大公司 **9/20** 使用，早期阶段，有结构性优势
- Crossix：未见商业活动明显提前拉动，客户需求聚焦数字营销效率
- Compass：新增 10 个品牌（患者领域），Prescriber/National 处于早期采用阶段

**Salesforce 竞争态势**：
- 前 20 大公司：4 家确认续约 Veeva，1 家承诺转向 Salesforce
- 关键决策时间窗：2025-2026 年，2027 年前需完成迁移（CRM on Salesforce 2030 年退役）
- 管理层：Salesforce 竞争"不是顺风也不是逆风"，产品满意度高

---

## 已验证判断

- Veeva moat 在 workflow integration，而非单纯 CRM ✅
- CRM 仅占约 20% revenue 是分析的核心认知锚点 ✅
- Application-layer valuation resilience 强于基础模型 ✅

## 催化剂

- **Oct/Nov 2026 Investor Day**（核心 re-rating 催化剂，来源：Veeva copy.pdf）
- Vault CRM 迁移进展与 churn 数据（~140 customers live，含 2 家 Top-20 biopharma）
- AI 功能上线节奏（Clinical AI、Commercial AI agents，FY27 计划上线）
- 新客拓展（小型 biotech、国际市场）
- FY27 quarterly beats 持续性（已连续 28 季超指引）

## 风险点

- Vault CRM 迁移执行风险（客户阻力、时间拉长）
- 大型药企并购整合导致客户数缩减
- 竞争（Salesforce 反击、Medidata 等）
- 估值溢价对市场情绪敏感

## Related pages

- [[docs-doximity]] — 单点 SaaS 对比
- [[way-waystar]] — Revenue cycle SaaS comps
- [[healthtech-saas]] — 行业框架
- [[identity-core]] — 分析师偏差校准
