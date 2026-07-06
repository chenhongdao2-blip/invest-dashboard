# W5 Hero — Wiring Note

**Builder:** W5 | **File:** `app/lib/strategy_hero.py` | **Date:** 2026-07-04

## Call-site status: NO CHANGES REQUIRED

The public API of both exported functions is unchanged:

```python
strategy_hero.render(
    strat_name, strat_dates, strat_curve,
    bench_name, bench_curve,
    cum_ret, bench_ret, alpha_pp,
    pick_date, n_hold, pool, days,
    wins, n_total, mdd, sharpe,
    bench_code, bench_sub,
    as_of, source
)

strategy_hero.render_compare_chart(
    dates, lines, marker_date, marker_label,
    title, source, height=460
)
```

Call site `pages/4_Strategy_Picks.py` (L232-245 render / L485-490 render_compare_chart)
requires **zero edits**.

## Internal changes (strategy_hero.py only)

| Area | Before | After |
|------|--------|-------|
| `_CSS` hero card | flat cream border | `rgba(255,255,255,.55)` + `blur(14px)` + `border-top: 3px solid #c8102e` |
| Radial wash | none | `.wash` dual radial via `position:absolute` overlay |
| `.wrap` | none | `position:relative` containing block for wash layering |
| `html,body` CSS | no height set | `height:100%` (CONTRACT K invariant) |
| Font in `_CSS.format()` | `FONT=t.FONT_STACK` | `FONT=t.FONT_DISPLAY` (Space Grotesk-first) |
| Font in `data` dict | `"FONT": t.FONT_STACK` | `"FONT": t.FONT_DISPLAY` |
| CSS format — new token | — | `EDGE_SOFT=t.PAPER_EDGE_SOFT` (#e4d2bd) |
| `.hero-left` | no glass overlay | `background:rgba(255,255,255,.35)` + `border-right:1px solid {EDGE_SOFT}` |
| Live dot in body HTML | orphan CSS, no DOM node | `<div class="live">…</div>` added before `.strat-name` |
| Live text | "TRACKING LIVE" (CSS dead) | "持续跟踪 · EOD" (CONTRACT D3: honest wording) |
| Keyframe name | `pulse` | `cmsiPulse` (namespace isolation) |
| `.live-t` color | `{UP_DEEP}` | `{UP}` (#0d7680) |
| MDD tile color | `t.DOWN` (#cc0000) | `t.CMSI_RED` (#c8102e) (CONTRACT D2) |
| `.big-num` font-size | 58px | 56px (CONTRACT N-6 budget) |
| `.big-lbl`, `.kh-lbl` | no `font-family` | `font-family:{MONO}` (JetBrains Mono) |
| `.bf-lbl`, `.bf-v` | generic | `font-family:{MONO}` |
| `.bf-div` divider | `{INK4}` | `{EDGE_SOFT}` (#e4d2bd) |
| `render_compare_chart` | unchanged | unchanged (CONTRACT §2 N: not to touch) |

## Token cross-check (theme.py)

- `t.CMSI_RED = "#c8102e"` — MDD + hero top border + strat line/area
- `t.PAPER_EDGE_SOFT = "#e4d2bd"` — left-panel border-r + bf-div + kh-tile border-r
- `t.FONT_DISPLAY` = Space Grotesk-first — render() hero context only
- `t.FONT_STACK` — kept as-is in render_compare_chart (not reskinned)
- `t.DOWN = "#cc0000"` — sign-color for negative cum_ret / alpha (invariant, unchanged)
