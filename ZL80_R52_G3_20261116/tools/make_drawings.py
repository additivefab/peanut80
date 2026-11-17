"""Reproducible CAD-derived review drawings (not AI raster concept art)."""
from pathlib import Path
import json,math,io
import numpy as np
from PIL import Image,ImageDraw
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor,Color
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
import cadquery as cq
import ezdxf
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
R=Path(__file__).resolve().parents[1];P=json.loads((R/'config/mechanical_parameters.json').read_text());M=json.loads((R/'cad/mesh_cache.json').read_text());I=json.loads((R/'cad/instances.json').read_text());D=json.loads((R/'engineering/registers.json').read_text())
pdfmetrics.registerFont(TTFont('CJK','/usr/share/fonts/truetype/arphic/uming.ttc',subfontIndex=0))
NAVY='#173D60';GRAY='#52606D';TEAL='#147D86';RED='#A33A32'

def matrix(axis,ang):
 a=np.array(axis,float);a=a/np.linalg.norm(a);x,y,z=a;c=math.cos(math.radians(ang));ss=math.sin(math.radians(ang));C=1-c
 return np.array([[c+x*x*C,x*y*C-z*ss,x*z*C+y*ss],[y*x*C+z*ss,c+y*y*C,y*z*C-x*ss],[z*x*C-y*ss,z*y*C+x*ss,c+z*z*C]])

def preview(name,pred,mode='closed',view='iso'):
 tris=[];allv=[]
 if view=='iso':
  horiz=np.array([.82,-.57,0]);vert=np.array([.28,.4,.87]);vert=vert/np.linalg.norm(vert)
 else:horiz=np.array([0,1,0]);vert=np.array([0,0,1])
 depth=np.cross(horiz,vert);light=np.array([-.3,-.5,1]);light/=np.linalg.norm(light)
 for r in I:
  if not pred(r):continue
  v=np.array(M[r['part']]['vertices']);t=np.array(M[r['part']]['triangles'])
  if r['rotation']:v=v@matrix(*r['rotation']).T
  pos=np.array(r['position'],float)
  if mode=='exploded':
   if r['moves_with_upper']:pos[2]+=45
   if r['group'] in ['bearing','bearing_cap','encoder','encoder_mount']:pos[0]+=35*(1 if pos[0]>0 else -1)
   if r['group'] in ['spring','preload']:pos[2]+=65
   if r['group']=='drive':pos[0]+=55
  v+=pos
  proj=np.column_stack([v@horiz,v@vert]);allv.append(proj)
  g=r['group'];base=np.array({'rubber':[65,72,79],'drive':[92,116,138],'encoder':[56,134,139],'spring':[173,151,103],'inherited':[159,177,187],'enclosure':[197,204,209],'fastener':[130,139,147]}.get(g,[162,174,184]))
  vv=v[t];normal=np.cross(vv[:,1]-vv[:,0],vv[:,2]-vv[:,0]);nn=np.linalg.norm(normal,axis=1);nn[nn==0]=1;normal/=nn[:,None]
  shade=.58+.42*np.abs(normal@light)
  for idx,tri in enumerate(t):tris.append((float(vv[idx].mean(axis=0)@depth),proj[tri],tuple((base*shade[idx]).astype(int))))
 a=np.concatenate(allv);lo=a.min(axis=0);hi=a.max(axis=0);W,H=1500,1000;scale=min((W-100)/(hi[0]-lo[0]),(H-100)/(hi[1]-lo[1]));off=(np.array([W,H])-((hi-lo)*scale))/2
 image=Image.new('RGB',(W,H),'white');draw=ImageDraw.Draw(image)
 for dep,xy,col in sorted(tris,key=lambda x:x[0]):
  z=(xy-lo)*scale+off;pts=[(float(xx),H-float(yy)) for xx,yy in z];draw.polygon(pts,fill=col)
 image.save(R/'drawings/png'/name)
 return R/'drawings/png'/name
