"""SQLite read helpers for Streamlit pages."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = REPO_ROOT / "data" / "snapshots.db"


@st.cache_data(ttl=600)
def load_domain_cfg(cfg_path: str) -> dict:
    """Load a domain YAML config (e.g. config/domains/{healthcare,ai}.yml).

    cfg_path is a HASHED argument, so each domain gets a DISTINCT cache entry.
    This is load-bearing: Streamlit keys @st.cache_data by
    (func.__module__, func.__qualname__, source_text) ONLY — module globals are
    invisible to the key. Pages are all exec'd under module "__main__", so the
    previous per-page `def load_domain_cfg()` (no args, identical body, differing
    only by a module-global DOMAIN_CFG) collapsed into ONE shared bucket across
    every page. Whichever page loaded first won for the whole TTL, and siblings
    silently got the wrong domain's sectors. Keying on the path fixes it by
    construction; centralizing here removes the duplicated def that bred the bug.
    """
    with open(cfg_path) as f:
        return yaml.safe_load(f)


def connect() -> sqlite3.Connection:
    """Read-only connection."""
    return sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)


def query(sql: str, params: tuple | list | dict | None = None) -> pd.DataFrame:
    conn = connect()
    try:
        return pd.read_sql_query(sql, conn, params=params or ())
    finally:
        conn.close()


# ---------- metadata ----------
@st.cache_data(ttl=300)
def latest_snapshot_date() -> str | None:
    df = query("SELECT MAX(date) AS d FROM multiples_daily")
    return df["d"].iloc[0] if not df.empty else None


@st.cache_data(ttl=300)
def last_fetch_utc() -> str | None:
    df = query("SELECT value FROM meta WHERE key = 'last_fetch_utc'")
    return df["value"].iloc[0] if not df.empty else None


@st.cache_data(ttl=300)
def universe_summary() -> pd.DataFrame:
    return query(
        "SELECT domain, sector, COUNT(*) AS n FROM universe_member "
        "WHERE sector != '_coverage' GROUP BY domain, sector ORDER BY domain, sector"
    )


# ---------- universe ----------
@st.cache_data(ttl=600)
def _has_column(table: str, col: str) -> bool:
    """Does `table` have `col` in the DB this process is reading?

    HOTFIX 2026-08-20: universe_member.status / secondary_listing 由
    jobs/load_universe.py 的 ensure_status_column() 幂等迁移添加, 但**应用是直接
    读 data/snapshots.db 的, 从不跑那个迁移**。代码先于 cron 部署时(本次就是),
    app 会对着还没长出新列的库执行 `WHERE status IS NULL` → OperationalError,
    整站 500。故所有依赖新列的过滤都必须先问一句列在不在。

    迁移跑过之后本函数恒真, 过滤照常生效; 跑之前退化为不过滤(退市股会短暂出现
    在扫描里)——这是可接受的降级, 比整站崩掉好。
    """
    try:
        with sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True) as conn:
            return col in {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
    except Exception:
        return False


def _active_clause(prefix: str = "") -> str:
    """`AND <p>status IS NULL` when the column exists, else empty string."""
    return f" AND {prefix}status IS NULL" if _has_column("universe_member", "status") else ""


@st.cache_data(ttl=300)
def all_tickers() -> list[str]:
    where = " WHERE status IS NULL" if _has_column("universe_member", "status") else ""
    return query(
        f"SELECT DISTINCT ticker FROM universe_member{where}"
    )["ticker"].tolist()


@st.cache_data(ttl=300)
def sector_tickers(domain: str, sector: str) -> pd.DataFrame:
    return query(
        "SELECT ticker, name_cn, name_en, region, "
        + ("COALESCE(secondary_listing, 0) AS secondary_listing "
           if _has_column("universe_member", "secondary_listing")
           else "0 AS secondary_listing ")
        + "FROM universe_member WHERE domain = ? AND sector = ? "
        + _active_clause()
        + " ORDER BY ticker",
        (domain, sector),
    )


@st.cache_data(ttl=300)
def ticker_to_name(prefer_cn: bool = True) -> dict[str, str]:
    """Resolve display name. M10 audit fix: default to Chinese first (中文卖方 习惯).

    NOTE: 刻意 **不** 过滤 status —— 已退市/更名的标的仍需解析出中文名, 否则
    Strategy Picks 里被收购的历史 pick(如 FOLD/阿米库斯)会退化成裸代码显示。
    扫描与排序路径的过滤在 all_tickers / sector_tickers / top_movers 三处。

    Set prefer_cn=False to fall back to English-first."""
    if prefer_cn:
        col_expr = "COALESCE(name_cn, name_en, ticker)"
    else:
        col_expr = "COALESCE(name_en, name_cn, ticker)"
    df = query(
        f"SELECT ticker, {col_expr} AS display_name "
        "FROM universe_member GROUP BY ticker"
    )
    return dict(zip(df["ticker"], df["display_name"]))


# ---------- per-domain market frame ----------
@dataclass(frozen=True)
class MarketFrame:
    """Everything a domain page needs off ONE cached read.

    R3 audit §4/§8.3: the heatmap issued `sector_tickers` once per sub-sector and
    then pulled the wide close frame twice (local + USD), 16 queries where 3 do.
    `close`/`close_usd`/`multiples` cover the domain's ACTIVE members only, which
    is what every scan path already filtered to.

    `meta` is deliberately NOT status-filtered — same reason `ticker_to_name` is
    not (see its NOTE above): a delisted or renamed pick must still resolve to a
    name. It carries a `status` column so callers that need the active set can
    filter, and `members` is pre-filtered for them.
    """

    close: pd.DataFrame                      # index=date, columns=ticker, local ccy
    close_usd: pd.DataFrame                  # same shape, COALESCE(close_usd, close)
    multiples: pd.DataFrame                  # index=ticker, latest multiples_daily row
    meta: pd.DataFrame                       # index=ticker, universe_member one row per ticker
    members: dict[str, tuple[str, ...]]      # sector -> ACTIVE tickers, ordered by ticker
    as_of: str | None                        # max(prices_daily.date) inside this frame


def _universe_subquery(domain: str | None) -> str:
    """`SELECT DISTINCT ticker …` for the domain's ACTIVE members.

    Used as a sub-select so neither price nor multiples query has to interpolate a
    500-placeholder `IN (?,?,…)` list — the SQL text stays constant.
    """
    return ("SELECT DISTINCT ticker FROM universe_member WHERE 1=1"
            + (" AND domain = ?" if domain else "") + _active_clause())


@st.cache_data(ttl=300)
def _frame_prices(domain: str | None) -> tuple[pd.DataFrame, pd.DataFrame, str | None]:
    """Local AND USD wide closes in ONE pass (audit §4: the double pull)."""
    args: tuple = (domain,) if domain else ()
    px = query(
        f"SELECT p.ticker, p.date, p.close, "
        f"       COALESCE(p.close_usd, p.close) AS close_usd "
        f"FROM prices_daily p JOIN ({_universe_subquery(domain)}) u ON u.ticker = p.ticker "
        f"ORDER BY p.ticker, p.date",
        args,
    )
    if px.empty:
        return pd.DataFrame(), pd.DataFrame(), None
    as_of = str(px["date"].max())
    px["date"] = pd.to_datetime(px["date"])
    return (px.pivot(index="date", columns="ticker", values="close").sort_index(),
            px.pivot(index="date", columns="ticker", values="close_usd").sort_index(),
            as_of)


@st.cache_data(ttl=300)
def _frame_multiples(domain: str | None) -> pd.DataFrame:
    df = query(
        f"SELECT m.* FROM multiples_daily m JOIN ("
        f"  SELECT ticker, MAX(date) AS d FROM multiples_daily "
        f"  WHERE ticker IN ({_universe_subquery(domain)}) GROUP BY ticker"
        f") l ON l.ticker = m.ticker AND m.date = l.d",
        (domain,) if domain else (),
    )
    return df.set_index("ticker") if not df.empty else df


@st.cache_data(ttl=300)
def _frame_meta(domain: str | None) -> pd.DataFrame:
    status_col = ("MAX(status)" if _has_column("universe_member", "status") else "NULL")
    sec_col = ("MAX(COALESCE(secondary_listing, 0))"
               if _has_column("universe_member", "secondary_listing") else "0")
    df = query(
        f"SELECT ticker, MAX(name_cn) AS name_cn, MAX(name_en) AS name_en, "
        f"       MAX(region) AS region, MAX(domain) AS domain, "
        f"       GROUP_CONCAT(DISTINCT sector) AS sectors, "
        f"       {status_col} AS status, {sec_col} AS secondary_listing "
        f"FROM universe_member{' WHERE domain = ?' if domain else ''} "
        f"GROUP BY ticker ORDER BY ticker",
        (domain,) if domain else (),
    )
    return df.set_index("ticker") if not df.empty else df


@st.cache_data(ttl=300)
def _frame_members(domain: str | None) -> dict[str, tuple[str, ...]]:
    """sector -> ACTIVE tickers, ordered by ticker (i.e. `sector_tickers`'s roster).

    First-wins assignment across sectors stays the CALLER's business — `heatmap.py`
    walks its configured sector order and keeps a ticker's first appearance.
    """
    meta = _frame_meta(domain)
    out: dict[str, list[str]] = {}
    if meta.empty:
        return {}
    for tkr, sectors, status in zip(meta.index, meta["sectors"], meta["status"]):
        if pd.notna(status):
            continue
        for sec in str(sectors or "").split(","):
            if sec:
                out.setdefault(sec, []).append(tkr)
    return {k: tuple(v) for k, v in out.items()}


def market_frame(domain: str | None = None) -> MarketFrame:
    """One domain's whole cross-section: three queries, four cache buckets.

    `domain=None` is the entire universe — what `quote_table`, `top_movers` and
    `returns_for` want. The argument is HASHED by each `_frame_*` helper, so
    healthcare / ai / etf / None land in distinct buckets; this is the same
    discipline `load_domain_cfg` documents above, and for the same reason.

    NOT itself `@st.cache_data` — deviation from design A.1, which asserted "a
    dataclass of DataFrames pickles fine". It does not, reliably: `cache_data`
    pickles the return value, and pickling a value by class reference fails with
    `PicklingError: it's not the same object as lib.db.MarketFrame` the moment
    `lib.db` is imported twice. `tests/test_hc_overview_cache_key.py` reproduces
    that by clearing `lib.*` out of `sys.modules` and re-importing — which is
    precisely what a Streamlit hot reload does, so the failure mode is a 500 on
    the deployed app, not a test artifact. Caching the DataFrames/tuple/dict
    pieces instead keeps every cached value a builtin container and makes this
    assembler free.
    """
    close, close_usd, as_of = _frame_prices(domain)
    return MarketFrame(
        close=close,
        close_usd=close_usd,
        multiples=_frame_multiples(domain),
        meta=_frame_meta(domain),
        members=_frame_members(domain),
        as_of=as_of,
    )


@st.cache_data(ttl=300)
def returns_for(tickers: tuple[str, ...], as_of: str | None = None,
                basis: str = "usd", domain: str | None = None) -> pd.DataFrame:
    """Cached `compute_returns` over a slice of a market frame.

    `compute_returns` takes a DataFrame, which Streamlit cannot hash, so the cache
    lives on this keyed shell instead. `as_of` (pass `market_frame(...).as_of`) is
    not read — it is in the signature so the key MOVES when new prices land and
    stays PUT across the re-runs a slider triggers, which is exactly the 258 ms
    recompute audit §5 measured on `3_Sector_Heatmap.py`'s min-mcap slider.

    Per-ticker results are independent, so `returns_for(all).loc[subset]` equals
    `returns_for(subset)` — call it once per domain and slice, do not call it once
    per sub-sector.

    `domain` picks WHICH frame to source from, and exists purely to avoid a cold-load
    regression: design A.2 sources this from `market_frame(None)` unconditionally,
    which makes a single domain page materialise the 494-ticker universe frame ON TOP
    of its own 326-ticker one. Measured on `3_Sector_Heatmap.py`, that pushed the cold
    AppTest render from 0.30 s to 0.39 s. Pass the same domain you passed
    `market_frame` and there is only ever one frame in play.
    """
    mf = market_frame(domain)
    src = mf.close_usd if basis == "usd" else mf.close
    if src.empty:
        return pd.DataFrame()
    # Sorted+deduped so the row order matches what the pivot in
    # `get_close_series_usd` always produced, whatever order the caller collected
    # its tickers in — and so two callers with the same SET share a cache bucket.
    cols = sorted(set(tickers) & set(src.columns))
    if not cols:
        return pd.DataFrame()
    return compute_returns(src[cols])


# ---------- prices & returns ----------
@st.cache_data(ttl=300)
def get_close_series(tickers: tuple[str, ...]) -> pd.DataFrame:
    """Wide-format close prices: index=date, columns=ticker. Tuple for cache.

    DEPRECATED for multi-ticker use — prefer `market_frame(domain).close`, which
    fetches local and USD closes in ONE pass instead of two (audit §4).

    Deliberately NOT a wrapper over the frame, despite the "thin wrapper" plan:
    it is still the right call for a SINGLE ticker (a 1-column pull beats
    materialising a domain frame) and it is the ONLY correct call for tickers the
    frame does not carry — Ticker Drill on a DELISTED name, and `ipo_tracker`'s
    yfinance symbols, which are not universe members at all. Serving those from
    the frame would hand back an empty column, and slicing the frame would widen
    every caller's date index to the union of the whole universe.
    """
    if not tickers:
        return pd.DataFrame()
    placeholders = ",".join("?" * len(tickers))
    df = query(
        f"SELECT ticker, date, close FROM prices_daily "
        f"WHERE ticker IN ({placeholders}) ORDER BY date",
        tuple(tickers),
    )
    if df.empty:
        return pd.DataFrame()
    df["date"] = pd.to_datetime(df["date"])
    return df.pivot(index="date", columns="ticker", values="close").sort_index()


# Split / bad-tick guard: a single-day DROP beyond this is almost never a real
# return — it's an un-back-adjusted forward split (yfinance sometimes MISSES the
# split entirely, e.g. 5801.T / 3110.T 2026-06 ~1:10, so the DB mixes pre- and
# post-split closes) or a bad tick. Any window spanning such a drop is suppressed
# (NaN) so the heatmap drops the tile rather than printing a fake -90%.
# DOWNWARD-only + 0.75 by design: real biotech catalysts pop UP big (e.g. 2565.HK
# +66% on 2026-05-18, no split — must NOT be suppressed), and genuine one-day
# crashes rarely exceed -75% (2617.HK -60% real distress stays), while
# forward-split jumps are -80/-90%.
SPLIT_GUARD = 0.75

# window label -> lookback in VALID observations (not calendar days)
_RET_WINDOWS = {"1d_%": 1, "5d_%": 5, "1m_%": 21, "3m_%": 63, "6m_%": 126, "60d_%": 60}
_RET_COLS = ["last", "1d_%", "5d_%", "1m_%", "3m_%", "6m_%", "ytd_%", "60d_%"]


def compute_returns(closes: pd.DataFrame) -> pd.DataFrame:
    """Per-ticker return windows. Each ticker uses its OWN last valid close —
    avoids the ragged-tail bug across markets (JP closes earlier than US).
    Output index=ticker, columns=`_RET_COLS`.

    R3 audit §5 / PR 2: this used to be a per-ticker Python loop costing 258 ms
    on 494 tickers and re-running on every slider tick. It is now column-wise;
    `tests/test_compute_returns_equiv.py` pins it against a verbatim copy of the
    loop over the whole committed DB, so the numbers are byte-identical.

    The trick is `rev`: the 1-based rank of each VALID observation counted from
    the end of its own column (1 = last valid bar). Every per-ticker `.dropna()`
    positional index in the old loop becomes a mask on `rev`, so the ragged tails
    stay per-ticker without ever leaving vectorized land.
    """
    if closes.empty:
        return pd.DataFrame()

    C = closes.sort_index()
    valid = C.notna()
    n_valid = valid.sum()                                # Series[ticker]
    rev = valid[::-1].cumsum()[::-1].where(valid)        # 1 = last valid, 2 = prior, …

    # One gather instead of a full-frame mask per window: `back[k]` is the close
    # k valid observations back, per column (NaN where the column is too short).
    # Doing this as 7 separate `C.where(rev == k+1).max()` passes cost 38 of the
    # function's 75 ms.
    _depth = max(_RET_WINDOWS.values()) + 1
    _rv, _cv = rev.to_numpy(), C.to_numpy(dtype="float64")
    _sel = np.isfinite(_rv) & (_rv <= _depth)
    _r, _c = np.nonzero(_sel)
    back = np.full((_depth, C.shape[1]), np.nan)
    back[_rv[_r, _c].astype(np.intp) - 1, _c] = _cv[_r, _c]

    def at(k: int) -> pd.Series:
        """Close k VALID observations back, per column."""
        return pd.Series(back[k], index=C.columns)

    last = at(0)

    # `C.ffill().shift(1)` is the previous VALID close, so this equals the old
    # `ser.dropna().pct_change()` on every valid row. `min_bad` = the smallest
    # `rev` carrying a guard-tripping drop, i.e. the most RECENT one; a window
    # reaching n bars back crosses it iff min_bad <= n.
    pc = C / C.ffill().shift(1) - 1.0
    bad = (pc < -SPLIT_GUARD) & valid
    min_bad = rev.where(bad).min()                       # NaN when the column is clean

    out: dict[str, pd.Series] = {"last": last}
    for col, n in _RET_WINDOWS.items():
        prev = at(n).replace(0.0, np.nan)                # anchor of 0 → undefined
        ok = (n_valid > n) & (min_bad.isna() | (min_bad > n))
        out[col] = ((last / prev - 1.0) * 100.0).where(ok)

    # YTD: anchor on the LAST close STRICTLY BEFORE Jan 1 of the series' own
    # latest year (each ticker uses its own year so cross-year DB rows work).
    #
    # R3 audit C1 — anchoring on the FIRST close *of* the year silently drops the
    # Jan-1 gap: shown = (1+true)/(1+jan_gap) − 1. Measured across 490 tickers:
    # median |error| 2.40pp, p90 10.6pp, max 86.0pp. The prior-year close is the
    # standard YTD base — a stock that gapped +10% on the first trading day of
    # January has earned that 10%.
    #
    # Fallback: a ticker listed mid-year (or backfilled only from January) has no
    # prior-year bar; keep the first-close-of-year behaviour there, as there is no
    # better base and the gap does not exist.
    pos = len(C) - 1 - np.argmax(valid.to_numpy()[::-1], axis=0)
    years = pd.Series(C.index[pos].year, index=C.columns).where(n_valid > 0)
    ytd = pd.Series(np.nan, index=C.columns, dtype="float64")
    for y in years.dropna().unique():
        cols = years.index[years == y]
        cut = pd.Timestamp(f"{int(y)}-01-01")
        pre, post = C.loc[C.index < cut, cols], C.loc[C.index >= cut, cols]
        anchor = pre.ffill().iloc[-1] if len(pre) else pd.Series(np.nan, index=cols)
        if len(post):                                    # no prior-year bar → fallback
            anchor = anchor.fillna(post.bfill().iloc[0])
        anchor = anchor.replace(0.0, np.nan)
        # bars from the anchor to the last one = 1 + n_ytd, so the guard window
        # spans rev 1..n_ytd — identical to the loop's `window.pct_change()`.
        n_ytd = valid.loc[C.index >= cut, cols].sum()
        clean = min_bad[cols].isna() | (min_bad[cols] > n_ytd)
        ytd.loc[cols] = ((last[cols] / anchor - 1.0) * 100.0).where(clean)
    out["ytd_%"] = ytd

    return pd.DataFrame(out).reindex(columns=_RET_COLS)


# ---------- multiples ----------
@st.cache_data(ttl=300)
def latest_multiples(tickers: tuple[str, ...]) -> pd.DataFrame:
    """Latest multiples_daily snapshot per ticker. Includes M1 close_usd + M11 mcap_tier.

    DEPRECATED for domain-wide use — prefer `market_frame(domain).multiples`,
    which runs the same query once per domain instead of once per sub-sector and
    without a 500-placeholder `IN` list. Kept for single-ticker callers
    (`6_Ticker_Drill.py`) and comp sets that are not a domain.
    """
    if not tickers:
        return pd.DataFrame()
    placeholders = ",".join("?" * len(tickers))
    df = query(
        f"""
        SELECT m.* FROM multiples_daily m
        INNER JOIN (
          SELECT ticker, MAX(date) AS max_date
          FROM multiples_daily
          WHERE ticker IN ({placeholders})
          GROUP BY ticker
        ) latest
        ON m.ticker = latest.ticker AND m.date = latest.max_date
        """,
        tuple(tickers),
    )
    if df.empty:
        return df
    return df.set_index("ticker")


@st.cache_data(ttl=300)
def rule_of_40_comps(tickers: tuple[str, ...]) -> pd.DataFrame:
    """Rule-of-40 valuation-matrix inputs for a software comp set (Model Drill ③).

    Joins the latest multiples_daily.ev_sales (Y axis) with company_profile's
    revenueGrowth + freeCashflow/totalRevenue (X axis = Rule of 40 = revenue
    growth % + FCF margin %). Everything comes from the daily snapshot, so the
    matrix tracks the current market — re-run jobs/fetch_eod to refresh. Rows
    missing any input (or with non-positive revenue) are dropped. Returns a frame
    indexed by ticker with name_cn / name_en / ev_sales / rev_growth / fcf_margin /
    rule40 (the last three already in PERCENT points)."""
    if not tickers:
        return pd.DataFrame()
    ph = ",".join("?" * len(tickers))
    df = query(
        f"""
        SELECT u.ticker,
               MIN(u.name_cn) AS name_cn, MIN(u.name_en) AS name_en,
               m.ev_sales, p.revenueGrowth, p.totalRevenue, p.freeCashflow
        FROM universe_member u
        INNER JOIN (
          SELECT ticker, MAX(date) AS d FROM multiples_daily
          WHERE ticker IN ({ph}) GROUP BY ticker
        ) lm ON lm.ticker = u.ticker
        INNER JOIN multiples_daily m ON m.ticker = u.ticker AND m.date = lm.d
        LEFT JOIN company_profile p ON p.ticker = u.ticker
        WHERE u.ticker IN ({ph})
        GROUP BY u.ticker, m.ev_sales, p.revenueGrowth, p.totalRevenue, p.freeCashflow
        """,
        tuple(tickers) + tuple(tickers),
    )
    if df.empty:
        return pd.DataFrame()
    df = df.dropna(subset=["ev_sales", "revenueGrowth", "totalRevenue", "freeCashflow"])
    df = df[df["totalRevenue"] > 0]
    if df.empty:
        return df
    df["rev_growth"] = df["revenueGrowth"] * 100.0
    df["fcf_margin"] = df["freeCashflow"] / df["totalRevenue"] * 100.0
    df["rule40"] = df["rev_growth"] + df["fcf_margin"]
    return df.set_index("ticker")[["name_cn", "name_en", "ev_sales",
                                   "rev_growth", "fcf_margin", "rule40"]]


@st.cache_data(ttl=300)
def adv_20d(ticker: str) -> float | None:
    """20-trading-day average daily turnover (close × volume) in the stock's LOCAL
    currency — a liquidity gauge (small-cap HK/A names can be hard to build/exit).
    Returns None when no volume is on file. Reads the committed snapshots.db only
    (works offline; no live call)."""
    df = query(
        "SELECT close, volume FROM prices_daily WHERE ticker = ? "
        "ORDER BY date DESC LIMIT 20",
        (ticker,),
    )
    if df.empty or df["volume"].isna().all():
        return None
    turn = (df["close"] * df["volume"]).dropna()
    return float(turn.mean()) if not turn.empty else None


@st.cache_data(ttl=3600)
def shares_outstanding(ticker: str) -> float | None:
    """Total shares outstanding from company_profile (yfinance snapshot; 484/494
    tickers non-null). Used by the Ticker Drill terminal for the EOD turnover-rate
    cell — None → the cell is simply not rendered (CONTRACT T8 only-available)."""
    df = query(
        "SELECT sharesOutstanding FROM company_profile WHERE ticker = ?",
        (ticker,),
    )
    if df.empty or pd.isna(df.iloc[0, 0]):
        return None
    v = float(df.iloc[0, 0])
    return v if v > 0 else None


@st.cache_data(ttl=300)
def get_close_series_usd(tickers: tuple[str, ...]) -> pd.DataFrame:
    """M1 audit fix: USD-converted close series (so cross-region returns are comparable).

    Falls back to local close × FX if close_usd is null (legacy rows pre-M1 fix).

    DEPRECATED for multi-ticker use — prefer `market_frame(domain).close_usd`.
    Kept for single-ticker and non-universe callers; see `get_close_series` for
    why it is not a wrapper over the frame.
    """
    if not tickers:
        return pd.DataFrame()
    placeholders = ",".join("?" * len(tickers))
    df = query(
        f"SELECT ticker, date, COALESCE(close_usd, close) AS close_usd "
        f"FROM prices_daily WHERE ticker IN ({placeholders}) ORDER BY date",
        tuple(tickers),
    )
    if df.empty:
        return pd.DataFrame()
    df["date"] = pd.to_datetime(df["date"])
    return df.pivot(index="date", columns="ticker", values="close_usd").sort_index()


# ---------- top movers ----------
@st.cache_data(ttl=300)
def top_movers(n: int = 10, domain: str | None = None,
               prefer_cn: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Top n gainers and losers by 1-day return across universe tickers, optionally
    scoped to a single `domain` (e.g. 'healthcare' / 'ai') so each home-page benchmark
    category can show its OWN movers (HC movers under HC, AI movers under AI).

    R3 audit H12: the name column used to be hard-wired to `ticker_to_name()`'s
    Chinese-first default, so EN mode showed Chinese names on every movers table.
    `prefer_cn` IS hashed into the cache key (no leading underscore) → each
    language gets its own bucket instead of one poisoning the other. The default
    stays True so any caller that has not been updated keeps today's behaviour.
    """
    if domain:
        tickers = tuple(
            query("SELECT DISTINCT ticker FROM universe_member "
                  "WHERE domain = ?" + _active_clause(),
                  (domain,))["ticker"].tolist()
        )
    else:
        tickers = tuple(all_tickers())
    if not tickers:
        return pd.DataFrame(), pd.DataFrame()
    closes = get_close_series(tickers)
    rets = compute_returns(closes)
    if rets.empty:
        return pd.DataFrame(), pd.DataFrame()
    name_map = ticker_to_name(prefer_cn=prefer_cn)
    rets["name"] = rets.index.map(name_map)
    rets = rets[["name", "last", "1d_%", "5d_%", "1m_%", "ytd_%"]]
    gainers = rets.sort_values("1d_%", ascending=False).head(n)
    losers = rets.sort_values("1d_%", ascending=True).head(n)
    return gainers, losers
