---
status: CONSUMED
consumed_at: 2026-05-29
consumed_note: 完成态快照，与新任务(Strategy Picks 双语+双口径打磨)无依赖；新任务 plan 见 docs/plans/strategy-picks-bilingual-dualtrack.md
created_at: 2026-05-29T15:30:00+08:00
updated_at: 2026-05-29T15:30:00+08:00
project_root: /Users/gcc/invest-dashboard
mission: invest-dashboard CMSI v2.0 视觉系统 + 上线后多轮布局/可读性 hotfix 已全部 ship 到 cloud (commit b1d574b, live)。本交接是「完成态状态快照 + 待办 backlog + 关键教训」，供下一 session 起新任务时参考——非未完成工作的续接。
---
# HANDOFF — invest-dashboard CMSI v2.0 hotfix 收尾 + 状态快照

> 自包含交接包。接棒人只读此文件即可动手，不需要对话历史。
> Live: https://agentmental-research.streamlit.app
> Repo: https://github.com/chenhongdao2-blip/invest-dashboard

## 1. 任务 Mission
CMSI v2.0 视觉系统（招商红 #c8102e × cream #fff1e5 × FT 编辑密度风）+ 上线后用户分多轮提出的布局/可读性 hotfix，**已全部完成并 ship 到 cloud**（commit `b1d574b`，已 push origin/main，云端 Reboot 后 live 正常）。本 session 无遗留进行中工作。下一 session 预计起**新任务（TBD）**——与本 hotfix 无依赖。

## 2. 进度快照
全部 ✅（本 session 修的 12 项，均经 Playwright live-DOM 实测 + /cccg + 9-agent workflow 审计）：
- ✅ sidebar 收起→重开（真 testid `stExpandSidebarButton`；chevron 被涂近白 fadedText → 强制 INK）
- ✅ 标题被 Streamlit 顶栏裁切（`.block-container` padding-top → 4.5rem）
- ✅ st.table / inline code chip / `代码`徽章 dark-mode 黑底 → INK-on-cream
- ✅ 下拉(selectbox popover) / expander summary / stApp 根 的 OS 暗黑漏光 → 全强制 cream
- ✅ ::selection 选中高亮（默认深 slate 不可读 → 招商红 tint + INK）
- ✅ st.warning/alert 正文字体 → INK 黑（原 faint 不可读）
- ✅ 收起 sidebar 后内容 reflow 占满宽（collapsed 时 max-width 2200，open 仍 1440 编辑宽）
- ✅ 去掉所有页 `[NN / 07]` 页码 + home 的 build/plan meta caption
- ✅ 正文残留 emoji 清除（strategy tabs 🧬💰 / strategy+valuation 的 📖 expander / valuation ℹ️）
- ✅ coverage 17 列表收紧 padding 12→8（Reco 评级列现完整可见）
- ✅ ticker 下拉加公司名（`公司名 · BBG`，CN 优先 EN fallback；105/106 有名）
- ✅ 回填 prices_daily 到 2025-09-22（250d）→ 6M 收益窗口能算（原数据从 2025-12-01 起，差~4 交易日）

**环境状态**：branch `main` / 工作树干净（仅 untracked: `demos/`、`docs/handoffs/*` — 永不 commit）/ build：本地 7 页全渲染、全页 dark 扫描=0、py_compile 过 / local==origin/main (0/0) / HEAD=`b1d574b`。
repro 本地：`kill $(lsof -ti:8503) 2>/dev/null; HTTPS_PROXY=http://127.0.0.1:7897 HTTP_PROXY=http://127.0.0.1:7897 uv run --with-requirements requirements.txt --no-project streamlit run app/streamlit_app.py --server.port 8503 --server.headless true`
**相关文件**：`app/lib/theme.py`（CSS 主体，~700 行）、`app/lib/ui.py`（render_html_table + sidebar_search + iframe 表 CSS `_cmsi_table_css`）、`app/home.py`、`app/pages/*.py`（6 页）、`data/snapshots.db`（已回填）。

