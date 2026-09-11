#!/usr/bin/env python3
"""Manage TED² without shipping or printing passwords or private data."""
from __future__ import annotations
import argparse,getpass,os,re,sqlite3,sys,uuid,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def environment():
    env=ROOT/'.env'
    if env.is_file():
        for line in env.read_text().splitlines():
            line=line.strip()
            if not line or line.startswith('#'): continue
            if '=' not in line: raise SystemExit('Invalid .env line; expected KEY=value.')
            key,val=line.split('=',1)
            if not re.fullmatch(r'TED2_[A-Z_]+',key): raise SystemExit('Only TED2_ settings are accepted in .env.')
            os.environ.setdefault(key,val.strip().strip('"').strip("'"))

def store():
    from backend.db import Store
    db=Store(os.getenv('TED2_DB',str(ROOT/'var/ted2.sqlite3')));db.initialize();return db

def prompt_password():
    p=getpass.getpass('Password (at least 12 characters): ')
    if p!=getpass.getpass('Confirm password: '): raise SystemExit('Passwords do not match. No account was created.')
    return p

def create_owner(db,username,password):
    from backend.security import password_hash
    from backend.db import now
    if not re.fullmatch(r'[a-z0-9][a-z0-9._-]{2,59}',username): raise ValueError('Use a lowercase username of 3–60 letters, digits, dots, underscores or hyphens.')
    hashed=password_hash(password);uid=uuid.uuid4().hex
    with db.connect(write=True) as c:
        if c.execute('SELECT COUNT(*) FROM users').fetchone()[0]: raise ValueError('Accounts already exist. Use the owner account screen or reset-password.')
        c.execute("INSERT INTO users VALUES(?,?,?,'owner','',1,?)",(uid,username,hashed,now()))
        db.audit(c,username,'initial-owner','users',uid,after={'username':username,'role':'owner'})
    return uid

