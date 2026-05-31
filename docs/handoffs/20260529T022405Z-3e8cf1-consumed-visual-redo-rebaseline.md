---
status: CONSUMED
created_at: 2026-05-29T10:08:00+08:00
updated_at: 2026-05-29T11:00:00+08:00
project_root: /Users/gcc/invest-dashboard
mission: invest-dashboard 视觉风格重做 — 从 Vercel 绿 startup 风切到 CMSI 招商红 × cream FT 编辑风 × Inter+CN sell-side institutional 风。Stage 1 (token CSS 重写) 已 local，但用户判定"不行 重来"。下一棒：看 Claude Design 在 ~/Downloads/ 的 DESIGN.md + mockup.html 理解真实视觉目标，对照 local 8503 列差异，极可能直接做 Stage 2 (Coverage 主表迁 HTML 绕开 st.dataframe canvas dark-mode 穿透)。
---
# HANDOFF — invest-dashboard 视觉风格重做（FT × Inter × CMSI 红 cream）

> 自包含交接包。接棒人只读此文件即可动手，不需要对话历史。
> Live URL: https://agentmental-research.streamlit.app（本 session 未 push，cloud 仍是上一棒状态）
> Repo: https://github.com/chenhongdao2-blip/invest-dashboard

## 1. 任务 Mission

把已上线的 invest-dashboard 从原本的 Vercel 绿 #22c55e startup 风换成 **CMSI 招商红 #c8102e × cream #fff1e5 × Inter+CN fallback** 的 FT 编辑 / sell-side institutional 风，目标"金融专业感"，给到 CMSI 内部 PM/desk + 国内一线公募 (富国/中欧/易方达 医药组) 看上去像 sell-side research portal，不像散户/SaaS 工具。

本 session 走通了"问需求 → cccg 4 方 advisor → Claude Design 出 DESIGN.md → port 到 theme.py"链路；**Stage 1 落地 local 后用户判定不达预期** — 视觉差距仍大，需要重做。

## 2. 进度快照

**本 session 已 ship（全部未 commit，working tree 脏）**:

- ✅ /cccg quad-advisor review（Codex + Gemini + GLM）4 方收敛一致:
  - GLM **BLOCKER**: FT 红 `#990f3d` → CMSI 招商红 `#c8102e` (国内 client demo 不应"过度西化")
  - GLM **MAJOR**: Inter + CN fallback 必须显式 chain (PingFang SC / Noto / 雅黑) 避免中英 baseline 割裂
  - Codex **TOP PICK**: Coverage 主表迁 HTML (`--gdg-*` CSS vars 是死代码，Streamlit useCustomTheme.ts 用 JS 覆盖)
  - Gemini **MAJOR**: `:root { color-scheme: light !important }` 防 OS dark-mode 穿透 + UX 上 cream 适合 healthcare equity research
- ✅ Claude Design (claude.ai/design) 完整输出: `~/Downloads/DESIGN.md` (22KB · 10 节完整 design system) + `~/Downloads/CMSI Dashboard mockup.html` (28KB · standalone 可浏览器打开)
- ✅ `.streamlit/config.toml` 改 light base + CMSI 红 + 官方 `dataframeHeaderBackgroundColor` + `dataframeBorderColor` (Streamlit 1.36+ 支持)
- ✅ `app/lib/theme.py` 全量重写为 Claude Design v1.0: 22 color tokens (paper 5 阶 / ink 4 阶 / brand 4 阶 / up 3 阶 / down 3 阶 / sector 7 阶) + 12 type tokens + 3 helper 函数 (`kpi_metric()` / `section_header()` / `page_header()`) + 完整 `PLOTLY_LAYOUT`
- ✅ `app/lib/ui.py` 在 `sidebar_search()` 顶部调 `theme.inject_css()` (每页自动注入)
- ✅ Streamlit 1.57 实测安装可用，跑在 local 8503

**🟡 进行中 / 用户判定不达预期**:

