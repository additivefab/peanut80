"""ADF50 V0.3 nominal envelope solids in the R5 global frame and a rigid interference check against every R5-PDR1
instance, with the R5.2 layout-B shift applied to the PMT group (conservative: shield kept un-notched).
Excluded R5 items: A01 (external ADF placeholder), A02 x2 (manual trays), H08 x2 (slot labyrinths) - all replaced
by this design. Front/rear panels are NOT excluded; the solids stop at the panel faces and the required panel
cut-outs are listed in the result. Envelopes only, not mechanism CAD. Needs cadquery."""
import json,math,sys
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[1];R5=ROOT.parent
p=json.loads((ROOT/'engineering/parameters.json').read_text());g=json.loads((R5/'engineering/parameters.json').read_text())['collector_guide_r52']
zf=p['scan_plane_z_mm'];yf=p['scanner_front_panel_y_mm'];yr=p['scanner_rear_panel_y_mm']
def box(x0,x1,y0,y1,z0,z1):return cq.Workplane('XY').box(x1-x0,y1-y0,z1-z0).val().translate(cq.Vector((x0+x1)/2,(y0+y1)/2,(z0+z1)/2))
def cyl(x,y,z0,z1,d):return cq.Workplane('XY').circle(d/2).extrude(z1-z0).val().translate(cq.Vector(x,y,z0))
fy,ey,sy,sx,sd=p['feed_nip_y_mm'],p['eject_nip_y_mm'],p['double_sheet_sensor_y_mm'],p['double_sheet_sensor_x_mm'],p['double_sheet_sensor_diameter_mm']
r=p['feed_roller_od_mm']/2;rear=p['dam_top_y_mm']-p['lift_plate_length_mm']-p['magazine_rear_allowance_mm'];hw=p['magazine_width_mm']/2
t=math.radians(p['output_tray_tilt_deg']);y0=yr+p['output_tray_gap_from_panel_mm'];L=p['output_tray_size_mm'][1]
inside={
 'IN_feed_roller_upper':box(-70,70,yf+2.5,fy+r+1,zf+.6,zf+40),
 'IN_retard_roller_lower':box(-70,70,yf+2.5,fy+r+1,zf-30,zf-.6),
 'IN_double_sensor_tx':cyl(sx,sy,zf+3,zf+25,sd),'IN_double_sensor_rx':cyl(sx,sy,zf-24,zf-3,sd),
 'OUT_eject_roller_upper':box(-70,70,ey-r-1,yr-2.5,zf+.6,zf+40),
 'OUT_eject_roller_lower':box(-70,70,ey-r-1,yr-2.5,zf-30,zf-.6)}
outside={
 'MAG_tray_lift_dam':box(-hw,hw,rear,yf-.5,zf-40,zf-.6),
 'MAG_pick_arm':box(-30,30,p['dam_top_y_mm']-p['pick_to_dam_free_length_mm']-15,yf-.5,zf+.6,zf+40),
 'MAG_lid':box(-hw-4,hw+4,rear-4,yf-.5,zf+41,p['magazine_lid_top_z_mm']),
 'OUT_tray':cq.Workplane('YZ').workplane(offset=-58).polyline([(y0,zf-6),(y0+L*math.cos(t),zf-6-L*math.sin(t)),(y0+L*math.cos(t),zf-6-L*math.sin(t)-p['output_tray_size_mm'][2]),(y0,zf-6-p['output_tray_size_mm'][2])]).close().extrude(116).val(),
 'OUT_hood':box(-62,62,yr+.5,y0+L*math.cos(t)+4,zf+41,zf+45)}
solids={**inside,**outside}
asm=cq.Assembly(name='ADF50_V03_envelope')
for k,s in solids.items():asm.add(s,name=k)
asm.add(box(-40,40,rear+12,y0+L*math.cos(t),zf-.1,zf+.1),name='REF_film_plane_Z110')
asm.add(cq.Workplane('XY').box(320,300,300).translate((0,0,150)).val(),name='REF_scanner_enclosure_320x300x300')
asm.save(str(ROOT/'cad/ADF50_V03_envelope.step'))
inst=json.loads((R5/'cad/instances.json').read_text());hits=[];checked=0;cache={};near=[]
MOVE={'C08','P03','P04','B01','H01'};SKIP={'A01','A02','H08','C06','C07'};dy=g['pmt_shift_y_vs_r5']
for row in inst:
    if row['part'] in SKIP:continue
    moved=row['part'] in MOVE or row['name'].startswith('AFE_post') or row['name']=='Temp_PMT'
    bb=list(row['aabb'])
    if moved:bb[1]+=dy;bb[4]+=dy
    for k,s in solids.items():
        b=s.BoundingBox();q=[b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax]
        gap=max(max(bb[i],q[i])-min(bb[i+3],q[i+3]) for i in range(3))
        if k in inside and 0<gap<6:near.append(dict(adf=k,r5=row['name'],aabb_gap_mm=round(gap,2)))
        if gap>=-1e-5:continue
        if row['part'] not in cache:cache[row['part']]=cq.importers.importStep(str(R5/'cad/step'/f"{row['part']}.step")).val()
        sh=cache[row['part']]
        if row['rotation']:ax,ang=row['rotation'];sh=sh.rotate((0,0,0),tuple(ax),ang)
        sh=sh.translate(cq.Vector(*row['position']))
        if moved:sh=sh.translate(cq.Vector(0,dy,0))
        checked+=1;v=sh.intersect(s).Volume()
        if v>.01:hits.append(dict(adf=k,r5=row['name'],r5_part=row['part'],volume_mm3=round(v,2)))
ab=lambda s:[round(x,1) for x in (s.BoundingBox().xmin,s.BoundingBox().ymin,s.BoundingBox().zmin,s.BoundingBox().xmax,s.BoundingBox().ymax,s.BoundingBox().zmax)]
res=dict(scope='ADF50 V0.3 nominal envelope solids vs R5-PDR1 instances with the R5.2 layout-B PMT-group shift (shield un-notched, conservative). Excluded as replaced: A01, A02 x2, H08 x2, C06, C07. Rigid, nominal, no tolerances; ADF solids are space envelopes, not parts.',
    r5_instances=len(inst),pairs_intersected=checked,overlaps=hits,tight_aabb_gaps_under_6mm=sorted(near,key=lambda x:x['aabb_gap_mm']),
    panel_cutouts_required=dict(front_H02=dict(x=[-70,70],z=[zf-30,zf+40],note='feed/retard roller module passes through; replaces the film slot and labyrinth H08'),
        rear_H02R=dict(x=[-70,70],z=[zf-30,zf+40],note='eject roller module; replaces the film slot and labyrinth H08')),
    envelopes_aabb={k:ab(s) for k,s in solids.items()})
(ROOT/'tests/envelope_interference.json').write_text(json.dumps(res,ensure_ascii=False,indent=2));print(json.dumps({k:res[k] for k in ('pairs_intersected','overlaps','tight_aabb_gaps_under_6mm')},ensure_ascii=False,indent=1))
