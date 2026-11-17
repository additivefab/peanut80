"""Independent vector rendering of the actual circuit graph, NOT KiCad export."""
from pathlib import Path
import json,sys,math
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from kicad_base import shapes,S
from sexpr import loads,child,children
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
D=R/'docs';D.mkdir(exist_ok=True)
scenes=json.loads((R/'engineering/schematic_scene.json').read_text());placements=json.loads((R/'engineering/placements.json').read_text());F=json.loads((R/'engineering/footprints.json').read_text());boards=json.loads((R/'engineering/circuits.json').read_text())['boards']
W,H=420*mm,297*mm
c=canvas.Canvas(str(D/'ZL80_G4_四板原理图审查.pdf'),pagesize=(W,H))
def text(x,y,s,font='Helvetica',size=7,align='left'):
 c.setFont(font,size);f={'left':c.drawString,'right':c.drawRightString,'center':c.drawCentredString}[align];f(x,y,s)
def header(title,page):
 c.setFillColorRGB(.07,.16,.25);c.rect(0,H-20*mm,W,20*mm,fill=1,stroke=0);c.setFillColorRGB(1,1,1);text(12*mm,H-12*mm,title,'STSong-Light',17)
 c.setFillColorRGB(0,0,0);text(12*mm,8*mm,'G4-E02 D01  |  继承G2电路拓扑 / 仅审查用途 / 非制造放行  |  独立矢量渲染，不是KiCad原生验证','STSong-Light',9);text(W-12*mm,8*mm,str(page),size=9,align='right')
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
c.save();print("4-page G4 schematic readback rendered")
