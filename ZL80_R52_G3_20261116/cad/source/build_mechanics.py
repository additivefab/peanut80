"""ZL80 G3 review geometry. Millimetres. Run from any cwd. Requires cadquery, ezdxf.
Purchased parts are dimensional envelopes, threaded bores are minor/clearance geometry.
No STEP in this package is a released production design. See docs and drawing notes.
"""
from pathlib import Path
import json,math,csv
import cadquery as cq
import ezdxf
R=Path(__file__).resolve().parents[2]
p=json.loads((R/'config/mechanical_parameters.json').read_text())
parts={}; meta=[]; instances=[]
def box(a,b,c,at=(0,0,0)):
 return cq.Workplane('XY').box(a,b,c).val().translate(at)
def cyl(r,l,axis='x',at=(0,0,0)):
 d={'x':(1,0,0),'y':(0,1,0),'z':(0,0,1)}[axis];start=tuple(at[i]-d[i]*l/2 for i in range(3))
 return cq.Solid.makeCylinder(r,l,cq.Vector(*start),cq.Vector(*d))
def cut_holes(s,coords,dia,depth,axis='z'):
 for c in coords:s=s.cut(cyl(dia/2,depth,axis,c))
 return s

def reg(pid,title,s,material='6061-T6',state='NEW_REVIEW_GEOMETRY',note='Unreleased nominal geometry'):
 parts[pid]=s;b=s.BoundingBox()
 meta.append(dict(id=pid,name=title,material=material,status=state,note=note,size=[b.xlen,b.ylen,b.zlen],volume_mm3=s.Volume(),valid=s.isValid()))
 cq.exporters.export(s,str(R/'cad/parts'/f'{pid}.step'))

def add(pid,name,pos=(0,0,0),group='transport',rot=None,move=False):
 instances.append(dict(part=pid,name=name,position=list(pos),group=group,rotation=rot,moves_with_upper=move))

# Base carries the R5 board and collector holes, enlarged only at approved G3 candidates.
base=box(300,288,6)
boarddefs=json.loads((R/'sources/inherited/R51_board_definitions.json').read_text())
base_inherited_holes=[(x,y,0) for x in (-48,48) for y in (-30,30)]
for bd in boarddefs:
 if bd['plane']=='XY':
  ox,oy,oz=bd['origin']
  if bd['id']=='B09':oy=-138
  for hx,hy in bd['holes']:base_inherited_holes.append((ox+hx,oy+hy,0))
base=cut_holes(base,base_inherited_holes,3.4,12)
base_holes=[(x,y,0) for x in (-132,132) for y in (-120,120)]
base_holes += [(x,y,0) for x in (-72,72) for y in (-55,55)]
base_holes += [(x,y,0) for x in (130,142) for y in (36,59)]
base=cut_holes(base,base_holes,4.5,12)
# bottom-side counterbores allow removal without disturbing datum face
base=cut_holes(base,[(x,y,-2) for x,y,_ in base_holes],8,2.2)
dowels=[(x,y,0) for x in (-72,72) for y in (-50,50)]
base=cut_holes(base,dowels,3,12)
reg('G3-M01','共同基准底板 300×288×6',base,note='Datum A = upper surface; frame holes 4.5, two-sided dowel strategy requires process approval')
add('G3-M01','BASE',[0,0,8],'base')

# Side frames, fixed lower bearing pockets, vertical upper slider guides.
# X local thickness 8, globally center +/-72. Outer cap closes counterbore.
frame=box(8,128,126,at=(0,0,80))  # global z17..143 but local x/y
frame=frame.cut(box(12,58,74,at=(0,0,54))) # lower central light/access opening
for y in (-42,42):
 frame=frame.cut(cyl(5.3,12,'x',(0,y,99.9)))
 # right-side pocket x=-2..4 for right frame; left frame mirrored during placement
 frame=frame.cut(cyl(6,6.2,'x',(1.1,y,99.9)))
 frame=frame.cut(box(12,18.15,24.3,at=(0,y,123.05)))
 for dy,dz in [(-7,-7),(-7,7),(7,-7),(7,7)]:
  frame=frame.cut(cyl(.8,12,'x',(0,y+dy,99.9+dz))) # M2 pilot
 for yy in (y-12,y+12):frame=frame.cut(cyl(1.25,10,'z',(0,yy,139)))
 frame=frame.cut(cyl(3,20,'z',(0,y-3,139)))
 frame=frame.cut(cyl(1.8,20,'z',(-1,y+6,139)))
