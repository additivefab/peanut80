"""Geometric tests only: no motion-force, optics, electrical or manufacturing release."""
from pathlib import Path
import json,csv,itertools,time
import cadquery as cq
R=Path(__file__).resolve().parents[1]
rows=json.loads((R/'cad/instances.json').read_text()); meta=json.loads((R/'cad/parts.json').read_text())
cache={}
def shape(r):
 pid=r['part']
 if pid not in cache:cache[pid]=cq.importers.importStep(str(R/'cad/parts'/f'{pid}.step')).val()
 s=cache[pid]
 if r['rotation']:ax,a=r['rotation'];s=s.rotate((0,0,0),ax,a)
 return s.translate(r['position'])
def overlap(a,b):
 return all(min(a[k+3],b[k+3])-max(a[k],b[k])>.002 for k in range(3))
# Check four-roller physical solids vs one another, plus nearby inherited optics/boards.
cands=[]
for a,b in itertools.combinations(rows,2):
 if a['group']=='reference' or b['group']=='reference':continue
 if a['group']=='inherited' and b['group']=='inherited':continue
 if a['group']=='enclosure' and b['group']=='enclosure':continue
 if overlap(a['aabb'],b['aabb']):cands.append((a,b))
results=[]
for a,b in cands:
 try:
  v=shape(a).intersect(shape(b)).Volume()
  if v>.01:
   names=[a['name'],b['name']]; cls='REVIEW_REQUIRED'
   if any('SCREW' in n for n in names) and any(n.startswith(('FRAME_R','FRAME_L','SLIDER_')) for n in names):cls='EXPECTED_THREAD_ENGAGEMENT'
   if any(n.startswith('UPPER_NUT') for n in names) and any(n.startswith('UPPER_CORE') for n in names):cls='EXPECTED_THREAD_ENGAGEMENT'
   if any(n.startswith('ADJUST_') for n in names) and any(n.startswith('TOP_') and not 'SCREW' in n for n in names):cls='EXPECTED_THREAD_ENGAGEMENT'
   if any(n.startswith('LIFT_ROD_') for n in names) and any(n.startswith('SLIDER_') for n in names):cls='EXPECTED_THREAD_ENGAGEMENT'
   results.append({'a':a['name'],'b':b['name'],'volume_mm3':round(v,5),'classification':cls})
 except Exception as e:results.append({'a':a['name'],'b':b['name'],'volume_mm3':None,'classification':'CHECK_ERROR_'+type(e).__name__})
out={'scope':'new physical part pair overlaps and inherited context; envelope collisions may be intentional. No full interference certificate.', 'candidate_pairs':len(cands),'intersections':results,'valid_parts':sum(x['valid'] for x in meta),'total_parts':len(meta)}
(R/'validation/results/geometry_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
with open(R/'validation/results/intersections.csv','w',newline='',encoding='utf-8-sig') as f:
 w=csv.DictWriter(f,fieldnames=['a','b','volume_mm3','classification']);w.writeheader();w.writerows(results)
print(json.dumps(out,ensure_ascii=False,indent=2))
