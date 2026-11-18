"""Geometry model for ECR-G3-01 channel E (B05 input + harness W13). Pure python, no CAD kernel.
All coordinates are the R5 global frame (mm). Nothing here is a connector pin-out qualification; it is a placement and corridor check."""
import json,math
from pathlib import Path
E=Path(__file__).resolve().parents[2];V=E.parent;R5=V.parent;G4=R5/'ZL80_R52_G4_20261116'
INST=json.loads((G4/'cad/context/instances.json').read_text())
PLC=[c for c in json.loads((R5/'electronics/component_placements.json').read_text()) if c.get('board')=='B05']
ROUTES={r['id']:r for r in json.loads((G4/'engineering/harness_G3_corridors.json').read_text())}
BOARD=dict(size=(65,100),origin=(-147.5,-15,22.0),top_z=22.0+1.6,holes=[(3,3),(62,3),(62,97),(3,97)],edge=3.0)
HOLE_KEEP=4.5   # radius around each mounting-hole centre kept free of bodies (screw head + clearance)
GAP=1.0         # minimum body-to-body gap on the board
# ---- B05 additions (local board coordinates, body dx,dy,dz)
J3_NEW=dict(ref='J3',xy=(52,72),body=(7,29.2,9),note='2x10 header, was 2x6 at (52,74)')
U3=dict(ref='U3',xy=(26,80),body=(12,10,2),note='SN74LVC3G17 + 3 filter networks (zone)')
J5=dict(ref='J5',xy=(40,93.5),body=(18,7,10),note='1x6 2.54 header, sensor E input')
def rect(c):
    (cx,cy),(w,h,_)=c['xy'],c['body'];return (cx-w/2,cy-h/2,cx+w/2,cy+h/2)
def gap(a,b):
    dx=max(a[0]-b[2],b[0]-a[2],0);dy=max(a[1]-b[3],b[1]-a[3],0);return math.hypot(dx,dy)
def board_check():
    base=[dict(ref=c['ref'],xy=tuple(c['xy']),body=tuple(c['body'])) for c in PLC if c['ref']!='J3']
    new=[J3_NEW,U3,J5];allc=base+new;W,H=BOARD['size'];e=BOARD['edge'];res=dict(overlaps=[],edge=[],holes=[],min_gap_mm=None)
    for c in allc:
        r=rect(c)
        if r[0]<e or r[1]<e or r[2]>W-e or r[3]>H-e:res['edge'].append(c['ref'])
        for hx,hy in BOARD['holes']:
            nx=min(max(hx,r[0]),r[2]);ny=min(max(hy,r[1]),r[3])
            if math.hypot(nx-hx,ny-hy)<HOLE_KEEP:res['holes'].append((c['ref'],(hx,hy)))
    mg=1e9
    for i,a in enumerate(allc):
        for b in allc[i+1:]:
            g=gap(rect(a),rect(b));mg=min(mg,g)
            if g<GAP:res['overlaps'].append((a['ref'],b['ref'],round(g,2)))
    res['min_gap_mm']=round(mg,2);res['components']=[dict(ref=c['ref'],rect=[round(v,1) for v in rect(c)],note=c.get('note','existing')) for c in allc]
    return res
def to_global(x,y,z=None):
    o=BOARD['origin'];return (o[0]+x,o[1]+y,BOARD['top_z'] if z is None else z)
# ---- harness W13 round-cable centreline (global). Starts at the adaptor board on the motor-bracket stand; the last point is a 12 mm plug-pull straight above J5
J5G=to_global(*J5['xy'])
W13=[(119.3,39.0,131.0),(119.3,39.0,150.0),(119.3,J5G[1],150.0),(J5G[0],J5G[1],150.0),(J5G[0],J5G[1],BOARD['top_z']+J5['body'][2]+12.0)]
W13_D=4.0;W13_MINBEND=15.0
def seg_len(p,q):return math.dist(p,q)
def fillet_report(P,R):
    """For every interior vertex: turning angle, tangent length for radius R, and the largest radius the adjacent segments allow."""
    out=[];arc=0.0;tang=0.0
    for i in range(1,len(P)-1):
        a=[P[i][k]-P[i-1][k] for k in range(3)];b=[P[i+1][k]-P[i][k] for k in range(3)]
        la=math.hypot(*a);lb=math.hypot(*b);c=sum(a[k]*b[k] for k in range(3))/(la*lb);th=math.acos(max(-1,min(1,c)))
        if th<1e-6:continue
        t=R*math.tan(th/2);avail=min(la/2 if i>1 else la,lb/2 if i<len(P)-2 else lb)
        rmax=avail/math.tan(th/2);out.append(dict(vertex=i,turn_deg=round(math.degrees(th),1),tangent_mm=round(t,1),r_max_mm=round(rmax,1),ok=t<=avail+1e-9))
        arc+=R*th;tang+=2*t
    return out,arc,tang
