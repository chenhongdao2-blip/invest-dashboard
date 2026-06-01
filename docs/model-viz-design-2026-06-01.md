---
title: 分析师模型→公司财务可视化页 整体设计
date: 2026-06-01
method: Workflow wf_a4271dec-585 (financial-strategist + designer + architect → synthesis, 4 agents/323k tok)
status: DESIGN — 待 George 审定 MVP 范围
---

# 分析师模型 → 公司财务可视化层｜整体设计方案（合成定稿）

> 三路 advisor 在核心上高度一致（统一 ModelView schema、actual/forecast 锚定、三色诚实标注、复用 wiki+深链）。唯一实质分歧在**「扩 Ticker Drill 内 tabs」 vs 「新建独立页」**——下方第 3 节给终裁。本方案标注每条结论的证据等级：**[已验证]** = VEEV 文件 cell 级实测；**[假设待验]** = 需 ISRG/TMO 第二个模型才能证伪。

---

## 1. 愿景（一句话）

**点击任一覆盖公司，打开该公司的「分析师工作底稿」视图——把分析师手搭 Excel 里的收入自下而上拆解（客户×ARPU）、GAAP/非GAAP 利润率桥、多年预测与 DCF 敏感性，连同 LLM Wiki thesis，渲染成 CMSI house 风格的诚实可视化（实际=实线、预测=半透明虚线、三色标注数据可信层级），补足现有 SEC GAAP 页「拆解不够细」的根本缺口。**

---

## 2. 整体架构

### 2.1 数据管道（模型 → JSON → 页面）

```
分析师在 Excel/LibreOffice "打开并保存" 模型  ← 硬前提: 写入公式缓存值
        │
        ▼
jobs/extract_model.py --ticker VEEV --xlsx <path>     (复用 extract_dcf.py:1063 骨架)
   ├─ openpyxl.load_workbook(data_only=True)           [已验证] 不可省:单元格 99% 是跨sheet公式
   │     └─ 检测 cached=None 占比 >20% → fail + 提示"请在Excel打开并保存"
   ├─ N_code 自动填三表 (Incomestatement_IS 等)        [已验证] N_5977340=Total revenue
   ├─ 按 config/models/VEEV.yml 覆盖 分部/驱动/margins/DCF/情景
   └─ validate(periods 对齐 / units 单源 / 必填字段) → 失败则不产出错数据
        │
        ▼
data/models/VEEV.json   ── git commit ──▶  (保密见 §6: MVP 不进公开仓库)
        │
        ▼
app/lib/model_view.py  load_model(ticker) / has_model(ticker)   (cache_data 按 ticker 显式 key)
        │
        ▼
页面渲染: 收入拆解 / 利润率+桥 / 预测+DCF敏感性 + wiki memo
```

**关键约束 [已验证]**：VEEV 模型几乎所有单元格是 `='VEEV US'!B4` 跨 sheet 公式，**必须 `data_only=True` 读缓存值**；缓存值仅在 Excel/LibreOffice 保存时写入。抽取器须统计 `None` 比例并在超阈值时 fail，不静默产出空 JSON。

### 2.2 统一 Financial Schema（定稿）

采用 architect 的 JSON 结构（最完整、含 coverage/confidence/units 单源声明），与 designer 的 `ModelView` 语义对齐。定稿字段：

```jsonc
{
  "meta": {
    "ticker":"VEEV","market":"US","company":"VEEVA SYSTEMS INC",
    "currency":"USD","units":"millions","fiscal_year_end":"January 31",
    "model_version":"Mar2026","as_of":"2024-10-28",
    "source":"CMSI analyst model + Visible Alpha","source_file":"VEEV US Mar2026.xlsx",
    "analyst":"<name>","extracted_at":"...",
    "coverage":"full",        // full | partial(三表only) | llm_low
    "confidence":"high",      // high | medium | llm_low
    "sector":"saas"           // 路由行业 plugin; 复用项目 domain 分层, 不 hardcode 医疗
  },
  "periods":[                 // 时间轴单源, 所有数组按此对齐; actual/forecast 在此维度统一标
    {"label":"FY25","kind":"annual","actual_est":"A"},
    {"label":"FY26E","kind":"annual","actual_est":"E"}   // ← 第一个 E = 全局渲染分界锚 [已验证]
  ],
  "revenue_breakdown":[       // (a) 双轴: basis(订阅/服务) + segment(Commercial/R&D) + drivers
    {"segment":"Commercial Solutions","segment_cn":"商业化解决方案","basis":"subscription",
     "values":{...},"yoy":{...},
     "drivers":{"customers_end":{...},"net_adds":{...},
                "products_per_customer":{...},"rev_per_product":{...}}}
  ],
  "margins":[                 // (b) 每行显式 basis: gaap|non_gaap
    {"metric":"operating_margin","metric_cn":"营业利润率","basis":"non_gaap",
     "values":{...},"estimate":{...},"var_bps":{...}}   // Beat_Miss: Actual/CMSI Est./Var
  ],
  "gaap_bridge":[             // GAAP→非GAAP 桥 (Beat_Miss)
    {"item":"GAAP Operating Income","item_cn":"GAAP营业利润","values":{"4Q26":245.88}},
    {"item":"(+) Stock-Based Comp","item_cn":"股权激励","values":{"4Q26":118.26}}
  ],
  "forecast":[                // (c) FYxxE
    {"line":"revenue","line_cn":"营业收入","basis":"gaap","values":{...}},
    {"line":"eps","line_cn":"每股收益","basis":"non_gaap","values":{...}}
  ],
  "dcf":{
    "wacc":0.0849,"terminal_growth":0.035,"target_price":352.66,
    "current_price":225.0,"ev":51309.24,
    "sensitivity":{"axis_x":"terminal_growth","axis_y":"wacc","x":[...],"y":[...],"grid":[[...]]},
    "scenarios_note_cn":"方案A 维持TG3.5%≈$352 / 方案B TG3.0%≈$330"
  }
}
```

设计要点：`actual_est` 在 **period 维度**统一标（不在每个数字重复标）；`basis` 显式标在每行（VEEV 两套并存）；`coverage/confidence` 驱动页面降级；`sector` 路由行业 plugin。

### 2.3 异构模型映射——最终推荐：分层映射

**[已验证]** 难点是真的、且是双层的：分析师手工层（Summary/Driver/Beat_Miss，语义丰富但布局随人漂移）+ 数据商结构化层（N_code feed，跨模型口径稳定但只有三表）。GBM 模型（`CMS 1/Valuation 2/Financials`）与 VEEV 布局完全不同——**实证异构。**

**终裁 = (i) per-model YAML config 为主 + (iii) N_code 自动兜底 + (iv) LLM 仅 flag-not-fact：**

1. 每 ticker 一份 `config/models/<TICKER>.yml`，声明 sheet/行列 → schema 字段映射。VEEV 直接从已存在的 `~/financial-models/_templates/model_schema.json` 转。
2. 抽取器先按 N_code 自动填三表（稳定层），再按 YAML 覆盖分部/驱动/DCF/情景（语义层）。
3. 无 config 的新模型 → 跑 N_code-only + 标 `coverage:"partial"`，页面显示「仅三表，无分部拆解」。**绝不让 LLM 静默猜数字**；若用 LLM 兜底，产物必带 `confidence:"llm_low"` + 人工复核 gate。

**收入驱动按 sector 走行业 plugin [假设待验]**：SaaS=客户×产品×ARPU；器械(ISRG)=装机×手术量×耗材ARPU；药=品种×价格×渗透。通用核心 5-6 张图所有公司共用，plugin 只负责 L2「收入怎么来」那一层。

> **诚实声明**：n=1。「per-model config 主方案」与「通用核心+行业 plugin」泛化能力**仅在 VEEV 上验证**。GBM 布局异构已确认存在，但映射方案能否优雅覆盖**尚未实测**——这是 P1 ISRG/TMO 的核心验收目标。

---

## 3. 页面与交互（定稿）

### 3.1 放哪——终裁：**新建独立页 `7_Model_Drill.py`**

> **这是三路 advisor 唯一实质分歧**：designer 主张「6_Ticker_Drill 内部 st.tabs（叙事/模型/SEC 三 tab）」；architect 主张「新建独立页，双向深链」。

**终裁取 architect 方案（新页），但吸收 designer 的 tab 内容契约思想。** 理由：

| 维度 | 判断 |
|---|---|
| 现状负载 | 6_Ticker_Drill 已 742 行（KPI strip+Variant+wiki+RS+SEC trends+yfinance），再灌 4 块模型图+DCF 会爆，违反「不做无限下拉页」 |
| 覆盖率不对称 | 模型只覆盖极少数 ticker；Ticker Drill 是全 universe 通用页。tabs 方案会让**无模型公司也带一个动态消失的 tab**，逻辑分支侵入通用页 |
| 数据保密粒度 | 模型 JSON 含 TP/盈利预测（§6），独立页便于整页 gating（公开 Cloud 不挂载该页 / 该页降级），tabs 方案保密边界穿透进通用页 |
| 深链清晰 | `7_Model_Drill?ticker=X` 语义干净；6 页检测 `has_model()` 显示「📊 分析师模型」按钮跳转，7 页顶部放回链 |

**但采纳 designer 的去重铁律**（这是分歧里 designer 最有价值的贡献）：
- **SEC Facts 页** = 公司官方申报（HIGH，可直引，事实锚）。
- **Model Drill 页** = 分析师非GAAP 拆解 + forecast（分析师 view，须标注）。
- 同口径数字（如营收）在 Model 页旁标 **`vs 公司申报 +0.3%`** 对账线——把分析师模型与监管事实摆在一起对账，是这套系统的稀缺价值。（MVP 可后置，P1 落地。）

