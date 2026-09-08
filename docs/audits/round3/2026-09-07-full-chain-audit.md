# invest-dashboard 全链路审查（Round 3）

日期：2026-09-07 · 审查者：Claude（6 条并行审查线 + 本机实测）· 分支：`feat/e7-v3-map-ledger`
范围：一条数据从 GitHub Actions / 本地 job 进来 → SQLite / data/external → app/lib 访问层 → Streamlit 页面渲染的全部路径。
目标：找出逻辑错误、伤用户体验的行为、性能大幅下降点、过度设计；给出性能最高、结构最简的目标架构。
证据：所有数字均为本机实测或对 `data/snapshots.db` 直接查询（截至 2026-09-07），标 `[未核实]` 的除外。

---

## 0. 结论先说

1. **性能不是这套系统的主要问题**。19 个页面 warm 渲染全部 < 0.35 s，只有 Strategy Picks 冷启动 9.5 s（页面加载时同步拉 yfinance）。真正的性能债集中在三处：Strategy Picks 的实时拉取、497 只全量 `compute_returns` 未缓存、SEC 页 `comp_table` 每次 rerun 重算。
2. **正确性才是主要问题**：有 6 处会把错数字摆在用户面前，其中 YTD 锚点错误影响每一个 YTD 列（490 只票中位误差 2.4pp、最大 86pp），SEC 年度过滤把 Q4 当全年（150 只票里已有 33 行错）。
3. **失败不留痕**：三次运行失败（08-29 ×2、09-01）manifest 无任何记录，09-01 是 `snapshots.db` 二进制 rebase 冲突把重试循环卡死。新鲜度审计寄生在被监控的 job 里。（初稿写的「管线黑 9 天」是本地 clone 落后所致，已更正。）
4. **仓库结构债**：`.git` 5.45 GiB 松散对象，`snapshots.db` 在历史里存了 205 个版本共 10.9 GB；README 自己定的迁移阈值（pack > 200 MB）早已越过。
5. **过度设计集中在"同一件事写了三遍"**：HC↔AI 页面对约 513 行逐字重复，三条策略对比曲线函数约 350 行重复，4 个 HTML 表构建器各自内嵌 CSS+JS，54 个 job 里 24 个是一次性脚本、11 个从未进 git。

---

## 1. 链路图与每段的核心缺陷

```
[GitHub Actions ×4] ──┐
   fetch_eod / public_data / sec_facts / earnings_cal
[本地 job ×18 recurring + 24 one-off] ──┤
                                        ▼
                 data/snapshots.db (67 MB, git 提交)   data/external/*.json|csv
                                        ▼
                 app/lib/db.py (+~50 个 lib 模块, @st.cache_data)
                                        ▼
                 20 个 Streamlit 页面 (HC 9 / AI 5 / ETF 3 / 通用 3)
```

| 段 | 核心缺陷 | 严重度 |
|---|---|---|
| Ingest | 失败不留痕、半更新提交或整天丢弃、UTC 日期戳与交易所日期错位、`multiples_daily` 从冻结 `.info` 造假序列 | Critical |
| Storage | 67 MB 可变二进制当版本单元；每日重写 30× 于真实增量；`sec_company` 40 MB 压缩 blob 每周整表重写 | High |
| Access | YTD 锚点错；`_mtime` 缓存失效是空操作；`compute_returns` 未缓存；同一行数据 4 次宽拉 | Critical |
| Render | 估值扫描器缓存键忽略板块；列表页与个股页同一票不同收益率且无币种标签；退市票混入行情表 | Critical |

---

## 2. Critical — 用户看到错数字