frame=cut_holes(frame,[(0,-55,23),(0,55,23)],3.3,12)
frame=cut_holes(frame,[(0,-50,20),(0,50,20)],3,6)
reg('G3-M02','片道侧框／轴承台阶孔与浮动槽',frame,note='Global Z retained in local model; right frame nominal. Left mirrored. M2/M4 are pilot-hole representation.')
add('G3-M02','FRAME_R',[72,0,0],'frame')
reg('G3-M02L','左片道侧框（X镜像）',frame.mirror('YZ'))
add('G3-M02L','FRAME_L',[-72,0,0],'frame')
foot=cut_holes(box(14,18,6),[(0,0,0)],4.5,10)
foot=cut_holes(foot,[(0,-5,0)],3,10)
reg('G3-M03','侧框安装脚／定位衬块',foot)
for x in (-72,72):
 for y in (-55,55):add('G3-M03',f'FOOT_{x}_{y}',[x,y,14],'frame',[[0,0,1],180] if y<0 else None)

# Roller cores: monolithic 304 stainless mandrel with coating bonded and ground as assembly.
def core(left,right,upper=False):
 s=cyl(7,100)
 for sign in (-1,1):s=s.fuse(cyl(3.7,20,'x',(sign*60,0,0)))
 s=s.fuse(cyl(3,4,'x',(-72,0,0))).fuse(cyl(3,4,'x',(72,0,0)))
 if upper:
  s=s.fuse(cyl(2.5,10,'x',(-79,0,0))) # M5 x .8, cosmetic nominal thread OD only
 else:s=s.fuse(cyl(3,abs(left)-74,'x',((left-74)/2,0,0)))
 s=s.fuse(cyl(3,right-74,'x',((right+74)/2,0,0)))
 return s
reg('G3-R01','入口测量辊芯／长端编码器轴',core(-105,84),'304不锈钢',note='OD14 core L100, journals at +/-72; left extension for AMT. Bonded coating final grind.')
reg('G3-R02','出口牵引辊芯／5-6联轴器轴',core(-105,91),'304不锈钢',note='Right shaft tip X91, coupling insertion10mm; all fits on drawing require supplier approval.')
reg('G3-R03','上压辊芯／M5定位端',core(-84,84,True),'304不锈钢',note='Left M5x0.8 thread not helical in CAD; fixed inner race against shoulder, nut+washer.')
rubber=cyl(10,100).cut(cyl(7,102))
reg('G3-R04','包胶层：硫化／粘结后整辊磨削',rubber,'PU50A或后硫化硅胶50A试样','DOE_MATERIAL','Not a freely sliding sleeve: compound+adhesive qualification required; full-face contact at 80mm film.')
for y,code in [(-42,'G3-R01'),(42,'G3-R02')]:
 add(code,f'LOWER_CORE_{y}',[0,y,99.9]);add('G3-R04',f'LOWER_COVER_{y}',[0,y,99.9],'rubber')
 add('G3-R03',f'UPPER_CORE_{y}',[0,y,120.1],move=True);add('G3-R04',f'UPPER_COVER_{y}',[0,y,120.1],'rubber',move=True)

bearing=cyl(6,4).cut(cyl(3,6))
reg('G3-P01','NMB L-1260ZZ 6×12×4',bearing,'轴承钢','PURCHASE_ENVELOPE','C=831 N, C0=363 N; no internal balls; fit/lubricant/grade requires RFQ')
slider=box(8,18,18).cut(cyl(5.3,12)).cut(cyl(6,6.2,'x',(1.1,0,0)))
for yy,zz in [(-7,-7),(-7,7),(7,-7),(7,7)]:slider=slider.cut(cyl(.8,12,'x',(0,yy,zz)))
slider=slider.cut(cyl(1.25,4,'z',(-1,6,7)))
reg('G3-M04','上辊浮动轴承滑块',slider,note='Guide clearance 0.15 in Y nominal; no claim of anti-stiction performance; axial retainer on both sides.')
reg('G3-M04L','左上辊浮动块（X镜像）',slider.mirror('YZ'))
# cap with pilot holes and spigot; two cap boss lengths define fixed and floating outer race chamber.
def cap(gap):
 s=box(24,24,2,at=(0,0,0)) # will rotate to x thickness
 s=box(2,24,18).fuse(cyl(5.98,1.95-gap,'x',(-(2+1.95-gap)/2,0,0)))
 s=s.cut(cyl(5.3,10))
 for yy,zz in [(-7,-7),(-7,7),(7,-7),(7,7)]:s=s.cut(cyl(1.1,10,'x',(0,yy,zz)))
 return s
