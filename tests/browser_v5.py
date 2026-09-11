#!/usr/bin/env python3
"""Real localhost HTTP browser acceptance; synthetic records remain in a temporary DB."""
from __future__ import annotations
import base64,io,json,shutil,socket,subprocess,sys,tempfile,threading,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from PIL import Image
import uvicorn
from playwright.sync_api import sync_playwright
from backend.app import create_app
from backend.security import HASHER
from backend.db import now
from backend.publisher import Publisher

PASSWORD='Temporary local V5 browser testing password!'

def main():
    output=ROOT/'docs/test-results-v5';output.mkdir(exist_ok=True,parents=True)
    checks=[];errors=[]
    def check(name,condition=True):
        if not condition:raise AssertionError(name)
        checks.append(name);print('PASS',name,flush=True)
    with tempfile.TemporaryDirectory(prefix='ted2-v5-browser-') as tmp:
        temp=Path(tmp)
        with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        origin='http://127.0.0.1:'+str(port)
        app=create_app(temp/'var/data.sqlite3',base_url=origin,production=False);store=app.state.store;store.seed()
        with store.connect(write=True) as c:c.execute("INSERT INTO users VALUES('test-owner','owner',?,'owner','',1,?)",(HASHER.hash(PASSWORD),now()))
        repo=temp/'source';repo.mkdir();remote=temp/'remote.git'
        def git(*args):return subprocess.run(['git','-C',str(repo),*args],check=True,capture_output=True,text=True).stdout.strip()
        subprocess.run(['git','init','--bare',str(remote)],check=True,capture_output=True);git('init','-b','main');git('config','user.name','Local acceptance tester');git('config','user.email','test@example.invalid');(repo/'source.txt').write_text('source stays private');git('add','source.txt');git('commit','-m','Test baseline');git('remote','add','origin',str(remote));
        app.state.publisher=Publisher(store,app.state.uploads,repo,allow_local_remote=True)
        server=uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='error'));thread=threading.Thread(target=server.run,daemon=True);thread.start()
        for _ in range(100):
            if server.started:break
            time.sleep(.05)
        try:
            check('Server starts over real localhost HTTP',server.started)
            check('Health reports V5',json.load(urllib.request.urlopen(origin+'/api/health'))['version']=='5.0.0')
            with sync_playwright() as pw:
                browser=pw.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox'])
                context=browser.new_context(viewport={'width':1440,'height':1060})
                context.route('**/*',lambda route:route.continue_() if route.request.url.startswith((origin,'data:','blob:')) else route.abort())
                page=context.new_page();page.on('dialog',lambda d:d.accept());page.on('pageerror',lambda e:errors.append(str(e)))
                page.goto(origin+'/admin');page.locator('[name=username]').fill('owner');page.locator('[name=password]').fill(PASSWORD);page.get_by_role('button',name='Sign in →',exact=True).click();page.get_by_role('heading',name='Your laboratory. Your website.').wait_for()
                check('Real browser login and studio load');check('Theme navigation visible',page.get_by_role('link',name='Theme & colours',exact=True).count()==1)
                page.screenshot(path=str(output/'studio-desktop.png'),full_page=False)
                def route(path):
                    page.evaluate('(p)=>location.hash=p',path);page.wait_for_timeout(200)
                def save():
                    page.locator('#record-form [type=submit]').click();page.wait_for_timeout(400)
                    check('Editor save succeeds',page.locator('#form-error').is_hidden())
                route('/edit/people/paulus-hamutenya');page.get_by_role('link',name='Add contact for this researcher').click();page.locator('#f-label').fill('Research enquiries');page.locator('#f-kind').select_option('email');page.locator('#f-value').fill('research@example.invalid');page.locator('#f-show_homepage').check();page.locator('#record-visibility').select_option('public');save();check('Researcher contact assignment saved',store.list('contacts')[0]['researcher_id']=='paulus-hamutenya')
                route('/edit/people/paulus-hamutenya');page.get_by_role('link',name='Add custom field',exact=True).first.click();page.locator('#f-label').fill('Office hours');page.locator('#f-value').fill('By appointment');page.locator('#record-visibility').select_option('public');save();check('Custom field linked to researcher',store.list('fields')[0]['target_id']=='paulus-hamutenya')
                route('/edit/people/paulus-hamutenya');page.locator('#f-public_phone').fill('12345');save();page.locator('[data-clear-field=public_phone]').click();save();check('Optional field value can be cleared',store.get('people','paulus-hamutenya')['public_phone']=='')
                page.locator('#f-public_email').fill('hidden@example.invalid');page.locator('[data-choice-group=hidden_fields] input[value=public_email]').check();save();check('Optional public field can be hidden', 'public_email' in store.get('people','paulus-hamutenya')['hidden_fields'])
                buf=io.BytesIO();Image.new('RGB',(100,70)).save(buf,'JPEG');photo=buf.getvalue()
                page.locator('[data-approve-attachments]').check();page.locator('[data-attachment-files]').set_input_files({'name':'acceptance-photo.jpg','mimeType':'image/jpeg','buffer':photo});page.wait_for_function("document.querySelector('[data-attachment-progress]').textContent.startsWith('Files uploaded')");save()
                person=store.get('people','paulus-hamutenya');check('Inline JPEG upload attaches to profile',len(person['media_items'])==1)
                public=context.new_page();public.on('pageerror',lambda e:errors.append(str(e)));public.goto(origin+'/#/profiles/paulus-hamutenya');public.get_by_role('heading',name='Mr Paulus Hamutenya',exact=True).wait_for();check('Public profile shows assigned contact',public.get_by_text('research@example.invalid',exact=True).count()==1);check('Public profile shows custom value',public.get_by_text('By appointment',exact=True).count()==1);check('Hidden email absent from public page','hidden@example.invalid' not in public.content());check('Inline approved image displayed',public.locator('.record-attachments img').count()==1)
                route('/edit/theme/website');page.get_by_role('button',name='Clinical blue',exact=True).click();page.locator('[data-choice-group=home_blocks] input[value=research]').uncheck();page.locator('[data-choice-group=hidden_navigation] input[value=gallery]').check();page.locator('#f-corner_radius').fill('8');save()
                check('Theme preset saved',store.get('theme','website')['primary']=='#164f80')
                page.screenshot(path=str(output/'theme-editor-desktop.png'),full_page=False)
                public.goto(origin+'/');public.locator('.hero').wait_for();check('Theme applied on public page',public.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--forest').trim()")=='#164f80');check('Homepage research block can be removed',public.locator('#research').count()==0);check('Gallery navigation can be hidden',public.locator('#primary-nav a[href="#/gallery"]').count()==0)
                route('/records/contacts');page.locator('[data-trash-record]').first.click();page.wait_for_timeout(250);check('Contact removed from active records',len(store.list('contacts'))==0)
                route('/trash');page.get_by_role('button',name='Restore privately',exact=True).first.click();page.wait_for_timeout(250);check('Trash restores private record',store.list('contacts')[0]['visibility']=='private')
                route('/records/contacts');page.locator('[data-trash-record]').first.click();page.wait_for_timeout(250);route('/trash');page.get_by_role('button',name='Delete permanently',exact=True).first.click();page.locator('dialog [name=confirmation]').fill('DELETE');page.locator('dialog [name=password]').fill(PASSWORD);page.locator('dialog [type=submit]').click();page.locator('dialog').wait_for(state='detached',timeout=10000);check('Password-confirmed permanent deletion from UI',len(store.list('contacts'))==0 and page.locator('dialog').count()==0)
                route('/media');check('Media controls accept MP4 and JPEG','.mp4' in page.locator('#media-files').get_attribute('accept') and '.jpeg' in page.locator('#media-files').get_attribute('accept'))
                video=temp/'test.mp4';subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=size=48x48:rate=5','-t','1','-c:v','libx264','-pix_fmt','yuv420p',str(video)],check=True)
                page.locator('#media-files').set_input_files(str(video));page.get_by_role('heading',name='test',exact=True).wait_for();check('MP4 uploads in real browser',any(m['kind']=='video' for m in store.list('media')))
                media=next(x for x in store.list('media') if x['kind']=='video');route('/edit/media/'+media['id']);page.locator('#f-approved').check();page.locator('#record-visibility').select_option('public');save();check('Video preview uses native player',page.locator('.media-editor-preview video').count()==1)
                page.screenshot(path=str(output/'media-editor-desktop.png'),full_page=False)
                route('/publish');page.get_by_role('button',name='Prepare preview',exact=True).click();page.get_by_role('button',name='Confirm & publish',exact=True).wait_for();check('Real backend prepares approved release')
                page.get_by_role('button',name='Confirm & publish',exact=True).click();page.locator('dialog [name=password]').fill('wrong-password');page.locator('dialog [type=submit]').click();page.locator('#publish-error').wait_for(state='visible');check('Wrong push password rejected in browser');page.locator('dialog [name=password]').fill(PASSWORD);page.screenshot(path=str(output/'publish-password-confirmation.png'),full_page=False);page.locator('dialog [type=submit]').click();page.get_by_text('Push succeeded.',exact=True).wait_for(timeout=20000);check('Password-confirmed push succeeds to real local Git remote')
                check('Source working branch unchanged',git('branch','--show-current')=='main')
                tree=subprocess.run(['git','--git-dir',str(remote),'ls-tree','-r','--name-only','gh-pages'],capture_output=True,text=True,check=True).stdout
                check('Published files exclude source and database','source.txt' not in tree and 'sqlite' not in tree and 'index.html' in tree)
                route('/edit/theme/website');page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(200);check('Mobile theme editor fits screen',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'));print('Mobile screenshot omitted; mobile layout measured separately.',flush=True)
                check('No unhandled browser script errors',not errors)
                browser.close()
        finally:
            server.should_exit=True;thread.join(timeout=5)
            (output/'browser-report.json').write_text(json.dumps({'transport':'real HTTP to temporary localhost Uvicorn','git':'real temporary local bare remote; no GitHub deployment','checks':checks,'errors':errors},indent=2))
    print(str(len(checks))+' browser checks passed.')
if __name__=='__main__':main()
