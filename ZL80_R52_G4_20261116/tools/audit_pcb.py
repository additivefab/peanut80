"""Independent read-back audit of emitted copper. NOT KiCad ERC or DRC.
Uses no router connectivity edges. Zones are not treated as filled copper.
"""
from pathlib import Path
import json,math,csv
from collections import defaultdict
from shapely.geometry import Point,box,LineString
from shapely.affinity import rotate,translate
from shapely.strtree import STRtree
from sexpr import loads,child,children
from pcb_geometry import ROOT,LAYERS,load,pads_for

def floats(row):return list(map(float,row[1:]))
def parse(bid):
 p=ROOT/'electronics/projects'/bid/(bid+'_G4.kicad_pcb');r=loads(p.read_text());obs=[];holes=[];expected={}
 netmap={int(z[1]):z[2] for z in children(r,'net')}
 for fp in children(r,'footprint'):
  ref=next(z[2] for z in children(fp,'property') if z[1]=='Reference');at=floats(child(fp,'at'));cx,cy=at[:2];ang=at[2] if len(at)>2 else 0
  for z in children(fp,'pad'):
   a=floats(child(z,'at'));x,y=a[:2];pa=a[2] if len(a)>2 else 0;co,si=math.cos(math.radians(ang)),math.sin(math.radians(ang));x,y=cx+x*co+y*si,cy-x*si+y*co
   w,h=floats(child(z,'size'));dr=child(z,'drill');nr=child(z,'net');net=nr[2] if nr else '';ls=child(z,'layers')[1:];ly=list(range(4)) if '*.Cu' in ls else [LAYERS.index(v) for v in ls if v in LAYERS]
   shape=Point(x,y).buffer(w/2,32) if z[3]=='circle' else translate(rotate(box(-w/2,-h/2,w/2,h/2),-pa,origin=(0,0)),x,y)
   if z[2]=='np_thru_hole':holes.append((x,y,float(dr[1])));continue
   obs.append(dict(name=ref+'.'+z[1],kind='pad',net=net,x=x,y=y,shape=shape,layers=ly));expected[(ref,z[1])]=(net,x,y)
 for k,z in enumerate(children(r,'segment')):
  start=floats(child(z,'start'));end=floats(child(z,'end'));w=float(child(z,'width')[1]);net=netmap[int(child(z,'net')[1])];layer=LAYERS.index(child(z,'layer')[1])
  obs.append(dict(name='segment_'+str(k),kind='track',net=net,shape=LineString([start,end]).buffer(w/2,8),layers=[layer],length=math.dist(start,end)))
 for k,z in enumerate(children(r,'via')):
  at=floats(child(z,'at'));dia=float(child(z,'size')[1]);net=netmap[int(child(z,'net')[1])]
  obs.append(dict(name='via_'+str(k),kind='via',net=net,shape=Point(*at).buffer(dia/2,32),layers=list(range(4))))
 return r,obs,holes,expected

def run_board(bid):
 D,F,P=load();b=next(x for x in D['boards'] if x['id']==bid);r,obs,holes,actual=parse(bid);issues=[];parent=list(range(len(obs)))
 def find(x):
  while x!=parent[x]:parent[x]=parent[parent[x]];x=parent[x]
  return x
 def union(a,b):
  a,b=find(a),find(b)
  if a!=b:parent[b]=a
 W,H=b['size_mm'];outline=box(0,0,W,H)
 for l in range(4):
  ids=[i for i,o in enumerate(obs) if l in o['layers']];shapes=[obs[i]['shape'] for i in ids];tree=STRtree(shapes)
  for ii,i in enumerate(ids):
   o=obs[i]
   for jj in tree.query(o['shape'].buffer(.15+1e-7)):
    j=ids[int(jj)]
    if j<=i:continue
    p=obs[j];dist=o['shape'].distance(p['shape'])
    if o['net'] and o['net']==p['net']:
     if dist<1e-6:union(i,j)
    elif dist<.1499:
     issues.append(dict(board=bid,type='copper_clearance',a=o['name'],b=p['name'],layer=LAYERS[l],net_a=o['net'],net_b=p['net'],value_mm=round(dist,6)))
 for o in obs:
  if not outline.buffer(-.2499).covers(o['shape']):issues.append(dict(board=bid,type='edge',a=o['name'],b='',layer='',net_a=o['net'],net_b='',value_mm=round(o['shape'].distance(outline.boundary),6)))
  for hi,(x,y,d) in enumerate(holes):
   gap=o['shape'].distance(Point(x,y).buffer(d/2,24))
   if gap<.2499:issues.append(dict(board=bid,type='npth_clearance',a=o['name'],b='H'+str(hi+1),layer='',net_a=o['net'],net_b='',value_mm=round(gap,6)))
 # Rule areas are independently inspected, excluding TH pads but including copper of through-vias.
 for z in children(r,'zone'):
  if not child(z,'keepout'):continue
  l=LAYERS.index(child(z,'layer')[1]);pts=[floats(p) for p in child(child(z,'polygon'),'pts')[1:]]
  from shapely.geometry import Polygon
  area=Polygon(pts)
  for o in obs:
   if l in o['layers'] and o['kind'] in ['track','via'] and area.intersection(o['shape']).area>1e-8:
    issues.append(dict(board=bid,type='input_keepout',a=o['name'],b='',layer=LAYERS[l],net_a=o['net'],net_b='',value_mm=0))
 groups=defaultdict(lambda:defaultdict(list))
 for i,o in enumerate(obs):
  if o['kind']=='pad' and o['net']:groups[o['net']][find(i)].append(o['name'])
 netrows=[]
 for net,gr in groups.items():netrows.append(dict(board=bid,net=net,pad_count=sum(map(len,gr.values())),islands=len(gr),unconnected_min_links=max(0,len(gr)-1),groups=' | '.join(','.join(v) for v in gr.values())))
 parity=[]
 for p in pads_for(bid,P,F):
  ac=actual.get((p['ref'],p['pin']));ok=bool(ac and ac[0]==p['net'] and abs(ac[1]-p['x'])<1e-5 and abs(ac[2]-p['y'])<1e-5)
  parity.append(dict(board=bid,ref=p['ref'],pin=p['pin'],net=p['net'],match=ok))
 # independently check schematic instance pin labels: same G2 topology, audit graph tool added later.
 return dict(board=bid,segments=sum(o['kind']=='track' for o in obs),vias=sum(o['kind']=='via' for o in obs),pads=sum(o['kind']=='pad' for o in obs),track_length_mm=round(sum(o.get('length',0) for o in obs),3),clearance_violations=len(issues),unconnected_min_links=sum(x['unconnected_min_links'] for x in netrows),unconnected_nets=[x['net'] for x in netrows if x['islands']>1],pad_parity_pass=all(x['match'] for x in parity),zones_filled=False,native_drc='NOT_RUN',scope='geometric copper audit only; not electrical/thermal/EMC correctness'),issues,netrows,parity

def writecsv(p,rows):
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  if rows:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
  else:f.write('status\nNO_FINDINGS_IN_CHECK_SCOPE\n')
def main():
 summary=[];issues=[];nets=[];parity=[]
 for bid in ['B06','B07','B08','B01']:
  s,i,n,p=run_board(bid);print(s);summary.append(s);issues+=i;nets+=n;parity+=p
 out=ROOT/'validation/results';out.mkdir(exist_ok=True,parents=True)
 (out/'copper_audit.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));writecsv(out/'copper_findings.csv',issues);writecsv(out/'net_connectivity.csv',nets);writecsv(out/'pad_readback.csv',parity)
if __name__=='__main__':main()