reg('G3-M05','左侧定位轴承压盖',cap(0),note='Face to inner pocket forms ~4.05 chamber for bearing4; shim endplay after measuring actual bearing width')
reg('G3-M06','右侧游动轴承压盖',cap(.35),note='Outer race axial room ~0.4mm; do not clamp both rings by screw force')
inner=box(1.5,24,24).cut(cyl(4.2,5))
for yy,zz in [(-7,-7),(-7,7),(7,-7),(7,7)]:inner=inner.cut(cyl(1.1,5,'x',(0,yy,zz)))
reg('G3-M07','上辊内侧导向挡片',inner,'304不锈钢',note='Guide plate contacts side frame sliding face only; 0.10mm nominal axial running clearance')
for y in (-42,42):
 for z in (99.9,120.1):
  for x in (-72,72):
   moving=z>110
   add('G3-P01',f'BRG_{x}_{y}_{z}',[x,y,z],'bearing',move=moving)
   cpid='G3-M05' if x<0 else 'G3-M06'
   add(cpid,f'CAP_{x}_{y}_{z}',[(77.1 if x>0 else -77.1),y,z],'bearing_cap',[[0,0,1],180] if x<0 else None,moving)
   if moving:
    add('G3-M04L' if x<0 else 'G3-M04',f'SLIDER_{x}_{y}',[x,y,z],'slider',None,True)
    add('G3-M07',f'GUIDEPLATE_{x}_{y}',[(67.15 if x>0 else -67.15),y,z],'slider',move=True)

# Lower fixed-side collars and inner-ring-only spacers. Upper M5 nuts avoid collar swept-envelope collision.
reg('G3-P02','6mm夹紧轴环／MCL-6-A本体限界',cyl(8,9).cut(cyl(3,12)),'铝','PURCHASE_ENVELOPE','Hardware swept diameter20.8 reserved separately; never place this collar on both opposing rollers at same X')
reg('G3-M08','定位内圈垫套 6.1/7.4×5.1',cyl(3.7,5.1).cut(cyl(3.05,8)),'304不锈钢')
reg('G3-M09','上辊定位垫片 5.3/7.4×0.5',cyl(3.7,.5).cut(cyl(2.65,2)),'304不锈钢')
pts=[(4.62*math.cos(i*math.pi/3),4.62*math.sin(i*math.pi/3)) for i in range(6)]
nut=cq.Workplane('YZ').polyline(pts).close().extrude(2.5,both=True).val().cut(cyl(2.1,8))
reg('G3-P03','M5薄锁紧螺母包络',nut,'钢','PURCHASE_ENVELOPE','M5 prevailing torque type / locking method to be approved; CAD minor bore only')
for y in (-42,42):
 add('G3-M08',f'SPACER_L_{y}',[-76.55,y,99.9]);add('G3-P02',f'COLLAR_L_{y}',[-83.6,y,99.9])
 add('G3-M09',f'UPPER_WASHER_{y}',[-74.25,y,120.1],move=True);add('G3-P03',f'UPPER_NUT_{y}',[-77,y,120.1],move=True)

