Second-round UX/docs audit of invest-dashboard D4 + D5 work.

**Repo (public)**: https://github.com/chenhongdao2-blip/invest-dashboard

**Recent commits**:
- `251c6de` (round-1 audit fixes)
- `2863c72` (**D4 Strategy Picks**)
- `9e1179e` (**D5 CMSI Coverage + Valuation Scanner**)

**Current page list** (Streamlit sidebar order):
1. 🏠 streamlit_app.py (Home)
2. 🏥 Healthcare overview
3. 🔥 Sector Heatmap
4. 💎 CMSI Coverage (NEW)
5. 🧬 Strategy Picks (NEW)
6. 💰 Valuation Scanner (NEW)
(D6 Ticker Drill pending, D7 deploy pending)

**D4 Strategy Picks UX**:
- 3 tabs: 🧬 v4 biotech / 🧬 v5 biotech / 💰 HK 高股息
- Per strategy: 4 header metrics → 3 perf metrics with Alpha pp → Plotly cumulative chart (individual lines + bold portfolio + dashed benchmark) → Top/Bottom 5 ranking tables → expandable full picks
- Verified output (v4 biotech): Portfolio +1.04% / XBI -2.08% / Alpha +3.12pp outperform

**D5 CMSI Coverage UX**:
- 4 region tabs: HK (15) / US (10) / CN (3) / All (28)
- Per ticker: BBG style, name_cn, name_en, region, mcap_tier ("mid"/"small"/"micro"), cross-sector emoji (🧬💊🤖⚕️🏥🩺🧪), Mcap, YTD/1M/5D/1D %, Trail P/E, Fwd P/E, EV/EBITDA, FCF Yield, P/B
- Default sort: mcap desc (per M10 audit)
- HK tab top: 药明康德 $47.2B / 翰森 $24.9B / 信达 $17.1B / 药明生物 $17.1B / ...

**D5 Valuation Scanner UX**:
- Sidebar: sector multi-select / min mcap $5B / P/E percentile ≤25 / fwd vs trailing / YTD range / 5D ≥ -10%
- Output (default filters): 87 universe → 16 candidates
- Top candidates: PFE (9.2x, 6%, +4% YTD), ICLR (10.5x, 7%, -37% YTD, +14% 1M recovery), RPRX (9.6x, 15%, +38% YTD)
- "How to read" expandable with sell-side framework

**UX/docs audit angle**:

1. **D4 Strategy chart overload** — Cumulative return chart shows 27 individual ticker lines (translucent) + portfolio (thick green) + benchmark (purple dashed). For 27 tickers it's busy; for 40 (v5) it's worse. Better visualization choices?
   - (a) Keep as-is (showing dispersion has signal)
   - (b) Hide individual lines by default, click "show all" to expand
   - (c) Replace with portfolio + benchmark only + separate "Top 3 / Bottom 3" thin overlays
   - (d) Add range-spread band (10-90th percentile) instead of all 27 lines

2. **D4 Bottom 5 sort direction confusion** — Top 5 sorted by Since% desc, Bottom 5 sorted by Since% asc (so worst first). But "Bottom" implies opposite. Is this confusing? Should both tables share same desc sort and just slice differently?

3. **D5 Coverage cross-sector emoji** — Only one cover ticker (2506.HK = Xunfei Healthcare) shows the 🤖 cross-tag. Most HK CMSI cover tickers (信达/翰森/石药/中生制药 etc) have no cross-tag because they're not in sector universes. Is the emoji column useful when 90% empty?

4. **D5 Scanner filter UX** — 6 sliders/multi-selects in sidebar. Cognitive load on the user. Should we:
   - (a) Add preset filter buttons ("Deep value", "Quality cheap", "Recovery candidate")
   - (b) Add "Reset filters" button
   - (c) Inline filters into main page (sidebar real estate competes with search box)

5. **D5 Scanner output table columns** — 13 columns wide. On laptop screens needs horizontal scroll. Cull?

6. **Cross-page navigation** — sidebar "🔍 Find ticker" is reused across 4 pages now (Home, Strategy Picks, CMSI Coverage, Scanner). Should this be unified state (selecting ticker on page A persists to page B)? Currently each page has separate `key=` so state resets.

7. **Page order** — Streamlit auto-orders by filename prefix:
   - `1_🏥_Healthcare`
   - `2_🔥_Sector_Heatmap`
   - `3_💎_CMSI_Coverage`
   - `4_🧬_Strategy_Picks`
   - `5_💰_Valuation_Scanner`
   - (D6 Ticker_Drill will be `6_`)
   
   Round-1 Gemini suggested moving CMSI Coverage to position #2 for analyst workflow priority (his daily list). Is this still valid post-D5?

8. **Strategy Picks ↔ Scanner overlap** — Both are "find good picks" pages but with different mental models:
   - Strategy Picks: backward-looking (how did our picks do?)
   - Valuation Scanner: forward-looking (what looks cheap now?)
   
   Are page names + descriptions clear enough on this distinction?

9. **Mobile** — Now 6 pages + filters + multi-tabs. Streamlit mobile is rough. Worth investing or P2?

10. **"How to read this scan" expander on Scanner** — Useful for junior analyst? Should similar onboarding text exist on every page (Healthcare overview, Sector Heatmap, CMSI Coverage, Strategy Picks)?

Output: severity-tagged [BLOCKER] / [MAJOR] / [MINOR] / [NIT] actions.
