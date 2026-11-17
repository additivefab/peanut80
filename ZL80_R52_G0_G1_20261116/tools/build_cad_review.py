"""Reassemble inherited nominal STEP geometry; does not redesign vendor hardware."""
from pathlib import Path
import json,csv,sys
R=Path(__file__).resolve().parents[1]
import cadquery as cq
import ezdxf
rows=json.loads((R/'cad/instances.json').read_text())
parts={}
checks=[]
for p in sorted((R/'cad/parts').glob('*.step')):
 s=cq.importers.importStep(str(p)).val();parts[p.stem]=s
 b=s.BoundingBox()
 checks.append({'id':p.stem,'valid':s.isValid(),'volume_mm3':s.Volume(),'bbox_mm':[b.xlen,b.ylen,b.zlen]})
a=cq.Assembly(name='G1_Inherited_R5_ScanHead_Review')
b=cq.Assembly(name='G1_Interface_Context_Review')
for i,r in enumerate(rows):
 s=parts[r['part']]
 if r['rotation']:
  ax,ang=r['rotation'];s=s.rotate((0,0,0),ax,ang)
 s=s.translate(tuple(r['position']))
 color=cq.Color(.55,.58,.62)
 if r['part'].startswith('B'):color=cq.Color(.15,.45,.30)
 if r['part'].startswith('O'):color=cq.Color(.30,.40,.55)
 name=f'{i:02d}_{r["part"]}'
 b.add(s,name=name,color=color)
 if not r['part'].startswith('C'):a.add(s,name=name,color=color)
a.save(str(R/'cad/G1_Inherited_ScanHead_Review.step'))
b.save(str(R/'cad/G1_Interface_Context_Review.step'))
# Chief ray INPUT geometry: stop at nominal lens reference; there is no claimed lens prescription.
c=cq.Assembly(name='G1_InputChiefRays_NOT_FULL_OPTICS')
rr=list(csv.DictReader((R/'results/polygon_chief_rays.csv').open(encoding='utf-8-sig')))
for i,r in enumerate(rr[::10]):
 h=(float(r['hit_x_mm']),0,float(r['hit_z_mm'])+110)
 lens=(float(r['lens_reference_x_mm']),0,210)
 c.add(cq.Edge.makeLine(cq.Vector(-95,0,245),cq.Vector(*h)),name=f'input_{i}')
 c.add(cq.Edge.makeLine(cq.Vector(*h),cq.Vector(*lens)),name=f'reflected_{i}')
 x=float(r['ideal_f_theta_x_mm'])
 c.add(cq.Edge.makeCircle(.6,cq.Vector(x,0,110),cq.Vector(0,0,1)),name=f'ideal_target_{i}')
c.save(str(R/'cad/G1_ChiefRay_InputGeometry.step'))
doc=ezdxf.new('R2010');doc.units=4;ms=doc.modelspace()
for layer in ['IMAGE80','SYNC92','SCAN100','SLOT104','NOTES']:doc.layers.new(layer)
for w,ly,y in [(80,'IMAGE80',0),(92,'SYNC92',10),(100,'SCAN100',20),(104,'SLOT104',30)]:
 ms.add_line((-w/2,y),(w/2,y),dxfattribs={'layer':ly})
 for x in (-w/2,w/2):ms.add_line((x,y-2),(x,y+2),dxfattribs={'layer':ly})
 ms.add_text(f'{ly}: {w} mm',dxfattribs={'height':2.5,'layer':'NOTES','insert':(60,y)})
ms.add_lwpolyline([(-52,-.6),(52,-.6),(52,.6),(-52,.6)],close=True,dxfattribs={'layer':'SLOT104'})
ms.add_text('INTERFACE REFERENCE ONLY - NOT A MANUFACTURING DRAWING',dxfattribs={'height':2.5,'insert':(-52,42),'layer':'NOTES'})
doc.saveas(R/'cad/G1_Field_Boundaries_Interface.dxf')
result={'method':'CadQuery STEP import, isValid, volume and bbox; inherited source geometry reassembled',
'parts_count':len(checks),'instances_count':len(rows),'parts':checks,
'full_interference':'NOT_RUN','native_freecad':'NOT_RUN','manufacturing':'NOT_RELEASED'}
(R/'validation/cad_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print('CAD',len(checks),'parts,',len(rows),'instances; all_valid=',all(c['valid'] for c in checks))
