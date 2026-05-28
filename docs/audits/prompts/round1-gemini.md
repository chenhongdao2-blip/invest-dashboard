Review this multi-domain sell-side investment dashboard from a UX / docs / alternatives perspective.

**Repo (public)**: https://github.com/chenhongdao2-blip/invest-dashboard
**Three commits**: `7f71a91` (D1 bootstrap), `3157451` (D2 fetcher), `17f2f17` (D3 Streamlit pages)

**User profile**: George Chen — sell-side healthcare analyst at CMSI HK (招商证券国际). Bilingual CN+EN; daily workflow involves scanning multiple coverage lists + understanding cross-sectional valuation. Currently maintains a manual Bloomberg Excel comp table with 25E/26E/27E forward P/E. This dashboard is NOT a replacement — it's a complement for daily quick scan.

**Done in D1-D3**:
- 3 Streamlit pages live locally: Home (snapshot metrics + 8 benchmarks + top10 movers / top10 drags), Healthcare overview (7-sector summary + per-sector top-3 expanders), Sector Heatmap (dropdown picker + heatmap table with red-green diverging colors for returns + low-good gradient for P/E ratios).

**Pending (D4-D7)**: Strategy Picks (接 ic-foundry ledger), CMSI Coverage (28 ticker list view), Valuation Scanner (sector-internal P/E percentile + YTD filter), Ticker Drill (single-stock detail page), deploy to Streamlit Cloud.

**Known polish item**: some NaN cells display "None" instead of "—" due to Streamlit `st.dataframe(styler)` limitation (Styler.format with `na_rep="—"` not respected — `st.dataframe` strips Styler's format and uses raw values). Workaround paths considered: `st.table` (static HTML, loses interactivity), `st.column_config.NumberColumn(format="...")` (respects format but can't do B/M for market cap or "neg" for negative ratios).

**UX / docs / alternatives audit angle**:

1. **Streamlit rendering choice** — For the Sector Heatmap (the core view), which is best:
   - (a) Current `st.dataframe(styler)` — interactive sort but NaN shows "None"
   - (b) `st.table(styler)` — static HTML, formatting fully respected, but no sort/search
   - (c) `st.dataframe(df, column_config=...)` — format respected, NaN shows blank, but loses background gradient
   - (d) Hybrid: pre-format some columns to strings + Styler for color
   
   Which would you ship?

2. **Sector navigation pattern** — Current: dropdown to pick 1 of 7 sectors. Alternatives:
   - Tabs across the top (always visible, click to switch)
   - Side panel checkbox multi-select (compare 2+ sectors side-by-side)
   - Grid card layout (each sector = thumbnail card, click for detail)
   
   For a sell-side analyst's daily workflow (scan all 7 sectors quickly each morning), which is best?

3. **Dark theme not loading** — `.streamlit/config.toml` at repo root sets `base = "dark"` but page renders white. Why might Streamlit ignore this in a multipage app structure? (`streamlit_app.py` is in `app/` subdirectory, started via `streamlit run app/streamlit_app.py`. config.toml is at repo root.)

4. **README clarity** — Look at `README.md`. Does it explain enough to onboard a new contributor or just dev-friendly notes? What's missing?

5. **Daily workflow order** — Plan has 6 P0 views in this sidebar order:
   - 🏠 Home (today's mover + benchmarks)
   - 🏥 Healthcare (7-sector summary)
   - 🔥 Sector Heatmap (deep dive 1 sector)
   - 💎 CMSI Coverage
   - 🧬 Strategy Picks (v4/v5 biotech, HK 高股息)
   - 💰 Valuation Scanner
   - 🔍 Ticker Drill
   
   For a sell-side analyst's morning routine, is this order optimal? Should CMSI Coverage come first (most personal-relevant) or last (most "company-specific")?

6. **Global search** — There's no ticker search box. If user wants to jump to "GILD" detail page, they have to find it in a Heatmap. Should we add a global search bar in sidebar?

7. **Naming** — "invest-dashboard" is generic. The plan says future will add AI domain etc. What would you rename to?

8. **Mobile** — Streamlit's default layout doesn't optimize for mobile. User mentioned wanting to check on phone. Worth investing in mobile-first now or P2 polish?

9. **Onboarding for non-technical sell-side colleague** — Imagine a Junior who's never used Streamlit. Can they open the public URL and understand what to do without docs? What's confusing?

Output: severity-tagged [BLOCKER] / [MAJOR] / [MINOR] / [NIT] action items. Be specific and concrete.
