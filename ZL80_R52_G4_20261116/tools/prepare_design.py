"""Create review candidates from immutable G2 netlist, with explicit placement changes.
No vendor macro-model or physical performance is claimed. Dimensions in millimetres.
"""
from pathlib import Path
import json,copy,csv,math
R=Path(__file__).resolve().parents[1]
def dump(p,x): (R/p).write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf8')
def csvout(p,rows):
 if rows:
  with (R/p).open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 data=json.loads((R/'sources/inherited/G2_circuits.json').read_text());oldp=json.loads((R/'sources/inherited/G2_placements.json').read_text());F=json.loads((R/'sources/inherited/G2_footprints.json').read_text());S=data['symbols']
 data['revision']='R52-G4-E02-D01'; data['scope']='PCB copper candidates and explicit ECAD/MCAD integration; not manufacturing release'
 # Original 0603 copper land patterns preserved; compact critical passives moved to 0402 where needed.
 F['0402']=dict(w=1.8,h=1.0,z=.55,pads=[dict(num='1',x=-.5,y=0,w=.6,h=.6,drill=0),dict(num='2',x=.5,y=0,w=.6,h=.6,drill=0)],status='GENERIC_LAND_PATTERN_REVIEW',body=[1.0,.5,.5])
 for k in ['0603','SOIC8','SOT23_5','SOT23_6','TP1','S5971_TO18_TOP','HDR4','HDR6','HDR8','H10720_SOCKET_DRAFT']:
  F[k]['status']='INHERITED_CANDIDATE_VERIFY_LAND_PATTERN'
 F['SOT23_5']['body']=[1.6,2.9,1.45];F['SOT23_6']['body']=[1.6,2.9,1.45];F['SOIC8']['body']=[3.91,4.9,1.75];F['0603']['body']=[1.6,.8,.7]
 F['S5971_TO18_TOP']['body']=[5.6,5.6,3.8];F['S5971_TO18_TOP']['z']=7.4
 F['S5971_TO18_TOP']['note']+='; 3.6mm nominal lead stand-off, 3.6mm nominal can; model uses max3.8mm can for clearance. Photosensitive surface is 2.8mm above flange; NOT the package top.'
 F['HDR4']['h']=5.08;F['HDR4']['w']=2.5;F['HDR4']['z']=5.2
 for p in F['HDR4']['pads']:p['drill']=.66
 F['HDR4']['note']='Samtec TMS-104-02-L-S candidate;1.27mm pitch,0.66mm recommended finished hole. Mating socket and pull space still provisional.'
 # Manual placements prioritize current summing node/feedback and power pin access.
 P06={
 'D1':(15,4,0,'F'),'J1':(2.3,8.5,0,'F'), 'U1':(9.7,5.9,0,'F'), 'U2':(9.7,12.1,0,'F'), 'U3':(5.6,13.3,0,'F'),
 'R1':(12.8,8.0,90,'F'),'C1':(14.5,8.0,90,'F'), 'R2':(7.4,9.0,0,'F'),'R3':(9.5,14.6,0,'F'), 'R4':(12.8,13.2,90,'F'),'R5':(9.3,18.4,0,'F'),
 'R6':(5.7,4.9,0,'F'),'R7':(5.7,6.4,0,'F'),'C2':(5.7,8.0,0,'F'),'R8':(5.4,10.0,0,'F'),'R9':(7.2,10.4,90,'F'),'C3':(12.7,10.2,0,'F'),
 'C4':(5.5,15.8,0,'F'),'C5':(8.5,16.4,0,'F'), 'C6':(10.8,4.8,90,'B'),'C7':(10.8,13.0,90,'B'),
 'TP1':(7.5,7.8,0,'B'),'TP2':(15.5,11.8,0,'F'),'TP3':(12.8,16.8,0,'F')}
 # Top-view transforms for +Y normal use v=-Z, preserving mechanical rectangular envelope.
 # B08 D1 changed to match X=-62mm, Z=245mm; B01 module pin mapping matches G3 pins exactly.
 P08={
 'D1':(13,10,0,'F'),'U1':(7.2,10,0,'B'),'J1':(22,10,0,'F'),
 'R1':(7.2,6.0,0,'B'),'C1':(7.2,4.3,0,'B'),'R2':(18.4,10,90,'F'),'R3':(14.5,14.5,0,'F'),
 'C2':(18.0,13.2,90,'F'),'C3':(2.7,9.4,90,'B'),'C4':(12.2,13.3,90,'B'),
 'C5':(15.5,5.0,0,'B'),'C6':(15.5,7.0,0,'B'),'TP1':(19.0,6.2,0,'F')}
 P01={
 'JPMT1':(42,17,0,'F'),'J1':(78,34,0,'F'),'J2':(10,37,0,'F'),
 'U1':(35.6,28.5,0,'F'),'R1':(29.2,28.5,90,'F'),'C1':(30.6,28.5,90,'F'),
 'U2':(56.0,34.0,0,'F'), 'R2':(60.9,31.5,0,'F'),'R3':(61.0,36.0,0,'F'),'R4':(51.0,31.5,0,'F'),'R5':(51.0,36.0,0,'F'),
 'R6':(62.0,40.3,0,'F'),'R7':(65.5,40.3,0,'F'),'C2':(69.5,39.0,90,'F'),
 'C3':(40.2,27.9,90,'F'),'C4':(30.7,32.0,90,'F'),'C5':(51.0,34.0,90,'B'),'C6':(61.0,34.0,90,'B'),
 'C7':(25,36,0,'F'),'C8':(25,39,0,'F'),'C9':(10,28.4,0,'F'),'TP1':(43,30,0,'F'),'TP2':(73,41,0,'F')}
 allp=[];changes=[]
 for b in data['boards']:
  bid=b['id'];b['stage']='COPPER_CANDIDATE' if bid in ['B06','B07'] else 'PLACEMENT_AND_CRITICAL_ROUTING_CANDIDATE'; b['revision']=data['revision']
  if bid in ['B06','B07']:
   pp=copy.deepcopy(P06)
   if bid=='B07':
    pp={ref:(18-x,y,(a+180)%360,side) for ref,(x,y,a,side) in pp.items()}
    pp['U3']=(13.5,12.7,180,'F'); pp['R9']=(10.8,10.4,270,'B'); pp['C2']=(12.3,8.0,180,'B')
  else:pp=P08 if bid=='B08' else P01
  for c in b['components']:
   if S[c['kind']]['fp'] is None:continue
   ref=c['ref'];x,y,a,side=pp[ref];c['pcb_xy']=[x,y];c['angle']=a;c['side']=side;c['fp']=S[c['kind']]['fp']
   if c['kind'].startswith(('R_','C_')) and not c['value'].startswith('2.2u') :c['fp']='0402'
   if ref=='J1' and bid in ['B06','B07','B08']:c['mpn']='TMS-104-02-L-S';c['source']='V_G4_04; mating connector still TBD'
   if c['kind'].startswith('R_'):c['mpn']='';c['procurement_requirement']=c['value']+'; exact resistance/voltage/power/tolerance series not frozen'
   allp.append(dict(board=bid,**copy.deepcopy(c)))
   old=next(z for z in oldp if z['board']==bid and z['ref']==ref)
   changes.append(dict(board=bid,ref=ref,old_xy_mm=str(old['pcb_xy']),new_xy_mm=str(c['pcb_xy']),old_side=old['side'],new_side=side,rotation_deg=a,old_footprint=old['fp'],new_footprint=c['fp'],status='PROPOSED_REQUIRES_REVIEW'))
  b['notes'] += ['G4: schematic topology unchanged from G2; placements and body-side mapping revised explicitly.', 'All native ERC/DRC, vendor SPICE and bench remain required; routed artwork is NOT a release.']
 dump('engineering/circuits.json',data);dump('engineering/footprints.json',F);dump('engineering/placements.json',allp);csvout('engineering/placement_changes.csv',changes)
 defs=json.loads((R/'sources/inherited/board_definitions.json').read_text());reg=[]
 for b in defs:
  o=b['origin'];W,H,T=b['size'];normal=b['normal'];plane=b['plane']
  if plane=='XY':origin=[o[0],o[1],o[2]-T/2];u=[1,0,0];v=[0,1,0];n=[0,0,1]
  elif normal=='+Y':origin=[o[0],o[1]-T/2,o[2]+H];u=[1,0,0];v=[0,0,-1];n=[0,1,0]
  else:origin=[o[0],o[1]+T/2,o[2]];u=[1,0,0];v=[0,0,1];n=[0,-1,0]
  reg.append(dict(board=b['id'],origin=origin,u=u,v=v,n=n,size=[W,H,T],normal=normal,holes=b['holes'],status='PROPOSED_MAPPING' if b['id'] in ['B01','B06','B07','B08'] else 'INHERITED_INTERFACE_ONLY'))
 dump('engineering/board_transforms.json',reg)
 print('Prepared',len(allp),'component placements; schematic topology preserved')
if __name__=='__main__':main()
