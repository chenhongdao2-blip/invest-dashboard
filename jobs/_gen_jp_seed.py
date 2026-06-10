"""One-off: generate config/universes/hc_japan.yml from the iFind Japan-Healthcare
watchlist xlsx (snapshot 2026/05/26: 42 names → 40 live; 2 delisted excluded, see
DELISTED below).

The xlsx is the PROVENANCE (George's curated iFind 自选股清单); the quote columns
are a stale snapshot and PE/PB are all zero, so only code + name + mcap order are
consumed. Live quotes flow through the normal yfinance `.T` EOD pipeline instead.

Subsector classification + clean bilingual names are curated HERE (the xlsx 所属行业
column is empty). Re-run only if the watchlist itself changes.

Usage:
    uv run --with openpyxl,pandas,pyyaml python jobs/_gen_jp_seed.py
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
XLSX_SRC = Path.home() / "Desktop" / "Copy of Japan-Healthcare.xlsx"
XLSX_ARCHIVE = REPO_ROOT / "data" / "external" / "jp_healthcare_watchlist_20260526.xlsx"
YML_OUT = REPO_ROOT / "config" / "universes" / "hc_japan.yml"

SUBSECTOR_ORDER = ["pharma", "medtech", "diagnostics", "distribution"]

# code → (name_cn, name_en, subsector[, note])  — curated 2026-06-10.
CURATED: dict[str, tuple] = {
    # --- pharma (20) ---
    "4502": ("武田药品", "Takeda Pharmaceutical", "pharma"),
    "4519": ("中外制药", "Chugai Pharmaceutical", "pharma", "罗氏控股子公司"),
    "4568": ("第一三共", "Daiichi Sankyo", "pharma", "ADC: Enhertu/Datroway"),
    "4578": ("大冢控股", "Otsuka Holdings", "pharma"),
    "4503": ("安斯泰来", "Astellas Pharma", "pharma"),
    "4507": ("盐野义制药", "Shionogi", "pharma"),
    "4523": ("卫材", "Eisai", "pharma", "阿尔茨海默 Leqembi"),
    "4528": ("小野药品", "Ono Pharmaceutical", "pharma", "Opdivo 日本权益"),
    "4151": ("协和麒麟", "Kyowa Kirin", "pharma"),
    "4506": ("住友制药", "Sumitomo Pharma", "pharma"),
    "4536": ("参天制药", "Santen Pharmaceutical", "pharma", "眼科"),
    "4967": ("小林制药", "Kobayashi Pharmaceutical", "pharma", "OTC/消费保健"),
    "4540": ("津村", "Tsumura", "pharma", "汉方药"),
    "4516": ("日本新药", "Nippon Shinyaku", "pharma"),
    "4887": ("泽井集团", "Sawai Group Holdings", "pharma", "仿制药"),
    "4553": ("东和药品", "Towa Pharmaceutical", "pharma", "仿制药"),
    "4547": ("橘生药品", "Kissei Pharmaceutical", "pharma"),
    "4521": ("科研制药", "Kaken Pharmaceutical", "pharma"),
    "4587": ("PeptiDream", "PeptiDream", "pharma", "多肽药物发现 biotech"),
    # --- medtech (11) ---
    "7741": ("豪雅", "HOYA", "medtech", "光学玻璃/内窥镜/眼科镜片"),
    "4543": ("泰尔茂", "Terumo", "medtech"),
    "7733": ("奥林巴斯", "Olympus", "medtech", "内窥镜"),
    "7747": ("朝日英达", "Asahi Intecc", "medtech", "导丝/介入器械"),
    "4901": ("富士胶片控股", "FUJIFILM Holdings", "medtech", "Bio CDMO + 医疗影像；综合体"),
    "8086": ("尼普洛", "Nipro", "medtech"),
    "7716": ("NAKANISHI", "NAKANISHI", "medtech", "牙科器械"),
    "6849": ("日本光电", "Nihon Kohden", "medtech", "监护/急救设备"),
    "6960": ("福田电子", "Fukuda Denshi", "medtech"),
    "7730": ("马尼", "MANI", "medtech", "手术缝合针/牙科"),
    # --- diagnostics (5) ---
    "6869": ("希森美康", "Sysmex", "diagnostics", "血液/体外诊断"),
    "6951": ("日本电子", "JEOL", "diagnostics", "电镜/科学仪器"),
    "4544": ("H.U.集团", "H.U. Group Holdings", "diagnostics", "检验服务/试剂"),
    "4694": ("BML", "BML", "diagnostics", "临床检验"),
    "4483": ("JMDC", "JMDC", "diagnostics", "医疗数据/数字健康"),
    # --- distribution (6) ---
    "7459": ("Medipal 控股", "Medipal Holdings", "distribution", "医药流通"),
    "2784": ("阿弗瑞萨", "Alfresa Holdings", "distribution", "医药流通"),
    "9987": ("铃谦", "Suzuken", "distribution", "医药流通"),
    "8129": ("东邦控股", "Toho Holdings", "distribution", "医药流通"),
    "3360": ("SHIP HEALTHCARE", "SHIP HEALTHCARE", "distribution", "医院后勤/设备服务"),
    "7476": ("亚速旺", "As One", "distribution", "实验室器材流通"),
}

# xlsx 快照(2026/05/26)里有、但已退市的票 — 不进 universe（活数据 dashboard 容不下
# 冻结平线），记在这里留 provenance。核验 2026-06-10：
#   3593 HOGY MEDICAL — 凯雷 TOB ¥6,700，2026-05-15 上場廃止
#   4530 久光制药     — MBO 非公开化 TOB ¥6,082，价格序列止于 2026-05-11
DELISTED: dict[str, str] = {
    "3593": "HOGY MEDICAL — Carlyle TOB, delisted 2026-05-15",
    "4530": "Hisamitsu — MBO going-private, last trade 2026-05-11",
}

SUBSECTOR_LABEL = {
    "pharma": "制药 Pharma",
    "medtech": "医疗器械 Medtech",
    "diagnostics": "诊断·检测 Diagnostics",
    "distribution": "流通·服务 Distribution",
}


def main() -> None:
    df = pd.read_excel(XLSX_SRC, sheet_name="行情报价", dtype={"代码": str})
    codes_xlsx = set(df["代码"].astype(str).str.strip())
    codes_curated = set(CURATED) | set(DELISTED)
    if codes_xlsx != codes_curated:
        raise SystemExit(
            f"code set mismatch — xlsx only: {sorted(codes_xlsx - codes_curated)}, "
            f"curated only: {sorted(codes_curated - codes_xlsx)}"
        )

    # mcap order from the xlsx (its row order is already mcap-desc)
    mcap_rank = {str(c).strip(): i for i, c in enumerate(df["代码"])}
    # 市值快照（JPY，2026/05/26）→ 专栏指数的市值加权权重。股本不变时
    # 「锚日市值权重 × 归一价格」= 标准市值加权指数；快照漂移以重跑本脚本刷新。
    mcap_bn = {str(c).strip(): round(float(v) / 1e9)
               for c, v in zip(df["代码"], df["总市值"])}

    lines = [
        f"# Japan Healthcare 区域 universe — {len(CURATED)} tickers",
        "# Source: iFind 自选股 Japan-Healthcare.xlsx (snapshot 2026/05/26, 42 names),",
        "#         archived at data/external/jp_healthcare_watchlist_20260526.xlsx.",
        "# 已退市剔除 (2026-06-10 核验): 3593 HOGY MEDICAL (凯雷 TOB, 05-15 上場廃止) /",
        "#         4530 久光制药 (MBO 非公开化, 价格止于 05-11)。",
        "# Generated by jobs/_gen_jp_seed.py — edit the script's CURATED map, not this file.",
        "# subsector ∈ pharma / medtech / diagnostics / distribution (page groups by it;",
        "# NOT stored in DB — this yml is the single source for grouping).",
        "sector_id: japan",
        "domain: healthcare",
        "",
        "tickers:",
    ]
    for sub in SUBSECTOR_ORDER:
        members = sorted(
            (c for c, v in CURATED.items() if v[2] == sub),
            key=lambda c: mcap_rank[c],
        )
        lines.append(f"  # ── {SUBSECTOR_LABEL[sub]} ({len(members)}) ──")
        for code in members:
            v = CURATED[code]
            name_cn, name_en, _ = v[0], v[1], v[2]
            lines.append(f"  - ticker: {code}.T")
            lines.append(f'    name_cn: "{name_cn}"')
            lines.append(f'    name_en: "{name_en}"')
            lines.append("    region: JP")
            lines.append(f"    subsector: {sub}")
            lines.append(f"    mcap_bn_jpy: {mcap_bn[code]}   # 市值快照 2026/05/26, 十亿日元")
            if len(v) > 3:
                lines.append(f'    note: "{v[3]}"')
    YML_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[gen_jp_seed] wrote {YML_OUT} ({len(CURATED)} tickers)")

    if not XLSX_ARCHIVE.exists():
        shutil.copy2(XLSX_SRC, XLSX_ARCHIVE)
        print(f"[gen_jp_seed] archived xlsx → {XLSX_ARCHIVE}")


if __name__ == "__main__":
    main()
