#!/usr/bin/env python3
"""V6.1 HTTP, permissions, migration, metadata and export tests (includes V6 regressions)."""
import json, os, re, subprocess, unittest, pathlib, hashlib
import test_http as base

class V61Tests(base.HTTPTests):
    def new(self,c,**values):
        p=super().new(c)
        for f in self.schemas[c]['fields']:
            if 'default' in f:p[f['key']]=f['default']
            elif f['type']=='quantity':p[f['key']]=None
        p.update(values);return p
    def php(self,code):
        p=subprocess.run(['php','-r',"require 'php/bootstrap.php';$s=new Ted2\\Store();"+code],cwd=base.ROOT,env=self.env,text=True,capture_output=True)
        self.assertEqual(p.returncode,0,p.stderr);return json.loads(p.stdout)
    def method(self,who='paulus-hamutenya',visibility='private'):
        return self.create('methods',self.new('methods',title='Recorded method reference',researcher_id=who,reference='Owner protocol version 1, section 3',status='planned',visibility=visibility))
    def requirement(self,**values):
        opts=dict(title='General laboratory notebook',researcher_id='paulus-hamutenya',category='consumable',method_step='Documentation stage in the owner-approved method',required_quantity=5,available_quantity=2,ordered_quantity=1,unit='items',condition='ready')
        opts.update(values);return self.create('procurement',self.new('procurement',**opts))
    def test_33_new_release_design_defaults(self):
        d=self.client.request('/api/bootstrap')[1];self.assertEqual(d['version'],'6.1.0');self.assertEqual(len(d['design']['presets']),14);self.assertEqual(len(d['design']['motifs']),19)
        theme=d['records']['theme'][0];self.assertEqual(theme['notice_seconds'],5)
        status,html,_=self.client.request('/');self.assertIn(b'data-seconds="5"',html);self.assertIn(b'ornament-header',html);self.assertIn(b'ornament-footer',html)
    def test_34_notice_validation(self):
        t=self.get('theme','website');bad=dict(t);bad['notice_seconds']=0;self.assertEqual(self.client.request('/api/records/theme/website','PUT',bad)[0],422)
        bad['notice_effect']='javascript:alert(1)';bad['notice_seconds']=5;self.assertEqual(self.client.request('/api/records/theme/website','PUT',bad)[0],422)
        t['notice_seconds']=9;t['notice_effect']='settle';t['notice_layout']='stack';self.save('theme',t)
        h=self.client.request('/')[1];self.assertIn(b'data-seconds="9"',h);self.assertIn(b'data-effect="settle"',h)
        t=self.get('theme','website');t.update(notice_seconds=5,notice_effect='fade',notice_layout='split');self.save('theme',t)
    def test_35_all_presets_and_motifs(self):
        design=self.client.request('/api/bootstrap')[1]['design'];t=self.get('theme','website')
        for name,colors in design['presets'].items():
            with self.subTest(theme=name):
                t.update(colors);t=self.save('theme',t);self.assertIn(('data-theme="'+name+'"').encode(),self.client.request('/')[1])
        for name in ['none']+list(design['motifs']):
            with self.subTest(motif=name):
                t.update(header_motif=name,footer_motif=name);t=self.save('theme',t);h=self.client.request('/')[1];self.assertEqual(b'ornament-header'in h,name!='none')
        t.update(design['presets']['vintage'],header_motif='test-tubes',footer_motif='leaves');self.save('theme',t)
    def test_36_private_portrait_preview(self):
        p=self.get('people','naungwe-simasiku');status,img,_=self.client.request('/api/portrait/'+p['id']);self.assertEqual(status,200);self.assertGreater(len(img),100)
        self.assertEqual(base.Client(self.base).request('/api/portrait/'+p['id'])[0],401)
        status,uploaded,_=self.client.upload('people',p['id'],'replacement.jpeg',base.png());self.assertEqual(status,201)
        p.update(photo_upload_id=uploaded['id'],photo_permission='approved');p=self.save('people',p)
        self.assertEqual(self.client.request('/api/portrait/'+p['id'])[1],self.client.request('/media/'+uploaded['id'])[1])
        p.update(photo_upload_id='',bundled_portrait='',photo_url='',photo_permission='unconfirmed');self.save('people',p)
        self.assertEqual(self.client.request('/api/portrait/'+p['id'])[0],404)
    def test_37_procurement_without_project_or_method(self):
        p=self.requirement();self.assertEqual(p['project_id'],'');self.assertEqual(p['method_id'],'')
        report=self.client.request('/api/tracking')[1];item=next(x for x in report['items'] if x['record']['id']==p['id'])
        self.assertEqual(item['calculation']['shortfall'],3);self.assertEqual(item['calculation']['to_source'],2);self.assertIn('Method linkage needs review',item['calculation']['warnings'])
    def test_38_methodology_scope_and_public_gate(self):
        method=self.method();p=self.new('procurement',title='Scope test',researcher_id='naungwe-simasiku',method_step='Section 3',method_id=method['id'],category='equipment',required_quantity=1,available_quantity=0,ordered_quantity=0,unit='instruments',condition='check-needed',status='needed')
        self.assertEqual(self.client.request('/api/records/procurement','POST',p)[0],422)
        p['researcher_id']='paulus-hamutenya';p['visibility']='public';self.assertEqual(self.client.request('/api/records/procurement','POST',p)[0],422)
        method['visibility']='public';self.save('methods',method);p=self.create('procurement',p)
        self.assertIn(p['id'].encode(),self.client.request('/procurement/')[1]);method=self.get('methods',method['id']);method['visibility']='private';self.save('methods',method)
        self.assertNotIn(p['id'].encode(),self.client.request('/procurement/')[1]);self.assertEqual(self.client.request('/records/procurement/'+p['id']+'/')[0],404)
    def test_39_procurement_required_reason_and_quantity(self):
        p=self.new('procurement',title='No reason',researcher_id='paulus-hamutenya',category='consumable',method_step='',required_quantity=1,available_quantity=0,ordered_quantity=0,unit='items',condition='ready',status='needed')
        self.assertEqual(self.client.request('/api/records/procurement','POST',p)[0],422);p['method_step']='Method specification';p['required_quantity']=-1;self.assertEqual(self.client.request('/api/records/procurement','POST',p)[0],422)
        p['required_quantity']=1.5;p['available_quantity']=.5;p=self.create('procurement',p);self.assertEqual(p['required_quantity'],1.5)
    def test_40_expired_stock_is_not_ready(self):
        p=self.requirement(available_quantity=10,expiry_date='2020-01-01',due_date='2020-01-02')
        item=next(x for x in self.client.request('/api/tracking')[1]['items'] if x['record']['id']==p['id'])
        self.assertEqual(item['calculation']['usable'],0);self.assertTrue(item['calculation']['expired']);self.assertFalse(item['calculation']['ready'])
    def test_41_procurement_private_details_excluded(self):
        p=self.requirement(visibility='public',supplier='PRIVATE_SUPPLIER_61',next_action='PRIVATE_ACTION_61',estimated_cost=9133,currency='PRIVATE_CURRENCY_61')
        text=self.client.request('/records/procurement/'+p['id']+'/')[1].decode();self.assertNotIn('PRIVATE_',text);self.assertIn(p['method_step'],text)
        h=self.client.request('/researchers/paulus-hamutenya/')[1];self.assertIn(p['id'].encode(),h)
    def test_42_researcher_procurement_boundaries(self):
        u={'username':'procurement-test','role':'researcher','researcher_id':'paulus-hamutenya','password':base.PASSWORD,'active':True,'edit_profile':True,'edit_research':True};self.assertEqual(self.client.request('/api/users','POST',u)[0],200)
        own=base.Client(self.base);own.login('procurement-test')
        p=self.new('methods',title='Private work package',researcher_id='paulus-hamutenya',reference='Documentation plan version 1',status='planned');p=self.create('methods',p,own)
        p['researcher_id']='naungwe-simasiku';self.assertEqual(own.request('/api/records/methods/'+p['id'],'PUT',p)[0],403)
        other=self.method('naungwe-simasiku');self.assertEqual(own.request('/api/records/methods/'+other['id'])[0],404)
        self.assertEqual(own.request('/api/literature/status')[0],403)
        p=self.requirement(researcher_id='naungwe-simasiku');ids=[x['record']['id'] for x in own.request('/api/tracking?researcher_id=naungwe-simasiku')[1]['items']];self.assertNotIn(p['id'],ids)
    def test_43_builder_multi_question_atomic(self):
        survey=self.create('questionnaires',self.new('questionnaires',title='Readiness feedback',open=True,visibility='public'))
        q1=self.new('survey_questions',label='Was the workspace easy to use?',questionnaire_id=survey['id'],kind='rating',visibility='public',required_answer=True)
        q2=self.new('survey_questions',label='What could improve?',questionnaire_id=survey['id'],kind='long-text',visibility='public')
        status,data,_=self.client.request('/api/questionnaire-builder/'+survey['id'],'POST',{'survey_version':survey['_version'],'questions':[q1,q2],'versions':{}});self.assertEqual(status,200,data)
        questions=data['questions'];versions={q['id']:q['_version'] for q in questions};questions.reverse()
        status,data,_=self.client.request('/api/questionnaire-builder/'+survey['id'],'POST',{'survey_version':survey['_version'],'questions':questions,'versions':versions});self.assertEqual(status,200,data);self.assertEqual(data['questions'][0]['order'],0)
        versions={q['id']:q['_version'] for q in data['questions']};retained=data['questions'][:1]
        self.assertEqual(self.client.request('/api/questionnaire-builder/'+survey['id'],'POST',{'survey_version':survey['_version'],'questions':retained,'versions':versions})[0],200)
        trash=self.client.request('/api/trash')[1];self.assertTrue(any(r['id']==q1['id'] for r in trash))
    def test_44_builder_stale_refused(self):
        survey=self.create('questionnaires',self.new('questionnaires',title='Version test'))
        q=self.create('survey_questions',self.new('survey_questions',label='Question',questionnaire_id=survey['id'],kind='text'))
        status,_,_=self.client.request('/api/questionnaire-builder/'+survey['id'],'POST',{'survey_version':survey['_version'],'questions':[],'versions':{q['id']:0}});self.assertEqual(status,409)
        self.assertEqual(self.client.request('/api/records/survey_questions/'+q['id'])[0],200)
    def test_45_guided_form_markup(self):
        h=self.client.request('/questions/')[1];self.assertIn(b'data-wizard="yes"',h);self.assertIn(b'data-question-step',h);self.assertIn(b'data-step-next',h);self.assertIn(b'No name or email',h)
    def test_46_fact_approval_and_no_private_leak(self):
        facts=self.client.request('/api/records/lab_facts')[1];self.assertGreaterEqual(len(facts),3);self.assertTrue(all(f['visibility']=='private' for f in facts))
        p=facts[0];p['visibility']='public';self.assertEqual(self.client.request('/api/records/lab_facts/'+p['id'],'PUT',p)[0],422)
        p['approved']=True;p=self.save('lab_facts',p);t=self.get('theme','website');t['home_blocks']=list(dict.fromkeys(t['home_blocks']+['facts']));self.save('theme',t)
        h=self.client.request('/')[1];self.assertIn(p['title'].encode(),h);self.assertIn(b'data-fact-id',h)
        p['expires_on']='2020-01-01';self.save('lab_facts',p);self.assertNotIn(p['title'].encode(),self.client.request('/')[1])
    def test_47_literature_dedup_and_tombstone(self):
        out=self.php("$l=new Ted2\\Literature($s);$r=['source'=>'MED','id'=>'fixture-61001','title'=>'Fixture metadata, not a real article','doi'=>'10.test/dedup','pubYear'=>'2026','firstPublicationDate'=>'2026-09-10'];$a=$l->ingest([$r],'paulus-hamutenya');$r['id']='fixture-61002';$b=$l->ingest([$r],'paulus-hamutenya');$ids=$s->db->all(\"SELECT record_id FROM discovery_seen WHERE owner=? AND identity=?\",['paulus-hamutenya','doi:10.test/dedup']);$s->db->query('DELETE FROM records WHERE collection=? AND id=?',['discoveries',$ids[0]['record_id']]);$c=$l->ingest([$r],'paulus-hamutenya');echo Ted2\\json([$a,$b,$c]);")
        self.assertEqual(out,[1,0,0])
    def test_48_scheduled_fetch_does_not_publish(self):
        out=self.php("$p=$s->get('settings','laboratory');$p['discovery_enabled']=true;$p['discovery_query']='tissue engineering';$v=$p['_version'];unset($p['_version'],$p['_updated_at']);$s->replace('settings',$p,$v,'test');$n=0;$l=new Ted2\\Literature($s,function($url)use(&$n){$n++;return ['resultList'=>['result'=>[['source'=>'MED','id'=>'fixture-61010','title'=>'Source fixture for review','doi'=>'10.test/queue','pubYear'=>'2026']]]];});$first=$l->sync();$again=$l->sync();echo Ted2\\json([$n,$first['inserted'],$again['skipped'],$s->db->one(\"SELECT visibility,payload FROM records WHERE collection='discoveries' AND id LIKE 'lit-%' AND payload LIKE '%fixture-61010%'\")]);")
        self.assertEqual(out[:3],[1,1,1]);self.assertEqual(out[3]['visibility'],'private');self.assertFalse(json.loads(out[3]['payload'])['approved'])
        s=self.get('settings','laboratory');s['discovery_enabled']=False;self.save('settings',s)
    def test_49_tiny_mobile_diagnostic(self):
        code,h,_=self.client.request('/connection-check/');self.assertEqual(code,200);self.assertLess(len(h),3000);self.assertNotIn(b'<script',h);self.assertNotIn(b'<img',h)
        code,h,_=self.client.request('/light/');self.assertEqual(code,200);self.assertIn(b'Paulus Hamutenya',h);self.assertLess(len(h),18000);self.assertNotIn(b'<script',h);self.assertNotIn(b'<img',h)
    def test_50_approved_export_links_all_exist(self):
        dest=self.tmp/'export-v61';p=subprocess.run(['php','bin/console.php','build',str(dest)],cwd=base.ROOT,env=self.env,text=True,capture_output=True);self.assertEqual(p.returncode,0,p.stderr)
        for html in dest.rglob('*.html'):
            for link in re.findall(r'(?:src|href)="(/MPHILL-research-2026/[^"#?]*)(?:[?#][^"]*)?"',html.read_text()):
                rel=link[len('/MPHILL-research-2026/'):];target=dest/rel
                self.assertTrue(target.exists() or (target/'index.html').exists(),(html,link))
        self.assertEqual(json.loads((dest/'release.json').read_text())['version'],'6.1.0')
    def test_51_export_rejects_insecure_and_private_media(self):
        out=self.php("$results=[];foreach(['http://example.org/p.jpg','https://127.0.0.1/p.jpg','https://192.168.1.1/p.jpg','https://localhost/p.jpg'] as $url){try{Ted2\\Public61::validateExport('<img src=\"'.$url.'\">','test');$results[]=false;}catch(Ted2\\Problem $e){$results[]=$e->status===422;}}Ted2\\Public61::validateExport('<img src=\"/MPHILL-research-2026/public-media/photo.jpg\"><a href=\"http://example.org/evidence\">Source</a>','test');echo Ted2\\json($results);")
        self.assertEqual(out,[True,True,True,True])
    def test_52_low_data_footer_control(self):
        s=self.get('settings','laboratory');s['enable_light_page']=False;self.save('settings',s)
        self.assertNotIn(b'>Low-data view</a>',self.client.request('/')[1]);self.assertEqual(self.client.request('/light/')[0],200)
        s=self.get('settings','laboratory');s['enable_light_page']=True;self.save('settings',s)
if __name__=='__main__':unittest.main(verbosity=2)
