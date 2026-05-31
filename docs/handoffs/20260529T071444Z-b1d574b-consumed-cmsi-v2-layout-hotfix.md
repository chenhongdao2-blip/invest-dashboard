---
status: CONSUMED
created_at: 2026-05-29T22:10:00+08:00
updated_at: 2026-05-29T22:10:00+08:00
consumed_at: 2026-05-29
consumed_by_commit: b1d574b
outcome: >
  全部修复并 ship 到 cloud (commit b1d574b, pushed to main 2026-05-29).
  根因经 Playwright live-DOM 实测确认（chrome-devtools MCP 本 session 未注册）：
  (1) sidebar 真 testid 是 stExpandSidebarButton 非交接里猜的 stSidebarCollapsedControl；
  chevron 被 Streamlit 涂成近白 fadedText60，在 cream 上隐形 → 强制 INK。
  (2) 标题 padding 1.5→4.5rem 清顶栏。
  此外修了用户上线后追加的多项：dark-mode bleed (stApp 根/popover 下拉/expander
  summary/st.table 全强制 cream)、::selection 高亮、alert 字体 INK、下拉框加公司名、
  去 [NN/07] 页码 + build/plan meta、正文 emoji、collapse reflow、coverage 表收紧；
  并回填 prices_daily 到 2025-09-22 让 6M 窗口能算。经 /cccg + 9-agent workflow 审计。
project_root: /Users/gcc/invest-dashboard
mission: invest-dashboard CMSI v2.0 视觉系统已上线 cloud (91349d8)，但线上有 2 个上线后才发现的布局 bug 未修复——(1) page_header 标题被 Streamlit 顶栏裁切 (2) sidebar 收起后无法重新打开 (Material 图标 ligature 渲染成文字 "keyboard_double_arrow_left"，控件失效)。本地 theme.py 修复尝试未 commit 且**没修好 sidebar**。
---
# HANDOFF — invest-dashboard CMSI v2.0 上线后布局 hotfix

> 自包含交接包。接棒人只读此文件即可动手，不需要对话历史。
> Live: https://agentmental-research.streamlit.app （已是 v2.0 但带 bug）
> Repo: https://github.com/chenhongdao2-blip/invest-dashboard

## 1. 任务 Mission

CMSI v2.0 视觉重做（Vercel 绿 → 招商红 #c8102e × cream #fff1e5 × FT 编辑密度风）**已全部完成并 push 上线**（commit `91349d8`，Streamlit Cloud 已 auto-redeploy）。但上线后用户在 cloud 上发现 **2 个布局 bug**，需要 hotfix：

1. **page_header 标题被裁切** —— 每页顶部 `[NN / 07] 标题` 被 Streamlit 固定顶栏（Share/Manage app 工具条）压住/裁掉上半截。
2. **sidebar 收起后打不开** —— 收起左侧 sidebar 后，重新展开的控件渲染成**文字** "keyboard_double_arrow_left"（Material 图标 ligature 没渲染成 `»` 字形），且点了也打不开。

**本地已尝试修复（仅改 `app/lib/theme.py`，未 commit），但用户实测「还不对」—— sidebar 仍打不开。** 标题裁切修没修好未确认。

## 2. 进度快照

**✅ 已完成并上线（commit 91349d8，已 push，local==origin 0/0）**：
- 8 张表全迁 `ui.render_html_table`（`st.iframe` HTML 表，治 `st.dataframe` canvas dark-mode 黑底）
- 2 个 Plotly 图走 `theme.style_plotly`（cream/FT teal）+ `st.plotly_chart(theme=None)`
- `page_header("NN / 07", …)` + `section_header()` 替换所有 st.title/st.subheader；正文 emoji 全删；cross-sector 文字码 BIO/PHAR/AI/…；多域措辞
- `requirements.txt` pin `streamlit==1.58.0`（cloud↔local parity）；5 处 `use_container_width`→`width="stretch"`
- 装了 4 个设计 skill（`taste-skill`/`taste-minimalist`/`taste-redesign`/`ui-ux-pro-max` 在 `~/.claude/skills/`）
- `docs/design/DESIGN.md` v2.0 + `docs/design/mockup-v1.html` 落 repo
- 经过 3 轮 /cccg 审计（Gemini lane 每轮 geo-block，实为 Claude+Codex+GLM 3-way）

