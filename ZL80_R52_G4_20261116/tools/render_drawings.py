"""Draw emitted PCB copper by independently reading .kicad_pcb, plus actual STEP.
Vector review drawings; not KiCad-native exports, not fabrication masks.
"""
from pathlib import Path
import json,math,csv
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from shapely.geometry import Polygon,LineString,Point
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
import cadquery as cq
from pcb_geometry import ROOT,load,LAYERS,rotated_rect
from audit_pcb import parse
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
D,F,P=load();W,H=420*mm,297*mm
C=canvas.Canvas(str(ROOT/'drawings/ZL80_G4_PCB与装配审查图册.pdf'),pagesize=(W,H))
COL=['#B73737','#3E7B57','#A47426','#375B9F']
def text(x,y,s,size=8,color='#172F46',align='left'):
 C.setFillColor(color);C.setFont('STSong-Light',size);getattr(C,{'left':'drawString','center':'drawCentredString','right':'drawRightString'}[align])(x,y,str(s))
def head(title,sub,no):
 C.setFillColor('#112F4B');C.rect(0,H-23*mm,W,23*mm,fill=1,stroke=0);text(12*mm,H-12*mm,title,16,'#FFFFFF');text(12*mm,H-19*mm,sub,8,'#D2E2EB')
 text(12*mm,9*mm,'ZL80 / R52-G4-E02-D01 | 工程审查候选；非KiCad原生导出；禁止制造放行',9);text(W-12*mm,9*mm,f'D{no:02d}',10,align='right')
def poly(g,fn,fill=None,stroke='#000000',width=.3):
 if g.is_empty:return
 if g.geom_type.startswith('Multi') or g.geom_type=='GeometryCollection':
  for z in g.geoms:poly(z,fn,fill,stroke,width)
  return
 if g.geom_type!='Polygon':return
 p=C.beginPath();pts=list(g.exterior.coords);p.moveTo(*fn(*pts[0]));
 for xy in pts[1:]:p.lineTo(*fn(*xy))
 p.close()
 C.setLineWidth(width);C.setStrokeColor(stroke);C.setFillColor(fill or '#FFFFFF');C.drawPath(p,stroke=1,fill=int(bool(fill)))
def board(bid,layer,left,top,pw,ph):
 b=next(x for x in D['boards'] if x['id']==bid);bw,bh=b['size_mm'];s=min((pw-18*mm)/bw,(ph-18*mm)/bh);ox=left+(pw-bw*s)/2;oy=top-9*mm
 fn=lambda x,y:(ox+x*s,oy-y*s);r,obs,holes,_=parse(bid)
 C.setStrokeColor('#627180');C.setLineWidth(.6);C.rect(ox,oy-bh*s,bw*s,bh*s)
 for x,y,d in holes:C.setFillColor('#FFFFFF');C.circle(*fn(x,y),d*s/2,fill=1,stroke=1)
 for c in [c for c in P if c['board']==bid and ((layer==0 and c['side']=='F') or (layer==3 and c['side']=='B'))]:
  poly(rotated_rect(c,F[c['fp']]['w'],F[c['fp']]['h']),fn,stroke='#AAB3BB',width=.35)
 for o in obs:
  if layer not in o['layers']:continue
  if o['kind']=='pad':poly(o['shape'],fn,fill='#A4A4A4',stroke='#555555',width=.15)
  elif o['kind']=='track':poly(o['shape'],fn,fill=COL[layer],stroke=COL[layer],width=.1)
  else:poly(o['shape'],fn,fill='#666666',stroke='#333333',width=.1)
 for c in [c for c in P if c['board']==bid and ((layer==0 and c['side']=='F') or (layer==3 and c['side']=='B'))]:
  x,y=c['pcb_xy'];text(*fn(x,y-.15),c['ref'],6 if bw<30 else 7,align='center')
 # Input guard/no-plane area is shown even on inner layers; no fake fills.
 rt=json.loads((ROOT/'engineering'/f'{bid}_routing.json').read_text())
 if rt['input_keepout'] and layer in (1,2):
  x1,y1,x2,y2=rt['input_keepout'];C.setStrokeColor('#BC7025');C.setDash(3,3);C.rect(*fn(x1,y2),(x2-x1)*s,(y2-y1)*s);C.setDash()
 text(left+pw/2,top+1*mm,f'{LAYERS[layer]}   |   {bw} × {bh} mm',10,align='center')
 text(left+pw/2,oy-bh*s-5*mm,'同一顶视投影，B.Cu未镜像；非底面装配视图',7,align='center')