- 🟡 **Stage 1 token CSS** local 跑通但用户说"不行 重来"。具体不行在哪 **未追问**，可能（按概率）:
  1. `st.dataframe` canvas cells 仍黑（Stage 1 没改 render_styled_table，dataframe 内部仍是 Streamlit JS-rendered canvas → 表格仍可能是黑底）
  2. emoji 还在 (`📊🏥🔥🧬💎💰🔍` 在 home.py + 6 个 page 文件标题里，Stage 1 没动 per-page 文件)
  3. KPI 卡未启用新 helper (st.metric 仍是 native，没换 `kpi_strip([kpi_metric(...)])`)
  4. sidebar 仅 CSS 染色，没换成 Claude Design §4.4 的 240px brand bar + 4px 红条 active nav
  5. 整体观感跟 Claude Design mockup 仍有距离 (mockup 是纯 HTML，Streamlit DOM 复杂得多)
- 🟡 上述 5 项 **没** 在 Stage 1 里做，是 Stage 2/3 内容

**⚪ 未开始**:

- ⚪ **Stage 2**: Coverage 主表迁 HTML —— 重写 `app/lib/ui.py:render_styled_table` 用 `df.style.to_html()` 输出 + `<th title="">` 走 `ui.COLUMN_HELP` tooltips + ~35 行 vanilla JS sort handler。**这才是真正治本 dataframe canvas dark**，是 Codex TOP PICK + Claude Design 单点建议
- ⚪ **Stage 3**: per-page polish — 7 个 page 文件 (home.py + pages/{1-6}_*.py) 改用 `theme.page_header("01/07", "...")` 替代 `st.title("📊 ...")`，删 emoji，KPI 用 `theme.kpi_strip()`
- ⚪ Plotly 全 codebase sweep apply `theme.PLOTLY_LAYOUT` (Stage 2.5)
- ⚪ commit + push cloud（**严禁** 在 Stage 2/3 落地 + 用户确认前 push，cloud auto-redeploy）

**环境状态**:
- branch `main`, **working tree dirty**: `M .streamlit/config.toml` / `M app/lib/ui.py` / `?? app/lib/theme.py` / `?? demos/` / `?? docs/HANDOFF.md`
- 最新 commit: `08b2e35 feat(wiki-public): weekly launchd auto-sync (Phase 2)` (上一棒，本 session 未新 commit)
- Streamlit 本地: port 8503 跑着 Stage 1 版本（PID 不确定，需 `lsof -ti:8503` 重检）
- Demo 备份: port 8502 是 demos/theme_preview/app.py (3 theme 切换 demo, 已选定 B × Inter)
- repro: `uv run --with-requirements requirements.txt --no-project streamlit run app/streamlit_app.py --server.port 8503 --server.headless true`

**相关文件（按优先级）**:
- `~/Downloads/DESIGN.md` — **必读** Claude Design 完整 spec (token + 组件 + Streamlit 兼容性 + 反向 checklist + roadmap)
- `~/Downloads/CMSI Dashboard mockup.html` — **必看** standalone HTML，浏览器打开直接对比 local 8503
- `app/lib/theme.py` — Stage 1 已重写，含全套 tokens + 3 helpers (kpi_metric / section_header / page_header) + 完整 PLOTLY_LAYOUT
- `app/lib/ui.py` — `sidebar_search()` 顶部调 `theme.inject_css()`; `render_styled_table()` **未动**（Stage 2 重写目标）
- `.streamlit/config.toml` — light base + CMSI 红 + 官方 dataframe key
- `app/streamlit_app.py` + `app/home.py` + `app/pages/{1-6}_*.py` — **未动**（Stage 3 重做目标）
- `.omc/artifacts/ask/cccg-{codex,gemini,glm}-out.txt` — cccg review 输出。codex/gemini 是 pointer 到 `.omc/artifacts/ask/{codex,gemini}-*.md` 真文件；glm 直接是 content
- `.omc/artifacts/ask/glm-review-20260528-190228.md` — GLM BLOCKER 原文
- `.omc/artifacts/ask/codex-you-are-auditing-*-2026-05-28T11-05-37-397Z.md` — Codex 完整原文（1.9MB，要用 tail 读）
- `.omc/artifacts/ask/gemini-you-are-an-independent-reviewer-*-2026-05-28T11-09-48-535Z.md` — Gemini 完整原文
- `demos/theme_preview/app.py` — 三 theme (A Bloomberg / B FT / C Stripe) 切换 demo, port 8502; 用户已选 B × Inter 路径
- `demos/cmsi_coverage_editorial_v1.html` — **orphan**, 我做了一个 v64 IPO 编辑风的 Coverage mockup，**用户明确说"忽略 我复制多了"**，可删
- `docs/handoffs/20260529T0207123NZ-641bc9-launchd-wiki-still-pending.md` — 上一棒（Phase 2 launchd wiki cron）未消费状态归档，**关键 task 仍未执行**：`bash scripts/install_launchd_wiki.sh`

