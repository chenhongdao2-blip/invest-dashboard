"""个股行情终端 · FT-salmon glass K 线 — lib/candlestick_terminal.py
====================================================================

FT-salmon glass 设计语言(K线行情.dc.html 1:1 契约 2026-07-03):
  涨跌色   — 涨 teal #0d7680(UP) / 跌 CMSI_RED #c8102e (CONTRACT O1 page-scope)
  MA 配色  — MA5 #e0963c / MA10 INK_4 #b8b1a8 / MA20 INK #1a1a1a
  字体     — Space Grotesk(FONT_DISPLAY) 正文; JetBrains Mono 数字/chip
  玻璃卡   — rgba(255,255,255,.55) + blur(14px), border-top 3px INK, 无 box-shadow
  数据     — 真实 EOD OHLCV(yfinance auto_adjust), 非 mock, 无 LIVE tick
  静态资源 — 相对路径 NO 前导 /: 云端 /~/+/ 前缀下 load ✓

调用:
    from lib import candlestick_terminal as cterm
    df = cterm.fetch_ohlcv(ticker)
    cterm.render(ticker=ticker, name=name, df=df, ccy=ccy,
                 prefer_cn=(lang=='zh'), as_of=latest, pe=fwd_pe)
"""
from __future__ import annotations

import json
from datetime import date, timedelta

import pandas as pd
import streamlit as st

from lib import theme
from lib import echarts_boot

# 相对路径 NO 前导 /: Streamlit Cloud /~/+/ 前缀兼容
# (绝对 /app/static/ 会丢前缀 → login 重定向 → echarts undefined → 全站空图)
ECHARTS_SRC = "app/static/echarts.min.js"

# ── 终端调色板 ─────────────────────────────────────────────────────────────
# CONTRACT O1: 跌色用 CMSI_RED(page-scope 豁免); theme.DOWN(#cc0000)全局不变。
_UP   = theme.UP        # 涨 teal #0d7680
_DOWN = theme.CMSI_RED  # 跌 #c8102e — CONTRACT O1 page-scope exemption; theme.DOWN untouched globally

# MA 线 cream 底克制色(避开涨跌/品牌色撞)
_MA5  = "#e0963c"     # 暖金
_MA10 = theme.INK_4  # #b8b1a8 淡灰
_MA20 = theme.INK    # #1a1a1a 近黑

