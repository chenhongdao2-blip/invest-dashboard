"""HC Sector Heatmap — nav shim.

Body: lib/views/heatmap.py (shared with a3_ai_heatmap.py). Kept as its own file
so `st.Page(..., url_path="Sector_Heatmap")` and its deep-links are unchanged.
"""

from lib.views import heatmap

heatmap.render("healthcare")
