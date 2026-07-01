"""Shared ECharts iframe bootstrap — lib/echarts_boot.py
=========================================================
根治「echarts.init 抢在容器 0 宽时执行 → canvas 永久空白」的 intermittent race。
诊断:/ccgg 三方(Claude + Codex + GLM)一致;契约:docs/harness/echarts-race/CONTRACT.md。

**问题**:st.iframe/srcdoc 里的 echarts,若在容器(flex/grid 列、隐藏 tab、iframe 尚未
分配宽度)`clientWidth===0` 时 `echarts.init`,canvas 会永久空白;后续即便容器变大,
没有 resize 触发也不会重画。旧代码只有 `typeof echarts==='undefined'` 的**库加载**守卫,
没有**容器就绪**守卫 —— 于是概率性空图(布局/字体/父容器算宽的那一帧输了 race)。

**统一修法** —— 所有 iframe echarts 组件在 echarts.min.js `<script>` 之后注入 MOUNT_JS,
把裸 `echarts.init(el); ch.setOption(...)` 换成:

    <script>{MOUNT_JS}</script>
    <script>
      mountEChart('kc', function(){ return { ...echarts option... }; });
    </script>

mountEChart(id, buildOption):
  1. requestAnimationFrame 轮询,等 `echarts` 已加载 + `el.clientWidth>0 && clientHeight>0` 再 init
     (上限 ~120 帧后转 setTimeout 兜底,防极端下死循环烧 CPU)。
  2. getInstanceByDom(el) || init(el)  —— 防同一 DOM 被重复 init(rerun/热重载)。
  3. ch.setOption(buildOption())。
  4. ResizeObserver(el) → 后续 flex 重排 / 切 tab / 断点变化时 ch.resize();
     无 ResizeObserver 的旧环境退回 window resize 监听。

不改任何 option 内容、涨跌色、自托管路径 —— 只换启动时序。
"""
from __future__ import annotations

# 纯 JS 函数定义字符串;注入各 echarts iframe 的 <script>。无 Python 占位,直接拼接。
MOUNT_JS = r"""
function mountEChart(id, buildOption){
  var el = document.getElementById(id);
  if(!el){ return; }
  var tries = 0;
  function ready(){
    return typeof echarts !== 'undefined'
      && el.clientWidth > 0 && el.clientHeight > 0;
  }
  function boot(){
    if(!ready()){
      return (++tries < 120) ? requestAnimationFrame(boot) : setTimeout(boot, 100);
    }
    var ch = echarts.getInstanceByDom(el) || echarts.init(el, null, {renderer:'canvas'});
    ch.setOption(buildOption());
    if(typeof ResizeObserver !== 'undefined'){
      // 复用/断开旧 observer:同一 DOM 上重复 mount 不叠加 RO(Codex 终审 caveat)。
      if(el.__echartsRO){ el.__echartsRO.disconnect(); }
      el.__echartsRO = new ResizeObserver(function(){
        if(el.clientWidth > 0 && el.clientHeight > 0){ ch.resize(); }
      });
      el.__echartsRO.observe(el);
    } else {
      window.addEventListener('resize', function(){ ch.resize(); });
    }
  }
  boot();
}
""".strip()
