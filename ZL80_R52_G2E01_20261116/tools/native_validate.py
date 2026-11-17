#!/usr/bin/env python3
"""Call installed native tools and retain their actual reports; never substitute text checks.
Usage: python tools/native_validate.py [--kicad-cli /path/to/kicad-cli] [--ngspice /path/to/ngspice]
No board programming, laser enable, production Gerber export or deletion occurs.
"""
from pathlib import Path
import argparse,shutil,subprocess,json,datetime,hashlib
R=Path(__file__).resolve().parents[1]
def execute(cmd,log):
 try:
  p=subprocess.run(cmd,capture_output=True,text=True,errors='replace',timeout=180)
  log.write_text(p.stdout+'\n'+p.stderr,encoding='utf-8');return dict(status='EXECUTED',returncode=p.returncode,command=cmd,log=str(log.relative_to(R)))
 except Exception as e:
  log.write_text(str(e),encoding='utf-8');return dict(status='ERROR',command=cmd,error=str(e))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--kicad-cli');ap.add_argument('--ngspice');a=ap.parse_args()
 d=R/'evidence/native';d.mkdir(parents=True,exist_ok=True)
 report={'run_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Native ERC/DRC/SPICE only; no bench testing','boards':{},'spice':{}}
 kc=a.kicad_cli or shutil.which('kicad-cli');ng=a.ngspice or shutil.which('ngspice')
 if kc:report['kicad_version']=execute([kc,'version'],d/'kicad_version.log')
 for bid in ['B06','B07','B08','B01']:
  p=R/'electronics/projects'/bid;sc=p/(bid+'_G2E01.kicad_sch');pc=p/(bid+'_G2E01.kicad_pcb')
  report['boards'][bid]={}
  for mode,f in [('sch',sc),('pcb',pc)]:
   op='erc' if mode=='sch' else 'drc';name=bid+'_'+op
   if not kc:report['boards'][bid][op]={'status':'NOT_RUN','reason':'kicad-cli executable unavailable'};continue
   cmd=[kc,mode,op,'--format','json','--exit-code-violations','-o',str(d/(name+'.json')),str(f)]
   report['boards'][bid][op]=execute(cmd,d/(name+'.log'))
  if kc:report['boards'][bid]['pdf']=execute([kc,'sch','export','pdf','-o',str(d/(bid+'_native.pdf')),str(sc)],d/(bid+'_pdf.log'))
 for f in (R/'simulations/spice').glob('*.cir'):
  if not ng:report['spice'][f.name]={'status':'NOT_RUN','reason':'ngspice executable unavailable'};continue
  report['spice'][f.name]=execute([ng,'-b',str(f)],d/(f.stem+'.log'))
 report['bench']={'status':'NOT_RUN','reason':'No hardware in this execution environment'}
 report['release']='BLOCKED: native success alone cannot approve procurement/layout or bench performance.'
 (R/'evidence/native_tool_status.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
