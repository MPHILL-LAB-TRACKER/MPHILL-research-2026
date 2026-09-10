#!/usr/bin/env python3
"""One-command local setup. The default host is loopback, not the internet."""
from __future__ import annotations
import argparse,importlib.util,os,subprocess,sys,venv
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--use-current-python',action='store_true',help='Use an already prepared Python environment');args=p.parse_args()
    if sys.version_info<(3,11): raise SystemExit('Python 3.11 or newer is required.')
    if not args.use_current_python:
        v=ROOT/'.venv';python=v/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
        if not python.exists():
            print('Creating an isolated Python environment…',flush=True)
            try: venv.EnvBuilder(with_pip=True).create(v)
            except Exception as exc: raise SystemExit('Could not create .venv. Install your operating system’s Python venv support. '+str(exc))
        marker=v/'ted2-requirements.txt';req=(ROOT/'requirements.txt').read_text()
        if not marker.exists() or marker.read_text()!=req:
            subprocess.run([str(python),'-m','pip','install','-r',str(ROOT/'requirements.txt')],check=True,cwd=ROOT)
            marker.write_text(req)
        return subprocess.run([str(python),str(ROOT/'start.py'),'--use-current-python'],cwd=ROOT).returncode
    missing=[name for name in ('fastapi','uvicorn','argon2','PIL','multipart') if importlib.util.find_spec(name) is None]
    if missing: raise SystemExit('Missing dependencies: '+', '.join(missing)+'. Run python start.py without --use-current-python.')
    subprocess.run([sys.executable,'manage.py','init'],cwd=ROOT,check=True)
    print('\nPublic site: http://127.0.0.1:8000/\nAdministration: http://127.0.0.1:8000/admin\nResearcher workspace: http://127.0.0.1:8000/workspace\nPress Ctrl+C to stop.\n',flush=True)
    try: return subprocess.run([sys.executable,'manage.py','serve'],cwd=ROOT).returncode
    except KeyboardInterrupt: return 0
if __name__=='__main__': sys.exit(main() or 0)
