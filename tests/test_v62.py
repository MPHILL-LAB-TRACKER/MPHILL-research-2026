"""V6.2 HTTP/security contracts, inheriting the preserved laboratory workflows.
External sources use explicit metadata fixtures, never asserted as live research.
"""
import json, pathlib, re, subprocess, unittest
import test_v61 as previous
import test_http as base
class V62Tests(previous.V61Tests):
    def test_18_theme_both_interfaces(self):
        old=self.get('theme','website');t=dict(old);t.update(primary='#314159',appearance='dark',header_alignment='center');self.save('theme',t)
        for path in ['/', '/admin']:
            h=self.client.request(path)[1];self.assertIn(b'#314159',h);self.assertIn(b'TED2_APPEARANCE',h)
        self.assertIn(b'align-center',self.client.request('/')[1]);old['_version']=self.get('theme','website')['_version'];self.save('theme',old)
    def test_33_new_release_design_defaults(self):
        self.assertEqual(self.client.request('/api/bootstrap')[1]['version'],'6.2.0');self.assertGreaterEqual(len(self.client.request('/api/bootstrap')[1]['design']['presets']),14)
        self.assertGreaterEqual(len(self.client.request('/api/bootstrap')[1]['design']['photography']),7)
        self.assertIn(b'photo-band-header',self.client.request('/')[1]);self.assertIn(b'photo-band-footer',self.client.request('/')[1])
    def test_35_all_presets_and_motifs(self):
        old=self.get('theme','website')
        for name, preset in self.client.request('/api/bootstrap')[1]['design']['presets'].items():
            t=self.get('theme','website');t.update(preset,preset=name);self.save('theme',t)
            self.assertIn(f'data-theme="{name}"'.encode(),self.client.request('/')[1])
        for picture in self.client.request('/api/bootstrap')[1]['design']['photography']:
            if not picture['installed']:continue
            t=self.get('theme','website');t.update(header_art=picture['id']);self.save('theme',t)
            self.assertIn(b'photo-band-header',self.client.request('/')[1]);self.assertEqual(self.client.request(picture['preview_url'])[0],200)
        old['_version']=self.get('theme','website')['_version'];self.save('theme',old)
    def test_50_approved_export_links_all_exist(self):
        dest=self.tmp/'export-v62';p=subprocess.run(['php','bin/console.php','build',str(dest)],cwd=base.ROOT,env=self.env,text=True,capture_output=True);self.assertEqual(p.returncode,0,p.stderr)
        for html in dest.rglob('*.html'):
            for link in re.findall(r'(?:src|href)="(/MPHILL-research-2026/[^"#?]*)(?:[?#][^"]*)?"',html.read_text()):
                target=dest/link[len('/MPHILL-research-2026/'):];self.assertTrue(target.exists() or (target/'index.html').exists(),(html,link))
        self.assertEqual(json.loads((dest/'release.json').read_text())['version'],'6.2.0')
        self.assertTrue((dest/'sw.js').is_file());self.assertTrue((dest/'science-config.json').is_file())
    def test_53_quote_requires_source_and_approval(self):
        q=self.get('science_quotes','darwin-grandeur') if any(p['id']=='darwin-grandeur' for p in self.client.request('/api/records/science_quotes')[1]) else self.client.request('/api/records/science_quotes')[1][0]
        q['visibility']='public';q['approved']=False
        self.assertEqual(self.client.request('/api/records/science_quotes/'+q['id'],'PUT',q)[0],422)
        q['approved']=True;q['source_url']='';q['attribution_type']='primary-source'
        self.assertEqual(self.client.request('/api/records/science_quotes/'+q['id'],'PUT',q)[0],422)
    def test_54_public_quote_and_rotation(self):
        q=self.create('science_quotes',self.new('science_quotes',quote='A test reflection, not a historical quotation.',author='Test editorial reflection',source_label='Test fixture',attribution_type='original',license='CC0',homepage=True,approved=True,tags=['ScientificCuriosity'],visibility='public'))
        h=self.client.request('/')[1];self.assertIn(q['quote'].encode(),h);self.assertIn(b'data-quotes',h);self.assertIn(b'#ScientificCuriosity',h)
        q['visibility']='private';self.save('science_quotes',q);self.assertNotIn(q['quote'].encode(),self.client.request('/')[1])
    def test_55_public_render_cache_hit_and_invalidation(self):
        self.client.request('/api/cache/clear','POST',{});status,h,headers=self.client.request('/');self.assertEqual(headers.get('X-TED2-Render-Cache'),'MISS')
        _,same,headers=self.client.request('/');self.assertEqual(headers.get('X-TED2-Render-Cache'),'HIT');self.assertEqual(h,same)
        s=self.get('settings','laboratory');old=s['hero_title'];s['hero_title']='Cache invalidation checked';self.save('settings',s)
        _,new,headers=self.client.request('/');self.assertEqual(headers.get('X-TED2-Render-Cache'),'MISS');self.assertIn(b'Cache invalidation checked',new)
        s=self.get('settings','laboratory');s['hero_title']=old;self.save('settings',s)
    def test_56_private_routes_never_cache(self):
        for path in ['/admin','/api/bootstrap','/questions/']:
            _,_,h=self.client.request(path);self.assertIn('no-store',h.get('Cache-Control',''));self.assertIsNone(h.get('X-TED2-Render-Cache')) if path!='/questions/' else None
    def test_57_public_etag_and_immutable_asset(self):
        _,body,h=self.client.request('/');tag=h['ETag'];self.assertEqual(self.client.request('/',headers={'If-None-Match':tag})[0],304)
        image=re.search(rb'<img[^>]*src="([^"]+public-media/[^"]+)"',body).group(1).decode()
        _,_,h=self.client.request(image);self.assertIn('immutable',h['Cache-Control']);self.assertEqual(self.client.request(image,headers={'If-None-Match':h['ETag']})[0],304)
        _,_,h=self.client.request('/assets/site.css');self.assertIn('no-cache',h['Cache-Control'])
    def test_58_uploaded_decoration_approval(self):
        t=self.get('theme','website');status,row,_=self.client.upload('theme','website','header.png',base.png(),'image/png');self.assertEqual(status,201,row)
        t.update(header_art='custom',header_art_upload=row['id'],photo_art_approved=True);self.save('theme',t);self.assertIn(b'photo-band-header',self.client.request('/')[1])
        t=self.get('theme','website');t['photo_art_approved']=False;self.save('theme',t);self.assertNotIn(b'photo-band-header',self.client.request('/')[1]);t=self.get('theme','website');t.update(header_art='lab-bench',photo_art_approved=True);self.save('theme',t)
    def test_59_feed_dedup_private_review_then_auto(self):
        result=self.php("$p=$s->get('settings','laboratory');$v=$p['_version'];unset($p['_version'],$p['_updated_at']);$p['pulse_enabled']=true;$p['pulse_policy']='review';$p['pulse_sources']=['europepmc'];$s->replace('settings',$p,$v,'test');$fetch=fn($u)=>['resultList'=>['result'=>[['source'=>'MED','id'=>'pulse-fixture','title'=>'Nanomedicine fixture, not a real article','doi'=>'10.test/v62','firstPublicationDate'=>gmdate('Y-m-d')],['source'=>'MED','id'=>'duplicate-id','title'=>'Duplicate fixture','doi'=>'10.test/v62','firstPublicationDate'=>gmdate('Y-m-d')]]]];$pulse=new Ted2\\Pulse($s,$fetch);$first=$pulse->sync(true);$second=$pulse->sync(true);echo Ted2\\json([$first['inserted'],$second['inserted'],$s->list('science_news')]);")
        self.assertEqual(result[:2],[1,0]);self.assertEqual(result[2][0]['visibility'],'private');self.assertNotIn(b'Nanomedicine fixture',self.client.request('/')[1])
    def test_60_automatic_policy_revocation(self):
        s=self.get('settings','laboratory');s.update(pulse_enabled=True,pulse_policy='source-headlines',pulse_sources=['europepmc']);self.save('settings',s)
        p=self.create('science_news',self.new('science_news',title='Nanomedicine policy-test headline',source_url='https://europepmc.org/article/MED/fixture',source_label='Fixture',source_kind='research',source_key='europepmc:fixture-auto',published_date=__import__('datetime').date.today().isoformat(),automatic=True,approved=False,homepage=True,visibility='public',tags=['Nanomedicine']))
        self.assertIn(p['title'].encode(),self.client.request('/')[1]);s=self.get('settings','laboratory');s['pulse_enabled']=False;self.save('settings',s);self.assertNotIn(p['title'].encode(),self.client.request('/')[1])
    def test_61_reading_feed_no_private_leak(self):
        status,d,h=self.client.request('/science-feed.json');self.assertEqual(status,200);self.assertNotIn('internal_notes',json.dumps(d));self.assertNotIn('private_email',json.dumps(d))
    def test_62_admin_only_visual_cache_and_pulse(self):
        self.client.request('/api/users','POST',{'username':'pulse-researcher','role':'researcher','researcher_id':'paulus-hamutenya','password':base.PASSWORD,'active':True,'edit_profile':True,'edit_research':True})
        other=base.Client(self.base);other.login('pulse-researcher')
        for path in ['/api/cache','/api/pulse/status','/api/visuals']:
            self.assertEqual(other.request(path)[0],403)
        for path in ['/api/cache/clear','/api/pulse/sync']:
            self.assertEqual(other.request(path,'POST',{})[0],403)
        self.assertEqual(self.client.request('/api/visuals/not-a-source','POST',{})[0],422)
    def test_63_cache_worker_scope(self):
        out=self.php("$site=new Ted2\\PublicSite($s,true);echo Ted2\\json(Ted2\\Cache62::worker($site));")
        self.assertIn('request.method',out);self.assertIn('request.headers.has(\'range\')',out);self.assertNotIn('cache.put(event.request',out.split('if (!allowed')[0]);self.assertNotIn("request.mode === 'navigate'",out)
    def test_64_schema_ranges(self):
        t=self.get('theme','website');t['quote_seconds']=1;self.assertEqual(self.client.request('/api/records/theme/website','PUT',t)[0],422)
        t=self.get('theme','website');t['render_cache_seconds']=999999;self.assertEqual(self.client.request('/api/records/theme/website','PUT',t)[0],422)
    def test_65_feed_failure_is_not_fresh_success(self):
        result=self.php("$p=$s->get('settings','laboratory');$v=$p['_version'];unset($p['_version'],$p['_updated_at']);$p['pulse_enabled']=true;$s->replace('settings',$p,$v,'test');$pulse=new Ted2\\Pulse($s,function($u){throw new Ted2\\Problem(503,'Fixture outage');});echo Ted2\\json($pulse->sync(true));")
        self.assertEqual(result['inserted'],0);self.assertTrue(result['errors']);self.assertNotEqual(result['state'],'ok')
    def test_66_plos_source_is_metadata_only(self):
        out=self.php("$c=Ted2\\Pulse::configuration(['pulse_enabled'=>true,'pulse_topics'=>['open science'],'pulse_sources'=>['plos-blog']]);$p=new Ted2\\Pulse(null,fn($u)=>[['id'=>7,'date'=>gmdate('Y-m-d').'T00:00:00','link'=>'https://theplosblog.plos.org/test','title'=>['rendered'=>'Open science &amp; practice'],'excerpt'=>['rendered'=>'<p>Full article must not be copied</p>']]]);echo Ted2\\json($p->collect($c));")
        self.assertEqual(out['items'][0]['title'],'Open science & practice');self.assertEqual(out['items'][0]['summary'],'');self.assertEqual(out['items'][0]['source_kind'],'blog')
if __name__=='__main__':unittest.main(verbosity=2)
