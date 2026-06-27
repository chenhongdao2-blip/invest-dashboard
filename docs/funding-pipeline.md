# Funding / MNC-Deal 数据刷新管道 (Runbook)

> invest-dashboard「投融资」页(MNC M&A + BD/合作 + IPO + 余额表)的数据刷新方法论,固化成可复用流程。
> 触发:开 cc 在本文件夹 → SessionStart hook 每周检测一次 stale → 提示跑本管道。
> Owner: George Chen。最后更新 2026-06-01。

## 数据层 + 源 + 节奏

| 层 | 文件 | 源 | 节奏 | 自动化 |
|---|---|---|---|---|
| MNC M&A 历史 | `data/external/mnc_ma_deals.csv` | MNCs basket xlsx(mnc-deal-scanner)+ web 扫新 deal | 老数据静态;新收购 ~月度 | 半自动(分析师在环)|
| BD / 合作 | `data/external/bd_deals.csv` | ED Funding 报告 TABLE 59(2025)+ web 扫(2026) | 报告更新 / 新 BD ~月度 | 半自动 |
| MNC 余额表 | `data/external/funding_mnc_balance_*.json` | SEC 10-Q/20-F(edgartools `jobs/fetch_mnc_q1_2026.py`)| 季度(财报)| ✅ 可全自动 |
| 价格/multiples/benchmarks | `data/snapshots.db` | yfinance(`jobs/fetch_eod.py`)| 每日 | ✅ GitHub Action `fetch_eod.yml` |
| SEC 财报 | `data/snapshots.db` | edgartools(`jobs/fetch_sec_facts.py`)| 每日/季度 | ✅ GitHub Action `fetch_sec_facts.yml` |
| CN 基准(恒生医疗/中证医疗)| `data/snapshots.db` | iFind(`jobs/fetch_cn_benchmarks.py`)| 每周 | ⚠️ cron 够不到 iFind,需本地 |
| LLM Wiki(公司 memo)| `data/wiki/companies/*.md` | `~/Documents/LLM Wiki` → `jobs/export_wiki_public.py`(脱敏)| 按需 | ✅ 本地一条命令 |
| IPO 打分 | `data/external/ipo_picks.csv` | `/ipo-score` 卡 | 按 IPO 发生 | 手动 |

## 刷新管道(deal 部分 = 本管道核心)

新 M&A / BD deal 的刷新是 3 个 workflow + merge,**需交互 session**(web/MCP + 分析师拍板值冲突,投资人面数字必须人验):

### Step 1 · 扫新 deal(web)
核心 13 家 MNC(PFE/MRK/LLY/JNJ/ABBV/BMY/AMGN/AZN/GSK/NVS/SNY/ROG/NVO)+ 2026-06 扩入的活跃买家(GILD/BIIB/UCB/MRK.DE「Merck KGaA」/VRTX/TAK 等),分头 WebSearch + 各家 IR/newsroom/8-K + deal tracker(BioPharma Dive/Endpoints/Fierce/labiotech/BioBucks),找窗口内(上次刷新→今天)新 deal。
- ⚠️ **M&A 必须走 web/deal-tracker,不能用医药魔方**:PharmCube `drugDeal` 是药物交易库(license/合作/期权/资产出售),**结构上不收整体公司收购**(实测 Arcellx/Apellis/Apogee 反查全 0)。魔方只供 BD 那半;M&A 全靠 web/PR/8-K。
- universe 已超出原 13 家:M&A 收购方扩到"研发驱动的全球 biopharma";剔除仿制药/区域 specialty(Sun Pharma/Angelini/Chiesi 这类)与 PE 财团杠杆收购(Recordati 这类)。tools/诊断标的(如 Bio-Techne)入库时标 `deal_subtype=other` + note 注明"非药物管线"。
- **markdown scanner(不强制 schema)→ structurer 出 JSON** —— 强制 schema 的 agent 会因过度研究漏调 StructuredOutput 集体失败(踩过坑)。

### Step 2 · 分类 M&A vs BD
- **M&A** = 控制权转移(买下整个公司/控股)。
- **BD** = 无控制权转移:license / option / collaboration / rights。
- 陷阱:note 写「secured full rights to X」通常是**收购了拥有 X 的公司** = M&A,不是 rights license(Warner-Lambert/ICOS 踩过)。

### Step 3 · biotech-researcher 核(B3 + cross-check)
派多个 biotech-researcher 逐笔核:
- **B3 三段**:upfront 首付 + milestone 里程碑 ≈ total 总额(sum-check)。
- 授权方→被授权方**方向**(licensor 拥有资产、licensee 付钱)。
- 资产 / MoA / TA / 阶段。
- 重新确认 M&A vs BD。
- 读 funding 报告(`/tmp/ed_*_funding_cn.txt` 或 docx TABLE 59)+ 原始公告。
- 实战抓到过:荃信首付/里程碑写反、Orna $1065→$700 虚高、4 笔实为 M&A 混进 BD、Saniona TA「电线」垃圾值。

### Step 4 · merge + apply 修正
- 把 verified deal 写进 CSV(deal_type / upfront_musd / milestone_musd / total_musd / source_url)。
- apply cross-check corrections。
- 重算 `mnc_ma_deals_meta.json`。
- **公司名清洗**:中文统一(石药集团/信达生物/荣昌生物),去资产描述/ticker/（中国）。

### Step 5 · 刷其余层(脚本,顺序跑防 db 锁)
```bash
# ⚠️ SQLite 单写,不能并发 —— 顺序跑
uv run --with-requirements requirements.txt python jobs/fetch_eod.py          # 价格/benchmarks/multiples
uv run --with-requirements requirements.txt python jobs/fetch_sec_facts.py    # SEC 财报
uv run --with-requirements requirements.txt python jobs/build_peer_medians.py # peer median(SEC 后)
uv run --with-requirements requirements.txt python jobs/fetch_cn_benchmarks.py # iFind CN 基准
uv run --with-requirements requirements.txt python jobs/export_wiki_public.py  # LLM wiki 脱敏导出
```

### Step 6 · 上云
```bash
python3 -c "import datetime,pathlib; pathlib.Path('data/external/.last_refresh').write_text(datetime.date.today().isoformat())"
git add -A && git commit -m "data: funding + market refresh $(date +%Y-%m-%d)"
git push   # Streamlit Cloud 自动重新部署
```
> ⚠️ 硬约束(local-first ship gate):改动须 George 本地眼验、明说「可以 ship」才 push。

## 自动检测(SessionStart hook)
开 cc 在本文件夹 → `.claude/hooks/funding-staleness.mjs` 读 `data/external/.last_refresh`,超过 **7 天**注入提示「funding 数据 N 天未刷,跑 docs/funding-pipeline.md」。hook 只检测,不调 MCP;实际刷由分析师在 session 内跑本管道。

## 边界(诚实)
- deal(M&A+BD)必须分析师在环:web 查 + 分类 + biotech 核 + **人拍板值冲突**。~月度,触发时 ~30-60 min。
- SEC/价格:GitHub Action cron 已每日自动;本地刷只为「一次性全量上云」。
- 报告 BD(2025 那批):George 出新 ED Funding 报告时重抽 TABLE 59 覆盖。
