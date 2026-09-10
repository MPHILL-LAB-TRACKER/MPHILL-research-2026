#!/usr/bin/env python3
"""Offline Chromium UI checks using local API transport (not a live-origin E2E test).

The browser renders in memory. A TestClient bridge exercises actual application
routes without network navigation. Origin/cookie policies are covered separately
by test_app.py. tests/browser_check.py is the live-origin staging test.
"""
from __future__ import annotations
import argparse,json,shutil,sys,tempfile,re,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.db import ROOT
from backend.build import image_data
from manage import create_owner

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=Path('test-results/render'));args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    checks=[];errors=[]
    def check(name,ok=True):
        if not ok:raise AssertionError(name)
        checks.append(name)
    with tempfile.TemporaryDirectory(prefix='ted2-ui-') as d:
        app=create_app(Path(d)/'ui.sqlite3',base_url='http://testserver',production=False);app.state.store.seed();create_owner(app.state.store,'ui-test-owner','Temporary UI test password 2026!')
        client=TestClient(app)
        def bridge(url,method,headers,body):
            if not url.startswith('/api/'):raise ValueError('Only local API requests are accepted.')
            headers=dict(headers)
            if method not in ('GET','HEAD'):headers['Origin']='http://testserver'
            response=client.request(method,url,headers=headers,content=body)
            return {'body':response.text,'status':response.status_code,'headers':dict(response.headers)}
        with sync_playwright() as pw:
            browser=pw.chromium.launch(executable_path=shutil.which('chromium') or None,headless=True,args=['--no-sandbox'])
            context=browser.new_context(viewport={'width':1440,'height':1050});context.route('**/*',lambda r:r.abort())
            def new_page():
                p=context.new_page();p.on('pageerror',lambda e:errors.append(str(e)));return p
            def route(p,hash):p.evaluate('(h)=>location.hash=h',hash);p.wait_for_timeout(130)
            def section_snapshot(p, selector, filename):
                """Capture a complete section without smooth-scroll clipping or sticky overlays."""
                original = dict(p.viewport_size)
                style = p.add_style_tag(content='html{scroll-behavior:auto!important}')
                target = p.locator(selector)
                target.locator('img').evaluate_all('(images)=>images.forEach(i=>i.loading="eager")')
                p.evaluate('window.scrollTo(0,0)')
                p.wait_for_timeout(100)
                bounds = target.bounding_box()
                p.set_viewport_size({'width': original['width'], 'height': max(original['height'], math.ceil(bounds['y'] + bounds['height'] + 160))})
                p.evaluate('window.scrollTo(0,0)')
                p.wait_for_timeout(150)
                target.screenshot(path=str(args.output/filename), animations='disabled')
                p.set_viewport_size(original)
                style.evaluate('(s)=>s.remove()')
            page=new_page();page.set_content((ROOT/'index.html').read_text(),wait_until='load');page.get_by_role('heading',name='Engineering better biomedical solutions.').wait_for()
            check('Public single-file homepage renders in Chromium')
            check('All twelve homepage research descriptions render',page.locator('.research-card,.topic-row').count()==12)
            check('Corrected researcher name visible on homepage',page.get_by_text('Ms Vevangapi Mbatara',exact=True).count()==1)
            check('Disliked grayscale photograph absent','photo-1631556096543-23fdcb5896da' not in page.content())
            check('Desktop public view has no horizontal overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
            page.screenshot(path=str(args.output/'public-home-desktop.png'),full_page=False)
            route(page,'/profiles/nailoke-pauline-kadhila');check('Kadhila individual profile opens',page.get_by_role('heading',name='Prof Nailoke Pauline Kadhila',exact=True).count()==1)
            check('Three publisher-checked Kadhila records render',page.locator('.publication-card').count()==3)
            check('Unavailable portrait has initials fallback',page.locator('.avatar.large .profile-image').count()==0)
            page.screenshot(path=str(args.output/'profile-desktop.png'),full_page=False)
            route(page,'/profiles/mbotarai-vevangapi');check('Legacy profile URL resolves to corrected name',page.get_by_role('heading',name='Ms Vevangapi Mbatara',exact=True).count()==1)
            route(page,'/publications');page.locator('#pub-person').select_option('nailoke-pauline-kadhila');check('Publication researcher filter',page.locator('.publication-card').count()==3);page.locator('#pub-search').fill('2022');check('Publication search',page.locator('.publication-card').count()==1)
            route(page,'/researchers');page.locator('#directory-search').fill('Vevangapi');check('Researcher directory search',page.locator('.person-card').count()==1)
            for path in ['research','pipeline','collaborators','funders','sources','contact','access']:
                route(page,'/'+path);check('Public view renders: '+path,page.locator('main h1').count()==1)
            route(page,'/');page.set_viewport_size({'width':390,'height':844});check('Mobile public view has no horizontal overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
            page.locator('#menu-toggle').click();check('Public mobile menu opens',page.locator('#primary-nav').is_visible());page.locator('#menu-toggle').click();page.screenshot(path=str(args.output/'public-home-mobile.png'),full_page=False)
            # V3 content and local-image checks; remote networks remain deliberately blocked.
            page.set_viewport_size({'width':1440,'height':1050});route(page,'/')
            check('Homepage Alerts contains three individual conference presentations',page.locator('#alerts .event-card').count()==3)
            check('Nanomedicine seminar is present on the homepage',page.locator('#alerts .seminar-notice h3').inner_text()=='Nanomedicine in Health')
            check('NCRST November date is visibly qualified against the September host notice','17–18 November 2026' in page.locator('#alerts .date-discrepancy').inner_text() and '17–18 September 2026' in page.locator('#alerts .date-discrepancy').inner_text())
            check('No Instagram outbound links in the public page',page.locator('a[href*="instagram.com"]').count()==0)
            check('Homepage has eleven locally embedded labelled portraits',page.locator('.roster-link img[src^="data:image/jpeg"]').count()==11)
            section_snapshot(page,'#alerts','homepage-alerts-desktop.png')
            route(page,'/researchers');page.locator('.person-card').last.scroll_into_view_if_needed();page.wait_for_timeout(200)
            check('All eleven supplied portraits decode without remote requests',page.locator('.profile-image').evaluate_all('(images)=>images.length===11 && images.every(i=>i.complete && i.naturalWidth>0)'))
            page.evaluate('window.scrollTo(0,0)');page.screenshot(path=str(args.output/'team-directory-desktop.png'),full_page=False)
            for alias,name in [('denise-bouman','Ms Denise Bouman'),('maneria-halweendo','Dr Maneria Halweendo'),('charity-maepa','Ms Charity Maepa'),('nonku-phili','Ms Nonku Phili'),('jaydine-jeris','Ms Jaydine Jeris')]:
                route(page,'/profiles/'+alias);check('Corrected profile alias: '+alias,page.get_by_role('heading',name=name,exact=True).count()==1)
            route(page,'/profiles/paulus-hamutenya');check('Paulus profile shows the correct biosensor research topic','Aptamer-functionalised Gold Nanoparticle Biosensors' in page.locator('#bio').inner_text())
            check('Certificate and selection evidence appear together on Paulus profile',page.locator('#recognition .certificate-preview').count()==1 and 'not printed on the certificate' in page.locator('#recognition').inner_text())
            check('Certificate image loads offline',page.locator('.certificate-preview img').evaluate('(i)=>{i.loading="eager";return i.src.startsWith("data:image/jpeg;base64,")}'))
            section_snapshot(page,'#recognition','paulus-certificate-desktop.png')
            with page.expect_download(timeout=8000) as info:
                page.locator('[data-certificate]').click()
            download=info.value;target=args.output/'downloaded-participation-certificate.pdf';download.save_as(target)
            check('Certificate PDF downloads from the standalone HTML with original bytes',target.read_bytes()==(ROOT/'data/assets/certificates/falling-walls-paulus-hamutenya-2026.pdf').read_bytes());target.unlink()
            route(page,'/profiles/albertina-shatri');check('Dr Shatri profile includes both conference notices',page.locator('#activity .event-card').count()==2)
            route(page,'/profiles/naungwe-simasiku');check('Ms Simasiku profile includes her NCRST notice',page.locator('#activity .event-card').count()==1)
            route(page,'/activity/shatri-ncrst-2026');check('Individual NCRST activity page links to the official organiser',page.locator('.activity-detail a[href="https://www.ncrst.na/calls/"]').count()>=1)
            page.set_viewport_size({'width':390,'height':844});route(page,'/');page.locator('#alerts').scroll_into_view_if_needed()
            check('Mobile alerts have no horizontal overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
            section_snapshot(page,'#alerts','homepage-alerts-mobile.png')
            route(page,'/profiles/paulus-hamutenya');check('Mobile certificate profile has no horizontal overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
            section_snapshot(page,'#recognition','paulus-certificate-mobile.png')
            route(page,'/activity');check('Activity directory renders all four notices',page.locator('.event-card').count()==4)
            page.evaluate("window.__OLD_DATES={...window.TED2_DATA.announcements[0]}; window.TED2_DATA.announcements[0].start_date='2020-09-22';window.TED2_DATA.announcements[0].end_date='2020-09-25'")
            route(page,'/');check('Expired event leaves the homepage upcoming list',page.locator('#alerts [data-event="shatri-sanord-2026"]').count()==0)
            route(page,'/activity');check('Expired event moves into the Past activity section',page.get_by_role('heading',name='Past activity',exact=True).count()==1)
            page.evaluate('Object.assign(window.TED2_DATA.announcements[0],window.__OLD_DATES)')
            page.close()
            js=(ROOT/'web/assets/admin.js').read_text().replace('/images/ted2-wordmark.png',image_data('ted2-wordmark.png'))
            # Full document navigation is captured, not exercised, by this offline test.
            js=re.sub(r"location\.href\s*=\s*result\.next", "window.__NAV=result.next",js)
            js=re.sub(r"location\.href\s*=\s*['\"]/login['\"]", "window.__NAV='/login'",js)
            js=re.sub(r"location\.replace\((.*?)\)", r"window.__NAV=(\1)",js)
            adapter='''window.fetch=async function(url,init={}){const h=Object.fromEntries(new Headers(init.headers||{}));const r=await window.__LOCAL_API(String(url),init.method||'GET',h,init.body||null);return new Response(r.body,{status:r.status,headers:r.headers});};'''
            html=(ROOT/'web/admin.html').read_text().replace('<link rel="stylesheet" href="/assets/admin.css">','<style>'+(ROOT/'web/assets/admin.css').read_text()+'</style>').replace('<script src="/assets/admin.js" defer></script>','<script>'+adapter+'</script><script>'+js+'</script>')
            def management_page():
                p=new_page();p.expose_function('__LOCAL_API',bridge);p.set_content(html,wait_until='load');p.wait_for_timeout(300);return p
            page=management_page();page.locator('#login-form').wait_for();check('Sign-in UI renders without authenticated data');page.screenshot(path=str(args.output/'login-desktop.png'),full_page=False)
            page.locator('[name=username]').fill('ui-test-owner');page.locator('[name=password]').fill('Temporary UI test password 2026!');page.locator('#login-form button').click();page.wait_for_function("window.__NAV==='/admin'");check('Login form authenticates through actual local API and chooses admin destination');page.close()
            page=management_page();page.get_by_role('heading',name='Research, with a clear next step.').wait_for();check('Authenticated owner dashboard renders');page.screenshot(path=str(args.output/'admin-dashboard.png'),full_page=False)
            route(page,'/records/announcements');check('Admin navigation includes editable homepage alerts',page.locator('#record-list tbody tr').count()==4)
            page.screenshot(path=str(args.output/'admin-alerts-desktop.png'),full_page=False)
            route(page,'/edit/announcements/shatri-ncrst-2026');check('Admin editor exposes both supplied and host-published dates',page.locator('#f-start_date').input_value()=='2026-11-17' and page.locator('#f-official_start_date').input_value()=='2026-09-17')
            page.locator('#f-description').fill('UI TEST ONLY — notice content changed.');page.locator('#record-form [type=submit]').click();page.wait_for_function("document.querySelector('.save-hint')?.textContent.includes('Record version 2')")
            check('Alert editor saves through the real local API',any(a['description']=='UI TEST ONLY — notice content changed.' for a in client.get('/api/public').json()['announcements']))
            route(page,'/edit/achievements/paulus-falling-walls-2026');check('Certificate editor offers explicit publication approval',page.locator('#f-document_public').is_checked())
            page.locator('#f-document_public').uncheck();page.locator('#record-form [type=submit]').click();page.wait_for_function("document.querySelector('.save-hint')?.textContent.includes('Record version 2')")
            check('Certificate approval can be revoked through the admin form','document_url' not in client.get('/api/public').json()['achievements'][0])
            route(page,'/new/people');check('New profiles do not inherit someone else’s supplied portrait',page.locator('#f-bundled_portrait').input_value()=='')
            route(page,'/new/achievements');check('New achievements do not inherit an existing certificate',page.locator('#f-certificate_key').input_value()=='')
            route(page,'/edit/people/vevangapi-mbatara');page.locator('#f-bio').fill('UI TEST ONLY — a temporary biography.');page.locator('#record-form [type=submit]').click();page.wait_for_function("document.querySelector('.save-hint')?.textContent.includes('Record version 2')");check('Biography editor saves through local API')
            check('Saved biography appears in public projection',any(p.get('bio')=='UI TEST ONLY — a temporary biography.' for p in client.get('/api/public').json()['people']))
            route(page,'/edit/people/nailoke-pauline-kadhila');page.locator('#f-bio').wait_for();page.screenshot(path=str(args.output/'profile-editor-desktop.png'),full_page=False)
            route(page,'/new/projects');page.locator('#f-title').fill('UI test — research project');page.locator('#f-lead_id').select_option('paulus-hamutenya');page.locator('#f-people').select_option(['paulus-hamutenya']);page.locator('#f-stage').select_option('active');page.locator('#record-form [type=submit]').click();page.wait_for_function("location.hash.includes('/edit/projects/ui-test-research-project')");check('Project editor creates a private assigned project')
            route(page,'/new/milestones');page.locator('#f-title').fill('UI test — completed milestone');page.locator('#f-project_id').select_option('ui-test-research-project');page.locator('#f-researcher_id').select_option('paulus-hamutenya');page.locator('#f-status').select_option('done');page.locator('#record-form [type=submit]').click();page.wait_for_function("location.hash.includes('/edit/milestones/ui-test-completed-milestone')");check('Milestone editor assigns and completes a weighted task')
            route(page,'/progress');page.locator('#progress-person').select_option('paulus-hamutenya');check('Individual researcher view calculates 100% completed test milestones',page.get_by_text('100% · internal weighted progress').count()==1)
            route(page,'/new/manuscripts');page.locator('#f-title').fill('UI test — private manuscript');page.locator('#f-people').select_option(['paulus-hamutenya']);page.locator('#f-stage').select_option('under-review');page.locator('#f-internal_notes').fill('PRIVATE-UI-REVIEWER-NOTE');page.locator('#record-form [type=submit]').click();page.wait_for_function("location.hash.includes('/edit/manuscripts/ui-test-private-manuscript')");check('Manuscript editor saves a private draft and review note')
            route(page,'/board');check('Manuscript displays in the correct review stage',page.locator('.board-column').nth(1).get_by_text('UI test — private manuscript').count()==1)
            route(page,'/export');check('Connected and snapshot export links render',page.locator('a[href="/api/export/connected"]').count()==1 and page.locator('a[href="/api/export/snapshot"]').count()==1)
            route(page,'/users');page.locator('#account-form [name=username]').fill('ui-researcher');page.locator('#account-form [name=researcher_id]').select_option('paulus-hamutenya');page.locator('#account-form [name=password]').fill('Temporary researcher password 2026!');page.locator('#account-form [type=submit]').click();page.get_by_text('Account created.',exact=True).wait_for();check('Account editor creates a researcher linked to a profile')
            page.set_viewport_size({'width':390,'height':844});route(page,'/dashboard');check('Mobile admin layout has no horizontal overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth'));page.locator('#mobile-menu').click();check('Admin mobile menu opens',page.locator('#sidebar').get_attribute('class').endswith('open'));page.locator('#mobile-menu').click();page.screenshot(path=str(args.output/'admin-mobile.png'),full_page=False)
            page.locator('#logout').click();page.wait_for_function("window.__NAV==='/login'");check('Sign-out revokes API session',client.get('/api/session').json()['user'] is None);page.close()
            response=client.post('/api/login',headers={'Origin':'http://testserver'},json={'username':'ui-researcher','password':'Temporary researcher password 2026!'});check('Researcher login chooses workspace destination',response.json()['next']=='/workspace')
            page=management_page();page.get_by_role('heading',name='Your work. Your next milestone.').wait_for();check('Researcher-specific dashboard renders');route(page,'/progress');check('Researcher sees assigned progress only',page.get_by_text('100% · internal weighted progress').count()==1)
            route(page,'/new/updates');page.locator('#f-title').fill('UI test — private progress update');page.locator('#f-text').fill('A private test progress note.');page.locator('#record-form [type=submit]').click();page.wait_for_function("location.hash.includes('/edit/updates/ui-test-private-progress-update')");check('Researcher can save an assigned private update');check('Researcher publishing control is disabled',page.locator('#record-visibility').is_disabled())
            public=client.get('/api/public').text;check('Private UI-created titles and notes never enter the public response',all(x not in public for x in ['UI test — private manuscript','PRIVATE-UI-REVIEWER-NOTE','A private test progress note.']))
            check('No JavaScript runtime errors',not errors)
            report={'checks_passed':len(checks),'checks':checks,'javascript_errors':errors,'mode':'In-memory Chromium rendering and form interactions, using a FastAPI TestClient bridge. Real network navigation, browser-origin cookies, HTTPS and deployment were not exercised.','images':'Remote image requests aborted deliberately. Eleven supplied portraits, certificate preview and original PDF download tested offline; remaining remote-image fallback also tested.','test_data':'All UI test projects, accounts, manuscripts and updates were temporary and are not shipped in seed.json.'}
            (args.output/'render-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));browser.close()
        client.close()
if __name__=='__main__':main()
