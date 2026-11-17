"""ADF50 V0.2 nominal envelope solids in the R5 global frame and a rigid interference check against every
R5-PDR1 instance (core + enclosure + feet). The R5 placeholder A01 (old external ADF box) and the two manual
trays A02 are excluded because this module replaces them. Envelopes only, not mechanism CAD. Needs cadquery."""
import json,math,sys
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[1];R5=ROOT.parent
sys.path.insert(0,str(ROOT/'engineering'));import calculate as C
p=json.loads((ROOT/'engineering/parameters.json').read_text());r=C.calculate(p);pa=r['path']
a=math.radians(p['magazine_angle_deg_from_horizontal']);u=(math.cos(a),math.sin(a));nrm=(u[1],-u[0])
hw=p['adf_module_width_mm']/2;zf=p['scan_plane_z_mm'];Rr=p['guided_turn_radius_mm'];yh=p['horizontal_run_start_y_mm']
def prism(pts,halfw=hw):   # polygon in (Y,Z) extruded along X
    return cq.Workplane('YZ').workplane(offset=-halfw).polyline(pts).close().extrude(2*halfw).val()
ae=pa['arc_end_yz'];dam=pa['dam_yz'];top=pa['magazine_top_yz'];ret=pa['retard_nip_yz']
off=lambda pt,d:(pt[0]+d*nrm[0],pt[1]+d*nrm[1])
depth=p['magazine_stack_depth_budget_mm']+p['magazine_tray_thickness_mm']
solids={
 'ADF_turn_housing':prism([(yh-Rr-20,zf-30),(p['scanner_front_panel_y_mm']-2,zf-30),(p['scanner_front_panel_y_mm']-2,zf+25),(yh+10,zf+25),off(ae,30),off(ae,-25),(yh-Rr-20,ae[1]-10)]),
 'ADF_separation_head':prism([off(ae,30),off(ret,30),off(dam,depth),off(dam,-45),off(ae,-25)]),
 'ADF_magazine':prism([off(dam,depth),off(top,depth),off(top,-45),off(dam,-45)]),
 'ADF_dock_guide':prism([(p['scanner_front_panel_y_mm']-2,zf-6),(p['scanner_front_panel_y_mm']-2,zf+6),(yh+10,zf+6),(yh+10,zf-6)],45),
}
t=math.radians(p['output_tray_tilt_deg']);y0=p['scanner_rear_panel_y_mm']+10;L=p['output_tray_size_mm'][1];w=p['output_tray_size_mm'][0]/2+8
solids['ADF_output_tray']=prism([(y0,zf-4),(y0+L*math.cos(t),zf-4-L*math.sin(t)),(y0+L*math.cos(t),zf-4-L*math.sin(t)-p['output_tray_size_mm'][2]),(y0,zf-4-p['output_tray_size_mm'][2])],w)
asm=cq.Assembly(name='ADF50_V02_envelope')
for k,s in solids.items():asm.add(s,name=k)
film=prism([(p['parked_leading_edge_y_mm'],zf-.1),(yh,zf-.1),(yh,zf+.1),(p['parked_leading_edge_y_mm'],zf+.1)],40);asm.add(film,name='REF_film_path_horizontal')
asm.add(cq.Workplane('XY').box(320,300,300).translate((0,0,150)).val(),name='REF_scanner_enclosure_320x300x300')
asm.save(str(ROOT/'cad/ADF50_V02_envelope.step'))
inst=json.loads((R5/'cad/instances.json').read_text());hits=[];checked=0;cache={}
for row in inst:
    if row['part'] in ('A01','A02'):continue
    bb=row['aabb']
    for k,s in solids.items():
        b=s.BoundingBox();q=[b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax]
        if min(min(bb[i+3],q[i+3])-max(bb[i],q[i]) for i in range(3))<=1e-5:continue
        if row['part'] not in cache:cache[row['part']]=cq.importers.importStep(str(R5/'cad/step'/f"{row['part']}.step")).val()
        sh=cache[row['part']]
        if row['rotation']:ax,ang=row['rotation'];sh=sh.rotate((0,0,0),tuple(ax),ang)
        sh=sh.translate(cq.Vector(*row['position']));checked+=1
        v=sh.intersect(s).Volume()
        if v>.01:hits.append(dict(adf=k,r5=row['name'],r5_part=row['part'],volume_mm3=round(v,2)))
env={k:[round(x,1) for x in (s.BoundingBox().xmin,s.BoundingBox().ymin,s.BoundingBox().zmin,s.BoundingBox().xmax,s.BoundingBox().ymax,s.BoundingBox().zmax)] for k,s in solids.items()}
res=dict(scope='ADF50 V0.2 nominal envelope solids vs all R5-PDR1 instances except A01/A02 (replaced). Rigid, nominal, no tolerances; ADF solids are space envelopes, not parts.',
    r5_instances=len(inst),pairs_intersected=checked,overlaps=hits,envelopes_aabb=env)
(ROOT/'tests/envelope_interference.json').write_text(json.dumps(res,ensure_ascii=False,indent=2));print(json.dumps(res,ensure_ascii=False,indent=1))