**🟡 进行中 / 没修好（`app/lib/theme.py` 未 commit，diff = +32/-5）**：
- 标题裁切修复：`theme.py:231` `.block-container` padding-top `1.5rem`→`4rem`；`theme.py:176` 删掉了 stHeader 的 `height:1px`+`border-bottom`（改成只 `background:cream`）。**用户未确认标题是否修好。**
- sidebar 修复尝试：`theme.py:154-161` 加了 Material 图标保护规则（`[data-testid="stIconMaterial"]`/`.material-symbols-rounded`/`[class*="material-symbols"]` 强制 `font-family: 'Material Symbols Rounded'` + `font-feature-settings:'liga'`）；`theme.py:181-187` 加 `[data-testid="stSidebarCollapsedControl"]` z-index/color；`theme.py:200-204` 把原 `[data-testid="stSidebar"] *` 的 `font-family !important` 去掉、color 规则 `:not()` 排除图标。**用户实测 sidebar 仍打不开 → 这套 selector 大概率不匹配 Streamlit 1.58 真实 DOM，或问题根本不是字体而是 layout/点击。**

**⚪ 未开始**：
- sidebar 重开真正的修复（需 devtools 查真实 selector）
- self-host Inter（fast-follow，已写 project memory `selfhost-inter-fastfollow.md`；Google Fonts CDN 国内被墙）
- launchd wiki cron 安装（更早遗留：`bash scripts/install_launchd_wiki.sh`）

**环境状态**：
- branch `main`，**local == origin/main（0/0，91349d8 已 push）**
- 唯一未提交改动：`M app/lib/theme.py`（+32/-5，上述 2 个 bug 的修复尝试）
- build：`python3 -m py_compile app/lib/theme.py` 过；历史 `AppTest` 7/7 页零异常
- 本地 server 跑在 8503（可能还活着）。repro：
  `kill $(lsof -ti:8503) 2>/dev/null; HTTPS_PROXY=http://127.0.0.1:7897 HTTP_PROXY=http://127.0.0.1:7897 uv run --with-requirements requirements.txt --no-project streamlit run app/streamlit_app.py --server.port 8503 --server.headless true`
- **cloud 现状 = 91349d8 = v2.0 但带这 2 个 bug**（修复未 push）

**相关文件**：
- `app/lib/theme.py` — **唯一改动文件**；CSS 在 `_CSS` f-string（line ~144 起）。关键行：`stHeader`(176) / `stSidebarCollapsedControl`(181) / Material 图标保护(154) / sidebar(192,200,203) / `.block-container`(231)
- `app/streamlit_app.py` — `st.navigation` hub（sidebar nav 在此；已删 page icon）
- `app/lib/ui.py` — `render_html_table` + `inject_css` 调用点（`sidebar_search` 顶部）
- `docs/design/DESIGN.md` — v2.0 设计语言（§4.4 sidebar 规范）

## 3. 关键决策

- **已上线，graceful degradation 接受**：用户选「现在 ship + self-host Inter 作 fast-follow」，所以 Google Fonts 国内加载隐患是已知接受项，不是 blocker。
- **streamlit pin `==1.58.0`**：保证 cloud 渲染==本地实测版本（st.iframe/theme/use_container_width 都在 1.58.0 验过）。
- **HTML 表走 st.iframe 而非 st.dataframe**：治本 canvas dark-mode 黑底（Codex TOP PICK，4 advisor 收敛）。
- **stHeader 不能 crush 成 1px**（这次的教训）：原 Stage-1 写了 `[data-testid="stHeader"]{height:1px;border-bottom:2px}`，正是它同时造成「标题被压」+「sidebar 控件被藏」两个 bug。已在未提交 diff 里改掉。

## 4. 失败的尝试

- **stHeader `height:1px` + `border-bottom:2px`**（Stage-1 原写法）→ 同时引发标题裁切 + sidebar 重开控件消失。已改成 `background:cream` 自然高度。
- **Material 图标保护规则**（本次未提交尝试，selector = `[data-testid="stIconMaterial"]`/`.material-symbols-rounded`/`[class*="material-symbols"]`/`[data-testid="stSidebarCollapsedControl"]`）→ **用户实测 sidebar 仍打不开**。说明：(a) 这些 selector 可能不匹配 Streamlit 1.58 真实 DOM；或 (b) 问题不是字体 ligature 而是 layout（控件被遮挡/`pointer-events`/z-index/被裁出可视区）或 Streamlit 自身 collapse 状态。**别再盲猜 selector——必须用 devtools 查真实 DOM。**
- **Gemini advisor lane**：连续 3 轮 geo-block（"User location is not supported"，proxy 7897 出口非美区）→ /cccg 实为 3-way。想用 Gemini 得配美区出口代理。

