"""Global visual theme — CMSI Healthcare Research Portal · Design System v1.0.

Provenance: Claude Design (claude.ai/design) brief, 2026-05-28, after /cccg
quad-advisor review (Codex + Gemini + GLM) converged on:
- CMSI 招商证券 red `#c8102e` (GLM BLOCKER — replaces FT暗酒红)
- Cream `#fff1e5` paper bg (Gemini PASS for healthcare equity research)
- HTML table for Coverage (Codex TOP PICK — solves canvas dark-mode穿透)
- 22 color tokens / 12 type tokens / hairline-only borders / no emoji

Full design language spec: ~/Downloads/DESIGN.md (also in repo at docs/DESIGN.md
once landed).
Mockup reference: ~/Downloads/CMSI Dashboard mockup.html

How CSS reaches the page:
- `.streamlit/config.toml` sets the JS-side palette (cream + CMSI red + official
  `dataframeHeaderBackgroundColor` + `dataframeBorderColor`) so pre-CSS render
  flash matches and Streamlit's internal widget theme picks up the same colors.
- `inject_css()` is called from `ui.sidebar_search()` on every page, AFTER
  `st.set_page_config`. Streamlit reruns the script on every interaction and
  rebuilds DOM, so inject every call — no session-state guard.
- `PLOTLY_LAYOUT` is the dict patch to pass into `fig.update_layout(**...)`.
- Helpers `kpi_metric()` / `section_header()` / `page_header()` emit HTML
  components that replace native `st.metric` / `st.subheader` / `st.title`
  for consistent editorial styling.
"""
from __future__ import annotations

from html import escape as _esc
from textwrap import dedent

import streamlit as st

# ── Color tokens (Claude Design v1.0) ────────────────────────────────────
# Brand
CMSI_RED = "#c8102e"        # 主红 · 表头字 / active / 跌幅 (signal-red 同色但语义分)
CMSI_RED_DEEP = "#9c0e25"   # hover / 章节重号
CMSI_RED_TINT = "#fbe9ec"   # 跌幅 cell heatmap 12%
CMSI_RED_BAND = "#f2dfce"   # 表头米色档

# Paper / surface (cream stack)
PAPER = "#fff1e5"           # body bg 主画布
PAPER_DEEP = "#f9e6d4"      # sidebar / 二级 surface
PAPER_BAND = "#f2dfce"      # 表头 band / KPI label band
PAPER_RULE = "#ebd9c8"      # hairline · 行间分隔
PAPER_EDGE = "#d4c4b0"      # 强 hairline · KPI 卡边

# Ink (text)
INK = "#1a1a1a"             # primary · 数字 / H1
INK_2 = "#4a4a4a"           # secondary · body / 公司名
INK_3 = "#8a8580"           # muted · 副标 / 单位
INK_4 = "#b8b1a8"           # faint · 占位 / disabled

# Up / Down (港美股 convention)
UP = "#0d7680"              # FT teal-green (not vivid #00c853)
UP_DEEP = "#0a5a62"
UP_TINT = "#d9e8e6"
DOWN = "#cc0000"            # signal-red — distinct from brand #c8102e
DOWN_DEEP = "#a30000"
DOWN_TINT = "#f7d9d9"
FLAT = "#8a8580"

# Sector accents (muted FT palette)
SECTOR_PALETTE = ["#c8102e", "#0d7680", "#a07a2c", "#4a6fa5",
                  "#8b3a62", "#5d7c3a", "#6b4423", "#4a4a4a"]

# Aliases kept for backward compat with prior imports
BG = PAPER
BG_ALT = PAPER_BAND
TABLE_BG = PAPER
TABLE_ALT = PAPER_DEEP
BORDER = PAPER_EDGE
TEXT = INK
TEXT_MUTED = INK_3
PRIMARY = CMSI_RED

# ── Font stack ───────────────────────────────────────────────────────────
FONT_STACK = (
    "'Inter', 'PingFang SC', 'Hiragino Sans GB', 'Noto Sans SC', "
    "'Microsoft YaHei', -apple-system, BlinkMacSystemFont, sans-serif"
)
FONT_MONO = "'JetBrains Mono', 'IBM Plex Mono', 'SF Mono', 'Courier New', monospace"

