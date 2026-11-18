"""ECR-G3-01 channel E: B05 input channel, FFC link and round-cable harness W13.
Writes parts (STEP), interference, route checks, electrical numbers and CSV tables. Needs cadquery.
Everything is nominal geometry in the R5 global frame; harness and connector parts are placeholders for purchased items."""
import json,math,sys,csv
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import geom_e as g
import cadquery as cq
E=g.E;EL=E/'electrical';V=g.V;G3=g.R5/'ZL80_R52_G3_20261116'
(EL/'step').mkdir(exist_ok=True)
def box(x0,x1,y0,y1,z0,z1):return cq.Workplane('XY').box(x1-x0,y1-y0,z1-z0).val().translate(cq.Vector((x0+x1)/2,(y0+y1)/2,(z0+z1)/2))
YC=39.0;WSTR=4.5;TSTR=0.3             # FFC 6P 0.5 mm: width, thickness
# sensor-side FFC connector (on the +x face of the sensor board G3E-03) and the fixed end (adaptor board on a stand on the motor bracket top)
CONN=box(91.8,93.4,YC-2.75,YC+2.75,121.3,123.9);ZS=122.6;XS=93.4
STAND=box(116.6,131.0,31,47,124.0,125.5).fuse(box(120.1,121.7,34,44,125.5,131.5)).clean()
ADAPT=box(118.5,120.1,34.5,43.5,125.8,131.0).fuse(box(117.0,118.5,YC-2.75,YC+2.75,126.5,129.1)).clean()
XF=117.0;ZF=127.8;STRIP_LEN=27.0
def arc_points(p,q,s,n=24):
    """Circular arc between p and q (x,z) of length s, bowing towards +z."""
    d=math.dist(p,q);lo,hi=1e-6,2*math.pi-1e-6
    f=lambda th:math.sin(th/2)/(th/2)-d/s
    for _ in range(80):
        mid=(lo+hi)/2
        if f(mid)>0:lo=mid
        else:hi=mid
    th=(lo+hi)/2;R=s/th;mx,mz=(p[0]+q[0])/2,(p[1]+q[1])/2;ux,uz=(q[0]-p[0])/d,(q[1]-p[1])/d;nx,nz=-uz,ux   # n points to +z for p->q along +x
    if nz<0:nx,nz=-nx,-nz
    hc=R*math.cos(th/2);cx,cz=mx-nx*hc,mz-nz*hc;a0=math.atan2(p[1]-cz,p[0]-cx);a1=math.atan2(q[1]-cz,q[0]-cx)
    # go the short way through the +z side
    pts=[]
    for i in range(n+1):
        a=a0+(a1-a0)*i/n if abs(a1-a0)<math.pi else a0+((a1-a0)-math.copysign(2*math.pi,a1-a0))*i/n
        pts.append((cx+R*math.cos(a),cz+R*math.sin(a)))
    return pts,R,R*(1-math.cos(th/2))
def strip_solid(dz):
    pts,R,h=arc_points((XS,ZS+dz),(XF,ZF),STRIP_LEN)
    up=[];lo=[]
    for i,(x,z) in enumerate(pts):
        a=pts[max(i-1,0)];b=pts[min(i+1,len(pts)-1)];tx,tz=b[0]-a[0],b[1]-a[1];tl=math.hypot(tx,tz);nx,nz=-tz/tl,tx/tl
        up.append((x+nx*TSTR/2,z+nz*TSTR/2));lo.append((x-nx*TSTR/2,z-nz*TSTR/2))
    poly=up+lo[::-1]
    wp=cq.Workplane('XZ',origin=(0,YC+WSTR/2,0)).polyline(poly).close().extrude(WSTR)   # XZ normal is -y: extrudes from y=YC+w/2 down to YC-w/2
    return wp.val(),R,h
# ------------------------------------------------------------- interference against G3 integrated context at three roller heights
inst=json.loads((G3/'cad/instances.json').read_text());cache={}
REPLACED={'CAP_SCREW_72_42_120.1_-7_7','CAP_SCREW_72_42_120.1_7_7'}
def load(pid):
    if pid not in cache:cache[pid]=cq.importers.importStep(str(G3/'cad/parts'/f'{pid}.step')).val()
    return cache[pid]
def placed(row,dz):
    sh=load(row['part'])
    if row.get('rotation'):ax,ang=row['rotation'];sh=sh.rotate(cq.Vector(0,0,0),cq.Vector(*ax),ang)
    sh=sh.translate(cq.Vector(*row['position']))
    return sh.translate(cq.Vector(0,0,dz)) if row.get('moves_with_upper') else sh
def aabb(s):
    b=s.BoundingBox();return [b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax]
