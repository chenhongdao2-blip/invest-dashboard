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

已验证可用代码 (标准申万一级31 — 周线后缀必须 .SL，.SI 多数返回空!)：
  基准: 000300.SH 沪深300 (不入 sector)
  31行业(.SL): 801010农林牧渔 801030基础化工 801040钢铁 801050有色金属 801080电子
  801110家用电器 801120食品饮料 801130纺织服饰 801140轻工制造 801150医药生物
  801160公用事业 801170交通运输 801180房地产 801200商贸零售 801210社会服务
  801230综合 801710建筑材料 801720建筑装饰 801730电力设备 801740国防军工
  801750计算机 801760传媒 801770通信 801780银行 801790非银金融 801880汽车
  801890机械设备 801950煤炭 801960石油石化 801970环保 801980美容护理
  ⚠️ 部分行业(家电/医药/计算机)周线多返回一列"自由流通换手率"→解析取"收盘=最大数值,
     换手=末列"鲁棒法(见 jobs/_gen_sw31_seed.py)。
  港股11(HSCI*族): 见 jobs/_gen_hk_seed.py，基准 HSI.GI。

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

# 已验证代码表 (code -> (name_cn, is_benchmark))。申万一级周线后缀 .SL。
CODE_MAP: dict[str, tuple[str, bool]] = {
    "000300.SH": ("沪深300", True),
    "801010.SL": ("农林牧渔", False), "801030.SL": ("基础化工", False),
    "801040.SL": ("钢铁", False), "801050.SL": ("有色金属", False),
    "801080.SL": ("电子", False), "801110.SL": ("家用电器", False),
    "801120.SL": ("食品饮料", False), "801130.SL": ("纺织服饰", False),
    "801140.SL": ("轻工制造", False), "801150.SL": ("医药生物", False),
    "801160.SL": ("公用事业", False), "801170.SL": ("交通运输", False),
    "801180.SL": ("房地产", False), "801200.SL": ("商贸零售", False),
    "801210.SL": ("社会服务", False), "801230.SL": ("综合", False),
    "801710.SL": ("建筑材料", False), "801720.SL": ("建筑装饰", False),
    "801730.SL": ("电力设备", False), "801740.SL": ("国防军工", False),
    "801750.SL": ("计算机", False), "801760.SL": ("传媒", False),
    "801770.SL": ("通信", False), "801780.SL": ("银行", False),
    "801790.SL": ("非银金融", False), "801880.SL": ("汽车", False),
    "801890.SL": ("机械设备", False), "801950.SL": ("煤炭", False),
    "801960.SL": ("石油石化", False), "801970.SL": ("环保", False),
    "801980.SL": ("美容护理", False),
}

if __name__ == "__main__":
    raise SystemExit(
        "本脚本是 iFind MCP 拉取流程的文档 + 代码表，不能直接 python 运行。\n"
        "请在本地 Claude 父会话里按 docstring 的 RECIPE 用 index_data MCP 逐行业拉取，\n"
        "写 data/external/sw_industry_seed.csv，再跑 jobs/load_sw_industry.py 入库。"
    )
