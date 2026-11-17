"""R5.2 collector change: place the trapezoid guide plate and the parts that move with it into the
R5-PDR1 core assembly and rerun the rigid nominal B-rep interference check (same rule as build_cad.py:
AABB broad phase, then OCC intersection volume > 0.01 mm3). Also checks the new collector parts against
the G3 four-roller package. Does not overwrite R5-PDR1 CAD; writes cad/step/ZL80_R52_core_review.step,
cad/instances_R52_delta.json and tests/cad_overlap_R52.json. Needs cadquery.
Usage: python cad/source/check_collector_r52.py [A|B]   (A = plain shift, B = with layout fixes; default B)"""
import json,sys
from pathlib import Path
import cadquery as cq
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
R=Path(__file__).resolve().parents[2]
P=json.loads((R/'engineering/parameters.json').read_text());g=P['collector_guide_r52'];zc=P['cavity_center_z']
variant=(sys.argv[1] if len(sys.argv)>1 else 'B').upper()
dy=g['pmt_shift_y_vs_r5']
def box(x,y,z,c=(0,0,0)):return cq.Workplane('XY').box(x,y,z).val().translate(cq.Vector(*c))
_cache={}
def load(folder,pid):
    k=(folder,pid)
    if k not in _cache:_cache[k]=cq.importers.importStep(str(R/folder/f'{pid}.step')).val()
    return _cache[k]
def placed(folder,row):
    s=load(folder,row['part'])
    if row['rotation']:axis,ang=row['rotation'];s=s.rotate((0,0,0),tuple(axis),ang)
    return s.translate(cq.Vector(*row['position']))
inst=[r for r in json.loads((R/'cad/instances.json').read_text()) if r['group'] not in ('enclosure','external','optional_external')]
MOVE={'C08','P03','P04','B01','H01'};delta=[];items=[]
side_slot=box(g['cavity_side_slot'][0],14,g['cavity_side_slot'][1],(0,-25,zc))
for r in inst:
    if r['part'] in ('C06','C07'):delta.append(dict(name=r['name'],part=r['part'],change='removed'));continue
    s=placed('cad/step',r);note=None
    moved=r['part'] in MOVE or r['name'].startswith('AFE_post') or r['name']=='Temp_PMT'
    if moved:s=s.translate(cq.Vector(0,dy,0));note=f'shift y {dy}'
    if r['part'] in ('C01','C02'):s=s.cut(side_slot);note='side slot %sx%s replaces the 8x10 window'%tuple(g['cavity_side_slot'])
    if variant=='B':
        f=g['layout_fix_b']
        if 'afe_top_z' in f and r['part'] in ('B01','H01'):
            s=s.cut(box(400,400,50,(0,0,f['afe_top_z']+25)));note+=f"; top trimmed to z {f['afe_top_z']}"
        if 'shield_notch' in f and r['part']=='H01':
            n=f['shield_notch']
            for xc in n['x_centres']:s=s.cut(box(2*n['half_width_x'],40,40,(xc,n['y_max']-20,n['z_min']+20)))
            note+=f"; local step-down to z {n['z_min']} at x {n['x_centres']} for y < {n['y_max']}"
        if r['name'].startswith('AFE_post') and r['position'][2]>80:
            s=s.translate(cq.Vector(0,0,f['afe_top_post_dz']));note+=f"; z {f['afe_top_post_dz']}"
    if note:b=s.BoundingBox();delta.append(dict(name=r['name'],part=r['part'],change=note,aabb=[round(v,2) for v in (b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax)]))
    items.append((r['name'],r['part'],s))
plate=cq.importers.importStep(str(R/'cad/step/C06_R52_plate.step')).val()
# flat light-tight shroud following the plate with side_face_clearance air gap, 1.5 mm wall, open at both ends
c=g['side_face_clearance_mm'];w0,w1,t,L,y0=g['input_width_x'],g['output_width_x'],g['thickness_z'],g['length_y'],g['input_face_y']
ya,yb=-30.5,y0-L+2.0
def wid(y,extra):return w0+(w1-w0)*(y0-y)/L+2*extra
def trap(extra,h):
    pts=[(-wid(ya,extra)/2,ya),(wid(ya,extra)/2,ya),(wid(yb,extra)/2,yb),(-wid(yb,extra)/2,yb)]
    return cq.Workplane('XY').workplane(offset=zc-h/2).polyline(pts).close().extrude(h).val()
