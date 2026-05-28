你是 CMSI HK 医药/healthcare 组 senior reviewer。审一个 sell-side dashboard 项目，重点找**中文卖方 / 国内投研 / 中文 SDK** 盲点。

**仓库 public**：https://github.com/chenhongdao2-blip/invest-dashboard
**三个 commit**：`7f71a91` (D1) / `3157451` (D2) / `17f2f17` (D3)

**目标**：George Chen (CMSI HK healthcare analyst) 的多领域 sell-side dashboard，首期 Healthcare 7 板块，未来加 AI 等。手工 Bloomberg Excel 多年份 25E/26E/27E forward P/E **不被替代**，dashboard 是 daily quick scan 补充。

**已完成 D1-D3**：
- 仓库脚手架 + 8 个 sector YAML
- yfinance 数据 fetcher（FX 转 USD）+ GitHub Actions cron (22:30 UTC US 收盘 + 09:00 UTC HK 收盘，跑在 Microsoft server)
- Streamlit 3 个 page：Home / Healthcare 板块概览 / Sector Heatmap

**Healthcare 7 板块定义**（97 ticker，含 cross-membership）：
- **Biotech (16)**: GILD/VRTX/REGN/ARGX/ALNY/BNTX/BIIB/ONC/MRNA/RPRX/GMAB/NBIX/INCY/BMRN/RVMD/4587.T
- **Hospital Care (10)**: HCA/THC/UHS/DVA/EHC/CHE/ENSG/SEM/OPCH/ACHC
- **Healthcare + AI (13)**: CRM/ISRG/HIMS/VEEV/IQV/6618.HK/DOCS/TEM/HQY/RXRX/2506.HK/OMCL/2413.T
- **Managed Care (10)**: UNH/ELV/HCA/CI/CVS/HUM/CNC/MOH/THC/UHS
- **Medtech (13)**: ABT/ISRG/SYK/BSX/MDT/BDX/EW/ALC/GEHC/RMD/4543.T/7747.T/6869.T
- **CXO & Life Sci (14)**: TMO/DHR/207940.KS/LZAGY/IQV/A/IDXX/MTD/WAT/LH/ILMN/MEDP/CRL/ICLR
- **Pharma (16)**: LLY/NVO/JNJ/ABBV/MRK/RHHBY/NVS/AZN/AMGN/PFE/GSK/4502.T/4151.T/4506.T/4519.T/4568.T

**CMSI HK Healthcare Cover List (28 ticker)**：
- HK 15: 1093/1177/1530/1681/1801/2162/2256/2269/2359/2506/2616/2666/3320/3692/9995
- US 10: ALNY/BSX/GPCR/HCM/ISRG/LLY/NVS/ONC/TMO/VEEV
- CN A 3: 300760.SZ (迈瑞医疗) / 300832.SZ (新产业) / 688575.SS (亚辉龙)

**中文名 mapping（部分）**：
- 石药集团 = CSPC Pharmaceutical (1093.HK)
- 中国生物制药 = Sino Biopharm (1177.HK)
- 信达生物 = Innovent Bio (1801.HK)
- 翰森制药 = Hansoh Pharma (3692.HK)
- 药明康德 = WuXi AppTec (2359.HK)
- 药明生物 = WuXi Biologics (2269.HK)
- 百济神州 = BeOne Medicines (ONC, 原 BGNE)
- 迈瑞医疗 = Mindray (300760.SZ)

**技术取舍**：
- 估值仅 trailing P/E + 12M forward P/E（yfinance），**不做** 25E/26E/27E 多年份 forward
- 港股 yfinance 复权略糙（用户严肃 backtest 用 Futu，dashboard 不重叠）
- public Streamlit Cloud 部署，无 password gate（用户 confirm OK）
- dashboard UI 大量用 emoji：🏥🔥💎🧬💰🔍📊🌐

**审查角度（重点找 sell-side / 国内 盲点）**：