## 3. 关键决策

- **CMSI 红 `#c8102e` 而非 FT 红 `#990f3d`** — GLM BLOCKER。理由：用户是 CMSI 分析师，dashboard 给国内/CMSI 客户 demo；FT 暗酒红会引发"洋"/合规错觉
- **cream `#fff1e5` 保留** — Gemini PASS。FT 米黄适合 healthcare equity research，不要走 Bloomberg 终端黑或中信中金深表头白底（GLM 建议过深表头，但用户 Phase 2 选 A = 全 cream）
- **港美股 convention 涨绿 `#0d7680` (FT teal) / 跌红 `#cc0000`** — 不 flip 成 A 股范式（28 标的里 HK 15 + US 10 占 25/28）
- **brand-red `#c8102e` 与 signal-red `#cc0000` 分离** — Claude Design 设计：brand 出现在表头/标题/导航/active，signal 出现在跌幅数据。视觉几乎相同但语义不串
- **Inter + CN fallback 显式 chain** — `'Inter', 'PingFang SC', 'Hiragino Sans GB', 'Noto Sans SC', 'Microsoft YaHei', sans-serif`
- **emoji 全删** — 用 `[01/07]` mono 序号 + 4px ▎红竖条替代 (Claude Design §6 明确决策；GLM MINOR 同意)
- **HTML 表替代 st.dataframe** — Codex TOP PICK + Claude Design 单点建议。理由：(a) `--gdg-*` CSS vars 是死代码 (Streamlit useCustomTheme.ts 用 JS 覆盖) (b) body cell bg 即便配 config.toml `backgroundColor` 也受 OS dark-mode 穿透 (c) 28×14 = 392 cell, vanilla JS sort 毫无压力 (d) 失去 column_config 但得 100% CSS 控制 + tabular-nums + heatmap cell + sticky header
- **不动 Streamlit 主框架** — 不切 Next.js / Flask（user 7 constraint）

## 4. 失败的尝试

- **`--gdg-bg-cell` / `--gdg-bg-header` / `--gdg-text-dark` 等 glide-data-grid CSS custom properties** — Codex 证据明示是死代码: Streamlit `frontend/lib/src/components/widgets/DataFrame/hooks/useCustomTheme.ts` 用 JS 重建 glideTheme，从 `theme.colors.bgColor` / `theme.colors.dataframeHeaderBackgroundColor` 覆盖。已从 theme.py 删除
- **仅靠 .streamlit/config.toml `base="light"` + `backgroundColor="#fff1e5"`** — 改不动 dataframe canvas cell。Streamlit 1.57 即便支持官方 `dataframeHeaderBackgroundColor`/`dataframeBorderColor` 也只改外框 + header band，body cells 仍可能受 OS dark-mode 穿透（实测：用户 hard-refresh 后 cells 仍黑）
- **CSS `:root { color-scheme: light !important }` + `[data-baseweb=select]` + 多层 `[data-testid="stDataFrame"] *` aggressive selector** — page chrome / sidebar / selectbox 修了，dataframe 内部 canvas 改不动
- **`session_state` guard `_theme_injected_this_run`** — 错误设计：Streamlit 每次 rerun 重建 DOM 但 session_state 持久，第二次 rerun 会跳过 inject_css() → 第二次起 CSS 全丢。已删 guard，每次 rerun 都 inject

## 5. 下一步

**接棒立即执行**（按 ROI 排序）:

1. **看 ~/Downloads/DESIGN.md + 浏览器开 ~/Downloads/CMSI Dashboard mockup.html** —— 必读必看。这是真实视觉目标。同时 hard-refresh local http://localhost:8503，**列 5-10 条具体差异**（gap 矩阵）：
   - mockup 是什么样 vs 8503 是什么样
   - 差距来自 (a) Stage 1 token 没生效 (b) Stage 2 dataframe 还是 canvas (c) Stage 3 page 文件未改 (d) Streamlit DOM 复杂度 fight Claude Design 纯 HTML

