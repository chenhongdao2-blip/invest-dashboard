"""Load universe YAML files into the universe_member table.

Idempotent — uses INSERT OR REPLACE.

Usage:
    python jobs/load_universe.py
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "snapshots.db"
DOMAINS_DIR = REPO_ROOT / "config" / "domains"
UNIVERSES_DIR = REPO_ROOT / "config" / "universes"


def load_domains() -> list[dict]:
    """Read all domain YAMLs."""
    domains = []
    for p in sorted(DOMAINS_DIR.glob("*.yml")):
        with p.open() as f:
            data = yaml.safe_load(f)
        data["_file"] = p.name
        data["_domain_id"] = p.stem      # e.g. "healthcare"
        domains.append(data)
    return domains


def load_universe_file(filename: str) -> dict:
    """Read a single universe YAML by filename."""
    path = UNIVERSES_DIR / filename
    with path.open() as f:
        return yaml.safe_load(f)


def upsert_members(conn: sqlite3.Connection, domain_id: str,
                   sector_id: str, tickers: list[dict]) -> int:
    """Insert/replace universe_member rows. Returns row count."""
    rows = []
    for entry in tickers:
        rows.append((
            domain_id,
            sector_id,
            entry["ticker"],
            entry.get("name_cn"),
            entry.get("name_en"),
            entry.get("region"),
            entry.get("note"),
        ))
    conn.executemany(
        """
        INSERT OR REPLACE INTO universe_member
            (domain, sector, ticker, name_cn, name_en, region, note)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    return len(rows)


def main() -> None:
    if not DB_PATH.exists():
        raise SystemExit(
            f"DB not found at {DB_PATH}. Run jobs/init_db.py first."
        )

    conn = sqlite3.connect(DB_PATH)
    try:
        total = 0
        for domain in load_domains():
            domain_id = domain["_domain_id"]
            sectors = domain.get("sectors") or []
            # Regions (e.g. healthcare.regions → japan) ride the same ingest path:
            # one universe_member row per ticker with sector_id = region id. They are
            # NOT in cfg["sectors"], so sector summary / heatmap tabs stay sector-pure.
            regions = domain.get("regions") or []
            for sector in [*sectors, *regions]:
                uni = load_universe_file(sector["universe_file"])
                n = upsert_members(
                    conn,
                    domain_id,
                    sector["id"],
                    uni.get("tickers") or [],
                )
                total += n
                print(f"[load_universe] {domain_id} / {sector['id']}: {n} tickers")
            # Coverage list (CMSI)
            cov = domain.get("coverage")
            if cov:
                uni = load_universe_file(cov["universe_file"])
                cov_tickers = uni.get("tickers") or []
                # 1) mark every cover name with the _coverage pseudo-sector
                n = upsert_members(conn, domain_id, "_coverage", cov_tickers)
                total += n
                print(f"[load_universe] {domain_id} / _coverage: {n} tickers")
                # 2) also write each cover name into its REAL sector (entry's
                #    `sector:` field) so the dashboard shows e.g. "生物科技 / 覆盖"
                #    instead of a bare "_coverage". Group by sector → one upsert each.
                by_sector: dict[str, list[dict]] = {}
                for entry in cov_tickers:
                    sec = entry.get("sector")
                    if sec:
                        by_sector.setdefault(sec, []).append(entry)
                for sec, entries in sorted(by_sector.items()):
                    m = upsert_members(conn, domain_id, sec, entries)
                    total += m
                    print(f"[load_universe] {domain_id} / {sec} (from coverage): {m} tickers")
        conn.commit()
        # Summary
        cur = conn.execute(
            "SELECT domain, sector, COUNT(*) FROM universe_member "
            "GROUP BY domain, sector ORDER BY domain, sector"
        )
        print(f"\n[load_universe] Total upserted: {total}")
        print("\n[load_universe] universe_member rows by (domain, sector):")
        for row in cur.fetchall():
            print(f"  {row[0]:>14s} / {row[1]:<16s} {row[2]:>3d}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
