> 📋 **Public sanitized view** — CMSI 内部 Rating / TP / 研报源文件引用 / 分析师姓名已删除。完整内部 view 需在本地 ~/Documents/LLM Wiki/Wiki/ 下访问。
> Sanitized at: 2026-07-10 via jobs/export_wiki_public.py.

# 英伟达 (NVDA)

**Summary**: 全球 AI 算力基础设施龙头，从 GPU 芯片公司演进为覆盖计算（Rubin/Blackwell GPU + Grace/Vera CPU）、纵向扩展互联（NVLink）、横向扩展网络（Spectrum-X/InfiniBand/CPO）、DPU（BlueField）、软件（CUDA）的全栈"AI 工厂"系统级公司。

**Thesis**（卖方/管理层叙事，非本人结论）:
1. **"算力=收入=GDP"叙事**：管理层主张推理/Agentic AI 时代算力直接换算成 Token 产出与客户营收，每瓦性能领先一个数量级构成系统级护城河。
2. **全栈协同设计 vs 单芯片 ASIC**：管理层反复强调以"机架级全栈架构"对抗超大规模厂商自研 ASIC，认为单点芯片迭代难以跟上 Vera Rubin 年度全平台更新节奏。
3. **核心争议在估值定价权与利润率**：买方对增长无疑虑，分歧集中在 ASIC/TPU 替代、存储涨价、电力约束三大空头论点是否侵蚀定价权与毛利率。

**Sectors**: [[ai-compute-capex]], [[semi-ai-infrastructure-demand]], [[semi-advanced-packaging]], [[optical-module-cpo]]

**Last updated**: 2026-05-29

---

## 财务快照

> ⚠️ 以下区分**管理层披露**（HIGH）vs **卖方预测**（MEDIUM，卖方一致预期，不采信为结论）。

| 指标 | 数值 | 期间 | 来源 |
|------|------|------|------|
| 收入（管理层披露） | 570 亿美元 | FY26 Q3 | 黄仁勋_CES_分析师问答.md |
| 收入指引（管理层） | 650 亿美元 ±2% | FY26 Q4 | 黄仁勋_CES_分析师问答.md / 英伟达业绩前瞻.md |
| 数据中心收入（卖方共识） | ~600 亿美元（门槛 ~620 亿）| FY26 Q4 | 英伟达业绩前瞻.md |
| Non-GAAP 毛利率（管理层披露） | 73.6% | FY26 Q3 | 黄仁勋_CES_分析师问答.md |
| Non-GAAP 毛利率指引（管理层） | 75.0% ±50bps | FY26 Q4 | 黄仁勋_CES / 英伟达业绩前瞻.md |
| FY27 Q1（4月）收入指引（卖方预期） | 共识 715–718 亿；买方期望 735 亿（不含中国）| FY27 Q1 | 英伟达业绩前瞻.md |
| EPS（卖方共识 vs 买方）| FY26: 共识 7.75 / 买方 9–10；FY27: 共识 9.50 / 买方 12–14 美元 | FY26–FY27 | 英伟达业绩前瞻.md |
| P/E（卖方测算）| 按 FY27 买方 EPS 计 <15x（若毛利率降至 68–70% 仍约 16–17x）| FY27 | 英伟达业绩前瞻.md |
| 预计年度现金生成 | ~1000 亿美元 | 2026 | 英伟达业绩会问答环节.md |
| EV/EBITDA | [待补] | | |

## 催化剂

**近期**
- **GTC 大会（2026/3/16–19，圣何塞）**：预期公布 Rubin Ultra、Feynman 路线图、低延迟推理 LPU，以及 Quantum-X/Spectrum-X CPO 交换机供应链名单。
- **MS TMT 大会（2026/3/4）已召开**：管理层称交付"人类有记录以来单季最佳财报"，提出"三个新增长支柱"——OpenAI 算力扩展至 AWS、Anthropic 跨平台扩容、Meta MSL 全新数百万 GPU 需求。
- **Vera Rubin 平台**：CES 表态已进入"全面量产阶段"（流片完成），2026 下半年向合作伙伴供货，生产周期 9 个月以上；管理层预期"大规模出货"。

