# Funding Deal Refresh — 2026-06-18

Window: 2026-06-01 (last_refresh) → 2026-06-18. Pipeline: docs/funding-pipeline.md.
Verification: biotech-researcher (20 web checks + domain memory), 2026-06-18.

## New M&A (added to mnc_ma_deals.csv, basket-relevant)

| acquirer | target | date | size USDmn | TA | source | verdict |
|---|---|---|---|---|---|---|
| GSK | Nuvalent | 2026-06-09 | 10,600 (equity; 9,400 net of cash); $124/sh, 40% premium (来源: gsk.com PR, 2026-06-09) | Oncology/NSCLC (ROS1 zidesamtinib + ALK neladalkib) | gsk.com PR / SEC 6-K | ✓ M&A (tender+merger) |
| J&J (JNJ) | Firefly Bio | 2026-06-08 | 1,000 cash | Oncology (Firelink DAC, KRAS) | jnj.com PR / FierceBiotech | ✓ M&A (definitive) |

Out-of-basket M&A noted but NOT added (CSV tracks 13 MNCs only): Incyte/Vega ($1.25bn + $0.75bn ms, vWD); Novanta/Riverpoint ($1.2bn, medtech) (来源: Intellizence weekly M&A, 2026-06).
Excluded rumors (not announced): Revolution Medicines/Merck ~$32bn ("in talks"); Lilly/Abivax €15bn (Jan-2026 JPM speculation, unconfirmed) (来源: BioPharma Dive / Pharmaceutical-Technology, 2026-01, 仅传闻不入表).

## BD corrections + source backfill (bd_deals.csv) — the 14 rows backfilled 2026-06-10 all lacked source_url

| licensor → licensee | date | corrected up/ms/tot | source | note |
|---|---|---|---|---|
| 海思科 → 礼来 | 2026-06 (signed 5-29) | **87 / 2,967 / 3,054** (was 87/2,913/3,000) | prnewswire 302786957 | 5-target discovery; "$3B" rounded |
| 云顶新耀 → Travere | 2026-06-04 | 112.5 / 1,030 / 1,142 ✓ | prnewswire 302788528 | EVER001 civorebrutinib BTK, kidney |
| 恒瑞 → BMS | 2026-05 | 600 / 14,600 / 15,200 (near-term cash actually $950M) | prnewswire 302769021 | 13 programs; split is simplification |
| 华辉安健 → 百济神州 | 2026-04 | 20 / 1,980 / 2,000 (20 option + 100 exercise + 1,900 ms) | prnewswire 302758566 | HH160 trispecific preclinical; licensee now "BeOne Medicines" |
| 爱科瑞思 → K2 | 2026-04 | NewCo (headline ≤730) | vcbeathealth 30885 | ACR246 5T4 ADC; +equity, B3 n/a |
| **康诺亚 → 吉利德** | 2026-04 | ⚠ CONFLATED — pending George decision | vcbeathealth 2983 / PharmExec | Keymed 15% stake take 250+70=320 vs Gilead/Ouro acquisition $2,175M |
| 中国生物制药 → 赛诺菲 | 2026-03 | 135 / 1,395 / 1,530 ✓ | endpoints | Rovadicitinib JAK/ROCK, myelofibrosis |
| 德琪医药 → UCB | 2026-03 | **80 / 1,100 / 1,180** (was -/-/1180) | prnewswire 302702638 | ATG-201 CD19/CD3 TCE |
| 圣因生物 → 罗氏 | 2026-02 | 200 / 1,500 / 1,700 ✓ | prnewswire 302676224 | RNAi; contracting entity = Genentech |
| 复宏汉霖 → 卫材 | 2026-02 | 75 / 315 / 390 ✓ | eisai.com | Serplulimab PD-1, **Japan-only** |
| 瑞博生物 → Madrigal | 2026-02 | 60 / 4,340 / 4,400 ✓ | prnewswire 302685018 | 6 siRNA MASH |
| 先为达生物 → 辉瑞 | 2026-02 | -/-/ 495 ✓ | SEC 8-K pfe | Ecnoglutide GLP-1, **China-only**, NOT NewCo |
| 和铂医药 → Solstice | 2026-02 | NewCo (~105 / 1,100 / 1,200) | harbourbiomed 257 | Porustobart CTLA-4; upfront equity-heavy |
| 海思科 → AirNexis | 2026-01 | **108 / 955 / 1,063** (was -/-/1000) | prnewswire 302657951 | HSK39004 PDE3/4, COPD, NewCo equity |

## Flags
- **B6 康诺亚/吉利德**: worst record — mixes two cash flows. Needs George's call (split / relabel / keep).
- No M&A-misfiled-as-BD, no direction reversals, no inflated totals (beyond B6 conflation).
- Scope flags affecting rNPV: 复宏汉霖/卫材 Japan-only; 先为达/辉瑞 China-only.
