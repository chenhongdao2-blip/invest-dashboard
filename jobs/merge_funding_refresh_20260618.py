#!/usr/bin/env python3
"""One-shot merge for the 2026-06-18 funding deal refresh.

- Adds 2 window M&A rows (GSK/Nuvalent, JNJ/Firefly) to mnc_ma_deals.csv.
- Backfills source_url + applies verified numeric corrections to the 14 BD rows
  someone added 2026-06-10 (they all lacked source_url).
- B6 康诺亚/吉利德 is INTENTIONALLY left untouched (value-conflict pending George).
- Recomputes mnc_ma_deals_meta.json from the CSV.

Idempotent-ish: skips M&A rows already present (by target+date). Safe to re-run.
Backups already taken (*.bak-20260618-174259).
"""
import csv
import json
import pathlib

ROOT = pathlib.Path("/Users/gcc/invest-dashboard")
MNC = ROOT / "data/external/mnc_ma_deals.csv"
META = ROOT / "data/external/mnc_ma_deals_meta.json"
BD = ROOT / "data/external/bd_deals.csv"

# ── 1. New M&A rows (mnc_ma_deals.csv schema) ──────────────────────────────
MNC_COLS = ["ticker", "company", "target", "date", "year", "deal_size_mn",
            "deal_type", "ta_group", "specialty", "size_basis", "note",
            "source_url", "upfront_musd", "milestone_musd", "deal_subtype", "confidence"]

NEW_MA = [
    {"ticker": "GSK", "company": "GSK", "target": "Nuvalent", "date": "2026-06-09",
     "year": "2026", "deal_size_mn": "10600.0", "deal_type": "M&A", "ta_group": "Oncology",
     "specialty": "Oncology/NSCLC (ROS1 zidesamtinib + ALK neladalkib, both FDA-filed)",
     "size_basis": "Actual",
     "note": "Tender offer + back-end merger; $124/sh, 40% premium; $9.4bn net of cash. GSK largest-ever buy.",
     "source_url": "https://www.gsk.com/en-gb/media/press-releases/gsk-enters-agreement-to-acquire-nuvalent-inc/",
     "upfront_musd": "", "milestone_musd": "", "deal_subtype": "M&A", "confidence": "HIGH"},
    {"ticker": "JNJ", "company": "Johnson & Johnson", "target": "Firefly Bio", "date": "2026-06-08",
     "year": "2026", "deal_size_mn": "1000.0", "deal_type": "M&A", "ta_group": "Oncology",
     "specialty": "Oncology (Firelink degrader-antibody-conjugate / DAC platform, KRAS)",
     "size_basis": "Actual",
     "note": "Definitive agreement, all-cash; expands DAC oncology pipeline.",
     "source_url": "https://www.jnj.com/media-center/press-releases/johnson-johnson-to-acquire-firefly-bio-inc-to-expand-oncology-pipeline-with-novel-degrader-antibody-conjugate-platform",
     "upfront_musd": "", "milestone_musd": "", "deal_subtype": "M&A", "confidence": "HIGH"},
]

ma_rows = list(csv.DictReader(MNC.open(encoding="utf-8")))
existing = {(r["target"].strip(), r["date"]) for r in ma_rows}
added = []
for nr in NEW_MA:
    if (nr["target"], nr["date"]) in existing:
        print(f"  skip (already present): {nr['target']} {nr['date']}")
        continue
    ma_rows.append(nr)
    added.append(nr["target"])
with MNC.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=MNC_COLS)
    w.writeheader()
    w.writerows(ma_rows)
print(f"M&A: added {added}; total rows now {len(ma_rows)}")