# Springs/preload/release: four independent spring plungers, two synchronised manual lift bars.
top=box(24,30,10)
top=cut_holes(top,[(0,-3,0)],3.3,16)
top=top.cut(cyl(2.75,5,'z',(0,-3,-2.5)))
top=cut_holes(top,[(-1,6,0)],3.4,16)
for yy in (-12,12):top=top.cut(cyl(1.7,16,'z',(0,yy,0)))
reg('G3-M10','弹簧与释放顶座',top,note='M4 preload adjust pilot3.3; M3 lift clearance3.4; fix screws separate from moving lift rod')
reg('G3-M10L','左弹簧与释放顶座（X镜像）',top.mirror('YZ'))
spring=cyl(2.5,13.9,'z').cut(cyl(1.5,16,'z'))
reg('G3-P04','压簧工作包络 OD5×13.9',spring,'弹簧钢','PURCHASE_SPRING_ENVELOPE','k0.5 N/mm, free18, installed13.9; supplier solid length<=7.5mm and fatigue proof required; tube is not a real spring')
reg('G3-M16','M4调压隔离压垫 OD5.2×1',cyl(2.6,1,'z'),'304不锈钢',note='Moves with preload screw; avoids spring contacting screw threads')
adj=cyl(2,16,'z').fuse(cyl(4,3,'z',(0,0,9.5)))
reg('G3-P05','M4调压螺钉／防松标记',adj,'钢','PURCHASE_ENVELOPE')
lift=cyl(1.5,46,'z').fuse(cyl(3,2,'z',(0,0,24)))
reg('G3-P06','M3双端提辊螺杆限界',lift,'钢','PURCHASE_ENVELOPE','two ends linked by crossbar; do not twist roller during loading')
liftbar=cut_holes(box(164,8,4),[(-71,0,0),(71,0,0)],3.4,8)
reg('G3-M11','双端提辊联动横杆',liftbar,note='Lift travel5 mm; hold open only after motor/laser disabled. Provisional mechanism, ergonomic test pending.')
for y in (-42,42):
 for x in (-72,72):
  add('G3-M10L' if x<0 else 'G3-M10',f'TOP_{x}_{y}',[x,y,148],'preload')
  add('G3-P04',f'SPRING_{x}_{y}',[x,y-3,136.05],'spring')
  add('G3-P05',f'ADJUST_{x}_{y}',[x,y-3,152],'preload')
  add('G3-M16',f'PRESSPAD_{x}_{y}',[x,y-3,143.5],'preload')
  add('G3-P06',f'LIFT_ROD_{x}_{y}',[x-1 if x>0 else x+1,y+6,148.1],'release',move=True)
 add('G3-M11',f'LIFT_BAR_{y}',[0,y+6,168.1],'release',move=True)

# Outlet motor real length and commercial coupling envelope, not inherited 16mm placeholder.
coupler=cyl(10,30).cut(cyl(4,32))
# Add bored hub sleeves to the generic spider envelope: left 6mm / right5mm.
coupler=coupler.fuse(cyl(4,10,'x',(-10,0,0)).cut(cyl(3,12,'x',(-10,0,0))))
coupler=coupler.fuse(cyl(4,10,'x',(10,0,0)).cut(cyl(2.5,12,'x',(10,0,0))))
reg('G3-P07','NBK MJC-20CS-WH-5-6',coupler,'铝＋弹性体','PURCHASE_ENVELOPE','OD20,W30; CAD has insertion bores but not proprietary jaw detail; nominal grip10mm each side')
add('G3-P07','COUPLING',[96,42,99.9],'drive')
motor=box(26,35.2,35.2,(13,0,0)).fuse(cyl(11,2,'x',(-1,0,0))).fuse(cyl(2.5,20.5,'x',(-10.25,0,0)))
for yy in (-13,13):
 for zz in (-13,13):motor=motor.cut(cyl(1.25,5,'x',(2,yy,zz)))
reg('G3-P08','14HS10-0404S 尺寸候选',motor,'采购','PURCHASE_ENVELOPE','Origin at front mounting face. D-flat omitted. Source verifies shaft20.5, body26; holes26pitch require signed supplier drawing')
add('G3-P08','DRIVE_MOTOR',[121.5,42,99.9],'drive')
mount=box(5,48,49,(119,42,99.5)).fuse(box(5,34,64,(119,49,43))).fuse(box(31,34,5,(132,49,13.5)))
mount=mount.cut(cyl(11.1,10,'x',(119,42,99.9)))
for yy in (-13,13):
 for zz in (-13,13):mount=mount.cut(cyl(1.7,10,'x',(119,42+yy,99.9+zz)))
mount=mount.cut(box(9,30,40,(119,42,48)))
mount=cut_holes(mount,[(x,y,13.5) for x in (130,142) for y in (36,59)],4.5,10)
reg('G3-M12','出口电机直立支座',mount,note='Global coordinates in part; 4x4.5 foot holes at X130/142 Y36/59. D-flat/clamp screw interface to confirm')
add('G3-M12','MOTOR_BRACKET',group='frame')
guard=cyl(12.5,36.1,'x').cut(cyl(11.2,39,'x'))
reg('G3-M13','联轴器旋转防护筒',guard,'铝','PROTOTYPE_GUARD','Support clamp/fasteners not frozen; guard must be retained before powered test')
add('G3-M13','COUPLER_GUARD',[98.35,42,99.9],'guard')

