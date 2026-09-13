#!/usr/bin/env python3
"""Real HTTP regression tests. Standard-library Python drives the PHP application.
The temporary database, test credentials and uploaded files are never release data.
"""
from __future__ import annotations
import base64, hashlib, http.cookiejar, json, os, pathlib, shutil, socket, sqlite3
import struct, subprocess, tempfile, time, unittest, urllib.request, urllib.error, zlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
PASSWORD='TestingOnly!V6-9832'
def png():
    def chunk(t,d): return struct.pack('!I',len(d))+t+d+struct.pack('!I',zlib.crc32(t+d)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',4,4,8,2,0,0,0))+chunk(b'IDAT',zlib.compress((b'\0'+b'\x40\x80\xa0'*4)*4))+chunk(b'IEND',b'')
class Client:
    def __init__(self,base): self.base=base; self.csrf=''; self.cookies=http.cookiejar.CookieJar(); self.opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookies))
    def request(self,path,method='GET',body=None,headers=None,raw=None):
        h={'Origin':self.base,'X-CSRF-Token':self.csrf}; h.update(headers or {})
        if body is not None: raw=json.dumps(body).encode(); h['Content-Type']='application/json'
        req=urllib.request.Request(self.base+path,data=raw,method=method,headers=h)
        try: r=self.opener.open(req,timeout=50)
        except urllib.error.HTTPError as e:r=e
        data=r.read(); result=json.loads(data) if 'application/json' in r.headers.get('Content-Type','') else data
        return r.code,result,r.headers
    def login(self,name='owner-test'):
        status,data,_=self.request('/api/login','POST',{'username':name,'password':PASSWORD}); assert status==200,(status,data); self.csrf=data['csrf'];return data
    def upload(self,c,rid,name,data,mime='application/octet-stream'):
        boundary='----TED2'+hashlib.sha256(os.urandom(8)).hexdigest()
        raw=(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\nContent-Type: {mime}\r\n\r\n'.encode()+data+f'\r\n--{boundary}--\r\n'.encode())
        return self.request(f'/api/uploads/{c}/{rid}','POST',raw=raw,headers={'Content-Type':'multipart/form-data; boundary='+boundary})
class HTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='ted2-v6-tests-');cls.tmp=pathlib.Path(cls.temp.name);cls.db=cls.tmp/'ted2.sqlite3'
        with socket.socket() as s:s.bind(('127.0.0.1',0));cls.port=s.getsockname()[1]
        cls.base=f'http://127.0.0.1:{cls.port}';cls.env={**os.environ,'TED2_DB':str(cls.db),'TED2_BASE_URL':cls.base,'TED2_SQLITE_DRIVER':os.environ.get('TED2_TEST_DRIVER','native')}
        code="require 'php/bootstrap.php';$s=new Ted2\\Store();$s->init();$s->seed();$s->migrate();$s->db->query('INSERT INTO users VALUES(?,?,?,?,?,?,?)',['owner-test-id','owner-test',Ted2\\Auth::hash('"+PASSWORD+"'),'owner','',1,Ted2\\utc()]);"
        subprocess.run(['php','-r',code],cwd=ROOT,env=cls.env,check=True,capture_output=True)
        cls.log=open(cls.tmp/'server.log','w+')
        cls.server=subprocess.Popen(['php','-d','upload_max_filesize=80M','-d','post_max_size=84M','-d','memory_limit=512M','-d','max_execution_time=300','-S',f'127.0.0.1:{cls.port}','-t','public','public/router.php'],cwd=ROOT,env=cls.env,stdout=cls.log,stderr=cls.log)
        for _ in range(60):
            try:urllib.request.urlopen(cls.base+'/admin',timeout=.4);break
            except Exception:time.sleep(.05)
        else:raise RuntimeError('PHP server did not start')
        cls.client=Client(cls.base);cls.user=cls.client.login();cls.schemas=cls.client.request('/api/bootstrap')[1]['schemas']
        cls.video=None
        if shutil.which('ffmpeg') and shutil.which('ffprobe'):
            vid=cls.tmp/'sample.mp4';subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-f','lavfi','-i','color=c=blue:s=160x120:d=1','-c:v','libx264','-pix_fmt','yuv420p','-threads','1',str(vid)],check=True);cls.video=vid.read_bytes()
    @classmethod
    def tearDownClass(cls):
        cls.server.terminate();cls.server.wait(timeout=10);cls.log.seek(0);log=cls.log.read();cls.log.close();
        if 'PHP Warning' in log or 'PHP Fatal' in log or 'TED2 request failed' in log:print('\nPHP LOG DIAGNOSTICS:\n'+log[-6000:])
        cls.temp.cleanup()
    def new(self,c,**values):
        p={'id':hashlib.sha256(os.urandom(10)).hexdigest()[:24],'visibility':'private'}
        for f in self.schemas[c]['fields']:
            t=f['type'];p[f['key']]=[] if t in ('multi','lines','urls','multi-choice') else False if t=='checkbox' else None if t in ('number','year','percent','weight','money') else ''
            if t=='select' and f['required']:p[f['key']]=f['options'][0]
        p.update(values);return p
    def create(self,c,p,client=None):
        status,data,_=(client or self.client).request('/api/records/'+c,'POST',p);self.assertEqual(status,201,data);return data
    def save(self,c,p,client=None):
        status,data,_=(client or self.client).request('/api/records/'+c+'/'+p['id'],'PUT',p);self.assertEqual(status,200,data);return data
    def get(self,c,rid):return self.client.request('/api/records/'+c+'/'+rid)[1]
    def media(self,who='',public=True,kind='image',data=None):
        p=self.create('media',self.new('media',title='Upload '+hashlib.sha256(os.urandom(8)).hexdigest()[:6],scope='researcher' if who else 'laboratory',researcher_id=who,kind=kind,approved=public,visibility='public' if public else 'private',caption='A caption with clear context.'))
        status,file,_=self.client.upload('media',p['id'],'sample.mp4' if kind=='video' else 'sample.png',data or png());self.assertEqual(status,201,file);p['file_id']=file['id'];p['display_filename']='renamed-material';p=self.save('media',p);return p,file
    def test_01_public_server_rendered(self):
        status,html,h=self.client.request('/');self.assertEqual(status,200);self.assertIn(b'Biomaterial',html);self.assertIn(b'data-carousel',html);self.assertIn(b'Naungwe Simasiku',html);self.assertNotIn(b'window.TED2_DATA=',html);self.assertLess(len(html),100_000)
    def test_02_profile_search_and_sitemap(self):
        status,html,_=self.client.request('/researchers/paulus-hamutenya/');self.assertEqual(status,200);self.assertIn(b'application/ld+json',html);self.assertIn(b'ProfilePage',html);self.assertIn(b'rel="canonical"',html)
        status,xml,_=self.client.request('/sitemap.xml');self.assertIn(b'/researchers/paulus-hamutenya/',xml)
    def test_03_core_content_and_names(self):
        data=self.client.request('/api/bootstrap')[1];self.assertEqual(len(data['records']['people']),12);self.assertEqual(len(data['records']['capabilities']),12);self.assertEqual(next(p for p in data['records']['people'] if p['id']=='jaydine-feris')['name'],'Ms Jaydine Feris')
    def test_04_private_storage_inaccessible(self):
        guest=Client(self.base)
        for path in ['/var/ted2.sqlite3','/.env','/php/Core.php','/data/seed.json','/api/bootstrap','/api/users']:
            with self.subTest(path=path):self.assertIn(guest.request(path)[0],(401,404))
    def test_05_host_origin_csrf(self):
        p=self.get('people','naungwe-simasiku')
        for headers in [{'Origin':'https://attacker.invalid'},{'X-CSRF-Token':'wrong'},{'Origin':''},{'Sec-Fetch-Site':'cross-site'}]:
            with self.subTest(headers=headers):self.assertEqual(self.client.request('/api/records/people/'+p['id'],'PUT',p,headers)[0],403)
        self.assertEqual(self.client.request('/',headers={'Host':'attacker.invalid'})[0],400)
    def test_06_milestone_no_project(self):
        p=self.create('milestones',self.new('milestones',title='Standalone milestone',researcher_id='paulus-hamutenya',status='todo',project_id='',weight=1));self.assertEqual(p['project_id'],'');p['status']='done';self.assertEqual(self.save('milestones',p)['status'],'done')
    def test_07_stale_version_conflict(self):
        p=self.create('updates',self.new('updates',title='Test update',researcher_id='paulus-hamutenya',date='2026-09-13',kind='progress',text='Test progress'));old=dict(p);p['title']='Latest';self.save('updates',p);old['title']='Stale';self.assertEqual(self.client.request('/api/records/updates/'+p['id'],'PUT',old)[0],409)
    def test_08_achievements_without_project(self):
        p=self.create('achievements',self.new('achievements',title='Test recognition',researcher_id='paulus-hamutenya',date='2026-09-13',summary='This is a test record.'));self.assertNotIn('project_id',p)
    def test_09_public_private_projection(self):
        p=self.get('people','paulus-hamutenya');old=dict(p);p.update(private_email='PRIVATE_SENTINEL@example.org',private_phone='PRIVATE_PHONE_SENTINEL',bio='Public biography\n\nSecond paragraph.',visibility='public');self.save('people',p)
        html=self.client.request('/researchers/paulus-hamutenya/')[1];self.assertNotIn(b'PRIVATE_SENTINEL',html);self.assertNotIn(b'PRIVATE_PHONE_SENTINEL',html);self.assertIn(b'<p>Second paragraph.</p>',html)
        old['_version']=self.get('people',p['id'])['_version'];self.save('people',old)
    def test_10_escaped_content(self):
        p=self.create('sections',self.new('sections',title='<script>alert(1)</script>',body='<img src=x onerror=alert(1)>',location='standalone-page',layout='text',visibility='public'))
        html=self.client.request('/pages/'+p['id']+'/')[1];self.assertIn(b'&lt;script&gt;',html);self.assertNotIn(b'<script>alert(1)',html)
    def test_11_media_general(self):
        p,f=self.media();status,body,h=Client(self.base).request('/media/'+f['id']);self.assertEqual(status,200);self.assertEqual(h['Content-Type'],'image/png');self.assertTrue(body.startswith(b'\x89PNG'))
    def test_12_media_scopes(self):
        a,fa=self.media('paulus-hamutenya');b,fb=self.media('naungwe-simasiku')
        p=self.get('people','paulus-hamutenya');p['media_items']=[b['id']];self.assertEqual(self.client.request('/api/records/people/'+p['id'],'PUT',p)[0],422)
        p['media_items']=[a['id']];self.save('people',p);html=self.client.request('/researchers/paulus-hamutenya/')[1];self.assertIn(a['title'].encode(),html);self.assertNotIn(b['title'].encode(),html)
        gallery=self.client.request('/gallery/')[1];self.assertNotIn(a['title'].encode(),gallery)
    def test_13_private_media_not_served(self):
        p,f=self.media(public=False);self.assertEqual(Client(self.base).request('/media/'+f['id'])[0],404)
    def test_14_uploads_reject_executable(self):
        p=self.create('media',self.new('media',title='Invalid file',scope='laboratory'))
        status,_,_=self.client.upload('media',p['id'],'fake.jpg',b'<?php system($_GET["cmd"]); ?>');self.assertEqual(status,422)
    def test_15_video_and_range(self):
        if self.video is None:self.skipTest('ffmpeg/ffprobe not installed')
        p,f=self.media(kind='video',data=self.video);self.assertEqual(f['mime'],'video/mp4');status,data,h=Client(self.base).request('/media/'+f['id'],headers={'Range':'bytes=0-31'});self.assertEqual(status,206);self.assertEqual(len(data),32);self.assertIn('bytes 0-31/',h['Content-Range']);html=self.client.request('/gallery/')[1];self.assertIn(b'playsinline',html);self.assertIn(b'preload="none"',html)
    def test_16_caption_filename_reorder(self):
        a,_=self.media();b,_=self.media();p=self.get('settings','laboratory');p['media_items']=[b['id'],a['id']];self.save('settings',p);html=self.client.request('/')[1];self.assertLess(html.find(b['title'].encode()),html.find(a['title'].encode()));self.assertIn(b'renamed-material.png',html);self.assertIn(b'A caption with clear context.',html)
    def test_17_reassignment_blocked(self):
        a,_=self.media('paulus-hamutenya');p=self.get('people','paulus-hamutenya');p['media_items']=[a['id']];self.save('people',p);a['researcher_id']='naungwe-simasiku';self.assertEqual(self.client.request('/api/records/media/'+a['id'],'PUT',a)[0],409)
    def test_18_theme_both_interfaces(self):
        p=self.get('theme','website');old=dict(p);p.update(primary='#314159',preset='modern',header_band='modern',footer_band='none',header_alignment='center');self.save('theme',p)
        for path in ['/','/admin']:
            with self.subTest(path=path):self.assertIn(b'--primary:#314159',self.client.request(path)[1])
        self.assertIn(b'band-modern align-center',self.client.request('/')[1]);old['_version']=self.get('theme','website')['_version'];self.save('theme',old)
    def test_19_all_logos_uploadable(self):
        p=self.get('theme','website')
        for key,flag in [('logo_upload_id','logo_approved'),('institution_logo_id','institution_logo_approved'),('footer_logo_id','footer_logo_approved'),('favicon_id','favicon_approved')]:
            with self.subTest(slot=key):
                status,f,_=self.client.upload('theme','website','logo.png',png());self.assertEqual(status,201,f);p[key]=f['id'];p[flag]=True;p=self.save('theme',p);self.assertEqual(Client(self.base).request('/media/'+f['id'])[0],200)
    def test_20_trash_restore(self):
        p=self.create('contacts',self.new('contacts',label='Temporary contact',kind='email',value='test@example.org'));status,_,_=self.client.request('/api/records/contacts/'+p['id'],'DELETE',{'_version':p['_version']});self.assertEqual(status,200);self.assertEqual(self.client.request('/api/records/contacts/'+p['id'])[0],404);self.assertEqual(self.client.request('/api/trash/contacts/'+p['id']+'/restore','POST',{})[0],200)
    def test_21_protected_records(self):
        p=self.get('theme','website');self.assertEqual(self.client.request('/api/records/theme/website','DELETE',{'_version':p['_version']})[0],422)
    def test_22_permanent_delete_password(self):
        p=self.create('contacts',self.new('contacts',label='Delete permanently',kind='other',value='Test'))
        self.client.request('/api/records/contacts/'+p['id'],'DELETE',{'_version':p['_version']});url='/api/trash/contacts/'+p['id']+'/purge';self.assertEqual(self.client.request(url,'POST',{'password':'incorrect','confirm':'DELETE'})[0],403);self.assertEqual(self.client.request(url,'POST',{'password':PASSWORD,'confirm':'DELETE'})[0],200)
    def test_23_researcher_rights(self):
        data={'username':'researcher-test','password':PASSWORD,'role':'researcher','researcher_id':'paulus-hamutenya','active':True,'edit_profile':True,'edit_research':True};status,result,_=self.client.request('/api/users','POST',data);self.assertEqual(status,200,result);r=Client(self.base);r.login('researcher-test')
        self.assertEqual(r.request('/api/records/people/naungwe-simasiku')[0],404);self.assertEqual(r.request('/api/users')[0],403);self.assertEqual(r.request('/api/responses')[0],403);self.assertEqual(r.request('/api/publish/prepare','POST',{})[0],403)
        p=r.request('/api/records/people/paulus-hamutenya')[1];p['bio']='Own researcher edit';self.assertEqual(r.request('/api/records/people/'+p['id'],'PUT',p)[0],200)
        p=r.request('/api/records/people/paulus-hamutenya')[1];p['priority']=2;self.assertEqual(r.request('/api/records/people/'+p['id'],'PUT',p)[0],403)
        other=self.get('people','naungwe-simasiku');other['bio']='Forbidden';self.assertEqual(r.request('/api/records/people/'+other['id'],'PUT',other)[0],403)
        p=self.new('milestones',title='Own milestone',researcher_id='paulus-hamutenya',status='todo',weight=1);self.assertEqual(r.request('/api/records/milestones','POST',p)[0],201)
        p['id']+='z';p['researcher_id']='naungwe-simasiku';self.assertEqual(r.request('/api/records/milestones','POST',p)[0],403)
        data['edit_profile']=False;data['password']='';self.client.request('/api/users/'+result['id'],'PUT',data);self.assertEqual(r.request('/api/bootstrap')[0],401);r.login('researcher-test');p=self.get('people','paulus-hamutenya');self.assertEqual(r.request('/api/records/people/'+p['id'],'PUT',p)[0],403)
    def test_24_anonymous_moderation(self):
        settings=self.get('settings','laboratory');settings['anonymous_enabled']=True;self.save('settings',settings);g=Client(self.base);token=g.request('/api/anonymous/token')[1]['token'];time.sleep(2.1);status,d,_=g.request('/api/anonymous','POST',{'kind':'question','token':token,'question':'Can researchers propose a public seminar?','website':''});self.assertEqual(status,200,d)
        q=next(p for p in self.client.request('/api/records/questions')[1] if p['question'].startswith('Can researchers'));self.assertEqual(q['visibility'],'private');self.assertNotIn(q['question'].encode(),g.request('/questions/')[1]);q['visibility']='public';self.assertEqual(self.client.request('/api/records/questions/'+q['id'],'PUT',q)[0],422);q.update(answer='Please contact the laboratory coordinator.',status='answered');self.save('questions',q);self.assertIn(q['question'].encode(),g.request('/questions/')[1])
    def test_25_questionnaire_anonymous(self):
        p=self.create('questionnaires',self.new('questionnaires',title='Feedback form',description='Anonymous test questionnaire',open=True,visibility='public'));q=self.create('survey_questions',self.new('survey_questions',label='How clear is the site?',questionnaire_id=p['id'],kind='rating',required_answer=True,visibility='public'));g=Client(self.base);token=g.request('/api/anonymous/token')[1]['token'];time.sleep(2.1)
        body={'kind':'survey','questionnaire_id':p['id'],'token':token,'answers':{q['id']:'5'}};self.assertEqual(g.request('/api/anonymous','POST',body)[0],200);body['answers'][q['id']]='9';self.assertEqual(g.request('/api/anonymous','POST',body)[0],422)
        response=self.client.request('/api/responses')[1][0];self.assertEqual(set(response),{'id','questionnaire_id','answers','created_at'});self.assertEqual(g.request('/api/responses')[0],401)
    def test_26_hidden_optional_fields(self):
        p=self.get('people','vevangapi-mbatara');old=dict(p);p['public_phone']='VISIBLE_THEN_HIDDEN';p['hidden_fields']=[*p.get('hidden_fields',[]),'public_phone'];self.save('people',p);self.assertNotIn(b'VISIBLE_THEN_HIDDEN',self.client.request('/researchers/'+p['id']+'/')[1]);old['_version']=self.get('people',p['id'])['_version'];self.save('people',old)
    def test_27_custom_contact_assignment(self):
        p=self.create('contacts',self.new('contacts',label='Research office',kind='email',value='research-test@example.org',researcher_id='naungwe-simasiku',visibility='public'));self.assertIn(b'research-test@example.org',self.client.request('/researchers/naungwe-simasiku/')[1]);self.assertNotIn(b'research-test@example.org',self.client.request('/researchers/paulus-hamutenya/')[1])
    def test_28_source_does_not_accept_javascript(self):
        p=self.new('contacts',label='Unsafe',kind='website',value='javascript:alert(1)');status,_,_=self.client.request('/api/records/contacts','POST',p);self.assertEqual(status,422)
    def test_29_static_export_is_private_safe(self):
        dest=self.tmp/'export';proc=subprocess.run(['php','bin/console.php','build',str(dest)],cwd=ROOT,env=self.env,capture_output=True,text=True);self.assertEqual(proc.returncode,0,proc.stderr)
        text='\n'.join(p.read_text() for p in dest.rglob('*') if p.suffix in ('.html','.json','.xml','.js','.css'))
        self.assertNotIn(PASSWORD,text);self.assertNotIn('PRIVATE_SENTINEL',text);self.assertNotIn('owner-test-id',text);self.assertNotIn('/api/anonymous/token',text.split('Questions & privacy')[0]);self.assertTrue((dest/'researchers/paulus-hamutenya/index.html').exists());self.assertTrue((dest/'release.json').exists());self.assertIn('Online submissions are not connected yet', (dest/'questions/index.html').read_text());self.assertNotIn('data-anonymous', (dest/'questions/index.html').read_text())
    def test_30_literature_no_invention(self):
        status,result,_=self.client.request('/api/literature/sync','POST',{});self.assertEqual(status,200);self.assertEqual(result['inserted'],0);self.assertEqual(result['researchers'],0)
    def test_31_ui_assets(self):
        for path in ['/assets/admin.js','/assets/admin.css','/assets/site.js','/assets/site.css']:
            with self.subTest(path=path):self.assertEqual(self.client.request(path)[0],200)
    def test_32_no_private_upload_after_owner_unpublished(self):
        p,f=self.media('vevangapi-mbatara');owner=self.get('people','vevangapi-mbatara');old=dict(owner);owner['visibility']='private';self.save('people',owner);self.assertEqual(Client(self.base).request('/media/'+f['id'])[0],404);old['_version']=self.get('people',old['id'])['_version'];self.save('people',old)
if __name__=='__main__':unittest.main(verbosity=2)
