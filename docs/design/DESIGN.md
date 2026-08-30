# CMSI Research Portal — Design System v2.0 (multi-domain)

> CMS International HK · Multi-Asset Research Desk · George Chen
> Stack: Streamlit 1.57 (CSS injection + `st.components.v1.html` for the data table)
> Style: FT editorial × sell-side institutional × 中信中金研报排版
> **v2.0 re-baseline (2026-05-29):** generalized from "Healthcare Research Portal" →
> **multi-domain investment & strategy portal** (医药 / AI·科技 / 宏观 / 策略表现 …).
> Direction (CMSI 红 × cream × FT density) unchanged — only scope widened + execution swapped.

> **Token values are NOT duplicated here.** `app/lib/theme.py` is the single source of
> truth for every hex / px / font value. This file is the *language, rationale, mapping,
> chart grammar, and pre-flight* — read it with `theme.py` open.

---

## 0. 设计原则 (Read this first)

1. **Density over decoration.** 卖方早会看密度。表格行高 36px、字 13px、tabular-nums。任何让单屏少看 3 行数据的装饰（圆角 >4px、阴影、肥 padding）都砍。
2. **Hairline, not box.** FT/中信研报没有 card-shadow。分组用 1px `paper-rule` 细线 + 2px `ink` 章节重线。**禁 box-shadow**。
3. **Tabular numbers everywhere.** 所有数字 cell `font-variant-numeric: tabular-nums`。这是散户 dashboard 与 sell-side 最大的视觉差。
4. **Color is a signal, not a fill.** 涨跌**只染字不染底**（heatmap 模式例外，且 tint ≤12% opacity）。大色块背景 = 散户。
5. **Type is the brand.** 不靠 logo，靠层级：UPPERCASE eyebrow + 大号 tabular 数字 + cream + CMSI 红。
6. **Cream is the canvas, red is the stamp.** `paper` 占 90% 面积，`cmsi-red` 只出现在：表头 eyebrow / 章节标号 / 跌幅 / active nav。
7. **No emoji. Use codes.** 锚点用 `[03 / 07]` 序号 + 4px ▎红竖条。Emoji 是消费级语言，机构 email / PDF / 富途 client 渲染不一致。

> **外部校验（ui-ux-pro-max DB, 2026-05-29）:** "Data-Dense Dashboard" 风格的 design
> variables —— `table-row-height: 36px / card-padding: 12px / sidebar-width: 240px /
> sticky headers` —— 与本 spec 几乎逐项吻合；"Swiss Modernism 2.0" 明确背书 *single accent
> + Inter + mathematical spacing*。即本方向通过了一个 161-rule 设计引擎的独立验证。

---

## 1. Multi-domain scope (v2.0 核心变更)

这个 portal **不锁单一行业**。它要装：医药覆盖、AI/科技覆盖、宏观看板、**多策略表现追踪**、IPO 打新、估值扫描。设计语言必须 domain-agnostic。

### 1.1 Sector 7 槽 — 行业无关语义（色值见 `theme.SECTOR_PALETTE`）

| Slot | 语义 | 用途 |
|------|------|------|
| s-1 (CMSI red) | **医药 Healthcare** | 创新药/CXO/器械/服务 统归一槽 |
| s-2 (teal)     | **AI · 科技 Tech** | AI/半导体/软件/互联网 |
| s-3 (dark gold)| **宏观 Macro** | 利率/汇率/商品/指数 |
| s-4 (slate blue)| **消费 Consumer** | 必选/可选消费 |
| s-5 (plum)     | **金融 Financials** | 银行/保险/券商 |
| s-6 (olive)    | **策略 Strategy** | 选股策略/因子/组合 |
| s-7 (sepia)    | **其他 Other** | 周期/公用/未分类 |

> 旧 v1 的「创新药/CXO/医疗器械」细分**收敛进 s-1 一个槽**。细分行业若需区分，在医药专页内部用次级色阶，不占顶层 7 槽。

### 1.2 Brand 措辞

- Sidebar brand: `CMSI` + 副标 `招商证券国际 · MULTI-ASSET RESEARCH`（v1 是 `HC RESEARCH`）。
- Page footer / status: `CMSI · MULTI-ASSET RESEARCH · INTERNAL USE`。

---

## 2. Typography / Color / Spacing

→ **全部 token 值在 `app/lib/theme.py`**：`FONT_STACK`（Inter + PingFang/Noto CN fallback 显式 chain）、`PLOTLY_LAYOUT`、color tokens（paper 5 阶 / ink 4 阶 / brand 4 阶 / up·down 各 3 阶 / sector 7 阶）。

硬规则（不在 theme.py 里、属于语言约定）：
- H1/H2/H3 **永远黑色**，红只配合 4px ▎竖条出现，标题字本身黑。
- `-` 跌幅用 ASCII hyphen，**不用** unicode `−`（copy 时蛋疼）。
- 中文不开 italic；英文 italic 仅用于 latin 公司名补注。
- font-size **任何位置 ≥ 11px**。