### 3.2 三块可视化——最终图表选型

**(a) 收入拆解** — 分部堆叠面积（季度时序）+ actual｜forecast 竖线分界 + 右侧占比/增速侧栏。
- 分部 Commercial(teal `#0d7680`)/R&D(`#a07a2c`)，订阅 vs 服务用**同色深浅**（不引第三色族，避免彩虹 slop）。
- L2 驱动层（模型真正的 alpha，必画）：客户数双轴柱+净增 overlay、ARPU/产品数线，**订阅收入瀑布**（上年订阅 →+净增客户 →+ARPU →+渗透 → 本年订阅）。这是 SEC GAAP 页永远给不出的层。
- 默认聚合到 FY（81 列季度会糊），提供「展开季度」toggle。

**(b) 利润率** — 双层：上半利润率多线（GAAP 墨色虚线 / 非GAAP teal 实线，**虚实+色相双编码，色盲可读**）；下半**最新 actual 季 GAAP→非GAAP 桥水平瀑布**（+SBC/+购买摊销/+诉讼和解）。
- **桥是核心差异点**：VEEV 4Q26 SBC≈118M vs GAAP OI≈246M，SBC 压掉约 1/3 利润——这张图本身就是相对 SEC 页的增量 alpha。
- 桥用**中性灰**，不上 teal/red——会计调整不是市场涨跌。
- 加费用率结构（R&D%/S&M%/G&A% 非GAAP）看经营杠杆。
- Beat/Miss 面板：Actual vs **CMSI Est.** vs Var，bps 偏差色块。**标清「招商自有预测，非共识」**。

**(c) 预测 + DCF** — 预测柱（actual/estimate 分色）+ EPS 折线叠加；**DCF 卡做成「假设面板」**（WACC/TG/隐含 EV/Sales 与 TP 并列，逼出推导，反 slop）；WACC×TG 敏感性热力图。
- 默认展示 **FY26E–FY30E（5 年）**，完整 9 年折叠在「展开长期」toggle（5 年是 sell-side memo 标准视野，9 年全给稀释可信度）。
- **敏感性网格用单色 sequential teal ramp（深=TP 高）+ ◆ 标基准格**——这是「假设→TP」网格不是市场涨跌，**不锁 teal涨/red跌**（避开 A 股红绿误读叠加会计误读）。基准 TP≈$352 高亮。
- 分析师**中文情景注释**（方案A/B）作为图注**原文直出不翻译**——手搭模型独有、AI 编不出的人类判断。

### 3.3 与 wiki / SEC Facts 分工
- **wiki**：Model 页顶调 `wiki.find_wiki(ticker)` 复用 memo（6_Ticker_Drill.py:393-449 段抽成 lib 共用）。模型给数字，wiki 给 thesis。
- **SEC Facts**：监管 GAAP 事实锚；Model 页对账线引用（P1）。
- **深链与 fallback**：`7_Model_Drill?ticker=X`；`has_model()` False → 不空白，显示「该公司暂无分析师模型，见 个股详情/SEC 数据」+ 跳 6 页。某 block 字段缺失 → 整块隐藏，**绝不画空轴**。

---

## 4. 金融内容定稿——三类数据标注规则

| 数据类 | 来源 sheet | 可靠性 | 视觉 | 能否裸展示 |
|---|---|---|---|---|
| GAAP 财报实际 | actual 列 FY≤FY25 / SEC | **HIGH** | 实线实心，无水印，teal chip「GAAP 申报」 | ✅ 标「来源:财报+截至」 |
| 分析师模型 view | Summary/Driver/Beat_Miss/Valuation | **MEDIUM** | 主色 + amber chip「分析师 view」 | ⚠️ 须标「招商模型预测」 |
| VA 共识 feed | N_code item sheets | **LOW-MED** | 灰调 + 蓝 chip「卖方共识(VA)」 | ⚠️ 须标「卖方一致预期」 |
| forecast 任意来源 | 含 "E" 列 | 降级 | 虚线/半透明 + hover「估」+ 竖线分界 | ❌ 绝不裸展示 |

**硬规则**：① 任何 FYxxE/TP/margin forecast 卡角带「分析师预测」badge；② DCF TP 永远与 sensitivity 网格同屏，不单独甩数字；③ Beat_Miss「CMSI Est.」标「招商自有预测，≠ 共识」；④ 每图脚注 `来源: 分析师模型 {file}, 截至 {model_date}`，>90 天标「待更新」。

**MVP 具体图表+字段清单（VEEV，5 section + wiki）**：

| # | Section | 图 | 字段 (sheet!行) [已验证] |
|---|---|---|---|
| 0 | Header | rating/TP 卡 + 时间戳 +「TP $352/现价/+57%」 | wiki.py + Sensitivity D8/D9 |
| 1a | 收入总览 | Sub/Prof 堆叠柱 + Y/Y 三线 | Summary r16/17/22, r12-14 |
| 1b | 分部拆解 | Commercial vs R&D 堆叠 + 增速 | Driver r25 + R&D 段 |
| 1c | 驱动因子 | 客户数双柱+净增；ARPU/产品线；**订阅瀑布** | Driver r3-13/r29-39 |
| 2a | 利润率三联 | 毛/营/净，每条 GAAP灰+非GAAP主色 | Summary r59-62, Beat_Miss r28/32/34 |
| 2b | 费用率 | R&D%/S&M%/G&A% 面积 | Beat_Miss r29-31 |
| 2c | **GAAP→非GAAP 桥** | 水平瀑布 (4Q26) | Beat_Miss r38-41 |
| 2d | Beat/Miss | 表 + bps 色块 | Beat_Miss r5-34 |
| 3a | 预测面板 | 收入/营利/净利/EPS/FCF FY26E-30E 卡 | Summary r22/41/43/44/35 |
| 3b | DCF 假设卡 | WACC/TG/TP/现价/EV | Sensitivity D6-10 |
| 3c | 敏感性热力图 | WACC×TG → TP，基准高亮 | Sensitivity B14:I21 |
| 3d | 情景注释 | 方案A/B 中文 callout | Sensitivity B24+ |
| 4 | LLM Wiki | 公司 wiki 正文 | wiki.find_wiki(VEEV) |

---

## 5. MVP vs 泛化边界

| | 范围 | 状态 |
|---|---|---|
| **P0 MVP** | VEEV 单只；config 已存在；手动跑脚本；新页 7_Model_Drill；5 block+wiki 全图；本地验证；**JSON 不上公开 Cloud** | 数据 [已验证] 可解析 |
| **P1 泛化验证** | ISRG/TMO（同 N_code 口径，结构近似 VEEV）2-3 只；落地 sector plugin；Model vs SEC 对账线 | [假设待验] |
| **P2 异构 + 保密上线** | GBM/300760 等异构布局；LLM flag 兜底；refresh job；公开脱敏双轨上 Cloud | [假设待验] |

**诚实边界**：P0 只证明「单模型可抽可视」；「per-model config + 通用核心+plugin」能否泛化到异构布局，**必须 P1 第二个模型才能证伪/证成**。不要在 P0 完成时宣称泛化方案 work。

---

## 6. 风险与保密

| 风险 | 严重度 | 缓解 |
|---|---|---|
| **TP/分析师模型上公开 Cloud** | **高** | **MVP 阶段 model JSON 不进 public 仓库 / 不上 Cloud**；P2 比照 `wiki.py:36-48` internal-first/public-fallback 双轨：内部全量（gitignore）+ 公开脱敏（去 TP/DCF target，只留历史 actual）。独立页便于整页 gating |
| 公式缓存缺失（未保存过） | 高 | 抽取器统计 None 占比 >20% fail + 提示「Excel 打开并保存」 |
| 源 xlsx 进仓库膨胀 (1.6MB×N) | 中 | **源 xlsx 不进 invest-dashboard 仓库**，留 `~/financial-models/`；只 commit JSON (~50KB) |
| 模型格式漂移 | 中 | YAML config 版本化 + 抽取后 validate；漂移→fail 而非产错数 |
| N_code 口径假设失效（非全模型用 VA） | 中 | 检测 `Data Type/As Of` 元数据头存在才走 N_code，否则纯 config |
| 跨页 cache 碰撞（本项目史） | 中 | load 函数显式 `ticker` 参数 keying，**禁 `_` 前缀**（db.py:16-29） |
| 单位/FX 混乱（GBM=CNY, VEEV=USD） | 中 | `meta.units`+`currency` 单源，按 currency 标注，不跨币聚合 |

---

## 7. 分阶段 Build Plan

**P0 — MVP（VEEV 先行）**
- 交付物：`jobs/extract_model.py`（复用 extract_dcf.py，data_only + None 检测 + N_code + YAML 覆盖 + validate）；`config/models/VEEV.yml`（从 _templates 转）；`data/models/VEEV.json`；`app/lib/model_view.py`（load/has_model，ticker key）；`app/pages/7_Model_Drill.py`；`charts.py` 新增 `revenue_build_area/margin_lines_and_bridge/forecast_bars/dcf_sensitivity_heatmap`（吃 ModelView，全 `theme.PLOTLY_LAYOUT`）；`i18n` 新增 `model.*`（中默）。
- 验收：VEEV JSON None 占比<20%；5 block+wiki 全渲染；actual/forecast 竖线正确（FY26E）；三色 chip 到位；TP 与 sensitivity 同屏；本地 George 眼验「可以 ship」；**JSON 不进公开仓库**。

