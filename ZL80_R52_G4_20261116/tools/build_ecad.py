"""Emit KiCad candidate schematics and actual routed copper geometry.
Generator is explicitly not KiCad. Native parse/ERC/DRC must run locally before release.
"""
from pathlib import Path
import json,csv,math,re
from pcb_geometry import load,ROOT,LAYERS
import kicad_base as K
q,n,fx,uid=K.q,K.n,K.fx,K.uid

def footprint(key,d,c,bid,codes,rootid,library=False):
 ref=c['ref'];side=c.get('side','F');at=c.get('pcb_xy',[0,0]);ang=c.get('angle',0);w,h=d['w'],d['h']
 a=[f'(footprint {q(key if library else "ZL80_G4:"+key)}'+(' (version 20240108) (generator "zl80_g4_engineering")' if library else '')+f' (layer "{side}.Cu")']
 if not library:a += [f'(uuid {uid(bid+ref+"fp")}) (at {n(at[0])} {n(at[1])} {ang})',f'(path {q("/"+rootid+"/"+uid(bid+"_G4"+ref))})']
 a += [f'(property "Reference" {q(ref)} (at 0 {n(-h/2-1)} {ang}) (layer "{side}.Fab") {fx(.6)})',f'(property "Value" {q(c["value"])} (at 0 {n(h/2+1)} {ang}) (layer "{side}.Fab") {fx(.6)})','(attr '+('through_hole' if any(p['drill'] for p in d['pads']) else 'smd')+')']
 for layer,extra in [('Fab',0),('CrtYd',0)]:a.append(f'(fp_rect (start {n(-w/2)} {n(-h/2)}) (end {n(w/2)} {n(h/2)}) (stroke (width 0.05) (type default)) (fill none) (layer "{side}.{layer}"))')
 # Small pin-one marking kept on fabrication layer; silk requires native mask review.
 a.append(f'(fp_circle (center {n(-w/2+.3)} {n(-h/2+.3)}) (end {n(-w/2+.45)} {n(-h/2+.3)}) (stroke (width .12) (type default)) (fill none) (layer "{side}.Fab"))')
 for p in d['pads']:
  px=p['x']*(-1 if side=='B' else 1);py=p['y'];layers='"*.Cu" "*.Mask"' if p['drill'] else f'"{side}.Cu" "{side}.Paste" "{side}.Mask"'
  st=f'(pad {q(p["num"])} {"thru_hole" if p["drill"] else "smd"} {"circle" if p["drill"] else "rect"} (at {n(px)} {n(py)} {ang}) (size {n(p["w"])} {n(p["h"])})'
  if p['drill']:st+=f' (drill {n(p["drill"])})'
  st+=f' (layers {layers})';net=c['nets'].get(p['num'],'')
  if codes and net:st+=f' (net {codes[net]} {q(net)})'
  a.append(st+')')
 if not library:
  a.append(f'(model "${{KIPRJMOD}}/../../models3d/{key}.step" (offset (xyz 0 0 0)) (scale (xyz 1 1 1)) (rotate (xyz 0 0 0)))')
 return '\n'.join(a+[')'])
