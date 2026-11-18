"""Route figure for W13: top view (X-Y), side view (X-Z) and the B05 board (local coordinates). Schematic from nominal AABBs; not CAD."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import geom_e as g
import fitz
EL=g.E/'electrical'
k=1.55;PAD=14
def panel(title,ix,iy,xr,yr,boxes,routes,w13,marks,flipy=False):
    """ix,iy select the two plotted global axes (0=x,1=y,2=z)."""
    W=(xr[1]-xr[0])*k;H=(yr[1]-yr[0])*k
    X=lambda v:(v-xr[0])*k;Y=lambda v:(yr[1]-v)*k
    o=[f'<g><text x="0" y="-6" font-size="13" font-weight="bold" fill="#222">{title}</text><rect x="0" y="0" width="{W}" height="{H}" fill="#fff" stroke="#999"/>']
    for name,b,col in boxes:
        x0,x1=b[ix],b[ix+3];y0,y1=b[iy],b[iy+3]
        if x1<xr[0] or x0>xr[1] or y1<yr[0] or y0>yr[1]:continue
        o.append(f'<rect x="{X(max(x0,xr[0]))}" y="{Y(min(y1,yr[1]))}" width="{(min(x1,xr[1])-max(x0,xr[0]))*k}" height="{(min(y1,yr[1])-max(y0,yr[0]))*k}" fill="{col}" fill-opacity="0.55" stroke="#889" stroke-width="0.6"/>')
    for rid,pts,col in routes:
        o.append('<polyline fill="none" stroke="'+col+'" stroke-width="1.6" stroke-opacity="0.8" points="'+' '.join(f'{X(p[ix]):.1f},{Y(p[iy]):.1f}' for p in pts)+'"/>')
        o.append(f'<text x="{X(pts[0][ix])+3:.1f}" y="{Y(pts[0][iy])-3:.1f}" font-size="9" fill="{col}">{rid}</text>')
    o.append('<polyline fill="none" stroke="#d11" stroke-width="3" points="'+' '.join(f'{X(p[ix]):.1f},{Y(p[iy]):.1f}' for p in w13)+'"/>')
    for t,p,col in marks:o.append(f'<circle cx="{X(p[ix]):.1f}" cy="{Y(p[iy]):.1f}" r="4" fill="{col}"/><text x="{X(p[ix])-(62 if t.startswith("G3E-05") else -6):.1f}" y="{Y(p[iy])+(-8 if t.startswith("G3E-05") else 4):.1f}" font-size="10" fill="{col}">{t}</text>')
    o.append('</g>');return o,W,H
frames=[(i['name'],i['aabb'],'#c8d0da') for i in g.INST if i['group'] in ('frame','preload','bearing_cap','slider','bearing','drive','encoder','encoder_mount')]
other=[(i['name'],i['aabb'],'#e0cfa0') for i in g.INST if i['name'] in ('MOTOR_BRACKET','R5_Optic_post-72','R5_Optic_post72','COUPLER_GUARD','DRIVE_MOTOR','LIFT_BAR_42','LIFT_BAR_-42')]
b05=[(i['name'],i['aabb'],'#bfe3c8') for i in g.INST if i['name']=='R5_运动驱动与传感接口板']
boards=[(i['name'],i['aabb'],'#d9e6c8') for i in g.INST if i['name'].startswith('R5_B0') and 'post' not in i['name']]
oth=[(rid,[tuple(p) for p in r['points']],'#7a7a7a') for rid,r in g.ROUTES.items() if rid in ('W03','W04','W05','W09','W11','W12')]
P=g.fillet_points(g.W13,15.0)
marks=[('G3E-03',(91.8,42.0,120.1),'#195'),('G3E-05/06',(119.3,39.0,131.0),'#a40'),('B05 J5',g.J5G,'#05a')]
svg=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1180 780" font-family="PingFang SC,Microsoft YaHei,sans-serif"><rect width="100%" height="100%" fill="#fff"/>']
# top view X-Y
t,W1,H1=panel('俯视（X 向右，Y 向后）：W13 红色，灰色为 W03/04/05/09/11/12 走廊',0,1,(-165,165),(-30,100),frames+other+boards+b05,oth,P,marks)
svg.append('<g transform="translate(14,28)">'+''.join(t)+'</g>')
s,W2,H2=panel('侧视（X 向右，Z 向上）',0,2,(-165,165),(10,180),frames+other+boards+b05,oth,P,marks)
svg.append(f'<g transform="translate(14,{28+H1+34})">'+''.join(s)+'</g>')
# B05 board (local coordinates)
bk=5.3;bx=14+W1+30;by=28
bd=['<g>',f'<text x="{bx}" y="{by-6}" font-size="13" font-weight="bold" fill="#222">B05 板面（板坐标 mm，65×100）</text>',f'<rect x="{bx}" y="{by}" width="{65*bk}" height="{100*bk}" fill="#f4faf0" stroke="#555"/>']
for c in g.board_check()['components']:
    r=c['rect'];new=c['ref'] in ('U3','J5') or (c['ref']=='J3');col='#f9c98a' if new else '#d5d9de'
    bd.append(f'<rect x="{bx+r[0]*bk}" y="{by+(100-r[3])*bk}" width="{(r[2]-r[0])*bk}" height="{(r[3]-r[1])*bk}" fill="{col}" stroke="#444" stroke-width="0.8"/><text x="{bx+r[0]*bk+2}" y="{by+(100-r[3])*bk+11}" font-size="10" fill="#222">{c["ref"]}</text>')
for hx,hy in g.BOARD['holes']:bd.append(f'<circle cx="{bx+hx*bk}" cy="{by+(100-hy)*bk}" r="{1.6*bk}" fill="#fff" stroke="#555"/>')
bd.append(f'<text x="{bx}" y="{by+100*bk+16}" font-size="10" fill="#c60">橙色：本设计新增或改动（U3、J5、J3 加长）；灰色：G4 原位置</text></g>')
svg+=bd;svg.append('</svg>')
(EL/'_r.svg').write_text('\n'.join(svg),encoding='utf-8')
pm=fitz.open(str(EL/'_r.svg'))[0].get_pixmap(matrix=fitz.Matrix(1.7,1.7));pm.save(str(EL/'ECR_G3_01_E_走线与板面.png'));(EL/'_r.svg').unlink();print('route fig ok')
