"""The FactSet holdings adapter in jobs/build_etf_panel.py.

stockanalysis started 404-ing for every ETF (verified 2026-09-07) and the
barchart fallback returns nothing, so the panel's weights now come from FactSet
Ownership `fund_holdings`, fetched by a Claude session into
`data/external/_factset_raw/etf_holdings_<T>.json` and read here.

What these tests pin is the failure behaviour. The 2026-08-29 incident (R3 audit
item 7) was not a fetch that errored — it was a fetch that quietly returned worse
data and got written anyway. The adapter's job is to make every degradation mode
of a hand-written raw file loud: a truncated fetch, a duplicated row, a missing
weight, or a licensed identifier leaking into a public repo.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "build_etf_panel", REPO_ROOT / "jobs" / "build_etf_panel.py")
bep = importlib.util.module_from_spec(_spec)
sys.modules["build_etf_panel"] = bep
_spec.loader.exec_module(bep)


def _write(tmp_path: Path, ticker: str, holdings: list[dict], **over) -> Path:
    doc = {
        "etf_ticker": ticker,
        "as_of": "2026-08-31",
        "currency": "USD",
        "source": "FactSet_Ownership.fund_holdings topn=ALL",
        "holdings": holdings,
    }
    doc.update(over)
    p = tmp_path / f"etf_holdings_{ticker}.json"
    p.write_text(json.dumps(doc), encoding="utf-8")
    return p


def _h(tkr: str, name: str, w: float) -> dict:
    return {"securityTicker": tkr, "securityName": name, "weightClose": w}


# --- happy path -------------------------------------------------------------

def test_maps_factset_fields_onto_the_holdings_envelope(tmp_path):
    _write(tmp_path, "XLV", [
        _h("JNJ-US", "JOHNSON & JOHNSON  COM", 10.421315180149),
        _h("LLY-US", "ELI LILLY & CO  COM", 74.9009597451818),
        _h("ABBV-US", "ABBVIE INC  COM", 7.37751972896867),
    ])
    env = bep._read_factset_holdings("XLV", tmp_path)

    assert env["_source"] == "factset:fund_holdings"
    assert env["_as_of"] == "2026-08-31"
    assert env["_reliability"] == "HIGH"
    assert env["_partial"] is False

    rows = env["holdings"]
    assert [r["symbol"] for r in rows] == ["LLY", "JNJ", "ABBV"], "sorted by weight desc"
    assert [r["rank"] for r in rows] == [1, 2, 3], "rank follows the sorted order"
    assert rows[0]["weight_pct"] == pytest.approx(74.901, abs=1e-3)
    assert rows[0]["name"] == "Eli Lilly & Co Com"


def test_a_non_us_line_keeps_its_region_suffix(tmp_path):
    """`-US` is stripped to match the panel's symbol convention; anything else
    stays, because a bare foreign ticker would collide with a US one."""
    _write(tmp_path, "IBB", [
        _h("AMGN-US", "AMGEN INC  COM", 60.0),
        _h("AZN-GB", "ASTRAZENECA PLC  ORD", 30.0),
    ])
    rows = bep._read_factset_holdings("IBB", tmp_path)["holdings"]
    assert [r["symbol"] for r in rows] == ["AMGN", "AZN-GB"]


def test_known_mixed_case_brands_survive_the_title_casing(tmp_path):
    _write(tmp_path, "XBI", [_h("ABBV-US", "ABBVIE INC  COM", 60.0),
                             _h("BNTX-US", "BIONTECH SE  ADR", 35.0)])
    rows = bep._read_factset_holdings("XBI", tmp_path)["holdings"]
    names = {r["symbol"]: r["name"] for r in rows}
    assert names["ABBV"] == "AbbVie Inc Com"
    assert names["BNTX"] == "BioNTech SE ADR", "legal form + ADR stay capitalised, brand keeps its case"


# --- the failure modes that matter -----------------------------------------

def test_a_missing_file_says_how_to_produce_it(tmp_path):
    with pytest.raises(FileNotFoundError) as e:
        bep._read_factset_holdings("XLV", tmp_path)
    assert "fund_holdings" in str(e.value), "the error must name the fetch to run"


def test_a_licensed_identifier_in_the_raw_file_is_refused(tmp_path):
    """This repo is public. fsymId / adjMarketValue are licensed FactSet data and
    must never reach a committed file, so the adapter refuses the whole build."""
    _write(tmp_path, "XLV", [
        {"securityTicker": "LLY-US", "securityName": "ELI LILLY & CO  COM",
         "weightClose": 90.0, "fsymId": "MWPZX1-S"},
    ])
    with pytest.raises(ValueError, match="licensed FactSet fields"):
        bep._read_factset_holdings("XLV", tmp_path)


def test_a_row_without_a_weight_is_refused(tmp_path):
    """FactSet weights every line, so a hole is a transcription error, not data."""
    _write(tmp_path, "XLV", [_h("LLY-US", "ELI LILLY & CO  COM", 90.0),
                             {"securityTicker": "JNJ-US", "securityName": "JOHNSON & JOHNSON  COM"}])
    with pytest.raises(ValueError, match="has no weight"):
        bep._read_factset_holdings("XLV", tmp_path)


def test_a_row_without_a_ticker_is_refused(tmp_path):
    _write(tmp_path, "XLV", [_h("LLY-US", "ELI LILLY & CO  COM", 90.0),
                             {"securityName": "EQUITY OTHER", "weightClose": 1.0}])
    with pytest.raises(ValueError, match="has no ticker"):
        bep._read_factset_holdings("XLV", tmp_path)


def test_a_duplicated_symbol_is_refused(tmp_path):
    """Two lines for one security double-count its weight in every downstream sum."""
    _write(tmp_path, "XLV", [_h("LLY-US", "ELI LILLY & CO  COM", 45.0),
                             _h("LLY-US", "ELI LILLY & CO  COM", 45.0)])
    with pytest.raises(ValueError, match="duplicate symbol"):
        bep._read_factset_holdings("XLV", tmp_path)


def test_a_truncated_fetch_is_refused(tmp_path):
    """The realistic transcription failure: the fetcher stops early, so the file
    parses fine and every row is real — but the panel would show a fund that is
    30% invested. Only the total catches this."""
    _write(tmp_path, "VHT", [_h("LLY-US", "ELI LILLY & CO  COM", 12.8),
                             _h("JNJ-US", "JOHNSON & JOHNSON  COM", 9.0)])
    with pytest.raises(ValueError, match="outside"):
        bep._read_factset_holdings("VHT", tmp_path)


def test_weights_over_the_ceiling_are_refused(tmp_path):
    _write(tmp_path, "XLV", [_h("LLY-US", "ELI LILLY & CO  COM", 60.0),
                             _h("JNJ-US", "JOHNSON & JOHNSON  COM", 60.0)])
    with pytest.raises(ValueError, match="outside"):
        bep._read_factset_holdings("XLV", tmp_path)


def test_an_empty_holdings_list_is_refused(tmp_path):
    _write(tmp_path, "XLV", [])
    with pytest.raises(ValueError, match="refusing to build a weightless panel"):
        bep._read_factset_holdings("XLV", tmp_path)


def test_a_missing_as_of_is_refused(tmp_path):
    """`as_of` becomes the panel's holdings date; guessing it would date a stale
    snapshot as today's."""
    _write(tmp_path, "XLV", [_h("LLY-US", "ELI LILLY & CO  COM", 90.0)], as_of=None)
    with pytest.raises(ValueError, match="as_of"):
        bep._read_factset_holdings("XLV", tmp_path)


# --- the real fetched files -------------------------------------------------

def test_every_curated_etf_has_a_raw_file_that_parses(tmp_path):
    """Guards the committed inputs, not a fixture: each ETF on the page must have
    a FactSet file that clears every rule above."""
    raw = bep.FACTSET_RAW_DIR
    if not raw.exists():
        pytest.skip("FactSet raw files not fetched in this checkout")
    for ticker, _sub in bep.ETF_LIST:
        env = bep._read_factset_holdings(ticker, raw)
        assert env["holdings"], ticker
        assert all(r["weight_pct"] is not None for r in env["holdings"]), ticker


def test_no_raw_file_carries_a_licensed_identifier():
    """A second, blunter pass over the committed files — the adapter only checks
    the first row, this checks the whole text."""
    raw = bep.FACTSET_RAW_DIR
    if not raw.exists():
        pytest.skip("FactSet raw files not fetched in this checkout")
    for p in sorted(raw.glob("etf_holdings_*.json")):
        blob = p.read_text(encoding="utf-8")
        for banned in bep._FACTSET_BANNED_KEYS:
            assert banned not in blob, f"{p.name} leaks {banned}"
