"""Strategy picks data layer — reads from data/external/.

Strategies tracked:
- v4 biotech (2026-04-22, 27 picks, XBI benchmark) — CSV
- v5 biotech (2026-05-15, 40 picks, XBI benchmark) — CSV (derived from picks.db)
- HK 高股息 v1 (2026-03-20, 34 picks equal-weight, 3466.HK benchmark) — CSV
- HK 高股息 v2 (2026-06-11, 20 picks score-weighted + 12% cash, 3466.HK) — CSV
  (standard build, George sign-off 2026-06-11; canonical source:
  portfolio-engine/high_div_screen standard-build output. v1 history is frozen
  and never edited — v2 is a NEW book starting 2026-06-11, not a restatement.)

B1 audit fix: picks.db not committed (contains thesis/conviction IP).
Sync via `scripts/sync_ledger.sh` to regenerate v5_picks.csv from local ic-foundry.

Prices fetched live via yfinance, cached 1 hour.
"""

from __future__ import annotations

import time
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st
import yfinance as yf

from lib import portfolio_math as pm

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_EXT = REPO_ROOT / "data" / "external"
DATA_CONTENT = REPO_ROOT / "data" / "content"

V4_CSV = DATA_EXT / "v4_picks.csv"
V5_CSV = DATA_EXT / "v5_picks.csv"
V6_CSV = DATA_EXT / "v6_picks.csv"
HD_CSV = DATA_EXT / "hd_picks.csv"
HD_V2_CSV = DATA_EXT / "hd_picks_v2.csv"
HD_V3_CSV = DATA_EXT / "hd_picks_v3.csv"
IPO_CSV = DATA_EXT / "ipo_picks.csv"
IPO_INTRADAY_CSV = DATA_EXT / "ipo_day1_intraday.csv"
# Acquired / delisted picks: yfinance purges their history, so a live fetch returns
# nothing and the book silently drops the name (+ "possibly delisted" warning). This
# map pins each to its cash-out value (held as cash from delist_date), so the book
# accounts an acquired pick at the deal price instead of losing it. Analyst-editable.
DELISTED_CSV = DATA_EXT / "delisted_overrides.csv"


def _delisted_mtime() -> float:
    """mtime of the override CSV (0.0 if absent). Used as a cache key so editing the
    file invalidates fetch_picks_closes / _delisted_overrides instead of going stale."""
    return DELISTED_CSV.stat().st_mtime if DELISTED_CSV.exists() else 0.0


@st.cache_data(ttl=3600)
def _delisted_overrides(_mtime: float) -> dict[str, tuple[float, float, object]]:
    """{yf_sym: (entry_price, final_price, delist_ts)} for acquired/delisted picks.

    entry_price defaults to final_price when blank → the holding is flat at the
    cash-out value (correct for a merger-arb pick entered ~at the deal price). When
    the pick ran up before acquisition, the analyst fills entry_price so the realized
    return = final/entry, recognized as a step at delist_date. `_mtime` is only a
    cache key (see _delisted_mtime). Empty if file absent."""
    if not DELISTED_CSV.exists():
        return {}
    d = pd.read_csv(DELISTED_CSV)
    fin = pd.to_numeric(d["final_price"], errors="coerce")
    ent = (pd.to_numeric(d["entry_price"], errors="coerce")
           if "entry_price" in d.columns else pd.Series([float("nan")] * len(d)))
    dl = d["delist_date"] if "delist_date" in d.columns else pd.Series([None] * len(d))
    out: dict[str, tuple[float, float, object]] = {}
    for i, s in enumerate(d["yf_sym"]):
        if pd.isna(s) or pd.isna(fin.iloc[i]):
            continue
        f = float(fin.iloc[i])
        e = float(ent.iloc[i]) if pd.notna(ent.iloc[i]) else f          # blank → flat
        ts = pd.Timestamp(dl.iloc[i]) if pd.notna(dl.iloc[i]) else None
        out[str(s)] = (e, f, ts)
    return out


