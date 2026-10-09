"""Cloud packaging boundaries and page render; interactive checks use the browser."""
import hashlib
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
from lib.storage_research_panel import BUNDLE, MODULES, _json_script, build_doc, revision


def test_release_manifest_and_source_boundary():
    manifest = json.loads((BUNDLE / "manifest.json").read_text())
    assert manifest["entities"] == 114
    for rel, sha in manifest["files"].items():
        path = BUNDLE / rel
        assert hashlib.sha256(path.read_bytes()).hexdigest() == sha
        assert not re.search(r"/Users/|file://|127\.0\.0\.1|metrics-audit\.json|wind-probe\.json", path.read_text())


def test_references_resolve_and_financials_have_public_primary_sources():
    modules = {k: json.loads((BUNDLE / "data" / f"{k}.json").read_text()) for k in MODULES}
    sources = {s["id"]: s for m in modules.values() for s in m["sources"]}
    assert len(sources) == 81
    assert all(s["url"] is None or s["url"].startswith("https://") for s in sources.values())
    def walk(x):
        if isinstance(x, dict):
            for key, val in x.items():
                if key == "sourceIds":
                    assert set(val) <= sources.keys()
                walk(val)
        elif isinstance(x, list):
            for val in x:
                walk(val)
    walk(modules)
    finance = modules["finance"]
    for company in finance["companies"]:
        for metric in company["latest"]["metrics"]:
            assert any(sources[s]["url"] for s in metric["sourceIds"])
        for period in company["annual"] + company["interim"]:
            assert any(sources[s]["url"] for s in period["sourceIds"])


def test_document_has_no_runtime_local_dependencies():
    doc = build_doc(revision())
    assert 'src="diagram.html"' not in doc
    assert 'src="app.js"' not in doc
    assert "assets/fonts/" not in doc
    assert "location.origin" not in doc
    assert "new URL(document.baseURI).origin" in doc
    for module in MODULES:
        assert f'id="storage-data-{module}"' in doc
    nested = html.unescape(re.search(r'srcdoc="([^"]*)"', doc).group(1))
    assert "fitLaneLabels" in nested
    assert 'app/static/echarts.min.js' in nested
    assert 'assets/fonts/' not in nested
    assert "storageHistoryMain" in nested


def test_json_script_cannot_break_out():
    value = {"text": '</script><script>alert(1)</script>\u2028'}
    encoded = _json_script(value)
    assert "</script>" not in encoded
    assert json.loads(encoded) == value


def test_streamlit_page_renders():
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_file(str(ROOT / "app/pages/a6_ai_storage.py"), default_timeout=20).run()
    assert not app.exception


def test_storage_is_registered_under_ai_and_overview_links_to_it():
    nav = (ROOT / "app/streamlit_app.py").read_text()
    ai_group = nav.split('_t("AI", "AI 人工智能"): [', 1)[1].split('],', 1)[0]
    assert "ai_storage," in ai_group
    assert 'url_path="AI_Storage"' in nav
    overview = (ROOT / "app/pages/a2_ai_overview.py").read_text()
    assert "dram_cycles_panel.render()" not in overview
    assert '"pages/a6_ai_storage.py"' in overview
