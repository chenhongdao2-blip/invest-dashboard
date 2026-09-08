"""AI Sector Heatmap — nav shim.

Body: lib/views/heatmap.py (shared with 3_Sector_Heatmap.py). Kept as its own
file so `st.Page(..., url_path="AI_Sector_Heatmap")` and its deep-links are
unchanged.
"""

from lib.views import heatmap

heatmap.render("ai")
