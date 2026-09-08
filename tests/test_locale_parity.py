"""The two locale tables must carry identical key sets.

R3 audit §7 measured 1,157 keys across `lib/locales/{en,zh}.py` +
`pages_{en,zh}.py` with ZERO drift and called the design correct — the finding
was that pages BYPASS it with inline `X if _prefer_cn else Y`. Moving the
Strategy Picks label dicts in means the tables now carry strings that used to be
maintained as literal pairs, so the no-drift property is worth an actual test
rather than a measurement someone took once.

A missing key does not crash: `i18n.t` falls back to the default language and
then to the key string itself, so drift shows up as an English label in a Chinese
table (or a raw `picks.sc.hd.footnote` in the UI) — silent, and exactly the kind
of thing a test should catch instead of a reader.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
_APP = REPO_ROOT / "app"
if str(_APP) not in sys.path:
    sys.path.insert(0, str(_APP))


@pytest.mark.parametrize("module_pair", [("en", "zh"), ("pages_en", "pages_zh")])
def test_locale_modules_have_identical_key_sets(module_pair):
    import importlib  # noqa: PLC0415

    en_name, zh_name = module_pair
    en = importlib.import_module(f"lib.locales.{en_name}").STRINGS
    zh = importlib.import_module(f"lib.locales.{zh_name}").STRINGS

    only_en = sorted(set(en) - set(zh))
    only_zh = sorted(set(zh) - set(en))
    assert not only_en, f"{en_name} has keys {zh_name} lacks: {only_en}"
    assert not only_zh, f"{zh_name} has keys {en_name} lacks: {only_zh}"


def test_merged_tables_have_identical_key_sets():
    """What i18n.t actually reads: en.py + pages_en.py vs zh.py + pages_zh.py."""
    from lib.locales import en, zh, pages_en, pages_zh  # noqa: PLC0415

    merged_en = {**en.STRINGS, **pages_en.STRINGS}
    merged_zh = {**zh.STRINGS, **pages_zh.STRINGS}

    assert set(merged_en) == set(merged_zh), (
        f"only in en: {sorted(set(merged_en) - set(merged_zh))}\n"
        f"only in zh: {sorted(set(merged_zh) - set(merged_en))}"
    )
    assert len(merged_en) >= 1157, (
        f"merged table shrank to {len(merged_en)} keys — the audit counted 1,157; "
        "keys should only ever be added"
    )


def test_no_key_maps_to_none_or_a_non_string():
    from lib.locales import en, zh, pages_en, pages_zh  # noqa: PLC0415

    for name, table in (("en", en.STRINGS), ("zh", zh.STRINGS),
                        ("pages_en", pages_en.STRINGS), ("pages_zh", pages_zh.STRINGS)):
        bad = {k: v for k, v in table.items() if not isinstance(v, str)}
        assert not bad, f"{name} has non-string values: {bad}"


def test_the_strategy_picks_label_blocks_resolve_in_both_languages():
    """Every field the picks / scorecard tables read must exist in both tables.

    These are the keys moved out of app/pages/4_Strategy_Picks.py. An absent key
    would render as the literal key string in the table header.
    """
    from lib.locales import pages_en, pages_zh  # noqa: PLC0415

    tbl_fields = (
        "col_rank", "col_tick", "col_name", "col_score", "col_weight", "col_price",
        "col_d1", "col_d5", "col_m1", "col_ytd", "col_since", "col_spark",
        "nm_label", "footnote", "brand",
    )
    sc_fields = (
        "col_num", "col_held", "col_tick", "col_name", "col_ta", "col_final",
        "col_seg", "col_driver", "nm_label", "sum_top20", "sum_pool", "sum_unheld",
        "sum_diff", "sum_diff_note", "sum_n_suffix", "footnote", "brand",
    )
    expected = {f"picks.tbl.{f}" for f in tbl_fields}
    expected |= {f"picks.sc.hd.{f}" for f in sc_fields}
    expected |= {f"picks.sc.bio.{f}" for f in sc_fields}
    expected |= {f"picks.sc.hd.sub_{c}" for c in ("gov", "fin", "moat")}

    for name, table in (("pages_en", pages_en.STRINGS), ("pages_zh", pages_zh.STRINGS)):
        missing = expected - set(table)
        assert not missing, f"{name} is missing {sorted(missing)}"


def test_the_page_no_longer_hand_writes_those_label_dicts():
    """Guard the move itself — the inline ternary block must not come back."""
    src = (_APP / "pages" / "4_Strategy_Picks.py").read_text(encoding="utf-8")
    assert "_prefer_cn2" not in src, (
        "4_Strategy_Picks.py reintroduced an inline `_prefer_cn2` label block; "
        "the strings belong in lib/locales/pages_{en,zh}.py"
    )
    assert '_label_block("picks.tbl"' in src
    assert '_label_block("picks.sc.hd"' in src
    assert '_label_block("picks.sc.bio"' in src
