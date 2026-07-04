# W6 Banner — Wiring Notes
> Builder: W6 | File: `app/lib/strategy_banner.py` | Date: 2026-07-04
> CONTRACT: BANR1–BANR12 (wave-2 reskin)

These are the call-site / data-contract changes that **cannot** land in
`strategy_banner.py` itself (scope restriction). Each item is a pending wiring
task for the page owner or a downstream builder.

---

## W6-WIRE-1 — Radial wash (BANR1)

**File:** `app/pages/4_Strategy_Picks.py`

**Why:** Glass cards (`backdrop-filter:blur`) need a non-white wash behind them
to show any effect. `theme.page_radial_wash(1240)` injects dual radial
gradients (red + teal) at page level (theme.py:1022). Without this call the
glass looks like plain white.

**Change:** Add one line near the top of the page rendering block, after
`theme.apply()` and before the first `st.markdown` / tab render:

```python
# wave-2: radial wash for glass card backdrops (BANR1)
t.page_radial_wash(1240)
```

No new import needed — `t` is already aliased as `from lib import theme as t`
in the page.

---

## W6-WIRE-2 — Per-holding win_list for dot band (BANR8 CRITICAL)

**File:** `app/pages/4_Strategy_Picks.py` — function `_overview_curve_card()`

**Why:** `_dots()` in the banner now draws from a real per-holding boolean
list (truthy = win, falsy = loss), not from a pseudo-random seed shuffle.
The banner falls back gracefully to a wins-first ordering when `win_list` is
absent from the dict, but the CONTRACT requires real data (BANR8).

**Current state (approx. line 105):**

```python
return {
    ...
    "wins":  int((normed.iloc[-1] > 100).sum()),
    "total": int(normed.shape[1]),
    ...
}
```

**Required addition:**

```python
# BANR8: per-holding sign list for _dots() (real, no shuffle)
# Column order = rank order from top_syms → deterministic display
"win_list": (normed.iloc[-1] > 100).tolist(),
```

`normed.columns` retains the `top_syms` rank order (highest conviction first),
so the dot display is both real and deterministic without any additional sort.

**Banner behaviour when `win_list` is absent (backward-compat fallback):**
`_curve_card()` synthesises `[True]*wins + [False]*(total-wins)` — all wins
clustered first, all losses after. Functional but not real-data compliant.

---

## W6-WIRE-3 — IPO pending count (informational, no code change)

**File:** `app/pages/4_Strategy_Picks.py` — function `_overview_ipo_card()`

The banner's `_ipo_card()` reads `it.get("pending", it["n"] - it["listed"])`
so it works whether or not the caller adds a `"pending"` key. No action
required unless the caller wants to supply a more precise pending count
(e.g. excluding withdrawn deals).

---

## Summary table

| Wire ID | File | Function | Priority | Status |
|---------|------|----------|----------|--------|
| W6-WIRE-1 | 4_Strategy_Picks.py | page render block | P1 — visual | pending |
| W6-WIRE-2 | 4_Strategy_Picks.py | `_overview_curve_card()` | P0 — data integrity | pending |
| W6-WIRE-3 | 4_Strategy_Picks.py | `_overview_ipo_card()` | P2 — optional | n/a |
