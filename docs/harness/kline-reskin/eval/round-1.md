# Stage 2 · Independent Evaluator — Round 1 Verdict

Task: K线行情 FT-salmon glass 1:1 重实现 · Ticker Drill 整页 reskin
Branch: `feat/kline-reskin` @ `ccb9bec` (all Builder work committed)
Evaluator context: independent (did not author any app/ code); zero app-edit rights.
Real machine: `bash docs/harness/kline-reskin/init.sh` → :8599 HTTP 200 (killed+relaunched, no stale lib cache).
Primary test ticker: `000977.SZ` (浪潮信息) — has real yfinance OHLCV (267 candles) AND a wiki page with 催化剂/风险点 (so the 多空看板 rendered live). Cross-tickers for G2: `000660.KS`, `LLY`.

**Headline: 37 PASS / 4 FAIL (P8c, T2, T10, T11) + 2 documented minor deviations (T5 eyebrow, T6 down-chip). 8/11 features flip to `passes:true`; U2/U4/U8 held at false.**

Methods legend: JS = claude-in-chrome computed-style probe (primary gate) · EO = echarts getOption probe · GR = grep battery · RM = real machine · SS = screenshot corroboration.

---

## Verdict table (contract §2 order)

| id | verdict | expected | measured | method |
|---|---|---|---|---|
| P1 | PASS | stApp bg #fff1e5 | `rgb(255, 241, 229)` | JS |
| P2 | PASS | dual radial wash (900×520@10%/-8% α.09 + 820×520@94%/4% α.10) | `radial-gradient(900px 520px at 10% -8%, rgba(200,16,46,0.09)…) , radial-gradient(820px 520px at 94% 4%, rgba(13,118,128,0.1)…)` | JS |
| P3 | PASS | tick 5×44 #c8102e + name 30/700 + chip mono border #e4d2bd, same row | tick `5px×44px rgb(200,16,46)`; name `30px/700` Space Grotesk; chip border `rgb(228,210,189)` mono; nmrow has name+chip | JS |
| P4 | PASS | bottom rule 2px solid #1a1a1a | `2px solid rgb(26, 26, 26)` | JS |
| P5 | PASS | sub mono 12.5px `日K线 · MA5/MA10/MA20 · 成交量 · <时段>` | `12.5px` mono; text `日K线 · MA5 / MA10 / MA20 · 成交量 · 09:30 — 15:00 (UTC+8)` | JS |
| P6 | PASS | teal dot #0d7680 anim 1.5s∞; EOD label; clock; 0 tick-interval; 0 buttons | dot `rgb(13,118,128)` anim `1.5s ease-in-out infinite liveBlink`; label `EOD 数据流`; clock running `14:15:19`; `tick interval`=absent; buttons=0 | JS+GR |
| P7 | PASS | Space Grotesk self-host relative + @font-face in srcdoc; no CDN | srcdoc has `@font-face` + `Space Grotesk`; url `app/static/fonts/space-grotesk-var.woff2` (rel); zero real googleapis/gstatic (1 comment-only hit stock_header.py:15) | JS+GR |
| P8a | PASS | KPI glass 4-value + shadow none | bg `rgba(255,255,255,0.55)`, `blur(14px)`, border-top `3px solid rgb(26,26,26)`, radius `0px`, shadow `none` | JS |
| P8b | UNTESTED (code-verified) | consensus_house `.cmsi-ch` glass | not rendered for 000977 (no house rating/TP). `GLASS_CARD_CSS` targets `.cmsi-ch` with identical recipe as verified `.cmsi-stat-strip` (same selector group, theme.py:1007) | JS+GR |
| **P8c** | **FAIL** | 多空看板 cards border-top **3px solid #1a1a1a** | both cards glass OK, but border-top = **`3px solid rgb(13,118,128)` (bull/teal) / `3px solid rgb(200,16,46)` (bear/red)** — NOT #1a1a1a. Fix: stock_header.py:211,218 (bull_card/bear_card inline `border-top:3px solid {t.UP}/{t.CMSI_RED}`). See adjudication note below. | JS |
| P8d | UNTESTED (code-verified) | memo bar `.cmsi-memo-bar` glass | not rendered for 000977 (no wiki rating/TP bar). `GLASS_CARD_CSS` covers `.cmsi-memo-bar` identically | JS+GR |
| P8e | PASS | stat strips glass 4-value | `rgba(255,255,255,0.55)`/`blur(14px)`/`3px solid rgb(26,26,26)`/`0px`/`none` (2 strips: returns+valuation) | JS |
| P8f | PASS | expander glass 4-value | same 4-value (4 expanders) | JS |
| P9 | PASS | no wash/glass leak on Sector Heatmap + Strategy Picks | both: bgImage `none` (no radial); expander border-top `1px` (not 3px ink); page_radial_wash+GLASS_CARD_CSS injected only in 6_Ticker_Drill:200-201, outside theme._CSS | RM+GR |
| P10 | PASS | zh/en parity, no new emoji | 105 drill.* keys each, zero set-diff; +1 key (`drill.term.meta_line`) both; no emoji in added lines | RM+GR |
| T1 | PASS | html,body 100%; color-scheme light; bg #fff1e5 | srcdoc `html,body{height:100%`; body bg `rgb(255,241,229)`; colorScheme `light` | JS |
| **T2** | **FAIL** | iframe wash **同 P2 参数** (900×520@10%/-8% α.09 + 820×520@94%/4% α.10) | `.glow` = **`820px 480px at 8% -10% α.08`** + **`760px 480px at 96% 4% α.10`** — geometry+red-alpha differ from P2. Fix: candlestick_terminal.py:218-221. | JS |
| T3 | PASS | glass 4-value + pcard box-shadow removed | chartcard+pcard: `rgba(255,255,255,0.55)`/`blur(14px)`/`3px solid rgb(26,26,26)`/`0px`/shadow `none` | JS |
| T4 | PASS | grid 1fr 340px, gap 26px | `664px 340px`, gap `26px` | JS |
| T5 | PASS (price) · minor dev | eyebrow mono 11px/.16em; price 46px/700 mono dynamic; ccy | price `46px/700` `rgb(13,118,128)` mono + `CNY`; **eyebrow measured `10px`/`.1em` vs spec `11px`/`.16em`** (candlestick_terminal.py:232-233) | JS |
| T6 | PASS (up) · code dev (down) | up chip rgba(13,118,128,.12) / down rgba(200,16,46,**.10**) | live up-day: `rgba(13,118,128,0.12)` ✓. **Code hardcodes `.12` for BOTH dirs → down would be `rgba(200,16,46,.12)` ≠ contract .10** (candlestick_terminal.py:131) | JS+src |
| T7 | PASS | 高 teal / 低 red / 开·收 ink | 开 `67.00 rgb(26,26,26)`; 高 `69.21 rgb(13,118,128)`; 低 `63.79 rgb(200,16,46)`; 收 `67.25 rgb(26,26,26)` | JS |
| T8 | PASS | only-available metrics, no 2.69/1.34/28.4 | 4 cells: 振幅 `8.50%` (cross-checks (69.21−63.79)/63.79), 量比(5日) `1.01x`, 换手率 `6.06%`, 市盈率 `18.3x`; no demo literals (GR7 clean) | JS+GR |
| T9 | PASS | 0 buttons, no fake tick setInterval | buttons=0; `setInterval` absent from terminal srcdoc | JS+GR |
| **T10** | **FAIL** | footer = `配色(港美股惯例):青=涨·红=跌(与A股红涨绿跌相反)` + provenance; no MOCK | footer = **`来源: yfinance · 复权 OHLCV · 000977.SZ · 截至 2026-07-03` ONLY — color-convention note MISSING**. (Note: the same convention note DOES exist on the home treemap, so this is a drop, not a global choice.) Fix: candlestick_terminal.py:372-376/389. Violates §4 still-valid invariant "涨 teal + 页脚惯例注". | SS+GR |
| **T11** | **FAIL (literal) / borderline** | 页模式图容器 560px; modal scales, slider unclipped | `#kc` offsetHeight = **`504`** (page mode = render height 560 − 56 footer budget), not 560. Grids are %-based so proportional (C6 PASS); slider not clipped (SS). Modal (height 480) scales + slider unclipped (G6 SS). Fix or contract-amend: candlestick_terminal.py:207. See note. | JS+EO+SS |
| C1 | PASS | candle #0d7680/#c8102e + borders | `color:#0d7680, color0:#c8102e, borderColor:#0d7680, borderColor0:#c8102e, borderWidth:1` | EO |
| C2 | PASS | MA5 #e0963c / MA10 #b8b1a8 / MA20 #1a1a1a | `#e0963c` / `#b8b1a8` / `#1a1a1a` | EO |
| C3 | PASS | MA width1, smooth true, symbol none | all three: `width:1, smooth:true, symbol:'none'` | EO |
| C4 | PASS | legend left-top, mono, fs 11 | `left:12, top:6, fontSize:11, ff:JetBrains Mono` | EO |
| C5 | PASS | tooltip #1a1a1a/#fff1e5, cross dashed #b8b1a8, 开/收/低/高 | bg `#1a1a1a`, text `#fff1e5`, axisPointer `cross`/`#b8b1a8`/`dashed`, formatter=fn | EO |
| C6 | PASS | grids 7.9%/57.1% + 71.4%/19.6% | `[{top:7.9%,h:57.1%},{top:71.4%,h:19.6%}]` | EO |
| C7 | PASS | y right, splitLine #ebd9c8, x-line #d4c4b0 | yAxis0 `right`/split `#ebd9c8`; yAxis1 `right`; xAxis line `#d4c4b0` | EO |
| C8 | PASS | inside+slider bottom6 h14 filler rgba(200,16,46,.12) handle #c8102e border #d4c4b0 | slider `bottom:6,h:14,filler:rgba(200,16,46,.12),handle:#c8102e,border:#d4c4b0` + inside | EO |
| C9 | PASS | vol rgba(13,118,128,.5) / rgba(200,16,46,.5) | first 3 bars: `rgba(13,118,128,.5),rgba(200,16,46,.5),rgba(13,118,128,.5)` | EO |
| C10 | PASS | series exactly {日K,MA5,MA10,MA20,Vol}, no bench | `[日K,MA5,MA10,MA20,Vol]` types `[candlestick,line,line,line,bar]` | EO |
| C11 | PASS | mountEChart, __echartsRO present, no bare init | `__echartsRO`=true; candle data len 267; zero bare `echarts.init` outside MOUNT_JS (GR1) | EO+GR |
| G1 | PASS | py_compile all changed .py | `PY_COMPILE_ALL_CLEAN` (7 files) | RM |
| G2 | PASS | AppTest 000977.SZ + 000660.KS + US no exception | all three `OK` (AppTest.exception empty) | RM |
| G3 | PASS | init.sh 200 + 3× reload candle draws | 200 in 1s; reload×3 → 267 candles each, canvas 1292×1008 non-blank | RM |
| G4 | PASS | grep battery 10 patterns clean | all clean; only comment/docstring hits (GR2 stock_header:15 "不引…", GR6 home:238/market_hub_tiles:25 "非 MOCK", GR8 comments "无 box-shadow", GR9 ✓-in-comment) | GR |
| G5 | PASS | bench channel fully removed | `bench_overlay|_terminal_bench_overlay` zero repo-wide; `benchName` only in whitelisted strategy_hero.py (×3) | GR |
| G6 | PASS | kline_picker modal new-skin renders, no crash | live: selected 000977 → modal `个股 K 线 · K-line` rendered glass terminal (header+candles+MA+vol+red slider unclipped+panel+footer) | RM+SS |
| G7 | PASS (code inspection) | no-OHLCV plotly RS fallback works | fallback branch 6_Ticker_Drill.py:518-552 (`else` → relative_strength_chart / price_line_chart from DB close); `_route_benchmarks` retained (:110) | RM |
| G8 | PASS | list mode: shell new-skin, quote_table unchanged | fresh session bare /Ticker_Drill → heading `行情 / 个股`, radial wash present, glass stat cards (497/497), selectbox + quote-table iframe render | RM+SS |
| G9 | PASS | 1440×900 gestalt vs design | corroboration matches FT-salmon glass (masthead + 340px right panel + red slider + teal/red candles); binding verdict via JS/EO | SS |

