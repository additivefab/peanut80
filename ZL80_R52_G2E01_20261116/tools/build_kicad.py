#!/usr/bin/env python3
"""Write editable KiCad schematics, local libraries, netlists and UNROUTED PCB candidates.
The scene graph is also rendered independently as PDF; this is NOT KiCad native validation.
"""
from pathlib import Path
import json, uuid, math, csv, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path(__file__).parent))
from design_circuits import S,BOARDS
NS=uuid.UUID('87993508-b1d3-423c-aa23-053cdca3dd90')
def uid(s):return str(uuid.uuid5(NS,str(s)))
def q(s):return json.dumps(str(s),ensure_ascii=False)
def n(v):return ('%.5f'%float(v)).rstrip('0').rstrip('.') or '0'
def fx(sz=1,j='',hide=False):return f'(effects (font (size {n(sz)} {n(sz)}))'+(f' (justify {j})' if j else '')+(' hide' if hide else '')+')'
def prop(k,v,x,y,sz=1,hide=False):return f'(property {q(k)} {q(v)} (at {n(x)} {n(y)} 0) {fx(sz,hide=hide)})'
def poly(pts):return '(polyline (pts '+' '.join(f'(xy {n(x)} {n(y)})' for x,y in pts)+') (stroke (width 0.254) (type default)) (fill (type none)))'
def line(a,b):return poly([a,b])
def shapes(kind):
 sh=S[kind]['shape']
 if sh=='res_h':return [poly([(-3.81,-1.27),(3.81,-1.27),(3.81,1.27),(-3.81,1.27),(-3.81,-1.27)]),line((-7.62,0),(-3.81,0)),line((3.81,0),(7.62,0))]
 if sh=='res_v':return [poly([(-1.27,-3.81),(1.27,-3.81),(1.27,3.81),(-1.27,3.81),(-1.27,-3.81)]),line((0,-7.62),(0,-3.81)),line((0,3.81),(0,7.62))]
 if sh=='cap_h':return [line((-.762,-3.81),(-.762,3.81)),line((.762,-3.81),(.762,3.81)),line((-7.62,0),(-.762,0)),line((.762,0),(7.62,0))]
 if sh=='cap_v':return [line((-3.81,-.762),(3.81,-.762)),line((-3.81,.762),(3.81,.762)),line((0,-7.62),(0,-.762)),line((0,.762),(0,7.62))]
 if sh in ('opamp','comp'):
  return [poly([(-7.62,7.62),(-7.62,-7.62),(7.62,0),(-7.62,7.62)]),f'(text "+" (at -5.08 4.57 0) {fx(1.27)})',f'(text "-" (at -5.08 -4.57 0) {fx(1.27)})']
 if sh=='fda':return [poly([(-10.16,10.16),(-10.16,-10.16),(10.16,-7.62),(10.16,7.62),(-10.16,10.16)])]
 if sh=='pd':return [poly([(-5.08,3.81),(-5.08,-3.81),(3.81,0),(-5.08,3.81)]),line((3.81,-4.57),(3.81,4.57)),line((-10.16,0),(-5.08,0)),line((3.81,0),(10.16,0)),f'(circle (center 0 0) (radius 6.35) (stroke (width 0.254) (type default)) (fill (type none)))']
 if sh=='box':return [poly([(-10.16,10.16),(10.16,10.16),(10.16,-10.16),(-10.16,-10.16),(-10.16,10.16)])]
 if sh=='connector':
  h=max(5.08,len(S[kind]['pins'])*2.54)
  return [poly([(-2.54,h),(7.62,h),(7.62,-h),(-2.54,-h),(-2.54,h)])]
 if sh=='tp':return [f'(circle (center 0 0) (radius 1.27) (stroke (width 0.254) (type default)) (fill (type none)))']
 if sh=='flag':return [poly([(0,0),(0,2.54),(-2.54,3.81),(0,5.08),(2.54,3.81),(0,2.54)])]
 return []