**P1 — 泛化验证（核心证伪点）**
- 交付物：ISRG/TMO config + JSON；sector plugin 路由（saas/medtech）；通用核心降级（缺字段隐藏不报错）；Model vs SEC 对账线。
- 验收：第二个 N_code 模型用同抽取器跑通；缺 segment 的模型优雅降级；证明「通用核心+plugin」假设成立或暴露需改的点。

**P2 — 异构 + 保密上线**
- 交付物：GBM/A股异构 config（实测映射方案上限）；LLM flag 兜底（confidence:llm_low + 复核 gate）；`jobs/refresh_models.py` 增量重抽；公开脱敏双轨 + 上 Cloud。
- 验收：异构布局成功映射或明确标 partial；脱敏版无 TP/DCF target；Cloud 部署保密合规。

---

## 关键文件 References（绝对路径）
- 样本模型：`/Users/gcc/Downloads/VEEV US Mar2026.xlsx`
- per-model config 起点：`/Users/gcc/financial-models/_templates/model_schema.json`
- 异构实证：`/Users/gcc/financial-models/2661/Project GBM Model_Mar 2026.xlsx`
- 抽取器骨架：`/Users/gcc/.claude/skills/earnings-house/scripts/extract_dcf.py`（:1063 data_only+LABEL_MAPPING+跨sheet rescue）
- 复用入口：`/Users/gcc/invest-dashboard/app/pages/6_Ticker_Drill.py`（:169-175 深链；:233/:620 cache key 坑；:393-449 wiki memo 段可抽 lib）
- 保密双轨模板：`/Users/gcc/invest-dashboard/app/lib/wiki.py`（:36-48 `_wiki_roots`）
- cache 碰撞根因：`/Users/gcc/invest-dashboard/app/lib/db.py`（:16-29）
- flat-file+build-job 模式：`/Users/gcc/invest-dashboard/jobs/export_wiki_public.py` + `data/wiki/companies/*.md`
- 图表/配色/i18n：`/Users/gcc/invest-dashboard/app/lib/charts.py`, `theme.py`, `heatmap.py`, `i18n.py`
- 新建：`app/pages/7_Model_Drill.py`、`app/lib/model_view.py`、`jobs/extract_model.py`、`config/models/VEEV.yml`、`data/models/VEEV.json`

---

# 附录: 三路 advisor 原始设计稿

## A. 金融内容 (financial-strategist)

The data confirms everything. Actual/forecast boundary is clean: **FY26E is the first estimate column** (header literally suffixes "E"; FY19–FY25 are actuals, FY26E onward through FY34E are forecast). Here is the financial content layer design.

---

# 模型可视化层 — 金融内容设计（financial-strategist）

**Tier 声明**: Tier 2（投资分析层）。模型抽取数 = MEDIUM（分析师手算 view）/ Visible Alpha feed = LOW-to-MEDIUM（共识）；二者与 GAAP 财报（HIGH）**分轨标注**，所有 FY26E+ 数字必须带"分析师预测"水印，不裸展示。

核心设计原则：**actual/forecast 边界 = header 带 "E" 后缀的第一列（VEEV = FY26E）**。这是全屏渲染的硬分界线 —— 实线 vs 虚线、实心 vs 半透明、左/右背景分区，全部以此为锚。

---

## 1. 收入拆解 (a) — VEEV 拆解维度

VEEV 的收入有两个正交拆解轴，模型里都齐：

**轴 1 — 收入性质（财报口径）**: Subscription Services Revenue vs Professional Services Revenue
**轴 2 — 业务分部（战略口径）**: Commercial Solutions vs R&D Solutions

二者交叉成 2×2，但分析师 Driver sheet 的真正引擎是 **分部 × (客户数 × 每产品 ARPU)** 自下而上推。这是这个模型的 alpha 所在，必须展示，不能只画一根总收入线。

### 要展示的指标（分三层）

**L0 顶层（一眼看全貌）**
| 指标 | 来源 sheet | actual/forecast |
|---|---|---|
| Reported Revenue 总收入 + Y/Y% | Summary r22 | FY19–FY25 actual｜FY26E+ forecast |
| Subscription vs Professional 占比（堆叠面积/100%柱）| Summary r16/r17 | 同上 |
| Subscription Y/Y% & Professional Y/Y% & Total Y/Y%（三线增速图）| Summary r12-14 | 同上 |

**L1 分部拆解（Commercial vs R&D）**
| 指标 | 来源 | 说明 |
|---|---|---|
| Total Commercial Solutions Rev vs Total R&D Solutions Rev（堆叠）| Driver r25 / 对应 R&D 行 | 战略视角占比 |
| 各分部内部再拆 订阅 vs 服务 | Driver r16/r22（Comm）+ R&D 镜像段 | 2×2 全展开 |
| 各分部 Y/Y% | Driver r17/r23/r26 等 | 看哪个分部驱动增长 |

**L2 驱动因子（这是模型真正的差异化，必须画）**
| 驱动 | Commercial | R&D | 图形 |
|---|---|---|---|
| 期末客户数 Customer Ending | Driver r5 | Driver r31 | 双轴柱 + 净增 overlay |
| 净增客户 Net Addition | Driver r4 | Driver r30 | 季度 bar，看锯齿/平滑 |
| 每客户产品数 Products/Customer | Driver r8 | Driver r34 | 线 |
| 每产品订阅收入 Sub Rev per Product（ARPU 代理）| Driver r13 | Driver r39 | 线 |
| 衍生：客户 Y/Y% | Driver r6/r32 | | |

> **桥式呈现**: 用瀑布图把"上年订阅收入 → ＋净增客户贡献 → ＋ARPU 提升贡献 → ＋产品渗透 → 本年订阅收入"拆开。这正面回应痛点"拆解不够细"—— SEC GAAP 页永远给不出客户×ARPU 这层。

**Actual/forecast 分界**: 单一规则全局复用 —— 渲染时遍历 period header，命中第一个含 "E" 的 FY 列即切样式。actual 段实线/实心；forecast 段虚线/半透明，并在分界处画一条竖直 reference line 标 "Forecast →"。季度数据从 1Q19 起，默认视图聚合到 FY（避免 81 列季度糊成一团），提供"展开季度"toggle。

---

## 2. 利润率 (b) — 正面解决"GAAP 太多、拆解不够"

用户痛点的根因：SEC 页只有 GAAP，而 SaaS 公司的 GAAP 被 SBC（股权激励）严重压低，**非GAAP 才是 sell-side 和 buy-side 实际定价口径**。所以这里的设计哲学是 **非GAAP 为主视图、GAAP 为参照、中间放可审计的桥**。

### 三组利润率（GAAP vs 非GAAP 并列）
| 利润率 | GAAP 来源 | 非GAAP 来源 | 展示 |
|---|---|---|---|
| 毛利率 Gross Margin | — | Beat_Miss r28 | 双线（实=actual虚=forecast）|
| 营业利润率 Operating Margin | Summary r60 | Summary r61 (Non-GAAP OPM) / Beat_Miss r32 | **并列双线，GAAP 灰、非GAAP 主色** |
| 净利率 Net Margin | Summary r62 | Beat_Miss r34 | 同上 |

外加费用率结构（非GAAP，Beat_Miss r29-31）: R&D% / S&M% / G&A% 三条占收入比 —— 看经营杠杆（S&M% 下降 = 规模效应），这是 SaaS 估值的核心叙事。

### GAAP → 非GAAP 桥（必须展示，且是差异化卖点）
Beat_Miss r36-40 已有完整桥。用**水平瀑布图**呈现单季/单年：
```
GAAP Operating Income (r38)
  (+) Stock-Based Compensation (r39)   ← VEEV 4Q26 = 118.3M，占比巨大
  (+) Amort. of Purchased Intangibles (r40)
  (+) Litigation Settlement (诉讼和解)
= Non-GAAP Operating Income (r41/Summary)
```
**为什么必须画**: SBC 118M vs GAAP OI 246M —— SBC 把利润压了三分之一。客户和 IC 看到这张桥才理解"为什么非GAAP OPM 44% 但 GAAP 只有 30 出头"。这一张图本身就是相对 SEC 页的增量 alpha。桥默认显示最近一个 actual 季度（4Q26），可下拉切季。

### Beat/Miss 面板（Tier 2 的 variant 价值）
Beat_Miss sheet 是 "Actual vs CMSI Est. vs Var" 三列结构 —— 这是分析师**自己预测 vs 实际**的偏差表。做成一个紧凑表格 + bps 偏差色块（绿=beat 红=miss），直接服务 earnings 复盘。注意 col 标签是 "CMSI Est."，即招商自有预测，**不是共识**，要标清楚。

---

## 3. 未来预测 (c) — FYxxE

模型预测跨度极长（FY26E–FY34E，9 年），但**展示分层**：

| 展示项 | 默认年限 | 来源 | 理由 |
|---|---|---|---|
| 收入 + 各分部 FYxxE | FY26E–FY30E（5年）| Summary/Driver | 5 年是 sell-side memo 标准视野；9 年全给会稀释可信度 |
| 非GAAP 营业利润 / 净利 / EPS FYxxE | FY26E–FY30E | Summary r41/r43/r44 | EPS 是定价锚 |
| OCF / FCF + FCF/share FYxxE | FY26E–FY30E | Summary r34/r35/r38 | FCF 是 DCF 输入，SaaS 看 FCF margin trend |
| 完整 9 年 | 折叠在"展开长期"toggle | | DCF 需要全程，但默认不堆给客户 |

