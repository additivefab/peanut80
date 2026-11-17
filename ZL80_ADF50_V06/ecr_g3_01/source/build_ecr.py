"""ECR-G3-01 (approved 2026-11-17): independent follower encoder on the exit pressure (upper) roller of the G3 four-roller package.
A diametric magnet in a carrier sleeve on the Ø6 right shaft tip of the upper roller core (G3-R03), a small magnetic-encoder board facing it,
and a bracket that rides on the right bearing cap (G3-M06 upper, moves with the roller). Nothing existing is cut except that the carrier
slides over the Ø6 tip. Nominal geometry in the R5 global frame; checked against the G3 integrated context at three roller heights.
Needs cadquery."""
import json,math,sys
from pathlib import Path
import cadquery as cq
E=Path(__file__).resolve().parents[1];V=E.parent;R5=V.parent;G3=R5/'ZL80_R52_G3_20261116'
AX=(42.0,120.1)                                   # exit upper roller axis (Y,Z)
def cylx(x0,x1,d):return cq.Workplane('YZ').workplane(offset=x0).center(*AX).circle(d/2).extrude(x1-x0).val()
def box(x0,x1,y0,y1,z0,z1):return cq.Workplane('XY').box(x1-x0,y1-y0,z1-z0).val().translate(cq.Vector((x0+x1)/2,(y0+y1)/2,(z0+z1)/2))
P={}
carrier=cylx(80.0,88.2,9).cut(cylx(79.9,84.2,6.0)).cut(cylx(85.7,88.3,6.1));P['G3E-01']=('磁铁载体套 Ø9×8.2（铝，Ø6 内孔套在上辊右轴端）',carrier,'6061-T6',2.70,'车削；内孔 Ø6 H7，粘接加顶丝；端面 Ø6.1×2.5 磁铁槽')
magnet=cylx(85.7,88.2,6.0);P['G3E-02']=('径向充磁钕铁硼磁铁 Ø6×2.5',magnet,'外购',7.40,'压入载体槽，面低于载体端面 0')
board=box(90.2,91.8,36,48,115.1,125.1).fuse(box(89.2,90.2,AX[0]-2.5,AX[0]+2.5,AX[1]-2.2,AX[1]+2.2)).clean();P['G3E-03']=('磁编码器小板 12×12×1.6（芯片面朝磁铁，ABI 输出）',board,'外购',2.0,'候选 AS5047P 类，手册指标待核对；气隙 1.0 mm；芯片中心对轴 ±0.25 mm')
bracket=box(78.1,91.8,32.5,51.5,130.2,131.7).fuse(box(78.1,79.6,32.5,37.5,124.6,131.7)).fuse(box(78.1,79.6,46.5,51.5,124.6,131.7)).fuse(box(90.2,91.8,36,48,125.1,131.7)).clean();P['G3E-04']=('编码器支架（Z 形，两耳固定在右轴承压盖外侧面）',bracket,'5052-H32',2.68,'折弯 t1.5；两耳套在 G3-M06 上排两颗压盖螺钉下，这两颗换成长 1.5 mm 的同规格螺钉；随上辊升降')
asm=cq.Assembly(name='ECR_G3_01')
for k,(n,s,m,rho,note) in P.items():
    asm.add(s,name=k);(E/'step').mkdir(exist_ok=True);cq.exporters.export(cq.Workplane('XY').add(s),str(E/'step'/f'{k}.step'))
asm.save(str(E/'step'/'ECR_G3_01_exit_follower_encoder.step'))
mass={k:round(s.Volume()*rho/1000,2) for k,(n,s,m,rho,note) in P.items()}
mass['G3E-03']=1.5   # assumed: board with chip, capacitor and connector (solid block would give 0.43 g)
moving=mass['G3E-03']+mass['G3E-04']+mass['G3E-01']+mass['G3E-02']
# ---- interference against the G3 integrated context at three upper-roller heights (0, +5 release lift, -1)
inst=json.loads((G3/'cad/instances.json').read_text());cache={};res={};tight={};REPLACED={'CAP_SCREW_72_42_120.1_-7_7','CAP_SCREW_72_42_120.1_7_7'}
def load(pid):
    if pid not in cache:cache[pid]=cq.importers.importStep(str(G3/'cad/parts'/f'{pid}.step')).val()
    return cache[pid]
def placed(row,dz=0.0):
    sh=load(row['part'])
    if row.get('rotation'):ax,ang=row['rotation'];sh=sh.rotate(cq.Vector(0,0,0),cq.Vector(*ax),ang)
    sh=sh.translate(cq.Vector(*row['position']))
    return sh.translate(cq.Vector(0,0,dz)) if row.get('moves_with_upper') else sh
for dz in (0.0,5.0,-1.0):
    hits=[];near=[]
    ecr_shapes={k:(s.translate(cq.Vector(0,0,dz)) if k in ('G3E-03','G3E-04','G3E-01','G3E-02') else s) for k,(n,s,m,rho,note) in P.items()}
    for row in inst:
        if row['name'] in REPLACED:continue
        bb=list(row['aabb'])
        if row.get('moves_with_upper'):bb[2]+=dz;bb[5]+=dz
        if bb[3]<70 or bb[0]>100 or bb[4]<25 or bb[1]>58:continue
        sh=placed(row,dz)
        for k,s in ecr_shapes.items():
            d=sh.distance(s)
            if d<=1e-6:
                v=sh.intersect(s).Volume()
                if v>0.01:hits.append(dict(ecr=k,g3=row['name'],g3_part=row['part'],volume_mm3=round(v,3)))
                else:near.append((0.0,k,row['name']))
            elif d<3.0:near.append((round(d,2),k,row['name']))
    res[f'dz_{dz:+.0f}']=dict(overlaps=hits,min_clearances_lt3mm=sorted(set(near))[:14])
out=dict(scope='ECR-G3-01 nominal geometry vs G3 integrated context (238 instances), parts that move with the upper roller lifted by dz. Rigid, no tolerances, no fasteners, no cable.',
    parts={k:dict(name=n,material=m,process_note=note,volume_mm3=round(s.Volume(),1),mass_g=mass[k],mass_basis='assumed' if k=='G3E-03' else 'volume x nominal density') for k,(n,s,m,rho,note) in P.items()},
    moving_mass_added_g=round(moving,2),rotating_mass_added_g=round(mass['G3E-01']+mass['G3E-02'],2),interference=res,
    replaced_g3_screws=sorted(REPLACED),axis_yz=AX,magnet_to_chip_gap_mm=1.0,carrier_over_guard_clearance_mm=round(AX[1]-4.5-112.4,2),board_over_guard_clearance_mm=round(115.1-112.4,2))
(E/'interference.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
with open(E/'ECR_G3_01_件表.csv','w',encoding='utf-8-sig') as f:
    f.write('件号,名称,材料,单件质量g,备注\n')
    for k,(n,s,m,rho,note) in P.items():f.write(f'{k},{n},{m},{mass[k]},{note}\n')
print(json.dumps({'moving_g':out['moving_mass_added_g'],'rot_g':out['rotating_mass_added_g'],'interference':{k:{'overlaps':v['overlaps'],'min_clearances':v['min_clearances_lt3mm']} for k,v in res.items()}},ensure_ascii=False,indent=1))
