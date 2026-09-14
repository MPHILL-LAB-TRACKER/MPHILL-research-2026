"""V6.2 Playwright interface and regression tests. In-memory fetch/image bridge to a real temporary PHP HTTP server.
Direct browser navigation is not exercised by this test. Dependencies: playwright, requests.
"""
from pathlib import Path
import os,sys,tempfile,subprocess,socket,time,shutil
import base64,json,re,requests,urllib.parse
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ.get('TED2_BROWSER_OUTPUT',str(ROOT/'test-results/browser-v62')));OUT.mkdir(parents=True,exist_ok=True)
TMP=tempfile.TemporaryDirectory(prefix='ted2-browser-')
with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
BASE=f'http://127.0.0.1:{port}'
env={**os.environ,'TED2_DB':str(Path(TMP.name)/'ted2.sqlite3'),'TED2_BASE_URL':BASE,'TED2_SQLITE_DRIVER':os.environ.get('TED2_TEST_DRIVER','native')}
subprocess.run(['php','bin/console.php','init'],cwd=ROOT,env=env,input='v6-test-owner\nStudioTesting!123\nStudioTesting!123\n',text=True,check=True,capture_output=True)
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
 browser=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH',shutil.which('chromium') or '/usr/bin/chromium'),args=['--no-sandbox']);ctx=browser.new_context(viewport={'width':1440,'height':1040});page=ctx.new_page();page.set_default_timeout(7000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.expose_function('__http',bridge);page.expose_function('__image',image_data)
 def load(path='/admin',is_admin=True):
  html=s.get(BASE+path).text;html=re.sub(r'<link[^>]+stylesheet[^>]*>','',html);html=re.sub(r'<script[^>]*>.*?</script>','',html,flags=re.S);page.set_content(html);page.add_style_tag(content=(ROOT/'public/assets/site.css').read_text());
  if is_admin:page.add_style_tag(content=(ROOT/'public/assets/admin.css').read_text())
  page.add_script_tag(content='(()=>{'+BRIDGE+'})();')
  page.add_script_tag(content='window.TED2_APPEARANCE={mode:"system",allow:true};')
  page.add_script_tag(content=(ROOT/'public/assets/experience.js').read_text());page.add_script_tag(content=(ROOT/('public/assets/admin.js' if is_admin else 'public/assets/site.js')).read_text());page.evaluate('window.__loadImages()');page.wait_for_timeout(150)
 def route(h):page.evaluate('(h)=>location.hash=h',h);page.wait_for_timeout(220)
 load();page.get_by_label('Username',exact=True).fill('v6-test-owner');page.get_by_label('Password',exact=True).fill('StudioTesting!123');page.get_by_role('button',name='Sign in',exact=True).click();page.wait_for_selector('.studio-shell')
 check(page.locator('.nav-section').count()==5,'Five focused admin navigation groups')
 page.locator('#nav-search').fill('quotations');check(page.locator('.nav-link:visible').count()==1,'Navigation search reveals hidden group and exact section');page.locator('#nav-search').fill('')
 check(page.locator('.photo-band img').count()==2,'Admin has photographic header and footer')
 page.get_by_label('Colour mode',exact=True).select_option('dark');check(page.locator('html').get_attribute('data-appearance')=='dark','Admin dark-mode control changes appearance')
 page.screenshot(path=str(OUT/'admin-dark.png'),full_page=False)
 page.get_by_label('Colour mode',exact=True).select_option('light');page.screenshot(path=str(OUT/'admin-overview.png'),full_page=False)
 route('theme');page.wait_for_selector('#record-form');check(page.locator('.photo-choice').count()==7,'Seven attributed photographic options including optional downloads')
 check(page.locator('[data-photo="lab-bench"]').count()==1,'Laboratory-supplied photograph is selectable')
 check(page.locator('[data-import-photo]').count()==2,'Optional glassware and fern imports are explicitly labelled')
 page.locator('#photo-target').select_option('footer');page.locator('[data-photo="launch"]').click();check(page.locator('#f-footer_art').input_value()=='launch','Image picker updates footer form value')
 page.get_by_role('button',name='Save changes',exact=True).click();page.wait_for_timeout(400)
 check(s.get(BASE+'/api/records/theme/website').json()['footer_art']=='launch','Photographic selection persists to database')
 page.locator('#photo-target').select_option('footer');page.locator('[data-photo="deep-field"]').click();page.get_by_role('button',name='Save changes',exact=True).click();page.wait_for_timeout(250)
 page.screenshot(path=str(OUT/'appearance-studio.png'),full_page=False)
 route('pulse');page.wait_for_selector('#pulse-check');check('source-headlines' not in page.locator('h1').inner_text(),'Reading desk opens with clear explanatory sections');check(page.get_by_role('link',name='Science quotations →').count()==1,'Quotes accessible from research-intelligence desk');page.screenshot(path=str(OUT/'research-pulse-admin.png'),full_page=False)
 route('performance');page.wait_for_selector('#clear-render-cache');page.locator('#clear-render-cache').click();page.wait_for_timeout(200);check('Private research' in page.locator('#toast').inner_text(),'Cache clear confirms no private files touched')
 route('edit/people/naungwe-simasiku');page.wait_for_selector('#portrait-drop');page.locator('#portrait-drop input[type=file]').set_input_files({'name':'Updated portrait.jpg','mimeType':'image/jpeg','buffer':(ROOT/'data/assets/portraits/naungwe-simasiku-v4.jpg').read_bytes()});page.wait_for_function("document.querySelector('input[name=photo_upload_id]')?.value.length>0");page.wait_for_timeout(200);check(bool(s.get(BASE+'/api/records/people/naungwe-simasiku').json()['photo_upload_id']),'Portrait replacement regression remains fixed')
 route('new/milestones');page.wait_for_selector('#record-form');check(not page.locator('#f-project_id').get_attribute('required'),'Milestone does not require project')
 route('tracking');check(page.locator('#tracking-person').count()==1,'Research resource tracker remains accessible')
 # Approve real, source-backed quotations in a temporary test database only.
 b=s.get(BASE+'/api/bootstrap').json();headers={'Origin':BASE,'X-CSRF-Token':b['user']['csrf']}
 quotes=b['records']['science_quotes'][:3]
 for q in quotes:
  q.update(visibility='public',approved=True,homepage=True);r=s.put(BASE+'/api/records/science_quotes/'+q['id'],json=q,headers=headers);check(r.status_code==200,'Reviewed quote is accepted')
 t=s.get(BASE+'/api/records/theme/website').json();t['quote_seconds']=5;t['home_blocks']=list(dict.fromkeys(t['home_blocks']+['quotes']));s.put(BASE+'/api/records/theme/website',json=t,headers=headers)
 load('/',False);check(page.locator('.photo-band-header img').count()==1,'Public photographic header rendered')
 check(page.locator('.nav-dropdown').count()==2,'Public navigation has grouped secondary links')
 page.locator('.nav-dropdown summary').first.click();check(page.locator('.nav-dropdown').first.get_attribute('open') is not None,'Grouped navigation opens without special routing');page.keyboard.press('Escape');check(page.locator('.nav-dropdown[open]').count()==0,'Escape closes navigation and restores focus')
 page.get_by_label('Colour mode',exact=True).select_option('dark');check(page.locator('html').get_attribute('data-appearance')=='dark','Public page dark mode works');page.screenshot(path=str(OUT/'homepage-dark.png'),full_page=False)
 page.get_by_label('Colour mode',exact=True).select_option('light');page.screenshot(path=str(OUT/'homepage-light.png'),full_page=False)
 check(page.locator('[data-quotes]').count()==1,'Approved quotation panel rendered')
 quotesPanel=page.locator('[data-quotes]');quotesPanel.scroll_into_view_if_needed();visible=quotesPanel.locator('[data-slide]:visible').inner_text();quotesPanel.locator('[data-carousel-next]').click();check(quotesPanel.locator('[data-slide]:visible').inner_text()!=visible,'Quotation rotation changes current card')
 check(quotesPanel.locator('.topic-tags').count()>0,'Quotations carry informative hashtags');page.screenshot(path=str(OUT/'science-quotations.png'),full_page=False)
 page.set_viewport_size({'width':390,'height':844});page.evaluate('window.scrollTo(0,0)');page.wait_for_timeout(200);check(page.evaluate('document.documentElement.scrollWidth <= window.innerWidth+1'),'Mobile homepage has no horizontal overflow')
 page.locator('.menu-toggle').click();check(page.locator('#main-nav').is_visible(),'Mobile menu opens');page.locator('.menu-toggle').click();page.screenshot(path=str(OUT/'homepage-mobile.png'),full_page=False)
 page.emulate_media(reduced_motion='reduce');load('/',False);check(page.locator('[data-quotes] [data-carousel-pause]').inner_text()=='Play','Reduced motion disables quotation autoplay')
 page.set_viewport_size({'width':390,'height':844});load('/admin',True);page.wait_for_selector('.studio-shell');check(page.evaluate('document.documentElement.scrollWidth <= window.innerWidth+1'),'Mobile admin has no horizontal overflow');page.locator('.studio-mobile-menu').click();check(page.locator('.sidebar').is_visible(),'Mobile administration navigation opens')
 check(not errors,'No uncaught JavaScript errors: '+str(errors));(OUT/'results.json').write_text(json.dumps({'checks':len(checks),'passed':checks,'errors':errors,'transport':'in-memory fetch bridge to real PHP server; not physical device or live deployment'},indent=2));browser.close()
print(f'{len(checks)} browser checks passed.')
