"""Optional Playwright rendering tests. In-memory fetch/image bridge to a real temporary PHP HTTP server.
Direct browser navigation is not exercised by this test. Dependencies: playwright, requests.
"""
from pathlib import Path
import os,sys,tempfile,subprocess,socket,time,shutil
import base64,json,re,requests,urllib.parse
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ.get('TED2_BROWSER_OUTPUT',str(ROOT/'test-results/browser')));OUT.mkdir(parents=True,exist_ok=True)
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
 browser=pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH',shutil.which('chromium') or '/usr/bin/chromium'),args=['--no-sandbox']);ctx=browser.new_context(viewport={'width':1440,'height':1000});page=ctx.new_page();page.set_default_timeout(5000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.expose_function('__http',bridge);page.expose_function('__image',image_data)
 def admin():
  html=s.get(BASE+'/admin').text;html=re.sub(r'<link[^>]+stylesheet[^>]*>','',html);html=re.sub(r'<script[^>]*>.*?</script>','',html,flags=re.S);page.set_content(html);page.add_style_tag(content=(ROOT/'public/assets/site.css').read_text());page.add_style_tag(content=(ROOT/'public/assets/admin.css').read_text());page.add_script_tag(content=BRIDGE);page.add_script_tag(content=(ROOT/'public/assets/admin.js').read_text())
 admin();page.get_by_label('Username',exact=True).fill('v6-test-owner');page.get_by_label('Password',exact=True).fill('StudioTesting!123');page.get_by_role('button',name='Sign in',exact=True).click();page.wait_for_selector('.studio-shell');check('at a glance' in page.locator('h1').inner_text(),'Sign-in and dashboard');page.screenshot(path=str(OUT/'admin-overview.png'),full_page=True)
 def route(h):page.evaluate('(h)=>location.hash=h',h);page.wait_for_timeout(150)
 route('theme');page.wait_for_selector('#record-form');check(page.get_by_role('button',name='Modern',exact=True).count()==1,'Modern theme preset visible');check(page.get_by_label('Header decoration',exact=True).count()==1 if page.get_by_label('Header decoration',exact=True).count() else page.locator('#f-header_band').count()==1,'Header-only style control');page.screenshot(path=str(OUT/'admin-theme.png'),full_page=True)
 page.get_by_role('button',name='Modern',exact=True).click();page.get_by_role('button',name='Save changes',exact=True).click();page.wait_for_timeout(400);check(page.locator('body').get_attribute('data-theme')=='modern','Saved theme affects admin');check('data-theme="modern"' in s.get(BASE+'/').text,'Saved theme affects public page');page.get_by_role('button',name='Vintage',exact=True).click();page.get_by_role('button',name='Save changes',exact=True).click();page.wait_for_timeout(300)
 route('new/milestones');page.wait_for_selector('#record-form');check(not page.locator('#f-project_id').get_attribute('required'),'Milestone project selector optional');page.locator('#f-title').fill('Browser test milestone');page.locator('#f-researcher_id').select_option('paulus-hamutenya');page.locator('#f-status').select_option('todo');page.get_by_role('button',name='Save changes',exact=True).click();page.wait_for_timeout(300);check('edit/milestones/' in page.evaluate('location.hash'),'Milestone saved without project')
 route('media');page.get_by_role('button',name='Upload files',exact=True).click();page.wait_for_selector('dialog[open]');page.locator('#batch-owner').select_option('paulus-hamutenya');page.locator('#batch-approve').check();page.locator('#batch-files').set_input_files({'name':'Example laboratory.png','mimeType':'image/png','buffer':(ROOT/'data/branding/ted2-icon.png').read_bytes()});page.wait_for_function("document.querySelector('#batch-results')?.textContent.includes('saved public')");page.get_by_role('button',name='Done',exact=True).click();page.wait_for_timeout(350);check(page.locator('.library-card').count()==1,'Browse upload creates one scoped media card');page.screenshot(path=str(OUT/'admin-media.png'),full_page=True)
 page.get_by_role('link',name='Edit & rename',exact=True).click();page.wait_for_selector('#record-form');page.locator('#f-caption').fill('A separately editable caption.\n\nSecond paragraph.');page.locator('#f-display_filename').fill('Research-note-cover.png');page.get_by_role('button',name='Save changes',exact=True).click();page.wait_for_timeout(300);check(page.locator('#f-caption').input_value().startswith('A separately'),'Caption and public filename edited')
 route('edit/people/paulus-hamutenya');page.wait_for_selector('#record-form');select=page.locator('[data-add-to="media_items"]');check(select.locator('option').count()==2,'Profile picker includes only its own upload');select.select_option(index=1);page.get_by_role('button',name='Save changes',exact=True).click();page.wait_for_timeout(300);check(page.locator('[data-ordered="media_items"] .ordered-item').count()==1,'Profile media ordering control');
 route('edit/people/naungwe-simasiku');page.wait_for_selector('#record-form');check(page.locator('[data-add-to="media_items"] option').count()==1,'Other profile cannot pick another researcher upload');
 route('accounts');page.wait_for_selector('#new-account');check(page.get_by_role('button',name='Edit rights').count()>=1,'Owner can manage researcher permissions');
 route('publish');page.wait_for_selector('#prepare-publish');check(page.locator('input[type=password]').count()==0,'Publishing does not ask for a second password');check(page.get_by_role('button',name='Configure Pages',exact=True).count()==1,'Pages configuration action available');page.screenshot(path=str(OUT/'admin-publish.png'),full_page=True)
 route('dashboard');page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(100);check(page.locator('.studio-mobile-menu').is_visible(),'Mobile admin navigation');page.get_by_role('button',name='Open navigation',exact=True).click();check(page.locator('.sidebar').is_visible(),'Mobile sidebar opens');page.get_by_role('button',name='Open navigation',exact=True).click();check(page.evaluate('document.documentElement.scrollWidth<=innerWidth'),'Admin no horizontal overflow at 390px');page.screenshot(path=str(OUT/'admin-mobile.png'),full_page=True)
 # Public renderer: bytes come from the actual PHP HTTP server, assets are inlined because direct browser network is blocked by environment policy.
 page.set_viewport_size({'width':1440,'height':1000});html=s.get(BASE+'/').text;html=re.sub(r'<link[^>]+stylesheet[^>]*>','',html);html=re.sub(r'<script[^>]*src=[^>]*>.*?</script>','',html,flags=re.S)
 def src_replace(m):return 'src="'+image_data(m.group(1))+'"'
 html=re.sub(r'src="(/[^\"]+)"',src_replace,html);page.set_content(html);page.add_style_tag(content=(ROOT/'public/assets/site.css').read_text());page.add_script_tag(content=(ROOT/'public/assets/site.js').read_text());page.wait_for_timeout(150);check(page.locator('.person-card').count()==12,'Twelve profiles rendered');check(page.locator('[data-carousel]').count()==1,'Rotating homepage notice board');page.get_by_role('button',name='Next notice',exact=True).click();check(page.locator('[data-carousel-count]').inner_text().startswith('2 /'),'Notice next control works');check(page.locator('[data-slide]:visible').count()==1,'Only one notice displayed');page.get_by_role('button',name='Pause',exact=True).click();check(page.get_by_role('button',name='Play',exact=True).count()==1,'Carousel can be paused');page.screenshot(path=str(OUT/'home-desktop.png'),full_page=True)
 page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(100);check(page.evaluate('document.documentElement.scrollWidth<=innerWidth'),'Public page no horizontal overflow at 390px');check(page.get_by_role('button',name='Menu',exact=True).is_visible(),'Mobile public navigation');page.get_by_role('button',name='Menu',exact=True).click();check(page.locator('#main-nav').is_visible(),'Mobile menu opens');page.get_by_role('button',name='Menu',exact=True).click();page.screenshot(path=str(OUT/'home-mobile.png'),full_page=True)
 check(not errors,'No browser script exceptions: '+repr(errors));browser.close()
OUT.joinpath('browser-tests.json').write_text(json.dumps({'transport':'In-memory browser bridge to real local PHP HTTP server. Direct browser navigation was blocked by environment policy.','passed':len(checks),'checks':checks,'page_errors':errors},indent=2))
print(len(checks),'browser interface checks passed')
