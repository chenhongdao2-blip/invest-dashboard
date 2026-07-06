# WAVE-3 SPEC — 眼验反馈三连修（Planner 宏观 spec，2026-07-05）

> Planner 出宏观 spec，**故意不过度指定实现细节**——可测试契约由 Builder↔Evaluator 在
> `contract-draft-builder.md` / `contract-critique-evaluator.md` 磁盘博弈后冻结为 `CONTRACT.md`。
> 背景探索与推荐方案（非强制）见 `~/.claude/plans/agent-mellow-snowglobe.md`。

## 缘起

Wave-1/2 reskin 全绿后（HEAD `154a36c`），George 本地眼验（:8599, local-first ship gate）提出 4 项：

## F1-toggle — 中英切换模块全站统一

- **现状**：策略页 banner 内是新版描边分段 `中|EN`（`strategy_banner.live_title()` 的 seg()，`?lang=` 真锚点 target=_self）；其余 **19 处调用点**（18 个 pages/*.py + app/home.py）仍是旧版实心红钮（`i18n.render_lang_toggle()`，st.button，i18n.py:241-260）。
- **目标**：全站视觉统一为策略页的分段控件样式。改动收敛在共享层（i18n.py），调用点零改动或近零改动；策略页 banner 内的 toggle 与其他页视觉一致（可共享 helper 防发散），BANR 契约项不许回归。
- **机制事实**：`?lang=` query-param → session_state 的读取逻辑现散在 `4_Strategy_Picks.py:41-43`，统一后应中心化（single source）。

## F2-pitch — strategy.pitch 文案换 B 口径（George 已拍板）

- 位置：`app/lib/locales/zh.py:20`（`strategy.pitch`）+ `en.py:17` 镜像。
- **中文定稿**（George 选定，逐字执行，不再发挥）：

  > **方法论** — 本页跟踪一套量化基本面（Quantamental）选股体系的实盘表现：以临床试验读出、FDA 审批进度、财报披露与公司治理事件为输入，按多维度评分筛选入池。**持仓自入选之日起登记在册**，业绩以原始记录为准复盘，盈亏均客观呈现。
  >
  > 下方三个策略展示**自选股日起的真实累计收益 vs 基准**（非回测美化）。

- 英文按上述镜像改写（financially professional，不逐词直译但语义/粗体结构对齐）。
- 约束：保持 `**…**` markdown 约定（BANR4 dek 包装器 `4_Strategy_Picks.py:146-149` 做 `**`→`<b>`、`\n\n`→`<br><br>`，包装器不动）；zh.py docstring 备注本次 supersede。

## F3-ipo-rank — IPO 评分排行表：列排序 + 图表 dock 重设计

- 位置：`app/lib/ipo_stage.py`（872 行，自包含 srcdoc HTML，`render()` 经 `st.iframe` 嵌入）。
- **缺陷 a（George 原话"filter 不能排序"）**：表头 8 列（#/代码/名称/评分/申购档/子板块/上市日期/首日涨幅）不可点击排序。目标：点列头升/降序切换，含排序方向指示。
- **缺陷 b（根因已确诊）**：`.dock{position:sticky;top:16px}` 无效——iframe 高度 = 全内容高（`render()` `max(2400, 900+n*33)` ≈ 2682px @54行），滚动发生在**父页面**，iframe 文档自己不滚 → sticky 永不触发 → 滚到第 29 名 hover 时右侧大图在视口外。目标：重设计使 **hover 任意行（含最后一行）时盘中大图始终可视**。推荐方向（非强制）：表格内滚容器 + 组件定高；Builder 可提替代方案但须过 Evaluator。
- **不许回归（wave-2 Codex 修复，数字级）**：d1 ×100 口径；None/NaN 诚实渲染 '—'；pending rank '—' + 待上市沉底语义；盘中路径末笔 NaN 整路径丢弃（ipo_stage.py:455-466）；终点=首日收盘锚（IPO12）。排序只动展示顺序，禁碰数值计算。
- `__main__` 自测须扩展覆盖新行为。

## F4-home-dedup — 首页双标题去重（George 已拍板"去掉旧标题"）

- `app/home.py:46-49` 旧 `theme.page_header("行情中枢")` 与 `home.py:237-256` 新 HUB masthead 同标题叠加 → 删旧留新。
- 旧 meta 中的 fetch 时间信息不得丢失（可折进 masthead 时间戳行）。
- 已核查：Healthcare/AI 页的 `so.masthead` 是页中段板块小节头，非重复，**不在本 wave 范围**。

## 全局约束

1. 分支 `feat/kline-reskin` 续跑；PR-based 禁直推 main；最终 ship gate = George 眼验。
2. lib 改动后验收必须重启 :8599（`bash docs/harness/kline-reskin/init.sh`）——Streamlit 热进程缓存 lib 模块。
3. wave-1（11/11）与 wave-2（85/85）已验收项不许回归；Evaluator 须抽查关键回归面。
4. Builder 物理碰不到 `CONTRACT.md` / `feature_list.json` / `eval/`（验收门归 Evaluator）。
5. 成本断路器：max 3 轮；连续 1 轮 0 新通过 → 停下回报 George。

## 角色路由

| 角色 | 载体 |
|---|---|
| Planner | 主循环（本文件） |
| 契约协商 | builder-negotiator agent ↔ evaluator-negotiator agent（磁盘 markdown） |
| Builder | Workflow 4 路并行（F1-F4 文件互不相交） |
| Evaluator | 独立 agent：py_compile + ipo_stage 自测 + AppTest + _build_html 静态 DOM 探针 + :8599 真机 |
| Auditor | Codex read-only（scripts/audit_code.sh 或 codex exec） |
