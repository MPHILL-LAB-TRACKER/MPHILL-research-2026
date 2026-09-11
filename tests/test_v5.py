"""V5 acceptance: deletion, privacy, contacts/fields, theming, media and Git exports."""
import io,json,shutil,subprocess,tempfile,unittest
from pathlib import Path
from PIL import Image
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.db import now
from backend.security import HASHER
from backend.media_v4 import process
from backend.release import release_files
from backend.content_update import upgrade_content

PASSWORD='V5 temporary acceptance testing password!'
ORIGIN='http://testserver'
class V5Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.encoded=HASHER.hash(PASSWORD)
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.app=create_app(self.root/'private/data.sqlite3',base_url=ORIGIN,production=False);self.store=self.app.state.store;self.store.seed()
        with self.store.connect(write=True) as c:
            for name,role,rid in [('owner','owner',''),('researcher','researcher','paulus-hamutenya')]:c.execute('INSERT INTO users VALUES(?,?,?,?,?,1,?)',(name,name,self.encoded,role,rid,now()))
        self.client=TestClient(self.app);self.login()
    def tearDown(self):self.client.close();self.tmp.cleanup()
    def login(self,name='owner'):
        self.client.cookies.clear();self.client.post('/api/login',headers={'Origin':ORIGIN},json={'username':name,'password':PASSWORD})
        self.headers={'Origin':ORIGIN,'X-CSRF-Token':self.client.get('/api/session').json()['user']['csrf']}
    def create(self,collection,data):
        r=self.client.post('/api/records/'+collection,headers=self.headers,json=data);self.assertEqual(r.status_code,200,r.text);return r.json()
    def update(self,collection,p):
        p={k:v for k,v in p.items() if k!='_updated_at'};r=self.client.put('/api/records/'+collection+'/'+p['id'],headers=self.headers,json=p);self.assertEqual(r.status_code,200,r.text);return r.json()
    def remove(self,c,p):return self.client.post('/api/records/'+c+'/'+p['id']+'/trash',headers=self.headers,json={'_version':p['_version']})
    def contact(self,**kw):return self.create('contacts',dict(id='research-contact',label='Research enquiries',kind='email',value='research@example.invalid',researcher_id='paulus-hamutenya',visibility='public',**kw))
    def image(self,fmt='PNG',mode='RGB'):
        buf=io.BytesIO();Image.new(mode,(32,24)).save(buf,fmt);return buf.getvalue()
    def upload(self,fmt='PNG',name='image.png'):
        r=self.client.post('/api/media/upload',headers=self.headers,files={'file':(name,self.image(fmt),'application/octet-stream')});self.assertEqual(r.status_code,200,r.text);return r.json()['record']
    def test_01_linked_contacts_are_public_only_when_approved(self):
        p=self.contact();self.assertEqual(self.client.get('/api/public').json()['contacts'][0]['value'],p['value']);p['visibility']='private';self.update('contacts',p);self.assertEqual(self.client.get('/api/public').json()['contacts'],[])
    def test_02_contact_omitted_when_researcher_is_private(self):
        self.contact();p=self.store.get('people','paulus-hamutenya');p['visibility']='private';self.update('people',p);self.assertEqual(self.client.get('/api/public').json()['contacts'],[])
    def test_03_field_link_validation(self):
        r=self.client.post('/api/records/fields',headers=self.headers,json={'id':'bad-field','label':'Other','target_collection':'people','target_id':'missing','kind':'text','value':'Test'});self.assertEqual(r.status_code,422)
    def test_04_private_custom_fields_never_export(self):
        self.create('fields',{'id':'private-field','label':'Private number','target_collection':'people','target_id':'paulus-hamutenya','kind':'text','value':'PRIVATE-V5-MARKER','visibility':'private'})
        self.assertNotIn('PRIVATE-V5-MARKER',self.client.get('/api/public').text);self.assertNotIn(b'PRIVATE-V5-MARKER',release_files(self.store,self.app.state.uploads)['index.html'])
    def test_05_custom_field_types_validate(self):
        for kind,value in [('email','bad-address'),('url','javascript:alert(1)'),('number','NaN'),('date','invalid')]:
            r=self.client.post('/api/records/fields',headers=self.headers,json={'id':'test-'+kind,'label':kind,'kind':kind,'value':value,'target_collection':'people','target_id':'paulus-hamutenya'});self.assertEqual(r.status_code,422,r.text)
    def test_06_hidden_builtin_field_not_in_public_data(self):
        p=self.store.get('people','paulus-hamutenya');p['public_email']='HIDDEN-V5-MARKER@example.invalid';p['hidden_fields']=['public_email'];self.update('people',p)
        self.assertNotIn('HIDDEN-V5-MARKER',self.client.get('/api/public').text);self.assertIn('HIDDEN-V5-MARKER',self.store.get('people','paulus-hamutenya')['public_email'])
    def test_07_cannot_hide_required_identity(self):
        p=self.store.get('people','paulus-hamutenya');p['hidden_fields']=['id'];p.pop('_updated_at');r=self.client.put('/api/records/people/'+p['id'],headers=self.headers,json=p);self.assertEqual(r.status_code,422)
    def test_08_trash_restore_private_and_migration_no_resurrection(self):
        p=self.store.get('people','jaydine-feris');self.assertEqual(self.remove('people',p).status_code,200);self.assertIsNone(self.store.get('people',p['id']))
        upgrade_content(self.store,apply=True);self.assertIsNone(self.store.get('people',p['id']));item=self.client.get('/api/trash').json()[0]
        r=self.client.post('/api/trash/people/'+p['id']+'/restore',headers=self.headers,json={'_version':item['_version']});self.assertEqual(r.status_code,200);self.assertEqual(r.json()['visibility'],'private')
    def test_09_stale_delete_refused(self):
        p=self.contact();p['label']='Edited contact';self.update('contacts',p);self.assertEqual(self.remove('contacts',p).status_code,409)
    def test_10_core_settings_protected(self):
        for c,rid in [('settings','laboratory'),('theme','website')]:self.assertEqual(self.remove(c,self.store.get(c,rid)).status_code,422)
    def test_11_permanent_delete_password_and_csrf(self):
        p=self.contact();self.remove('contacts',p);version=self.client.get('/api/trash').json()[0]['_version'];url='/api/trash/contacts/'+p['id']+'/purge'
        body={'_version':version,'confirmation':'DELETE','password':'wrong-password'}
        self.assertEqual(self.client.post(url,headers=self.headers,json=body).status_code,403)
        body['password']=PASSWORD;self.assertEqual(self.client.post(url,headers={'Origin':ORIGIN},json=body).status_code,403)
        self.assertEqual(self.client.post(url,headers=self.headers,json=body).status_code,200);self.assertEqual(self.client.get('/api/trash').json(),[])
        with self.store.connect() as c:self.assertIsNone(c.execute("SELECT 1 FROM records WHERE collection='contacts' AND id=?",(p['id'],)).fetchone());self.assertTrue(all(r[0] is None and r[1] is None for r in c.execute("SELECT before_json,after_json FROM audit WHERE collection='contacts' AND record_id=?",(p['id'],))))
    def test_12_linked_media_cannot_purge(self):
        p=self.upload();self.create('sections',{'id':'gallery','title':'Gallery','location':'homepage','media_items':[p['id']]});self.remove('media',p)
        item=self.client.get('/api/trash').json()[0];r=self.client.post('/api/trash/media/'+p['id']+'/purge',headers=self.headers,json={'_version':item['_version'],'confirmation':'DELETE','password':PASSWORD});self.assertEqual(r.status_code,409);self.assertIn('sections/gallery',r.text)
    def test_13_trashed_media_not_served_or_exported(self):
        p=self.upload();p.update(approved=True,visibility='public');p=self.update('media',p);uid=p['file_id'];self.remove('media',p)
        self.assertEqual(self.client.get('/api/public').json()['media'],[]);self.client.cookies.clear();self.assertEqual(self.client.get('/media/'+uid).status_code,401);self.assertNotIn(uid.encode(),release_files(self.store,self.app.state.uploads)['index.html'])
    def test_14_researcher_denied_administration(self):
        self.login('researcher');self.assertEqual(self.client.get('/api/trash').status_code,403);self.assertEqual(self.client.get('/api/system/info').status_code,403)
        self.assertEqual(self.client.post('/api/records/people/paulus-hamutenya/trash',headers=self.headers,json={'_version':1}).status_code,403)
    def test_15_multiple_image_formats(self):
        for fmt,suffix in [('JPEG','jpg'),('PNG','png'),('WEBP','webp'),('GIF','gif'),('BMP','bmp'),('TIFF','tiff')]:
            with self.subTest(fmt=fmt):self.assertEqual(self.upload(fmt,'test.'+suffix)['kind'],'image')
    def test_16_png_transparency_preserved(self):
        result=process(self.image('PNG','RGBA'),'transparent.png');self.assertEqual(result[1],'image/png');self.assertEqual(Image.open(io.BytesIO(result[0])).mode,'RGBA')
    def test_17_mp4_and_mov_real_conversion(self):
        if not shutil.which('ffmpeg'):self.skipTest('FFmpeg not installed')
        for suffix,codec in [('mp4','libx264'),('mov','mpeg4')]:
            dest=self.root/('test.'+suffix);subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=size=32x32:rate=5','-t','1','-c:v',codec,'-pix_fmt','yuv420p',str(dest)],check=True)
            r=self.client.post('/api/media/upload',headers=self.headers,files={'file':(dest.name,dest.read_bytes(),'video/'+suffix)});self.assertEqual(r.status_code,200,r.text);self.assertEqual(r.json()['upload']['mime'],'video/mp4')
    def test_18_theme_values_and_css_injection(self):
        p=self.store.get('theme','website');p['primary']='#225588';p['home_blocks']=['hero','contacts'];p=self.update('theme',p);self.assertEqual(self.client.get('/api/public').json()['theme'][0]['primary'],'#225588')
        p['primary']='red;}body{display:none}';p.pop('_updated_at');r=self.client.put('/api/records/theme/website',headers=self.headers,json=p);self.assertEqual(r.status_code,422)
    def test_19_theme_logo_owned_upload(self):
        r=self.client.post('/api/uploads/theme/website',headers=self.headers,files={'file':('logo.png',self.image('PNG','RGBA'),'image/png')});self.assertEqual(r.status_code,200,r.text)
        p=self.store.get('theme','website');p['logo_upload_id']=r.json()['id'];p['logo_approved']=True;self.update('theme',p);self.assertIn('logo_url',self.client.get('/api/public').json()['theme'][0]);files=release_files(self.store,self.app.state.uploads);self.assertTrue(any(x.endswith('.png') for x in files))
    def test_20_attachment_on_any_record_and_visibility(self):
        media=self.upload();p=self.store.get('people','paulus-hamutenya');p['media_items']=[media['id']];self.update('people',p)
        person=next(x for x in self.client.get('/api/public').json()['people'] if x['id']==p['id']);self.assertEqual(person['media_items'],[])
        media.update(approved=True,visibility='public');self.update('media',media)
        person=next(x for x in self.client.get('/api/public').json()['people'] if x['id']==p['id']);self.assertEqual(person['media_items'],[media['id']])
    def test_21_system_version_and_asset_cache(self):
        self.assertEqual(self.client.get('/api/system/info').json()['version'],'5.0.0');self.assertEqual(self.client.get('/assets/admin.js?v=5.0.0').headers['cache-control'],'no-store')
    def test_22_hidden_portrait_not_readded_by_asset_projection(self):
        p=self.store.get('people','naungwe-simasiku');p['hidden_fields']=['photo_url'];self.update('people',p);person=next(x for x in self.client.get('/api/public').json()['people'] if x['id']==p['id']);self.assertNotIn('photo_url',person)
