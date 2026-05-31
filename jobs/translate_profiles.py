"""Translate company_profile.longBusinessSummary → Chinese via GLM, cache in profile_cn.

yfinance only provides English business descriptions. This LOCAL job translates them
once with GLM (z.ai) and stores the result in profile_cn (a table the daily cron does
NOT touch, so translations survive). Idempotent: only (re)translates a ticker when its
profile_cn row is missing or the English text changed (en_hash mismatch).

Run LOCALLY (needs GLM key in ~/.config/cg/api_key + China proxy for z.ai):
    SEC_PROXY unused here; z.ai is reachable directly or via system proxy.
    python jobs/translate_profiles.py                 # only missing/changed
    python jobs/translate_profiles.py --force         # re-translate all
    python jobs/translate_profiles.py --limit 5       # debug

NOT run on the GitHub Actions runner (no GLM key there). The committed profile_cn rows
are what the deployed app reads.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = REPO_ROOT / "data" / "snapshots.db"

API_URL = "https://api.z.ai/api/anthropic/v1/messages"
MODEL = "glm-5.1"
BATCH = 6          # summaries per GLM call (keeps prompts small + within quota)
SEP = "\n@@@TICKER:"   # delimiter for robust multi-item parsing

SYSTEM = (
    "你是招商证券国际(CMS HK)医疗组的中文翻译。把英文公司业务简介翻译成专业、简洁的"
    "中文卖方研报口径。要求：保留药品/产品商品名原文(如 TYVYT、mazdutide)并在首次出现时"
    "可加简短中文注释；专业术语用国内习惯译法(monoclonal antibodies=单克隆抗体, oncology="
    "肿瘤, autoimmune=自身免疫, CXO 等)；不要逐字直译，要通顺；不要加入原文没有的信息；"
    "不要加任何前言/结语，只输出译文。"
)


def get_api_key() -> str:
    key = os.environ.get("Z_AI_API_KEY", "").strip()
    if key:
        return key
    cfg = Path.home() / ".config" / "cg" / "api_key"
    if cfg.exists():
        return cfg.read_text(encoding="utf-8").strip()
    sys.exit("ERROR: no GLM key (Z_AI_API_KEY or ~/.config/cg/api_key).")


def call_glm(prompt: str, system: str, max_tokens: int = 4000) -> str:
    body = {"model": MODEL, "max_tokens": max_tokens,
            "system": system, "messages": [{"role": "user", "content": prompt}]}
    req = urllib.request.Request(
        API_URL, data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {get_api_key()}",
                 "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
    )
    timeout = int(os.environ.get("CG_TIMEOUT", "180"))
    with urllib.request.urlopen(req, timeout=timeout) as r:
        resp = json.load(r)
    return resp["content"][0]["text"]


def _hash(s: str) -> str:
    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()


def translate_batch(items: list[tuple[str, str]]) -> dict[str, str]:
    """items = [(ticker, english_summary)]. Returns {ticker: chinese}."""
    # Build a delimited prompt; ask GLM to echo the same delimiter per item.
    parts = [f"{SEP}{tk}@@@\n{en}" for tk, en in items]
    prompt = (
        "翻译下面每段公司业务简介为中文。每段以一行 `@@@TICKER:<代码>@@@` 开头标识，"
        "请在你的输出中对每段也用完全相同的 `@@@TICKER:<代码>@@@` 行开头，紧跟该段中文译文。"
        "严格保持代码标记一致，不要合并或遗漏任何一段。\n" + "".join(parts)
    )
    out = call_glm(prompt, SYSTEM, max_tokens=4000 + 600 * len(items))
    # parse by the delimiter
    result: dict[str, str] = {}
    for chunk in out.split("@@@TICKER:")[1:]:
        head, _, body = chunk.partition("@@@")
        tk = head.strip()
        cn = body.strip()
        if tk and cn:
            result[tk] = cn
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true", help="Re-translate all (ignore cache).")
    ap.add_argument("--limit", type=int, default=0, help="Only first N (debug).")
    args = ap.parse_args()

    if not DB_PATH.exists():
        sys.exit(f"DB not found at {DB_PATH}. Run jobs/init_db.py first.")
    conn = sqlite3.connect(DB_PATH, timeout=120)
    conn.execute("PRAGMA busy_timeout=120000")  # coexist with concurrent DB writers
    try:
        rows = conn.execute(
            "SELECT ticker, longBusinessSummary FROM company_profile "
            "WHERE longBusinessSummary IS NOT NULL AND longBusinessSummary != '' ORDER BY ticker"
        ).fetchall()
        existing = {r[0]: r[1] for r in conn.execute("SELECT ticker, en_hash FROM profile_cn")}

        todo: list[tuple[str, str]] = []
        for tk, en in rows:
            if args.force or existing.get(tk) != _hash(en):
                todo.append((tk, en))
        if args.limit:
            todo = todo[: args.limit]

        print(f"[translate] {len(rows)} profiles w/ summary; {len(todo)} need translation")
        done = 0
        for i in range(0, len(todo), BATCH):
            batch = todo[i:i + BATCH]
            try:
                cn_map = translate_batch(batch)
            except (urllib.error.HTTPError, urllib.error.URLError, KeyError) as e:
                print(f"[translate] batch {i // BATCH + 1} failed: {e}; keeping going")
                continue
            now = datetime.now(timezone.utc).isoformat(timespec="seconds")
            for tk, en in batch:
                cn = cn_map.get(tk)
                if not cn:
                    print(f"[translate]   {tk}: no translation returned (skipped)")
                    continue
                conn.execute(
                    "INSERT OR REPLACE INTO profile_cn (ticker, en_hash, summary_cn, translated_at) "
                    "VALUES (?, ?, ?, ?)",
                    (tk, _hash(en), cn, now),
                )
                done += 1
            conn.commit()
            print(f"[translate] batch {i // BATCH + 1}/{(len(todo) + BATCH - 1) // BATCH}: +{len(cn_map)} (total {done})")
            time.sleep(1.0)
        print(f"[translate] done. translated {done}/{len(todo)}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