transport=lambda r:r['group'] not in ('inherited','enclosure','reference','external_foot')
preview('01_FourRoller_Assembly.png',transport)
preview('02_FourRoller_Exploded.png',transport,'exploded')
preview('03_Core_Context.png',lambda r:r['group'] not in ('enclosure','reference','external_foot','fastener'))
preview('04_Case.png',lambda r:r['group'] in ('enclosure','base','external_foot'))
# Drawing helpers
W,H=1190.55,841.89
pdfpath=R/'drawings/ZL80_G3_机械加工与装配图册.pdf';c=canvas.Canvas(str(pdfpath),pagesize=(W,H));page=0;index=[]
def text(x,y,s,size=12,color=GRAY):c.setFillColor(HexColor(color));c.setFont('CJK',size);c.drawString(x,y,str(s))
def lines(x,y,items,size=13,leading=23):
 for i,s in enumerate(items):text(x,y-i*leading,s,size)
def title(code,name,sub='尺寸单位 mm｜审查稿，非加工放行图'):
 global page;page+=1;index.append([code,name,page]);c.setFillColor(HexColor(NAVY));c.rect(0,H-73,W,73,fill=1,stroke=0);text(30,H-35,code+'  '+name,23,'#FFFFFF');text(30,H-58,sub,12,'#DCE8EE')
 c.setStrokeColor(HexColor('#B7C7D3'));c.line(25,53,W-25,53)
 text(27,32,'ZL80 / R52-G3-M01-D01  ·  2026-11-16',11);text(430,32,'CAD名义几何＋建议公差；须供应商确认、DFM与台架验证后放行',11,RED);text(W-100,32,f'{page:02d}',12)
def end():c.showPage()
def note_box(x,y,w,h,title_,items):
 c.setFillColor(HexColor('#F1F6F8'));c.rect(x,y,w,h,fill=1,stroke=0);text(x+12,y+h-24,title_,15,NAVY);lines(x+12,y+h-49,items,11.8,20)
def arrow(x1,y1,x2,y2,col=GRAY):
 c.setStrokeColor(HexColor(col));c.setLineWidth(.7);c.line(x1,y1,x2,y2)
 a=math.atan2(y2-y1,x2-x1);l=6
 for side in (-1,1):c.line(x2,y2,x2-l*math.cos(a+side*.35),y2-l*math.sin(a+side*.35))
def dim(x1,y1,x2,y2,label):
 arrow(x1,y1,x2,y2);arrow(x2,y2,x1,y1);text((x1+x2)/2+4,(y1+y2)/2+6,label,11,NAVY)
def img(path,x,y,w,h):c.drawImage(str(path),x,y,w,h,preserveAspectRatio=True,anchor='c',mask='auto')
def partview(pid,x,y,w,h,proj=(1,-1,1)):
 q=R/'drawings/svg'/f'{pid}_{proj[0]}_{proj[1]}_{proj[2]}.svg'
 if not q.exists():
  sh=cq.importers.importStep(str(R/'cad/parts'/f'{pid}.step')).val()
  q.write_text(cq.exporters.getSVG(sh,opts={'width':w,'height':h,'marginLeft':18,'marginTop':18,'projectionDir':proj,'showHidden':False,'strokeWidth':.6}))
 dr=svg2rlg(str(q));dr.scale(w/dr.width,h/dr.height);renderPDF.draw(dr,c,x,y)
def table(x,y,headers,rows,widths,rowh=27,size=10.5):
 total=sum(widths);c.setFillColor(HexColor(NAVY));c.rect(x,y-rowh,total,rowh,fill=1,stroke=0)
 xx=x
 for h,wd in zip(headers,widths):text(xx+6,y-rowh+8,h,size,'#FFFFFF');xx+=wd
 for i,row in enumerate(rows):
  yy=y-(i+2)*rowh;c.setFillColor(HexColor('#F0F5F7' if i%2==0 else '#FFFFFF'));c.rect(x,yy,total,rowh,fill=1,stroke=0);xx=x
  for cell,wd in zip(row,widths):text(xx+6,yy+8,str(cell),size);xx+=wd

