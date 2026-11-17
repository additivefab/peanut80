"""ZL80 R5 integration model. mm. B-rep and envelope design; NOT production geometry.
Rebuild: python cad/source/build_cad.py. Dependencies: cadquery, ezdxf.
Coordinate: X fast scan, Y feed, Z up; base bottom z=5, film center z=110.
"""
from pathlib import Path
import cadquery as cq, ezdxf, json, math, csv
R=Path(__file__).resolve().parents[2];O=R/'cad/step';O.mkdir(exist_ok=True,parents=True)
p=json.loads((R/'engineering/parameters.json').read_text());boards=json.loads((R/'electronics/board_definitions.json').read_text())
parts={};meta=[];inst=[];reserved=[]
def box(x,y,z):return cq.Workplane('XY').box(x,y,z).val()
def tr(s,v):return s.translate(cq.Vector(*v))
def cyl(r,l,a='z',c=(0,0,0)):
 d={'x':(1,0,0),'y':(0,1,0),'z':(0,0,1)}[a];q=[c[i]-d[i]*l/2 for i in range(3)]
 return cq.Solid.makeCylinder(r,l,cq.Vector(*q),cq.Vector(*d))
def reg(i,n,s,mat='6061-T6',status='自制名义几何',note='未冻结加工公差/表面处理/完整紧固'):
 parts[i]=s;b=s.BoundingBox();m=dict(id=i,name=n,material=mat,status=status,note=note,dimensions=[round(b.xlen,4),round(b.ylen,4),round(b.zlen,4)],volume_mm3=s.Volume(),valid=s.isValid());meta.append(m)
 cq.exporters.export(s,str(O/(i+'.step')))
 return i
def at(i,n,pos,g,rot=None):inst.append(dict(part=i,name=n,position=list(pos),group=g,rotation=rot))
def reserve(i,n,c,d,kind):reserved.append(dict(id=i,name=n,center=c,size=d,kind=kind))
def drill(s,holes,axis='z',r=1.7,l=20):
 for c in holes:s=s.cut(cyl(r,l,axis,c))
 return s
# Base, side frames and optical supports.
s=box(300,280,6)
holes=[(x,y,0) for x in (-138,138) for y in (-128,128)]+[(x,y,0) for x in (-72,72) for y in (-55,55)]+[(x,y,0) for x in (-48,48) for y in (-30,30)]
for b in boards:
 if b['plane']=='XY':
  ox,oy,oz=b['origin'];oy=-138 if b['id']=='B09' else oy
  for hx,hy in b['holes']:holes.append((ox+hx,oy+hy,0))
s=drill(s,holes);reg('M01','共同基准底板300×280×6',s);at('M01','Base',[0,0,8],'structure')
f=box(6,128,132)
for y in (-42,42):
 f=f.cut(cyl(6,10,'x',(0,y,99.9-77)))
 f=f.cut(tr(box(10,18,26),(0,y,120.1-77)))
 f=f.cut(cyl(3.2,20,'z',(0,y,136.05-77)))
# lower central opening provides no hidden load-bearing claim; side feet remain.
f=f.cut(tr(box(10,72,65),(0,0,-25)))
reg('M02','片道侧框含轴承孔与上辊浮槽',f);at('M02','FrameL',[-72,0,77],'structure');at('M02','FrameR',[72,0,77],'structure')
reg('M03','20mm辊芯与6mm轴',cyl(7,100,'x').fuse(cyl(3,176,'x')),'不锈钢');reg('M04','20mm可换胶辊套',cyl(10,100,'x').cut(cyl(7,102,'x')),'PU50A试样/硅胶候选','材料DOE件','不得以材料名宣称无划伤；动态轮径需校准')
reg('M05','6×12×4轴承包络',cyl(6,4,'x').cut(cyl(3,6,'x')),'轴承钢','MR126尺寸族候选','精度/密封/预载/游隙需定型')
reg('M06','上辊浮动轴承滑块',box(12,18,18).cut(cyl(6,16,'x')))
for y in (-42,42):
 for z in (99.9,120.1):
  at('M03',f'Roller_core_{y}_{z}',[0,y,z],'transport');at('M04',f'Roller_rubber_{y}_{z}',[0,y,z],'rubber')
  for x in (-72,72):at('M05',f'Bearing_{x}_{y}_{z}',[x,y,z],'transport')
 for x in (-72,72):at('M06',f'Floating_{x}_{y}',[x,y,120.1],'transport')