for num,bid in enumerate(['B06','B07','B08','B01'],1):
 ar=next(x for x in json.loads((ROOT/'validation/results/copper_audit.json').read_text()) if x['board']==bid)
 head(f'{bid} | 四层铜线、过孔与器件布置',f"实际铜线段 {ar['segments']} / 过孔 {ar['vias']} / 自编回读最少未连 {ar['unconnected_min_links']} / 1.6mm四层候选 / 铺铜尚未原生填充",num)
 for l in range(4):board(bid,l,12*mm+(l%2)*198*mm,H-38*mm-(l//2)*115*mm,192*mm,103*mm)
 text(12*mm,18*mm,'B01只布输入与TIA输出关键网；B06/B07/B08连通性不代表回流、稳定性、时序或EMC已通过。',8)
 C.showPage()
# Export true BRep line projections, not invented surfaces.
for j,(fn,title) in enumerate([('ZL80_G4_Core_Integration.step','G3去罩机械基线 + G4板卡安装'),('ZL80_G4_4Boards_Installed.step','四块板卡安装坐标与元件双面空间')],5):
 s=cq.importers.importStep(str(ROOT/'cad/assemblies'/fn)).val();sp=ROOT/'drawings'/f'D{j:02d}_actual_step.svg'
 cq.exporters.export(s,str(sp),exportType='SVG',opt={'width':1000,'height':620,'marginLeft':20,'marginTop':20,'projectionDir':(1,-1,1),'showAxes':False,'showHidden':False,'strokeWidth':.4})
 head(title,'真实STEP的可见边投影；非光学追迹；元件为厂家尺寸/保守包络，不等于厂家完整模型。',j)
 dr=svg2rlg(str(sp));scale=min(390*mm/dr.width,235*mm/dr.height);dr.scale(scale,scale);renderPDF.draw(dr,C,15*mm,28*mm)
 C.showPage()
# Interface coordinate diagram with exact numeric tables and front/back schema.
head('接口复核 | 感光面与PMT针脚','感光面不是封装顶面；局部板坐标与整机坐标通过显式右手变换关联。',7)
y=H-38*mm
for row in csv.DictReader((ROOT/'engineering/photodiode_coordinates.csv').open(encoding='utf-8-sig')):
 text(20*mm,y,f"{row['board']}  D1感光面：X={row['x_mm']}  Y={row['y_mm']}  Z={row['z_mm']} mm",13);y-=12*mm
text(20*mm,y,'S5971：候选引脚架高3.6 mm；感光面距法兰2.8 mm；壳高按最大3.8 mm检查。',10);y-=10*mm
text(20*mm,y,'X/Z坐标对齐不代表光线落入窗口。必须验证实际光束方向、到达面及安装公差。',10);y-=20*mm
text(20*mm,y,'B01 → 世界坐标：X = x − 27，Y = −91.8 + z，Z = 100 − y。',12);y-=12*mm
text(20*mm,y,'B06/B07：u=+X，v=+Z，正面法向=−Y；B08同B01采用v=−Z，正面法向=+Y。',10);y-=18*mm
pins=[r for r in csv.DictReader((ROOT/'engineering/connector_pin_world.csv').open(encoding='utf-8-sig')) if r['connector']=='JPMT1']
text(20*mm,y,'PMT插座针脚 | PCB面坐标与原G3针脚在X/Z平面吻合；Y方向插深和真实插座仍待定。',10);y-=10*mm
for r in pins:
 text(25*mm,y,f"Pin {r['pin']:>2}   {r['net']:<15}  X={r['world_x_mm']:>8}  Z={r['world_z_mm']:>8} mm",10);y-=8*mm
C.showPage()
head('叠层与布线约束 | 不是阻抗或制造批准','4层/1.6mm候选；保留输入节点禁布区；地平面必须由KiCad重新填充。',8)
stack=list(csv.DictReader((ROOT/'engineering/stackup.csv').open(encoding='utf-8-sig')));y=H-45*mm
for r in stack:
 C.setFillColor('#A49A8B' if r['type']=='Copper' or 'copper' in r['type'] else '#DDE7EC');C.rect(20*mm,y-10*mm,140*mm,10*mm,fill=1,stroke=0);text(25*mm,y-6.5*mm,r['layer']+'  '+r['type'],10);text(165*mm,y-6.5*mm,r['thickness_mm']+' mm',10);y-=14*mm
notes=['最小候选铜间距：0.15 mm；线宽：0.15 mm。','过孔铜径 / 成品钻孔：0.60 / 0.30 mm。','In1.Cu：定义了GND/AGND区，但当前无填充多边形。','In2.Cu：电源/信号候选；输入高阻节点下方禁止走线与铺铜。','PD_SUM / PMT_I：顶层、无过孔；REF_SUM：底层、无过孔。','串联电阻、局部去耦、输入保护与回流需结合真实边沿复核。','板厂叠层、铜厚公差、阻焊、丝印、可焊性与清洗仍需DFM。','没有导出Gerber、钻孔或生产贴片坐标；只交付审查源文件。']
y=H-50*mm
for st in notes:text(215*mm,y,st,9);y-=15*mm
C.showPage()
head('线束接口 | 继承G3走线走廊，更新G4端点','下图仅XY投影；高度和接插件引出方向见harness_endpoints.json；未完成圆角与线束扫掠。',9)
ox,oy=125*mm,145*mm;sc=.65*mm
h=json.loads((ROOT/'engineering/harness_G3_corridors.json').read_text())
C.setStrokeColor('#8093A4');C.rect(ox-150*sc,oy-144*sc,300*sc,288*sc)
for i,r in enumerate(h):
 C.setStrokeColor(COL[i%4]);C.setLineWidth(.6);pts=r['points']
 for p,q in zip(pts,pts[1:]):C.line(ox+p[0]*sc,oy+p[1]*sc,ox+q[0]*sc,oy+q[1]*sc)
 text(ox+pts[0][0]*sc,oy+pts[0][1]*sc,r['id'],7)
y=H-43*mm
for r in h:
 text(240*mm,y,f"{r['id']}  {r['start']} → {r['end']}",9);y-=10*mm
text(240*mm,y-10*mm,'B01/J2改到板坐标(10,37)，避开PMT插拔走廊冲突。',9)
text(240*mm,y-20*mm,'实际对接件、防反插、屏蔽回接与弯曲半径仍需确认。',9)
C.showPage();C.save()
# Outline interface DXF for each board, no manufacturing copper export.
import ezdxf
for b in D['boards']:
 doc=ezdxf.new();doc.units=4;m=doc.modelspace();w,h=b['size_mm'];m.add_lwpolyline([(0,0),(w,0),(w,-h),(0,-h)],close=True)
 for x,y in b['holes']:m.add_circle((x,-y),1.1 if w<30 else 1.6)
 m.add_text(b['id']+' G4 OUTLINE REVIEW ONLY',dxfattribs={'height':1.5,'insert':(0,3)})
 doc.saveas(str(ROOT/'drawings'/f'{b["id"]}_G4_Outline.dxf'))
print('9 pages review drawings +4 outline DXF; actual STEP projection SVGs')