def draw_dxf(pid,x,y,w,h):
 doc=ezdxf.readfile(R/'drawings/dxf'/f'{pid}_cut_review.dxf');m=doc.modelspace();ents=[];pts=[]
 for e in m:
  if e.dxftype()=='LWPOLYLINE':
   ps=[tuple(v[:2]) for v in e.get_points()];pts+=ps;ents.append(('poly',ps,e.closed))
  elif e.dxftype()=='CIRCLE':
   cx,cy,_=e.dxf.center;rad=e.dxf.radius;pts.extend([(cx-rad,cy-rad),(cx+rad,cy+rad)]);ents.append(('circle',(cx,cy,rad),False))
 lo=np.min(pts,axis=0);hi=np.max(pts,axis=0);scale=min((w-50)/(hi[0]-lo[0]),(h-50)/(hi[1]-lo[1]));ox=x+(w-(hi[0]-lo[0])*scale)/2-lo[0]*scale;oy=y+(h-(hi[1]-lo[1])*scale)/2-lo[1]*scale
 c.setStrokeColor(HexColor(NAVY));c.setLineWidth(.7)
 for typ,data,closed in ents:
  if typ=='circle':cx,cy,rad=data;c.circle(ox+cx*scale,oy+cy*scale,rad*scale,stroke=1,fill=0)
  else:
   path=c.beginPath();path.moveTo(ox+data[0][0]*scale,oy+data[0][1]*scale)
   for xx,yy in data[1:]:path.lineTo(ox+xx*scale,oy+yy*scale)
   if closed:path.close()
   c.drawPath(path,stroke=1,fill=0)
 dim(ox+lo[0]*scale,oy+lo[1]*scale-12,ox+hi[0]*scale,oy+lo[1]*scale-12,f'{hi[0]-lo[0]:g}')
 dim(ox+lo[0]*scale-12,oy+lo[1]*scale,ox+lo[0]*scale-12,oy+hi[1]*scale,f'{hi[1]-lo[1]:g}')
 return ox,oy,scale

# 01-03 assembly explanations from actual CAD
for code,name,png,notes in [
('D01','四辊机构总装／功能边界','01_FourRoller_Assembly.png',['入口：测量随动辊，不承担独立恒张力控制。','出口：单电机牵引；两下辊各有编码器。','80mm有效片宽；100mm辊面；两辊距84。','下辊中心Z99.9；名义0.2mm胶片中心Z110。','光学／电子模型为继承接口，不是本轮定型。','未建模标准件清单见机械BOM末项。']),
('D02','分层拆装／上辊释放','02_FourRoller_Exploded.png',['总装、释放5mm、爆炸三种STEP分别提供。','先断光/停驱动，再两端同步提辊。','弹簧工作长度13.9；释放后8.9。','要求采购弹簧压并长度不超过7.5。','上辊定位：M5螺母＋窄垫片。','下辊轴环移出压盖；旋转扫掠另审。']),
('D03','光机电回装关系／机箱外观','03_Core_Context.png',['继承扫描线X[-40,+40]、Y0、Z110。','积分筒薄唇顶面Z109.4不改动。','板框位置保持；电机脚座避开B02。','基座改300×288，修复B04后孔开边。','G2新元件占位与R5板法向仍须核对。','完整机箱名义包络仍320×300×300。'])]:
 title(code,name);img(R/'drawings/png'/png,25,105,825,620);note_box(860,315,305,380,'装配说明',notes);end()

# 04 side section / correct axes
title('D04','四辊片道纵剖面与接口尺寸')
ox,oy,sc=460,345,4.8
for yy in (-42,42):
 for zz in (99.9,120.1):
  c.setStrokeColor(HexColor(NAVY));c.circle(ox+yy*sc,oy+(zz-100)*sc,10*sc,stroke=1,fill=0)
  c.line(ox+yy*sc-7,oy+(zz-100)*sc,ox+yy*sc+7,oy+(zz-100)*sc)
