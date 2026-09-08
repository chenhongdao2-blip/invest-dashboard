"""HC Valuation Scanner — nav shim.

Body: lib/views/valuation.py (shared with a4_ai_valuation.py). Kept as its own
file so `st.Page(..., url_path="Valuation_Scanner")` and its deep-links are
unchanged.
"""

from lib.views import valuation as valuation_view

valuation_view.render("healthcare")
