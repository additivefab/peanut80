from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parents[1]
for s in ['prepare_design.py','route_candidates.py','build_ecad.py','audit_pcb.py','build_mcad.py','build_support.py']:
    subprocess.run([sys.executable,str(R/'tools'/s)],cwd=R,check=True)
print('Candidates rebuilt. Native validation and manual review still required.')