# Encoder body with shaft hole, mounting plate and two stand-offs.
enc=box(10.34,28.58,37.25,(0,0,-3.295)).cut(cyl(3.1,15))
reg('G3-P09','AMT112S带轴孔包络',enc,'采购','PURCHASE_ENVELOPE','R5 overall envelope; mounting-hole detail must be checked against supplier drawing; no 3.3V direct connect')
encplate=box(3,40,46).cut(cyl(7.8,8))
for yy,zz in [(-16,-12),(16,-12),(-16,12),(16,12)]:encplate=encplate.cut(cyl(1.7,8,'x',(0,yy,zz)))
reg('G3-M14','编码器可换安装板',encplate,note='4 prototype holes ±16Y,-12/+12Z are adapter interface, not claimed AMT factory pattern; supplier hole insert pending')
reg('G3-M15','编码器支柱 6OD×12.5L',cyl(3,12.5).cut(cyl(1.7,16)),'黄铜')
for y in (-42,42):
 add('G3-P09',f'ENCODER_{y}',[-98,y,99.9],'encoder')
 add('G3-M14',f'ENC_PLATE_{y}',[-90,y,99.9],'encoder_mount')
 for dy in (-16,16):add('G3-M15',f'ENC_POST_{y}_{dy}',[-82.25,y+dy,87.9],'encoder_mount')

# Scan support is kept from R5 as interface only; do not cover the slit with a roller/plate.
# Case: all six panels are flat laser-cut sheet; no fake bend allowance.
front=box(320,1.5,297)
front=front.cut(box(86,5,5,(0,0,-40)))
front_holes=[(x,0,z-150) for x in (-154,154) for z in (20,150,280)]
front=cut_holes(front,front_holes,3.4,6,'y')
reg('G3-H01','前片口平板 320×297×1.5',front,'5052-H32','FLAT_SHEET_REVIEW','Y=-149.25,Z150; 86x5 slot. Light labyrinth inherited, not laser safety certification')
rear=front.cut(box(40,5,40,(-115,0,-80))).cut(box(24,5,14,(-110,0,-110)))
reg('G3-H02','后片口与风道平板',rear,'5052-H32','FLAT_SHEET_REVIEW')
side=box(1.5,297,297)
side=cut_holes(side,[(0,y,z-150) for y in (-144,144) for z in (20,150,280)],3.4,6,'x')
right=side.cut(box(5,64,35,(0,-103,-113)))
left=side.cut(cyl(6.1,6,'x',(0,110,-108)))
reg('G3-H03','右检修侧板／SP2插拔窗',right,'5052-H32','FLAT_SHEET_REVIEW','Window64x35 for replaceable I/O insert, actual SP2 port pattern not frozen')
reg('G3-H04','左侧板／24V入口',left,'5052-H32','FLAT_SHEET_REVIEW','12.2 inlet hole is placeholder, MPN of power connector required')
top=box(320,300,1.5)
top=cut_holes(top,[(x,y,0) for x in (-154,154) for y in (-144,144)],3.4,8)
reg('G3-H05','顶盖平板',top,'5052-H32','FLAT_SHEET_REVIEW')
bottom=cut_holes(top,[(x,y,0) for x in (-132,132) for y in (-120,120)],4.5,8)
reg('G3-H06','底盖平板',bottom,'5052-H32','FLAT_SHEET_REVIEW')
for pid,name,pos in [('G3-H01','FRONT',[0,-149.25,150]),('G3-H02','REAR',[0,149.25,150]),('G3-H03','RIGHT',[159.25,0,150]),('G3-H04','LEFT',[-159.25,0,150]),('G3-H05','TOP',[0,0,299.25]),('G3-H06','BOTTOM',[0,0,.75])]:add(pid,name,pos,'enclosure')
# Corner angles are external sheet supports, kept out of calibrated optical load path.
angle=box(10,2,297,(0,4,0)).fuse(box(2,10,297,(4,0,0)))
reg('G3-H07','10×10×2机箱角撑型材',angle,'铝型材','EXTRUSION_REVIEW','Panel hole positions on drawings; thread pilot not repeated in CAD; end caps not load datum')
for x in (-153.5,153.5):
 for y in (-143.5,143.5):
  rot=0 if x>0 and y>0 else 90 if x<0 and y>0 else 180 if x<0 and y<0 else 270
  add('G3-H07',f'CORNER_{x}_{y}',[x,y,150],'enclosure',[[0,0,1],rot])

