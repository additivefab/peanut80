"""ADF50 V0.6 part-level mechanical design (nominal geometry) built from engineering/parameters.json.
Three sub-assemblies: MAG = magazine + separation head + slide bend (in front of the scanner),
ENT = entry roller unit inside the front panel, BIN = ramp bend + eject unit + standing output bin (behind).
Outputs: one STEP per part (local frame), assembly STEP, parts/instances JSON, BOM CSV, side-plate DXF,
self-interference and scanner-interference reports. Nominal, no tolerances, no fasteners modelled. Needs cadquery, ezdxf."""
import json,math,sys,csv
from pathlib import Path
import cadquery as cq, ezdxf
M=Path(__file__).resolve().parents[1];V=M.parent;R5=V.parent
sys.path.insert(0,str(V/'engineering'));import calculate as C
p=json.loads((V/'engineering/parameters.json').read_text());G=C.geometry(p);FRONT=C.calculate(p)['envelope']['front_y_mm']
A=p['magazine_angle_deg_from_horizontal'];B=p['output_bin_angle_deg_from_horizontal'];a,b=math.radians(A),math.radians(B)
R=G['R'];zf=p['scan_plane_z_mm'];bs=G['entry_bend_start'];xe=G['exit_bend_end'];ce=(G['entry_bend_end'][0],zf+R);cx=(G['exit_bend_start'][0],zf+R)
ST=p['slope_station_from_bend_start_mm'];T_SENS,T_FEED,T_DAM,T_PICK=-ST['double_sheet_sensor'],-ST['feed_retard_nip'],-ST['dam_top'],-ST['pick_contact']
PF=G['entry_bend_end'][0]-1;NI=p['idler_count_per_bend'];IOD=p['idler_od_mm'];IR=R+IOD/2+0.15;GAP=p['inner_guide_gap_mm'];LA=p['lift_arm_length_mm'];CART=p['cartridge'];T_TOP=-G['s_top'];DAMH=p['dam_height_mm'];TRAVEL=max(float(k) for k in p['pick_arm_force_recipes_n'])*p['batch_size']+p['plate_margin_mm']
# ---------- primitives (a,b are the two in-plane coordinates: Y,Z globally or t,n in a local frame)
def box(x0,x1,a0,a1,b0,b1):return cq.Workplane('XY').box(x1-x0,a1-a0,b1-b0).val().translate(cq.Vector((x0+x1)/2,(a0+a1)/2,(b0+b1)/2))
def cylx(x0,x1,ca,cb,d):return cq.Workplane('YZ').workplane(offset=x0).center(ca,cb).circle(d/2).extrude(x1-x0).val()
def tubex(x0,x1,ca,cb,od,idd):return cq.Workplane('YZ').workplane(offset=x0).center(ca,cb).circle(od/2).circle(idd/2).extrude(x1-x0).val()
def prism(pts,x0,x1):return cq.Workplane('YZ').workplane(offset=x0).polyline(pts).close().extrude(x1-x0).val()
def arcpts(c,r,f0,f1,sgn,n=24):return [(c[0]+sgn*r*math.sin(f0+(f1-f0)*i/n),c[1]-r*math.cos(f0+(f1-f0)*i/n)) for i in range(n+1)]
def sector(c,r0,r1,f0,f1,sgn,x0,x1):return prism(arcpts(c,r1,f0,f1,sgn)+arcpts(c,r0,f1,f0,sgn),x0,x1)
def rotx(s,ca,cb,deg):return s.rotate(cq.Vector(0,ca,cb),cq.Vector(1,ca,cb),deg)
# ---------- frames. MAG local (x,t,n): t down-slope from the entry bend start, n toward the lid (free face side).
# BIN local (x,t,n): t up the bin from the exit bend end, n toward the scanner (front of the bin).
FR={'G':lambda s:s,'MAG':lambda s:s.rotate(cq.Vector(0,0,0),cq.Vector(1,0,0),-A).translate(cq.Vector(0,bs[0],bs[1])),
    'BIN':lambda s:s.rotate(cq.Vector(0,0,0),cq.Vector(1,0,0),B).translate(cq.Vector(0,xe[0],xe[1]))}
gm=lambda t,n:(bs[0]+t*math.cos(a)+n*math.sin(a),bs[1]-t*math.sin(a)+n*math.cos(a))
gb=lambda t,n:(xe[0]+t*math.cos(b)-n*math.sin(b),xe[1]+t*math.sin(b)+n*math.cos(b))
RHO={'6061-T6':2.70,'5052-H32':2.68,'SUS304':7.93,'POM':1.41,'EPDM':1.25,'PC':1.20,'45钢':7.85,'PU':1.20,'外购':None}
PARTS={};INST=[]
def add(pid,name,shape,frame,group,mat,proc,note=''):
    if pid not in PARTS:PARTS[pid]=dict(id=pid,name=name,material=mat,process=proc,note=note,frame=frame,shape=shape,qty=0)
    PARTS[pid]['qty']+=1;INST.append(dict(part=pid,name=f"{name}#{PARTS[pid]['qty']}",group=group,frame=frame,shape=FR[frame](shape)))
