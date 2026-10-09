"""Self-contained research document; no localhost server or evidence-file upload.

Relative static URLs preserve Streamlit Cloud's /~/+/ proxy prefix, matching
the existing DRAM renderer. Both documents inherit the same origin for their
strict source-window + origin checked research-card message bridge.
"""
from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path

import streamlit as st

BUNDLE = Path(__file__).resolve().parents[1] / "assets" / "storage_research"
MODULES = ("history", "routes", "finance", "research")


def _json_script(value) -> str:
    return json.dumps(value, ensure_ascii=False).replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def revision() -> str:
    files = sorted(p for p in BUNDLE.rglob("*") if p.is_file())
    return hashlib.sha256(b"".join(p.read_bytes() for p in files)).hexdigest()


@st.cache_data(show_spinner=False)
def build_doc(content_revision: str) -> str:
    doc = (BUNDLE / "index.html").read_text()
    styles = (BUNDLE / "styles.css").read_text().replace("assets/fonts/", "app/static/fonts/")
    polish = (BUNDLE / "research-polish.css").read_text()
    script = (BUNDLE / "app.js").read_text()
    diagram = (BUNDLE / "diagram.html").read_text()
    # about:srcdoc has a literal location.origin of "null" even though its
    # security origin/base URL is inherited. Use the inherited base origin.
    script = script.replace("location.origin", "new URL(document.baseURI).origin")
    diagram = diagram.replace("location.origin", "new URL(document.baseURI).origin")
    diagram = diagram.replace("assets/fonts/", "app/static/fonts/")
    diagram = diagram.replace("assets/echarts.min.js", "app/static/echarts.min.js")
    diagram = diagram.replace('<link rel="stylesheet" href="research-polish.css">', f"<style>{polish}</style>")
    # Nested iframe can begin at width zero during Streamlit layout.
    start, end = "<script>\n(function(){", "})();\n</script>"
    if diagram.count(start) != 1 or diagram.count(end) != 1:
        raise ValueError("Storage history boot boundary changed")
    diagram = diagram.replace(start, "<script>\nfunction storageHistoryMain(){")
    diagram = diagram.replace(end, "}" + "\n(function ready(){if(typeof echarts==='undefined'||!document.getElementById('chart')?.clientWidth){requestAnimationFrame(ready);return;}storageHistoryMain();})();\n</script>")
    doc = doc.replace('<link rel="stylesheet" href="styles.css">', f"<style>{styles}</style>")
    doc = doc.replace('<link rel="stylesheet" href="research-polish.css">', f"<style>{polish}</style>")
    doc = doc.replace('<script src="assets/echarts.min.js" defer></script>', '<script src="app/static/echarts.min.js"></script>')
    doc = doc.replace('<script src="app.js" defer></script>', '')
    doc = doc.replace('src="diagram.html"', 'srcdoc="' + html.escape(diagram, quote=True) + '"')
    payload = "".join(
        f'<script type="application/json" id="storage-data-{name}">{_json_script(json.loads((BUNDLE / "data" / f"{name}.json").read_text()))}</script>'
        for name in MODULES
    )
    # Keep one scroll viewport so fixed detail drawers are always visible, even
    # when opened from the cash/source sections near the end of the document.
    fit = """<script>
    document.querySelectorAll('a[href^="#"]').forEach(function(a){a.addEventListener('click',function(e){var id=a.getAttribute('href').slice(1);var target=document.getElementById(id);if(target){e.preventDefault();target.scrollIntoView({block:'start'});}});});
    function fitResearchViewport(){try{if(window.frameElement)window.frameElement.style.height=Math.max(560,Math.min(1050,window.parent.innerHeight-130))+'px';}catch(e){}}
    fitResearchViewport();window.addEventListener('resize',fitResearchViewport);
    </script>"""
    boot = "<script>function storageResearchMain(){" + script + "}\n(function ready(){if(typeof echarts==='undefined'||!document.body.clientWidth){requestAnimationFrame(ready);return;}storageResearchMain();})();</script>"
    return doc.replace("</body>", payload + boot + fit + "</body>")


def render() -> None:
    st.iframe(build_doc(revision()), height=1000, tab_index=0)