inner=cq.Workplane('XY').workplane(offset=zc-(t+2*c)/2).polyline([(-wid(ya+1,c)/2-1,ya+1),(wid(ya+1,c)/2+1,ya+1),(wid(yb-1,c)/2,yb-1),(-wid(yb-1,c)/2,yb-1)]).close().extrude(t+2*c).val()
shroud=trap(c+1.5,t+2*c+3.0).cut(inner)
cq.exporters.export(cq.Workplane(obj=shroud),str(R/'cad/step/C07_R52_shroud.step'))
new=[('Guide_plate_R52','C06_R52',plate),('Guide_shroud_R52','C07_R52',shroud)]
for n,p,s in new:
    b=s.BoundingBox();delta.append(dict(name=n,part=p,change='new',aabb=[round(v,2) for v in (b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax)]))
items+=new
def aabb(s):b=s.BoundingBox();return [b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax]
def overlaps(A,B=None):
    out=[];bb=[aabb(s) for _,_,s in A];bb2=bb if B is None else [aabb(s) for _,_,s in B]
    for i,(na,pa,sa) in enumerate(A):
        for j,(nb,pb,sb) in enumerate(A[i+1:] if B is None else B):
            q=bb[i+1+j] if B is None else bb2[j]
            if min(min(bb[i][k+3],q[k+3])-max(bb[i][k],q[k]) for k in range(3))<=1e-5:continue
            try:v=sa.intersect(sb).Volume()
            except Exception:v=None
            if v is None or v>.01:out.append(dict(a=na,b=nb,a_part=pa,b_part=pb,volume_mm3=None if v is None else round(v,3)))
    return out
core=overlaps(items)
# G3 four-roller package: its own parts (not the REF_ copies of R5) against everything new or moved here
g3dir=R/'ZL80_R52_G3_20261116';g3=[]
for r in json.loads((g3dir/'cad/instances.json').read_text()):
    if r['part'].startswith('REF_') or r.get('group') in ('enclosure','case','external'):continue
    try:s=cq.importers.importStep(str(g3dir/'cad/parts'/f"{r['part']}.step")).val()
    except Exception:continue
    if r['rotation']:axis,ang=r['rotation'];s=s.rotate((0,0,0),tuple(axis),ang)
    g3.append((r['name'],r['part'],s.translate(cq.Vector(*r['position']))))
changed=[x for x in items if any(d['name']==x[0] for d in delta)]
vs_g3=overlaps(changed,g3)
def dist(a,b):
    d=BRepExtrema_DistShapeShape(a.wrapped,b.wrapped);d.Perform();return round(d.Value(),2)
by={n:s for n,_,s in items};g3by={n:s for n,_,s in g3}
pairs=[('Guide_shroud_R52','Roller_rubber_-42_99.9'),('Guide_plate_R52','Guide_shroud_R52'),('Guide_shroud_R52','Analog_shield'),('Guide_plate_R52','PMT'),
       ('Analog_shield','Film_sensor_-25_-110_102'),('Analog_shield','Film_sensor_25_-110_102'),('Analog_shield','Labyrinth-132'),('Analog_shield','SP2_envelope'),('PMT线性TIA前端卡','Film_sensor_-25_-110_102'),('PMT线性TIA前端卡','Film_sensor_25_-110_102'),('AFE_post_-24_97','Film_sensor_-25_-110_102'),
       ('Guide_shroud_R52','Cavity_shell'),('Guide_shroud_R52','Saddle_48'),('PMT','Roller_rubber_-42_99.9')]
clear=[dict(a=a,b=b,min_distance_mm=dist(by[a],by[b])) for a,b in pairs if a in by and b in by]
for n in ('LOWER_COVER_-42','LOWER_CORE_-42'):
    if n in g3by:clear.append(dict(a='Guide_shroud_R52',b='G3:'+n,min_distance_mm=dist(by['Guide_shroud_R52'],g3by[n])))
near=sorted(((dist(by['Guide_shroud_R52'],s),n) for n,_,s in g3))[:3]
res=dict(variant=variant,scope='rigid nominal B-rep intersections of the R5-PDR1 core with the R5.2 collector change; no tolerances, cables, fasteners; boards and purchased items are envelopes',
    core_instances=len(items),core_overlaps=core,g3_parts_checked=len(g3),overlaps_vs_g3=vs_g3,clearances=clear,g3_nearest_to_shroud=[dict(name=n,min_distance_mm=d) for d,n in near])
(R/'tests'/f'cad_overlap_R52_{variant}.json').write_text(json.dumps(res,ensure_ascii=False,indent=2))
if variant=='B':
    (R/'cad/instances_R52_delta.json').write_text(json.dumps(delta,ensure_ascii=False,indent=2))
    a=cq.Assembly(name='ZL80_R52_core_review')
    for k,(n,p,s) in enumerate(items):a.add(s,name=f'{k:03d}_{p}_{n[:32]}')
    a.save(str(R/'cad/step/ZL80_R52_core_review.step'))
print(json.dumps(res,ensure_ascii=False,indent=1))
