"""V4 behavior tests: media, privacy, migration and real Git objects in local remotes."""
from __future__ import annotations
import base64,io,json,os,shutil,subprocess,tempfile,unittest
from pathlib import Path
from PIL import Image
from fastapi import HTTPException
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.db import ROOT,now
from backend.security import HASHER
from backend.publisher import Publisher
from backend.media_v4 import process
from backend.release import release_files,fingerprint
from backend.content_update import upgrade_content
PASSWORD='Temporary V4 testing password 2026!'
ORIGIN='http://testserver'

def git(root,*args):
    return subprocess.run(['git','-C',str(root),*args],check=True,capture_output=True,text=True).stdout.strip()
def photo():
    stream=io.BytesIO();Image.new('RGB',(30,20)).save(stream,'PNG');return stream.getvalue()
class V4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.encoded=HASHER.hash(PASSWORD)
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.app=create_app(self.root/'runtime/db.sqlite3',base_url=ORIGIN,production=False);self.store=self.app.state.store;self.store.seed()
        with self.store.connect(write=True) as c:
            for uid,role,rid in [('owner','owner',''),('researcher','researcher','paulus-hamutenya')]:c.execute('INSERT INTO users VALUES(?,?,?,?,?,1,?)',(uid,uid,self.encoded,role,rid,now()))
        self.client=TestClient(self.app);self.login()
    def tearDown(self):self.client.close();self.temp.cleanup()
    def login(self,name='owner'):
        self.client.cookies.clear();res=self.client.post('/api/login',headers={'Origin':ORIGIN},json={'username':name,'password':PASSWORD});self.assertEqual(res.status_code,200)
        self.user=self.client.get('/api/session').json()['user'];self.headers={'Origin':ORIGIN,'X-CSRF-Token':self.user['csrf']}
    def update(self,col,p):
        p={k:v for k,v in p.items() if k!='_updated_at'}
        res=self.client.put('/api/records/'+col+'/'+p['id'],headers=self.headers,json=p);self.assertEqual(res.status_code,200,res.text);return res.json()
    def upload(self):
        res=self.client.post('/api/media/upload',headers=self.headers,files={'file':('photo.png',photo(),'image/png')});self.assertEqual(res.status_code,200,res.text);return res.json()['record']
    def approve(self,p):p.update(approved=True,visibility='public');return self.update('media',p)
    def setup_repo(self):
        repo=self.root/'clone';repo.mkdir();remote=self.root/'remote.git';subprocess.run(['git','init','--bare',str(remote)],check=True,capture_output=True)
        git(repo,'init','-b','main');git(repo,'config','user.name','Temporary tester');git(repo,'config','user.email','tester@example.invalid');(repo/'source.txt').write_text('source');git(repo,'add','source.txt');git(repo,'commit','-m','Test baseline');git(repo,'remote','add','origin',str(remote))
        publisher=Publisher(self.store,self.app.state.uploads,repo,allow_local_remote=True);self.app.state.publisher=publisher
        return repo,remote,publisher
    def test_01_upload_starts_private(self):
        p=self.upload();self.assertFalse(p['approved']);self.assertEqual(p['visibility'],'private');self.assertEqual(self.client.get('/api/public').json()['media'],[])
    def test_02_approved_media_exports(self):
        p=self.approve(self.upload());public=self.client.get('/api/public').json()['media'][0];self.assertEqual(public['asset_url'],ORIGIN+'/media/'+p['file_id']);self.assertNotIn('file_id',public)
        files=release_files(self.store,self.app.state.uploads);self.assertTrue(any(n.startswith('public-media/') for n in files));self.assertNotIn(('/media/'+p['file_id']).encode(),files['index.html'])
    def test_03_public_without_approval_not_exported(self):
        p=self.upload();p['visibility']='public';self.update('media',p);self.assertEqual(self.client.get('/api/public').json()['media'],[])
    def test_04_private_media_requires_login(self):
        p=self.upload();self.client.cookies.clear();self.assertEqual(self.client.get('/media/'+p['file_id']).status_code,401)
    def test_05_researcher_cannot_upload_library(self):
        self.login('researcher');self.assertEqual(self.client.post('/api/media/upload',headers=self.headers,files={'file':('a.png',photo(),'image/png')}).status_code,403)
    def test_06_csrf_enforced_for_media(self):
        self.assertEqual(self.client.post('/api/media/upload',headers={'Origin':ORIGIN},files={'file':('a.png',photo(),'image/png')}).status_code,403)
    def test_07_private_contacts_excluded(self):
        p=self.store.get('people','paulus-hamutenya');p.update(private_email='private@example.invalid',private_phone='PRIVATE-PHONE-MARKER',private_address='PRIVATE-ADDRESS-MARKER',public_email='public@example.invalid');self.update('people',p)
        text=self.client.get('/api/public').text;self.assertNotIn('private@example.invalid',text);self.assertNotIn('PRIVATE-PHONE',text);self.assertIn('public@example.invalid',text)
        self.assertNotIn(b'PRIVATE-ADDRESS',release_files(self.store,self.app.state.uploads,embedded=True)['index.html'])
    def test_08_sections_filter_private_media(self):
        p=self.upload();res=self.client.post('/api/records/sections',headers=self.headers,json={'id':'gallery','title':'Gallery','location':'homepage','body':'Test gallery','visibility':'public','media_items':[p['id']]});self.assertEqual(res.status_code,200,res.text);self.assertEqual(self.client.get('/api/public').json()['sections'][0]['media_items'],[])
    def test_09_bad_svg_rejected(self):
        res=self.client.post('/api/media/upload',headers=self.headers,files={'file':('image.svg',b'<svg onload="alert(1)"/>','image/svg+xml')});self.assertEqual(res.status_code,422)
    def test_10_invalid_video_rejected(self):
        with self.assertRaises(HTTPException):process(b'not a video','test.mp4')
    def test_11_video_supported_container(self):
        if not shutil.which('ffmpeg'):self.skipTest('ffmpeg unavailable')
        p=self.root/'sample.mp4';subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=size=32x32:rate=5','-t','1','-c:v','libx264','-pix_fmt','yuv420p',str(p)],check=True)
        result=process(p.read_bytes(),'clip.mp4');self.assertEqual(result[1],'video/mp4')
    def test_12_media_type_mismatch(self):
        p=self.upload();p['kind']='video';body={k:v for k,v in p.items() if k!='_updated_at'};self.assertEqual(self.client.put('/api/records/media/'+p['id'],headers=self.headers,json=body).status_code,422)
    def test_13_filename_traversal_normalized(self):
        res=self.client.post('/api/media/upload',headers=self.headers,files={'file':('../../test.png',photo(),'image/png')});self.assertEqual(res.status_code,200);self.assertEqual(res.json()['upload']['name'],'test.png')
    def test_14_prepare_requires_admin(self):
        self.login('researcher');self.assertEqual(self.client.post('/api/publish/prepare',headers=self.headers).status_code,403)
    def test_15_password_required_per_push(self):
        self.setup_repo();release=self.client.post('/api/publish/prepare',headers=self.headers).json();res=self.client.post('/api/publish/confirm',headers=self.headers,json={'preview_id':release['id'],'password':'wrong'});self.assertEqual(res.status_code,403)
    def test_16_real_push_preserves_source_and_index(self):
        repo,remote,pub=self.setup_repo();(repo/'source.txt').write_text('staged source edit');git(repo,'add','source.txt');before=git(repo,'diff','--cached');head=git(repo,'rev-parse','HEAD');self.approve(self.upload())
        release=pub.prepare(self.user);result=pub.push(release['id'],self.user)
        self.assertEqual(git(repo,'rev-parse','HEAD'),head);self.assertEqual(git(repo,'diff','--cached'),before);self.assertEqual(git(repo,'branch','--show-current'),'main')
        paths=git(remote,'ls-tree','-r','--name-only','gh-pages').splitlines();self.assertIn('index.html',paths);self.assertNotIn('source.txt',paths);self.assertTrue(all(p in ('index.html','.nojekyll') or p.startswith('public-media/') for p in paths));self.assertTrue(result['ok'])
    def test_17_stale_preview_refused(self):
        _,_,pub=self.setup_repo();release=pub.prepare(self.user);p=self.store.get('settings','laboratory');p['hero_intro']='Edited since preview';self.update('settings',p)
        with self.assertRaises(HTTPException) as caught:pub.push(release['id'],self.user)
        self.assertEqual(caught.exception.status_code,409)
    def test_18_preview_replay_refused(self):
        _,_,pub=self.setup_repo();release=pub.prepare(self.user);pub.push(release['id'],self.user)
        with self.assertRaises(HTTPException):pub.push(release['id'],self.user)
    def test_19_remote_history_is_preserved(self):
        repo,remote,pub=self.setup_repo();first=pub.push(pub.prepare(self.user)['id'],self.user)['commit'];p=self.store.get('settings','laboratory');p['hero_intro']='Second release';self.update('settings',p);second=pub.push(pub.prepare(self.user)['id'],self.user)['commit'];self.assertEqual(git(repo,'rev-parse',second+'^'),first)
    def test_20_publication_pdf_embedded(self):
        p=self.store.list('publications')[0];res=self.client.post('/api/uploads/publications/'+p['id'],headers=self.headers,files={'file':('paper.pdf',b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF','application/pdf')});self.assertEqual(res.status_code,200);p.update(document_id=res.json()['id'],document_public=True);self.update('publications',p)
        self.assertIn(b'data:application/pdf;base64,',release_files(self.store,self.app.state.uploads,embedded=True)['index.html'])
    def test_21_portrait_cannot_accept_pdf(self):
        r=self.client.post('/api/uploads/people/paulus-hamutenya',headers=self.headers,files={'file':('a.pdf',b'%PDF-1.4\n%%EOF','application/pdf')});self.assertEqual(r.status_code,422)
    def test_22_v3_upgrade_preserves_owner_edits(self):
        v3=json.loads((ROOT/'data/updates/v3-baseline.json').read_text())
        with self.store.connect(write=True) as c:
            c.execute('DELETE FROM records')
            for col,rows in v3.items():
                for p in rows:
                    if p['id']=='paulus-hamutenya':p['bio']='MY CUSTOM BIO'
                    c.execute('INSERT INTO records VALUES(?,?,?,?,1,?,?)',(col,p['id'],json.dumps(p),p['visibility'],'seed',now()))
        report=upgrade_content(self.store,apply=True);self.assertTrue(Path(report['backup']).exists());self.assertEqual(self.store.get('people','paulus-hamutenya')['bio'],'MY CUSTOM BIO');self.assertEqual(self.store.get('people','jaydine-feris')['name'],'Ms Jaydine Feris');self.assertEqual(self.store.get('people','naungwe-simasiku')['bundled_portrait'],'naungwe-simasiku-v4');self.assertEqual(upgrade_content(self.store,apply=True)['updated'],[])
    def test_23_unapproved_file_not_fetchable_after_revoke(self):
        p=self.approve(self.upload());url='/media/'+p['file_id'];p['approved']=False;self.update('media',p);self.client.cookies.clear();self.assertEqual(self.client.get(url).status_code,401)
    def test_24_invalid_remote_is_blocked(self):
        repo,_,_=self.setup_repo();git(repo,'remote','set-url','origin','https://example.invalid/repo.git');pub=Publisher(self.store,self.app.state.uploads,repo)
        with self.assertRaises(HTTPException):pub.configuration()
    def test_25_confirm_success_and_password_not_audited(self):
        _,_,pub=self.setup_repo();rid=pub.prepare(self.user)['id'];res=self.client.post('/api/publish/confirm',headers=self.headers,json={'preview_id':rid,'password':PASSWORD});self.assertEqual(res.status_code,200,res.text)
        with self.store.connect() as c:text=' '.join(str(tuple(r)) for r in c.execute('SELECT * FROM audit'))
        self.assertNotIn(PASSWORD,text)
    def test_26_preview_is_not_anonymous(self):
        _,_,pub=self.setup_repo();rid=pub.prepare(self.user)['id'];self.client.cookies.clear();self.assertEqual(self.client.get(f'/api/publish/preview/{rid}/index.html').status_code,401)
    def test_27_snapshot_deterministic(self):
        a=release_files(self.store,self.app.state.uploads);b=release_files(self.store,self.app.state.uploads);self.assertEqual(fingerprint(a),fingerprint(b))
    def test_28_homepage_upload_approval(self):
        p=self.store.get('settings','laboratory');r=self.client.post('/api/uploads/settings/laboratory',headers=self.headers,files={'file':('hero.png',photo(),'image/png')});self.assertEqual(r.status_code,200);p.update(hero_upload_id=r.json()['id'],hero_permission='approved');self.update('settings',p);self.assertEqual(self.client.get('/api/public').json()['settings'][0]['hero_image_url'],ORIGIN+r.json()['url'])
if __name__=='__main__':unittest.main()