# Standard fastener envelopes. Thread minor-diameter overlaps are classified explicitly.
def screw(d,L,hd,hh,axis='z'):
 direction={'x':(1,0,0),'z':(0,0,1)}[axis]
 return cyl(d/2,L,axis,tuple(q*(-L/2) for q in direction)).fuse(cyl(hd/2,hh,axis,tuple(q*hh/2 for q in direction)))
reg('G3-F01','M2×5压盖螺钉',screw(2,5,3.8,2,'x'),'钢','FASTENER_ENVELOPE','No helix; shank/minor-hole overlap represents thread engagement')
reg('G3-F02','M3×15顶座螺钉',screw(3,15,5.5,3),'钢','FASTENER_ENVELOPE')
reg('G3-F03','M4×20基座紧固螺钉',screw(4,20,7,4),'钢','FASTENER_ENVELOPE')
for y in (-42,42):
 for z in (99.9,120.1):
  for x in (-72,72):
   for dy,dz in [(-7,-7),(-7,7),(7,-7),(7,7)]:
    add('G3-F01',f'CAP_SCREW_{x}_{y}_{z}_{dy}_{dz}',[78.1 if x>0 else -78.1,y+dy,z+dz],'fastener',[[0,0,1],180] if x<0 else None,z>110)
 for x in (-72,72):
  for dy in (-12,12):add('G3-F02',f'TOP_SCREW_{x}_{y}_{dy}',[x,y+dy,153],'fastener')
for x in (-72,72):
 for y in (-55,55):add('G3-F03',f'FRAME_SCREW_{x}_{y}',[x,y,7.1],'fastener',[[1,0,0],180])

reg('G3-P10','可换弹性脚垫 OD16×8',cyl(8,8,'z').cut(cyl(2.25,12,'z')),'弹性体','PURCHASE_ENVELOPE','M4 through mounting; load rating to be checked')
for x in (-132,132):
 for y in (-120,120):add('G3-P10',f'RUBBER_FOOT_{x}_{y}',[x,y,-4],'external_foot')

# Film and kinematic/connector envelopes are separated from manufactured solids.
reg('REF_FILM','80mm胶片基准面',box(80,270,.2),'film','REFERENCE_ONLY')
add('REF_FILM','FILM',[0,0,110],'reference')

# Retain optical/electronic context at exact R5 poses. Their definitions are not silently redesigned.
old=json.loads((R/'sources/inherited/instances_R5.json').read_text())
for pid in sorted(set(r['part'] for r in old)):
 q=R/'sources/inherited/parts'/f'{pid}.step'
 if q.exists():reg('REF_'+pid,pid+' R5继承接口',cq.importers.importStep(str(q)).val(),'inherited','INHERITED_NOT_REVALIDATED','Optical/purchased/PCB geometry inherited; G2 native board remains electrical authority')
for r in old:
 pid='REF_'+r['part']
 if pid in parts:add(pid,'R5_'+r['name'],r['position'],'inherited',r['rotation'])

def place(r,mode='closed'):
 s=parts[r['part']]
 if r['rotation']:
  axis,ang=r['rotation'];s=s.rotate((0,0,0),tuple(axis),ang)
 v=list(r['position'])
 if mode=='open' and r['moves_with_upper']:v[2]+=p['upper_release_lift']
 if mode=='open' and r['group']=='spring':
  h=p['spring_installed_length']-p['upper_release_lift'];s=cyl(2.5,h,'z').cut(cyl(1.5,h+2,'z'));v[2]+=p['upper_release_lift']/2
 if mode=='exploded':
  if r['moves_with_upper']:v[2]+=45
  if r['group'] in ('bearing','bearing_cap','encoder','encoder_mount'):v[0]+=35*(1 if v[0]>0 else -1)
  if r['group'] in ('preload','spring'):v[2]+=65
  if r['group']=='drive':v[0]+=55
 return s.translate(v)
colors={'rubber':(.18,.20,.23),'bearing':(.7,.72,.75),'drive':(.26,.32,.4),'encoder':(.33,.51,.56),'spring':(.65,.57,.35),'reference':(.2,.45,.55),'inherited':(.48,.57,.60),'enclosure':(.78,.81,.84)}
transport=lambda r:r['group'] not in ('enclosure','inherited','reference','external_foot')
def ass(name,pred,mode='closed'):
 a=cq.Assembly(name=name)
 for i,r in enumerate(instances):
  if pred(r):a.add(place(r,mode),name=f'{i:03d}_{r["name"]}',color=cq.Color(*colors.get(r['group'],(.66,.69,.73))))
 a.save(str(R/'cad/assemblies'/f'{name}.step'))
