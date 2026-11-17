from pathlib import Path
import json,math,html,base64,io,csv,textwrap
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import cairosvg,fitz
R=Path(__file__).resolve().parents[2];D=R/'drawings';TMP=R/'.build/render';TMP.mkdir(parents=True,exist_ok=True)
meshes=json.loads((R/'cad/render_meshes.json').read_text());parts=json.loads((R/'cad/parts.json').read_text());boards=json.loads((R/'electronics/board_definitions.json').read_text());comps=json.loads((R/'electronics/component_placements.json').read_text());sensors=json.loads((R/'engineering/sensors.json').read_text());P=json.loads((R/'engineering/parameters.json').read_text());CAL=json.loads((R/'engineering/calculated_results.json').read_text())
NAVY='#143c61';BLUE='#226da6';LIGHT='#edf4f8';INK='#172d3f';GRAY='#5e7180';RED='#cb462e';GREEN='#20826c';AMBER='#a75f12'
# CAD mesh renders: actual surfaces, depth-sorted triangles, no synthetic component images.
def render(items,path,size=(1400,1000),explode=False,view=(1.15,-1.7,1.15)):
 v=np.array(view,float);v/=np.linalg.norm(v);right=np.cross(np.array([0.,0.,1.]),v);right/=np.linalg.norm(right);up=np.cross(v,right)
 tris=[];all2=[];light=np.array([-.4,-.6,1.]);light/=np.linalg.norm(light)
 for m in items:
  vs=np.array(m['vertices'],float);vs0=vs.copy()
  if explode:
   g=m['group'];pos=vs.mean(axis=0)
   if g in ('optics','glass') and pos[2]>170:vs[:,2]+=65
   if g in ('electronics','purchased_envelope'):vs[:,0]+=55*(1 if pos[0]>0 else -1)
   if m['id']=='H04':vs[:,2]+=80
  f=np.array(m['faces'],int);t=vs[f];n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);nn=np.linalg.norm(n,axis=1);n/=np.maximum(nn[:,None],1e-10)
  keep=(n@v)>-.03
  t=t[keep];n=n[keep]
  c=np.array(m['color'])*255
  intensity=.58+.35*np.maximum(n@light,0)
  pts2=np.stack([t@right,-t@up],axis=-1);depth=np.mean(t@v,axis=1)
  if len(pts2):all2.append(pts2.reshape(-1,2))
  for q,z,inten in zip(pts2,depth,intensity):tris.append((z,q,tuple(np.clip(c*inten+20,0,255).astype(int))))
 if not all2:return
 xy=np.concatenate(all2);lo=xy.min(axis=0);hi=xy.max(axis=0);span=np.maximum(hi-lo,1);scale=min((size[0]-80)/span[0],(size[1]-80)/span[1]);offs=(np.array(size)-span*scale)/2-lo*scale
 ss=2;im=Image.new('RGB',(size[0]*ss,size[1]*ss),'white');dr=ImageDraw.Draw(im)
 for z,q,c in sorted(tris,key=lambda a:a[0]):
  p=(q*scale+offs)*ss;dr.polygon([tuple(t) for t in p],fill=c)
 im.resize(size,Image.Resampling.LANCZOS).save(path)
core=[m for m in meshes if m['group'] not in ('enclosure','external')]
render(core,TMP/'core.png');render(core,TMP/'exploded.png',explode=True)
render([m for m in meshes if m['id'].startswith('C') or m['id'] in ('P03','P04','B01','EP_VERT')],TMP/'collector.png')
render([m for m in meshes if m['group'] in ('transport','rubber') or m['id'] in ('M02','M12','M13','P01','P02','M01')],TMP/'transport.png')
render([m for m in meshes if m['group'] not in ('external',) and m['id'] not in ('H03','H04')],TMP/'casecut.png')
# Render populated boards in a separate assembly of mechanical placement envelopes.
import cadquery as cq,ezdxf
cadcomp=cq.Assembly(name='PCB_COMPONENT_ENVELOPES_NOT_AS_BUILT');compmeshes=[]
for b in boards:
 if b['id']=='B09':continue
 for p in [c for c in comps if c['board']==b['id']]:
  u,v=p['xy'];w,h,z=p['body'];ox,oy,oz=b['origin'];t=b['size'][2]
  if p['rotation']%180:w,h=h,w
  if b['plane']=='XY':sz=[w,h,z];pos=[ox+u,oy+v,oz+t/2+z/2]
  else:
   sg=1 if b['normal']=='+Y' else -1
   sz=[w,z,h];pos=[ox+u,oy+sg*(t/2+z/2),oz+b['size'][1]-v if sg==1 else oz+v]
  s=cq.Workplane('XY').box(*sz).translate(pos).val();col=(.23,.28,.32) if p['ref'].startswith('U') else (.77,.65,.34) if p['ref'].startswith('J') else (.37,.41,.43)
  cadcomp.add(s,name=b['id']+'_'+p['ref'],color=cq.Color(*col));vs,fs=s.tessellate(.5,.2);compmeshes.append(dict(id=b['id']+'_'+p['ref'],name=p['value'],group='component_envelope',vertices=[[v.x,v.y,v.z] for v in vs],faces=[list(f) for f in fs],color=col))