reg('M07','上辊调压横盖',drill(box(24,26,5),[(0,0,0)],r=2.1),'6061-T6')
reg('M08','压簧安装包络',cyl(3,13.9).cut(cyl(1.5,16)),'弹簧钢','按0.2-1N张力DOE选型','实体环是弹簧外廓，不是弹簧制造模型')
for x in (-72,72):
 for y in (-42,42):at('M07',f'Springcap_{x}_{y}',[x,y,145.5],'structure');at('M08',f'Spring_{x}_{y}',[x,y,136.05],'transport')
reg('M09','近扫描线低摩擦支承条',box(84,2,.5),'表面保护材料DOE');
for y in (-5,5):at('M09',f'Scan_support_{y}',[0,y,109.65],'transport')
reg('M10','可调边导块',box(3,25,3),'PEEK/POM试片','自制试验几何','不挤占80mm通道；片边保护实测')
for x in (-43,43):
 for y in (-90,90):at('M10',f'Guide_{x}_{y}',[x,y,111.5],'transport')
reg('M11','牵引柔性联轴器外廓',cyl(8,16,'x').cut(cyl(3,18,'x')),'采购','16OD×16L规格限界','6→5mm孔径正式采购确认');at('M11','Coupling',[88,42,99.9],'transport')
# Motor candidate body (shaft geometry separate, procurement shaft detail not final).
mot=box(26,35.2,35.2).fuse(cyl(11,2,'x',(-14,0,0))).fuse(cyl(2.5,18,'x',(-24,0,0)))
reg('P01','14HS10-0404S电机本体外廓',mot,'采购','厂家本体+轴长限界','安装孔4-M3 26mm方距应向厂家二次确认');at('P01','Capstan_motor',[122,42,99.9],'motor')
br=box(5,48,48).cut(cyl(11.2,8,'x'))
for y in (-13,13):
 for z in (-13,13):br=br.cut(cyl(1.7,10,'x',(0,y,z)))
reg('M12','电机安装法兰',br);at('M12','Motor_flange',[106.5,42,99.9],'structure')
# Encoder is an envelope placed with the shaft center correctly offset from external rectangle.
reg('P02','AMT112S编码器外廓',tr(box(10.34,28.58,37.25),(0,0,-3.295)),'采购','厂家外廓；无内部结构','15.33mm上边距；包含轴孔视觉标志，不是完整厂家STEP')
for y in (-42,42):at('P02',f'Encoder_{y}',[-98,y,99.9],'sensor')
reg('M13','编码器安装板',box(3,36,46).cut(cyl(7.8,7,'x')))
for y in (-42,42):at('M13',f'Encoder_mount_{y}',[-90,y,99.9],'structure')
# Collector / cylinder X-axis, side window -Y.
zc=p['cavity_center_z'];shell=cyl(26,126,'x').cut(cyl(23.5,128,'x'))
shell=shell.fuse(tr(box(114,14,3),(0,0,24.5))).fuse(tr(box(22,8,20),(0,-26,0))).cut(cyl(23.5,128,'x'))
shell=shell.cut(tr(box(110,6,14),(0,0,26))).cut(tr(box(8.4,22,10.4),(0,-26,0)))
for deg in range(0,360,60):
 yy=24.75*math.cos(math.radians(deg));zz=24.75*math.sin(math.radians(deg))
 for xx in (-60,60):shell=shell.cut(cyl(.8,6,'x',(xx,yy,zz)))
