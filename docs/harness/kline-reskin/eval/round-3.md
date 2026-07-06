# Stage 2 · Independent Evaluator — Round 3 Verdict

Task: K线行情 FT-salmon glass 1:1 重实现 · Ticker Drill 整页 reskin
Branch: `feat/kline-reskin` @ `3f2c839` (Codex 终审 3 MAJOR 修复 commit)
Real machine: `init.sh` → :8599 HTTP 200 (restarted, py_compile clean).
Scope: targeted re-verify of the 3 Codex fixes + new C5 value-level assertion + regression.

**Result: 1 NEW FAIL — the Codex tooltip "fix" REGRESSED the OHLC tooltip (shows dataIndex as 开). The other two Codex fixes (量比/PE guards) PASS. Regression spot-check clean. NOT clean — bounce to Builder. U5-chart-option reverts to `passes:false`.**

---

## 1. Tooltip value correctness (NEW C5 value-level assertion) — **FAIL**

The Codex fix changed the formatter indices from `v[1..4]` (original, correct) to `v[0..3]` on the theory that `k.data = [open,close,low,high]` (indices 0-3). **That theory is wrong for this ECharts candlestick setup.** Empirically, on a category x-axis, the live tooltip `params.data` = **`[dataIndex, open, close, low, high]`** (5-element, index prepended) — so the correct indices are 1-4, i.e. the ORIGINAL code.

Four independent confirmations (all on `000977.SZ`, up-day, last candle dataIndex 266, true OHLC 开67.00/高69.21/低63.79/收66.35):

1. **Real mouse hover** (screenshot ss_0394g8uey + zoom): tooltip for the 06/30 candle showed `开 263.00 · 收 65.21 · 低 70.00 · 高 64.83` — 开 = a 3-digit index where price is ~66, and 低 (70) > 高 (64.83), physically impossible.
2. **Programmatic param capture** (intercepted formatter + `dispatchAction showTip`): `params.data = params.value = [266, 67, 66.35, 63.79, 69.21]` = `[dataIndex, open, close, low, high]`; `getOption().series.data[last] = [67, 66.35, 63.79, 69.21]` (index stripped — this is why a naive `getOption`-based probe gives a FALSE pass).
3. **Deployed formatter run with the real 5-element param**: output `{开:266.00, 收:67.00, 低:66.35, 高:63.79}` vs truth `{开:67.00, 收:66.35, 低:63.79, 高:69.21}` → verdict string "BROKEN — 开 shows dataIndex". Every value shifted; the true high (69.21) is dropped entirely.
4. **Source**: `app/lib/candlestick_terminal.py:345-350` — `var v=k.data;` then `开 fmt(v[0]) / 收 fmt(v[1]) / 低 fmt(v[2]) / 高 fmt(v[3])`. (The fix's own comment on line 343 even documents the category-axis layout as `[xCategoryValue,open,close,low,high]` (indices 1-4) but then wrongly assumes `k.data` differs from `k.value`; my probe shows `k.data === k.value === [266,67,66.35,63.79,69.21]`.)

**Fix (file:line):** `app/lib/candlestick_terminal.py:347-350` — revert to `fmt(v[1])` / `fmt(v[2])` / `fmt(v[3])` / `fmt(v[4])` (i.e. the ORIGINAL v[1..4]), and correct the misleading comment at 342-344. Net: the Codex MAJOR-1 "fix" should be reverted; the R2 tooltip was already correct.

Note on prior rounds: R1/R2 used `v[1..4]` and thus rendered correct values — my R1/R2 C5 PASS (formatter-existence only, not value-level) happened to be correct in outcome. This regression is NEW in `3f2c839`. Tooltip STYLING (bg #1a1a1a / text #fff1e5 / cross dashed #b8b1a8) is unaffected and still passes; only value correctness fails.

## 2. 量比 nullable guard + PE isfinite guard — **PASS**

| ticker | scenario | metric cells | verdict |
|---|---|---|---|
| 000977.SZ | normal | 振幅=8.50% · 量比(5日)=1.12x · 换手率=6.73% · 市盈率=18.3x (4 cells) | PASS — 量比 & PE both render on real data |
| BNTX | forward_pe = **−19.37** (loss-making) | 振幅=4.60% · 量比(5日)=1.92x · 换手率=0.55% (**3 cells, NO 市盈率**) | PASS — negative PE suppressed by `isfinite && >0`; graceful 4→3 degrade |

- No `nanx` / `NaN` literals in either terminal (`has_nanx=false`, `has_NaN=false`; the earlier `'nan'` substring hit was a false positive inside "yfi**nan**ce" in the footer).
- 2696.HK confirmed the no-OHLCV plotly fallback (terminal not rendered) — orthogonal but consistent with G7.

## 3. Regression spot-check (000977 + BNTX) — **PASS**

- T10 footer: `配色(港美股惯例):青 = 涨 · 红 = 跌(与 A 股红涨绿跌相反) · 来源: yfinance…` present ✓
- T2 glow: `900px 520px at 10% -8% rgba(200,16,46,0.09) + 820px 520px at 94% 4% rgba(13,118,128,0.1)` — unchanged ✓
- T11 #kc offsetHeight = 560 ✓
- C1 candle `#0d7680/#c8102e` ✓ · C2 MA `#e0963c/#b8b1a8/#1a1a1a` ✓ · C10 series `{日K,MA5,MA10,MA20,Vol}` ✓

## Verdict

| feature | accept | R3 |
|---|---|---|
| U5-chart-option | C1-C9,C11 + **C5 (value-level)** | **FAIL → reverted to passes:false** (C5 tooltip values broken) |
| U4-term-panel | T5,T6,T7,T8,T9,T10 | PASS held (PE/量比 guards confirmed; T8 degrade verified) |
| (all other 9 features) | — | PASS held (unchanged from R2) |

**Round 3 NOT clean.** One-line revert needed at `candlestick_terminal.py:347-350` (v[0..3] → v[1..4]). Everything else — including the other two Codex MAJOR fixes (量比 nullable, PE isfinite) — is verified good. `cycles_used=3` (1 of 4 remaining). Recommend the Builder revert MAJOR-1 and re-submit for a fast Round 4 tooltip-only re-check.
