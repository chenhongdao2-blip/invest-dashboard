# Reskin Wave-2 — Current-State Map

Branch: `feat/kline-reskin`. Generated 2026-07-03. Read-only survey of the 6 components
scheduled for wave-2 reskin. All paths absolute; line numbers as of this commit.

> NOTE ON PATHS: the task brief refers to `lib/…`, but the real tree is `app/lib/…`
> (there is NO repo-root `lib/`). Streamlit runs with `app/` on `sys.path`, so imports
> read `from lib import …`. Everything below is under `/Users/gcc/invest-dashboard/app/`.

---

## 0. Shared substrate (theme tokens + kline-reskin reuse candidates)

`app/lib/theme.py` — every wave-2 module imports `from lib import theme` and pulls flat
module-level color/font constants (NOT CSS vars):

| token | value | line |
|---|---|---|
| `CMSI_RED` / `CMSI_RED_DEEP` / `CMSI_RED_TINT` / `CMSI_RED_BAND` | `#c8102e` / `#9c0e25` / `#fbe9ec` / `#f2dfce` | 35-38 |
| `PAPER` / `PAPER_DEEP` / `PAPER_BAND` / `PAPER_RULE` / `PAPER_EDGE` / `PAPER_EDGE_SOFT` | `#fff1e5` / `#f9e6d4` / `#f2dfce` / `#ebd9c8` / `#d4c4b0` / `#e4d2bd` | 41-46 |
| `INK` / `INK_2` / `INK_3` / `INK_4` | `#1a1a1a` / `#4a4a4a` / `#8a8580` / `#b8b1a8` | 49-52 |
| `UP` / `UP_DEEP` / `UP_TINT` | `#0d7680` (FT teal) / `#0a5a62` / `#d9e8e6` | 55-57 |
| `DOWN` / `DOWN_DEEP` / `DOWN_TINT` | `#cc0000` / `#a30000` / `#f7d9d9` | 58-60 |
| `FONT_STACK` (Inter + CJK) | 78-81 |
| `FONT_MONO` (JetBrains Mono …) | 82 |
| `FONT_FACE_CSS` (self-hosted @font-face block) | 160 |

INVARIANT color semantics (港美股 / HK-US): **teal = up, red = down** (opposite A-share).
Every module hardcodes this; several docstrings warn against flipping it.

**kline-reskin assets wave-2 may reuse** (both introduced on this branch, currently used
ONLY by `app/pages/6_Ticker_Drill.py`):

- `theme.GLASS_CARD_CSS` — f-string, `theme.py:1008-1019`. Frosted-glass panel
  (`rgba(255,255,255,.55)` + `backdrop-filter: blur(14px)`, `border-top: 3px solid INK`).
  Injected at `6_Ticker_Drill.py:201` via `st.markdown(f"<style>{theme.GLASS_CARD_CSS}</style>", …)`.
  Targets `.cmsi-memo-bar, .cmsi-stat-strip, .cmsi-ch, .cmsi-note, [data-testid="stExpander"] details`.
- `theme.page_radial_wash(max_width_px=1240)` — function, `theme.py:1022-1042`. Injects a
  page-scoped `<style>` layering two radial washes (red top-left `rgba(200,16,46,.09)` /
  teal top-right `rgba(13,118,128,.10)`) over `PAPER`, `background-attachment: fixed`, and a
  1240px `.block-container` cap. Called at `6_Ticker_Drill.py:200`. Page-scoped by
  construction (only the calling page gets it).

Common editorial helpers wave-2 modules already lean on: `theme.section_header()` (1069),
`theme.kpi_strip()` (1191), `theme.kpi_metric()` (1122), `theme.md_note()` (1318),
`theme.subsection()` (1348), `theme.page_header()` (1047).