reg('C01','横置狭缝积分筒壳',shell,note='顶部104mm薄唇；侧窗8×10；两端均封闭');at('C01','Cavity_shell',[0,0,zc],'collector')
liner=cyl(23.4,120,'x').cut(cyl(20,122,'x')).cut(tr(box(110,6,14),(0,0,25))).cut(tr(box(8,15,10),(0,-22,0)))
reg('C02','一体漫反射内胆',liner,'光学级烧结PTFE候选','试制几何','首落点轨迹无接缝/胶线/补漆；位置响应待测');at('C02','Liner',[0,0,zc],'liner')
cap=cyl(29,4,'x',(2,0,0)).fuse(cyl(23.45,1.5,'x',(-.75,0,0)))
for a in range(0,360,60):cap=cap.cut(cyl(1.1,8,'x',(1,24.75*math.cos(math.radians(a)),24.75*math.sin(math.radians(a)))))
reg('C03','两端封闭端盖',cap)
at('C03','Cap_R',[63,0,zc],'collector');at('C03','Cap_L',[-63,0,zc],'collector',[[0,0,1],180])
reg('C04','漫反射端衬',cyl(23.4,1.5,'x'),'光学漫反射试样')
for x in (-60.75,60.75):at('C04',f'End_liner{x}',[x,0,zc],'liner')
lip=box(114,14,.3).cut(box(104,1.2,2));lip=drill(lip,[(x,y,0) for x in (-55,55) for y in (-5,5)],r=.85,l=3)
reg('C05','104×1.2矩形薄唇片',lip,'不锈钢消光','名义几何','薄唇0.3；片面至唇口0.5；毛刺/反射须实测');at('C05','Slot_lip',[0,0,109.25],'collector')
pl=cq.Plane(origin=(0,0,0),xDir=(1,0,0),normal=(0,-1,0))
guide=cq.Workplane(pl).rect(8,10).workplane(offset=32).rect(5.2,5.2).loft().val()
reg('C06','矩形锥形PMMA导光件',guide,'光学PMMA','R5耦合试样','入口8×10；出口5.2×5.2；L32；出端到φ8PMT窗口0.4间隙；效率未验证');at('C06','Taper_lightguide',[0,-23.4,zc],'glass')
sleeve=box(22,23.3,12.4).cut(box(9.4,26,11.4))
reg('C07','导光遮光套/空气间隙',sleeve,'消光铝','名义包络','内槽为全长保守让位；仅端部软支承，侧面不灌黑胶');at('C07','Guide_sleeve',[0,-41.85,zc],'collector')
ad=box(26,3,29).cut(cyl(5.4,6,'y'))
for x in (-7,7):
 for z in (-7,7):ad=ad.cut(cyl(1.1,7,'y',(x,0,z)))
reg('C08','PMT窗口接口法兰',ad,note='14×14孔距4×M2，来自H10720配件螺孔；深度3mm不得超入');at('C08','PMT_flange',[0,-55.8,zc],'collector')
saddle=box(12,70,44.1).cut(cyl(26,16,'x',(0,0,50.05)))
# saddle bottom at base top11; top55.1; cut cylinder lower edge≈24.05 local: shallow saddle support.
# Define correct saddle center and cutter based on zc.
sc=36.05;saddle=box(12,70,50.1).cut(cyl(26,16,'x',(0,0,zc-sc)))
for y in (-30,30):saddle=saddle.cut(cyl(1.7,60,'z',(0,y,0)))
reg('C09','积分筒鞍座',saddle)
for x in (-48,48):at('C09',f'Saddle_{x}',[x,0,sc],'structure')
reg('C10','可拆遮直视挡片A/B',box(50,.8,22),'漫反射材料','仅变体/不装入基线','新增实验件；只定义几何，不保证均匀性')
# PMT real orientation: 50 X, 18 Y, 25 Z. Window 11mm from X left edge.
pmt=tr(box(50,18,25),(14,0,0)).fuse(cyl(5,1.5,'y',(0,9.75,0)))
reg('P03','H10720-20本体含凸窗',pmt,'采购','厂家机械尺寸外廓','有效光阴极φ8；引脚单独建模；不可把25mm外壳当有效面');at('P03','PMT',[0,-66.3,zc],'pmt')
reg('P04','PMT引脚空间',cyl(.5,12,'y'),'采购','引脚外廓','8针位置由数据表名义布局转录；原理图/PCB须二次核对镜像')
# rows from manufacturer's bottom view, outward viewing transform must be reverified before fabrication.
pp=[(1,4.68,7.62),(2,40.24,7.62),(3,45.32,7.62),(8,4.68,-7.62),(7,17.38,-7.62),(6,22.46,-7.62),(5,40.24,-7.62),(4,45.32,-7.62)]
for pin,x,z in pp:at('P04',f'PMT_pin_{pin}',[x-11,-81.3,zc+z],'pmt_pin')
sh=box(96,46,54).cut(box(93,43,51)).cut(tr(box(28,5,31),(-18,22,zc-75)))
# B01 rear mounting holes and spacer bodies, not floating circuitry.
for xx in (-24,60):
 for zz in (53,97):sh=sh.cut(cyl(1.7,5,'y',(xx-18,-22,zz-75)))
