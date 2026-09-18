export default function(component) {
  const { data, setTriggerValue, setStateValue, parentElement } = component;
  // Streamlit may remount this renderer on rerun; retain one view node.
  const mounts = [...parentElement.querySelectorAll('[data-trust-board-host]')];
  const host = mounts[0] || document.createElement('div');
  host.dataset.trustBoardHost = '1';
  mounts.slice(1).forEach(node => node.remove());
  if (!host.isConnected) parentElement.appendChild(host);
  const e = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const num = (v,d=2) => Number.isFinite(v) ? v.toLocaleString('zh-CN',{minimumFractionDigits:d,maximumFractionDigits:d}) : '—';
  const money = v => Number.isFinite(v) ? Math.abs(v)>=1e8 ? num(v/1e8)+'亿' : Math.abs(v)>=1e4 ? num(v/1e4)+'万' : num(v) : '资料待补';
  const percent = v => Number.isFinite(v) ? num(v,2)+'%' : '待核';
  const ret = v => Number.isFinite(v) ? (v>0?'+':'')+num(v*100,2)+'%' : '待核';
  const safeLink = (url, label) => /^https:\/\//.test(url||'') ? `<a target="_blank" rel="noopener noreferrer" href="${e(url)}">${e(label)} ↗</a>` : /^evidence\/[A-Za-z0-9._-]+\.(pdf|html)(?:#(?:L[0-9]+|page=[0-9]+))?$/.test(url||'') ? `<button type="button" data-source="${e(url)}">${e(label)} ↗</button>` : '';
  const defaults = {view:'company', market:'HK', query:'', sort:'total', dir:-1, minS12:'', minTotal:'', status:'all', industry:'all', grade:'strong_medium', advanced:false, scroll:0, restoreScroll:false};
  let state = host.trustState || {...defaults,...(data.ui||{})};
  const persist = () => {host.trustState={...state};setStateValue('ui', state);};
  const marketByCode=Object.fromEntries(data.roster.companies.map(r=>[r.code,r.market]));
  const visible = () => {
    const rows = state.view === 'person' ? data.roster.people : data.roster.companies;
    const query = state.query.trim().toLowerCase();
    const filtered = rows.filter(r => {
      if(state.view==='company') {
        if(r.market!==state.market || (state.status!=='all'&&r.status!==state.status) || (state.industry!=='all'&&r.industry!==state.industry)) return false;
        if(state.minS12!=='' && (!Number.isFinite(r.s12_pct)||r.s12_pct<Number(state.minS12))) return false;
        if(state.minTotal!=='' && (!Number.isFinite(r.total_pct)||r.total_pct<Number(state.minTotal))) return false;
      } else {
        if(state.grade==='strong_medium' && !['strong','medium'].includes(r.residency_grade)) return false;
        if(state.market!=='all' && !(r.company_codes||[]).some(code=>marketByCode[code]===state.market)) return false;
      }
      return !query || [r.name,r.code,r.company,(r.company_codes||[]).join(' ')].join(' ').toLowerCase().includes(query);
    });
    const key = state.sort;
    if(key==='name') return filtered.sort((a,b)=>String(a.name||'').localeCompare(String(b.name||''),'zh-CN')*state.dir);
    const value=r=>state.view==='person'?key==='s3'?(() => {const parts=[r.s3_realized_cny,r.s3_exposure_cny].filter(Number.isFinite);return parts.length?parts.reduce((x,y)=>x+y,0):null;})():r[key+'_cny']:(key==='s12'?r.s12_pct:key==='ratio'?r.total_pct:key==='policy'?r.policy_return:r.total_cny);
    filtered.sort((a,b)=>{
      const va = value(a);
      const vb = value(b);
      const na=Number.isFinite(va), nb=Number.isFinite(vb);
      if(!na||!nb) return na&&!nb?-1:!na&&nb?1:String(a.code||a.name).localeCompare(String(b.code||b.name));
      return (va-vb)*state.dir;
    });
    return filtered;
  };
  const sourceList = sources => `<div class="source-list">${(sources||[]).map(s=>safeLink(s.url,s.title||'原文')).join('')}</div>`;
  const scenario = (node,field) => Number.isFinite(node?.[field]) ? money(node[field])+'元人民币' : '资料待补';
  const caseHtml = c => {
    const sp=c.scenario_profile||{}, p=c.period_evidence||{}, hist=c.s1_hist_rows||[];
    const dates=hist.map(r=>r.pay_date).filter(Boolean).sort();
    const start = p.trust_established_at ? `成立 ${e(p.trust_established_at)}` : p.first_disclosure?.date ? `最早披露 ${e(p.first_disclosure.date)}（非成立日）` : '信托成立日待核';
    const groups = {};
    hist.forEach(r=>{if(Number.isFinite(r.shares_used)&&Number.isFinite(r.dps)){let k=r.currency||'币种待核';groups[k]=(groups[k]||0)+r.shares_used*r.dps;}});
    const formula=Object.entries(groups).length?Object.entries(groups).map(([cur,base])=>{const fx=data.roster.fx?.[cur];return `${e(cur)}：Σ(分段股数×每股股息)＝${money(base)}${e(cur)}${Number.isFinite(fx)?` ×20% ×${num(fx,5)}＝${money(base*.2*fx)}元人民币`:'；汇率待核'}`;}).join('<br>'):['confirmed_no_dividend','confirmed_no_dividend_for_case_period'].includes(c.calculation_status)?'年报原文确认已核期间未派息；该股票现金股息税额为0':'本段无可算分红；持股期间或原文待核，缺失不填0';
    const link=safeLink(c.source_url,'年报／持股来源');
    const sale=sp.S1?.disposal_tax_cny;
    return `<section><h3>${e(c.trust||c.id)} · ${e(start)}</h3><p class="muted">${e(c.company_name||c.code)} · ${hist.length}笔已计现金股息${dates.length?` · ${e(dates[0])}—${e(dates.at(-1))}`:''}</p><div class="formula">${formula}<br>现金股息税额：${scenario(sp.S1,'dividend_amount_cny')}${Number.isFinite(sale)?`<br>股票减持：已核收入额×20%＝${money(sale)}元人民币`:''}<br>S1小计：${scenario(sp.S1,'amount_cny')}</div><div class="row"><span>S2 装入</span><b>${scenario(sp.S2,'amount_cny')}</b></div><div class="row"><span>S3 已发生</span><b>${scenario(sp.S3,'realized_tax_cny')}</b></div><div class="row"><span>S3 未来敞口</span><b>${scenario(sp.S3,'tax_stepped_up_cny')==='资料待补'?scenario(sp.S3,'tax_zero_cost_cny'):scenario(sp.S3,'tax_stepped_up_cny')}</b></div><p class="note">条件试算，非核定税单；未来敞口不是已发生税款。共有池不按人物重复分配。</p>${link}<details><summary>明细与依据</summary><p>股数：${e(c.shares==null?'待核':num(c.shares,0))}股。计算起点：${e(p.calculation_from||'待核')}。${e(c.coverage_note||'')}</p><p>未计入事项：${e((c.unverified_share_intervals||[]).length)}段待核；逐笔原文、冻结旧列与税务假设可在受保护导出中核对。</p></details></section>`;
  };
  const detail = () => {
    const detail=data.detail;
    if (!detail && data.document) {
      const content=data.document.mime==='application/pdf'?`<embed type="application/pdf" src="data:application/pdf;base64,${e(data.document.content)}" width="100%" height="560">`:`<pre>${e(new TextDecoder().decode(Uint8Array.from(atob(data.document.content),x=>x.charCodeAt(0))))}</pre>`;
      return `<div class="overlay" data-close-doc="1"></div><aside class="drawer" role="dialog" aria-modal="true" aria-label="研究来源"><div class="drawer-head"><h2>研究来源</h2><button type="button" data-close-doc="1" aria-label="关闭来源">关闭 ×</button></div><section>${content}</section></aside>`;
    }
    if(!detail)return '';
    const company=detail.company, person=detail.person, name=company?.name||person?.name||'研究详情';
    const cases=detail.cases||[];
    const research=detail.research_note||detail.research_notes?.['6862.HK'];
    const ms=research?.ms31||{}, cross=ms.independent_check||{};
    const reportedPct=Number(ms.proceeds_hkd)/Number(ms.implied_denominator_at_31pct_hkd)*100;
    const rHtml=research?`<section><h3>${e(research.title||'处置研究')}</h3><p>${e(research.transaction.event_date)}出售${money(research.transaction.sold_shares)}股，毛对价${money(research.summary.gross_cash_hkd)}港元。</p><p>已知历史税额情景${money(research.funding.assumed_historical_tax_cny)}元人民币；实际已缴金额与缴税用途未确认。</p><details><summary>卖方分红对比怎么算</summary><p>本次毛套现 ÷ ${e((research.associated_people||[]).join("、"))}自 IPO 以来累计分红，分母不是公司营收或单一股池收入；报告比例约${percent(reportedPct)}；逐年底稿${ms.original_workings_disclosed?'已披露':'未披露'}。按本次毛套现反推分母约${money(Number(ms.implied_denominator_at_31pct_hkd))}港元。</p><p>仅两池独立复算：按已支付日股息${percent(Number(cross.proceeds_over_paid_date_dividends_pct))}；若含已宣派未支付股息${percent(Number(cross.proceeds_over_including_sept_declared_pct))}。未付股息不视为已到账。</p>${safeLink(research.sources?.ms?.url,'卖方报告原文')}</details><details><summary>中外资观点 · 非税务认定</summary>${(research.broker_views||[]).map(v=>`<p><b>${e(v.broker)} · ${e(v.date)}</b><br>${e(v.view)}<br><small>${e(v.channel)}</small><br><button type="button" data-source="report:${e(v.id)}">核对报告／观点全文</button></p>`).join('')}</details><details><summary>来源与限制</summary>${sourceList(Object.values(research.sources||{}))}<p>专题价格截至${e(research.price_asof)}；主表行情以本次发布的价格截止日为准。卖出／不卖使用相同期末价，仅为算术桥，不作股价因果估计。</p></details></section>`:'';
    const body=company?`<p class="note">${e(company.code)} · ${e(company.market)} · 公司市值及收益只用已核日期。</p>${rHtml}${cases.map(caseHtml).join('')}`:
      `<p class="note">${e(person.company||'')} · 大陆居民证据：${e(person.residency_evidence?.grade||'待核')}</p><section><h3>三情形合计（含未来敞口）</h3><p>${scenario(person.scenario_profile,'combined_total_cny')}</p><p class="note">含已发生与未来情景，不是已缴或欠税金额。</p></section>${rHtml}${cases.map(caseHtml).join('')}`;
    const doc=data.document?`<section><h3>受保护来源</h3>${data.document.mime==='application/pdf'?`<embed type="application/pdf" src="data:application/pdf;base64,${e(data.document.content)}" width="100%" height="500">`:`<pre>${e(new TextDecoder().decode(Uint8Array.from(atob(data.document.content),x=>x.charCodeAt(0))))}</pre>`}</section>`:'';
    return `<div class="overlay" data-close="1"></div><aside class="drawer" role="dialog" aria-modal="true" aria-label="${e(name)}研究详情"><div class="drawer-head"><div><h2>${e(name)}</h2><small>持股起点 · 公式 · 来源 · 金额</small></div><button type="button" data-close="1" aria-label="关闭详情">关闭 ×</button></div>${body}${doc}</aside>`;
  };
  function render(){
    const rows=visible();
    const metrics=[['观察标的',data.roster.coverage.watch_securities,'只含已发现线索'],['股池',data.roster.coverage.pools,'唯一经济股池'],['人物',data.roster.coverage.people,'关联人物'],['有可算合计',`${data.roster.coverage.mainland_strong_medium_with_main_total}/${data.roster.coverage.mainland_strong_medium_people}`,'强／中证据；非资料齐全']];
    const headings=state.view==='company'?['公司 / 代码','合计（可算）','S1+S2 / 市值','S1+S2+S3 / 市值','政策以来']:['人物 / 公司','合计（可算）','S1 存续','S2 装入','S3 已发生 / 敞口'];
    const sortKeys=state.view==='company'?['name','total','s12','ratio','policy']:['name','combined_total','s1','s2','s3'];
    const industries=[...new Set(data.roster.companies.filter(r=>r.market===state.market).map(r=>r.industry).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'zh-CN'));
    host.innerHTML=`<div class="board"><header class="head"><div><h1>股东与信托</h1><p>先找对象，再看起点、算式与来源。</p></div><div class="asof">行情 ${e(data.roster.price_asof)}<br>模型 ${e(data.roster.model_built_at?.slice(0,10))}<br>扫描 ${e(data.roster.scan_asof?.slice(0,10))}</div></header><div class="coverage">${metrics.map(([l,v,n])=>`<div><small>${e(l)}</small><strong>${e(v)}</strong><span>${e(n)}</span></div>`).join('')}</div><div class="insights">${data.roster.insights.map(x=>`<article><small>${e(x.broker)} · ${e(x.date)}</small><p>${e(x.text)}</p>${x.source_id?`<button type="button" data-source="report:${e(x.source_id)}">查看来源 ↗</button>`:''}</article>`).join('')}</div><div class="tabs"><button type="button" data-view="company" class="${state.view==='company'?'active':''}">公司名单</button><button type="button" data-view="person" class="${state.view==='person'?'active':''}">按人算税</button></div><div class="tools"><select aria-label="市场" data-market>${(state.view==='person'?['all','HK','A','US']:['HK','A','US']).map(m=>`<option value="${m}" ${m===state.market?'selected':''}>${{all:'全部',HK:'港股',A:'A股',US:'中概'}[m]}</option>`).join('')}</select><input aria-label="搜索公司或人物" type="search" data-search value="${e(state.query)}" placeholder="搜索公司、代码或人物">${state.view==='person'?`<select aria-label="人物证据范围" data-grade><option value="strong_medium" ${state.grade==='strong_medium'?'selected':''}>大陆证据强／中</option><option value="all" ${state.grade==='all'?'selected':''}>全部人物</option></select>`:`<button data-advanced type="button">${state.advanced?'收起':'更多筛选'}</button>`}<button data-export type="button">导出完整数据</button></div>${state.advanced&&state.view==='company'?`<div class="advanced"><label>S1+S2占比下限 %<input type="number" min="0" step="any" data-mins12 value="${e(state.minS12)}"></label><label>总占比下限 %<input type="number" min="0" step="any" data-mintotal value="${e(state.minTotal)}"></label><label>行业<select data-industry><option value="all">全部行业</option>${industries.map(v=>`<option value="${e(v)}" ${state.industry===v?'selected':''}>${e(v)}</option>`).join('')}</select></label><label>资料状态<select data-status><option value="all">全部</option><option value="confirmed" ${state.status==='confirmed'?'selected':''}>已核关联</option><option value="partial" ${state.status==='partial'?'selected':''}>资料待补</option><option value="pending" ${state.status==='pending'?'selected':''}>待判</option></select></label></div>`:''}<p class="count">${rows.length}条 · 合计含未来敞口，非已发生税额；占比只含已纳入的可算部分</p><table class="tbl"><thead><tr>${headings.map((h,j)=>`<th><button type="button" data-sort="${sortKeys[j]}">${e(h)} ${state.sort===sortKeys[j]?(state.dir===-1?'↓':'↑'):''}</button></th>`).join('')}</tr></thead><tbody>${rows.length?rows.map(r=>state.view==='company'?`<tr data-select="company:${e(r.code)}" tabindex="0"><td>${e(r.name)}<span class="ticker">${e(r.code)}</span></td><td>${money(r.total_cny)}</td><td>${percent(r.s12_pct)}</td><td>${percent(r.total_pct)}</td><td class="${Number.isFinite(r.policy_return)?r.policy_return<0?'down':'up':'muted'}">${ret(r.policy_return)}</td></tr>`:`<tr data-select="person:${e(r.id)}" tabindex="0"><td>${e(r.name)}<span class="ticker">${e(r.company)}</span></td><td>${money(r.combined_total_cny)}</td><td>${money(r.s1_cny)}</td><td>${money(r.s2_cny)}</td><td>${money(r.s3_realized_cny)} / ${money(r.s3_exposure_cny)}</td></tr>`).join(''):`<tr><td colspan="5" class="empty">没有符合条件的记录；缺失不等于不存在。</td></tr>`}</tbody></table><div class="mobile-list">${rows.map(r=>`<button type="button" class="mobile-row" data-select="${state.view==='company'?'company:'+e(r.code):'person:'+e(r.id)}"><span>${e(r.name)}<small class="ticker">${e(r.code||r.company)}</small></span><strong>${money(state.view==='company'?r.total_cny:r.combined_total_cny)}</strong></button>`).join('')}</div><p class="note">${e(data.roster.disclaimer)} 完整计算明细在详情中。</p><details class="method"><summary>资料与口径</summary><p>先核持股载体与大陆居民证据，再按唯一经济股池计算。S1 分红和已核实卖股、S2 装入、S3 已发生及未来敞口分别展示；未确认期间与原文留作缺口，不用最新股数回推。合计为条件情景，不是税务机关核定或已缴金额。逐笔公告、年报、旧口径和排除原因见详情及受保护导出。</p></details></div>${detail()}`;
    const root=host;
    root.querySelectorAll('[data-view]').forEach(b=>b.onclick=()=>{state.view=b.dataset.view;state.sort=state.view==='company'?'total':'combined_total';state.market=state.view==='company'?'HK':'all';persist();if(data.detail)setTriggerValue('selected','');render();});
    root.querySelector('[data-market]').onchange=event=>{state.market=event.target.value;state.industry='all';persist();render();};
    root.querySelector('[data-search]').oninput=event=>{const pos=event.target.selectionStart;state.query=event.target.value;persist();render();const input=root.querySelector('[data-search]');input.focus();input.setSelectionRange(pos,pos);};
    const advancedButton=root.querySelector('[data-advanced]');if(advancedButton)advancedButton.onclick=()=>{state.advanced=!state.advanced;persist();render();};
    root.querySelectorAll('[data-sort]').forEach(b=>b.onclick=()=>{state.dir=state.sort===b.dataset.sort?-state.dir:-1;state.sort=b.dataset.sort;persist();render();});
    ['mins12','mintotal','industry','status','grade'].forEach(key=>{const input=root.querySelector('[data-'+key+']');if(input){const update=()=>{state[key==='mins12'?'minS12':key==='mintotal'?'minTotal':key]=input.value;persist();render();if(key==='mins12'||key==='mintotal')root.querySelector('[data-'+key+']')?.focus();};if(key==='mins12'||key==='mintotal')input.oninput=update;else input.onchange=update;}});
    root.querySelectorAll('[data-select]').forEach(node=>{const choose=()=>{state.scroll=window.scrollY;state.restoreScroll=false;persist();window.scrollTo(0,0);setTriggerValue('selected',node.dataset.select);};node.onclick=choose;node.onkeydown=event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();choose();}};});
    root.querySelectorAll('[data-close]').forEach(b=>b.onclick=()=>{state.restoreScroll=true;persist();setTriggerValue('selected','');});
    root.querySelectorAll('[data-close-doc]').forEach(b=>b.onclick=()=>setTriggerValue('source_request',''));
    root.querySelectorAll('[data-source]').forEach(b=>b.onclick=()=>setTriggerValue('source_request',b.dataset.source));
    root.querySelector('[data-export]').onclick=()=>setTriggerValue('export_request',String(Date.now()));
  }
  const onEscape=event=>{if(event.key==='Escape'&&data.detail)setTriggerValue('selected','');};
  document.addEventListener('keydown',onEscape);
  render();
  if (!data.detail && state.restoreScroll) {
    const scroll=state.scroll;
    state.restoreScroll=false;
    persist();
    requestAnimationFrame(()=>window.scrollTo(0,scroll));
  }
  if(data.export_blob && sessionStorage.getItem('trustExportNonce')!==data.export_blob.nonce){
    sessionStorage.setItem('trustExportNonce',data.export_blob.nonce);
    const raw=atob(data.export_blob.content);
    const bytes=Uint8Array.from(raw,c=>c.charCodeAt(0));
    const url=URL.createObjectURL(new Blob([bytes],{type:'text/csv;charset=utf-8'}));
    const a=document.createElement('a');a.href=url;a.download=data.export_blob.name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
    setTriggerValue('export_done',data.export_blob.nonce);
  }
  return ()=>document.removeEventListener('keydown',onEscape);
}