**i18n pattern (uniform across all 6):** `app/lib/i18n.py`. `i18n.t(key, **kwargs)` does a
flat-dict lookup on `MAPS[lang]` where `MAPS = {"zh": {**zh.STRINGS, **pages_zh.STRINGS},
"en": {**en.STRINGS, **pages_en.STRINGS}}` (i18n.py:30-31; strings live in
`app/lib/locales/{zh,en,pages_zh,pages_en}.py`). `i18n.get_lang()` returns `"zh"|"en"`;
convention `prefer_cn = i18n.get_lang() == "zh"`. Helpers: `i18n.ipo_tier()` (203),
`i18n.bench_name()` (211), `i18n.common_cols()` (65). Two i18n styles in play:
(a) modules that take `prefer_cn` as a param and branch internally
(`market_hub_tiles`, `heatmap_treemap`); (b) modules that hardcode Chinese literals and
receive only pre-localized strings from the caller (`sector_overview`, `strategy_banner`).

**RENDERING-MECHANISM MAP (the reskin decision axis):**

| module | mechanism | charts |
|---|---|---|
| market_hub_tiles | `st.iframe(srcdoc)` | inline SVG sparkline + count-up JS (NO echarts) |
| heatmap_treemap | `st.iframe(srcdoc)` | echarts treemap via `mountEChart('m',…)` |
| strategy_hero | `st.iframe(srcdoc)` | echarts line via `mountEChart('eq'|'cmp',…)` + count-up |
| sector_overview | `st.markdown(unsafe_allow_html)` | inline SVG sparkline (NO iframe/JS) |
| strategy_banner | `st.markdown(unsafe_allow_html)` | inline SVG sparkline pairs (NO iframe/JS) |
| IPO tab | `theme.kpi_strip` + `ui.render_html_table` + `st.plotly_chart` | Plotly small-multiples |

`echarts_boot.MOUNT_JS` (`app/lib/echarts_boot.py:32-60`) is the shared bootstrap injected
into every echarts iframe: rAF-polls until `echarts` loaded AND `clientWidth/Height>0`
before `init`, reuses `getInstanceByDom`, attaches a `ResizeObserver`. Fixes the
"0-width race → permanent blank canvas" bug. Contract: `docs/harness/echarts-race/CONTRACT.md`.

---

## 1. IPO tab — `app/pages/4_Strategy_Picks.py` + `app/lib/strategy.py`

### Public signatures
- `_overview_ipo_card() -> dict | None` — `4_Strategy_Picks.py:112-125`. Builds the IPO
  card dict for the opening overview strip. Returns `{kind:"ipo", name, tag:"六因子 v6.7",
  n, listed, median, hi, lo}`. **Guard:** returns `None` if `load_ipo()` empty OR
  `day1_ret.max() <= 0` (bar widths divide by `hi`). Called at L129-131 alongside two
  `_overview_curve_card()` results, filtered `if c`, fed to `sb.overview_strip()` (L137).
- `render_ipo_strategy() -> None` — `4_Strategy_Picks.py:571-707`. The whole IPO tab body.
  Invoked at L818-819 inside the last `st.tabs` slot.
- `_render_ipo_table(picks: pd.DataFrame) -> None` — `4_Strategy_Picks.py:710-788`. Dual
  leaderboard (sort by score / by day-1 return, `st.segmented_control` key `ipo_rank_sort`).
  Called twice: L600 (early-bail path when no listed rows) and L703 (normal path).

### Data plumbing (`app/lib/strategy.py`)
- `load_ipo() -> pd.DataFrame` — strategy.py:112-123. `@st.cache_data(ttl=900)`. Reads
  `data/external/ipo_picks.csv` with `dtype={"code": str}` (leading-zero HK codes, e.g.
  `0901`, must not coerce to int). Never routed through yfinance/`compute_strategy_returns`.
  `day1_ret` is a **DECIMAL** (3.84 = +384%); `×100` happens once at render (L587
  `picks["ret_pct"] = picks["day1_ret"] * 100`).
  CSV columns: `code, name_cn, name_en, score, tier, list_date, day1_ret, sub_sector,
  offer_price, day1_close, status, source`.
  ⚠ **STALE DOCSTRING / FRAGILE:** docstring says "STATIC cross-section snapshot (18 rows)"
  but the live CSV has **54 data rows → 38 `listed` + 16 `pending`**. Any reskin copy that
  quotes "18" is wrong.
