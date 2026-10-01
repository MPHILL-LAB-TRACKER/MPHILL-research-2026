"""V7 Playwright interface and regression tests. In-memory fetch/image bridge to a real temporary PHP HTTP server.
Direct browser navigation is not exercised by this test. Dependencies: playwright, requests.
"""
from pathlib import Path
import os,sys,tempfile,subprocess,socket,time,shutil
import base64,json,re,requests,urllib.parse
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ.get('TED2_BROWSER_OUTPUT',str(ROOT/'test-results/browser-v7')));OUT.mkdir(parents=True,exist_ok=True)
TMP=tempfile.TemporaryDirectory(prefix='ted2-browser-')
with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
BASE=f'http://127.0.0.1:{port}'
env={**os.environ,'TED2_DB':str(Path(TMP.name)/'ted2.sqlite3'),'TED2_BASE_URL':BASE,'TED2_SQLITE_DRIVER':os.environ.get('TED2_TEST_DRIVER','native')}
subprocess.run(['php','bin/console.php','init'],cwd=ROOT,env=env,input='studio-preview\nStudioTesting!123\nStudioTesting!123\n',text=True,check=True,capture_output=True)
log=open(Path(TMP.name)/'server.log','w')
server=subprocess.Popen(['php','-S',f'127.0.0.1:{port}','-t','public','public/router.php'],cwd=ROOT,env=env,stdout=log,stderr=log)
import atexit
@atexit.register
def cleanup():
 server.terminate();server.wait(timeout=10);log.close();TMP.cleanup()
for _ in range(50):
 try:requests.get(BASE+'/admin',timeout=.3);break
 except requests.RequestException:time.sleep(.1)

s=requests.Session();checks=[]
def check(cond,label):
 if not cond:raise AssertionError(label)
 checks.append(label); print('PASS',label)
def bridge(q):
 url=q['url'];path=urllib.parse.urlsplit(url).path if '://' in url else url
 headers=q.get('headers',{});headers['Origin']=BASE
 if q.get('multipart') is not None:
  files={};data={}
  for part in q['multipart']:
   if part.get('file'):files[part['key']]=(part['name'],base64.b64decode(part['data']),part['type'])
   else:data[part['key']]=part['value']
  r=s.request(q.get('method','GET'),BASE+path,headers=headers,data=data,files=files)
 else:r=s.request(q.get('method','GET'),BASE+path,headers=headers,data=q.get('body'))
 return {'status':r.status_code,'body':base64.b64encode(r.content).decode(),'headers':dict(r.headers)}
def image_data(path):
 try:
  r=s.get(BASE+path);return 'data:'+r.headers.get('Content-Type','image/png')+';base64,'+base64.b64encode(r.content).decode() if r.status_code==200 else ''
 except:return ''
