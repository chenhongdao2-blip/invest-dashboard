# Stage 2 · Independent Evaluator — Reskin Wave-2 · Round 1 (CLOSED)

Branch: `feat/kline-reskin` @ `618319a` (started 6b568cf; Builder pushed IPO15+HERO8 fix mid-round) · Contract: `docs/harness/reskin-wave2/CONTRACT.md` (86 items) · Real machine: :8599 (restarted after the lib fix).

**Round 1 outcome: 1 hard FAIL found (IPO15 import) → FIXED @618319a and re-verified; 1 contract typo (HERO8) corrected → PASS. All 6 blocks render and match design on structure / data-integrity / interaction. Remaining ~46 computed-style *spot* items were interrupted by a browser-extension disconnect (OAuth account mismatch) — deferred to Round 2, NOT failures.** No demo-literal / fake-series / CDN / MOCK violations. cycles_used=1.

---

## §A · Static gates (W7) — GRD1 ✓ / GRD3 ✓ / GRD4 ✓ (after fix)
- **GRD4 py_compile**: all 6 modules + 4 pages CLEAN.
- **GRD1 grep battery (12 patterns)**: CLEAN. Only hits are ipo_stage.py `if __name__=="__main__":` self-test (lines 631+) asserting no MOCK/CDN and using fixture literals `+384.0%/-56.9%` — never in the Streamlit render path.
- **GRD3 parity**: pages_zh vs pages_en = **721 keys each, zero diff**.
- **GRD4 AppTest**: **initially `4_Strategy_Picks: EXC ModuleNotFoundError: No module named 'app'`** (root: `ipo_stage.py:22 from app.lib import theme` — the only `from app.` import in the repo; `app/__init__.py` absent). **FIXED @618319a → `from lib import theme`; re-run AppTest = home / 4_Strategy_Picks / 2_Healthcare / a2_ai_overview ALL OK.** ✓

