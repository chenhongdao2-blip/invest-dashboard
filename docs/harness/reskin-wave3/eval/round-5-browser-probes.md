# WAVE-3 ROUND-5 — C45 真机探针清单（browser_needed）

> Evaluator 无法直接执行：本会话中途第二个 Chrome 连入，`tabs_context_mcp` 报「none selected」，工具硬规则禁止 evaluator 自选浏览器（可能操作到错误用户的 Chrome）。以下探针交主循环/team-lead 执行（先 select_browser 选定 George 的实例），原始返回值回传给 Evaluator 裁决。判决权仍在 Evaluator。

## 前置
- URL：`localhost:8599/Strategy_Picks?lang=zh`，等 ~15s 重载完，**点末 tab「港股IPO打新」激活**（tab strip 第 4 个）。
- 窗口默认宽（≥1280）。
- IPO 排行表在该 tab 内的 srcdoc iframe，用 `iframe.contentDocument` 探。

## 探针 A — C45 核心（默认宽，逐 charted 行 hover）
```js
(() => {
  const ifr=[...document.querySelectorAll('iframe')].find(f=>{try{return f.contentDocument&&f.contentDocument.querySelector('.rank-table')&&f.getBoundingClientRect().height>100;}catch(e){return false;}});
  if(!ifr) return JSON.stringify({error:'IPO iframe not visible — activate 港股IPO打新 tab first'});
  const d=ifr.contentDocument;
  const rows=[...d.querySelectorAll('#rank-body tr')];
  const footer=d.querySelector('.footer'), dock=d.querySelector('.dock'), scroll=d.querySelector('.rank-scroll');
  const res=[]; let n=0;
  for(const r of rows){
    r.dispatchEvent(new MouseEvent('mouseenter'));
    const svg=d.querySelector('.dock-chart svg'); if(!svg) continue;
    const chartEl=svg.parentElement;
    const sr=svg.getBoundingClientRect(), cr=chartEl.getBoundingClientRect();
    const zt=[...svg.querySelectorAll('text')].find(t=>t.textContent.trim()==='0%');
    const zr=zt?zt.getBoundingClientRect():null;
    const cir=svg.querySelector('circle'); const cirR=cir?cir.getBoundingClientRect():null;
    res.push({
      code:r.children[1].textContent.trim(),
      svg_not_taller_than_cell: sr.height<=chartEl.clientHeight+2,      // C45 核心：不裁(高)
      svg_bottom_within_cell: sr.bottom<=cr.bottom+2,                    // C45 核心：不裁(底缘)
      zero_label_within_cell: zr? (zr.bottom<=cr.bottom+2 && zr.top>=cr.top-2):false, // 0% 完整可视
      endpoint_within_cell: cirR? (cirR.bottom<=cr.bottom+2):false,
      dock_bottom:Math.round(dock.getBoundingClientRect().bottom),
      footer_top:Math.round(footer.getBoundingClientRect().top)
    });
    if(++n>=5) break;
  }
  const dr=dock.getBoundingClientRect(), fr=footer.getBoundingClientRect(), scr=scroll.getBoundingClientRect();
  const df=d.querySelector('.dock-foot');
  return JSON.stringify({
    win:'DEFAULT', iframe_w:Math.round(ifr.getBoundingClientRect().width),
    per_row:res,
    all_no_clip: res.length>0 && res.every(x=>x.svg_not_taller_than_cell && x.svg_bottom_within_cell && x.zero_label_within_cell),
    C45_dock_le_footer: dr.bottom<=fr.top,
    dock_foot_text: df?df.textContent.slice(0,30):'NONE',
    dock_foot_visible: df? (df.getBoundingClientRect().height>0 && df.getBoundingClientRect().bottom<=dr.bottom+1):false,
    dock_fills_track: Math.abs(dr.height-scr.height)<40   // dock 与左表对称同高(撑满行轨)
  });
})()
```
**PASS 判据**：`all_no_clip:true`（svg 高≤cell、底缘≤cell、0% 标签完整落 cell）+ `C45_dock_le_footer:true` + `dock_foot_visible:true` + `dock_fills_track:true`。

