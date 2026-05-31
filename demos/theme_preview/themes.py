"""Three candidate visual themes for invest-dashboard.

Each theme is a dict with:
- name / tagline / palette swatches (for the picker UI)
- css: a full <style> string injected via st.markdown(unsafe_allow_html=True)
- plotly_template: dict patch applied to fig.update_layout()
"""
from __future__ import annotations

# Shared CSS reset applied before each theme (kills Streamlit default chrome
# we don't want and makes overrides cleaner).
RESET = """
/* hide hamburger + footer + deploy badge */
#MainMenu, footer, [data-testid="stStatusWidget"], [data-testid="stDeployButton"] { visibility: hidden; }
/* tighten container */
.block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1280px; }
/* remove default st.metric label uppercase / heavy bg */
[data-testid="stMetric"] { background: transparent !important; padding: 0.25rem 0 !important; }
/* themed HTML table — shared structure, theme overrides colors */
.themed-table-wrap { width: 100%; overflow-x: auto; margin: 0.4rem 0 0.6rem 0; }
.themed-table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }
.themed-table th { text-align: left; padding: 10px 14px; font-size: 0.74rem; text-transform: uppercase; letter-spacing: 0.9px; }
.themed-table td { padding: 10px 14px; font-size: 0.92rem; }
.themed-table td.num { text-align: right; font-variant-numeric: tabular-nums; }
.themed-table th.num { text-align: right; }
"""

