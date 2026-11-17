"""Board/part keepout STEP models from new placements. No supplier lead geometry."""
from pathlib import Path
import json
import cadquery as cq
R=Path(__file__).resolve().parents[1]
P=json.loads((R/'engineering/placements.json').read_text());F=json.loads((R/'engineering/footprints.json').read_text());B=json.loads((R/'engineering/circuits.json').read_text())['boards']
o=R/'electronics/space_models';o.mkdir(exist_ok=True);checks=[]
for b in B:
 w,h=b['size_mm'];bid=b['id'];base=cq.Workplane('XY').box(w,h,1.6,centered=(False,False,False))
 for x,y in b['holes']:base=base.cut(cq.Workplane('XY').center(x,y).circle(1.1 if w<30 else 1.6).extrude(1.6))
 ass=cq.Assembly(name=bid+'_SPACE_ONLY');ass.add(base,name='PCB_outline',color=cq.Color(.15,.4,.25))
 for c in [x for x in P if x['board']==bid]:
  d=F[c['fp']];x,y=c['pcb_xy'];z=1.6 if c['side']=='F' else -d['z'];body=cq.Workplane('XY').box(d['w'],d['h'],d['z'],centered=(True,True,False)).translate((x,y,z))
  ass.add(body,name=c['ref'],color=cq.Color(.55,.55,.58));checks.append(dict(board=bid,ref=c['ref'],valid=body.val().isValid(),volume_mm3=body.val().Volume(),scope='rectangular courtyard-height keepout, NOT exact body or leads'))
 ass.save(str(o/(bid+'_space_review.step')))
(R/'evidence/space_model_checks.json').write_text(json.dumps(checks,indent=2));print('4 STEP board/part space envelopes generated; not native ECAD export.')