| # | 问题 | 位置 | 证据 |
|---|---|---|---|
| C1 | **YTD 锚在当年第一个收盘价，而非上年末收盘价**。`shown = (1+true)/(1+jan_gap) − 1`，乘性偏差 | `app/lib/db.py:195-200`；`4_Strategy_Picks.py:281` 取数起点同错 | 490 只票实测：中位 \|误差\| 2.40pp，均值 4.67pp，p90 10.6pp，最大 86.0pp；205 只偏差 > 3pp。SNDK 显示 +439.5% 真值 +525.6%；MU +195.8% vs +226.8% |
| C2 | **SEC 年度过滤放行 3 个月区间**。`fp=="FY"` 在 10-K 里也标 Q4 的 91 天行；`_rank` 按 (end_date, filed) 排序两行同键，非稳定 quicksort 决定谁赢 | `app/lib/sec_facts.py:403,420` | 150 只票：231 个歧义期组，33 行短区间值胜出。AGIO FY2014 Revenues 显示 14,636,000，真值 65,358,000（4.5× 低估）；ADI EPS FY2013 显示 0.64 真值 2.14 |
| C3 | **估值扫描器板块分位数缓存键忽略输入**。`_mults_df` / `_sector_map` 带下划线被 Streamlit 排除，只哈希 `pe_col`（2 个值）；换板块 300 s 内返回上一个板块的分位数 | `5_Valuation_Scanner.py:126-127`，`a4_ai_valuation.py:131` | 代码结构证实；`6_Ticker_Drill.py:347-349` 自己已记录过这条规则 |
| C4 | **失败不留痕**（原判「管线黑 9 天」已更正：云端 Actions 正常，数据提交到 2026-09-05，是本地 clone 落后 15 个 commit 造成的错觉）。真实缺陷：08-29 两次、09-01 一次运行失败，manifest 无任何 `failed` 记录；09-01 失败原因是 `commit_data.sh` rebase 时 `snapshots.db` 二进制冲突，重试 5 次全部撞 "unmerged files"（即 H10 实发）。审计只在 `fetch_eod.yml:49` 内执行，job 死审计死；无 `if: failure()` | `.github/workflows/fetch_eod.yml:49`；`jobs/update_manifest.py:288`；`scripts/commit_data.sh` | `gh run list` 2026-09-07：09-01 public-data 失败日志 "Pulling is not possible because you have unmerged files"；`origin/main` 最新数据 commit e49308f 2026-09-05 |
| C5 | **`multiples_daily.last_price` 是冻结 `.info` 造出的假时间序列**。`info_to_multiple_row` 声明可返 None 实际永不返 None，`if row:` 恒真；无价格交叉校验 | `jobs/fetch_eod.py:344,523,536` | 10 只票单一常数跨 27-64 个快照：108320.KQ multiples 78,000 恒定，同日 prices_daily 36,550→37,800，**2.06× 分歧**；3 只 KR 票 market_cap_usd 为 NULL 静默掉出加权聚合 |
| C6 | **同一票在列表页与个股页收益率不同**。列表/扫描/热力图用 USD 收盘算窗口收益，个股页与轮动页用本币；两边都没标基准。`quote_table.py:111` 把 USD 换算价标成 "Last"，个股页头显示 `HKD 97.50` | `quote_table.py:94` vs `6_Ticker_Drill.py:436,552`；`3b_Sector_Rotation.py:151` | 港/日/中/韩票 1D/5D/YTD 差一个汇率变动 |

---

## 3. High

| # | 问题 | 位置 | 证据 |
|---|---|---|---|
| H1 | 高股息策略（总回报）对标 `^HSI` 价格指数，高估相对表现约一个 HSI 股息率 | `strategy.py:351-399`；`4_Strategy_Picks.py:928-931` | 机制确定，幅度 [未核实] |
| H2 | `_mtime` 缓存失效是空操作：下划线前缀参数不进缓存键，docstring 说反了 | `earnings_cal.py:19,57`；`strategy.py:56` | `streamlit/runtime/caching/cache_utils.py:509`；同仓库 `hc_overview.py:66` 写法正确 |
| H3 | 退市票混入全市场行情表，价格冻结 105-126 天无标记 | `quote_table.py:18-29` 无 status 过滤 | 511 行 vs 497 活跃 → 14 只退市（DAWN 停在 04-24，APLS 05-15） |
| H4 | fetch 部分失败：先逐批提交价格，再在 >10% 阈值处 raise → CI 里整天数据丢弃且无 failed 戳；本地则留半更新 70 MB DB 等待被 `git add` | `fetch_eod.py:485-493` | 代码结构 |
| H5 | 快照日期用 runner 的 UTC `date.today()`，价格日期用交易所 bar 日期 → `multiples_daily` 有 08-29 行而 `prices_daily` 没有；估值与收益率不同日 | `fetch_eod.py:444,447,280` | DB 实测 |
| H6 | SEC 季度报表丢 Q4：只保留 span ≤ 100 天，US GAAP 不单独标 Q4 三个月区间 | `sec_facts.py:405`；说明文字 `sec_statements.py:634-641` 未披露 | LLY/AMGN/VEEV 季度收入序列无任何 Q4 |
| H7 | `_chain_nav` 每次换仓丢一个交易日收益（段界 `<` 应为 `<=`） | `4_Strategy_Picks.py:792-800` | 两次换仓 = 两天 |
| H8 | `rank(pct=True)` 最低只能到 100/N，"deep value" 预设（≤15 分位）在 <7 只票的板块返回 0 行且无解释 | `5_Valuation_Scanner.py:46,148` | 数学 |
| H9 | BD 交易 $ 总额只覆盖 44% 行却对着全量条数展示 | `funding.py:583`；`9_HC_Capital_Markets.py:429` | 145/328 行有金额 |
| H10 | 两个 workflow 直接 push 不 rebase；本地 Mac 分支上还有未提交的 70 MB DB 与 bot 写同一路径，合并时二进制冲突整文件二选一 | `fetch_eod.yml:51-61`；`fetch_sec_facts.yml:47-56` | `git status` |
| H11 | `fix_splits` 只调 `prices_daily`，`multiples_daily`/`benchmarks_daily` 留在拆股前 | `fix_splits.py:44` | 代码 |
| H12 | EN 模式下 Top movers 名字永远是中文（`ticker_to_name()` 默认 `prefer_cn=True`） | `db.py:359`；4 个页面硬编码 | 代码 |
| H13 | 语言切换是真实 `<a href>` 整页 reload，丢全部 session_state（热力图窗口、板块选择全部复位） | `i18n.py:99-108` | 代码 |
| H14 | 5 个 ETF 测试失败（holdings 数据为空） | `tests/test_etf_panel.py` | `5 failed, 106 passed` |