# ── Plotly layout patch ──────────────────────────────────────────────────
PLOTLY_LAYOUT: dict = {
    "paper_bgcolor": PAPER,
    "plot_bgcolor": PAPER,
    "font": {"family": FONT_STACK, "size": 12, "color": INK},
    "colorway": SECTOR_PALETTE,
    "xaxis": {
        "gridcolor": PAPER_RULE,
        "linecolor": INK,
        "linewidth": 1,
        "zerolinecolor": INK,
        "zerolinewidth": 1,
        "tickfont": {"size": 11, "color": INK_2},
        "showspikes": False,
    },
    "yaxis": {
        "gridcolor": PAPER_RULE,
        "linecolor": INK,
        "linewidth": 1,
        "zerolinecolor": INK,
        "zerolinewidth": 1,
        "tickfont": {"size": 11, "color": INK_2},
        "tickformat": ",.2f",
    },
    "margin": {"l": 48, "r": 24, "t": 92, "b": 40},
    "hovermode": "x unified",
    "hoverlabel": {
        "bgcolor": INK,
        "bordercolor": INK,
        "font": {"family": "Inter", "size": 11, "color": PAPER},
    },
    "showlegend": True,
    "legend": {
        "orientation": "h",
        "yanchor": "bottom", "y": 1.06,
        "xanchor": "left",   "x": 0,
        "font": {"size": 11, "color": INK},
        "bgcolor": "rgba(0,0,0,0)",
    },
    # Title sits in its own band at the container top; legend at y=1.06 of the
    # plot area sits below it. margin.t=92 reserves room so they never collide
    # (cccg-2 fix — title.yref=container vs legend.yref=paper were crammed in t=32).
    "title": {
        "xref": "container", "x": 0, "xanchor": "left",
        "yref": "container", "y": 0.985, "yanchor": "top",
        "font": {"size": 15, "color": INK},
    },
}


def style_plotly(fig):
    """Apply the CMSI/FT Plotly look to a figure: cream paper/plot bg, FT grid,
    Inter font, sector colorway. Call right before st.plotly_chart. Idempotent.
    Chart-specific title/height set before this call are preserved (PLOTLY_LAYOUT
    does not set them).
    """
    fig.update_layout(template="plotly_white")
    fig.update_layout(**PLOTLY_LAYOUT)
    return fig


# ── CSS ──────────────────────────────────────────────────────────────────
_CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');

/* force light color-scheme — dodge OS dark-mode for canvas widgets */
:root, html, body {{ color-scheme: light !important; }}

/* Text-selection highlight. Without this the browser default (a dark slate in
   OS dark-mode) paints behind selected text → unreadable on cream. Use a soft
   CMSI-red tint + INK text so selected text stays legible and on-brand. */
::selection {{ background: rgba(200, 16, 46, 0.22) !important; color: {INK} !important; }}
::-moz-selection {{ background: rgba(200, 16, 46, 0.22) !important; color: {INK} !important; }}

/* NEVER override Streamlit's Material icon font / ligatures — else controls like
   the sidebar collapse/expand chevron render as raw ligature TEXT
   ("keyboard_double_arrow_left") and stop working. Our global tnum/ss01 + the
   sidebar font-family override would otherwise kill the icon ligatures. */
[data-testid="stIconMaterial"], span[data-testid="stIconMaterial"],
.material-symbols-rounded, .material-symbols-outlined, .material-icons,
[class*="material-symbols"] {{
  font-family: 'Material Symbols Rounded', 'Material Symbols Outlined', 'Material Icons' !important;
  font-feature-settings: 'liga' !important;
  -webkit-font-feature-settings: 'liga' !important;
  font-variant-numeric: normal !important;
}}

/* base page — include stApp ROOT. On an OS in dark mode Streamlit 1.58 paints
   [data-testid="stApp"] dark slate (#0f172a) despite config base="light"; that
   dark root then shows through any transparent child AND through portaled
   BaseWeb popovers (which mount into stApp, not stAppViewContainer). Force cream
   on the root so nothing bleeds dark. */
html, body, [data-testid="stApp"], [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
  background: {PAPER} !important;
  color: {INK} !important;
  font-family: {FONT_STACK} !important;
  font-size: 15px;
  line-height: 23px;
  font-feature-settings: 'tnum', 'ss01', 'cv11';
  -webkit-font-smoothing: antialiased;
}}
/* Header: cream, NATURAL height. Do NOT crush to 1px — that (a) lets page_header
   slide under the fixed toolbar (clipped title) and (b) hides the sidebar
   collapse/expand control which lives in this header. */
