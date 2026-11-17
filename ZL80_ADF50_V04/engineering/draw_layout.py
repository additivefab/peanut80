"""Side view (Y horizontal, Z vertical, 1.25 px = 1 mm) of ADF50 V0.4 from calculated geometry. Functional layout, not CAD."""
import json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'engineering'));import calculate as C
p=json.loads((ROOT/'engineering/parameters.json').read_text());r=C.calculate(p);G=C.geometry(p);e=r['envelope'];pa=r['path']
k=1.25;Y0=-470;ZT=600;X=lambda y:(y-Y0)*k;Z=lambda z:(ZT-z)*k;W,H=int((440-Y0)*k),int((ZT+70)*k)
zf=p['scan_plane_z_mm'];R=G['R'];a,b=G['a'],G['b'];nt,n2=G['n_tray'],G['n_bin']
o=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="PingFang SC,Microsoft YaHei,sans-serif" font-size="13">',f'<rect width="{W}" height="{H}" fill="#ffffff"/>']
def line(p1,p2,c='#555',sw=1,extra=''):o.append(f'<line x1="{X(p1[0])}" y1="{Z(p1[1])}" x2="{X(p2[0])}" y2="{Z(p2[1])}" stroke="{c}" stroke-width="{sw}" {extra}/>')
def poly(pts,f,s,op=1):o.append('<polygon points="'+' '.join(f'{X(y)},{Z(z)}' for y,z in pts)+f'" fill="{f}" stroke="{s}" fill-opacity="{op}"/>')
def roller(c,d,col='#334'):o.append(f'<circle cx="{X(c[0])}" cy="{Z(c[1])}" r="{d/2*k}" fill="#ffffff" stroke="{col}" stroke-width="1.4"/>')
def text(pt,s,c='#223',anchor='start',dx=0,dy=0):o.append(f'<text x="{X(pt[0])+dx}" y="{Z(pt[1])+dy}" fill="{c}" text-anchor="{anchor}">{s}</text>')
off=lambda pt,nrm,d:(pt[0]+d*nrm[0],pt[1]+d*nrm[1])
line((Y0,0),(440,0),'#999');poly([(-150,0),(150,0),(150,300),(-150,300)],'#eef1f4','#556');text((-70,265),'ZL80 扫描仪 320×300×300','#334')
line((0,300),(0,zf),'#c33',1,'stroke-dasharray="4 3"');text((4,282),'扫描线 Y=0','#c33')
hb,hl=p['magazine_housing_below_path_mm'],p['magazine_lid_above_path_mm']
poly([off(G['entry_bend_start'],nt,hb),off(G['mag_top'],nt,hb),off(G['mag_top'],nt,-hl),off(G['entry_bend_start'],nt,-hl)],'#f4f7fa','#89a')
tr=pa['plate_travel_mm'];poly([G['dam'],G['mag_top'],off(G['mag_top'],nt,tr-3),off(G['dam'],nt,tr-3)],'#cfe3f7','#06c')
poly([off(G['exit_bend_end'],n2,p['output_bin_depth_mm']),off(G['bin_top'],n2,p['output_bin_depth_mm']),off(G['bin_top'],n2,-p['output_bin_front_cover_mm']),off(G['exit_bend_end'],n2,-p['output_bin_front_cover_mm'])],'#f4f7fa','#89a')
poly([off(G['eject_nip'],n2,4),off(G['bin_top'],n2,4),off(G['bin_top'],n2,25),off(G['eject_nip'],n2,25)],'#d9efdf','#2a7')
ce=(G['entry_bend_end'][0],zf+R);cx=(G['exit_bend_start'][0],zf+R)
pin=[(ce[0]-R*math.sin(t),ce[1]-R*math.cos(t)) for t in [a*(1-i/16) for i in range(17)]];pout=[(cx[0]+R*math.sin(t),cx[1]-R*math.cos(t)) for t in [b*i/16 for i in range(17)]]
path=[G['mag_top']]+pin+pout+[G['bin_top']]
o.append('<polyline points="'+' '.join(f'{X(y)},{Z(z)}' for y,z in path)+'" fill="none" stroke="#06c" stroke-width="2.4"/>')
for i in range(1,6):t=a*i/6;roller((ce[0]-(R+6)*math.sin(t),ce[1]-(R+6)*math.cos(t)),10,'#777')
for i in range(1,6):t=b*i/6;roller((cx[0]+(R+6)*math.sin(t),cx[1]-(R+6)*math.cos(t)),10,'#777')
for y in (-42,42):roller((y,zf+10.1),20);roller((y,zf-10.1),20)
roller((p['entry_nip_y_mm'],zf+10),20,'#a50');roller((p['entry_nip_y_mm'],zf-10),20,'#a50')
for key in ('feed_nip','eject_nip'):
    c=G[key];nn=nt if key=='feed_nip' else n2;col='#a50' if key=='feed_nip' else '#2a7';roller(off(c,nn,10),20,col);roller(off(c,nn,-10),20,col)
