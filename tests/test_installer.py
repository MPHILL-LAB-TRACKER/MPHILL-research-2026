"""Non-destructive V6-to-V6.1 upgrade and allowlisted commit integration test.

Uses a copied V6 release, fake private data and a temporary local Git repository.
No Git fetch/push or network access. Set TED2_V6_FIXTURE to an extracted V6 package.
When run as root in a test container, installation is exercised as nobody.
"""
from __future__ import annotations
import hashlib,json,os,pwd,shutil,sqlite3,subprocess,tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
V6=Path(os.environ.get('TED2_V6_FIXTURE',str(ROOT.parent/'TED2-Research-Workspace-v6')))
if not V6.joinpath('php/Application.php').is_file():
    raise SystemExit('Set TED2_V6_FIXTURE to the extracted original V6 package for this integration test.')
if not ROOT.joinpath('release-manifest.json').is_file():
    raise SystemExit('This test requires the packaged release-manifest.json.')
checks=[]
def check(ok:bool,label:str):
    if not ok:raise AssertionError(label)
    checks.append(label);print('PASS',label)
def sha(p:Path):return hashlib.sha256(p.read_bytes()).hexdigest()
root_user=os.geteuid()==0
uid=pwd.getpwnam('nobody').pw_uid if root_user else os.getuid()
gid=pwd.getpwnam('nobody').pw_gid if root_user else os.getgid()
with tempfile.TemporaryDirectory(prefix='ted2-installer-test-') as td:
    tmp=Path(td);tmp.chmod(0o755)
    if root_user:os.chown(tmp,uid,gid)
    home=tmp/'home';home.mkdir();repo=home/'Documents'/'GitHub tracker'/'MPHILL-research-2026';repo.parent.mkdir(parents=True)
    shutil.copytree(V6,repo,ignore=shutil.ignore_patterns('var','.git','.venv','__pycache__','test-results','.pytest_cache'))
    # Current V6 main still contains this legacy V5 release marker.
    (repo/'VERSION').write_text('5.0.0\n')
    var=repo/'var';var.mkdir();(var/'uploads').mkdir();(var/'native').mkdir()
    binary=ROOT/'var/native/ted2-worker'
    if binary.is_file():shutil.copy2(binary,var/'native/ted2-worker')
    # Seed with the ORIGINAL V6 PHP implementation, not the new release.
    init=r"""require $argv[1].'/php/bootstrap.php';
$s=new Ted2\Store($argv[2]);$s->init();$s->seed();$s->migrate();
$s->db->query('INSERT INTO users VALUES(?,?,?,?,?,?,?)',['preserved-user','preserved-owner',Ted2\Auth::hash('V6Preservation!3821'),'owner','',1,Ted2\utc()]);
$p=$s->get('people','paulus-hamutenya');$v=$p['_version'];unset($p['_version'],$p['_updated_at']);$p['bio']='Owner-edited biography before upgrade';$p['private_phone']='PRIVATE_SENTINEL_V6';$s->replace('people',$p,$v,'fixture');
$t=$s->get('theme','website');$v=$t['_version'];unset($t['_version'],$t['_updated_at']);$t['primary']='#1b405a';$t['home_blocks']=['alerts','research','people'];$s->replace('theme',$t,$v,'fixture');
"""
    subprocess.run(['php','-r',init,str(repo),str(var/'ted2.sqlite3')],check=True,capture_output=True,text=True,env={**os.environ,'TED2_DB':str(var/'ted2.sqlite3'),'TED2_NATIVE':str(var/'native/ted2-worker'),'TED2_SQLITE_DRIVER':'native' if binary.is_file() else 'pdo'})
    (var/'uploads'/'do-not-publish.txt').write_text('PRIVATE_UPLOAD_SENTINEL')
    (repo/'.env').write_text('TED2_DB=var/ted2.sqlite3\nTED2_BASE_URL=http://127.0.0.1:48639\n')
    (repo/'.venv').mkdir();(repo/'.venv'/'KEEP').write_text('existing Python environment')
    before_env=(repo/'.env').read_bytes();before_upload=(var/'uploads'/'do-not-publish.txt').read_bytes()
    with sqlite3.connect(var/'ted2.sqlite3') as db:before_hash=db.execute('SELECT password_hash FROM users').fetchone()[0]
    if root_user:
        for parent,dirs,files in os.walk(home):
            os.chown(parent,uid,gid)
            for fn in files:os.chown(Path(parent)/fn,uid,gid)
    env={**os.environ,'HOME':str(home),'TED2_SQLITE_DRIVER':'native' if binary.is_file() else 'pdo'}
    for k in ['TED2_DB','TED2_BASE_URL','TED2_NATIVE']:env.pop(k,None)
    def run(args,input=None,checkcode=True,cwd=repo):
        prefix=['runuser','-u','nobody','--','env','HOME='+str(home)] if root_user else []
        p=subprocess.run(prefix+args,cwd=cwd,env=env,input=input,text=True,capture_output=True,timeout=120)
        if checkcode and p.returncode:raise AssertionError(p.stdout+'\n'+p.stderr)
        return p
    run(['git','init','-b','main']);run(['git','config','user.name','Upgrade fixture']);run(['git','config','user.email','fixture@example.invalid']);run(['git','remote','add','origin','https://github.com/MPHILL-LAB-TRACKER/MPHILL-research-2026.git']);run(['git','add','.']);run(['git','commit','-m','Original V6 fixture'])
    old_head=run(['git','rev-parse','HEAD']).stdout.strip()
    (repo/'unrelated-work.txt').write_text('keep this separately staged')
    if root_user:os.chown(repo/'unrelated-work.txt',uid,gid)
    run(['git','add','unrelated-work.txt']);old_index=sha(repo/'.git/index')
    installer=['php',str(ROOT/'installer/upgrade.php'),'--target',str(repo)]
    dry=run(installer+['--dry-run']);check('Dry run passed' in dry.stdout,'V6 upgrade dry run succeeds')
    check(not (repo/'php/Upgrade61.php').exists(),'Dry run does not install V6.1 source')
    if root_user:
        p=subprocess.run(installer+['--yes'],env=env,text=True,capture_output=True)
        check(p.returncode!=0 and 'not root' in p.stderr,'Installer refuses root')
    # Fail closed for a non-clone and locally customised overlapping source.
    p=run(['php',str(ROOT/'installer/upgrade.php'),'--target',str(repo.parent),'--yes'],checkcode=False)
    check(p.returncode!=0,'Parent folder is not treated as the actual clone')
    old_readme=(repo/'README.md').read_bytes();(repo/'README.md').write_text('Important local custom source')
    p=run(installer+['--yes'],checkcode=False);check(p.returncode!=0 and 'Locally customised' in p.stderr,'Custom source is not overwritten');check((repo/'README.md').read_text()=='Important local custom source','Custom source bytes preserved');(repo/'README.md').write_bytes(old_readme)
    result=run(installer+['--yes']);check('V6.1 installed' in result.stdout,'Complete V6-to-V6.1 in-place installation')
    check((repo/'VERSION').read_text()=='6.1.0\n','Legacy V5 version marker is safely updated')
    check((repo/'php/Application.php').is_file() and (repo/'public/index.php').is_file(),'PHP backend and front controller installed')
    check((repo/'php/PublicSite.php').is_file(),'Existing PHP rendering remains available')
    check((repo/'.env').read_bytes()==before_env,'Private environment preserved byte-for-byte')
    check((var/'uploads'/'do-not-publish.txt').read_bytes()==before_upload,'Existing upload preserved byte-for-byte')
    check((repo/'.venv'/'KEEP').is_file(),'Existing Python environment not removed')
    check(run(['git','rev-parse','HEAD']).stdout.strip()==old_head,'Git history unchanged by upgrade')
    check(run(['git','branch','--show-current']).stdout.strip()=='main','Source branch remains main')
    check(sha(repo/'.git/index')==old_index,'Staged index preserved by installer')
    with sqlite3.connect(var/'ted2.sqlite3') as db:
        check(db.execute('SELECT password_hash FROM users WHERE id=?',('preserved-user',)).fetchone()[0]==before_hash,'V6 Argon2 password hash retained')
        p=json.loads(db.execute("SELECT payload FROM records WHERE collection='people' AND id='paulus-hamutenya'").fetchone()[0])
        check(p['bio']=='Owner-edited biography before upgrade','Existing edited biography retained')
        check(p['private_phone']=='PRIVATE_SENTINEL_V6','Existing private profile information retained')
        check(db.execute("SELECT value FROM v6_meta WHERE key='migration-6.1'").fetchone() is not None,'V6.1 additive migration completed')
        theme=json.loads(db.execute("SELECT payload FROM records WHERE collection='theme' AND id='website'").fetchone()[0])
        check(theme['primary']=='#1b405a','Owner theme colour is not replaced by a preset')
        check(theme['home_blocks']==['alerts','research','people'],'Owner homepage section selection preserved')
        check(theme['notice_seconds']==5,'Absent notice interval defaults to five seconds')
        check(db.execute("SELECT COUNT(*) FROM records WHERE collection='lab_facts' AND visibility='public'").fetchone()[0]==0,'Starter facts are private, not silently published')
    backups=list((home/'TED2-private-backups').glob('v6.1-*'))
    check(len(backups)==1,'One external private backup created')
    check(all((backups[0]/name).is_file() for name in ['source-and-config.tar.gz','ted2.sqlite3','uploads.tar.gz','migration-report.txt']),'Source, database, uploads and migration report backed up')
    check(backups[0].stat().st_mode & 0o077 ==0,'Backup directory is owner-only')
    p=run(['bash','scripts/commit-v6.1.sh'],input='COMMIT\n',checkcode=False)
    check(p.returncode!=0 and 'already staged' in p.stderr,'Commit helper refuses unrelated staged work')
    run(['git','restore','--staged','unrelated-work.txt'])
    # Reproduce the user stopping after staging: the helper must safely resume.
    run(['git','add','php/Upgrade61.php','README.md'])
    p=run(['bash','scripts/commit-v6.1.sh'],input='COMMIT\n');check('Source committed locally' in p.stdout,'Release-only source commit resumes already-staged release files')
    changed=run(['git','diff-tree','--no-commit-id','--name-only','-r','HEAD']).stdout.splitlines()
    check(not any(n.startswith(('var/','.venv/')) or n in ['.env','unrelated-work.txt'] for n in changed),'Commit excludes private runtime and unrelated file')
    check('php/Upgrade61.php' in changed and 'release-manifest.json' in changed,'Commit includes new backend and integrity manifest')
    check(run(['git','rev-parse','HEAD^']).stdout.strip()==old_head,'Release commit preserves original parent history')
    again=run(['php','bin/console.php','migrate']);check('already_upgraded' in again.stdout,'Repeated data migration is idempotent')
    repeat=run(installer+['--dry-run']);check('Dry run passed' in repeat.stdout,'Already installed release passes repeated dry run')
    check((repo/'unrelated-work.txt').is_file(),'Unrelated local work remains present')
    check('.env' not in run(['git','ls-files']).stdout.splitlines(),'Private environment remains untracked')
print(f'\n{len(checks)} installer/commit checks passed. No network push performed.')
