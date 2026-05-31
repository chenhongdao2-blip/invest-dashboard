"""Translate company English names → Chinese (name_cn) via GLM, write to universe_member.

The daily cron / load_universe leaves name_cn empty for newly-added tickers.
translate_profiles.py only handles the business *summary* (profile_cn); company
NAMES need their own pass. This LOCAL job fills universe_member.name_cn for rows
where it is missing/empty, using GLM (z.ai) for the standard sell-side Chinese
short name. Idempotent: only fills blank name_cn (unless --force).

Run LOCALLY (needs GLM key in ~/.config/cg/api_key + proxy for z.ai):
    HTTPS_PROXY=http://127.0.0.1:7897 uv run --python 3.12 \
        --with-requirements requirements.txt python jobs/translate_names.py
    python jobs/translate_names.py --domain healthcare --sector biotech
    python jobs/translate_names.py --force

Writes a JSON report to /tmp/biotech_name_report.json.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
import urllib.error
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "jobs"))
import translate_profiles as tp  # reuse call_glm / get_api_key  # noqa: E402

DB = str(REPO_ROOT / "data" / "snapshots.db")
REPORT = "/tmp/biotech_name_report.json"
BATCH = 15

SYSTEM = (
    "你是招商证券国际(CMS HK)医疗组的翻译。把美股/港股生物医药公司英文名翻译成"
    "中文研报常用简称(去掉 Inc./Corp./Ltd./N.V./plc/S.A./AG 等公司形式后缀)。"
    "已有约定俗成中文名的用约定名(如 Gilead=吉利德, Moderna=莫德纳, BeOne/BeiGene=百济神州)；"
    "没有约定名的音译或意译为简洁专业的中文简称。每行一个,格式 `代码=中文名`,"
    "严格对应输入代码,不要解释,不要加任何前后缀。"
)


def translate_names(items: list[tuple[str, str]]) -> dict[str, str]:
    """items=[(ticker, english_name)] → {ticker: chinese_name}."""
    lines = [f"{tk}\t{en}" for tk, en in items]
    prompt = (
        "把下面每个公司英文名翻译成中文研报简称。输入每行格式 `代码<TAB>英文名`。"
        "你的输出每行格式 `代码=中文名`,与输入代码一一对应:\n" + "\n".join(lines)
    )
    out = tp.call_glm(prompt, SYSTEM, max_tokens=2000)
    result: dict[str, str] = {}
    for line in out.splitlines():
        line = line.strip()
        if "=" not in line:
            continue
        tk, _, cn = line.partition("=")
        tk, cn = tk.strip(), cn.strip()
        if tk and cn:
            result[tk] = cn
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", default="healthcare")
    ap.add_argument("--sector", default="biotech")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    conn = sqlite3.connect(DB, timeout=120)
    conn.execute("PRAGMA busy_timeout=120000")  # coexist with concurrent agents
    q = ("SELECT DISTINCT ticker, name_en FROM universe_member "
         "WHERE domain=? AND sector=? AND name_en IS NOT NULL AND name_en!=''")
    rows = conn.execute(q, (args.domain, args.sector)).fetchall()
    if not args.force:
        # only those with blank name_cn
        blanks = {r[0] for r in conn.execute(
            "SELECT DISTINCT ticker FROM universe_member WHERE domain=? AND sector=? "
            "AND (name_cn IS NULL OR name_cn='')", (args.domain, args.sector)).fetchall()}
        rows = [(t, n) for t, n in rows if t in blanks]
    if args.limit:
        rows = rows[: args.limit]

    print(f"[names] {args.domain}/{args.sector}: {len(rows)} names need name_cn")
    done = 0
    fail_batches = 0
    for i in range(0, len(rows), BATCH):
        batch = rows[i:i + BATCH]
        try:
            cn_map = translate_names(batch)
        except (urllib.error.HTTPError, urllib.error.URLError, KeyError) as e:
            print(f"[names] batch {i // BATCH + 1} failed: {e}; keeping going")
            fail_batches += 1
            continue
        for tk, en in batch:
            cn = cn_map.get(tk)
            if not cn:
                print(f"[names]   {tk}: no name returned (skipped)")
                continue
            # update ALL universe_member rows for this ticker (cross-sector safe)
            conn.execute(
                "UPDATE universe_member SET name_cn=? WHERE ticker=? AND (name_cn IS NULL OR name_cn='' OR ?=1)",
                (cn, tk, 1 if args.force else 0),
            )
            done += 1
        conn.commit()
        print(f"[names] batch {i // BATCH + 1}/{(len(rows) + BATCH - 1) // BATCH}: +{len(cn_map)} (total {done})")
        time.sleep(1.0)
    conn.close()

    report = {"target": f"{args.domain}/{args.sector}", "candidates": len(rows),
              "translated": done, "failed_batches": fail_batches}
    with open(REPORT, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"[names] done. translated {done}/{len(rows)}  report → {REPORT}")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