- `load_ipo_intraday() -> pd.DataFrame` — strategy.py:126-139. `@st.cache_data(ttl=900)`.
  Reads `data/external/ipo_day1_intraday.csv` (`dtype={"code": str}`, `time` parsed to
  datetime). Columns: `code, time, close`. Missing file → empty DF (graceful degrade).
  **Coverage:** the CSV holds **20 distinct codes** (`1081, 1187, 1236, 1511, 1609, 1779,
  1879, 2493, 2553, 2723, 3296, 3310, 3388, 6810, 6871, 6872, 7630, 7666, 7688, 901`).
  ⚠ docstring says "17 listed names" — also stale vs the 20 present. Intraday is only drawn
  for `listed` picks whose `code` has a path (inner-join at render).

### render_ipo_strategy internals (L571-707)
1. L578-581 load + empty guard. L583 intro markdown. L586-589 `ret_pct` decimal→pct, split
   `listed` / `pending` by `status`.
2. L592-593 methodology `st.expander`.
3. **L598-602 INVARIANT guard:** `if listed.empty:` → render `md_note` caveat +
   `_render_ipo_table(picks)` + source caption, then `return`. Protects the KPI/scatter/
   intraday blocks (which assume ≥1 listed via `idxmax`/`median`).
4. L604-629 KPI strip via `theme.kpi_strip([...])` — 3 hand-built `.cmsi-kpi` HTML cards
   (`_ipo_kpi()` local, L612): 样本规模 / 最高 (`top_row=idxmax`, class `up-deep`) /
   最差 (`worst_row=idxmin`).
5. L631-658 by-tier staircase table. Iterates a **fixed tier order**
   `["重点申购+","重点申购","推荐申购","谨慎申购","不申购"]` (L641), computes
   n/median/win/broke per tier, renders `ui.render_html_table(..., height=260)`.
6. **L660-700 intraday small-multiples** (the block the brief flags ~L690-700):
   `intra = strat.load_ipo_intraday()`; order `listed` by `score` desc; per row inner-join
   on `code`, drop NaN, compute `pct = (closes*(1+d1)/last - 1)*100` so **the path
   terminates EXACTLY at the labelled day-1 return** (`offer = last/(1+d1)`; INVARIANT that
   fixes an old open-bar=100 title/line mismatch). `up = d1 >= 0` colors by FULL day-1 sign
   (not intraday sign). Builds `paths=[{title, y, up, hover}]` then
   `charts.ipo_intraday_facets(paths, ncols=4, title=…, use_hover=True)` →
   `st.plotly_chart(fig, width="stretch", theme=None)`. This is the ONE **Plotly** surface
   in the tab (`app/lib/charts.py:553 ipo_intraday_facets`, `go.Figure`+`make_subplots`,
   shared y-range, no legend/gridlines).
7. L703 `_render_ipo_table(picks)`. L706-707 caveat `md_note` + source caption.

### _render_ipo_table (L710-788)
- Builds `disp` DataFrame with columns keyed by i18n: `col.code, col.name, **col.list_date
  ("上市日期" / "List Date")**, col.score, col.tier, col.sub_sector, col.day1_ret, col.source`.
  The **上市日期 column** (`tbl["list_date"]`, added 2026-07-03) is a first-class column at
  L756; locale keys `strategy.ipo.col.list_date` exist in `zh.py:272` / `en.py:292`.
  Pending name cells get `· 待上市` appended (L769-774) now that the date lives in its own
  column (comment L771).
- Rank: only `listed` names ranked (L737-746); pending shows `—`.
- Render: `ui.render_html_table(disp, pct_cols=[day1], text_cols=[name,tier,sub_sector,
  source], extra_formats={score:"%.2f"}, right_text_cols=[code,list_date],
  index_label=…, height=720)`.

