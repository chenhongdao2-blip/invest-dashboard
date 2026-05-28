# GLM 5.1 — mode: review
> 20260528-113753 | input=2202 output=1641 cached=0

## System
```
你是 senior reviewer for 投研 + 国内 SDK / 中文 code / 中文 docs。任务：对下面的 output 做 balanced critical review。重点视角：1. 中文 phrasing / 卖方研报口径 (CMS HK house style 偏好) 2. 中文 SDK / 中文 path / 国内 ops gotchas 3. 国内 framework: 集采/医保谈判/VBP/DRG/CSRC/NMPA 4. 跨域 (医药 + finance + 中国 capital market) 盲点 5. 数字 fidelity / 事实准确性 / 跨域 misuse 输出格式：[BLOCKER]/[MAJOR]/[MINOR]/[NIT] 严重性标注，每条带具体 evidence，不和稀泥但不切换立场，中文输出简洁。
```
## Prompt
```
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
- public Streaml...[truncated]
```

## Response
作为 CMSI HK Healthcare 组的 Senior Reviewer，基于 George Chen 的使用场景（Daily quick scan 补充，手工 Bloomberg 为主，国内/跨境多市场覆盖），对该 Dashboard 输出进行以下代码与投研业务逻辑审查：

### [BLOCKER] (必须修改，否则上线会引起投研合规或数据事故)

**1. Cover List 资产范围界定失真 (Missing 18A / 真实 cover gap)**
*   **Evidence**: 28 ticker 的 "CMSI HK Healthcare Cover List" 明显缺失核心中国生物科技资产。CMSI 真实的 A+H biotech cover 通常必含 2269 (药明生物)、1801 (信达) 等，且 18A 核心标的如 9926 (康方生物)、9688 (再鼎医药)、6994 (和铂医药) 毫无踪迹。此外，港股医药牛市的风向标 600276.SS (恒瑞医药) 居然不在 A 股 3 个席位内（仅有迈瑞/新产业/亚辉龙），这在跨区资金对比上不可接受。
*   **Impact**: 该 Dashboard 无法反映团队真实的推介标的池，作为 daily scan 遗漏核心 Alpha 标的，属于投研框架缺失。需 George 确认这是否为刻意精简，否则必须补齐核心 18A/Biotech 标的。

**2. 缺失核心 A/H 股卖方高频指标：港股通 / 南北向资金**
*   **Evidence**: 审查视角第 8 点提到 Dashboard 缺失“港股通持股比例 / 北向资金”。对于 CMSI HK 这种深耕中国 Healthcare 的卖方团队，A/H 股的生物医药估值极大程度由南向/北向资金定价（尤其是 1177, 2269 等大票）。如果不做 CCASS (中央结算系统) 持仓或北向资金净流入的每日高频扫描，这个 Dashboard 对中资/港股医药股的 daily scan 价值趋近于零。
*   **Impact**: 完全脱离国内卖方投研习惯。必须至少加入 Sino / Futu 的北向资金每日净流入 Quick API（yfinance 无此数据，需考虑 Futu OpenD 或 Tushare 接入）。

### [MAJOR] (影响投研专业度或准确性，建议优先排期)

**3. 核心标的跨分类硬伤 (IQV / CRM 定位)**
*   **Evidence**: CRM (Salesforce) 放入 "Healthcare + AI" 板块，这在国内医药投研框架里极违和，国内通常将其归为“医疗信息化/软件 SaaS”或放入 TMT 组覆盖；IQVIA (IQV) 放在 CXO + HC_AI 交叉是对的（本质上它是全球最大的 CSO + 数据 SaaS），但 Dashboard UI 展示时必须打上双重标签。
*   **Impact**: 容易引起买方客户挑战分类标准。建议严格按 GICS 行业标准做一级映射，再附上 AI/Tech 的主题 Tag。