roller(off(G['pick'],nt,-10),20,'#a50');o.append(f'<circle cx="{X(G["sensor"][0])}" cy="{Z(G["sensor"][1])}" r="4" fill="#e80"/>')
text(G['mag_top'],'片仓 %d°，50 张靠在推片板上'%p['magazine_angle_deg_from_horizontal'],'#06c','start',95,60)
text(G['mag_top'],'（上口装片，片面朝扫描仪）','#06c','start',95,78)
text(off(G['pick'],nt,-10),'拾取辊','#a50','start',22,-6);text(G['feed_nip'],'送片辊 / 限矩反转辊','#a50','start',30,2);text(G['sensor'],'超声双张检测','#a50','start',22,12)
text(G['dam'],'斜坝','#334','end',-46,10)
text((ce[0]-R*math.sin(a/2),ce[1]-R*math.cos(a/2)),'下滑弯道 R%d，转 %d°'%(R,p['magazine_angle_deg_from_horizontal']),'#06c','end',-34,34)
text((ce[0]-R*math.sin(a/2),ce[1]-R*math.cos(a/2)),'外侧托辊，内侧不接触','#555','end',-34,52)
text((p['entry_nip_y_mm'],zf),'入口辊','#a50','middle',0,-34);text((0,zf),'扫描段四辊（沿用）','#334','middle',0,48)
text((cx[0]+R*math.sin(b/2),cx[1]-R*math.cos(b/2)),'上行弯道 R%d，转 %d°'%(R,p['output_bin_angle_deg_from_horizontal']),'#06c','start',40,30)
text(G['eject_nip'],'排片辊（带拨片）','#2a7','start',42,4);text(G['bin_top'],'竖立收片仓 %d°'%p['output_bin_angle_deg_from_horizontal'],'#2a7','start',46,70)
o.append(f'<path d="M {X(-330)} {Z(585)} L {X(-250)} {Z(585)}" stroke="#06c" stroke-width="1.5" marker-end="url(#m)"/><defs><marker id="m" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#06c"/></marker></defs>')
text((-240,580),'走片方向始终朝 +Y，不折回','#06c')
env=[round(x) for x in e['working_envelope_mm_WDH']]
text((Y0+8,-22),'工作包络 宽%d × 深%d × 高%d mm（要求：进深约 700，高度 650 以内）。前伸 %d，后伸 %d；扫描仪顶盖上方无遮挡。'%(*env,round(e['front_protrusion_mm']),round(e['rear_protrusion_mm'])))
text((Y0+8,-44),'侧视功能布局，1.25 px = 1 mm；不是制造 CAD');o.append('</svg>')
(ROOT/'docs/ADF50_V04_布局.svg').write_text('\n'.join(o),encoding='utf-8')