def pcb(b,cs,F,rt):
 bid=b['id'];W,H=b['size_mm'];codes={v:i+1 for i,v in enumerate(sorted({v for c in cs for v in c['nets'].values() if v}))}
 a=[f'(kicad_pcb (version 20240108) (generator "zl80_g4_engineering") (general (thickness 1.6)) (paper "A3")',f'(title_block (title "{bid} G4 routing candidate") (rev "G4-E02-D01-NOT-RELEASED"))', '(layers (0 "F.Cu" signal) (1 "In1.Cu" power) (2 "In2.Cu" signal) (31 "B.Cu" signal) (34 "B.Paste" user) (35 "F.Paste" user) (36 "B.SilkS" user) (37 "F.SilkS" user) (38 "B.Mask" user) (39 "F.Mask" user) (40 "Dwgs.User" user) (44 "Edge.Cuts" user) (46 "B.CrtYd" user) (47 "F.CrtYd" user) (48 "B.Fab" user) (49 "F.Fab" user))', '''(setup (stackup
(layer "F.SilkS" (type "Top Silk Screen")) (layer "F.Mask" (type "Top Solder Mask"))
(layer "F.Cu" (type "copper") (thickness 0.035))
(layer "dielectric 1" (type "prepreg") (thickness 0.18) (material "FR4_CANDIDATE") (epsilon_r 4.2) (loss_tangent 0.02))
(layer "In1.Cu" (type "copper") (thickness 0.035))
(layer "dielectric 2" (type "core") (thickness 1.10) (material "FR4_CANDIDATE") (epsilon_r 4.2) (loss_tangent 0.02))
(layer "In2.Cu" (type "copper") (thickness 0.035))
(layer "dielectric 3" (type "prepreg") (thickness 0.18) (material "FR4_CANDIDATE") (epsilon_r 4.2) (loss_tangent 0.02))
(layer "B.Cu" (type "copper") (thickness 0.035)) (layer "B.Mask" (type "Bottom Solder Mask")) (layer "B.SilkS" (type "Bottom Silk Screen"))
(copper_finish "ENIG_CANDIDATE") (dielectric_constraints no))
(pad_to_mask_clearance 0.05) (solder_mask_min_width 0.10) (aux_axis_origin 0 0) (grid_origin 0 0))''','(net 0 "")']
 a +=[f'(net {v} {q(k)})' for k,v in codes.items()]
 for i,(p,z) in enumerate(zip([(0,0),(W,0),(W,H),(0,H)],[(W,0),(W,H),(0,H),(0,0)])):
  a.append(f'(gr_line (start {p[0]} {p[1]}) (end {z[0]} {z[1]}) (stroke (width .05) (type default)) (layer "Edge.Cuts") (uuid {uid(bid+"edge"+str(i))}))')
 for i,(x,y) in enumerate(b['holes']):
  dia=2.2 if W<30 else 3.2
  a.append(f'(footprint "ZL80_G4:NPTH" (layer "F.Cu") (uuid {uid(bid+"hole"+str(i))}) (at {x} {y}) (attr board_only exclude_from_pos_files exclude_from_bom) (property "Reference" "H{i+1}" (at 0 -2) (layer "F.Fab") {fx(.5)}) (pad "" np_thru_hole circle (at 0 0) (size {dia} {dia}) (drill {dia}) (layers "*.Cu" "*.Mask")))')
 for c in cs:a.append(footprint(c['fp'],F[c['fp']],c,bid,codes,uid(bid+'_G4')))
 for i,t in enumerate(rt['tracks']):
  for j,(p,z) in enumerate(zip(t['points'],t['points'][1:])):
   a.append(f'(segment (start {n(p[0])} {n(p[1])}) (end {n(z[0])} {n(z[1])}) (width {t["width"]}) (layer {q(LAYERS[t["layer"]])}) (net {codes[t["net"]]}) (uuid {uid(bid+"track"+str(i)+"_"+str(j))}))')
 for i,v in enumerate(rt['vias']):a.append(f'(via (at {n(v["x"])} {n(v["y"])}) (size {v["size"]}) (drill {v["drill"]}) (layers "F.Cu" "B.Cu") (net {codes[v["net"]]}) (uuid {uid(bid+"via"+str(i))}))')
 g='GND' if bid in ['B06','B07'] else 'AGND'
 # Actual plane definition, deliberately no fabricated filled_polygons. Refill + native DRC required.
 a += [f'''(zone (net {codes[g]}) (net_name "{g}") (layer "In1.Cu") (uuid {uid(bid+"plane")}) (hatch edge 0.5)
(connect_pads (clearance 0.2)) (min_thickness 0.2) (filled_areas_thickness no)
(fill yes (thermal_gap 0.2) (thermal_bridge_width 0.2))
(polygon (pts (xy 0.4 0.4) (xy {W-.4} 0.4) (xy {W-.4} {H-.4}) (xy 0.4 {H-.4}))))''']
 if rt['input_keepout']:
  x1,y1,x2,y2=rt['input_keepout']
  for l in ['In1.Cu','In2.Cu']:
   a.append(f'''(zone (net 0) (net_name "") (layer "{l}") (uuid {uid(bid+l+"input_keepout")}) (hatch edge 0.5)
(keepout (tracks not_allowed) (vias not_allowed) (pads allowed) (copperpour not_allowed) (footprints allowed))
(polygon (pts (xy {n(x1)} {n(y1)}) (xy {n(x2)} {n(y1)}) (xy {n(x2)} {n(y2)}) (xy {n(x1)} {n(y2)}))))''')
 a.append(f'(gr_text "{bid} G4 | REVIEW ONLY | NATIVE DRC REQUIRED" (at {W/2} {H+4}) (layer "Dwgs.User") {fx(.7)})')
 return '\n'.join(a+[')'])