---

## 4. Medium（摘要，详见各线原报告）

- `fetch_eod.py:121` 不过滤 status，18 只死票每天各吃 4 次 `.info` 重试与失败预算。
- `fix_splits` 的 `judged` 集合仅内存，32 处历史断点（MRNA/MLTX/2617.HK 真崩盘）每次 cron 重新下载复判。
- `058470.KQ` 与 `078000.KQ` 同一家公司未标 `secondary_listing`，等权聚合重复计数。
- `sec_company` 40 MB blob：`FRESH_HOURS=18` 配周频 cron → 每周整表重写；app 只用约 12 个概念。
- 无 schema 版本；`init_db._safe_alter` 与 `load_universe.ensure_status_column` 两套迁移路径。
- `sector_pe_percentile` 在两个 `__main__` 页面同名定义，只差一行，未来一改就撞缓存桶（仓库已为此付过一次学费：`db.py:18-29`）。
- `_has_column` 用 `with sqlite3.connect()` 不关连接。
- `get_close_series` 与 `get_close_series_usd` 拉同样的行两遍；Home 冷加载 4 次宽拉（约 520 ms 可省）；热力图板块循环 16 次 N+1 查询。
- `set_page_config` 在 19 个页面各调一次，入口没调；首帧先按 centered 渲染再变宽。
- IPO 覆盖层 `overlay_date` 算了从不显示；`closes.ffill()` 把停牌票的旧价当现价。
- `bd_canon_ta` / `bd_canon_phase` 不幂等，已规范化的值再过一次会退化为 Other。
- `fetch_picks_closes` 用 override 无条件覆盖实时价；FOLD 收益 = 0% 是未核实的注释断言。
- RRG 对历史不足的序列输出 (100,100) 点，视觉上落在 Leading 象限原点。

---

## 5. 性能实测（AppTest + 直接计时，本机，2026-09-07）

| 项 | 冷 | 暖 | 备注 |
|---|---|---|---|
| 4_Strategy_Picks | **9.46 s** | 0.13 s | 加载即同步拉 yfinance；`prices_daily` 已有同样数据 |
| home | 1.02 s | 0.29 s | 4 次宽拉 + 3 个各 1 MB 的 ECharts iframe |
| 2_Healthcare | 0.59 s | 0.26 s | 逐板块调 `compute_returns` |
| 其余 17 页 | ≤ 0.43 s | ≤ 0.33 s | 无问题 |
| `compute_returns`（497 只） | 235-330 ms | 每次 rerun 重算 | 唯一未缓存的热路径函数，滑块每动一格全跑 |
| SEC `comp_table`（10 票 × 5 KPI） | 1010 ms | 838 ms | 未缓存；`_load_facts` 单票 17 MB 常驻 ×2（pickle 副本）→ 1 GB Streamlit Cloud 的 OOM 路径 |
| `get_close_series`（497 只） | 63-70 ms | — | 索引命中，跨票 ORDER BY 需临时 B 树 |
| `sec_company` 单 blob 取 | 0.37 ms | — | **PK 索引，blob 设计本身没问题**；成本在解析后的 DataFrame |
| `theme.inject_css` | 32.7 ms 首次 | 0.35 ms | 38 KB CSS 每次 rerun 重发，可忽略 |
| 全部页面跑一遍峰值 RSS | 282 MB | — | 不含 SEC 多票选择 |