def mirror(s):return s.mirror('YZ')
# =====================================================================================================
# MAG  - magazine, separation head, slide bend
# =====================================================================================================
front_outline=[gm(T_TOP,-40),gm(T_TOP,34),gm(-110,34),gm(-110,50),gm(8,50),(PF,150),(PF,11),(PF-147,11),gm(-150,-40)]
LIFT_T=(-120,-310);LIFT_N=-(TRAVEL+7.5);PIV_RET=(-8,-30);REL=(-2,24);FEED=(T_FEED,10);PICK=(T_PICK,-DAMH+10)
idl_in=[(ce[0]-IR*math.sin(a*i/(NI+1)),ce[1]-IR*math.cos(a*i/(NI+1))) for i in range(1,NI+1)]
tie_front=[gm(-380,30),gm(-200,30),(PF-12,60),(PF-137,40)]
holes_front=[(gm(*FEED),16),(gm(*REL),6.4),(gm(*PIV_RET),6.4)]+[(gm(t,LIFT_N),6.4) for t in LIFT_T]+[(q,4.2) for q in idl_in]+[(q,4.3) for q in tie_front]
def _inside(pt,poly):
    x,y=pt;c=False
    for i in range(len(poly)):
        x1,y1=poly[i];x2,y2=poly[(i+1)%len(poly)]
        if (y1>y)!=(y2>y) and x<(x2-x1)*(y-y1)/(y2-y1)+x1:c=not c
    return c
def plate(outline,holes,x0,x1):
    bad=[h[0] for h in holes if not _inside(h[0],outline)]
    assert not bad,('hole centre outside plate outline',bad)
    s=prism(outline,x0,x1)
    for (c,d) in holes:s=s.cut(cylx(x0-1,x1+1,c[0],c[1],d))
    return s
add('AF01','片仓侧板（左）',plate(front_outline,holes_front,-49,-46),'G','MAG','5052-H32','激光切割 t3','左右孔位相同')
add('AF02','片仓侧板（右）',plate(front_outline,holes_front,46,49),'G','MAG','5052-H32','激光切割 t3','外侧装送片电机、推片电机、脱开电机')
add('AF03','片仓背板',box(-46,46,-385,-52,-38,-35),'MAG','MAG','5052-H32','激光切割 t3','')
td0=lambda beta:T_DAM-DAMH/math.tan(math.radians(beta))
pp=box(-39,39,-383,-50,-TRAVEL-2,-TRAVEL)
for te in (-100,-330):pp=pp.fuse(box(39,43.5,te-4,te+4,-TRAVEL-2,-TRAVEL)).fuse(box(-43.5,-39,te-4,te+4,-TRAVEL-2,-TRAVEL))
add('AF04','推片板',pp.clean(),'MAG','MAG','SUS304','激光切割 t2','图示为退到底的装片位置；四耳在侧导条槽内导向')
strip=box(41,46,-385,-52,-35,8)
for te in (-100,-330):strip=strip.cut(box(40.9,44,te-4.2,te+4.2,-TRAVEL-3.5,0.5))
for t in LIFT_T:strip=strip.cut(cylx(40,47,t,LIFT_N,6.4))
add('AF05','片仓侧导条',strip,'MAG','MAG','POM','铣削','左右镜像各 1');add('AF05','片仓侧导条',mirror(strip),'MAG','MAG','POM','铣削')
add('AF06','顶升轴',cylx(-60,52,LIFT_T[0],LIFT_N,6),'MAG','MAG','SUS304','车削 φ6×112','前轴右端接推片电机')
add('AF06B','顶升轴（后）',cylx(-60,52,LIFT_T[1],LIFT_N,6),'MAG','MAG','SUS304','车削 φ6×112','')
for t0 in LIFT_T:
    for xc in (-25,25):
        arm=box(xc-2.5,xc+2.5,t0-4,t0+LA+3,LIFT_N-2.5,LIFT_N+2.5).cut(cylx(xc-3,xc+3,t0,LIFT_N,6))
        add('AF07','顶升臂',rotx(arm,t0,LIFT_N,math.degrees(math.asin(3.0/LA))-0.8),'MAG','MAG','SUS304','线切割 t5',f'臂长 {LA:g}；转角 10°–74° 对应行程 {TRAVEL:g}')
    add('AF08','顶升曲柄',box(-55,-51,t0-4,t0+4,LIFT_N-4,LIFT_N+24).cut(cylx(-56,-50,t0,LIFT_N,6)),'MAG','MAG','SUS304','线切割 t4','')
