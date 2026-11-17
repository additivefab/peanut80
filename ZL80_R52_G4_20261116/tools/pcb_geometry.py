from pathlib import Path
import math,json
from shapely.geometry import Point,Polygon,box,LineString
from shapely.affinity import rotate,translate
ROOT=Path(__file__).resolve().parents[1]
LAYERS=['F.Cu','In1.Cu','In2.Cu','B.Cu']
def load():return json.loads((ROOT/'engineering/circuits.json').read_text()),json.loads((ROOT/'engineering/footprints.json').read_text()),json.loads((ROOT/'engineering/placements.json').read_text())
def xy(c,p):
 # Native KiCad positive footprint rotations are counter-clockwise in screen coordinates (Y down).
 x=p['x']*(-1 if c['side']=='B' else 1);y=p['y'];a=math.radians(c.get('angle',0));co,si=math.cos(a),math.sin(a)
 return (c['pcb_xy'][0]+x*co+y*si,c['pcb_xy'][1]-x*si+y*co)
def rotated_rect(c,w,h):
 a=-c.get('angle',0);return translate(rotate(box(-w/2,-h/2,w/2,h/2),a,origin=(0,0)),*c['pcb_xy'])
def pads_for(bid,P,F):
 rows=[]
 for c in [x for x in P if x['board']==bid]:
  for p in F[c['fp']]['pads']:
   x,y=xy(c,p)
   shape=Point(x,y).buffer(p['w']/2,resolution=12) if p['drill'] else translate(rotate(box(-p['w']/2,-p['h']/2,p['w']/2,p['h']/2),-c.get('angle',0),origin=(0,0)),x,y)
   rows.append(dict(ref=c['ref'],pin=p['num'],net=c['nets'].get(p['num'],''),x=x,y=y,w=p['w'],h=p['h'],drill=p['drill'],layers=list(range(4)) if p['drill'] else [0 if c['side']=='F' else 3],shape=shape))
 return rows
