"""Compile ONLY the three trusted packaged starter templates in a temporary directory.
Not a web feature: no arbitrary user source is executed. Requires pdflatex.
"""
from pathlib import Path
import subprocess,shutil,tempfile
ROOT=Path(__file__).resolve().parents[1]
if not shutil.which('pdflatex'):raise SystemExit('pdflatex is required only for this developer smoke test.')
with tempfile.TemporaryDirectory(prefix='ted2-trusted-template-') as temp:
    for kind in ('report','review','protocol'):
        out=Path(temp)/kind;out.mkdir()
        text=subprocess.check_output(['php','-r',"require 'php/bootstrap.php';echo Ted2\\Writing7::template($argv[1]);",kind],cwd=ROOT)
        (out/'main.tex').write_bytes(text)
        p=subprocess.run(['pdflatex','-no-shell-escape','-interaction=nonstopmode','-halt-on-error','main.tex'],cwd=out,capture_output=True,timeout=30)
        assert p.returncode==0,p.stdout.decode(errors='replace')[-4000:]
        assert (out/'main.pdf').stat().st_size>1000
        print('PASS trusted template compiles:',kind)
print('3 trusted source templates compiled. No online Overleaf project was created.')