def length_with_fillets(P,R):
    L=sum(seg_len(P[i],P[i+1]) for i in range(len(P)-1));rep,arc,tang=fillet_report(P,R);return L-tang+arc,rep
def fillet_points(P,R,n=8):
    """Densified centreline with circular fillets of radius R at interior vertices."""
    pts=[P[0]]
    for i in range(1,len(P)-1):
        a=[P[i][k]-P[i-1][k] for k in range(3)];b=[P[i+1][k]-P[i][k] for k in range(3)]
        la=math.hypot(*a);lb=math.hypot(*b);ua=[v/la for v in a];ub=[v/lb for v in b];c=sum(ua[k]*ub[k] for k in range(3));th=math.acos(max(-1,min(1,c)))
        if th<1e-6:pts.append(P[i]);continue
        t=R*math.tan(th/2);s=[P[i][k]-ua[k]*t for k in range(3)];e=[P[i][k]+ub[k]*t for k in range(3)]
        bis=[ub[k]-ua[k] for k in range(3)];bl=math.hypot(*bis);bis=[v/bl for v in bis]
        cen=[P[i][k]+bis[k]*R/math.cos(th/2) for k in range(3)]   # centre lies inside the turn, R/cos(th/2) from the vertex
        d0=[s[k]-cen[k] for k in range(3)];d1=[e[k]-cen[k] for k in range(3)]
        for j in range(n+1):
            f=j/n;v=[d0[k]*(1-f)+d1[k]*f for k in range(3)];vl=math.hypot(*v);pts.append(tuple(cen[k]+v[k]/vl*R for k in range(3)))
    pts.append(P[-1]);return pts
def seg_seg_dist(p1,q1,p2,q2):
    """Minimum distance between two 3D segments."""
    import itertools
    u=[q1[k]-p1[k] for k in range(3)];v=[q2[k]-p2[k] for k in range(3)];w=[p1[k]-p2[k] for k in range(3)]
    a=sum(x*x for x in u);b=sum(u[k]*v[k] for k in range(3));c=sum(x*x for x in v);d=sum(u[k]*w[k] for k in range(3));e=sum(v[k]*w[k] for k in range(3))
    D=a*c-b*b;sN=sD=D;tN=tD=D
    if D<1e-9:sN=0.0;sD=1.0;tN=e;tD=c
    else:
        sN=b*e-c*d;tN=a*e-b*d
        if sN<0:sN=0;tN=e;tD=c
        elif sN>sD:sN=sD;tN=e+b;tD=c
    if tN<0:
        tN=0
        if -d<0:sN=0
        elif -d>a:sN=sD
        else:sN=-d;sD=a
    elif tN>tD:
        tN=tD
        if (-d+b)<0:sN=0
        elif (-d+b)>a:sN=sD
        else:sN=-d+b;sD=a
    sc=0 if abs(sN)<1e-9 else sN/sD;tc=0 if abs(tN)<1e-9 else tN/tD
    dp=[w[k]+sc*u[k]-tc*v[k] for k in range(3)];return math.hypot(*dp)
def poly_poly_dist(A,B):
    m=1e9;at=None
    for i in range(len(A)-1):
        for j in range(len(B)-1):
            d=seg_seg_dist(A[i],A[i+1],B[j],B[j+1])
            if d<m:m=d;at=(i,j)
    return m,at
def seg_box_gap(p,q,box,n=60):
    """Conservative gap between a segment (sampled) and an axis aligned box [x0,y0,z0,x1,y1,z1]."""
    m=1e9
    for i in range(n+1):
        f=i/n;pt=[p[k]+(q[k]-p[k])*f for k in range(3)]
        d=[max(box[k]-pt[k],pt[k]-box[k+3],0) for k in range(3)];m=min(m,math.hypot(*d))
    return m
def b05_boxes():
    out=[]
    for c in PLC:
        if c['ref']=='J3':continue
        out.append((c['ref'],c))
    allc=[(c['ref'],dict(xy=c['xy'],body=c['body'])) for c in PLC if c['ref']!='J3']+[('J3',J3_NEW),('U3',U3),('J5',J5)]
    res=[]
    for ref,c in allc:
        r=rect(dict(xy=c['xy'],body=c['body']));o=BOARD['origin'];res.append((f'B05_{ref}',[o[0]+r[0],o[1]+r[1],BOARD['top_z'],o[0]+r[2],o[1]+r[3],BOARD['top_z']+c['body'][2]]))
    return res
