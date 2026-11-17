"""Side views (Y horizontal, Z vertical) of ADF50 V0.3 from the parameters: whole machine at 1 px = 1 mm and the
entry zone at 4 px = 1 mm. Functional layout, not CAD."""
import json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'engineering'));import calculate as C
p=json.loads((ROOT/'engineering/parameters.json').read_text());r=C.calculate(p);st=r['path']['stations_y_mm'];e=r['envelope']
zf=p['scan_plane_z_mm'];FONT='font-family="PingFang SC,Microsoft YaHei,sans-serif"'
def view(k,y0,ztop,w,h,fs):
    X=lambda y:(y-y0)*k;Z=lambda z:(ztop-z)*k
    o=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" {FONT} font-size="{fs}">',f'<rect width="{w}" height="{h}" fill="#ffffff"/>']
    def roller(y,z,d,c='#334',f='none'):o.append(f'<circle cx="{X(y)}" cy="{Z(z)}" r="{d/2*k}" fill="{f}" stroke="{c}" stroke-width="1.4"/>')
    def text(y,z,s,c='#223',a='start',dy=0):o.append(f'<text x="{X(y)}" y="{Z(z)+dy}" fill="{c}" text-anchor="{a}">{s}</text>')
    def line(y1,z1,y2,z2,c='#555',sw=1,dash=''):o.append(f'<line x1="{X(y1)}" y1="{Z(z1)}" x2="{X(y2)}" y2="{Z(z2)}" stroke="{c}" stroke-width="{sw}" {dash}/>')
    def rect(y1,z1,y2,z2,f,s='#556',op=1):o.append(f'<rect x="{X(y1)}" y="{Z(z2)}" width="{(y2-y1)*k}" height="{(z2-z1)*k}" fill="{f}" stroke="{s}" fill-opacity="{op}"/>')
    return o,X,Z,roller,text,line,rect