### Overview strip IPO card (`sb._ipo_card`, strategy_banner.py:174-204)
Rendered as one of three cards in `sb.overview_strip`; SVG-free bar rows (最高/中位/最差)
+ big median 首日 number + `已上市 N / 待上市 M` footer. Colors: `t.UP` for hi/median,
`t.DOWN` for lo.

### Height budgets (IPO tab)
tier table `height=260` (L656) · leaderboard `height=720` (L787) · intraday Plotly
(auto, `width="stretch"`) · KPI strip via `theme.kpi_strip` (no explicit px).

### Spillover
IPO tab is **single-page** (only `4_Strategy_Picks.py`, last tab, L818-819). No spillover.

---

## 2. `app/lib/market_hub_tiles.py` (SVG index tiles)

### Public signature
`render_index_tiles(tiles: list[dict], *, as_of: str | None, prefer_cn: bool,
height: int = 372) -> tuple[str, int]` — market_hub_tiles.py:165. Returns `(doc, height)`;
caller does `st.iframe(doc, height=h)`.

### Payload (per tile dict)
`name(str)` · `value(pre-formatted str)` · `value_raw(float|None → enables count-up)` ·
`chg_pct(float|None, day %)` · `lo`/`hi(pre-formatted 52w str|None)` · `pos(0-1 位置|None)`
· `m1`/`ytd(float|None %)` · `spark(list[float], ~30 closes; <2 pts → no line)`.

### Call site (ONLY one)
`app/home.py:285-287` — Market Overview / 市场总览 block (`home.py:232-287`). Builds
`_tiles` from `bench_df` (`benchmarks.fetch_benchmarks()`) rows for `_panels["broad_market"]`
present in the index; `_range52()` (home.py:241) computes real trailing-52w lo/hi/pos from
`bm.close_series()` (guards <330d window so it never mislabels as "52W"); `_spark()`
(home.py:260) takes last 30 closes. `import market_hub_tiles` at home.py:22.

### Rendering mechanism
`st.iframe` self-contained srcdoc. Sparkline = **inline SVG** area+polyline (`_spark_svg`
L64), colored by `chg` sign. 52w micro-bar = `_range_bar` (L93). Market-read dek =
`_market_read` (L130, real N-up/M-down + leader/laggard, non-fabricated). Entry animations
only (NOT realtime): sparkline draw-in via `polyline pathLength="1"` + CSS
`stroke-dashoffset 1→0`; tiles staggered fade-rise (`animation-delay: idx*90ms`); big value
`count-up` via a minimal `<script>` reading `data-countup` (L235-246). `prefers-reduced-
motion` honored (L229-231). Uses tokens `PAPER, INK, INK_2/3/4, UP, DOWN, CMSI_RED,
PAPER_RULE, PAPER_EDGE, FONT_STACK, FONT_MONO`.

### Height budget
Default 372, returned unchanged; grid is `repeat(n,1fr)`. Big value `.tval` 35px/39px.

### Fragile / INVARIANTs
- **Sparklines MUST stay inline SVG, NOT echarts** (docstring L21-24): multiple small
  echarts in initially-0-width grid columns race to blank. This is a hard design guard —
  a reskin that swaps SVG→echarts here reintroduces the blank-chart bug.
- No TRACKING/live badge — data is EOD/cron; entry animation ≠ realtime (George ruling).
- Single call site → no spillover.

---

## 3. `app/lib/heatmap_treemap.py` (echarts treemap `#m`)

### Public signature
`render_treemap_html(payload: dict, *, window_label: str, as_of: str | None,
prefer_cn: bool, height: int = 720) -> tuple[str, int]` — heatmap_treemap.py:81.