def main():
 D,F,P=load();lib=ROOT/'electronics/libraries';records=[];scenes=[]
 # Keep library symbol defaults, override each instantiated footprint to the actual physical choice.
 (lib/'ZL80_G4.kicad_sym').write_text('(kicad_symbol_lib (version 20231120) (generator "zl80_g4_engineering")\n'+'\n'.join(K.libsym(k,False) for k in K.S)+'\n)')
 for key,d in F.items():(lib/'ZL80_G4.pretty'/f'{key}.kicad_mod').write_text(footprint(key,d,dict(ref='REF**',value=key,nets={},pcb_xy=[0,0],side='F',angle=0),'',{},'',True))
 for b in D['boards']:
  bid=b['id'];project=bid+'_G4';out=ROOT/'electronics/projects'/bid;out.mkdir(exist_ok=True)
  txt,rec,scene=K.schematic(b)
  # Footprint property must be the component instance choice, not just library default.
  for c in b['components']:
   if 'fp' not in c:continue
   old='ZL80_G4:'+str(K.S[c['kind']]['fp']);new='ZL80_G4:'+c['fp'];x,y=c['xy']
   txt=txt.replace(f'(property "Footprint" {q(old)} (at {n(x)} {n(y)}',f'(property "Footprint" {q(new)} (at {n(x)} {n(y)}')
  (out/(project+'.kicad_sch')).write_text(txt);records+=rec;scenes.append(scene)
  rt=json.loads((ROOT/'engineering'/f'{bid}_routing.json').read_text());cs=[c for c in P if c['board']==bid]
  (out/(project+'.kicad_pcb')).write_text(pcb(b,cs,F,rt))
  pro={'meta':{'filename':project+'.kicad_pro','version':1},'text_variables':{'DESIGN_STATUS':'REVIEW_ONLY_BLOCKED'},'board':{'design_settings':{'rules':{'min_clearance':.15,'min_track_width':.15,'min_via_annular_width':.15,'min_via_diameter':.6,'min_through_hole_diameter':.3,'min_copper_edge_clearance':.25}}},'schematic':{'meta':{'version':1}}}
  (out/(project+'.kicad_pro')).write_text(json.dumps(pro,indent=2))
  (out/(project+'.kicad_dru')).write_text('''(version 1)
(rule "G4 minimum copper clearance" (constraint clearance (min 0.15mm)))
(rule "G4 minimum width" (constraint track_width (min 0.15mm)))
(rule "G4 board edge clearance" (constraint edge_clearance (min 0.25mm)))
''')
  (out/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "ZL80_G4") (type "KiCad") (uri "${KIPRJMOD}/../../libraries/ZL80_G4.kicad_sym") (options "") (descr "G4 candidate; native validation required")))')
  (out/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "ZL80_G4") (type "KiCad") (uri "${KIPRJMOD}/../../libraries/ZL80_G4.pretty") (options "") (descr "G4 candidate land patterns")))')
  (out/'README.md').write_text(f'# {bid} G4\n\n{project}.kicad_pro 为入口。原理图拓扑继承G2；PCB包含实际铜线和过孔。B01仅输入/TIA关键网布线，其余故意保持未连。所有铺铜必须在KiCad重新填充，运行ERC/DRC和原理图一致性检查。禁止直接下单。\n\nG4所有小板无台架实测，无原生KiCad验证。0402焊接/清洗、接插件对接、PD方向和插针需人工复核。\n')
 with (ROOT/'engineering/pin_net_types.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
 (ROOT/'engineering/schematic_scene.json').write_text(json.dumps(scenes,ensure_ascii=False,indent=2))
 print('Written 4 candidate KiCad projects, copper+vias+unfilled planes; no Gerber')
if __name__=='__main__':main()