---

## FAILs — fix locations

1. **P8c** `app/lib/stock_header.py:211,218` — bull/bear cards use inline `border-top:3px solid {t.UP}` (teal) / `{t.CMSI_RED}` (red). Contract P8 mandates uniform `border-top:3px solid #1a1a1a` for all six glass blocks incl. 多空看板. **Adjudication flag:** the teal/red top borders are a plausibly *intentional* semantic signal (bull=teal, bear=red). If George/orchestrator wants to keep them, amend CONTRACT P8 to exempt 多空看板's top-border color (bg/blur/radius/shadow already conform). Otherwise change to `theme.INK`. Either way the frozen contract as written is not met.

2. **T2** `app/lib/candlestick_terminal.py:218-221` — `.glow` wash = `820px 480px at 8% -10%, rgba(200,16,46,.08)` + `760px 480px at 96% 4%, rgba(13,118,128,.10)`. Contract T2 requires "同 P2 参数" i.e. `900px 520px at 10% -8%, rgba(200,16,46,.09)` + `820px 520px at 94% 4%, rgba(13,118,128,.10)`. Align the geometry (900/520, 10%/-8%, 820/520, 94%/4%) and the red alpha (.08→.09).

3. **T10** `app/lib/candlestick_terminal.py:372-376` (+ line 389 `.fnote`) — `src_note` carries only the yfinance provenance. Contract T10 + §4 still-valid invariant require the color-convention note `配色(港美股惯例):青 = 涨 · 红 = 跌(与 A 股红涨绿跌相反)` in the footer as well. Prepend/append it (bilingual). This is a hard regression against a preserved invariant — highest-priority fix of the four.