**中期**
- **CoWoS 产能上调**：JPM 三个月内第二次上调 2026/2027 CoWoS（+8%/+13%）；NVDA 2026 分配维持 70 万片，2027 上调 4%，Rubin/Rubin Ultra 为增长主力。
- **CoWoP 提前**：广发预期 CoWoP 最早 2026 年底用于 Rubin、Rubin Ultra 量产，早于市场原预期 2027 底–2028.md）。
- **机架级 ASP 抬升**：卖方测算 Rubin 系列 ASP 700–800 万美元/台，GB300 400–500 万；Rubin Ultra 机架约 1000 万美元（区间 850–1100 万），较 Rubin Vera +100%。Rubin 单台 PCB 价值量从 GB200 的 400 美元升至 1095 美元，引入背板后或超 2000 美元.md）。
- **CSP capex 爆发**：四大巨头单季合计上调 2026 capex 约 1400–1450 亿美元，2026 总支出预计破 6000 亿（+60% YoY）；ODM 供应链截至 1 月同比 +91%。
- **DC 需求持续上修**：OpenAI 美国需求从 5GW 升至接近 10GW；Anthropic 9GW 长期规划；供需比 3:1 将于 2026 年底升至 4:1（史上最紧张）。
- **Groq / Enfabrica 类并购**：与 Groq 达成非排他技术授权 + 吸纳团队（低延迟推理，约占 AI 基建需求 10%）；斥资 >9 亿美元延揽 Enfabrica CEO + 技术授权（解决超大规模集群互联）。
- **CPO 部署启动**：Quantum-X InfiniBand + CPO 首批伙伴 CoreWeave、Lambda、TACC；功耗较可插拔降约 5 倍。
- **中国 H200 许可**：仍在政府审批中，是潜在增量利好但受监管不确定性约束。
- **物理 AI / 机器人 / 自动驾驶**：管理层定位为下一个万亿级增长极，自动驾驶当前营收已达数十亿美元级。

## 风险点

- **ASIC/TPU 替代叙事升温**：最近一次 CSP 业绩季对 NVDA 提及率为历次最低，市场转向 ASIC/Trainium/TPU/AMD；NVDA 因 CSP 业绩后罕见暴跌。
- **Harness/系统工程范式转移**：Agentic 框架成型后 AI 基建要求改变，CPU/内存/存储/调度/安全等"非 GPU 零部件"价值抬升；CSP 须自任"main chef"做系统设计，单一 NVDA 方案无法满足多样化需求（GB 系列已为不同客户定制几十款参考设计）。
- **利润率 2027 风险**：每代产品 HBM 用量增加，即便单价受 LTA 保护（HBM 长协至 2026），绝对美元影响扩大；机架级转型引入网络/冷却/供电等低毛利 BOM；毛利率每降 100bps 约影响 EPS 15 美分。
- **定价权风险**：若竞品在核心负载实现"性价比相当"的 Token 经济性，将削弱 75% 毛利率目标的定价权——第三方基准（SemiAnalysis）与超大规模自研 ASIC 路线图是关键监控对象。
- **Vera Rubin 集成执行风险**：平台依赖 HBM4、CPO、第六代 NVLink、新 DPU/NIC 多供应链同步就绪与良率，全自研多芯片平台执行复杂度高（管理层自认"具有内在难度"）。
- **电力 / 土地 / 部署速度约束**：增长瓶颈来自物理条件而非需求；管理层反将"约束"解读为利好（逼客户选最优方案）。
- **新兴云客户融资敏感性**：CoreWeave/Lambda 等对融资成本与利用率敏感，若 capex 进入消化期受冲击显著。
- **股价对超预期无反应**：买方情绪"知道会超预期但股价不动"，资金已前置布局上游存储/CPU/光。
- **游戏业务显存供应紧张**：未来几个季度 GDDR 供应紧张，FY27 同比增长存疑。

## Related pages

- [[ai-compute-capex]]
- [[semi-ai-infrastructure-demand]]
- [[semi-advanced-packaging]]
- [[optical-module-cpo]]
- [[googl-alphabet-tpu]]
- [[avgo-broadcom]]

---

## 最新季度数据 (as_of 2026-07-10)

> 轻档(财务快照 + 会议指针,未做深提炼)· SEC EDGAR + minodata · 研究用途,非投资建议

**财务(SEC 10-Q, CIK 1045810, 截至 2026-04-26)**

| 指标 | 值 |
|---|---|
| 现金+投资 | **$62,359.0M** (现金 $13,237.0M + 短投 $49,122.0M) |
| 季度 R&D | $6,321.0M |
| 季度收入 | $81,615.0M |
| 季度净利 | $58,321.0M |
| 季度 OCF | $50,344.0M |
| Runway | —(现金流为正/NA) |

**会议指针(minodata,未提炼)**:最新业绩会 **2026-05-20**(ipid 360370565) · 最新大会 2026-05-28(ipid 360374944)

**来源**:SEC CIK 1045810 · minodata · 截至 2026-07-10
