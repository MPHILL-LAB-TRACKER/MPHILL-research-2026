"""V7 release HTTP contracts plus the preserved V6.2 regression suite.
Network providers are not queried; a real PHP server, database and uploaded files are used.
"""
import base64,datetime,hashlib,io,json,os,pathlib,re,subprocess,time,unittest,zipfile
import test_http as base
import test_v62
class V7Tests(test_v62.V62Tests):
    def new(self,c,**values):
        p=super().new(c)
        for f in self.schemas[c]['fields']:
            if 'default' in f:p[f['key']]=f['default']
        p.update(values);return p
    def test_15_video_and_range(self):
        if not self.video:self.skipTest('ffmpeg/ffprobe unavailable')
        p,f=self.media(kind='video',data=self.video)
        self.assertEqual(f['mime'],'video/mp4')
        status,data,h=base.Client(self.base).request('/media/'+f['id'],headers={'Range':'bytes=0-31'})
        self.assertEqual(status,206);self.assertEqual(len(data),32);self.assertIn('bytes 0-31/',h['Content-Range'])
        html=self.client.request('/gallery/general/')[1]
        self.assertIn(b'playsinline',html);self.assertIn(b'preload="none"',html)
    def test_33_new_release_design_defaults(self):
        b=self.client.request('/api/bootstrap')[1]
        self.assertEqual(b['version'],'7.0.0');self.assertGreaterEqual(len(b['design']['presets']),18)
        self.assertIn('writing_projects',b['schemas']);self.assertIn(b'v7-hero',self.client.request('/')[1])
    def test_50_approved_export_links_all_exist(self):
        dest=self.tmp/'export-v7';p=subprocess.run(['php','bin/console.php','build',str(dest)],cwd=base.ROOT,env=self.env,text=True,capture_output=True);self.assertEqual(p.returncode,0,p.stderr)
        for html in dest.rglob('*.html'):
            for link in re.findall(r'(?:src|href)="(/MPHILL-research-2026/[^"#?]*)(?:[?#][^"]*)?"',html.read_text()):
                target=dest/link[len('/MPHILL-research-2026/'):];self.assertTrue(target.exists() or (target/'index.html').exists(),(html,link))
        self.assertEqual(json.loads((dest/'release.json').read_text())['version'],'7.0.0')
        for path in ['connect/index.html','resources/index.html','assets/v7.css','assets/v7.js','gallery/researchers/paulus-hamutenya/index.html','sw.js']:self.assertTrue((dest/path).is_file(),path)
        self.assertNotIn('community-admin-token',str(list(dest.rglob('*'))))
    def test_70_original_quote_library(self):
        quotes=self.client.request('/api/records/science_quotes')[1];mine=[p for p in quotes if p['id'].startswith('v7-reflection-')]
        self.assertEqual(len(mine),32);self.assertEqual(len(set(p['quote'] for p in mine)),32)
        self.assertTrue(all(p['attribution_type']=='original' and p['license']=='CC0-1.0' for p in mine))
        t=self.get('theme','website');t.update(original_quote_library=False);self.save('theme',t);self.assertNotIn(b'data-quote-id="v7-reflection-',self.client.request('/')[1]);t=self.get('theme','website');t['original_quote_library']=True;self.save('theme',t)
        self.assertIn(b'data-quote-id="v7-reflection-',self.client.request('/')[1])
    def test_71_quote_topic_filter(self):
        t=self.get('theme','website');t['quote_topics']=['NoSuchTopic'];self.save('theme',t);self.assertNotIn(b'data-quote-id="v7-reflection-',self.client.request('/')[1]);t=self.get('theme','website');t['quote_topics']=[];self.save('theme',t)
    def test_72_elapsed_event_stays_archived(self):
        p=self.create('announcements',self.new('announcements',title='Elapsed event fixture',description='A synthetic expiry test.',kind='conference',date_status='lab-supplied',start_date='2020-01-01',end_date='',homepage=True,visibility='public'))
        h=self.client.request('/')[1].decode();self.assertNotIn('Elapsed event fixture',h);self.assertIn(b'Elapsed event fixture',self.client.request('/activity/')[1]);self.assertIn(b'elapsed',self.client.request('/records/announcements/'+p['id']+'/')[1])
    def test_73_manual_closure(self):
        p=self.create('announcements',self.new('announcements',title='Future event fixture',description='A future event test.',kind='seminar',date_status='lab-supplied',start_date='2099-02-01',end_date='2099-02-02',homepage=True,visibility='public'))
        self.assertIn(b'Future event fixture',self.client.request('/')[1]);p['lifecycle']='cancelled';self.save('announcements',p);self.assertNotIn(b'Future event fixture',self.client.request('/')[1])
    def test_74_explicit_expiry_and_timezone(self):
        r=self.php("echo Ted2\\json([Ted2\\Research7::eventStatus(['start_date'=>'2026-10-01'],['lab_timezone'=>'Africa/Windhoek'],strtotime('2026-10-01T22:30:00Z')),Ted2\\Research7::eventStatus(['start_date'=>'2020-01-01','expires_on'=>'2099-01-01'],['lab_timezone'=>'Africa/Windhoek'])]);")
        self.assertEqual(r,['elapsed','open'])
    def test_75_album_owner_checks(self):
        a=self.create('albums',self.new('albums',title='A researcher album',scope='researcher',researcher_id='paulus-hamutenya',visibility='public'))
        m,_=self.media('naungwe-simasiku');m['album_id']=a['id'];self.assertEqual(self.client.request('/api/records/media/'+m['id'],'PUT',m)[0],422)
        m,_=self.media('paulus-hamutenya');m['album_id']=a['id'];self.save('media',m);self.assertIn(m['title'].encode(),self.client.request('/gallery/albums/'+a['id']+'/')[1]);a['researcher_id']='naungwe-simasiku';self.assertEqual(self.client.request('/api/records/albums/'+a['id'],'PUT',a)[0],409)
    def test_76_private_album_hides_media(self):
        a=self.create('albums',self.new('albums',title='Private album',scope='researcher',researcher_id='paulus-hamutenya'))
        m,f=self.media('paulus-hamutenya');m['album_id']=a['id'];self.save('media',m)
        guest=base.Client(self.base);self.assertEqual(guest.request('/media/'+f['id'])[0],404);self.assertEqual(guest.request('/gallery/albums/'+a['id']+'/')[0],404)
        self.assertNotIn(m['title'].encode(),self.client.request('/gallery/researchers/paulus-hamutenya/')[1])
        a['visibility']='public';a=self.save('albums',a);self.assertEqual(guest.request('/media/'+f['id'])[0],200)
        self.client.request('/api/records/albums/'+a['id'],'DELETE',{'_version':a['_version']});self.assertEqual(guest.request('/media/'+f['id'])[0],404)
    def test_77_private_writing_export(self):
        source='\\documentclass{article}\n\\begin{document}\nPrivate V7 fixture.\\end{document}'
        p=self.create('writing_projects',self.new('writing_projects',title='Writing fixture',researcher_id='paulus-hamutenya',main_tex=source,bibtex='@misc{test,title={Test}}'))
        status,b,h=self.client.request('/api/writing/'+p['id']+'/export');self.assertEqual(status,200);self.assertIn('no-store',h['Cache-Control']);z=zipfile.ZipFile(io.BytesIO(b));self.assertIsNone(z.testzip());self.assertEqual(z.read('main.tex').decode(),source)
        guest=base.Client(self.base);self.assertEqual(guest.request('/api/writing/'+p['id']+'/export')[0],401)
        p['visibility']='public';self.assertEqual(self.client.request('/api/records/writing_projects/'+p['id'],'PUT',p)[0],422)
        self.assertNotIn(b'Private V7 fixture',self.client.request('/')[1])
    def test_78_overleaf_requires_consent(self):
        p=self.create('writing_projects',self.new('writing_projects',title='Transfer fixture',researcher_id='paulus-hamutenya',main_tex='\\documentclass{article}\\begin{document}test\\end{document}'))
        self.assertEqual(self.client.request('/api/writing/'+p['id']+'/overleaf','POST',{})[0],422)
        status,r,_=self.client.request('/api/writing/'+p['id']+'/overleaf','POST',{'confirm_transfer':True});self.assertEqual(status,200);self.assertEqual(r['action'],'https://www.overleaf.com/docs');self.assertTrue(r['snip_uri'].startswith('data:application/zip;base64,'));z=zipfile.ZipFile(io.BytesIO(base64.b64decode(r['snip_uri'].split(',')[1])));self.assertEqual(z.read('main.tex').decode(),p['main_tex'])
        p['overleaf_url']='https://evil.example/project/a';self.assertEqual(self.client.request('/api/records/writing_projects/'+p['id'],'PUT',p)[0],422)
    def test_79_templates_are_source_not_execution(self):
        for kind in ['review','protocol','report']:
            status,r,_=self.client.request('/api/writing/template','POST',{'kind':kind});self.assertEqual(status,200);self.assertIn('\\begin{document}',r['source']);self.assertNotIn('\\write18',r['source'])
    def test_80_researcher_scoping_new_collections(self):
        status,r,_=self.client.request('/api/users','POST',{'username':'v7-researcher','role':'researcher','researcher_id':'paulus-hamutenya','password':base.PASSWORD,'active':True,'edit_profile':True,'edit_research':True});self.assertEqual(status,200,r)
        who=base.Client(self.base);who.login('v7-researcher')
        p=self.create('writing_projects',self.new('writing_projects',title='Owned writing',researcher_id='paulus-hamutenya'),who)
        q=self.create('writing_projects',self.new('writing_projects',title='Other writing',researcher_id='naungwe-simasiku'))
        self.assertEqual(who.request('/api/writing/'+q['id']+'/export')[0],403)
        self.create('albums',self.new('albums',title='Own private album',scope='researcher',researcher_id='paulus-hamutenya'),who)
        note=self.create('bench_notes',self.new('bench_notes',title='Owned note',researcher_id='paulus-hamutenya',date='2026-10-01',observations='Private observation fixture'),who)
        note['visibility']='public';self.assertEqual(who.request('/api/records/bench_notes/'+note['id'],'PUT',note)[0],422)
        self.assertEqual(who.request('/api/community-admin/messages')[0],403)
    def test_81_community_private_reply_and_receipt(self):
        guest=base.Client(self.base);challenge=guest.request('/api/community/challenge')[1];time.sleep(2.1)
        payload={'token':challenge['token'],'subject':'Direct reply fixture','message':'A private question for the test laboratory.','nickname':'','consent_public':False,'researcher_id':'paulus-hamutenya'}
        status,result,h=guest.request('/api/community/submit','POST',payload);self.assertEqual(status,201,result);self.assertIn('no-store',h['Cache-Control']);rid=result['id'];self.assertEqual(guest.request('/api/community/submit','POST',payload)[0],409)
        self.assertEqual(guest.request('/api/community/lookup','POST',{'id':rid,'receipt':'a'*48})[0],404)
        status,item,_=guest.request('/api/community/lookup','POST',{'id':rid,'receipt':result['receipt']});self.assertEqual(status,200);self.assertNotIn('receipt_hash',item['item'])
        self.assertEqual(self.client.request('/api/community-admin/messages/'+rid,'PUT',{'reply':'Response from the laboratory.','status':'public'})[0],422)
        self.assertEqual(self.client.request('/api/community-admin/messages/'+rid,'PUT',{'reply':'Response from the laboratory.','status':'answered'})[0],200)
        answer=guest.request('/api/community/lookup','POST',{'id':rid,'receipt':result['receipt']})[1];self.assertEqual(answer['item']['reply'],'Response from the laboratory.')
        self.assertNotIn(rid,json.dumps(guest.request('/api/community/public')[1]))
    def test_82_community_consent_public_and_delete(self):
        guest=base.Client(self.base);token=guest.request('/api/community/challenge')[1]['token'];time.sleep(2.1)
        status,p,_=guest.request('/api/community/submit','POST',{'token':token,'subject':'Public fixture','message':'Shareable science question test.','nickname':'Test','consent_public':True});self.assertEqual(status,201,p)
        self.assertEqual(self.client.request('/api/community-admin/messages/'+p['id'],'PUT',{'reply':'Reviewed reply test.','status':'public'})[0],200)
        self.assertIn(p['id'],json.dumps(guest.request('/api/community/public')[1]));self.assertEqual(self.client.request('/api/community-admin/messages/'+p['id'],'DELETE',{'confirm':'DELETE'})[0],200);self.assertNotIn(p['id'],json.dumps(guest.request('/api/community/public')[1]))
    def test_83_community_origin_challenge_size_and_privacy(self):
        guest=base.Client(self.base)
        self.assertEqual(guest.request('/api/community/submit','POST',{'token':'invalid'},headers={'Origin':'https://evil.example'})[0],403)
        self.assertEqual(guest.request('/api/community/submit','POST',{'token':'invalid'})[0],403)
        self.assertEqual(guest.request('/api/community-admin/status')[0],401)
        self.assertIn('no-store',guest.request('/connect/')[2]['Cache-Control'])
        s=self.get('settings','laboratory');s['community_endpoint']='http://127.0.0.1';self.assertEqual(self.client.request('/api/records/settings/laboratory','PUT',s)[0],422)
        s['community_endpoint']='https://localhost.workers.dev';self.assertEqual(self.client.request('/api/records/settings/laboratory','PUT',s)[0],422)
    def test_84_disabled_community(self):
        s=self.get('settings','laboratory');s['community_enabled']=False;self.save('settings',s);self.assertEqual(base.Client(self.base).request('/api/community/challenge')[0],403);self.assertNotIn(b'data-message>',self.client.request('/connect/')[1]);s=self.get('settings','laboratory');s['community_enabled']=True;self.save('settings',s)
    def test_85_new_resources_curatable(self):
        self.assertIn(b'eLabFTW',self.client.request('/resources/')[1]);r=self.create('resources',self.new('resources',title='Fixture resource',description='Test external tool entry.',url='https://example.org/',category='methods',visibility='public',homepage=True));self.assertIn(b'Fixture resource',self.client.request('/resources/')[1]);r['visibility']='private';self.save('resources',r);self.assertNotIn(b'Fixture resource',self.client.request('/resources/')[1])
    def test_86_v7_migration_idempotent_and_removed_quote_stays_removed(self):
        q=self.get('science_quotes','v7-reflection-32');self.client.request('/api/records/science_quotes/'+q['id'],'DELETE',{'_version':q['_version']});r=self.php('echo Ted2\\json(Ted2\\Upgrade7::apply($s));');self.assertTrue(r['already_upgraded']);self.assertEqual(self.client.request('/api/records/science_quotes/'+q['id'])[0],404)
    def test_87_no_server_tex_engine(self):
        for path in ['/api/latex/compile','/writing_projects/']:
            self.assertIn(self.client.request(path)[0],(404,405))
        self.assertIn('https://www.overleaf.com',self.client.request('/admin')[2]['Content-Security-Policy'])
if __name__=='__main__':unittest.main(verbosity=2)