c.setStrokeColor(HexColor(TEAL));c.setLineWidth(2);c.line(70,oy+9.9*sc,850,oy+9.9*sc)
arrow(320,oy+14*sc,520,oy+14*sc,TEAL);text(350,oy+20*sc,'Y 连续走片',16,TEAL)
c.setStrokeColor(HexColor(NAVY));c.circle(ox,oy+(83.1-100)*sc,26*sc,stroke=1,fill=0)
text(390,oy-155,'横置积分筒：轴线沿X',13)
dim(ox-42*sc,oy-190,ox+42*sc,oy-190,'84.00 ±0.05（候选）')
dim(ox+42*sc+75,oy-.1*sc,ox+42*sc+75,oy+20.1*sc,'20.20名义中心距')
lines(865,660,['下辊φ20，面宽100','胶片厚度：0.15~0.35','上辊释放：+5','名义片底：Z109.9','薄唇顶面：Z109.4','片底到薄唇：0.50','厚度增加会抬高片中心','不能把厚度误差重复加进片底间隙'],14,29)
note_box(60,560,740,110,'重要边界',['此纵剖面沿Y-Z；旋转多面镜横扫沿X，不能画成沿Y扫整条长片。','近扫描线支承条维持片底，狭缝通光区域不放实体辊或整块遮光托板。']);end()

# 05 fixed-floating bearing section
title('D05','轴承定位／游动结构与轴向尺寸链')
# Axial bearing section, global X used for chain; exaggerated radial sizes for readability.
sx=lambda xx:590+xx*5.05
sy=570
c.setStrokeColor(HexColor(NAVY));c.setLineWidth(1)
for aa,bb,dd in [(-105,-74,6),(-74,-70,6),(-70,-50,7.4),(-50,50,14),(50,70,7.4),(70,74,6),(74,91,6)]:
 c.rect(sx(aa),sy-dd*3,(bb-aa)*5.05,dd*6,stroke=1,fill=0)
for xx in (-72,72):
 c.setFillColor(HexColor('#D8E5EE'));c.rect(sx(xx-2),sy-36,4*5.05,72,stroke=1,fill=1)
 c.setFillColor(HexColor('#FFFFFF'));c.rect(sx(xx-2),sy-18,4*5.05,36,stroke=1,fill=1)
text(sx(-74)-12,sy+58,'左固定端',13,NAVY);text(sx(70)-15,sy+58,'右游动端',13,NAVY)
c.setDash(4,3);c.line(sx(-109),sy,sx(95),sy);c.setDash()
dim(sx(-72),sy-70,sx(72),sy-70,'轴承中心距144（全局X±72）')
text(390,sy+95,'轴向剖面示意：径向比例夸大，尺寸以标注及STEP为准',13,NAVY)
lines(55,420,['左：轴肩X=-70 → 轴承(-74~-70) → 窄垫套(-79.1~-74) → 夹紧轴环(-88.1~-79.1)。','右：轴承(70~74)在加长外圈座内游动；轴肩和外圈盖不能同时把轴承压死。','轴承L-1260ZZ：内径6、外径12、宽4；实测游隙与厂家配合建议是冻结前置条件。'],14,31)
table(55,285,['位置','结构目标','验收方式'],[['左外圈','0.02~0.05轴向端隙候选','压盖垫片＋百分表'],['右外圈','0.20~0.50轴向浮动候选','温度范围内推拉检查'],['轴承轴颈','φ6.000~6.004候选','轴承样品/安装力审核'],['外圈座','φ12.000~12.010候选','塞规/量仪'],['轴肩圆角','r<=0.10建议，留退刀位','倒角实物与轴承图确认']],[180,450,380],34,13)
end()