2. **不要再 token-level 改 theme.py** — 用户已判定 Stage 1 token 不够。**直接做 Stage 2** —— 重写 `app/lib/ui.py:render_styled_table`：
   ```python
   def render_styled_table(df, *, pct_cols=None, pct_decimal_cols=None, mult_cols=None,
                            money_b_cols=None, int_cols=None, text_cols=None,
                            column_widths=None, extra_formats=None, column_help=None,
                            height=500, hide_index=False):
       # 用 df.style.format(...).background_gradient(...) 配 inline style
       # 用 _to_html_with_class() 输出，套 .cmsi-table CSS class
       # th 加 title="..." 走 COLUMN_HELP
       # 末尾注入 35 行 vanilla JS sort handler (click <th> 切 asc/desc/none 三态)
   ```
   验证：CMSI Coverage 页 cells 应该完全 cream 米黄，无 dark 穿透；click 表头 sort 正常；hover 表头看到 tooltip

3. **Stage 3 per-page polish**（7 文件，可批量 sed-like）:
   - `app/home.py`: `st.title("📊 Multi-Domain...")` → `theme.page_header("01/07", "Multi-Domain Investment Dashboard", meta="As of 2026-05-29 ...")`
   - 6 个 `app/pages/*.py`: 同样替换。删所有 `📊🏥🔥🧬💎💰🔍` emoji
   - st.metric 调用 → `theme.kpi_strip([theme.kpi_metric(...)])`
   - st.subheader → `theme.section_header()`
   - 注意：page 文件名含 emoji（`pages/1_💎_CMSI_Coverage.py`）**不要改名**，只改文件内容（streamlit_app.py 用 `url_path` 锁定 slug）

4. **重启 + 截图给用户**: `kill $(lsof -ti:8503) ; uv run --with-requirements requirements.txt --no-project streamlit run app/streamlit_app.py --server.port 8503 --server.headless true`，然后用户对照 Claude Design mockup 验收

5. **commit + push cloud**（仅在用户明确 OK 后）:
   ```
   git add -A && git commit -m "feat(theme): port Claude Design v1.0 — CMSI red cream FT editorial"
   git push origin main  # Streamlit Cloud auto-redeploy ~1min
   ```

## 6. 陷阱与约束