[data-testid="stHeader"] {{
  background: {PAPER} !important;
}}
[data-testid="stToolbar"] {{ background: {PAPER} !important; }}
/* Sidebar collapse + collapsed-state reopen chevrons.
   Real Streamlit 1.58 testids (verified against the shipped build + live Chrome
   DOM probe): stSidebarCollapseButton (open → collapse, « icon) and
   stExpandSidebarButton (collapsed → reopen, » icon). The earlier guess
   `stSidebarCollapsedControl` does NOT exist in 1.58 — that CSS was dead.
   Streamlit paints both chevrons with fadedText60, which resolves to
   #f1f5f9 (near-white, dark-theme bleed) → invisible on our cream paper.
   Force INK so they are actually visible/findable. */
[data-testid="stSidebarCollapseButton"] [data-testid="stIconMaterial"],
[data-testid="stExpandSidebarButton"] [data-testid="stIconMaterial"],
[data-testid="stExpandSidebarButton"] svg {{
  color: {INK} !important;
  fill: {INK} !important;
}}
/* Make the collapsed reopen control discoverable — hairline chip + red hover.
   It lives inside stHeader at y≈14; NEVER crush stHeader to 1px or this gets
   clipped out of the viewport (that was the original cloud bug). */
[data-testid="stExpandSidebarButton"] {{
  background: {PAPER} !important;
  border: 1px solid {PAPER_EDGE} !important;
  border-radius: 2px !important;
}}
[data-testid="stExpandSidebarButton"]:hover {{
  background: {PAPER_BAND} !important;
  border-color: {CMSI_RED} !important;
}}

/* sidebar — Claude Design §4.4 (CSS-mapped onto Streamlit's native sidebar) */
[data-testid="stSidebar"] {{
  background: {PAPER_DEEP} !important;
  border-right: 1px solid {PAPER_EDGE} !important;
  min-width: 240px !important;
}}
[data-testid="stSidebar"] > div:first-child {{
  padding-top: 1rem;
}}
[data-testid="stSidebar"] {{
  font-family: {FONT_STACK} !important;
}}
[data-testid="stSidebar"] *:not([data-testid="stIconMaterial"]):not([class*="material-symbols"]) {{
  color: {INK_2} !important;
}}
[data-testid="stSidebar"] [data-testid="stHeading"] h2,
[data-testid="stSidebar"] [data-testid="stHeading"] h3 {{
  font-size: 11px !important;
  text-transform: uppercase;
  letter-spacing: 0.14em !important;
  color: {INK_3} !important;
  font-weight: 600 !important;
  border-left: none !important;
  border-bottom: none !important;
  padding: 0 !important;
  margin: 0 0 6px 0 !important;
}}
[data-testid="stSidebarNav"] ul li a,
[data-testid="stSidebarNav"] a {{
  border-left: 4px solid transparent;
  padding-left: 16px !important;
}}
[data-testid="stSidebarNav"] a[aria-current="page"] {{
  border-left-color: {CMSI_RED} !important;
  background: {PAPER_BAND} !important;
  color: {INK} !important;
  font-weight: 600 !important;
}}

/* page typography — Claude Design §2 */
/* padding-top clears the fixed 53px stHeader. 4.5rem (=72px) leaves ~19px gap
   so [NN/07] never tucks under the toolbar (4rem left only ~3px on localhost;
   too tight for the cloud Manage-app bar). */
.block-container {{ padding-top: 4.5rem !important; padding-bottom: 4rem !important; max-width: 1440px; }}
/* When the sidebar is COLLAPSED, let main content reclaim the freed width
   instead of staying boxed at 1440px (which left a big empty band where the
   sidebar was). stExpandSidebarButton is rendered ONLY while collapsed, so
   :has() detects the collapsed state in pure CSS — editorial 1440 cap stays
   when the sidebar is open, content goes fluid when it's hidden. */