@st.cache_data(ttl=900)
def load_v4() -> pd.DataFrame:
    if not V4_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(V4_CSV)


@st.cache_data(ttl=900)
def load_v5() -> pd.DataFrame:
    """v5 biotech: from CSV (derived from ic-foundry catalyst-monitor picks)."""
    if not V5_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(V5_CSV)


@st.cache_data(ttl=900)
def load_v6() -> pd.DataFrame:
    """v6 biotech (7月调仓, effective 2026-07-08). Same schema as v4/v5
    (rank/ticker/name/score/pick_date/benchmark/yf_sym). Data is added separately
    via an insert script; until v6_picks.csv lands this returns an empty frame so
    the page renders a "即将上线" placeholder instead of crashing (三代演进)."""
    if not V6_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(V6_CSV)


SCORECARD_MD = DATA_EXT / "v4_v5_full_scorecard.md"
# 未建仓票段收益回补（一次性离线算好：yfinance auto_adjust 复权价按段区间
# v4=04-22→05-15 / v5=05-15→07-09；口径已用已建仓票 vs md 跟踪值 cross-check，
# 20+20 支全部 |diff|≤1pp。FOLD 按 delisted_overrides 现金锁定口径钉 0.0）。
SCORECARD_UNHELD_CSV = DATA_EXT / "v4_v5_unheld_segret.csv"


@st.cache_data(ttl=900)
def load_scorecard(version: str) -> pd.DataFrame:
    """v4/v5 全量评分明细（过闸后打分池，按 Final 降序）— 解析 L6 归因附表
    data/external/v4_v5_full_scorecard.md 中对应版本的 markdown 表。

    version: "v4" | "v5"（对应 "### v4 评分池全 27 支" 等 section 标题）。
    列: num/held/tick/name/ta/p/e/f/m/r/final/seg_ret/seg_bf/driver。
    seg_ret / driver 建仓票来自 md 跟踪值；未建仓票 seg_ret 由
    SCORECARD_UNHELD_CSV 事后回补并标 seg_bf=True（渲染层降色 + † 标注）。
    文件或 section 缺失 → 空 frame（页面回退旧 picks_table 全池表）。"""
    if not SCORECARD_MD.exists():
        return pd.DataFrame()
    text = SCORECARD_MD.read_text(encoding="utf-8")
    idx = text.find(f"### {version} ")
    if idx < 0:
        return pd.DataFrame()
    seg = text[idx:]
    nxt = seg.find("### ", 4)
    if nxt > 0:
        seg = seg[:nxt]

    def _num(s: str) -> float | None:
        try:
            return float(s.replace("+", ""))
        except ValueError:
            return None

    rows: list[dict] = []
    for line in seg.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        # skip header / separator rows
        if len(cells) < 13 or not cells[0].isdigit():
            continue
        rows.append({
            "num":     int(cells[0]),
            "held":    cells[1] == "●",
            "tick":    cells[2],
            "name":    cells[3],
            "ta":      "" if cells[4] == "—" else cells[4],
            "p":       _num(cells[5]),
            "e":       _num(cells[6]),
            "f":       _num(cells[7]),
            "m":       _num(cells[8]),
            "r":       _num(cells[9]),
            "final":   _num(cells[10]),
            "seg_ret": _num(cells[11]),
            "seg_bf":  False,
            "driver":  cells[12],
        })
    df = pd.DataFrame(rows)

    # 未建仓票段收益回补（缺文件 → 保持 None，渲染成 "—"）
    if not df.empty and SCORECARD_UNHELD_CSV.exists():
        bf = pd.read_csv(SCORECARD_UNHELD_CSV)
        bf = bf[bf["version"] == version]
        bf_map = {str(r["tick"]): float(r["seg_ret"])
                  for _, r in bf.iterrows() if pd.notna(r["seg_ret"])}
        for i in df.index:
            if pd.isna(df.at[i, "seg_ret"]) and df.at[i, "tick"] in bf_map:
                df.at[i, "seg_ret"] = bf_map[df.at[i, "tick"]]
                df.at[i, "seg_bf"] = True
    return df


