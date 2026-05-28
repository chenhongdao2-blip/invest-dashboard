# Project Docs — invest-dashboard

整个 dashboard 项目的文档 / 设计 / 审计沉淀，方便 IDE 一站式打开。

## 📂 结构

```
docs/
├── plans/                Initial implementation plans
├── audits/               Multi-agent code review artifacts
│   ├── round1/           First /cccg audit (post D1-D3 ship)
│   ├── round2/           Second /cccg audit (post D4-D5 ship)
│   └── prompts/          The actual questions sent to Codex / Gemini / GLM
├── screenshots/          Key visual milestones
└── README.md             ← you are here
```

## 📋 Plans

| File | Purpose | Date |
|---|---|---|
| [modular-toasting-spindle.md](plans/modular-toasting-spindle.md) | D1-D7 implementation plan + open questions + verification gates | 2026-05-28 |

## 🔬 Audit Round 1 (post D1-D3)

3-advisor review after D1 (repo bootstrap), D2 (data fetcher), D3 (Streamlit Home + Sector Heatmap).

| Advisor | Focus | Artifact | Prompt |
|---|---|---|---|
| **Codex** | Architecture / correctness / data integrity | [round1/codex-architecture.md](audits/round1/codex-architecture.md) | [prompts/round1-codex.md](audits/prompts/round1-codex.md) |
| **Gemini** | UX / docs / alternatives | [round1/gemini-ux.md](audits/round1/gemini-ux.md) | [prompts/round1-gemini.md](audits/prompts/round1-gemini.md) |
| **GLM** | 中文卖方 / 国内 SDK / domain critique | [round1/glm-domestic-sellside.md](audits/round1/glm-domestic-sellside.md) | [prompts/round1-glm.md](audits/prompts/round1-glm.md) |

**Key findings**：
- Codex: USD price normalization missing, YTD anchor fake, yfinance rate limit too optimistic
- Gemini: Dropdown → tabs; NaN → "—"; global search needed; dark theme not loading
- GLM: name_cn 优先 / mcap desc sort 默认 / Bloomberg ticker style / 4587.T 拉低 biotech 均值

Resolved via commits `251c6de` (Round 1 fixes).

## 🔬 Audit Round 2 (post D4-D5)

3-advisor review after D4 (Strategy Picks) and D5 (CMSI Coverage + Valuation Scanner).

| Advisor | Focus | Artifact | Prompt |
|---|---|---|---|
| **Codex** | Architecture / correctness | [round2/codex-architecture.md](audits/round2/codex-architecture.md) | [prompts/round2-codex.md](audits/prompts/round2-codex.md) |
| **Gemini** | UX / docs (also applied auto-fixes via YOLO mode) | [round2/gemini-ux.md](audits/round2/gemini-ux.md) | [prompts/round2-gemini.md](audits/prompts/round2-gemini.md) |
| **GLM** | 中文卖方 framework / 国内 ops | [round2/glm-domestic-sellside.md](audits/round2/glm-domestic-sellside.md) | [prompts/round2-glm.md](audits/prompts/round2-glm.md) |

**Key findings**:
- Codex: **picks.db raw IP leak** (full ic-foundry ledger w/ thesis/conviction JSON), portfolio math mismatch with weekly_perf.py
- Gemini: Chart overload (27+ lines) → dispersion band, fragmented nav → unified session state, filter cognitive load → Presets
- GLM: P/E percentile cross-sectional 是 quant 半成品（卖方真用 5Y P/E band）, $5B min mcap 港股严重失真, look-ahead bias 警告

Resolved via commits:
- `16a190a` Round 2 fixes (B1 IP scrub / page rename / dispersion band / Presets / TP upside)
- `f6d8e4b` Sort numeric bug fix on CMSI Coverage

## 🖼️ Screenshots

| File | What it shows |
|---|---|
| [d3-healthcare.jpg](screenshots/d3-healthcare.jpg) | D3 Healthcare overview, light theme |
| [d3-sector-heatmap.jpg](screenshots/d3-sector-heatmap.jpg) | D3 Sector Heatmap with diverging gradient |
| [d4-strategy-picks.jpg](screenshots/d4-strategy-picks.jpg) | D4 v4 biotech, +1.04% portfolio / +3.12pp alpha |
| [audit-heatmap.jpg](screenshots/audit-heatmap.jpg) | Post-Round-1 dark theme + tabs + mcap desc sort |
| [r2-sort-fixed.jpg](screenshots/r2-sort-fixed.jpg) | CMSI Coverage page with TP Upside / column_config rendering |

## 🔗 Cross-references

- Live URL: TBD (Streamlit Community Cloud deploy is D7)
- Upstream: ic-foundry ledger via `scripts/sync_ledger.sh`
- Cron: `.github/workflows/fetch_eod.yml` runs daily 22:30 UTC US + 09:00 UTC HK
- Skipped audit items (P1 defer): 港股通/北向资金、5Y P/E band time-series、CSRC/集采 calendar overlay

## ✏️ Future write-here notes

- TODOs / scratch / design iterations: add as `docs/notes/<topic>.md`
- D6 Ticker Drill design: TBD
- Performance / cache optimization ideas: TBD
