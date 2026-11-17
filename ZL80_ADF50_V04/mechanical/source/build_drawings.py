"""ADF50 V0.4 mechanical atlas (PDF): assembly views, sub-assembly views, and one cell per part number with an
isometric hidden-line view, overall size, material, process and quantity. Views are projections of the STEP solids;
they are review drawings without tolerances, not released manufacturing drawings. Needs cadquery, pymupdf, reportlab."""
import json,sys
from pathlib import Path
import cadquery as cq, fitz
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas
M=Path(__file__).resolve().parents[1];T=M/'drawings'/'_views';T.mkdir(parents=True,exist_ok=True)
parts=json.loads((M/'parts.json').read_text());chk=json.loads((M/'interference.json').read_text())
def view(shape,name,direction,w=1400,h=1000,hidden=False):
    svg=T/f'{name}.svg'
    cq.exporters.export(cq.Workplane('XY').add(shape),str(svg),opt=dict(width=w,height=h,marginLeft=20,marginTop=20,showAxes=False,projectionDir=direction,strokeWidth=0.6,strokeColor=(20,30,45),hiddenColor=(170,175,185),showHidden=hidden))
    d=fitz.open(str(svg));pg=d[0];r=None
    for it in pg.get_drawings():r=it['rect'] if r is None else r|it['rect']
    r=(r+(-6,-6,6,6))&pg.rect if r else pg.rect;k=min(3.0,1800/max(r.width,1),1300/max(r.height,1))
    pm=pg.get_pixmap(matrix=fitz.Matrix(k,k),clip=r);png=T/f'{name}.png';pm.save(str(png));return png,pm.width,pm.height
def load(n):
    v=cq.importers.importStep(str(M/'step'/n)).vals();return v[0] if len(v)==1 else cq.Compound.makeCompound(v)
def inner(s,lim=46.01):
    v=[q for q in s.Solids() if q.BoundingBox().xmin>=-lim and q.BoundingBox().xmax<=lim];return cq.Compound.makeCompound(v)
ROT=lambda s:s.rotate(cq.Vector(0,0,0),cq.Vector(1,1,1),-120)
def side(s):return inner(s).rotate(cq.Vector(0,0,0),cq.Vector(1,1,1),-120)   # Y->X, Z->Y so a view along +Z shows the Y-Z side elevation
V={}
for g in ('MAG','ENT','BIN'):
    s=load(f'ADF50_V04_{g}_subassembly.step')
    V[g+'_side']=view(side(s) if g!='ENT' else ROT(inner(s,57)),g+'_side',(0,0,1),1400,1000,True);V[g+'_iso']=view(s,g+'_iso',(1,-0.8,0.6))
def low(s,zmax,lim=46.01):
    v=[q for q in s.Solids() if q.BoundingBox().xmin>=-lim and q.BoundingBox().xmax<=lim and q.BoundingBox().zmax<zmax];return ROT(cq.Compound.makeCompound(v))
V['MAG_head']=view(low(load('ADF50_V04_MAG_subassembly.step'),262),'MAG_head',(0,0,1),1400,1000,True)
V['BIN_head']=view(low(load('ADF50_V04_BIN_subassembly.step'),235),'BIN_head',(0,0,1),1400,1000,True)
full=load('ADF50_V04_mechanical_assembly.step')
V['ALL_side']=view(side(full),'ALL_side',(0,0,1),1800,1100,True);V['ALL_iso']=view(full,'ALL_iso',(1,-0.9,0.6),1800,1100);V['ALL_top']=view(full,'ALL_top',(0,0,1),1800,700)
for P in parts:V[P['id']]=view(load(P['id']+'.step'),P['id'],(1,-0.8,0.6),520,360,True)
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'));F='STSong-Light';W,H=landscape(A4)
c=canvas.Canvas(str(M/'drawings'/'ZL80_ADF50_V04_机械图册.pdf'),pagesize=landscape(A4));c.setTitle('ZL80 ADF50 V0.4 机械图册');page=[0]
def frame(title):
    page[0]+=1;c.setFont(F,13);c.drawString(12*mm,H-12*mm,title);c.setFont(F,7.5)
    c.drawString(12*mm,6*mm,f'ZL80 ADF50 V0.4 机械图册 2026-11-17｜名义几何评审图，无公差，非制造放行｜第 {page[0]} 页');c.setLineWidth(.4);c.rect(8*mm,10*mm,W-16*mm,H-26*mm)
def img(key,x,y,w,h):
    png,pw,ph=V[key];k=min(w/pw,h/ph);c.drawImage(str(png),x+(w-pw*k)/2,y+(h-ph*k)/2,pw*k,ph*k)
def lines(x,y,rows,size=9,lead=13):
    c.setFont(F,size)
    for i,r in enumerate(rows):c.drawString(x,y-i*lead,r)