# 06 release
title('D06','上辊浮动、调压与手动释放机构')
partview('G3-M04',45,410,310,260);partview('G3-M10',390,410,310,260);partview('G3-M11',720,410,410,260)
text(95,385,'浮动块8×18×18',15,NAVY);text(435,385,'顶座24×30×10，内有弹簧调节井',15,NAVY);text(770,385,'双端提辊横杆164×8×4',15,NAVY)
lines(55,330,['1. 槽18.150±0.025，滑块18.000±0.025：名义Y间隙0.15；X导板间隙0.10。','2. 压簧自由18／工作13.9／刚度0.5 N/mm：两端弹簧合力4.1 N。','3. 实际法向力还包括上辊移动自重及滑块摩擦，必须用测力传感器校准。','4. 调压顶座的下部φ5.5井允许改变弹簧压缩量；M4压垫隔离螺纹与弹簧。','5. 上辊抬升5时，弹簧工作长度变为8.9；厂家压并长度要求<=7.5。','6. 双端提辊与锁紧方式仍须人体操作/失效验证；释放开关必须先断光与禁驱动。'],14,34)
end()

title('D07','电机—联轴器—牵引辊接口尺寸链')
partview('G3-P08',70,420,380,250,(0,-1,1));partview('G3-P07',490,440,220,210);partview('G3-M12',770,410,330,260)
# Axis chain, horizontal X coordinate at arbitrary drawing scale
sx=lambda a:100+(a-70)*11
c.setStrokeColor(HexColor(NAVY));c.line(sx(70),330,sx(148),330)
for xx,label in [(74,'轴承外侧'),(81,'联轴器左端'),(91,'φ6轴端'),(101,'φ5电机轴端'),(111,'联轴器右端'),(121.5,'电机安装面'),(147.5,'电机后端')]:
 c.line(sx(xx),320,sx(xx),340);text(sx(xx)-30,295 if xx in (74,91,111,147.5) else 365,f'{xx:g}',12,NAVY)
dim(sx(81),245,sx(111),245,'W=30（不是端毂L=10）');dim(sx(121.5),205,sx(147.5),205,'本体26')
lines(65,155,['电机φ5轴长20.5；φ6辊轴与φ5电机轴各插入约10。候选对中：偏心<=0.03、偏角<=0.1°。','NBK允许偏差不能当作装调目标；名义转矩预算0.0451 N·m，仍需电机动态曲线/低速台架确认。'],13,27);end()

title('D08','测量编码器与安装转接板')
partview('G3-P09',40,400,340,280);partview('G3-M14',420,400,340,280);partview('G3-M15',820,430,250,220)
note_box(45,120,1095,225,'位置测量的边界',['AMT112S：原厂0.2°角精度不是4096PPR量化；20mm辊对应约34.91μm位置量级。','四倍频计数步距：π×20／(4096×4)=3.83495μm；不等于实际走片精度。','适配板4孔±16Y、±12Z是自定义接口，不宣称为AMT原厂孔；厂家底座孔与实物必须复核。','5V CMOS A/B/Z不直接接3.3V FPGA；电平转换、屏蔽回流和插头针脚由G2 B05闭合。','启动约200ms保持轴静止；4096PPR须配置，不能默认已是4096。来源S04。']);end()

title('D09','基准底板／激光切割与机加工孔位')
draw_dxf('G3-M01',25,110,770,600)
note_box(820,160,335,535,'底板修订与工艺',['300×288×6；材质6061-T6。','上表面为物理基准A。','旧后排孔Y139在280深底板开边。','本版加深8，保留板卡原坐标。','脚孔改X±132／Y±120。','旧脚孔与B03安装孔过近。','40个顶面孔见下一页坐标表。','框架、脚和电机脚孔φ4.5。','支柱普通孔φ3.4；定位孔φ3。','底部指定孔另有φ8浅沉孔。','M3/M4螺纹用底孔表示，见说明。','普通孔位不是全部精密定位孔。','DXF单位mm，所有图层须核验。']);end()

