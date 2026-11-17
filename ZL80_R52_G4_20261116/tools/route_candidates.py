"""Conservative deterministic grid routing for review, NOT a replacement for KiCad DRC.
Physical copper emitted separately; input nodes are single-layer and no-via.
Ground/power have explicit track connectivity in addition to UNFILLED zone definitions.
"""
from pathlib import Path
import json,math,heapq,time,sys
import numpy as np
from shapely.geometry import Point,LineString,box
from shapely import contains_xy
from pcb_geometry import load,pads_for,ROOT
GRID=.1; WIDTH=.15; CLEAR=.15; EDGE=.35; VIA=.6; DRILL=.3
class Router:
 def __init__(self,b,P,F):
  self.b=b;self.w,self.h=b['size_mm'];self.ps=pads_for(b['id'],P,F);self.nx=int(round(self.w/GRID))+1;self.ny=int(round(self.h/GRID))+1
  self.X,self.Y=np.meshgrid(np.arange(self.nx)*GRID,np.arange(self.ny)*GRID);self.tracks=[];self.vias=[];self.fail=[];self.edges=[]
  # No planes/inner routes directly under summing node. Envelope is a model rule, not measured capacitance.
  sump=[p for p in self.ps if p['net'] in ['PD_SUM','REF_SUM','PMT_I']]
  if sump:
   self.input_keepout=box(min(p['x'] for p in sump)-.6,min(p['y'] for p in sump)-.6,max(p['x'] for p in sump)+.6,max(p['y'] for p in sump)+.6)
  else:self.input_keepout=None
  if b['id']=='B07':
   self.tracks.append(dict(net='GND',layer=0,width=.15,points=[[9.4,12.1],[10.6,12.1]]))
   self.vias.append(dict(net='GND',x=10.6,y=12.1,size=VIA,drill=DRILL))
 def raster(self,geom):return contains_xy(geom,self.X,self.Y)
 def mask(self,net):
  a=np.zeros((4,self.ny,self.nx),dtype=bool)
  edge=(self.X<EDGE)|(self.X>self.w-EDGE)|(self.Y<EDGE)|(self.Y>self.h-EDGE);a[:]=edge
  for x,y in self.b['holes']:
   rad=(1.1 if self.w<30 else 1.6)+CLEAR+WIDTH/2+.03;a[:]|=((self.X-x)**2+(self.Y-y)**2<rad*rad)
  for p in self.ps:
   if p['net']!=net or not p['net']:
    obs=self.raster(p['shape'].buffer(CLEAR+WIDTH/2+.02));
    for l in p['layers']:a[l]|=obs
  for t in self.tracks:
   if t['net']!=net:a[t['layer']]|=self.raster(LineString(t['points']).buffer(t['width']/2+CLEAR+WIDTH/2+.025))
  for v in self.vias:
   if v['net']!=net:a[:]|=((self.X-v['x'])**2+(self.Y-v['y'])**2<(VIA/2+CLEAR+WIDTH/2+.03)**2)
  if self.input_keepout is not None:
   obs=self.raster(self.input_keepout.buffer(WIDTH/2+.025))
   a[1]|=obs;a[2]|=obs
  return a
 def viamask(self,net,mask):
  # Through vias need clearance on all layers and remain outside component pads to avoid via-in-pad fabrication.
  a=np.any(mask,axis=0).copy()
  a|=(self.X<EDGE+VIA/2)|(self.X>self.w-EDGE-VIA/2)|(self.Y<EDGE+VIA/2)|(self.Y>self.h-EDGE-VIA/2)
  for p in self.ps:a|=self.raster(p['shape'].buffer(VIA/2+(CLEAR+.025 if p['net']!=net else .07)))
  for t in self.tracks:
   if t['net']!=net:a|=self.raster(LineString(t['points']).buffer(t['width']/2+CLEAR+VIA/2+.02))
  for v in self.vias:
   if v['net']!=net:a|=((self.X-v['x'])**2+(self.Y-v['y'])**2<(VIA+CLEAR+.03)**2)
  for x,y in self.b['holes']:a|=((self.X-x)**2+(self.Y-y)**2<((1.1 if self.w<30 else 1.6)+CLEAR+VIA/2+.03)**2)
  if self.input_keepout is not None:a|=self.raster(self.input_keepout.buffer(VIA/2+.025))
  return a
 def find(self,net,p,q,allowed):
  mask=self.mask(net);via=self.viamask(net,mask)
  px,py=int(round(p['x']/GRID)),int(round(p['y']/GRID));qx,qy=int(round(q['x']/GRID)),int(round(q['y']/GRID))
  starts=[(l,py,px) for l in p['layers'] if l in allowed];goals={(l,qy,qx) for l in q['layers'] if l in allowed}
  if not starts or not goals:return None
  for st in starts:mask[st]=False
  for st in goals:mask[st]=False
  costs={st:0. for st in starts};prev={};queue=[];counter=0
  def heur(s):
   dy=abs(s[1]-qy);dx=abs(s[2]-qx);return max(dx,dy)+.41421356*min(dx,dy)+(0 if any(g[0]==s[0] for g in goals) else 12)
  for s in starts:heapq.heappush(queue,(heur(s),0,counter,s));counter+=1
  steps=0;seen=set()
  while queue and steps<45000:
   _,g,_,s=heapq.heappop(queue)
   if s in seen:continue
   if s in goals:
    path=[s]
    while s in prev:s=prev[s];path.append(s)
    return path[::-1]
   seen.add(s);steps+=1;l,y,x=s
   neigh=[]
   for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
    nx,ny=x+dx,y+dy
    if not (0<=nx<self.nx and 0<=ny<self.ny) or mask[l,ny,nx]:continue
    if dx and dy and (mask[l,y,nx] or mask[l,ny,x]):continue
    # Mild layer preferences: no routing on In1 unless ground; low-speed/power prefer In2.
    layercost=(1.5 if l!=1 else 0) if net in ['GND','AGND'] else (0.1 if (l==2 and net not in ['3V3','+5VA','-5VA','5VA_IN','5VA_PMT']) else 0)
    neigh.append(((l,ny,nx),(1.41421356 if dx and dy else 1)+layercost))
   if len(allowed)>1 and not via[y,x]:
    for nl in allowed:
     if nl!=l and not mask[nl,y,x]:neigh.append(((nl,y,x),4.0 if net in ['GND','AGND'] else 16.0))
   # Plated holes provide zero extra via when the search reaches their centre.
   for pad in (p,q):
    if pad['drill'] and abs(pad['x']/GRID-x)<.55 and abs(pad['y']/GRID-y)<.55:
     neigh += [((nl,y,x),.05) for nl in allowed if nl!=l and not mask[nl,y,x]]
   for ns,ds in neigh:
    ng=g+ds
    if ng<costs.get(ns,1e30):costs[ns]=ng;prev[ns]=s;heapq.heappush(queue,(ng+heur(ns),ng,counter,ns));counter+=1
  return None
 def emit(self,net,p,q,path):
  # Compress straight grid runs, retaining exact original pad centres for solid electrical contact.
  chunks=[];l=path[0][0];pts=[(p['x'],p['y']),(path[0][2]*GRID,path[0][1]*GRID)]
  for a,b in zip(path,path[1:]):
   if a[0]!=b[0]:
    pos=(a[2]*GRID,a[1]*GRID);pts.append(pos);chunks.append((l,pts));l=b[0];pts=[pos]
    if not any(z['drill'] and math.hypot(z['x']-pos[0],z['y']-pos[1])<.08 for z in self.ps):
     if not any(v['net']==net and math.hypot(v['x']-pos[0],v['y']-pos[1])<.01 for v in self.vias):self.vias.append(dict(net=net,x=pos[0],y=pos[1],size=VIA,drill=DRILL))
   else:pts.append((b[2]*GRID,b[1]*GRID))
  pts.append((q['x'],q['y']));chunks.append((l,pts))
  for l,pts in chunks:
   out=[]
   for t in pts:
    t=[round(t[0],5),round(t[1],5)]
    if out and t==out[-1]:continue
    if len(out)>=2:
     a,b=out[-2],out[-1]
     if abs((b[0]-a[0])*(t[1]-b[1])-(b[1]-a[1])*(t[0]-b[0]))<1e-9:out.pop()
    out.append(t)
   if len(out)>1:self.tracks.append(dict(net=net,layer=l,width=WIDTH,points=out))
  self.edges.append(dict(net=net,source=f'{p["ref"]}.{p["pin"]}',target=f'{q["ref"]}.{q["pin"]}'))
 def run(self,critical_only=False):
  nets=sorted({p['net'] for p in self.ps if p['net']})
  pri=['PD_SUM','REF_SUM','PMT_I','TIA_OUT','REF_TIA','FDA_P','FDA_N','D_A_P','D_A_N','CMP_P','CMP_OUT','SYNC','THRESH','VBIAS','REF_V','ADC_A_P','ADC_A_N','OFFSET_0V5','ADC_VCM','PMT_VREF','PMT_VCONT','PD_NBIAS','5VA_IN','5VA_PMT','3V3','+5VA','-5VA','GND','AGND']
  nets.sort(key=lambda n:pri.index(n) if n in pri else 100)
  for net in nets:
   if critical_only and net not in ['PMT_I','TIA_OUT']:continue
   ps=[p for p in self.ps if p['net']==net]
   if len(ps)<2:continue
   if net in ['PD_SUM','PMT_I']:allowed=[0]
   elif net=='REF_SUM':allowed=[3]
   elif net in ['GND','AGND']:allowed=[0,1,3]
   elif net in ['5VA_IN','5VA_PMT','3V3','+5VA','-5VA']:allowed=[0,2,3]
   else:allowed=[0,2,3]
   connected=[ps.pop(0)]
   while ps:
    candidates=sorted([(math.hypot(a['x']-b['x'],a['y']-b['y']),i,j) for i,a in enumerate(connected) for j,b in enumerate(ps)])
    success=False
    for _,i,j in candidates[:3]:
     a,b=connected[i],ps[j];path=self.find(net,a,b,allowed)
     if path:
      self.emit(net,a,b,path);connected.append(ps.pop(j));success=True;break
    if not success:
     p=ps.pop(0);self.fail.append(dict(net=net,target=p['ref']+'.'+p['pin'],reason='GRID_NO_ROUTE_OR_LAYER_POLICY'));connected.append(p)
   print(self.b['id'],net,'tracks',len(self.tracks),'vias',len(self.vias),'fail',len(self.fail),flush=True)
  return dict(board=self.b['id'],grid_mm=GRID,track_width_mm=WIDTH,clearance_mm=CLEAR,via_size_mm=VIA,via_drill_mm=DRILL,tracks=self.tracks,vias=self.vias,attempted_edges=self.edges,unrouted=self.fail,input_keepout=list(self.input_keepout.bounds) if self.input_keepout else None,scope='CUSTOM_GRID_MODEL; NATIVE_DRC_NOT_RUN; PCB_ZONES_UNFILLED',critical_only=critical_only)
def main():
 D,F,P=load();only=sys.argv[1:]
 for b in D['boards']:
  if only and b['id'] not in only:continue
  t=time.time();x=Router(b,P,F).run(critical_only=b['id']=='B01');x['elapsed_s']=round(time.time()-t,2)
  (ROOT/'engineering'/f'{b["id"]}_routing.json').write_text(json.dumps(x,indent=2));print('DONE',b['id'],x['elapsed_s'],flush=True)
if __name__=='__main__':main()
