#!/usr/bin/env python3
"""Release installer/commit smoke checks in disposable clones; no network is used."""
from __future__ import annotations
import argparse,json,os,shutil,sqlite3,subprocess,sys,sysconfig,tempfile,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.db import Store,now
from manage import create_owner
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=Path('test-results/installer-v5.json'));p.add_argument('--baseline-zip',type=Path,help='Optional original V4 ZIP to test the complete source transition.');args=p.parse_args()
    if os.geteuid()==0:raise SystemExit('Run this installer test as a normal non-root account.')
    checks=[]
    def check(name,ok=True):
        if not ok:raise AssertionError(name)
        checks.append(name)
    with tempfile.TemporaryDirectory(prefix='ted2-upgrade-v5-') as temporary:
        base=Path(temporary);home=base/'home';home.mkdir();repo=home/'Documents/MPhill (medical microbiology)/GitHub tracker/MPHILL-research-2026';repo.mkdir(parents=True)
        env={k:v for k,v in os.environ.items() if not k.startswith(('TED2_','GIT_'))};env['HOME']=str(home)
        def git(*a,check_return=True):return subprocess.run(['git','-C',str(repo),*a],check=check_return,capture_output=True,text=True,env=env)
        git('init','-b','main');git('config','user.name','Installer test');git('config','user.email','installer@example.invalid')
        if args.baseline_zip:
            with zipfile.ZipFile(args.baseline_zip) as archive:
                for item in archive.infolist():
                    path=Path(item.filename)
                    if item.is_dir():continue
                    if path.is_absolute() or '..' in path.parts or len(path.parts)<2:raise ValueError('Unsafe baseline archive')
                    target=repo/Path(*path.parts[1:]);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(archive.read(item))
        else:
            for rel in ('manage.py','backend/__init__.py','web/public.html'):
                target=repo/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/rel,target)

        subprocess.run([sys.executable,'-m','venv','--without-pip',str(repo/'.venv')],check=True)
        site=repo/'.venv/lib'/('python'+str(sys.version_info.major)+'.'+str(sys.version_info.minor))/'site-packages';(site/'test-environment.pth').write_text(sysconfig.get_path('purelib')+'\n')
        (repo/'.gitignore').write_text('var/\n.venv/\n.env\n');(repo/'.env').write_text('TED2_BASE_URL=http://127.0.0.1:48763\n');(repo/'index.html').write_text('Old standalone homepage')
        db=Store(repo/'var/ted2.sqlite3');db.initialize();create_owner(db,'existing-owner','Existing private testing password!')
        baseline=json.loads((ROOT/'data/updates/v4-baseline.json').read_text())
        with db.connect(write=True) as c:
            for collection,rows in baseline.items():
                for record in rows:
                    if record['id']=='paulus-hamutenya':record['bio']='Existing owner edited biography'
                    c.execute('INSERT INTO records VALUES(?,?,?,?,1,?,?)',(collection,record['id'],json.dumps(record),record['visibility'],'original',now()))
        (repo/'var/uploads').mkdir();(repo/'var/uploads/keep-private.txt').write_text('Retain this existing private upload')
        git('add','manage.py','backend','web','.gitignore','index.html');git('commit','-m','Existing application');head=git('rev-parse','HEAD').stdout.strip()
        (repo/'already-staged.txt').write_text('Existing staged work');git('add','already-staged.txt');staged=git('diff','--cached').stdout
        def install():return subprocess.run([sys.executable,str(ROOT/'scripts/install_v5.py'),'--target',str(repo),'--yes','--no-deps'],env=env,capture_output=True,text=True)
        result=install();check('Existing-clone upgrade exits successfully',result.returncode==0 or (print(result.stdout,result.stderr) or False))
        check('Git HEAD preserved',git('rev-parse','HEAD').stdout.strip()==head);check('Previously staged work preserved',git('diff','--cached').stdout==staged)
        check('Existing environment preserved',(repo/'.venv/bin/python').is_symlink());check('Existing config preserved',(repo/'.env').read_text()=='TED2_BASE_URL=http://127.0.0.1:48763\n')
        with db.connect() as c:check('Existing owner account preserved',c.execute("SELECT count(*) FROM users WHERE username='existing-owner'").fetchone()[0]==1)
        check('Owner-edited biography preserved',db.get('people','paulus-hamutenya')['bio']=='Existing owner edited biography')
        check('Feris correction migrated',db.get('people','jaydine-feris')['name']=='Ms Jaydine Feris');check('New supplied portrait migrated',db.get('people','naungwe-simasiku')['bundled_portrait']=='naungwe-simasiku-v4')
        check('Existing upload preserved',(repo/'var/uploads/keep-private.txt').read_text()=='Retain this existing private upload')
        check('Compiled main website uses existing public edits','Existing owner edited biography' in (repo/'index.html').read_text());check('Private database content is not serialized','existing-owner' not in (repo/'index.html').read_text())
        backups=list((home/'TED2-private-backups').glob('v5-*'));check('Private backup created outside clone',len(backups)==1 and (backups[0]/'ted2.sqlite3').is_file());check('Backup folder private',backups[0].stat().st_mode & 0o777==0o700)
        def commit():return subprocess.run([sys.executable,str(repo/'scripts/commit_release.py'),'--yes'],cwd=repo,env=env,capture_output=True,text=True)
        r=commit();check('Commit helper refuses unrelated staged work',r.returncode!=0 and 'staged work' in r.stderr);check('Staged work still untouched after refusal',git('diff','--cached').stdout==staged)
        git('reset','--','already-staged.txt');r=commit();check('Release-only commit succeeds',r.returncode==0 or (print(r.stdout,r.stderr) or False))
        names=git('show','--pretty=format:','--name-only','HEAD').stdout.splitlines();manifest=json.loads((repo/'RELEASE-MANIFEST.json').read_text())['files'];check('Commit contains only manifest-approved release paths',all(n in manifest or n=='RELEASE-MANIFEST.json' for n in names))
        tracked=git('ls-files').stdout;check('Private runtime/config/staged-only file not committed',all(n not in tracked for n in ['var/','.env\n','.venv/','already-staged.txt']))
        check('All V5 backend and publisher code committed','backend/publisher.py' in tracked and 'web/assets/admin.js' in tracked);check('No remote needed or changed',git('remote').stdout=='');check('New theme configuration installed',db.get('theme','website')['primary']=='#244d3e');check('V5 record controls installed','backend/v5_routes.py' in tracked and 'backend/schema_v5.py' in tracked)
        result=install();check('Repeat upgrade is safe and succeeds',result.returncode==0 or (print(result.stdout,result.stderr) or False));check('Repeat upgrade preserves owner biography',db.get('people','paulus-hamutenya')['bio']=='Existing owner edited biography')
        original=(repo/'backend/publisher.py').read_text();(repo/'backend/publisher.py').write_text(original+'\n# local customization\n');result=install();check('Customized source causes safe stop',result.returncode!=0 and 'customization' in result.stderr);check('Customized source is not overwritten',(repo/'backend/publisher.py').read_text().endswith('# local customization\n'))
    report={'checks_passed':len(checks),'checks':checks,'mode':'Disposable existing Git clones and V4 SQLite content; actual installer and source commit subprocesses; no pip/network/remote GitHub actions.', 'full_v4_source_fixture':bool(args.baseline_zip)};args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
