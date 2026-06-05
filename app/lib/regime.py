"""周期级别水印 (护栏①) — 给 RRG 盖一个"战术 vs 战略"资格背景.

WHY (周期 agent 研判 + 周金涛级别服从 R5)：RRG 信号是周–月级别 (基钦以下)，
只能解释节奏，绝不能推翻大级别约束。康波/债务周期下行期里某板块 Leading 8 周，
只能定义为"战术抢反弹"，不构成战略重仓依据。本模块把这条级别服从物化进 UI：
level=战术 时页面顶部打水印"⚠️ 本图轮动仅供战术，不构成战略配置依据"。

v1 数据来源 (两档)：
  1) config/rotation_regime.yml — 分析师周度手设的母框架背景 (优先)。George 是
     宏观判断主体；手设 backdrop 文案 (康波/信用-盈利象限) + level。
  2) auto 兜底 — 基准 vs SMA200 + 斜率：close>SMA 且 SMA 上行→战略多头；
     close<SMA→战略防御/战术。仅当 config 缺该市场时启用。
全自动宏观 regime feed (Dalio 信用脉冲等) 留 v2。
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

try:
    import yaml
except ImportError:                       # pragma: no cover
    yaml = None

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = REPO_ROOT / "config" / "rotation_regime.yml"

_TACTICAL = "战术"
_STRATEGIC = "战略"

_WATERMARK_CN = "⚠️ 战术级别：本图轮动信号仅供战术，不构成战略配置依据"
_WATERMARK_EN = "⚠️ Tactical regime: rotation signals are tactical only — not a strategic allocation basis"


def load_config(path: Path | str = CONFIG_PATH) -> dict:
    p = Path(path)
    if yaml is None or not p.exists():
        return {}
    try:
        with p.open(encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def auto_regime(benchmark: pd.Series, *, sma_win: int = 40) -> tuple[str, str]:
    """兜底：基准 vs SMA + 斜率 → (level, backdrop_cn)。

    sma_win 单位 = 输入序列的 bar (周频用 40≈200日；日频用 200)。
    """
    s = benchmark.dropna().sort_index()
    if len(s) < sma_win + 4:
        return _TACTICAL, "历史不足，默认按战术级别审慎对待"
    sma = s.rolling(sma_win).mean()
    last, sma_last = float(s.iloc[-1]), float(sma.iloc[-1])
    sma_prev = float(sma.iloc[-4])               # ~1 月前斜率
    rising = sma_last > sma_prev
    if last > sma_last and rising:
        return _STRATEGIC, "基准在 200 日均线上方且均线上行 → 战略多头背景"
    if last < sma_last:
        return _TACTICAL, "基准跌破 200 日均线 → 战略防御，轮动信号仅作战术"
    return _TACTICAL, "基准均线走平/震荡 → 级别未定，按战术对待"


def regime_banner(
    market: str,
    benchmark: pd.Series | None = None,
    *,
    prefer_cn: bool = True,
    cfg: dict | None = None,
) -> dict:
    """返回 {level, backdrop, is_tactical, watermark}。

    market: "a_share" | "us"。config 优先，缺则 auto_regime 兜底 (需 benchmark)。
    """
    cfg = load_config() if cfg is None else cfg
    entry = (cfg.get(market) or {}) if isinstance(cfg, dict) else {}

    level = entry.get("level")
    backdrop = entry.get("backdrop")
    if level not in (_TACTICAL, _STRATEGIC):
        if benchmark is not None and len(benchmark.dropna()):
            level, auto_backdrop = auto_regime(benchmark)
            backdrop = backdrop or auto_backdrop
        else:
            level, backdrop = _TACTICAL, backdrop or "无数据，默认战术级别"

    is_tactical = level == _TACTICAL
    watermark = (_WATERMARK_CN if prefer_cn else _WATERMARK_EN) if is_tactical else ""
    return {
        "level": level,
        "backdrop": backdrop or "",
        "is_tactical": is_tactical,
        "watermark": watermark,
    }
