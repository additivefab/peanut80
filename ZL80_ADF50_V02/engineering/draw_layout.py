"""Side-view layout (Y horizontal, Z vertical, 1 px = 1 mm) of ADF50 V0.2 from calculated geometry. Not CAD."""
import json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'engineering'));import calculate as C
p=json.loads((ROOT/'engineering/parameters.json').read_text());r=C.calculate(p);pa=r['path'];e=r['envelope']
a=math.radians(p['magazine_angle_deg_from_horizontal']);u=(math.cos(a),math.sin(a));n=(u[1],-u[0])
X=lambda y:y+450;Z=lambda z:700-z
o=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 760" font-family="PingFang SC,Microsoft YaHei,sans-serif" font-size="11">',
   '<rect width="1000" height="760" fill="#ffffff"/>',
   f'<line x1="0" y1="{Z(0)}" x2="1000" y2="{Z(0)}" stroke="#999"/>',
   f'<rect x="{X(-150)}" y="{Z(300)}" width="300" height="300" fill="#eef1f4" stroke="#556"/>',
   f'<text x="{X(-60)}" y="{Z(200)}" fill="#334">ZL80 扫描仪 320×300×300</text>',
   f'<line x1="{X(0)}" y1="{Z(300)}" x2="{X(0)}" y2="{Z(110)}" stroke="#c33" stroke-dasharray="4 3"/><text x="{X(4)}" y="{Z(250)}" fill="#c33">扫描线 Y=0</text>']
for y in (-42,42):o.append(f'<circle cx="{X(y)}" cy="{Z(100)}" r="10" fill="none" stroke="#334"/><circle cx="{X(y)}" cy="{Z(120)}" r="10" fill="none" stroke="#334"/>')
o.append(f'<path d="M {X(-52)} {Z(84)} L {X(32)} {Z(84)}" stroke="#2a7" stroke-width="2" fill="none"/><text x="{X(-48)}" y="{Z(70)}" fill="#2a7">同步带联动两只下辊（单电机）</text>')
yh,R,zf=p['horizontal_run_start_y_mm'],p['guided_turn_radius_mm'],p['scan_plane_z_mm'];ae=pa['arc_end_yz'];top=pa['magazine_top_yz'];dam=pa['dam_yz']
t=math.radians(p['output_tray_tilt_deg']);y0=p['scanner_rear_panel_y_mm']+10;L=p['output_tray_size_mm'][1]
o.append(f'<path d="M {X(y0+L*math.cos(t))} {Z(zf-6-L*math.sin(t))} L {X(y0)} {Z(zf-6)}" stroke="#555" stroke-width="5" fill="none"/><text x="{X(y0+60)}" y="{Z(zf-90)}">收片托盘 340，倾 {p["output_tray_tilt_deg"]}°</text>')
o.append(f'<path d="M {X(e["rear_y_mm"]-340)} {Z(zf)} L {X(yh)} {Z(zf)} A {R} {R} 0 0 1 {X(ae[0])} {Z(ae[1])} L {X(top[0])} {Z(top[1])}" stroke="#06c" stroke-width="2.2" fill="none"/>')
d=p['magazine_stack_depth_budget_mm'];q=lambda pt,k:(pt[0]+k*n[0],pt[1]+k*n[1])
P=[dam,top,q(top,d),q(dam,d)];o.append('<polygon points="'+' '.join(f'{X(a_)},{Z(b_)}' for a_,b_ in P)+'" fill="#cfe3f7" stroke="#06c"/>')
for key,lab,dy in (('double_station_yz','双张检测站',10),('retard_nip_yz','限矩反向辊',6),('dam_yz','斜坝（托住整叠下缘）',2)):
    y,z=pa[key];o.append(f'<circle cx="{X(y)}" cy="{Z(z)}" r="4" fill="#e80"/><text x="{X(y)-12}" y="{Z(z)+dy}" fill="#a50" text-anchor="end">{lab}</text>')
pk=(dam[0]+25*u[0]-10*n[0],dam[1]+25*u[1]-10*n[1]);o.append(f'<circle cx="{X(pk[0])}" cy="{Z(pk[1])}" r="10" fill="none" stroke="#a50" stroke-width="1.5"/><text x="{X(pk[0])-16}" y="{Z(pk[1])-10}" fill="#a50" text-anchor="end">拾取辊（配重臂，压自由面）</text>')
o+=[f'<text x="{X(top[0])+45}" y="{Z(top[1])+60}" fill="#06c">片仓 {p["magazine_angle_deg_from_horizontal"]}°，50 张靠在托板上</text>',
    f'<text x="{X(yh-R)-18}" y="{Z(zf)+34}" fill="#06c">R{R} 转 {pa["turn_angle_deg"]:.0f}°</text>',
    f'<circle cx="{X(-35)}" cy="{Z(zf)}" r="3" fill="#c33"/><text x="{X(-135)}" y="{Z(zf)+16}" fill="#c33">停片前沿 Y=-35</text>',
    f'<text x="{X(-290)}" y="{Z(0)+20}">检测站到停片前沿 {pa["qualified_path_to_park_mm"]:.0f} mm（需 {pa["qualified_path_required_mm"]:.1f}）</text>',
    f'<text x="{X(-290)}" y="{Z(0)+36}">工作包络 宽{e["working_envelope_mm_WDH"][0]:.0f} × 深{e["working_envelope_mm_WDH"][1]:.0f} × 高{e["working_envelope_mm_WDH"][2]:.0f} mm；V0.1 为 350×1100×550</text>',
    f'<text x="{X(-290)}" y="{Z(0)+52}">侧视功能布局，1 px = 1 mm；不是制造 CAD</text>','</svg>']
(ROOT/'docs/ADF50_V02_布局.svg').write_text('\n'.join(o),encoding='utf-8')