body:has([data-testid="stExpandSidebarButton"]) .block-container {{
  max-width: 2200px !important;
}}
h1, h2, h3, h4 {{
  font-family: {FONT_STACK} !important;
  color: {INK} !important;
  font-weight: 600 !important;
  letter-spacing: -0.01em;
}}
h1 {{ font-size: 32px !important; line-height: 36px !important; margin: 0 0 0.4rem 0 !important; border-bottom: 2px solid {INK}; padding-bottom: 0.6rem; }}
h2 {{ font-size: 24px !important; line-height: 30px !important; margin: 1.5rem 0 1rem !important; border-top: 1px solid {INK}; border-left: none !important; border-bottom: none !important; padding: 0.6rem 0 0 0 !important; }}
h3 {{ font-size: 18px !important; line-height: 24px !important; margin: 1.2rem 0 0.6rem !important; color: {INK_2} !important; font-weight: 600 !important; text-transform: none; letter-spacing: 0 !important; }}
h4 {{ font-size: 14px !important; color: {INK_3} !important; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; }}

/* metric KPI — native st.metric inherits these (kpi_metric helper is preferred) */
[data-testid="stMetric"] {{
  background: {PAPER} !important;
  border: 1px solid {PAPER_EDGE} !important;
  border-radius: 0 !important;
  padding: 14px 16px !important;
}}
[data-testid="stMetricValue"] {{
  font-family: {FONT_STACK} !important;
  font-feature-settings: 'tnum';
  font-variant-numeric: tabular-nums lining-nums;
  font-size: 30px !important;
  line-height: 36px !important;
  color: {INK} !important;
  font-weight: 500;
  letter-spacing: -0.02em;
}}
[data-testid="stMetricLabel"] {{
  font-family: {FONT_STACK} !important;
  font-size: 10px !important;
  color: {INK_3} !important;
  font-weight: 600 !important;
  text-transform: uppercase;
  letter-spacing: 0.12em !important;
}}
[data-testid="stMetricDelta"] {{
  font-family: {FONT_STACK} !important;
  font-feature-settings: 'tnum';
  font-size: 12px !important;
  font-weight: 600;
}}

/* captions */
.stCaption, [data-testid="stCaptionContainer"] {{
  color: {INK_3} !important;
  font-family: {FONT_STACK} !important;
  font-size: 12px !important;
  font-weight: 400;
  letter-spacing: 0.02em;
}}

/* dividers */
hr {{ border-color: {PAPER_RULE} !important; border-width: 0 0 1px 0 !important; }}

/* buttons */
.stButton button {{
  background: {CMSI_RED} !important;
  border: none !important;
  color: {PAPER} !important;
  font-family: {FONT_STACK} !important;
  font-weight: 600 !important;
  font-size: 12px !important;
  letter-spacing: 0.04em !important;
  border-radius: 2px !important;
  padding: 0 16px !important;
  height: 32px !important;
}}
.stButton button:hover {{ background: {CMSI_RED_DEEP} !important; }}
/* Button :active / :focus — without these the click/pressed + focus-ring state
   bleeds dark-slate (OS dark-mode) → the button "turns black" on click. Pin all
   interaction states to the CMSI-red brand and kill the dark focus box-shadow.
   Covers the top-bar language toggle (a single st.button) and every other button. */
.stButton button:active,
.stButton button:focus,
.stButton button:focus-visible {{
  background: {CMSI_RED_DEEP} !important;
  color: {PAPER} !important;
  border: none !important;
  outline: none !important;
  box-shadow: none !important;
}}

/* download buttons — LIGHT secondary style. Streamlit's stDownloadButton is a
   separate testid from .stButton and was uncovered → OS dark-mode bled through
   (button rendered black). Pin it to the cream/ink FT-editorial surface and lock
   all interaction states so no dark focus/active shadow leaks back in. */
[data-testid="stDownloadButton"] button {{
  background: {PAPER_BAND} !important;
  color: {INK} !important;
  border: 1px solid {PAPER_EDGE} !important;
  font-family: {FONT_STACK} !important;
  font-weight: 600 !important;
  font-size: 12px !important;
  letter-spacing: 0.04em !important;
  border-radius: 2px !important;
  padding: 0 16px !important;
  height: 32px !important;
}}
[data-testid="stDownloadButton"] button:hover {{
  background: {PAPER_EDGE} !important;
  color: {INK} !important;
  border-color: {CMSI_RED} !important;
}}
[data-testid="stDownloadButton"] button:active,
[data-testid="stDownloadButton"] button:focus,
[data-testid="stDownloadButton"] button:focus-visible {{
  background: {PAPER_BAND} !important;
  color: {INK} !important;
  border: 1px solid {CMSI_RED} !important;
  outline: none !important;
  box-shadow: none !important;
}}