title('D10','底板孔坐标表／来源到几何的核对')
holes=json.loads((R/'engineering/base_holes_top.json').read_text())
for start,x in [(0,35),(20,625)]:
 table(x,710,['序号','X','Y','孔径'],[[i+1,f'{v["x"]:.3f}',f'{v["y"]:.3f}',f'{v["diameter"]:.2f}'] for i,v in enumerate(holes) if start<=i<start+20],[75,135,135,130],27,12)
text(45,95,'孔表从实际CAD圆孔提取；对顶面完整圆孔计数，不用开边圆弧的质心冒充孔中心。',13,RED);end()

title('D11','片道侧框／CNC加工与定位')
partview('G3-M02',35,270,520,440,(1,0,0));partview('G3-M02',640,330,440,330,(1,-1,1))
lines(630,270,['右框8厚；外形128×126，Z17~143。','左框为X镜像，不可绕Z翻转代替。','轴承中心Y±42，Z99.9。','上浮槽18.15宽，高24.3，中心Z123.05。','顶部弹簧井和提辊孔有方向性。','底部M4底孔与φ3定位孔分别标识。','每框一圆销一菱形销，避免两圆销强装。'],13,27)
text(45,100,'基准A=底板上表面；B/C=主框圆销/菱形销定位特征。胶片名义平面F不是实体加工基准。',13,RED);end()

def roller_page(pid,code,title_,left,right,upper=False):
 title(code,title_)
 x0=90;scale=4.8;xx=lambda x:x0+(x+110)*scale;yy=500
 segments=[(left,-74,5 if upper else 6),(-74,-70,6),(-70,-50,7.4),(-50,50,14),(50,70,7.4),(70,74,6),(74,right,6)]
 c.setStrokeColor(HexColor(NAVY));c.setLineWidth(1)
 for a,b,d in segments:c.rect(xx(a),yy-d/2*scale,(b-a)*scale,d*scale,stroke=1,fill=0)
 c.setDash(5,3);c.line(xx(left)-10,yy,xx(right)+10,yy);c.setDash()
 dim(xx(left),405,xx(right),405,f'总长 {right-left:.1f}')
 dim(xx(-50),575,xx(50),575,'100.00 ±0.05 / φ14包胶芯')
 for a,b,d in segments:
  dim(xx(a),625,xx(b),625,f'{b-a:g}')
 table(55,330,['区域','名义','建议尺寸／工艺','状态'],[['轴承段','φ6×4，中心X±72','6.000~6.004；Ra<=0.4μm候选','须轴承厂家批准'],['肩段','φ7.4×20，各端','端面垂直；r<=0.10；退刀槽DFM','待冻结'],['包胶芯','φ14×100','胶接前处理按已验证工艺','材料DOE'],['外伸段','φ6','5.988~6.000；夹紧处无涂层','采购配合候选'],['左端' if upper else '端部','M5×0.8' if upper else '编码器/联轴器','螺纹与锁紧工艺见装配，不以CAD光杆替代验牙','待冻结']],[135,215,490,240],35,12)
 lines(60,100,['胶辊成品须在已检验轴承基准上磨削；不要将STL用于数控加工。STEP不含真实螺纹牙型。'],12,24);end()
roller_page('G3-R01','D12','入口测量辊芯加工图（候选）',-105,84)
roller_page('G3-R02','D13','出口牵引辊芯加工图（候选）',-105,91)
roller_page('G3-R03','D14','上压辊芯加工图（候选）',-84,84,True)

