"""ADF50 V0.4 nominal envelope solids in the R5 global frame and a rigid interference check against every R5-PDR1
instance, with the R5.2 layout-B shift applied to the PMT group (conservative: shield kept un-notched).
Excluded R5 items: A01 (external ADF placeholder), A02 x2 (manual trays), front labyrinth H08 (replaced by the entry
roller pair), C06/C07 (removed in R5.2). The rear labyrinth H08 stays and IS checked. Panels are not excluded; the
solids stop at the panel faces and the required front cut-out is listed. Envelopes only. Needs cadquery."""
import json,math,sys
from pathlib import Path
import cadquery as cq
ROOT=Path(__file__).resolve().parents[1];R5=ROOT.parent
sys.path.insert(0,str(ROOT/'engineering'));import calculate as C
p=json.loads((ROOT/'engineering/parameters.json').read_text());g=json.loads((R5/'engineering/parameters.json').read_text())['collector_guide_r52']
G=C.geometry(p);zf=p['scan_plane_z_mm'];yf=p['scanner_front_panel_y_mm'];yr=p['scanner_rear_panel_y_mm'];R=G['R']
def box(x0,x1,y0,y1,z0,z1):return cq.Workplane('XY').box(x1-x0,y1-y0,z1-z0).val().translate(cq.Vector((x0+x1)/2,(y0+y1)/2,(z0+z1)/2))
def prism(pts,halfw):return cq.Workplane('YZ').workplane(offset=-halfw).polyline(pts).close().extrude(2*halfw).val()
def arc(c,r,a0,a1,n=12):return [(c[0]+r*math.sin(a0+(a1-a0)*i/n),c[1]-r*math.cos(a0+(a1-a0)*i/n)) for i in range(n+1)]
off=lambda pt,nrm,d:(pt[0]+d*nrm[0],pt[1]+d*nrm[1])
nt=G['n_tray'];hb,hl=p['magazine_housing_below_path_mm'],p['magazine_lid_above_path_mm'];hw=p['magazine_width_mm']/2
ce=(G['entry_bend_end'][0],zf+R)                                   # entry bend centre; path point at angle t: c+(−R sin t, −R cos t)
a=G['a'];chute_out=[(ce[0]-(R+18)*math.sin(t),ce[1]-(R+18)*math.cos(t)) for t in [a*i/12 for i in range(13)]]
chute_in=[(ce[0]-(R-14)*math.sin(t),ce[1]-(R-14)*math.cos(t)) for t in [a*i/12 for i in range(12,-1,-1)]]
r=p['entry_roller_od_mm']/2;ey=p['entry_nip_y_mm']
bw=p['output_bin_width_mm']/2;b=G['b'];cx=(G['exit_bend_start'][0],zf+R);n2=G['n_bin']
ramp_out=[(cx[0]+(R+18)*math.sin(t),cx[1]-(R+18)*math.cos(t)) for t in [b*i/12 for i in range(13)]]
ramp_in=[(cx[0]+(R-14)*math.sin(t),cx[1]-(R-14)*math.cos(t)) for t in [b*i/12 for i in range(12,-1,-1)]]
solids={
 'IN_entry_roller_upper':box(-70,70,yf+2.5,ey+r+1,zf+.6,zf+40),
 'IN_entry_roller_lower':box(-70,70,yf+2.5,ey+r+1,zf-30,zf-.6),
 'MAG_slide_bend':prism(chute_out+chute_in,hw),
 'MAG_head_and_magazine':prism([off(G['entry_bend_start'],nt,hb),off(G['mag_top'],nt,hb),off(G['mag_top'],nt,-hl),off(G['entry_bend_start'],nt,-hl)],hw),
 'OUT_ramp_bend':prism(ramp_out+ramp_in,bw),
 'OUT_standing_bin':prism([off(G['exit_bend_end'],n2,p['output_bin_depth_mm']),off(G['bin_top'],n2,p['output_bin_depth_mm']),off(G['bin_top'],n2,-p['output_bin_front_cover_mm']),off(G['exit_bend_end'],n2,-p['output_bin_front_cover_mm'])],bw)}
