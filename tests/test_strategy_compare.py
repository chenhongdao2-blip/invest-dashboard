"""Contract for the shared generation-compare tearsheet (Strategy Picks).

R3 audit §7: `render_hd_compare` (176 lines), `render_biotech_compare` (163) and
`_overview_curve_card` each re-implemented the same compute path, and the two
compare views then re-implemented the whole tearsheet assembly on top. They now
share `_book_curve` / `_bench_norm` / `_union_index` / `_align` and one
`_render_generation_compare`.

The refactor was verified by capturing every kwarg handed to
`strategy_hero.render_gen_compare` for both views, before and after, with the
price frame pinned — all 23 kwargs identical for both views (HD reads live
yfinance, so an unpinned comparison only drifts by the intraday bar).

These tests keep that shape pinned going forward. They pin prices too, so they
never depend on the network or on today's bar: what they assert is the structure
and the internal consistency of what the page displays, which is what a bad
parameterization would break (wrong line order, a benchmark rendered as a
generation, a curve not aligned to the shared x-axis, the wrong rebalance-marker
base, a dropped `pending` flag).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
_APP = REPO_ROOT / "app"
if str(_APP) not in sys.path:
    sys.path.insert(0, str(_APP))

_PAGE = _APP / "pages" / "4_Strategy_Picks.py"


def _synthetic_closes(symbols, start="2026-01-01", periods=200) -> pd.DataFrame:
    """Deterministic, strictly-positive prices — no network, no DB, no drift.

    Each symbol gets its own gentle slope so curves are distinguishable and every
    book has a non-degenerate return.
    """
    idx = pd.bdate_range(start=start, periods=periods)
    data = {}
    for i, s in enumerate(sorted(symbols)):
        base = 100.0 + i
        drift = 1.0 + ((i % 7) - 3) / 5000.0
        data[s] = [base * (drift ** n) for n in range(len(idx))]
    return pd.DataFrame(data, index=idx)


@pytest.fixture()
def compare_calls(monkeypatch):
    """Render each compare view with pinned prices; return {view: kwargs}."""
    from streamlit.testing.v1 import AppTest
    from lib import strategy as strat, strategy_hero, i18n

    all_syms: set[str] = set()
    for cfg in strat.STRATEGIES.values():
        picks = cfg["loader"]()
        if not picks.empty and "yf_sym" in picks.columns:
            all_syms |= set(picks["yf_sym"].dropna().tolist())
        for key in ("benchmark", "benchmark2"):
            if cfg.get(key):
                all_syms.add(cfg[key])
    frame = _synthetic_closes(all_syms)

    def fake_fetch(symbols, start=None, ovr_mtime=None, **kw):
        cols = [s for s in symbols if s in frame.columns]
        sub = frame[cols]
        if start:
            sub = sub[sub.index >= pd.Timestamp(start)]
        return sub

    monkeypatch.setattr(strat, "fetch_picks_closes", fake_fetch)

    captured: dict[str, dict] = {}
    i18n.init_lang()
    views = {
        "hd": (i18n.t("strategy.name.hk_hd"), "hd_version",
               i18n.t("strategy.hd.version.compare")),
        "biotech": (i18n.t("strategy.name.v4_biotech"), "biotech_version",
                    i18n.t("strategy.biotech.version.compare")),
    }
    for name, (view, vkey, vval) in views.items():
        seen: list[dict] = []
        monkeypatch.setattr(strategy_hero, "render_gen_compare",
                            lambda **kw: seen.append(dict(kw)))
        at = AppTest.from_file(str(_PAGE), default_timeout=300)
        at.session_state["strategy_view"] = view
        at.session_state[vkey] = vval
        at.run()
        assert not at.exception, f"{name} compare raised: {at.exception}"
        assert len(seen) == 1, f"{name} compare called render_gen_compare {len(seen)}x"
        captured[name] = seen[0]
    return captured


# ── the generation/benchmark split ────────────────────────────────────────────

@pytest.mark.parametrize("view,n_gens", [("hd", 3), ("biotech", 3)])
def test_one_card_per_generation_plus_the_benchmark(compare_calls, view, n_gens):
    cards = compare_calls[view]["cards"]
    assert len(cards) == n_gens + 1, "cards = one per generation, then the benchmark"
    assert all(c["value"].endswith("%") or c["value"] == "—" for c in cards)


def test_only_the_biotech_v6_card_carries_a_pending_flag(compare_calls):
    """`pending` exists on exactly one card and only in the biotech view.

    Collapsing the two views into one function must not leak the flag into HD
    (which has no pending generation) nor drop it from biotech v6.
    """
    hd = [c for c in compare_calls["hd"]["cards"] if "pending" in c]
    bio = [c for c in compare_calls["biotech"]["cards"] if "pending" in c]
    assert hd == [], "HD cards must not carry a pending flag"
    assert len(bio) == 1 and bio[0] is compare_calls["biotech"]["cards"][2], (
        "biotech v6 (3rd card) must keep its pending flag"
    )


@pytest.mark.parametrize("view,n_bench", [("hd", 2), ("biotech", 1)])
def test_benchmark_lines_come_first_and_are_never_solid(compare_calls, view, n_bench):
    """HD overlays 2 benchmarks (3466.HK + ^HSI), biotech 1 (XBI).

    Benchmarks lead the overlay and are dashed/dotted; generations follow and are
    solid. Getting this order wrong is the classic parameterization slip.
    """
    lines = compare_calls[view]["cmp_lines"]
    heads, tails = lines[:n_bench], lines[n_bench:]
    assert all(ln["dash"] in ("dashed", "dotted") for ln in heads), \
        f"first {n_bench} overlay line(s) must be the benchmark(s)"
    assert all(ln["dash"] == "solid" for ln in tails), \
        "generation lines must be solid and come after the benchmarks"
    assert len(tails) >= 1


# ── shared x-axis ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("view", ["hd", "biotech"])
def test_every_curve_is_aligned_to_the_shared_date_axis(compare_calls, view):
    """Chained account, benchmark and every overlay share one x-axis.

    A late-starting generation must be padded with None (its inception gap), not
    back-filled and not truncated.
    """
    kw = compare_calls[view]
    n = len(kw["dates"])
    assert n > 0
    assert len(kw["chain_curve"]) == n
    assert len(kw["bench_curve"]) == n
    for ln in kw["cmp_lines"]:
        assert len(ln["values"]) == n, f"{ln['name']} is not on the shared axis"
    assert kw["dates"] == sorted(kw["dates"]), "date axis must be sorted"


@pytest.mark.parametrize("view", ["hd", "biotech"])
def test_a_later_generation_starts_later_than_the_first(compare_calls, view):
    """The None prefix is the whole point of the shared axis — assert it exists."""
    gen_lines = [ln for ln in compare_calls[view]["cmp_lines"] if ln["dash"] == "solid"]
    firsts = [next((i for i, v in enumerate(ln["values"]) if v is not None), None)
              for ln in gen_lines]
    assert firsts[0] == 0, "the first generation starts at the left edge"
    assert any(f is not None and f > 0 for f in firsts[1:]), (
        "at least one later generation must begin after the first (None-padded)"
    )


# ── chained account ───────────────────────────────────────────────────────────

@pytest.mark.parametrize("view,base", [("hd", 2), ("biotech", 5)])
def test_rebalance_markers_are_numbered_from_the_right_generation(compare_calls, view, base):
    """HD hands over to v2, v3 …; biotech to v5, v6 … — the offset is per view."""
    markers = compare_calls[view]["chain_markers"]
    for i, m in enumerate(markers):
        assert m["label"].endswith(f"v{base + i}"), m["label"]
        assert m["date"] in compare_calls[view]["dates"]


@pytest.mark.parametrize("view", ["hd", "biotech"])
def test_alpha_is_cumulative_minus_benchmark(compare_calls, view):
    """The three headline numbers must stay internally consistent."""
    kw = compare_calls[view]
    cum = float(kw["cum_str"].rstrip("%"))
    bench = float(kw["bench_cum_str"].rstrip("%"))
    alpha = float(kw["alpha_str"].rstrip("p"))
    assert alpha == pytest.approx(cum - bench, abs=0.02)


@pytest.mark.parametrize("view", ["hd", "biotech"])
def test_nav_gain_and_cumulative_agree_with_the_starting_capital(compare_calls, view):
    kw = compare_calls[view]
    cap = float(kw["capital_str"].replace(",", ""))
    nav = float(kw["nav_str"].split()[-1].replace(",", ""))
    gain = float(kw["gain_str"].split()[-1].replace(",", ""))
    cum = float(kw["cum_str"].rstrip("%"))
    assert abs(nav - cap) == pytest.approx(gain, abs=1.0)
    assert (nav / cap - 1.0) * 100.0 == pytest.approx(cum, abs=0.02)


@pytest.mark.parametrize("view,currency", [("hd", "HKD"), ("biotech", "USD")])
def test_currency_stays_per_view(compare_calls, view, currency):
    kw = compare_calls[view]
    assert kw["currency"] == currency
    assert kw["nav_str"].startswith(currency)
    assert currency in kw["gain_str"]


def test_six_kpi_tiles_in_both_views(compare_calls):
    for view in ("hd", "biotech"):
        assert len(compare_calls[view]["kpi_tiles"]) == 6, view