/* dataframe — outer frame only; cell colors come from config.toml */
[data-testid="stDataFrame"] {{
  font-family: {FONT_STACK} !important;
  font-feature-settings: 'tnum';
  border: 1px solid {PAPER_EDGE};
  border-radius: 0;
}}

/* st.table — native HTML <table> (NOT the canvas grid). Streamlit's base theme
   paints its text in dark-theme fadedText (rgb(241,245,249), near-white) on a
   gray border → unreadable / "black" on cream. Force editorial light styling.
   (Sortable data tables go through ui.render_html_table, not st.table.) */
[data-testid="stTable"] table {{
  background: {PAPER} !important;
  color: {INK} !important;
  border-collapse: collapse !important;
  border: 1px solid {PAPER_EDGE} !important;
  font-family: {FONT_STACK} !important;
  font-feature-settings: 'tnum';
}}
[data-testid="stTable"] thead th {{
  background: {PAPER_BAND} !important;
  color: {INK} !important;
  font-weight: 600 !important;
  border-bottom: 1px solid {PAPER_EDGE} !important;
}}
[data-testid="stTable"] tbody th,
[data-testid="stTable"] tbody td {{
  background: {PAPER} !important;
  color: {INK} !important;
  border-bottom: 1px solid {PAPER_RULE} !important;
}}

/* inline code / `badges` (e.g. `1801 HK`, `streamlit_app.py`) — Streamlit's
   default code chip resolves to a dark background; recolor to a cream band so
   it reads on paper instead of showing as a dark/black pill. */
code {{
  background: {PAPER_BAND} !important;
  color: {INK} !important;
  border: 1px solid {PAPER_RULE} !important;
  border-radius: 2px !important;
  padding: 0 4px !important;
  font-family: {FONT_MONO} !important;
  font-size: 0.85em !important;
}}
/* …but don't chip-style multi-line st.code() blocks — only inline chips.
   (No st.code() in the app today; this hardens against future use.) */
pre code {{
  background: transparent !important;
  border: none !important;
  padding: 0 !important;
  font-size: inherit !important;
}}

/* selectbox / popover — light & cream-bordered */
[data-baseweb="select"] > div {{
  background-color: {PAPER} !important;
  color: {INK} !important;
  border-color: {PAPER_EDGE} !important;
  border-radius: 2px !important;
}}
[data-baseweb="select"] input,
[data-baseweb="select"] span {{ color: {INK} !important; }}
[data-baseweb="popover"], [data-baseweb="menu"], [role="listbox"] {{
  border: 1px solid {PAPER_EDGE} !important;
  border-radius: 2px !important;
}}
/* The dropdown LIST in Streamlit 1.58 is a bare <div>/<ul> carrying ONLY
   emotion classes (st-*) — no data-baseweb/role — so the earlier
   [data-baseweb=menu]/[role=listbox] rules never matched it and it bled dark
   slate (#0f172a / #1e293b). Force cream on EVERY container inside the popover;
   options get INK text + a band hover. */
[data-baseweb="popover"],
[data-baseweb="popover"] div,
[data-baseweb="popover"] ul,
[data-baseweb="popover"] li,
[data-baseweb="menu"], [data-baseweb="menu"] li,
[role="listbox"], [role="option"] {{
  background-color: {PAPER} !important;
  color: {INK} !important;
}}
[data-baseweb="popover"] li:hover,
[data-baseweb="menu"] li:hover,
[role="option"]:hover,
[aria-selected="true"][role="option"] {{
  background-color: {PAPER_BAND} !important;
}}

/* text input */
[data-baseweb="input"] > div,
[data-testid="stTextInput"] input {{
  background-color: {PAPER} !important;
  color: {INK} !important;
  border-color: {PAPER_EDGE} !important;
  border-radius: 2px !important;
}}

/* tabs — Claude Design §4.3 underline style, FT/Stripe-like */
.stTabs [data-baseweb="tab-list"] {{
  border-bottom: 1px solid {PAPER_RULE};
  gap: 32px;
}}
.stTabs [data-baseweb="tab"] {{
  font-family: {FONT_STACK} !important;
  font-size: 11px !important;
  font-weight: 600 !important;
  color: {INK_3} !important;
  text-transform: uppercase;
  letter-spacing: 0.1em !important;
  background: transparent !important;
  border-radius: 0 !important;
  padding: 10px 0 !important;
}}
.stTabs [aria-selected="true"] {{
  color: {CMSI_RED} !important;
  border-bottom: 2px solid {CMSI_RED} !important;
}}

