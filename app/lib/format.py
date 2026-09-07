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


def fmt_ticker_bbg(ticker: str) -> str:
    """n2 audit fix: Bloomberg ticker style '2269 HK' instead of '2269.HK'.

    Suffix mapping:
      .HK → HK (Hong Kong)
      .T  → JP (Tokyo, Bloomberg uses JP not T)
      .SS → CH (Shanghai, Bloomberg uses CH)
      .SZ → CH (Shenzhen, Bloomberg uses CH)
      .KS → KS (Korea)
    """
    if not ticker or "." not in ticker:
        return ticker
    code, suffix = ticker.split(".", 1)
    mapping = {"HK": "HK", "T": "JP", "SS": "CH", "SZ": "CH", "KS": "KS"}
    return f"{code} {mapping.get(suffix, suffix)}"


def color_pct(v) -> str:
    """Return CSS color string for a percentage value."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return f"color: {NEUTRAL}"
    if v > 0:
        return f"color: {GREEN}; font-weight: 600"
    if v < 0:
        return f"color: {RED}; font-weight: 600"
    return f"color: {NEUTRAL}"