add('AF09','顶升连杆',box(-59,-55,LIFT_T[1]-4,LIFT_T[0]+4,LIFT_N+16,LIFT_N+24),'MAG','MAG','SUS304','激光切割 t4','两曲柄平行四边形同步')
def dam(beta):return prism([(td0(beta),-30),(td0(beta),-DAMH),(T_DAM,0),(-36.5,0),(-36.5,-30)],-40,40)
add('AF10B','斜坝块 55°（0.20 mm 片）',dam(55),'MAG','MAG','POM','铣削','可换件；装配图示此件')
PARTS['AF10A']=dict(id='AF10A',name='斜坝块 62°（0.15 mm 片）',material='POM',process='铣削',note='可换件，不在装配体中',frame='MAG',shape=dam(62),qty=1)
PARTS['AF10C']=dict(id='AF10C',name='斜坝块 38°（0.35 mm 片）',material='POM',process='铣削',note='可换件，不在装配体中',frame='MAG',shape=dam(38),qty=1)
add('AF11','斜坝座',box(-46,46,-52,-36.5,-38,-30),'MAG','MAG','6061-T6','铣削','')
add('AF12','拾取轴',cylx(-36,30,PICK[0],PICK[1],6),'MAG','MAG','SUS304','车削 φ6×66','')
for x0 in (10,-20):add('AF13','拾取胶轮',tubex(x0,x0+10,PICK[0],PICK[1],20,6),'MAG','MAG','EPDM','包胶 φ20×10','邵氏 A40–50')
for x0 in (23,-25):
    arm=box(x0,x0+2,-76,2,3,15).cut(cylx(x0-1,x0+3,PICK[0],PICK[1],6.2)).cut(cylx(x0-1,x0+3,FEED[0],FEED[1],8.2))
    add('AF14','拾取臂',arm,'MAG','MAG','SUS304','激光切割 t2','绕送片轴摆动；尾端受脱开凸轮下压')
add('AF15','送片轴',cylx(-58,62,FEED[0],FEED[1],8),'MAG','MAG','SUS304','车削 φ8×120','')
add('AF16','送片胶辊',tubex(-15,15,FEED[0],FEED[1],20,8),'MAG','MAG','EPDM','包胶 φ20×30','')
RET=(T_FEED,-10)
add('AF18','阻尼辊轴',cylx(-22,22,RET[0],RET[1],6),'MAG','MAG','SUS304','车削 φ6×44','轴不转；辊经限矩器套在轴上')
add('AF19','限矩阻尼胶辊',tubex(-15,15,RET[0],RET[1],20,6),'MAG','MAG','EPDM','包胶 φ20×30','内装限矩器')
for x0 in (19,-21):
    lv=box(x0,x0+2,-30,-4,-34,-6).cut(cylx(x0-1,x0+3,RET[0],RET[1],6.2)).cut(cylx(x0-1,x0+3,PIV_RET[0],PIV_RET[1],6.2))
    add('AF20','阻尼辊摆杆',lv,'MAG','MAG','SUS304','激光切割 t2','')
add('AF21','阻尼辊摆轴',cylx(-58,49,PIV_RET[0],PIV_RET[1],6),'MAG','MAG','SUS304','车削 φ6×107','摆杆与轴固连，扭簧上顶')
add('AF22','脱开轴',cylx(-58,51,REL[0],REL[1],6),'MAG','MAG','SUS304','车削 φ6×109','')
for x0 in (22,-26):add('AF23','脱开凸轮',tubex(x0,x0+4,REL[0],REL[1],14,6),'MAG','MAG','POM','车削','偏心 2，压拾取臂尾端')
add('AF24','脱开曲柄（上）',box(-55,-52,-6,12,20,28).cut(cylx(-56,-51,REL[0],REL[1],6)),'MAG','MAG','SUS304','激光切割 t3','')
add('AF25','脱开曲柄（下）',box(-55,-52,-12,12,-34,-26).cut(cylx(-56,-51,PIV_RET[0],PIV_RET[1],6)),'MAG','MAG','SUS304','激光切割 t3','')
add('AF26','脱开拉杆',box(-59,-55,5,11,-34,28),'MAG','MAG','SUS304','激光切割 t4','凸轮抬起拾取臂的同时拉下阻尼辊')
SX=31
add('AF27','超声传感器支架',box(28,46,-14,-6,23,27),'MAG','MAG','6061-T6','铣削','上下各 1');add('AF27','超声传感器支架',box(28,46,-14,-6,-26,-22),'MAG','MAG','6061-T6','铣削')
lg=box(-46,46,-13,0,-2,-0.4).cut(box(SX-6,SX+6,-16,-4,-3,0))
add('AF28','坝后下导板',lg,'MAG','MAG','SUS304','激光切割 t1.5','')
for q in idl_in:
    add('AF29','弯道托辊',tubex(-42,42,q[0],q[1],IOD,4),'G','MAG','POM',f'车削 φ{IOD}×84','自由转动');add('AF30','托辊销',cylx(-52,52,q[0],q[1],4),'G','MAG','SUS304','φ4×104 销轴','两端卡簧')
add('AF31','下滑弯道内导板',sector(ce,R-GAP-1.5,R-GAP,0,a-math.radians(3),-1,-46,46),'G','MAG','SUS304','滚弯 t1.5',f'与片留 {GAP} mm 首轮间隙；0.8/2/3 mm 为可换垫对比件')
for g_ in p['inner_guide_gap_variants_mm']:
    if g_!=GAP:PARTS[f'AF31_{g_:g}']=dict(id=f'AF31_{g_:g}',name=f'下滑弯道内导板（间隙 {g_:g} mm）',material='SUS304',process='滚弯 t1.5',note='对比件，不在装配体中',frame='G',shape=sector(ce,R-g_-1.5,R-g_,0,a-math.radians(3),-1,-46,46),qty=1)
