#!/usr/bin/env python3
"""Upgrade the verified existing clone without touching Git history, accounts or uploads."""
from __future__ import annotations
import argparse,hashlib,json,os,re,shutil,sqlite3,subprocess,sys,uuid
from datetime import datetime,timezone
from pathlib import Path
PACKAGE=Path(__file__).resolve().parents[1]
DEFAULT=Path.home()/'Documents/MPhill in biomedical sciences (medical microbiology)/GitHub tracker/MPHILL-research-2026'

def run(args,cwd,**kw):
    return subprocess.run([str(a) for a in args],cwd=cwd,check=True,**kw)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def safe_name(name):
    path=Path(name)
    return not path.is_absolute() and '..' not in path.parts and not any(p in {'.git','.venv','var','backups','__pycache__','.env'} for p in path.parts)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--target',type=Path,default=DEFAULT);p.add_argument('--yes',action='store_true');p.add_argument('--no-deps',action='store_true',help='Skip pip when the existing environment already has all pinned dependencies.');args=p.parse_args()
    if hasattr(os,'geteuid') and os.geteuid()==0:raise SystemExit('Run as your normal account, not sudo/root.')
    if sys.version_info<(3,11):raise SystemExit('Python 3.11 or newer is required.')
    target=args.target.expanduser().resolve()
    if target==PACKAGE:raise SystemExit('Extract the release outside your installed repository, then run this installer.')
    for name in ('manage.py','backend','web','.venv/bin/python'):
        if not (target/name).exists():raise SystemExit(f'Missing {name} in {target}. Select the existing installed clone with --target.')
    top=run(['git','rev-parse','--show-toplevel'],target,capture_output=True,text=True).stdout.strip()
    if Path(top).resolve()!=target:raise SystemExit('Target is not the actual Git repository root.')
    manifest=json.loads((PACKAGE/'RELEASE-MANIFEST.json').read_text())['files']
    baseline=json.loads((PACKAGE/'scripts/baseline-sha256.json').read_text())
    for name,expected in manifest.items():
        src=PACKAGE/name;dest=target/name
        if not safe_name(name) or src.is_symlink() or not src.is_file() or digest(src)!=expected:raise SystemExit('Release integrity check failed: '+name)
        if any(x.is_symlink() for x in [dest,*list(dest.parents)[:len(Path(name).parts)-1]]):raise SystemExit('Refusing a symlink destination: '+name)
        if dest.exists() and not dest.is_file():raise SystemExit('Destination is not a file: '+name)
        if dest.exists() and name not in ('index.html','.gitignore') and digest(dest) not in [expected,*baseline.get(name,[])]:
            raise SystemExit('Local source customization detected: '+name+'\nNo source was replaced. Back up and merge that customization before upgrading.')
    env={k:v for k,v in os.environ.items() if k.startswith('TED2_')}
    config=target/'.env'
    if config.is_symlink():raise SystemExit('Review the .env symlink manually before upgrading.')
    if config.exists():
        for line in config.read_text().splitlines():
            line=line.strip()
            if not line or line.startswith('#'):continue
            key,sep,value=line.partition('=')
            if not sep or not re.fullmatch('TED2_[A-Z_]+',key):raise SystemExit('Invalid .env configuration.')
            env.setdefault(key,value.strip().strip('"').strip("'"))
    db=Path(env.get('TED2_DB',str(target/'var/ted2.sqlite3'))).expanduser()
    if not db.is_absolute():db=target/db
    db=db.resolve()
    if not db.is_file():raise SystemExit('Existing database not found: '+str(db)+'\nDo not initialize a replacement database.')
    # A listening instance must be stopped before copying code or migrating.
    import socket
    from urllib.parse import urlsplit
    origin=urlsplit(env.get('TED2_BASE_URL','http://127.0.0.1:8000'))
    port=origin.port or (443 if origin.scheme=='https' else 80)
    with socket.socket() as sock:
        sock.settimeout(.3)
        if sock.connect_ex(('127.0.0.1',port))==0:raise SystemExit(f'Stop the running server first (port {port} is listening), then retry.')
    print('Package:  ',PACKAGE,'\nRepository:',target,'\nDatabase:  ',db)
    print('This preserves .git, .venv, .env, accounts, uploads and owner-edited database fields.\nThe compiled root index.html is rebuilt from approved database content. Current source and data are backed up privately.')
    if not args.yes and input('Type UPGRADE to continue: ').strip()!='UPGRADE':raise SystemExit('Cancelled; nothing changed.')
    backup=Path.home()/'TED2-private-backups'/('v4-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:8])
    backup.mkdir(parents=True,mode=0o700);backup.chmod(0o700)
    for name in list(manifest)+['RELEASE-MANIFEST.json','.env']:
        current=target/name
        if current.is_file():
            dest=backup/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(current,dest)
    with sqlite3.connect(db) as src,sqlite3.connect(backup/'ted2.sqlite3') as dest:src.backup(dest)
    (backup/'ted2.sqlite3').chmod(0o600)
    upload_dir=db.parent/'uploads'
    if upload_dir.exists():
        if any(path.is_symlink() for path in upload_dir.rglob('*')):raise SystemExit('Symlink found in uploads. No source copied; inspect it before retrying.')
        shutil.copytree(upload_dir,backup/'uploads')
    print('Private backup:',backup)
    python=target/'.venv/bin/python'
    if not args.no_deps:run([python,'-m','pip','install','-r',PACKAGE/'requirements.txt'],target)
    for name in manifest:
        if name=='index.html':continue
        dest=target/name;dest.parent.mkdir(parents=True,exist_ok=True)
        if name=='.gitignore' and dest.exists():
            content=dest.read_text();addition='\n# TED2 V4 private/runtime exclusions\n'+(PACKAGE/name).read_text()
            if (PACKAGE/name).read_text() not in content:dest.write_text(content+addition)
        else:shutil.copy2(PACKAGE/name,dest)
    shutil.copy2(PACKAGE/'RELEASE-MANIFEST.json',target/'RELEASE-MANIFEST.json')
    run([python,'manage.py','upgrade-content'],target)
    run([python,'manage.py','upgrade-content','--apply'],target)
    run([python,'manage.py','export-public','--output','index.html'],target)
    print('\nV4 installed. Existing data preserved. No Git commit or push has been made.')
    print('Review and commit: bash scripts/commit-v4.sh\nPush source: git push origin main\nStart backend: .venv/bin/python manage.py serve')
    print('Recovery backup:',backup)
if __name__=='__main__':
    try:main()
    except (OSError,ValueError,subprocess.CalledProcessError) as e:raise SystemExit('Upgrade stopped: '+str(e)+'\nKeep any printed private backup. Do not delete the database.')
