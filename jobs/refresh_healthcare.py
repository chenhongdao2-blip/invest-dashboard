"""一键回补 Healthcare 页 4 个 external 数据集 —— 单入口 orchestrator。

⚠️ 诚实边界:这些数据源云端 CI 够不到,真·自动/实时不可行——
  - HK 指数 / HSHCI: iFind(会话级 MCP,无裸 key 进不了 CI)
  - 机构持仓: 你 Desktop 的 audited xlsx(云端没有)
  - 员工人数: 手工核年报/ESG(iFind NL 对纯 H 坏了)
本脚本只能跑「不依赖新 iFind 拉取」的再 bake;真要让 HK/HSHCI/员工的【数字】前进,
得先在带 iFind 的会话里拉新数据 → 更新对应 job 的 ROWS / provenance,再跑本脚本。

会做什么:
  1. build_hc_overview_data.py  —— 相对表现(US 走 yfinance 实拉 + HK 读 committed provenance)
                                    + 机构持仓(读本地 audited xlsx)。需 HTTP(S)_PROXY + 本地 xlsx。
  2. hshci_history.py           —— 重写 HSHCI 长周期 CSV/PNG(数据嵌在 ROWS,不自动前进)
  3. cn_pharma_headcount_2025.py—— 重写员工人数 CSV/PNG/XLSX(数据嵌在 ROWS,不自动前进)
  4. export_hc_relative_xlsx.py —— 相对表现独立 xlsx
跑完打印每个数据集的最新 asof + 哪些是「嵌入数据、需先人工拉 iFind 才会真前进」。

Run(中国网络需代理):
    HTTP_PROXY=http://127.0.0.1:7897 HTTPS_PROXY=http://127.0.0.1:7897 \
        uv run --with pandas --with yfinance --with openpyxl --with matplotlib \
        python jobs/refresh_healthcare.py
"""

from __future__ import annotations

import subprocess
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EXT = REPO / "data" / "external"

# (脚本, 说明, 是否真从源头拉新数据)
STEPS = [
    ("build_hc_overview_data.py", "相对表现(US=yfinance 实拉, HK=committed provenance) + 机构持仓(本地 xlsx)", True),
    ("hshci_history.py",          "HSHCI 长周期(数据嵌 ROWS — 需先人工拉 iFind 月线才前进)", False),
    ("cn_pharma_headcount_2025.py", "员工人数(数据嵌 ROWS — 需先人工核年报才前进)", False),
    ("export_hc_relative_xlsx.py", "相对表现独立 xlsx(从上面的 CSV 再生成)", True),
]

# 数据集 → (文件, asof 取法)
DATASETS = [
    ("相对表现",   "hc_index_comparison.csv",      "maxdate", "date"),
    ("HSHCI长周期", "hshci_history_monthly.csv",    "asof",    "asof"),
    ("机构持仓",   "china_fund_hc_positioning.csv", "maxdate", "data_date"),
    ("员工人数",   "cn_pharma_headcount.csv",       "asof",    "asof"),
]


def run_step(script: str) -> tuple[bool, str]:
    p = REPO / "jobs" / script
    if not p.exists():
        return False, "脚本不存在"
    r = subprocess.run([sys.executable, str(p)], capture_output=True, text=True, cwd=str(REPO))
    tail = (r.stdout or r.stderr).strip().splitlines()
    return r.returncode == 0, (tail[-1] if tail else "")


def asof_of(file: str, mode: str, col: str) -> str | None:
    import csv
    fp = EXT / file
    if not fp.exists():
        return None
    with fp.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return None
    if mode == "asof":
        return rows[0].get(col)
    vals = [str(r.get(col, ""))[:10] for r in rows]
    vals = [v for v in vals if len(v) == 10]
    return max(vals) if vals else None


def main() -> None:
    print("=== refresh_healthcare ===\n")
    for script, desc, live in STEPS:
        tag = "↻ 实拉" if live else "↺ 再bake(嵌入数据)"
        print(f"[{tag}] {script} — {desc}")
        ok, last = run_step(script)
        print(f"    {'✓' if ok else '✗ 失败'}  {last}\n")

    print("=== 各数据集最新 asof ===")
    today = date.today()
    for label, file, mode, col in DATASETS:
        iso = asof_of(file, mode, col)
        age = "?"
        if iso:
            try:
                age = f"{(today - date.fromisoformat(iso[:10])).days} 天前"
            except ValueError:
                pass
        print(f"  {label:<9} {file:<32} 截至 {iso or '?'} ({age})")

    print("\n⚠️ HSHCI / 员工人数 是「嵌入 ROWS」的——上面只是重写文件,数字未前进。")
    print("   要真前进:带 iFind 的会话里拉新数据 → 更新 jobs/{hshci_history,cn_pharma_headcount_2025}.py 的 ROWS → 重跑本脚本。")
    print("   完整说明见 docs/healthcare-data-pipeline.md。")


if __name__ == "__main__":
    main()