## 3. 关键决策 / 可复用技术（高价值，下次别重踩）
- **改函数签名后云端必 Reboot**：Streamlit Cloud 在 git pull 后只做热重载（hot-rerun），会用 `sys.modules` 里**缓存的旧**子模块（lib.theme/lib.ui）跑**新** page 脚本 → 报 `page_header() missing 'title'`、`render_styled_table() unexpected kwarg`、`cannot import name 'db'` 等**假错**。本地全新进程不受影响（所以本地一直正常）。**解法：Manage app（右下角）→ ⋮ → Reboot app**（清 sys.modules）。再 push 不解决，只有 reboot 解决。
- **chrome-devtools MCP 本 session 未注册** → 改用 **Playwright 驱动系统 Chrome**（`p.chromium.launch(channel="chrome", headless=True)`）读 live computed styles + 真实 DOM + 测点击。这是查 Streamlit 真实 testid / 暗黑漏光的金标准，别再盲猜 selector。
- **Streamlit 1.58 真实 testid 速查**：reopen 控件=`stExpandSidebarButton`（**非** `stSidebarCollapsedControl`，后者不存在）；折叠按钮=`stSidebarCollapseButton`；图标=`stIconMaterial`（font `Material Symbols Rounded`，靠 liga）；下拉列表是裸 `ul`/`div` 带 `st-*` emotion class（无 data-baseweb/role，所以旧 selector 没命中）。
- **OS 暗黑根因**：Mac 暗色模式下 Streamlit 即使 config `base="light"` 仍把 `stApp` 根 + portaled popover + expander summary + st.table 涂成 slate（#0f172a/#1e293b/rgb(22,32,51)）→ 必须逐个 `[data-testid] { background: cream !important }` 盖。
- push main = 生产 redeploy，auto-mode classifier 会拦，需用户**明确**「推/go/push」（"等 X 一起"不算明确放行——这次被 classifier 正确拦了一次）。

## 4. 失败的尝试
- 上一棒（已 archived）猜 `stSidebarCollapsedControl` 做 sidebar 修复 → 该 testid 在 1.58 不存在，死 CSS，从没生效。
- 旧 popover 规则只盖 `[data-baseweb="popover"]` 本身 → 内层 `ul`/`div`（带 st-* class）仍漏暗黑；必须 `[data-baseweb="popover"] div/ul/li` 全盖。
- /cccg 的 Gemini lane 持续 geo-block（"User location not supported"，proxy 7897 出口非美区）→ 实为 Claude+Codex+GLM 3-way。要 Gemini 得配美区出口。
- 试过 push 后等热重载自动生效 → 云端缓存旧模块，没用，必须 reboot（见 §3）。

## 5. 下一步
1. **起新任务**（用户本意）——本 hotfix 链路已闭环。
2. 若继续打磨 dashboard，待办 backlog（fast-follow，全非阻塞）：
   - `use_container_width` → `width="stretch"` 批量迁移（云端日志大量弃用 warning，非 error，但噪音大）
   - self-host Inter 字体（Google Fonts CDN 国内被墙；见 project memory `selfhost-inter-fastfollow.md`）
   - launchd wiki cron 安装（更早遗留：`bash scripts/install_launchd_wiki.sh`；见 archived `...launchd-wiki-still-pending.md`）
   - coverage 表 open-sidebar 1300px 下 N analysts/Cross 仍需横滚（已部分缓解，sidebar 收起态全显）

## 6. 陷阱与约束
- 改 page_header 等**签名后云端必 reboot**（见 §3，本 session 最大的坑）。
- 不要 commit `demos/`、`docs/handoffs/*`（untracked）、`.omc/`、`.claude/`（.gitignore）。hotfix 只动 app/ 下文件 + data。
- push main 前 `git fetch`——GitHub Actions EOD cron 会推 `data/snapshots.db`；二进制库 rebase 冲突时取**本地回填版超集**。
- 本地 yfinance 需 proxy `http://127.0.0.1:7897`；云端无需。
- macOS：`grep -E` 不用 `-P`。
- 破坏性/数据改写前先备份（本次回填 DB 前已备份 `/tmp/snapshots.db.bak.1780038399`，回填前库的拷贝）。

## 7. 打开的问题
- 无阻塞项。下一任务待用户定义。

## ⚠️ 低置信度决策点（接棒人请核对）
- **云端是否已 reboot 成功并 live 正常**：用户口头确认「都OK」，但我无 Streamlit Cloud 访问权、未亲眼复验。若接棒后发现 live 仍报 `page_header() missing 'title'` 同一行 → 就是 reboot 没生效，去 Manage app → Reboot app（代码本身已验证内部一致：fresh 进程导入全干净，page_header=[title,meta,subtitle]、render_styled_table 含 heatmap）。
- 本 session 临时 Playwright 脚本散在 `/tmp/*.py`（diag_*/verify_*/inspect_*/scan_*），非项目资产，可忽略。

<!-- HANDOFF-END -->