def main():
    environment();parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    init=sub.add_parser('init',help='Seed public content and create the first owner');init.add_argument('--username')
    server=sub.add_parser('serve',help='Serve locally (use a TLS reverse proxy in production)');server.add_argument('--host',default='127.0.0.1');server.add_argument('--port',type=int,default=8000)
    sub.add_parser('build-public',help='Rebuild root index.html from the public seed')
    upgrade=sub.add_parser('upgrade-content',help='Preview/apply the V4 studio, media and profile update while preserving owner edits');upgrade.add_argument('--apply',action='store_true')
    export=sub.add_parser('export-public',help='Build current approved database content into a public HTML snapshot');export.add_argument('--output',type=Path,default=ROOT/'index.html')
    reset=sub.add_parser('reset-password',help='Local-server emergency password reset');reset.add_argument('username')
    backup=sub.add_parser('backup',help='Back up private database and uploads securely');backup.add_argument('destination',type=Path)
    sub.add_parser('configure-production',help='Write production settings interactively')
    args=parser.parse_args()
    if args.command=='build-public':
        from backend.build import build_seed
        print('Built',build_seed());return
    if args.command=='configure-production':
        from urllib.parse import urlsplit
        origin=input('Public HTTPS server origin (no trailing path): ').strip().rstrip('/')
        p=urlsplit(origin)
        if p.scheme!='https' or not p.netloc or p.path or p.query or p.fragment or p.username: raise SystemExit('A public HTTPS origin without a path is required.')
        dest=ROOT/'.env'
        if dest.exists() and input('Replace existing .env settings? Type yes: ').strip()!='yes': raise SystemExit('Cancelled.')
        dest.write_text('TED2_PRODUCTION=1\nTED2_BASE_URL='+origin+'\nTED2_PUBLIC_ORIGINS=https://mphill-lab-tracker.github.io\n')
        try: os.chmod(dest,0o600)
        except OSError: pass
        print('Saved .env. Configure HTTPS and persistent storage before exposing the server.');return
    db=store()
    if args.command=='export-public':
        from backend.release import release_files
        target=args.output.resolve()
        if target.suffix.lower()!='.html' or target==db.path:raise SystemExit('Choose an HTML output filename.')
        target.write_bytes(release_files(db,db.path.parent/'uploads',embedded=True)['index.html'])
        print('Exported approved public website:',target);return
    if args.command=='upgrade-content':
        import json
        from backend.content_update import upgrade_content
        try: report=upgrade_content(db,apply=args.apply)
        except ValueError as exc: raise SystemExit(str(exc))
        print(json.dumps(report,indent=2))
        if not args.apply: print('Preview only. Apply with: python manage.py upgrade-content --apply')
        return
    if args.command=='init':
        db.seed()
        with db.connect() as c: existing=c.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        if existing: print('Already initialized. Existing records and accounts were preserved.');return
        name=(args.username or input('Owner username: ')).strip().lower()
        try: create_owner(db,name,prompt_password())
        except ValueError as e: raise SystemExit(str(e))
        print('Owner account created. No public sign-up or default password exists.');return
    if args.command=='serve':
        with db.connect() as c: count=c.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        if not count: raise SystemExit('Create the first owner with: python manage.py init')
        if args.host not in ('localhost','127.0.0.1','::1') and 'TED2_BASE_URL' not in os.environ:
            raise SystemExit('Set the real TED2_BASE_URL before exposing the application outside loopback.')
        os.environ.setdefault('TED2_BASE_URL',f'http://127.0.0.1:{args.port}')
        from backend.app import create_app
        import uvicorn
        uvicorn.run(create_app(),host=args.host,port=args.port,proxy_headers=False,server_header=False,limit_concurrency=100,timeout_keep_alive=5)
    elif args.command=='reset-password':
        from backend.security import password_hash
        with db.connect() as c: user=c.execute('SELECT id FROM users WHERE username=?',(args.username.lower(),)).fetchone()
        if not user: raise SystemExit('No such account.')
        try: encoded=password_hash(prompt_password())
        except ValueError as e: raise SystemExit(str(e))
        with db.connect(write=True) as c:
            c.execute('UPDATE users SET password_hash=? WHERE id=?',(encoded,user['id']))
            c.execute('DELETE FROM sessions WHERE user_id=?',(user['id'],))
            db.audit(c,'server-operator','emergency-password-reset','users',user['id'])
        print('Password changed and all sessions for this account revoked. Account activation status was not changed.')
    elif args.command=='backup':
        destination=args.destination.resolve()
        if destination.is_relative_to(ROOT/'web') or destination==ROOT/'index.html': raise SystemExit('Private backups cannot be placed in the public web directory.')
        if destination.exists(): raise SystemExit('Choose a new backup filename; existing backups are not overwritten.')
        destination.parent.mkdir(parents=True,exist_ok=True)
        temp=db.path.parent/('backup-'+uuid.uuid4().hex+'.sqlite3')
        try:
            with db.connect() as source,sqlite3.connect(temp) as target: source.backup(target)
            # Immutable upload files are copied after the consistent SQLite backup.
            with sqlite3.connect(temp) as snapshot:
                files=list(snapshot.execute('SELECT path FROM uploads'))
            with zipfile.ZipFile(destination,'w',compression=zipfile.ZIP_DEFLATED) as z:
                z.write(temp,'ted2.sqlite3')
                for (path,) in files:
                    source=db.path.parent/'uploads'/path
                    if not source.is_file(): raise SystemExit('Missing upload in backup: '+path)
                    z.write(source,'uploads/'+path)
            try: os.chmod(destination,0o600)
            except OSError: pass
            print('Private backup created:',destination)
            print('Keep it outside the public repository; it contains accounts, sessions, research records and documents.')
        except BaseException:
            destination.unlink(missing_ok=True);raise
        finally: temp.unlink(missing_ok=True)

if __name__=='__main__': main()
