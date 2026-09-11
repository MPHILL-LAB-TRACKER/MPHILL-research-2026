#!/usr/bin/env python3
"""Real Chromium interaction smoke test. Never starts from or mutates real lab data."""
from __future__ import annotations
import argparse, json, shutil, sys, tempfile, threading, time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import uvicorn
from playwright.sync_api import sync_playwright
from backend.app import create_app
from manage import create_owner


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=Path('test-results/browser'));parser.add_argument('--port',type=int,default=8765);args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True);checks=[];errors=[]
    def checked(name,ok=True):
        if not ok: raise AssertionError(name)
        checks.append(name)
    with tempfile.TemporaryDirectory(prefix='ted2-browser-') as temp:
        base=f'http://127.0.0.1:{args.port}'
        application=create_app(Path(temp)/'browser.sqlite3',base_url=base,production=False);application.state.store.seed()
        create_owner(application.state.store,'browser-owner','Temporary browser test password 2026!')
        server=uvicorn.Server(uvicorn.Config(application,host='127.0.0.1',port=args.port,log_level='error',access_log=False));thread=threading.Thread(target=server.run,daemon=True);thread.start()
        for _ in range(100):
            if server.started:break
            time.sleep(.05)
        try:
            with sync_playwright() as pw:
                browser=pw.chromium.launch(executable_path=shutil.which('chromium') or None,headless=True,args=['--no-sandbox'])
                context=browser.new_context(viewport={'width':1440,'height':1050},device_scale_factor=1)
                # Remote photo networks are deliberately blocked: this test validates fallbacks, not licensing or remote availability.
                context.route('**/*',lambda route:route.continue_() if route.request.url.startswith(base) or route.request.url.startswith('data:') else route.abort())
                page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
                page.goto(base,wait_until='networkidle');page.get_by_role('heading',name='Engineering better biomedical solutions.').wait_for();checked('Live public homepage renders')
                checked('All twelve homepage research descriptions render',page.locator('.research-card,.topic-row').count()==12)
                checked('Corrected name is visible',page.get_by_text('Ms Vevangapi Mbatara',exact=True).count()==1)
                checked('Removed grayscale cell image is absent','photo-1631556096543-23fdcb5896da' not in page.content())
                checked('Desktop public layout has no horizontal overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
                page.screenshot(path=str(args.output/'public-home-desktop.png'),full_page=False)
                page.locator('a[href="#/profiles/nailoke-pauline-kadhila"]').first.click();page.get_by_role('heading',name='Prof Nailoke Pauline Kadhila',exact=True).wait_for()
                checked('Kadhila profile opens');checked('Three Kadhila publications render',page.locator('.publication-card').count()==3)
                checked('Supplied Kadhila portrait is displayed',page.locator('.avatar.large .profile-image').count()==1)
                page.screenshot(path=str(args.output/'profile-desktop.png'),full_page=False)
                page.goto(base+'/#/profiles/mbotarai-vevangapi',wait_until='networkidle');checked('Legacy misspelled profile route still resolves',page.get_by_role('heading',name='Ms Vevangapi Mbatara',exact=True).count()==1)
                page.goto(base+'/#/publications',wait_until='networkidle');page.locator('#pub-person').select_option('nailoke-pauline-kadhila');checked('Publication researcher filter',page.locator('.publication-card').count()==3)
                page.locator('#pub-search').fill('2022');checked('Publication year search',page.locator('.publication-card').count()==1)
                page.goto(base+'/#/researchers',wait_until='networkidle');page.locator('#directory-search').fill('Vevangapi');checked('Researcher directory search',page.locator('.person-card').count()==1)
                for route in ['research','pipeline','collaborators','funders','sources','contact','access']:
                    page.goto(base+'/#/'+route,wait_until='networkidle');checked('Public route renders: '+route,page.locator('main h1').count()==1)
                page.set_viewport_size({'width':390,'height':844});page.goto(base,wait_until='networkidle');checked('Mobile public layout has no overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
                page.locator('#menu-toggle').click();checked('Mobile public menu opens',page.locator('#primary-nav').is_visible());page.locator('#menu-toggle').click();page.screenshot(path=str(args.output/'public-home-mobile.png'),full_page=False)
                page.goto(base+'/admin',wait_until='networkidle');checked('Anonymous admin route opens sign-in',page.locator('#login-form').is_visible());page.screenshot(path=str(args.output/'login-mobile.png'),full_page=False)
                page.set_viewport_size({'width':1440,'height':1050});page.screenshot(path=str(args.output/'login-desktop.png'),full_page=False)
                page.locator('[name=username]').fill('browser-owner');page.locator('[name=password]').fill('Temporary browser test password 2026!');page.locator('#login-form button').click();page.get_by_role('heading',name='Your laboratory. Your website.').wait_for();checked('Owner can sign in and open real administration')
                page.screenshot(path=str(args.output/'admin-dashboard.png'),full_page=False)
                page.goto(base+'/admin#/edit/people/vevangapi-mbatara',wait_until='networkidle');page.locator('#f-bio').fill('BROWSER TEST — biography edit for integration testing only.');page.locator('#record-form [type=submit]').click();page.wait_for_function("document.querySelector('.save-hint')?.textContent.includes('Record version 2')");checked('Biography form saves to the server')
                public=context.new_page();public.goto(base+'/#/profiles/vevangapi-mbatara',wait_until='networkidle');checked('Saved biography appears on the public profile',public.get_by_text('BROWSER TEST — biography edit for integration testing only.',exact=True).count()==1);public.close()
                page.goto(base+'/admin#/new/projects',wait_until='networkidle');page.locator('#f-title').fill('Browser test — research project');page.locator('#f-lead_id').select_option('paulus-hamutenya');page.locator('#f-people').select_option(['paulus-hamutenya']);page.locator('#f-stage').select_option('active');page.locator('#record-form [type=submit]').click();page.wait_for_url('**/#/edit/projects/browser-test-research-project');checked('Administrator can create a private project through the UI')
                page.goto(base+'/admin#/new/milestones',wait_until='networkidle');page.locator('#f-title').fill('Browser test — completed milestone');page.locator('#f-project_id').select_option('browser-test-research-project');page.locator('#f-researcher_id').select_option('paulus-hamutenya');page.locator('#f-status').select_option('done');page.locator('#record-form [type=submit]').click();page.wait_for_url('**/#/edit/milestones/browser-test-completed-milestone');checked('Administrator can assign and complete a weighted milestone')
                page.goto(base+'/admin#/progress',wait_until='networkidle');page.locator('#progress-person').select_option('paulus-hamutenya');checked('Per-researcher weighted progress is calculated',page.get_by_text('100% · internal weighted progress').count()==1)
                page.goto(base+'/admin#/new/manuscripts',wait_until='networkidle');page.locator('#f-title').fill('Browser test — private manuscript');page.locator('#f-people').select_option(['paulus-hamutenya']);page.locator('#f-stage').select_option('under-review');page.locator('#f-internal_notes').fill('BROWSER-PRIVATE-REVIEW-NOTE');page.locator('#record-form [type=submit]').click();page.wait_for_url('**/#/edit/manuscripts/browser-test-private-manuscript');checked('Private manuscript and review notes save through the UI')
                page.goto(base+'/admin#/board',wait_until='networkidle');checked('Manuscript appears in the review stage',page.locator('.board-column').nth(1).get_by_text('Browser test — private manuscript').count()==1)
                page.goto(base+'/admin#/export',wait_until='networkidle');checked('Both public export modes available',page.locator('a[href="/api/export/bundle"]').count()==1 and page.locator('a[href="/api/export/snapshot"]').count()==1)
                page.goto(base+'/admin#/users',wait_until='networkidle');page.locator('#account-form [name=username]').fill('browser-researcher');page.locator('#account-form [name=researcher_id]').select_option('paulus-hamutenya');page.locator('#account-form [name=password]').fill('Temporary researcher password 2026!');page.locator('#account-form [type=submit]').click();page.get_by_text('Account created.',exact=True).wait_for();checked('Owner can create a linked researcher account in the UI')
                page.set_viewport_size({'width':390,'height':844});page.goto(base+'/admin#/dashboard',wait_until='networkidle');checked('Mobile administration has no overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth'));page.locator('#mobile-menu').click();checked('Mobile admin navigation opens',page.locator('#sidebar').get_attribute('class').endswith('open'));page.locator('#mobile-menu').click();page.screenshot(path=str(args.output/'admin-mobile.png'),full_page=False)
                page.locator('#logout').click();page.locator('#login-form').wait_for();checked('Sign-out returns to login')
                page.locator('[name=username]').fill('browser-researcher');page.locator('[name=password]').fill('Temporary researcher password 2026!');page.locator('#login-form button').click();page.get_by_role('heading',name='Your work. Your next milestone.').wait_for();checked('Researcher receives a separate workspace, not the admin page')
                page.set_viewport_size({'width':1440,'height':1050});page.goto(base+'/workspace#/progress',wait_until='networkidle');checked('Assigned researcher sees their progress',page.get_by_text('100% · internal weighted progress').count()==1)
                page.goto(base+'/workspace#/new/updates',wait_until='networkidle');page.locator('#f-title').fill('Browser test — private progress update');page.locator('#f-text').fill('Private progress note from researcher.');page.locator('#record-form [type=submit]').click();page.wait_for_url('**/#/edit/updates/browser-test-private-progress-update');checked('Researcher creates an assigned private activity update')
                checked('Researcher cannot choose public visibility',page.locator('#record-visibility').is_disabled())
                public=context.new_page();public.goto(base+'/#/pipeline',wait_until='networkidle');checked('Private manuscript absent from public pipeline',public.get_by_text('Browser test — private manuscript').count()==0);public.close()
                checked('No JavaScript runtime errors',not errors)
                report={'checks_passed':len(checks),'checks':checks,'javascript_errors':errors,'external_images':'Blocked deliberately; source attribution reviewed separately. Remote image delivery is not asserted.','test_data':'Fictional browser test records in a temporary SQLite database; never included in seed data.'}
                (args.output/'browser-report.json').write_text(json.dumps(report,indent=2))
                print(json.dumps(report,indent=2));browser.close()
        finally:
            server.should_exit=True;thread.join(timeout=8)
if __name__=='__main__':main()