### DCF 输出 — 纳入，但单独成块、强标注
Sensitivity Analysis sheet 已有干净输出：
- **核心假设卡**: WACC 8.49% / Terminal Growth 3.5% / Target Price $352.66 / Current Price $225 / EV $51.3B（r6-10）
- **敏感性热力网格**: WACC(7%–10%) × TG(2%–4.5%) → TP 矩阵（r14-21），用热力图，基准格 $351.84 高亮。**复用项目现有 lib/heatmap.py 配色约定**（teal/red 不翻）。
- **分析师情景注释**（r24-39，中文）: "方案A 维持TG3.5%≈$352 / 方案B TG3.0%≈$330 / Driver 改进自我对冲"—— 这是分析师的定性判断，放在网格下方作为 callout，**明确标注"分析师 view，非共识"**。

> 隐含上行: TP $352 vs 现价 $225 = +57%。但这是单一模型的 base case，必须配 sensitivity 网格让用户自己看 WACC/TG 假设的脆性，不给孤立 TP。

### 共识 vs 分析师 view 的区分（关键标注）
- **结构化 feed sheet**（Incomestatement_IS / Segment_SG / KeyValues_KV 等，列 A 是 "N_xxxx" item code）= **Visible Alpha 口径**，疑似含 sell-side consensus →标 **"卖方一致预期（Visible Alpha）"**，可靠性 LOW-MEDIUM。
- **Summary / Driver / Beat_Miss / Valuation**（分析师手搭、含 CMSI Est.）= **分析师自己的 view** →标 **"招商证券国际模型预测"**。
- 同一指标若两源都有（如收入 FY26E），可做"模型 view vs VA 共识"的 variant 对比条 —— 这正是 `/variant-check` 的可视化形态，是最高价值的增量。

---

## 4. 数据口径与可靠性标注

三类数据，三种视觉处理，**绝不混淆**：

| 数据类 | 来源 | 可靠性 | 视觉标注 | 能否裸展示 |
|---|---|---|---|---|
| GAAP 财报实际 | SEC/财报，对应 actual 列 (FY≤FY25) | **HIGH** | 实线/实心，无水印 | ✅ 可，标"来源:财报 + 截至" |
| 分析师模型 view | Summary/Driver/Beat_Miss/Valuation | **MEDIUM** | 主色 + 角标"招商模型" | ⚠️ 须标"分析师预测/估算" |
| VA 共识 feed | N_xxxx item sheets | **LOW-MED** | 灰调 + 角标"VA 共识" | ⚠️ 须标"卖方一致预期" |
| forecast 任意来源 | 含 "E" 列 | 降级 | 虚线/半透明 + "Forecast" 水印 | ❌ 绝不裸展示 |

**硬规则**:
- 任何 FYxxE 数字、任何 TP、任何 margin forecast → 卡片角必带 "分析师预测" badge。
- DCF TP 永远和 sensitivity 网格同屏，不单独给一个数。
- Beat_Miss 的 "CMSI Est." 列标"招商自有预测"，**不等于共识** —— 防止用户误读为市场预期。
- 每张图脚注: `来源: 分析师模型 VEEV US Mar2026.xlsx, 数据截至 [模型文件日期]`；模型 >30 天标"待更新"。

---

## 5. 跨模型泛化 — 通用核心 + 行业插件 schema

异构模型（SaaS VEEV / 器械 ISRG / 药 / A股 300760 等）sheet 名和结构全不同，但**金融语义可统一**。设计成两层 schema：

### 通用核心（Universal Core）— 所有公司必有，进统一可视化框架
```
revenue_total[]          总收入时序 + YoY%
segment_mix[]            分部收入占比（名字行业相关，结构通用）
margins{gross,op,net}    三大利润率 × {gaap, non_gaap}
gaap_nongaap_bridge[]    桥项目（行业无关：SBC/摊销/一次性）
forecast_horizon         FYxxE 序列 + 第一个 E 列索引（actual/forecast 分界锚）
eps[], fcf[], fcf_margin
dcf{wacc, tg, tp, current_price, ev}
sensitivity_grid[][]     WACC×TG → TP
beat_miss[]              Actual vs Est vs Var（若有）
```
→ 这部分驱动**所有公司共用的 5-6 张标准图**：收入趋势、分部占比、利润率三联、GAAP桥、预测面板、DCF敏感性。

### 行业插件（Sector Plugin）— 收入驱动因子，按行业建模
| 行业 | 驱动因子（plugin schema）| 对应展示 |
|---|---|---|
| **SaaS (VEEV)** | 客户数 × 每客户产品 × 每产品ARPU；订阅 vs 服务 | 客户净增锯齿图、ARPU 趋势、订阅收入瀑布 |
| **器械 (ISRG)** | 装机量(installed base) × 每台手术量 × 耗材ARPU；设备 vs 耗材 vs 服务 | 装机增长、procedure volume、耗材占比上升曲线 |
| **药 (制药/biotech)** | 单品种销量 × 价格 × 渗透率；按产品/适应症/地区 | 品种收入堆叠、专利悬崖、管线 NPV |

→ plugin 只负责"收入是怎么来的"那一层 L2，渲染成行业专属的 1-2 张驱动图。

### 落地机制（金融视角，不涉代码细节）
- 每个模型配一个 **mapping descriptor**（JSON）: 声明 "本模型的总收入在 Summary!r22"、"第一个 forecast 列 = FY26E"、"行业 = SaaS"、driver 字段映射。异构问题收敛成"为每个模型写一份映射"，而非写 N 个 parser。
- 通用核心字段缺失 → 该图优雅降级/隐藏，不报错。
- 行业 plugin 按 `sector` 字段路由（复用项目已有 `domain` 分层思路，别 hardcode 医疗）。
- 映射 descriptor 落盘 `data/models/<ticker>.json`（frozen，遵循项目现有 JSON 模式），与 wiki house view 一起喂给详情页。

---

## MVP（VEEV 先行）— 具体图表 + 字段清单

**入口**: 复用 `app/pages/6_Ticker_Drill.py` 模式，新增"分析师模型"Tab/页；支持 `global_ticker` + `query_params` 深链；点击公司即开。

**页面布局（自上而下 5 个 section + wiki）**:

| # | Section | 图表 | 字段 (sheet!行) | actual/forecast |
|---|---|---|---|---|
| 0 | Header | rating/TP 卡（复用 wiki house view）+ 模型时间戳 + "TP $352 / 现价 $225 / +57%" | wiki.py + Sensitivity r8/r9 | — |
| 1a | 收入总览 | 收入堆叠柱(Sub vs Prof) + Y/Y 线 | Summary r16/r17/r22, r12-14 | FY26E 起虚线 |
| 1b | 分部拆解 | Commercial vs R&D 堆叠 + 各分部增速 | Driver r25 + R&D段 | 同 |
| 1c | 驱动因子 | 客户数柱(双分部) + 净增 overlay；ARPU/产品数 双线；**订阅收入瀑布** | Driver r3-13(Comm)/r29-39(R&D) | 同 |
| 2a | 利润率三联 | 毛利/营业/净利率，每条 GAAP(灰)+非GAAP(主色) 双线 | Summary r59-62, Beat_Miss r28/32/34 | 同 |
| 2b | 费用率结构 | R&D%/S&M%/G&A% 堆叠面积（非GAAP）| Beat_Miss r29-31 | 同 |
| 2c | **GAAP→非GAAP 桥** | 水平瀑布(GAAP OI →+SBC →+摊销 →+诉讼 → 非GAAP OI) | Beat_Miss r38-41 | actual 季度 (4Q26) |
| 2d | Beat/Miss 面板 | 表格 + bps 偏差色块 | Beat_Miss r5-34 | 最近 actual |
| 3a | 预测面板 | 收入/非GAAP营利/净利/EPS/FCF 的 FY26E-FY30E 卡片网格 | Summary r22/r41/r43/r44/r35 | 全 forecast |
| 3b | DCF 假设卡 | WACC/TG/TP/现价/EV | Sensitivity r6-10 | 标"分析师预测" |
| 3c | 敏感性热力图 | WACC×TG → TP 网格，基准格高亮 | Sensitivity r14-21 | 复用 lib/heatmap.py 配色 |
| 3d | 情景注释 | 方案A/B callout（中文）| Sensitivity r24-39 | 标"分析师 view" |
| 4 | LLM Wiki | 公司 wiki 正文 | wiki.py find_wiki(VEEV) | — |

**全局标注规则（MVP 即落实）**: forecast 列虚线+半透明+竖直分界线；所有预测卡角标 "招商模型预测"；DCF/TP 永远配 sensitivity 同屏；图脚注带源+时间戳。

**已知坑提醒（交给实现层）**: `st.cache_data` 必须按 `ticker` 参数 key 缓存模型解析函数，避免本项目已知的跨页 key 碰撞；模型文件解析一次缓存，别每次 rerun 重读 15 sheets。

**相关文件路径**（供实现层接手）:
- 样本模型: `/Users/gcc/Downloads/VEEV US Mar2026.xlsx`
- 复用入口: `/Users/gcc/invest-dashboard/app/pages/6_Ticker_Drill.py`
- wiki 接入: `/Users/gcc/invest-dashboard/app/lib/wiki.py`
- 图表/配色/i18n: `/Users/gcc/invest-dashboard/app/lib/charts.py`, `theme.py`, `heatmap.py`, `i18n.py`
- 抽取器复用模式: `/Users/gcc/.claude/skills/earnings-house/scripts/extract_dcf.py`
- 建议 descriptor 落盘: `/Users/gcc/invest-dashboard/data/models/VEEV.json`

## B. 可视化/交互 (designer)

I now have full grounding on the house design system, the existing components, and the integration surface. Delivering the design.

---

# 分析师模型 → 公司财务可视化层 设计方案