/* form widgets */
.stSelectbox, .stTextInput, .stMultiSelect, .stRadio, .stCheckbox {{
  font-family: {FONT_STACK} !important;
}}
.stAlert {{
  font-family: {FONT_STACK} !important;
  border-radius: 2px !important;
  border-width: 1px !important;
}}
/* Alert text → INK. Streamlit paints st.warning/st.info body text a faint
   muted color that is unreadable on the light tint; force black so the
   disclaimer (and any caveat) is legible. Tint bg is left as-is. */
[data-testid="stAlert"],
[data-testid="stAlert"] [data-testid="stMarkdownContainer"],
[data-testid="stAlert"] p,
[data-testid="stAlert"] strong,
[data-testid="stAlert"] li {{
  color: {INK} !important;
}}

/* hide chrome */
#MainMenu, footer, [data-testid="stStatusWidget"], [data-testid="stDeployButton"] {{
  visibility: hidden !important;
}}

/* expander */
[data-testid="stExpander"] {{
  border: 1px solid {PAPER_EDGE} !important;
  border-radius: 0 !important;
  background: {PAPER} !important;
}}
[data-testid="stExpander"] summary {{
  font-family: {FONT_STACK} !important;
  font-weight: 600 !important;
  color: {INK} !important;
  font-size: 13px;
  background: {PAPER} !important;   /* expanded summary bleeds dark slate otherwise */
}}
[data-testid="stExpander"] summary:hover {{ background: {PAPER_BAND} !important; }}
[data-testid="stExpander"] details,
[data-testid="stExpander"] details > div,
[data-testid="stExpanderDetails"] {{
  background: {PAPER} !important;
}}

/* ──────────────────────────────────────────────────────────────────────
   Editorial component classes (used by helpers below — kpi_metric etc.)
   ────────────────────────────────────────────────────────────────────── */

/* KPI metric card */
.cmsi-kpi-strip {{
  display: grid;
  gap: 0;
  border: 1px solid {PAPER_EDGE};
  background: {PAPER};
  margin: 0.4rem 0 1.2rem;
}}
.cmsi-kpi {{
  padding: 14px 16px;
  border-right: 1px solid {PAPER_EDGE};
  position: relative;
}}
.cmsi-kpi:last-child {{ border-right: none; }}
.cmsi-kpi-head {{ display: flex; justify-content: space-between; align-items: center; }}
.cmsi-kpi-label {{
  font-size: 10px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  font-weight: 600;
  color: {INK_3};
}}
.cmsi-kpi-label b {{
  color: {INK};
  font-weight: 600;
  letter-spacing: 0.04em;
  font-size: 11px;
  margin-right: 6px;
}}
.cmsi-kpi-stamp {{
  width: 4px;
  height: 12px;
  background: {CMSI_RED};
  display: inline-block;
}}
.cmsi-kpi-num {{
  font-size: 38px;
  line-height: 44px;
  font-weight: 500;
  letter-spacing: -0.02em;
  color: {INK};
  margin-top: 10px;
  font-variant-numeric: tabular-nums lining-nums;
  font-family: {FONT_STACK};
}}
.cmsi-kpi-delta {{
  margin-top: 4px;
  font-size: 12px;
  font-variant-numeric: tabular-nums;
  line-height: 16px;
}}
.cmsi-kpi-delta.up {{ color: {UP}; }}
.cmsi-kpi-delta.down {{ color: {DOWN}; }}
.cmsi-kpi-delta.flat {{ color: {FLAT}; }}
.cmsi-kpi-delta .pct {{ margin-left: 8px; font-weight: 600; }}
.cmsi-kpi-foot {{
  margin-top: 8px;
  font-size: 10px;
  letter-spacing: 0.04em;
  color: {INK_3};
  text-transform: uppercase;
  font-weight: 500;
  font-family: {FONT_MONO};
}}