# ---------- whole machine
o,X,Z,roller,text,line,rect=view(1,-530,330,1060,420,11)
line(-530,0,530,0,'#999');rect(-150,0,150,300,'#eef1f4');text(-60,262,'ZL80 扫描仪 320×300×300','#334')
line(0,300,0,zf,'#c33',1,'stroke-dasharray="4 3"');text(4,280,'扫描线 Y=0','#c33')
rect(st['magazine_rear_y']-4,zf-40,-150,p['magazine_lid_top_z_mm'],'#f4f7fa','#89a');text(-490,p['magazine_lid_top_z_mm']+6,'片仓（带遮光盖），平放 50 张','#06c')
tr=r['path']['lift_travel_mm'];rear=st['magazine_rear_y']+12;dam=st['dam_top_y']
o.append(f'<polygon points="{X(rear)},{Z(zf-2.5)} {X(dam)},{Z(zf-2.5)} {X(dam)},{Z(zf-2.5-17.5)} {X(rear)},{Z(zf-2.5-3)}" fill="#cfe3f7" stroke="#06c"/>')
line(rear,zf-6,dam,zf-21,'#555',3);text(-420,zf-34,'升片板：后端铰接，前端升 %.1f mm'%tr,'#555')
for y in (-42,42):roller(y,zf+10.1,20);roller(y,zf-10.1,20)
roller(st['feed_nip_y'],zf+10,20,'#a50');roller(st['feed_nip_y'],zf-10,20,'#a50');roller(st['pick_contact_y'],zf-2.5+10,20,'#a50')
roller(st['eject_nip_y'],zf+10,20,'#2a7');roller(st['eject_nip_y'],zf-10,20,'#2a7')
line(st['magazine_rear_y']+12,zf,st['output_tray_end_y']-330,zf,'#06c',2.2)
t=math.radians(p['output_tray_tilt_deg']);y0=160
line(y0,zf-6,y0+340*math.cos(t),zf-6-340*math.sin(t),'#555',5);text(y0+70,zf-80,'收片托盘 340，倾 %d°'%p['output_tray_tilt_deg'])
rect(150.5,zf+41,st['output_tray_end_y']+4,zf+45,'#f4f7fa','#89a');text(300,zf+52,'收片遮光罩','#555')
text(-205,zf+62,'拾取辊+送片辊','#a50');text(120,zf+62,'排片辊','#2a7',a='end')
text(-520,-18,'片从片堆顶面到收片托盘全程在 Z=%d 平面，0 处弯道；工作包络 宽%d × 深%d × 高%d mm（V0.1 350×1100×550，V0.2 320×785×639）'%(zf,*[round(x) for x in e['working_envelope_mm_WDH']]))
text(-520,-36,'侧视功能布局，1 px = 1 mm；不是制造 CAD');o.append('</svg>')
(ROOT/'docs/ADF50_V03_布局.svg').write_text('\n'.join(o),encoding='utf-8')
# ---------- entry zone detail
o,X,Z,roller,text,line,rect=view(4,-265,172,1000,480,13)
rect(-150,60,-148,172,'#c9d2da');text(-146,166,'前面板 Y=-150','#334')
rect(-112.4,60,-66.4,102,'#f7ecd9','#b83');text(-100,70,'模拟屏蔽罩（R5.2 布局 B）','#b83')
rect(-104.2,60,-102.6,100,'#d9c9a6','#b83')
for z in (98,114):rect(-115,z,-105,z+8,'#dde','#66a')
text(-104,126,'片到位传感器 S03（x=±25）','#66a')
rect(-125,zf+3,-115,zf+25,'#fde3c4','#e80');rect(-125,zf-24,-115,zf-3,'#fde3c4','#e80');text(-127,zf+46,'超声双张检测（x=0）','#a50')
roller(st['feed_nip_y'],zf+10,20,'#a50','#fff4e6');roller(st['feed_nip_y'],zf-10,20,'#a50','#fff4e6')
text(-147,zf+30,'送片辊（固定轴）','#a50');text(-152,zf-36,'限矩反转辊（扫描时下落脱开）','#a50',a='end')
py=st['pick_contact_y'];roller(py,zf-2.5+10,20,'#a50','#fff4e6');line(py,zf+7.5,st['feed_nip_y'],zf+10,'#a50',2.5);text(py+8,zf+34,'拾取辊：配重臂绕送片辊轴摆动','#a50',a='end')
dam=st['dam_top_y'];o.append(f'<polygon points="{X(dam-2.5/math.tan(math.radians(55)))},{Z(zf-2.5)} {X(dam)},{Z(zf)} {X(-150)},{Z(zf)} {X(-150)},{Z(zf-24)} {X(dam-2.5/math.tan(math.radians(55)))},{Z(zf-24)}" fill="#e4e8ec" stroke="#556"/>')
text(dam+4,zf-9,'斜坝','#334',a='middle')
rect(-265,zf-2.5-10,dam-1.8,zf-2.5,'#cfe3f7','#06c');text(-262,zf-6.5,'片堆（顶面恒在 Z=107.5）','#046')
line(-265,zf-12.8,dam-1.8,zf-14,'#555',3);line(-265,zf,-40,zf,'#06c',2)
roller(-42,zf+10.1,20);roller(-42,zf-10.1,20);text(-42,zf+26,'扫描段入口辊','#334',a='middle')
for y,lab in ((dam,'坝顶 -158'),(st['feed_nip_y'],'-138'),(-120,'-120'),(-110,'-110'),(-42,'-42')):line(y,64,y,60,'#333');text(y,61,lab,'#333',a='middle',dy=28)
text(-262,56,'进片区放大，4 px = 1 mm；尺寸为名义占位','#333');o.append('</svg>')
(ROOT/'docs/ADF50_V03_进片区.svg').write_text('\n'.join(o),encoding='utf-8')
