"""Self-checking RTL simulation, only if real tools are present. Never fakes PASS."""
from pathlib import Path
import argparse,subprocess,shutil,json,sys,os
R=Path(__file__).resolve().parents[1];O=R/'validation/results/native';O.mkdir(parents=True,exist_ok=True)
p=argparse.ArgumentParser();p.add_argument('--iverilog');p.add_argument('--vvp');a=p.parse_args()
iv=a.iverilog or shutil.which('iverilog');vv=a.vvp or shutil.which('vvp')
benches=sorted((R/'sim/tb').glob('tb_*.sv'));results=[]
if not iv or not vv:
    for tb in benches:results.append({'test':tb.stem,'status':'NOT_RUN','reason':'iverilog/vvp unavailable'})
else:
    for tb in benches:
        d=O/tb.stem;d.mkdir(parents=True,exist_ok=True);exe=d/'sim.vvp'
        cmd=[iv,'-g2012','-Wall','-s',tb.stem,'-o',str(exe)]+[str(x) for x in sorted((R/'rtl').rglob('*.sv'))]+[str(tb)]
        try:
            c=subprocess.run(cmd,cwd=d,capture_output=True,text=True,timeout=60)
            (d/'compile.log').write_text(c.stdout+c.stderr)
            if c.returncode:results.append({'test':tb.stem,'status':'FAIL_COMPILE','returncode':c.returncode});continue
            s=subprocess.run([vv,str(exe)],cwd=d,capture_output=True,text=True,timeout=90)
            (d/'simulate.log').write_text(s.stdout+s.stderr)
            ok=s.returncode==0 and 'PASS '+tb.stem in s.stdout
            results.append({'test':tb.stem,'status':'PASS' if ok else 'FAIL_SIM','returncode':s.returncode})
        except (OSError,subprocess.TimeoutExpired) as e:results.append({'test':tb.stem,'status':'ERROR','reason':str(e)})
status='PASS' if results and all(x['status']=='PASS' for x in results) else ('NOT_RUN' if not iv or not vv else 'FAIL')
report={'scope':'ACTUAL_IVERILOG_RTL_SIMULATION','status':status,'tools':{'iverilog':iv,'vvp':vv},'tests':results,
        'vivado_synthesis':'NOT_RUN','vivado_implementation_timing':'NOT_RUN','physical_bench':'NOT_RUN'}
(O.parent/'native_validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2));sys.exit(0 if status=='PASS' else 2)
