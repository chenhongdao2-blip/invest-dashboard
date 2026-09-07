"""Regression guard for the ETF holdings weighted/tail split.

Context (R3 audit item 7). `etf_panel.holdings_for` used to split an ETF's rows
into "weighted head" vs "symbol-only tail" on `rank.notna()`. That was never the
contract — it only *happened* to work while the upstream primary source
(stockanalysis) was up, because that source assigns a rank exclusively to the
rows it also weights.

On 2026-08-29 stockanalysis started returning 404 and etf-data-mcp fell through
to its barchart symbols-only fallback, which numbers **every** row 1..N and
carries no weights at all. The rank-based split then classified 59 weightless
XLV rows as "weighted" and produced an empty tail — a silent shape break.

The real contract is the one etf_panel's own docstring states: a weighted row is
a row that has a weight. These tests pin that, using synthetic frames so they
stay green regardless of what the committed CSV currently holds.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "app"))


def _frame(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["etf_ticker", "rank", "symbol", "name", "weight_pct"])


def test_weighted_tail_split_uses_weight_not_rank():
    """A ranked-but-weightless row is TAIL, not a weighted holding.

    This is the exact shape the barchart symbols-only fallback emits.
    """
    from lib import etf_panel  # noqa: PLC0415

    df = _frame([
        {"etf_ticker": "XLV", "rank": 1, "symbol": "LLY", "name": "Eli Lilly", "weight_pct": 16.4},
        {"etf_ticker": "XLV", "rank": 2, "symbol": "JNJ", "name": "J&J", "weight_pct": 10.5},
        # ranked by the fallback, but no weight → belongs in the tail
        {"etf_ticker": "XLV", "rank": 3, "symbol": "ABBV", "name": None, "weight_pct": None},
        {"etf_ticker": "XLV", "rank": 4, "symbol": "MRK", "name": None, "weight_pct": None},
    ])
    weighted, tail = etf_panel.holdings_for(df, "XLV")

    assert weighted["symbol"].tolist() == ["LLY", "JNJ"]
    assert weighted["weight_pct"].notna().all(), "weighted_df must never carry a null weight"
    assert tail == ["ABBV", "MRK"], "ranked-but-weightless rows must surface as tail symbols"


def test_weighted_tail_split_still_handles_the_classic_null_rank_shape():
    """The pre-2026-08-29 shape (tail rows have no rank either) is unchanged."""
    from lib import etf_panel  # noqa: PLC0415

    df = _frame([
        {"etf_ticker": "XLV", "rank": 1, "symbol": "LLY", "name": "Eli Lilly", "weight_pct": 16.4},
        {"etf_ticker": "XLV", "rank": None, "symbol": "EW", "name": None, "weight_pct": None},
    ])
    weighted, tail = etf_panel.holdings_for(df, "XLV")

    assert weighted["symbol"].tolist() == ["LLY"]
    assert tail == ["EW"]


def test_weighted_rows_are_sorted_by_rank_even_when_the_input_is_not():
    from lib import etf_panel  # noqa: PLC0415

    df = _frame([
        {"etf_ticker": "IBB", "rank": 3, "symbol": "C", "name": "c", "weight_pct": 1.0},
        {"etf_ticker": "IBB", "rank": 1, "symbol": "A", "name": "a", "weight_pct": 3.0},
        {"etf_ticker": "IBB", "rank": 2, "symbol": "B", "name": "b", "weight_pct": 2.0},
    ])
    weighted, _ = etf_panel.holdings_for(df, "IBB")

    assert weighted["symbol"].tolist() == ["A", "B", "C"]


def test_a_fully_unweighted_etf_degrades_to_all_tail_and_never_fabricates_zero():
    """Whole-ETF degradation: no weighted rows, every symbol kept as tail, no 0.0."""
    from lib import etf_panel  # noqa: PLC0415

    df = _frame([
        {"etf_ticker": "XBI", "rank": i, "symbol": f"S{i}", "name": None, "weight_pct": None}
        for i in range(1, 6)
    ])
    weighted, tail = etf_panel.holdings_for(df, "XBI")

    assert weighted.empty
    assert tail == ["S1", "S2", "S3", "S4", "S5"]
    assert not (weighted["weight_pct"] == 0.0).any(), "unknown weight must never become 0.0"


def test_unknown_ticker_and_empty_frame_are_safe():
    from lib import etf_panel  # noqa: PLC0415

    weighted, tail = etf_panel.holdings_for(_frame([]), "XLV")
    assert weighted.empty and tail == []

    df = _frame([{"etf_ticker": "XLV", "rank": 1, "symbol": "LLY", "name": "x", "weight_pct": 1.0}])
    weighted, tail = etf_panel.holdings_for(df, "NOPE")
    assert weighted.empty and tail == []


def test_weight_coverage_flags_a_degraded_etf():
    """`weight_coverage` is the app-side tripwire for the silent-degradation bug."""
    from lib import etf_panel  # noqa: PLC0415

    df = _frame([
        {"etf_ticker": "XLV", "rank": 1, "symbol": "LLY", "name": "Eli Lilly", "weight_pct": 16.4},
        {"etf_ticker": "XLV", "rank": 2, "symbol": "JNJ", "name": None, "weight_pct": None},
        {"etf_ticker": "XBI", "rank": 1, "symbol": "A", "name": None, "weight_pct": None},
    ])
    cov = etf_panel.weight_coverage(df)

    assert cov["XLV"] == (1, 2)
    assert cov["XBI"] == (0, 1)
    assert etf_panel.degraded_etfs(df) == ["XBI"]