BRIDGE="""window.fetch=async (url,options={})=>{const q={url:String(url),method:options.method||'GET',headers:options.headers||{},body:options.body};if(options.body instanceof FormData){q.body=null;q.multipart=[];for(const [key,value] of options.body.entries()){if(value instanceof File){const bytes=new Uint8Array(await value.arrayBuffer());let binary='';for(const x of bytes)binary+=String.fromCharCode(x);q.multipart.push({key,file:true,name:value.name,type:value.type,data:btoa(binary)});}else q.multipart.push({key,value});}}const r=await window.__http(q);return new Response(Uint8Array.from(atob(r.body),c=>c.charCodeAt(0)),{status:r.status,headers:r.headers});};
const loadImages=()=>document.querySelectorAll('img[src^="/"]').forEach(async img=>{const url=img.getAttribute('src');img.removeAttribute('src');const data=await window.__image(url);if(data)img.src=data;});new MutationObserver(loadImages).observe(document.documentElement,{subtree:true,childList:true});window.__loadImages=loadImages;
"""
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH',shutil.which('chromium') or '/usr/bin/chromium'),args=['--no-sandbox']);ctx=browser.new_context(viewport={'width':1440,'height':1040});page=None;errors=[]
 def load(path='/admin',is_admin=True):
  global page
  if page:page.close()
  page=ctx.new_page();page.set_default_timeout(8000);page.on('pageerror',lambda e:errors.append(str(e)));page.expose_function('__http',bridge);page.expose_function('__image',image_data)
  html=s.get(BASE+path).text;styles=re.findall(r'<style[^>]*>(.*?)</style>',html,re.S);html=re.sub(r'<link[^>]+stylesheet[^>]*>','',html);html=re.sub(r'<script[^>]*>.*?</script>','',html,flags=re.S);page.set_content(html)
  page.add_style_tag(content=(ROOT/'public/assets/site.css').read_text())
  if is_admin:page.add_style_tag(content=(ROOT/'public/assets/admin.css').read_text())
  for st in styles:page.add_style_tag(content=st)
  page.add_style_tag(content=(ROOT/'public/assets/v7.css').read_text())
  page.add_script_tag(content='(()=>{'+BRIDGE+'})();');page.add_script_tag(content='window.TED2_APPEARANCE={mode:"system",allow:true};')
  page.add_script_tag(content=(ROOT/'public/assets/experience.js').read_text())
  if not is_admin:page.add_script_tag(content=(ROOT/'public/assets/v7.js').read_text())
  page.add_script_tag(content=(ROOT/('public/assets/admin.js' if is_admin else 'public/assets/site.js')).read_text())
  page.evaluate('window.__loadImages()');page.wait_for_timeout(180)
 def route(h):page.evaluate('(h)=>location.hash=h',h);page.wait_for_timeout(250)
 def req(path,method='GET',data=None):
  h={'Origin':BASE,'X-CSRF-Token':s.get(BASE+'/api/bootstrap').json()['user']['csrf']}
  rr=s.request(method,BASE+path,headers=h,json=data);assert rr.status_code<300,(rr.status_code,rr.text);return rr.json()
 def new(c,**kw):
  p={'id':'browser-'+str(time.time_ns()),'visibility':'private'}
  for f in s.get(BASE+'/api/bootstrap').json()['schemas'][c]['fields']:
   t=f['type'];p[f['key']]=f.get('default',[] if t in ['multi','lines','urls','multi-choice'] else False if t=='checkbox' else None if t in ['number','year','weight','percent','money'] else '')
   if t=='select' and f['required'] and not p[f['key']]:p[f['key']]=f['options'][0]
  p.update(kw);return req('/api/records/'+c,'POST',p)
 load();page.get_by_label('Username',exact=True).fill('studio-preview');page.get_by_label('Password',exact=True).fill('StudioTesting!123');page.get_by_role('button',name='Sign in',exact=True).click();page.wait_for_selector('.studio-shell')
 check(page.locator('.v7-desk-banner').count()==1,'V7 research desk loads after existing owner login')
 check(page.locator('a[href="#writing_projects"]').count()>=1,'Writing desk is reachable from navigation and shortcuts')
 check(page.locator('a[href="#inbox"]').count()>=1,'Visitor inbox is linked in admin navigation')
 page.locator('#nav-search').fill('writing');check(page.locator('.nav-link:visible').count()>=1,'Navigation search finds private writing');page.locator('#nav-search').fill('')
 page.get_by_label('Colour mode',exact=True).select_option('dark');check(page.locator('html').get_attribute('data-appearance')=='dark','Admin dark mode works');page.screenshot(path=str(OUT/'admin-dark.png'),full_page=False)
 page.get_by_label('Colour mode',exact=True).select_option('light');page.screenshot(path=str(OUT/'admin-desk.png'),full_page=False)
 route('theme');page.wait_for_selector('#record-form');check(page.locator('#f-v7_style').count()==1,'Biomedical composition is an editable theme setting')
 check(page.locator('#f-v7_style option').evaluate_all('(opts)=>opts.filter(o=>o.value).length')==4,'Four distinct V7 structural compositions')
 page.get_by_text('Page borders & structure',exact=True).click();page.locator('#f-v7_style').select_option('atlas');page.get_by_role('button',name='Save changes',exact=True).click();page.wait_for_timeout(300);check(s.get(BASE+'/api/records/theme/website').json()['v7_style']=='atlas','Composition saves to actual database')
 page.get_by_text('Page borders & structure',exact=True).click();page.locator('#f-v7_style').select_option('biomedical');page.get_by_role('button',name='Save changes',exact=True).click();page.wait_for_timeout(300);page.screenshot(path=str(OUT/'theme-studio.png'),full_page=False)
 route('new/writing_projects');page.wait_for_selector('#writing-template');check(page.locator('#f-researcher_id').count()==1,'Private manuscript must belong to a researcher')
 page.locator('#f-title').fill('Evidence-led manuscript draft');page.locator('#f-researcher_id').select_option('paulus-hamutenya');page.locator('#insert-template').click();page.wait_for_timeout(180);check('\\documentclass' in page.locator('#f-main_tex').input_value(),'Template inserts actual LaTeX source')
 check(not page.locator('#f-project_id').get_attribute('required'),'Writing can start without a project list')
 page.get_by_role('button',name='Save changes',exact=True).click();page.wait_for_timeout(400);check(page.locator('#send-overleaf').count()==1,'Saving enables the Overleaf handoff')
 p=s.get(BASE+'/api/records/writing_projects').json()[0];check(p['visibility']=='private','Writing stays private after browser save')
 export=s.get(BASE+'/api/writing/'+p['id']+'/export');check(export.status_code==200 and export.content[:2]==b'PK','ZIP download returns an actual archive')
 page.screenshot(path=str(OUT/'writing-desk.png'),full_page=False)
 page.locator('#send-overleaf').click();page.get_by_role('button',name='Transfer saved source',exact=True).click();page.wait_for_timeout(300)
 check(page.locator('form[action="https://www.overleaf.com/docs"]').count()==1,'Official Overleaf transfer form appears only after consent')
 check(page.locator('input[name=snip_uri]').input_value().startswith('data:application/zip;base64,'),'Overleaf receives a ZIP payload, not a public draft URL')
 check(page.locator('input[name=main_document]').input_value()=='main.tex','Overleaf main document is explicitly selected');page.get_by_role('button',name='Close',exact=True).click()
 route('new/bench_notes');check(page.locator('.v7-privacy-banner').count()==1,'Bench notebook has explicit private boundary')
 check(page.locator('#f-visibility').count()==0 or page.locator('[name=visibility]').is_disabled(),'Private notebook visibility cannot be made public')
 check(page.locator('#f-observations').count()==1 and page.locator('#f-interpretation').count()==1,'Observation and interpretation have separate fields')
 route('new/albums');page.locator('#f-title').fill('Methods in focus');page.locator('#f-scope').select_option('researcher');page.locator('#f-researcher_id').select_option('paulus-hamutenya');page.locator('[name=visibility]').select_option('public');page.get_by_role('button',name='Save changes',exact=True).click();page.wait_for_timeout(300)
 albums=s.get(BASE+'/api/records/albums').json();a=next(p for p in albums if p['title']=='Methods in focus');check(a['researcher_id']=='paulus-hamutenya','Named album persists with its owner')
 route('albums');check(page.locator('a[href="#media/album/'+a['id']+'"]').count()==1,'Album opens its own file collection');page.screenshot(path=str(OUT/'admin-collections.png'),full_page=False)
 route('media/album/'+a['id']);check(page.locator('#media-owner').count()==1,'Album media view retains owner filtering')
 route('new/milestones');check(not page.locator('#f-project_id').get_attribute('required'),'Project-free milestone editing remains supported')
 route('edit/people/naungwe-simasiku');page.wait_for_selector('#portrait-drop');check(page.locator('#portrait-drop input[type=file]').count()==1,'Portrait uploader remains directly available')
 # Controlled fixture to show future/elapsed behavior; never exported with the package.
 ann=new('announcements',title='A future laboratory seminar',description='Temporary browser-test fixture.',kind='seminar',date_status='lab-supplied',start_date='2099-01-01',end_date='2099-01-02',homepage=True,visibility='public')
 load('/',False);check(page.locator('.v7-hero').count()==1,'Public biomedical hero is server rendered')
 check(page.locator('[data-slide][data-expiry="2099-01-02"]').count()==1,'Active seminar appears in notice board')
 page.locator('[data-slide][data-expiry="2099-01-02"]').evaluate('(e)=>e.dataset.expiry="2000-01-01"');page.locator('.v7-notice [data-carousel-next]').click();check(page.locator('[data-slide][data-expiry="2000-01-01"]').count()==0,'Expired snapshot notice is removed without republication')
 check(page.locator('[data-quotes] [data-slide]').count()>=32,'Public reflection pool has at least thirty-two options')
 panel=page.locator('[data-quotes]');one=panel.locator('[data-slide]:visible').inner_text();panel.locator('[data-carousel-next]').click();check(panel.locator('[data-slide]:visible').inner_text()!=one,'Quote next control rotates to a different reflection')
 check(page.locator('.v7-resource-grid a').count()>0,'Open-science resource shelf is reachable')
 page.evaluate("scrollTo({top:0,behavior:'instant'})");page.wait_for_timeout(400);page.screenshot(path=str(OUT/'homepage-light.png'),full_page=False)
 page.get_by_label('Colour mode',exact=True).select_option('dark');check(page.locator('html').get_attribute('data-appearance')=='dark','Public dark mode follows visitor choice');page.screenshot(path=str(OUT/'homepage-dark.png'),full_page=False)
 page.get_by_label('Colour mode',exact=True).select_option('light');page.set_viewport_size({'width':390,'height':844});page.evaluate("scrollTo({top:0,behavior:'instant'})");page.wait_for_timeout(400);check(page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),'Mobile home fits without horizontal scroll');page.locator('.menu-toggle').click();check(page.locator('#main-nav').is_visible(),'Touch-sized mobile menu opens');page.locator('.menu-toggle').click();page.screenshot(path=str(OUT/'homepage-mobile.png'),full_page=False)
 page.set_viewport_size({'width':1440,'height':1040});load('/gallery/',False);check(page.locator('a[href="/gallery/researchers/paulus-hamutenya/"]').count()==1,'Gallery has researcher folder rather than mixed linear feed');page.screenshot(path=str(OUT/'public-collections.png'),full_page=False)
 load('/connect/',False);check(page.locator('[data-message]').count()==1,'Anonymous visitor form is available on PHP-hosted page')
 page.locator('[name=subject]').fill('A question from a visitor');page.locator('[name=message]').fill('How does the laboratory review a proposed collaboration?');page.wait_for_function('!document.querySelector("[data-message] button[type=submit]").disabled');page.locator('[data-message] button[type=submit]').click();page.wait_for_selector('[aria-label="Your private response key"]');key=page.get_by_label('Your private response key',exact=True).input_value();check(bool(re.fullmatch(r'[a-f0-9]{32}\.[a-f0-9]{48}',key)),'Anonymous browser submission returns a private reply key')
 check('localStorage' not in (ROOT/'public/assets/v7.js').read_text(),'Reply keys are not persisted in browser localStorage');page.screenshot(path=str(OUT/'visitor-response.png'),full_page=False)
 load('/admin',True);page.wait_for_selector('.studio-shell');route('inbox');page.wait_for_selector('[data-message-id]');check('A question from a visitor' in page.locator('#inbox-messages').inner_text(),'Message arrives in real private admin inbox')
 item=page.locator('[data-message-id]').first;item.locator('textarea[name=reply]').fill('Thank you. Please use the published institutional contact for a formal introduction.');item.locator('select[name=status]').select_option('answered');item.locator('[data-save-reply]').click();page.wait_for_timeout(250);check('Saved' in item.locator('[role=status]').inner_text() or 'saved' in item.locator('[role=status]').inner_text(),'Admin reply saves from UI');page.screenshot(path=str(OUT/'visitor-inbox.png'),full_page=False)
 load('/connect/',False);page.get_by_text('Check a reply',exact=True).click();page.locator('[data-response-lookup] [name=key]').fill(key);page.locator('[data-response-lookup] button[type=submit]').click();page.wait_for_function('document.querySelector("[data-reply]").textContent.includes("formal introduction")');check('formal introduction' in page.locator('[data-reply]').inner_text(),'Visitor reads admin answer without an account')
 page.set_viewport_size({'width':390,'height':844});check(page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),'Mobile response form fits without horizontal overflow')
 load('/admin',True);page.wait_for_selector('.studio-shell');page.set_viewport_size({'width':390,'height':844});check(page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),'Mobile admin fits without horizontal overflow');page.locator('.studio-mobile-menu').click();check(page.locator('.sidebar').is_visible(),'Mobile admin menu remains reachable')
 check(not errors,'No uncaught JavaScript errors: '+str(errors));(OUT/'results.json').write_text(json.dumps({'checks':len(checks),'passed':checks,'errors':errors,'transport':'In-memory fetch/image bridge to a real isolated PHP server; not live navigation or physical device.'},indent=2));browser.close()
print(f'{len(checks)} browser checks passed.')