reg('EP_VERT','B01垂直支柱L6.7',cyl(3,6.7,'y').cut(cyl(1.6,8,'y')),'黄铜','采购尺寸')
for xx in (-24,60):
 for zz in (53,97):at('EP_VERT',f'AFE_post_{xx}_{zz}',[xx,-95.15,zz],'mount_hardware')
reg('H01','PMT与AFE接地屏蔽舱',sh,'铝1.5','名义屏蔽几何','外部不引出HV；前端窗口接缝需遮光；通风不直吹光学区');at('H01','Analog_shield',[18,-77,75],'shield')
# Optical platform.
reg('M14','上部基准支承柱',box(12,14,91))
for x in (-72,72):at('M14',f'Optic_post{x}',[x,65,188.5],'structure')
reg('M15','光学后横梁',box(228,20,6));at('M15','Optics_backbone',[-32,64,237],'structure')
reg('M16','激光器悬臂托板',box(34,90,5));at('M16','Laser_cantilever',[-120,25,231.5],'structure')
lmount=box(32,22,12).cut(cyl(6.1,40,'x',(0,0,5)))
reg('M17','激光头夹座',lmount);at('M17','Laser_mount',[-120,0,240],'structure')
reg('O01','635nm激光头RFQ限界',cyl(6,50,'x'),'采购','RFQ占位','波长/功率/APC/TTL接口待正式型号');at('O01','Laser',[-120,0,245],'optics')
reg('O02','准直整形组件RFQ限界',cyl(8,16,'x'),'采购','RFQ光学包络');at('O02','Beam_shaper',[-82,0,245],'glass')
reg('O03','ND与参考分光组件限界',box(14,18,18),'采购','光学功能包络','参考取样在衰减之后');at('O03','ND_pickoff',[-62,0,245],'optics')
reg('O04','失电关闭机械快门限界',box(18,24,24).cut(cyl(3,22,'x')),'采购','RFQ机械快门','硬件关断和机械快门双路径；该模型不表示快门运动片');at('O04','Shutter',[-43,0,245],'optics')
pts=[(20*math.cos(math.radians(-165+60*i)),20*math.sin(math.radians(-165+60*i))) for i in range(6)]
poly=cq.Workplane('XZ').polyline(pts).close().extrude(6,both=True).val()
reg('O05','六面polygon光学外廓',poly,'厂家精密反射转子','示意/不得按此生产高速件','高速转子的动平衡/防爆罩/轴承由供应商负责');at('O05','Polygon',[12.247,0,257.247],'optics')
reg('O06','Polygon主轴电机限界',cyl(18,40,'y'),'采购','RFQ占位');at('O06','Polygon_motor',[12.247,32,257.247],'motor')
reg('M18','主轴支承座',box(44,16,24).cut(cyl(18.2,20,'y',(0,0,10))))
at('M18','Spindle_cradle',[12.247,42,247.247],'structure')
reg('O07','f-theta扫描镜组RFQ限界',box(96,44,30),'采购','光学RFQ占位','EFL100不等于工作距；本图光程须由供应商处方关闭');at('O07','Ftheta',[0,0,210],'glass')
reg('M19','扫描镜组安装框',box(110,60,6).cut(box(96.4,44.4,10)));at('M19','Lens_frame',[0,0,198],'structure')
for sign in (-1,1):
 pid='M20L' if sign<0 else 'M20R'
 arm=box(24,48,6).cut(tr(box(12,14,10),(sign*8,19,0)))
 reg(pid,'镜组框连接臂',arm)
 at(pid,f'Lens_arm{sign*64}',[sign*64,46,204],'structure')
# sensors optical packages/entry/exit; reservations track mating and film beam gaps.
reg('S01','片外SOS/EOS接收头限界',cyl(3,8,'y'),'采购','S5971封装限界','不表示内部光学器件和比较器抖动')
for x in (-46,46):at('S01',f'PD_sync{x}',[x,12,112],'sensor')
at('S01','PD_reference',[-62,-24,245],'sensor')
reg('S02','片外取样折转片',box(2,3,.7),'消光支架+小镜片','光路接口示意')
for x in (-46,46):at('S02',f'Sync_pickoff{x}',[x,0,112],'optics',[[1,0,0],45])
reg('S03','进出片对射头限界',box(15,10,8),'采购','RFQ传感器','不能按透射强弱单独判双张；ROI时禁止IR发射')
for x,y in [(-25,-110),(25,-110),(0,110)]:
 for z in (102,118):at('S03',f'Film_sensor_{x}_{y}_{z}',[x,y,z],'sensor')
