"""Run the REAL KiCad CLI when installed. No substitute PASS on missing tools.
Run after filling zones in KiCad and saving. This script never generates manufacturing outputs.
"""
import argparse,json,subprocess,shutil,sys,datetime,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def run(cmd):
 try:
  p=subprocess.run(cmd,capture_output=True,text=True,timeout=180)
  return dict(command=cmd,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr,status='TOOL_EXIT_OK_REVIEW_REPORT' if p.returncode==0 else 'VIOLATIONS_OR_TOOL_ERROR')
 except (OSError,subprocess.TimeoutExpired) as ex:return dict(command=cmd,status='TOOL_ERROR',error=str(ex))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--kicad-cli');args=ap.parse_args();exe=args.kicad_cli or shutil.which('kicad-cli');out=R/'validation/results/native';out.mkdir(exist_ok=True,parents=True)
 result={'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'kicad_cli':exe,'zone_refill':'MANUAL_REQUIRED_BEFORE_DRC','checks':[],'release':'BLOCKED'}
 if not exe:result['status']='NOT_RUN';result['reason']='kicad-cli not installed/in PATH; no native parse/ERC/DRC performed'
 else:
  result['version']=run([exe,'--version']);result['status']='EXECUTED_REVIEW_REQUIRED'
  for bid in ['B06','B07','B08','B01']:
   base=R/'electronics/projects'/bid/(bid+'_G4');sch=str(base.with_suffix('.kicad_sch'));pcb=str(base.with_suffix('.kicad_pcb'))
   for ty,source in [('sch',sch),('pcb',pcb)]:
    mode='erc' if ty=='sch' else 'drc';rep=str(out/(bid+'_'+mode+'.json'));cmd=[exe,ty,mode,'--format','json','--severity-all','--exit-code-violations','--output',rep]
    if ty=='pcb':cmd+=['--schematic-parity','--all-track-errors']
    cmd+=[source];res=run(cmd);res['source_sha256']=hashlib.sha256(Path(source).read_bytes()).hexdigest();res['board']=bid;res['report']=rep;result['checks'].append(res)
  if any(c.get('returncode')!=0 for c in result['checks']):result['status']='HAS_VIOLATIONS_OR_ERRORS'
 (R/'validation/results/native_tools.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
 print(result['status']);return 2 if not exe else int(result['status']=='HAS_VIOLATIONS_OR_ERRORS')
if __name__=='__main__':sys.exit(main())
