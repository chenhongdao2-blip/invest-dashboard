'use strict';

(() => {
  const $ = (id) => document.getElementById(id);
  const countryLabels = { US: '美国', KR: '韩国', JP: '日本', CN: '中国大陆', TW: '中国台湾', EU: '欧洲' };
  const statuses = { fact: '事实', plan: '披露计划', inference: '研究推断', unverified: '待核' };
  const relationLabels = { complement: '互补', conditional_substitute: '有条件替代', resource_competition: '资源竞争', enables: '使能' };
  const colors = ['#4a6fa5', '#a07a2c', '#8b3a62', '#c8102e', '#52725b', '#817795'];
  const relationColors = { enables: '#4a6fa5', complement: '#6f8068', conditional_substitute: '#a07a2c', resource_competition: '#8b3a62' };
  const proofLabels = { statement: '来源陈述，未独立验证', checked: '原始材料局部核对', method: '本项目方法', unclassified: '既有来源未单独标注' };
  const state = { history: {}, routes: {}, finance: {}, research: {}, entities: new Map(), sources: new Map(), era: null, country: 'all', historyKind: 'margin', selectedRoute: null, routeCompany: 'all', routeTheme: null, company: null, sourceQuery: '', sourcePage: 0, sourceCategory: 'all', sourceProof: 'all', scenarioSteps: {}, path: null, pathStep: 0, drawerEntity: null, previousFocus: null };
  const charts = {};
  let toastTimer;
  const array = (value) => Array.isArray(value) ? value : [];
  const listOf = (value) => Array.isArray(value) ? value : value ? [String(value)] : [];
  const text = (value) => value == null ? '' : String(value);
  const node = (tag, className, content) => { const n = document.createElement(tag); if (className) n.className = className; if (content != null) n.textContent = text(content); return n; };
  const button = (label, className, handler) => { const b = node('button', className, label); b.type = 'button'; if (handler) b.addEventListener('click', handler); return b; };
  const clear = (element) => { element.replaceChildren(); return element; };
  const statusTag = (value) => node('span', `status-tag ${statuses[value] ? value : 'unverified'}`, statuses[value] || '口径待核');
  const countryText = (list) => array(list).map((code) => countryLabels[code] || code).join(' · ');
  const unique = (list) => [...new Set(list)];
  const number = (value) => typeof value === 'number' && Number.isFinite(value) ? new Intl.NumberFormat('zh-CN', { maximumFractionDigits: 3 }).format(value) : '未取得';
  const dateText = (value) => value ? text(value) : '日期未取得';
  const eraEndLabel = (era) => Number.isInteger(era.end) ? text(era.end) : '进行中';
  const disclosureLabel = (row) => row.publishedAt ? `文件披露 ${row.publishedAt}` : row.documentDate ? `文件日期 ${row.documentDate} · 首次披露日未核` : '文件披露日期未取得';
  const durationLabels = { annual: '完整财年', nine_months_cumulative: '九个月累计', six_months_cumulative: '半年累计', half_year: '半年累计', quarter: '单季' };
  const entityFor = (id) => state.entities.get(id);
  const toast = (message) => { clearTimeout(toastTimer); $('toast').textContent = message; $('toast').hidden = false; toastTimer = setTimeout(() => { $('toast').hidden = true; }, 4200); };
  const safeLink = (url) => {
    if (!url || typeof url !== 'string') return null;
    try { const resolved = new URL(url, location.href); return ['http:', 'https:', 'file:'].includes(resolved.protocol) ? resolved.href : null; } catch { return null; }
  };
  function sourceLink(source) {
    const href = safeLink(source.url);
    if (!href) return node('span', '', source.title || source.id);
    const a = node('a', '', `${source.title || source.id} ↗`); a.href = href; a.target = '_blank'; a.rel = 'noopener noreferrer'; return a;
  }
  function sourceSummary(source) {
    const row = node('div', 'drawer-source'); row.append(sourceLink(source));
    row.append(node('p', '', `${dateText(source.date)} · ${source.kind || '来源类型未标注'} · ${source.id}`));
    if (source.locator) row.append(node('p', 'source-location', `定位：${source.locator}`));
    if (source.scope) row.append(node('p', '', `证明范围：${source.scope}`));
    if (source.family) row.append(node('p', '', `来源血缘：${source.family}；同源不重复计票。`));
    if (source.proofState) row.append(node('p', '', `证据状态：${proofLabels[source.proofState] || '未单独标注'}`));
    return row;
  }
  function appendSources(container, ids) {
    unique(array(ids)).forEach((id) => { const source = state.sources.get(id); container.append(source ? sourceSummary(source) : node('p', 'empty-note', `来源 ${id} 尚未载入`)); });
    if (!array(ids).length) container.append(node('p', 'empty-note', '暂无直接来源；保留为研究问题。'));
  }
  function showSources(ids, title = '来源与口径', notes = []) {
    openDrawer(); state.drawerEntity = null; $('drawer-kicker').textContent = 'SOURCEBOOK / EVIDENCE';
    $('detail-drawer').classList.remove('is-research-analysis');
    const body = clear($('drawer-body')); const head = node('div', 'drawer-header'); const h = node('h2', '', title); h.id = 'drawer-title'; head.append(h); body.append(head);
    array(notes).forEach((item) => head.append(node('p', '', item)));
    appendSources(body, ids); $('detail-drawer').scrollTop = 0;
  }
  function section(title, items, ordered = false) {
    const wrap = node('section', 'drawer-section'); wrap.append(node('h3', '', title));
    const entries = array(items).filter(Boolean);
    if (!entries.length) { wrap.append(node('p', 'empty-note', '当前材料未列明；后续补证。')); return wrap; }
    const list = node(ordered ? 'ol' : 'ul', ordered ? 'causal-chain' : ''); entries.forEach((item) => list.append(node('li', '', item))); wrap.append(list); return wrap;
  }
  function analysisTable(entity) {
    const spec = entity.analysisTable; if (!spec) return null;
    const wrap = node('section', 'drawer-section'); wrap.append(node('h3', '', '分析表 / 条件与口径'), node('p', 'analysis-table-hint', '左右滑动可查看完整分析表 →'));
    const scroll = node('div', 'analysis-table-scroll'); scroll.tabIndex = 0; scroll.setAttribute('role', 'region'); scroll.setAttribute('aria-label', `${entity.title}分析表，窄屏可横向滚动`);
    const table = node('table', 'analysis-table'); const caption = node('caption', '', entity.title); table.append(caption);
    const head = node('thead'); const hr = node('tr'); array(spec.columns).forEach((c) => { const th = node('th', '', c); th.scope = 'col'; hr.append(th); }); head.append(hr); table.append(head);
    const body = node('tbody'); array(spec.rows).forEach((row) => { const tr = node('tr'); row.forEach((value, index) => { const cell = node(index ? 'td' : 'th', '', value); if (!index) cell.scope = 'row'; tr.append(cell); }); body.append(tr); }); table.append(body); scroll.append(table); wrap.append(scroll);
    if (array(entity.checklist).length) wrap.append(section('使用前固定的比较条件', entity.checklist));
    return wrap;
  }
  function renderScenario(entity) {
    const spec = entity.scenario; if (!spec) return null;
    const wrap = node('section', 'drawer-section scenario-walk'); wrap.append(node('h3', '', '条件场景 / 逐环检查'), node('p', 'scenario-premise', spec.premise));
    const current = Math.min(state.scenarioSteps[entity.id] || 0, spec.steps.length - 1); state.scenarioSteps[entity.id] = current;
    const stepper = node('div', 'scenario-stepper'); stepper.setAttribute('role', 'group'); stepper.setAttribute('aria-label', '场景步骤');
    spec.steps.forEach((step, i) => { const b = button(String(i + 1), i === current ? 'is-active' : '', () => { state.scenarioSteps[entity.id] = i; openEntity(entity.id); }); b.setAttribute('aria-label', step.title); b.setAttribute('aria-pressed', String(i === current)); stepper.append(b); }); wrap.append(stepper);
    const step = spec.steps[current]; const active = node('div', 'scenario-active'); active.setAttribute('aria-live', 'polite');
    active.append(node('h4', '', step.title), node('p', '', step.body), node('p', 'scenario-result', `本环结论：${step.result}`));
    const refs = node('div', 'drawer-related'); array(step.related).forEach((id) => refs.append(button(`${entityFor(id)?.title || id} ↗`, '', () => openEntity(id)))); active.append(refs); wrap.append(active);
    const nav = node('div', 'scenario-navigation'); const prev = button('← 上一步', '', () => { state.scenarioSteps[entity.id] = current - 1; openEntity(entity.id); }); prev.disabled = current === 0;
    const next = button('下一步 →', '', () => { state.scenarioSteps[entity.id] = current + 1; openEntity(entity.id); }); next.disabled = current === spec.steps.length - 1;
    nav.append(prev, node('span', '', `${current + 1} / ${spec.steps.length}`), next); wrap.append(nav);
    if (current === spec.steps.length - 1) wrap.append(node('p', 'scenario-conclusion', spec.outcome), node('p', 'scenario-unknown', '季度预测：原预测 未知 / 新预测 未知 / 修订额 未知。此处是条件推演，未形成实际公司预测。'));
    return wrap;
  }
  function appendResearchLinks(container, id) {
    const ids = array(state.research.enrichments?.[id]); if (!ids.length) return;
    const section = node('section', 'drawer-section'); section.append(node('h3', '', '研究深化 / 比较条件、分歧与场景'));
    const list = node('div', 'drawer-related'); ids.forEach((rid) => { const e = entityFor(rid); if (e) list.append(button(`${e.title} ↗`, '', () => openEntity(rid))); }); section.append(list); container.append(section);
  }
  function openEntity(id) {
    const entity = entityFor(id); if (!entity) { toast(`这张研究卡尚未载入：${id}`); return; }
    const previous = state.drawerEntity;
    openDrawer(); state.drawerEntity = id; $('drawer-kicker').textContent = `${entity.kicker || entity.type || 'RESEARCH DETAIL'} / ${entity.id}`;
    $('detail-drawer').classList.toggle('is-research-analysis', !!entity.analysisTable || !!entity.scenario);
    const body = clear($('drawer-body')); const head = node('div', 'drawer-header');
    if (previous && previous !== id && entityFor(previous)) body.append(button(`← 返回 ${entityFor(previous).title}`, 'drawer-return', () => openEntity(previous)));
    const meta = node('div', 'drawer-meta'); meta.append(statusTag(entity.status)); if (entity.year) meta.append(node('span', '', entity.year)); if (array(entity.countries).length) meta.append(node('span', '', countryText(entity.countries)));
    const h = node('h2', '', entity.title); h.id = 'drawer-title'; head.append(meta, h, node('p', '', entity.summary)); body.append(head);
    const q = node('section', 'drawer-section'); q.append(node('h3', '', '01 / 研究问题'), node('p', '', entity.question || '这一变化经过哪些条件，才能影响公司的经营与利润？')); body.append(q);
    const scenario = renderScenario(entity); if (scenario) body.append(scenario);
    const table = analysisTable(entity); if (table) body.append(table);
    appendResearchLinks(body, id);
    body.append(section('02 / 传导链', entity.chain, true), section('03 / 已知证据', entity.evidence), section('04 / 分歧与适用边界', entity.disagreements), section('05 / 什么会推翻判断', entity.counterevidence), section('06 / 待补数据', entity.gaps), section('07 / 下一更新条件', entity.next));
    const related = array(entity.related); if (related.length) {
      const r = node('section', 'drawer-section'); r.append(node('h3', '', '继续追问 / 关联研究')); const list = node('div', 'drawer-related');
      related.forEach((rid) => { const target = entityFor(rid); if (target) list.append(button(`${target.title} ↗`, '', () => { navigateToEntity(rid, false); openEntity(rid); })); }); r.append(list); body.append(r);
    }
    const sources = node('section', 'drawer-section'); sources.append(node('h3', '', '来源 / 日期 / 原文定位')); appendSources(sources, entity.sourceIds); body.append(sources);
    if (state.path && state.path.steps.includes(id)) {
      const pathNav = node('section', 'drawer-section'); pathNav.append(node('h3', '', `研究路径 / ${state.path.title}`)); const idx = state.path.steps.indexOf(id); const nav = node('div', 'drawer-related');
      if (idx > 0) nav.append(button('← 上一环', '', () => goPathStep(idx - 1)));
      if (idx < state.path.steps.length - 1) nav.append(button('下一环 →', '', () => goPathStep(idx + 1))); else nav.append(button('完成路径 · 回到画布', '', closeDrawer)); pathNav.append(nav); body.append(pathNav);
    }
    $('detail-drawer').scrollTop = 0;
  }
  function renderResearchTools() {
    const host = clear($('research-tools'));
    if (!array(state.research.entities).length) { host.append(node('p', 'empty-note', '研究深化资料未载入；原图与已载入资料仍可使用。')); return; }
    [['tools', '分析表'], ['disputes', '分歧核验'], ['scenarios', '条件场景']].forEach(([key, label]) => {
      const row = node('div', 'research-tool-row'); row.append(node('strong', '', label));
      array(state.research[key]).forEach((id) => { const e = entityFor(id); if (e) row.append(button(e.title, 'research-tool', () => openEntity(id))); }); host.append(row);
    });
    const more = node('div', 'research-tool-row'); more.append(node('strong', '', '供给跟踪'), button('动态瓶颈与利润归属', 'research-tool', () => openEntity('x-bottleneck'))); host.append(more);
    host.append(node('p', 'research-tools-note', '分析表与场景是本项目研究方法；嘉宾观点、原厂披露和待核项分别保留。'));
  }
  function openEdgeDetail(link) {
    const detail = array(state.research.edgeDetails).find((x) => x.source === link.source && x.target === link.target);
    if (!detail) { toast('这条关系的适用条件尚未载入。'); return; }
    const from = array(state.routes.nodes).find((n) => n.id === link.source); const to = array(state.routes.nodes).find((n) => n.id === link.target);
    const id = `edge-${link.source}-${link.target}`;
    state.entities.set(id, { id, type: 'relationship', status: 'inference', title: `${from?.label} → ${to?.label}`, kicker: `关系条件 / ${relationLabels[link.kind]}`, summary: detail.evidenceBoundary,
      question: `${detail.object}：这条关系在什么条件下成立？`, chain: [detail.object, detail.condition, detail.observe], evidence: ['以下条件为本项目研究设计；节点内保留各自原始披露与阶段。'], disagreements: [detail.evidenceBoundary],
      counterevidence: [detail.counter], gaps: ['具体平台、SKU、客户、期间及实际数量尚需逐项填证。'], next: ['用同对象同口径证据更新，缺数据不预设方向或固定滞后。'], related: [from.entityId, to.entityId, detail.analysisId], sourceIds: detail.sourceIds, countries: [],
      analysisTable: { columns: ['字段', '本关系需核'], rows: [['对象', detail.object], ['成立条件', detail.condition], ['观察量', detail.observe], ['反例', detail.counter]] } });
    openEntity(id);
  }
  function openDrawer() {
    if ($('detail-drawer').hidden) state.previousFocus = document.activeElement;
    $('detail-drawer').hidden = false; $('drawer-backdrop').hidden = false; document.body.classList.add('drawer-open');
    requestAnimationFrame(() => $('drawer-close').focus({ preventScroll: true }));
  }
  function closeDrawer() {
    $('detail-drawer').hidden = true; $('drawer-backdrop').hidden = true; document.body.classList.remove('drawer-open'); state.drawerEntity = null;
    if (state.previousFocus && document.contains(state.previousFocus)) state.previousFocus.focus({ preventScroll: true });
  }
  function navigateToEntity(id, scroll = true) {
    const route = array(state.routes.nodes).find((n) => n.entityId === id);
    const era = array(state.history.eras).find((e) => e.id === id || Object.values(e.lanes || {}).some((ids) => array(ids).includes(id)));
    if (route) { state.selectedRoute = route.id; highlightRoutes(); if (scroll) $('ai').scrollIntoView({ behavior: 'smooth' }); }
    else if (era) { state.era = era.id; renderEraSelector(); renderLanes(); renderHistoryChart(); syncOriginalEra(era.id); if (scroll) $('history').scrollIntoView({ behavior: 'smooth' }); }
    else if (id.startsWith('c-')) { const company = array(state.finance.companies).find((c) => `c-${c.id}` === id || c.id === id); if (company) { state.company = company.id; renderFinanceDetail(); renderCompanyCards(); } if (scroll) $('cash').scrollIntoView({ behavior: 'smooth' }); }
  }
  function syncOriginalEra(id) {
    const frame = $('original-history-frame');
    if (frame?.contentWindow && typeof id === 'string' && /^h-era-[1-9]$/.test(id)) frame.contentWindow.postMessage({ type: 'storage-era', id }, location.origin);
  }
  function renderGuides() {
    const container = clear($('guided-paths'));
    array(state.history.paths).forEach((path, index) => {
      const b = button('', `path-card${state.path?.id === path.id ? ' is-active' : ''}`, () => { state.path = path; state.pathStep = 0; renderGuides(); renderPathProgress(); goPathStep(0); });
      b.title = path.description; b.append(node('h3', '', path.title)); container.append(b);
    });
    if (!container.children.length) container.append(node('p', 'empty-note', '研究路径资料尚未载入。'));
  }
  function goPathStep(index) {
    const steps = array(state.path?.steps); if (!steps[index]) return;
    state.pathStep = index; renderPathProgress(); navigateToEntity(steps[index], false); openEntity(steps[index]);
  }
  function renderPathProgress() {
    const container = clear($('path-progress')); container.hidden = !state.path; if (!state.path) return;
    container.append(node('strong', '', state.path.title)); array(state.path.steps).forEach((id, index) => { const entity = entityFor(id); container.append(button(`${index + 1}. ${entity?.title || id}`, index === state.pathStep ? 'is-active' : '', () => goPathStep(index))); });
    container.append(button('退出路径 ×', '', () => { state.path = null; renderPathProgress(); renderGuides(); }));
  }
  function renderThemeStrip() {
    const themes = [ ['周期与产业迁移', 'history'], ['AI 需求', 'ai'], ['技术路径', 'ai'], ['供给价格库存', 'ai'], ['现金与资本', 'cash'], ['国家与地区', 'countries'], ['公司与预期', 'cash'] ];
    const strip = clear($('theme-strip')); themes.forEach(([name, target], index) => { const b = button('', 'theme-button', () => $(target).scrollIntoView({ behavior: 'smooth' })); b.append(node('span', '', `0${index + 1}`), node('b', '', name)); strip.append(b); });
  }
  function selectedEra() { return array(state.history.eras).find((e) => e.id === state.era); }
  function renderEraSelector() {
    const eras = array(state.history.eras); const container = clear($('era-selector'));
    eras.forEach((era) => {
      const b = button('', `era-button${state.era === era.id ? ' is-active' : ''}`, () => { state.era = era.id; renderEraSelector(); renderLanes(); renderHistoryChart(); openEntity(era.id); });
      b.setAttribute('aria-pressed', String(state.era === era.id)); const date = node('small'); date.append(node('span', 'era-code', era.code || ''), document.createTextNode(`${era.start}–${eraEndLabel(era)}`)); b.append(date, node('b', '', era.title)); container.append(b);
    });
  }
  function renderLanes() {
    const era = selectedEra(); const container = clear($('event-lanes')); $('era-summary').textContent = era ? `${era.start}–${eraEndLabel(era)} · ${era.summary}` : '历史时期资料尚未载入。';
    array(state.history.lanes).forEach((lane, index) => {
      const wrapper = node('div', 'event-lane'); const label = node('h4', 'lane-label', lane.label); label.append(node('span', '', String(index + 1).padStart(2, '0'))); wrapper.append(label);
      const ids = array(era?.lanes?.[lane.id]); const events = ids.map(entityFor).filter(Boolean).filter((e) => state.country === 'all' || array(e.countries).includes(state.country));
      events.forEach((entity) => { const b = button('', 'event-card', () => openEntity(entity.id)); b.append(node('span', 'event-title', `${entity.title} ↗`), node('span', 'event-subtitle', entity.summary)); const meta = node('span', 'event-meta'); meta.append(statusTag(entity.status), node('span', 'country-chip', countryText(entity.countries))); b.append(meta); wrapper.append(b); });
      if (!events.length) wrapper.append(node('p', 'empty-note', state.country === 'all' ? '本时期此项仍待补证。' : '该地区暂无已关联事件。'));
      container.append(wrapper);
    });
    renderTimelineMatrix();
  }
  function renderTimelineMatrix() {
    const container = clear($('timeline-matrix')); const eras = array(state.history.eras); const lanes = array(state.history.lanes);
    if (!eras.length || !lanes.length) return;
    container.style.gridTemplateColumns = '';
    const startMs = Date.UTC(1978, 0, 1), endMs = Date.UTC(2027, 0, 1);
    const position = (year) => { const whole = Math.floor(year); const fraction = year - whole; const ms = Date.UTC(whole, 0, 1) + fraction * (Date.UTC(whole + 1, 0, 1) - Date.UTC(whole, 0, 1)); return Math.max(0, Math.min(100, (ms - startMs) / (endMs - startMs) * 100)); };
    const makeLane = (label, index) => { const lane = node('div', 'shared-time-lane'); const title = node('div', 'shared-lane-label', label); if (index) title.dataset.index = index; const field = node('div', 'shared-lane-field'); lane.append(title, field); container.append(lane); return field; };
    const periods = makeLane('研究时期');
    eras.forEach((era, i) => { const left = position(era.start); const stop = Number.isInteger(era.end) ? Math.min(era.end + 1, eras[i + 1]?.start || 2027) : era.end; const right = position(stop); const b = button(`${era.code} · ${era.start}–${eraEndLabel(era)}`, `shared-era${state.era === era.id ? ' is-active' : ''}`, () => { state.era = era.id; renderEraSelector(); renderLanes(); renderHistoryChart(); openEntity(era.id); }); b.style.left = `${left}%`; b.style.width = `calc(${right - left}% - 4px)`; b.title = `${era.title} · ${era.start}–${eraEndLabel(era)}`; periods.append(b); });
    lanes.forEach((lane, index) => { const field = makeLane(lane.label, String(index + 1));
      eras.forEach((era, i) => { const matching = array(era.lanes?.[lane.id]).map(entityFor).filter(Boolean).filter((entity) => state.country === 'all' || array(entity.countries).includes(state.country)); const left = position(era.start); const stop = Number.isInteger(era.end) ? Math.min(era.end + 1, eras[i + 1]?.start || 2027) : era.end; const right = position(stop);
        matching.forEach((entity) => { const b = button(entity.title, `shared-event lane-${lane.id}${state.era === era.id ? ' is-active' : ''}`, () => { state.era = era.id; renderEraSelector(); renderLanes(); renderHistoryChart(); openEntity(entity.id); }); b.style.left = `${left}%`; b.style.width = `calc(${right - left}% - 4px)`; b.title = `${entity.title} · ${entity.summary}`; field.append(b); });
      });
    });
    const years = makeLane('年份'); years.parentElement.classList.add('shared-year-lane'); [1980,1985,1990,1995,2000,2005,2010,2015,2020,2025].forEach((year) => { const n = node('span', 'shared-year', year); n.style.left = `${position(year)}%`; years.append(n); });
  }
  function initChart(id) {
    const host = $(id); if (!host || host.closest('[hidden]')) return null;
    if (!window.echarts) { clear($(id)).append(node('p', 'empty-note', '本地图表依赖未载入；请查看结构化表格与来源。')); return null; }
    if (!charts[id]) charts[id] = window.echarts.init($(id), null, { renderer: 'canvas' }); return charts[id];
  }
  function renderHistoryChart() {
    if ($('history-chart')?.closest('[hidden]')) return;
    const allSeries = array(state.history.historySeries?.series); const series = allSeries.filter((s) => s.kind === state.historyKind);
    const notes = clear($('history-chart-notes')); if (state.history.historySeries?.asOf) notes.append(node('p', '', `历史曲线快照：${state.history.historySeries.asOf}；专题资料截止日不代表曲线已重新取数。`)); const parentNotes = state.history.historySeries?.notes; array(Array.isArray(parentNotes) ? parentNotes : [parentNotes]).filter(Boolean).forEach((note) => notes.append(node('p', '', note)));
    series.forEach((s) => { const row = node('p'); row.append(document.createTextNode(`${s.name} · ${s.scope || ''} · ${s.unit || '%'} `), statusTag(s.status)); if (array(s.sourceIds).length) row.append(button('查看来源', '', () => showSources(s.sourceIds, s.name, [s.scope]))); notes.append(row); });
    if (!series.some((s) => array(s.points).some((p) => typeof p[1] === 'number'))) {
      if (charts['history-chart']) { charts['history-chart'].dispose(); delete charts['history-chart']; }
      const c = clear($('history-chart')); c.classList.add('chart-empty'); c.append(node('p', '', state.historyKind === 'margin' ? '尚无可展示的历史利润率序列。时间轴与研究卡保留；不以示意数值补齐。' : '尚无可展示的历史回撤序列。股价回撤与产品价格跌幅不混用。')); return;
    }
    $('history-chart').classList.remove('chart-empty'); const chart = initChart('history-chart'); if (!chart) return;
    const era = selectedEra(); const isMargin = state.historyKind === 'margin';
    chart.setOption({ backgroundColor: 'transparent', animation: false, color: colors, textStyle: { fontFamily: 'Inter,PingFang SC,sans-serif' }, legend: { top: 0, left: 0, type: 'scroll', itemWidth: 15, itemHeight: 2, textStyle: { color: '#777166', fontSize: 10 } }, grid: { top: 40, left: 96, right: 18, bottom: 29 }, tooltip: { trigger: 'axis', confine: true, textStyle: { fontSize: 11 }, valueFormatter: (v) => v == null ? '未取得' : `${number(v)}%` }, xAxis: { type: 'time', min: '1978-01-01', max: '2027-01-01', axisLine: { lineStyle: { color: '#c9c1b2' } }, axisTick: { show: false }, axisLabel: { color: '#827a6e', fontSize: 9, formatter: '{yyyy}' }, splitLine: { show: false } }, yAxis: { type: 'value', name: isMargin ? '利润率 (%)' : '距前高回撤 (%)', nameTextStyle: { color: '#827a6e', fontSize: 9, align: 'left' }, axisLabel: { color: '#827a6e', fontSize: 9, formatter: '{value}%' }, splitLine: { lineStyle: { color: '#e7e2d7', type: 'dashed' } }, scale: true, ...(isMargin ? {} : { max: 0 }) }, series: series.map((s, index) => ({ type: 'line', name: s.name, data: array(s.points), showSymbol: false, connectNulls: false, itemStyle: { color: s.kind === 'drawdown' ? '#8b3a62' : s.name.includes('海力士') ? '#a07a2c' : '#4a6fa5' }, lineStyle: { width: 1.6, color: s.kind === 'drawdown' ? '#8b3a62' : s.name.includes('海力士') ? '#a07a2c' : '#4a6fa5', ...(s.name.includes('年度') ? { type: 'dotted' } : {}) }, emphasis: { focus: 'series' }, ...(index === 0 && era ? { markArea: { silent: true, itemStyle: { color: '#b9a57d13' }, label: { show: false }, data: [[{ xAxis: `${era.start}-01-01` }, { xAxis: (Number.isInteger(era.end) ? `${era.end}-12-31` : state.history.asOf || '2026-10-08') }]] } } : {}) })) }, true);
    chart.off('click'); chart.on('click', (params) => {
      const point = params.data; if (!Array.isArray(point) || point[0] == null) return;
      const year = new Date(point[0]).getUTCFullYear(); const era = array(state.history.eras).findLast((item) => year >= item.start && year <= Math.ceil(item.end || 2026));
      if (era) { state.era = era.id; renderEraSelector(); renderLanes(); renderHistoryChart(); openEntity(era.id); }
      else showSources(array(series[params.seriesIndex]?.sourceIds), series[params.seriesIndex]?.name || '历史序列');
    });
  }
  function renderRouteGraph() {
    const container = clear($('route-columns')); const columns = array(state.routes.columns); container.style.gridTemplateColumns = `repeat(${Math.max(columns.length, 1)},minmax(0,1fr))`;
    columns.forEach((column, index) => {
      const col = node('section', 'route-column'); const header = node('h3', 'route-column-header', column.label); header.append(node('span', '', String(index + 1).padStart(2, '0'))); col.append(header); const body = node('div', 'route-column-body');
      array(state.routes.nodes).filter((n) => n.column === column.id).forEach((n) => { const b = button('', 'route-node', () => { state.selectedRoute = n.id; highlightRoutes(); openEntity(n.entityId); }); b.dataset.nodeId = n.id; b.setAttribute('aria-label', `${n.label}，${n.stage || '发展状态见来源'}`); b.append(node('b', '', n.label), node('small', '', n.stage || '发展状态见来源')); body.append(b); }); col.append(body); container.append(col);
    });
    if (!columns.length) container.append(node('p', 'empty-note', 'AI 路线数据尚未载入。'));
    const themes = clear($('route-themes')); array(state.routes.themes).forEach((theme) => { themes.append(button(theme.title, `route-theme${state.routeTheme === theme.id ? ' is-active' : ''}`, () => { state.routeTheme = state.routeTheme === theme.id ? null : theme.id; state.selectedRoute = null; renderRouteThemesOnly(); highlightRoutes(); showTheme(theme); })); });
    const select = clear($('route-company')); select.append(new Option('全部路径', 'all')); const ids = unique(array(state.routes.entities).flatMap((e) => array(e.companyIds))).sort();
    const companyNames = { mu: '美光', samsung: '三星', hynix: 'SK 海力士', cxmt: '长鑫存储', ymtc: '长江存储', longsys: '江波龙', biwin: '佰维存储', tsmc: '台积电', nvidia: 'NVIDIA', amd: 'AMD' };
    ids.forEach((id) => select.append(new Option(companyNames[id] || id, id))); select.value = state.routeCompany;
    renderRouteInsights(); requestAnimationFrame(() => { drawRouteLines(); highlightRoutes(); });
  }
  function renderRouteThemesOnly() { Array.from($('route-themes').children).forEach((b, i) => { b.classList.toggle('is-active', array(state.routes.themes)[i]?.id === state.routeTheme); }); }
  function showTheme(theme) {
    if (state.routeTheme !== theme.id) return;
    const synthetic = { id: `view-${theme.id}`, title: theme.title, kicker: '研究主题', type: 'theme', summary: theme.summary, question: '这一主线如何与需求、技术、资金和公司利润相连？', chain: array(theme.entityIds).map((id) => entityFor(id)?.title).filter(Boolean), evidence: [], disagreements: ['主题入口用于组织研究，具体事实和发展阶段以关联卡片及原始披露为准。'], counterevidence: [], gaps: [], next: ['选择下方关联研究，查看每条路径的证据与更新条件。'], related: theme.entityIds, sourceIds: unique(array(theme.entityIds).flatMap((id) => array(entityFor(id)?.sourceIds))), countries: [], status: 'inference' };
    state.entities.set(synthetic.id, synthetic); openEntity(synthetic.id);
  }
  function drawRouteLines() {
    const svg = clear($('route-lines')); if (window.innerWidth <= 600) return;
    const graph = $('route-graph'); const bounds = graph.getBoundingClientRect(); svg.setAttribute('viewBox', `0 0 ${bounds.width} ${graph.scrollHeight}`); svg.style.height = `${graph.scrollHeight}px`;
    const elements = new Map(Array.from(graph.querySelectorAll('[data-node-id]')).map((n) => [n.dataset.nodeId, n]));
    array(state.routes.links).forEach((link, i) => {
      const a = elements.get(link.source), b = elements.get(link.target); if (!a || !b) return;
      const ar = a.getBoundingClientRect(), br = b.getBoundingClientRect(); const fromLeft = ar.left > br.left;
      let x1 = (fromLeft ? ar.left : ar.right) - bounds.left; let x2 = (fromLeft ? br.right : br.left) - bounds.left; const y1 = ar.top + ar.height / 2 - bounds.top, y2 = br.top + br.height / 2 - bounds.top;
      const gap = Math.max(Math.abs(x2 - x1) * .45, 28); const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      path.setAttribute('d', `M ${x1},${y1} C ${x1 + (fromLeft ? -gap : gap)},${y1} ${x2 + (fromLeft ? gap : -gap)},${y2} ${x2},${y2}`); path.setAttribute('class', 'route-edge'); path.dataset.linkIndex = String(i); path.style.stroke = relationColors[link.kind] || colors[1]; if (['conditional_substitute', 'resource_competition'].includes(link.kind)) path.setAttribute('stroke-dasharray', '4 4'); svg.append(path);
    });
  }
  function highlightRoutes() {
    const selected = state.selectedRoute; const links = array(state.routes.links); const adjacentLinks = selected ? links.filter((l) => l.source === selected || l.target === selected) : [];
    const neighbors = new Set(adjacentLinks.flatMap((l) => [l.source, l.target])); const theme = array(state.routes.themes).find((t) => t.id === state.routeTheme); const themeSet = new Set(array(theme?.entityIds));
    $('route-columns').querySelectorAll('[data-node-id]').forEach((b) => { const n = array(state.routes.nodes).find((item) => item.id === b.dataset.nodeId); const entity = entityFor(n?.entityId); const companyMatch = state.routeCompany === 'all' || array(entity?.companyIds).includes(state.routeCompany); const themeMatch = !theme || themeSet.has(n?.entityId); b.classList.toggle('is-active', b.dataset.nodeId === selected); b.classList.toggle('is-related', selected && neighbors.has(b.dataset.nodeId) && b.dataset.nodeId !== selected); b.classList.toggle('is-dimmed', !!selected && !neighbors.has(b.dataset.nodeId)); b.classList.toggle('is-filtered', !companyMatch || !themeMatch); b.classList.toggle('is-filter-match', (state.routeCompany !== 'all' || !!theme) && companyMatch && themeMatch); b.setAttribute('aria-pressed', String(b.dataset.nodeId === selected)); });
    $('route-lines').querySelectorAll('[data-link-index]').forEach((p) => { const link = links[Number(p.dataset.linkIndex)]; const active = selected && (link.source === selected || link.target === selected); p.classList.toggle('is-active', !!active); p.classList.toggle('is-dimmed', !!selected && !active); });
    const info = clear($('route-selection'));
    if (selected) {
      const n = array(state.routes.nodes).find((n) => n.id === selected); info.append(node('span', 'selection-label', n?.label || '路径关系')); const list = node('div', 'relationship-list');
      adjacentLinks.forEach((link) => { const otherId = link.source === selected ? link.target : link.source; const other = array(state.routes.nodes).find((n) => n.id === otherId); const from = array(state.routes.nodes).find((n) => n.id === link.source); const to = array(state.routes.nodes).find((n) => n.id === link.target); list.append(button(`${from?.label || link.source} → ${to?.label || link.target}｜${relationLabels[link.kind] || link.kind} · ${link.label || ''}`, '', () => { state.selectedRoute = otherId; highlightRoutes(); if (other) openEntity(other.entityId); })); }); if (!adjacentLinks.length) list.append(node('p', '', '此节点的跨层关系仍待补证。')); info.append(list);
      if (array(state.research.edgeDetails).length && adjacentLinks.length) {
        const details = node('details', 'edge-conditions'); details.append(node('summary', '', `查看 ${adjacentLinks.length} 条关系的适用条件与反例`));
        adjacentLinks.forEach((link) => { const d = array(state.research.edgeDetails).find((x) => x.source === link.source && x.target === link.target); if (!d) return; const from = array(state.routes.nodes).find((x) => x.id === link.source); const to = array(state.routes.nodes).find((x) => x.id === link.target); const row = node('div', 'edge-condition-row'); row.append(button(`${from.label} → ${to.label} · 条件与证据 ↗`, '', () => openEdgeDetail(link)), node('p', '', `${d.object}｜${d.condition}`)); details.append(row); }); info.append(details);
      }
    } else { info.append(node('span', 'selection-label', theme ? '当前主题' : '读图方式'), node('p', '', theme ? theme.summary : state.routeCompany !== 'all' ? '高亮所选公司明确关联的节点；其他路径保留以供比较。具体资格和业务暴露请打开研究卡。' : '点击节点展开研究方法与证据；高亮连线表示相邻关系。路线发展状态以原始披露日期为准。')); }
  }
  function renderRouteInsights() {
    const container = clear($('route-insights')); const themes = array(state.routes.themes).slice(0, 3); themes.forEach((theme, i) => { const b = button('', 'insight-card', () => { state.routeTheme = theme.id; state.selectedRoute = null; renderRouteThemesOnly(); highlightRoutes(); showTheme(theme); }); b.append(node('span', '', `RESEARCH QUESTION / 0${i + 1}`), node('h3', '', theme.title), node('p', '', theme.summary)); container.append(b); });
  }
  function companyEntityId(company) { return company.id.startsWith('c-') ? company.id : `c-${company.id}`; }
  function renderCompanyCards() {
    const container = clear($('company-cards')); array(state.finance.companies).forEach((company) => {
      const card = node('article', `company-card${company.id === state.company ? ' is-active' : ''}`); const head = node('div', 'company-heading'); head.append(node('h3', '', company.name), button('业务与证据 ↗', '', () => openEntity(companyEntityId(company)))); card.append(head);
      card.append(node('p', 'company-period', `${company.latest?.period || '最新期间未取得'} · ${dateText(company.latest?.periodEnd)}\n${company.currency || ''} / ${company.unit || ''} · ${disclosureLabel(company.latest || {})}`));
      const metrics = node('div', 'metric-grid'); array(company.latest?.metrics).forEach((metric) => { const m = node('div', 'metric'); m.append(node('span', 'metric-label', metric.label)); const val = node('span', `metric-value${metric.value == null ? ' missing' : ''}`, number(metric.value)); if (metric.value != null) val.append(node('span', 'metric-unit', metric.unit || company.unit)); m.append(val); if (array(metric.sourceIds).length) m.append(button('口径与来源', 'metric-source', () => showSources(metric.sourceIds, `${company.name} · ${metric.label}`, [metric.scope, ...listOf(metric.notes)].filter(Boolean)))); metrics.append(m); });
      if (!metrics.children.length) metrics.append(node('p', 'empty-note', '最新财务字段未取得。')); card.append(metrics, node('p', 'company-scope', company.scope || '财务主体口径待核'));
      if (array(company.limitations)[0]) card.append(node('p', 'company-key-limit', company.limitations[0]));
      card.append(button('查看五年现金流及披露期间 →', 'company-finance-button', () => { state.company = company.id; renderCompanyCards(); renderFinanceDetail(); document.querySelector('.finance-detail').scrollIntoView({ behavior: 'smooth', block: 'start' }); })); container.append(card);
    });
    if (!container.children.length) container.append(node('p', 'empty-note', '当前公司财务模块尚未载入，不以示意值代替。'));
  }
  function renderFinanceDetail() {
    const company = array(state.finance.companies).find((c) => c.id === state.company) || array(state.finance.companies)[0]; if (!company) { clear($('finance-table')).append(node('p', 'empty-note', '财务数据未载入。')); clear($('finance-chart')).append(node('p', 'empty-note', '没有可展示的公司财务序列。')); return; } state.company = company.id;
    $('finance-title').textContent = `${company.name} · 现金流的五年轨迹`; $('finance-scope').textContent = `${company.scope} · ${company.currency} / ${company.unit} · 数据截止 ${dateText(company.asOf)}。各点为公司原始财年，未统一成自然年。`;
    const tabs = clear($('finance-company-tabs')); array(state.finance.companies).forEach((c) => { const b = button(c.name, c.id === company.id ? 'is-active' : '', () => { state.company = c.id; renderFinanceDetail(); renderCompanyCards(); }); b.setAttribute('aria-pressed', String(c.id === company.id)); tabs.append(b); });
    const annual = array(company.annual); const chart = initChart('finance-chart');
    if (chart) chart.setOption({ animation: false, color: [colors[2], '#ba9c73', colors[0]], textStyle: { fontFamily: 'Inter,PingFang SC,sans-serif' }, grid: { top: 58, left: 55, right: 12, bottom: 30 }, legend: { top: 7, left: 0, itemWidth: 13, itemHeight: 7, textStyle: { color: '#777166', fontSize: 10 } }, tooltip: { trigger: 'axis', confine: true, textStyle: { fontSize: 11 }, valueFormatter: (v) => v == null ? '未取得' : `${number(v)} ${company.unit}` }, xAxis: { type: 'category', data: annual.map((r) => r.period), axisLine: { lineStyle: { color: '#c9c1b2' } }, axisTick: { show: false }, axisLabel: { fontSize: 9, color: '#827a6e', interval: 0 } }, yAxis: { type: 'value', name: `${company.currency} / ${company.unit}`, nameTextStyle: { fontSize: 9, color: '#827a6e', align: 'left' }, axisLabel: { fontSize: 9, color: '#827a6e' }, splitLine: { lineStyle: { color: '#e7e2d7', type: 'dashed' } } }, series: [{ name: '经营现金流', type: 'bar', barMaxWidth: 22, data: annual.map((r) => r.ocf ?? null) }, { name: '资本开支（支出额）', type: 'bar', barMaxWidth: 22, data: annual.map((r) => r.capex ?? null) }, { name: '自由现金流', type: 'line', symbolSize: 6, connectNulls: false, lineStyle: { width: 2 }, data: annual.map((r) => r.fcf ?? null) }] }, true);
    if (chart) { chart.off('click'); chart.on('click', (params) => { const row = annual[params.dataIndex]; if (row) showSources(row.sourceIds, `${company.name} · ${row.period}`, listOf(row.notes)); }); }
    const wrapper = clear($('finance-table')); const table = node('table'); const thead = node('thead'); const hrow = node('tr'); ['期间 / 披露日', '现金', '短期投资', '有息债务', '经营现金流', '资本开支', '自由现金流', '币种 / 单位', '来源'].forEach((label) => hrow.append(node('th', '', label))); thead.append(hrow); table.append(thead); const tbody = node('tbody');
    [...annual.map((r) => ({ ...r, isInterim: false })), ...array(company.interim).map((r) => ({ ...r, isInterim: true }))].forEach((row) => { const tr = node('tr', row.isInterim ? 'interim-row' : ''); const period = node('td', 'row-period', `${row.period}${row.isInterim ? ' · 中期' : ''}`); period.append(node('small', '', `${dateText(row.periodStart)} — ${dateText(row.periodEnd)}`), node('small', '', `${disclosureLabel(row)}${row.durationType ? ` · ${durationLabels[row.durationType] || row.durationType}` : ''}`)); tr.append(period); ['cash', 'shortInvestments', 'debt', 'ocf', 'capex', 'fcf'].forEach((key) => tr.append(node('td', '', number(row[key])))); tr.append(node('td', '', `${row.currency || company.currency} / ${row.unit || company.unit}`)); const source = node('td'); source.append(button('查看', '', () => showSources(row.sourceIds, `${company.name} · ${row.period}`, listOf(row.notes)))); tr.append(source); tbody.append(tr); }); table.append(tbody); wrapper.append(table);
    const limitations = clear($('finance-limitations')); limitations.append(node('b', '', '口径与未决项')); const list = node('ul'); array(company.limitations).forEach((item) => list.append(node('li', '', item))); limitations.append(list);
  }
  function renderFinanceNotes() {
    const c = clear($('finance-channel-notes'));
    c.append(node('p', '', '财务以公司/SEC原始披露为准，FactSet用于发现与交叉对照；Wind验证未完成。金额保持本币与原始期间，中期不与全年相加。'));
    const details = node('details'); details.append(node('summary', '', '展开数据口径与验证记录'));
    array(state.finance.channelNotes).forEach((note) => details.append(node('p', '', note))); c.append(details);
  }
  function renderCountryEvents() {
    const ids = ['h-vlsi', 'h-hynix-restructure', 'h-elpida', 'h-china-access', 'h-export-controls', 'h-chips', 'h-nation-support']; const events = ids.map(entityFor).filter(Boolean); const c = clear($('country-events'));
    events.forEach((e) => { const b = button('', 'country-event', () => { navigateToEntity(e.id, false); openEntity(e.id); }); b.append(node('small', '', `${e.year || ''} ${countryText(e.countries)}`), node('strong', '', `${e.title} ↗`), node('p', '', e.summary)); c.append(b); });
    if (!events.length) c.append(node('p', 'empty-note', '国家事件资料尚未载入。'));
  }
  function renderSources() {
    const all = [...state.sources.values()]; const query = state.sourceQuery.toLowerCase();
    const results = all.filter((s) => (state.sourceCategory === 'all' || sourceCategory(s) === state.sourceCategory) && (state.sourceProof === 'all' || (s.proofState || 'unclassified') === state.sourceProof) && [s.title, s.date, s.locator, s.scope, s.kind, s.id, s.family].some((v) => text(v).toLowerCase().includes(query))); const perPage = 10; const maxPage = Math.max(0, Math.ceil(results.length / perPage) - 1); state.sourcePage = Math.min(state.sourcePage, maxPage); const start = state.sourcePage * perPage; const slice = results.slice(start, start + perPage); const container = clear($('source-list'));
    slice.forEach((source, i) => { const row = node('article', 'source-item'); row.append(node('span', 'source-index', String(start + i + 1).padStart(2, '0'))); const content = node('div'); content.append(sourceLink(source), node('span', 'source-id', source.id)); if (source.locator) content.append(node('p', '', `定位：${source.locator}`)); if (source.scope) content.append(node('p', '', source.scope)); if (source.family) content.append(node('p', '', `来源血缘：${source.family}；同源不重复计票。`)); const meta = node('div', 'source-meta', dateText(source.date)); meta.append(node('small', '', source.kind || '类型待标注')); if (source.proofState) meta.append(node('small', '', proofLabels[source.proofState] || '未单独标注')); row.append(content, meta); container.append(row); });
    if (!slice.length) container.append(node('p', 'empty-note', '没有匹配来源。')); $('evidence-count').textContent = `${all.length} SOURCES`; $('source-range').textContent = results.length ? `${start + 1}–${Math.min(start + perPage, results.length)} / ${results.length} 条来源` : '0 条来源'; $('sources-prev').disabled = state.sourcePage === 0; $('sources-next').disabled = state.sourcePage >= maxPage;
  }
  function sourceCategory(s) {
    if (s.category) return s.category;
    const kind = text(s.kind);
    if (/播客|访谈|视频/.test(kind)) return 'podcast';
    if (/论文|研究方/.test(kind)) return 'paper';
    if (/研报|作者材料/.test(kind)) return 'report';
    if (/原厂|原公告|发行人|报表|公司|标准组织|一手|SEC|披露|监管|官方|^primary$|平台技术文档/.test(kind)) return 'issuer';
    if (/方法|记录|框架/.test(kind)) return 'method';
    return 'other';
  }
  function openResearchHash() {
    if (!location.hash.startsWith('#research=')) return;
    let id;
    try { id = decodeURIComponent(location.hash.slice('#research='.length)); } catch { return; }
    if (entityFor(id)) { navigateToEntity(id, false); openEntity(id); }
  }
  function wireInteractions() {
    window.addEventListener('hashchange', openResearchHash);
    const historyFrame = $('original-history-frame');
    window.addEventListener('message', (event) => {
      if (!historyFrame || event.origin !== location.origin || event.source !== historyFrame.contentWindow) return;
      const message = event.data; if (!message || typeof message !== 'object') return;
      if (message.type === 'storage-height' && typeof message.height === 'number' && Number.isFinite(message.height)) {
        const height = Math.ceil(Math.max(500, Math.min(8000, message.height))); historyFrame.height = String(height); historyFrame.style.height = `${height}px`;
      } else if (message.type === 'storage-open' && typeof message.id === 'string' && entityFor(message.id)) {
        navigateToEntity(message.id, false); openEntity(message.id);
      }
    });
    historyFrame?.addEventListener('load', () => { if (state.path && state.era) syncOriginalEra(state.era); });
    $('drawer-close').addEventListener('click', closeDrawer); $('drawer-backdrop').addEventListener('click', closeDrawer);
    document.addEventListener('keydown', (event) => {
      if ($('detail-drawer').hidden) return;
      if (event.key === 'Escape') { event.preventDefault(); closeDrawer(); }
      if (event.key === 'Tab') { const nodes = [...$('detail-drawer').querySelectorAll('a[href],button:not([disabled]),[tabindex="0"]')].filter((n) => n.getClientRects().length); const first = nodes[0], last = nodes[nodes.length - 1]; if (!first) return; if (event.shiftKey && (document.activeElement === first || document.activeElement === $('detail-drawer'))) { event.preventDefault(); last.focus(); } else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); } }
    });
    document.querySelectorAll('[data-history-chart]').forEach((b) => b.addEventListener('click', () => { state.historyKind = b.dataset.historyChart; document.querySelectorAll('[data-history-chart]').forEach((other) => { other.classList.toggle('is-active', other === b); other.setAttribute('aria-pressed', String(other === b)); }); renderHistoryChart(); }));
    $('country-filter').addEventListener('change', (e) => { state.country = e.target.value; renderLanes(); });
    $('reset-history').addEventListener('click', () => { state.country = 'all'; $('country-filter').value = 'all'; state.era = array(state.history.eras).at(-1)?.id || null; renderEraSelector(); renderLanes(); renderHistoryChart(); });
    $('route-company').addEventListener('change', (e) => { state.routeCompany = e.target.value; state.selectedRoute = null; highlightRoutes(); });
    $('reset-routes').addEventListener('click', () => { state.routeCompany = 'all'; state.selectedRoute = null; state.routeTheme = null; $('route-company').value = 'all'; renderRouteThemesOnly(); highlightRoutes(); });
    $('source-search').addEventListener('input', (e) => { state.sourceQuery = e.target.value; state.sourcePage = 0; renderSources(); }); $('sources-prev').addEventListener('click', () => { state.sourcePage--; renderSources(); }); $('sources-next').addEventListener('click', () => { state.sourcePage++; renderSources(); });
    $('source-category').addEventListener('change', (e) => { state.sourceCategory = e.target.value; state.sourcePage = 0; renderSources(); });
    $('source-proof').addEventListener('change', (e) => { state.sourceProof = e.target.value; state.sourcePage = 0; renderSources(); });
    $('source-reset').addEventListener('click', () => { state.sourceCategory = state.sourceProof = 'all'; state.sourceQuery = ''; state.sourcePage = 0; $('source-category').value = $('source-proof').value = 'all'; $('source-search').value = ''; renderSources(); });
    let resizeTimer; window.addEventListener('resize', () => { clearTimeout(resizeTimer); resizeTimer = setTimeout(() => { Object.values(charts).forEach((chart) => chart.resize()); drawRouteLines(); highlightRoutes(); }, 100); });
  }
  async function load() {
    wireInteractions(); renderThemeStrip();
    const modules = ['history', 'routes', 'finance', 'research']; const results = await Promise.allSettled(modules.map(async (name) => { const embedded = document.getElementById(`storage-data-${name}`); if (embedded) return JSON.parse(embedded.textContent); const response = await fetch(`data/${name}.json`); if (!response.ok) throw new Error(`${name}.json: HTTP ${response.status}`); return response.json(); }));
    const errors = []; results.forEach((result, index) => { const module = modules[index]; if (result.status === 'fulfilled') { state[module] = result.value; array(result.value.entities).forEach((e) => state.entities.set(e.id, e)); array(result.value.sources).forEach((s) => state.sources.set(s.id, s)); } else { errors.push(module); console.warn('Research module unavailable:', module, result.reason); } });
    const dates = unique(modules.map((name) => state[name].asOf).filter(Boolean)); $('asof-label').textContent = dates.length ? `资料截止 ${dates.join(' / ')}` : '资料截止日未取得'; $('coverage-summary').textContent = `${array(state.history.eras).length} 个历史时期 · ${array(state.routes.nodes).length} 个技术节点`;
    const status = $('load-status'); if (errors.length) { status.classList.add('error'); status.textContent = `以下本地数据模块未载入：${errors.join('、')}。已载入内容仍可使用。请刷新页面；如仍不可用，请联系维护者。`; } else status.hidden = true;
    state.era = array(state.history.eras).at(-1)?.id || null; state.company = array(state.finance.companies)[0]?.id || null;
    renderGuides(); renderPathProgress(); renderEraSelector(); renderLanes(); renderHistoryChart(); renderRouteGraph(); renderResearchTools(); renderCompanyCards(); renderFinanceDetail(); renderFinanceNotes(); renderCountryEvents(); renderSources();
    openResearchHash();
    if (document.fonts?.ready) document.fonts.ready.then(() => { Object.values(charts).forEach((chart) => chart.resize()); drawRouteLines(); highlightRoutes(); });
  }
  load().catch((error) => { $('load-status').hidden = false; $('load-status').classList.add('error'); $('load-status').textContent = '页面遇到数据格式问题，部分图表无法展示。请联系维护者核对资料；不完整数据不会被补成示意值。'; console.error(error); });
})();