reg('S04','机械互锁开关限界',box(16,8,12),'采购','NC开关RFQ限界','安装操动/冗余/失效分析未认证')
for x in (-145,145):at('S04',f'Lid_switch{x}',[x,100,278],'sensor')
at('S04','Roller_release_switch',[95,-42,147],'sensor')
reg('S05','温度小板限界',box(10,12,1.6),'PCB','TMP117安装区')
for name,pos in [('PMT',[48,-75,82]),('Optics',[72,57.2,220]),('Drive',[-115,50,46])]:at('S05','Temp_'+name,pos,'electronics',[[1,0,0],90] if name=='Optics' else None)
# Board shapes, mount posts, and component-side reservations.
# Each PCB post reaches from datum z=11 to the underside of its board.
post_ids={}
for b in boards:
 w,h,t=b['size'];shape=box(w,h,t)
 for x,y in b['holes']:shape=shape.cut(cyl(b['mount_dia']/2,6,'z',(x-w/2,y-h/2,0)))
 reg(b['id'],b['name'],shape,'FR4' if b['layers'] else '6061-T6',b['status'],b['notes'])
 ox,oy,oz=b['origin']
 if b['id']=='B09':oy=-138;b['origin'][1]=oy
 if b['plane']=='XY':
  pos=[ox+w/2,oy+h/2,oz];rot=None
  ph=oz-t/2-11
  key=round(ph,2);pid='EP_'+str(key).replace('.','p')
  if pid not in parts:reg(pid,'M3支柱L'+str(key),cyl(3,ph).cut(cyl(1.6,ph+2)),'黄铜','采购尺寸')
  for n,(x,y) in enumerate(b['holes']):at(pid,f'{b["id"]}_post{n}',[ox+x,oy+y,11+ph/2],'mount_hardware')
  reserve(b['id']+'_KO',b['name']+'器件高/焊脚净空',[ox+w/2,oy+h/2,oz+(b['top']-b['bottom'])/2],[w,h,t+b['top']+b['bottom']],'board_assembly')
 else:
  pos=[ox+w/2,oy,oz+h/2];rot=[[1,0,0],90]
  sign=1 if b['normal']=='+Y' else -1
  reserve(b['id']+'_KO',b['name']+'装联净空',[ox+w/2,oy+sign*(b['top']-b['bottom'])/2,oz+h/2],[w,t+b['top']+b['bottom'],h],'board_assembly')
 at(b['id'],b['name'],pos,'electronics',rot)
