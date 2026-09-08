"""AI Valuation Scanner — nav shim.

Body: lib/views/valuation.py (shared with 5_Valuation_Scanner.py). Kept as its
own file so `st.Page(..., url_path="AI_Valuation_Scanner")` and its deep-links
are unchanged.
"""

from lib.views import valuation as valuation_view

valuation_view.render("ai")