SQL 层全部索引命中，没有全表扫描问题。**性能瓶颈全在 Python 侧的重复计算与页面加载时的网络调用。**

---

## 6. 存储与仓库

- `.git`：5.45 GiB 松散对象（4231 个）+ 409 MiB 三个 pack；`git gc` 只跑过 3 次（07-29 / 08-12 / 08-29），无自动打包。
- `data/snapshots.db` 历史 205 个 blob 版本合计 10.9 GB，136 个仍松散。
- 每日重写：价格 5 日窗 2,460 行、基准 200 日窗 5,729 行（全表 34%）、`company_profile` 505 行含 625 KB 简介；`INSERT OR REPLACE` 删后重插改变页布局，git 视整个 67 MB 为新文件。从未 VACUUM。
- `data/` 下 11 份 `snapshots.db.bak-*` 共 452 MB（已 gitignore，但占盘）；`app/` 下 4 个 `.bak` 代码文件在 import 根目录里。
- 两个 workflow 各自再拉一遍 `URTH`/`CNY=X`/`HKD=X`（`fetch_eod.py:56` 与 `fetch_fx_world.py:31`，注释承认重复）。

---

## 7. 过度设计与死代码

| 类别 | 事实 |
|---|---|
| 页面复制 | `a5_ai_sec`↔`8_SEC_Facts` 共享 274/300 行（92%）；`a4`↔`5` 146 行（78%）；`a3`↔`3` 93 行（89%）。合计约 513 行，只差 `domain=="ai"` 一处。C2 的修复今天必须改两遍。ETF 页不是复制（e1↔a2 仅 13 行共享） |
| 三写一事 | `render_hd_compare`（176 行）、`render_biotech_compare`（163 行）、`_overview_curve_card` 第三次实现同一算路径，约 350 行可并为一个参数化函数 |
| 单调用点巨模块 | `ipo_stage.py` 1356 行只有约 80 行 Python 逻辑，其余是 CSS+JS+HTML 字符串，仅 `4_Strategy_Picks.py:1292` 一处调用，无测试 |
| HTML 表构建器 ×4 | `heat_table` / `coverage_table` / `picks_table` / `rrg` 各自拼接完整 HTML+CSS+JS 文档 |
| 为 32 行造搜索引擎 | `fix_splits` `while True` 全表重扫；一张 `price_adjustment(ticker,date,factor,verdict)` 表即可替代 |
| 用代码解 schema 问题 | `update_manifest.resolve_source_date` 120 行逐数据集 if/elif 解析器 |
| jobs/ | 54 个：CI 接线 10、本地周期 18、一次性/海报/xlsx 24；11 个从未进 git（含活跃的 `fetch_patsnap_deals.py`）；文档引用 3 个已不存在的 job |
| 零调用函数 | 31 个：`charts.py` 9 个、`funding.py` 整个退役 PitchBook 层 10 个、`format.py` 5 个、`home.py` 三个退役渲染函数 |
| 孤儿 | `7_Market_Data.py` 不在导航里；`app/static/house.css` 13.7 KB 无引用；`ui.render_styled_table` 自标 DEPRECATED 仍有 6 个调用点 |
| i18n | 两张 1,157 键的 locale 表**零漂移**，设计是对的；问题是被绕过：`home.py` 54 处、`sec_statements.py` 25 处、`rrg.py` 22 处、`charts.py` 19 处内联 `X if _prefer_cn else Y`，`4_Strategy_Picks.py:477-622` 145 行手写标签字典 |
| 4 个 workflow | 各自重复 checkout + pip + init_db + load_universe |

---

## 8. 目标架构

**一句话**：数据按可变性分层存、写入确定性化、访问层每个 domain 只建一次"市场帧"、页面按 domain 参数化而不是按 domain 复制。

### 8.1 Ingest 契约
- 每个 producer 写自己的 `<dataset>.meta.json`：`{as_of, rows, status, error}`；`update_manifest.py` 只聚合，删掉 120 行解析器。
- 新鲜度审计独立成一个 workflow，不寄生在任何 producer 里。
- 每个 workflow 加 `if: failure()` 步骤：写 `failed` 戳 + 开/更新 GitHub issue。零成本，C4 第一天就能抓到。
- 入库后一致性闸：`multiples_daily.last_price ≈ prices_daily.close` 同键同日；`count(distinct date)` 必须前进。C5 / H5 / H11 全部当场拦下。
- 所有 workflow 统一走 `scripts/commit_data.sh`；本地 Mac 走分支 + PR，不直接 push `data/snapshots.db`。
- `fetch_eod.py:121` 加 `WHERE status IS NULL`；`info_to_multiple_row` 真正返回 None；日期戳用交易所日期。
- 删掉重复的基准拉取；4 个 workflow 抽公共 composite action。

