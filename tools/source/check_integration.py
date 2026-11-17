from pathlib import Path
import json,cadquery as cq,math,collections,re
R=Path(__file__).resolve().parents[2];inst=json.loads((R/'cad/instances.json').read_text());cm=json.loads((R/'cad/component_render_meshes.json').read_text());parts={};issues=[];expected=[];checked=0
for m in cm:
 vs=m['vertices'];lo=[min(v[k] for v in vs) for k in range(3)];hi=[max(v[k] for v in vs) for k in range(3)];c=[(lo[k]+hi[k])/2 for k in range(3)];sz=[hi[k]-lo[k] for k in range(3)]
 box=cq.Workplane('XY').box(*sz).translate(c).val()
 for q in inst:
  if q['group'] in ('enclosure','external','optional_external'):continue
  bb=q['aabb'];ov=[min(hi[k],bb[k+3])-max(lo[k],bb[k]) for k in range(3)]
  if min(ov)<=1e-4:continue
  if q['part'] not in parts:parts[q['part']]=cq.importers.importStep(str(R/'cad/step'/f'{q["part"]}.step')).val()
  s=parts[q['part']]
  if q['rotation']:s=s.rotate((0,0,0),q['rotation'][0],q['rotation'][1])
  s=s.translate(q['position']);checked+=1;vol=box.intersect(s).Volume()
  if vol>.01:
   record=dict(component=m['id'],core_part=q['part'],core_instance=q['name'],intersection_mm3=vol)
   if m['id'].startswith('B01_JP') and q['part']=='P04':record['classification']='intended pin/socket engagement';expected.append(record)
   elif m['id'] in ('B06_D1','B07_D1','B08_D1') and q['part']=='S01':record['classification']='same sensor shown as body and PCB envelope';expected.append(record)
   else:issues.append(record)
(R/'tests/component_space_check.json').write_text(json.dumps(dict(scope='key component/function-envelope boxes vs nominal core B-reps; not actual component solids or full cable tolerance check',broad_phase_pairs_checked=checked,expected_engagements=expected,unresolved=issues),ensure_ascii=False,indent=2))
print('component space',checked,'checks',len(expected),'expected',len(issues),'issues');print(json.dumps(issues,indent=2))
# S-expression hierarchy without pretending it is KiCad validation.
def parse(text):
 tok=re.findall(r'"(?:\\.|[^"\\])*"|\(|\)|[^\s()]+',text);stack=[];root=None
 for t in tok:
  if t=='(':
   z=[]
   if stack:stack[-1].append(z)
   stack.append(z)
  elif t==')':
   z=stack.pop()
   if not stack:root=z
  else:stack[-1].append(t)
 return root
checks=[]
for f in (R/'electronics/boards').glob('*.kicad_pcb'):
 root=parse(f.read_text());fps=[x for x in root if isinstance(x,list) and x and x[0]=='footprint'];padroot=[x for x in root if isinstance(x,list) and x and x[0]=='pad'];nets={x[1]:x[2] for x in root if isinstance(x,list) and x and x[0]=='net'}
 pads=[x for fp in fps for x in fp if isinstance(x,list) and x and x[0]=='pad'];ok=True
 for pad in pads:
  for node in pad:
   if isinstance(node,list) and node and node[0]=='net' and nets.get(node[1])!=node[2]:ok=False
 checks.append(dict(file=f.name,root=root[0],footprints=len(fps),pads=len(pads),no_top_level_pads=not padroot,net_references_consistent=ok))
(R/'tests/ecad_structure_check.json').write_text(json.dumps(dict(method='custom S-expression hierarchy and net reference checks, NOT KiCad native parser/ERC/DRC',checks=checks),indent=2))
print('ECAD hierarchy',checks)
