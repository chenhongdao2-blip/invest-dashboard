# US Biotech 组合 · 换仓与收益台账

> 医药股选股组合(catalyst-driven,Line B 1-30B 中小盘),基准 XBI,起始资金 $1,000,000。
> 口径:Top-N 等权、buy&hold、entry = 各 pick_date 收盘价、复权;与 invest-dashboard 完全一致。
> 本台账 = 决策 provenance,3 个月后可复盘规则是否有 edge。每次换仓追加一段。

## 收益链总览(截至 2026-07-09 收盘)

| 时点 | 组合 | 区间收益 | 资金 | 同期 XBI | 超额 |
|---|---|---|---|---|---|
| 2026-04-22 建仓 | v4 book(20 支等权) | — | **$1,000,000** | — | — |
| 2026-05-15 换仓 | v4 段收官 | **+0.60%** | $1,005,990 | −4.82% | **+5.42pp** |
| 2026-07-09 换仓 | v5 段收官 | **+28.88%** | **$1,296,511** | +25.83% | +3.05pp |

### ★ 累计:$1,000,000 → **$1,296,511**(**+29.65%**,盈亏 **+$296,511**);同期 XBI 链 +19.76% → **累计 alpha +9.89pp**

---

## 段①:v4 book(2026-04-22 → 2026-05-15,持有 23 天)

- 组合:v4_picks 前 20 等权(CYTK/BMRN/GMAB/IONS/MIRM/XENE/PTCT/EWTX/RVMD/ARGX/DNTH/CORT/ARWR/TNGX/SYRE/CELC/JAZZ/VRTX/ALMS/GPCR)
- 区间收益 **+0.60%**;同期 XBI **−4.82%** → **防御型 alpha +5.42pp**(下跌市扛住 + 反超)
- 最强:CORT +21% / CYTK +14% / JAZZ +13%;最弱:TNGX −24% / GPCR −17% / ALMS −12%

## 段②:v5 book(2026-05-15 → 2026-07-09,持有 55 天)

- 组合:v5_picks 前 20 等权(ARWR/NAMS/SNDX/CYTK/GMAB/RARE/COGT/AGIO/IMCR/JAZZ/MRNA/CRNX/GERN/MLTX/BMRN/TLX/IRON/APGE/ROIV/INCY)
- 区间收益 **+28.88%**;同期 XBI **+25.83%** → alpha +3.05pp(吃到 biotech 反弹)
- 三大功臣:**CRNX +127% / APGE +65%(并购)/ MRNA +56%**;最弱:NAMS +1% / JAZZ +8% / ARWR +10%

## 段③:v5.2 换仓(2026-07-09 建仓,进行中)

- **触发**:距上次 run 2 个月 + 首次用 v5.2 probe harness fresh run(50 支过三闸 → biotech-researcher ×10 批评分)
- **新组合(22 支等权,~4.55%/支)**:20 引擎票 + **2 人工主观加入(ALNY / GPCR)**
  - 引擎 Top20:IMCR CYTK NAMS RAPP XENE IRON QURE BNTX CLDX SRRK MIRM BBIO RYTM PHVS SNDX EWTX MAZE WVE CORT GMAB
  - 人工:ALNY(RNAi 平台龙头)· GPCR(口服 GLP-1)
- **卖出 14**:ARWR · CRNX(+118% 人工清仓落袋)· MRNA(+53%)· AGIO(+49%)· APGE(+65% 并购了结)· RARE · ROIV · INCY(走弱)· COGT · GERN · TLX · BMRN · JAZZ · MLTX
- **继续持有 6**:IMCR CYTK NAMS IRON SNDX GMAB
- **新建仓 14**:RAPP XENE QURE BNTX CLDX SRRK MIRM BBIO RYTM PHVS EWTX MAZE WVE CORT
- **换手率 70%**;等权卖 N 买 N,净现金中性;资金从 $1,296,511 滚入
- **换仓逻辑**:卖点 = 驱动本轮上涨的催化剂已兑现(掉出 v5.2 Top20 = 无 30-120 天临床催化剂),非裸涨幅;CRNX 为 PM 主观利润落袋(引擎仍认 Elite #7)
- **风险**:2026-08 催化剂拥挤(XENE 抑郁 / MIRM 丁肝);新池多 FIC 早期单资产票(QURE/RAPP),建仓前做 kill-criteria 复核
- 产物:`03_scoring_v5.xlsx`(评分)· `06_portfolio_v5.json`(组合)· `~/Desktop/biotech_v5.2_换仓可视化_2026-07-10.html`(可视化)· dashboard `v6_picks.csv`(pick_date 2026-07-09,22 支等权)

---

## 待办 / 已知问题

- **权重迭代规则设计**(进行中):从等权起步,涨幅/信号触发 trim/add/rebalance 的规则,调多 agent 讨论中 → 综合成 rulebook 后追加本台账。
- **probe BUG-009 不完整修复**:sec_10q_probe 漏 `us-gaap:MarketableSecurities` / `DebtSecuritiesHeldToMaturity...Current` 两个标签,本轮误伤 EWTX($33M→真实$500M)/QURE($140M→$586M),已父会话补数放行;待补 probe 概念清单。
- **M 维度普遍偏高**(v5.2 Top20 多支 M≥9.5)→ 记 v5.3 校准项,收紧 M_base×bd_coef 锚点。

*台账创建 2026-07-10 | 口径:招商证券(香港)AI 投研 | 评分为研究工具,不构成投资建议*

## 段③补记:transcript triage 捞回 2 票(2026-07-10)

- **背景**:发现催化剂闸(CT.gov PCD)有结构盲区(看不见 PDUFA/管理层 guided 时点)。用 minodata 管理层 transcript 对"过 Gate0 但被催化剂闸刷掉"的新面孔做 triage。
- **捞回**:8 支 triage → 4 支确认有近期催化剂 → 补跑 v5.2 评分 → **2 支够格进榜**:
  - **DNLI**(Denali)**8.28 → #3 Elite**:TransportVehicle 脑穿透平台,DNL126 Sanfilippo(零获批)近乎独家;催化剂 2026-09 pivotal
  - **MLYS**(Mineralys)**7.90 → #12 Top**:难治性高血压数十亿峰值;催化剂 2026-12 PDUFA(BUG-009 修正现金 646M/29mo)
  - INSM(6.22)/AXSM(5.59)排除:大盘商业化票,催化剂相对市值不 material
- **换仓 A**:DNLI/MLYS 进,**WVE/CORT 出**(最弱两只 7.21),维持 22 格等权。dashboard v6_picks.csv 已更新(pick_date 2026-07-09,备份 .backup-external-20260710T145135)。
- **方法沉淀**:催化剂闸边界票须用 transcript 管理层原话交叉核对(工具 `minodata_transcript.py`);⚠️ 该源 ipid 偶返错公司(KURA→Empire),fetch 后须校验内容含预期公司名。