### 2.1 Emoji 替代锚点（v1.0 §6 并入，2026-08-30）

§0.7 禁 emoji 后，靠这四个锚点承担"视觉定位"职能：

| 位置 | 锚点 | 规格 |
|------|------|------|
| 页面标题前 | `[03 / 07]` 序号 | mono · ink-3 · 11px |
| Section h2 | 4px ▎红竖条 + 标题 | 标题字本身黑（见 §2 硬规则） |
| Ticker 前缀 | 1-2 字母 region chip | `HK` / `US` / `CN` |
| KPI label | UPPERCASE eyebrow + 末尾 ▎红条 | tracking 放宽 |

补充理由（v1.0 原文）：emoji 在富途/同花顺 client、Windows、PDF 导出、机构 email 转发时渲染各不相同，**部分 GB 字体直接缺字**（如 🧬 显示成豆腐块）。卖方研报从不出现 emoji。

---

## 3. Page mapping (v2.0 — 容纳策略表现)

| 页面 | 上方组件 | 主区组件 | Eyebrow |
|------|----------|----------|---------|
| Home | KPI strip ×5 (指数) | Benchmark 表 + Top Movers | [01 / 07] |
| Ticker Drill | Ticker hero + chips | Price chart + Multiples KPI + Memo | [02 / 07] |
| **Coverage** | Tabs (region/sector) | **主表 HTML (任意 universe)** + heatmap toggle | [03 / 07] |
| Sector / Domain Overview | Sub-sector KPI ×7 | Top movers 表 | [04 / 07] |
| Sector Heatmap | Sector legend | 7×N heatmap | [05 / 07] |
| **Strategy Performance** | 策略 chip filter | **净值 Line (≤6) + Bullet vs benchmark 网格** | [06 / 07] |
| Valuation Scanner | 估值 slider | 结果表 + 散点 | [07 / 07] |

> Coverage 主表从「28 医药票」泛化为「任意传入 universe」—— 同一 HTML 表组件服务医药/AI/全市场。

---

## 4. Chart grammar (multi-domain · 来自 ui-ux-pro-max chart DB)

未来「很多策略 + 多行业」靠这套图表词汇，全部套 `theme.PLOTLY_LAYOUT`：

| 要展示 | 图表 | 约束 |
|--------|------|------|
| 策略累计收益 / 净值曲线 | **Line** | ≤6 series；多 series 靠**虚实线**区分不靠颜色；fill 20% opacity |
| 策略 vs 基准（多 KPI 并排） | **Bullet chart 网格** | 3-10 个；比 gauge 省空间；target 用黑色 3px marker；数值必显文字 |
| 单一指标 vs 目标 | Gauge / Bullet | 数值 + % of target 必须文字并显 |
| 板块 × 时间 强度 | **Heatmap** | divergent ±色阶（up-tint→down-tint）；>20 cell 才用；色阶必带 legend |
| 占比 / 构成 | 横向 stacked bar | 不用饼图（>5 类难读） |

- Trace line-width **1.5**（FT 标准，不用 2/3）。
- Volume bar width 0.7，半透明 CMSI red。
- 涨跌色用 `theme.UP`(teal) / `theme.DOWN`(red) —— **不采纳** ui-ux-pro-max 默认的 `#22C55E`/`#EF4444`（那是美式 vivid，我们走 FT 港美股 convention）。

---

## 5. Streamlit 技术决策 (v2.0 execution — 治本)

### 5.1 数据表：迁 `st.components.v1.html` iframe（**核心改动**）

`st.dataframe` 内是 glide-data-grid **canvas**，CSS 进不去 cell，OS dark-mode 穿透 → 表格黑底。这是 v1「不行」的头号根因。

**决策：Coverage 主表改用 `st.components.v1.html(html, height=…)` 渲染自包含 HTML 表。**

- ✅ 100% CSS 控制 · tabular-nums · sticky header/first-col · heatmap cell · FT 调性全可达。
- ✅ **vanilla JS click-sort 可用**（iframe 内 `<script>` 不被 Streamlit strip；`st.markdown` 会 strip script，故必须走 components.html）。sort/heatmap JS reference 见 `docs/design/mockup-v1.html`。
- ⚠️ 代价：iframe 隔离 → 必须把 `.cmsi-table` CSS **内联**进 html（不继承父页 theme）；高度需 Python 端按行数估算传入；失去 `st.column_config`（改 Python 端 format）。
- ⚠️ 失去的功能补法：`background_gradient` → Styler 仍可输出 inline style，或 Python 端算 cell bg；tooltip → `<th title="…">` 走 `ui.COLUMN_HELP`；sort → JS 三态；sticky → CSS `position: sticky`。

`render_styled_table` 重写为输出内联 HTML 表的函数（保持现有 `pct_cols / mult_cols / money_b_cols / column_help …` 签名向后兼容，7 个调用页不用改调用）。