### 8.2 Storage
- **时序表 → Parquet 按 table/year 分区，DuckDB 零拷贝读**。旧年份分区跨提交字节相同，每日 diff 从 67 MB 塌到一个当年小文件；保留 git 审计轨迹、$0、Mac 可关机三个约束。
- **`sec_company` blob 出 git**：把 app 真用的约 40 个概念规范化成 `sec_fact` 表（几百 KB），重取只按 `latest_filed` 触发。
- 小配置表留 SQLite 或 YAML。
- 迁移前的零成本止血：`git gc`；每次提交前 `VACUUM`；`ON CONFLICT DO UPDATE ... WHERE excluded.close IS NOT close` 让未变行零页写；基准窗口改增量。
- `meta.schema_version` + 编号迁移脚本；删掉 `load_universe.py` 里的第二套迁移。

### 8.3 Access 层
- 每个 domain 一个缓存的 `market_frame(domain)`：本币与 USD 收盘、最新估值、名字、status，一次 TTL 建一次；`get_close_series` 两个变体合并；热力图 16 次查询变 1 次。
- `compute_returns` 加 `@st.cache_data`，向量化（按列 `pct_change` 而不是 Python 循环），先按市值过滤再算。
- 收益率列**每列固定一个币种基准并在表头标出**；YTD 锚改上年末收盘。
- 去掉 4 个下划线参数（H2 / C3）；`sector_pe_percentile` 搬进 `lib/`。
- Strategy Picks 从 `prices_daily` 取价，yfinance 只做补缺且延迟到 tab 打开。

### 8.4 Presentation
- HC / AI 页面对合并为一个文件，domain 来自导航或 query param（省约 513 行，修 bug 不再改两遍）。
- 三条策略对比曲线合成一个参数化函数（省约 350 行）。
- 内联 `_prefer_cn` 三元全部回 locale 表；locale 表加键集一致性测试。
- `set_page_config` 只在入口调一次；语言切换改 `session_state` + `st.rerun()`；Home 两个 treemap 合进一个 iframe，K 线延迟挂载。
- HTML 表构建器抽一个共享 `html_table(spec)`，CSS/JS 各只存一份。

### 8.5 回归测试（先于任何重构）
1. YTD 锚 = 上年末收盘（用 DB 里现成数据断言 SNDK）。
2. SEC 年度过滤：`AGIO FY2014 Revenues == 65,358,000`。
3. `sector_pe_percentile` 换板块结果不同。
4. 行情表不含 `status != NULL`。
5. HD 策略基准为总回报序列。

---

## 9. 分阶段顺序

**Day 1（≤ 2 小时，不动架构）**
C1 YTD 锚；C2 span 闸 + `mergesort`；C3/H2 去掉 4 处下划线；H3 + `fetch_eod` status 过滤；H12 `prefer_cn` 参数；`git gc`；4 个 workflow 加 `if: failure()` 戳；查清 08-29 之后 Actions 为何没跑；H14 修 ETF 测试或标数据过期。

**Week 1**
`compute_returns` 缓存 + `market_frame`；Strategy Picks 改读 `prices_daily`；合并 HC/AI 页面对；删死代码与 `.bak`（约 500 行 + 600 行 bak + 13.7 KB CSS）；统一 `commit_data.sh`；一致性闸；H1 换总回报基准；C6 标币种；H7 段界；H8 分位公式；H9 分母。

**Month 1**
Parquet + DuckDB 迁移；`sec_fact` 规范化与 blob 出 git；独立审计 workflow；schema 版本；`fix_splits` 改成裁决表；`update_manifest` 改成 sidecar 聚合。

---

## 10. 未核实与边界

- H1 的幅度（HSI 股息率对窗口的贡献）未取数验证，机制确定。
- 08-29 之后 Actions 停跑的直接原因没有 Actions 日志无法判断；缺陷在于 9 天静默是可能的。
- `rebalance_panel.py:113-120` 冻结基准与实时 v6 段的窗口是否精确衔接，依赖 `data/content/rebalance_v6.json` 里的 `to` 日期，未打开核对。
- 浏览器侧 ECharts 解析成本与语言切换 reload 时长是由资产大小推断，未用网络面板实测。
- round2 审计里 "D4 组合数学与 weekly_perf.py 不一致"、"ticker 别名搜索缺失" 两条，本轮未复核其当前状态。

各线原始报告（含完整 file:line 引用）在会话产物中；本文为去重与排序后的综合。
