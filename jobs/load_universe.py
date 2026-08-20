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


def ensure_status_column(conn: sqlite3.Connection) -> None:
    """Idempotent migration: add universe_member.status / secondary_listing if missing.

    init_db.py uses CREATE TABLE IF NOT EXISTS, so an ALREADY-EXISTING db (incl.
    the one cron drives on Cloud) never picks up new columns on its own. Without
    this, the first run after deploy would die on 'no such column: status' and
    take the whole daily refresh down with it.
    """
    cols = {r[1] for r in conn.execute("PRAGMA table_info(universe_member)")}
    for name, decl in (("status", "TEXT"), ("secondary_listing", "INTEGER")):
        if name not in cols:
            conn.execute(f"ALTER TABLE universe_member ADD COLUMN {name} {decl}")
            print(f"[load_universe] migrated: universe_member.{name} added")


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
    """Insert/replace universe_member rows. Returns row count.

    保留语义 (2026-08-20): status / secondary_listing 只有在 entry 显式给出时才写入,
    否则沿用库里已有的值。

    为什么必需: 同一个 (domain, sector, ticker) 会被写两次 —— 一次来自板块 yml,
    一次来自 coverage yml 的「回填真实 sector」二轮 (例如 2359.HK 在 hc_cxo.yml 里
    标了 secondary_listing, 又在 cmsi_coverage_hc.yml 里带 sector: cxo)。两条走同一
    主键, 后写的 INSERT OR REPLACE 会把前者的标记整列抹成 NULL。这类丢失是静默的:
    行还在、名称还在, 只有标记没了, 页面照常渲染。
    """
    existing: dict[tuple, tuple] = {}
    keys = [(domain_id, sector_id, e["ticker"]) for e in tickers]
    if keys:
        ph = ",".join("?" * len(keys))
        cur = conn.execute(
            f"""SELECT domain, sector, ticker, status, secondary_listing
                FROM universe_member
                WHERE domain = ? AND sector = ? AND ticker IN ({ph})""",
            (domain_id, sector_id, *[k[2] for k in keys]),
        )
        existing = {(r[0], r[1], r[2]): (r[3], r[4]) for r in cur}

    rows = []
    for entry in tickers:
        prev = existing.get((domain_id, sector_id, entry["ticker"]), (None, None))
        rows.append((
            domain_id,
            sector_id,
            entry["ticker"],
            entry.get("name_cn"),
            entry.get("name_en"),
            entry.get("region"),
            entry.get("note"),
            entry.get("status") if "status" in entry
                else prev[0],
            (1 if entry.get("secondary_listing") else None) if "secondary_listing" in entry
                else prev[1],
        ))
    conn.executemany(
        """
        INSERT OR REPLACE INTO universe_member
            (domain, sector, ticker, name_cn, name_en, region, note, status,
             secondary_listing)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
        ensure_status_column(conn)
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