### Payload source
`heatmap.build_domain_bento(domain_id, window_col, prefer_cn)` — `app/lib/heatmap.py:103`.
Returns `{id, cn, en, median, n_total, sectors:[{id, cn, en, median, pct_up, n_valid,
n_members, n_shown, rank, tiles:[{tk, ret, mcap, name}]}]}` sorted hottest-first (by member
median return). `_payload_to_treemap()` (heatmap_treemap.py:59) flattens sectors→parents,
tiles→leaves with `value:[mcap, ret]`, `itemStyle.color=_ramp(ret)`, `label.color=_txt(ret)`.
`WIN_TO_COL = {"1D":"1d_%","5D":"5d_%","1M":"1m_%"}` (heatmap.py:50).

### Call site (ONLY one for the treemap)
`app/home.py:178-180` inside `_render_stock_heatmap()` (home.py:142-191, invoked L292).
Segmented controls pick window (1D/5D/1M) + domain (All/Healthcare/AI); loops domains,
`hm.build_domain_bento(did, window_col, prefer_cn)`, and for each renders
`heatmap_treemap.render_treemap_html(_d, window_label=win, as_of=latest, prefer_cn=…,
height=_h)` then `st.iframe(_doc, height=_hh)`. `import heatmap_treemap` at home.py:21.
`_h = 600 if len(domains) > 1 else 720` (home.py:176).
NOTE: `build_domain_bento` is ALSO consumed by the OLD bento renderer
`heatmap.render_bento_html` at `app/pages/e2_etf_heatmap.py:52` — so the **payload** is
shared, but the **treemap renderer is home-only**.

### Rendering mechanism
`st.iframe` srcdoc. ECharts treemap via `mountEChart('m', …)` (echarts_boot). Self-hosts
`_ECHARTS_SRC = "app/static/echarts.min.js"` (**relative, NO leading `/`** — heatmap_treemap.py:34).
`<script>` tag literal is split (`chr(60)+"scr"+"ipt"`, L97-99) to dodge a build-time
validator. `_ramp(r)` (L39) = FT diverging teal↔red, 7-stop, `CAP=12.0`% saturation;
`_txt(r)` (L55) = cream text when `|ret|≥5` else ink. Header band + convention note
(teal=up/red=down/area=mcap). Tokens: `INK, PAPER, PAPER_DEEP, INK_2/3, CMSI_RED`.

### Height budget
Default 720; `#m` CSS height = `height - 90` px (heatmap_treemap.py:135). Home overrides to
600 when >1 domain stacked.

### Fragile / INVARIANTs
- **`_ECHARTS_SRC` must stay relative** (docstring L31-33): cloud Streamlit serves under a
  `/~/+/` prefix; an absolute `/app/static/...` loses the prefix → login redirect → echarts
  undefined → blank map. Do not "normalize" to leading-slash.
- **srcdoc MUST set `html,body{height:100%}` + `#m` explicit px height** or canvas collapses
  to 0 (docstring L22; CSS L133-135).
- Missing `mcap` → block median fallback so a tile never has 0 area (L69).
- Color semantics teal-up/red-down are an INVARIANT (HK/US convention, note baked into UI).

---

## 4. `app/lib/sector_overview.py` (benchmark_table / movers)

### Public signatures
- `benchmark_table(rows: list[dict], *, source: str | None = None) -> None` — L102.
  Row dict: `{tk, name, periods:{label:pct,...}, rel_sp(float pp), spark:[~30 raw closes]}`.
  Period column order = first row's `periods` dict key order (callers pass identical keys).
- `movers(*, gainers: list[dict], losers: list[dict], window: str = "1 日") -> None` — L165.
  Item dict: `{tk, name, last, d1}`.

### Call sites (TWO pages → spillover)
- `app/pages/2_Healthcare.py:152` (`so.benchmark_table`, rows built L123-152 from
  `bm.fetch_benchmarks()` focus `["XLV","XBI","XPH","IXJ","IHF","IHI"]`) and
  `2_Healthcare.py:521` (`so.movers`, gainers/losers from combined per-sector returns,
  L504-522). `import sector_overview as so` at 2_Healthcare.py:18.
