# Plan — Strategy Picks 打磨：双语(顶栏切换) + 双口径 rebalance + 溯源说明

> Provenance plan. 起因：用户(资深医药卖方)从客户视角提的 Strategy Picks 反馈。
> 已过 `/cccg` 动手前 gate(3-way: Claude+Codex+GLM；Gemini lane 地域封锁降级)。
> Date: 2026-05-29 · Status: AWAITING GREENLIGHT(consult 模式，未动 app 码)

## 0. 用户决策(已定)
- **A/B**：走 A(落 plan)；B 的内容缺口由用户提供的源材料补齐(已读)。
- **语言切换**：放**最顶栏**(非侧边栏)，中/EN 切换按钮。
- **中文表达**：由 **GLM 参与执行和决策**(cg-call.py)，术语 + 文案定稿过 GLM。

## 1. 源材料(已溯源，零"待确认")
| 策略 | 来源文件 | 关键口径 |
|---|---|---|
| Biotech v4/v5 | `~/Desktop/🧬 US Biotech AI选股系统/` 白皮书 + 投资人简版 | 全市场美股 biotech 扫描；5维(管线40/催化25/并购20/财务10/风险5)；市值分线 Line A≥$30B 大盘对标XBI / Line B $1-30B 中小盘追10x；v4=27回看/v5=40 catalyst-monitor；月度出新版、版内不调仓；诚实口径(24日小样本/AI主观60%权重/hindsight haircut 3-5%/v5.2前 not investable-grade) |
| HK 高股息 | `high-dividend-scoring/methodology.md` + scoring-rubric + 官方 CN/EN 报告(20260320) | 港股~2500→硬筛(日均成交>5kw港元/股息率TTM>5%/ROE>7%/派息率30-80%/安全垫>3/FCF>股息支出；金融地产豁免现金流)→34；100分制(治理55愿意分+财务25分得出+护城河20分得久)；≥80优秀(招行87)；静态高息**不作评分依据**；基准3110.HK；哲学:巴菲特/芒格/马克斯/格雷厄姆 |

> 官方高股息报告本身有 CN+EN 双版 → 双语术语的权威来源。

## 2. /cccg 审计升级的 4 个硬 GATE
1. **rebalance 算法**：月度再平衡 = 日收益链式累乘、月末当日收盘重置等权、下一交易日生效；**不能**用现 indexed-mean 冒充调仓组合。
2. **图表口径统一**：compute 一次；`charts.py:80-82` 不再独立用 `closes.iloc[0]+mean` 重算 → 传序列进图，否则图/metric/表三个数。
3. **i18n × cache**：翻译只在 render 层；**绝不**在 `@st.cache_data` 函数内读 `session_state["lang"]`(cache key 不含 lang → 返回旧语言)；缓存只存 raw data。入口 `streamlit_app.py` 统一初始化 lang(否则半中半英)。
4. **数学 oracle 单测**：`tests/test_strategy.py` 固定价格矩阵手算验证两条线 + 边界(pick_date非交易日/首日NaN/整月停牌ffill/benchmark短于组合)。

## 3. 审计 reconcile(带证据，已处置)
- GLM「高股息 price-return vs benchmark total-return 错配」→ **降级为披露**：`strategy.py:90` picks 与 benchmark 同走 `auto_adjust=True` → 两边已含息，数字无系统错配；只需 methodology 写明"已含息"。按 GLM 原样"手动加回股息"反而二次加息算错。
- Codex「US/HK calendar 不同日归一」→ **降级**：每策略单市场(biotech全美/高股息全港)，跨日历不存在；残留=个股首日缺价 skipna 早剔致权重重分配(保留 MAJOR)。
- GLM「biotech 风格敞口缺失」→ **由源材料解决**：方法论本就市值分线，说明写明 Line A/B + 为何 XBI。

## 4. 架构
- `app/lib/i18n.py`：`t("page.section.key")` + `init_lang()` + `render_lang_toggle()`(顶栏右上，CSS 定位；共享 helper 每页顶部调用，state 经 session_state 持久)。
- `app/lib/locales/zh.py` + `en.py`：dict；**锁定术语表**(GLM)：rebalance=再平衡 / turnover(v4→v5)=调仓(严禁混用) / 股息率 / 等权 / 成立至今 / 买入持有 / 股票池 / 催化事件(非催化剂)。
- `lib/strategy.py`：`compute_strategy_returns` 返回增 `portfolio_rebalanced`；月度参数化(默认 M)。
- 双线图：默认"买入持有"实线；"月度再平衡"虚线 + sidebar 开关(沿用 Show individual lines 模式，避免两实线打架)。
- metric：`+15.2%(买入持有) | +14.8%(月度再平衡 | Δ-40bp)`。

## 5. 分期
- **Phase 1**(任务1+2+3+4)：Strategy Picks 页双语 + 双口径 + 说明 + 美化，本地实测 → 给用户审。
- **Phase 2**(任务5)：i18n 扫全其余 6 页 + theme/ui 共享件；入口统一 lang；ship 前 /cccg 或 verifier(GLM lane) → commit + push + 云端验收。

## 6. 待用户 greenlight
- rebalance 对照默认**按月**(v4→v5≈月度，口径自洽) — 确认？
- 策略说明定稿(见对话) — 数字/口径 OK？
