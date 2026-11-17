from pathlib import Path
import html,base64,cairosvg,fitz,json
R=Path(__file__).resolve().parents[2];D=R/'drawings';TMP=R/'.build/render'
NAVY='#143c61';BLUE='#226da6';LIGHT='#edf4f8';INK='#172d3f';GRAY='#5e7180';RED='#cb462e';GREEN='#20826c';AMBER='#a75f12'
s=Path(__file__).with_name('render_design.py').read_text();exec(s[s.index('class Page:'):s.index('pages=[]')])
q=Page('D08','积分筒横剖面与真实侧向接口','Y-Z剖面按名义尺寸比例绘制，X垂直图面。红线是顺序飞点透射后的示意反射路径，不是光线追迹结果。')
# physical scales, datum center Y=0/Z=83.1 at page(800,600), 8 px/mm
q.circle(800,600,208,'#dee7ed',BLUE,3);q.circle(800,600,187.2,'#fafaf1',GRAY,2);q.circle(800,600,160,'white',BLUE,2)
# film / top slit gap
q.line(520,384.8,1015,384.8,GRAY,5);q.rect(744,389.6,112,2.4,'#586b79',GRAY,1);q.rect(795.2,389,9.6,29,'white','white')
q.text(510,330,'胶片中心 Z=110；薄唇顶 Z=109.4',22,BLUE,True);q.text(510,360,'片厚0.2时，片下表面至薄唇0.5',20)
# guide is confined to side port, never starts inside cavity center
q.poly([(612.8,560),(356.8,579.2),(356.8,620.8),(612.8,640)],'#d7f0f6',BLUE,2)
q.rect(578,557,20,86,'#dee7ed',BLUE,2);q.rect(599,561,20,78,'#d7f0f6',0)
# PMT body, window, pins, vertical board
q.rect(197.6,500,144,200,'#434f5b',BLUE,2);q.rect(341.6,560,12,80,'#cfe5ef',BLUE,2)
q.rect(65.6,464.8,12.8,400,'#69a28c',GREEN,2)
for y in (539.04,660.96):q.line(101.6,y,197.6,y,'#9a8044',5);q.rect(78.4,y-10,48,20,'#c3ab6b',GRAY,1)
q.text(50,910,'B01板面Y=−91',19,GREEN,True);q.text(197,755,'PMT本体18深×25高',19,BLUE,True);q.text(197,789,'光窗与导光端间隙0.4',19)
q.text(360,705,'锥形PMMA：L32',20,BLUE,True);q.text(360,738,'入口8×10，出口5.2方',19)
for a,b in [((800,383),(800,759)),((800,759),(950,545)),((950,545),(700,475)),((700,475),(640,600)),((612,600),(358,600))]:q.line(*a,*b,RED,3,arrow=True)
q.text(710,870,'首落点轨迹必须连续均匀',20,BLUE,True)
q.table(1050,205,500,['约束','设计与待验证项'],[['方向','筒轴X；侧窗朝−Y'],['输出','经导光件直接耦合PMT'],['收光口','不得轴向穿过封闭端盖'],['PMT光窗','φ10窗口，φ8有效面'],['装配状态','尺寸源于S01；引脚镜像复核'],['均匀性','位置与角度扫描验证'],['高反射点','作为亮线风险，禁止刻意加入']],[.3,.7],83,18)
q.text(80,1005,'图中没有把导光件伸到筒中心；PMT、光窗、导光件与侧窗依次相接。遮光套/盖板在此剖面中省略。',19,RED);q.save()
# Fix conceptual optical chain end so PMT is actually linked to guide.
f=D/'svg/D06.svg';txt=f.read_text();txt=txt.replace('x1="445" y1="690" x2="330"','x1="445" y1="690" x2="440"')
# Replace the guide/PMT tail by regenerating from original general functions keeps source coherent.
if '<rect x="130" y="640"' in txt:
    start=txt.index('<rect x="130" y="640"');end=txt.index('<text x="1000" y="200"',start)
    tail=Page('tmp','tmp');tail.s=[];tail.box(245,640,190,110,'PMMA导光','侧窗8×10 → 5.2方');tail.line(245,690,200,690,BLUE,5,arrow=True);tail.box(45,640,150,110,'单PMT','先透片后收光')
    txt=txt[:start]+'\n'.join(tail.s)+'\n'+txt[end:];f.write_text(txt);cairosvg.svg2png(bytestring=txt.encode(),write_to=str(D/'png/D06.png'),output_width=1920,output_height=1357);cairosvg.svg2pdf(bytestring=txt.encode(),write_to=str(TMP/'D06.pdf'))
reg=json.loads((D/'drawing_register.json').read_text())
for name,seq in [('ZL80_R5_系统与PCB图册',reg[:32]),('ZL80_R5_零件名义几何图册',reg[32:]),('ZL80_R5_完整图册',reg)]:
 out=fitz.open()
 for p in seq:
  s=fitz.open(TMP/f'{p["id"]}.pdf');out.insert_pdf(s);s.close()
 out.save(D/(name+'.pdf'));out.close()
print('corrected D06/D08, merged atlases')