# ── 交易所时段映射 (CONTRACT O3) ─────────────────────────────────────────
_EXCH_META: dict[str, tuple[str, str]] = {
    ".HK": ("HKEX",     "09:30–12:00 / 13:00–16:00 HKT"),
    ".SS": ("SSE",      "09:30–11:30 / 13:00–15:00 CST"),
    ".SZ": ("SZSE",     "09:30–11:30 / 13:00–15:00 CST"),
    ".T":  ("TSE",      "09:00–11:30 / 12:30–15:30 JST"),
    ".KS": ("KRX",      "09:00–15:30 KST"),
    ".KQ": ("KOSDAQ",   "09:00–15:30 KST"),
}
_EXCH_DEFAULT: tuple[str, str] = ("NYSE/NASDAQ", "09:30–16:00 ET")


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_ohlcv(ticker: str, lookback_days: int = 400) -> pd.DataFrame:
    """单 ticker 真实 OHLCV(yfinance, auto_adjust, cached 1h)。
    失败/空 → 空 DataFrame(上层 fallback)。"""
    import yfinance as yf

    start = (date.today() - timedelta(days=lookback_days)).isoformat()
    end   = (date.today() + timedelta(days=1)).isoformat()
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
           prefer_cn: bool, as_of: str | None = None, height: int = 560,
           pe: float | None = None, shares_out: float | None = None,
           show_header: bool = True) -> bool:
    """渲染 FT-salmon glass K 线终端。成功 True, 数据不足 False(上层回退)。

    pe          — 市盈率(NTM/TTM); 传入则在指标格显示。
    shares_out  — 流通股数(股单位); 传入则计算换手率显示。
    show_header — 顶部代码+名称+交易所+EOD 状态头。弹窗 True, 页面嵌入 False。
    """
    if df is None or df.empty or len(df) < 5:
        return False

    o, h, l, c = df["Open"], df["High"], df["Low"], df["Close"]
    dates = [d.strftime("%m/%d") for d in df.index]
    kline = [[round(float(o.iloc[i]), 2), round(float(c.iloc[i]), 2),
              round(float(l.iloc[i]), 2), round(float(h.iloc[i]), 2)]
             for i in range(len(df))]
    if "Volume" in df.columns:
        vol = [0 if pd.isna(v) else int(v) for v in df["Volume"]]
    else:
        vol = [0] * len(df)
    vol_up = [bool(kline[i][1] >= kline[i][0]) for i in range(len(df))]

    last   = float(c.iloc[-1])
    prev   = float(c.iloc[-2]) if len(c) > 1 else last
    chg    = last - prev
    chgpct = (chg / prev * 100) if prev else 0.0
    up     = chg >= 0
    col    = _UP if up else _DOWN
    last_o = float(o.iloc[-1])
    last_h = float(h.iloc[-1])
    last_l = float(l.iloc[-1])
    ampl   = ((last_h - last_l) / prev * 100) if prev else 0.0
    as_of_str = as_of or df.index[-1].strftime("%Y-%m-%d")

    # 交易所 meta (CONTRACT O3)
    exch_sfx = next((s for s in _EXCH_META if ticker.endswith(s)), None)
    exch_name, exch_hours = _EXCH_META.get(exch_sfx, _EXCH_DEFAULT)  # type: ignore[arg-type]

    # 涨跌 rgb 分量(chip 背景用)
    rgb = "13,118,128" if up else "200,16,46"

    chg_chip = (f'<span class="chip" style="color:{col};background:rgba({rgb},.12)">'
                f'{"+" if up else ""}{chgpct:.2f}%</span>')

    # ── 只显示可用指标 (T8 only-available — 无 hardcoded demo 值) ─────────
    metrics_cells: list[tuple[str, str]] = []
    # 振幅: 始终显示
    metrics_cells.append(("振幅" if prefer_cn else "AMPL", f"{ampl:.2f}%"))
    # 量比(5日): 需有成交量且历史足够
    if vol and len(vol) >= 6 and vol[-1] > 0:
        avg5 = sum(vol[-6:-1]) / 5
        if avg5 > 0:
            metrics_cells.append(
                ("量比(5日)" if prefer_cn else "VOL/5D", f"{vol[-1] / avg5:.2f}x")
            )
    # 换手率: 仅当 shares_out 传入
    if shares_out and shares_out > 0 and vol and vol[-1] > 0:
        metrics_cells.append(
            ("换手率" if prefer_cn else "TURNOVER",
             f"{vol[-1] / shares_out * 100:.2f}%")
        )
    # PE: 仅当 pe 传入
    if pe is not None:
        metrics_cells.append(("市盈率" if prefer_cn else "P/E", f"{pe:.1f}x"))

    if len(metrics_cells) >= 2:
        if len(metrics_cells) >= 3:
            pg = 'style="display:grid;grid-template-columns:repeat(2,1fr);gap:14px"'
        else:
            pg = 'style="display:flex;gap:20px"'
        metrics_html = (
            f'<div class="pcard" {pg}>'
            + "".join(
                f'<div class="st"><div class="stl">{lbl}</div>'
                f'<div class="stv">{val}</div></div>'
                for lbl, val in metrics_cells
            )
            + "</div>"
        )
    else:
        metrics_html = ""

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
        '<div class="ohlc">'
        f'<div><span>{"开" if prefer_cn else "O"}</span><b>{_fmt(last_o)}</b></div>'
        f'<div><span>{"高" if prefer_cn else "H"}</span>'
        f'<b style="color:{_UP}">{_fmt(last_h)}</b></div>'
        f'<div><span>{"低" if prefer_cn else "L"}</span>'
        f'<b style="color:{_DOWN}">{_fmt(last_l)}</b></div>'
        f'<div><span>{"收" if prefer_cn else "C"}</span><b>{_fmt(last)}</b></div>'
        '</div></div>'
        + metrics_html
        + '</div>'
    )

    # ── ECharts data payload ──────────────────────────────────────────────
    payload = {
        "dates": dates, "kline": kline, "vol": vol, "volUp": vol_up,
        "ma5": _ma(c, 5), "ma10": _ma(c, 10), "ma20": _ma(c, 20),
        "UP":   _UP,  "DOWN":  _DOWN,
        "INK":  theme.INK,   "FAINT": theme.INK_3, "INK4": theme.INK_4,
        "EDGE": theme.PAPER_EDGE, "GRID": theme.PAPER_RULE,
        "MA5C": _MA5, "MA10C": _MA10, "MA20C": _MA20,
        "MONO": theme.FONT_MONO,
        "n": len(df),
    }

    # ── CSS ──────────────────────────────────────────────────────────────
    chart_h  = (height - 120) if show_header else (height - 56)
    iframe_h = (height + 92)  if show_header else (height + 26)
    _tpad    = "14px 16px 12px" if show_header else "6px 16px 10px"

    css = f"""\
{theme.FONT_FACE_CSS}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{height:100%;background:{theme.PAPER};color:{theme.INK};
  font-family:{theme.FONT_DISPLAY};font-feature-settings:'tnum','ss01';
  -webkit-font-smoothing:antialiased;color-scheme:light}}
body{{position:relative;overflow:hidden}}
.glow{{position:absolute;inset:0;z-index:0;pointer-events:none;
  background:
    radial-gradient(820px 480px at 8% -10%,rgba(200,16,46,.08),transparent 60%),
    radial-gradient(760px 480px at 96% 4%,rgba(13,118,128,.10),transparent 60%)}}
.term{{position:relative;z-index:1;padding:{_tpad};display:flex;flex-direction:column;height:100%}}
.body{{display:grid;grid-template-columns:1fr 340px;gap:26px;flex:1;min-height:0;align-items:stretch}}
.chartcard{{background:rgba(255,255,255,.55);-webkit-backdrop-filter:blur(14px);
  backdrop-filter:blur(14px);border:1px solid rgba(255,255,255,.7);
  border-top:3px solid {theme.INK};border-radius:0;padding:8px;min-width:0}}
#kc{{width:100%;height:{chart_h}px}}
.side{{display:flex;flex-direction:column;gap:12px}}
.pcard{{background:rgba(255,255,255,.55);-webkit-backdrop-filter:blur(14px);
  backdrop-filter:blur(14px);border:1px solid rgba(255,255,255,.7);
  border-top:3px solid {theme.INK};border-radius:0;padding:18px 20px}}
.plbl{{font-family:{theme.FONT_MONO};font-size:10px;letter-spacing:.1em;
  text-transform:uppercase;color:{theme.INK_3};margin-bottom:9px;font-weight:600}}
.prow{{display:flex;align-items:baseline;gap:9px}}
.pbig{{font-family:{theme.FONT_MONO};font-size:46px;font-weight:700;line-height:1;
  font-variant-numeric:tabular-nums}}
.pccy{{font-size:13px;color:{theme.INK_3}}}
.pchg{{display:flex;align-items:center;gap:10px;margin-top:10px;
  font-family:{theme.FONT_MONO};font-size:14px}}
.chip{{font-family:{theme.FONT_MONO};font-size:13px;font-weight:700;
  padding:2px 8px;border-radius:3px}}
.ohlc{{display:flex;flex-direction:column;gap:8px}}
.ohlc>div{{display:flex;justify-content:space-between;font-family:{theme.FONT_MONO};font-size:13px}}
.ohlc span{{color:{theme.INK_2};font-family:{theme.FONT_DISPLAY}}}
.ohlc b{{font-weight:600;font-variant-numeric:tabular-nums}}
.st .stl{{font-family:{theme.FONT_MONO};font-size:9.5px;letter-spacing:.12em;
  text-transform:uppercase;color:{theme.INK_3};margin-bottom:5px}}
.st .stv{{font-family:{theme.FONT_MONO};font-size:15px;font-weight:600;
  font-variant-numeric:tabular-nums;color:{theme.INK}}}
.fnote{{font-family:{theme.FONT_MONO};font-size:10.5px;color:{theme.INK_3};
  letter-spacing:.02em;margin-top:10px;flex-shrink:0}}
@keyframes pulse{{0%,100%{{opacity:1;transform:scale(1)}}50%{{opacity:.35;transform:scale(.82)}}}}
@media (max-width:760px){{.body{{grid-template-columns:1fr}}}}
"""

    # ── 头部 HTML (show_header=True → 弹窗模式) ───────────────────────────
    if show_header:
        name_span = (
            f'<span style="font-family:{theme.FONT_DISPLAY};font-size:30px;'
            f'font-weight:700;color:{theme.INK};letter-spacing:-.01em">'
            f'{name}</span>'
        ) if name and name != ticker else ""
        thead_html = (
            f'<div style="display:flex;align-items:flex-start;'
            f'justify-content:space-between;margin-bottom:14px">'
            f'<div>'
            f'<div style="display:flex;align-items:center;gap:12px">'
            f'<span style="width:5px;height:44px;background:{theme.CMSI_RED};'
            f'display:inline-block;flex-shrink:0"></span>'
            f'{name_span}'
            f'<span style="font-family:{theme.FONT_MONO};font-size:13px;'
            f'color:{theme.INK_2};border:1px solid {theme.PAPER_EDGE_SOFT};'
            f'border-radius:3px;padding:3px 9px;align-self:center">{ticker}</span>'
            f'</div>'
            f'<div style="font-size:12px;color:{theme.INK_3};margin-top:7px;'
            f'margin-left:17px;font-family:{theme.FONT_MONO};letter-spacing:.02em">'
            f'{exch_name}&nbsp;·&nbsp;{exch_hours}</div>'
            f'</div>'
            f'<div style="display:flex;align-items:center;gap:7px;padding-top:8px">'
            f'<span style="width:7px;height:7px;border-radius:50%;'
            f'background:{_UP};display:inline-block;'
            f'animation:pulse 1.8s ease-in-out infinite"></span>'
            f'<span style="font-family:{theme.FONT_MONO};font-size:11px;'
            f'color:{theme.INK_3};letter-spacing:.04em">'
            f'EOD 数据&nbsp;·&nbsp;截至 {as_of_str}</span>'
            f'</div></div>'
        )
    else:
        thead_html = ""

    # ── ECharts option JS ─────────────────────────────────────────────────
    chart_js = """
mountEChart('kc', function(){
  function fmt(x){
    return Number(x).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
  }
  var series=[
    {name:'日K',type:'candlestick',data:D.kline,xAxisIndex:0,yAxisIndex:0,z:3,
      itemStyle:{color:D.UP,color0:D.DOWN,borderColor:D.UP,borderColor0:D.DOWN}},
    {name:'MA5',type:'line',data:D.ma5,xAxisIndex:0,yAxisIndex:0,
      smooth:true,symbol:'none',lineStyle:{width:1,color:D.MA5C}},
    {name:'MA10',type:'line',data:D.ma10,xAxisIndex:0,yAxisIndex:0,
      smooth:true,symbol:'none',lineStyle:{width:1,color:D.MA10C}},
    {name:'MA20',type:'line',data:D.ma20,xAxisIndex:0,yAxisIndex:0,
      smooth:true,symbol:'none',lineStyle:{width:1,color:D.MA20C}},
    {name:'Vol',type:'bar',xAxisIndex:1,yAxisIndex:1,
      data:D.vol.map(function(v,i){
        return {value:v,itemStyle:{color:D.volUp[i]?'rgba(13,118,128,.5)':'rgba(200,16,46,.5)'}};
      })}
  ];
  return {
    backgroundColor:'transparent',
    animation:true,animationDuration:680,animationEasing:'cubicOut',
    legend:{
      top:6,left:12,data:['MA5','MA10','MA20'],
      textStyle:{color:D.FAINT,fontFamily:D.MONO,fontSize:11},
      itemWidth:14,itemHeight:3,itemGap:15
    },
    tooltip:{
      trigger:'axis',
      axisPointer:{type:'cross',lineStyle:{color:D.INK4,type:'dashed'}},
      backgroundColor:D.INK,borderColor:D.INK,borderWidth:1,
      textStyle:{color:'#fff1e5',fontFamily:D.MONO,fontSize:12},
      padding:[9,13],
      formatter:function(ps){
        var k=ps.find(function(p){return p.seriesName==='日K';});
        if(!k){return '';}
        var v=k.data;
        return '<div style="font-size:11px;color:'+D.FAINT+';margin-bottom:5px">'+k.name+'</div>'
          +'<div>开 <b>'+fmt(v[1])+'</b></div>'
          +'<div>收 <b>'+fmt(v[2])+'</b></div>'
          +'<div>低 <b>'+fmt(v[3])+'</b></div>'
          +'<div>高 <b>'+fmt(v[4])+'</b></div>';
      }
    },
    axisPointer:{link:[{xAxisIndex:'all'}],label:{backgroundColor:D.EDGE}},
    grid:[
      {left:14,right:58,top:'7.9%',height:'57.1%'},
      {left:14,right:58,top:'71.4%',height:'19.6%'}
    ],
    xAxis:[
      {type:'category',data:D.dates,gridIndex:0,boundaryGap:true,
        axisLine:{lineStyle:{color:D.EDGE}},axisTick:{show:false},
        axisLabel:{color:D.FAINT,fontFamily:D.MONO,fontSize:10},
        splitLine:{show:false}},
      {type:'category',data:D.dates,gridIndex:1,boundaryGap:true,
        axisLine:{lineStyle:{color:D.EDGE}},axisTick:{show:false},
        axisLabel:{show:false}}
    ],
    yAxis:[
      {scale:true,gridIndex:0,position:'right',axisLine:{show:false},
        axisLabel:{color:D.FAINT,fontFamily:D.MONO,fontSize:10},
        splitLine:{lineStyle:{color:D.GRID}}},
      {scale:true,gridIndex:1,position:'right',
        axisLabel:{show:false},axisLine:{show:false},splitLine:{show:false}}
    ],
    dataZoom:[
      {type:'inside',xAxisIndex:[0,1],start:Math.max(0,100-100*120/D.n),end:100},
      {type:'slider',xAxisIndex:[0,1],bottom:6,height:14,
        start:Math.max(0,100-100*120/D.n),end:100,
        borderColor:D.EDGE,fillerColor:'rgba(200,16,46,.12)',
        handleStyle:{color:'#c8102e'},
        textStyle:{color:D.FAINT,fontSize:9},
        dataBackground:{lineStyle:{color:D.EDGE},areaStyle:{color:D.GRID}}}
    ],
    series:series
  };
});
"""

    # ── 来源脚注 ──────────────────────────────────────────────────────────
    src_note = (
        f"来源: yfinance · 复权 OHLCV · {ticker} · 截至 {as_of_str}"
        if prefer_cn else
        f"Source: yfinance · adj. OHLCV · {ticker} · as of {as_of_str}"
    )

    # ── 组装 srcdoc ───────────────────────────────────────────────────────
    doc = (
        '<!doctype html><html><head><meta charset="utf-8">'
        f'<style>{css}</style></head><body>'
        '<div class="glow"></div>'
        '<div class="term">'
        + thead_html
        + '<div class="body">'
        '<div class="chartcard"><div id="kc"></div></div>'
        + panel
        + '</div>'
        f'<div class="fnote">{src_note}</div>'
        '</div>'
        f'<script>var D={json.dumps(payload)};</script>'
        f'<script src="{ECHARTS_SRC}"></script>'
        f'<script>{echarts_boot.MOUNT_JS}</script>'
        f'<script>{chart_js}</script>'
        '</body></html>'
    )
    st.iframe(doc, height=iframe_h)
    return True