## 5. 下一步

1. **用 chrome-devtools MCP 查真实 DOM**（已配置该 MCP）：开 localhost:8503（先按 §2 repro 重启），收起 sidebar，inspect 重开控件——拿到 **真实 `data-testid` / class**、图标元素的 computed `font-family` 和 `font-feature-settings`、以及它是否被 `pointer-events:none`/被遮挡/被裁。**先确诊「字体 ligature 坏」还是「layout/点击坏」，再写 CSS。** 别再盲改。
2. **标题裁切**：确认 `.block-container` padding-top `4rem` 是否真让 `[NN/07]` 标题完全避开顶栏（用户没确认）；不够就加到 4.5–5rem。
3. **两个 bug 都在 localhost 验过没问题后** → `git add app/lib/theme.py && git commit && git push origin main`（cloud 会 auto-redeploy 这个 hotfix；**push 是生产部署，需用户明确 go，且 auto-mode classifier 会拦 main push**）。注意 push 前先 `git fetch` —— GitHub Actions EOD 数据 cron 会往 main 推 `data/snapshots.db`，可能要先 `git rebase origin/main`（纯数据文件，不冲突）。

## 6. 陷阱与约束

- **cloud 现在带 bug 在线上**——这是生产 hotfix，用户要在 localhost 验对了再 push。
- **绝不再把 stHeader crush 成 height:1px**（就是它造成两个 bug）。
- **Material 图标靠 ligature + 'Material Symbols' 字体**：全局 `font-feature-settings:'tnum','ss01','cv11'`（theme.py:170）+ 任何 `font-family` override 都会 kill 图标 ligature 让它显示成文字。图标保护规则必须用**真实** selector（待 devtools 确认）。
- **push main = 生产 redeploy**：需用户明确「推/ship」指令；classifier 会拦。push 前 `git fetch` + 可能 `git rebase origin/main`（EOD 数据 cron）。
- **不要重命名 page 文件**（`pages/1_💎_*.py` 等，`st.navigation` 用 `url_path` 锁 slug）；`page_icon=` favicon 保留。
- macOS：`grep -E` 不用 `-P`；本地 yfinance 需 proxy `http://127.0.0.1:7897`；cloud 无需 proxy。
- `.omc/`、`.claude/` 在 .gitignore；`demos/`（含 orphan `cmsi_coverage_editorial_v1.html`）+ `docs/handoffs/*` 是 untracked，**别 commit 进 hotfix**（hotfix 只动 `app/lib/theme.py`）。

## 7. 打开的问题

- **sidebar 重开控件在 Streamlit 1.58 的真实 selector 是什么？**（crux，未知，需 devtools）
- **bug 本质是字体 ligature 还是 layout/点击？** 用户说「按到了一个按钮 不是文字，点完就打不开」——暗示控件可点但重开无效，或点击命中了错的元素 → 偏向 layout/click 问题，不只是字体。devtools 确认。
- **标题裁切 4rem 够不够？** 未经用户确认。

## ⚠️ 低置信度决策点（接棒人请核对）

1. **标题裁切是否已修好**——用户聚焦在 sidebar，没确认标题。可能还需调 padding。
2. **Material 图标 selector 是否匹配 1.58 真实 DOM**——大概率不匹配（所以 fix 失败）。`[data-testid="stIconMaterial"]` 和 `[data-testid="stSidebarCollapsedControl"]` 是我**猜的**，没用 devtools 验证过。
3. **sidebar 问题是字体还是 layout**——我先假设是字体 ligature（被全局 tnum/ss01 + font-family override 破坏），但 fix 没成功，所以很可能是 layout/click（控件被遮挡或裁出视区）。**接棒第一件事用 devtools 确诊，别继承我的字体假设。**
4. **是否该先 `git stash` 现有未提交 theme.py 改动重新来**——现有改动部分对（un-crush header 是对的方向），但 sidebar 那部分没用，接棒人可保留 header/padding 改动、重做 sidebar 部分。

<!-- HANDOFF-END -->
