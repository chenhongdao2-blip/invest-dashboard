"""个股行情终端 · ECharts 暗色 K 线 — lib/candlestick_terminal.py
====================================================================

Hybrid 基调:整站 cream 编辑底 + 「行情/个股」这类 chart-heavy surface 局部上**暗色交易台**
(源自设计项目的 `K线行情.dc.html` dark terminal 思路),作为一块自包含 dark 模块嵌进 cream 页。

与 strategy_hero / heatmap_treemap 同套路:单张大 echarts 走 st.iframe(self-contained srcdoc),
自托管 echarts(`/app/static/echarts.min.js`,China 安全)。**单张大图**(非小多图)→ 不触
「0 宽 grid 列 echarts.init 竞态画空白」那条坑;srcdoc 内 `html,body{height:100%}` + 容器显式高。

落地纪律(踩过坑 / George 拍板):
- 数据 = 真实 EOD OHLCV(yfinance auto_adjust),**非 mock**;**无假实时 tick / 无 LIVE 脉冲 / 无时钟**
  (设计稿那套 1500ms 模拟 tick 是演示用,真实数据是 EOD,造假=违纪 + 无 TRACKING 决策)。
- 涨跌色走 **app 惯例:涨 teal / 跌 red**(港美股),**不**用 K线行情 设计稿的 A 股「红涨绿跌」。
- 字体走**自托管 Inter + JetBrains Mono**(不引 Space Grotesk / IBM Plex Mono CDN — 国内会挂)。
- 入场只做 echarts 自带 draw-in(animationDuration),不做花哨动效。

调用(pages/6_Ticker_Drill.py 行情区):
    from lib import candlestick_terminal as cterm
    ohlcv = cterm.fetch_ohlcv(ticker)           # cached yfinance OHLCV(DB 只存 close,这里单独取)
    if cterm.render(ticker=ticker, name=display_name, df=ohlcv, ccy=ccy,
                    prefer_cn=(i18n.get_lang()=='zh'), as_of=latest):
        pass                                      # 渲染成功;失败(无数据)返回 False → 上层走原 RS 图
"""
from __future__ import annotations

import json
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from lib import theme
from lib import echarts_boot

# 相对路径(NO 前导 /):Streamlit Cloud 把 app 服务在 /~/+/ 前缀下,srcdoc iframe 的
# baseURI = 该前缀;相对 "app/static/..." 解析为 /~/+/app/static/...(云端实测 load ✓),
# 本地(无前缀)解析为 /app/static/...。**禁改回绝对 "/app/static/..."** —— 云端丢前缀
# → 撞 login 重定向 → echarts 永远 undefined → 全站图空白(2026-07-01 实机验证根因)。
ECHARTS_SRC = "app/static/echarts.min.js"

# 亮版(cream)终端调色板 — 全站统一 cream FT 调,终端的「冲击力」来自密度/结构而非暗色皮。
# (George 2026-06-30:暗色太跳,要亮版;放弃 Hybrid 的 dark-terminal,整站留 cream。)
_BG = theme.PAPER          # cream 页底 #fff1e5
_PANEL = theme.PAPER       # 卡片:同底色 + 1px border 定义(market_hub_tiles / hero 同套路)
_EDGE = theme.PAPER_EDGE   # 描边 #d4c4b0
_GRID = theme.PAPER_RULE   # 网格线 #ebd9c8
_INK = theme.INK           # 主文字 #1a1a1a
_MUTE = theme.INK_2        # 次文字(加深 · George:灰字太淡看不清)~#4a4a4a
_FAINT = theme.INK_3       # 弱文字 / 轴标(加深一级)~#8a8580
_UP = theme.UP             # 涨 teal #0d7680
_DOWN = theme.DOWN         # 跌 red #cc0000
# MA 线在 cream 上的克制配色(避开 teal/red/招商红,免与涨跌/品牌色撞)
_MA5, _MA10, _MA20 = "#a07a2c", "#4a6fa5", "#9a6a9e"   # 金 / 青石蓝 / 黛紫


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_ohlcv(ticker: str, lookback_days: int = 400) -> pd.DataFrame:
    """单 ticker 的真实 OHLCV(yfinance, auto_adjust, cached 1h)。DB 只存 close,K 线需 OHLC 故单取。
    proxy 走进程 env(app 启动已注入 https_proxy);失败/空 → 空 DataFrame(上层 fallback)。"""
    import yfinance as yf

    start = (date.today() - timedelta(days=lookback_days)).isoformat()
    end = (date.today() + timedelta(days=1)).isoformat()
    try:
        d = yf.download(ticker, start=start, end=end, auto_adjust=True,
                        progress=False, threads=False)
    except Exception:
        return pd.DataFrame()
    if d is None or d.empty:
        return pd.DataFrame()
    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.droplevel(1)
    need = ["Open", "High", "Low", "Close"]
    if not all(c in d.columns for c in need):
        return pd.DataFrame()
    keep = need + (["Volume"] if "Volume" in d.columns else [])
    return d[keep].dropna(subset=need)