cadcomp.save(str(R/'cad/step/ZL80_R5_PCB_component_envelopes.step'))
render([m for m in meshes if m['group'] in ('electronics','purchased_envelope')]+compmeshes,TMP/'electronics.png',view=(1,-1.7,1.7))
(R/'cad/component_render_meshes.json').write_text(json.dumps(compmeshes,separators=(',',':')))
# Draft corridor DXF, intentionally not claiming swept bend validity.
d=ezdxf.new('R2010');d.units=4;ms=d.modelspace()
for h in json.loads((R/'electronics/harness_routes.json').read_text()):
 ms.add_polyline3d(h['points']);ms.add_text(h['id'],dxfattribs={'height':3}).set_placement(h['points'][0])
d.saveas(R/'cad/dxf/W00_harness_corridors_3D.dxf')
# SVG engineering atlas helpers.
class Page:
 def __init__(self,num,title,sub='设计分配与名义几何；图中包络不等于厂商实物认证。'):
  self.num=num;self.title=title;self.s=[f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1600" height="1131" viewBox="0 0 1600 1131"><defs><marker id="arr" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto-start-reverse"><path d="M0,0 L8,4 L0,8 Z" fill="{BLUE}"/></marker></defs><rect width="1600" height="1131" fill="white"/>']
  self.rect(30,25,1540,74,NAVY,0);self.text(55,74,f'ZL80 / R5   {num}  {title}',31,'white',True)
  self.text(45,129,sub,18,GRAY);self.line(40,1065,1560,1065,BLUE,2)
  self.text(45,1095,'R5-PDR1  |  80 mm有效 / 100 mm扫描预留  |  2026-11-14  |  单位 mm',17,INK)
  self.text(1080,1095,'初步工程设计 · 非加工/PCB制造放行图',17,RED)
 def text(self,x,y,s,size=20,c=INK,bold=False,anchor='start'):
  self.s.append(f'<text x="{x}" y="{y}" font-family="Noto Sans CJK SC, sans-serif" font-size="{size}" fill="{c}" font-weight="{700 if bold else 400}" text-anchor="{anchor}">{html.escape(str(s))}</text>')
 def rect(self,x,y,w,h,fill='none',stroke=BLUE,sw=1.5,rx=0):self.s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke if stroke else "none"}" stroke-width="{sw}"/>')
 def line(self,x,y,x2,y2,c=BLUE,sw=2,dash=None,arrow=False):self.s.append(f'<line x1="{x}" y1="{y}" x2="{x2}" y2="{y2}" stroke="{c}" stroke-width="{sw}" '+(f'stroke-dasharray="{dash}" ' if dash else '')+('marker-end="url(#arr)" ' if arrow else '')+'/>')
 def circle(self,x,y,r,fill='none',stroke=BLUE,sw=2):self.s.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
 def poly(self,pts,fill='none',stroke=BLUE,sw=2):self.s.append(f'<polygon points="'+ ' '.join(f'{x},{y}' for x,y in pts)+f'" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
 def image(self,x,y,w,h,path):
  b=base64.b64encode(Path(path).read_bytes()).decode();self.s.append(f'<image x="{x}" y="{y}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid meet" xlink:href="data:image/png;base64,{b}"/>')
 def para(self,x,y,text,width=38,size=20,color=INK,step=31):
  # width is count of fullwidth characters; latin characters use approx half width.
  lines=[]
  for raw in str(text).split('\n'):
   line='';n=0
   for ch in raw:
    w=.56 if ord(ch)<128 else 1
    if n+w>width:lines.append(line);line='';n=0
    line+=ch;n+=w
   lines.append(line)
  for i,l in enumerate(lines):self.text(x,y+i*step,l,size,color)
  return y+len(lines)*step
 def note(self,x,y,w,title,text):
  self.rect(x,y,w,115,LIGHT,0,rx=5);self.text(x+18,y+32,title,22,BLUE,True);self.para(x+18,y+65,text,(w-36)/20,18,INK,27)
 def box(self,x,y,w,h,title,sub='',fill=LIGHT):
  self.rect(x,y,w,h,fill,BLUE,1.3,6);self.text(x+w/2,y+35,title,21,BLUE,True,'middle')
  if sub:self.para(x+12,y+65,sub,(w-24)/18,17,INK,25)
 def table(self,x,y,width,headers,rows,colfrac=None,rowh=48,font=17):
  f=colfrac or [1/len(headers)]*len(headers);xx=[x]
  for q in f:xx.append(xx[-1]+q*width)
  self.rect(x,y,width,rowh,NAVY,0)
  for i,h in enumerate(headers):self.text(xx[i]+10,y+30,h,font,'white',True)
  for j,row in enumerate(rows):
   yy=y+(j+1)*rowh;self.rect(x,yy,width,rowh,LIGHT if j%2==0 else 'white','#d7e2eb',.6)
   for i,c in enumerate(row):self.para(xx[i]+10,yy+26,str(c),(xx[i+1]-xx[i]-20)/font,font,INK,22)
  return y+(len(rows)+1)*rowh
 def save(self):
  txt='\n'.join(self.s+['</svg>']);s=D/'svg'/f'{self.num}.svg';s.write_text(txt)
  cairosvg.svg2png(bytestring=txt.encode(),write_to=str(D/'png'/f'{self.num}.png'),output_width=1920,output_height=1357)
  cairosvg.svg2pdf(bytestring=txt.encode(),write_to=str(TMP/f'{self.num}.pdf'))
  return {'id':self.num,'title':self.title,'svg':f'drawings/svg/{self.num}.svg','png':f'drawings/png/{self.num}.png'}
pages=[]
def finish(p):pages.append(p.save())
# 01 actual CAD overview
q=Page('D01','总体设计与零件空间布置','旋转多面镜飞点扫描；采用已选候选器件与RFQ包络分层集成，不用相机替代PMT。');q.image(45,160,1020,730,TMP/'core.png');q.text(65,940,'核心总装：实际B-rep投影，已去除外壳以看见片道、收光及电子舱。',20)
q.note(1100,175,450,'有效幅宽与运动','X横扫80 mm有效；100 mm预留；Y连续送片。');q.note(1100,315,450,'整机包络','320(X) × 300(Y) × 300(Z)，不含外置托架、脚垫及卷架。');q.note(1100,455,450,'实体与空间限界分开','自制件、厂家外廓、功能占位、维护禁布区均独立标注。');q.note(1100,595,450,'本版新增','8块定制PCB外形/关键布局；SP2独立托板；传感器与线束通道。');q.note(1100,735,450,'尚未冻结','光学处方、完整PCB电路/布线、公差与紧固、实际性能及安全。');finish(q)
q=Page('D02','外壳、接口及维护方向');q.image(45,165,980,790,TMP/'casecut.png');q.table(1050,170,500,['项目','本版接口'],[['片口','前后86 × 5，需迷宫遮光'],['右侧','64 × 35可换SP2接口片'],['左侧','φ12.2电源口RFQ限界'],['后侧','40 × 40电子舱风口'],['维护','顶盖上提；模拟舱独立拆卸'],['尺寸状态','名义板，不是钣金展开图']],[.27,.73],72,18);q.para(1050,790,'开盖时硬件禁能先动作。所有片口必须在无片、片尾、翘曲、窄片状态检查激光泄漏。',25,20,RED);finish(q)
q=Page('D03','总装分层与装配基准');q.image(40,155,1040,825,TMP/'exploded.png');q.table(1100,165,450,['层/基准','装配含义'],[['底板A','300×280×6共同基准'],['侧框B','两轴承座与浮动上辊'],['收光层','筒轴X，侧窗朝−Y'],['计量层','胶片中心Z=110'],['光学层','共享后横梁与支柱'],['电子层','B01屏蔽舱；余板下层'],['外壳','不承担光学基准定位']],[.3,.7],80,18);finish(q)
# floorplan supports arbitrary board plane
q=Page('D04','下层PCB空间布置与高度预算','二维投影须结合Z高度阅读；每块板均给本体、器件侧、焊脚侧、安装孔和拆卸方向。')
sc=2.45;cx,cy=520,600
for x in range(-150,151,50):q.line(cx+x*sc,cy-140*sc,cx+x*sc,cy+140*sc,'#e4ebef',1)
for y in range(-140,141,40):q.line(cx-150*sc,cy+y*sc,cx+150*sc,cy+y*sc,'#e4ebef',1)
q.rect(cx-150*sc,cy-140*sc,300*sc,280*sc,'none',GRAY,3)
for b in boards:
 if b['plane']!='XY':continue
 x,y,z=b['origin'];w,h,t=b['size'];q.rect(cx+x*sc,cy-(y+h)*sc,w*sc,h*sc,'#dbece7',GREEN,2);q.text(cx+(x+w/2)*sc,cy-(y+h/2)*sc,b['id'],22,GREEN,True,'middle')
q.rect(cx-30*sc,cy+54*sc,96*sc,46*sc,'#e8e3da',AMBER,2);q.text(cx+18*sc,cy+77*sc,'B01 / PMT',20,AMBER,True,'middle');q.line(cx,cy-350,cx,cy-405,BLUE,3,arrow=True);q.text(cx+15,cy-380,'+Y送片',18)
q.table(1010,165,545,['板号','板框mm','本版Z/方向'],[[b['id'],str(b['size'][:2]),str(b['origin'][2])+' / '+b['plane']] for b in boards],[.15,.38,.47],60,18)
q.para(1050,835,'B09是SP2可调安装托板，不是第9块定制电子板。SP2 110×60×25为待实测限界。',24,20,RED);finish(q)
q=Page('D05','PCB装联空间与采购件高度');q.image(40,165,960,720,TMP/'electronics.png');q.table(1000,165,550,['板','器件/背面高度','层数建议'],[[b['id'],f'{b["top"]} / {b["bottom"]} mm',str(b['layers']) if b['layers'] else '托板'] for b in boards],[.16,.52,.32],62,18);q.para(65,950,'图中芯片与功能区方块是装联包络。FUNCTION_ONLY并非芯片实体，不可直接按占位贴片生产。',66,21,RED);finish(q)
# optical path explicit not generic laser sheet
q=Page('D06','光学顺序与二维扫描几何','多条红线表示不同时刻的飞点路径，不表示同时照亮整条线。光学处方与真实工作距仍待联合RFQ。')
for x,title,sub,w in [(70,'635nm激光','APC / 硬件禁能',180),(290,'整形+ND','参考光取样',190),(530,'六面polygon','单方向周期扫点',210)]:q.box(x,185,w,115,title,sub)
q.line(250,245,285,245,RED,4,arrow=True);q.line(480,245,525,245,RED,4,arrow=True)
q.poly([(630,320),(800,520),(460,520)],'#fff0eb',RED,1);q.rect(450,390,370,48,'#d4edf4',BLUE,2);q.text(860,420,'f-θ镜组：RFQ 96×44×30',23,BLUE,True)
q.rect(380,520,500,15,'#d5d9dc',GRAY);q.text(910,540,'80mm胶片，Y连续运动',23)
q.line(450,555,820,555,BLUE,3);q.text(635,590,'100 mm扫描预留 / ROI ±40',23,BLUE,True,'middle')
q.rect(445,635,390,105,'#e8edf0',BLUE,2,12);q.rect(460,625,360,8,'white',RED,2);q.text(640,685,'横置积分筒 / 顶部104×1.2狭缝',20,BLUE,True,'middle')
q.line(600,535,600,625,RED,4,arrow=True);q.line(445,690,330,690,BLUE,5,arrow=True);q.box(130,640,190,110,'PMMA导光','侧窗8×10 → 5.2方');q.line(130,690,80,690,BLUE,5,arrow=True);q.box(45,800,215,100,'单PMT','先透过胶片，后收光')
q.para(1000,200,'X=快扫描，Y=连续送片，Z=高度。\n光斑在一行内经过不同Y位置，不能把整条轨迹写成同一Y。\n有效图像80mm≠镜组可只覆盖80mm。\nEFL100mm仅算例，不等于胶片与镜片机械间距。',26,23,INK,38)
q.note(970,695,570,'参考光不是第二个图像探测器','参考PD用于归一化光源变化；PMT负责透射光计量。SOS/EOS是片外定时点。');finish(q)
q=Page('D07','横置积分筒总成与R5耦合修正');q.image(45,160,1010,650,TMP/'collector.png');q.table(1070,170,480,['部位','名义尺寸'],[['内腔','φ40 × 120'],['筒壳','φ52 × 126'],['顶部狭缝','104 × 1.2，薄唇0.3'],['径向侧窗','8 × 10，朝−Y'],['导光件','长32；出端5.2×5.2'],['PMT有效面','φ8；出端间隙0.4'],['两端','封闭，无轴向收光口']],[.38,.62],72,18)
q.note(65,850,930,'导光不是无损压缩','出口对角线7.354mm小于φ8，几何可放入；展度、角分布、散射及耦合效率必须测量。');finish(q)
q=Page('D08','积分筒横剖面与侧窗关系','剖面为Y-Z示意，X为筒轴/扫描方向。参考图的“局部高反射点”是风险，不设计成增强贴片。')
q.circle(550,555,240,'#dee7ed',BLUE,3);q.circle(550,555,216,'#fafaf1',GRAY,2);q.circle(550,555,185,'white',BLUE,2)
q.rect(538,308,24,36,'white','white');q.rect(400,299,300,9,'#6b7b87',GRAY);q.rect(541,295,18,20,'white','white');q.line(250,275,860,275,GRAY,9);q.text(900,285,'胶片中心 Z=110',23)
q.poly([(540,555),(290,527),(25,543),(25,567),(290,583),(540,555)],'#e4f4f7',BLUE,2);q.rect(270,515,32,80,'#d9dfe1',BLUE,2);q.box(50,660,225,100,'H10720-20','窗口朝+Y；φ8有效面')
for a,b in [((550,280),(550,730)),((550,730),(705,520)),((705,520),(405,440)),((405,440),(310,552))]:q.line(*a,*b,RED,3,arrow=True)
q.line(550,790,550,825,BLUE,2);q.text(580,815,'下壁首落点应连续均匀',22,BLUE,True)
q.table(1030,205,520,['约束','检查'],[['片面到薄唇','0.5mm，厚度/翘曲需验证'],['侧窗路径','无任何筒端轴向收光'],['遮光套','避开入口下辊，留0.6mm名义隙'],['可拆挡片','仅A/B试样，基线不强装'],['内胆接缝','不得落在首落点轨迹上'],['均匀性','整筒位置响应，不只材料反射率']],[.32,.68],86,18);finish(q)
q=Page('D09','扫描宽度、狭缝及筒轴尺寸链');
for yy,ww,lab,c in [(240,80,'有效成像80 mm（X=−40…+40）',RED),(390,100,'光学预留100 mm（X=−50…+50）',BLUE),(540,104,'实体狭缝104 mm（两端各多2）',GREEN),(690,120,'有效内腔120 mm',AMBER),(840,126,'筒壳126 mm（不含端盖）',GRAY)]:
 x=790-ww*5;q.line(x,yy,x+ww*10,yy,c,4);q.line(x,yy-20,x,yy+20,c,2);q.line(x+ww*10,yy-20,x+ww*10,yy+20,c,2);q.text(790,yy-35,lab,26,c,True,'middle')
q.text(790,980,'片外SOS/EOS取样点：名义X=±46；镜片在Z=112，其坐标需光学校准。',23,INK,False,'middle');finish(q)
q=Page('D10','PMT实物接口、针脚与模拟板耦合');
q.rect(110,240,700,350,'#d5dce1',BLUE,3);q.circle(264,415,70,'#abd6e5',BLUE,3);q.circle(264,415,56,'#eaf8fc',BLUE,2)
q.text(280,645,'本体50×25×18；图示为光窗面',22);q.text(300,700,'光窗中心距左端11；φ10窗 / φ8有效面',22)
q.line(110,205,810,205,BLUE,3);q.text(460,190,'50',24,BLUE,True,'middle')
q.line(880,240,880,590,BLUE,3);q.text(900,420,'25',24)
q.table(1030,195,520,['针脚','功能'],[['1 / 8','NC'],['2','Vref输出，禁止反向供电'],['3','Vcont 0.5–1.1V，慢调'],['4 / 5','+5V / GND'],['6 / 7','Signal GND / 电流输出'],['4×M2','14mm方距，深度3mm']],[.26,.74],79,19)
q.note(80,820,920,'R5基线采用H10720针脚版本','12mm引脚到可拆插座；B01改至Y=−91，插座6mm高，名义插入约3.1mm。底视图镜像、孔位与配合需复核。')
q.para(1050,800,'电流信号在模块后立即进入TIA，不经跨机箱长同轴。内部高压已封装，不另接裸高压。',24,20,RED);finish(q)
q=Page('D11','四辊片道与独立计量链');q.image(30,160,1010,730,TMP/'transport.png');q.table(1050,175,500,['项目','名义设计'],[['胶辊','OD20 / 面长100'],['轴','φ6 / 总长176'],['辊站Y','−42与+42，中心距84'],['测量编码','入口下辊，独立ABZ'],['主动牵引','出口下辊，右侧电机'],['复核编码','出口下辊，比较速度'],['上辊','浮动+预载+手动释放'],['扫描线','Y=0，无实体辊遮光']],[.33,.67],68,18);q.para(80,940,'散片首尾跨辊未稳定段必须标记；长度较短时用引带/载片，不补造Master像素。',64,22,RED);finish(q)
q=Page('D12','编码器精度预算与安装');q.box(70,205,420,140,'AMT112S-V ×2','5V供电；4096PPR编程；ABZ → 3.3V缓冲');q.box(580,205,420,140,'直径20 mm测量辊','有效直径随压紧、磨损和温度变化');q.box(1080,205,450,140,'FPGA位置标记','入口计量＋出口复核，不把电机步数当片长');q.line(490,275,570,275,BLUE,3,arrow=True);q.line(1000,275,1070,275,BLUE,3,arrow=True)
q.table(90,420,1420,['量','结果','工程解释'],[['四倍频计数','16,384 count/rev','量化步距 = π×20/16384'],['名义位移步距','3.835 μm','不是实际测量精度'],['典型角度误差','0.2° → 34.9 μm弧长','未经LUT标定，不支持5μm精度声明'],['外部基准验证','全周轮角LUT + 长度/滑移试验','两轮一致也可能共同打滑'],['更高精度路线','精密光学编码器/直接位移参考','重新核算体积、成本、计量链']],[.25,.25,.5],92,22)
q.para(100,1000,'主机上电时轴静止等待编码器初始化；运行时同步监测非法AB跳变、丢脉冲、反转和两轮差值。',65,21,INK);finish(q)
q=Page('D13','传感器位置、检测范围与干扰抑制');q.table(50,175,1500,['ID','坐标(X,Y,Z)','作用 / 注意'],[[s['id'],str(s['center']),s['type']+'；'+s['role']] for s in sensors],[.18,.27,.55],54,18);q.text(70,1040,'入口IR双头横距50；ROI有效期间硬件熄灭IR，避免PMT拾取传感器光。双张不能只按透射OD判断。',19,RED,True);finish(q)
q=Page('D14','电气信号链与电压域');
for xx,ttl,sub in [(55,'PMT','5V内部高压模块'),(355,'B01 TIA','±5VA，短电流节点'),(655,'B02 ADC','AD9268 / 1.8V'),(955,'SP2 FPGA','J6 Bank33=1.8V'),(1255,'主机文件','GigE / 分块Master')]:q.box(xx,210,260,130,ttl,sub)
for xx in (315,615,915,1215):q.line(xx,275,xx+35,275,BLUE,3,arrow=True)
q.box(55,455,260,130,'B08参考PD','就地TIA → ADC B');q.box(355,455,260,130,'B06/B07同步','SOS/EOS → J5 3.3V');q.box(655,455,260,130,'B05运动/传感','5V编码器缓冲为3.3V');q.box(955,455,260,130,'B03静电源/增益','PMT增益慢调且记录');q.box(1255,455,260,130,'B04硬件禁止链','独立于操作系统')
q.table(70,715,1450,['链路','电压/时间条件','关键禁忌'],[['ADC数据32+DCO2','1.8V，持续20MHz，两DCO域处理','不可接3.3V Vadj'],['ADC控制','J5 3.3V ↔ ADC 1.8V，SDIO双向','未定型转换器不可直接跳线'],['AMT112编码','5V供电，输出先缓冲','5V不直入Zynq IO'],['J6电源针','37/38=3.3V，39/40=5V','不因Bank33改1.8V而自动改变']],[.22,.43,.35],65,20);finish(q)
q=Page('D15','线性TIA与对数前端的分支决策','资料冲突不静默合并：原机照片显示LOG；新增PPT提出TIA。R5明确选择线性TIA为基线，LOG保留替换卡。')
q.box(60,235,240,130,'PMT电流','阳极接口短连接');q.box(390,235,300,130,'OPA828线性TIA','Rf100k / Cf1.5p起算');q.box(780,235,300,130,'AD8138差分驱动','偏置/VCM；保留DC');q.box(1170,235,300,130,'AD9268通道A','20MSPS / 饱和标志')
for x in (300,690,1080):q.line(x,300,x+80,300,BLUE,4,arrow=True)
q.table(75,470,1450,['档位/分支','初步参数','验证要求'],[['低跨阻试样','10k / 4.7p','亮端饱和、输入寄生、阶跃'],['标准跨阻试样','100k / 1.5p','非最终补偿值；全链幅相测试'],['高跨阻试样','1M / 0.5p','不能只因Rf大就认为高OD可用'],['LOG替换','同90×50空间，不与TIA并联','电流极性转换与低光响应待定'],['动态边界','纵向过采样 ≠ 横向拖尾修复','高低OD邻边、不同速度A/B']],[.23,.32,.45],85,21)
q.text(85,990,'PDR原理草图与部分针脚网表见 electronics；正式抗混叠滤波、偏置、保护和噪声预算尚未闭合。',21,RED);finish(q)
q=Page('D16','功率分配、硬件互锁与散热');
q.box(55,180,265,135,'外置24 V / 90W','不将市电放入主机');q.box(420,180,280,135,'B04保护与分配','保险 / 反接 / 过压 / 硬禁能');q.box(800,180,310,135,'负载电源域','5VD、12VM、模拟预稳压');q.box(1200,180,330,135,'B03 / B02本地稳压','5VA、±5VA、1.8VA/D')
for x in (320,700,1110):q.line(x,245,x+90,245,BLUE,3,arrow=True)
q.table(70,410,1450,['项目','预算/逻辑','注意'],[['名义/峰值功耗','32.3 W / 52 W','不含外置ADF；不是实测'],['理想换气','ΔT10K约5.7CFM','实际风扇须考虑压损、过滤与噪声'],['失效安全','开盖/放辊/失扫/过温/看门狗→关光','硬件禁能＋失电关快门'],['分舱','风流只穿电子舱，不吹胶片/积分筒','粉尘与热漂均进入密度误差'],['接地','机壳端接与连续返回平面分清','不能用割裂地平面替代回流设计']],[.22,.4,.38],88,21)
q.para(90,955,'未给Class 1、EMC或电气安全合格结论；硬件失效注入和整机无片泄漏必须实测。',65,22,RED);finish(q)
q=Page('D17','线束通道、插拔与维护净空');q.table(50,170,1500,['线束','起点→终点','中心线 / 下料预算','设计通道'],[[h['id'],h['start']+' → '+h['end'],f'{h["polyline_length_mm"]} / {h["cut_length_budget_mm"]} mm',h['type']] for h in json.loads((R/'electronics/harness_routes.json').read_text())],[.08,.38,.22,.32],65,17)
q.para(80,1010,'中心线折角未圆滑；最小弯曲半径、接头护套、理线夹和整束扫掠干涉仍须装配样机验证。',66,21,RED);finish(q)
q=Page('D18','扫描时序、数据与位置标签延迟','六面/3000rpm与EFL100仅用于预算，实际扫频/视场占空比由扫描头规格与标定决定。')
labels=['FACET/SOS','ROI_VALID','ADC_CLK','ADC_DATA','TAG_ALIGNED','ENCODER_Y'];x0=280;length=1160
for j,l in enumerate(labels):
 yy=220+j*115;q.text(60,yy+10,l,22,BLUE,True);q.line(x0,yy+30,1480,yy+30,GRAY,1)
 if j==0:
  for x in (x0,x0+540,x0+1080):q.line(x,yy+30,x,yy-20,BLUE,3);q.line(x,yy-20,x+15,yy-20,BLUE,3);q.line(x+15,yy-20,x+15,yy+30,BLUE,3)
 elif j==1:
  for x in (x0+70,x0+610):q.rect(x,yy-20,205,50,'#d7eaf5',BLUE,2)
 elif j==2:
  for k in range(60):x=x0+k*20;q.line(x,yy+30,x,yy-5,BLUE,1.4);q.line(x,yy-5,x+10,yy-5,BLUE,1.4);q.line(x+10,yy-5,x+10,yy+30,BLUE,1.4)
 elif j in (3,4):
  off=25 if j==3 else 45
  for x in (x0+70+off,x0+610+off):q.rect(x,yy-20,205,50,LIGHT,BLUE,2);q.text(x+12,yy+10,'原采样时刻标签',16)
 else:
  for k in range(24):x=x0+k*49;q.line(x,yy+30,x,yy-5,GREEN,2);q.line(x,yy-5,x+20,yy-5,GREEN,2)
q.note(70,935,1450,'不对ADC时钟做ROI门控','ADC连续运行；延迟的是与原采样时刻对应的ROI/位置/增益状态。600ns ADC延迟与数字滤波群延迟分开校验，不能重复错移。');finish(q)
q=Page('D19','空间重建与原始数据边界');
for k in range(6):
 pts=[(110+j*65,290+k*65-j*4) for j in range(8)]
 for a,b in zip(pts,pts[1:]):q.line(*a,*b,BLUE,2)
 for a in pts:q.circle(*a,5,BLUE,BLUE)
q.text(110,750,'按ADC时刻采样：斜行轨迹',25,BLUE,True)
q.line(700,450,850,450,BLUE,6,arrow=True)
for k in range(6):
 for j in range(8):q.circle(955+j*65,290+k*65,5,GREEN,GREEN)
q.text(960,750,'按实际(x,y)映射：矩形输出网格',25,GREEN,True)
q.note(75,850,710,'数据与标定顺序','线性基线：dark扣除 → 参考光归一 → 平场/密度标定 → 几何映射。LOG替换先反演到线性量。')
q.note(825,850,710,'不填补成合格Master','保留Raw与Calibrated Master；缺行、过载、滑移、缺编码均保留质量标记。AI只处理派生副本。');finish(q)
q=Page('D20','扫描、数据率与光子预算','下列为显式假设的计算例，不是OD、MTF或速度验收结果。')
q.table(60,175,1480,['量','计算值','含义'],[['物理行频','300 line/s','6面 × 3000rpm / 60'],['100mm / 80mm窗口','1.5915ms / 1.2732ms','有效视场占比由几何计算，不任取80%'],['50μm驻留','0.7958μs；约15.92个ADC样本','数字过采不等于新增入射光子'],['连续走片','15mm/s；16倍Y过采时0.9375mm/s','不能宣称这些模式达到相同MTF/OD'],['原始双通道流','80MB/s','需DMA缓存与回压，不依赖PC时间戳'],['16位50μm图像','64MB/m；正常行频0.96MB/s','元数据、参考与原始片段另算']],[.25,.32,.43],80,21)
q.table(60,790,1480,['OD算例','初级光电子/像素','仅统计噪声 σD'],[[str(a['od']),f'{a["photoelectrons_per_pixel"]:.2f}',f'{a["shot_only_sigma_D"]:.5f} D'] for a in CAL['photon_example']],[.25,.35,.4],48,19)
q.text(75,1038,'假设：片面50μW、收光5%、QE15%、635nm、额外噪声因子1.3；真实噪声只会叠加。',18,RED);finish(q)
q=Page('D21','外置自动馈片接口与解耦设计','用户新PPT的350mm/大幅机型不直接缩成80mm机；保留可靠单张交接原则，外置ADF独立开发。')
for i,(t,s) in enumerate([('倾斜堆叠','恒力压板/侧导轨'),('拾取/分离','摩擦差+反向辊'),('检测/预定位','双张+偏斜+前沿'),('交给主机','独立计量辊接管'),('扫描Master','异常拒片/重扫')]):
 x=50+i*310;q.box(x,210,270,140,t,s)
 if i<4:q.line(x+270,280,x+300,280,BLUE,3,arrow=True)
q.table(70,465,1450,['项目','本版交付边界'],[['外置机械空间','250×300×330mm概念包络；不计入主机体积'],['主机片口高度','胶片中心Z=110，左右侧向基准可调'],['控制握手','REQUEST / READY / SINGLE_OK / JAM / EXIT_FULL / FAULT'],['电气接口','外置24V独立电源；隔离/缓冲接口，不把24V送入FPGA'],['30片目标','只作为PoC目标，不是完成自动分片设计'],['禁止方案','不以固定窄缝限张数；不靠透射OD单独判双张']],[.24,.76],80,21)
q.text(90,1025,'散片输送与长卷连续模式互斥管理；外置收卷只管低张力，不决定图像像素间距。',21,RED);finish(q)
q=Page('D22','装调顺序与可维护设计');q.table(70,175,1450,['步骤','定位/动作','验收点'],[['1 基准底板','清洁A面；装两侧框与轴承座','同轴/平行、辊跳动、无卡滞'],['2 走片链','装胶辊、弹簧预载和释放','真片压力DOE、保护两面乳剂'],['3 收光组件','鞍座/狭缝/侧窗/导光/PMT','0.5mm间隙、导光端定位、遮光'],['4 光学头','低功率/闭盖条件对准polygon+fθ','全幅焦点、面倾斜、SOS/EOS'],['5 PCB与线束','按板位/绝缘/返回路径安装','1.8VBank、5V传感缓冲、接地'],['6 标定','dark/参考/平场/阶梯片/几何','低光阶跃与饱和恢复'],['7 故障注入','失扫/编码断线/开盖/回压','关光、受控停片、质量标记']],[.2,.42,.38],108,21);finish(q)
q=Page('D23','验证范围与设计冻结门槛');
with (R/'engineering/设计冻结门槛.csv').open(encoding='utf-8-sig') as f:rr=list(csv.DictReader(f))
q.table(50,170,1500,['编号','风险项','放行门槛'],[[r['id'],r['topic'],r['gate']] for r in rr],[.1,.42,.48],55,19);q.text(65,1035,'完整关闭措施见 engineering/设计冻结门槛.csv；本页“通过”不能由图纸外观替代。',20,RED);finish(q)
q=Page('D24','版本差异、继承关系与文件入口');
q.table(60,175,1480,['依据','保留 / 变更','理由'],[['用户纠正','polygon + 横置矩形狭缝筒 + 径向侧窗','不再改成振镜、相机或立式积分杯'],['R4','80 / 100 / 104 的三重定义保留','光学扫描、ROI、实体狭缝不同'],['新增PPT','TIA基线 / LOG作为替换分支','明确两种材料的差异，不静默合并'],['器件选型','H10720针脚版，φ8有效窗口','导光出端改5.2方，短电流连接'],['PCB集成','8板+SP2托板；给坐标、高度、针脚','占位与已选实物外形分开'],['尺寸/重量','320×300×300mm展开原型','尚未达到旧3.5kg便携目标，不强行缩图'],['验证','刚性名义几何与软件算例检查','不代表布线、光学、热与性能合格']],[.2,.43,.37],99,20)
q.text(90,1025,'从 index.html 浏览全包；STEP / DXF / SVG / PNG / PDF / DOCX / XLSX / KiCad / CSV / 源码均可继续编辑。',20,BLUE,True);finish(q)
# Per-board drawings, generated from exactly the ECAD placement data.
for b in boards:
 if b['id']=='B09':continue
 bid=b['id'];q=Page('E'+bid[1:],bid+' '+b['name']+'：外形、布局与接插件','关键布局与功能占位：未布线；器件高度纳入安装预算。原理针脚图见electronics/schematics。')
 w,h,t=b['size'];s=min(820/w,700/h);ox,oy=80,220;q.rect(ox,oy,w*s,h*s,'#e1eee8',GREEN,3)
 for x,y in b['holes']:q.circle(ox+x*s,oy+y*s,b['mount_dia']/2*s,'white',BLUE,2)
 for c in [x for x in comps if x['board']==bid]:
  x,y=c['xy'];cw,ch,ht=c['body'];cw,ch=(ch,cw) if c['rotation']%180 else (cw,ch)
  color='#f1d9b6' if c['ref'].startswith('J') else '#d7e0e6' if c['ref'].startswith('U') else '#edf2f5'
  q.rect(ox+(x-cw/2)*s,oy+(y-ch/2)*s,cw*s,ch*s,color,GRAY,1)
  q.text(ox+x*s,oy+y*s+4,c['ref'],max(10,min(17,s*2)),INK,True,'middle')
 q.line(ox,oy-35,ox+w*s,oy-35,BLUE,2);q.text(ox+w*s/2,oy-50,f'{w} mm',23,BLUE,True,'middle');q.text(ox+w*s+15,oy+h*s/2,f'{h} mm',23,BLUE)
 q.table(1010,185,540,['约束','值'],[['板厚/层数',f'{t} / {b["layers"]}层建议'],['装联高度',f'正面{b["top"]}；背面{b["bottom"]}'],['世界原点',str(b['origin'])],['平面/器件侧',b['plane']+' / '+b['normal']],['安装孔',f'{len(b["holes"])}×φ{b["mount_dia"]}'],['状态','布置草稿，不是投板文件']],[.33,.67],74,18)
 q.para(1010,700,b['notes'],26,19,INK,31);q.para(1010,880,'外围/保护/参考/阻抗/地返回及完整元件尚需细化。厂家焊盘、针脚镜像、插拔行程应复核。',26,19,RED,31)
 q.text(80,1000,'板上(u,v)坐标与世界坐标变换见electronics/README；XZ板须注意焊接面镜像。',19,INK);finish(q)
# Per-part nominal CAD views, deliberately not labelled production 2D drawings.
partpages=[]
for p in parts:
 m=next((m for m in meshes if m['id']==p['id']),None)
 if not m:
  # spare experiment geometry may not be instantiated. Load its STEP only for render.
  s=cq.importers.importStep(str(R/'cad/step'/f'{p["id"]}.step')).val();vs,fs=s.tessellate(.35,.2);m=dict(id=p['id'],name=p['name'],group='part',vertices=[[v.x,v.y,v.z] for v in vs],faces=[list(f) for f in fs],color=(.6,.67,.73))
 rp=TMP/(p['id']+'_part.png');render([m],rp,size=(1100,760))
 q=Page('P_'+p['id'],p['id']+' '+p['name'],'零件CAD名义几何 / 采购限界图；不含完整加工公差、表面粗糙度、热处理和检验尺寸。')
 q.image(40,170,980,750,rp);q.table(1050,185,500,['字段','值'],[['零件号',p['id']],['材料/类型',p['material']],['局部包络XYZ','×'.join(str(round(a,3)) for a in p['dimensions'])],['状态',p['status']],['实体有效性','有效' if p['valid'] else '失败'],['模型文件',p['id']+'.step']],[.3,.7],88,18)
 q.para(1060,800,p['note'],24,19,RED,29);q.text(70,1005,'尺寸指STEP局部坐标包络；示意姿态可能与装配姿态不同。采购件限界不可作为内部结构制造依据。',19,INK)
 partpages.append(q.save())
# Individual PDFs and merged atlases.
for name,seq in [('ZL80_R5_系统与PCB图册',pages),('ZL80_R5_零件名义几何图册',partpages),('ZL80_R5_完整图册',pages+partpages)]:
 out=fitz.open()
 for p in seq:
  s=fitz.open(TMP/f'{p["id"]}.pdf');out.insert_pdf(s);s.close()
 out.set_metadata({'title':name,'author':'ZL80 project / preliminary integration','subject':'R5-PDR1 - not released for manufacture'});out.save(D/(name+'.pdf'));out.close()
(D/'drawing_register.json').write_text(json.dumps(pages+partpages,ensure_ascii=False,indent=2))
# Overview image of system drawings is useful for browsing, not a replacement for actual pages.
thumbw,thumbh=320,227;ov=Image.new('RGB',(thumbw*4,thumbh*8),'white')
for i,p in enumerate(pages):
 im=Image.open(D/'png'/f'{p["id"]}.png').convert('RGB');im.thumbnail((thumbw,thumbh));ov.paste(im,((i%4)*thumbw,(i//4)*thumbh))
ov.save(D/'图纸总览.jpg',quality=90)
print('atlas',len(pages),'system/PCB',len(partpages),'parts',len(pages)+len(partpages),'pages')
