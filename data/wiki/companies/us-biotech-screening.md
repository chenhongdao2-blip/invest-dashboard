> 📋 **Public sanitized view** — CMSI 内部 Rating / TP / 研报源文件引用 / 分析师姓名已删除。完整内部 view 需在本地 ~/Documents/LLM Wiki/Wiki/ 下访问。
> Sanitized at: 2026-07-10 via jobs/export_wiki_public.py.

# US Biotech Screening（催化剂驱动选股体系）

**Summary**: 招商证券(香港) AI 投研的美股 biotech 催化剂选股体系(v5.2-RFC)。双产品线——Line A 大盘 Long-only(≥30B)/ Line B 中小盘 Venture(1–30B);以 30–120 天临床催化剂为闸,经 Gate0 研发履历 + 机构门槛 + P·E·F·M·R 五维评分,输出 tear sheet 并接 ic-foundry 做回测/后测。本页为该体系在 wiki 的**索引/落地页**,汇集各期筛选快照与被覆盖标的。

**评分为研究工具,不构成投资建议。**

## 方法论(v5.2-RFC 公式)

```
Final Score = 0.40×P + 0.25×E + 0.10×F + 0.20×M + 0.025×(10−R) + 0.025×MSO
  P 管线稀缺(base + rank_modifier)   E 商业价值(peak sales/管线/rel_anchor)
  F 现金/runway                       M 并购吸引(bd_predictability × MNC overlap)
  R 风险(Ph3 失败史时间衰减)          MSO 市场信号(暂 NaN, weight_sum=0.975)
Tier: Elite≥8.0 / Top≥7.0 / Watch≥5.5 / Rest<5.5
```

数据源:universe 6 源 union(stockanalysis/IBB/XBI/ARKG/finviz/CT.gov)· 催化剂 clinical-trials MCP · P_rank pharmcube · 财务 SEC EDGAR · 电话会/大会 minodata。

## 各期筛选快照

- [[us-biotech-v5.2-screening-2026-07-10]] — **v5.2-RFC Line B fresh run(2026-07-10)**,50 家结构化评分 + 2 家 triage(DNLI/MLYS),全 52 家公司页索引

## 数据口径

- 每家公司页含 `## 最新季度数据` 节:SEC Q1'26 财务(ground truth)+ minodata 电话会/大会要点
- IMCR 等 minodata call stale 的标 `⚠STALE`,财务仍用 SEC 最新
- 港股同类标的走 gangtise(半年报制,最新=FY 年报),见 [[09926-akeso]] 等

## Related

- [[biopharma]]
- 完整 skill / runbook:`~/.claude/skills/us-biotech/`;原始产物:`RAW/us-biotech-screening-v5/`

**Last updated**: 2026-07-10