def _ma(close: pd.Series, n: int) -> list:
    m = close.rolling(n).mean()
    return [None if pd.isna(v) else round(float(v), 2) for v in m]


def _fmt(v: float) -> str:
    return f"{v:,.2f}"


def render(*, ticker: str, name: str, df: pd.DataFrame, ccy: str,
           prefer_cn: bool, as_of: str | None = None, height: int = 540,
           bench_overlay: tuple[str, list] | None = None,
           show_header: bool = True) -> bool:
    """渲染 cream K 线终端;成功 True,数据不足 False(上层回退原图)。

    bench_overlay = (基准名, [值…]) — 板块基准相对强弱**折进 K 线**(George 指示:
    基准跟 K 线放一起不另开一栏)。值已由上层按区间起点 rebase 到本股价格,故与蜡烛同
    一价格轴;画成灰色虚线,蜡烛在虚线上方=跑赢板块。None → 只画蜡烛。

    show_header — 顶部「代码 + 名称 + 交易所 chip + meta」头。页面用 False(masthead 已带
    身份,设计稿 个股行情 美化 的 price panel 无重复头);弹窗 modal 用 True(无 masthead)。
    卡片走毛玻璃(rgba 白 + blur)叠角落径向微光,对齐设计稿 glass price panel。"""
    if df is None or df.empty or len(df) < 5:
        return False

    o, h, l, c = df["Open"], df["High"], df["Low"], df["Close"]
    dates = [d.strftime("%m/%d") for d in df.index]
    # echarts candlestick 值序 = [open, close, low, high]
    kline = [[round(float(o.iloc[i]), 2), round(float(c.iloc[i]), 2),
              round(float(l.iloc[i]), 2), round(float(h.iloc[i]), 2)]
             for i in range(len(df))]
    if "Volume" in df.columns:
        vol = [0 if pd.isna(v) else int(v) for v in df["Volume"]]
    else:
        vol = [0] * len(df)
    # 量柱颜色随当日 K 阴阳
    vol_up = [bool(kline[i][1] >= kline[i][0]) for i in range(len(df))]

    last = float(c.iloc[-1])
    prev = float(c.iloc[-2]) if len(c) > 1 else last
    chg = last - prev
    chgpct = (chg / prev * 100) if prev else 0.0
    up = chg >= 0
    col = _UP if up else _DOWN
    last_o, last_h, last_l = float(o.iloc[-1]), float(h.iloc[-1]), float(l.iloc[-1])
    ampl = ((last_h - last_l) / prev * 100) if prev else 0.0
    phi, plo = float(h.max()), float(l.min())
    avg_vol = (sum(vol[-20:]) / max(1, len(vol[-20:]))) if vol else 0

    exch = {".HK": "HKEX · 香港", ".SS": "SSE · 上海", ".SZ": "SZSE · 深圳",
            ".T": "TSE · 东京", ".KS": "KRX · 韩国", ".KQ": "KOSDAQ"}.get(
        next((s for s in [".HK", ".SS", ".SZ", ".T", ".KS", ".KQ"] if ticker.endswith(s)), ""),
        "US · 美股")

    bench_name = bench_overlay[0] if bench_overlay else None
    bench_vals = bench_overlay[1] if bench_overlay else None

    payload = {
        "dates": dates, "kline": kline, "vol": vol, "volUp": vol_up,
        "ma5": _ma(c, 5), "ma10": _ma(c, 10), "ma20": _ma(c, 20),
        "bench": bench_vals, "benchName": bench_name,
        "UP": _UP, "DOWN": _DOWN, "INK": _INK, "MUTE": _MUTE, "FAINT": _FAINT,
        "EDGE": _EDGE, "GRID": _GRID, "PANEL": _PANEL, "BG": _BG, "PAPER": theme.PAPER,
        "MA5C": _MA5, "MA10C": _MA10, "MA20C": _MA20,
        "MONO": theme.FONT_MONO, "FONT": theme.FONT_STACK,
        "n": len(df),
    }

    def stat(lbl, val, vcol=None):
        vc = vcol or _INK
        return (f'<div class="st"><div class="stl">{lbl}</div>'
                f'<div class="stv" style="color:{vc}">{val}</div></div>')

    chg_chip = (f'<span class="chip" style="color:{col};background:rgba('
                f'{"13,118,128" if up else "204,0,0"},.12)">'
                f'{"+" if up else ""}{chgpct:.2f}%</span>')

    meta = ("日K · MA5/10/20 · 成交量 · EOD 收盘" if prefer_cn
            else "Daily · MA5/10/20 · Volume · EOD close")
    if bench_overlay:
        meta += (" · 虚线 vs 板块基准(起点对齐)" if prefer_cn
                 else " · dashed = vs sector (rebased)")
    src = (f"来源 yfinance · 复权 OHLCV · {ticker} · 截至 {as_of or df.index[-1].strftime('%Y-%m-%d')}"
           if prefer_cn else
           f"Source: yfinance · adj OHLCV · {ticker} · as of {as_of or df.index[-1].strftime('%Y-%m-%d')}")

    panel = (
        '<div class="side">'
        '<div class="pcard">'
        f'<div class="plbl">{"最新价 LAST" if prefer_cn else "LAST PRICE"}</div>'
        f'<div class="prow"><span class="pbig" style="color:{col}">{_fmt(last)}</span>'
        f'<span class="pccy">{ccy}</span></div>'
        f'<div class="pchg"><span style="color:{col};font-weight:700">'
        f'{"+" if up else ""}{_fmt(chg)}</span>{chg_chip}</div></div>'
        '<div class="pcard">'
        f'<div class="plbl">{"当日 OHLC" if prefer_cn else "TODAY OHLC"}</div>'
        f'<div class="ohlc">'
        f'<div><span>{"开" if prefer_cn else "O"}</span><b>{_fmt(last_o)}</b></div>'
        f'<div><span>{"高" if prefer_cn else "H"}</span><b style="color:{_UP}">{_fmt(last_h)}</b></div>'
        f'<div><span>{"低" if prefer_cn else "L"}</span><b style="color:{_DOWN}">{_fmt(last_l)}</b></div>'
        f'<div><span>{"收" if prefer_cn else "C"}</span><b>{_fmt(last)}</b></div></div></div>'
        '<div class="pcard pgrid">'
        + stat("振幅" if prefer_cn else "AMPL", f"{ampl:.2f}%")
        + stat(("区间高" if prefer_cn else "RANGE HI"), _fmt(phi), _UP)
        + stat(("区间低" if prefer_cn else "RANGE LO"), _fmt(plo), _DOWN)
        + stat(("均量(20)" if prefer_cn else "AVG VOL"), f"{avg_vol/1e6:.1f}M" if avg_vol >= 1e6 else f"{avg_vol/1e3:.0f}K")
        + '</div></div>'
    )

    # 毛玻璃卡(rgba 白 + blur)叠角落径向微光 —— 对齐设计稿「个股行情 美化」glass price panel。
    chart_h = (height - 150) if show_header else (height - 56)
    _GLASS = "rgba(255,255,255,.5)"      # chart card
    _GLASS2 = "rgba(255,255,255,.55)"    # side cards
    _GBORD = "rgba(255,255,255,.7)"      # glass hairline
    _term_pad = "14px 16px 12px" if show_header else "4px 4px 8px"
    css = f"""
    *{{box-sizing:border-box;margin:0;padding:0}}
    html,body{{height:100%;background:{_BG};color:{_INK};font-family:{theme.FONT_STACK};
      font-feature-settings:'tnum','ss01';-webkit-font-smoothing:antialiased;color-scheme:light}}
    body{{position:relative;overflow:hidden}}
    .glow{{position:absolute;inset:0;z-index:0;pointer-events:none;
      background:radial-gradient(820px 480px at 8% -10%,rgba(200,16,46,.08),transparent 60%),
                 radial-gradient(760px 480px at 96% 4%,rgba(13,118,128,.10),transparent 60%)}}
    .term{{position:relative;z-index:1;padding:{_term_pad};min-height:100%}}
    .thead{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:14px}}
    .tk{{display:flex;align-items:baseline;gap:13px}}
    .tk .tick{{width:4px;height:24px;background:{theme.CMSI_RED};display:inline-block;align-self:center}}
    .tk .code{{font-family:{theme.FONT_MONO};font-size:24px;font-weight:700;color:{_INK};letter-spacing:.01em}}
    .tk .nm{{font-size:20px;font-weight:600;color:{_INK};letter-spacing:.01em}}
    .tk .ex{{font-family:{theme.FONT_MONO};font-size:11px;color:{_MUTE};border:1px solid {_EDGE};
      border-radius:4px;padding:3px 8px;align-self:center}}
    .tmeta{{font-family:{theme.FONT_MONO};font-size:11px;color:{_FAINT};letter-spacing:.04em;text-align:right;padding-top:6px}}
    .body{{display:grid;grid-template-columns:1fr 300px;gap:16px;align-items:stretch}}
    .chartcard{{background:{_GLASS};-webkit-backdrop-filter:blur(16px);backdrop-filter:blur(16px);
      border:1px solid {_GBORD};border-radius:4px;padding:8px;min-width:0}}
    #kc{{width:100%;height:{chart_h}px}}
    .side{{display:flex;flex-direction:column;gap:14px}}
    .pcard{{background:{_GLASS2};-webkit-backdrop-filter:blur(14px);backdrop-filter:blur(14px);
      border:1px solid {_GBORD};border-radius:4px;padding:18px 20px;box-shadow:0 1px 0 rgba(26,26,26,.04)}}
    .plbl{{font-family:{theme.FONT_MONO};font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:{_FAINT};margin-bottom:9px;font-weight:600}}
    .prow{{display:flex;align-items:baseline;gap:9px}}
    .pbig{{font-family:{theme.FONT_MONO};font-size:34px;font-weight:700;line-height:1;font-variant-numeric:tabular-nums}}
    .pccy{{font-size:13px;color:{_FAINT}}}
    .pchg{{display:flex;align-items:center;gap:10px;margin-top:10px;font-family:{theme.FONT_MONO};font-size:14px}}
    .chip{{font-family:{theme.FONT_MONO};font-size:13px;font-weight:700;padding:2px 8px;border-radius:3px}}
    .ohlc{{display:flex;flex-direction:column;gap:8px}}
    .ohlc>div{{display:flex;justify-content:space-between;font-family:{theme.FONT_MONO};font-size:13px}}
    .ohlc span{{color:{_MUTE};font-family:{theme.FONT_STACK}}}
    .ohlc b{{font-weight:600;font-variant-numeric:tabular-nums}}
    .pgrid{{display:grid;grid-template-columns:1fr 1fr;gap:14px}}
    .st .stl{{font-family:{theme.FONT_MONO};font-size:9.5px;letter-spacing:.12em;text-transform:uppercase;color:{_FAINT};margin-bottom:5px}}
    .st .stv{{font-family:{theme.FONT_MONO};font-size:16px;font-weight:600;font-variant-numeric:tabular-nums}}
    @media (max-width:760px){{.body{{grid-template-columns:1fr}}}}
    """

    chart_js = """
    mountEChart('kc', function(){
      function fmt(x){return Number(x).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});}
      var legendData=['MA5','MA10','MA20'];
      var series=[];
      // 板块基准折进 K 线:已 rebase 到本股价格 → 同价格轴灰虚线,蜡烛在它上方=跑赢。
      // 先 push(z 低)→ 落在蜡烛/MA 之下,不抢价格信号。
      if(D.bench){
        legendData.push(D.benchName);
        series.push({name:D.benchName,type:'line',data:D.bench,xAxisIndex:0,yAxisIndex:0,
          smooth:false,symbol:'none',connectNulls:true,z:1,
          lineStyle:{width:1.5,color:D.FAINT,type:'dashed',opacity:0.95}});
      }
      series.push(
        {name:'日K',type:'candlestick',data:D.kline,xAxisIndex:0,yAxisIndex:0,z:3,
          itemStyle:{color:D.UP,color0:D.DOWN,borderColor:D.UP,borderColor0:D.DOWN}},
        {name:'MA5',type:'line',data:D.ma5,xAxisIndex:0,yAxisIndex:0,smooth:true,symbol:'none',lineStyle:{width:1.3,color:D.MA5C}},
        {name:'MA10',type:'line',data:D.ma10,xAxisIndex:0,yAxisIndex:0,smooth:true,symbol:'none',lineStyle:{width:1.3,color:D.MA10C}},
        {name:'MA20',type:'line',data:D.ma20,xAxisIndex:0,yAxisIndex:0,smooth:true,symbol:'none',lineStyle:{width:1.3,color:D.MA20C}},
        {name:'Vol',type:'bar',xAxisIndex:1,yAxisIndex:1,
          data:D.vol.map(function(v,i){return {value:v,itemStyle:{color:D.volUp[i]?'rgba(13,118,128,.45)':'rgba(204,0,0,.4)'}};})});
      return {
        backgroundColor:'transparent', animation:true, animationDuration:680, animationEasing:'cubicOut',
        legend:{top:6,left:12,data:legendData,
          textStyle:{color:D.MUTE,fontFamily:D.MONO,fontSize:11},itemWidth:14,itemHeight:3,itemGap:15},
        tooltip:{trigger:'axis',axisPointer:{type:'cross',lineStyle:{color:'#4a4f5a',type:'dashed'}},
          backgroundColor:D.INK,borderColor:D.INK,borderWidth:1,
          textStyle:{color:D.PAPER,fontFamily:D.MONO,fontSize:12},padding:[9,13],
          formatter:function(ps){var k=ps.find(function(p){return p.seriesName==='日K';});
            if(!k){return '';}var v=k.data;
            var html='<div style="font-size:11px;color:'+D.MUTE+';margin-bottom:5px">'+k.name+'</div>'
              +'<div>开 <b>'+fmt(v[1])+'</b></div><div>收 <b>'+fmt(v[2])+'</b></div>'
              +'<div>低 <b>'+fmt(v[3])+'</b></div><div>高 <b>'+fmt(v[4])+'</b></div>';
            if(D.bench){var b=ps.find(function(p){return p.seriesName===D.benchName;});
              if(b&&b.data!=null){html+='<div style="margin-top:5px;color:'+D.FAINT+'">'+D.benchName
                +' <b>'+fmt(b.data)+'</b></div>';}}
            return html;}},
        axisPointer:{link:[{xAxisIndex:'all'}],label:{backgroundColor:D.EDGE}},
        grid:[{left:14,right:58,top:40,height:'62%'},{left:14,right:58,top:'74%',height:'15%'}],
        xAxis:[
          {type:'category',data:D.dates,gridIndex:0,boundaryGap:true,
            axisLine:{lineStyle:{color:D.EDGE}},axisTick:{show:false},
            axisLabel:{color:D.FAINT,fontFamily:D.MONO,fontSize:10},splitLine:{show:false}},
          {type:'category',data:D.dates,gridIndex:1,boundaryGap:true,
            axisLine:{lineStyle:{color:D.EDGE}},axisTick:{show:false},axisLabel:{show:false}}],
        yAxis:[
          {scale:true,gridIndex:0,position:'right',axisLine:{show:false},
            axisLabel:{color:D.FAINT,fontFamily:D.MONO,fontSize:10},splitLine:{lineStyle:{color:D.GRID}}},
          {scale:true,gridIndex:1,position:'right',axisLabel:{show:false},
            axisLine:{show:false},splitLine:{show:false}}],
        dataZoom:[
          {type:'inside',xAxisIndex:[0,1],start:Math.max(0,100-100*120/D.n),end:100},
          {type:'slider',xAxisIndex:[0,1],bottom:4,height:15,start:Math.max(0,100-100*120/D.n),end:100,
            borderColor:D.EDGE,fillerColor:'rgba(13,118,128,.10)',handleStyle:{color:D.UP},
            textStyle:{color:D.FAINT,fontSize:9},dataBackground:{lineStyle:{color:D.EDGE},areaStyle:{color:D.GRID}}}],
        series:series
      };
    });
    """

    head_name = f'<span class="nm">{name}</span>' if name and name != ticker else ""
    thead = (
        '<div class="thead"><div class="tk">'
        f'<span class="tick"></span><span class="code">{ticker}</span>{head_name}'
        f'<span class="ex">{exch}</span></div>'
        f'<div class="tmeta">{meta}<br>{src}</div></div>'
    ) if show_header else ""
    doc = (
        '<!doctype html><html><head><meta charset="utf-8">'
        f'<style>{css}</style></head><body><div class="glow"></div><div class="term">'
        f'{thead}'
        '<div class="body">'
        '<div class="chartcard"><div id="kc"></div></div>'
        f'{panel}</div></div>'
        f'<script>var D={json.dumps(payload)};</script>'
        f'<script src="{ECHARTS_SRC}"></script>'
        f'<script>{echarts_boot.MOUNT_JS}</script>'
        f'<script>{chart_js}</script>'
        '</body></html>'
    )
    st.iframe(doc, height=(height if show_header else chart_h + 30))
    return True


