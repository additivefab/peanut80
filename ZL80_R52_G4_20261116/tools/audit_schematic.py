"""Independently reconstruct same-sheet wires/labels/pins from KiCad text.
NOT KiCad ERC. Supports this package's zero-rotation, single-sheet schematics only.
"""
from pathlib import Path
import sys,json,math
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from sexpr import loads,child,children,walk

def key(x,y):return (round(float(x),5),round(float(y),5))
def check(path):
 t=loads(path.read_text());points=set();wires=[];labels=[];pins=[]
 libs={x[1]:x for x in children(child(t,'lib_symbols'),'symbol')}
 for w in children(t,'wire'):
  ps=child(w,'pts');a,b=key(*ps[1][1:]),key(*ps[2][1:]);points.update([a,b]);wires.append((a,b))
 for l in children(t,'label'):
  at=child(l,'at');p=key(at[1],at[2]);points.add(p);labels.append((p,l[1]))
 for s in children(t,'symbol'):
  k=child(s,'lib_id')[1];at=child(s,'at');x,y=float(at[1]),float(at[2]);assert float(at[3])==0
  ref=next(p[2] for p in children(s,'property') if p[1]=='Reference')
  for p in walk(libs[k],'pin'):
   pp=child(p,'at');num=child(p,'number')[1];pos=key(x+float(pp[1]),y-float(pp[2]));points.add(pos);pins.append((ref,num,pos))
 parent={p:p for p in points}
 def find(p):
  while parent[p]!=p:parent[p]=parent[parent[p]];p=parent[p]
  return p
 def union(a,b):parent[find(a)]=find(b)
 def inside(p,a,b):
  return abs((p[0]-a[0])*(b[1]-a[1])-(p[1]-a[1])*(b[0]-a[0]))<1e-4 and min(a[0],b[0])-1e-5<=p[0]<=max(a[0],b[0])+1e-5 and min(a[1],b[1])-1e-5<=p[1]<=max(a[1],b[1])+1e-5
 for a,b in wires:
  for p in points:
   if inside(p,a,b):union(a,p)
 names={}
 for p,name in labels:names.setdefault(find(p),set()).add(name)
 conflicts=[dict(node=p,names=sorted(n)) for p,n in names.items() if len(n)>1]
 netlist=[dict(ref=ref,pin=num,nets=sorted(names.get(find(pos),set()))) for ref,num,pos in pins]
 return dict(file=str(path.relative_to(R)),pin_count=len(pins),wire_count=len(wires),label_count=len(labels),local_shorts=conflicts,pins=netlist)
def main():
 rr=[check(p) for p in sorted((R/'electronics/projects').glob('*/*.kicad_sch'))]
 import csv
 expected=list(csv.DictReader((R/'engineering/pin_net_types.csv').open(encoding='utf-8-sig')));bad=[]
 for report in rr:
  bid=Path(report['file']).parent.name;e={(x['ref'],x['pin']):x['net'] for x in expected if x['board']==bid}
  for p in report['pins']:
   ex=e[p['ref'],p['pin']];got=p['nets'];target=[ex] if ex else []
   if got!=target:bad.append(dict(board=bid,ref=p['ref'],pin=p['pin'],expected=target,actual=got))
 result=dict(scope='Independent KiCad text graph; NOT native ERC',status='PASS' if not bad and all(not r['local_shorts'] for r in rr) else 'FAIL',mismatches=bad,boards=rr)
 (R/'validation/results/schematic_graph_audit.json').write_text(json.dumps(result,indent=2))
 print(result['status'],'mismatches=',bad,'shorts=',[x['local_shorts'] for x in rr]);return 0 if result['status']=='PASS' else 1
if __name__=='__main__':sys.exit(main())