- `app/pages/a2_ai_overview.py:136` (`so.benchmark_table`, focus `["^SOX","SMH","AIQ",
  "512480.SS","515880.SS","442580.KS"]`, L106-136) and `a2_ai_overview.py:157`
  (`so.movers`, L140-158). `import … as so` at a2_ai_overview.py:21.
- Both pages compute `rel_sp` = ticker YTD − `^GSPC` YTD; `spark` = last 30 closes from
  `bm.close_series()`; `source` string pre-localized by the caller.

### Rendering mechanism
**Pure `st.markdown(unsafe_allow_html=True)` — NO iframe, NO JS.** A real
`<table>` (sortable DOM stays intact) for `benchmark_table`; flex rows for `movers`.
Sparkline = inline SVG (`_spark_svg` L62, `<span>—</span>` when <2 pts). Diverging period
heat via `_tint()` (L43, `REL_CAP=25.0` pp, ≤0.16 alpha, teal/red). Relative-to-SPX =
center-diverging `_rel_bar` (L86, 0-centered). Movers = per-row momentum bar `_mover_row`
(L143). HTML escaped via `html.escape as _esc`. Chinese literals hardcoded
("涨跌榜", "涨幅前 10", "相对标普 PP", "趋势 30D") — only `window` and `source`/`name`
are caller-localized. Tokens: `INK, INK_2/3, UP, DOWN, CMSI_RED, PAPER_RULE, PAPER_EDGE,
PAPER_BAND, FONT_MONO`.

### Height budget
None — flows in the normal Streamlit column (no fixed-height container).

### Fragile / spillover
- **SPILLOVER RISK: renders on TWO pages** (Healthcare + AI overview) — the only wave-2
  module used by >1 page. A reskin here changes both pages at once; verify both.
- Hardcoded Chinese labels mean the module is not fully bilingual (movers header etc. stay
  CN regardless of lang).

---

## 5. `app/lib/strategy_hero.py` (`#eq` / `#cmp` echarts + KPI count-up)

### Public signatures
- `render(*, strat_name, strat_dates, strat_curve, bench_name, bench_curve, cum_ret,
  bench_ret, alpha_pp, pick_date, n_hold, pool, days, wins, n_total, mdd, sharpe,
  bench_code, bench_sub, as_of, source) -> None` — strategy_hero.py:53. Tearsheet hero:
  left 58px count-up cumulative return + bench/alpha, right `#eq` equity curve, bottom
  7-tile KPI row (`_kpi_tile` L40). Ends with `st.iframe(doc, height=470)` (L183).
- `render_compare_chart(*, dates, lines, marker_date, marker_label, title, source,
  height=460) -> None` — strategy_hero.py:186. Multi-line overlay `#cmp`
  (v1/v2 + benchmarks). `lines=[{name, values(None=gap), color, dash∈solid/dashed/dotted,
  width}]`. Optional dotted vertical `markLine` at `marker_date`. `st.iframe(doc,
  height=height)` (L273).

### Call sites (ONLY `4_Strategy_Picks.py`)
- `render(...)` at `4_Strategy_Picks.py:232-245`, inside `render_strategy()`. **Gated**
  (L224-229): `not portfolio.empty and not bench_norm.empty and not normed.empty and
  len(portfolio) >= 10` AND a non-degenerate sharpe (`_rets.std() > 0`) AND non-NaN bench
  tail — so it never shows a fabricated 0.0 sharpe / 0 win (audit MEDIUM B1/B2). Curves come
  from `strat.compute_strategy_returns` (portfolio rebased=100) + `_bench_norm`.
- `render_compare_chart(...)` at `4_Strategy_Picks.py:485-490`, inside the HD v1-vs-v2
  compare block (`render_hd_versions`), lines built L461-479 (bench dashed INK_3, bench2
  dotted `#4a6fa5`, v1 solid `theme.UP`, v2 solid `theme.CMSI_RED`), marker = v2 first
  trading day. `import strategy_hero` at 4_Strategy_Picks.py:27.

