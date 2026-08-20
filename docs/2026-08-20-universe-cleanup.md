# Universe 清理清单 — 2026-08-20

**范围**：`config/universes/*.yml` 全量 483 只（US 288 / JP 70 / HK 58 / CN 47 / KR 20）
**方法**：与现用行情源逐只比对，筛出标的失效、实体错配、重复计数三类问题

> ⚠️ 除 C 类外，本清单**未自动执行**。请逐条核对后再改 config。
> 退市/收购属可核实的公开事实，动手前**请以 SEC EDGAR（Form 25 / 15-12G）为准**。

---

## A. 已退市 / 被收购 —— 13 只（建议标记 delisted）

全部位于 `config/universes/hc_biotech.yml`，除 SEM 在 `hc_hospital_care.yml`。
以下标的在交叉比对中**不再返回可交易行情**，疑为已退市或完成收购：

| 行号 | ticker | 公司 |
|---|---|---|
| hc_biotech.yml:94 | `KALV` | KalVista Pharmaceuticals |
| hc_biotech.yml:114 | `CPRX` | Catalyst Pharmaceuticals |
| hc_biotech.yml:294 | `SLNO` | Soleno Therapeutics |
| hc_biotech.yml:299 | `CNTA` | Centessa Pharmaceuticals |
| hc_biotech.yml:304 | `TERN` | Terns Pharmaceuticals |
| hc_biotech.yml:314 | `DAWN` | Day One Biopharmaceuticals |
| hc_biotech.yml:319 | `APLS` | Apellis Pharmaceuticals |
| hc_biotech.yml:324 | `FOLD` | Amicus Therapeutics |
| hc_biotech.yml:334 | `ACLX` | Arcellx |
| hc_biotech.yml:449 | `NUVL` | Nuvalent |
| hc_biotech.yml:834 | `RAPT` | RAPT Therapeutics |
| hc_biotech.yml:844 | `VTYX` | Ventyx Biosciences |
| hc_hospital_care.yml:27 | `SEM` | Select Medical Holdings |

⚠️ **上表为待核实线索，不是已确认结论**。每只须经 SEC EDGAR 终核后再改 config。

### 为什么必须处理

现用数据源是 yfinance。repo 自己的 `dashboard/README.md` 记着这个坑：
> 退市标的的 `price_return_*` 由冻结价算出，会把僵尸股呈现为「低波动稳步上涨」。

→ 这些标的很可能正以冻结价躺在看板里，且会在**低波动 / 稳健上涨类排序中排到前面**。
行情源对已退市标的返 null 是正确行为，yfinance 不会告诉你。

**建议**：不直接删行，加 `status: delisted` 字段并在 loader 过滤，保留历史序列可回溯。

---

## B. 同一公司两个 ticker —— 1 组（重复计数）

| 行号 | ticker | 实际实体 |
|---|---|---|
| hc_biotech.yml:404 | `DMRA` | **Damora Therapeutics, Inc.** |
| hc_biotech.yml:839 | `GLTO` | **Damora Therapeutics, Inc.**（同一家；Galecto 更名）|

两行指向同一家公司 → 任何计数、等权重、行业汇总都会**把它算两次**。

**建议**：保留 `DMRA`（新代码），删除或标记 `GLTO` 为 renamed。

---

## C. ticker 与名称错配 —— ✅ **已于 2026-08-20 修复**

| 行号 | 原状 |
|---|---|
| `ai_equip.yml:122` | `ticker: 078000.KQ` / `name_cn: Leeno工业` |

`078000.KQ` 与 Leeno Industrial（리노공업，半导体测试探针 / test socket 厂商）无关。

**这是本轮唯一一条正在污染数据、且完全不可见的错误**：yfinance 对 `078000.KQ`
返回 longName 缺失、shortName 为代码串（`078000.KQ,0P0000CKV8,1567`）的畸形对象，
**但仍有价格**（10,640），因此下游一切照跑，看板上看不出任何异常。

### 修复内容

正确代码 **`058470.KQ`**，双源独立确认：

| 源 | `078000.KQ` | `058470.KQ` |
|---|---|---|
| drillr（KR 覆盖） | 无任何数据 | 리노공업，最新交易日 2026-08-20 |
| yfinance `.info` | shortName 为代码串，longName 为空 | `LEENO Industrial Inc.` |

