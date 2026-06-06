"""拥挤度 (护栏②) — RRG 看不到筹码结构，这里补盲.

WHY (周期 agent 研判)：RRG 的 Leading 象限和拥挤度警戒区在时间上高度重叠——
板块越深入右上角、停留越久，越可能买盘枯竭。RRG 本身完全看不到筹码结构，宏观
没坏、微观交易结构塌时板块会从 Leading 直接崩 (跳过 Weakening)。所以叠加规则是：
**仅当 Leading 象限 AND 拥挤度 z > 阈值** 才标红 [过热]——这是 RRG 从"注意力地图"
升级为"可防误用工具"的关键增量，也是相对中信原版最有价值的差异化。

Tier A (本模块, v1) = per-sector 板块级拥挤：
  A股 : 换手率 z-score (turnover_z) — iFind 周换手率，真·成交集中度信号 (已实测)
  美股 : 价格拉伸 z-score (extension_z) — close/SMA200−1 的 z。⚠️ benchmarks_daily
         只有 close，无量；这是"拉伸/超买"代理，非真换手集中度。真·换手/breadth
         crowding 留 v2 (需成分股 EOD 聚合)。文案须如实标注两市场口径不同。

Tier B (大盘风险偏好闸 AAII/COT/GEX) 不在本模块——那是全站水印级，喂 lib.regime。
口径 scoping：docs/plans/2026-06-05-rrg-crowding-data-sources.md
"""

from __future__ import annotations

import numpy as np
import pandas as pd

OVERHEAT_Z = 1.5          # 默认过热阈值 (z-score)


def _last_z(s: pd.Series, win: int) -> float:
    """末值相对trailing窗口的 z-score (population std)。样本不足返回 nan。

    必须 sort_index 升序 — iFind 原样返回 newest-first，不排序会取到最老的点。
    """
    s = s.dropna().sort_index()
    if len(s) < max(8, win // 2):
        return float("nan")
    window = s.iloc[-win:] if len(s) > win else s
    mu = float(window.mean())
    sd = float(window.std(ddof=0))
    if sd == 0 or np.isnan(sd):
        return float("nan")
    return (float(s.iloc[-1]) - mu) / sd


def turnover_z(turnover_rate: pd.Series, win: int = 52) -> float:
    """A股板块换手率 z-score。turnover_rate = iFind 周换手率% 序列。"""
    return _last_z(turnover_rate, win)


def extension_z(close: pd.Series, *, sma_win: int = 200, z_win: int = 252) -> float:
    """美股 sector 价格拉伸 z-score = z(close/SMA(close,sma_win) − 1)。

    输入日频 close (benchmarks_daily)。sma_win/z_win 为交易日。周频输入时调小
    (sma_win≈40, z_win≈52)。代理"超买/拉伸"，非真换手集中度 (见模块 docstring)。
    """
    close = close.dropna().sort_index()
    if len(close) < sma_win + 8:
        return float("nan")
    ext = close / close.rolling(sma_win).mean() - 1.0
    return _last_z(ext, z_win)


def is_overheated(quadrant: str, z: float, *, thr: float = OVERHEAT_Z) -> bool:
    """护栏②叠加规则：仅 Leading 象限 + 拥挤度 z>阈值 → 标红 [过热]。"""
    if z is None or np.isnan(z):
        return False
    return quadrant == "Leading" and z > thr