### Rendering mechanism
`st.iframe` srcdoc. ECharts line via `mountEChart('eq'|'cmp', …)`. Self-hosts
`ECHARTS_SRC = "app/static/echarts.min.js"` (**relative** — same cloud-prefix INVARIANT as
§3, docstring L32-37). Count-up: `[data-count]` nodes animated 1500ms easeOutCubic; MDD tile
force-prefixes `-`, sharpe 2dp (L136-150). **Fonts passed through `json.dumps`, NOT inlined**
(FONT_STACK contains single quotes that would break the JS string literal — comment L72-75).
Sign-coloring INVARIANT (L61-64): `_cum_col`/`_alpha_col` = `UP if ≥0 else DOWN` (a loss must
read red; the reference had hardcoded UP). Strategy line = `CMSI_RED` w/ gradient area;
bench = `INK_3` dashed; both have value `endLabel`. CSS via `_CSS.format(...)` (L279).

### Height budgets
`render`: outer `st.iframe height=470` (hardcoded), `#eq` CSS height **290px fixed**
(L306), KPI row `repeat(7,1fr)`. `render_compare_chart`: `height=460` default, `#cmp` =
`height-96` px (L217/221).

### Fragile / spillover
- Same relative-echarts-path + `html,body{height:100%}` + `#id` px-height INVARIANTs as §3.
- Responsive breakpoint `@media (max-width:860px)` collapses hero-grid to 1col + KPI to
  3col (L316) — reskin must preserve or the 7-tile row overflows.
- Single-page (4_Strategy_Picks only) → no spillover. (`deal_sankey.py:8` only *mentions*
  strategy_hero in a docstring; not an import.)

---

## 6. `app/lib/strategy_banner.py` (live_title / overview_strip / dual_track)

### Public signatures
- `live_title(title: str, *, as_of: str | None = None, lang: str | None = "中") -> None`
  — L45. H1 + red bar + right-side 中/EN segmented `<a href="?lang=zh|en" target="_self">`
  toggle (reads `st.query_params` in caller) + `更新 … HKT` stamp. `lang='中'|'EN'`
  highlights current; `None` hides toggle.
- `overview_strip(items: list[dict]) -> None` — L207. Three-strategy preview grid. Curve
  card item: `{name, bench_code, pick_date, n_picks, cum_ret, bench_ret, alpha, wins, total,
  hold_days, curve:(strat_vals, bench_vals)}` (rebased=100). IPO card item:
  `{kind:"ipo", name, tag, n, listed, median, hi, lo}`.
- `dual_track(cards: list[tuple], *, footer: str | None = None) -> None` — L221.
  `cards=[(num, title, body_html), ...]`.