/* Page hero header — [NN/07] code + title + 4px red bar */
.cmsi-page-hero {{
  display: flex;
  align-items: baseline;
  gap: 16px;
  margin: 0 0 1rem 0;
  border-bottom: 2px solid {INK};
  padding-bottom: 0.6rem;
}}
.cmsi-page-hero .code {{
  font-family: {FONT_MONO};
  font-size: 11px;
  letter-spacing: 0.1em;
  color: {INK_3};
  font-weight: 500;
}}
.cmsi-page-hero .ttl {{
  font-size: 32px;
  line-height: 36px;
  font-weight: 600;
  letter-spacing: -0.01em;
  color: {INK};
  margin: 0;
}}
.cmsi-page-hero .bar {{
  display: inline-block;
  width: 4px;
  height: 24px;
  background: {CMSI_RED};
  vertical-align: middle;
  margin-left: 4px;
}}
.cmsi-page-hero .meta {{
  margin-left: auto;
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: {INK_3};
  font-weight: 500;
  font-family: {FONT_MONO};
}}
.cmsi-page-hero .sub {{
  display: block;
  font-size: 12px;
  color: {INK_3};
  font-weight: 400;
  letter-spacing: 0.02em;
  margin-top: 4px;
}}

/* Section header — Tier 2 (1px ink top + h2 + 4px red bar) */
.cmsi-section {{
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin: 1.6rem 0 0.8rem;
  border-top: 1px solid {INK};
  padding-top: 10px;
}}
.cmsi-section .bar {{
  width: 4px;
  height: 18px;
  background: {CMSI_RED};
  display: inline-block;
}}
.cmsi-section .ttl {{
  font-size: 21px;
  line-height: 27px;
  font-weight: 600;
  color: {INK};
}}
.cmsi-section .meta {{
  margin-left: auto;
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: {INK_3};
  font-weight: 500;
  font-family: {FONT_MONO};
}}

/* ── Research-memo editorial block (Ticker Drill wiki memo) ─────────────── */
/* Rating / TP meta strip — hairline cells, eyebrow label over INK value. */
.cmsi-memo-bar {{
  display: flex; flex-wrap: wrap; align-items: stretch;
  border: 1px solid {PAPER_EDGE}; background: {PAPER};
  margin: 0.2rem 0 1rem;
}}
.cmsi-memo-cell {{
  padding: 8px 16px; border-right: 1px solid {PAPER_RULE};
  display: flex; flex-direction: column; gap: 3px; min-width: 116px;
}}
.cmsi-memo-cell:last-child {{ border-right: none; }}
.cmsi-memo-k {{
  font-size: 10px; letter-spacing: 0.12em; text-transform: uppercase;
  font-weight: 600; color: {INK_3};
}}
.cmsi-memo-v {{
  font-size: 18px; font-weight: 600; color: {INK};
  font-variant-numeric: tabular-nums lining-nums;
}}

/* Eyebrow label (摘要 / 投资逻辑 …) — ▎red + uppercase; body markdown follows. */
.cmsi-eyebrow {{
  font-size: 11px; letter-spacing: 0.14em; text-transform: uppercase;
  font-weight: 600; color: {INK_3};
  display: flex; align-items: center; gap: 8px;
  margin: 1.1rem 0 0.35rem;
}}
.cmsi-eyebrow::before {{
  content: ''; width: 3px; height: 13px; background: {CMSI_RED}; display: inline-block;
}}

