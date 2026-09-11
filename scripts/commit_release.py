#!/usr/bin/env python3
"""Commit only release-manifest paths in the existing source clone. Never git add ."""
import argparse,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def git(*args,check=True):return subprocess.run(['git','-C',str(ROOT),*args],check=check,capture_output=True,text=True)
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--yes',action='store_true');args=parser.parse_args()
    if Path(git('rev-parse','--show-toplevel').stdout.strip()).resolve()!=ROOT:raise SystemExit('Run inside the installed clone, not the extracted ZIP folder.')
    if git('branch','--show-current').stdout.strip()!='main':raise SystemExit('Source release commits must be reviewed on main. Your branch was not changed.')
    staged=git('diff','--cached','--name-only').stdout.strip()
    if staged:raise SystemExit('Existing staged work found. Commit it separately before using this helper:\n'+staged)
    manifest=json.loads((ROOT/'RELEASE-MANIFEST.json').read_text())['files'];names=sorted(set(manifest)|{'RELEASE-MANIFEST.json'})
    for name in names:
        parts=Path(name).parts
        if Path(name).is_absolute() or '..' in parts or any(x in {'.git','.env','.venv','var','backups','__pycache__'} for x in parts):raise SystemExit('Unsafe release path: '+name)
        if (ROOT/name).is_symlink() or not (ROOT/name).is_file():raise SystemExit('Missing or symlink release file: '+name)
    private=[n for n in git('ls-files').stdout.splitlines() if re.search(r'(^|/)(?:var|backups|\.venv)/|(^|/)\.env$|\.sqlite',n)]
    if private:raise SystemExit('Private runtime files are already tracked; remove them from version control before pushing:\n'+'\n'.join(private))
    print(git('status','--short').stdout)
    print('Only the',len(names),'release-manifest paths will be staged. Databases, .env, uploads and other files are excluded.')
    if not args.yes and input('Type COMMIT to record V4: ').strip()!='COMMIT':raise SystemExit('Cancelled; no files were staged.')
    git('add','--',*names)
    if not git('diff','--cached','--name-only').stdout.strip():print('No new release changes to commit.');return
    print(git('diff','--cached','--stat').stdout)
    result=git('commit','-m','Upgrade TED2 Research Workspace to V4: media studio and authenticated publishing')
    print(result.stdout);print('Source commit created. Push it with: git push origin main')
if __name__=='__main__':
    try:main()
    except subprocess.CalledProcessError as e:raise SystemExit('Git stopped: '+e.stderr+'\nNo force-push or reset was attempted.')