- **launchd wiki cron 仍未安装** — 上一棒（Phase 2）已归档到 `docs/handoffs/20260529T0207123NZ-641bc9-launchd-wiki-still-pending.md`，**关键动作**：用户执行 `bash scripts/install_launchd_wiki.sh` 安装 launchd job (5 秒)。本 session 不动它，但接棒人若有时间可帮用户跑一下
- **macOS shell**: `grep -E`，不用 `grep -P`（用户 CLAUDE.md hard rule）
- **HK proxy**: 用户中国本地跑 yfinance 需 `HTTP_PROXY=http://127.0.0.1:7897`；GitHub Actions / Streamlit Cloud 在 Microsoft cloud 跑，无需 proxy
- **页面文件名含 emoji** — `app/pages/1_💎_CMSI_Coverage.py` 等，`st.navigation` 用 `url_path` 锁 slug 成 ASCII，**不要**改文件名
- **`--gdg-*` CSS dead** — 不要再加这些。Streamlit JS 在 useCustomTheme.ts 用 `theme.colors.*` 覆盖
- **session_state guard for CSS inject 反 pattern** — Streamlit rerun 重建 DOM 但 session_state 持久，guard 会让第二次起跳过注入。每次 rerun 都 inject 是正确做法
- **Cloud auto-redeploy** — `git push origin main` 会立刻触发 Streamlit Cloud 重 build。**严禁** 在用户验证前 push
- **app slug `agentmental-research` 已锁** — URL 改名破坏 deep link
- **`.omc/` 和 `.claude/`** 在 `.gitignore`，不能 commit
- **demos/cmsi_coverage_editorial_v1.html 是 orphan** — 用户说"一页纸的请忽略 我复制多了"，可 `rm demos/cmsi_coverage_editorial_v1.html`
- **demos/theme_preview/** 是已选定后的产物（B × Inter），可保留作为 reference 或归档

## 7. 打开的问题

- **Stage 2 重写丢失的功能怎么补**:
  - click-to-sort: vanilla JS 35 行重做（mockup.html 里有 reference 实现）
  - column_config NumberColumn format: Python 端手 format（pct_cols 加 `%`+.1f`%%` 等）
  - column tooltips via `column_config(help=...)`: 改用 `<th title="...">` HTML attr
  - background_gradient: **preserved** —— `Styler.to_html()` 输出 inline style 保留 gradient color
  - sticky header / sticky first col: CSS `position: sticky; top: 0;` 实现
- **Streamlit 1.57 官方 dataframe key 是否真生效** — 加了 `dataframeHeaderBackgroundColor` / `dataframeBorderColor` 但实测表格仍黑；可能 (a) Streamlit 1.57 没完全支持 (b) OS dark-mode 穿透 (c) 用户没 hard-refresh 拿到新 config。Stage 2 走 HTML 表后此问题自动消失
- **Sidebar 进一步 polish (Claude Design §4.4 完整版)** — 240px 固定 + brand bar + 4px 红条 active nav + footer "AS OF ... · DATA · FACTSET/WIND"。Streamlit 原生 sidebar 通过 CSS-override 部分可达，完整版需要 wrap navigation
- **Plotly chart sweep** — `st.plotly_chart` 调用散在多个 page，Stage 2.5 要扫所有调用 apply `theme.PLOTLY_LAYOUT`
- **A/B test cream-full-bg (Phase 2 A) vs 中信深表头白底 (B)** — 用户已选 A，但若 Stage 2 落地后还不达预期，B 是 fallback

## ⚠️ 低置信度决策点（接棒人请核对）

> 以下几点我注意力可能记偏，磁盘真值优先。请核对：

1. **Streamlit 1.57 是否真支持官方 `dataframeHeaderBackgroundColor` / `dataframeBorderColor`** — Codex 引的源码是 develop 分支，未独立 verify 1.57.0 release 已合入。如果配 config.toml 后表头颜色没变，说明 1.57 还没支持，要么升 Streamlit 要么走 HTML 表（Stage 2）。Verify: 启动后看 dataframe header 是否真 `#f2dfce` 米黄
2. **body cell bg 来源** — Codex 说是 `theme.backgroundColor` (config.toml `backgroundColor`)，但实测 cream config 下 cells 仍黑。可能的真实原因 (a) Streamlit 1.57 行为不一致 (b) OS dark-mode 穿透 canvas (c) Styler 没颜色的 cell 走 `secondaryBackgroundColor` 而非 `backgroundColor` (d) 浏览器缓存。要重 verify
3. **Claude Design mockup.html 是 standalone HTML，不是 Streamlit 兼容代码** — 直接复制 CSS 到 theme.py 不一定 work，因为 Streamlit 的 DOM selector (`[data-testid="..."]`) 跟普通 HTML class 不一样。Stage 1 已经做了一遍映射但用户判定不达预期。要核对 mockup 里的 CSS 哪些 selector 在 Streamlit DOM 里实际匹配，哪些只匹配纯 HTML
4. **demos/cmsi_coverage_editorial_v1.html 该不该删** — 用户明确说"一页纸的请忽略 我复制多了"，可 rm。但它是 v64 IPO 风格的 Coverage 改写，未来可能想看 — 折中：移到 `docs/design-experiments/`
5. **Stage 1 用户说"不行 重来"具体不行在哪** — 我**没追问**，可能是 (a)/(b)/(c)/(d)/(e) 5 项任一。接棒人开局应**主动**问用户："你说不行，具体指：① dataframe 还黑 ② emoji 还在 ③ KPI 卡未启用 helper ④ sidebar 没改成 mockup 样 ⑤ 整体观感对不上 — 哪一项最重？"
6. **launchd wiki cron 老 handoff 处理** — 已移至 `docs/handoffs/20260529T0207123NZ-641bc9-launchd-wiki-still-pending.md`，session-start hook 不会再提醒，需用户主动记得执行 `bash scripts/install_launchd_wiki.sh`
7. **cccg artifact 文件位置** — `.omc/artifacts/ask/cccg-codex-out.txt` 和 `cccg-gemini-out.txt` 只是 pointer (140 字节)，真内容在 `.omc/artifacts/ask/{codex,gemini}-you-are-...-2026-05-28T11-XX-XX-XXX.md` 大文件里（Codex 1.9MB 用 tail 读，Gemini 较小）。GLM 直接是 `.omc/artifacts/ask/cccg-glm-out.txt` 内容
8. **working tree 脏** — 3 个 M + 2 个 ??。接棒人决定 Stage 2/3 完整 ship 后是否一次性 commit，或分阶段 commit（Stage 1 token 单独 commit / Stage 2 HTML 单独 commit / Stage 3 per-page 单独 commit）

<!-- HANDOFF-END -->