# ── 内联 K 线弹窗(点 ticker 看 K 线,不离开本页)──────────────────────────────
# 热力图/表格里的股票 → 选代码 → st.dialog 模态弹出 cream 终端,页面不跳转。
# (热力图瓦片在 sandbox iframe 里,瓦片点击无法直接触发 Streamlit rerun —— 需重型双向
#  自定义组件;此 picker→modal 路径轻量可靠,达成「inline K 线、不进新页」同效。)

def _ccy_of(ticker: str) -> str:
    if ticker.endswith(".HK"):
        return "HKD"
    if ticker.endswith((".SS", ".SZ")):
        return "CNY"
    if ticker.endswith(".T"):
        return "JPY"
    if ticker.endswith((".KS", ".KQ")):
        return "KRW"
    return "USD"


@st.dialog("个股 K 线 · K-line", width="large")
def _kline_modal(ticker: str, name: str, ccy: str, prefer_cn: bool) -> None:
    with st.spinner("加载行情…" if prefer_cn else "Loading…"):
        df = fetch_ohlcv(ticker)
    if df is None or df.empty or len(df) < 5:
        st.warning(("暂无 OHLCV 数据(yfinance 未返回 " + ticker + ")")
                   if prefer_cn else f"No OHLCV data for {ticker}")
        return
    render(ticker=ticker, name=name, df=df, ccy=ccy, prefer_cn=prefer_cn, height=520)