add('AF32','下滑弯道外护板',sector(ce,R+IOD+2.5,R+IOD+4,0,a,-1,-46,46),'G','MAG','SUS304','滚弯 t1.5','遮光兼护罩，不接触片')
for q in tie_front:add('AF33','拉杆 φ8×92',cylx(-46,46,q[0],q[1],8),'G','MAG','6061-T6','车削，两端 M4','')
lid=box(-50.5,50.5,T_TOP,-110,34.5,36).fuse(box(49,50.5,T_TOP,-110,20,34.5)).fuse(box(-50.5,-49,T_TOP,-110,20,34.5))
add('AF34','片仓盖',lid.clean(),'MAG','MAG','5052-H32','折弯 t1.5','上端铰接，带联锁磁块')
add('AF35','分离头罩',box(-46,46,-110,5,48,49.5),'MAG','MAG','5052-H32','折弯 t1.5','')
add('AF36','前底板',box(-75,75,FRONT,PF,5,11),'G','MAG','6061-T6','铣削 t6','')
for sx in (1,-1):
    ang=box(49,64,PF-142,PF-5,11,13).fuse(box(49,51,PF-142,PF-5,13,26)).clean()
    add('AF37','侧板角码',ang if sx>0 else mirror(ang),'G','MAG','5052-H32','折弯 t2','')
for (x,y) in ((-62,FRONT+17),(62,FRONT+17),(-62,PF-17),(62,PF-17)):add('ST01','调平脚 φ20×13（行程±3）',cq.Workplane('XY').circle(10).extrude(13).val().translate(cq.Vector(x,y,-8)),'G','MAG','外购','标准件','脚底 Z=-8，与 G3 橡胶脚同一水平面')
add('AF38','对接舌板',box(-40,20,PF-22,PF+31,11,17),'G','MAG','6061-T6','铣削 t6','固定在扫描仪底板前缘；2×φ6 定位销 + 2 手拧螺钉')
# purchased items (envelopes)
add('ST02','NEMA17 步进电机 42×42×40',box(72,112,-96,-54,-7,35),'MAG','MAG','外购','标准件','送片/拾取驱动')
mp=box(69,72,-100,-50,-11,39)
for dt in (-15.5,15.5):
    for dn in (-15.5,15.5):mp=mp.fuse(cylx(49,69,-75+dt,14+dn,6))
add('AF17','电机座板（带 4 柱）',mp.clean(),'MAG','MAG','6061-T6','铣削 + 4×φ6 支柱','')
add('ST03','GT2 20 齿带轮',cylx(52,66,-75,14,16),'MAG','MAG','外购','标准件','');add('ST04','GT2 40 齿带轮',tubex(52,60,FEED[0],FEED[1],26,8),'MAG','MAG','外购','标准件','')
add('ST05','NEMA11 行星减速步进 28×28×58',box(52,110,LIFT_T[0]-14,LIFT_T[0]+14,LIFT_N-14,LIFT_N+14),'MAG','MAG','外购','标准件','推片板驱动，减速比约 14')
add('ST06','微型减速电机 12×10×34',box(51,85,REL[0]-6,REL[0]+6,REL[1]-5,REL[1]+5),'MAG','MAG','外购','标准件','脱开驱动，带原点开关')
add('ST07','超声双张传感器 φ10×20',cylx(0,20,0,0,10).rotate(cq.Vector(0,0,0),cq.Vector(0,1,0),-90).translate(cq.Vector(SX,T_SENS,3)),'MAG','MAG','外购','标准件','发射')
add('ST07','超声双张传感器 φ10×20',cylx(0,19,0,0,10).rotate(cq.Vector(0,0,0),cq.Vector(0,1,0),-90).translate(cq.Vector(SX,T_SENS,-22)),'MAG','MAG','外购','标准件','接收')
# =====================================================================================================
# ENT - throat cartridge: flange, light-trap tunnel, entry roller unit (global coordinates)
# =====================================================================================================
EY=p['entry_nip_y_mm'];EZU,EZL=zf+10.1,zf-10.1;EPV=(EY+8,90)
fl=box(CART['flange_x_mm'][0],CART['flange_x_mm'][1],-150-CART['flange_thickness_mm'],-150,CART['flange_z_mm'][0],CART['flange_z_mm'][1]).cut(box(-71,71,-160,-140,zf-CART['tunnel_slot_height_mm']/2,zf+CART['tunnel_slot_height_mm']/2))
add('EN12','喉口卡匣法兰',fl,'G','ENT','5052-H32','激光切割 t3','压在前面板外侧，带密封垫；整个卡匣由此拆装')
tp=box(-70,70,-150,EY-9,zf+CART['tunnel_slot_height_mm']/2,zf+CART['tunnel_slot_height_mm']/2+2)
add('EN13','喉口光陷阱板',tp,'G','ENT','5052-H32','折弯 t2，哑黑阳极氧化','上下各 1；只有 %d mm 长，与 R5 原迷宫（30 mm）不等价'%CART['tunnel_length_mm'])
add('EN13','喉口光陷阱板',box(-70,70,-150,EY-9,zf-CART['tunnel_slot_height_mm']/2-2,zf-CART['tunnel_slot_height_mm']/2),'G','ENT','5052-H32','折弯 t2，哑黑阳极氧化')
sdp=box(70,71.5,-150,EY-9,zf-CART['tunnel_slot_height_mm']/2-2,zf+CART['tunnel_slot_height_mm']/2+2)
add('EN14','喉口侧挡板',sdp,'G','ENT','5052-H32','折弯 t1.5','左右各 1');add('EN14','喉口侧挡板',mirror(sdp),'G','ENT','5052-H32','折弯 t1.5')
for sx in (1,-1):
    ck=box(58,61,EY-9,EY+12,82,148).cut(cylx(57,62,EY,EZU,16)).cut(cylx(57,62,EPV[0],EPV[1],5.4)).cut(box(57,62,EY-4,EY+4,EZL-6,EZL+4))
    add('EN01','入口辊颊板',ck if sx>0 else mirror(ck),'G','ENT','5052-H32','激光切割 t3','')
