# Healthcare 页数据刷新管道 (Runbook)

> invest-dashboard「Healthcare」页 4 个 external 数据集的刷新方法论。
> 触发:开 cc 在本文件夹 → SessionStart hook `.claude/hooks/hc-staleness.mjs` 按各自周期检测 stale → 提示回补。
> Owner: George Chen。最后更新 2026-06-03。

## 为什么不能"实时/自动"更新(诚实边界)

这 4 个数据集的源头**云端 CI(GitHub Actions)和 Streamlit Cloud 都够不到**:

| 源 | 为什么 CI 够不到 |
|---|---|
| iFind | 会话级 MCP,无裸 API key;CI runner 也无中国代理 |
| 本地 audited xlsx | 在 George 的 Desktop,云端无此文件 |
| 手工核年报/ESG | iFind NL 对纯 H biotech 解析坏了,需人逐家核 |

且这些是**月/季/年频**数据,盘中"实时"无意义。已有的 `fetch_eod.yml` / `fetch_sec_facts.yml`
CI 只覆盖 `snapshots.db`(yfinance/SEC,US runner 直连),够不到上面这几类。

**真要让 HK 数据自动**:把 iFind 开放接口的裸 key 喂进 CI secret(目前用的是 MCP,不是裸 key)——
有凭证再说,否则做不到。当前策略 = **永不静默过期(app 徽章)+ 按周期人工回补(hook 提醒)**。

## 数据层 + 源 + 节奏 + 回补命令

| 数据集 | 文件 | 源 | 节奏 | 阈值(hook) | 回补 |
|---|---|---|---|---|---|
| 相对表现(指数对标) | `hc_index_comparison.csv` | US=yfinance 实拉 / HK=iFind provenance CSV | US 日频可刷 / HK 随 provenance | 35 天 | `build_hc_overview_data.py`(需代理) |
| HSHCI 长周期 | `hshci_history_monthly.csv` | iFind 指数月线(嵌 `hshci_history.py` ROWS) | 月频 | 45 天 | 拉 iFind 月线 → 更新 ROWS → 跑 `hshci_history.py` |
| 机构持仓 | `china_fund_hc_positioning.csv` | 本地 audited xlsx(基金 factsheet) | 季频 | 135 天 | 更新 Desktop xlsx → `build_hc_overview_data.py` |
| 员工人数 | `cn_pharma_headcount.csv` | 手工核年报业绩公告/ESG(经 iFind) | 年频(~3-4 月 FY 年报出齐) | 300 天 | 核新 FY → 更新 `cn_pharma_headcount_2025.py` ROWS → 跑 |

> HK 指数/HSHCI/员工的【数字前进】都需要**带 iFind 的 cc 会话**先拉新数据并更新对应 job 的
> `ROWS`/provenance;脚本本身不会自己去 iFind 抓。

## 回补流程

### 一键(跑所有"不需新 iFind 拉取"的再 bake)
```bash
HTTP_PROXY=http://127.0.0.1:7897 HTTPS_PROXY=http://127.0.0.1:7897 \
  uv run --with pandas --with yfinance --with openpyxl --with matplotlib \
  python jobs/refresh_healthcare.py
```
跑完打印每个数据集最新 asof + 哪些是嵌入数据(数字未前进)。

### 让 HK/HSHCI/员工的数字真前进(需 iFind 会话)
1. **HSHCI 长周期**:`index_data` 拉 HSHCI.HK 月收盘(上次→今)→ 更新 `jobs/hshci_history.py` 的 `ROWS` → 跑它。
2. **相对表现 HK 面板**:`index_data` 拉 HSHCI/HSI/HSTECH → 更新 provenance CSV `hk_index_raw_ifind_<date>.csv` → 跑 `build_hc_overview_data.py`。
3. **员工人数**:新 FY 年报出齐后,逐家核「雇员及薪酬」段(A 股走 iFind 报告期;纯 H 走 `search_notice` 年报原文)→ 更新 `jobs/cn_pharma_headcount_2025.py` 的 `ROWS` → 跑它。
4. **机构持仓**:季度基金 factsheet 更新本地 audited xlsx → 跑 `build_hc_overview_data.py`。

### 上云
回补 + 本地眼验后:`git add data/external/*.csv jobs/*.py && git commit && git push`(Streamlit Cloud 自动 redeploy)。

## 兜底机制(已接)

- **app 内徽章**:`2_Healthcare.py` 每节显示「数据截至 X」,超阈值标 ⚠ —— 客户端永不把旧数据当实时。
- **SessionStart hook**:`.claude/hooks/hc-staleness.mjs` 每次新会话检测 4 个 CSV 的 asof,过期注入提示。阈值见上表。
- **一键脚本**:`jobs/refresh_healthcare.py`。