**Aesthetic Direction:** CMSI 卖方 house · "分析师工作底稿" 编辑风 — cream 纸面、hairline-only 分隔、▎red section bar、KPI 不堆卡而做"价值条/桥"。三色诚实标注（house view / 卖方共识 / GAAP 财报）是这页的记忆点，不是通用 dashboard。
**Framework:** Streamlit 1.58.0 多页 + Plotly（`theme.PLOTLY_LAYOUT` patch）+ HTML components（`theme.kpi_strip` / `section_header`）。

---

## 决策 0 — 组织方式（先定位，再画图）

**结论：不新增独立顶层页，也不塞进 6_Ticker_Drill 的线性流。改用 6_Ticker_Drill 内部 `st.tabs` 顶部分栏 + 一个新 lib 模块 `lib/model_view.py`。**

理由（这是反 slop 的核心架构判断）：

| 选项 | 否决理由 |
|---|---|
| 独立新页 `pages/10_Analyst_Model.py` | 破坏"点公司 = 一个落点"心智；deep-link `?ticker=` 要在两页同步；导航栏第 11 个页签是噪音 |
| 塞进 6 的线性 section 流 | 6 现已是 KPI 条→Variant→Wiki memo→RS 图→SEC 趋势的长滚动；再灌入收入拆解+利润率+预测+敏感性会变成"无限下拉的什么都有页"——典型 slop |
| **6 内部 tabs（采纳）** | 一个 ticker、一套 `global_ticker`/`query_params`、一个 sidebar 搜索；用户在同一公司语境下横切"叙事 vs 数据 vs 模型" |

**6_Ticker_Drill 的新顶层结构**（Header 永远在 tabs 之上，保持身份锚定）：

```
┌──────────────────────────────────────────────────────────────────────┐
│ ▎VEEVA SYSTEMS · VEEV US           [评级 增持]  [TP $352]  [lang 中/EN]│ ← Header 不变, 永远在 tabs 上方
│ Last 218.40 · Mcap 35.4B · Fwd P/E 52x · YTD +12.3%                    │
├────────────────────────────────────────────────────────────────────── │
│  〔 叙事 House View 〕  〔 分析师模型 Model 〕  〔 GAAP 财报 SEC 〕      │ ← st.tabs (3)
└──────────────────────────────────────────────────────────────────────┘
```

**三 tab 的分工契约（谁讲什么，零重复）：**

- **Tab 1 叙事 House View** = 现有内容收纳进来：Variant（house vs 共识）+ LLM Wiki memo（thesis / 催化剂 / 风险）+ RS 相对强弱图。讲 **"为什么买"**。
- **Tab 2 分析师模型 Model** = 本次新增主体。讲 **"分析师怎么算"**：收入拆解 / 利润率 / 预测 + DCF。数据源 = 分析师手搭 Excel（Summary/Driver/Beat_Miss/Valuation sheet）。
- **Tab 3 GAAP 财报 SEC** = 现有 8_SEC_Facts 的逻辑下沉/链接。讲 **"监管口径事实"**：GAAP us-gaap/ifrs-full company facts。

> **去重铁律**：SEC tab 只放 **公司官方申报口径**（HIGH 源，可直引）；Model tab 放 **分析师非GAAP拆解 + forecast**（分析师 view，须标注）。同一个"营收"数字若两边都有，SEC tab 是事实锚，Model tab 旁标 `vs 公司申报 +0.3%` 做对账线。这正是稀缺价值：把分析师模型和监管事实摆在一个公司语境里对账。

---

## 决策 1 — 三块内容的图表设计 + ASCII 线框

### (a) 收入拆解 Revenue Build

不用通用饼图/堆叠柱了事。用 **分部堆叠面积（季度时序） + actual｜forecast 竖线分界 + 右侧占比/增速侧栏**。数据源：Summary sheet 分部收入 + Driver sheet 的 Commercial vs R&D Solutions / 订阅 vs 服务。

```
▎收入拆解 · 分部 × 订阅/服务            来源: 分析师模型 Summary+Driver · 截至 2026-03
┌────────────────────────────────────────────────┬──────────────────┐
│  $M  实际 ACTUAL  ┊  预测 FORECAST              │  最新季占比       │
│ 800├                          ┊         ╱▒▒▒▒▒  │  ┌────────────┐  │
│    │                    ╱▓▓▓▓▓┊▓▓▓▓▓▓▒▒▒▒▒▒▒▒  │  │Comm 订阅 58%│  │  ← 横向 100%
│ 600├              ╱▓▓▓▓▓▓▓▓▓▓▓┊▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │  │R&D  订阅 22%│  │     占比条
│    │        ╱▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓┊                 │  │Comm 服务 12%│  │   (teal 系
│ 400├  ▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░┊░░░░░░░░░░░░░░░░  │  │R&D  服务  8%│  │    深浅区分
│    │  ░░░░░░░░░░░░░░░░░░░░░░░┊░░░░░░░░░░░░░░░░  │  └────────────┘  │    分部)
│ 200├  ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒┊▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒  │                  │
│    └──┬────┬────┬────┬────┬──┊─┬────┬────┬────  │  YoY 增速        │
│      1Q22 ... ...        4Q25┊ 1Q26E ... 4Q27E  │  Comm +18% ↑     │
│                              ↑实线=最近实际季    │  R&D  +24% ↑     │
│  ▓Comm订阅 ░Comm服务 ▒R&D订阅 ▒R&D服务          │  服务 +6%  →     │
└──────────────────────────────────────────────────┴──────────────────┘
  forecast 区: 半透明 (opacity 0.45) + 斜纹/虚线边, 与实际同色但"未结算"质感
```

设计要点：
- 分部用 `SECTOR_PALETTE` 取 2 主色（Comm=teal `#0d7680`、R&D=`#a07a2c`），订阅 vs 服务用**同色深浅**（订阅深、服务浅），不引第三色族——避免彩虹 slop。
- **actual｜forecast 竖线分界**是诚实性核心：forecast 段 `opacity≈0.45` + hover 标 `估` 字。

### (b) 利润率 Margin Bridge

**双层**：上半 = 利润率多线共享时间轴（GAAP vs 非GAAP 配对线）；下半 = 最新季 **GAAP→非GAAP 桥瀑布**（Beat_Miss sheet 的 SBC / 摊销 / 诉讼和解）。

```
▎利润率 · GAAP vs 非GAAP               来源: 分析师模型 Beat_Miss · 截至 2026-03
┌──────────────────────────────────────────────────────────────────────┐
│ %                                                  ┌─ 图例 ─────────┐  │
│40├          非GAAP营业利润率 ●━━━●━━━●━━━●━━━○━━━○ │ ━━ 非GAAP (实) │  │
│  │      ●━━━●                                      │ ┄┄ GAAP   (虚) │  │
│30├  ●━━━                                           │ ○  = 预测段    │  │
│  │          GAAP营业利润率 ●┄┄┄●┄┄┄●┄┄┄●┄┄┄○┄┄┄○ │ teal=非GAAP    │  │
│20├  ●┄┄┄●┄┄┄                                       │ ink =GAAP      │  │
│  └──┬────┬────┬────┬────┬────┊────┬────┬────────── └────────────────┘  │
│    1Q22 ...                4Q25┊ 1Q26E ...  ←同一条 actual|forecast 轴   │
├──────────────────────────────────────────────────────────────────────┤
│  最新季 GAAP → 非GAAP 桥 (4Q25)            非GAAP 营业利润率 35.2%       │
│                                                                        │
│  GAAP 22.1% ┤████                                                      │
│   +SBC      ┤    ▒▒▒▒▒▒▒  +9.4%   (股权激励, 最大调整项)                │
│   +购买摊销 ┤           ▒▒▒  +2.8%                                      │
│   +诉讼和解 ┤              ▒  +0.9%                                     │
│  非GAAP     ┤██████████████████  35.2%                                 │
└──────────────────────────────────────────────────────────────────────┘
```

设计要点：
- GAAP=实心墨线 `INK`，非GAAP=实心 teal——**质感区分（虚/实 + 颜色）双重编码**，色盲也能读。
- 桥是这块的差异点：通用 dashboard 只会画两条线；卖方真正想看的是**调整项构成**（SBC 占多少）。瀑布块用中性灰 `PAPER_RULE`/`INK_3`，不上涨跌色（这是会计调整不是市场涨跌，乱用 teal/red 会误导）。

### (c) 未来财务预测 Forecast + DCF

三件套：**预测柱（actual/estimate 分色）+ DCF 输出卡 + WACC×TG 敏感性热力图**。

```
▎未来财务预测 & 估值                    来源: 分析师模型 Valuation+Sensitivity · 截至 2026-03
┌──────────────────────────────────────┬───────────────────────────────┐
│ 营收 & 非GAAP EPS 预测                 │  DCF 输出 (分析师 view)        │
│ $M                          EPS$       │ ┌───────────────────────────┐ │
│3k├          ████ ███▒ ▒▒▒▒  ┤8         │ │ 目标价 TP      $352       │ │ ← KPI 不是
│  │     ███ █████ ████▒ ▒▒▒▒ ┤6         │ │ 现价对比       +61%↑      │ │   通用卡,
│2k├ ███ ████ ████ ████▒▒▒▒▒▒ ┤4         │ │ WACC           8.5%       │ │   是"估值
│  │ ███ ████ ████ ████▒ ▒▒▒▒ ┤2         │ │ 永续增长 TG    3.5%       │ │   假设面板"
│1k├ ███ ████ ████ ████▒ ▒▒▒▒           │ │ 隐含 EV/Sales  14.2x      │ │
│  └─23A─24A─25A─26E─27E─28E─            │ └───────────────────────────┘ │
│   实际=实心teal  预测=半透明斜纹        │  ●━ EPS 折线叠加              │
├────────────────────────────────────────┴───────────────────────────────┤
│  敏感性 · WACC × 永续增长 → 目标价网格            基准 ◆ TP $352          │
│              永续增长 TG →                                               │
│          2.5%   3.0%   3.5%   4.0%   4.5%                                │
│  W  7.5% │ 358 │ 378 │ 401 │ 428 │ 461 │   ← teal 深=TP 高(看涨方向)     │
│  A  8.0% │ 335 │ 351 │ 370 │ 392 │ 418 │      但本网格中性 ramp,         │
│  C  8.5% │ 314 │ 330 │◆352◆│ 373 │ 397 │      不锁涨跌语义(是敏感性不是行情)│
│  C  9.0% │ 296 │ 309 │ 328 │ 349 │ 372 │   ◆ = 基准方案 (WACC8.5/TG3.5)  │
│     9.5% │ 279 │ 291 │ 308 │ 327 │ 348 │                                 │
│  ▸ 分析师情景注: 方案A 维持TG3.5%≈$352 / 方案B TG3.0%≈$330 (中文原注)    │
└──────────────────────────────────────────────────────────────────────┘
```

