"""Number / color formatters for dashboard tables."""

from __future__ import annotations

import pandas as pd

# Colors
GREEN = "#22c55e"
RED = "#ef4444"
NEUTRAL = "#94a3b8"


def _is_na(v) -> bool:
    if v is None:
        return True
    if isinstance(v, float) and pd.isna(v):
        return True
    return False


def fmt_pct(v, decimals: int = 2) -> str:
    if _is_na(v):
        return "—"
    return f"{v:+.{decimals}f}%"


def fmt_pct_decimal(v, decimals: int = 2) -> str:
    """For values already in decimal form (0.05 = 5%)."""
    if _is_na(v):
        return "—"
    return f"{v * 100:+.{decimals}f}%"


def fmt_money_b(v) -> str:
    """USD billions / millions."""
    if _is_na(v):
        return "—"
    if abs(v) >= 1e9:
        return f"${v / 1e9:.1f}B"
    if abs(v) >= 1e6:
        return f"${v / 1e6:.0f}M"
    return f"${v:.0f}"


def fmt_ratio(v, decimals: int = 1) -> str:
    if _is_na(v):
        return "—"
    if v < 0:
        return "neg"
    return f"{v:.{decimals}f}x"


def fmt_price(v, decimals: int = 2) -> str:
    if _is_na(v):
        return "—"
    return f"{v:,.{decimals}f}"


def fmt_num(v, decimals: int = 2) -> str:
    """Plain number, e.g. for benchmark Last price."""
    if _is_na(v):
        return "—"
    return f"{v:,.{decimals}f}"


def color_pct(v) -> str:
    """Return CSS color string for a percentage value."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return f"color: {NEUTRAL}"
    if v > 0:
        return f"color: {GREEN}; font-weight: 600"
    if v < 0:
        return f"color: {RED}; font-weight: 600"
    return f"color: {NEUTRAL}"


def style_pct_column(s: pd.Series) -> list[str]:
    """For DataFrame.style.apply: color each cell red/green."""
    return [color_pct(v) for v in s]


def background_gradient_diverging(
    s: pd.Series,
    mid: float = 0,
    pos_color: str = "#16a34a",
    neg_color: str = "#dc2626",
    intensity: float = 0.35,
) -> list[str]:
    """Diverging color background for numeric Series. Intensity 0-1 (alpha)."""
    out = []
    s_clean = s.dropna()
    if s_clean.empty:
        return [""] * len(s)
    max_abs = max(abs(s_clean.min() - mid), abs(s_clean.max() - mid)) or 1
    for v in s:
        if pd.isna(v):
            out.append("")
            continue
        if v >= mid:
            ratio = min(abs(v - mid) / max_abs, 1.0) * intensity
            color = pos_color
        else:
            ratio = min(abs(v - mid) / max_abs, 1.0) * intensity
            color = neg_color
        out.append(f"background-color: {color}{int(ratio * 255):02x}")
    return out


def background_gradient_low_good(
    s: pd.Series,
    low_color: str = "#16a34a",
    high_color: str = "#dc2626",
    intensity: float = 0.30,
) -> list[str]:
    """For ratios where lower is better (P/E, EV/EBITDA). Green = low, Red = high."""
    out = []
    s_clean = s.dropna()
    if s_clean.empty or len(s_clean) < 2:
        return [""] * len(s)
    lo, hi = s_clean.min(), s_clean.max()
    if hi == lo:
        return [""] * len(s)
    for v in s:
        if pd.isna(v) or v < 0:    # negative ratios = neg earnings, skip
            out.append("")
            continue
        ratio_lo = (hi - v) / (hi - lo) * intensity   # closer to low = greener
        ratio_hi = (v - lo) / (hi - lo) * intensity
        if ratio_lo >= ratio_hi:
            out.append(f"background-color: {low_color}{int(ratio_lo * 255):02x}")
        else:
            out.append(f"background-color: {high_color}{int(ratio_hi * 255):02x}")
    return out
