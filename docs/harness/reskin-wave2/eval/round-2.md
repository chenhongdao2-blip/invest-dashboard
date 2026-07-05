# Stage 2 · Independent Evaluator — Reskin Wave-2 · Round 2 (in progress)

Branch @ `618319a` · continues Round 1 (which found+fixed IPO15, resolved HERO8). Round 2 completes the computed-style spot items after the browser reconnected. Incremental.

## W1-IPO — **COMPLETE, all 15 PASS** → flip
Round 1 verified IPO2/4/9/10/12/15. Round 2 computed-style:
- IPO1: masthead red bar **5px×48px rgb(200,16,46)** #c8102e ✓.
- IPO3: KPI 3-card glass tri-color 顶边 — 样本 **3px #1a1a1a** / 最高 **3px #0d7680** / 最差 **3px #c8102e**, all bg `rgba(255,255,255,0.55)` + `blur(14px)` ✓.
- IPO5: 分档表现/TIER PERFORMANCE section header present ✓. IPO6: tier bars render on real tier data (5-tier fixed order, computed medians) ✓.
- IPO7: all **5 tier colors** present — #a00d25 / #c8102e / #0d7680 / #a06d1f / #6b6560 ✓.
- IPO8: ranking table + dock in **one** iframe (single srcdoc, hover-linkable) ✓.
- IPO11: dock `position:sticky; top:16px`, bg `rgba(255,255,255,0.6)`, `blur(16px)`, border-top **3px #1a1a1a** ✓.
- IPO13: footer box border **1px #e4d2bd**, bg `rgba(255,255,255,0.4)`, JetBrains Mono, **no MOCK** ✓.
- IPO14: superseded toggle/facets removed (GR battery clean).
**W1 → passes:true.**

## W6-BANR — one deviation (BANR2 H1), rest PASS
- BANR2: red bar **5px×34px #c8102e** ✓. BUT **H1 "AI Agent 选股 · 策略表现" computes `font-weight:600` + `font-family: Inter…` (Space Grotesk absent)** — the module's inline `font-family:"Space Grotesk",…` IS set on the H1, but a Streamlit/theme heading rule overrides it (markdown H1, not iframe). Contract BANR2 wants **32px/700 + FONT_DISPLAY (Space Grotesk)**; rendered is Inter/600. **FAIL (medium)** — fix needs higher-specificity/`!important` on the banner H1 (or render title as a styled span, not `<h1>`). Blocks W6.
- BANR6: 3-card glass strip = `rgba(255,255,255,0.55)` + `blur(14px)` + border-top **3px #1a1a1a** ✓.
- BANR8: 盈亏点带 = SVG circles, **teal 26 / red 16, zero random** (real per-holding sign; GR④ no Math.random) ✓.
- BANR10: 双轨 cards border-left **3px #c8102e** (×2) ✓.
- BANR3/5/7 (R1): teal dot #0d7680 + honest DAILY, "3 STRATEGIES" chip, mono32 sign-colored + D2 #c8102e ✓.
- PENDING: BANR1(display font — code sets it but see BANR2 override), BANR4 dek copy, BANR9 IPO card, BANR11/12.
**W6 held false (BANR2 FAIL).**

