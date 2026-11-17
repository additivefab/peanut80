"""Monte-Carlo screen of the ZL80 collector: integrating cylinder (ID40 x 120, Lambertian wall 0.98,
104 x 1.2 slot) + PMMA guide + PMT (effective dia 8). Design screening only, not a measurement.
Simplifications: ideal Lambertian liner, no seams, flat port, no PMMA absorption, side faces either
total-internal-reflection or lost (optionally a 0.97 specular wrap), statistical error about 1-2 %.
Usage: python engineering/collector_guide_mc.py 120000 engineering/collector_guide_variants.json engineering/导光件方案对比_蒙特卡洛.csv"""
import math,random,sys,json
from multiprocessing import Pool
R=20.0;HL=60.0;RHO=0.98;SLOT_L=52.0;SLOT_W=0.6;N_PMMA=1.49;PMT_R=4.0
SINC=1/N_PMMA
def norm(v):
    m=math.sqrt(v[0]*v[0]+v[1]*v[1]+v[2]*v[2]);return (v[0]/m,v[1]/m,v[2]/m)
def lambert(n,rng):
    # cosine-weighted direction about unit normal n
    u,v=rng.random(),rng.random();r=math.sqrt(u);ph=2*math.pi*v
    a=(1,0,0) if abs(n[0])<0.9 else (0,1,0)
    t=norm((a[1]*n[2]-a[2]*n[1],a[2]*n[0]-a[0]*n[2],a[0]*n[1]-a[1]*n[0]))
    b=(n[1]*t[2]-n[2]*t[1],n[2]*t[0]-n[0]*t[2],n[0]*t[1]-n[1]*t[0])
    c=math.sqrt(1-u);x=r*math.cos(ph);y=r*math.sin(ph)
    return (x*t[0]+y*b[0]+c*n[0],x*t[1]+y*b[1]+c*n[1],x*t[2]+y*b[2]+c*n[2])
def refract(d,n,n1,n2):
    # n = unit normal pointing against d (into incident medium). returns (dir, transmittance) or None for TIR
    ci=-(d[0]*n[0]+d[1]*n[1]+d[2]*n[2]);e=n1/n2;s2=e*e*(1-ci*ci)
    if s2>=1: return None
    ct=math.sqrt(1-s2)
    rs=((n1*ci-n2*ct)/(n1*ci+n2*ct))**2;rp=((n1*ct-n2*ci)/(n1*ct+n2*ci))**2
    k=e*ci-ct
    return (e*d[0]+k*n[0],e*d[1]+k*n[1],e*d[2]+k*n[2]),1-0.5*(rs+rp)
def make_guide(wx_in,hz_in,wx_out,hz_out,L):
    """Frustum with rectangular ends; local coords: input face at y=0 (cavity side), output at y=-L. planes: (normal outward, point)."""
    pl=[((0,1,0),(0,0,0),'in'),((0,-1,0),(0,-L,0),'out')]
    for sx in (1,-1):
        n=norm((sx*L,-(wx_in-wx_out)/2*1.0,0)) ; n=norm((sx*L, -(wx_in-wx_out)/2,0))
        # side plane through (sx*wx_in/2,0,0) and (sx*wx_out/2,-L,0); outward normal has +sx x-component and -y component
        pl.append((norm((sx*L,-(wx_in-wx_out)/2,0)),(sx*wx_in/2,0,0),'side'))
    for sz in (1,-1):
        pl.append((norm((0,-(hz_in-hz_out)/2,sz*L)),(0,0,sz*hz_in/2),'side'))
    return pl
def trace_guide(pl,p,d,cfg,rng):
    """returns ('pmt',w) / ('back',p,d,w) / ('lost',)"""
    w=1.0
    for _ in range(400):
        best=None
        for n,q,kind in pl:
            dn=d[0]*n[0]+d[1]*n[1]+d[2]*n[2]
            if dn<=1e-12: continue
            s=((q[0]-p[0])*n[0]+(q[1]-p[1])*n[1]+(q[2]-p[2])*n[2])/dn
            if s<1e-9: s=0.0
            if best is None or s<best[0]: best=(s,n,kind,dn)
        if best is None: return ('lost',)
        s,n,kind,dn=best
        p=(p[0]+s*d[0],p[1]+s*d[1],p[2]+s*d[2])
        if kind=='side':
            if dn<math.sqrt(1-SINC*SINC):   # incidence beyond critical: TIR
                d=(d[0]-2*dn*n[0],d[1]-2*dn*n[1],d[2]-2*dn*n[2]);continue
            if cfg.get('mirror_sides'):     # external specular wrap with air gap (ESR-like), 0.97
                w*=0.97;d=(d[0]-2*dn*n[0],d[1]-2*dn*n[1],d[2]-2*dn*n[2]);continue
            return ('lost',)
        if kind=='out':
            if cfg['grease']:
                if cfg.get('round_out') or True:
                    if p[0]*p[0]+p[2]*p[2]<=PMT_R*PMT_R: return ('pmt',w)
                return ('lost',)
            r=refract(d,(-n[0],-n[1],-n[2]),N_PMMA,1.0)
            if r is None:
                d=(d[0]-2*dn*n[0],d[1]-2*dn*n[1],d[2]-2*dn*n[2]);continue
            d2,T=r;g=cfg['gap']/abs(d2[1]);x=p[0]+g*d2[0];z=p[2]+g*d2[2]
            if x*x+z*z<=PMT_R*PMT_R: return ('pmt',w*T*0.96)   # 0.96: PMT window front surface
            return ('lost',)
        # input face from inside
        r=refract(d,(-n[0],-n[1],-n[2]),N_PMMA,1.0)
        if r is None:
            d=(d[0]-2*dn*n[0],d[1]-2*dn*n[1],d[2]-2*dn*n[2]);continue
        return ('back',p,r[0],w*r[1])
    return ('lost',)
