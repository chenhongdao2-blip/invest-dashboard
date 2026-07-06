"""C43 差分门测量脚本 — 19 pages + home × {zh,en} AppTest 矩阵。

同一脚本在基线（154a36c 干净 worktree + 本地数据镜像）与改后各跑一遍，
Evaluator diff 两份 JSON：PASS = 零新增异常 + 零 raw i18n key + 零 rerun 上限
+ 零 i18n/toggle 路径 TypeError（CONTRACT.md C43，Planner 裁决）。

用法（cwd = 目标 repo/worktree 根，用主 repo 的 .venv）：
    PYTHONPATH=app <repo>/.venv/bin/python <this file> --out <json path>

设计约束：
- 逐页隔离子进程不做（AppTest 同进程串行即可；单页崩溃被 try 包住不炸矩阵）。
- raw-key 启发式：locale 前缀 + 点分 token 出现在渲染文本中 = t() 回退键本身。
  两次运行同一启发式 → 差分有效（绝对误报在 diff 中抵消）。
- 网络页超时按 TIMEOUT 记录为一种 outcome（非崩溃），同样参与差分。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import traceback
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path.cwd()
PAGES = sorted((ROOT / "app" / "pages").glob("*.py")) + [ROOT / "app" / "home.py"]
LANGS = ("zh", "en")
TIMEOUT_S = 120

# t() 回退 = key 本身出现在正文。前缀集覆盖 locales/ 全部命名空间。
_RAW_KEY_RE = re.compile(
    r"\b(?:strategy|home|hc|ai|market|common|etf|sec|drill|cov|val|heat|rrg|ipo)"
    r"\.[a-z0-9_]+(?:\.[a-z0-9_]+)*\b"
)


def _texts(at: AppTest) -> list[str]:
    out: list[str] = []
    for attr in ("markdown", "caption", "title", "header", "subheader", "text"):
        try:
            for el in getattr(at, attr):
                v = getattr(el, "value", None) or getattr(el, "body", None)
                if isinstance(v, str):
                    out.append(v)
        except Exception:
            pass
    return out


def run_one(page: Path, lang: str) -> dict:
    rec: dict = {"status": "ok", "exceptions": [], "raw_keys": [], "secs": 0.0}
    t0 = time.time()
    try:
        at = AppTest.from_file(str(page), default_timeout=TIMEOUT_S)
        at.session_state["lang"] = lang
        at.run()
        for exc in at.exception:
            msg = f"{getattr(exc, 'type', '?')}: {str(getattr(exc, 'message', ''))[:300]}"
            rec["exceptions"].append(msg)
        hits = set()
        for txt in _texts(at):
            hits.update(_RAW_KEY_RE.findall(txt))
        rec["raw_keys"] = sorted(hits)
        if rec["exceptions"]:
            rec["status"] = "exception"
    except Exception as e:  # AppTest 层崩溃（含 rerun 上限 / timeout / import 错）
        kind = type(e).__name__
        rec["status"] = "TIMEOUT" if "imeout" in kind or "imeout" in str(e) else "crash"
        rec["exceptions"].append(f"{kind}: {str(e)[:300]}")
        rec["trace_tail"] = traceback.format_exc().splitlines()[-3:]
    rec["secs"] = round(time.time() - t0, 1)
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    matrix: dict = {"_meta": {"root": str(ROOT), "n_pages": len(PAGES), "ts": time.strftime("%F %T")}}
    for page in PAGES:
        key = page.name
        matrix[key] = {}
        for lang in LANGS:
            matrix[key][lang] = run_one(page, lang)
            print(f"[{time.strftime('%T')}] {key} × {lang}: {matrix[key][lang]['status']}"
                  f" ({matrix[key][lang]['secs']}s)", flush=True)
        # 增量落盘：跑一页存一次，崩溃不丢已有结果
        Path(args.out).write_text(json.dumps(matrix, ensure_ascii=False, indent=1))
    print(f"DONE → {args.out}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