add('EN02','入口辊上横梁',box(-58,58,EY-9,EY+12,144,148),'G','ENT','6061-T6','铣削','与法兰螺接');add('EN03','入口辊下横梁',box(-58,58,EY-9,EY+12,82,86),'G','ENT','6061-T6','铣削','')
add('EN04','入口上辊轴',cylx(-66,73,EY,EZU,8),'G','ENT','SUS304','车削 φ8×139','主动');add('EN05','入口上胶辊',tubex(-42,42,EY,EZU,20,8),'G','ENT','EPDM','包胶 φ20×84','')
add('EN06','入口下辊轴',cylx(-56,56,EY,EZL,6),'G','ENT','SUS304','车削 φ6×112','');add('EN07','入口下胶辊',tubex(-42,42,EY,EZL,20,6),'G','ENT','EPDM','包胶 φ20×84','从动；扫描时脱开')
for x0 in (52,-54):
    lv=box(x0,x0+2,EY-5,EY+11.5,86.5,104).cut(cylx(x0-1,x0+3,EY,EZL,6.2)).cut(cylx(x0-1,x0+3,EPV[0],EPV[1],5.2))
    add('EN08','入口下辊摆杆',lv,'G','ENT','SUS304','激光切割 t2','')
add('EN09','入口下辊摆轴',cylx(-61,66,EPV[0],EPV[1],5),'G','ENT','SUS304','车削 φ5×127','')
add('EN10','入口脱开曲柄',box(62,65,EY+4,EY+12,68,94).cut(cylx(61,66,EPV[0],EPV[1],5)),'G','ENT','SUS304','激光切割 t3','')
add('EN15','侧密封块',box(42,58,EY-9,EY+9,zf-2.5,zf+2.5),'G','ENT','EPDM','模切','辊端与颊板之间的挡光块；左右各 1')
add('EN15','侧密封块',box(-58,-42,EY-9,EY+9,zf-2.5,zf+2.5),'G','ENT','EPDM','模切')
add('ST06','微型减速电机 12×10×34',box(66,100,EY+2,EY+14,58,68),'G','ENT','外购','标准件','入口辊脱开')
add('ST03','GT2 20 齿带轮',tubex(63,71,EY,EZU,16,8),'G','ENT','外购','标准件','');add('ST03','GT2 20 齿带轮',cylx(63,73,EY+5,150,16),'G','ENT','外购','标准件','')
add('ST08','NEMA11 步进电机 28×28×32',box(75,107,EY-9,EY+19,136,164),'G','ENT','外购','标准件','入口辊驱动，经限矩联轴器')
add('EN11','入口电机座',box(73,75,EY-9,EY+19,100,166).fuse(box(61,73,EY-9,EY-5,100,108)).clean(),'G','ENT','5052-H32','折弯 t2','固定在右颊板')
# =====================================================================================================
# BIN - ramp bend, eject unit, standing output bin
# =====================================================================================================
EJ=(p['eject_nip_after_bend_mm'],-10);PIN=(p['eject_nip_after_bend_mm'],10);PV2=(30,16);TB=p['eject_nip_after_bend_mm']+p['output_bin_length_mm']
rear_outline=[(153,11),(153,128),gb(10,24),gb(45,24),gb(45,14),gb(TB,14),gb(TB,-35),gb(-5,-35),(265,11)]
idl_out=[(cx[0]+IR*math.sin(b*i/(NI+1)),cx[1]-IR*math.cos(b*i/(NI+1))) for i in range(1,NI+1)]
tie_rear=[(165,60),(255,40),gb(30,-27)]
holes_rear=[(gb(*EJ),16),(gb(*PV2),6.4),(gb(*p['output_gate']['finger_pivot_tn_mm']),4.2),(gb(*p['output_gate']['paddle_pivot_tn_mm']),5.2)]+[(q,4.2) for q in idl_out]+[(q,4.3) for q in tie_rear]
add('XB01','收片侧板（左）',plate(rear_outline,holes_rear,-49,-46),'G','BIN','5052-H32','激光切割 t3','');add('XB02','收片侧板（右）',plate(rear_outline,holes_rear,46,49),'G','BIN','5052-H32','激光切割 t3','外侧装排片电机')
add('XB03','收片仓后壁',box(-46,46,14,TB,-35,-33),'BIN','BIN','5052-H32','激光切割 t2','后仰 10°')
add('XB05','排片主动轴',cylx(-49,62,EJ[0],EJ[1],8),'BIN','BIN','SUS304','车削 φ8×111','');add('XB06','排片主动胶辊',tubex(-12,12,EJ[0],EJ[1],20,8),'BIN','BIN','EPDM','包胶 φ20×24','')
GT=p['output_gate'];PV=GT['finger_pivot_tn_mm'];TP=GT['finger_tip_tn_mm'];PP=GT['paddle_pivot_tn_mm']
import math as _m
def strip2(p0,p1,w,x0,x1):
    dx,dy=p1[0]-p0[0],p1[1]-p0[1];L=_m.hypot(dx,dy);nx,ny=-dy/L*w/2,dx/L*w/2
    return prism([(p0[0]+nx,p0[1]+ny),(p1[0]+nx,p1[1]+ny),(p1[0]-nx,p1[1]-ny),(p0[0]-nx,p0[1]-ny)],x0,x1)
