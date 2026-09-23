"""美光股价回撤（距前 36 个月最高收盘）→ mu_price_drawdown_36m.json

用法: uv run --with yfinance --with pandas python fetch_mu_drawdown.py
口径: adj close 月线; dd_t = close_t / max(close_{t-35..t}) - 1 (%); 前 35 个月用可得窗口。
"""
import json, time, datetime as dt
from pathlib import Path
import yfinance as yf

OUT = Path(__file__).resolve().parent / "mu_price_drawdown_36m.json"
time.sleep(1)  # rate-limit courtesy (skills.md 惯例)
h = yf.download("MU", start="1984-01-01", interval="1mo", auto_adjust=True, progress=False)
if hasattr(h.columns, "levels"):
    h.columns = h.columns.droplevel(1)
close = h["Close"].dropna()
roll_max = close.rolling(36, min_periods=1).max()
dd = (close / roll_max - 1) * 100
rows = [[d.strftime("%Y-%m-01"), round(float(v), 1)] for d, v in dd.items()]
assert all(v <= 0 for _, v in rows), "drawdown must be <= 0"
def trough(y0, y1):
    return min(v for d, v in rows if y0 <= d[:4] <= y1)
assert trough("2001", "2002") <= -60, trough("2001", "2002")
assert trough("2008", "2009") <= -60, trough("2008", "2009")
assert trough("2022", "2023") <= -40, trough("2022", "2023")
assert -30 <= rows[-1][1] <= 0, rows[-1]
OUT.write_text(json.dumps({
    "source": "yfinance MU monthly adj close (auto_adjust)",
    "fetched": dt.date.today().isoformat(),
    "window_months": 36,
    "first": rows[0][0], "last": rows[-1][0], "n": len(rows),
    "rows": rows,
}, ensure_ascii=False, indent=0))
print("wrote", OUT, rows[0], rows[-1], "n=", len(rows))
for y in ("1985","1986","1998","2001","2002","2008","2009","2012","2016","2019","2022","2023","2026"):
    print(y, trough(y, y))
