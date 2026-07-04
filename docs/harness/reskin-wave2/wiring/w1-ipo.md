# W1-IPO Wiring Instructions

> Builder W1 deliverable — 港股 IPO 打新 1a 报纸精修  
> File created: 2026-07-04 | Status: ready for W-INT

## What was built

`app/lib/ipo_stage.py` — self-contained IPO 1a composition module.

Public surface:
```python
from app.lib.ipo_stage import render

render(
    picks: pd.DataFrame,
    intraday: pd.DataFrame,
    *,
    prefer_cn: bool,
    as_of: str,
) -> None
```

Emits exactly one `st.iframe(srcdoc, height=...)` call. No other Streamlit state is
mutated. The inner HTML builder `_build_html(picks, intraday, prefer_cn, as_of) -> str`
is a pure function with no Streamlit dependency — testable standalone.

---

## Integration target

File: `app/pages/4_Strategy_Picks.py`  
Function to supersede: `render_ipo_strategy()` (L571–707) + `_render_ipo_table()` (L710–788)

### Minimal wiring diff

```python
# --- top of file, add import ---
from app.lib.ipo_stage import render as _render_ipo_1a

# --- inside render_ipo_strategy() body, replace existing content with: ---
def render_ipo_strategy() -> None:
    picks    = load_ipo()           # pd.DataFrame, 54 rows
    intraday = load_ipo_intraday()  # pd.DataFrame, code/time/close
    prefer_cn = st.session_state.get("lang", "zh") != "en"
    as_of = picks["list_date"].dropna().max() if "list_date" in picks.columns else "2026-07-03"
    _render_ipo_1a(picks, intraday, prefer_cn=prefer_cn, as_of=str(as_of))
```

The tab slot itself is already wired at L818–819:
```python
with strategy_tabs[-1]:
    render_ipo_strategy()
```
No change needed there.

---

## Data shape contract

### picks (from `load_ipo()`)

| Column | Type | Notes |
|--------|------|-------|
| `code` | str/int → coerced to str | e.g. "1234" |
| `name_cn` | str | Chinese name |
| `name_en` | str | English name |
| `score` | float | Sort key (desc) |
| `tier` | str | One of: 重点申购+ / 重点申购 / 推荐申购 / 谨慎申购 / 不申购 |
| `list_date` | str/date/None | Pending rows: None/NaN |
| `day1_ret` | float | DECIMAL — ×100 at render; e.g. 3.84 = 384% |
| `sub_sector` | str | Shown in ranking table |
| `status` | str | "listed" or anything else (→ pending) |
| `source` | str | Provenance label in dock footer |

### intraday (from `load_ipo_intraday()`)

| Column | Type | Notes |
|--------|------|-------|
| `code` | str/int → coerced to str | Must match picks.code |
| `time` | str | e.g. "09:30"; used for sort order only |
| `close` | float | 5-min closing price |

Only listed codes with paths appear. Empty DataFrame is valid (all docks show
"盘中路径未采集" state).

---

## Superseded items (CONTRACT IPO14)

These are fully removed by 1a — W-INT must delete or no-op them:

- `_render_ipo_table()` function (L710–788) — the dual-sort-toggle HTML table
- `ipo_rank_sort` session state key — no longer used
- `render_html_table` call path inside `render_ipo_strategy()`
- Plotly `go.Figure` small-multiples intraday wall — removed (dock SVG replaces it)

---

## CSS / font invariants

- Fonts: self-hosted via `theme.FONT_FACE_CSS` (relative `app/static/fonts/…` URL,
  no leading `/`). Do NOT add Google Fonts CDN.
- Down/break colour: `#c8102e` (CMSI_RED) — page-scope exemption per CONTRACT §0 D2.
  `theme.DOWN` (#cc0000) is unchanged globally.
- No `box-shadow` anywhere — station rule.
- Glass: `rgba(255,255,255,.55)` / blur14 / `rgba(255,255,255,.7)` border.
- All radii ≤ 4px.

---

## Smoke test

```bash
PYTHONPATH=/path/to/invest-dashboard uv run python app/lib/ipo_stage.py
```

12 assertions, all must PASS:
- "上市日期" in html
- "待上市" in html
- no "MOCK"
- no "2.69"
- KPI "已上市 3 · 待上市 1" (synthetic data)
- best return "+384.0%"
- worst return "-56.9%"
- no CDN fonts.googleapis.com / fonts.gstatic.com
- no box-shadow
- "重点申购+" in tier rows
- intraday code "1234" in INTRADAY json
- html size ≥ 10,000 bytes

---

## iframe height

Computed dynamically: `max(2400, 900 + len(picks) * 33)` px.  
For 54 rows → 2682 px. Adjust in `render()` if layout changes.

---

## Files touched by W1

| File | Action |
|------|--------|
| `app/lib/ipo_stage.py` | CREATED |
| `docs/harness/reskin-wave2/wiring/w1-ipo.md` | CREATED |

No other files modified. W-INT owns the integration into `4_Strategy_Picks.py`.
