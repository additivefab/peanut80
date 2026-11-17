import subprocess,sys,json,datetime
from pathlib import Path
R=Path(__file__).resolve().parents[1]
for s in ['audit_schematic.py','audit_pcb.py']:
 subprocess.run([sys.executable,str(R/'tools'/s)],check=True,cwd=R)
p=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=R,capture_output=True,text=True)
(R/'validation/results/python_tests.log').write_text(p.stdout+p.stderr)
print(p.stdout+p.stderr);sys.exit(p.returncode)
