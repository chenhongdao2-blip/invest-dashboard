> 📋 **Public sanitized view** — CMSI 内部 Rating / TP / 研报源文件引用 / 分析师姓名已删除。完整内部 view 需在本地 ~/Documents/LLM Wiki/Wiki/ 下访问。
> Sanitized at: 2026-07-10 via jobs/export_wiki_public.py.

# NewAmsterdam Pharma (NAMS)

> **US Biotech v5.2 筛选快照** · as_of 2026-07-10 · Line B Venture (1–30B) · 招商证券(香港) AI 投研 · 评分为研究工具，不构成投资建议

**Tier**: Elite | **Final Score**: 8.225 | **Rank**: #3 | **Mcap**: $4.19B | **进 book**: 是

**TA / Modality**: 血脂异常/ASCVD(CVRM慢病) / 口服CETP小分子抑制剂
**Lead asset**: obicetrapib
**Indication / Phase**: 高LDL/ASCVD(降LDL) / 申请上市 (BIC)

**Variant perception（引擎 thesis，非本人结论）**: 共识被CETP墓地(torcetrapib/dalcetrapib/evacetrapib/anacetrapib皆败)吓住,给obicetrapib折价。我们的差异:obicetrapib是纯降LDL口服选项而非HDL假说,Ph3 LDL降幅强、安全性无脱靶,填补statin不耐受+口服便利缺口。催化=FDA审批+CVOT进展。结论:高赔率高信念,BD吸引力顶级,Top。

---

## 评分拆解（v5.2-RFC: 0.40P + 0.25E + 0.10F + 0.20M + 0.025(10-R)）

| 维度 | 分 | 关键子项 / 理由 |
|---|---|---|
| **P** 管线稀缺 (0.40) | **9** | base 7.5 + rank_mod 1.5 · 口服CETP降LDL赛道唯一后期(Top1),其他CETP多已失败退出 |
| **E** 商业价值 (0.25) | **6.3** | E1 8(DOMAIN_EST) / E2 5 / E3 0, conf MEDIUM |
| **F** 现金 (0.10) | **9** | runway 34.2 mo · runway 34.2mo(HIGH)+cash 707mm,足以覆盖上市+CVOT前期 |
| **M** 并购吸引 (0.20) | **10** | base 8 × bd_coef 1.5 + MNC hits 4 · 口服降脂大品类,与CVRM巨头(NVS/AMGN/LLY/AZN)管线互补强,并购/授权高概率 |
| **R** 风险 (逆权 0.025) | **4** | Ph3 fails 0 · 单资产高度集中+CETP类历史阴影;LDL达标但CVOT硬终点未证 |
| **MSO** | NaN | DATA_MISSING, weight_sum=0.975 (INV-V4) |

> ⚠️ **P 置信度 flag**: `NEEDS_ANALYST_TA_SPECIFIC` — LDL为surrogate终点,CETP类心血管结局(CVOT)历史屡败,类效应风险需专业裁

> ⚠️ **NEEDS_ANALYST**: CETP类LDL surrogate vs CVOT硬终点脱节史(anacetrapib阳性但增量小),类效应风险需专业裁

## 催化剂 / 时点

- **CT.gov PCD**: 2026-09（30–120d 催化剂窗口）

## 数据来源 / provenance

- **lead_asset**: ctgov_probe NCT=NCT06982508 pcd=2026-09 retrieved=2026-07-09
- **gate0**: orange_book_probe verdict=EMERGING nda={'nda': 0, 'bla': 0, 'total': 0} ipo=None retrieved=2026-07-09
- **runway**: sec_10q_probe accession=00 as_of=2026-03-31 runway=34.2mo
- **p_rank**: pharmcube drugBaseLiteCN lead=obicetrapib target=CETP抑制剂 phase=申请上市 quality=HIGH retrieved=2026-07-09

**Sectors**: [[biopharma]], [[us-biotech-screening]]

## Related pages

- [[us-biotech-v5.2-screening-2026-07-10]]
- [[biopharma]]

---

## 最新季度数据 (as_of 2026-07-10)

> 数据抓取 2026-07-10 · SEC EDGAR + minodata 海外纪要 · 研究用途,非投资建议

**财务(SEC 10-Q, CIK 1936258, 截至 2026-03-31)**

| 指标 | 值 |
|---|---|
| 现金+投资 | **$707.3M** (现金 $457.6M + 短投 $178.5M) |
| 季度 R&D | $38.0M |
| 季度收入 | $3.0M |
| 季度净利 | $-48.4M |
| 季度 OCF | $-30.6M |
| Runway | ~69 个月 |

**业绩会要点(minodata 2026-05-07)**

1. obicetrapib PREVAIL:末位患者入组满 2 年,盲态 MACE 率低于预期,决定 2026Q4 中期分析,2027Q1 出结果
2. MACE-4 主终点扩至纳入全冠脉事件,平均随访近 3.5 年,事件数远超原预期~950 起→统计效力增强(BROADWAY HR 0.79)
3. 2026-08-05 年度投资者日披露更多细节

**来源**:SEC CIK 1936258 · minodata ipid 360373391(业绩会 2026-05-07) · 截至 2026-07-10
