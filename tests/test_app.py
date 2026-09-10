"""Security and behavior regression tests. All accounts/data exist in temporary folders."""
from __future__ import annotations
import io,json,secrets,sqlite3,tempfile,time,unittest
from pathlib import Path
from PIL import Image
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.db import ROOT,now
from backend.schema import SCHEMAS,validate
from backend.security import HASHER,COOKIE
from backend.public import project_public
from backend.build import build_seed

PASSWORD='Temporary test password only 2026!'
ORIGIN='http://testserver'
def plain(p): return {k:v for k,v in p.items() if not k.startswith('_')}

class WorkspaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.encoded=HASHER.hash(PASSWORD)
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'test.sqlite3'
        self.app=create_app(self.path,base_url=ORIGIN,production=False);self.store=self.app.state.store;self.store.seed()
        with self.store.connect(write=True) as c:
            for uid,name,role,rid in [('owner1','owner-test','owner',''),('admin1','admin-test','admin',''),('a','researcher-a','researcher','paulus-hamutenya'),('b','researcher-b','researcher','vevangapi-mbatara')]:
                c.execute('INSERT INTO users VALUES(?,?,?,?,?,1,?)',(uid,name,self.encoded,role,rid,now()))
        self.client=TestClient(self.app)
    def tearDown(self): self.client.close();self.temp.cleanup()
    def login(self,name='owner-test',client=None):
        c=client or self.client
        response=c.post('/api/login',headers={'Origin':ORIGIN},json={'username':name,'password':PASSWORD})
        self.assertEqual(response.status_code,200,response.text)
        return c.get('/api/session').json()['user']
    def headers(self):
        u=self.client.get('/api/session').json()['user'];return {'Origin':ORIGIN,'X-CSRF-Token':u['csrf']}
    def save(self,collection,p):
        return self.client.post('/api/records/'+collection,headers=self.headers(),json=p)
    def update(self,c,p):
        b=plain(p);b['_version']=p['_version'];return self.client.put('/api/records/'+c+'/'+p['id'],headers=self.headers(),json=b)
    def project(self,id='project-one',person='paulus-hamutenya',visibility='private'):
        r=self.save('projects',{'id':id,'title':'Temporary research project','lead_id':person,'people':[person],'stage':'active','visibility':visibility,'internal_notes':'PRIVATE-PROJECT-NOTES'})
        self.assertEqual(r.status_code,200,r.text);return r.json()
    def manuscript(self,id='manuscript-one',people=None,visibility='private',project=''):
        r=self.save('manuscripts',{'id':id,'title':'PRIVATE-DRAFT-TITLE' if visibility=='private' else 'Approved manuscript status','people':people or ['paulus-hamutenya'],'project_id':project,'stage':'under-review','visibility':visibility,'internal_notes':'PRIVATE-REVIEWER-COMMENTS','submission_id':'SECRET-SUBMISSION-REFERENCE'})
        self.assertEqual(r.status_code,200,r.text);return r.json()
    def milestone(self,id='milestone-one',person='paulus-hamutenya',project='project-one'):
        r=self.save('milestones',{'id':id,'title':'Temporary milestone','researcher_id':person,'project_id':project,'status':'todo','weight':2,'visibility':'private'})
        self.assertEqual(r.status_code,200,r.text);return r.json()
    def upload(self,c,rid,raw,name):
        return self.client.post(f'/api/uploads/{c}/{rid}',headers=self.headers(),files={'file':(name,raw)})

    def test_01_corrected_roster_and_publisher_records(self):
        d=self.client.get('/api/public').json()
        self.assertEqual(len(d['people']),12);self.assertEqual(len(d['capabilities']),12)
        self.assertIn('Ms Vevangapi Mbatara',[p['name'] for p in d['people']]);self.assertNotIn('Ms Mbotarai Vevangapi',[p['name'] for p in d['people']])
        kp=[p for p in d['publications'] if 'nailoke-pauline-kadhila' in p['people']]
        self.assertEqual(len(kp),3);self.assertTrue(all(x['doi'] and x['type']=='peer-reviewed' for x in kp))
    def test_02_anonymous_private_api_blocked(self):
        for path in ['/api/bootstrap','/api/records/people/albertina-shatri','/api/users','/api/audit','/api/export/snapshot']:
            self.assertEqual(self.client.get(path).status_code,401,path)
    def test_03_admin_document_redirects_anonymous(self):
        response=self.client.get('/admin',follow_redirects=False)
        self.assertEqual(response.status_code,303);self.assertEqual(response.headers['location'],'/login?next=admin')
    def test_04_no_filesystem_exposure(self):
        for path in ['/var/ted2.sqlite3','/.env','/backend/app.py','/data/seed.json','/uploads/anything','/docs/../var/ted2.sqlite3']:
            self.assertEqual(self.client.get(path).status_code,404,path)
    def test_05_cookie_is_http_only_and_samesite_strict(self):
        r=self.client.post('/api/login',headers={'Origin':ORIGIN},json={'username':'owner-test','password':PASSWORD})
        self.assertIn('HttpOnly',r.headers['set-cookie']);self.assertIn('SameSite=strict',r.headers['set-cookie'])
        self.assertNotIn(PASSWORD,r.text)
    def test_06_login_requires_same_origin(self):
        for headers in [{},{'Origin':'https://attacker.invalid'}]:
            self.assertEqual(self.client.post('/api/login',headers=headers,json={'username':'owner-test','password':PASSWORD}).status_code,403)
    def test_07_mutations_require_csrf(self):
        self.login()
        for hdr in [{'Origin':ORIGIN},{'Origin':ORIGIN,'X-CSRF-Token':'bad'}]:
            self.assertEqual(self.client.post('/api/records/updates',headers=hdr,json={}).status_code,403)
    def test_08_valid_csrf_cannot_bypass_origin(self):
        self.login();h=self.headers();h['Origin']='https://attacker.invalid'
        self.assertEqual(self.client.post('/api/records/updates',headers=h,json={}).status_code,403)
    def test_09_researcher_cannot_open_admin_or_accounts(self):
        self.login('researcher-a')
        self.assertEqual(self.client.get('/admin').status_code,403)
        self.assertEqual(self.client.get('/workspace').status_code,200)
        self.assertEqual(self.client.get('/api/users').status_code,403)
        self.assertEqual(self.client.get('/api/export/snapshot').status_code,403)
    def test_10_researcher_cannot_read_another_private_record(self):
        self.login();p=self.project(person='vevangapi-mbatara');self.login('researcher-a')
        self.assertEqual(self.client.get('/api/records/projects/'+p['id']).status_code,403)
        self.assertEqual(self.client.get('/api/bootstrap').json()['records']['projects'],[])
    def test_11_researcher_can_update_own_private_milestone(self):
        self.login();self.project();m=self.milestone();self.login('researcher-a');m['status']='done'
        r=self.update('milestones',m);self.assertEqual(r.status_code,200,r.text);self.assertEqual(r.json()['status'],'done')
    def test_12_researcher_cannot_publish(self):
        self.login('researcher-a')
        r=self.save('manuscripts',{'id':'draft-public','title':'A title','people':['paulus-hamutenya'],'stage':'drafting','visibility':'public'})
        self.assertEqual(r.status_code,403)
    def test_13_researcher_cannot_edit_other_milestone(self):
        self.login();self.project(person='vevangapi-mbatara');m=self.milestone(person='vevangapi-mbatara');self.login('researcher-a');m['status']='done'
        self.assertEqual(self.update('milestones',m).status_code,403)
    def test_14_researcher_cannot_modify_public_manuscript(self):
        self.login();m=self.manuscript(visibility='public');self.login('researcher-a');m['title']='Unreviewed change'
        self.assertEqual(self.update('manuscripts',m).status_code,403)
    def test_15_researcher_cannot_change_coauthor_assignment(self):
        self.login();m=self.manuscript();self.login('researcher-a');m['people'].append('vevangapi-mbatara')
        self.assertEqual(self.update('manuscripts',m).status_code,403)
    def test_16_researcher_can_create_own_private_draft(self):
        self.login('researcher-a');m=self.manuscript()
        self.assertEqual(m['visibility'],'private')
    def test_17_public_projection_never_exposes_internal_fields(self):
        self.login();self.project(visibility='public');self.manuscript();self.manuscript('approved',visibility='public')
        self.save('funders',{'id':'test-funder','name':'Test funder','visibility':'public','amount':123456.78,'currency':'PRIVATE-CURRENCY','internal_notes':'PRIVATE-FUNDER-NOTE'})
        public=self.client.get('/api/public').text;snapshot=self.client.get('/api/export/snapshot').text
        for secret in ['PRIVATE-PROJECT-NOTES','PRIVATE-DRAFT-TITLE','PRIVATE-REVIEWER-COMMENTS','SECRET-SUBMISSION-REFERENCE','PRIVATE-CURRENCY','PRIVATE-FUNDER-NOTE','123456.78']:
            self.assertNotIn(secret,public);self.assertNotIn(secret,snapshot)
    def test_18_public_links_filter_private_relations(self):
        self.login();self.project();self.manuscript('approved',visibility='public',project='project-one')
        public=self.client.get('/api/public').json();m=next(p for p in public['manuscripts'] if p['id']=='approved')
        self.assertEqual(m['project_id'],'')
    def test_19_optimistic_conflicts_do_not_overwrite(self):
        self.login();p=self.project();p['summary']='First change';r=self.update('projects',p);self.assertEqual(r.status_code,200)
        p['summary']='Stale edit';self.assertEqual(self.update('projects',p).status_code,409)
        self.assertEqual(self.store.get('projects',p['id'])['summary'],'First change')
    def test_20_unknown_or_injection_fields_rejected(self):
        self.login();r=self.save('people',{'id':'injected','name':'Someone','group':'researcher','visibility':'public','password_hash':'not-allowed'})
        self.assertEqual(r.status_code,422)
        r=self.save('people',{'id':'bad-url','name':'Someone','group':'researcher','photo_url':'javascript:alert(1)'})
        self.assertEqual(r.status_code,422)
    def test_21_new_records_default_private(self):
        self.login();r=self.save('funders',{'id':'private-funder','name':'Private by default'})
        self.assertEqual(r.status_code,200);self.assertEqual(r.json()['visibility'],'private')
    def test_22_admin_cannot_grant_roles(self):
        self.login('admin-test')
        self.assertEqual(self.client.post('/api/users',headers=self.headers(),json={'username':'evil','password':PASSWORD,'role':'owner'}).status_code,403)
    def test_23_owner_can_add_and_revoke_researcher(self):
        self.login();r=self.client.post('/api/users',headers=self.headers(),json={'username':'new-researcher','password':PASSWORD,'role':'researcher','researcher_id':'paulus-hamutenya'})
        self.assertEqual(r.status_code,200,r.text);uid=r.json()['id']
        with TestClient(self.app) as other:
            self.login('new-researcher',other);self.assertEqual(other.get('/api/bootstrap').status_code,200)
            r=self.client.put('/api/users/'+uid,headers=self.headers(),json={'role':'researcher','active':False,'researcher_id':'paulus-hamutenya'})
            self.assertEqual(r.status_code,200);self.assertEqual(other.get('/api/bootstrap').status_code,401)
    def test_24_last_owner_cannot_be_removed(self):
        self.login();r=self.client.put('/api/users/owner1',headers=self.headers(),json={'role':'admin','active':True})
        self.assertEqual(r.status_code,409)
    def test_25_logout_revokes_session(self):
        self.login();token=self.client.cookies.get(COOKIE)
        self.assertEqual(self.client.post('/api/logout',headers=self.headers()).status_code,200)
        self.client.cookies.set(COOKIE,token)
        self.assertEqual(self.client.get('/api/bootstrap').status_code,401)
    def test_26_expired_session_is_denied(self):
        self.login()
        with self.store.connect(write=True) as c:c.execute('UPDATE sessions SET last_seen=0')
        self.assertEqual(self.client.get('/api/bootstrap').status_code,401)
    def test_27_login_rate_limit(self):
        for _ in range(8):
            self.assertEqual(self.client.post('/api/login',headers={'Origin':ORIGIN},json={'username':'wrong-account','password':'bad'}).status_code,401)
        self.assertEqual(self.client.post('/api/login',headers={'Origin':ORIGIN},json={'username':'wrong-account','password':'bad'}).status_code,429)
    def test_28_private_pdf_cannot_be_downloaded_anonymously(self):
        self.login();m=self.manuscript();r=self.upload('manuscripts',m['id'],b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF\n','draft.pdf')
        self.assertEqual(r.status_code,200,r.text);uid=r.json()['id'];m['document_id']=uid;self.assertEqual(self.update('manuscripts',m).status_code,200)
        self.assertEqual(self.client.get('/media/'+uid).status_code,200)
        with TestClient(self.app) as guest:self.assertEqual(guest.get('/media/'+uid).status_code,401)
    def test_29_public_manuscript_pdf_still_private(self):
        self.login();m=self.manuscript(visibility='public');r=self.upload('manuscripts',m['id'],b'%PDF-1.4\n%%EOF\n','draft.pdf');uid=r.json()['id'];m['document_id']=uid
        self.assertEqual(self.update('manuscripts',m).status_code,200)
        with TestClient(self.app) as guest:self.assertEqual(guest.get('/media/'+uid).status_code,401)
        self.assertNotIn(uid,self.client.get('/api/public').text)
    def test_30_unapproved_photo_is_private(self):
        self.login();p=self.store.get('people','paulus-hamutenya');b=io.BytesIO();Image.new('RGB',(30,30)).save(b,'PNG')
        r=self.upload('people',p['id'],b.getvalue(),'portrait.png');self.assertEqual(r.status_code,200,r.text);uid=r.json()['id'];p['photo_upload_id']=uid;p['photo_permission']='unconfirmed'
        self.assertEqual(self.update('people',p).status_code,200)
        with TestClient(self.app) as guest:self.assertEqual(guest.get('/media/'+uid).status_code,401)
        p=self.store.get('people',p['id']);p['photo_permission']='approved';self.assertEqual(self.update('people',p).status_code,200)
        with TestClient(self.app) as guest:self.assertEqual(guest.get('/media/'+uid).status_code,200)
        image=Image.open(io.BytesIO(self.client.get('/media/'+uid).content));self.assertEqual(image.format,'JPEG');self.assertEqual(len(image.getexif()),0)
    def test_31_upload_svg_and_active_pdf_rejected(self):
        self.login();r=self.upload('people','albertina-shatri',b'<svg onload="alert(1)"></svg>','portrait.svg');self.assertEqual(r.status_code,422)
        m=self.manuscript();r=self.upload('manuscripts',m['id'],b'%PDF-1.4\n/JavaScript bad\n%%EOF','active.pdf');self.assertEqual(r.status_code,422)
    def test_32_upload_cannot_be_attached_to_other_record(self):
        self.login();a=self.manuscript();b=self.manuscript('other-draft');r=self.upload('manuscripts',a['id'],b'%PDF-1.4\n%%EOF','draft.pdf');b['document_id']=r.json()['id']
        self.assertEqual(self.update('manuscripts',b).status_code,422)
    def test_33_researcher_cannot_upload_to_anothers_record(self):
        self.login();m=self.manuscript(people=['vevangapi-mbatara']);self.login('researcher-a')
        self.assertEqual(self.upload('manuscripts',m['id'],b'%PDF-1.4\n%%EOF','draft.pdf').status_code,403)
    def test_34_public_cors_never_enables_credentials(self):
        origin='https://mphill-lab-tracker.github.io';r=self.client.get('/api/public',headers={'Origin':origin})
        self.assertEqual(r.headers['access-control-allow-origin'],origin);self.assertNotIn('access-control-allow-credentials',r.headers)
        self.login();r=self.client.get('/api/bootstrap',headers={'Origin':origin});self.assertNotIn('access-control-allow-origin',r.headers)
    def test_35_unsafe_origin_not_allowed(self):
        r=self.client.get('/api/public',headers={'Origin':'https://other.invalid'});self.assertNotIn('access-control-allow-origin',r.headers)
    def test_36_security_headers_and_no_store(self):
        r=self.client.get('/login');self.assertEqual(r.headers['x-frame-options'],'DENY');self.assertEqual(r.headers['cache-control'],'no-store');self.assertIn("script-src 'self'",r.headers['content-security-policy'])
        self.assertEqual(self.client.get('/api/public').headers['x-content-type-options'],'nosniff')
    def test_37_production_requires_https(self):
        with self.assertRaises(RuntimeError):create_app(self.path,base_url='http://public.example.org',production=True)
        with self.assertRaises(RuntimeError):create_app(self.path,base_url='https://public.example.org/path',production=True)
    def test_38_connected_export_contains_no_research_records(self):
        self.login();self.manuscript();html=self.client.get('/api/export/connected').text
        self.assertIn('"live":true',html);self.assertIn('"apiBase":"http://testserver"',html)
        self.assertIn('window.TED2_DATA={}',html);self.assertNotIn('PRIVATE-DRAFT-TITLE',html);self.assertNotIn(self.encoded,html)
    def test_39_removed_photo_and_original_homepage_content(self):
        html=(ROOT/'index.html').read_text();self.assertNotIn('photo-1631556096543-23fdcb5896da',html)
        seed=json.loads((ROOT/'data/seed.json').read_text())
        for cap in seed['capabilities']:self.assertIn(cap['text'].replace('&','\\u0026'),html)
    def test_40_audit_events_exclude_passwords(self):
        self.login();self.project();logs=self.client.get('/api/audit').json();self.assertTrue(any(x['action']=='create' for x in logs))
        with self.store.connect() as c: events=''.join(str(tuple(r)) for r in c.execute('SELECT * FROM audit'))
        self.assertNotIn(PASSWORD,events);self.assertNotIn(self.encoded,events)
    def test_41_password_change_revokes_all_sessions(self):
        self.login();new='A different temporary password 2026!'
        r=self.client.post('/api/password',headers=self.headers(),json={'current':PASSWORD,'password':new});self.assertEqual(r.status_code,200)
        self.assertEqual(self.client.get('/api/bootstrap').status_code,401)
        self.assertEqual(self.client.post('/api/login',headers={'Origin':ORIGIN},json={'username':'owner-test','password':PASSWORD}).status_code,401)
        self.assertEqual(self.client.post('/api/login',headers={'Origin':ORIGIN},json={'username':'owner-test','password':new}).status_code,200)
    def test_42_dates_and_references_validated(self):
        self.login();r=self.save('projects',{'id':'bad-dates','title':'Invalid dates','lead_id':'paulus-hamutenya','stage':'active','start_date':'2026-10-01','due_date':'2026-09-01'})
        self.assertEqual(r.status_code,422)
        r=self.save('projects',{'id':'missing-person','title':'Missing person','lead_id':'missing-person','stage':'active'})
        self.assertEqual(r.status_code,422)
    def test_43_unpublishing_removes_public_photo_access(self):
        self.login();p=self.store.get('people','paulus-hamutenya');b=io.BytesIO();Image.new('RGB',(25,25)).save(b,'JPEG');r=self.upload('people',p['id'],b.getvalue(),'p.jpg');uid=r.json()['id'];p['photo_upload_id']=uid;p['photo_permission']='approved';p=self.update('people',p).json()
        with TestClient(self.app) as guest:self.assertEqual(guest.get('/media/'+uid).status_code,200)
        p['visibility']='private';self.assertEqual(self.update('people',p).status_code,200)
        with TestClient(self.app) as guest:self.assertEqual(guest.get('/media/'+uid).status_code,401)
    def test_44_request_size_limit(self):
        r=self.client.post('/api/login',headers={'Origin':ORIGIN,'Content-Length':str(23*1024*1024)},content=b'x')
        self.assertEqual(r.status_code,413)
    def test_45_initial_source_does_not_invent_active_research(self):
        d=self.client.get('/api/public').json()
        self.assertEqual(d['projects'],[]);self.assertEqual(d['manuscripts'],[]);self.assertEqual(d['milestones'],[]);self.assertEqual(d['funders'],[])
    def test_46_json_escaping_in_public_export(self):
        self.login();p=self.store.get('people','paulus-hamutenya');p['bio']='</script><script>alert("bad")</script>'
        self.assertEqual(self.update('people',p).status_code,200)
        html=self.client.get('/api/export/snapshot').text
        self.assertNotIn('</script><script>alert("bad")</script>',html)
        self.assertIn('\\u003c/script\\u003e',html)

if __name__=='__main__': unittest.main(verbosity=2)