### 5.2 CSS 注入

`theme.inject_css()` 在 `ui.sidebar_search()` 顶部每次 rerun 注入（**无 session_state guard** —— guard 会让第二次 rerun 跳过注入丢 CSS）。`config.toml` 设 JS 侧 palette 防 pre-CSS flash。

### 5.3 不可回退的坑（INVARIANT 级）

- ❌ 不要再加 `--gdg-*` glide-data-grid CSS vars —— 死代码，Streamlit `useCustomTheme.ts` 用 JS 覆盖。
- ❌ CSS inject 不加 session_state guard。
- ❌ 页面文件名含 emoji（`pages/1_💎_*.py`）**不改名**，`st.navigation` 用 `url_path` 锁 slug；只改文件**内容**里的 emoji。

---

## 6. Anti-slop pre-flight (来自 taste-skill，截取**纪律**部分)

> taste-skill 的*审美处方*（serif/留白/禁 Inter）与本 FT 密度方向冲突，**不采纳**；只取其可移植的一致性纪律。每次改完 UI、声明完成前过这张表：

- [ ] **One accent lock** —— 全站只有 CMSI red 一个品牌色，没有第 7 节突然冒蓝色 CTA。
- [ ] **Shape lock** —— 圆角统一（表/卡/表头 = 0；input/button ≤ 4px）。没有圆角混用。
- [ ] **Emoji = 0** —— code / markup / 标题 / page 文件内容 全删。
- [ ] **对比度** —— 文字 vs 背景 WCAG AA（正文 4.5:1）；placeholder / 跌幅红字在 cream 上可读。
- [ ] **Copy self-audit** —— 每个可见字符串读一遍：无语法破碎、无 AI 套话（"赋能/无缝/下一代"）、数字非编造（标 source 或 mock）。
- [ ] **数字右对齐 + tabular** —— 所有数字 cell 右对齐 + tabular-nums，无居中数字。
- [ ] **theme lock** —— 整页 light，不中途反色。

---

## 7. "金融专业感" 自评 (1-10) + 落地顺序

目标 8.5（FT.com tables = 9.0 天花板；Bloomberg 9.5 不追）。

### 7.1 分维度评分口径（v1.0 §7 并入，2026-08-30）

「当前」列是 **2026-05 v1.0 成文时的基线快照，非现状**——保留它是为了能量出进展，别当今天的读数用。「目标 / 关键动作」是仍然有效的设计指引。

| 维度 | 2026-05 基线 | 目标 | 关键动作 |
|------|--------------|------|----------|
| 字体执行 (tabular) | 5 | 9 | 全表 `font-variant-numeric: tabular-nums` |
| 颜色克制 | 7 | 9 | 删 emoji + cell 染字不染底 |
| 表格密度 | 4 | 8.5 | 行高 36px + padding-x 12px + 字 13px |
| 排版层级 (eyebrow) | 5 | 9 | UPPERCASE + tracking + `[NN / 07]` 序号 |
| 章节分隔 | 3 | 8 | 2px ink top rule + 4px 红条（替代 `st.divider`） |
| Plotly 调性 | 5 | 8.5 | 套 `theme.PLOTLY_LAYOUT` + line-width 1.5 |
| 整体 | 6 | 8.5 | —— |

外部对照阶梯（主观，用于校准"8.5 是什么水平"）：Bloomberg terminal 9.5（数字密度天花板，属 desk 不属早会，不追）· FT.com tables 9.0（本方案对标方向）· Stifel research PDF 8.5（黑红 + Times serif，不是我们的色）· 中信中金 PDF 8.0（传统但信息密度高）。

### 7.2 落地顺序

落地顺序（v2.0）：
1. **Stage 2** —— Coverage 主表迁 `components.html` HTML 表（治本 dark；本文件 §5.1）。
2. **Stage 3** —— 7 page 文件删 emoji + `theme.page_header("NN/07", …)` + `theme.kpi_strip()` + `theme.section_header()`。
3. **Stage 2.5** —— Plotly 全 sweep 套 `theme.PLOTLY_LAYOUT`；策略页加 line + bullet。
4. 每轮重启截图 → 用户对照 `docs/design/mockup-v1.html` 验收 → **验收后才 push**（cloud auto-redeploy）。

---

## 8. Don't do this (反向 checklist)

- ❌ box-shadow（除 sticky header 下沿 `0 1px 0 rgba(0,0,0,0.04)`）
- ❌ border-radius > 4px
- ❌ gradient 背景 / cell 整片染底（heatmap ≤12% 除外）
- ❌ 斑马纹表格行
- ❌ emoji（任何位置）
- ❌ 红色标题字（红只在 eyebrow / signal / active bar）
- ❌ 居中数字（永远右对齐）
- ❌ Plotly 默认 colorway / 默认 grid color
- ❌ font-size < 11px
- ❌ KPI 卡 sparkline / row action menu (⋮) on 表

— END v2.0 —
