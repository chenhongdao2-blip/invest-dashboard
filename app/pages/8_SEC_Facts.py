"""HC SEC Company Facts — nav shim.

Body: lib/views/sec_facts.py (shared with a5_ai_sec.py). Kept as its own file so
`st.Page(..., url_path="SEC_Facts")` and its `?ticker=` deep-links are unchanged.
"""

from lib.views import sec_facts as sec_facts_view

sec_facts_view.render("healthcare")
