> 📋 **Public sanitized view** — CMSI 内部 Rating / TP / 研报源文件引用 / 分析师姓名已删除。完整内部 view 需在本地 ~/Documents/LLM Wiki/Wiki/ 下访问。
> Sanitized at: 2026-07-10 via jobs/export_wiki_public.py.

# Scholar Rock (SRRK)

> **US Biotech v5.2 筛选快照** · as_of 2026-07-10 · Line B Venture (1–30B) · 招商证券(香港) AI 投研 · 评分为研究工具，不构成投资建议

**Tier**: Top | **Final Score**: 7.925 | **Rank**: #11 | **Mcap**: $6.71B | **进 book**: 是

**TA / Modality**: 神经肌肉/SMA+肥胖 / 选择性anti-myostatin抗体
**Lead asset**: apitegromab(SRK-015)
**Indication / Phase**: 脊髓性肌萎缩SMA附加治疗 / 申请上市 (FIC)

**Variant perception（引擎 thesis，非本人结论）**: 共识只给SMA附加治疗定价;真正期权在SRK-439与GLP-1联用的肌肉保留赛道——肥胖减重伴随肌肉流失是LLY/NVS的核心痛点,anti-myostatin是最直接解法。runway偏紧是短板,但也放大被并购概率。myostatin平台稀缺性支撑高M。

---

## 评分拆解（v5.2-RFC: 0.40P + 0.25E + 0.10F + 0.20M + 0.025(10-R)）

| 维度 | 分 | 关键子项 / 理由 |
|---|---|---|
| **P** 管线稀缺 (0.40) | **9.5** | base 8.5 + rank_mod 1 · 选择性myostatin抑制Top1(叠加0) |
| **E** 商业价值 (0.25) | **6.3** | E1 7.5(DOMAIN_EST) / E2 6 / E3 0, conf MEDIUM |
| **F** 现金 (0.10) | **4** | runway 10.6 mo · 现金4.8亿/10.6mo,商业化爬坡期偏紧[RUNWAY_TIGHT] |
| **M** 并购吸引 (0.20) | **10** | base 8 × bd_coef 1.5 + MNC hits 3 · SRK-439肥胖肌肉保留+GLP-1联用契合LLY/NVS代谢管线,并购预测性高 |
| **R** 风险 (逆权 0.025) | **4** | Ph3 fails 0 · 单产品SMA依赖+runway<12mo需融资,肥胖资产尚早 |
| **MSO** | NaN | DATA_MISSING, weight_sum=0.975 (INV-V4) |

> ⚠️ **P 置信度 flag**: `NEEDS_ANALYST` — SMA附加疗效surrogate+肥胖肌肉保留赛道拥挤度演化中

> ⚠️ **NEEDS_ANALYST**: SMA附加疗效终点+肥胖肌肉保留竞争演化需分析师判读

## 催化剂 / 时点

- **CT.gov PCD**: 2026-11-01（30–120d 催化剂窗口）
- **presentation_type**: readout

## 数据来源 / provenance

- **lead_asset**: ctgov_probe NCT=NCT05626855 pcd=2026-11-01 retrieved=2026-07-09
- **gate0**: orange_book_probe verdict=EMERGING nda={'nda': 0, 'bla': 0, 'total': 0} ipo=None retrieved=2026-07-09
- **runway**: sec_10q_probe accession=00 as_of=2026-03-31 runway=10.6mo
- **p_rank**: pharmcube drugBaseLiteCN lead=apitegromab(SRK-015) target=肌肉生长抑制素myostatin phase=申请上市 quality=HIGH retrieved=2026-07-09

**Sectors**: [[biopharma]], [[us-biotech-screening]]

## Related pages

- [[us-biotech-v5.2-screening-2026-07-10]]
- [[biopharma]]

---

## 最新季度数据 (as_of 2026-07-10)

> 数据抓取 2026-07-10 · SEC EDGAR + minodata 海外纪要 · 研究用途,非投资建议

**财务(SEC 10-Q, CIK 1727196, 截至 2026-03-31)**

| 指标 | 值 |
|---|---|
| 现金+投资 | **$479.9M** (现金 $430.5M + 短投 $49.4M) |
| 季度 R&D | $51.8M |
| 季度收入 | $0.0M |
| 季度净利 | $-105.5M |
| 季度 OCF | $-82.1M |
| Runway | ~18 个月 |

**业绩会要点(minodata 2026-05-07)**

1. apitegromab(SMA)BLA 获 FDA 受理,PDUFA 9-30;覆盖两灌装厂(Catalent Indiana+第二厂)双获批路径
2. Catalent 印第安纳厂受理后遭 FDA 突击复查(符合预期),FDA 有 90 天分类;第二厂全部药品已递,Q3 初充足商业供应(早于 PDUFA)
3. 去年 CRL 唯一问题系 Novo 拥有的 Catalent 厂常规检查发现,非药品本身

**来源**:SEC CIK 1727196 · minodata ipid 360367704(业绩会 2026-05-07) · 截至 2026-07-10
