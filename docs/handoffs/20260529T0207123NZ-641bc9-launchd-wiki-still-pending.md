---
status: ACTIVE
created_at: 2026-05-28T16:50:00+08:00
updated_at: 2026-05-28T16:50:00+08:00
project_root: /Users/gcc/invest-dashboard
mission: invest-dashboard 已上线 Streamlit Cloud（agentmental-research.streamlit.app），Phase 1 sanitized wiki 已 ship，Phase 2 weekly launchd cron 已写但**尚未安装**。下一棒：用户执行 `bash scripts/install_launchd_wiki.sh` 激活周日 20:00 自动同步，验证 launchctl list 看到 job，端到端测一次推送链路。
---
# HANDOFF — invest-dashboard 上线后 polish 第三段

> 自包含交接包。接棒人只读此文件即可动手，不需要对话历史。
> Live URL: https://agentmental-research.streamlit.app
> Repo: https://github.com/chenhongdao2-blip/invest-dashboard

## 1. 任务 Mission

D1-D7 + Streamlit Cloud 全部上线，进入 polish 阶段。本 session 已 ship 10 个 commit（包括 sanitized wiki 公开镜像 + weekly cron 脚手架）。**真正未完成的只有一件事**：用户在本地执行 `bash scripts/install_launchd_wiki.sh` 把 launchd job 加载进系统。其余都是 nice-to-have backlog。

## 2. 进度快照

