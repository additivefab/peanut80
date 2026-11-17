"""Coordinate diagram only; not a detailed CAD assembly or interference result."""
from pathlib import Path
import math,html,json
R=Path(__file__).resolve().parents[1];p=json.loads((R/'engineering/parameters.json').read_text())
s=1.08;ox=690;oy=690
X=lambda y:ox+y*s
Y=lambda z:oy-z*s
els=['<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="880" viewBox="0 0 1500 880"><rect width="1500" height="880" fill="white"/><defs><marker id="a" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#236d9a"/></marker></defs>']
def text(x,y,t,size=20,color='#19364e',anchor='start'):
 els.append(f'<text x="{x}" y="{y}" fill="{color}" font-family="Noto Sans CJK SC,sans-serif" font-size="{size}" text-anchor="{anchor}">{html.escape(t)}</text>')
def line(a,b,color='#236d9a',width=2,dash='',arrow=False):
 els.append(f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" stroke="{color}" stroke-width="{width}" stroke-dasharray="{dash}" '+('marker-end="url(#a)"' if arrow else '')+'/>')
def rect(x,y,w,h,fill='#eaf2f7',stroke='#5d798f'):
 els.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
def poly(pts,fill='#dceae2',stroke='#388464'):
 els.append('<polygon points="'+' '.join(f'{x},{y}' for x,y in pts)+f'" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
rect(25,22,1450,70,'#173a56','#173a56');text(50,67,'ZL80 + ADF50  |  50 × 80 × 300 mm  重力供片一体化接口示意',29,'white')
text(40,120,'侧视：横轴为走片方向 Y，纵轴为高度 Z；全部新增坐标是设计分配，非已完成装配CAD。',20)
# Main chassis profile only. Source source coordinates are discussed nominal values.
rect(X(-150),Y(300),300*s,300*s,'#f2f5f7','#8194a2');text(X(0),Y(275),'原ZL80扫描主机',23,anchor='middle');text(X(0),Y(248),'光学/PMT与亚克力收光路径不改',15,anchor='middle')
# gravity magazine connects via circular arc to horizontal buffer
r=60;a=math.radians(80);end_y=-410;start_y=end_y-r*math.sin(a);start_z=110+r*(1-math.cos(a));length=330
st=(start_y,start_z);en=(start_y-length*math.cos(a),start_z+length*math.sin(a));normal=(math.sin(a),math.cos(a));depth=35
poly([(X(st[0]),Y(st[1])),(X(en[0]),Y(en[1])),(X(en[0]+depth*normal[0]),Y(en[1]+depth*normal[1])),(X(st[0]+depth*normal[0]),Y(st[1]+depth*normal[1]))])
text(285,200,'A01 近立式片仓',23);text(285,231,'80°起点；75–85°可调',19);text(285,260,'50张；堆叠空间35 mm',19)
line((X(en[0]+10),Y(en[1]-30)),(X(st[0]-5),Y(st[1]+40)),arrow=True,width=4)
text(288,435,'托挡+剥离+分离辊',18);line((300,445),(X(start_y)+20,Y(start_z)-15),arrow=True)
# Arc: guide trajectory along tangent from -80 deg to horizontal
pts=[]
for i in range(51):
 theta=a*(1-i/50);yy=end_y-r*math.sin(theta);zz=110+r*(1-math.cos(theta));pts.append((X(yy),Y(zz)))
els.append('<polyline points="'+' '.join(f'{x},{y}'for x,y in pts)+'" fill="none" stroke="#248663" stroke-width="5"/>')
text(X(-450),Y(80),'R60导向试验件',16,anchor='middle')
# final inspection and buffer
rect(X(-400),Y(190),20*s,150*s,'#e4eff8','#236d9a');text(X(-390),Y(213),'DS整张检测',18,anchor='middle')
line((X(-410),Y(110)),(X(460),Y(110)),color='#1d6693',width=3)
# one fully qualified 300mm sheet parked upstream
rect(X(-335),Y(113),300*s,6,'#e4ad45','#9d6b1d');text(X(-185),Y(150),'已分离300 mm单张，前沿停在Y=-35',18,anchor='middle')
for yy in [-300,-180,-75]:
 for zz in [100,120]:
  els.append(f'<circle cx="{X(yy)}" cy="{Y(zz)}" r="{10*s}" fill="white" stroke="#388464" stroke-width="2"/>')
text(X(-260),Y(65),'缓冲夹持辊：接管后全部抬起/卸载',17,anchor='middle')
for yy in [-42,42]:
 for zz in [99.9,120.1]:
  els.append(f'<circle cx="{X(yy)}" cy="{Y(zz)}" r="{10*s}" fill="#c7dbe6" stroke="#234d68" stroke-width="2"/>')
line((X(0),Y(200)),(X(0),Y(82)),color='#cf462d',width=3,arrow=True)
text(X(0),Y(218),'扫描线Y=0',17,'#b43c29',anchor='middle')
text(X(-42),Y(48),'入口主动接管',16,anchor='end');text(X(42),Y(48),'出口同步接管',16)
# output catching deck and tray shown as separate stages
rect(X(150),Y(85),340*s,35*s,'#e2e9ed','#667e8e');text(X(325),Y(172),'A11 低阻接片 / 收片盘',23,anchor='middle');text(X(325),Y(143),'尾端越过出口辊后才加速、堆叠',17,anchor='middle')
for i in range(5):line((X(170),Y(58+i*2)),(X(460),Y(58+i*2)),color='#839daf',width=1)
text(X(325),Y(25),'60张容量设计；首版无下一张并行上片',17,anchor='middle')
# dimensions
for a0,a1,z,label in [(-390,-35,-35,'最终双张站 → 停片前沿：355 mm'),(-560,550,-80,'运行深度约1100 mm（含供片和出片空间）')]:
 yy=Y(z);line((X(a0),yy),(X(a1),yy));line((X(a0),yy-8),(X(a0),yy+8));line((X(a1),yy-8),(X(a1),yy+8));text((X(a0)+X(a1))/2,yy+28,label,18,anchor='middle')
text(40,855,'ADF50-V0.1 / 2026-11-16 · 路径/功能示意，不含全部辊轴、托趾细节、支架、线束和光学安全遮罩。',17,'#6b7d89')
els.append('</svg>');(R/'docs/ADF50_布局示意.svg').write_text('\n'.join(els))
import cairosvg
cairosvg.svg2png(bytestring='\n'.join(els).encode(),write_to=str(R/'docs/ADF50_布局示意.png'),output_width=1800,output_height=1056)
print('Layout diagram saved')