# SP2 actual mechanical drawing is missing. This conservative envelope is not falsely called a model.
reg('P05','SP2模块安装限界110×60×25',box(110,60,25),'采购实物','待实测包络','照片只确认V1.3B；此形状不表示厂家实际PCB孔位');at('P05','SP2_envelope',[90,-103,32.5],'purchased_envelope')
reserve('KO_SP2_IO','SP2外接RJ45/USB插拔空间',[147,-103,37],[30,62,35],'external_service')
reserve('KO_ADC','ADC/FPGA转接净空',[106,-59,34],[54,31,12],'connector')
reserve('KO_PMT','PMT窗口/AFE维护拆出空间',[18,-125,80],[100,50,65],'service_only')
reserve('KO_OPTICS','镜组焦距调节±15和工具',[0,0,210],[112,64,62],'adjustment')
# Externally coupled feeders. Not loaded into base host assembly.
reg('A01','外置馈片模块接口占位',box(250,300,330),'外置附件','功能/空间接口，未完成分片细节','30片仅PoC上限假设；不纳入主机包络/质量');at('A01','External_ADF',[0,-340,165],'optional_external')
reg('A02','外置进出片托板',box(86,80,2),'铝+可换保护衬')
for y in (-190,190):at('A02',f'Tray{y}',[0,y,108.9],'external')
# Sheet metal case front / rear feed apertures, access panels. PDR seams not bent manufacture flats.
fr=box(320,2,300).cut(tr(box(86,5,5),(0,0,-40)))
# Service apertures are part of the integration envelope; supplier connector patterns remain gated.
front=fr.cut(cyl(4.1,6,'y',(-100,0,10)))
for xx in (-70,-60,-50):front=front.cut(cyl(2.6,6,'y',(xx,0,10)))
reg('H02','前面板/片口/按钮/三状态灯',front,'铝2mm','接口名义板','状态灯硬件安装口；光泄漏须实测');at('H02','Front_panel',[0,-149,150],'enclosure')
rear=fr.cut(tr(box(40,6,40),(-115,0,-80))).cut(tr(box(24,6,14),(-110,0,-110)))
reg('H02R','后面板/片口/电子舱通风/ADF接口',rear,'铝2mm','接口名义板','风口需遮光风道；外部ADF接口不得直达FPGA');at('H02R','Rear_panel',[0,149,150],'enclosure')
right=box(2,296,300).cut(tr(box(6,64,35),(0,-103,-113)))
left=box(2,296,300).cut(cyl(6.1,6,'x',(0,110,-108)))
reg('H03','右检修板及SP2连接器可换开窗',right,'铝2mm','名义板','64×35检修口加可换遮光接口片；真实接口孔位待量测SP2')
reg('H03L','左检修板及24V锁紧电源入口',left,'铝2mm','名义板','φ12.2安装限界；最终连接器料号须冻结')
at('H03','Side_panelR',[159,0,150],'enclosure');at('H03L','Side_panelL',[-159,0,150],'enclosure')
reg('H04','顶盖',box(316,296,2),'铝2mm','名义板');at('H04','Top',[0,0,299],'enclosure')
reg('H05','底盖',box(316,296,2),'铝2mm','名义板');at('H05','Bottom',[0,0,1],'enclosure')
reg('H06','脚垫',cyl(8,8),'弹性体','采购')
for x in (-138,138):
 for y in (-128,128):at('H06',f'Foot_{x}_{y}',[x,y,-4],'external')
reg('H07','散热风扇/风道限界',box(40,10,40),'采购','40mm风扇RFQ占位','只吹电子舱；粉尘不能直接进入片道和积分筒');at('H07','Fan',[-115,135,70],'electronics')
reg('H08','前后遮光迷宫框',box(94,30,16).cut(box(86,32,5)),'消光铝','遮光外形起点','仍需无片/片尾/翘曲激光泄漏评估')
for y in (-132,132):at('H08',f'Labyrinth{y}',[0,y,110],'shield')
# updated board coordinate persisted for all drawings/calculations
(R/'electronics/board_definitions.json').write_text(json.dumps(boards,ensure_ascii=False,indent=2))
colors={'structure':(.67,.7,.73),'transport':(.56,.60,.63),'rubber':(.17,.19,.21),'collector':(.62,.67,.7),'liner':(.94,.94,.89),'glass':(.3,.72,.83),'pmt':(.16,.18,.21),'pmt_pin':(.76,.72,.5),'optics':(.36,.43,.51),'motor':(.17,.20,.22),'sensor':(.25,.43,.58),'electronics':(.13,.42,.33),'shield':(.58,.64,.68),'purchased_envelope':(.22,.39,.35),'mount_hardware':(.65,.54,.3),'enclosure':(.82,.85,.87),'external':(.55,.61,.66),'optional_external':(.35,.55,.7)}
def placed(row,exp=False):
 s=parts[row['part']]
 if row['rotation']:axis,ang=row['rotation'];s=s.rotate((0,0,0),axis,ang)
 v=list(row['position'])
 if exp:
  if row['group']=='enclosure':
   if row['part']=='H04':v[2]+=80
   elif row['part'] in ('H02','H02R'):v[1]+=80*(1 if v[1]>0 else -1)
   elif row['part'] in ('H03','H03L'):v[0]+=90*(1 if v[0]>0 else -1)
  elif row['group'] in ['optics','glass'] and v[2]>170:v[2]+=50
  elif row['group']=='electronics':v[0]+=55*(1 if v[0]>0 else -1)
 return tr(s,v)
placed_shapes=[placed(r) for r in inst]
for row,s in zip(inst,placed_shapes):
 b=s.BoundingBox();row['aabb']=[b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax]
def assembly(name,pred,explode=False):
 a=cq.Assembly(name=name)
 for n,r in enumerate(inst):
  if pred(r):a.add(placed(r,explode),name=f'{n:03d}_{r["part"]}_{r["name"][:32]}',color=cq.Color(*colors[r['group']]))
 a.save(str(O/(name+'.step')))
 return a