HD_SCORECARD_CSV = DATA_EXT / "hd_v1_v2_full_scorecard.csv"


@st.cache_data(ttl=900)
def load_hd_scorecard(version: str) -> pd.DataFrame:
    """高股息 v1(34支)/v2(54支) 全量评分明细 — jobs/build_hd_scorecard.py 一次性产物
    （源: 2026-03-19 Agent增强版评分 xlsx / 2026-06-10 Part2 定性评分底稿，总分已与
    hd_picks / hd_picks_v2 逐支对账一致）。

    version: "hd_v1" | "hd_v2"。列: num/held/tick/name/sector/gov/fin/moat/final/
    status/seg_ret/seg_bf。段收益全部为 yfinance 含息复权计算（等权口径已与 L6 归因
    Wind TR 对账: v1 全池 −0.57% / 3466 −1.69% 一致）；未建仓票 seg_bf=True（渲染层
    灰色 + † 标注为事后对照）。缺文件 → 空 frame（页面回退旧全池表）。"""
    if not HD_SCORECARD_CSV.exists():
        return pd.DataFrame()
    df = pd.read_csv(HD_SCORECARD_CSV)
    df = df[df["version"] == version].reset_index(drop=True)
    if df.empty:
        return pd.DataFrame()
    df["held"] = df["held"].astype(bool)
    df["seg_bf"] = ~df["held"]
    return df


@st.cache_data(ttl=900)
def load_catalysts() -> pd.DataFrame:
    """Near-term catalysts for the biotech book — ticker/catalyst/timing/type/source.

    Feeds the July-rebalance board (lib/rebalance_panel) with a per-name catalyst +
    timing + source badge. `source` encodes provenance (引擎 / transcript验证★ /
    transcript纠正⚠️ / 人工 / 追高) which the panel parses into chips. Missing file →
    empty frame so the panel degrades to plain move cards (no catalyst line)."""
    p = DATA_CONTENT / "biotech_catalysts.csv"
    if not p.exists():
        return pd.DataFrame()
    return pd.read_csv(p)


@st.cache_data(ttl=900)
def load_rebalance_meta() -> dict:
    """Structured rebalance/ledger data (data/content/rebalance_v6.json): frozen
    performance-chain facts + sell-reason map + transcript-triage note + condensed
    rulebook. held/sold/new sets are derived live from v5/v6 picks by the panel;
    this file only carries what isn't in the CSVs. Missing/invalid → {} (panel skips)."""
    import json
    p = DATA_CONTENT / "rebalance_v6.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {}


@st.cache_data(ttl=900)
def load_hd_rebalance_meta() -> dict:
    """Structured HK high-div rebalance/ledger data (data/content/hd_rebalance_v3.json):
    chain segment metadata (labels/dates, returns computed live) + rebalance logic +
    condensed HD rulebook (愿意分/分得出/分得久). Missing/invalid → {} (panel skips)."""
    import json
    p = DATA_CONTENT / "hd_rebalance_v3.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return {}


@st.cache_data(ttl=900)
def load_hd() -> pd.DataFrame:
    if not HD_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(HD_CSV)


@st.cache_data(ttl=900)
def load_hd_v2() -> pd.DataFrame:
    """HD v2 standard build (2026-06-11). Public fields only (rank/score/weight/
    bucket/runrate) — B1 audit convention, no thesis/conviction columns.
    weight_pct = absolute book weight, Σ=88.01; the other ~12% is idle cash by
    design (not an error). bucket: rate=利率溢价桶 / nonrate=非利率桶."""
    if not HD_V2_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(HD_V2_CSV)


@st.cache_data(ttl=900)
def load_hd_v3() -> pd.DataFrame:
    """HD v3 Wind single-source build (2026-07-06 data date, effective 2026-07-07
    after George sign-off). Public fields only — same schema as v2. weight_pct =
    absolute book weight, Σ≈88; the other ~12% is idle cash by design. bucket:
    rate=利率溢价桶 / nonrate=非利率桶. A NEW book from 2026-07-07, not a restatement
    of v2 — v1/v2 histories stay frozen and comparable (三代演进)."""
    if not HD_V3_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(HD_V3_CSV)


