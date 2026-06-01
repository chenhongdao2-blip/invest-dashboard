> 📋 **Public sanitized view** — CMSI 内部 Rating / TP / 研报源文件引用 / 分析师姓名已删除。完整内部 view 需在本地 ~/Documents/LLM Wiki/Wiki/ 下访问。
> Sanitized at: 2026-06-01 via jobs/export_wiki_public.py.

# 谷歌/Alphabet TPU (GOOGL)

**Summary**: Alphabet 旗下谷歌通过自研 TPU（张量处理单元，由博通联合设计、台积电制造）+ 自建数据中心 + Gemini 模型构建全栈 AI 体系，是 NVDA GPU 之外最具规模的自研 ASIC 算力路线，并通过 Google Cloud 对外输出算力。

**Thesis**（卖方/管理层叙事，非本人结论）:
1. **自研 ASIC 替代叙事的核心标的**：TPU v7（Ironwood）/v8 量产爬坡 + 出货量大幅上修，是"ASIC 替代 GPU"主线的最大受益方，叠加博通 730 亿订单的核心来源。
2. **capex 爆表 + 云加速变现**：2026 资本开支指引 1750–1850 亿美元，Google Cloud +48%、年化运行率超 700 亿美元、订单储备 2400 亿。
3. **全栈 AI 飞轮**：自研 TPU + NVDA GPU 双路线 + Gemini 3 + 自建数据中心效率，单位服务成本 2025 年下降 78%。

**Sectors**: [[ai-compute-capex]], [[semi-ai-infrastructure-demand]], [[semi-supply-diversification]]

**Last updated**: 2026-05-29

---

## 财务快照

> ⚠️ 以下为**管理层披露**（谷歌业绩电话会，HIGH）。Alphabet 整体估值倍数 [待补]。

| 指标 | 数值 | 期间 | 来源 |
|------|------|------|------|
| Alphabet 年收入 | 首次突破 4000 亿美元 | FY2025 | 谷歌业绩电话会_爆表的资本开支.md |
| Google Services Q4 收入 | 960 亿美元（+14% YoY）| 2025 Q4 | 谷歌业绩电话会_爆表的资本开支.md |
| 搜索及其他收入 | +17% YoY | 2025 Q4 | 谷歌业绩电话会_爆表的资本开支.md |
| Google Cloud 收入 | +48% YoY，年化运行率 >700 亿美元 | 2025 Q4 | 谷歌业绩电话会_爆表的资本开支.md |
| Cloud 订单储备（backlog）| 2400 亿美元（环比 +55%）| 2025 Q4 | 谷歌业绩电话会_爆表的资本开支.md |
| YouTube 广告+订阅年收入 | 突破 600 亿美元 | FY2025 | 谷歌业绩电话会_爆表的资本开支.md |
| 资本开支 | 2025: 914 亿；2026 指引 1750–1850 亿美元 | 2025 / 2026E | 谷歌业绩电话会_爆表的资本开支.md |
| P/E (TTM) | [待补] | | |
| EV/EBITDA | [待补] | | |

## 催化剂

**近期**
- **Gemini 3 发布**：带动全公司 AI 产品使用量、参与度显著提升，成为关键节点；Gemini App 月活超 7.5 亿（Q4 新增 1 亿）。
- **TPU v8 提前出货**：v8 提前 3 个月出货，年底月出货量将突破百万台；TPU v7（Ironwood）2025 出货数十万台，2026 增至"数百万台"。
- **CoWoS 分配上修**：谷歌 TPU 2026/2027 出货预期上调至 370 万/500 万台，博通、联发科分配同步增加，当前主要由台积电 CoWoS-S 供应。
- **Gemini Enterprise**：推出 4 个月卖出 800 万付费席位，服务 >2800 家企业客户。

**中期**
- **OCS（光电路交换机）+ TPU 出货增长**：v7 集群持续部署 OCS，商业化加速；TPU 出货 2027 base case ~700 万、2028 ~1000 万（2030FY 认为很保守，市场曾传 2028 几千万片）。
- **TPU v9 研发中**：博通已参与，称"性能强劲"；下一代用 3.5D 面对面堆叠 + 4 计算芯片 + 400G SerDes，2028 向 2 家客户送样；2027 年底 SoIC 将用于 TPU v9、Trainium4 等 2nm AI ASIC。
- **Anthropic 算力绑定 TPU**：Anthropic 9GW 长期规划中约 1/3（3GW）来自亚马逊+谷歌；Fluidstack 作为 TPUaaS 提供商同意从谷歌采购约 1.2GW TPU 机架。
- **Apple 战略合作**：谷歌成为 Apple 首选云服务商，并基于 Gemini 共建下一代基础模型；Siri 新合作。
- **效率红利**：约 50% 代码由智能体编写（工程师审核）；2025 Gemini 单位服务成本降 78%。

## 风险点

- **算力供应短缺**：管理层明确 2026 全年仍将面临算力供应短缺（电力、网络、供应链多重约束）；供应链交付周期延长。
- **TPU 外溢有限**：管理层称 TPU 核心价值体现在 Google Cloud 整体竞争力中，未明确承诺 TPU 走出谷歌云至外部数据中心（回避了分析师追问）。
- **Meta 对 TPU 采用仍有限**：原因是软件与工作流优化仍 N 卡占优，Meta 继续试用 TPU 以避免供应商锁定，但规模相比 N 卡太小。
- **TPU 出货量预期分歧**：DCI/OCS 访谈认为不会达到传闻"每年数千万片"规模，2028 接近 1000 万更现实。
- **capex 折旧拖累**：2026 资本支出约 60% 设备 / 40% 长周期资产（建筑折旧 40 年+）；略超 50% ML 算力投向云业务。
- **SaaS 客户定价权质疑**：市场担心 Gemini 的 SaaS 客户正失去定价权、非优质客户群（管理层反驳）。
- **AI 搜索变现/导流风险**：AI 模式对话化、单会话更长、对外部链接导流下降，商业化路径仍在试点。

## Related pages

- [[ai-compute-capex]]
- [[semi-ai-infrastructure-demand]]
- [[semi-supply-diversification]]
- [[avgo-broadcom]]
- [[nvda-nvidia]]
- [[optical-module-cpo]]