title('D15','辊轮包胶、磨削与材料放行')
partview('G3-R04',55,430,650,230,(1,-1,1))
note_box(745,380,400,305,'成品工作面',['φ20.000±0.010候选；面长100。','相对两轴承位总跳动<=0.010候选。','两端倒圆，不得割伤片边。','不采用会相对轴旋转的松套。','按两面都需要保护的胶片验证。','胶层变形导致有效滚动直径改变。','无划伤不能由Ra或材料名字证明。'])
lines(60,320,['工序建议：辊芯检验 → 表面处理/底涂验证 → 包胶/硫化 → 后处理 → 基准磨削 → 清洗 → 标识 → 材料DOE。','PU50A、后硫化硅胶50A、防静电PU50A仅为候选；须记录供应商、配方/批次、固化和后硫化记录。','首轮采用光面，不新增网纹变量。材料筛选矩阵18组，每组3片；材料合格后再扩大速度、厚度与张力范围。','每根辊单独标识；测出负载有效径和角周期误差，保留标定版本，不能只量一次自由外径。'],14,40);end()

title('D16','浮动块、压盖与调压顶座零件图')
for pid,x,label in [('G3-M04',35,'8×18×18 浮动块'),('G3-M05',420,'2×24×18 压盖／台阶凸台'),('G3-M10',805,'24×30×10 顶座')]:
 partview(pid,x,390,340,280,(1,-1,1));text(x+25,360,label,14,NAVY)
lines(45,290,['轴承座φ12.000~12.010；轴承通孔φ10.6避让外圈肩；左右压盖轴向尺寸不同。','盖孔为4×φ2.2，自定义孔距Y14×Z14；M2×5有效啮合约2.9mm，铝牙强度/锁固待确认。','顶座：M4调压螺纹底孔；底面φ5.5调节井；M3提辊孔偏置X=-1,Y=+6。左件必须X镜像。','上辊导板24×24×1.5；名义轴向滑动间隙0.10；量测摩擦/卡滞，不能把“无实体重叠”当作运动顺畅。','压盖和脚垫孔位、轴肩、螺纹深度详见STEP与零件附注；未注倒角/表面处理须供应商DFM关闭。'],13.5,37);end()

title('D17','电机支座与防护罩／避让ADC空间')
partview('G3-M12',35,240,610,450,(1,-1,1));partview('G3-M13',760,400,310,250)
lines(670,340,['支座底面Z11，脚厚5。','前部脚让至Y32，避开B02板。','脚孔X130/142、Y36/59，4×φ4.5。','安装面X121.5；4孔26×26名义。','联轴器护罩X80.3~116.4。','采购件夹紧螺钉和护罩固定方式待审。','不运行裸露联轴器或未固定护罩。'],14,30)
text(55,95,'保持型步进电机不是张力伺服。正式运行前，B05限流、故障关断与低速脉动须先通过G2台架。',13,RED);end()

for code,name,pa,pb in [('D18','机箱前后平板／切割图','G3-H01','G3-H02'),('D19','机箱左右检修板／接口片','G3-H03','G3-H04'),('D20','机箱顶底平板／脚孔','G3-H05','G3-H06')]:
 title(code,name)
 draw_dxf(pa,35,230,540,480);draw_dxf(pb,615,230,540,480);text(150,210,pa,16,NAVY);text(745,210,pb,16,NAVY)
 lines(45,150,['材质候选5052-H32，板厚1.5；全为平板激光切割件，不存在未给出的K因子/折弯补偿。','普通外形±0.20、孔位±0.15建议；去毛刺、接地点去涂层、切口保护与遮光迷宫须单独审核。','机箱采用角撑螺接，连接器最终开孔/提手承重/搬运刚度/漏光仍未验证，DXF不是量产下单授权。'],12.5,25);end()

title('D21','线束分区与走线路径／俯视投影')
ox,oy,sc=450,405,1.85
c.setStrokeColor(HexColor('#A8BAC6'));c.rect(ox-160*sc,oy-150*sc,320*sc,300*sc,stroke=1,fill=0)
for yy in (-42,42):c.rect(ox-50*sc,oy+(yy-10)*sc,100*sc,20*sc,stroke=1,fill=0)
c.setFillColor(HexColor('#E8EEF1'));c.rect(ox-57*sc,oy-7*sc,114*sc,14*sc,fill=1,stroke=0)
for j,r in enumerate(D['routes']):
 pts=r['points'];col=[NAVY,TEAL,'#B57238','#6A5583'][j%4];c.setStrokeColor(HexColor(col));c.setLineWidth(1.3)
 for a,b in zip(pts,pts[1:]):c.line(ox+a[0]*sc,oy+a[1]*sc,ox+b[0]*sc,oy+b[1]*sc)
 text(ox+pts[0][0]*sc+5,oy+pts[0][1]*sc+5,r['id'],10,col)