add('XB20','止退指轴',cylx(-42,42,PV[0],PV[1],4),'BIN','BIN','SUS304','车削 φ4×84','三只止退指的铰轴；扭簧使指尖回到路径内')
for xf in (-30,0,30):add('XB21','止退指',strip2(PV,TP,2,xf-GT['finger_width_mm']/2,xf+GT['finger_width_mm']/2).cut(cylx(xf-6,xf+6,PV[0],PV[1],4.2)),'BIN','BIN','SUS304','激光切割 t2','被动单向：片头向上顶开，片尾落回时托住')
add('XB22','拨入轴',cylx(-56,46,PP[0],PP[1],5),'BIN','BIN','SUS304','车削 φ5×102','带两只拨入板，微型减速电机驱动')
for xp in (-20,20):add('XB23','拨入板',strip2(PP,(PP[0]+30,PP[1]),2,xp-4,xp+4).cut(cylx(xp-6,xp+6,PP[0],PP[1],5.2)),'BIN','BIN','SUS304','激光切割 t2','静止位平贴前盖；转 %d° 把被托住的片推向片堆'%GT['paddle_sweep_deg'])
add('ST06','微型减速电机 12×10×34',box(-90,-56,PP[0]-6,PP[0]+6,PP[1]-5,PP[1]+5),'BIN','BIN','外购','标准件','拨入驱动，带原点开关')
add('XB08','排片压轮轴',cylx(-45,45,PIN[0],PIN[1],6),'BIN','BIN','SUS304','车削 φ6×90','');add('XB09','排片压轮',tubex(-12,12,PIN[0],PIN[1],20,6),'BIN','BIN','EPDM','包胶 φ20×24','从动，可脱开')
for x0 in (43,-45):
    lv=box(x0,x0+2,2,36,6,20).cut(cylx(x0-1,x0+3,PIN[0],PIN[1],6.2)).cut(cylx(x0-1,x0+3,PV2[0],PV2[1],6.2))
    add('XB10','压轮摆杆',lv,'BIN','BIN','SUS304','激光切割 t2','')
add('XB11','压轮摆轴',cylx(-58,49,PV2[0],PV2[1],6),'BIN','BIN','SUS304','车削 φ6×107','')
add('XB12','排片脱开曲柄',box(-55,-52,26,34,12,36).cut(cylx(-56,-51,PV2[0],PV2[1],6)),'BIN','BIN','SUS304','激光切割 t3','')
add('ST06','微型减速电机 12×10×34',box(-86,-52,36,48,38,48),'BIN','BIN','外购','标准件','排片压轮脱开')
add('XB13','收片仓前挡板',box(-46,46,40,TB,10,12),'BIN','BIN','PC','切割 t2','透明，可看到片数')
bs_strip=box(41,46,40,TB,-33,10).cut(cylx(40,47,p['output_gate']['paddle_pivot_tn_mm'][0],p['output_gate']['paddle_pivot_tn_mm'][1],5.6))
add('XB14','收片侧导条',bs_strip,'BIN','BIN','POM','铣削','');add('XB14','收片侧导条',mirror(bs_strip),'BIN','BIN','POM','铣削')
add('XB15','上行弯道内导板',sector(cx,R-GAP-1.5,R-GAP,0,b-math.radians(1.5),1,-46,46),'G','BIN','SUS304','滚弯 t1.5','间隙同前弯')
add('XB16','上行弯道外护板',sector(cx,R+IOD+2.5,R+IOD+4,0,b-math.radians(8),1,-46,46),'G','BIN','SUS304','滚弯 t1.5','')
for q in idl_out:
    add('AF29','弯道托辊',tubex(-42,42,q[0],q[1],IOD,4),'G','BIN','POM',f'车削 φ{IOD}×84');add('AF30','托辊销',cylx(-52,52,q[0],q[1],4),'G','BIN','SUS304','φ4×104 销轴')
for q in tie_rear:add('AF33','拉杆 φ8×92',cylx(-46,46,q[0],q[1],8),'G','BIN','6061-T6','车削，两端 M4')
add('XB17','后底板',box(-75,75,153,300,5,11),'G','BIN','6061-T6','铣削 t6','')
for sx in (1,-1):
    ang=box(49,64,158,260,11,13).fuse(box(49,51,158,260,13,26)).clean()
    add('AF37','侧板角码',ang if sx>0 else mirror(ang),'G','BIN','5052-H32','折弯 t2')