## 探针 B — 窄宽模拟（探针级，非 resize_window）
> round-4 实测 resize_window 不改 rendered viewport（parent innerWidth 恒 1512）。改用侵入式：临时缩 iframe 元素宽，reflow 后重测，**测完必须恢复**。
```js
(() => {
  const ifr=[...document.querySelectorAll('iframe')].find(f=>{try{return f.contentDocument&&f.contentDocument.querySelector('.rank-table')&&f.getBoundingClientRect().height>100;}catch(e){return false;}});
  const orig=ifr.style.width; ifr.style.width='900px'; void ifr.offsetWidth;  // force reflow
  const d=ifr.contentDocument;
  const rows=[...d.querySelectorAll('#rank-body tr')];
  let out={sim:'iframe.style.width=900px'};
  for(const r of rows){ r.dispatchEvent(new MouseEvent('mouseenter')); const svg=d.querySelector('.dock-chart svg'); if(svg){ const ce=svg.parentElement; const sr=svg.getBoundingClientRect(), cr=ce.getBoundingClientRect(); const zt=[...svg.querySelectorAll('text')].find(t=>t.textContent.trim()==='0%'); const zr=zt?zt.getBoundingClientRect():null; out.code=r.children[1].textContent.trim(); out.narrow_svg_within_cell=sr.bottom<=cr.bottom+2; out.narrow_zero_visible=zr?(zr.bottom<=cr.bottom+2):false; const dock=d.querySelector('.dock'), footer=d.querySelector('.footer'); out.narrow_dock_le_footer=dock.getBoundingClientRect().bottom<=footer.getBoundingClientRect().top; break; } }
  ifr.style.width=orig; void ifr.offsetWidth;  // RESTORE
  return JSON.stringify(out);
})()
```
**PASS 判据**：`narrow_svg_within_cell:true` + `narrow_zero_visible:true` + `narrow_dock_le_footer:true`。局限：模拟只缩 iframe 元素宽，不完全等价真实 viewport 换行增高；但 meet 缩放物理不可裁 → 结构上任意宽度成立（见 round-5.md 结构论证）。

## 探针 C — 溅射面（C17 + sort + hover + console）
```js
(() => {
  const ifr=[...document.querySelectorAll('iframe')].find(f=>{try{return f.contentDocument&&f.contentDocument.querySelector('.rank-table')&&f.getBoundingClientRect().height>100;}catch(e){return false;}});
  const d=ifr.contentDocument; const rows=()=>[...d.querySelectorAll('#rank-body tr')];
  const clickTh=k=>d.querySelector(`th[data-key="${k}"]`).click(); const ind=k=>d.querySelector(`th[data-key="${k}"] .sort-ind`).textContent;
  const dockText=()=>d.querySelector('#dock-content').textContent.replace(/\s+/g,' ').trim();
  const out={};
  clickTh('d1_pct'); let L=rows().filter(r=>r.children[0].textContent.trim()!=='—');
  out.sort_ind=ind('d1_pct'); out.sort_first=L[0].children[7].textContent.trim();
  const a=rows()[2],b=rows()[9]; a.dispatchEvent(new MouseEvent('mouseenter')); out.hoverA=dockText().includes(a.children[2].textContent.trim());
  b.dispatchEvent(new MouseEvent('mouseenter')); out.hoverB=dockText().includes(b.children[2].textContent.trim());
  const sc=d.querySelector('.rank-scroll'); sc.scrollTop=sc.scrollHeight; const last=rows()[rows().length-1]; last.dispatchEvent(new MouseEvent('mouseenter'));
  const dock=d.querySelector('.dock'), footer=d.querySelector('.footer');
  out.c17_dock_le_footer=dock.getBoundingClientRect().bottom<=footer.getBoundingClientRect().top;
  out.c17_last_has_dock=dockText().includes(last.children[2].textContent.trim());
  return JSON.stringify(out);
})()
```
+ `read_console_messages(onlyErrors:true, pattern:"error|Uncaught|not defined")` → 应零。

## George 眼验补充（team-lead task#2 视觉项）
- dock 撑满行轨后与左表对称双栏，**玻璃视觉正常、无诡异空洞/大片留白**。
- charted 行图表：折线 + 终点圆点 + 0% 基准线标签完整，无被裁、无 meet letterbox 导致的过窄/畸形。
