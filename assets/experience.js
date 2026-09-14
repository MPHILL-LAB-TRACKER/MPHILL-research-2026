/* Public appearance preferences only; never store accounts, tokens or unpublished content. */
'use strict';
(() => {
  const $ = (s, root=document) => root.querySelector(s), $$ = (s, root=document) => [...root.querySelectorAll(s)];
  const key = 'ted2-appearance-v62:' + location.host;
  function setAppearance(selection, remember=false) {
    const config=window.TED2_APPEARANCE||{mode:'system',allow:true};
    if(!['system','light','dark'].includes(selection))selection=config.mode;
    if(!config.allow)selection=config.mode;
    document.documentElement.dataset.appearance=selection==='system'?(matchMedia('(prefers-color-scheme:dark)').matches?'dark':'light'):selection;
    $$('[data-appearance-control]').forEach(el=>{el.value=selection;el.hidden=!config.allow;});
    if(remember&&config.allow)try{localStorage.setItem(key,selection);}catch{}
    window.dispatchEvent(new CustomEvent('ted2-appearance-changed'));
  }
  function current() {let mode=(window.TED2_APPEARANCE||{}).mode||'system';try{if((window.TED2_APPEARANCE||{}).allow)mode=localStorage.getItem(key)||mode;}catch{}return mode;}
  window.TED2Appearance={apply:()=>setAppearance(current()),set:setAppearance};
  document.addEventListener('change',e=>{if(e.target.matches('[data-appearance-control]'))setAppearance(e.target.value,true);});
  const observer=new MutationObserver(()=>{ $$('[data-appearance-control]:not([data-ready])').forEach(el=>{el.dataset.ready='yes';el.value=current();}); });observer.observe(document.body,{childList:true,subtree:true});
  matchMedia('(prefers-color-scheme:dark)').addEventListener('change',()=>setAppearance(current()));setAppearance(current());
  document.addEventListener('keydown',e=>{if(e.key==='Escape')$$('.nav-dropdown[open]').forEach(d=>{d.open=false;$('summary',d)?.focus();});});
  document.addEventListener('click',e=>{$$('.nav-dropdown[open]').forEach(d=>{if(!d.contains(e.target))d.open=false;});});
  $$('nav a').forEach(a=>{try{if(new URL(a.href).pathname===location.pathname)a.setAttribute('aria-current','page');}catch{/* Detached or file previews may not have a URL base. */}});
  if(document.body.dataset.publicCache==='yes'&&'serviceWorker' in navigator&&window.isSecureContext&&!location.pathname.includes('/api/publish/preview/')) {
    const base=(document.body.dataset.base||'')+'/';
    navigator.serviceWorker.register(base+'sw.js',{scope:base,updateViaCache:'none'}).then(r=>r.update()).catch(()=>{/* cache failure must not block content */});
  }
  function text(tag,value,cls=''){const el=document.createElement(tag);el.textContent=String(value??'');if(cls)el.className=cls;return el;}
  function safeLink(value){try{const u=new URL(value);return u.protocol==='https:'&&!u.username&&!u.password?u.href:null;}catch{return null;}}
  $$('[data-pulse]').forEach(panel=>{
    const list=$('[data-pulse-list]',panel),status=$('[data-pulse-status]',panel),filter=$('[data-pulse-filter]',panel);let data=[];
    function prepareFilter(){const selected=filter.value;filter.replaceChildren(new Option('All topics',''));const tags=new Set();$$('[data-pulse-tags]',list).forEach(c=>c.dataset.pulseTags.split(' ').filter(Boolean).forEach(t=>tags.add(t)));[...tags].sort().forEach(t=>filter.add(new Option('#'+t,t)));filter.value=[...tags].includes(selected)?selected:'';filter.onchange=()=>$$('[data-pulse-tags]',list).forEach(c=>{c.hidden=!!filter.value&&!c.dataset.pulseTags.split(' ').includes(filter.value);});filter.onchange();}
    function render(items){
      const nodes=[];for(const row of items.slice(0,Number(panel.dataset.limit)||6)){
        const url=safeLink(row.source_url);if(!url||typeof row.title!=='string')continue;
        const card=text('article','','pulse-card');card.dataset.pulseTags=(row.tags||[]).map(t=>String(t).replace(/[^\p{L}\p{N}_-]/gu,'')).join(' ');
        const top=text('div','','pulse-meta');top.append(text('span',['research','preprint','blog'].includes(row.source_kind)?row.source_kind:'Source record','tag'),text('time',row.published_date||''));card.append(top);
        const heading=text('h3',''),link=text('a',row.title);link.href=url;link.rel='noopener';heading.append(link);card.append(heading);
        // Cloud delivery intentionally contains no generated/republished scientific abstract.
        if(row.summary&&!row.automatic)card.append(text('p',row.summary));
        card.append(text('p',(row.source_label||'Source')+(row.authors?' · '+row.authors:''),'small muted'),text('p',row.automatic?'Automatic source headline — not reviewed by the laboratory':'Administrator-reviewed item','small evidence-label'));
        const tags=text('div','','topic-tags');for(const t of (row.tags||[]).slice(0,8))tags.append(text('span','#'+String(t).replace(/^#/,'')));card.append(tags);nodes.push(card);
      }
      if(nodes.length)list.replaceChildren(...nodes);else list.replaceChildren(text('p','No matching records are available for the current source window.'));prepareFilter();
    }
    prepareFilter();
    if(panel.dataset.auto!=='yes'||location.pathname.includes('/api/publish/preview/'))return;
    const isStatic=document.body.dataset.publicCache==='yes';
    if(isStatic&&panel.dataset.delivery!=='github-scheduled'){status.textContent='Published snapshot. Local source checks appear online after the next publication.';return;}
    const url=isStatic?'https://raw.githubusercontent.com/MPHILL-LAB-TRACKER/MPHILL-research-2026/science-feed/feed.json':'/science-feed.json';
    async function refresh(){if(document.hidden)return;const ctrl=new AbortController(),timer=setTimeout(()=>ctrl.abort(),10000);
      try{const response=await fetch(url,{cache:'no-store',credentials:'omit',signal:ctrl.signal});if(!response.ok)throw Error('unavailable');const bytes=await response.text();if(bytes.length>2097152)throw Error('oversize');const feed=JSON.parse(bytes);if(feed.digest!==panel.dataset.policy||!Array.isArray(feed.items))throw Error('policy');
        data=feed.items;render(data);const checked=feed.last_success||feed.state?.last_success||'';status.textContent=checked?'Source check: '+new Date(checked).toLocaleString()+'. '+(feed.errors?.length?'Some sources were unavailable; earlier dated records are retained.':'Read the original sources for context.'):'No successful source check yet.';
        if(!data.length)status.textContent='No matching records were returned. Try a broader administrator-approved topic; no results were invented.';
      }catch{status.textContent='Automatic source feed is currently unavailable or awaiting its first matching update. The last published selection is shown.';}
      finally{clearTimeout(timer);}
    }
    refresh();setInterval(refresh,5*60*1000);document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh();});
  });
})();