@st.cache_data(ttl=900)
def load_ipo() -> pd.DataFrame:
    """HK IPO 打新 backtest — STATIC cross-section snapshot.

    NOT a time-series strategy: this reads the frozen ipo_picks.csv only and is
    NEVER routed through compute_strategy_returns / yfinance. `code` kept as str
    so leading-zero HK codes (e.g. 0901) don't get coerced to int. `day1_ret` is
    a DECIMAL (3.84 = +384%); ×100 happens at the render layer.
    """
    if not IPO_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(IPO_CSV, dtype={"code": str})


@st.cache_data(ttl=900)
def load_ipo_intraday() -> pd.DataFrame:
    """Listing-day 5-min intraday closes for the IPO backtest (listed names).

    Columns: code(str) / time(datetime) / close(float). `time` parsed once here;
    used for the post-open intraday-path small-multiples. Missing file → empty DF
    so the page degrades gracefully instead of crashing.
    """
    if not IPO_INTRADAY_CSV.exists():
        return pd.DataFrame()
    df = pd.read_csv(IPO_INTRADAY_CSV, dtype={"code": str})
    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"], errors="coerce")
    return df


STRATEGIES = {
    "v4_biotech": {
        "name": "v4 biotech",
        "emoji": "🧬",  # tagged data only — never concatenated into a rendered label (DESIGN Emoji=0)
        "loader": load_v4,
        "pick_date": "2026-04-22",
        "benchmark": "XBI",
        "benchmark_name": "SPDR S&P Biotech",
        "currency": "USD",
        "initial_capital": 1_000_000,
    },
    "v5_biotech": {
        "name": "v5 biotech",
        "emoji": "🧬",
        "loader": load_v5,
        "pick_date": "2026-05-15",
        "benchmark": "XBI",
        "benchmark_name": "SPDR S&P Biotech",
        "currency": "USD",
        "initial_capital": 1_000_000,
        # renders INSIDE the v4_biotech group tab (version toggle), not its own tab.
        "version_of": "v4_biotech",
    },
    "v6_biotech": {
        "name": "v6 biotech",
        "emoji": "🧬",
        "loader": load_v6,
        # effective = 2026-07-09 换仓 (v5.2 fresh run, 22 支等权: 20 引擎 + 2 人工 ALNY/GPCR); forward NAV anchored here.
        "pick_date": "2026-07-09",
        "top_n": 22,
        "benchmark": "XBI",
        "benchmark_name": "SPDR S&P Biotech",
        "currency": "USD",
        "initial_capital": 1_000_000,
        # current (default) version toggle inside the v4_biotech group tab.
        "version_of": "v4_biotech",
    },
    # HD benchmarks (George 2026-06-12): primary 3466.HK Hang Seng High
    # Dividend 30 ETF (was 3110.HK), plus ^HSI as a broad-market reference
    # overlay — both versions, so the v1/v2 curves stay comparable.
    "hk_hd": {
        "name": "HK 高股息 v1",
        "emoji": "💰",
        "loader": load_hd,
        "pick_date": "2026-03-20",
        "benchmark": "3466.HK",
        "benchmark_name": "恒生高股息30",
        "benchmark2": "^HSI",
        "benchmark2_name": "恒生指数",
        "currency": "HKD",
        "initial_capital": 1_000_000,
    },
    "hk_hd_v2": {
        "name": "HK 高股息 v2",
        "emoji": "💰",
        "loader": load_hd_v2,
        "pick_date": "2026-06-11",
        "benchmark": "3466.HK",
        "benchmark_name": "恒生高股息30",
        "benchmark2": "^HSI",
        "benchmark2_name": "恒生指数",
        "currency": "HKD",
        "initial_capital": 1_000_000,
        # score-weighted book: weight_pct column = absolute %, plus idle cash.
        "weight_col": "weight_pct",
        "cash_pct": 12.0,
        # page renders this INSIDE the hk_hd tab (version toggle), not as its
        # own tab — see HD_VERSION_GROUP filter in 4_Strategy_Picks.py.
        "version_of": "hk_hd",
    },
    "hk_hd_v3": {
        "name": "HK 高股息 v3",
        "emoji": "💰",
        "loader": load_hd_v3,
        # effective = George sign-off date (2026-07-07), not the 2026-07-06 data
        # date — the book goes live on approval, forward NAV anchored here.
        "pick_date": "2026-07-07",
        "benchmark": "3466.HK",
        "benchmark_name": "恒生高股息30",
        "benchmark2": "^HSI",
        "benchmark2_name": "恒生指数",
        "currency": "HKD",
        "initial_capital": 1_000_000,
        # score-weighted book (Wind single-source): weight_pct = absolute %, + idle cash.
        "weight_col": "weight_pct",
        "cash_pct": 12.0,
        # renders inside the hk_hd tab as the current (default) version toggle.
        "version_of": "hk_hd",
    },
}