**4. 中文投研语境与显示口径错位 (Sell-side style gap)**
*   **Evidence**: 默认显示 `name_en` 且按 ticker alpha 排序。中国卖方日常对接的买方（公募/险资/外资 China Fund）都是看中文习惯，比如 “信达生物” 优先于 “Innovent Bio”。且排序默认必须是 Market Cap Desc (按市值降序) 或 YTD Return。
*   **Impact**: 增加分析师日常阅读摩擦力。需修改前端 Streamlit 默认配置：`name_cn` 作为第一列并固定，默认按 `market_cap_usd` 降序。

**5. 日本/亚洲中盘标的拉低估值中位数 (PeptiDream / 4587.T)**
*   **Evidence**: 4587.T (PeptiDream) 市值仅 $900M，与 GILD/VRTX 等 $100B+ 大药厂同放在 Biotech (16) 且计算板块平均 Forward P/E，会严重扭曲整体估值中枢。
*   **Impact**: 卖方讲究 Large/Mid/Small cap 拆分定价。建议将 Biotech 细分拆为 "Large-cap Biopharma" 和 "Mid-cap Biotech/Speculative"，或者在 Dashboard 加权时剔除极小市值（< $5B）标的。

**6. 命名与 UI 风格不符 House Style (Toy-ish)**
*   **Evidence**: Repo 名 `invest-dashboard` 太泛，UI 使用大量 emoji（🏥🔥💎）。CMSI 作为顶流外资大行的卖方团队，向买方发送的 Daily Snapshot 若带此风格显得极不专业。
*   **Impact**: 品牌合规风险。建议重命名为 `cmsi-hc-daily-tracker` 或 `cmsi-hc-monitor`；剔除 UI 中所有非必要 emoji，回归严肃的 `Altair` / `Plotly` 原生 Business 主题色板（蓝/白/深灰）。

### [MINOR] (优化体验，国内 Ops / 部署相关)

**7. yfinance 国内 Ops 连通性阻断**
*   **Evidence**: 虽说明确了 Actions 在 M$ Server 跑没问题，但如果 George 在 HK/内地 office 本地 run `streamlit run app.py` 拉取实时数据，需要稳定的 proxy。若 `yfinance` 依赖 `yahoo` 的 cookie 验证，在国内网络极易报 `403/Timeout`。
*   **Fix**: 确保本地 `.env` 强制读取 `HTTP_PROXY=http://127.0.0.1:7897`，并在 README 用中文写明国内 Ops 依赖。

**8. 缺失国内政策周期 Calendar (集采 / 国谈 Overlay)**
*   **Evidence**: Dashboard 是 pure quant (P/E, Market cap, YTD)，完全剥离了政策面。国内 HC 投研最大的 Margin 变量是“国采 (VBP)”与“医保谈判 (NRDL)”。
*   **Fix**: P2 需加入一个简易的 Markdown/JSON policy calendar：例如标注每年 6 月/11 月的国采批次截点，以及 11 月底 NRDL 谈判落地日，作为 Tooltip overlay 在 Time-series 上。

### [NIT] (代码细节/一致性)

**9. 港股代码规范化**
*   **Evidence**: 4587.T, 7747.T, 6869.HK 等。日本与港股后缀处理在 yfinance 里没问题，但在 Dashboard 显示时，中文研报习惯统一省略后缀或加括号说明。例如：`PeptiDream (4587 JP)`，`WuXi Bio (2269 HK)`，`Mindray (300760 CH)`。建议前端格式化函数统一转为此 Bloomberg 通用的 Ticker 格式。

**10. ONC (BeOne Medicines) 历史回溯 Bug 隐患**
*   **Evidence**: BGNE 更名为 ONC，yfinance 在处理此类 corporate action 时，历史 Price 有时会出现非复权断层。由于 Dashboard 只做 12M fwd 和 trailing，影响有限，但计算 YTD 走势时如果底层数据未做 Adjusted Close 校准，K 线图会有假断崖。开发者需在 fetcher 层写死 `auto_adjust=True`。