def libsym(kind,emb=True):
 d=S[kind]; name=('ZL80_G2:'+kind) if emb else kind
 a=[f'(symbol {q(name)} (pin_names (offset 0.508)) (in_bom yes) (on_board yes)',prop('Reference','U' if kind.startswith(('OPA','TLV','AD')) else kind[0],0,15.24),prop('Value',kind,0,-15.24),prop('Footprint','ZL80_G2:'+str(d['fp']),0,0,hide=True),f'(symbol {q(kind+"_0_1")}']+shapes(kind)+[')',f'(symbol {q(kind+"_1_1")}']
 for p in d['pins']:
  length=0 if d['shape'] in ('res_h','res_v','cap_h','cap_v','pd','flag') else 5.08
  a.append(f'(pin {p["type"]} line (at {n(p["x"])} {n(p["y"])} {p["angle"]}) (length {n(length)}) (name {q(p["name"])} {fx(.762)}) (number {q(p["num"])} {fx(.762)}))')
 return '\n'.join(a+[')',')'])
def pinpos(c,p):return [c['xy'][0]+p['x'],c['xy'][1]-p['y']]
def schematic(b):
 bid=b['id'];proj=bid+'_G2E01';rootid=uid(proj);cs=b['components'];keys=sorted({c['kind'] for c in cs})
 out=[f'(kicad_sch (version 20231120) (generator "zl80_g2_engineering") (uuid {rootid}) (paper "A3")',f'(title_block (title {q(bid+" | "+b["name"])}) (date "2026-11-16") (rev "G2E01-D01-CANDIDATE") (company "ZL80 | NOT RELEASED FOR FABRICATION") (comment 1 "Actual circuit candidate; native ERC/DRC and bench NOT RUN"))','(lib_symbols']+[libsym(k) for k in keys]+[')']
 out.append(f'(text {q(bid+" | G2-E01 / schematic candidate / 4-layer PCB UNROUTED")} (at 15.24 10.16 0) {fx(1.27,"left")} (uuid {uid(proj+"title")}))')
 records=[];scene=dict(board=bid,title=b['name'],components=[],wires=[],labels=[],notes=b['notes'])
 for c in cs:
  k=c['kind'];d=S[k];x,y=c['xy'];ref=c['ref'];su=uid(proj+ref);bom=c.get('in_bom',True);onboard=d['fp'] is not None
  out.append(f'(symbol (lib_id {q("ZL80_G2:"+k)}) (at {n(x)} {n(y)} 0) (unit 1) (in_bom {"yes" if bom else "no"}) (on_board {"yes" if onboard else "no"}) (dnp no) (uuid {su})')
  if d['shape'] in ('opamp','comp','fda','box'):rx,ry=x+17.78,y-17.78;vx,vy=x+22.86,y-13.97
  elif d['shape'] in ('res_v','cap_v'):rx,ry=x+10.16,y-2.54;vx,vy=x+12.7,y+1.27
  elif d['shape']=='pd':rx,ry=x,y-12.7;vx,vy=x,y-8.89
  elif d['shape']=='connector':rx,ry=x,y-len(d['pins'])*2.54-5.08;vx,vy=x,y-len(d['pins'])*2.54-1.27
  elif d['shape']=='tp':rx,ry=x,y-5.08;vx,vy=x,y+5.08
  else:rx,ry=x,y-5.08;vx,vy=x,y+5.08
  out += [prop('Reference',ref,rx,ry,1.1),prop('Value',c['value'],vx,vy,.9,hide=(d['shape'] in ('tp','flag'))),prop('Footprint','ZL80_G2:'+str(d['fp']) if onboard else '',x,y,hide=True),prop('ManufacturerPartNumber',c.get('mpn',''),x,y,hide=True),prop('Evidence',c.get('source',d.get('source','DESIGN_PROPOSED')),x,y,hide=True),prop('Release','NOT_RELEASED',x,y,hide=True)]
  for pp in d['pins']:out.append(f'(pin {q(pp["num"])} (uuid {uid(proj+ref+pp["num"])}))')
  out.append(f'(instances (project {q(proj)} (path {q("/"+rootid)} (reference {q(ref)}) (unit 1)))) )')
  scene['components'].append(dict(**c,props=dict(ref=[rx,ry],value=[vx,vy]),definition=d))
  for pp in d['pins']:
   px,py=pinpos(c,pp);net=c['nets'].get(pp['num'],'');rec=dict(board=bid,ref=ref,pin=pp['num'],pin_name=pp['name'],pin_type=pp['type'],net=net,source=c.get('source',d.get('source','DESIGN_PROPOSED')),symbol_uuid=su)
   records.append(rec)
   if not net:
    out.append(f'(no_connect (at {n(px)} {n(py)}) (uuid {uid(proj+ref+pp["num"]+"nc")}))'); continue
   # Directional stubs + named nets are native electrical connections, not decorative leaders.
   a=math.radians(pp['angle']);dx=-math.cos(a)*5.08;dy=math.sin(a)*5.08
   ex,ey=round(px+dx,5),round(py+dy,5)
   if k=='PWR_FLAG':ex,ey=px,py+5.08
   if pp['angle']==90 and d['shape'] in ('opamp','comp','fda'):
    bp=[z['num'] for z in d['pins'] if z['angle']==90 and c['nets'].get(z['num'])]
    ey=py+10.16+bp.index(pp['num'])*7.62
   out.append(f'(wire (pts (xy {n(px)} {n(py)}) (xy {n(ex)} {n(ey)})) (stroke (width 0) (type default)) (uuid {uid(proj+ref+pp["num"]+"wire")}))')
   # 0-degree labels remain readable; justification changes with pin side.
   angle=180 if pp['angle']==0 else 0
   out.append(f'(label {q(net)} (at {n(ex)} {n(ey)} {angle}) {fx(.8,"left bottom")} (uuid {uid(proj+ref+pp["num"]+"label")}))')
   scene['wires'].append([[px,py],[ex,ey]])
   scene['labels'].append(dict(x=ex,y=ey,text=net,angle=angle))
 # Explicit negative-feedback loops and key signal routes; other connections use same-name labels.
 loops=[]
 if bid in ('B06','B07'):
  loops=[[(48.26,81.28),(68.58,81.28),(68.58,86.36),(104.14,86.36)],[(109.22,22.86),(76.2,22.86),(76.2,86.36)],[(109.22,40.64),(76.2,40.64)],[(124.46,22.86),(157.48,22.86),(157.48,81.28)],[(124.46,40.64),(157.48,40.64)],[(129.54,81.28),(167.64,81.28),(167.64,76.2),(182.88,76.2)],[(198.12,76.2),(238.76,76.2)],[(243.84,40.64),(220.98,40.64),(220.98,76.2)],[(259.08,40.64),(284.48,40.64),(284.48,81.28)],[(264.16,81.28),(299.72,81.28)],[(30.48,182.88),(30.48,205.74)],[(60.96,205.74),(60.96,193.04),(30.48,193.04)],[(106.68,182.88),(106.68,205.74)],[(137.16,205.74),(137.16,193.04),(106.68,193.04)]]
 elif bid=='B01':
  loops=[[(45.72,93.98),(91.44,93.98),(91.44,96.52),(119.38,96.52)],[(124.46,30.48),(91.44,30.48),(91.44,96.52)],[(124.46,48.26),(91.44,48.26)],[(139.7,30.48),(177.8,30.48),(177.8,91.44)],[(139.7,48.26),(177.8,48.26)],[(144.78,91.44),(200.66,91.44),(200.66,76.2),(210.82,76.2)],[(226.06,76.2),(246.38,76.2),(246.38,86.36),(266.7,86.36)]]
 elif bid=='B08':
  loops=[[(55.88,83.82),(76.2,83.82),(76.2,88.9),(119.38,88.9)],[(124.46,22.86),(91.44,22.86),(91.44,88.9)],[(124.46,40.64),(91.44,40.64)],[(139.7,22.86),(177.8,22.86),(177.8,83.82)],[(139.7,40.64),(177.8,40.64)],[(144.78,83.82),(215.9,83.82)]]
 for j,path in enumerate(loops):
  for h,(a,z) in enumerate(zip(path,path[1:])):
   out.append(f'(wire (pts (xy {n(a[0])} {n(a[1])}) (xy {n(z[0])} {n(z[1])})) (stroke (width 0) (type default)) (uuid {uid(proj+"route"+str(j)+"_"+str(h))}))')
   scene['wires'].append([a,z])
 out+=['(sheet_instances (path "/" (page "1")))',')']
 return '\n'.join(out),records,scene

