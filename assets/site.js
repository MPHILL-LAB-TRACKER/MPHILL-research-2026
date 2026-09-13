'use strict';
(() => {
  document.documentElement.classList.add('js');
  const base = document.body.dataset.base || '';
  // Preserve links from earlier hash-routed releases while exposing crawlable URLs.
  if (location.hash.startsWith('#/')) {
    const parts = location.hash.slice(2).split('?')[0].split('/');
    const aliases = {'jaydine-jeris':'jaydine-feris','denise-bouman':'denis-bouman','maneria-halweendo':'manelia-halweendo','charity-maepa':'charity-mepa','nonku-phili':'nonku-phiri'};
    if (['researcher','researchers','profile','profiles','person'].includes(parts[0]) && parts[1]) location.replace(base + '/researchers/' + encodeURIComponent(aliases[parts[1]] || parts[1]) + '/');
    else if (['research','publications','gallery','activity','collaborators','funders','sources','pipeline'].includes(parts[0])) location.replace(base + '/' + parts[0] + '/');
  }
  const toggle = document.querySelector('.menu-toggle');
  toggle?.addEventListener('click', () => {const nav=document.getElementById('main-nav');const open=nav.classList.toggle('open');toggle.setAttribute('aria-expanded',String(open));});
  const input = document.querySelector('[data-filter]');
  input?.addEventListener('input',()=>{const q=input.value.trim().toLocaleLowerCase();document.querySelectorAll('[data-filter-grid]>.person-card').forEach(c=>c.hidden=!c.textContent.toLocaleLowerCase().includes(q));});
  document.querySelectorAll('[data-carousel]').forEach(carousel => {
    const slides=[...carousel.querySelectorAll('[data-slide]')],pause=carousel.querySelector('[data-carousel-pause]');let index=0,manual=carousel.dataset.autoplay!=='yes'||matchMedia('(prefers-reduced-motion: reduce)').matches,hover=false,focus=false;
    const show=n=>{index=(n+slides.length)%slides.length;slides.forEach((s,i)=>s.hidden=i!==index);carousel.querySelector('[data-carousel-count]').textContent=`${index+1} / ${slides.length}`;};
    const label=()=>{pause.textContent=manual?'Play':'Pause';pause.setAttribute('aria-pressed',String(manual));};label();
    pause.addEventListener('click',()=>{manual=!manual;label();});carousel.querySelector('[data-carousel-prev]').onclick=()=>show(index-1);carousel.querySelector('[data-carousel-next]').onclick=()=>show(index+1);
    carousel.addEventListener('mouseenter',()=>hover=true);carousel.addEventListener('mouseleave',()=>hover=false);carousel.addEventListener('focusin',()=>focus=true);carousel.addEventListener('focusout',e=>focus=carousel.contains(e.relatedTarget));
    setInterval(()=>{if(!manual&&!hover&&!focus&&!document.hidden&&slides.length>1)show(index+1);},15000);
  });
  document.querySelectorAll('[data-anonymous]').forEach(async form => {
    let token='';const status=form.querySelector('[role=status]');
    try {const r=await fetch('/api/anonymous/token',{cache:'no-store',credentials:'omit'});if(!r.ok)throw Error('Anonymous submission is currently unavailable.');token=(await r.json()).token;}catch(e){status.textContent=e.message;form.querySelector('button').disabled=true;}
    form.addEventListener('submit',async event=>{event.preventDefault();const button=form.querySelector('button');button.disabled=true;status.textContent='Submitting…';
      try{const fd=new FormData(form),payload={kind:form.dataset.anonymous,token,website:fd.get('website')||''};if(payload.kind==='question')payload.question=fd.get('question');else{payload.questionnaire_id=form.dataset.survey;payload.answers={};for(const [k,v]of fd)if(k.startsWith('q_'))payload.answers[k.slice(2)]=v;}
        const res=await fetch('/api/anonymous',{method:'POST',headers:{'Content-Type':'application/json'},credentials:'omit',body:JSON.stringify(payload)});const data=await res.json();if(!res.ok)throw Error(data.error||'Submission failed.');status.textContent=data.message;form.reset();
      }catch(e){status.textContent=e.message;}finally{button.disabled=false;}
    });
  });
})();