设计要点：
- 预测柱沿用 (a) 的 actual/estimate 分色，全页一致语言。
- **DCF 卡 = 假设面板而非结论卡**：把 WACC/TG/隐含倍数和 TP 并列，逼用户看"TP 是怎么来的"——反 slop（slop 只甩一个大 TP 数字）。
- **敏感性热力图**：连续 ramp 而非锁 teal涨/red跌——因为这是"假设→TP"网格，不是市场涨跌。用单色 sequential teal ramp（深=TP 高），`◆` 标基准格。复用分析师的中文情景注释作为图注（这是手搭模型独有的、AI 编不出的东西）。

---

## 决策 2 — 异构模型 → 统一 schema（可视化层的前置契约）

可视化层只认一个 **`ModelView` 中间 schema**，不直接读 xlsx。抽取归一在数据层（不在本设计范围，但可视化层须声明它要什么）：

```
ModelView (per ticker, frozen JSON at data/models/{TICKER}.json)
├── meta:      {ticker, analyst, model_date, currency, source_file, taxonomy}
├── revenue:   [{period, is_forecast, segment, sub("subscription"/"services"), value}]
├── margins:   [{period, is_forecast, gaap_op_margin, nongaap_op_margin, ...}]
├── bridge:    {period, gaap, items:[{label, delta}], nongaap}   # GAAP→非GAAP
├── forecast:  [{period, is_forecast, revenue, nongaap_eps}]
└── dcf:       {tp, wacc, tg, implied_ev_sales, sensitivity:[[...]], scenarios_note}
```

可视化函数全部消费 `ModelView`，对 VEEV/ISRG/TMO/300760 一视同仁。某 block 缺字段（如某模型无 segment 拆分）→ 该图整块隐藏，**绝不画空轴**（见决策 3 降级）。"异构 → schema" 的脏活在抽取器（复用 `extract_dcf.py` 模式 + per-sheet 适配器），可视化层保持纯净。

---

## 决策 3 — 点击交互 + 优雅降级

**深链复用现有机制**（零改动）：`?ticker=VEEV&tab=model` → 6 页已读 `st.query_params` + `global_ticker`，新增解析 `tab` 参数选中默认 tab。Coverage 表/热力图里的公司链接已是 `?ticker=`，天然落到 6 页。

**有模型 vs 无模型 fallback（三层降级，这是诚实性所在）：**

```
进入 6_Ticker_Drill (ticker=X)
        │
        ├─ model_view.has_model(X)? ──┬── YES → 3 tabs: [叙事][分析师模型 ●][GAAP财报]
        │                             │         model tab 正常渲染
        │                             │
        │                             └── NO  → 2 tabs: [叙事][GAAP财报]
        │                                       model tab 不显示 (不是显示空壳!)
        │                                       叙事 tab 顶部 caption:
        │                                       "本标的暂无分析师模型, 数据来自 LLM Wiki + SEC 公司申报"
        │
        └─ 若 model 有但某 block 缺 (如无 DCF):
                  该 section 整块跳过, 不画占位空卡
```

`model_view.has_model(ticker)` = 检查 `data/models/{TICKER}.json` 是否存在（cache_data 按 ticker key，避开已知跨页缓存碰撞坑）。tab 数量动态——无模型的公司**根本看不到 model tab**，而不是看到一个写着"暂无数据"的空 tab（后者是 slop）。

---

## 决策 4 — 配色 / 排版 / 双语 / 诚实标注

**沿用 house token，新增 3 个语义规则：**

| 维度 | 规则 |
|---|---|
| **涨跌锁定** | teal `#0d7680` 涨 / red `#cc0000` 跌 **只用在 YoY 增速、现价 vs TP 这类有方向的市场量**。利润率桥、敏感性网格是**中性量**，用 sequential ramp / 灰阶，不碰涨跌色——防 A 股红绿误读叠加会计误读 |
| **actual vs forecast** | 实际=实心满 opacity；预测=同色 `opacity 0.45` + 斜纹/虚线边 + hover `估` 字；中间一条 `INK` 竖线分界。全页统一这套质感 |
| **GAAP vs 非GAAP** | GAAP=墨色 `INK` 虚线/实心；非GAAP=teal 实线。**虚实 + 色相双编码** |
| **三色诚实标注** | 每个数据块右上角一枚来源 chip（复用 `theme.chips`）:<br>`分析师 view`（amber `#a07a2c` 描边）/ `卖方共识`（蓝 `#4a6fa5`）/ `GAAP 申报`（teal `#0d7680`）。一眼分清这个数字的可信层级——直接落地 research-data.md 的 HIGH/MEDIUM/分析师 view 分层 |
| **双语** | 全部走 `i18n.t("model.*")` 新 key 段；中文默认。分析师中文情景注（Sensitivity sheet）作为**原文引用**直出，不翻译（保真）。`render_lang_toggle` 已在 Header，tab 内不再放第二个切换 |
| **排版** | `▎red bar + section_header`；数字 `FONT_MONO`（JetBrains Mono，已有 token）；hairline-only，无阴影无圆角大卡——延续底稿质感 |

---

## 决策 5 — 反 AI-slop 自检（这页凭什么不像模板）

1. **不堆通用 KPI 卡**：DCF 卡是"假设面板"（WACC/TG/隐含倍数并列），逼出 TP 的推导，不是甩一个孤零零的大数字。
2. **三色来源标注 = 可信度分层**：通用 dashboard 把所有数字平等呈现；这页把"分析师 view / 卖方共识 / GAAP 申报"视觉分层，是卖方台真正的纪律。
3. **GAAP→非GAAP 桥**：模板只画两条利润率线就完事；这页拆出 SBC/摊销/和解的调整构成——分析师真正争论的地方。
4. **actual｜forecast 竖线 + 半透明质感**：诚实区分"已结算事实"和"分析师外推"，模板常把预测和实际画成同质，制造虚假确定性。
5. **保留分析师中文手写情景注**：方案A/方案B 的中文注释是手搭 xlsx 独有的、AI 生成不出的人类判断——直接展示而非洗白成机器文本。
6. **中性量不滥用涨跌色**：利润率桥、敏感性网格不碰 teal/red，专门避开"什么都是红绿"的 A 股 slop 观感。
7. **动态 tab 数量**：无模型公司看不到 model tab，而非空壳"暂无数据"页。
8. **Model vs SEC 对账线**：同口径数字旁标 `vs 公司申报 +0.3%`——把分析师模型和监管事实放一起对账，是别处没有的稀缺视角。

---

## MVP 页面整体布局线框（6_Ticker_Drill 改造后）

```
┌════════════════════════════════════════════════════════════════════════┐
║ sidebar: 全局搜索 (ui.sidebar_search)         [ 中文 / EN ]  ← lang toggle║
╠════════════════════════════════════════════════════════════════════════╣
║ ▎VEEVA SYSTEMS · VEEV US                          [增持]  [TP $352]      ║ ← Header (永驻, tabs 上方)
║ Last 218.40  ·  Mcap 35.4B  ·  Fwd P/E 52x  ·  YTD +12.3%               ║   身份锚定
╟────────────────────────────────────────────────────────────────────────╢
║  ┌─ 叙事 House View ─┐ ┌─ 分析师模型 Model ●─┐ ┌─ GAAP 财报 SEC ─┐       ║ ← st.tabs(动态)
║  └───────────────────┘ └─────────────────────┘ └──────────────────┘      ║
╟────────────────────────────────────────────────────────────────────────╢
║  ▼ TAB = 分析师模型 Model            [分析师 view] 来源 chip 右上          ║
║                                                                          ║
║  ▎收入拆解 · 分部 × 订阅/服务                          [分析师 view]      ║
║  ┌──────────── 堆叠面积 actual|forecast 竖线 ─────┬─ 占比/增速侧栏 ─┐   ║  (a)
║  └─────────────────────────────────────────────────┴──────────────────┘   ║
║  ── hairline ────────────────────────────────────────────────────────── ║
║  ▎利润率 · GAAP vs 非GAAP                              [分析师 view]      ║
║  ┌─── 多线 GAAP┄/非GAAP━ 共享时间轴 ──────────────────────────────────┐ ║  (b)
║  ├─── GAAP→非GAAP 桥 瀑布 (SBC/摊销/和解, 中性灰) ───────────────────┤ ║
║  └───────────────────────────────────────────────────────────────────┘ ║
║  ── hairline ────────────────────────────────────────────────────────── ║
║  ▎未来财务预测 & 估值                                  [分析师 view]      ║
║  ┌── 预测柱 actual/estimate 分色 + EPS线 ──┬── DCF 假设面板 ──────────┐ ║  (c)
║  ├──────────────────────────────────────────┴──────────────────────────┤ ║
║  │  敏感性 WACC×TG 网格 (teal ramp, ◆基准) + 分析师中文情景注          │ ║
║  └───────────────────────────────────────────────────────────────────┘ ║
║  caption: 来源 分析师模型 {analyst} {model_date} · file: VEEV US Mar2026.xlsx║ ← provenance 落盘
╚════════════════════════════════════════════════════════════════════════╝
```