lines(790,690,['W01：模拟差分，PMT/ADC局部','W02：ADC数字转接，长度受控','W03/W04：两路编码器独立束','W05：电机相线走后侧功率通道','W06：SP2供电，禁止误接24V','W07：PMT供电/控制屏蔽','W08：参考PD缓冲输出','W09：SOS/EOS及回流成对','W10：激光硬禁能/快门','W11：24V入口到保护电路','W12：上辊释放NC互锁'],13.5,31)
lines(45,115,['图为三维中心线的XY投影，不证明拐弯半径、接插件朝向或线束干涉通过。三维节点、长度预算见CSV/JSON。','保留USB/JTAG插拔和维修拆出通道；最终针脚表、电平转换由G2闭合，不能按本图直接接线。'],12.5,24);end()

title('D22','装配公差链／片底间隙与焦平面')
s=D['summary'];table(45,710,['项','半宽 / mm','符号系数','来源'],[[r[0],f'{r[2]:.3f}',r[3],r[1]] for r in D['stack']],[355,160,150,430],40,12)
lines(55,410,[f"片底间隙 = 下辊中心99.9 + 加载半径10 - 薄唇顶面109.4 = 0.500 mm。",f"最坏值叠加 ±{s['gap_stack_wc_mm']:.3f} mm → [{s['gap_min_candidate_mm']:.3f}, {s['gap_max_candidate_mm']:.3f}] mm。",f"RSS={s['gap_stack_rss_HALF_WIDTH_NOT_SIGMA_mm']:.4f} mm，仅是独立公差半宽平方和，不是已验证的1σ。",'胶片下表面由下辊/支承条定位时，厚度变化不重复进入片底间隙链。','厚度0.15~0.35，以0.20为名义：胶片中心高度改变 -0.025 / +0.075 mm。','该焦平面变化需与G1离焦敏感性联合验证；不能从0.5mm间隙推出光斑合格。','胶层压陷、轴承运行误差、污染和温漂尚未关闭，故此公差预算不代表成品精度。'],15,40)
end()

title('D23','装配工序与质量检查接口')
rows=[['1','底板检验','测A面、40孔及板卡后孔边距；坐标表与STEP一致'],['2','片道侧框','每框圆销＋菱形销；脚垫配磨，不以拧紧螺钉强行找正'],['3','辊芯/包胶','检验轴承段、跳动、材料批次；不在污染面施加胶黏剂'],['4','轴承定位','左侧定轴向、右侧留游动；记录压入力与旋转阻力'],['5','上辊调压','先测移动自重，再设两端弹簧；标记力值，不只记录圈数'],['6','电机/编码器','先对中，再固定；验证轴伸/插拔和信号电平'],['7','不通电走片','验证0.15/0.2/0.35片、片首尾、释放5和无划伤'],['8','台架与回装','低速、低张力、禁光起步；核验G2板卡/线束与光学接口'],['9','DFM与放行','补齐未建模紧固/接插件；有证据后才批准试制/生产']]
table(45,710,['工序','对象','要求'],rows,[75,210,810],48,13)
text(55,175,'本图册将所有新结构定义为候选设计。明确的孔位和公差不意味着已经获得加工/计量/激光安全批准。',14,RED)
end();c.save()
with open(R/'drawings/drawing_index.csv','w',encoding='utf-8-sig',newline='') as f:
 import csv;w=csv.writer(f);w.writerow(['code','title','page']);w.writerows(index)
print('drawings:',page,pdfpath)