def abgap(a,b):return math.hypot(*[max(a[k]-b[k+3],b[k]-a[k+3],0) for k in range(3)])
ecr_moving={'conn':CONN}
# ECR parts from the approved package (rebuilt as boxes/cylinders only for a nearest-neighbour check against the new items)
ECRP={k:cq.importers.importStep(str(E/'step'/f'{k}.step')).val() for k in ('G3E-01','G3E-02','G3E-03','G3E-04')}
res={};tight={}
for dz in (0.0,5.0,-1.0):
    strip,R,h=strip_solid(dz);sh_move={'G3E-08_connector':CONN.translate(cq.Vector(0,0,dz)),'G3E-07_FFC':strip}
    fixed={'G3E-05_stand':STAND,'G3E-06_adaptor':ADAPT}
    allp={**sh_move,**fixed};hits=[];near=[]
    for row in inst:
        if row['name'] in REPLACED:continue
        bb=list(row['aabb'])
        if row.get('moves_with_upper'):bb[2]+=dz;bb[5]+=dz
        sh=None
        for k,s in allp.items():
            if abgap(bb,aabb(s))>6:continue
            if sh is None:sh=placed(row,dz)
            d=sh.distance(s)
            if d<=1e-6:
                v=sh.intersect(s).Volume()
                if v>0.01:hits.append(dict(item=k,g3=row['name'],volume_mm3=round(v,3)))
                else:near.append((0.0,k,row['name']))
            elif d<6:near.append((round(d,2),k,row['name']))
    for k,s in sh_move.items():
        for pk,ps in ECRP.items():
            if k=='G3E-08_connector' and pk=='G3E-03':continue    # the connector is soldered to that board
            ps2=ps.translate(cq.Vector(0,0,dz))
            d=ps2.distance(s)
            if d<=1e-6 and ps2.intersect(s).Volume()>0.01:hits.append(dict(item=k,g3=pk,volume_mm3=round(ps2.intersect(s).Volume(),3)))
            elif d<3:near.append((round(d,2),k,pk))
    res[f'dz_{dz:+g}']=dict(overlaps=hits,strip_radius_mm=round(R,1),strip_arch_height_mm=round(h,1))
    for d,k,n in near:
        key=f'{k}|{n}';tight[key]=min(tight.get(key,9e9),d)
envelope_min=sorted((v,k) for k,v in tight.items())[:10]
# ------------------------------------------------------------- parts
P={'G3E-05':('FFC 固定端支架（5052-H32，L 形，贴在 G3-M12 电机支架顶面）',STAND,'5052-H32',2.68),
   'G3E-06':('转接小板 9×8.5×1.6（FFC 连接器 + 5 路焊盘）',ADAPT,'FR4+外购',1.9),
   'G3E-08':('传感器端 FFC 连接器 6P 0.5 mm（竖直进线，焊在 G3E-03 +x 面）',CONN,'外购',1.2)}
strip0,_,_=strip_solid(0.0);P['G3E-07']=('FFC 6P 0.5 mm 0.3 mm 厚 4.5 mm 宽，长 27 mm 预成形上拱',strip0,'PI/Cu',1.4)
asm=cq.Assembly(name='ECR_G3_01_E_link')
mass={}
for k,(n,s,m,rho) in P.items():
    asm.add(s,name=k);cq.exporters.export(cq.Workplane('XY').add(s),str(EL/'step'/f'{k}.step'));mass[k]=round(s.Volume()*rho/1000,2)
mass['G3E-08']=0.15       # assumed: solid block would overstate a small plastic connector
mass['G3E-06']=1.0        # assumed (board + connector), fixed side so it does not load the roller
mass['G3E-07']=round(strip0.Volume()*1.4/1000,3)
asm.save(str(EL/'step'/'ECR_G3_01_E_link.step'))
# moving mass added by the link: the sensor-side connector and half of the strip (the other half rests on the fixed end)
moving_add=round(mass['G3E-08']+mass['G3E-07']/2,2)
# ------------------------------------------------------------- electrical numbers
um=3.834951969714103       # um per count (G3 / G5: pi*20/(4096*4))
speeds={'0.234 mm/s（G3 最低标称）':0.234,'15 mm/s（扫描）':15.0,'50 mm/s（进出片）':50.0}
Rs=470.0;Cf=470e-12;Rpd=47e3;Cc=0.4*100e-12;Rsrc=100.0
tau=(Rs+Rsrc)*(Cf+Cc);t50=math.log(2)*tau
timing={}
for n,v in speeds.items():
    cps=v*1000/um;state_us=1e6/cps
    timing[n]=dict(counts_per_s=round(cps,1),state_time_us=round(state_us,2),filter_delay_us=round(t50*1e6,3),filter_over_state_pct=round(t50*1e6/state_us*100,3),
                   position_offset_um=round(v*t50*1000,4),fpga_clocks_per_state=round(state_us*100,0))