`ai_equip.yml:122` 已改为 `058470.KQ`，note 同步记录来由。
YAML 校验通过（38 只，无重复）。→ PR #42

**已澄清（原记录有误，2026-08-20 当日更正）**：本文档初稿曾称 drillr 与 yfinance
对 `058470.KQ` 的 2026-08-20 收盘价相差 18%（81,700 vs 69,000），据此列为「遗留待查」。
**该差异不存在。** 起因是初次查询写成 `MAX(close) AS last_close`，取到的是 7 月以来的
区间最高价 81,700，却按「最新收盘」解读。逐日比对显示两源一致：

| 日期 | drillr | yfinance |
|---|---|---|
| 2026-08-13 | 71,300 | 71,300 |
| 2026-08-14 | 70,800 | 70,800 |
| 2026-08-18 | 67,800 | 67,800 |
| 2026-08-19 | 67,900 | 67,900 |
| 2026-08-20 | 69,500 | 69,000 |

KR 腿无需口径对齐工作。教训：聚合函数的结果不要起一个非聚合的变量名。

---

## D. A+H 双重上市 —— 4 组（市值聚合会重复计数）

同一 universe 文件内同时收录 A 股与 H 股：

| 公司 | H 股 | A 股 | 文件 |
|---|---|---|---|
| 药明康德 | 2359.HK | 603259.SS | hc_cxo.yml |
| 泰格医药 | 3347.HK | 300347.SZ | hc_cxo.yml |
| 康龙化成 | 3759.HK | 300759.SZ | hc_cxo.yml |
| 凯莱英 | 6821.HK | 002821.SZ | hc_cxo.yml |

**如果只做行情/涨跌幅展示，这是合理的**（A/H 溢价本身有信息量）。

**已核实（2026-08-20，原归因有误）**：本文档初稿称「市值聚合会 4 倍计数」。
代码里**不存在**对本板块的市值加权聚合——板块汇总（`lib/heat_table.py`）与组合
净值（`lib/portfolio_math.py`）全部走**等权**；唯一的市值加权是日本医药专栏指数，
它走独立的 `hc_japan.yml`，且日本无 A+H 对。

但危害确实存在，机制是另一个：4 组的两条腿**全部落在同一个 `(healthcare, cxo)`**。
该板块 28 个活跃成分，等权下每只应占 1/28 = 3.57%，这 4 家各得 **7.14%（2 倍）**，
合计吃掉 **28.6%** 的权重——而板块里实际只有 24 家不同公司。

**建议**：加 `secondary_listing` 标记（**不能复用 `status`**——status 会把标的
逐出板块展示，而 A/H 两条腿都应当可见）。仅在等权聚合处排除次要腿，明细表保留两条。
**前置决策**：每组以哪条腿为主尚未确定，该选择会直接改变板块收益读数。

---

## E. 跨文件重复 —— 8 只（可能是设计如此）

同一 ticker 出现在多个 sector 文件里：

```
ISRG   hc_medtech + hc_ai + cmsi_coverage_hc   （3 个文件）
BSX    hc_medtech + cmsi_coverage_hc
ONC    hc_biotech + cmsi_coverage_hc           （百济神州）
IQV    hc_ai + hc_cxo
TMO    hc_cxo + cmsi_coverage_hc
2359.HK  hc_cxo + cmsi_coverage_hc
2269.HK  hc_cxo + cmsi_coverage_hc
2506.HK  hc_ai + cmsi_coverage_hc
```

**这大概率是有意的**（一只股票属于多个 sector 视图），去重后总数 483 说明 loader 已处理。
**仅在做全池汇总时需确认去重逻辑生效。** 不需要改 config。

---

## 汇总

| 类别 | 数量 | 处理优先级 | 状态 |
|---|---|---|---|
| **C. ticker/名称错配** | 1 | 🔴 **最高**——正在污染数据且不可见 | ✅ 已修复 |
| **A. 已退市/被收购** | 13 | 🔴 高——僵尸行会污染排序 | 待核实后处理 |
| **B. 同公司双 ticker** | 1 组 | 🟡 中——重复计数 | 未处理 |
| **D. A+H 双上市** | 4 组 | 🟡 中——仅影响市值聚合 | 未处理 |
| **E. 跨文件重复** | 8 | ⚪ 可能无需处理 | 无需处理 |

**清理后有效标的数**：483 − 13（退市）− 1（GLTO 重复）= **469**
