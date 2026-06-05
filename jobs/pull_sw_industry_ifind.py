"""拉申万/中证行业指数周线 → 生成 sw_industry_seed.csv (RRG 板块轮动数据源).

⚠️ 本脚本依赖 iFind index MCP，**只能在本地 Claude 父会话里跑**（MCP 绑父会话，
   GitHub Actions cron 上没有）。它不是一个能 `python` 直接跑的脚本——它是「父会话
   按下面的 RECIPE 用 MCP 逐行业拉、把结果写进 seed CSV」这套流程的可执行文档 +
   验证过的代码表。刷新 = 重跑这套 recipe 重生 CSV 后 commit。

────────────────────────────────────────────────────────────────────────────
实测 iFind 管道铁律 (2026-06-05 摸清，违反即拿到脏数据)：
  • 周线一次拿满 52 周 (~52 行，~80 行/次上限内) → 单调用即得 close+周换手率
  • 自然语言名称解析**不可靠**，跨 申万SL/中证CSI/中信CI 三族乱跳：
      "申万电子" → 802612.SL (全空)   "申万银行" → 801001.SL (竟是申万50!)
    ⇒ **必须钉死显式代码 + 逐个验证非空**，不靠模糊名
  • 多实体合并查询会被压成单实体 ⇒ 逐行业调用
  • 周线代码族与日线不同：日线 医药=801150.SL，周线 医药=000808.CSI

已验证可用代码 (v1 seed 初始板块集 — 注意是 中证细分+中信 混合，非纯申万一级)：
  000300.SH  沪深300        (基准, benchmark — 不入 sector)
  000808.CSI 医药生物
  000807.CSI 食品饮料
  000806.CSI 消费服务
  000805.CSI A股资源
  000811.CSI 细分有色
  000812.CSI 细分机械
  CI005026.CI 通信           (中信口径)

TODO(v2): 建标准「申万一级 28/31」验证代码表替换上面的混合集。申万一级的 .SL/.SI
  代码在 iFind 周线下多数解析失败，需逐个用显式代码 probe 出可用的那支再固化。

RECIPE (父会话执行)：
  for code, name in CODE_MAP.items():
      r = mcp__hexin-ifind-ds-index-mcp__index_data(
            query=f"{code} 近52周周线收盘点位与周换手率")
      # 解析 r 的 markdown 表 → rows [(code,name,YYYY-MM-DD,close,turnover_rate)]
      # 跳过 "查询结果为空" 与空白行
  写 data/external/sw_industry_seed.csv (列: ticker,name_cn,date,close,turnover_rate)
  然后: python jobs/load_sw_industry.py   # 入库 sw_industry_daily
"""
from __future__ import annotations

# 已验证代码表 (code -> (name_cn, is_benchmark))
CODE_MAP: dict[str, tuple[str, bool]] = {
    "000300.SH": ("沪深300", True),
    "000808.CSI": ("医药生物", False),
    "000807.CSI": ("食品饮料", False),
    "000806.CSI": ("消费服务", False),
    "000805.CSI": ("A股资源", False),
    "000811.CSI": ("细分有色", False),
    "000812.CSI": ("细分机械", False),
    "CI005026.CI": ("通信", False),
}

if __name__ == "__main__":
    raise SystemExit(
        "本脚本是 iFind MCP 拉取流程的文档 + 代码表，不能直接 python 运行。\n"
        "请在本地 Claude 父会话里按 docstring 的 RECIPE 用 index_data MCP 逐行业拉取，\n"
        "写 data/external/sw_industry_seed.csv，再跑 jobs/load_sw_industry.py 入库。"
    )