ass('ZL80_G3_FourRoller_Assembly',transport)
ass('ZL80_G3_FourRoller_Released',transport,'open')
ass('ZL80_G3_FourRoller_Exploded',transport,'exploded')
ass('ZL80_G3_Integrated_Context',lambda r:r['group']!='reference')
ass('ZL80_G3_Case_Base',lambda r:r['group'] in ('enclosure','base'))
ass('ZL80_G3_Core_Review',lambda r:r['group'] not in ('enclosure','reference'))

# Machine-readable shape checks, mesh cache only for rendering, never as manufacturing authority.
meshes={}
for pid,s in parts.items():
 verts,tris=s.tessellate(.3,.18)
 meshes[pid]={'vertices':[[v.x,v.y,v.z] for v in verts],'triangles':[list(t) for t in tris]}
for r in instances:
 s=place(r);b=s.BoundingBox();r['aabb']=[b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax]
(R/'cad/parts.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2))
(R/'cad/instances.json').write_text(json.dumps(instances,ensure_ascii=False,indent=2))
(R/'cad/mesh_cache.json').write_text(json.dumps(meshes,separators=(',',':')))
# Export flat cut profiles; circles and contours, no dimensions hidden in manufacturing DXF.
def dxf(pid,outline,holes,rectholes=[]):
 d=ezdxf.new('R2010');d.units=4;m=d.modelspace();d.layers.new('CUT');d.layers.new('HOLES');d.layers.new('NOTES')
 m.add_lwpolyline(outline,close=True,dxfattribs={'layer':'CUT'})
 for x,y,diam in holes:m.add_circle((x,y),diam/2,dxfattribs={'layer':'HOLES'})
 for x,y,w,h in rectholes:m.add_lwpolyline([(x-w/2,y-h/2),(x+w/2,y-h/2),(x+w/2,y+h/2),(x-w/2,y+h/2)],close=True,dxfattribs={'layer':'CUT'})
 m.add_text(pid+' REVIEW ONLY / mm',dxfattribs={'height':3,'layer':'NOTES'}).set_placement((0,-12))
 d.saveas(str(R/'drawings/dxf'/f'{pid}_cut_review.dxf'))
bh={}
for e in base.Edges():
 if e.geomType()=='CIRCLE':
  c=e.Center();rr=e.radius()
  if abs(c.z-3)<.01:bh[(round(c.x,4),round(c.y,4))]=round(rr*2,4)
dxf('G3-M01',[(-150,-144),(150,-144),(150,144),(-150,144)],[(x,y,d) for (x,y),d in bh.items()])
(R/'engineering/base_holes_top.json').write_text(json.dumps([{'x':x,'y':y,'diameter':d} for (x,y),d in sorted(bh.items())],indent=2))
for pid in ['G3-H01','G3-H02']:
 rects=[(0,110,86,5)]
 if pid=='G3-H02':rects += [(-115,70,40,40),(-110,40,24,14)]
 dxf(pid,[(-160,1.5),(160,1.5),(160,298.5),(-160,298.5)],[(x,z,3.4) for x in (-154,154) for z in (20,150,280)],rects)
for pid in ['G3-H03','G3-H04']:
 holes=[(y,z,3.4) for y in (-144,144) for z in (20,150,280)]
 if pid=='G3-H04':holes += [(110,42,12.2)]
 dxf(pid,[(-148.5,1.5),(148.5,1.5),(148.5,298.5),(-148.5,298.5)],holes,[(-103,37,64,35)] if pid=='G3-H03' else [])
for pid in ['G3-H05','G3-H06']:
 holes=[(x,y,3.4) for x in (-154,154) for y in (-144,144)]
 if pid=='G3-H06':holes +=[(x,y,4.5) for x in (-132,132) for y in (-120,120)]
 dxf(pid,[(-160,-150),(160,-150),(160,150),(-160,150)],holes)
print(json.dumps({'parts':len(parts),'instances':len(instances),'transport_instances':sum(transport(r) for r in instances),'valid':sum(x['valid'] for x in meta)},ensure_ascii=False))
