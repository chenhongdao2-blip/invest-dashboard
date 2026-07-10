> 📋 **Public sanitized view** — CMSI 内部 Rating / TP / 研报源文件引用 / 分析师姓名已删除。完整内部 view 需在本地 ~/Documents/LLM Wiki/Wiki/ 下访问。
> Sanitized at: 2026-07-10 via jobs/export_wiki_public.py.

# EyePoint (EYPT)

> **US Biotech v5.2 筛选快照** · as_of 2026-07-10 · Line B Venture (1–30B) · 招商证券(香港) AI 投研 · 评分为研究工具，不构成投资建议

**Tier**: Rest | **Final Score**: 5.305 | **Rank**: #39 | **Mcap**: $1.17B | **进 book**: 否

**TA / Modality**: Ophthalmology(wet AMD/DME) / TKI缓释植入(vorolanib)
**Lead asset**: Duravyu(EYP-1901)
**Indication / Phase**: 湿性年龄相关黄斑变性/DME / III期 (BIC)

**Variant perception（引擎 thesis，非本人结论）**: 共识对Duravyu缓释减少注射频率的临床价值有共识,分歧在LUGANO(2026-08)/LUCIA能否对Eylea/Vabysmo证明视力非劣。给药间隔延长若成立TAM巨大。硬约束:runway仅6mo,双P3前需融资摊薄。风险:眼底红海+现金bomb叠P3二元。结论:高赔率二元催化+融资风险,vol放大Watch。

---

## 评分拆解（v5.2-RFC: 0.40P + 0.25E + 0.10F + 0.20M + 0.025(10-R)）

| 维度 | 分 | 关键子项 / 理由 |
|---|---|---|
| **P** 管线稀缺 (0.40) | **6.7** | base 7 + rank_mod -0.3 · 眼底缓释Top4-5 0;me-too 6-10红海-0.3 |
| **E** 商业价值 (0.25) | **5.1** | E1 6(DOMAIN_EST) / E2 5 / E3 0, conf MEDIUM |
| **F** 现金 (0.10) | **2** | runway 6.3 mo · runway仅6.3mo[RUNWAY_TIGHT],cash$222M需融资撑双P3 |
| **M** 并购吸引 (0.20) | **5** | base 6 × bd_coef 1 + MNC hits 2 · 缓释差异化但与REGN/Roche眼底franchise直接竞争,BD中等 |
| **R** 风险 (逆权 0.025) | **4** | Ph3 fails 0 · 单产品>80%价值+runway<12mo需融资+眼底红海,无ph3失败 |
| **MSO** | NaN | DATA_MISSING, weight_sum=0.975 (INV-V4) |

> ⚠️ **P 置信度 flag**: `NEEDS_ANALYST_BIC` — cross-trial对比aflibercept/faricimab给药间隔非劣需专科+P3<90d降档

> ⚠️ **NEEDS_ANALYST**: wet AMD给药间隔非劣性BIC路径涉cross-trial对比Eylea/Vabysmo,需眼科专科判读

## 催化剂 / 时点

- **CT.gov PCD**: 2026-08（30–120d 催化剂窗口）

## 数据来源 / provenance

- **lead_asset**: ctgov_probe NCT=NCT06668064 pcd=2026-08 retrieved=2026-07-09
- **gate0**: orange_book_probe verdict=EMERGING nda={'nda': 0, 'bla': 0, 'total': 0} ipo=None retrieved=2026-07-09
- **runway**: sec_10q_probe accession=00 as_of=2026-03-31 runway=6.3mo
- **p_rank**: pharmcube drugBaseLiteCN lead=EYP-1901(Duravyu) target=VEGFR/PDGFR缓释(tyrosine kinase) phase=III期 quality=HIGH retrieved=2026-07-09

**Sectors**: [[biopharma]], [[us-biotech-screening]]

## Related pages

- [[us-biotech-v5.2-screening-2026-07-10]]
- [[biopharma]]

---

## 最新季度数据 (as_of 2026-07-10)

> 轻档(财务快照 + 会议指针,未做深提炼)· SEC EDGAR + minodata · 研究用途,非投资建议

**财务(SEC 10-Q, CIK 1314102, 截至 2026-03-31)**

| 指标 | 值 |
|---|---|
| 现金+投资 | **$222.5M** (现金 $77.7M + 短投 $144.8M) |
| 季度 R&D | $72.1M |
| 季度收入 | $0.7M |
| 季度净利 | $-84.8M |
| 季度 OCF | $-80.5M |
| Runway | ~8 个月 |

**会议指针(minodata,未提炼)**:最新业绩会 **2026-05-06**(ipid 360369588) · 最新大会 2026-06-09(ipid 360374753)

**来源**:SEC CIK 1314102 · minodata · 截至 2026-07-10
