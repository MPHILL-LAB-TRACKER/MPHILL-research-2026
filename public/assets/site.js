/* TED² 6.1 progressive enhancements; the page remains readable without this file. */
'use strict';
(() => {
 document.documentElement.classList.add('js');
 const base=document.body.dataset.base||'', reduced=()=>window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;
 if(location.hash.startsWith('#/')){
  const parts=location.hash.slice(2).split('?')[0].split('/'),aliases={'jaydine-jeris':'jaydine-feris','denise-bouman':'denis-bouman','maneria-halweendo':'manelia-halweendo','charity-maepa':'charity-mepa','nonku-phili':'nonku-phiri'};
  if(['researcher','researchers','profile','profiles','person'].includes(parts[0])&&parts[1])location.replace(base+'/researchers/'+encodeURIComponent(aliases[parts[1]]||parts[1])+'/');
  else if(['research','publications','gallery','activity','collaborators','funders','sources','pipeline','procurement','discoveries'].includes(parts[0]))location.replace(base+'/'+parts[0]+'/');
 }
 const toggle=document.querySelector('.menu-toggle');if(toggle)toggle.addEventListener('click',()=>{const nav=document.getElementById('main-nav'),open=nav.classList.toggle('open');toggle.setAttribute('aria-expanded',String(open));});
 const filter=document.querySelector('[data-filter]');if(filter)filter.addEventListener('input',()=>{const q=filter.value.trim().toLocaleLowerCase();document.querySelectorAll('[data-filter-grid]>.person-card').forEach(c=>c.hidden=!c.textContent.toLocaleLowerCase().includes(q));});
 document.querySelectorAll('[data-carousel]').forEach(carousel=>{
  const slides=[...carousel.querySelectorAll('[data-slide]')],pause=carousel.querySelector('[data-carousel-pause]'),count=carousel.querySelector('[data-carousel-count]');if(!slides.length||!pause)return;
  let index=0,manual=carousel.dataset.autoplay!=='yes'||reduced(),hover=false,focus=false;const isQuotes=carousel.hasAttribute('data-quotes'),isFacts=carousel.hasAttribute('data-facts')||isQuotes;const storageKey=isQuotes?'ted2-reviewed-quotes':'ted2-reviewed-facts';if(isQuotes&&carousel.dataset.random==='yes'){for(let i=slides.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[slides[i],slides[j]]=[slides[j],slides[i]];}slides.forEach(s=>s.dataset.factId=s.dataset.quoteId);}let seen=[];
  if(isFacts){try{seen=JSON.parse(sessionStorage.getItem(storageKey)||'[]');if(!Array.isArray(seen))seen=[];}catch{seen=[];}const i=slides.findIndex(s=>!seen.includes(s.dataset.factId));index=i<0?0:i;}
  const remember=()=>{if(!isFacts)return;const id=slides[index].dataset.factId;if(slides.every(s=>seen.includes(s.dataset.factId)))seen=[];if(id&&!seen.includes(id))seen.push(id);try{sessionStorage.setItem(storageKey,JSON.stringify(seen.slice(-100)));}catch{/* Storage may be blocked; in-page rotation still works. */}};
  const show=n=>{index=(n+slides.length)%slides.length;slides.forEach((s,i)=>{s.hidden=i!==index;s.classList.remove('slide-enter');});const current=slides[index];if(!reduced()){void current.offsetWidth;current.classList.add('slide-enter');}if(count)count.textContent=`${index+1} / ${slides.length}`;remember();};
  const label=()=>{pause.textContent=manual?'Play':'Pause';pause.setAttribute('aria-pressed',String(manual));};show(index);label();
  pause.addEventListener('click',()=>{manual=!manual;label();});carousel.querySelector('[data-carousel-prev]').onclick=()=>show(index-1);carousel.querySelector('[data-carousel-next]').onclick=()=>show(index+1);
  carousel.addEventListener('mouseenter',()=>hover=true);carousel.addEventListener('mouseleave',()=>hover=false);carousel.addEventListener('focusin',()=>focus=true);carousel.addEventListener('focusout',e=>focus=carousel.contains(e.relatedTarget));
  const seconds=Math.max(3,Math.min(120,Number(carousel.dataset.seconds)||5));carousel.dataset.activeInterval=String(seconds);
  setInterval(()=>{if(!manual&&!hover&&!focus&&!document.hidden&&slides.length>1)show(index+1);},seconds*1000);
 });
 document.querySelectorAll('[data-anonymous]').forEach(async form=>{
  const status=form.querySelector('[role=status]'),submit=form.querySelector('[type=submit]'),steps=[...form.querySelectorAll('[data-question-step]')],next=form.querySelector('[data-step-next]'),back=form.querySelector('[data-step-back]');let step=0,token='';
  const wizard=form.dataset.wizard==='yes'&&steps.length>0;
  const draw=()=>{if(!wizard)return;steps.forEach((s,i)=>s.hidden=i!==step);next.hidden=step>=steps.length-1;back.hidden=step===0;submit.hidden=step<steps.length-1;const count=form.querySelector('[data-step-count]'),progress=form.querySelector('[data-step-progress]');count.textContent=`Question ${step+1} of ${steps.length}`;progress.value=step+1;};
  const valid=index=>{for(const input of steps[index].querySelectorAll('input,textarea,select'))if(!input.checkValidity()){step=index;draw();input.reportValidity();return false;}return true;};
  if(wizard){form.noValidate=true;draw();next.onclick=()=>{if(valid(step)){step++;draw();steps[step].querySelector('input,textarea,select')?.focus();}};back.onclick=()=>{step=Math.max(0,step-1);draw();};}
  try{const r=await fetch('/api/anonymous/token',{cache:'no-store',credentials:'omit'});if(!r.ok)throw Error('Anonymous submission is currently unavailable.');token=(await r.json()).token;}catch(e){status.textContent=e.message;submit.disabled=true;}
  form.addEventListener('submit',async event=>{event.preventDefault();if(wizard&&!steps.every((_,i)=>valid(i)))return;submit.disabled=true;status.textContent='Submitting…';
   try{const fd=new FormData(form),payload={kind:form.dataset.anonymous,token,website:fd.get('website')||''};if(payload.kind==='question')payload.question=fd.get('question');else{payload.questionnaire_id=form.dataset.survey;payload.answers={};for(const[k,v]of fd)if(k.startsWith('q_'))payload.answers[k.slice(2)]=v;}
    const res=await fetch('/api/anonymous',{method:'POST',headers:{'Content-Type':'application/json'},credentials:'omit',body:JSON.stringify(payload)}),data=await res.json();if(!res.ok)throw Error(data.error||'Submission failed.');status.textContent=data.message;form.reset();if(wizard){step=0;draw();}const fresh=await fetch('/api/anonymous/token',{cache:'no-store',credentials:'omit'});if(fresh.ok)token=(await fresh.json()).token;
   }catch(e){status.textContent=e.message;}finally{submit.disabled=false;}
  });
 });
})();
