# Stage 2 · Independent Evaluator — Round 4 Verdict (FINAL, max_cycles=4)

Task: K线行情 FT-salmon glass 1:1 重实现 · Ticker Drill 整页 reskin
Branch: `feat/kline-reskin` @ `4d746ec` ("tooltip params 双形状防御归一")
Real machine: `init.sh` → :8599 HTTP 200 (restarted, py_compile clean).
Scope: C5 tooltip value re-verification (the R3 FAIL) + diff-scope spot.

**Result: C5 tooltip PASS — the R3 regression is fixed by defensive shape-normalization. Diff is formatter-only, no drift. ALL 11 FEATURES → `passes:true`. cycles_used=4.**

---

## 1. C5 tooltip value correctness — **PASS** (was R3 FAIL)

The fix normalizes both param shapes before indexing:
`var a = (v && v.length===5) ? v.slice(1) : v;` then reads `a[0..3]`. This handles the live category-axis shape `[dataIndex,open,close,low,high]` (slices off the index) AND the nominal `[open,close,low,high]`.

Verified **three independent ways** on `000977.SZ` (last candle idx 266; true OHLC 开67.00/高69.21/低63.79/收66.35):

1. **Programmatic formatter run on the REAL live 5-element param** `[266,67,66.35,63.79,69.21]` → `{开:67.00, 收:66.35, 低:63.79, 高:69.21}`; and on the nominal 4-element `[67,66.35,63.79,69.21]` → same. Both `live_match=true` AND `nominal_match=true` vs the panel.
2. **Real rendered tooltip DOM** for the last candle (`dispatchAction showTip` → read DOM): `{开:67.00, 收:66.35, 低:63.79, 高:69.21}` = panel exactly, `all_four_equal=true`.
3. **Real mouse hover** (screenshot ss_5849iokk6 + zoom, 06/26 candle): `开 67.00 · 收 63.89 · 低 63.66 · 高 67.20` — all sane prices, no dataIndex, low(63.66) ≤ high(67.20). Contrast R3's broken `开 263.00 · 低 70 > 高 64.83`.

The R3 failure mode (开 showing dataIndex 266) is gone. C5 value-level assertion PASS; tooltip styling (bg #1a1a1a / text #fff1e5 / cross dashed #b8b1a8) unchanged.

## 2. Diff-scope spot — **PASS**

`git diff 3f2c839..4d746ec --stat`: only `app/lib/candlestick_terminal.py` (15 lines, all inside the formatter region 339-352) + docs (`eval/round-3.md`, `feature_list.json`). No other code drift. `py_compile` clean.

## 3. Regression spot-check — **PASS (no drift)**

C1 candle `#0d7680/#c8102e` · C2 MA `#e0963c/#b8b1a8/#1a1a1a` · C10 series `{日K,MA5,MA10,MA20,Vol}` · T10 footer convention note present · T2 glow `900×520@10%/-8% α.09` · #kc `560` · metric cells 4 (振幅/量比(5日)/换手率/市盈率 — 量比 & PE guards from R3 still intact for 000977). The other two Codex fixes (量比 nullable, PE isfinite) carried over from R3 PASS.

## Final ledger — 11/11 PASS

| feature | R4 |
|---|---|
| U1-fonts | PASS |
| U2-term-shell | PASS |
| U3-term-header | PASS |
| U4-term-panel | PASS |
| **U5-chart-option** | **PASS (C5 tooltip fixed — restored from R3 revert)** |
| U6-bench-removal | PASS |
| U7-page-shell | PASS |
| U8-page-sections | PASS (P8c amended; P8b/P8d code-verified env-blocked) |
| U9-i18n-guards | PASS |
| U10-regression | PASS |
| U11-harness-init | PASS |

**ALL GREEN. Zero outstanding FAILs. Ready for Stage 4 (Codex final approve) + Stage 5 (George ship).**

Carry-over note for Codex final approve / George: (a) P8b/P8d were code-verified only (internal wiki absent on this eval machine — render one covered name with house rating+TP to fully close). (b) The C5 tooltip round-trip (R3 break → R4 fix) shows this echarts candlestick setup prepends the category index to `params.data`; the normalization guards both shapes, so future data-shape changes stay safe.