v5=5.0*Rpd/(Rpd+Rs);i_pd=5.0/(Rpd+Rs)
AWG30=0.339;ffc_r=1.72e-8/(0.3e-3*35e-6)    # ohm/m (35 um Cu, 0.3 mm trace assumed)
Lcab,rep=g.length_with_fillets(g.W13,15.0);Lcab=round(Lcab,1)
I5=0.030
drop=2*(AWG30*Lcab/1000+ffc_r*0.027)*I5
# routes
P_=g.fillet_points(g.W13,15.0);rr=g.W13_D/2
others={k:round(g.poly_poly_dist(P_,[tuple(p) for p in v['points']])[0]-rr-v['diameter']/2,1) for k,v in g.ROUTES.items()}
ctx=[]
for ins in g.INST:
    m=min(g.seg_box_gap(P_[i],P_[i+1],ins['aabb'],14) for i in range(len(P_)-1))-rr
    if m<10:ctx.append((round(m,1),ins['name']))
ctx.sort()
b05=[(n,round(min(g.seg_box_gap(P_[i],P_[i+1],b,20) for i in range(len(P_)-1))-rr,1)) for n,b in g.b05_boxes()]
bc=g.board_check()
# FFC stiffness (guided-end beam, E assumed) and force at the film-thickness excursion
Eff=5000.0;w=WSTR;t=TSTR;I=w*t**3/12;L=24.0
k_ffc=12*Eff*I/L**3*1.0;F5=k_ffc*5.0;F035=k_ffc*0.35
out=dict(date='2026-11-17',status='设计完成；硬件未制造；无实测',
 b05_layout=bc,u3=dict(part='SN74LVC3G17（3 路施密特缓冲，与 U2 同型号，手册指标待核对）',vcc='3V3',gates=['ENC_E_A','ENC_E_B','ENC_E_OPEN']),
 input_network=dict(Rs_ohm=Rs,C_pF=Cf*1e12,Rpd_ohm=Rpd,source_ohm_assumed=Rsrc,cable_C_pF_assumed=round(Cc*1e12,1),tau_us=round(tau*1e6,3),node_high_V=round(v5,3),sensor_load_mA=round(i_pd*1000,3)),
 timing=timing,
 supply=dict(sensor_current_mA_assumed=I5*1000,awg30_ohm_per_m=AWG30,ffc_ohm_per_m=round(ffc_r,2),drop_mV=round(drop*1000,1),min_5v_at_sensor_V=round(5-drop,3)),
 w13=dict(centreline=[list(p) for p in g.W13],length_filleted_mm=Lcab,cut_length_mm=round(Lcab+2*20+30,0),fillet=rep,min_bend_mm=g.W13_MINBEND,od_mm=g.W13_D,
          gap_to_other_harness_mm=others,gap_to_context_mm=ctx[:8],gap_to_b05_mm=b05),
 ffc=dict(pitch_mm=0.5,pins=6,width_mm=WSTR,thickness_mm=TSTR,length_mm=STRIP_LEN,chord_mm=round(math.dist((XS,ZS),(XF,ZF)),1),
          by_height={k:dict(radius_mm=v['strip_radius_mm'],arch_height_mm=v['strip_arch_height_mm']) for k,v in res.items()},
          stiffness_N_per_mm=round(k_ffc,4),force_at_5mm_N=round(F5,3),force_at_0p35mm_N=round(F035,4),preload_N=6.06,force_at_0p35mm_pct_of_preload=round(F035/6.06*100,2),E_assumed_MPa=Eff),
 interference=res,nearest_mm=[dict(gap=a,pair=b) for a,b in envelope_min],mass_g=mass,moving_mass_added_g=moving_add,
 moving_mass_total_g=round(4.44+moving_add,2))
(EL/'ECR_G3_01_E_计算.json').write_text(json.dumps(out,ensure_ascii=False,indent=1))
(EL/'interference.json').write_text(json.dumps(dict(method='cadquery rigid nominal B-rep, volume>0.01 mm3, against 238 G3 integrated instances plus the four approved ECR parts; strip rebuilt per roller height',
    replaced_g3_screws=sorted(REPLACED),interference=res,nearest=out['nearest_mm']),ensure_ascii=False,indent=1))
print(json.dumps({k:out[k] for k in ('b05_layout',) if False},ensure_ascii=False))
print('overlaps',{k:v['overlaps'] for k,v in res.items()});print('nearest',envelope_min[:6]);print('strip',{k:(v['strip_radius_mm'],v['strip_arch_height_mm']) for k,v in res.items()})
print('cable len',Lcab,'drop mV',round(drop*1000,1),'mass',mass,moving_add);print('others',others);print('ctx',ctx[:6]);print('F',round(F5,3),round(F035,4))