### Call sites (ONLY `4_Strategy_Picks.py`)
- `sb.live_title(...)` at `4_Strategy_Picks.py:132-134` (title = `i18n.t("strategy.page.title")`,
  `as_of` = first card's `_as_of`, `lang` from `i18n.get_lang()`).
- `sb.overview_strip(_ov_cards)` at `4_Strategy_Picks.py:137`; `_ov_cards` built L129-131
  from `_overview_curve_card("v5_biotech")`, `_overview_curve_card("hk_hd")`,
  `_overview_ipo_card()` (filtered `if c`).
- `sb.dual_track([...], footer=…)` at `4_Strategy_Picks.py:792-803` (two hardcoded cards
  "01 催化剂驱动" / "02 新股打新多维评分").
- `import strategy_banner as sb` at 4_Strategy_Picks.py:28.

### Rendering mechanism
**Pure `st.markdown(unsafe_allow_html=True)` — NO iframe/JS.** Curve card `_curve_card`
(L141): dual SVG sparkline `_spark_pair` (L84, strat red solid + gradient area + bench grey
dashed + red endpoint dot; shared min/max; **unique gradient id per card** via
`"sp_"+hash(name)` L150 — same-page `<linearGradient>` ids must not collide) + big cum%
(sign-colored `_ret_color`) + α chip (**sign-colored**, L148-149: teal bg if ≥0 else red —
INVARIANT, reference hardcoded UP) + `_dots` win/loss scatter (L119, pseudo-random shuffle,
teal=win/red=loss). IPO card `_ipo_card` (L174) = bar rows. Chinese literals hardcoded
("策略速览", "如何阅读本页", "基准", "胜率"). Tokens: `CMSI_RED, INK, INK_2/3/4, UP, DOWN,
PAPER, PAPER_RULE, PAPER_EDGE, PAPER_DEEP, FONT_MONO`.

### LIVE_DOT_CSS in theme
`strategy_banner.LIVE_DOT_CSS` (strategy_banner.py:249-255) is a `.format()`-ready snippet
(`.cmsi-live-dot` + `@keyframes cmsiPulse`). It has been **inlined into theme's global
`_CSS`** at `theme.py:741-746` (comment: "Strategy banner LIVE pulse dot
(lib/strategy_banner.live_title)"). ⚠ **DEAD / FRAGILE:** `live_title` NO LONGER renders any
`.cmsi-live-dot` element — the TRACKING/LIVE badge was removed (docstring L47-49, "实时跟踪·
TRACKING 徽标已去除 — George 拍板", data is EOD/cron). So the CSS class + the module-level
`LIVE_DOT_CSS` constant are both orphaned. A reskin should not assume there is a live dot to
restyle; if it wants one it must re-add the DOM element.

### Height budget
None — pure markdown flow. Grids: `repeat(len(items),1fr)` (strip), `repeat(len(cards),1fr)`
(dual_track).

### Fragile / spillover
- Single-page (4_Strategy_Picks only) → no spillover.
- α chip + cum% sign-coloring INVARIANT (must read red on loss/underperformance).
- Unique gradient-id-per-card INVARIANT (else SVG fills bleed across cards).
- `live_title` lang toggle is a real anchor navigation (`?lang=…`, `target="_self"`);
  caller wires `st.query_params` → `session_state`.

---

## Spillover summary (which modules touch >1 page)

| module | pages rendered on | spillover |
|---|---|---|
| IPO tab | 4_Strategy_Picks (last tab) | none (single) |
| market_hub_tiles | home | none (single) |
| heatmap_treemap (renderer) | home | none — BUT `build_domain_bento` payload shared w/ `e2_etf_heatmap.py` (old `render_bento_html`) |
| sector_overview | **2_Healthcare + a2_ai_overview** | **YES — 2 pages** |
| strategy_hero | 4_Strategy_Picks | none (single) |
| strategy_banner | 4_Strategy_Picks | none (single) |

Only **`sector_overview`** renders on more than one page → highest cross-page regression
risk. The **`build_domain_bento`** payload is shared between the home treemap and the ETF
bento page, so a payload-shape change (not a treemap-render change) would hit `e2_etf_heatmap`.

## Cross-cutting INVARIANTs a reskin must not break
1. teal = up / red = down (HK-US), everywhere.
2. echarts `src` stays relative `app/static/echarts.min.js` (cloud `/~/+/` prefix).
3. echarts iframes need `html,body{height:100%}` + `#id` explicit px height.
4. multi-small-chart surfaces (market_hub_tiles, sector_overview, strategy_banner) stay
   **inline SVG, not echarts** (0-width race).
5. sign-color the strategy's own cum/alpha (loss/underperformance reads red).
6. IPO `day1_ret` is DECIMAL (×100 at render); `code` stays str.
7. stale docstrings: `load_ipo` "18 rows" (actual 54: 38 listed/16 pending);
   `load_ipo_intraday` "17 listed" (actual 20 distinct codes).
8. `.cmsi-live-dot` CSS is orphaned dead code (no live dot rendered anymore).
