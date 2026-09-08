# Inline `prefer_cn` ternaries still bypassing the locale tables

Follow-up note for R3 audit §7 / §8.4. **Not done in PR 3** — recorded so the
remaining work is a list rather than a re-count.

## What the audit found

The two locale tables are the right design and carry **zero drift** (now pinned
by `tests/test_locale_parity.py`). The problem is that pages route around them
with `X if prefer_cn else Y` written inline, so those strings are invisible to
the tables, cannot be reviewed as a pair, and drift silently.

## What PR 3 moved

`app/pages/4_Strategy_Picks.py` — the largest single block, ~145 lines of
hand-written label dicts (holdings table, HD scorecard, biotech scorecard).
98 strings now live in `lib/locales/pages_{en,zh}.py` under `picks.tbl.*`,
`picks.sc.hd.*`, `picks.sc.bio.*`. Verified byte-identical in both languages
against the previous inline dicts before the swap.

That page is down to **1** remaining occurrence (`_prefer_cn`, passed through to
`picks_table.render_methodology` as a flag, not a string choice — nothing to
move).

## What is left

Counted with `grep -cE "if _?prefer_cn|prefer_cn else"` over `app/`, 2026-09-07,
after PR 3. Note the audit's own figures were per-file greps of a slightly
different pattern, so these run a little higher; the ordering matches.

| file | count | note |
|---|---:|---|
| `app/home.py` | 49 | audit said 54 — the biggest remaining block by far |
| `app/lib/sec_statements.py` | 25 | audit said 25 |
| `app/lib/rrg.py` | 21 | audit said 22 |
| `app/lib/charts.py` | 18 | audit said 19 |
| `app/lib/candlestick_terminal.py` | 15 | not in the audit's list |
| `app/pages/3b_Sector_Rotation.py` | 14 | |
| `app/lib/heatmap_treemap.py` | 13 | |
| `app/lib/stock_header.py` | 7 | |
| `app/lib/heatmap.py` | 7 | |
| `app/lib/views/sec_facts.py` | 6 | mostly `prefer_cn = get_lang() == "zh"` flags |
| `app/pages/1_CMSI_Coverage.py` | 4 | |
| `app/lib/market_hub_tiles.py` | 4 | |
| `app/pages/model_drill.py` | 3 | |
| `app/pages/6_Ticker_Drill.py` | 3 | **owned by another branch — do not touch** |
| `app/lib/sector_overview.py` | 3 | |
| `app/lib/rs_panel.py` | 3 | |
| `app/lib/rebalance_panel.py` | 3 | |
| `app/lib/hd_rebalance_panel.py` | 3 | |
| 15 files with 1–2 each | 21 | incl. `app/pages/4_Strategy_Picks.py` (1) |

**Total remaining: ~222 occurrences across 33 files.**

Not all are string choices. A large share are the single line
`prefer_cn = i18n.get_lang() == "zh"` followed by passing that boolean to a
renderer that does its own bilingual layout (`section_header.cover`,
`picks_table.render_methodology`, the iframe table builders). Those are a
different pattern and are fine as they are. Before migrating a file, split its
hits into:

1. **string choices** — `"名称" if prefer_cn else "Name"` → move to the tables;
2. **layout flags** — `prefer_cn=` passed to a component → leave alone.

`home.py` is where that split is worth doing first: it has the most hits, and it
is the page every session opens.
