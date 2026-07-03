# Stage 2 · Independent Evaluator — Round 2 Verdict

Task: K线行情 FT-salmon glass 1:1 重实现 · Ticker Drill 整页 reskin
Branch: `feat/kline-reskin` @ `20cb669` (fix commit "R1 打回修复 … + P8c 语义色契约裁决")
Real machine: `init.sh` → :8599 HTTP 200 (killed+relaunched, no stale lib cache; py_compile clean on 4 changed .py).
Tickers: `000977.SZ` (up-day, has bull/bear board), `AVGO` (down-day, for T6 down-case), `LLY` (house-view probe).

**Result: all 5 R1 FAILs/minors FIXED and re-verified live; P8c re-scored PASS under amended contract; P8b/P8d remain code-verified (environment-blocked). ALL 11 FEATURES → `passes:true`. No regressions.**

---

## R1 remediation — re-verification (real machine, computed-style)

| id | R1 status | R2 verdict | expected | measured | fix confirmed |
|---|---|---|---|---|---|
| **T2** | FAIL | **PASS** | `.glow` = 900×520@10%/-8% α.09 + 820×520@94%/4% α.10 (=P2) | `radial-gradient(900px 520px at 10% -8%, rgba(200,16,46,0.09)…), radial-gradient(820px 520px at 94% 4%, rgba(13,118,128,0.1)…)` | candlestick_terminal.py:219-221 |
| **T10** | FAIL | **PASS** | footer = 色约定注 + provenance | `配色(港美股惯例):青 = 涨 · 红 = 跌(与 A 股红涨绿跌相反) · 来源: yfinance · 复权 OHLCV · 000977.SZ · 截至 2026-07-03` (bilingual EN verified in source) | candlestick_terminal.py:373-379 |
| **T11** | FAIL | **PASS** | 页模式 #kc = 560, slider unclipped | `#kc offsetHeight = 560`; iframe = 642; body scrollH==clientH==642 (no overflow clip); slider fully visible above footer (SS ss_89332zvxz) | candlestick_terminal.py:208-210 (chart_h=height; iframe_h=height+82) |
| **T5** | minor dev | **PASS** | eyebrow 11px/.16em | `font-size:11px`, `letter-spacing:1.76px` (=.16em); price `46px/700` teal | candlestick_terminal.py:234-235 |
| **T6** | minor dev | **PASS** | up chip .12 / down chip .10 | up (000977 +4.83%): `rgba(13,118,128,0.12)`; **down (AVGO −2.41%): `rgba(200,16,46,0.1)`** — both live | candlestick_terminal.py:131 (`chip_alpha = ".12" if up else ".10"`) |

## P8c — re-scored under amended CONTRACT (R1 裁决 2026-07-03)

CONTRACT P8 amended: 多空看板 顶边允许 BULL teal `#0d7680` / BEAR red 语义色 (3px); 其余四值照断。

| id | R2 verdict | measured | note |
|---|---|---|---|
| **P8c** | **PASS** | bull card: bg `rgba(255,255,255,0.55)`, `blur(14px)`, border-top `3px solid rgb(13,118,128)` (teal — allowed), radius `0px`, shadow `none`; bear card: same but border-top `3px solid rgb(200,16,46)` (red — allowed) | four glass values conform; teal/red top is the sanctioned semantic exception |

## P8b / P8d — environment-blocked, code-verified (per orchestrator instruction "两只都不渲则保持 code-verified 并注明")

Tried `000977.SZ` and `LLY`: neither renders `.cmsi-memo-bar` (P8d) or `.cmsi-ch` (P8b). Root cause is the **eval machine environment, not the code**:
- Internal wiki root `~/Documents/LLM Wiki/Wiki/companies` is **absent** on this machine; only the sanitized public wiki (`data/wiki/companies`, 196 files) exists, and it is `is_sanitized=True`.
- Sanitized files explicitly strip Rating/TP (`CMSI 内部 Rating / TP … 已删除`) and put 评级 in a `| 评级 |` table that the `**Rating**:` parser (wiki.py:150) does not read → `page.rating`/`page.tp` empty for every ticker.
- P8d memo bar renders only when `wiki_page.rating or wiki_page.tp` (6_Ticker_Drill.py:586-591) → never here.
- P8b consensus_house renders only when `not is_sanitized AND rating/tp AND consensus` (6_Ticker_Drill.py:441-446) → structurally impossible with sanitized-only wiki.

**Code-verification (rigorous, not a guess):** `GLASS_CARD_CSS` (theme.py) applies the glass recipe to `.cmsi-memo-bar, .cmsi-stat-strip, .cmsi-ch, .cmsi-note, [data-testid="stExpander"] details` in ONE declaration block, with `!important` on background / border / border-top / border-radius / box-shadow. Two selectors in that identical block — `.cmsi-stat-strip` and `[data-testid=stExpander] details` — were live-confirmed this round computing `rgba(255,255,255,0.55) / blur(14px) / 3px solid rgb(26,26,26) / 0px / none`. Since `.cmsi-memo-bar` and `.cmsi-ch` share the same `!important` rule, they compute identically on all five glass properties; no base `_CSS` rule can leak through those five `!important` declarations. → **P8b/P8d PASS by shared-selector proof.** (A machine with the internal wiki present would render them directly for a covered name with rating+TP.)

## Regression sweep (no drift from R1 PASSes)

Re-probed live on both up (000977) and down (AVGO) terminals:
- T1 body bg `#fff1e5` + color-scheme light ✓ · T3 chartcard+pcard glass 4-value + shadow none ✓ · T4 grid `664px 340px` gap `26px` ✓ · T7 OHLC 开/收 ink, 高 teal `rgb(13,118,128)`, 低 red `rgb(200,16,46)` ✓ · T8 4 real cells (振幅 8.50% cross-checks) ✓
- C6 grids still `7.9%/57.1% + 71.4%/19.6%` (now proportional on the 560px canvas), dataZoom slider `bottom:6/height:14` ✓; 267 candles rendered ✓ — chart option untouched by the fix commit.
- P8a KPI / P8e stat-strip / P8f expander still `3px solid rgb(26,26,26)` glass ✓ (no ink→color drift).

## Final feature ledger

| feature | accept | R2 |
|---|---|---|
| U1-fonts | P7 | PASS (R1) |
| U2-term-shell | T1,T2,T3,T4,T11 | **PASS** (T2/T11 fixed) |
| U3-term-header | P3,P4,P5,P6 | PASS (R1) |
| U4-term-panel | T5,T6,T7,T8,T9,T10 | **PASS** (T5/T6/T10 fixed) |
| U5-chart-option | C1-C9,C11 | PASS (R1) |
| U6-bench-removal | C10,G5 | PASS (R1) |
| U7-page-shell | P1,P2,P9 | PASS (R1) |
| U8-page-sections | P8a-f | **PASS** (P8c amended; P8b/P8d code-verified) |
| U9-i18n-guards | P10,G1,G4 | PASS (R1) |
| U10-regression | G2,G3,G6,G7,G8,G9 | PASS (R1) |
| U11-harness-init | G3 | PASS (R1) |

**11/11 features PASS. Zero outstanding FAILs. Ready for Stage 4 (Codex异模型终审) + Stage 5 (George 眼验 ship).**

Note for Codex Auditor: P8b/P8d were not live-rendered on this eval machine (internal wiki absent). Recommend the auditor (or George on his machine, which has `~/Documents/LLM Wiki/`) render one covered name with a house rating+TP to close the last live-confirmation gap; the CSS proof is sound but a direct render would fully retire the code-verified caveat.
