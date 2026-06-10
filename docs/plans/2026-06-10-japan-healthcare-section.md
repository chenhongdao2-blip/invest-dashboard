# 日本医药 Japan Healthcare section — 设计文档

> 2026-06-10 · George 已批准方案 A（「区域 universe」+ Healthcare 页新 section）
> 源数据：`~/Desktop/Copy of Japan-Healthcare.xlsx`（iFind 自选股导出，42 支，快照 2026/05/26）
> xlsx 价值 = universe 清单（代码+中文名+市值序），行情/PE/PB 列不可用（静态/全 0）；实时数据走现有 yfinance `.T` 管道。

## 决策记录

| 问题 | 决定 |
|------|------|
| 专栏形态 | 并入 `2_Healthcare.py` 作为新 section（不做独立页） |
| 内容范围 | 子板块汇总表 + 相对表现图 + 明细 expander + Agent read + xlsx 下载 |
| Universe 范围 | 全收 42 支 → **实施时改 40 支**：HOGY MEDICAL(3593, 凯雷 TOB 2026-05-15 退市)、久光制药(4530, MBO 非公开化)已退市剔除，记录在 `_gen_jp_seed.py` 的 `DELISTED` |
| Universe 注册 | `healthcare.yml` 新增顶层 `regions:` key（与 `sectors:` 平级，**不混 sector taxonomy**） |
| 相对表现口径 | hero = 40 支等权专栏指数(USD)；peers = TOPIX ETF 代理 + 日经(^N225)，均换 USD |
| TOPIX 代理 | **1305.T（大和）**，非原定 1306.T：1306.T 2026-03-30 10:1 拆股 Yahoo 缺 split factor，auto_adjust 修不掉 −90% 假断崖（实测 +88pp 假 spread 后换代理） |

## §1 数据层

- `config/universes/hc_japan.yml`（新建）：42 条，字段 `ticker(.T) / name_cn / name_en / region: JP / subsector`。
  subsector 四分类：pharma(20) / medtech(11) / diagnostics(5) / distribution(6)。
  由一次性脚本 `jobs/_gen_jp_seed.py` 从 xlsx 生成（仿 `_gen_hk_seed.py`）；xlsx 归档 `data/external/jp_healthcare_watchlist_20260526.xlsx`。
- `config/domains/healthcare.yml`：新增顶层 `regions:` → `- id: japan, universe_file: hc_japan.yml`。
- `jobs/load_universe.py`：+几行，把 `regions` 也 ingest（DB sector_id=`japan`；subsector 不进 DB，页面读 yml 分组——yml 是单一数据源）。
- `jobs/fetch_eod.py`：`BENCHMARK_TICKERS += ["1306.T", "^N225", "JPY=X"]`（JPY=X 仿 CNY=X/HKD=X 先例，供 JPY→USD 序列换算）。
- 一次性回填：`python jobs/fetch_eod.py --backfill-days 260`（新增 33 支对齐 2025-09-22 起点）。
- 与 hc_pharma/hc_medtech 已有 9 支日本股不冲突（不同 sector_id 并存，价格按 ticker 去重）。

## §2 计算层（`app/lib/hc_overview.py` 追加）

- `jp_universe()`：读 hc_japan.yml → DataFrame(ticker/name_cn/name_en/subsector)。
- `jp_composite()`：42 支 `get_close_series_usd` → 各自归一 100 → 等权平均；TOPIX/日经从 benchmarks_daily 取 JPY 原值 ÷ JPY=X → USD 同口径；锚 = 共同最早日期。

## §3 页面层（`2_Healthcare.py`，插在「相对表现」section 之后——动线：全球→中国→日本）

1. section_header「日本医药 · Japan Healthcare」+ meta（42 支 · iFind 自选清单 · USD 口径）
2. 子板块汇总表：4 行 × (Tickers, 1D/5D/1M/YTD avg) — 复用 `_render_pct_table`
3. 相对表现图：专栏指数 vs TOPIX vs 日经 — 复用 `charts.index_compare_chart`（spreads caption）；
   caption 双重标注「TOPIX 用 1306.T ETF 代理 · USD 口径含汇率」（KURE/MCHI 先例 + RRG 护栏③精神）
4. 42 支明细表收进 expander（BBG ticker + 双语名 + Last + 回报列，按 subsector 排序）
5. Agent read 段（eyebrow，跨市场解读初稿待 George 终审）+ xlsx 下载（`hc_exports` 新增 `japan_bytes()`）
6. staleness：prices 最新日期，新 key `jp` 阈值 7 天（EOD cron 日刷）
- i18n：`pages_zh/pages_en` 新增 `hc.jp.*` 全套

## §4 明确不做（YAGNI）

不进 7-sector 汇总表；不加热力图 Japan tab；不做 JP 个股财务下钻（SEC facts 不适用）；不展示 PE/PB（源数据全 0，yfinance JP 覆盖不稳）。

## 验收

本地 streamlit 眼验（中/英双语各过一遍）→ George 说「可以 ship」才 commit（local-first ship gate）。