1. **板块划分准确性**：
   - CRM (Salesforce Health Cloud) 算 Healthcare+AI 板块吗？或者应该单独归 Software/SaaS？
   - IQV (IQVIA) 跨域 cxo + hc_ai，对吗？
   - 4587.T (PeptiDream) 在 Biotech 但市值仅 $904M，跟其他 large-cap biotech 一起看会不会失真？
   - 缺失：和铂医药 / 君实生物 / 复星医药 / 恒瑞医药 / 三生制药 / etc 应该不应该加 cover？

2. **CMSI cover list 28 ticker 是否真实 CMSI HK Healthcare cover**：
   - 没看到 CMSI 通常 cover 的：和铂医药、再鼎医药、康方生物、信达制药、Burning Rock Biotech、君实生物、复宏汉霖
   - 没看到 18A 通常 cover 的：科伦博泰、康宁杰瑞、亚盛医药、加科思
   - 没看到 AI/digital health：腾盛博药、晶泰科技 (2228 HK)、英矽智能 (3696 HK)
   - 28 个看着像 "George 关心的子集"，可能不是 CMSI **官方 cover list**

3. **中文卖方研报口径 vs dashboard 字段**：
   - dashboard 默认显示 name_en（英文名），sell-side 中文研报通常用 name_cn 优先
   - 默认排序按 ticker alpha，中文卖方更习惯按 market cap desc 或 YTD return desc
   - 没有"评级" / "目标价" 字段 — 卖方核心 framework 缺失（用户原 Excel 也没有，OK 但 P2 可加）

4. **国内 ops gotchas**：
   - yfinance 在国内访问：GitHub Actions 在 Microsoft server 跑，跑数据 OK；但用户本地 dev 时拉 yfinance 可能要 proxy `127.0.0.1:7897`（已在用户 CLAUDE.md）
   - SQLite commit 到 GitHub 后，国内访问 raw.githubusercontent.com 偶尔失败 — Streamlit Cloud 自身没问题
   - 港股 yfinance 复权数据：用户已用 Futu 替代严肃场景，dashboard 不重叠

5. **国内 framework 在 dashboard 中应不应该有**：
   - **集采 / 国采**: 影响 HK pharma 板块定价（1093 石药 / 1177 中生制药 / 3692 翰森都受影响）— dashboard 是否该加"近期集采事件" overlay？
   - **医保谈判 / 国谈**: 每年 11-12 月，PD-1/CAR-T/innovative drug 价格直接受影响
   - **VBP/DRG/医保支付改革**: HCA/THC/UHS 不受影响，但 HK 民营医院（2666 环球医疗 / 3320 华润医药）受影响
   - **港股 18A/18C**: 1801 信达 / 2269 药明生物 等都是 18A 通过，IPO 阶段评分系统已有 ipo-score skill — dashboard 应该接吗？
   - **CSRC**: 影响 A 股 healthcare (300760 迈瑞 / 688575 亚辉龙)

6. **CMSI house style**：
   - Dashboard 大量 emoji（🏥🔥💎🧬💰🔍）— 卖方分析师 daily 用合适吗？或太"toy"？
   - 命名 "invest-dashboard" 太 generic，CMSI 团队是否接受？建议 "CMSI Healthcare Monitor" / "Tracker" / etc

7. **数据精度**：
   - yfinance market_cap_usd 经 FX 转 USD — HK 股 cap 算出来跟 Bloomberg 差多少？
   - 港股 ONC 在 yfinance 是 BeOne Medicines (BGNE renamed)，注意 historic price 切断没有
   - CN A 股 688575 用 .SS 是对的（yfinance 这么处理上海上交易所）

8. **缺失的 sell-side 必备视角**：
   - YTD 业绩对比同业 — 已有 (sector heatmap)
   - 卖方评级分布 — 缺
   - 财报日历 (近 1 个月内业绩公告日期) — 缺
   - 持仓变化（institutional ownership）— 缺
   - Short interest — 缺
   - **港股通持股比例 / 北向资金** — 这是中国卖方分析师每天看的，dashboard **完全缺失**

请用 [BLOCKER] / [MAJOR] / [MINOR] / [NIT] 标注严重性，中文输出，简洁不和稀泥。