def run(args):
    cfg,x0,N,seed=args
    rng=random.Random(seed)
    port_hx,port_hz=cfg['port'][0]/2,cfg['port'][1]/2
    pl=None if cfg['kind']=='direct' else make_guide(*cfg['guide'])
    tot=0.0;first=0.0
    for i in range(N):
        # ray enters through slot, narrow cone about -Z, lands near bottom
        th=abs(rng.gauss(0,math.radians(cfg.get('src_sigma_deg',3))));ph=rng.random()*2*math.pi
        d=(math.sin(th)*math.cos(ph),math.sin(th)*math.sin(ph),-math.cos(th));p=(x0,0.0,R-1e-6);w=1.0;nb=0
        while w>2e-3:
            # intersect cylinder (y,z) and end caps
            a=d[1]*d[1]+d[2]*d[2];s_c=1e30
            if a>1e-14:
                b=p[1]*d[1]+p[2]*d[2];c=p[1]*p[1]+p[2]*p[2]-R*R
                disc=b*b-a*c
                if disc>0: s_c=(-b+math.sqrt(disc))/a
            s_e=((HL if d[0]>0 else -HL)-p[0])/d[0] if abs(d[0])>1e-14 else 1e30
            if s_e<s_c:
                p=(p[0]+s_e*d[0],p[1]+s_e*d[1],p[2]+s_e*d[2]);n=(-1.0 if d[0]>0 else 1.0,0,0)
            else:
                p=(p[0]+s_c*d[0],p[1]+s_c*d[1],p[2]+s_c*d[2]);n=(0,-p[1]/R,-p[2]/R)
                if p[2]>0 and abs(p[1])<SLOT_W and abs(p[0])<SLOT_L: break            # escapes through slot
                if p[1]<0 and abs(p[2])<port_hz and abs(p[0])<port_hx and (cfg['kind']!='direct' or p[0]*p[0]+p[2]*p[2]<port_hx*port_hx):
                    if cfg['kind']=='direct':
                        tot+=w*0.92
                        if nb==1: first+=w*0.92
                        break
                    r=refract(d,(0,1,0),1.0,N_PMMA)
                    res=trace_guide(pl,(p[0],0.0,p[2]),r[0],cfg,rng)
                    w*=r[1]
                    if res[0]=='pmt':
                        tot+=w*res[1]
                        if nb==1: first+=w*res[1]
                        break
                    if res[0]=='lost': break
                    _,q,d,w2=res;w*=w2
                    zz=max(-port_hz,min(port_hz,q[2]));p=(q[0],-math.sqrt(R*R-zz*zz)+1e-6,zz);continue
            w*=RHO;nb+=1;d=lambert(n,rng)
    return cfg['name'],x0,tot/N,first/N
if __name__=='__main__':
    N=int(sys.argv[1]) if len(sys.argv)>1 else 30000
    cfgs=json.load(open(sys.argv[2]))
    jobs=[(c,x,N,1000+7*k) for c in cfgs for k,x in enumerate((0,20,40,50))]
    with Pool(8) as pool: res=pool.map(run,jobs)
    out={}
    for name,x,t,f in res: out.setdefault(name,[]).append((x,round(t,4),round(f,4)))
    if len(sys.argv)>3:
        import csv
        with open(sys.argv[3],'w',newline='',encoding='utf-8-sig') as fh:
            wr=csv.writer(fh);wr.writerow(['variant','rays_per_position','collect_x0','collect_x20','collect_x40','collect_x50','first_strike_x0','nonuniformity_roi_pct','evidence'])
            for k,v in out.items():
                m=[t for _,t,_ in v]
                wr.writerow([k,N]+m+[v[0][2],round(100*(max(m[:3])-min(m[:3]))/(sum(m[:3])/3),1),'MONTE_CARLO_SCREEN_NOT_MEASURED'])
    for k,v in out.items():
        m=[t for _,t,_ in v];print(k,' '.join(f'x{x}:{t:.4f}(1st {f:.4f})' for x,t,f in v),' nonunif(max-min)/mean=%.1f%%'%(100*(max(m[:3])-min(m[:3]))/(sum(m[:3])/3)))