## §B · RM smoke (GRD7) — PASS
init.sh → :8599 HTTP 200; home / Strategy_Picks / Healthcare / AI_Overview all render live. (echarts #m + #eq both drew; explicit 3×-reload loop deferred with the browser pass.)

## §C · Per-block verification

### W2-HUB (home) — verified items PASS
- HUB3: eyebrow renderer label = **"SVG"** (honest, not fake ECHARTS) ✓.
- HUB4: glass container = bg `rgba(255,255,255,0.55)` / `blur(14px)` / border-top `3px rgb(26,26,26)` / **h 248px** ✓.
- HUB6: prices mono JetBrains Mono/700; down deltas -1.61% & -2.03% = **`rgb(200,16,46)` #c8102e** (D2) ✓.
- HUB7: **4 inline-SVG sparklines, zero echarts** in srcdoc ✓.
- HUB2 (D3): teal EOD dot + "EOD · 收盘" + "EOD 2026-07-02 HKT", no TRACKING (visual ✓; hex spot pending). HUB11 footer "SOURCE … cron EOD … 仅供参考", no MOCK (visual ✓).
- PENDING (browser-blocked): HUB1 kicker, HUB5 wash, HUB8 52W bar, HUB9 情境行, HUB10 v2-increments, HUB12 signature.

### W3-TMAP (home) — echarts core PASS (EO)
`#m` getOption: type treemap / roam false / nodeClick false / **levels 2** / animationDuration 900 (TMAP7); tooltip bg+border `#1a1a1a` (TMAP8); upperLabel h26 / **fontFamily 'Space Grotesk'** / #1a1a1a (TMAP9); real payload dataLen 9 (TMAP14); `__echartsRO` present (TMAP10 mountEChart). PENDING: TMAP1-6 (masthead/legend/banner/域条), TMAP11-13 spot.

### W4-SOVR (Healthcare + AI_Overview) — dual-page PASS (both rendered)
- **SOVR1 dual-page spillover CONFIRMED**: Healthcare "领域基准及同业 **HEALTHCARE**" + AI_Overview "域基准(^SOX)与同业 **AI TECH**" — parameterized, no hardcoded HEALTHCARE (SOVR2 ✓, multi-industry respected).
- SOVR3: teal masthead dot `rgb(13,118,128)` #0d7680, anim 1.5s (new teal dot) ✓.
- SOVR6: benchmark-table glass = `rgba(255,255,255,0.5)` / `blur(14px)` / no accent top ✓.
- SOVR7: th = transparent bg / **`rgb(138,133,128)` #8a8580** gray / JetBrains Mono / **border-bottom 1.5px solid rgb(26,26,26)** ✓ (was red header+red line). NIT: th `border-left:1px` — verify no visible vertical divider (screenshot clean).
- SOVR10: movers **▼ -x.x% negative-sign** + GAINERS/LOSERS双语 ✓.
- SOVR12: real `<table>` in main DOM, **not iframe** ✓.
- down-color red on both pages (IHI -16.0%, ^SOX -5.4%, 515880.SS -49.9%) visually #c8102e; computed hex + SOVR4/8/9/11/13/14 spot PENDING.

### W5-HERO (Strategy Picks) — verified items PASS (EO)
- HERO7: strategy line **#c8102e / w2.2 / smooth / symbol none / area gradient** ✓; bench **#8a8580 / w1.5 / dashed** ✓; legend fontFamily **'Space Grotesk'** ✓.
- HERO8: x boundaryGap false, y scale, tooltip #1a1a1a ✓. **axisPointer `type:'line'`** = design-correct per Builder's HERO8 contract-typo fix → **PASS** (was my R1 nit).
- HERO9: curve real, rebased **100 → 118.52**, 53 pts, no mock ✓. HERO11: `__echartsRO` (mountEChart) ✓.
- Visual: glass card + 巨号 "累计收益 +18.5%" teal + KPI 7-grid (胜率 19/20, MDD -6.3%, SHARPE 3.01). PENDING: HERO1-6/10/12 computed.

### W6-BANR (Strategy Picks) — verified items PASS
- BANR3 (D3): teal dot `rgb(13,118,128)` #0d7680 / cmsiPulse 1.5s / honest "EOD 跟踪 · DAILY" / **no fake-realtime** ✓.
- BANR5: dynamic counter chip "3 STRATEGIES" ✓.
- BANR7: big returns mono JetBrains Mono 32px/700, sign-colored; **D2 down = `rgb(200,16,46)` #c8102e** ✓.
- PENDING: BANR1/2/4/6/8/9/10/11/12.

### W1-IPO (Strategy Picks, IPO tab) — structure/data/interaction PASS; computed spot PENDING
- IPO2 (D3): **BACKTEST** wording, no fake-realtime ✓.
- IPO4 (data integrity, CONFIRMED vs `data/external/ipo_picks.csv`): 样本 **n=54**, **已上市 38 · 待上市 16**, best **+384.0%** (曦智科技) / worst **-56.9%** (华健未来-B) = exact CSV idxmax/idxmin, not hardcoded ✓.
- IPO9: **54 rows** score-descending + **上市日期 column present** ✓.
- IPO10 hover-dock CONFIRMED: default dock = "魔门塔" (rank 1); mouseenter row 5 → dock → "圣邦微" (`changed:true`) ✓.
- IPO12 (CRITICAL): empty-state "盘中路径未采集 · 仅首日收盘" present; **no Math.random/genData**; single real dock path ✓.
- IPO15: import FIXED + AppTest OK ✓.
- PENDING (browser-blocked, not failures): IPO1/3/5/6/7/8/11/13 — masthead 5×48, KPI tri-color glass顶边, tier-table geometry, tier chip 5-color, dock glass rgba.6/blur16, footer box.

---

## §D · Round 1 FAIL / issue ledger
| # | id | sev | status |
|---|---|---|---|
| 1 | IPO15 / GRD4 | HIGH | **FIXED @618319a** (`from app.lib`→`from lib`), AppTest all-4 OK — verified |
| 2 | HERO8 | — | **RESOLVED** by contract-typo correction (line pointer is design-correct) → PASS |
| 3 | SOVR7 th border-left 1px | NIT | verify no visible vertical divider (screenshot clean) — low priority |

**No outstanding hard FAILs.** No demo-literal / fake-series / CDN / MOCK / box-shadow / emoji violations (GRD1/GRD2 clean).

## §E · Coverage & blocker (honest)
Verified with hard evidence (JS computed-style / EO getOption / CSV cross-check / AppTest): ~40 of 86 items across all 7 features — every block's structural spine, data-integrity, and key interactions PASS. The remaining ~46 are **computed-style spot values** (exact glass rgba/blur/顶边 hex, masthead bar dims, tier/KPI geometry) that were mid-probe when the **claude-in-chrome extension disconnected (OAuth account mismatch — persistent, not transient)**. These are **PENDING, not FAIL**.

## §F · feature_list disposition (Round 1)
Per §5 "无证据的 PASS 无效", `passes` stays **false** for all W1-W7 this round (none has 100% item evidence yet) — but there are **zero hard FAILs** remaining after the IPO15 fix. Round 2 (browser restored) completes the computed-style spot items; expectation is a broad flip-to-true barring surprises. cycles_used=1.
