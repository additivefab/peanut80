"""Build review STEP models using real G3 geometry and G4 body envelopes.
Not a substitute for vendor STEP, socket selection, assembly tolerance or tool access.
"""
import json,math,csv
from pathlib import Path
import cadquery as cq
from pcb_geometry import ROOT,load,xy

def box(w,h,d,z=0):return cq.Workplane('XY').box(w,h,d,centered=(True,True,False)).translate((0,0,z)).val()
def cyl(rad,z,h):return cq.Solid.makeCylinder(rad,h,cq.Vector(0,0,z))
def compound(shapes):return cq.Compound.makeCompound(shapes)
def bounds(s):
 b=s.BoundingBox();return [b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax]
def overlap(a,b):return all(min(a[i+3],b[i+3])-max(a[i],b[i])>1e-5 for i in range(3))
def world(s,t):
 if t['normal']=='+Y':s=s.rotate((0,0,0),(1,0,0),-90)
 elif t['normal']=='-Y':s=s.rotate((0,0,0),(1,0,0),90)
 return s.translate(t['origin'])
def pointworld(x,y,z,t):return [t['origin'][i]+x*t['u'][i]+y*t['v'][i]+z*t['n'][i] for i in range(3)]
def csvwrite(path,rows):
 with path.open('w',newline='',encoding='utf-8-sig') as f:
  if rows:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
  else:f.write('status\nNO_FINDINGS_IN_DEFINED_SCOPE\n')
def package(k,d):
 if k=='S5971_TO18_TOP':return cyl(2.8,3.6,3.8)
 if k=='H10720_SOCKET_DRAFT':
  # Only hypothetical socket collars, not a second copy of the actual PMT.
  return compound([cyl(.85,0,4.0).translate((p['x'],p['y'],0)) for p in d['pads']])
 if k=='TP1':return cyl(.5,0,.1)
 if k.startswith('HDR'):return box(d['w'],d['h'],d['z'])
 if k.startswith('SOIC'):return box(6.2,5.0,1.75)
 if k.startswith('SOT'):return box(3.0,2.9,1.45)
 w,h,z=d.get('body',[d['w'],d['h'],d['z']]);return box(w,h,z)