THEMES = {
    "A": {
        "name": "Bloomberg Terminal",
        "tagline": "深色 · 高密度 · 数据为王 (sell-side trader 7am 屏)",
        "swatches": ["#0a0e1a", "#ff8c00", "#00d4ff", "#00ff7f", "#ff3b30"],
        "css": RESET + """
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Serif:wght@500;600&display=swap');

html, body, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {
  background: #0a0e1a !important;
  color: #d4d4d8 !important;
  font-family: 'IBM Plex Sans', -apple-system, sans-serif !important;
}
[data-testid="stSidebar"] { background: #0f1525 !important; border-right: 1px solid #1f2937; }
h1, h2, h3, h4 {
  font-family: 'IBM Plex Serif', Georgia, serif !important;
  font-weight: 600 !important;
  letter-spacing: 0.4px;
  color: #ff8c00 !important;
}
h1 { font-size: 1.7rem !important; border-bottom: 1px solid #2a3142; padding-bottom: 0.5rem; margin-bottom: 0.3rem; }
h2 { font-size: 1.15rem !important; color: #f4f4f5 !important; text-transform: uppercase; letter-spacing: 1.4px; margin-top: 1.4rem !important; }
h3 { font-size: 0.95rem !important; color: #a1a1aa !important; text-transform: uppercase; letter-spacing: 1.2px; }
[data-testid="stMetricValue"] {
  font-family: 'IBM Plex Mono', monospace !important;
  font-variant-numeric: tabular-nums;
  font-size: 1.55rem !important;
  color: #f4f4f5 !important;
  font-weight: 500;
}
[data-testid="stMetricLabel"] {
  font-family: 'IBM Plex Sans', sans-serif !important;
  text-transform: uppercase;
  font-size: 0.7rem !important;
  letter-spacing: 1.3px;
  color: #71717a !important;
}
[data-testid="stMetricDelta"] { font-family: 'IBM Plex Mono', monospace !important; font-size: 0.85rem !important; }
[data-testid="stTable"] table, [data-testid="stDataFrame"] {
  font-family: 'IBM Plex Mono', monospace !important;
  font-variant-numeric: tabular-nums;
}
[data-testid="stDataFrame"] [role="columnheader"] {
  background: #0f1525 !important;
  color: #ff8c00 !important;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  font-size: 0.72rem !important;
  border-bottom: 1px solid #2a3142 !important;
}
.stCaption, [data-testid="stCaptionContainer"] { color: #71717a !important; font-size: 0.78rem !important; letter-spacing: 0.3px; }
hr { border-color: #1f2937 !important; }
.stButton button {
  background: #1a1f2e !important; border: 1px solid #ff8c00 !important;
  color: #ff8c00 !important; font-family: 'IBM Plex Sans' !important;
  text-transform: uppercase; letter-spacing: 1px; font-size: 0.75rem !important;
  border-radius: 0 !important;
}
.themed-table { background: #0f1525; color: #d4d4d8; font-family: 'IBM Plex Mono', monospace; border: 1px solid #1f2937; }
.themed-table thead { background: #0a0e1a; }
.themed-table th { color: #ff8c00; border-bottom: 1px solid #2a3142; font-family: 'IBM Plex Sans', sans-serif; }
.themed-table tbody tr { border-bottom: 1px solid #1a1f2e; }
.themed-table tbody tr:nth-child(even) { background: #11172a; }
.themed-table tbody tr:hover { background: #1a2138; }
""",
        "plotly_template": {
            "paper_bgcolor": "#0a0e1a",
            "plot_bgcolor": "#0a0e1a",
            "font": {"family": "IBM Plex Mono, monospace", "color": "#d4d4d8", "size": 11},
            "xaxis": {"gridcolor": "#1f2937", "linecolor": "#2a3142", "zerolinecolor": "#2a3142"},
            "yaxis": {"gridcolor": "#1f2937", "linecolor": "#2a3142", "zerolinecolor": "#2a3142"},
            "colorway": ["#ff8c00", "#00d4ff", "#00ff7f", "#ff3b30", "#a78bfa"],
        },
        "accent_up": "#00ff7f",
        "accent_down": "#ff3b30",
        "use_emoji": False,
        "up_symbol": "▲",
        "down_symbol": "▼",
    },

    "B": {
        "name": "Financial Times × Inter",
        "tagline": "FT 米色 + 红 + Inter 全字体（保留 editorial 感但更现代）",
        "swatches": ["#fff1e5", "#990f3d", "#33302e", "#0d7680", "#cc0000"],
        "css": RESET + """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [data-testid="stAppViewContainer"] {
  background: #fff1e5 !important;
  color: #33302e !important;
  font-family: 'Inter', -apple-system, sans-serif !important;
  font-feature-settings: 'cv11', 'ss01';
}
[data-testid="stSidebar"] {
  background: #f2dfce !important;
  border-right: 1px solid #d9c7b6;
}
[data-testid="stSidebar"] * { color: #33302e !important; font-family: 'Inter', sans-serif !important; }
h1, h2, h3, h4 {
  font-family: 'Inter', sans-serif !important;
  color: #33302e !important;
  font-weight: 700 !important;
  letter-spacing: -0.025em;
}
h1 {
  font-size: 2rem !important;
  border-bottom: 3px double #990f3d;
  padding-bottom: 0.6rem;
  margin-bottom: 0.3rem;
}
h2 {
  font-size: 1.3rem !important;
  margin-top: 1.6rem !important;
  border-left: 4px solid #990f3d;
  padding-left: 0.8rem;
  font-weight: 700 !important;
}
h3 {
  font-size: 0.92rem !important;
  color: #6b6661 !important;
  font-weight: 600 !important;
  text-transform: uppercase;
  letter-spacing: 0.8px;
}
[data-testid="stMetricValue"] {
  font-family: 'Inter', sans-serif !important;
  font-feature-settings: 'tnum';
  font-variant-numeric: tabular-nums;
  font-size: 1.7rem !important;
  color: #33302e !important;
  font-weight: 700;
  letter-spacing: -0.02em;
}
[data-testid="stMetricLabel"] {
  font-family: 'Inter', sans-serif !important;
  font-size: 0.78rem !important;
  color: #6b6661 !important;
  font-weight: 500;
  letter-spacing: 0.2px;
}
[data-testid="stMetricDelta"] {
  font-family: 'Inter', sans-serif !important;
  font-feature-settings: 'tnum';
  font-size: 0.85rem !important;
  font-weight: 500;
}
.stCaption, [data-testid="stCaptionContainer"] {
  color: #6b6661 !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 0.85rem !important;
  font-weight: 400;
}
hr { border-color: #d9c7b6 !important; }
.stButton button {
  background: #990f3d !important; border: none !important; color: #fff1e5 !important;
  font-family: 'Inter', sans-serif !important; font-weight: 600 !important;
  border-radius: 2px !important;
}
.themed-table {
  background: #fdf6ec; color: #33302e;
  font-family: 'Inter', sans-serif;
  font-feature-settings: 'tnum';
  border: 1px solid #d9c7b6;
}
.themed-table thead { background: #f2dfce; }
.themed-table th {
  color: #990f3d;
  border-bottom: 2px solid #990f3d;
  font-family: 'Inter', sans-serif;
  font-weight: 600;
}
.themed-table tbody tr { border-bottom: 1px solid #e8dccc; }
.themed-table tbody tr:nth-child(even) { background: #f9ecdc; }
.themed-table tbody tr:hover { background: #f5e3cc; }
""",
        "plotly_template": {
            "paper_bgcolor": "#fdf6ec",
            "plot_bgcolor": "#fdf6ec",
            "font": {"family": "JetBrains Mono, monospace", "color": "#33302e", "size": 11},
            "xaxis": {"gridcolor": "#e8dccc", "linecolor": "#d9c7b6", "zerolinecolor": "#c9b8a6"},
            "yaxis": {"gridcolor": "#e8dccc", "linecolor": "#d9c7b6", "zerolinecolor": "#c9b8a6"},
            "colorway": ["#990f3d", "#0d7680", "#996b1f", "#5c2d91", "#cc7700"],
        },
        "accent_up": "#0d7680",
        "accent_down": "#cc0000",
        "use_emoji": False,
        "up_symbol": "▲",
        "down_symbol": "▼",
    },

    "C": {
        "name": "Stripe / Linear",
        "tagline": "现代 institutional · clean · 适合 demo / 路演",
        "swatches": ["#0c111d", "#635bff", "#06b6d4", "#22c55e", "#ef4444"],
        "css": RESET + """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [data-testid="stAppViewContainer"] {
  background: #0c111d !important;
  color: #cdd5e0 !important;
  font-family: 'Inter', -apple-system, sans-serif !important;
  font-feature-settings: 'cv11', 'ss01', 'ss03';
}
[data-testid="stSidebar"] {
  background: #11172a !important;
  border-right: 1px solid #1f2937;
}
h1, h2, h3, h4 {
  font-family: 'Inter', sans-serif !important;
  font-weight: 700 !important;
  letter-spacing: -0.028em !important;
  color: #ffffff !important;
}
h1 { font-size: 1.9rem !important; margin-bottom: 0.3rem; background: linear-gradient(90deg, #fff 0%, #a5b4fc 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
h2 { font-size: 1.25rem !important; margin-top: 1.6rem !important; color: #e5e7eb !important; font-weight: 600 !important; }
h3 { font-size: 0.92rem !important; color: #9ca3af !important; font-weight: 500 !important; text-transform: uppercase; letter-spacing: 0.8px; }
[data-testid="stMetric"] {
  background: linear-gradient(135deg, rgba(99,91,255,0.06) 0%, rgba(99,91,255,0.01) 100%) !important;
  border: 1px solid #1f2937 !important;
  border-radius: 10px !important;
  padding: 0.9rem 1.1rem !important;
}
[data-testid="stMetricValue"] {
  font-family: 'Inter', sans-serif !important;
  font-feature-settings: 'tnum';
  font-variant-numeric: tabular-nums;
  font-size: 1.65rem !important;
  font-weight: 700 !important;
  color: #ffffff !important;
  letter-spacing: -0.02em;
}
[data-testid="stMetricLabel"] {
  font-family: 'Inter', sans-serif !important;
  font-size: 0.78rem !important;
  color: #9ca3af !important;
  font-weight: 500 !important;
}
[data-testid="stMetricDelta"] {
  font-family: 'Inter', sans-serif !important;
  font-feature-settings: 'tnum';
  font-size: 0.85rem !important;
  font-weight: 500;
}
[data-testid="stTable"] table, [data-testid="stDataFrame"] {
  font-family: 'Inter', sans-serif !important;
  font-feature-settings: 'tnum';
  font-variant-numeric: tabular-nums;
}
[data-testid="stDataFrame"] [role="columnheader"] {
  background: #11172a !important;
  color: #9ca3af !important;
  font-weight: 600 !important;
  font-size: 0.78rem !important;
  border-bottom: 1px solid #1f2937 !important;
}
[data-testid="stDataFrame"] [role="row"]:hover { background: rgba(99,91,255,0.05) !important; }
.stCaption, [data-testid="stCaptionContainer"] {
  color: #6b7280 !important;
  font-size: 0.82rem !important;
}
hr { border-color: #1f2937 !important; }
.stButton button {
  background: #635bff !important; border: none !important; color: #fff !important;
  font-family: 'Inter', sans-serif !important; font-weight: 600 !important;
  border-radius: 8px !important;
  box-shadow: 0 1px 0 rgba(255,255,255,0.06), 0 2px 8px rgba(99,91,255,0.3);
}
.themed-table { background: #11172a; color: #cdd5e0; font-family: 'Inter', sans-serif; border: 1px solid #1f2937; border-radius: 10px; overflow: hidden; }
.themed-table thead { background: rgba(99,91,255,0.08); }
.themed-table th { color: #a5b4fc; border-bottom: 1px solid #1f2937; font-weight: 600; }
.themed-table tbody tr { border-bottom: 1px solid #1a2138; }
.themed-table tbody tr:hover { background: rgba(99,91,255,0.06); }
""",
        "plotly_template": {
            "paper_bgcolor": "#0c111d",
            "plot_bgcolor": "#0c111d",
            "font": {"family": "Inter, sans-serif", "color": "#cdd5e0", "size": 11},
            "xaxis": {"gridcolor": "#1f2937", "linecolor": "#1f2937", "zerolinecolor": "#1f2937"},
            "yaxis": {"gridcolor": "#1f2937", "linecolor": "#1f2937", "zerolinecolor": "#1f2937"},
            "colorway": ["#635bff", "#06b6d4", "#22c55e", "#f59e0b", "#ef4444"],
        },
        "accent_up": "#22c55e",
        "accent_down": "#ef4444",
        "use_emoji": False,
        "up_symbol": "↑",
        "down_symbol": "↓",
    },
}
