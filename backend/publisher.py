"""Git publishing through an isolated index in the existing clone; never switch branches."""
from __future__ import annotations
import hashlib,json,os,re,subprocess,tempfile,time,uuid
from contextlib import contextmanager
from pathlib import Path
from fastapi import HTTPException
from .db import ROOT
from .release import release_files,fingerprint,write_files

REPO='MPHILL-LAB-TRACKER/MPHILL-research-2026'
BRANCH='gh-pages'

class Publisher:
    def __init__(self,store,uploads,root=ROOT,*,allow_local_remote=False):
        self.store=store;self.uploads=Path(uploads);self.root=Path(root).resolve();self.allow_local=allow_local_remote
        self.directory=store.path.parent/'publishing';self.directory.mkdir(mode=0o700,exist_ok=True)
    def git(self,*args,env=None,input=None,check=True,timeout=90):
        environment={k:v for k,v in os.environ.items() if not k.startswith('GIT_')}
        environment.update(GIT_TERMINAL_PROMPT='0',GIT_SSH_COMMAND='ssh -oBatchMode=yes -oStrictHostKeyChecking=yes')
        if env:environment.update(env)
        try:r=subprocess.run(['git','-C',str(self.root),'-c','core.hooksPath=/dev/null',*args],env=environment,input=input,capture_output=True,timeout=timeout)
        except (OSError,subprocess.TimeoutExpired):raise HTTPException(503,'Git is unavailable or timed out. Check your connection and terminal Git authentication.')
        if check and r.returncode:
            # Deliberately do not echo arbitrary stderr (it can contain credentials).
            raise HTTPException(409,'Git operation failed. Check terminal authentication (gh auth login; gh auth setup-git), repository access, Git identity and branch protection. No force-push was used.')
        return r
    def configuration(self):
        top=self.git('rev-parse','--show-toplevel').stdout.decode().strip()
        if Path(top).resolve()!=self.root:raise HTTPException(409,'Run the backend inside the actual MPHILL-research-2026 clone, not its parent folder.')
        urls=self.git('remote','get-url','--push','--all','origin').stdout.decode().splitlines()
        if len(urls)!=1:raise HTTPException(409,'Exactly one origin push destination is required.')
        url=urls[0]
        valid=re.fullmatch(r'(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)'+re.escape(REPO)+r'(?:\.git)?',url,re.I)
        if not valid and not (self.allow_local and Path(url).is_absolute()):
            raise HTTPException(409,'Origin must point to MPHILL-LAB-TRACKER/MPHILL-research-2026 on GitHub, without embedded credentials.')
        return {'repository':REPO,'branch':BRANCH,'root':top,'remote':url,'website':'https://mphill-lab-tracker.github.io/MPHILL-research-2026/'}
    @contextmanager
    def lock(self):
        import fcntl
        with (self.directory/'publisher.lock').open('a+b') as lock:
            try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise HTTPException(409,'A publish or preview is already running. Wait for it to finish.')
            try:yield
            finally:fcntl.flock(lock,fcntl.LOCK_UN)
    def prepare(self,actor):
        self.configuration()
        with self.lock():
            files=release_files(self.store,self.uploads);rid=uuid.uuid4().hex;directory=self.directory/rid
            directory.mkdir(mode=0o700);write_files(files,directory/'site')
            meta={'id':rid,'actor':actor['id'],'created':time.time(),'digest':fingerprint(files),'files':{n:hashlib.sha256(v).hexdigest() for n,v in files.items()},'bytes':sum(map(len,files.values()))}
            (directory/'manifest.json').write_text(json.dumps(meta));(directory/'manifest.json').chmod(0o600)
            return {'id':rid,'preview_url':f'/api/publish/preview/{rid}/index.html','files':len(files),'bytes':meta['bytes'],'digest':meta['digest'],'branch':BRANCH}
    def manifest(self,rid,actor):
        if not re.fullmatch(r'[a-f0-9]{32}',rid):raise HTTPException(404,'Preview not found.')
        path=self.directory/rid/'manifest.json'
        if not path.is_file():raise HTTPException(404,'Preview not found.')
        meta=json.loads(path.read_text())
        if meta['actor']!=actor['id']:raise HTTPException(403,'Prepare a preview using your own account.')
        if time.time()-meta['created']>1800:raise HTTPException(409,'This preview expired. Prepare a fresh one.')
        return meta
    def push(self,rid,actor):
        config=self.configuration()
        with self.lock():
            meta=self.manifest(rid,actor)
            if meta.get('published'):raise HTTPException(409,'This preview has already been published. Prepare a new preview.')
            current=release_files(self.store,self.uploads)
            if fingerprint(current)!=meta['digest']:raise HTTPException(409,'Public content or code changed after this preview. Prepare and review a new preview.')
            site=self.directory/rid/'site'
            for name,expected in meta['files'].items():
                p=site/name
                if p.is_symlink() or not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=expected:raise HTTPException(409,'Preview integrity check failed. Prepare a new preview.')
            remote=config['remote']
            tip=self.git('ls-remote','--heads',remote,'refs/heads/'+BRANCH).stdout.decode().strip()
            parent=tip.split()[0] if tip else ''
            if parent:
                if not re.fullmatch(r'[a-f0-9]{40,64}',parent):raise HTTPException(409,'Invalid remote branch response.')
                self.git('fetch','--no-tags','--no-write-fetch-head',remote,parent)
            gitdir=self.git('rev-parse','--absolute-git-dir').stdout.decode().strip()
            with tempfile.TemporaryDirectory(prefix='ted2-index-',dir=self.directory) as tmp:
                env={'GIT_DIR':gitdir,'GIT_WORK_TREE':str(site),'GIT_INDEX_FILE':str(Path(tmp)/'index')}
                self.git('read-tree','--empty',env=env)
                lines=[]
                for name in sorted(meta['files']):
                    blob=self.git('hash-object','-w','--stdin',env=env,input=(site/name).read_bytes()).stdout.strip()
                    lines.append(b'100644 '+blob+b'\t'+name.encode()+b'\0')
                self.git('update-index','-z','--index-info',env=env,input=b''.join(lines))
                tree=self.git('write-tree',env=env).stdout.decode().strip()
                args=['commit-tree',tree]+(['-p',parent] if parent else [])+['-m','Publish TED2 approved website · '+rid[:8]]
                commit=self.git(*args,env=env).stdout.decode().strip()
                self.git('push','--porcelain',remote,commit+':refs/heads/'+BRANCH,timeout=180)
            meta['published']=time.time();meta['commit']=commit
            (self.directory/rid/'manifest.json').write_text(json.dumps(meta))
            with self.store.connect(write=True) as c:self.store.audit(c,actor['username'],'publish-github','website',rid,after={'commit':commit,'branch':BRANCH,'digest':meta['digest']})
            return {'ok':True,'commit':commit,'branch':BRANCH,'website':config['website'],'message':'Push succeeded. GitHub Pages deployment may still be running.'}