4. **T11** `app/lib/candlestick_terminal.py:207` — page-mode `#kc` = `height-56` = 504px, not the contract's "560px". Low severity: grids are %-based (C6 proportional) and the slider is not clipped, so it renders correctly — but the literal 560 probe fails. Fix EITHER by making page-mode chart height 560 (e.g. pass `height=616` from the page or drop the −56 and give the footer its own budget) OR amend CONTRACT T11 to state the render-height *parameter* is 560 with #kc=504 by design.

## Minor deviations (not failing their item, but flagged for the Builder)

- **T5 eyebrow** candlestick_terminal.py:232-233 — `.plbl` is `font-size:10px; letter-spacing:.1em`; design spec is `11px/.16em`. Price (the load-bearing assertion) is correct.
- **T6 down-chip** candlestick_terminal.py:131 — alpha hardcoded `.12` for both directions; contract wants down = `.10`. Live ticker was up so only the up-case (`.12`, correct) was directly observable.

## Notes for the Codex Auditor (Stage 4)
- P8b/P8d could not be live-rendered on 000977.SZ (no house rating/TP). They are code-verified via the shared `GLASS_CARD_CSS` selector group (theme.py:1007) proven correct on `.cmsi-stat-strip`/expander. A ticker with a full house-view wiki (e.g. a covered HK/US name with rating+TP) would render them for direct confirmation.
- 4 real machine screenshots saved to disk (page-mode terminal, modal, masthead 1440, list mode) as SS corroboration; binding verdicts are JS/EO.
