"""Independent vector rendering of the actual circuit graph, NOT KiCad export."""
from pathlib import Path
import json,sys,math
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from build_kicad import shapes,S
from sexpr import loads,child,children
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
D=R/'docs';D.mkdir(exist_ok=True)
scenes=json.loads((R/'engineering/schematic_scene.json').read_text());placements=json.loads((R/'engineering/placements.json').read_text());F=json.loads((R/'engineering/footprints.json').read_text());boards=json.loads((R/'engineering/circuits.json').read_text())['boards']
W,H=420*mm,297*mm
c=canvas.Canvas(str(D/'ZL80_G2E01_原理图与PCB空间审查.pdf'),pagesize=(W,H))
def text(x,y,s,font='Helvetica',size=7,align='left'):
 c.setFont(font,size);f={'left':c.drawString,'right':c.drawRightString,'center':c.drawCentredString}[align];f(x,y,s)
def header(title,page):
 c.setFillColorRGB(.07,.16,.25);c.rect(0,H-20*mm,W,20*mm,fill=1,stroke=0);c.setFillColorRGB(1,1,1);text(12*mm,H-12*mm,title,'STSong-Light',17)
 c.setFillColorRGB(0,0,0);text(12*mm,8*mm,'G2-E01 D01  |  原理图候选 / PCB未布线 / 非制造放行  |  独立矢量渲染，不是KiCad原生验证','STSong-Light',9);text(W-12*mm,8*mm,str(page),size=9,align='right')
for idx,scene in enumerate(scenes,1):
 header(scene['board']+'  元件级原理图 / 相同网络名表示电气连接',idx)
 # Shrink the original A3 logical drawing slightly to create title and footer space.
 scale=.91;ox=10*mm;oy=8*mm
 def P(x,y):return ox+x*mm*scale,oy+(297-y)*mm*scale
 def seg(x1,y1,x2,y2):c.line(*P(x1,y1),*P(x2,y2))
 c.setLineWidth(.5)
 for a,b in scene['wires']:seg(*a,*b)
 for comp in scene['components']:
  x,y=comp['xy'];kind=comp['kind'];dd=comp['definition']
  for sh in shapes(kind):
   a=loads(sh)
   if a[0]=='polyline':
    pts=[[float(p[1]),float(p[2])] for p in child(a,'pts')[1:]]
    for u,v in zip(pts,pts[1:]):seg(x+u[0],y-u[1],x+v[0],y-v[1])
   elif a[0]=='circle':
    ctr=child(a,'center');rad=float(child(a,'radius')[1]);c.circle(*P(x+float(ctr[1]),y-float(ctr[2])),rad*mm*scale,stroke=1,fill=0)
   elif a[0]=='text':
    at=child(a,'at');text(*P(x+float(at[1]),y-float(at[2])),a[1],size=6,align='center')
  for p in dd['pins']:
   px,py=x+p['x'],y-p['y'];length=0 if dd['shape'] in ('res_h','res_v','cap_h','cap_v','pd','flag') else 5.08
   ang=math.radians(p['angle']);ex,ey=px+length*math.cos(ang),py-length*math.sin(ang)
   if length:seg(px,py,ex,ey)
   if dd['shape'] not in ['res_h','res_v','cap_h','cap_v','tp','flag']:
    text(*P((px+ex)/2+.8,(py+ey)/2-1),p['num'],size=5.0)
    if dd['shape'] in ['fda','box','connector']:text(*P(ex+(.8 if p['angle']==0 else -.8),ey-.6),p['name'],size=5.0,align='left' if p['angle']==0 else 'right')
   if not comp['nets'].get(p['num']):
    seg(px-1,py-1,px+1,py+1);seg(px-1,py+1,px+1,py-1)
  pos=comp['props'];text(*P(*pos['ref']),comp['ref'],size=6.7,align='center')
  if dd['shape'] not in ('tp','flag'):text(*P(*pos['value']),comp['value'],size=5.6,align='center')
 for label in scene['labels']:
  text(*P(label['x'],label['y']-.7),label['text'],size=5.6,align='right' if label['angle']==180 else 'left')
 c.showPage()
for page,b in enumerate(boards,5):
 bid=b['id'];header(bid+'  PCB板框、安装孔、封装与器件空间初排',page)
 p=[x for x in placements if x['board']==bid];w,h=b['size_mm'];sc=min(190*mm/w,180*mm/h);ox=20*mm;oy=H-45*mm
 def xy(x,y):return ox+x*sc,oy-y*sc
 c.setLineWidth(.8);c.rect(ox,oy-h*sc,w*sc,h*sc)
 for i,(x,y) in enumerate(b['holes']):
  c.circle(*xy(x,y),(1.1 if w<30 else 1.6)*sc,stroke=1,fill=0);text(*xy(x,y),f'H{i+1}',size=6,align='center')
 for comp in p:
  d=F[comp['fp']];x,y=comp['pcb_xy'];xx,yy=xy(x-d['w']/2,y+d['h']/2);c.rect(xx,yy,d['w']*sc,d['h']*sc,stroke=1,fill=0)
  for pad in d['pads']:
   px,py=xy(x+pad['x'],y+pad['y']);c.rect(px-pad['w']*sc/2,py-pad['h']*sc/2,pad['w']*sc,pad['h']*sc,stroke=1,fill=0)
  text(*xy(x,y),comp['ref'],size=6.5,align='center')
 text(20*mm,oy-h*sc-10*mm,f'板框 {w} × {h} mm；厚1.6 mm；四层候选；无铜线、无过孔、无铺铜。','STSong-Light',10)
 text(20*mm,oy-h*sc-17*mm,'坐标(0,0)取板框图示左上角，+X向右、+Y向下；不是机架全局坐标。','STSong-Light',9)
 x0=225*mm;y0=H-37*mm;text(x0,y0,'元件 / 坐标(mm) / 面 / 暂定占位高度(mm)','STSong-Light',10)
 for i,comp in enumerate(p):
  y=y0-7*mm*(i+1);d=F[comp['fp']];text(x0,y,f"{comp['ref']:<7} ({comp['pcb_xy'][0]:5.1f}, {comp['pcb_xy'][1]:5.1f})  {comp['side']}   {d['z']}",size=8)
  text(x0+82*mm,y,comp['value'][:33],size=7)
 text(225*mm,35*mm,'矩形为候选封装/空间限界，不表示厂家完整三维实体。','STSong-Light',10)
 text(225*mm,28*mm,'反馈回路、去耦、插接与散热仍需在原生PCB中优化。','STSong-Light',10)
 c.showPage()
c.save();print('8-page schematic/PCB review PDF generated')