# ── 内联 K 线弹窗 ─────────────────────────────────────────────────────────
# 热力图/表格里的股票 → 选代码 → st.dialog 弹出 glass 终端, 页面不跳转。

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
        st.warning(
            ("暂无 OHLCV 数据(yfinance 未返回 " + ticker + ")")
            if prefer_cn else f"No OHLCV data for {ticker}"
        )
        return
    render(ticker=ticker, name=name, df=df, ccy=ccy, prefer_cn=prefer_cn, height=480)


def kline_picker(tickers, name_map: dict, *, prefer_cn: bool, key: str,
                 ccy_of=None) -> None:
    """「看个股 K 线」入口: 选代码 → 弹窗 glass 终端(不跳页)。
    tickers: 可选代码列表; name_map: {ticker: 显示名}; ccy_of: ticker→货币(默认按后缀)。
    弹窗仅在选择变化时打开 — 关闭后不因 rerun 反复弹。"""
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
        ("看个股 K 线 · 弹窗(不离开本页)"
         if prefer_cn else "View K-line · modal (stay on page)"),
        opts, index=0, format_func=_fmt, key=key,
    )
    last = f"{key}__last"
    if pick and st.session_state.get(last) != pick:
        st.session_state[last] = pick
        _kline_modal(pick, name_map.get(pick, pick), ccy_of(pick), prefer_cn)
    elif not pick:
        st.session_state[last] = ""
