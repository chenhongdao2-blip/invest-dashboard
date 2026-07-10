> 📋 **Public sanitized view** — CMSI 内部 Rating / TP / 研报源文件引用 / 分析师姓名已删除。完整内部 view 需在本地 ~/Documents/LLM Wiki/Wiki/ 下访问。
> Sanitized at: 2026-07-10 via jobs/export_wiki_public.py.

# Edgewise Therapeutics (EWTX)

> **US Biotech v5.2 筛选快照** · as_of 2026-07-10 · Line B Venture (1–30B) · 招商证券(香港) AI 投研 · 评分为研究工具，不构成投资建议

**Tier**: Top | **Final Score**: 7.388 | **Rank**: #17 | **Mcap**: $4.98B | **进 book**: 是

**TA / Modality**: 神经肌肉/心肌病 / 口服小分子(肌球蛋白myosin调节)
**Lead asset**: sevasemten(EDG-5506)
**Indication / Phase**: Becker型肌营养不良(BMD) / II期(GRAND CANYON) (FIC)

**Variant perception（引擎 thesis，非本人结论）**: 共识看好myosin平台(BMS mavacamten验证靶点)+BMD zero-comp GRAND CANYON Ph3将读出;基本面强。但dossier现金口径异常(1.6mo vs $5B市值),若属实则临近融资摊薄——大概率是probe未纳最新增发,需人工核SEC。催化:GRAND CANYON BMD数据(~9月,vol 1.3x)。结论:资产优质但F维数据存疑,晋级前须核现金。

---

## 评分拆解（v5.2-RFC: 0.40P + 0.25E + 0.10F + 0.20M + 0.025(10-R)）

| 维度 | 分 | 关键子项 / 理由 |
|---|---|---|
| **P** 管线稀缺 (0.40) | **8** | base 6.5 + rank_mod 1.5 · BMD无获批DMT,sevasemten独家zero-comp |
| **E** 商业价值 (0.25) | **4.95** | E1 5.5(DOMAIN_EST) / E2 5.5 / E3 0, conf LOW |
| **F** 现金 (0.10) | **8** | runway 1.6 mo · SEC 10-Q显示现金仅3320万/runway 1.6mo CRITICAL,与$5B市值严重背离,疑probe口径异常[RUNWAY_TIGHT] |
| **M** 并购吸引 (0.20) | **10** | base 8 × bd_coef 1.5 + MNC hits 2 · 肌肉myosin稀缺平台(BMS mavacamten已验证HCM靶点),BMD+HCM双资产,并购高发HIGH(8×1.5+0.5→clip10) |
| **R** 风险 (逆权 0.025) | **4** | Ph3 fails 0 · 早期Ph2资产+现金口径存疑(若1.6mo属实则融资/摊薄风险陡增),无Ph3失败 |
| **MSO** | NaN | DATA_MISSING, weight_sum=0.975 (INV-V4) |

> ⚠️ **P 置信度 flag**: `NEEDS_ANALYST_TA_SPECIFIC` — BMD罕见病依赖CK/生物标志物surrogate+功能终点(NSAA),非标准,需TA分析师

> ⚠️ **NEEDS_ANALYST**: BMD无DMT,疗效判读依赖CK下降+NSAA功能终点surrogate,非标准endpoint

## 催化剂 / 时点

- **CT.gov PCD**: 2026-09（30–120d 催化剂窗口）
- **presentation_type**: data_readout

## 数据来源 / provenance

- **lead_asset**: ctgov_probe NCT=NCT05291091 pcd=2026-09 retrieved=2026-07-09
- **gate0**: orange_book_probe verdict=EMERGING nda={'nda': 0, 'bla': 0, 'total': 0} ipo=None retrieved=2026-07-09
- **runway**: edgartools 10-Q 2026-03-31: cash 33.2M + MarketableSecurities 466.4M = 499.6M / burn~20.6M/mo → ~24mo (probe漏MarketableSecurities标签) retrieved=2026-07-10
- **p_rank**: pharmcube drugBaseLiteCN lead=sevasemten(EDG-5506)/EDG-7500 target=肌球蛋白myosin调节 phase=II期 quality=HIGH retrieved=2026-07-09

**Sectors**: [[biopharma]], [[us-biotech-screening]]

## Related pages

- [[us-biotech-v5.2-screening-2026-07-10]]
- [[biopharma]]

---

## 最新季度数据 (as_of 2026-07-10)

> 数据抓取 2026-07-10 · SEC EDGAR + minodata 海外纪要 · 研究用途,非投资建议

**财务(SEC 10-Q, CIK 1710072, 截至 2026-03-31)**

| 指标 | 值 |
|---|---|
| 现金+投资 | **$33.2M** (现金 $33.2M + 短投 —) |
| 季度 R&D | $42.7M |
| 季度收入 | $0（临床前/无产品收入） |
| 季度净利 | $-49.0M |
| 季度 OCF | $-42.5M |
| Runway | ~2 个月 |

**业绩会要点(minodata 2026-06-16)**

1. 重大事件:与 Servier 达成协议出售 sevasemten+肌营养不良平台,现金注入 $15.5亿+里程碑至 $11亿,Q3 完成;转型为纯心血管公司
2. EDG-7500(HCM 心肌肌小节调节剂)II 期 CIRRUS-HCM D 部分 12 周 topline(本次会议主题)
3. sevasemten Becker 肌营养不良 III 期 Q4 读出;EDG-15400(心衰)I 期,Q3 推进 II 期

**来源**:SEC CIK 1710072 · minodata ipid 360377465(业绩会 2026-06-16) · 截至 2026-07-10