@st.cache_data(ttl=3600, show_spinner="Fetching picks prices…")
def fetch_picks_closes(yf_syms: tuple[str, ...], start: str,
                       _ovr_mtime: float = 0.0) -> pd.DataFrame:
    """Wide-format close DataFrame for picks. Live yfinance, cached 1h.

    yfinance occasionally fails a whole burst of symbols in one batch
    ("possibly delisted" on clearly-listed names = rate-limit artifact, seen
    2026-06-11 with 12/21 HK names incl. the benchmark). A partial frame
    would be CACHED for 1h and silently shrink the book, so missing symbols
    get one re-download after a short pause; if still missing, the page is
    warned rather than left silently degraded.
    """
    if not yf_syms:
        return pd.DataFrame()
    end = (date.today() + timedelta(days=1)).isoformat()

    def _download(syms: tuple[str, ...]) -> dict[str, pd.Series]:
        try:
            d = yf.download(
                list(syms), start=start, end=end,
                auto_adjust=True, progress=False, threads=True, group_by="ticker",
            )
        except Exception as e:
            st.warning(f"Live fetch failed: {e}")
            return {}
        if d.empty:
            return {}
        if len(syms) == 1:
            sym = syms[0]
            if isinstance(d.columns, pd.MultiIndex):
                d.columns = d.columns.droplevel(1)
            if "Close" in d.columns:
                ser = d["Close"].dropna()
                if not ser.empty:
                    return {sym: ser}
            return {}
        out: dict[str, pd.Series] = {}
        for sym in syms:
            try:
                if sym in d.columns.get_level_values(0):
                    ser = d[sym]["Close"].dropna()
                    if not ser.empty:
                        out[sym] = ser
            except Exception:
                pass
        return out

    out = _download(tuple(yf_syms))
    missing = tuple(s for s in yf_syms if s not in out)
    if missing:
        time.sleep(2)  # rate-limit pause before the retry batch
        out.update(_download(missing))

    # Acquired/delisted picks (yfinance returns nothing): synthesize a held-then-
    # cashed-out series — entry_price until delist_date, then final cash price — so
    # the book books the REALIZED return (final/entry) instead of dropping the name.
    # entry defaults to final (flat) for merger-arb picks. Done BEFORE the missing-
    # warning so a known cash-out is never flagged as a fetch failure.
    overrides = _delisted_overrides(_ovr_mtime)
    idx = pd.bdate_range(start=start, end=date.today())
    for sym in yf_syms:
        if sym in overrides and len(idx):
            entry, final, delist_ts = overrides[sym]
            ser = pd.Series(final, index=idx, name=sym, dtype="float64")
            if delist_ts is not None and entry != final:
                ser[idx < delist_ts] = entry  # held at entry until cash-out step
            out[sym] = ser

    still = [s for s in yf_syms if s not in out]
    if still:
        st.warning(f"Price fetch incomplete after retry: {', '.join(still)}")
    if not out:
        return pd.DataFrame()
    return pd.DataFrame(out).sort_index()


