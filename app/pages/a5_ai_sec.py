"""AI SEC Company Facts — nav shim.

Body: lib/views/sec_facts.py (shared with 8_SEC_Facts.py). Kept as its own file
so `st.Page(..., url_path="AI_SEC_Facts")` and its `?ticker=` deep-links are
unchanged.

US AI tickers auto-enter the SEC pool via jobs/fetch_sec_facts.py; until that
fetch lands the page is empty-data safe (empty pool → info prompt; un-fetched
ticker → the standard "not cached yet" warning).
"""

from lib.views import sec_facts as sec_facts_view

sec_facts_view.render("ai")