e=chk['working_envelope_mm_WDH'];m=chk['fabricated_mass_g_by_group']
frame('1　总装：内部侧视（去掉两侧板和外侧电机）');img('ALL_side',10*mm,60*mm,W-20*mm,H-80*mm)
lines(12*mm,54*mm,[f"工作包络 宽 {e[0]:.0f} × 深 {e[1]:.1f} × 高 {e[2]:.1f} mm；件号 {chk['part_numbers']} 个，实例 {chk['instances']} 个，其中自制件号 {chk['fabricated_part_numbers']} 个。",
  f"自干涉：{len(chk['self_overlaps'])} 处（检查 {chk['self_pairs_intersected']} 对）；与扫描仪 R5.2 布局干涉：{len(chk['scanner_overlaps'])} 处。舌板穿过前后面板处需开缺口。",
  f"自制件质量（不含电机、紧固件）：片仓模块 {m['MAG']} g，入口辊组 {m['ENT']} g，收片模块 {m['BIN']} g。",
  '侧视图为内部视图，灰线为被遮挡轮廓。左：片仓、分离头、下滑弯道（MAG）；中：前面板内的入口辊组（ENT）；右：上行弯道、排片辊、竖立收片仓（BIN）。扫描仪本体未画出。'])
c.showPage();frame('2　总装：轴测与俯视');img('ALL_iso',10*mm,70*mm,W-20*mm,H-90*mm);img('ALL_top',10*mm,12*mm,W-20*mm,56*mm);c.showPage()
for g,t,note in (('MAG','3　片仓模块 MAG：片仓、分离头、下滑弯道',['推片板由两根顶升轴上的四只顶升臂平行顶起，行程 20.5 mm；两轴由侧板外的曲柄连杆同步，前轴接减速步进。','拾取臂绕送片轴摆动，送片电机经同步带同时带动送片辊和拾取辊。','脱开轴转动时凸轮压下拾取臂尾端抬起拾取辊，同时经拉杆拉下阻尼辊摆杆。','斜坝块按片厚更换（62° / 55° / 38°）。弯道外侧 5 只自由托辊，内导板与片留 3 mm。']),
                 ('ENT','4　入口辊组 ENT：装在前面板内侧，取代入口迷宫',['上辊主动（NEMA11 经同步带），下辊装在摆杆上，由微型减速电机经曲柄脱开。','整组占用了 PMT / 模拟前端的维护拆出空间，因此做成从前面板外侧整体抽出的卡座（上、下横梁各 2 颗螺钉）。']),
                 ('BIN','5　收片模块 BIN：上行弯道、排片辊、竖立收片仓',['排片主动辊在片的后侧，同轴两只软拨片轮；压轮在前侧，装在摆杆上，扫描时脱开。','片尾离开排片辊后由拨片拨到两侧挡台上，片立在后壁前，后仰 10°。前挡板透明。'])):
    frame(t);img(g+'_side',10*mm,40*mm,(W-20*mm)/2,H-58*mm);img(g+'_iso',W/2,40*mm,(W-20*mm)/2,H-58*mm);lines(12*mm,34*mm,note,8.5,11);c.showPage()
frame('6　放大：分离头与下滑弯道（左），排片辊与上行弯道（右），内部侧视');img('MAG_head',10*mm,24*mm,(W-20*mm)/2,H-44*mm);img('BIN_head',W/2,24*mm,(W-20*mm)/2,H-44*mm)
lines(12*mm,18*mm,['左图自上而下：拾取胶轮、斜坝块、送片胶辊与限矩阻尼胶辊、超声传感器、托辊 5 只、内导板与外护板。右图：托辊、排片主动辊与软拨片轮、压轮与摆杆、片尾挡台。'],8.5,11);c.showPage()
cols,rws=4,3;cw,chh=(W-16*mm)/cols,(H-26*mm)/rws;n=0
for i,P in enumerate(parts):
    if i%(cols*rws)==0:
        if i:c.showPage()
        n+=1;frame(f'7.{n}　零件一览（件号、外形、材料、工艺、数量）')
    k=i%(cols*rws);x=8*mm+(k%cols)*cw;y=H-16*mm-(k//cols+1)*chh;c.setLineWidth(.3);c.rect(x,y,cw,chh)
    img(P['id'],x+2,y+16*mm,cw-4,chh-22*mm)
    c.setFont(F,8.5);c.drawString(x+2*mm,y+chh-5*mm,f"{P['id']}　{P['name']}")
    c.setFont(F,7.5);c.drawString(x+2*mm,y+11*mm,f"外形 {'×'.join(f'{d:g}' for d in P['bbox_sorted_mm'])} mm　数量 {P['qty']}")
    c.drawString(x+2*mm,y+7*mm,f"{P['material']}　{P['process']}"+('' if P['mass_g'] is None else f"　{P['mass_g']} g"))
    c.drawString(x+2*mm,y+3*mm,(P['note'] or '')[:34])
c.showPage();c.save();print('pages',page[0])
