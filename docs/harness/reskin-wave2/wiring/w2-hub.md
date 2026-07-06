# Wiring Note — Builder W2 · Market Hub Tiles
> Builder: W2 · File: `app/lib/market_hub_tiles.py` · Wave-2 reskin · 2026-07-04

## Status

`app/lib/market_hub_tiles.py` is **done and verified** (py_compile OK, smoke OK, GR battery clean).
Public signature **unchanged** — no breaking call-site changes required.

---

## HUB1 · Masthead (at page level — not in market_hub_tiles.py)

Per `current-state.md` and `specs/hub.md §masthead`:

The masthead ("行情中枢" h1 + sub-kicker + right EOD timestamp) lives at **home.py** level,
rendered via `theme.page_header(...)` or an equivalent st.markdown block. It is **not**
rendered inside `market_hub_tiles.py`.

Wave-2 masthead delta (spec §1):

| Element | Old | New (wave-2) | File |
|---------|-----|------|------|
| Red accent | h1 trailing dot 4×24 | **Left-side bar 5×44 r1 #c8102e** | home.py masthead block |
| h1 size | 32px / 36px | **30px / 34px** | home.py |
| Sub-kicker | (none) | `CMSI · MARKET HUB · 四大指数总览` JetBrains Mono 11px/.08em #8a8580 mt5 | home.py |
| Right side | TRACKING 呼吸徽标(已删) | **EOD {date} · {fetch_utc} HKT** mono 11 #8a8580 (real value from `db.latest_snapshot_date()` + `db.last_fetch_utc()`) | home.py |

TRACKING/cmsiPulse徽标: George 已拍板删除 — **不回归**。右侧改为纯 EOD 时间戳。

Suggested home.py edit area: the existing `st.markdown(theme.page_header(...))` call for
the Market Hub section (around line 285-287 per current-state.md call-site).
Implementation is at **home.py builder's discretion** (no Wave-2 Builder owns home.py masthead
under the current harness split — assign separately or defer to post-merge).

---

## HUB2 · Eyebrow title (moved into market_hub_tiles.py — no home.py change needed)

In v1 the eyebrow "市场总览" was rendered by home.py. In v2, the entire eyebrow including
the bilingual title is rendered **inside the srcdoc** by `render_index_tiles()`:

```
市场总览 · Market Overview   (always bilingual, JetBrains Mono 12px/.16em UPPER)
```

The call-site in home.py (`st.iframe(doc, height=h)`) requires **no change** — the srcdoc
already contains the eyebrow. If home.py currently renders a separate `st.subheader` or
`st.markdown` for "市场总览" above the iframe, that duplicate should be **removed** to avoid
double-printing the eyebrow.

Check home.py around the Market Hub iframe call for any standalone "市场总览" markdown.

---

## Call-site (home.py) — unchanged

```python
# app/home.py ~line 285-287 (current-state.md)
from lib import market_hub_tiles as mht
doc, h = mht.render_index_tiles(tiles, as_of=as_of_str, prefer_cn=prefer_cn)
st.iframe(doc, height=h)
```

`render_index_tiles` signature is backward-compatible. `height` default is still 372.
The glass row inside the srcdoc is 248px; remaining 124px headroom covers eyebrow + dek +
footnote + padding. If the dek shows (market-read) the strip may need +20px; update
`height=392` at the call-site if the footnote clips.

---

## Page-level background (advisory — not W2 scope)

`specs/hub.md §交互` notes: the outer-page watercolor wash (`radial-gradient` on `.stApp`)
is high-risk (global CSS pollution). The **inner iframe** already carries the dual-radial
watercolor background, so glass blur is visible. Page-level outer wash is deferred /
optional — can be addressed independently with a scoped `st.markdown` injection.