for (x,y) in ((-62,165),(62,165),(-62,288),(62,288)):add('ST01','调平脚 φ20×13（行程±3）',cq.Workplane('XY').circle(10).extrude(13).val().translate(cq.Vector(x,y,-8)),'G','BIN','外购','标准件')
add('AF38','对接舌板',box(-40,20,122,175,11,17),'G','BIN','6061-T6','铣削 t6')
add('ST02','NEMA17 步进电机 42×42×40',box(72,112,39,81,-31,11),'BIN','BIN','外购','标准件','排片驱动')
mp=box(69,72,35,85,-35,15)
for dt in (-15.5,15.5):
    for dn in (-15.5,15.5):mp=mp.fuse(cylx(49,69,60+dt,-10+dn,6))
add('AF17','电机座板（带 4 柱）',mp.clean(),'BIN','BIN','6061-T6','铣削 + 4×φ6 支柱')
add('ST03','GT2 20 齿带轮',cylx(52,66,60,-10,16),'BIN','BIN','外购','标准件');add('ST04','GT2 40 齿带轮',tubex(52,60,EJ[0],EJ[1],26,8),'BIN','BIN','外购','标准件')
# =====================================================================================================
# outputs
# =====================================================================================================
(M/'step').mkdir(exist_ok=True);(M/'dxf').mkdir(exist_ok=True)
ab=lambda s:[round(v,2) for v in (s.BoundingBox().xmin,s.BoundingBox().ymin,s.BoundingBox().zmin,s.BoundingBox().xmax,s.BoundingBox().ymax,s.BoundingBox().zmax)]
rows=[]
for pid,P in sorted(PARTS.items()):
    s=P['shape'];cq.exporters.export(cq.Workplane('XY').add(s),str(M/'step'/f'{pid}.step'))
    bb=s.BoundingBox();dims=sorted([bb.xlen,bb.ylen,bb.zlen],reverse=True);rho=RHO[P['material']]
    P.update(volume_mm3=round(s.Volume(),1),bbox_sorted_mm=[round(d,1) for d in dims],mass_g=None if rho is None else round(s.Volume()*rho/1000,1),valid=bool(s.isValid()))
    rows.append([pid,P['name'],P['qty'],P['material'],P['process'],'×'.join(f'{d:g}' for d in P['bbox_sorted_mm']),'' if P['mass_g'] is None else P['mass_g'],P['note']])
with open(M/'ADF50_V06_机械BOM.csv','w',newline='',encoding='utf-8-sig') as f:
    w=csv.writer(f);w.writerow(['件号','名称','数量','材料','工艺','外形 mm','单件质量 g','备注']);w.writerows(rows)
asm=cq.Assembly(name='ADF50_V06_mechanical');COL={'MAG':cq.Color(0.55,0.70,0.90),'ENT':cq.Color(0.95,0.70,0.40),'BIN':cq.Color(0.55,0.85,0.65)}
sub={g:cq.Assembly(name=g) for g in COL}
for i,r in enumerate(INST):sub[r['group']].add(r['shape'],name=f"{r['part']}_{i:03d}",color=COL[r['group']])
for g in sub:asm.add(sub[g],name=g)
asm.save(str(M/'step'/'ADF50_V06_mechanical_assembly.step'))
for g in sub:sub[g].save(str(M/'step'/f'ADF50_V06_{g}_subassembly.step'))
def dxf(name,outline,holes):
    d=ezdxf.new('R2010');ms=d.modelspace();ms.add_lwpolyline(outline,close=True)
    for c,dia in holes:ms.add_circle(c,dia/2)
    d.saveas(str(M/'dxf'/name))
dxf('AF01_AF02_片仓侧板.dxf',front_outline,holes_front);dxf('XB01_XB02_收片侧板.dxf',rear_outline,holes_rear)
dxf('AF03_片仓背板.dxf',[(-46,-385),(46,-385),(46,-52),(-46,-52)],[]);dxf('XB03_收片仓后壁.dxf',[(-46,14),(46,14),(46,TB),(-46,TB)],[])
# ---- self interference (all pairs of placed instances)
N=len(INST);bbs=[ab(r['shape']) for r in INST];self_hits=[];pairs=0
for i in range(N):
    for j in range(i+1,N):
        if min(min(bbs[i][k+3],bbs[j][k+3])-max(bbs[i][k],bbs[j][k]) for k in range(3))<=1e-4:continue
        pairs+=1;v=INST[i]['shape'].intersect(INST[j]['shape']).Volume()
        if v>0.01:self_hits.append(dict(a=INST[i]['name'],b=INST[j]['name'],volume_mm3=round(v,2)))
