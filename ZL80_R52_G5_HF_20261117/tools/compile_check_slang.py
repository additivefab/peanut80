"""Compile/elaboration-level check of every RTL file with every bench using slang (pip install pyslang==8.1.0).
This is NOT simulation. 'no time scale' diagnostics are ignored (the RTL files carry no `timescale; the benches do)."""
import sys,json
from pathlib import Path
import pyslang
R=Path(__file__).resolve().parents[1];rtl=sorted(str(p) for p in (R/'rtl').rglob('*.sv'));res=[]
for tb in sorted((R/'sim/tb').glob('tb_*.sv'))+[None]:
    c=pyslang.Compilation()
    for f in rtl+([str(tb)] if tb else []):c.addSyntaxTree(pyslang.SyntaxTree.fromFile(f))
    errs=[pyslang.DiagnosticEngine.reportAll(c.sourceManager,[d]).strip() for d in c.getAllDiagnostics() if d.isError()]
    errs=[e for e in errs if 'time scale' not in e]
    res.append({'top':tb.stem if tb else 'rtl_only','errors':len(errs),'first':errs[:3]})
out={'scope':'SLANG_COMPILE_ELABORATION_ONLY_NOT_SIMULATION','tool':'pyslang '+getattr(pyslang,'__version__','8.1.0'),'results':res,
     'status':'PASS' if all(r['errors']==0 for r in res) else 'FAIL'}
(R/'validation/results/slang_compile_check.json').write_text(json.dumps(out,indent=2));print(out['status'],[ (r['top'],r['errors']) for r in res]);sys.exit(0 if out['status']=='PASS' else 1)
