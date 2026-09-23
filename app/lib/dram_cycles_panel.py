"""DRAM 周期一张图 → AI 总览页 iframe 卡片 — lib/dram_cycles_panel.py
====================================================================
单一真相 = ``docs/intelligence/2026-09-22-dram-cycles/dram-cycles.html``（claude.ai
artifact 源文件，无 html 壳）。本模块**不复制**图的任何数据或文案，只做三件事把它
装进 Streamlit：

1. 去掉 Google Fonts ``<link>``（国内被墙，见 memory selfhost-inter-fastfollow），
   改成自托管 Inter / JetBrains Mono 的 ``@font-face``，字体族名沿用源文件的
   IBM Plex Sans / Mono 以免改动源 CSS。
2. echarts.min.js 从 cdnjs 换成**相对路径** ``app/static/echarts.min.js``
   （云端 /~/+/ 前缀，绝对路径会撞 login → 全站空图，见 memory
   streamlit-cloud-static-path-prefix）。
3. 整段 IIFE 包进「容器就绪」守卫：等 ``echarts`` 已加载且 #chart 有宽度再执行，
   与 echarts_boot.MOUNT_JS 同一根治思路（0 宽 race → canvas 永久空白）。源文件
   里 ``var ch=echarts.init(el)`` 与后续代码同步耦合，不能拆成 mountEChart，所以
   守卫加在 IIFE 外层。

改图 → 只改 docs/intelligence 下的源文件；本模块无需动。
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SOURCE = REPO_ROOT / "docs" / "intelligence" / "2026-09-22-dram-cycles" / "dram-cycles.html"

_ECHARTS_SRC = "app/static/echarts.min.js"   # 相对路径，禁改绝对（云端丢前缀）
_CDN_ECHARTS = '<script src="https://cdnjs.cloudflare.com/ajax/libs/echarts/5.5.0/echarts.min.js"></script>'

_FONT_FACE = (
    "<style>"
    "@font-face{font-family:'IBM Plex Sans';font-style:normal;font-weight:100 900;font-display:swap;"
    "src:url('app/static/fonts/inter-var.woff2') format('woff2-variations');}"
    "@font-face{font-family:'IBM Plex Mono';font-style:normal;font-weight:100 800;font-display:swap;"
    "src:url('app/static/fonts/jetbrains-mono-var.woff2') format('woff2-variations');}"
    "</style>"
)

_BOOT_OPEN = "<script>\n(function(){"
_BOOT_CLOSE = "})();\n</script>"
_GUARD_OPEN = (
    "<script>\n"
    "function __dramMain(){"
)
_GUARD_CLOSE = (
    "}\n"
    "(function(){var tries=0;function ready(){var el=document.getElementById('chart');"
    "return typeof echarts!=='undefined'&&el&&el.clientWidth>0;}"
    "function tick(){if(ready()){__dramMain();return;}tries++;"
    "if(tries<120){requestAnimationFrame(tick);}else{setTimeout(tick,200);}}tick();})();\n"
    "</script>"
)


def _transform(src: str) -> str:
    # 1. fonts
    head, sep, tail = src.partition("<style>")
    lines = [ln for ln in head.split("\n") if "fonts.googleapis.com" not in ln]
    head = "\n".join(lines)
    src = head + _FONT_FACE + sep + tail
    # 2. echarts 自托管
    if _CDN_ECHARTS not in src:
        raise RuntimeError("dram-cycles.html: cdnjs echarts tag not found — source changed, update dram_cycles_panel")
    src = src.replace(_CDN_ECHARTS, f'<script src="{_ECHARTS_SRC}"></script>')
    # 3. 容器就绪守卫
    if src.count(_BOOT_OPEN) != 1 or src.count(_BOOT_CLOSE) != 1:
        raise RuntimeError("dram-cycles.html: IIFE boundary not found — source changed, update dram_cycles_panel")
    src = src.replace(_BOOT_OPEN, _GUARD_OPEN).replace(_BOOT_CLOSE, _GUARD_CLOSE)
    return src


@st.cache_data(show_spinner=False)
def build_doc(mtime: float) -> str:
    """完整 srcdoc（mtime 参与 cache key，改源文件即失效）。"""
    body = _transform(SOURCE.read_text(encoding="utf-8"))
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width'>"
        "<style>html,body{margin:0}</style></head><body>"
        f"{body}</body></html>"
    )


def render(height: int = 2600) -> None:
    if not SOURCE.exists():
        st.warning(f"DRAM 周期图源文件缺失：{SOURCE.relative_to(REPO_ROOT)}")
        return
    st.iframe(build_doc(SOURCE.stat().st_mtime), height=height)