asm=cq.Assembly(name='ADF50_V04_envelope')
for k,s in solids.items():asm.add(s,name=k)
path=[G['mag_top'],G['entry_bend_start']]+[(ce[0]-R*math.sin(t),ce[1]-R*math.cos(t)) for t in [a*(1-i/12) for i in range(1,13)]]+[G['exit_bend_start']]+[(cx[0]+R*math.sin(t),cx[1]-R*math.cos(t)) for t in [b*i/12 for i in range(1,13)]]+[G['bin_top']]
asm.add(cq.Workplane('YZ').workplane(offset=-40).polyline(path).offset2D(0.15).extrude(80).val(),name='REF_film_path')
asm.add(cq.Workplane('XY').box(320,300,300).translate((0,0,150)).val(),name='REF_scanner_enclosure_320x300x300')
asm.save(str(ROOT/'cad/ADF50_V04_envelope.step'))
inst=json.loads((R5/'cad/instances.json').read_text());hits=[];checked=0;cache={};near=[]
MOVE={'C08','P03','P04','B01','H01'};SKIP={'A01','A02','C06','C07'};dy=g['pmt_shift_y_vs_r5']
for row in inst:
    if row['part'] in SKIP or row['name']=='Labyrinth-132':continue
    moved=row['part'] in MOVE or row['name'].startswith('AFE_post') or row['name']=='Temp_PMT'
    bb=list(row['aabb'])
    if moved:bb[1]+=dy;bb[4]+=dy
    for k,s in solids.items():
        q=s.BoundingBox();q=[q.xmin,q.ymin,q.zmin,q.xmax,q.ymax,q.zmax]
        gap=max(max(bb[i],q[i])-min(bb[i+3],q[i+3]) for i in range(3))
        if 0<gap<6:near.append(dict(adf=k,r5=row['name'],aabb_gap_mm=round(gap,2)))
        if gap>=-1e-5:continue
        if row['part'] not in cache:cache[row['part']]=cq.importers.importStep(str(R5/'cad/step'/f"{row['part']}.step")).val()
        sh=cache[row['part']]
        if row['rotation']:ax,ang=row['rotation'];sh=sh.rotate((0,0,0),tuple(ax),ang)
        sh=sh.translate(cq.Vector(*row['position']))
        if moved:sh=sh.translate(cq.Vector(0,dy,0))
        checked+=1;v=sh.intersect(s).Volume()
        if v>.01:hits.append(dict(adf=k,r5=row['name'],r5_part=row['part'],volume_mm3=round(v,2)))
ab=lambda s:[round(x,1) for x in (s.BoundingBox().xmin,s.BoundingBox().ymin,s.BoundingBox().zmin,s.BoundingBox().xmax,s.BoundingBox().ymax,s.BoundingBox().zmax)]
allbb=[ab(s) for s in solids.values()]
res=dict(scope='ADF50 V0.4 nominal envelope solids vs R5-PDR1 instances with the R5.2 layout-B PMT-group shift (shield un-notched, conservative). Excluded as replaced/removed: A01, A02 x2, front labyrinth H08, C06, C07. Rigid, nominal, no tolerances; ADF solids are space envelopes, not parts.',
    r5_instances=len(inst),pairs_intersected=checked,overlaps=hits,tight_aabb_gaps_under_6mm=sorted(near,key=lambda x:x['aabb_gap_mm']),
    panel_cutouts_required=dict(front_H02=dict(x=[-70,70],z=[zf-30,zf+40],note='entry roller pair passes through; replaces the film slot and front labyrinth H08'),rear_H02R='none; existing slot and labyrinth kept'),
    overall_aabb_of_adf_solids=[min(b[0] for b in allbb),min(b[1] for b in allbb),min(b[2] for b in allbb),max(b[3] for b in allbb),max(b[4] for b in allbb),max(b[5] for b in allbb)],
    envelopes_aabb=dict(zip(solids,allbb)))
(ROOT/'tests/envelope_interference.json').write_text(json.dumps(res,ensure_ascii=False,indent=2))
print(json.dumps({k:res[k] for k in ('pairs_intersected','overlaps','tight_aabb_gaps_under_6mm','overall_aabb_of_adf_solids')},ensure_ascii=False,indent=1))
