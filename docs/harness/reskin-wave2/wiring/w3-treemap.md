# W3 Treemap — Call-site wiring notes

Builder: W3 · File owned: `app/lib/heatmap_treemap.py`

## New parameter

`render_treemap_html` gained one new keyword-only parameter with a backward-compatible default:

```python
def render_treemap_html(
    payload: dict,
    *,
    window_label: str,
    as_of: str | None,
    prefer_cn: bool,
    height: int = 720,
    show_header: bool = True,   # NEW — default True keeps existing behaviour
) -> tuple[str, int]:
```

**No breaking change.** Existing call in `app/home.py:178` continues to work as-is (masthead/legend/banner shown on every iframe, which is correct for the single-domain case today).

## Recommended wiring for multi-domain stacking

When `app/home.py` renders multiple domains in a loop (`_render_stock_heatmap`, lines ~170-180), the masthead, gradient legend, and convention banner should appear **once** (first domain only).  
Wiring change — `app/home.py` (NOT modified by W3; documented here for the integrator):

```python
for i, domain_id in enumerate(domains):
    payload = heatmap.build_domain_bento(domain_id, window_col, prefer_cn)
    if not payload:
        continue
    _h = 600 if len(domains) > 1 else 720
    doc, h = heatmap_treemap.render_treemap_html(
        payload,
        window_label=window_label,
        as_of=latest,
        prefer_cn=prefer_cn,
        height=_h,
        show_header=(i == 0),   # page-level elements only on first domain
    )
    st.iframe(doc, height=h)
```

The `show_header=False` iframes omit masthead/legend/banner and use a smaller canvas overhead (110 px instead of 200 px), which is correct for a vertically-stacked layout.

## Canvas height logic

| `show_header` | overhead | canvas formula |
|---|---|---|
| `True` (default) | 200 px | `max(200, height - 200)` |
| `False` | 110 px | `max(200, height - 110)` |

With `height=720` (single domain): canvas = 520 px  
With `height=600` + `show_header=False` (2nd+ domain): canvas = 490 px

## ETF page — not affected

`app/pages/e2_etf_heatmap.py:52` calls `heatmap.build_domain_bento` for its **payload** only — it does not call `render_treemap_html`.  
The payload shape (`sectors`, `tiles`, `mcap`, `ret`, `median`, `n_total`, `source`, `cn`, `en`) is **unchanged** in this reskin, so the ETF page has zero regression risk.