---

## 落地文件清单（供下游 executor）

- `app/pages/6_Ticker_Drill.py` — 包 `st.tabs`，Header 上移到 tabs 外；动态 tab 数量按 `has_model()`；解析 `?tab=` 深链。
- `app/lib/model_view.py`（**新**）— `load_model(ticker)→ModelView` / `has_model(ticker)`（cache_data 按 ticker key）；消费 `data/models/{TICKER}.json`。
- `app/lib/charts.py` — 新增 4 个函数：`revenue_build_area()` / `margin_lines_and_bridge()` / `forecast_bars()` / `dcf_sensitivity_heatmap()`，全部吃 `ModelView`，全部 `fig.update_layout(**theme.PLOTLY_LAYOUT)`。
- `app/lib/i18n.py` + `locales/` — 新增 `model.*` key 段（中默）。
- `data/models/{TICKER}.json` — frozen 抽取产物（抽取器复用 `extract_dcf.py` 模式 + per-sheet 适配器，归一异构 xlsx → ModelView；属数据层，本设计只定 schema 契约）。

**Verification（设计层）：** 不写生产代码故未运行；所有引用的 API（`theme.section_header/kpi_strip/kpi_metric/chips/PLOTLY_LAYOUT`、`i18n.t`、`st.query_params`/`global_ticker`、`charts.*` 的 Plotly+theme patch 模式）均已对照仓库现有实现核实存在且签名匹配。响应式：tabs + `kpi_strip` 的 `auto-fit minmax` 已是现有自适应模式；敏感性网格用 HTML table（复用 `ui.render_html_table` 解决 canvas 暗黑穿透坑）。

## C. 技术架构 (architect)

全部确认完毕。已有 `_templates/model_schema.json`(per-model mapping config 已起步)+ N_code taxonomy 实锤 + `data/wiki/companies/` 是 flat 公开镜像模式 + `jobs/` 是已有 build-job 落盘模式。证据齐全,可交付架构方案。

---

# 分析师模型 → 公司财务可视化页:技术架构与数据管道

## Summary

样本 VEEV 模型**完全可解析**,但有一个 load-bearing 约束:模型几乎所有单元格是跨 sheet 公式(`='VEEV US'!B4`),必须 `openpyxl.load_workbook(data_only=True)` 才能拿到缓存值——直接读公式只会得到 `=...` 字符串,所以**抽取脚本必须在分析师"保存过的 xlsx"上运行**(LibreOffice/Excel 保存时才写缓存值)。异构难点是真的:同分析师的 VEEV 两版(`Summary/Driver/OUTPUT/Valuation`)结构稳定,但 GBM 模型(`CMS 1/Valuation 2/Financials`)布局完全不同。推荐方案:**per-model YAML mapping config(主)+ N_code Visible Alpha taxonomy(自动兜底)**,产物 git-commit 到 `data/models/<TICKER>.json`,新建独立页 `7_Model_Drill.py`(不挤进 Ticker Drill)。

## Analysis(现状确认 — 全部 file:line/cell 验证过)

**1. 可解析性(已实测)**
- 15 sheets 全部 openpyxl 打开成功,1.6MB。
- `Summary` (`A1:CC336`):A列标签 + 第2行周期头(`B2=1Q19 … F2=FY19` 季度+年度混排),`data_only` 缓存值完整(`F16=694.467`)。**最干净的可视化数据源**。
- `Driver`:A列标签 + B1起周期头,客户数/产品/每产品收入逐段排列(`A3=Customer Beginning`、`A16=Sub Revenue mn`)。
- `Beat_Miss`:利润表(C列Actual/D列CMSI Est./E列Var)+ 利润率分析(`C28=Gross Margin 0.7647`)+ GAAP→非GAAP桥(`A39=(+) Stock-Based Comp`)。结构规整。
- `Sensitivity Analysis`:`D6=WACC 0.0849`、`D7=TG 0.035`、`D8=TP 352.66`,B14:I21 是 WACC×TG 网格,B24起有**中文情景注释**。
- `Incomestatement_IS` 等 6 个结构化 feed:含元数据头(`Company/Ticker/As Of 2024-10-28/IMPL or Raw/Data Type CD`)+ `Item Code | Line Item | Units` 三列,`N_5977340 = Total revenue`。**这是 Visible Alpha 标准口径的实锤**。

**2. 公式 vs 缓存(关键风险已验证)**
```
F16: formula="='VEEV US'!B4"   cached=694.467   ← data_only 必需
C28: formula='=C10/C7'          cached=0.7647    ← 派生比率也有缓存
```
若分析师从未在 Excel 里"打开并保存",缓存可能为 `None`——管道必须检测 `None` 比例并告警。

**3. 现有可复用件**
- `~/financial-models/_templates/model_schema.json` 已存在,VEEV 的 sheet→row 映射**已经手写到位**(per-model config 工作已起步,直接采用)。
- `app/pages/6_Ticker_Drill.py`:已支持 `?ticker=` 深链 + `st.session_state.global_ticker`(:169-175)。
- `app/lib/wiki.py:219` `find_wiki(ticker)` 用 `@lru_cache`,`data/wiki/companies/*.md` 是 flat 公开镜像(`export_wiki_public.py` 周 cron 生成)——**模型 JSON 应复用这个"flat-file + build job"模式**。
- `jobs/` 下已有 `fetch_*.py / export_*.py` 一批 build job,新抽取脚本进这里天然合群。
- **缓存碰撞坑(本项目刚踩过)**:`db.py:16-29` 注释明确——`@st.cache_data` 只按 `(module, qualname, source_text)` keying,所有 page 都 exec 在 `__main__` 下,无参函数会跨页串。`6_Ticker_Drill.py:233/620` 两处都强调"参数不能以 `_` 开头否则被踢出 cache key"。新页的 load 函数**必须以 `ticker`/`path` 作显式参数**。

## Root Cause(异构难点的本质)

不是"sheet 名不同"这么浅。本质是**两层数据共存于一个 xlsx**:
1. **分析师手工汇总层**(`Summary/OUTPUT/Driver/Beat_Miss`)— 命名/布局随分析师习惯漂移,但语义最丰富(分部/驱动/桥)。
2. **数据商结构化层**(`*_IS/_BS/_CF/_SG`,N_code)— **跨模型口径稳定**(只要都用 Visible Alpha),但只有原始三表、没有分部拆解和 DCF。

任何单一映射策略都会漏:只靠 N_code → 拿不到收入拆解/情景注释;只靠 per-model config → 每个新模型都要手写。**正解是分层映射**。

## Recommendations(异构映射逐一权衡)

| 候选方案 | Pros | Cons | 裁决 |
|---|---|---|---|
| **(i) per-model YAML config** | 精确;`_templates/` 已起步;分析师不用改工作习惯;可读可审 | 每个新 ticker 要手写一次(~30min) | **主方案** |
| (ii) 约定标准 OUTPUT/Summary tab | 一次约定全模型通用 | 要分析师改习惯,跨人难推行;VEEV 有 OUTPUT 但 GBM 没有 | 仅作"加分项",不强求 |
| (iii) N_code taxonomy | 跨模型自动稳定;无需人工 | 只覆盖三表,缺分部/DCF/情景;依赖都用同一数据商 | **自动兜底层**(填三表) |
| (iv) LLM 辅助抽取 | 兜底任意烂格式 | 不确定性高;数字幻觉风险违反 source 纪律;慢/贵 | **最后兜底**,且产物必须 `confidence:"llm_low"` 标记 + 人工复核 gate |

**推荐 = (i) 主 + (iii) 自动兜底 + (iv) 仅 flag-not-fact**:
1. 每个 ticker 一个 `config/models/<TICKER>.yml`,声明哪个 sheet/行列对应 revenue_breakdown/margins/forecast/dcf。VEEV 直接从 `_templates/model_schema.json` 转。
2. 抽取器先按 N_code 自动填三表(稳定层),再按 YAML 覆盖分部/DCF/情景(语义层)。
3. 找不到 config 的新模型 → 跑 N_code-only 自动抽 + 标 `coverage:"partial"`,页面显示"仅三表,无分部拆解"。绝不让 LLM 静默猜数字。

**MVP 取舍**:第一版只做 VEEV 一只(config 已存在),手动跑脚本,验证 schema + 页面闭环。不碰 LLM 兜底,不做 watch/job。

## 统一 Financial Schema(JSON 草案)