def kline_picker(tickers, name_map: dict, *, prefer_cn: bool, key: str,
                 ccy_of=None) -> None:
    """「看个股 K 线」入口:选代码 → 弹窗 cream 终端(不跳页)。
    tickers: 可选代码列表;name_map: {ticker: 显示名};ccy_of: ticker→货币(默认按后缀)。
    弹窗仅在选择**变化**时打开 —— 关闭后不会因 rerun 反复弹。"""
    tickers = [t for t in (tickers or []) if t]
    if not tickers:
        return
    ccy_of = ccy_of or _ccy_of
    opts = [""] + list(dict.fromkeys(tickers))

    def _fmt(t: str) -> str:
        if not t:
            return "— 选代码看 K 线 —" if prefer_cn else "— pick a ticker —"
        nm = name_map.get(t, t)
        return f"{nm} · {t}" if nm and nm != t else t

    pick = st.selectbox(
        ("看个股 K 线 · 弹窗(不离开本页)" if prefer_cn else "View K-line · modal (stay on page)"),
        opts, index=0, format_func=_fmt, key=key,
    )
    last = f"{key}__last"
    if pick and st.session_state.get(last) != pick:
        st.session_state[last] = pick
        _kline_modal(pick, name_map.get(pick, pick), ccy_of(pick), prefer_cn)
    elif not pick:
        st.session_state[last] = ""
