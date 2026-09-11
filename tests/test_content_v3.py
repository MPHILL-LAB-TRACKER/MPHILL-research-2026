"""Source mappings, public certificate boundaries and conservative content upgrades."""
from __future__ import annotations
import base64
import copy
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.db import ROOT, now, Store
from backend.schema import validate
from backend.public import project_public
from backend.content_update import upgrade_content
from backend.assets import ASSET_ROOT
from manage import create_owner

class ContentV3Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'lab.sqlite3'
        self.app=create_app(self.path,base_url='http://testserver',production=False)
        self.store=self.app.state.store;self.store.seed();self.client=TestClient(self.app)
        self.seed=json.loads((ROOT/'data/seed.json').read_text())
    def tearDown(self):
        self.client.close();self.temp.cleanup()
    def owner(self):
        create_owner(self.store,'content-owner','Temporary test password only 2026!')
        response=self.client.post('/api/login',headers={'Origin':'http://testserver'},json={'username':'content-owner','password':'Temporary test password only 2026!'})
        self.assertEqual(response.status_code,200)
        user=self.client.get('/api/session').json()['user']
        return {'Origin':'http://testserver','X-CSRF-Token':user['csrf']}
    def test_01_all_eleven_presented_people_have_local_portraits(self):
        public=self.client.get('/api/public').json();portraits=[p for p in public['people'] if p['photo_url'].startswith('data:image/jpeg;base64,')]
        self.assertEqual(len(portraits),12)
        for p in portraits:
            image=Image.open(io.BytesIO(base64.b64decode(p['photo_url'].split(',',1)[1])))
            self.assertGreaterEqual(image.width,200);self.assertGreaterEqual(image.height,200)
            self.assertNotIn('bundled_portrait',p)
    def test_02_corrected_names_follow_team_presentation(self):
        names={p['name'] for p in self.client.get('/api/public').json()['people']}
        self.assertTrue({'Dr Albertina Shatri','Ms Denise Bouman','Dr Maneria Halweendo','Ms Charity Maepa','Ms Nonku Phili','Ms Jaydine Feris','Ms Vevangapi Mbatara'}.issubset(names))
        self.assertIn('Prof Nailoke Pauline Kadhila',names)
    def test_03_postgraduate_topics_are_assigned_to_the_correct_captions(self):
        p={x['id']:x for x in self.seed['people']}
        for rid,term in [('naungwe-simasiku','Acute Dental Abscesses'),('vevangapi-mbatara','Apoptosis-inducing'),('paulus-hamutenya','Aptamer-functionalised'),('jaydine-feris','Resistance Genes')]:
            self.assertIn(term,p[rid]['work']);self.assertTrue(p[rid]['role'].startswith('Postgraduate student'))
    def test_04_ncrst_dates_are_preserved_and_explicitly_flagged(self):
        a=[x for x in self.seed['announcements'] if 'ncrst' in x['id']]
        self.assertEqual(len(a),2)
        for x in a:
            self.assertEqual(x['start_date'],'2026-11-17');self.assertEqual(x['end_date'],'2026-11-18')
            self.assertEqual(x['official_start_date'],'2026-09-17');self.assertEqual(x['date_status'],'date-conflict')
            self.assertIn('17–18 September 2026',x['evidence_note']);self.assertIn('ncrst.na',x['official_url'])
    def test_05_sanord_dates_and_undated_seminar(self):
        a={x['id']:x for x in self.seed['announcements']}
        self.assertEqual(a['shatri-sanord-2026']['end_date'],'2026-09-25')
        self.assertEqual(a['shatri-sanord-2026']['official_url'],'https://www.unam.edu.na/sanord')
        seminar=a['nanomedicine-in-health-seminars'];self.assertEqual(seminar['date_status'],'date-to-be-announced');self.assertEqual(seminar['start_date'],'')
        self.assertEqual(seminar['title'],'Nanomedicine in Health')
    def test_06_no_instagram_destination_or_internal_reference_leaks(self):
        public=self.client.get('/api/public').text
        self.assertNotIn('instagram.com',public);self.assertNotIn('internal_notes',public)
    def test_07_original_certificate_is_embedded_byte_for_byte(self):
        a=self.client.get('/api/public').json()['achievements'][0]
        expected=(ASSET_ROOT/'certificates/falling-walls-paulus-hamutenya-2026.pdf').read_bytes()
        self.assertEqual(base64.b64decode(a['document_url'].split(',',1)[1]),expected)
        self.assertTrue(a['certificate_preview'].startswith('data:image/jpeg;base64,'))
        self.assertNotIn('certificate_key',a)
    def test_08_rank_claim_is_distinguished_from_certificate(self):
        a=self.seed['achievements'][0]
        self.assertIn('90 candidates',a['summary']);self.assertIn('top 16',a['summary']);self.assertIn('did not place in the final top three',a['summary'])
        self.assertIn('not printed on the certificate',a['evidence_note'])
    def test_09_unapproved_certificate_never_serializes(self):
        s=copy.deepcopy(self.seed);s['achievements'][0]['document_public']=False
        a=project_public(s)['achievements'][0]
        self.assertNotIn('document_url',a);self.assertNotIn('certificate_preview',a)
    def test_10_private_achievement_never_serializes(self):
        s=copy.deepcopy(self.seed);s['achievements'][0]['visibility']='private'
        self.assertEqual(project_public(s)['achievements'],[])
    def test_11_private_researcher_suppresses_named_announcements_and_awards(self):
        s=copy.deepcopy(self.seed)
        for p in s['people']:
            if p['id'] in ('paulus-hamutenya','albertina-shatri'):p['visibility']='private'
        result=project_public(s)
        self.assertEqual(result['achievements'],[])
        self.assertFalse(any('shatri' in x['id'] for x in result['announcements']))
    def test_12_unapproved_bundled_portrait_is_not_serialized(self):
        s=copy.deepcopy(self.seed);s['people'][0]['photo_permission']='unconfirmed'
        p=next(x for x in project_public(s)['people'] if x['id']=='albertina-shatri')
        self.assertEqual(p['photo_url'],'')
    def test_13_bundled_asset_path_traversal_is_rejected(self):
        p=copy.deepcopy(self.seed['people'][0]);p['bundled_portrait']='../../private'
        with self.assertRaises(ValueError):validate('people',p)
        a=copy.deepcopy(self.seed['achievements'][0]);a['certificate_key']='../../private'
        with self.assertRaises(ValueError):validate('achievements',a)
    def test_14_date_validation_rejects_reverse_or_unexplained_dates(self):
        a=copy.deepcopy(self.seed['announcements'][0]);a['end_date']='2026-08-10'
        with self.assertRaises(ValueError):validate('announcements',a)
        a=copy.deepcopy(self.seed['announcements'][1]);a['evidence_note']=''
        with self.assertRaises(ValueError):validate('announcements',a)
        a=copy.deepcopy(self.seed['announcements'][0]);a['date_status']='date-to-be-announced'
        with self.assertRaises(ValueError):validate('announcements',a)
    def test_15_admin_can_edit_notice_and_change_its_public_visibility(self):
        headers=self.owner();p=self.store.get('announcements','shatri-ncrst-2026');body={k:v for k,v in p.items() if k!='_updated_at'}
        body['visibility']='private'
        response=self.client.put('/api/records/announcements/shatri-ncrst-2026',headers=headers,json=body)
        self.assertEqual(response.status_code,200,response.text)
        self.assertNotIn('shatri-ncrst-2026',[x['id'] for x in self.client.get('/api/public').json()['announcements']])
    def test_16_upload_replacement_certificate_respects_explicit_approval(self):
        headers=self.owner();raw=(ASSET_ROOT/'certificates/falling-walls-paulus-hamutenya-2026.pdf').read_bytes()
        upload=self.client.post('/api/uploads/achievements/paulus-falling-walls-2026',headers=headers,files={'file':('replacement.pdf',raw,'application/pdf')})
        self.assertEqual(upload.status_code,200,upload.text);uid=upload.json()['id']
        p=self.store.get('achievements','paulus-falling-walls-2026');body={k:v for k,v in p.items() if k!='_updated_at'};body['document_id']=uid;body['document_public']=False
        response=self.client.put('/api/records/achievements/paulus-falling-walls-2026',headers=headers,json=body);self.assertEqual(response.status_code,200,response.text)
        anonymous=TestClient(self.app);self.assertEqual(anonymous.get('/media/'+uid).status_code,401)
        body=response.json();body.pop('_updated_at',None);body['document_public']=True
        response=self.client.put('/api/records/achievements/paulus-falling-walls-2026',headers=headers,json=body);self.assertEqual(response.status_code,200,response.text)
        a=self.client.get('/api/public').json()['achievements'][0];self.assertEqual(a['document_url'],'http://testserver/media/'+uid);self.assertNotIn('certificate_preview',a)
        self.assertEqual(anonymous.get('/media/'+uid).content,raw);anonymous.close()
        snap=self.client.get('/api/export/snapshot').text;self.assertIn('data:application/pdf;base64,',snap)
    def test_17_managed_asset_directory_is_not_publicly_mounted(self):
        for url in ['/data/assets/certificates/falling-walls-paulus-hamutenya-2026.pdf','/data/assets/portraits/paulus-hamutenya.jpg','/api/records/achievements/paulus-falling-walls-2026']:
            self.assertIn(self.client.get(url).status_code,(401,404))
    def test_18_new_collections_require_admin_permissions(self):
        headers=self.owner();p=self.client.post('/api/users',headers=headers,json={'username':'new-researcher','password':'Temporary researcher password 2026!','role':'researcher','researcher_id':'paulus-hamutenya'})
        self.assertEqual(p.status_code,200,p.text)
        self.client.post('/api/login',headers={'Origin':'http://testserver'},json={'username':'new-researcher','password':'Temporary researcher password 2026!'})
        u=self.client.get('/api/session').json()['user'];h={'Origin':'http://testserver','X-CSRF-Token':u['csrf']}
        for c in ['announcements','achievements']:
            self.assertEqual(self.client.post('/api/records/'+c,headers=h,json=self.seed[c][0]).status_code,403)
    def test_19_legacy_update_preserves_owner_edits_and_is_repeatable(self):
        with tempfile.TemporaryDirectory() as d:
            store=Store(Path(d)/'legacy.sqlite3');store.initialize()
            baseline=json.loads((ROOT/'data/updates/v2-baseline.json').read_text())
            with store.connect(write=True) as c:
                for collection,items in baseline.items():
                    for item in items:
                        item=validate(collection,item)
                        if collection=='people' and item['id']=='paulus-hamutenya':item['bio']='Owner-authored biography to preserve.'
                        c.execute('INSERT INTO records VALUES(?,?,?,?,1,?,?)',(collection,item['id'],json.dumps(item),item['visibility'],'seed',now()))
            plan=upgrade_content(store);self.assertTrue(plan['inserted']);self.assertIsNone(plan['backup']);self.assertIsNone(store.get('announcements','shatri-sanord-2026'))
            report=upgrade_content(store,apply=True);self.assertTrue(Path(report['backup']).is_file())
            self.assertEqual(store.get('people','paulus-hamutenya')['bio'],'Owner-authored biography to preserve.')
            self.assertEqual(store.get('people','denis-bouman')['name'],'Ms Denise Bouman')
            self.assertIsNotNone(store.get('achievements','paulus-falling-walls-2026'))
            second=upgrade_content(store);self.assertEqual(second['inserted'],[]);self.assertEqual(second['updated'],[])
    def test_20_seed_preserves_all_twelve_homepage_capabilities(self):
        baseline=json.loads((ROOT/'data/updates/v2-baseline.json').read_text())
        self.assertEqual(self.seed['capabilities'],baseline['capabilities'])
        self.assertEqual(self.seed['publications'],baseline['publications'])

if __name__=='__main__':unittest.main()