## W5-HERO — verified items PASS, no hard FAIL (2 spot pending)
- HERO1: hero card glass bg `rgba(255,255,255,0.55)` + blur + **border-top 3px #c8102e** + radius 0 + **box-shadow none** ✓.
- HERO4: 巨号 **56px / 700 / JetBrains Mono**, sign-colored teal (+19.1%) ✓ (replaced non-mono 60/62).
- HERO6: **MDD value = `rgb(200,16,46)` #c8102e** (17px mono) ✓; SHARPE ink ✓. NIT: 胜率 "19 / 20" reads ink on the combined cell (contract wants 胜率 teal #0d7680) — the win number may be teal with a gray "/20" denominator; needs a finer split-probe before calling it.
- HERO7/8/9/11 (R1): strat #c8102e/w2.2/area, bench #8a8580 dashed, legend Space Grotesk, axisPointer line (contract-corrected), curve rebased 100→118.52 real, __echartsRO ✓.
- HERO2: srcdoc @font-face+Space Grotesk, double radial wash, body ff Space Grotesk ✓.
- HERO3: teal dot #0d7680, no fake-realtime, left-col border-right **#e4d2bd** ✓.
- HERO5: α label #c8102e/10px ✓; α value "+1.5pp" teal/17px/mono sign-colored ✓.
- HERO6 WIN-teal NIT **RESOLVED**: win number "19" = `rgb(13,118,128)` teal, "/ 20" gray denominator — correct (earlier grab was the combined cell). **HERO6 fully PASS.**
- **HERO12 GAP**: "QUANTAMENTAL · 量化基本面" right-float page-header label **absent from page DOM**; no 5×36 page-header bar (only banner's 5×34). Contract HERO12 wants red bar 5×36 + QUANTAMENTAL label. Either folded into BANR (contract note needed) or a real gap — flag for Builder. HERO10 render gate = code-verified (curve gate + no-mock).
**W5: HERO1-9,11 PASS; HERO12 gap open. Not flipped pending HERO12 disposition.**

## Round 2 FAIL ledger (so far)
| id | sev | expected | measured | fix |
|---|---|---|---|---|
| BANR2 | MED | H1 32px/**700** + Space Grotesk (FONT_DISPLAY) | 32px/**600** + Inter (Space Grotesk overridden) | force display font+700 on banner H1 (specificity/!important or styled span) — `strategy_banner.py` live_title |
| HERO12 | LOW-MED | 页面层页头 红条5×36 + 右浮 "QUANTAMENTAL · 量化基本面" | label absent from page DOM; only banner 5×34 bar | add the QUANTAMENTAL page-header eyebrow (or orchestrator confirm it's folded into BANR → contract note) — `4_Strategy_Picks.py` strategy-tab header / `strategy_hero.py` |

## W7-guards — **COMPLETE, all 7 PASS** → flipped
- GRD1 grep battery (12) clean · GRD2 no box-shadow/radius≥5/emoji in 6 modules · GRD3 parity 721==721 · GRD4 py_compile + AppTest 4/4 OK (post-fix) · GRD7 :8599 200 + echarts render.
- GRD5 no-leak: SEC Facts / Capital Markets / e2_etf_heatmap do **not** call `page_radial_wash`/`GLASS_CARD_CSS` (grep) — page_radial_wash callers = only the 4 opt-in pages (2_Healthcare/4_Strategy/6_Ticker_Drill/a2_ai_overview).
- GRD6 theme boundary (D5): `GLASS_CARD_CSS` (theme.py:1008) + `page_radial_wash` (1022) defined **outside** `_CSS` (185) — page-scoped, not global.
**W7 → passes:true.**

## HUB tail (partial) — HUB2 no-fake ✓, HUB8 52W ✓, HUB9 情境行 ✓; HUB1 kicker + HUB2 dot visually confirmed (computed probe too strict, re-probe pending). HUB5/10/12 pending.

---

## Post-fix (@cfad103) completion

**BANR2 FIXED + verified**: title now a styled `<div>` (bypasses `.stMarkdown h1` override) → computed **Space Grotesk / 32px / 700** ✓. **HERO12 contract-void** (adjudicated "与 BANR 页头重复计项" @cfad103) → removed from scoring.

**W2-HUB completed → flipped**: HUB1 kicker "CMSI · MARKET HUB · 四大指数总览" 11px/#8a8580/.08em/JetBrains Mono ✓; HUB5 double wash+cream ✓; HUB10 count-up ✓; + R1/R2 HUB2(no-fake+teal dot)/HUB3/4/6/7/8/9/11 ✓.
**W3-TMAP completed → flipped**: TMAP1 color-scheme light ✓; TMAP2 masthead ✓; TMAP3 gradient legend #a30000… ✓; TMAP4 no ⚠ + convention ✓; TMAP13 footer no-MOCK ✓; TMAP5 域条 ✓; + EO TMAP7/8/9/10/14 + #m h=400 (TMAP12).
**W4-SOVR completed → flipped**: SOVR4 wash ✓; SOVR5 期间收益色阶 gradient legend ✓; SOVR8 hover rule rgba(26,26,26,.045) ✓; SOVR9/SOVR13 down-color = **12× `rgb(200,16,46)` #c8102e** (▼-2.8%/-16.0%/-8.7%/-7.4%) ✓; SOVR11 GAINERS/LOSERS movers ✓; SOVR14 no raw-key ✓; + R1 SOVR1/2/3/6/7/10/12 both pages. (AI page shares same `sector_overview.py` code path.)
**W5-HERO completed → flipped**: HERO2/3/5 ✓ (this pass), HERO6 WIN-teal resolved, HERO12 void; + R1 HERO1/4/7/8/9/11 + HERO10 gate preserved.

## FINAL Round 2 verdict
**6 / 7 features PASS → flipped: W1-ipo-stage, W2-hub, W3-treemap, W4-sector, W5-hero, W7-guards.**
**1 held false: W6-banner** — only open item **BANR4** (dek styling).

### Remaining FAIL/NIT ledger
| id | sev | expected | measured | fix |
|---|---|---|---|---|
| BANR4 | LOW-MED | dek 14px / 1.65 / #4a4a4a / max-width 880 + 关键短语 `<b>` 墨 | `4_Strategy_Picks.py:139` renders `st.markdown(i18n.t("strategy.pitch"))` **plain** → 15px / #1a1a1a / full-width. **Copy is correct** (real pitch, no design-mock — BANR4's main ask ✓); only the styling wrapper is missing | wrap pitch in styled `<p style="font-size:14px;line-height:1.65;color:#4a4a4a;max-width:880px">…</p>` + `unsafe_allow_html=True` (or a `strategy_banner` dek helper) |

Fixed/resolved this cycle: IPO15 (import), HERO8 (contract typo), BANR2 (H1→div), HERO12 (voided). No other hard FAILs across all 86 items. Once BANR4 dek is wrapped, W6 flips → 7/7. cycles_used=1.

---

# Round 2 — INDEPENDENT FINISHER completion (@ HEAD `2d420d4`) → **7/7, all flipped**

Independent finisher (did not write any of this code; zero app-code edits). Began at `e507191`, re-launched the server (mandatory — lib changed), and re-verified the entire ~46-item computed-style tail with **measured** evidence (JS `getComputedStyle` rgb-normalized / EO / grep / AppTest). Mid-pass the repo advanced: `cfad103` (HERO12 void + CONTRACT amend) then `2d420d4` (**BANR4 dek fix**). `git diff --stat e507191 HEAD` = **only** `4_Strategy_Picks.py` + `CONTRACT.md` — so every module-level measurement below (all 6 libs) is unchanged and valid at HEAD; only BANR4's page-level dek changed and was re-verified against HEAD after a server restart.

### Independently re-verified with hard measured evidence (backs the cfad103 flips)
- **W2-HUB (12/12)** — HUB1 masthead (Space Grotesk 30/700, red bar 5×44 rgb(200,16,46) r1, kicker mono .08em INK_3, EOD·收盘 teal, EOD dot cmsiPulse 1.5s, border-b 2px INK); HUB5 iframe body = 2 radials red+teal; HUB8 track #ebd9c8 + teal fill + 2×9 ink marker; HUB9 `.tctx` mono .04em INK_3 + sign-colored red value; HUB10 real dek "2 涨 2 跌 …" + 4 count-up nodes + staggered mhtRise + reduced-motion; HUB2/3/4/6/7/11/12 (R1 + sig).
- **W3-TMAP (14/14)** — TMAP1 Space Grotesk + ss01/tnum + color-scheme light + wash 2 radials inset0; TMAP2 red bar 5×44 + title 26/700 + CMSI chip mono 10/700 PAPER-on-red .06em; TMAP3 legend 190×12 border #d4c4b0 gradient = exact `_ramp` 5 anchors; TMAP4 banner #f9e6d4/red-left, **⚠ absent**; TMAP5 domain bar #f9e6d4/red-left name 16/700; TMAP6 2nd-domain iframe headerless (masthead/banner absent, per-domain bar+canvas); TMAP12 #m 400px; TMAP13 footnote mono 11 INK_3 no-MOCK; TMAP11 payload shared w/ e2_etf (static); TMAP7/8/9/10/14 (R1 EO).
- **W4-SOVR (14/14, both pages)** — Healthcare: wash 2 radials; section head mono .16em INK + red tick 4×16 + legend 120×9 border #d4c4b0 exact 5-stop + 跌 #c8102e/涨 teal; Ticker td mono 12/700 .04em h46 border #ebd9c8 + `.sovr-row` hover; spark 1.5px non-scaling teal w110 dot r2.2 + down-cell #c8102e + rel track #f4ead9 h14 center #d4c4b0 value mono 12/700 w54; **movers 10 + 10**. AI_Overview: wash 2 radials, chip="**AI TECH**" (parameterized, no HEALTHCARE hardcode), legend present, LOSERS 10 rows d1 #c8102e "▼ -20.5%", GAINERS 10. SOVR13 `_DOWN=t.CMSI_RED` (module const, theme.DOWN untouched); SOVR14 parity 157/157 + bilingual labels; SOVR1/2/3/6/7/10/12 (R1).
- **W5-HERO (11/11; HERO12 voided)** — HERO2 Space Grotesk+ss01/tnum+overflow-hidden, wash 2 radials, @font-face in srcdoc; HERO3 left rgba .35 + border-r #e4d2bd + teal dot cmsiPulse + "持续跟踪 · EOD" honest; HERO5 bench 17/600 INK_2, α 17/700 teal sign-colored, α-label #c8102e, divider 1px #e4d2bd pl18; **HERO6 win-teal RESOLVED** (胜率 `.kh-num`=rgb(13,118,128) teal, "/ 20"=INK_3 gray; MDD #c8102e; 7-col grid; border-top #d4c4b0; tiles #ebd9c8); HERO10 render gate `4_Strategy_Picks.py:228-233` (portfolio/bench/normed non-empty + len≥10 + std>0, "audit MEDIUM B1/B2"); HERO1/4 (R2), HERO7/8/9/11 (R1). **HERO12 = CONTRACT-void @cfad103** (line 123 adjudication: hero-spec 页头 is a duplicate of the BANR2 masthead; banner版 语言钮+D3 EOD-dot is the implemented version; QUANTAMENTAL 装饰标 not implemented; "George 眼验可翻案"). This matches my own independent conflict analysis exactly (same page-top DOM; D3 EOD-dot governs the right-float). Accepted; flagged for George's eyeball confirm.
- **W7-GRD (7/7)** — GRD1 grep battery clean at e507191 (12 patterns; only whitelist negatives + self-test asserts); GRD2 no box-shadow/radius≥5, ⚠/emoji only in Python comments (treemap UI ⚠ removed = TMAP4), tabular-nums present; GRD3 pages 157/157 zero diff; GRD4 py_compile 10-clean + AppTest 4/4 OK; GRD5 `page_radial_wash`/`GLASS_CARD_CSS` only in the 4 opt-in pages + Ticker-Drill, SEC_Facts/HC_Capital_Markets/e2_etf leak-free + e2_etf unchanged `render_bento_html`; GRD6 `theme._CSS` zero new glass/wash (page-scoped constructs live module-level); GRD7 :8599 4-page 200 + `#m`/`#eq` echarts drew across ≥6 navigations.

### BANR4 re-verified at HEAD `2d420d4` — **PASS** ✓ (was the only open FAIL)
`4_Strategy_Picks.py:139-146` now wraps the pitch: `re.sub(r"\*\*(.+?)\*\*", '<b style="color:#1a1a1a;">…</b>', pitch)` inside `<p style="font-size:14px;line-height:1.65;color:#4a4a4a;max-width:880px;margin:16px 0 0;">`. `import re` present (line 15); py_compile clean; AppTest Strategy_Picks OK (re.sub runtime-safe). **Measured dek `<p>` at HEAD**: fontSize **14px** / lineHeight **23.1px** (=1.65) / color **rgb(74,74,74)** `#4a4a4a` / maxWidth **880px** / marginTop **16px** / bold = **4× `<b>` rgb(26,26,26)** ink; copy = real i18n pitch (`locales/zh.py:21`). Every BANR4 token now met. **W6 → all 12 PASS.**
(BANR1/2/9/11/12 measured this pass: BANR1 page wash 2 radials; BANR2 title DIV Space Grotesk 32/700 -0.32px + red bar 5×34 r1 + toggle mono .08em CMSI_RED-active + `?lang=zh` anchor + #d4c4b0 r3; BANR9 "54 样本 / 已上市38 待上市16" + median mono32/700 teal; BANR11 footer #f9e6d4 12.5px INK_2 mt14 red-tick 3×14; BANR12 pure page-DOM, no iframe. BANR3/5/7 R1, BANR6/8/10 R2.)

## FINISHER FINAL VERDICT (@ `2d420d4`)
**7 / 7 features PASS — all flipped to `passes:true`.** Scored items: 85 PASS / 85 (HERO12 voided from the 86 per cfad103 adjudication). **Zero open FAILs.** cycles_used → 2.
- Flipped this pass: **W6-banner → true** (BANR4 dek fix verified at HEAD).
- Confirmed (independent measured evidence backing the cfad103 flips): W1, W2, W3, W4, W5, W7.
- **Two open flags for the Codex Auditor / George eyeball gate** (substantively resolved, process-noted): (1) **HERO12 void** — contract amended by the build side, not the evaluator; substance is correct (I independently reached the same "BANR-duplicate, D3 EOD-dot governs" conclusion), marked "George 眼验可翻案". (2) **QUANTAMENTAL** decorative header label intentionally not implemented (consequence of HERO12 void). No 3-peat FAIL; no circuit-breaker stop.

---

# Codex-fix re-verification (@ HEAD `c8bb06e`) — all 7 findings FIXED & verified

After my "7/7 ALL GREEN" verdict, the cross-model **Codex auditor (CONTRACT §6) returned REJECT: 1 CRITICAL + 6 MAJOR** — every one a **data-correctness** defect that real-machine green / computed-style checks structurally cannot catch (rendering is *live*, but the *number* was wrong). Honest lesson logged: **visual/computed-green ≠ arithmetic-correct**; the evaluator (real-machine) and the auditor (CSV hand-computation + code-read) are genuine mutual blind spots — which is exactly why dual-authority exists. Builders committed the 7-file fix @`c8bb06e`; server restarted (lib+page changed). Targeted re-verification of my 5-item queue, this time cross-checking every number against CSV/loader arithmetic:

1. **RM restart** — init.sh → :8599 HTTP 200 @c8bb06e. ✓
2. **IPO 速览卡 (BANR9) ×100 — the CRITICAL — FIXED.** Locked CSV ground truth (`ipo_picks.csv`, 38 listed, `day1_ret` is a **decimal** ×100→pct): median **+76.1%** / hi **+384.0%** (曦智科技) / lo **-56.9%** (华健未来-B). **Measured @HEAD**: median big span "+76.1%" rgb(13,118,128) teal 32px/700; dist bars 最高 "+384.0%" teal / 中位 "+76.1%" teal / 最差 "-56.9%" **rgb(200,16,46) #c8102e**; two "+76.1%" instances (big + 中位); **zero stale +0.8%/+3.8%/-0.6%**. Fix at `4_Strategy_Picks.py:_overview_ipo_card` (`day1_ret … * 100`). Matches CSV exactly. ✓ *(My R2 "BANR9 PASS" had checked sample counts + non-mock but NOT the median vs CSV arithmetic — the miss Codex caught.)*
3. **pending rank '—' — FIXED.** ipo_stage iframe: 54 rows = **16 rank='—'** (pending) + **38 numbered** (listed); 16 pending also show 首日 '—'; last row rank '—'. Code: `r.rank === null ? '—'` + Python `"rank": None if is_pending`. ✓
4. **缺数 None→'—' (no fabricated 0.0) — FIXED.** (a) ipo_stage `__main__` self-test PASS all cases: all-pending → "暂无已上市样本", **no fabricated '0.0%'** in KPI divs, pending rows `rank: null`; NaN-close → path still emitted after dropping NaN, html 20,539 bytes. (b) Synthetic sector probe (direct helper calls): `_pct_cell(None)`/`_pct_cell(NaN)`/`_rel_bar(None|NaN)`/`_mover_row(d1=None)` → all emit '—', **fabricated_0.0=False**, no glyph; sanity `_pct_cell(-16.0)` still renders "-16.0%" in rgba(200,16,46). New `_is_missing()` gate in `sector_overview.py`. ✓
5. **hero 负值色 page-scope — FIXED.** `grep DOWN app/lib/strategy_hero.py` = **ZERO 'DOWN' token** (the `{DOWN}`/`DOWN=t.DOWN` placeholder removed); `_cum_col`/`_alpha_col` = `t.UP if ≥0 else t.CMSI_RED` (`strategy_hero.py:67-68`), MDD already CMSI_RED. Negative cum/α on the hero surface now renders **#c8102e** (D2), not the global #cc0000. Latent path (my R2 data had cum=+18.5% positive) closed by code-read. ✓

**Codex-fix verdict: all 7 findings FIXED & independently re-verified (real-machine + CSV arithmetic + synthetic None/NaN probes + code-read). feature_list stays 7/7 green (now data-correct, not just visually green). Awaiting Codex re-approve + George eyeball.**
