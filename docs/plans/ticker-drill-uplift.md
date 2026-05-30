# Ticker Drill 个股详情页 — 质感提升 plan

> Provenance: financial-strategist + designer 两 agent 讨论稿 → /cccg 四模型评审
> (实际 3-way: Claude + Codex gpt-5.5 + GLM 5.1；Gemini lane 被国内 geo-block 拦下).
> Date: 2026-05-30 · Owner: George Chen (CMS HK)
> Target file: `app/pages/6_🔍_Ticker_Drill.py` (+ `lib/theme.py`, `lib/i18n.py`, `lib/sec_facts.py` 复用)

---

## 0. 评审定论（一句话）

方向两个 agent 都对（首屏放了静态 reference、把决策信号埋下），但有 **3 道护栏不能省**，落地顺序按复杂度重排：先 Header+Variant(零风险/已落库数据)，相对强弱图次之(有对齐坑)，SEC 趋势殿后(仅美股有效)。

## 1. 三道护栏（Codex + GLM 一致 / 合规红线）

- **G1 [BLOCKER-if-naive] SEC 趋势必须 US-only + 上市地路由.** `sec_kpi_map` 绑 US-GAAP/SEC XBRL；港股 18A=HKFRS/IFRS、科创板=PRC CAS → 港股/A股票整列空白。复用 `lib.sec_facts`，US-only graceful fallback，**不**在页面解 gzip。(Codex MAJOR + GLM MAJOR)
- **G2 [MAJOR] Consensus rating 信源弱 + 合规.** yfinance `recommendation_mean` LOW 可靠性、港股 18A 覆盖极低。把 Yahoo 共识与 CMS 自家 TP 并排 = 卖方合规风险。必须：① 重命名「市场一致预期 · 仅供参考」② 组件底强制免责 ③ 无分析师覆盖时**隐藏**该组件。(GLM MAJOR)
- **G3 [MAJOR] 相对强弱图须共同交易日 anchor.** benchmarks 137d vs prices 179d；起点差会被误当 alpha。inner-join 共同交易日，anchor=首个共同日，图注 `Rebased to 100 on YYYY-MM-DD`。sector→基准要显式 mapping+fallback（多 sector 票 + 无 CXO/HC-AI 指数）；港股标基准口径(FX/市场差)。(Codex MAJOR)

## 2. 三个设计待裁点（已裁）

- (a) **不加 [NN/07] 页码** → 跟 `theme.py` 代码（已移除），改 `DESIGN.md` 文档。designer 判对。
- (b) **纵向混合表保留 `st.table`** + 补 `text-align:right` + tabular CSS → **不违反** §0.3。designer 判对，Codex 确认。
- (c) **sector chip teal 撞 UP teal** → 不止「只染边」，直接把 sector 色**重映射**到 palette 非 UP/DOWN/RED 色（blue/olive/brown）。Codex 微调 designer 方案。

## 3. 落地顺序

| 阶段 | 内容 | 风险 | 数据 | 状态 |
|------|------|------|------|------|
| **P0** | Header hero 重做(kpi_strip 4卡，只 TP upside 染色) + **Variant 三栏**(内部观点/市场一致预期/预期差，带 G2 合规护栏) | 低 | `recommendation_mean`+wiki rating/tp，全现成 | ✅ DONE (AppTest 验证) |
| **P1** | 绝对价单线 → **相对强弱图**，前置 G3(基准路由 + 共同日 anchor + 口径标注) | 中 | benchmarks+prices | ✅ DONE (anchor=2025-11-11 共同日，非个股 9/22 起点；US/HK 均渲染；无重叠数据回退绝对价) |
| **P1.5** | **本币切换**(个股不用 USD 用本币) + **区域基准路由**(用户要求: HK 不该对标美股 biotech) | 中 | iFind HSHCI + yfinance 512170 | ✅ DONE: HK→恒生医疗保健 HSHCI(iFind seed)+恒指(HKD) / A股→中证医疗512170(CNY) / US→sector ETF+XLV(USD)；个股 USD→本币(get_close_series)；同币种对照无汇率噪音。HSHCI 走 iFind seed CSV(cron 够不到 iFind)，jobs/fetch_cn_benchmarks.py 灌库 |
| **P2** | Extended fundamentals → **SEC 多期趋势**(US-only，复用 sec_facts，只画 Revenue/R&D/Cash，runway 标公式+period end) | 高 | SEC XBRL 仅美股 | ✅ DONE: 3 趋势(自适应 bn/mn)+YoY+biotech 现金跑道; 非美股 graceful fallback(IFRS/CAS 不适配); sec_facts.kpi_timeseries+charts.mini_trend_chart; 离线只读 DB; AppTest BIIB/LLY/1530/300760 全过 |
| 顺手 | section 标题统一 section_header / 删 st.divider / chip 系统(sector 避 teal) | 低 | 纯设计债 | 随 P0/P1 带 |
| **暂缓** | 估值历史分位 | — | multiples 仅 2 天历史=假数据，等 cron 累积 3-6 月 | hold |

## 4. P0 验收 checklist

- [ ] Header 4 张 KPI 卡走 `theme.kpi_strip`/`kpi_metric`，**只有 TP Upside 染色**(up=teal/down=red)，价/市值/PE flat 黑字
- [ ] Variant 三栏：内部观点(CMS HK) | 市场一致预期 · 仅供参考 | 预期差，bilingual
- [ ] G2 合规：consensus 重命名 + 免责 caption + **无 n_analysts 覆盖时隐藏** Variant
- [ ] Variant 仅在「有内部 house view(wiki rating/tp 且非 sanitized)」时渲染，避免云端空卡
- [ ] 新增 i18n keys 中英双版齐全；`recommendation_mean` 1-5 → 标签按 1.5/2.5/3.5/4.5 切档
- [ ] `python -m py_compile` 通过；streamlit 启动无 import/key 报错
- [ ] anti-slop：no emoji / hairline / tabular / 染字不染底 全过

## 5. 已知坑（来自 handoff）

- 改 `theme.py`/`lib` 函数签名后 **云端必 Reboot app**（Streamlit Cloud 热重载用缓存旧子模块 → 假错）。P0 只加 i18n key + 用现有 helper，不改签名，风险低。