/* Sector / tag chips — hairline, mono, no fill, no emoji. */
.cmsi-chips {{ display: flex; flex-wrap: wrap; gap: 6px; margin: 0 0 0.8rem; }}
.cmsi-chip {{
  display: inline-flex; align-items: center; height: 22px; padding: 0 10px;
  font-size: 11px; font-weight: 500; letter-spacing: 0.02em;
  font-family: {FONT_MONO}; color: {INK_2};
  border: 1px solid {PAPER_EDGE}; border-radius: 2px; background: {PAPER};
  white-space: nowrap;
}}
"""


def inject_css() -> None:
    """Inject the global theme CSS. Call AFTER set_page_config.

    Streamlit reruns on every interaction and rebuilds DOM, so inject every
    call — no session-state guard (would skip subsequent renders).
    """
    st.markdown(f"<style>{_CSS}</style>", unsafe_allow_html=True)


# ── Editorial component helpers ──────────────────────────────────────────

def page_header(title: str, meta: str | None = None,
                subtitle: str | None = None) -> None:
    """Render a Claude Design Tier-1 page header.

    Replaces `st.title("📊 Multi-Domain Investment Dashboard")` with:
        page_header("Multi-Domain Investment Dashboard",
                    meta="As of 2026-05-28 16:08 HKT")

    (The old "NN / 07" code prefix was dropped per user request — investor-facing
    pages don't need an internal page-numbering scheme.)
    """
    meta_html = f'<span class="meta">{meta}</span>' if meta else ""
    sub_html = f'<span class="sub">{subtitle}</span>' if subtitle else ""
    st.markdown(
        f'<div class="cmsi-page-hero">'
        f'<h1 class="ttl">{title}<span class="bar"></span></h1>'
        f'{meta_html}'
        f'</div>{sub_html}',
        unsafe_allow_html=True,
    )


def section_header(title: str, meta: str | None = None) -> None:
    """Render a Claude Design Tier-2 section header (replaces st.subheader).

    Use:
        section_header("Top Movers · 5D", meta="Across 7 sectors")
    """
    meta_html = f'<span class="meta">{meta}</span>' if meta else ""
    st.markdown(
        f'<div class="cmsi-section">'
        f'<span class="bar"></span>'
        f'<span class="ttl">{title}</span>'
        f'{meta_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def kpi_metric(label: str, value: str, delta_abs: str | None = None,
               delta_pct: str | None = None, foot: str | None = None,
               direction: str = "flat") -> str:
    """Render one KPI card. Returns the HTML — use kpi_strip([...]) to compose.

    `direction` ∈ {'up', 'down', 'flat'} drives delta color.

    Usage:
        kpi_strip([
            kpi_metric("HSI · HANG SENG", "19,247.82",
                       delta_abs="▲ +183.42", delta_pct="+0.96%",
                       foot="AS OF 28 MAY · 16:08 HKT", direction="up"),
            kpi_metric("S&P 500", "5,328.10", direction="flat"),
        ])
    """
    delta_html = ""
    if delta_abs or delta_pct:
        parts = []
        if delta_abs:
            parts.append(f'<span class="abs">{delta_abs}</span>')
        if delta_pct:
            parts.append(f'<span class="pct">{delta_pct}</span>')
        delta_html = f'<div class="cmsi-kpi-delta {direction}">{"".join(parts)}</div>'
    foot_html = f'<div class="cmsi-kpi-foot">{foot}</div>' if foot else ""

    return dedent(f"""
        <div class="cmsi-kpi">
          <div class="cmsi-kpi-head">
            <span class="cmsi-kpi-label">{label}</span>
            <span class="cmsi-kpi-stamp"></span>
          </div>
          <div class="cmsi-kpi-num">{value}</div>
          {delta_html}
          {foot_html}
        </div>
    """).strip()


def kpi_strip(cards: list[str]) -> None:
    """Render multiple KPI cards in a grid strip (1 row, N cols)."""
    n = len(cards) or 1
    body = "".join(cards)
    st.markdown(
        f'<div class="cmsi-kpi-strip" style="grid-template-columns:repeat({n},1fr);">'
        f'{body}</div>',
        unsafe_allow_html=True,
    )


# ── Research-memo helpers (Ticker Drill) ─────────────────────────────────

def memo_meta_bar(items: list[tuple[str, str]]) -> None:
    """Hairline meta strip for the research-memo header — [(label, value), …]
    e.g. [('评级', '增持/BUY'), ('目标价', 'HKD25 (+30%)')]. Label = uppercase
    eyebrow, value = INK bold tabular. Replaces the old '**评级**: x · …' markdown."""
    cells = "".join(
        f'<div class="cmsi-memo-cell"><span class="cmsi-memo-k">{_esc(str(k))}</span>'
        f'<span class="cmsi-memo-v">{_esc(str(v))}</span></div>'
        for k, v in items
    )
    st.markdown(f'<div class="cmsi-memo-bar">{cells}</div>', unsafe_allow_html=True)


def eyebrow(label: str) -> None:
    """Editorial eyebrow label (▎red + uppercase). Follow it with st.markdown(body)
    so the body keeps normal markdown rendering."""
    st.markdown(f'<div class="cmsi-eyebrow">{_esc(str(label))}</div>',
                unsafe_allow_html=True)


def chips(items: list[str]) -> None:
    """Hairline mono chips (sector tags etc) — no fill, no emoji. Replaces the old
    `code`-backtick tag list."""
    body = "".join(f'<span class="cmsi-chip">{_esc(str(c))}</span>' for c in items)
    st.markdown(f'<div class="cmsi-chips">{body}</div>', unsafe_allow_html=True)