# ── 2. BD corrections + source backfill ────────────────────────────────────
# key = (licensor startswith, licensee startswith) -> patch dict
# patch may set upfront_musd / milestone_musd / total_musd / source_url
PATCH = {
    ("海思科", "礼来"): {"milestone_musd": "2967.0", "total_musd": "3054.0",
        "source_url": "https://www.prnewswire.com/news-releases/haisco-announces-licensing-and-research-collaboration-agreement-with-lilly-to-develop-innovative-medicines-across-multiple-therapeutic-areas-302786957.html"},
    ("云顶新耀", "Travere"): {
        "source_url": "https://www.prnewswire.com/apac/news-releases/everest-medicines-enters-into-exclusive-licensing-agreement-with-travere-therapeutics-for-civorebrutinib-a-potential-best-in-class-btk-inhibitor-for-rare-kidney-diseases-302788528.html"},
    ("恒瑞", "百时美"): {
        "source_url": "https://www.prnewswire.com/news-releases/hengrui-pharma-and-bristol-myers-squibb-announce-strategic-agreements-to-advance-innovative-medicines-across-oncology-hematology-and-immunology-302769021.html"},
    ("华辉安健", "百济神州"): {
        "source_url": "https://www.prnewswire.com/news-releases/huahui-health-and-beone-medicines-enter-into-a-global-exclusive-option-license-and-collaboration-agreement-for-innovative-oncology-drug-hh160-302758566.html"},
    ("爱科瑞思", "K2"): {
        "source_url": "https://www.vcbeathealth.com/article/30885"},
    # 康诺亚 / 吉利德  -> B6, INTENTIONALLY SKIPPED (value-conflict pending George)
    ("中国生物制药", "赛诺菲"): {
        "source_url": "https://endpoints.news/sanofi-licenses-sino-biopharms-transplant-drug-for-135m-upfront/"},
    ("德琪医药", "优时比"): {"upfront_musd": "80.0", "milestone_musd": "1100.0", "total_musd": "1180.0",
        "source_url": "https://www.prnewswire.com/news-releases/antengene-and-ucb-enter-global-license-agreement-for-atg-201-a-cd19cd3-bispecific-t-cell-engager-for-autoimmune-diseases-302702638.html"},
    ("圣因生物", "罗氏"): {
        "source_url": "https://www.prnewswire.com/news-releases/sanegenebio-announces-rnai-global-licensing-collaboration-with-genentech-302676224.html"},
    ("复宏汉霖", "卫材"): {
        "source_url": "https://www.eisai.com/news/2026/news202606.html"},
    ("瑞博生物", "Madrigal"): {
        "source_url": "https://www.prnewswire.com/news-releases/ribo-and-ribocure-announce-exclusive-global-licensing-agreement-with-madrigal-for-novel-sirna-therapeutics-targeting-mash-302685018.html"},
    ("先为达生物", "辉瑞"): {
        "source_url": "https://www.sec.gov/Archives/edgar/data/0000078003/000007800326000005/pfe-12312025xex99.htm"},
    ("和铂医药", "Solstice"): {
        "source_url": "https://www.harbourbiomed.com/news/257.html"},
    ("海思科", "AirNexis"): {"upfront_musd": "108.0", "milestone_musd": "955.0", "total_musd": "1063.0",
        "source_url": "https://www.prnewswire.com/news-releases/haisco-grants-global-rights-of-innovative-drug-hsk39004-to-airnexis-in-deal-exceeding-usd-1-billion-302657951.html"},
}

bd_rows = list(csv.DictReader(BD.open(encoding="utf-8")))
patched = []
for r in bd_rows:
    lic, lee = r.get("licensor", ""), r.get("licensee", "")
    for (ls, les), patch in PATCH.items():
        if lic.startswith(ls) and lee.startswith(les):
            for k, v in patch.items():
                r[k] = v
            patched.append(f"{lic}->{lee}")
            break
with BD.open("w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(bd_rows[0].keys()))
    w.writeheader()
    w.writerows(bd_rows)
print(f"BD: patched {len(patched)} rows: {patched}")

# ── 3. Recompute mnc_ma_deals_meta.json ────────────────────────────────────
def fnum(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return 0.0

meta = json.loads(META.read_text(encoding="utf-8"))
n_ma = sum(1 for r in ma_rows if r["deal_type"] == "M&A")
n_bd = sum(1 for r in ma_rows if r["deal_type"] == "BD")
total = sum(fnum(r["deal_size_mn"]) for r in ma_rows)
ma_total = sum(fnum(r["deal_size_mn"]) for r in ma_rows if r["deal_type"] == "M&A")
bd_total = sum(fnum(r["deal_size_mn"]) for r in ma_rows if r["deal_type"] == "BD")
years = [int(r["year"]) for r in ma_rows if r["year"]]
meta.update({
    "as_of": "2026-06-18 (window 06-01..06-18 refresh; biotech-researcher B3-verified)",
    "n_deals": len(ma_rows), "n_ma": n_ma, "n_bd": n_bd,
    "total_mn": round(total, 1), "ma_total_mn": round(ma_total, 1), "bd_total_mn": round(bd_total, 1),
    "n_mncs": len({r["ticker"] for r in ma_rows}),
    "year_min": min(years), "year_max": max(years),
})
META.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
print("META:", {k: meta[k] for k in ["n_deals", "n_ma", "n_bd", "total_mn", "ma_total_mn", "n_mncs", "year_max"]})
print("DONE.")