def main():
 D,F,P=load();trans={x['board']:x for x in json.loads((ROOT/'engineering/board_transforms.json').read_text())};shapes={};records=[];allnew=[];connector=[];detectors=[];models={}
 for k,d in F.items():
  s=package(k,d);models[k]=s;cq.exporters.export(s,str(ROOT/'electronics/models3d'/f'{k}.step'))
 for b in D['boards']:
  bid=b['id'];W,H=b['size_mm'];t=trans[bid];T=1.6
  s=box(W,H,T).translate((W/2,H/2,0))
  for x,y in b['holes']:s=s.cut(cyl(1.1 if W<30 else 1.6,-1,4).translate((x,y,0)))
  local=[('PCB',s)]
  for c in [x for x in P if x['board']==bid]:
   k=c['fp'];z=T if c['side']=='F' else 0;ss=models[k]
   if c['side']=='B':ss=ss.rotate((0,0,0),(0,1,0),180)
   ss=ss.rotate((0,0,0),(0,0,1),-c['angle']).translate((*c['pcb_xy'],z));local.append((c['ref'],ss))
   # Explicit maximum solder/trimmed-lead tail envelopes where relevant.
   if k.startswith('HDR') or k=='S5971_TO18_TOP':
    for pad in F[k]['pads']:
     x,y=xy(c,pad);tail=1.45 if k=='HDR4' else 1.0
     lead=cyl(.23,-tail,T+tail+(3.6 if k=='S5971_TO18_TOP' else 0)).translate((x,y,0));local.append((c['ref']+'_lead'+pad['num'],lead))
   if k.startswith('HDR'):
    cx,cy=c['pcb_xy'];ww,hh=F[k]['w']+3,F[k]['h']+3
    m=box(ww,hh,10,T+F[k]['z']).rotate((0,0,0),(0,0,1),-c['angle']).translate((cx,cy,0))
    if c['side']=='B':m=m.mirror('XY')
    connector.append(dict(board=bid,ref=c['ref'],name=bid+'_'+c['ref']+'_MATE_PULL_PROVISIONAL',shape=world(m,t),status='MATING_PART_TBD;10mm_tool_pull_allowance_assumption'))
   if k=='S5971_TO18_TOP':
    x,y=c['pcb_xy'];pos=pointworld(x,y,T+3.6+2.8,t);detectors.append(dict(board=bid,ref=c['ref'],x_mm=pos[0],y_mm=pos[1],z_mm=pos[2],sensitive_plane_offset_mm=2.8,lead_standoff_mm=3.6,status='PROPOSED;G1_RECHECK_REQUIRED'))
  ass=cq.Assembly(name=bid+'_Local')
  for name,s in local:ass.add(s,name=name)
  ass.save(str(ROOT/'cad/boards'/f'{bid}_G4_local.step'))
  installed=cq.Assembly(name=bid+'_Installed')
  for name,s in local:
   ws=world(s,t);full=bid+'_'+name;installed.add(ws,name=full);allnew.append((full,ws));records.append(dict(board=bid,ref=name,aabb=bounds(ws),valid=ws.isValid(),volume_mm3=ws.Volume(),role='BODY_ENVELOPE' if name!='PCB' else 'BOARD_SOLID'))
  installed.save(str(ROOT/'cad/boards'/f'{bid}_G4_installed.step'))
 # Load the actual G3 context, dropping only replaced boards + duplicate photodiode proxies.
 inst=json.loads((ROOT/'cad/context/instances.json').read_text());ctx=[];excluded=[];cache={}
 for it in inst:
  name=it['name']
  if it['part'] in ['REF_B01','REF_B06','REF_B07','REF_B08'] or name in ['R5_PD_sync-46','R5_PD_sync46','R5_PD_reference'] or ('PD_sync' in name):excluded.append(name);continue
  pid=it['part']
  if pid not in cache:
   cache[pid]=cq.importers.importStep(str(ROOT/'cad/context/parts'/f'{pid}.step')).val()
  s=cache[pid]
  if it['rotation']:axis,ang=it['rotation'];s=s.rotate((0,0,0),axis,ang)
  s=s.translate(it['position']);ctx.append((name,s))
 ass=cq.Assembly(name='ZL80_G4_ECAD_MCAD_Review')
 for i,(name,s) in enumerate(ctx+allnew):ass.add(s,name=f'{i:03d}_{name}')
 ass.save(str(ROOT/'cad/assemblies/ZL80_G4_G3_Integration.step'))
 core=cq.Assembly(name='ZL80_G4_Core_Review')
 outer={it['name'] for it in inst if it['group']=='enclosure'}
 for i,(name,ss) in enumerate(ctx+allnew):
  if name not in outer:core.add(ss,name=f'{i:03d}_{name}')
 core.save(str(ROOT/'cad/assemblies/ZL80_G4_Core_Integration.step'))
 aa=cq.Assembly(name='G4_Four_Boards')
 for name,s in allnew:aa.add(s,name=name)
 aa.save(str(ROOT/'cad/assemblies/ZL80_G4_4Boards_Installed.step'))
 mm=cq.Assembly(name='Connector_Clearance_Assumptions')
 for c in connector:mm.add(c['shape'],name=c['name'])
 mm.save(str(ROOT/'cad/assemblies/ZL80_G4_Connector_Keepouts.step'))
 # New-body vs retained real context exact intersections. PCB drills exclude lead contact with own PCB from this cross-context scope.
 findings=[];checks=0
 for name,s in allnew:
  bs=bounds(s)
  for other,z in ctx:
   if not overlap(bs,bounds(z)):continue
   checks+=1;vol=s.intersect(z).Volume()
   if vol>1e-5:findings.append(dict(new_object=name,context_object=other,intersection_mm3=round(vol,6),status=('EXPECTED_SOCKET_PIN_OCCUPANCY_NOT_FIT_PROOF' if name=='B01_JPMT1' and other.startswith('R5_PMT_pin_') else 'OPEN_REVIEW')))
 matefind=[]
 for c in connector:
  for other,s in ctx+allnew:
   if other.startswith(c['board']+'_'+c['ref']):continue
   if not overlap(bounds(c['shape']),bounds(s)):continue
   vol=c['shape'].intersect(s).Volume()
   if vol>1e-4:matefind.append(dict(keepout=c['name'],other=other,intersection_mm3=round(vol,6),status='PROVISIONAL_CORRIDOR_CONFLICT;PART_OR_ACCESS_REVIEW'))
 csvwrite(ROOT/'validation/results/mcad_collisions.csv',findings);csvwrite(ROOT/'validation/results/connector_corridor_findings.csv',matefind);csvwrite(ROOT/'engineering/photodiode_coordinates.csv',detectors)
 (ROOT/'engineering/mcad_objects.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
 (ROOT/'validation/results/mcad_audit.json').write_text(json.dumps(dict(scope='New G4 board/component clearance envelopes versus retained actual G3 rigid parts; not full manufacturing assembly check',new_objects=len(allnew),context_objects=len(ctx),excluded_proxies=excluded,bbox_candidate_pairs=checks,body_collision_count=len(findings),unexpected_body_collisions=sum(x['status']=='OPEN_REVIEW' for x in findings),connector_corridor_conflicts=len(matefind),body_valid=all(x['valid'] for x in records),native_freecad='NOT_RUN',socket='TBD'),ensure_ascii=False,indent=2))
 print('MCAD:',len(allnew),'new',len(ctx),'context','collisions',findings,'mate',matefind,flush=True)
if __name__=='__main__':main()
