"""Three discrete nominal upper-roller positions; not a continuous swept-volume proof."""
from pathlib import Path
import json,itertools
import cadquery as cq
R=Path(__file__).resolve().parents[1]
rows=json.loads((R/'cad/instances.json').read_text()); cache={}
def placed(r,lift):
 pid=r['part']
 if pid not in cache:cache[pid]=cq.importers.importStep(str(R/'cad/parts'/f'{pid}.step')).val()
 s=cache[pid];v=list(r['position'])
 if r['rotation']:axis,angle=r['rotation'];s=s.rotate((0,0,0),axis,angle)
 if r['moves_with_upper']:v[2]+=lift
 if r['group']=='spring':
  h=13.9-lift;s=cq.Solid.makeCylinder(2.5,h,cq.Vector(0,0,-h/2)).cut(cq.Solid.makeCylinder(1.5,h+2,cq.Vector(0,0,-h/2-1)));v[2]+=lift/2
 return s.translate(v)
def bbox(s):
 b=s.BoundingBox();return [b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax]
def overlaps(a,b):return all(min(a[i+3],b[i+3])-max(a[i],b[i])>.002 for i in range(3))
def expected(a,b):
 ns=[a['name'],b['name']]
 return ((any('SCREW' in n for n in ns) and any(n.startswith(('FRAME_R','FRAME_L','SLIDER_')) for n in ns)) or (any(n.startswith('UPPER_NUT') for n in ns) and any(n.startswith('UPPER_CORE') for n in ns)) or (any(n.startswith('ADJUST_') for n in ns) and any(n.startswith('TOP_') and 'SCREW' not in n for n in ns)) or (any(n.startswith('LIFT_ROD_') for n in ns) and any(n.startswith('SLIDER_') for n in ns)))
out=[]
for lift in (0,2.5,5):
 ss={r['name']:placed(r,lift) for r in rows if r['group'] not in ('reference','enclosure')};bb={k:bbox(s) for k,s in ss.items()};res=[];n=0
 for a,b in itertools.combinations(rows,2):
  if a['name'] not in ss or b['name'] not in ss:continue
  if not (a['moves_with_upper'] or b['moves_with_upper'] or a['group']=='spring' or b['group']=='spring'):continue
  if not overlaps(bb[a['name']],bb[b['name']]):continue
  n+=1;v=ss[a['name']].intersect(ss[b['name']]).Volume()
  if v>.01:res.append({'a':a['name'],'b':b['name'],'volume_mm3':round(v,5),'classification':'EXPECTED_THREAD_ENGAGEMENT' if expected(a,b) else 'REVIEW_REQUIRED'})
 out.append({'upper_lift_mm':lift,'candidate_pairs':n,'intersections':res,'unresolved':sum(x['classification']=='REVIEW_REQUIRED' for x in res)})
(R/'validation/results/release_position_audit.json').write_text(json.dumps({'scope':'0/2.5/5mm nominal positions; moving upper items versus core only; no continuous collision, spring buckling, real thread or operator-force test','positions':out},ensure_ascii=False,indent=2))
print([(x['upper_lift_mm'],x['candidate_pairs'],x['unresolved']) for x in out])
