"""The language switch must not be a page reload.

R3 audit §8.4. `render_lang_toggle` rendered two `<a href="?lang=…"
target="_self">` anchors, so switching language navigated the browser. Streamlit
builds a fresh session on navigation, so every unrelated `st.session_state` entry
— an open expander, the picked ticker, a slider position — was destroyed as
collateral. It is a widget now: `set_lang()` writes session_state plus the query
param and calls `st.rerun()`, which keeps the session.

These tests run a tiny app that owns one unrelated session_state key, so what
they assert is exactly the regression: the key survives, the language changes,
and `?lang=` deep links still win on first load.
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
_APP = REPO_ROOT / "app"
if str(_APP) not in sys.path:
    sys.path.insert(0, str(_APP))

_SCRIPT = textwrap.dedent(
    """
    import sys
    sys.path.insert(0, {app!r})
    import streamlit as st
    from lib import i18n

    # An unrelated bit of session state, the kind a full reload used to destroy.
    st.session_state.setdefault("unrelated_state", "keep-me")
    st.session_state.setdefault("run_count", 0)
    st.session_state["run_count"] += 1

    i18n.render_lang_toggle()
    st.text(i18n.get_lang())
    """
).format(app=str(_APP))


@pytest.fixture()
def app(tmp_path):
    from streamlit.testing.v1 import AppTest  # noqa: PLC0415

    script = tmp_path / "lang_app.py"
    script.write_text(_SCRIPT, encoding="utf-8")
    return lambda **qp: _run(AppTest, script, qp)


def _qp(at, key):
    """AppTest.query_params returns list-valued params; collapse for comparison."""
    v = at.query_params.get(key)
    return v[0] if isinstance(v, list) and v else v


def _run(AppTest, script, qp):
    at = AppTest.from_file(str(script), default_timeout=60)
    for k, v in qp.items():
        at.query_params[k] = v
    at.run()
    return at


def test_toggle_is_a_widget_not_an_anchor(app):
    at = app()
    assert not at.exception
    assert len(at.segmented_control) == 1, "the language switch must be a real widget"
    assert list(at.segmented_control[0].options) == ["中", "EN"]


def test_toggling_changes_the_language(app):
    at = app()
    assert at.text[0].value == "zh"

    at.segmented_control[0].set_value("EN").run()

    assert not at.exception
    assert at.session_state["lang"] == "en"
    assert at.text[0].value == "en"


def test_toggling_preserves_unrelated_session_state(app):
    """The whole point. A full reload wiped these; a rerun must not."""
    at = app()
    at.session_state["picked_ticker"] = "NVDA"      # set by some other widget
    assert at.session_state["unrelated_state"] == "keep-me"

    at.segmented_control[0].set_value("EN").run()

    assert at.session_state["lang"] == "en"
    assert at.session_state["unrelated_state"] == "keep-me"
    assert at.session_state["picked_ticker"] == "NVDA"


def test_toggling_writes_the_query_param_so_the_url_stays_shareable(app):
    at = app()
    at.segmented_control[0].set_value("EN").run()
    assert _qp(at, "lang") == "en"


def test_toggling_leaves_sibling_query_params_alone(app):
    """`?ticker=` must survive the switch — the anchor needed doseq for this."""
    at = app(ticker="NVDA", lang="zh")
    at.segmented_control[0].set_value("EN").run()

    assert at.session_state["lang"] == "en"
    assert _qp(at, "ticker") == "NVDA"
    assert _qp(at, "lang") == "en"


def test_a_lang_deep_link_still_wins_on_first_load(app):
    """init_lang() must keep honouring `?lang=` — the widget must not fight it."""
    at = app(lang="en")
    assert not at.exception
    assert at.session_state["lang"] == "en"
    assert at.text[0].value == "en"
    assert at.segmented_control[0].value == "EN", "widget must reflect the deep link"


def test_a_deep_link_does_not_trigger_an_extra_rerun_loop(app):
    """Widget-vs-URL disagreement must resolve without ping-ponging."""
    at = app(lang="en")
    assert at.session_state["run_count"] == 1, (
        f"page ran {at.session_state['run_count']}x for one load — the toggle is "
        "fighting init_lang()"
    )


def test_toggling_back_returns_to_chinese(app):
    at = app(lang="en")
    at.segmented_control[0].set_value("中").run()
    assert at.session_state["lang"] == "zh"
    assert _qp(at, "lang") == "zh"
    assert at.text[0].value == "zh"


def test_set_lang_ignores_a_code_with_no_locale_table(tmp_path):
    """A bad code must leave the language alone, not blank every string.

    `t()` would fall through to the key itself for an unknown language, so
    accepting one would render the whole UI as raw dotted keys.
    """
    from streamlit.testing.v1 import AppTest  # noqa: PLC0415

    script = tmp_path / "bad_lang.py"
    script.write_text(textwrap.dedent(
        """
        import sys
        sys.path.insert(0, {app!r})
        import streamlit as st
        from lib import i18n

        i18n.init_lang()
        i18n.set_lang("de")          # no locale table -> must be a no-op
        st.text(i18n.get_lang())
        st.text(i18n.t("common.col.ticker"))
        """
    ).format(app=str(_APP)), encoding="utf-8")

    at = AppTest.from_file(str(script), default_timeout=60)
    at.run()

    assert not at.exception, "set_lang must not raise on an unknown code"
    assert at.text[0].value == "zh", "language must be unchanged"
    assert at.text[1].value != "common.col.ticker", "strings must still resolve"
