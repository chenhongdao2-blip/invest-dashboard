"""Strip third-party-licensed columns from the MNC M&A deal table for public release.

WHY THIS EXISTS
---------------
`data/external/mnc_ma_deals_full.csv` carries columns sourced from a paid,
third-party data vendor (the `fs_*` family: transaction value, deal status,
EV/EBITDA, EV/Sales, and the vendor's proprietary deal identifier). This repo is
PUBLIC and deploys to a public Streamlit Cloud site, so redistributing those
values is a licensing question, not a preference — and publishing is irreversible.

Removing only the *attribution* would be worse, not better: unattributed use of
licensed data is still redistribution. So this script deletes the values.

WHAT IT KEEPS
-------------
Everything the project sourced itself — target/acquirer, headline deal size,
therapeutic area, upfront/milestone splits, notes, source URLs — plus
announce_date / close_date / lag_days / date_basis, which are publicly
verifiable corporate-action facts (press releases, regulatory filings).

DOUBLE-FILE CONTRACT
--------------------
    data/external/mnc_ma_deals_full.csv   full     — gitignored, LOCAL ONLY
    data/external/mnc_ma_deals.csv        stripped — committed, ships to Cloud

`lib/funding.py` prefers the full file when present and falls back to the
stripped one, so local runs keep every column while Cloud sees only the public
subset. The page section that renders vendor values guards on their presence and
simply does not render when they are absent.

Usage:
    python jobs/export_mnc_deals_public.py
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
FULL = REPO_ROOT / "data" / "external" / "mnc_ma_deals_full.csv"
PUBLIC = REPO_ROOT / "data" / "external" / "mnc_ma_deals.csv"

# Vendor-derived columns — deleted wholesale from the public copy.
DROP_COLS = ["fs_tv_mn", "fs_status", "fs_ev_ebitda", "fs_ev_sales", "fs_deal_id"]

# Free-text columns can name the vendor or its fields inline; generalise rather
# than blank them, so the analytical point survives without the provenance.
TEXT_COLS = ["note", "flag", "size_basis", "date_basis", "confidence"]
_VENDOR_RE = re.compile(r"fs_tv_mn|fs_deal_id|fs_status|fs_ev_ebitda|fs_ev_sales|factset|fds",
                        re.IGNORECASE)


def _generalise(v: object) -> object:
    if not isinstance(v, str) or not _VENDOR_RE.search(v):
        return v
    out = v
    for pat, repl in (
        (r"fs_tv_mn", "第三方源口径"),
        (r"fs_deal_id", "第三方源交易号"),
        (r"fs_status", "第三方源状态"),
        (r"fs_ev_ebitda", "第三方源 EV/EBITDA"),
        (r"fs_ev_sales", "第三方源 EV/Sales"),
        (r"FactSet", "第三方数据源"),
        (r"factset", "第三方数据源"),
    ):
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)
    return out


def main() -> None:
    if not FULL.exists():
        raise SystemExit(
            f"{FULL.name} not found. It is the local-only full copy; without it "
            f"this script has nothing to strip."
        )
    df = pd.read_csv(FULL)
    before = list(df.columns)

    dropped = [c for c in DROP_COLS if c in df.columns]
    df = df.drop(columns=dropped)

    touched = 0
    for c in TEXT_COLS:
        if c in df.columns:
            new = df[c].map(_generalise)
            touched += int((new.fillna("") != df[c].fillna("")).sum())
            df[c] = new

    df.to_csv(PUBLIC, index=False)

    # Fail loudly rather than ship a leak.
    raw = PUBLIC.read_text(encoding="utf-8")
    leaks = _VENDOR_RE.findall(raw)
    if leaks:
        raise SystemExit(f"REFUSING: vendor tokens still present in {PUBLIC.name}: {set(leaks)}")

    print(f"[export] {len(df)} rows | dropped {len(dropped)} cols: {dropped}")
    print(f"[export] generalised {touched} free-text cell(s)")
    print(f"[export] {len(before)} -> {len(df.columns)} columns | leak scan clean -> {PUBLIC.name}")


if __name__ == "__main__":
    main()