def compute_strategy_returns(
    closes: pd.DataFrame, pick_date: str, rebalance_freq: str = "M",
    portfolio_syms: list[str] | tuple[str, ...] | None = None,
    weights: pd.Series | None = None, cash_pct: float = 0.0,
) -> tuple[pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """Compute since-inception cumulative return (indexed=100) + TWO portfolio
    curves (equal-weight by default) + per-window returns table.

    Weighted mode (HD v2): pass `weights` (pd.Series indexed by yf_sym, DECIMAL
    fractions, e.g. 0.0641) + `cash_pct` (12.0 = 12% idle cash, 0 return).
    Curves switch to pm.weighted_* (buy & hold drift + reset-to-target monthly);
    `weights=None` keeps the original equal-weight path — v1/v4/v5 unchanged.

    The strategy is a SCORING model: rank by score, build the portfolio from the
    **Top 20** by rank (equal-weight headline; `portfolio_syms` = those 20 yf
    symbols). The portfolio curves (`normed` / `portfolio` / `portfolio_rebalanced`)
    are computed ONLY on `portfolio_syms`; the per-ticker `perf` table is computed
    on ALL columns of `closes` (so the page can show the full ranked universe in an
    expander). If `portfolio_syms` is None the portfolio uses every column.

    Dual-track: buy & hold (shipped curve) + monthly-rebalanced (reproducible-
    strategy curve). Both computed once here — `charts.py` consumes the series.

    Returns: (normed, portfolio, portfolio_rebalanced, perf_table)
    """
    _empty4 = (pd.DataFrame(), pd.Series(dtype=float),
               pd.Series(dtype=float), pd.DataFrame())
    if closes.empty:
        return _empty4
    closes = closes.sort_index()
    anchor_ts = pd.Timestamp(pick_date)
    sub_all = closes[closes.index >= anchor_ts]
    if sub_all.empty:
        return _empty4
    # M2 audit fix: forward-fill missing closes (trading halts) before normalization
    # so portfolio weight per ticker stays constant; avoid bias toward currently-trading subset
    sub_all = sub_all.ffill()
    # Portfolio = Top-N subset (by rank, passed as portfolio_syms); fall back to all.
    if portfolio_syms:
        port_cols = [c for c in portfolio_syms if c in sub_all.columns]
        sub = sub_all[port_cols] if port_cols else sub_all
    else:
        sub = sub_all
    # Single-source math (lib.portfolio_math — pure, unit-tested in tests/test_strategy.py)
    normed = pm.normalize(sub)
    if weights is not None:
        cash_w = float(cash_pct) / 100.0
        portfolio = pm.weighted_buy_hold_portfolio(normed, weights, cash_weight=cash_w)
        portfolio_rebalanced = pm.weighted_rebalanced_portfolio(
            sub, weights, cash_weight=cash_w, freq=rebalance_freq)
    else:
        portfolio = pm.buy_hold_portfolio(normed)
        portfolio_rebalanced = pm.rebalanced_portfolio(sub, freq=rebalance_freq)

    # Per-window returns
    rows = []
    NAN = float("nan")
    for ticker in closes.columns:
        ser = closes[ticker].dropna()
        if ser.empty:
            continue
        last = float(ser.iloc[-1])
        after_pick = ser[ser.index >= anchor_ts]
        since = float((last / after_pick.iloc[0] - 1) * 100) if not after_pick.empty else NAN

        def ret_back(n: int) -> float:
            if len(ser) <= n:
                return NAN
            prev = ser.iloc[-n - 1]
            if pd.isna(prev) or prev == 0:
                return NAN
            return float((last / prev - 1) * 100)

        rows.append({
            "Ticker": ticker,
            "Last": last,
            "1D %": ret_back(1),
            "5D %": ret_back(5),
            "15D %": ret_back(15),
            "30D %": ret_back(30),
            "Since %": since,
        })
    perf = pd.DataFrame(rows).set_index("Ticker") if rows else pd.DataFrame()
    return normed, portfolio, portfolio_rebalanced, perf
