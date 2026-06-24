"""HK healthcare IPO tracker — local Wind + Futu reconcile job.

Pulls every HK healthcare IPO since 2025-04 (恒瑞 window) and writes:
  data/external/hk_hc_ipo_universe.csv  — static-ish universe (offer, ipo_date, 18A, sub_sector)
  data/external/hk_hc_ipo_tracker.csv   — daily snapshot (close, mktcap, turnover, flags, as_of)
  data/external/hk_hc_ipo_meta.json     — counts + as_of + fx + headline break rates

Run on a Mac with the Wind Financial Terminal logged in AND Futu OpenD running (port 11111):
    python3 jobs/build_hk_ipo_tracker.py
Idempotent; backs up the 3 files (.bak-TS) before overwrite. Wind is the primary source
(prices / market cap / 20-day avg turnover); Futu is an independent cross-check + listing_date.

Methodology guards baked in from the 2026-06-24 3-source cross-check (Wind/Futu/yfinance):
  - Market cap from WIND (yfinance lags HK corporate actions, e.g. 长风 H-share full-circulation).
  - Liquidity tier from WIND 20-session avg turnover only (Futu single-day flips the conclusion).
  - >=20 trading sessions required before a liquidity tier is assigned (else 待定).
  - Suspended names (停牌 / zero 20d turnover) -> tier N/A, excluded from live aggregates.
  - No-offer introduction listings (e.g. 6887 东阳光药) -> excluded from 破发 / return stats.
  - Market cap displayed in 亿 HKD; 3-tier 大>=300 / 中100-300 / 小<100.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
EXT = REPO_ROOT / "data" / "external"
UNIVERSE_CSV = EXT / "hk_hc_ipo_universe.csv"
TRACKER_CSV = EXT / "hk_hc_ipo_tracker.csv"
META_JSON = EXT / "hk_hc_ipo_meta.json"

# ---- methodology constants (cross-check 2026-06-24) ----
FX_HKD_USD = 7.80          # dated spot, within HKMA 7.75-7.85 band; sensitivity <1%
WINDOW_START = "2025-04-01"  # 映恩 2025-04-15 onward (恒瑞 2025-05-23)
ALL_HK_SECTORID = "a002010100000000"   # Wind '全部港股' (~2737 names)
HC_GICS = "医疗保健"
MIN_SESSIONS = 20          # need >=20 HK trading sessions before a liquidity tier is valid
# market-cap tiers in 亿 HKD
MKT_LARGE_YI = 300.0
MKT_MID_YI = 100.0
# liquidity tiers in USD millions (daily avg turnover)
LIQ_HIGH_USDM = 20.0
LIQ_MID_USDM = 10.0
# AI-pharma sub-sector tag (per ai-pharma-ipo-evaluation skill: 三小龙 英矽/剂泰 in this universe)
AI_PHARMA_CODES = {"3696.HK", "7666.HK"}

# Healthcare service / device / diagnostics names get a coarser tag than GICS '医疗保健';
# we keep GICS industry (type 3) as sub_sector and add an is_ai_pharma flag.


def backup(p: Path) -> None:
    if p.exists():
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        bak = p.with_name(p.name + f".bak-{ts}")
        shutil.copy2(p, bak)
        print(f"[backup] {bak.name}")


def fetch_futu(futu_codes: list[str]) -> pd.DataFrame:
    """Independent Futu snapshot (cross-check + listing_date). Subprocess via uv so no global
    futu-api install is needed. Returns empty frame if OpenD is unreachable (Wind still suffices)."""
    script = f'''
import json
from futu import OpenQuoteContext, RET_OK
ctx = OpenQuoteContext(host="127.0.0.1", port=11111)
codes = {futu_codes!r}
ret, snap = ctx.get_market_snapshot(codes)
keep = ["code","last_price","prev_close_price","volume","turnover","listing_date","total_market_val","issued_shares"]
out = snap[keep].to_dict("records") if ret == RET_OK else {{"error": str(snap)}}
ctx.close()
print("FUTU_SENTINEL" + json.dumps(out, default=str))
'''
    try:
        p = subprocess.run(["uv", "run", "--with", "futu-api", "python", "-c", script],
                           capture_output=True, text=True, timeout=120)
        line = [l for l in p.stdout.splitlines() if l.startswith("FUTU_SENTINEL")]
        if not line:
            print(f"[futu] no data (OpenD down?). stderr tail: {p.stderr[-200:]}")
            return pd.DataFrame()
        data = json.loads(line[0].replace("FUTU_SENTINEL", "", 1))
        if isinstance(data, dict):
            print(f"[futu] error: {data}")
            return pd.DataFrame()
        return pd.DataFrame(data)
    except Exception as e:  # noqa: BLE001
        print(f"[futu] skipped: {e}")
        return pd.DataFrame()


def main() -> None:
    from WindPy import w  # local import so `--help`/import elsewhere doesn't need the terminal
    r = w.start(waitTime=60)
    if r.ErrorCode != 0 or not w.isconnected():
        sys.exit(f"[wind] not connected (ErrorCode={r.ErrorCode}) — open the Wind terminal first.")
    today = date.today().isoformat()
    today_c = today.replace("-", "")

    # 1) all HK stocks -> filter to GICS 医疗保健 + ipo_date >= window start
    sec = w.wset("sectorconstituent", f"date={today};sectorid={ALL_HK_SECTORID}")
    if sec.ErrorCode != 0:
        sys.exit(f"[wind] sector pull failed ErrorCode={sec.ErrorCode}")
    all_codes = sec.Data[1]
    rows = []
    B = 600
    for i in range(0, len(all_codes), B):
        chunk = all_codes[i:i + B]
        rr = w.wss(chunk, "sec_name,ipo_date,industry_gics", "industryType=1")
        if rr.ErrorCode != 0:
            sys.exit(f"[wind] wss industry failed ErrorCode={rr.ErrorCode}: {rr.Data[:1]}")
        df = pd.DataFrame({f: c for f, c in zip(rr.Fields, rr.Data)})
        df.insert(0, "code", chunk)
        rows.append(df)
    base = pd.concat(rows, ignore_index=True)
    base["IPO_DATE"] = pd.to_datetime(base["IPO_DATE"], errors="coerce")
    hc = base[(base["INDUSTRY_GICS"].astype(str).str.contains("医疗|Health", na=False)) &
              (base["IPO_DATE"] >= WINDOW_START)].copy()
    hc = hc.sort_values("IPO_DATE").reset_index(drop=True)
    codes = hc["code"].tolist()
    print(f"[wind] HK healthcare IPOs since {WINDOW_START}: {len(codes)}")

    # 2) snapshot + static fields (Wind primary)
    f = "sec_name,sec_englishname,ipo_date,ipo_price,close,mkt_cap_ard,total_shares,trade_status,industry_gics"
    rs = w.wss(codes, f, f"tradeDate={today_c};unit=1;industryType=3")
    snap = pd.DataFrame({fld: c for fld, c in zip(rs.Fields, rs.Data)})
    snap.insert(0, "code", codes)

    # 3) 20-session avg turnover (amt) + trading-session count since ipo_date
    start = (date.today() - timedelta(days=60)).isoformat()
    rd = w.wsd(codes, "amt", start, today, "unit=1")
    avg_amt, tdays, day1 = {}, {}, {}
    for i, c in enumerate(codes):
        ser = pd.to_numeric(pd.Series(rd.Data[i], index=rd.Times), errors="coerce").dropna() if rd.ErrorCode == 0 else pd.Series(dtype=float)
        avg_amt[c] = ser.tail(MIN_SESSIONS).mean() if len(ser) else float("nan")
        ipod = pd.to_datetime(snap.loc[snap["code"] == c, "IPO_DATE"].iloc[0]).strftime("%Y-%m-%d")
        tc = w.tdayscount(ipod, today, "TradingCalendar=HKEX")
        tdays[c] = int(tc.Data[0][0]) if tc.ErrorCode == 0 and tc.Data and tc.Data[0] else None
        # listing-day close — the return base for no-offer introduction listings (e.g. 6887 东阳光药)
        d1 = w.wsd(c, "close", ipod, ipod, "unit=1")
        day1[c] = d1.Data[0][0] if d1.ErrorCode == 0 and d1.Data and d1.Data[0] and pd.notna(d1.Data[0][0]) else None
    snap["wind_avg_amt_hkd"] = snap["code"].map(avg_amt)
    snap["trading_days"] = snap["code"].map(tdays)
    snap["day1_close"] = snap["code"].map(day1)

    # 4) Futu cross-check (independent last_price; flag >5% divergence vs Wind close)
    num = snap["code"].str.split(".").str[0]
    futu = fetch_futu(("HK." + num.str.zfill(5)).tolist())
    futu_price = {}
    if not futu.empty:
        for _, fr in futu.iterrows():
            wc = str(fr["code"]).replace("HK.", "").lstrip("0") + ".HK"
            futu_price[wc] = fr.get("last_price")
        diverged = []
        for _, r in snap.iterrows():
            fp, wc = futu_price.get(r["code"]), r["CLOSE"]
            if pd.notna(fp) and pd.notna(wc) and wc and abs(fp - wc) / wc > 0.05:
                diverged.append(f"{r['code']}(W{wc}/F{fp})")
        print(f"[futu] cross-check ok ({len(futu)} names)"
              + (f"; PRICE DIVERGENCE: {diverged}" if diverged else "; all prices within 5%"))

    # 5) derive fields + apply cross-check guards
    out = []
    for _, r in snap.iterrows():
        code = r["code"]
        name_cn = str(r["SEC_NAME"]) if pd.notna(r["SEC_NAME"]) else code
        offer = r["IPO_PRICE"] if pd.notna(r["IPO_PRICE"]) else None
        close = r["CLOSE"] if pd.notna(r["CLOSE"]) else None
        shares = r["TOTAL_SHARES"] if pd.notna(r["TOTAL_SHARES"]) else None
        status = str(r["TRADE_STATUS"]) if pd.notna(r["TRADE_STATUS"]) else ""
        avg_amt_hkd = r["wind_avg_amt_hkd"] if pd.notna(r["wind_avg_amt_hkd"]) else None
        tdays_n = r["trading_days"]
        no_offer = offer is None
        is_18a = name_cn.endswith("-B") or name_cn.endswith("-P")
        # suspension: Wind 停牌 OR zero 20d turnover (frozen last trade)
        suspended = ("停牌" in status) or (avg_amt_hkd is not None and avg_amt_hkd == 0)
        # market cap (Wind), in 亿 HKD
        cur_mc = r["MKT_CAP_ARD"] if pd.notna(r["MKT_CAP_ARD"]) else (close * shares if close and shares else None)
        cur_mc_yi = round(cur_mc / 1e8, 1) if cur_mc else None
        list_mc_yi = round(offer * shares / 1e8, 1) if (offer and shares) else None
        mkt_tier = (None if cur_mc_yi is None else
                    "大市值" if cur_mc_yi >= MKT_LARGE_YI else
                    "中市值" if cur_mc_yi >= MKT_MID_YI else "小市值")
        # return: offer -> latest close (打新收益, also yields 破发). For no-offer introduction
        # listings (e.g. 6887 东阳光药) fall back to the listing-day close as base so they still
        # carry a 涨幅 — but 破发 stays undefined (no offer to break).
        d1c = r["day1_close"] if pd.notna(r["day1_close"]) else None
        base = offer if offer is not None else d1c
        ret = round((close - base) / base * 100, 1) if (base and close) else None
        ret_base = "发行价" if offer is not None else ("上市首日" if d1c else "—")
        broke = (close < offer) if (offer and close and not no_offer) else None
        # liquidity tier: Wind 20d avg / FX -> USD m; guard sessions + suspension
        tovr_usdm = round(avg_amt_hkd / FX_HKD_USD / 1e6, 2) if avg_amt_hkd else None
        if suspended:
            liq_tier = "停牌"
        elif tdays_n is None or tdays_n < MIN_SESSIONS:
            liq_tier = "待定"
        elif tovr_usdm is None:
            liq_tier = None
        else:
            liq_tier = (">$20M" if tovr_usdm >= LIQ_HIGH_USDM else
                        "$10-20M" if tovr_usdm >= LIQ_MID_USDM else "<$10M")
        # clean = eligible for aggregate stats (has offer, not suspended, >=20 sessions)
        clean = (not no_offer) and (not suspended) and (tdays_n is not None and tdays_n >= MIN_SESSIONS)
        out.append(dict(
            code=code,
            ticker_yf=code.split(".")[0].zfill(4) + ".HK",
            futu_code="HK." + code.split(".")[0].zfill(5),
            name_cn=name_cn,
            name_en=str(r["SEC_ENGLISHNAME"]) if pd.notna(r["SEC_ENGLISHNAME"]) else "",
            ipo_date=pd.to_datetime(r["IPO_DATE"]).strftime("%Y-%m-%d"),
            offer_price_hkd=offer,
            sub_sector=str(r["INDUSTRY_GICS"]) if pd.notna(r["INDUSTRY_GICS"]) else "",
            is_ai_pharma=code in AI_PHARMA_CODES,
            is_18a=is_18a,
            no_offer=no_offer,
            total_shares=shares,
            close=close,
            ret_pct=ret,
            ret_base=ret_base,
            broke=broke,
            cur_mktcap_yi=cur_mc_yi,
            listing_mktcap_yi=list_mc_yi,
            mktcap_tier=mkt_tier,
            avg_turnover_usdm=tovr_usdm,
            liquidity_tier=liq_tier,
            trading_days=tdays_n,
            suspended=suspended,
            trade_status=status,
            clean=clean,
        ))
    res = pd.DataFrame(out).sort_values("ipo_date").reset_index(drop=True)

    # 6) split universe (static) vs tracker (dynamic) and write
    uni_cols = ["code", "ticker_yf", "futu_code", "name_cn", "name_en", "ipo_date",
                "offer_price_hkd", "total_shares", "sub_sector", "is_ai_pharma", "is_18a", "no_offer"]
    trk_cols = ["code", "name_cn", "ipo_date", "offer_price_hkd", "close", "ret_pct", "ret_base",
                "broke", "cur_mktcap_yi", "listing_mktcap_yi", "mktcap_tier", "avg_turnover_usdm",
                "liquidity_tier", "trading_days", "suspended", "trade_status", "is_18a",
                "no_offer", "is_ai_pharma", "sub_sector", "clean"]
    for p in (UNIVERSE_CSV, TRACKER_CSV, META_JSON):
        backup(p)
    res[uni_cols].to_csv(UNIVERSE_CSV, index=False)
    res[trk_cols].to_csv(TRACKER_CSV, index=False)

    clean = res[res["clean"]]
    meta = {
        "as_of": today,
        "source": "Wind (price/mktcap/20d turnover) + Futu OpenD cross-check",
        "fx_hkd_usd": FX_HKD_USD,
        "n_listed": int(len(res)),
        "n_with_offer": int((~res["no_offer"]).sum()),
        "n_suspended": int(res["suspended"].sum()),
        "n_clean": int(len(clean)),
        "break_rate_full": f"{int(res['broke'].fillna(False).sum())}/{int(res['broke'].notna().sum())}",
        "break_rate_clean": f"{int(clean['broke'].fillna(False).sum())}/{int(clean['broke'].notna().sum())}",
        "n_large_300yi": int((res["mktcap_tier"] == "大市值").sum()),
        "n_mid_100_300yi": int((res["mktcap_tier"] == "中市值").sum()),
        "n_small_100yi": int((res["mktcap_tier"] == "小市值").sum()),
        "tier_note": "市值: 大>=300亿 / 中100-300亿 / 小<100亿 (亿 HKD, Wind). 流动性: Wind 20日均成交额, >=20交易日方分档.",
        "methodology": "cross-check 2026-06-24: 破发/回报排除无招股价(介绍上市)与停牌名(冻结价); 市值用Wind非yfinance; 流动性单源Wind 20日均.",
    }
    META_JSON.write_text(json.dumps(meta, ensure_ascii=False, indent=2))

    # 7) refresh stamp
    (EXT / ".last_refresh").write_text(f"1\t{today}")
    print(f"[done] universe={len(res)} | with_offer={meta['n_with_offer']} | suspended={meta['n_suspended']} | "
          f"clean={meta['n_clean']} | break(full)={meta['break_rate_full']} | break(clean)={meta['break_rate_clean']}")
    print(f"       大/中/小市值 = {meta['n_large_300yi']}/{meta['n_mid_100_300yi']}/{meta['n_small_100yi']}")
    print(f"       wrote {UNIVERSE_CSV.name}, {TRACKER_CSV.name}, {META_JSON.name}")


if __name__ == "__main__":
    main()
