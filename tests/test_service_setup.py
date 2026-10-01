"""Exercise provisioning orchestration with a fake CLI; never creates cloud resources."""
from pathlib import Path
import tempfile,subprocess,shutil,os,json
ROOT=Path(__file__).resolve().parents[1]
checks=[]
def check(x,label):
    assert x,label
    checks.append(label);print('PASS',label)
with tempfile.TemporaryDirectory(prefix='ted2-gateway-setup-') as td:
    tmp=Path(td);repo=tmp/'workspace with spaces';repo.mkdir();shutil.copytree(ROOT/'responses-service',repo/'responses-service')
    subprocess.run(['git','init','-q',str(repo)],check=True)
    commands=tmp/'commands.jsonl';mock=tmp/'mock';mock.mkdir();dbid='12345678-1234-4567-8901-123456789012'
    script='''#!/usr/bin/env python3
import sys,os,json,pathlib
a=sys.argv[1:];log=pathlib.Path(os.environ['MOCK_LOG']);f=log.open('a');f.write(json.dumps(a)+'\\n');f.close();marker=log.parent/'created'
if a[:2]!=['--yes','wrangler@4']:sys.exit(50)
a=a[2:]
if a==['login']:print('Mock authenticated');sys.exit()
if a==['d1','list','--json']:print(json.dumps([{'name':'lab-v7-responses','uuid':'DBID'}] if marker.exists() else []));sys.exit()
if a==['d1','create','lab-v7-responses']:marker.write_text('1');print('Created');sys.exit()
if a==['d1','info','lab-v7-responses','--json']:print(json.dumps({'name':'lab-v7-responses','uuid':'DBID'}));sys.exit()
if a==['d1','execute','lab-v7-responses','--remote','--file','schema.sql','--yes']:sys.exit()
if a==['deploy']:print('https://lab-v7.example.workers.dev');sys.exit()
if a==['secret','put','ADMIN_TOKEN']:secret=sys.stdin.read().strip();sys.exit(0 if len(secret)==64 else 20)
sys.exit(99)
'''.replace('DBID',dbid)
    (mock/'npx').write_text(script);(mock/'npx').chmod(0o755)
    env={**os.environ,'PATH':str(mock)+':'+os.environ['PATH'],'MOCK_LOG':str(commands)}
    def run(answer='DEPLOY\nlab-v7\n'):
        return subprocess.run(['bash','responses-service/setup.sh'],cwd=repo,env=env,input=answer,text=True,capture_output=True,timeout=20)
    p=run('NO\n');check(p.returncode!=0 and not commands.exists(),'Cancelled setup makes no external CLI call')
    p=run();check(p.returncode==0,p.stderr)
    seq=[json.loads(x)[2:] for x in commands.read_text().splitlines()];check(['d1','create','lab-v7-responses'] in seq,'Creation uses supported create syntax without --json')
    private=repo/'var/community-deploy';conf=json.loads((private/'wrangler.json').read_text());check(conf['d1_databases'][0]['database_id']==dbid,'Actual returned D1 identifier used in generated configuration')
    check(conf['observability']['enabled'] is False,'Application log collection is disabled in generated Worker settings')
    check(seq.index(['deploy'])<seq.index(['secret','put','ADMIN_TOKEN']),'Initial closed Worker exists before secret installation')
    token=(private/'admin-token.txt').read_text();check(len(token)==64,'Secret generated locally with correct length')
    check((private/'admin-token.txt').stat().st_mode&0o077==0,'Secret file is owner-only')
    p=run();check(p.returncode==0,p.stderr);seq=[json.loads(x)[2:] for x in commands.read_text().splitlines()];check(seq.count(['d1','create','lab-v7-responses'])==1,'Retry reuses existing database instead of recreating it')
    check((private/'admin-token.txt').read_text()==token,'Retry preserves the saved service key')
    p=run('DEPLOY\n../bad\n');check(p.returncode!=0,'Unsafe service name rejected')
    shutil.rmtree(repo/'.git');before=commands.read_bytes();p=run();check(p.returncode!=0 and commands.read_bytes()==before,'Extracted/non-Git folder is refused before provisioning')
print(f'{len(checks)} provisioning-orchestration checks passed with mocked Wrangler, not real deployment.')