corepred=lambda r:r['group'] not in ('enclosure','external','optional_external')
assembly('ZL80_R5_assembly',lambda r:r['group'] not in ('external','optional_external'))
assembly('ZL80_R5_core',corepred)
assembly('ZL80_R5_exploded',lambda r:r['group'] not in ('external','optional_external'),True)
assembly('ZL80_R5_collector',lambda r:r['part'].startswith('C') or r['part'] in ('P03','P04','H01','B01'))
assembly('ZL80_R5_transport',lambda r:r['group'] in ('transport','rubber') or r['part'] in ('P01','P02','M02','M12','M13'))
assembly('ZL80_R5_electronics',lambda r:r['group'] in ('electronics','purchased_envelope') or r['part'] in ('P03','H01'))
# Envelopes isolated from physical assembly; no pretend "all boxes fit" Boolean claims.
env=cq.Assembly(name='R5_reserved_spaces')
for q in reserved:env.add(tr(box(*q['size']),q['center']),name=q['id'],color=cq.Color(.9,.55,.18,.25))
env.save(str(O/'ZL80_R5_keepouts.step'))
# Surface meshes for reproducible engineering renders, no renderer/external assets required.
meshes=[]
for r,s in zip(inst,placed_shapes):
 if r['group']=='optional_external':continue
 vs,fs=s.tessellate(.65,.25)
 meshes.append(dict(id=r['part'],name=r['name'],group=r['group'],vertices=[[v.x,v.y,v.z] for v in vs],faces=[list(f) for f in fs],color=colors[r['group']]))
(R/'cad/render_meshes.json').write_text(json.dumps(meshes,separators=(',',':')))
(R/'cad/parts.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2));(R/'cad/instances.json').write_text(json.dumps(inst,ensure_ascii=False,indent=2));(R/'cad/keepouts.json').write_text(json.dumps(reserved,ensure_ascii=False,indent=2))
# DXF: authoritative nominal profiles for newly designed plate outlines.
def dxf(name,loops,holes=[],notes='R5-PDR NOMINAL mm - NO MANUFACTURING RELEASE'):
 d=ezdxf.new('R2010');d.units=4;m=d.modelspace()
 for a in loops:m.add_lwpolyline(a,close=True)
 for x,y,rr in holes:m.add_circle((x,y),rr)
 m.add_text(notes,dxfattribs={'height':2.5}).set_placement((0,-12))
 d.saveas(R/'cad/dxf'/f'{name}.dxf')
def rect(w,h):return [(0,0),(w,0),(w,h),(0,h)]
dxf('M01_base',[rect(300,280)],[(x+150,y+140,1.7) for x,y,z in holes])
dxf('C05_slit',[rect(114,14),[(5,6.4),(109,6.4),(109,7.6),(5,7.6)]],[(x,y,.85) for x in (2,112) for y in (2,12)])
for b in boards:dxf(b['id']+'_outline',[rect(*b['size'][:2])],[(x,y,b['mount_dia']/2) for x,y in b['holes']])
# Analytical broad phase + OCC intersection. Inventory all overlaps, distinguish intended mates from open issues.
checks=[]
core=[(r,s) for r,s in zip(inst,placed_shapes) if corepred(r)]
for i,(a,sa) in enumerate(core):
 for b,sb in core[i+1:]:
  aa=a['aabb'];bb=b['aabb'];ov=[min(aa[k+3],bb[k+3])-max(aa[k],bb[k]) for k in range(3)]
  if min(ov)<=1e-5:continue
  # actual B-rep intersection; sampling or AABB is not labelled a full collision test.
  try:v=sa.intersect(sb).Volume()
  except Exception:v=None
  if v is None or v>.01:
   checks.append(dict(a=a['name'],b=b['name'],a_part=a['part'],b_part=b['part'],volume_mm3=v,classification='REVIEW'))
(R/'tests/cad_overlap_raw.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
(R/'tests/cad_validity.json').write_text(json.dumps(dict(parts=len(meta),instances=len(inst),all_valid=all(x['valid'] for x in meta),scope='B-rep validity and rigid nominal core intersections only; excludes tolerances, cables, fasteners and optics performance',raw_overlap_count=len(checks)),indent=2))
print('CAD',len(meta),'parts',len(inst),'instances','overlaps',len(checks));print(json.dumps(checks,ensure_ascii=False,indent=2)[:10000])