def footprints():
 F={}
 F['0603']=dict(w=2.8,h=1.6,z=.7,pads=[dict(num='1',x=-.825,y=0,w=.95,h=.95,drill=0),dict(num='2',x=.825,y=0,w=.95,h=.95,drill=0)])
 for N in [5,6]:
  pads=[]
  for num,xy in {1:(-1.1,-.95),2:(-1.1,0),3:(-1.1,.95),**({4:(1.1,.95),5:(1.1,-.95)} if N==5 else {4:(1.1,.95),5:(1.1,0),6:(1.1,-.95)})}.items():pads.append(dict(num=str(num),x=xy[0],y=xy[1],w=1.2,h=.6,drill=0))
  F['SOT23_'+str(N)]=dict(w=3.6,h=3.1,z=1.45,pads=pads)
 pads=[]
 for i in range(4):
  pads.append(dict(num=str(i+1),x=-2.7,y=(i-1.5)*1.27,w=1.55,h=.6,drill=0));pads.append(dict(num=str(8-i),x=2.7,y=(i-1.5)*1.27,w=1.55,h=.6,drill=0))
 F['SOIC8']=dict(w=7.4,h=5.4,z=1.75,pads=pads)
 F['S5971_TO18_TOP']=dict(w=5.9,h=5.9,z=5.0,pads=[dict(num='1',x=-1.27,y=0,w=1.25,h=1.25,drill=.7),dict(num='2',x=0,y=1.27,w=1.25,h=1.25,drill=.7),dict(num='3',x=1.27,y=0,w=1.25,h=1.25,drill=.7)],note='Top-view mirror of manufacturer bottom view. Pin1 K left, pin3 A right, pin2 CASE bottom; confirm tab orientation and real sample.')
 F['TP1']=dict(w=1.3,h=1.3,z=.1,pads=[dict(num='1',x=0,y=0,w=1.0,h=1.0,drill=0)])
 for N in [1,4,6,8]:
  if N<=4:
   pitch=1.27 if N==4 else 2.54;pads=[dict(num=str(i+1),x=0,y=(i-(N-1)/2)*pitch,w=1.0 if N==4 else 1.8,h=1.0 if N==4 else 1.8,drill=.65 if N==4 else 1.) for i in range(N)]
   F['HDR'+str(N)]=dict(w=2.4,h=N*pitch+1,z=6,pads=pads)
  else:
   pads=[dict(num=str(i+1),x=(-1 if i%2==0 else 1)*1.27,y=(i//2-(N/2-1)/2)*2.54,w=1.7,h=1.7,drill=1) for i in range(N)]
   F['HDR'+str(N)]=dict(w=5.6,h=N/2*2.54+1,z=7,pads=pads)
 # PMT sockets: use exact inherited R5 pad positions, NOT arbitrary 2x4 header.
 old=json.loads((ROOT/'reference/R51_component_placements.json').read_text());rows=[c for c in old if c['board']=='B01' and c['ref'].startswith('JP')]
 pds=[]
 for c in rows:
  num=c['ref'][2:];pds.append(dict(num=num,x=c['xy'][0]-42,y=c['xy'][1]-17,w=2,h=2,drill=.9))
 F['H10720_SOCKET_DRAFT']=dict(w=50.0,h=25.0,z=22,pads=pds,note='Inherited single socket holes; socket MPN and bottom/top mirror not released. 0.9mm holes are for hypothetical socket tails, NOT bare 1mm PMT pins.')
 return F

def fp_text(key,d,c=None,bid='',netcodes=None,rootid=''):
 c=c or dict(ref='REF**',value=key,nets={},pcb_xy=[0,0],side='F');ref=c['ref'];side=c.get('side','F');at=c.get('pcb_xy',[0,0]);w,h=d['w'],d['h'];onboard=netcodes is not None
 a=[f'(footprint {q("ZL80_G2:"+key if onboard else key)}'+('' if onboard else ' (version 20240108) (generator "zl80_g2_engineering")')+f' (layer "{side}.Cu")']
 if onboard:a+=[f'(uuid {uid(bid+ref+"fp")}) (at {n(at[0])} {n(at[1])})',f'(path {q("/"+rootid+"/"+uid(bid+"_G2E01"+ref))})']
 a += [f'(property "Reference" {q(ref)} (at 0 {n(-h/2-1)} 0) (layer "{side}.Fab") {fx(.6)})',f'(property "Value" {q(c["value"])} (at 0 {n(h/2+1)} 0) (layer "{side}.Fab") {fx(.6)})', '(attr '+('through_hole' if any(p['drill'] for p in d['pads']) else 'smd')+')']
 for layer in ['Fab','CrtYd']:
  a.append(f'(fp_rect (start {n(-w/2)} {n(-h/2)}) (end {n(w/2)} {n(h/2)} ) (stroke (width 0.05) (type default)) (fill none) (layer "{side}.{layer}"))')
 for pp in d['pads']:
  layers='"*.Cu" "*.Mask"' if pp['drill'] else f'"{side}.Cu" "{side}.Paste" "{side}.Mask"'
  # Mirrors are applied to bottom SMD pads to retain the front-view footprint numbering.
  px=pp['x'] if side=='F' or pp['drill'] else -pp['x']
  st=f'(pad {q(pp["num"])} {"thru_hole" if pp["drill"] else "smd"} {"circle" if pp["drill"] else "rect"} (at {n(px)} {n(pp["y"])}) (size {n(pp["w"])} {n(pp["h"])})'
  if pp['drill']:st+=f' (drill {n(pp["drill"])})'
  st+=f' (layers {layers})'
  net=c['nets'].get(pp['num'],'')
  if onboard and net:st+=f' (net {netcodes[net]} {q(net)})'
  st+=')';a.append(st)
 a.append(')');return '\n'.join(a)

def place(b,F):
 # Deterministic floorplanning only. Pads/track SI optimization is still a native PCB task.
 W,H=b['size_mm']; placed=[];issues=[]
 def rect(c):
  d=F[c['fp']];x,y=c['pcb_xy'];return [x-d['w']/2,y-d['h']/2,x+d['w']/2,y+d['h']/2]
 def okay(c):
  r=rect(c)
  if r[0]<.3 or r[1]<.3 or r[2]>W-.3 or r[3]>H-.3:return False
  for x,y in b['holes']:
   dx=max(r[0]-x,0,x-r[2]);dy=max(r[1]-y,0,y-r[3])
   if math.hypot(dx,dy)<(1.1 if W<30 else 1.6)+.5:return False
  for o in placed:
   if o.get('side','F')!=c.get('side','F') and not(any(p['drill'] for p in F[o['fp']]['pads']) or any(p['drill'] for p in F[c['fp']]['pads'])):continue
   s=rect(o)
   if not (r[2]+.2<=s[0] or s[2]+.2<=r[0] or r[3]+.2<=s[1] or s[3]+.2<=r[1]):return False
  return True
 cs=[copyc(c) for c in b['components'] if S[c['kind']]['fp'] is not None]
 for c in cs:c['fp']='H10720_SOCKET_DRAFT' if c['ref']=='JPMT1' else S[c['kind']]['fp']
 priority={'R1':0,'C1':1,'C6':2,'C7':3,'C3':4,'C4':5,'C5':6,'C8':7,'C9':8}
 cs.sort(key=lambda c:(0 if 'pcb_anchor'in c else 1,priority.get(c['ref'],20) if 'pcb_anchor' not in c else -F[c['fp']]['w']*F[c['fp']]['h']))
 for c in cs:
  candidates=[]
  bid=b['id']
  targets={}
  if bid in ('B06','B07'):
   targets={'R1':[6.0,6.0],'C1':[6.0,8.0],'R2':[9.0,10.0],'R3':[9.0,12.0], 'C6':[9.0,5.0],'C7':[12.0,14.5], 'C4':[3.0,13.0],'C5':[5.5,15.0], 'R4':[9.0,16.0],'R5':[6.0,17.0]}
  elif bid=='B08':
   targets={'R1':[10.0,7.0],'C1':[10.0,9.0], 'C3':[17,4], 'C4':[17,12], 'C5':[14,3],'C6':[14,14], 'R2':[20,8], 'C2':[7,12], 'R3':[7,14]}
  elif bid=='B01':
   targets={'R1':[28.5,32.0], 'C1':[28.5,34.0], 'R2':[54,31], 'R3':[54,34], 'R4':[55,38], 'R5':[62,38], 'R6':[68,31], 'R7':[68,34], 'C2':[73,32.5], 'C3':[39.5,33], 'C4':[28.5,38], 'C5':[55.5,33], 'C6':[67,33], 'C7':[26,40], 'C8':[30,40], 'C9':[10,29], 'TP1':[42,35],'TP2':[72,38]}
  if c['ref'] in targets:
   target=targets[c['ref']]
   slots=([[xi*.5,yi*.5] for yi in range(3,int(H*2)-2) for xi in range(3,int(W*2)-2)])
   slots.sort(key=lambda xy:(xy[0]-target[0])**2+(xy[1]-target[1])**2)
   candidates += [(xy,'F') for xy in slots]
  if 'pcb_anchor' in c:candidates.append((c['pcb_anchor'],'F'))
  # Minimize loop area later in KiCad; present a legal starting envelope, not final routing.
  for side in ['F','B']:
   if side=='B' and (c['kind'] not in ['R_H','R_V','C_H','C_V','TP']):continue
   for yi in range(3,int(H*2)-2):
    for xi in range(3,int(W*2)-2):candidates.append(([xi*.5,yi*.5],side))
  found=False
  for pos,side in candidates:
   c['pcb_xy']=pos;c['side']=side
   if okay(c):found=True;break
  if not found:
   c['pcb_xy']=[W+10+len(issues)*10,10];c['side']='F';issues.append(dict(board=b['id'],ref=c['ref'],issue='NO_FIT_PARKED_OUTSIDE_BOARD',release_blocker=True))
  placed.append(c)
 return placed,issues

def copyc(c):return json.loads(json.dumps(c))
def boardtext(b,cs,F):
 bid=b['id'];w,h=b['size_mm'];names=sorted({net for c in cs for net in c['nets'].values() if net});codes={s:i+1 for i,s in enumerate(names)}
 a=[f'(kicad_pcb (version 20240108) (generator "zl80_g2_engineering") (general (thickness 1.6)) (paper "A3")',f'(title_block (title "{bid} G2-E01 placement candidate") (rev "UNROUTED-NOT-RELEASED"))', '(layers (0 "F.Cu" signal) (1 "In1.Cu" signal) (2 "In2.Cu" signal) (31 "B.Cu" signal) (34 "B.Paste" user) (35 "F.Paste" user) (36 "B.SilkS" user) (37 "F.SilkS" user) (38 "B.Mask" user) (39 "F.Mask" user) (40 "Dwgs.User" user) (44 "Edge.Cuts" user) (46 "B.CrtYd" user) (47 "F.CrtYd" user) (48 "B.Fab" user) (49 "F.Fab" user))','(setup (pad_to_mask_clearance 0))','(net 0 "")']+[f'(net {i} {q(s)})' for s,i in codes.items()]
 for j,(a1,a2) in enumerate(zip([(0,0),(w,0),(w,h),(0,h)],[(w,0),(w,h),(0,h),(0,0)])):
  a.append(f'(gr_line (start {n(a1[0])} {n(a1[1])}) (end {n(a2[0])} {n(a2[1])}) (stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid {uid(bid+"edge"+str(j))}))')
 for i,(x,y) in enumerate(b['holes']):
  dia=2.2 if w<30 else 3.2
  a.append(f'(footprint "ZL80_G2:NPTH" (layer "F.Cu") (uuid {uid(bid+"hole"+str(i))}) (at {x} {y}) (attr board_only exclude_from_pos_files exclude_from_bom) (property "Reference" "H{i+1}" (at 0 -2) (layer "F.Fab") {fx(.5)}) (pad "" np_thru_hole circle (at 0 0) (size {dia} {dia}) (drill {dia}) (layers "*.Cu" "*.Mask")))')
 for c in cs:a.append(fp_text(c['fp'],F[c['fp']],c,bid,codes,uid(bid+'_G2E01')))
 a.append(f'(gr_text "{bid} G2-E01 | NO TRACKS | NOT FOR FAB" (at {w/2} {h+4}) (layer "Dwgs.User") {fx(.8)})')
 return '\n'.join(a+[')'])
def writecsv(path,rows):
 if not rows:return
 with path.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 lib=ROOT/'electronics/libraries';F=footprints();(lib/'ZL80_G2.kicad_sym').write_text('(kicad_symbol_lib (version 20231120) (generator "zl80_g2_engineering")\n'+'\n'.join(libsym(k,False) for k in S)+'\n)')
 for key,d in F.items():(lib/'ZL80_G2.pretty'/f'{key}.kicad_mod').write_text(fp_text(key,d))
 recs=[];scenes=[];placements=[];allissues=[];bom=[]
 for b in BOARDS:
  bid=b['id'];d=ROOT/'electronics/projects'/bid;d.mkdir(exist_ok=True);proj=bid+'_G2E01';txt,rr,scene=schematic(b)
  (d/(proj+'.kicad_sch')).write_text(txt);recs+=rr;scenes.append(scene)
  # Update special PMT footprint reference to inherited composite socket.
  if bid=='B01':(d/(proj+'.kicad_sch')).write_text(txt.replace('(property "Footprint" "ZL80_G2:HDR8" (at 33.02 81.28','(property "Footprint" "ZL80_G2:H10720_SOCKET_DRAFT" (at 33.02 81.28'))
  cs,issues=place(b,F);placements += [dict(board=bid,**c) for c in cs];allissues+=issues
  (d/(proj+'.kicad_pcb')).write_text(boardtext(b,cs,F))
  pro=dict(meta=dict(filename=proj+'.kicad_pro',version=1),text_variables=dict(DESIGN_STATUS='NOT_RELEASED'),schematic=dict(meta=dict(version=1)))
  (d/(proj+'.kicad_pro')).write_text(json.dumps(pro,indent=2))
  (d/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "ZL80_G2") (type "KiCad") (uri "${KIPRJMOD}/../../libraries/ZL80_G2.kicad_sym") (options "") (descr "Audited pin types; native validation pending")))')
  (d/'fp-lib-table').write_text('(fp_lib_table (version 7) (lib (name "ZL80_G2") (type "KiCad") (uri "${KIPRJMOD}/../../libraries/ZL80_G2.pretty") (options "") (descr "Candidate land patterns; manufacturer approval pending")))')
  (d/'README.md').write_text(f'# {bid} G2-E01\n\n打开 {proj}.kicad_pro。原理图是元件级候选；PCB有板框/孔/封装/网络及初排，尚无布线。\n\n'+'\n'.join('- '+x for x in b['notes'])+'\n\n状态：NOT_RELEASED。仿真为有限模型证据；没有台架结果。\n')
  for c in cs:bom.append(dict(board=bid,reference=c['ref'],value=c['value'],mpn=c.get('mpn',''),footprint=c['fp'],x_mm=c['pcb_xy'][0],y_mm=c['pcb_xy'][1],side=c['side'],source=c.get('source',S[c['kind']].get('source','DESIGN_PROPOSED')),procurement_status='MPN_CANDIDATE' if c.get('mpn') else 'MPN_TBD',release='NOT_RELEASED'))
 (ROOT/'engineering/pin_net_type_audit.json').write_text(json.dumps(recs,indent=2,ensure_ascii=False));writecsv(ROOT/'engineering/pin_net_type_audit.csv',recs)
 (ROOT/'engineering/schematic_scene.json').write_text(json.dumps(scenes,indent=2));(ROOT/'engineering/placements.json').write_text(json.dumps(placements,indent=2));(ROOT/'engineering/footprints.json').write_text(json.dumps(F,indent=2))
 (ROOT/'evidence/placement_open_issues.json').write_text(json.dumps(allissues,indent=2));writecsv(ROOT/'engineering/BOM_candidate.csv',bom)
 print('Generated',len(BOARDS),'projects;',len(recs),'pin records;',len(bom),'BOM lines; placement blockers:',len(allissues))
if __name__=='__main__':main()