```jsonc
{
  "meta": {
    "ticker": "VEEV", "market": "US", "company": "VEEVA SYSTEMS INC",
    "currency": "USD", "units": "millions",        // 单位单源声明
    "fiscal_year_end": "January 31",
    "model_version": "Mar2026",                    // 来自文件名 {Mon}{YY}
    "as_of": "2024-10-28",                         // VA "As Of" header
    "source": "CMSI analyst model + Visible Alpha",
    "source_file": "VEEV US Mar2026.xlsx",
    "extracted_at": "2026-06-01T...",
    "coverage": "full",                            // full | partial(三表only) | llm_low
    "confidence": "high"                           // high | medium | llm_low
  },
  "periods": [                                     // 时间轴单源,所有数组按此对齐
    {"label":"FY25","kind":"annual","end":"2025-01-31","actual_est":"A"},
    {"label":"FY26E","kind":"annual","end":"2026-01-31","actual_est":"E"},
    {"label":"4Q26","kind":"quarter","end":"...","actual_est":"A"}
  ],
  "revenue_breakdown": [                            // (a) 收入拆解
    {"segment":"Subscription Services","segment_cn":"订阅服务","basis":"gaap",
     "values":{"FY25":2..., "FY26E":...},
     "yoy":{"FY26E":0.18}},
    {"segment":"Commercial Solutions","segment_cn":"商业化解决方案","parent":"Subscription Services",
     "drivers":{"customers_end":{"FY25":...},"products_per_customer":{...},"rev_per_product":{...}}}
  ],
  "margins": [                                     // (b) 利润率
    {"metric":"gross_margin","metric_cn":"毛利率","basis":"non_gaap",
     "values":{"4Q26":0.7648,"4Q25":0.7690},
     "estimate":{"4Q26":0.77},"var_bps":{"4Q26":-52.0}}   // Beat_Miss Actual/Est/Var
  ],
  "forecast": [                                    // (c) 未来财务预测
    {"line":"revenue","line_cn":"营业收入","basis":"gaap","values":{"FY26E":...,"FY27E":...}},
    {"line":"operating_income","basis":"non_gaap","values":{...}},
    {"line":"eps","basis":"non_gaap","values":{...}}
  ],
  "gaap_bridge": [                                  // GAAP→非GAAP 桥(Beat_Miss)
    {"item":"GAAP Operating Income","values":{"4Q26":245.88}},
    {"item":"(+) Stock-Based Comp","values":{"4Q26":118.26}}
  ],
  "dcf": {                                         // DCF 输出 + 敏感性
    "wacc":0.0849, "terminal_growth":0.035, "target_price":352.66,
    "current_price":225.0, "ev":51309.24,
    "sensitivity":{"axis_x":"terminal_growth","axis_y":"wacc",
      "x":[0.02,0.025,0.03,0.035,0.04,0.045,0.05],
      "y":[0.07,0.075,0.08,0.085,0.09,0.095,0.10],
      "grid":[[398.26,...],[...]]},
    "scenarios_note_cn":"方案A 维持TG3.5%≈$352 / 方案B TG3.0%≈$330"  // 分析师中文注释
  }
}
```
设计要点:`basis: gaap|non_gaap` 显式标在每行(VEEV 两套并存);`actual_est: A|E` 在 period 维度统一标(避免每个数字重复标);`coverage/confidence` 让页面对 partial/llm 数据降级显示;`units` 单源声明,值本身不带单位。

## 管道示意

```
分析师在 Excel/LibreOffice 保存模型 (写入公式缓存值 — 必需!)
        │
        ▼
jobs/extract_model.py --ticker VEEV --xlsx <path>      ← 复用 extract_dcf.py 模式
   ├─ openpyxl.load_workbook(data_only=True)            ← 缓存值;检测 None 比例→告警
   ├─ N_code auto-fill 三表 (Incomestatement_IS 等)     ← 稳定层
   ├─ apply config/models/VEEV.yml: 分部/margins/dcf    ← 语义层覆盖
   └─ validate (periods 对齐 / 单位 / 必填字段)
        │
        ▼
data/models/VEEV.json  ──git commit──▶  Streamlit Cloud (从 main 自动重部署)
        │
        ▼
app/pages/7_Model_Drill.py  (?ticker=VEEV 深链)
   @st.cache_data load_model(ticker)  ← 显式 ticker 参数 keying(防跨页碰撞)
   渲染: 收入拆解 / 利润率 / 预测 / DCF敏感性 + wiki memo
```

**何时抽取**:MVP 手动跑;V2 可做 `jobs/` 里一个 `refresh_models.py` 扫 `~/financial-models/**/*.xlsx` 增量重抽(对比 mtime)。**不做 watch**——分析师更新模型频率低(月度),手动/半自动足够。

## 页面集成

**新页 `7_Model_Drill.py`,不扩 `6_Ticker_Drill`**。理由:
- Ticker Drill 已经很重(742行,KPI strip + Variant + wiki + RS chart + SEC trends + yfinance)。塞 4 块模型图会爆。
- 模型数据只覆盖少数 ticker;Ticker Drill 是全 universe 通用页。耦合会让无模型公司页面出现空块。
- **但要双向深链**:Ticker Drill 检测 `has_model(ticker)` → 显示一个 "📊 分析师模型" 按钮跳 `7_Model_Drill?ticker=X`;反之 Model Drill 顶部放回链。复用现成 `st.query_params` 模式(`6_Ticker_Drill.py:169-175`)。

**缓存(必须按本项目教训写)**:
```python
@st.cache_data(ttl=600)
def load_model(ticker: str) -> dict | None:        # ← ticker 显式参数,NOT _ticker
    p = REPO_ROOT / "data" / "models" / f"{ticker}.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None

def has_model(ticker: str) -> bool:
    return (REPO_ROOT / "data" / "models" / f"{ticker}.json").exists()
```
渲染走现成 `app/lib/charts.py` + `app/lib/theme.py`(teal涨/red跌锁定),i18n key 加 `model.*`。DCF 敏感性网格用 plotly heatmap;收入拆解用 stacked bar;利润率用 line。

## 与 wiki/sec_facts 集成 + fallback + 演进

- **wiki**:Model Drill 顶部直接调 `wiki.find_wiki(ticker)` 复用 memo 渲染(`6_Ticker_Drill.py:393-449` 整段可抽成 `lib` 函数共用)。模型给数字,wiki 给 thesis,互补。
- **sec_facts**:模型预测(分析师 view)vs SEC XBRL 实际(`lib.sec_facts`)可做"模型 vs 已报"对照——但这是 V2,MVP 先不做。
- **无模型公司 fallback**:`has_model()` False → 页面显示"该公司暂无分析师模型,见 个股详情/SEC 数据"+ 跳 `6_Ticker_Drill` 的链接。绝不空白页。
- **数据时效**:`meta.as_of` + `meta.model_version` 显示在页头;>90天标"待更新"(对齐 research-data.md 失效协议)。
- **演进**:MVP(VEEV 单只,手动)→ V1(同分析师 N_code 模型批量,3-5只)→ V2(异构模型 config 库 + LLM 兜底 flag + 模型vs SEC 对照)。

## 风险清单

| 风险 | 严重度 | 缓解 |
|---|---|---|
| **公式缓存缺失**:分析师未在 Excel 存过,`data_only` 返回 `None` | 高 | 抽取器统计 `None` 占比,>20% 直接 fail + 提示"请在 Excel 打开并保存"。CI 不静默产出空 JSON |
| **保密 — TP/分析师模型上公开 Cloud** | **高** | **核心决策点**:`data/models/*.json` 含 TP/盈利预测/分部拆解,属内部研报衍生。**强烈建议比照 wiki 双轨**:内部全量(George Mac,gitignore)+ 公开脱敏(去 TP/去 DCF target,只留历史 actual)。`wiki.py:36-48` 的 `_wiki_roots()` internal-first/public-fallback 是现成模板。**MVP 阶段 model JSON 不进 public 仓库 / 不上 Cloud**,先本地验证 |
| 模型格式漂移(分析师改 sheet 布局) | 中 | YAML config 版本化 + 抽取后 validate 必填字段;漂移→validate 失败而非产出错数据 |
| xlsx 进仓库膨胀(1.6MB×N) | 中 | **源 xlsx 不进 invest-dashboard 仓库**(留在 `~/financial-models/`);只 commit 抽取后的 JSON(~50KB)。源模型留 Mac/单独私仓 |
| N_code 口径假设失效(非全模型用 VA) | 中 | 抽取器检测 `Data Type/As Of` 元数据头存在才走 N_code 路径;否则纯 config |
| 跨页 cache 碰撞(本项目史) | 中 | load 函数显式 `ticker` 参数 keying(已写进骨架)|
| 单位/FX 混乱(GBM 是 CNY,VEEV 是 USD) | 中 | `meta.units`+`currency` 单源;页面按 currency 标注,不跨币种聚合 |

## 关键交付物 References
- `~/financial-models/_templates/model_schema.json` — **per-model config 已起步**,VEEV sheet→row 映射现成,直接转 YAML
- `~/financial-models/VEEV/models/VEEV_US_Nov25.xlsx` vs `~/Downloads/VEEV US Mar2026.xlsx` — 同分析师结构稳定(命名一致)
- `~/financial-models/2661/Project GBM Model_Mar 2026.xlsx` — 异构实证(`CMS 1/Valuation 2/Financials`,布局完全不同)
- `~/.claude/skills/earnings-house/scripts/extract_dcf.py:1063` — `data_only=True` 模式 + `LABEL_MAPPING` 中英对照 + 跨 sheet rescue,抽取器骨架直接复用
- `app/lib/wiki.py:36-48` `_wiki_roots()` — internal/public 双轨脱敏模板(模型保密用同模式)
- `app/lib/db.py:16-29` — `@st.cache_data` 跨页碰撞根因注释(新 load 函数 keying 依据)
- `app/pages/6_Ticker_Drill.py:169-175` — `?ticker=` 深链模式;:233/:620 — `_`-prefix 参数会被踢出 cache key 的两处实证
- `app/pages/6_Ticker_Drill.py:393-449` — wiki memo 渲染段,可抽 `lib` 共用
- `jobs/export_wiki_public.py` + `data/wiki/companies/*.md` — flat-file + build-job 落盘模式,`data/models/*.json` 照搬