**本 session 已 ship（10 commits, 全部 pushed origin/main）**:
- ✅ `b4bbde4` 92 个 ticker 加 name_cn/name_en（jobs/migrate_yaml_names.py 一次性迁移 + load_universe.py reload），CMSI Coverage / Sector Heatmap 删 BBG 列
- ✅ `dc75b98` Sector Heatmap 删 Tier 列
- ✅ `686e144` FCF Yld 显示修正（pre-multiply ×100 + `%+.2f%%`；Streamlit NumberColumn 不支持 `%%` percent multiplier shorthand）
- ✅ `4c2c787` ui.COLUMN_HELP 共享 tooltip dict（Fwd P/E 注 NTM vs Yahoo webpage 口径差异 + 10 个其他字段）
- ✅ `fe8b3ac` st.navigation 分组：Home + Ticker Drill 顶层，Healthcare 折叠组下放 CMSI Coverage / Overview / Sector Heatmap / Strategy Picks / Valuation Scanner
- ✅ `4e803f4` Phase 1: jobs/export_wiki_public.py + data/wiki/companies/*.md (32 files, 192KB) + app/lib/wiki.py 双 root fallback + Ticker Drill 区分 sanitized vs internal banner
- ✅ `08b2e35` Phase 2: scripts/wiki_weekly_sync.sh + com.gcc.invest-dashboard.wiki-sync.plist + install_launchd_wiki.sh

**未开始 / 用户待动作**:
- ⚪ **关键**: 用户执行 `bash scripts/install_launchd_wiki.sh` 安装 launchd job（5 秒）
- ⚪ 用户验证 `launchctl list | grep com.gcc.invest-dashboard.wiki-sync` 看到一行
- ⚪ 用户手动跑一次 `bash scripts/wiki_weekly_sync.sh` 验证 git push 链路（手动 run 时若 wiki source 没变会 no-op exit；要真测 push 需先编辑一个 wiki 源 file）
- ⚪ 用户在 https://agentmental-research.streamlit.app/Ticker_Drill?ticker=1530.HK 验证 sanitized memo 真的渲染（应看到 📋 公开版 banner + Summary + Thesis + 财务快照 + 核心投资逻辑 + 催化剂 + 风险点）

**进行中**:
- 🟡 无 — working tree clean，无 in-flight 文件编辑

**环境状态**:
- branch `main`, working tree **clean**, all 10 commits pushed
- 最新 commit: `08b2e35 feat(wiki-public): weekly launchd auto-sync (Phase 2)`
- launchd job: **未加载**（`launchctl list | grep wiki` → NOT LOADED）
- Streamlit Cloud: 已自动 redeploy（08b2e35 push 完约 1 分钟内）
- repro 本地: `cd ~/invest-dashboard && uv run --with streamlit --with yfinance --with pandas --with plotly --with pyyaml --with numpy streamlit run app/streamlit_app.py --server.port 8517`

**相关文件**:
- `scripts/wiki_weekly_sync.sh` — 周日 cron 主脚本（git pull rebase → export → diff check → commit + push 或 no-op exit），所有 stdout/stderr → `.omc/logs/wiki_weekly.log`
- `scripts/com.gcc.invest-dashboard.wiki-sync.plist` — launchd Weekday=0 Hour=20 Minute=0，需 cp 到 `~/Library/LaunchAgents/`
- `scripts/install_launchd_wiki.sh` — 安装器（idempotent，支持 `--uninstall`），用 `launchctl bootstrap gui/$(id -u)` 现代 API，fallback `launchctl load`
- `jobs/export_wiki_public.py` — sanitization 引擎，strip Rating/TP/Sources/分析师姓名/dated report 引用/3 个内部 section（管理层动态/矛盾与待验证/自我进化追踪）
- `app/lib/wiki.py` — `_wiki_roots()` 返回 `[(internal, False), (public, True)]` 顺序，`find_wiki()` 设 `is_sanitized` 字段
- `app/pages/6_🔍_Ticker_Drill.py` — 根据 `is_sanitized` 切换 `st.warning` (full) vs `st.info` (📋 公开版) banner
- `app/lib/ui.py` — `COLUMN_HELP` dict + `render_styled_table` 接 `column_help` kwarg
- `app/streamlit_app.py` — `st.navigation({"": [home, drill], "🏥 Healthcare": [...]})` hub
- `app/home.py` — 原 Home 内容剥出来（因为 navigation hub 需要每个 page 是独立 script）
- `data/wiki/companies/*.md` — 32 sanitized public memos
- `.streamlit/config.toml` — 注意 `enableCORS=false` + `enableXsrfProtection=true` 互不兼容，Streamlit auto-override CORS=true，有警告 log 但功能正常

## 3. 关键决策

- **不把 raw wiki 上 Cloud**（GLM compliance BLOCKER）— CMSI 内部 Rating/TP/研报 PDF 引用 disseminate 到 public dashboard 违反卖方分发权限。改写 sanitization layer，data/wiki/ 只含公开-domain 内容（Summary/Thesis/财务快照/核心投资逻辑/催化剂/风险点）。
- **双 root resolver**（local internal > Cloud public）— 本地 dev 仍看完整 Rating/TP；Cloud 只看公开版。同一份 codebase，不同 path 自动 fallback。
- **launchd weekly Sunday 20:00**（非每日）— wiki 源在 Mac，源 update 频率本来就 weekly-ish，cron 每日跑大概率 no-op。Sunday 20:00 是 Mac 通常开机时段。launchd misfire 行为：Mac 睡眠错过 fire 时间，醒来后会补跑（最多延迟几小时）。
- **launchd 不 auto-install** — user opt-in 行为。`install_launchd_wiki.sh` 留给用户手动执行，不在 commit hook 里自动加载（用户对 Mac 上后台 job 有 sovereignty）。
- **sanitization 用 regex blacklist，不用 whitelist** — 初始考虑 whitelist sections 但保留过严会丢公开 thesis；改用黑名单 strip strategy + section-level drop（管理层动态/矛盾与待验证/自我进化追踪 整段 drop）。
- **table 来源列 cell 留空 `| |`** — 不重写表格结构，让 dated report ref strip 后 cell 空着，acceptable visual fallback。
- **app slug "agentmental-research"** — agent + fundamental portmanteau 模仿 quantmental，加 `-research` 后缀避开 short slug collision。Live: https://agentmental-research.streamlit.app

## 4. 失败的尝试

- **format `"%+.2%"`** 让 Streamlit NumberColumn 显示 percent — 不工作，printf `%` 不是 valid conversion specifier。Streamlit fallback 显示 raw decimal（0.023907）。修复：pre-multiply df[col] × 100 + format `"%+.2f%%"`。
- **`re.compile(r"\s*\|\s*$", re.MULTILINE)`** 想清理 Sources strip 后的 trailing `|` — 太贪，连 table row 尾的 `|` 也删了，破坏 markdown 表格。修复：让 Sources strip pattern 自己 include leading `\s*\|\s*`，不要单独的 trailing strip。
- **`_CN_PREFIX_RE` 没 strip 句末 paren meta** — 初版 hc_managed_care.yml 出现 `name_en: HCA Healthcare (cross: hospital_care)` 这种污染。补 `_META_PAREN_RE` 剥 `(cross: ...|ADR|formerly ...|primary ...|Nasdaq ...)`。但 `(US ADR; primary listing ROG.SW)` 这种带分号的没 cover，RHHBY 手 patch 一次。
- **GLM "复利 wiki" hallucination** — Codex/Gemini/GLM 三 advisor /cccg audit 中 GLM 凭空 critique 了一个 repo 里不存在的字符串"复利 wiki"。grep 验证为零匹配，discount 掉。

## 5. 下一步

**用户立即执行**（5 分钟内验证完）:

1. **安装 launchd job**:
   ```bash
   bash /Users/gcc/invest-dashboard/scripts/install_launchd_wiki.sh
   ```
   预期输出末尾："Loaded via launchctl bootstrap." 或 "Loaded via launchctl load (legacy API)."

2. **验证已加载**:
   ```bash
   launchctl list | grep com.gcc.invest-dashboard.wiki-sync
   ```
   应看到 PID 列为 `-`（未运行）、exit code `0`、label 字段对得上。

3. **（可选）测一次手动 run**:
   ```bash
   bash /Users/gcc/invest-dashboard/scripts/wiki_weekly_sync.sh
   tail -30 /Users/gcc/invest-dashboard/.omc/logs/wiki_weekly.log
   ```
   现在 wiki source 跟 public mirror 一致 → no-op exit。要真测 push：先编辑一个 `~/Documents/LLM Wiki/Wiki/companies/*.md` 加一个无害字符再 run。

4. **Cloud 验证 sanitized memo 渲染**:
   打开 https://agentmental-research.streamlit.app/Ticker_Drill?ticker=1530.HK，预期看到：
   - 📋 公开版 banner（蓝色 info 而非 ⚠️ warning）
   - 三生制药 3SBio 标题
   - Summary + Thesis + Sectors + Last updated（**无** Rating / TP / Sources / 分析师姓名）
   - 财务快照 + 核心投资逻辑 + 催化剂 + 风险点 sections

## 6. 陷阱与约束

- **`.omc/` 和 `.claude/`** 在 `.gitignore`，不能 commit
- **`data/external/*.db`** 也 ignored — 不要回提 ic-foundry ledger 副本（IP）
- **macOS shell**：`grep -E`，不用 `grep -P`（用户 CLAUDE.md hard rule）
- **HK proxy**：用户在 China 本地跑 yfinance 需 `HTTP_PROXY=http://127.0.0.1:7897`；GitHub Actions / Streamlit Cloud 在 Microsoft cloud 跑，无需 proxy
- **App slug 已锁** — `agentmental-research`，URL 改名会破现有 deep link
- **wiki sanitization 不可逆** — `data/wiki/` 是 generated artifact，不要手编辑；改源在 `~/Documents/LLM Wiki/Wiki/companies/`，下次 cron 自动 propagate
- **page 文件名含 emoji** — `app/pages/1_💎_CMSI_Coverage.py` 等，st.navigation 用 explicit `url_path` 把 slug 锁成 `/CMSI_Coverage` 等 ASCII，**不要**改文件名
- **Streamlit 1.50+ deprecation 警告** — `use_container_width=True` 应该改 `width="stretch"`（2025-12-31 之后强制），P2 backlog
- **`.streamlit/config.toml` CORS/XSRF 冲突警告** — `enableCORS=false` + `enableXsrfProtection=true` 互不兼容，Streamlit auto-override CORS=true。无 functional 影响，但每次 boot log 有 warning。修：删掉 `enableCORS=false` 行即可

## 7. 打开的问题

- **P1 deferred**（multiple commits 累积）:
  - 港股通 / 北向资金（AKShare/Tushare 集成）
  - Time-series 5Y P/E band（需 90 天+ 数据沉淀，已开始累积）
  - 集采/医保谈判 policy calendar overlay
  - 多年 forward consensus（Gangtise sell-side broker mean 接进来）
  - Mobile responsive
  - 28-ticker CMSI Coverage 名单缺 18A 核心（康方 9926 / 再鼎 9688 / 和铂 6994 / 恒瑞 600276）— user defer
- **Wiki sanitization 边缘 case**: `(US ADR; primary listing ROG.SW)` 这种带分号的 meta paren 没自动剥（RHHBY 手 patch）。未来要么改 regex 接分号 meta，要么开发 LLM-driven sanitization pass。
- **CMSI Coverage 没接 `render_styled_table`** — 手写 column_config（Gemini /cccg audit 标 [MINOR]）。重构能 dedupe 一些代码但风险不高，defer。
- **Streamlit 1.50+ deprecation**: `use_container_width=True` → `width="stretch"`。批量 sed 替换 5 个 page + lib/ui.py 可以一次性解决。

## ⚠️ 低置信度决策点（接棒人请核对）

> 以下几点我注意力可能记偏，磁盘真值优先。请核对：

1. **launchd Sunday 20:00 fire 行为** — 我没等到周日测过，只跑了 manual。launchd `StartCalendarInterval Weekday=0 Hour=20` 在 Mac 那时睡眠是否真的补跑，依赖 Apple 文档表述。万一不补跑，user 下次开机时不会自动 sync。补救：改 `RunAtLoad=true` + 加 `ThrottleInterval` 60s 防爆，或者改用 `StartInterval`（每 N 秒）但更费电。
2. **Streamlit Cloud 是否真重读 `data/wiki/`** — 我没在 Cloud 上 verify sanitized memo 实际渲染。理论上 Cloud git pull → 包含新 data/wiki/，wiki.py fallback chain 找到，render。但 Cloud 容器文件系统可能 caching，cold boot 才生效。如果 user 验证不到，先尝试 Streamlit Cloud Manage app → Reboot。
3. **`launchctl bootstrap gui/$(id -u)`** — install_launchd_wiki.sh 用了现代 API，fallback 到 legacy `launchctl load`。`id -u` 在 zsh / bash 都可用，但若用户 Mac 是 enterprise managed 有 SIP 限制，bootstrap 可能拒载。先跑 install 看 stderr。
4. **`exec >> "$LOG_FILE" 2>&1`** in wiki_weekly_sync.sh — 这把整个脚本 stdout/stderr 重定向到 log file。如果 log file path 不存在的 dir，会 fail。但 script 顶部已 `mkdir -p "$LOG_DIR"`，应该 ok。
5. **sanitization 漏网之鱼** — 我只抽样 verify 了 1530.HK 和 1093.HK。其他 30 个 sanitized files 可能还有未 cover 的 leak pattern（特别是 LLY US 的长 memo，有 1Q25 / 2Q25 业绩快照 sections 也是直接引用 CMS 研报）。用户在 demo 前应抽 3-5 个高敏感 ticker（LLY / 1093 / 1801 / 2616）spot check 一次。
6. **app slug `agentmental-research` 是否长期合适** — user 决策时是 60s 决策，未深思。如果之后想做 multi-domain（AI / consumer / industrial），"research" 可能太窄。改 slug 会破 deep-link，等于换 brand。建议 demo 1-2 周后再 revisit，不急。

<!-- HANDOFF-END -->
