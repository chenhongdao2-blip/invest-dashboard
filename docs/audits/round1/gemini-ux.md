# gemini advisor artifact

- Provider: gemini
- Exit code: 0
- Created at: 2026-05-28T03:37:14.615Z

## Original task

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

## Final prompt

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

## Raw output

```text
I will begin by researching the current implementation of the Sector Heatmap, the Streamlit configuration, and the project documentation to provide a well-grounded audit.
I will examine the multi-page app configuration and the heatmap implementation to understand why the dark theme might be failing and to evaluate the current rendering strategy.
I will examine the formatting logic in `lib/format.py` to understand how NaNs and background gradients are handled, which will help me address the rendering and polish issues.
I will check the data volume in `config/universes` to better understand the dashboard's scale and inform my recommendations on navigation and search.
This audit evaluates the **invest-dashboard** prototype from the perspective of George Chen, a sell-side analyst at CMSI HK. The goal is to move from a "dev-ready" prototype to a "production-grade" tool that complements a high-pressure Bloomberg/Excel workflow.

### 1. Rendering Strategy: The "None" vs "—" Polish
**Recommendation: Ship Option (d) - Pre-formatted Strings + Style Masking**
[MAJOR] The "None" display in heatmaps undermines the professional feel required for sell-side tools.
*   **Why Option (c) `column_config` fails**: You lose the background gradients, which are the primary "value-add" for George’s morning scan (identifying outliers visually).
*   **The Fix**: In `Sector Heatmap`, format the numeric columns into strings (with "—" and "neg" handling) into a separate `display_df`. Use the original numeric `merged_df` only for calculating the color gradients in `Styler.apply`. 
*   **Verdict**: This preserves the "Excel-like" interactivity (sorting) while ensuring bulletproof formatting.

### 2. Sector Navigation: The "Click Fatigue" Problem
**Recommendation: Replace Dropdown with `st.tabs`**
[MAJOR] A dropdown is a "High Interaction Cost" (HIC) pattern. To scan 7 sectors, George must click 14 times and read a menu 7 times.
*   **Alternative**: Use `st.tabs(["Biotech", "Pharma", "Medtech", ...])`. 
*   **Workflow Impact**: George can "piano-key" through the sectors in seconds. Since the data is cached via `@st.cache_data`, the switch will be near-instant.
*   **Edge Case**: If the list grows to 10+ domains, revert to dropdown, but for 7 healthcare sectors, tabs are superior.

### 3. Dark Theme & Sidebar Identity
**Recommendation: Force Theme & Sidebar Branding**
[MINOR] The `config.toml` is likely ignored because Streamlit is being run from the root but looking for configuration local to the entry point or execution environment.
*   **Fix 1**: Move `.streamlit/` into the `app/` directory or ensure `uv run` is executed from root.
*   **Fix 2 (Branding)**: Rename from "invest-dashboard" to **"CMSI Pulse | Healthcare"**. 
*   **Fix 3 (Sidebar)**: Add the CMSI logo (or a stylized 🏥) to the top of the sidebar. This makes it feel like an internal firm tool rather than a generic dashboard.

### 4. Workflow Order: "The Coverage First" Rule
**Recommendation: Re-order Navigation**
[MINOR] George's daily hierarchy of needs is: *Market Context -> My Names -> Sector Context -> Ideas.*
*   **Optimal Sidebar Order**:
    1.  🏠 **Home** (Market & Movers)
    2.  💎 **CMSI Coverage** (His 28-ticker list - *Most important*)
    3.  🔥 **Sector Heatmap** (The deep dive)
    4.  🏥 **Healthcare Overview** (The summary - *Moved down as it's less actionable*)
    5.  🧬 **Strategy Picks**
    6.  💰 **Valuation Scanner**
    7.  🔍 **Ticker Drill**

### 5. Search & Discovery: The "Phone Call" Scenario
**Recommendation: Add Global Sidebar Search**
[BLOCKER] If a client calls about "AstraZeneca (0593.HK / AZN)", George cannot quickly find it.
*   **Action**: Add a `st.sidebar.selectbox` (using `db.all_tickers()`) that appears on every page. Selecting a ticker should redirect to the **Ticker Drill** page. 

### 6. README & Docs: The "Junior Analyst" Test
**Recommendation: Add an "Analyst Glossary" Section**
[NIT] A non-technical colleague won't know why a P/E is "neg" or why data is "yfinance" vs "Bloomberg".
*   **Missing**: A simple table in the README/About page:
    *   `neg`: Negative earnings (P/E not meaningful).
    *   `—`: Data missing from yfinance (usually OTC or new listing).
    *   `Wgt Avg`: Market-cap weighted (prevents small-cap "noise" from skewing sector metrics).

### Action Item Summary

| Severity | Item | Action |
| :--- | :--- | :--- |
| 🔴 **BLOCKER** | **Global Search** | Add sidebar ticker picker for instant jump to "Ticker Drill". |
| 🟠 **MAJOR** | **Heatmap Render** | Pre-format to strings + use `Styler` for colors only to fix "None" values. |
| 🟠 **MAJOR** | **Navigation** | Switch Sector Heatmap from Dropdown to Tabs. |
| 🟡 **MINOR** | **Dark Theme** | Move `.streamlit` to `app/` or verify CWD on launch. |
| 🟡 **MINOR** | **Sidebar Order** | Move "CMSI Coverage" to position #2. |
| ⚪ **NIT** | **Naming** | Rename to "CMSI Pulse" or "AlphaStream". |

**Final UX Verdict**: The core logic (gradients for valuation vs. returns) is excellent and follows sell-side intuition (lower P/E = green = good). Solving the navigation and search hurdles will make this a "daily driver" for George.


YOLO mode is enabled. All tool calls will be automatically approved.
YOLO mode is enabled. All tool calls will be automatically approved.

```

## Concise summary

Provider completed successfully. Review the raw output for details.

## Action items

- Review the response and extract decisions you want to apply.
- Capture follow-up implementation tasks if needed.