# ---- against the scanner: G3 integrated context (238 instances: G3 case, base, feet, four-roller package, R5 core) with the
# R5.2 layout-B shift on the PMT group. Replaced/removed items are skipped. The panel cut-outs of this design are APPLIED to the
# G3 front/rear panels before testing, so a remaining overlap is a real conflict.
G3=R5/'ZL80_R52_G3_20261116'
g52=json.loads((R5/'engineering/parameters.json').read_text())['collector_guide_r52'];dy=g52['pmt_shift_y_vs_r5']
inst=json.loads((G3/'cad/instances.json').read_text());SHIFT=('PMT','B01','Analog','AFE_post','Temp_PMT');SKIP=('R5_Labyrinth-132','Guide_sleeve','Taper')
cache={};hits=[];mods=[];chk=0;OP=CART['panel_opening_x_mm'],CART['panel_opening_z_mm']
CUT_F=box(OP[0][0],OP[0][1],-152,-147,OP[1][0],OP[1][1]).fuse(box(-41,21,-152,-147,10.5,17.5));CUT_R=box(-41,21,147,152,10.5,17.5)
for row in inst:
    nm=row['name']
    if any(k in nm for k in SKIP):continue
    moved=any(k in nm for k in SHIFT);bb=list(row['aabb'])
    if moved:bb[1]+=dy;bb[4]+=dy
    for i in range(N):
        if min(min(bb[k+3],bbs[i][k+3])-max(bb[k],bbs[i][k]) for k in range(3))<=1e-4:continue
        f_=G3/'cad/parts'/f"{row['part']}.step"
        if row['part'] not in cache:cache[row['part']]=cq.importers.importStep(str(f_)).val()
        sh=cache[row['part']]
        if row.get('rotation'):ax,ang=row['rotation'];sh=sh.rotate(cq.Vector(0,0,0),cq.Vector(*ax),ang)
        sh=sh.translate(cq.Vector(*row['position']))
        if moved:sh=sh.translate(cq.Vector(0,dy,0))
        if row['part']=='G3-H01':sh=sh.cut(CUT_F)
        if row['part']=='G3-H02':sh=sh.cut(CUT_R)
        chk+=1;v=sh.intersect(INST[i]['shape']).Volume()
        if v>0.01:hits.append(dict(adf=INST[i]['name'],scanner=nm,scanner_part=row['part'],volume_mm3=round(v,2)))
ko_hits=[]
for k in json.loads((R5/'cad/keepouts.json').read_text()):
    c,sz=k['center'],k['size'];kb=[c[i]-sz[i]/2 for i in range(3)]+[c[i]+sz[i]/2 for i in range(3)]
    if k['id'].startswith('B01'):kb[1]+=dy;kb[4]+=dy
    for i in range(N):
        d=[min(kb[j+3],bbs[i][j+3])-max(kb[j],bbs[i][j]) for j in range(3)]
        if min(d)>0.01:ko_hits.append(dict(adf=INST[i]['name'],keepout=k['id'],keepout_name=k['name'],kind=k.get('kind'),aabb_overlap_mm=[round(x,1) for x in d]))
allbb=[min(q[0] for q in bbs),min(q[1] for q in bbs),min(q[2] for q in bbs),max(q[3] for q in bbs),max(q[4] for q in bbs),max(q[5] for q in bbs)]
env=[allbb[3]-allbb[0],allbb[4]-allbb[1],max(allbb[5],300)-min(allbb[2],-8)]  # height from the bench plane, feet bottom Z=-8
mass={g:round(sum((PARTS[r['part']]['mass_g'] or 0) for r in INST if r['group']==g)) for g in COL}
res=dict(scope='ADF50 V0.6 part-level nominal model. Rigid, no tolerances; fasteners, bearings, belts, springs and cables are not modelled. Purchased items are envelope solids.',
    part_numbers=len(PARTS),instances=N,fabricated_part_numbers=sum(1 for P in PARTS.values() if P['material']!='外购'),all_parts_valid=all(P['valid'] for P in PARTS.values()),
    self_pairs_intersected=pairs,self_overlaps=self_hits,scanner_pairs_intersected=chk,scanner_overlaps=hits,
    scanner_context='G3 integrated context + R5.2 layout B, panel cut-outs applied',keepout_aabb_overlaps=ko_hits,
    scanner_modifications_required=['前面板 G3-H01：开口 x −72…112、z 54…166（184×112），装喉口卡匣，卡匣法兰压在外侧；取消入口迷宫 H08','前、后面板下沿各开 62×7 缺口（x −41…21，z 10.5–17.5）让对接舌板通过','底板 G3-M01 前后缘各加 2×M5 螺孔和 2×φ6 销孔固定舌板','开口后 1.5 mm 薄板的刚度和遮光需复核'],
    overall_aabb=[round(v,1) for v in allbb],working_envelope_mm_WDH=[round(max(env[0],320),1),round(env[1],1),round(env[2],1)],
    fabricated_mass_g_by_group=mass)
(M/'interference.json').write_text(json.dumps(res,ensure_ascii=False,indent=2))
json.dump([{k:v for k,v in P.items() if k!='shape'} for P in PARTS.values()],open(M/'parts.json','w'),ensure_ascii=False,indent=1)
json.dump([dict(part=r['part'],name=r['name'],group=r['group'],frame=r['frame'],aabb=bbs[i]) for i,r in enumerate(INST)],open(M/'instances.json','w'),ensure_ascii=False,indent=1)
print(json.dumps({k:res[k] for k in ('part_numbers','instances','fabricated_part_numbers','all_parts_valid','self_pairs_intersected','self_overlaps','scanner_pairs_intersected','scanner_overlaps','overall_aabb','working_envelope_mm_WDH','fabricated_mass_g_by_group')},ensure_ascii=False,indent=1))
