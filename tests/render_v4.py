#!/usr/bin/env python3
"""V4 UI checks through explicit TestClient transport; never contacts GitHub."""
from __future__ import annotations
import argparse,base64,io,json,re,shutil,subprocess,sys,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PIL import Image
from playwright.sync_api import sync_playwright
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.db import ROOT
from backend.build import image_data
from backend.publisher import Publisher
from manage import create_owner
PASSWORD='Temporary UI checks password 2026!'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=Path('test-results/v4-ui'));args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    checks=[];errors=[]
    def check(name,ok=True):
        if not ok:raise AssertionError(name)
        checks.append(name)
    with tempfile.TemporaryDirectory(prefix='ted2-v4-browser-') as tmp:
        tmp=Path(tmp);app=create_app(tmp/'runtime/database.sqlite3',base_url='http://testserver',production=False);app.state.store.seed();create_owner(app.state.store,'test-owner',PASSWORD);client=TestClient(app)
        repo=tmp/'clone';repo.mkdir();remote=tmp/'remote.git'
        def git(*args):return subprocess.run(['git','-C',str(repo),*args],check=True,capture_output=True,text=True).stdout.strip()
        subprocess.run(['git','init','--bare',str(remote)],check=True,capture_output=True)
        git('init','-b','main');git('config','user.name','UI test');git('config','user.email','ui@example.invalid');(repo/'source.txt').write_text('original');git('add','source.txt');git('commit','-m','Temporary test');git('remote','add','origin',str(remote));head=git('rev-parse','HEAD')
        app.state.publisher=Publisher(app.state.store,app.state.uploads,repo,allow_local_remote=True)
        client.post('/api/login',headers={'Origin':'http://testserver'},json={'username':'test-owner','password':PASSWORD})
        def transport(url,method,headers,body):
            if not url.startswith('/api/'):raise ValueError('Only local test API URLs are allowed.')
            if method not in ('GET','HEAD'):headers['Origin']='http://testserver'
            if isinstance(body,dict) and body.get('multipart'):
                files=[(x['key'],(x['name'],base64.b64decode(x['data']),x['type'])) for x in body['files']]
                response=client.request(method,url,headers=headers,files=files)
            else:response=client.request(method,url,headers=headers,content=body)
            return {'status':response.status_code,'body':response.text,'headers':dict(response.headers)}
        adapter=r'''async function serialise(body){if(!(body instanceof FormData))return body||null;let files=[];for(const [key,file] of body){let b=new Uint8Array(await file.arrayBuffer()),s='';for(const x of b)s+=String.fromCharCode(x);files.push({key,name:file.name,type:file.type,data:btoa(s)});}return {multipart:true,files};}
window.fetch=async function(url,init={}){let r=await window.__API(String(url),init.method||'GET',Object.fromEntries(new Headers(init.headers||{})),await serialise(init.body));return new Response(r.body,{status:r.status,headers:r.headers});};
window.XMLHttpRequest=class {constructor(){this.upload={};this.headers={};}open(method,url){this.method=method;this.url=url;}setRequestHeader(k,v){this.headers[k]=v;}async send(body){try{const r=await window.__API(this.url,this.method,this.headers,await serialise(body));this.status=r.status;this.responseText=r.body;this.upload.onprogress?.({lengthComputable:true,loaded:1,total:1});this.onload?.();}catch(e){this.onerror?.(e);}}};'''
        js=(ROOT/'web/assets/admin.js').read_text().replace('/images/ted2-wordmark.png',image_data('ted2-wordmark.png'))
        js=re.sub(r"location\.href\s*=\s*['\"]/login['\"]", "window.__NAV='/login'",js)
        html=(ROOT/'web/admin.html').read_text().replace('<link rel="stylesheet" href="/assets/admin.css">','<style>'+(ROOT/'web/assets/admin.css').read_text()+'</style>').replace('<script src="/assets/admin.js" defer></script>','<script>'+adapter+'</script><script>'+js+'</script>')
        image=io.BytesIO();Image.new('RGB',(120,80)).save(image,'PNG');blob=image.getvalue()
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=shutil.which('chromium') or None,headless=True,args=['--no-sandbox']);context=browser.new_context(viewport={'width':1440,'height':1050});context.route('**/*',lambda r:r.abort());page=context.new_page();page.on('dialog',lambda dialog:dialog.accept());page.expose_function('__API',transport);page.on('pageerror',lambda e:errors.append(str(e)));page.set_content(html,wait_until='load')
            def route(path):page.evaluate('(p)=>location.hash=p',path);page.wait_for_timeout(200)
            def save():page.locator('#record-form [type=submit]').click();page.wait_for_timeout(350);check('Form save succeeds',page.locator('#form-error').is_hidden())
            page.get_by_role('heading',name='Your laboratory. Your website.').wait_for();check('Website studio loads');page.screenshot(path=str(args.output/'website-studio.png'),full_page=False)
            page.locator('#sidebar-search').fill('photos');check('Sidebar search selects media editor',page.get_by_role('link',name='Photos & videos',exact=True).is_visible());page.locator('#sidebar-search').fill('')
            route('/media');page.locator('#media-files').set_input_files({'name':'test-photo.png','mimeType':'image/png','buffer':blob});page.get_by_role('heading',name='test-photo',exact=True).wait_for();check('Browse uploads image through real backend');check('New upload is private',not client.get('/api/public').json()['media']);page.screenshot(path=str(args.output/'media-library.png'),full_page=False)
            route('/edit/media/'+app.state.store.list('media')[0]['id']);page.locator('#f-title').fill('Approved photograph');page.locator('#f-alt').fill('Temporary synthetic test photograph');page.locator('#f-approved').check();page.locator('#record-visibility').select_option('public');save();check('Media approval publishes intended metadata',client.get('/api/public').json()['media'][0]['title']=='Approved photograph')
            route('/media');page.evaluate('''(data)=>{const bytes=Uint8Array.from(atob(data),c=>c.charCodeAt(0));const transfer=new DataTransfer();transfer.items.add(new File([bytes],'dropped.png',{type:'image/png'}));document.querySelector('#media-drop').dispatchEvent(new DragEvent('drop',{dataTransfer:transfer,bubbles:true,cancelable:true}));}''',base64.b64encode(blob).decode());page.get_by_role('heading',name='dropped',exact=True).wait_for();check('Drag-and-drop uploads image through backend')
            if shutil.which('ffmpeg'):
                clip=tmp/'clip.mp4';subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=size=32x32:rate=5','-t','1','-c:v','libx264','-pix_fmt','yuv420p',str(clip)],check=True)
                page.locator('#media-files').set_input_files(str(clip));page.get_by_role('heading',name='clip',exact=True).wait_for();check('Video browse upload passes backend validation',any(p['kind']=='video' for p in app.state.store.list('media')))
            media=client.get('/api/public').json()['media'][0]
            route('/new/sections');page.locator('#f-title').fill('V4 test gallery');page.locator('#f-body').fill('Public gallery text.');page.locator('#f-location').select_option('homepage');page.locator('#f-position').select_option('after-hero');page.locator('#f-layout').select_option('gallery');page.locator('#f-media_items').select_option(media['id']);page.locator('#record-visibility').select_option('public');save();check('Administrator creates public gallery section',len(client.get('/api/public').json()['sections'])==1)
            public=context.new_page();public.set_content(client.get('/api/export/snapshot').text,wait_until='load');check('Snapshot renders new homepage section',public.get_by_role('heading',name='V4 test gallery',exact=True).count()==1);public.screenshot(path=str(args.output/'public-homepage.png'),full_page=False);public.close()
            route('/edit/people/nailoke-pauline-kadhila');check('Profile editor separates private personal information',page.get_by_role('heading',name='Private contact information',exact=True).count()==1);page.locator('#f-private_phone').fill('PRIVATE UI PHONE');save();check('Private profile edit excluded from public output','PRIVATE UI PHONE' not in client.get('/api/public').text)
            route('/publish');page.locator('#prepare-release').click();page.locator('#confirm-release').wait_for();check('Publisher prepares exact approved preview');page.locator('#confirm-release').click();page.locator('#publish-password-form').wait_for();check('Each push opens admin-password confirmation');page.screenshot(path=str(args.output/'publish-password.png'),full_page=False)
            page.locator('#publish-password-form [name=password]').fill('incorrect');page.locator('#publish-password-form [type=submit]').click();page.locator('#publish-error').wait_for(state='visible');check('Incorrect password fails visibly and safely','incorrect' in page.locator('#publish-error').inner_text())
            page.locator('#publish-password-form [name=password]').fill(PASSWORD);page.locator('#publish-password-form [type=submit]').click();page.get_by_text('Push succeeded.',exact=True).wait_for();check('Confirmed browser publish creates real local Git commit');check('Browser publishing preserves source HEAD',git('rev-parse','HEAD')==head)
            paths=subprocess.run(['git','--git-dir='+str(remote),'ls-tree','-r','--name-only','gh-pages'],check=True,capture_output=True,text=True).stdout.splitlines();check('Only generated public files reach local remote',all(n in ('index.html','.nojekyll') or n.startswith('public-media/') for n in paths));check('Password dialog removed after push',page.locator('#publish-password-form').count()==0)
            page.set_viewport_size({'width':390,'height':844});route('/studio');check('Mobile studio has no horizontal overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth'));page.screenshot(path=str(args.output/'admin-mobile.png'),full_page=False);check('No JavaScript errors',not errors);browser.close()
        report={'checks_passed':len(checks),'checks':checks,'javascript_errors':errors,'mode':'In-memory Chromium UI with TestClient transport for fetch and XHR; real Git operations against a temporary local bare remote. Not live browser-origin/HTTPS/GitHub testing.'};(args.output/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));client.close()
if __name__=='__main__':main()
