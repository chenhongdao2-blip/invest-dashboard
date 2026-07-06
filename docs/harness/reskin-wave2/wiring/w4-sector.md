# W4 Sector — Call-site Changes Required

**Builder:** W4 (sector_overview wave-2 reskin)
**Output file:** `app/lib/sector_overview.py`
**Status:** Implementation complete — call sites below need wiring by integration builder.

---

## Pages affected

Both pages import `sector_overview as so`. Neither file is touched by W4; changes below
belong to the integration pass.

- `app/pages/2_Healthcare.py`
- `app/pages/a2_ai_overview.py`

---

## 1. Add page_radial_wash call (both pages, SOVR4/D5)

`theme.page_radial_wash(1240)` must be called at page level before any `so.*` call
so backdrop-filter has something to blur behind the glass containers.

Both pages already import `theme` — just ensure the call happens early in the page body
(before the first column layout opens), e.g.:

```python
# Near top of page render block:
theme.page_radial_wash(1240)
```

---

## 2. Replace section_header with so.masthead() (both pages, SOVR2)

### 2a. Healthcare page (`app/pages/2_Healthcare.py`)

**Remove** (line ~124):
```python
theme.section_header(i18n.t("hc.section.benchmark"), ...)
```

**Replace with** (after building `_asof` and `_src` which already exist around line 148):
```python
prefer_cn = i18n.get_lang() == "zh"
so.masthead(
    title=i18n.t("hc.section.benchmark"),        # existing i18n key
    chip="HEALTHCARE",
    subtitle=i18n.t("hc.section.benchmark_sub"),  # new i18n key (add to locales)
    asof=_asof,
    source=_src,
    prefer_cn=prefer_cn,
)
```

If a subtitle i18n key doesn't yet exist, pass a literal fallback:
```python
subtitle="基准 ETF 分档表现 · 30 日趋势 · 相对标普超额",  # zh fallback
```

### 2b. AI Overview page (`app/pages/a2_ai_overview.py`)

**Remove** (line ~107):
```python
theme.section_header(i18n.t("ai.section.benchmark"))
```

**Replace with**:
```python
prefer_cn = i18n.get_lang() == "zh"
so.masthead(
    title=i18n.t("ai.section.benchmark"),
    chip="AI TECH",
    subtitle="基准 ETF 分档表现 · 30 日趋势 · 相对标普超额",
    asof=_asof,          # build from existing row payload (mirrors HC pattern)
    source=_src,
    prefer_cn=prefer_cn,
)
```

Note: `a2_ai_overview.py` already computes `prefer_cn = i18n.get_lang() == "zh"` at
line ~134 for the existing `window` label — reuse that binding.

---

## 3. Add prefer_cn to movers() calls (both pages, SOVR14)

### 3a. Healthcare page (`app/pages/2_Healthcare.py`, line ~521):

**Before:**
```python
so.movers(gainers=..., losers=..., window=...)
```

**After:**
```python
so.movers(gainers=..., losers=..., window=..., prefer_cn=prefer_cn)
```

`prefer_cn` is already bound from the masthead block above (step 2a). The `window`
argument string can stay as-is; the bilingual column headers ("涨幅前 10 · GAINERS" /
"跌幅前 10 · LOSERS") are now generated inside `movers()` regardless of `window` lang.

### 3b. AI Overview page (`app/pages/a2_ai_overview.py`):

Same pattern. `prefer_cn` is already bound at line ~134.

---

## 4. No other changes

`benchmark_table(rows, source=...)` signature is backward-compatible — same positional
`rows` arg, same keyword `source`. No changes needed to row construction or data loading.

The section header inside `benchmark_table` (色阶图例 + "基准 · Benchmark ETF" label) is
now emitted by the module itself, so any standalone `theme.section_header()` call for the
benchmark block should be removed to avoid a duplicate header.

---

## Token cross-check

All tokens consumed from `theme.py` — verified against theme.py line numbers:

| Token | Line | Value |
|---|---|---|
| `t.CMSI_RED` | 20 | `#c8102e` |
| `t.UP` | 56 | `#0d7680` |
| `t.INK` | 49 | `#1a1a1a` |
| `t.INK_2` | 50 | `#4a4a4a` |
| `t.INK_3` | 51 | `#8a8580` |
| `t.PAPER_RULE` | — | `#ebd9c8` |
| `t.PAPER_EDGE` | — | `#d4c4b0` |
| `t.PAPER_EDGE_SOFT` | — | `#e4d2bd` |
| `t.FONT_DISPLAY` | — | `'Space Grotesk', ...` |
| `t.FONT_MONO` | — | `'JetBrains Mono', ...` |

`theme.DOWN` (#cc0000) is NOT used. Module uses `_DOWN = t.CMSI_RED` per SOVR13.
