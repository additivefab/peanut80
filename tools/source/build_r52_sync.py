"""R5.2 synchronisation of derived documents (run after engineering/calculate.py and the collector checks):
  1. adds/refreshes R5.2 sheets in engineering/ZL80_R5_参数选型BOM与空间预算.xlsx (R5-PDR1 sheets untouched,
     gate sheet extended with G15-G21);
  2. writes drawings/ZL80_R52_补充图册.pdf (supplement; the R5-PDR1 atlases are not regenerated);
  3. renders docs/ZL80_R52_融合评估与设计基线.md to PDF.
Needs openpyxl and reportlab. Set ZL80_PDF_FONT to an embeddable CJK TrueType font
for readers without Adobe-GB1 font resources. --baseline-pdf-only refreshes just the baseline."""
import json,csv,os,re,sys
from pathlib import Path
import openpyxl
from openpyxl.styles import Font,PatternFill,Alignment
from reportlab.lib.pagesizes import A4,landscape
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Flowable
from reportlab.lib.styles import ParagraphStyle
R=Path(__file__).resolve().parents[2]
P=json.loads((R/'engineering/parameters.json').read_text());C=json.loads((R/'engineering/calculated_results.json').read_text())
g=P['collector_guide_r52'];sc=C['signal_chain_review']
ovA=json.loads((R/'tests/cad_overlap_R52_A.json').read_text());ovB=json.loads((R/'tests/cad_overlap_R52_B.json').read_text())
rd=lambda f:list(csv.reader(open(R/f,encoding='utf-8-sig')))
gates=rd('engineering/设计冻结门槛.csv');dec=rd('engineering/设计决策与版本差异.csv');mc=rd('engineering/导光件方案对比_蒙特卡洛.csv')
delta=json.loads((R/'cad/instances_R52_delta.json').read_text())
budget=[['方案','面数','PMT增益','行平均','走片 mm/s','扫1米 分钟','片面功率 µW','D0.5','D2.0','D3.5','D4.0','D4.5','达标最高D']]
for v in sc['variants']:
    row=[v['id'],v['facets'],v['pmt_gain'],v['line_average'],round(v['feed_mm_s'],3),round(v['seconds_per_metre']/60,1),round(v['film_power_w']*1e6,1)]
    row+=['饱和' if x['saturated'] else round(x['sigma_D_total'],4) for x in v['per_od']]+[v['max_od_meeting_target']]
    budget.append(row)
guide=[['项目','取值','说明']]+[[k,json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v,''] for k,v in g.items()]
inter=[['情况','核心装配实例','核心干涉数','G3零件数','与G3干涉数'],['A 只平移',ovA['core_instances'],len(ovA['core_overlaps']),ovA['g3_parts_checked'],len(ovA['overlaps_vs_g3'])],
       ['B 含布局修正',ovB['core_instances'],len(ovB['core_overlaps']),ovB['g3_parts_checked'],len(ovB['overlaps_vs_g3'])],[],['情况A干涉对','','体积 mm3']]
inter+=[[o['a'],o['b'],o['volume_mm3']] for o in ovA['core_overlaps']]+[[],['情况B名义间隙','','mm']]+[[c['a'],c['b'],c['min_distance_mm']] for c in ovB['clearances']]
inter+=[[],['变动零件','变动','包络 xmin,ymin,zmin,xmax,ymax,zmax']]+[[d['name'],d['change'],str(d.get('aabb',''))] for d in delta]
changes=[['编号','动作','决定','理由']]+[r for r in dec if r and r[0].startswith('R52')]
# ---------- 1. workbook
xl=R/'engineering/ZL80_R5_参数选型BOM与空间预算.xlsx';wb=openpyxl.load_workbook(xl)
def sheet(name,rows,title):
    if name in wb.sheetnames:del wb[name]
    ws=wb.create_sheet(name);ws.append([title]);ws['A1'].font=Font(bold=True,size=12);ws.append([])
    for r in rows:ws.append([x if isinstance(x,(int,float,str)) or x is None else str(x) for x in r])
    for c in ws[3]:c.font=Font(bold=True);c.fill=PatternFill('solid',fgColor='DDE6EE')
    for col in ws.columns:
        w=max((len(str(c.value)) for c in col if c.value is not None),default=8);ws.column_dimensions[col[0].column_letter].width=min(60,max(10,w*1.6))
    for row in ws.iter_rows(min_row=3):
        for c in row:c.alignment=Alignment(wrap_text=True,vertical='top')
    return ws
note='R5.2 2026-11-16｜由 tools/source/build_r52_sync.py 从 JSON/CSV 生成的数值副本，不含公式；R5-PDR1 原工作表未改'
sheet('R52变更',changes,'R5.2 设计决策｜'+note)
sheet('R52光电预算',budget,'R5.2 光电预算（单像素密度噪声，目标0.02，噪声底限0.005）｜'+note)
sheet('R52导光件',guide,'R5.2 梯形PMMA导光板 C06-R52｜'+note)
sheet('R52导光对比',mc,'导光件蒙特卡洛筛选（非实测）｜'+note)
sheet('R52干涉',inter,'R5.2 收光改动整机名义干涉复核｜'+note)
ws=wb['冻结门槛'];have={str(r[0].value) for r in ws.iter_rows(min_row=1) if r[0].value}
for r in gates:
    if r and r[0] not in have and re.match(r'G\d+',r[0]):ws.append(r)
if '--baseline-pdf-only' not in sys.argv:
    wb.save(xl)
# ---------- 2/3. PDFs
font_path = os.environ.get('ZL80_PDF_FONT')
if font_path:
    F = 'ZL80-CJK'
    pdfmetrics.registerFont(TTFont(F, font_path))
    pdfmetrics.registerFontFamily(F, normal=F, bold=F, italic=F, boldItalic=F)
else:
    F = 'STSong-Light'
    pdfmetrics.registerFont(UnicodeCIDFont(F))
ST=dict(h1=ParagraphStyle('h1',fontName=F,fontSize=16,leading=22,spaceAfter=6),h2=ParagraphStyle('h2',fontName=F,fontSize=13,leading=18,spaceBefore=8,spaceAfter=4),
        h3=ParagraphStyle('h3',fontName=F,fontSize=11,leading=15,spaceBefore=6,spaceAfter=3),p=ParagraphStyle('p',fontName=F,fontSize=9.5,leading=14,spaceAfter=4),
        c=ParagraphStyle('c',fontName=F,fontSize=8,leading=10.5),b=ParagraphStyle('b',fontName=F,fontSize=9.5,leading=14,leftIndent=10,spaceAfter=2))
for key in ('h1', 'h2', 'h3'):
    ST[key].keepWithNext = True
for key in ('p', 'c', 'b'):
    ST[key].wordWrap = 'CJK'
def esc(t):
    t=str(t).replace('Ø','φ').replace('−','-').replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
    t=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',t);t=re.sub(r'`(.+?)`',r'\1',t);return re.sub(r'\[(.+?)\]\((.+?)\)',r'\1',t)
def table(rows,widths=None,width=None):
    n=max(len(r) for r in rows);data=[[Paragraph(esc(x if x is not None else ''),ST['c']) for x in list(r)+['']*(n-len(r))] for r in rows]
    if widths is None and width:widths=[width/n]*n
    t=Table(data,colWidths=widths,repeatRows=1)
    t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.4,colors.grey),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DDE6EE')),('VALIGN',(0,0),(-1,-1),'TOP')]));return t
def md_to_story(text,width):
    out=[];lines=text.split('\n');i=0
    column_fractions = {'对象': (0.18, 0.39, 0.43), '接口': (0.25, 0.75), '复核项': (0.22, 0.78)}
    while i<len(lines):
        l=lines[i]
        if l.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].startswith('|'):
                cells=[c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?',c) for c in cells):rows.append(cells)
                i+=1
            fractions = column_fractions.get(rows[0][0])
            widths = [width * fraction for fraction in fractions] if fractions else None
            out+=[table(rows,widths=widths,width=width),Spacer(1,4)];continue
        if l.startswith('### '):out.append(Paragraph(esc(l[4:]),ST['h3']))
        elif l.startswith('## '):out.append(Paragraph(esc(l[3:]),ST['h2']))
        elif l.startswith('# '):out.append(Paragraph(esc(l[2:]),ST['h1']))
        elif re.match(r'^(- |\d+\. )',l):out.append(Paragraph(esc(l),ST['b']))
        elif l.strip():out.append(Paragraph(esc(l.lstrip('> ')),ST['p']))
        i+=1
    return out
foot=lambda label:(lambda cv,doc:(cv.setFont(F,7.5),cv.drawString(15*mm,8*mm,f'{label}｜非加工/投板放行｜第 {doc.page} 页')))
md=(R/'docs/ZL80_R52_融合评估与设计基线.md').read_text()
d=SimpleDocTemplate(str(R/'docs/ZL80_R52_融合评估与设计基线.pdf'),pagesize=A4,leftMargin=15*mm,rightMargin=15*mm,topMargin=14*mm,bottomMargin=14*mm,title='ZL80 R5.2 融合评估与设计基线')
date=json.loads((R/'release_status.json').read_text())['r52_update']['date']
f=foot(f'ZL80 R5.2 融合评估与设计基线 {date}');d.build(md_to_story(md,180*mm),onFirstPage=f,onLaterPages=f)
if '--baseline-pdf-only' in sys.argv:
    sys.exit(0)
class Drawing(Flowable):
    """Vector views: guide plate plan (1:1) and collector side section (1:1)."""
    def __init__(s,kind):s.kind=kind;s.width=250*mm;s.height=(70 if kind=='plan' else 95)*mm
    def draw(s):
        cv=s.canv;cv.setFont(F,8);cv.setLineWidth(0.7)
        w0,w1,t,L,y0=g['input_width_x'],g['output_width_x'],g['thickness_z'],g['length_y'],g['input_face_y']
        if s.kind=='plan':
            ox,oy=80*mm,58*mm;X=lambda x:ox+x*mm;Y=lambda y:oy+(y-y0)*mm   # 1:1, X right, -Y down
            p=cv.beginPath();p.moveTo(X(-w0/2),Y(y0));p.lineTo(X(w0/2),Y(y0));p.lineTo(X(w1/2),Y(y0-L));p.lineTo(X(-w1/2),Y(y0-L));p.close()
            cv.setFillColor(colors.HexColor('#CFEAF2'));cv.drawPath(p,fill=1);cv.setFillColor(colors.black)
            cv.circle(X(0),Y(g['pmt_window_y']),4*mm);cv.drawString(X(8),Y(y0-L)-2*mm,f'PMT 有效面 φ8，窗面 Y={g["pmt_window_y"]}；硅胶垫 {g["output_pad_mm"]}')
            cv.line(X(-w0/2),Y(y0)+4*mm,X(w0/2),Y(y0)+4*mm);cv.drawCentredString(X(0),Y(y0)+5.5*mm,f'入口 {w0:g}（沿扫描方向 X），与筒内壁齐平 Y={y0}')
            cv.line(X(w0/2)+6*mm,Y(y0),X(w0/2)+6*mm,Y(y0-L));cv.drawString(X(w0/2)+8*mm,Y(y0-L/2),f'长 {L:g}')
            cv.drawString(X(w0/2)+8*mm,Y(y0-L/2)-5*mm,f'出口 {w1:g}×{t:g}；板厚 {t:g}')
            cv.drawString(X(w0/2)+8*mm,Y(y0-L/2)-10*mm,'六面光学抛光；棱边倒角≤0.1')
            cv.drawString(X(-w0/2),Y(y0-L)-8*mm,'俯视 1:1（单位 mm）｜C06-R52｜光学级浇铸PMMA，加工后退火')
        else:
            oy0,oz0=205*mm,-55*mm;Yc=lambda y:oy0+y*mm;Z=lambda z:oz0+z*mm;zc=P['cavity_center_z']   # side view: -Y to the left
            cv.circle(Yc(0),Z(zc),20*mm);cv.circle(Yc(0),Z(zc),23.4*mm);cv.circle(Yc(0),Z(zc),26*mm)
            cv.setFillColor(colors.HexColor('#CFEAF2'));cv.rect(Yc(y0-L),Z(zc-t/2),L*mm,t*mm,fill=1);cv.setFillColor(colors.black)
            for d_ in delta:
                a=d_.get('aabb')
                if a and d_['name'] in ('PMT','Analog_shield','PMT线性TIA前端卡','Guide_shroud_R52'):
                    cv.setDash(2,2) if d_['name']=='Analog_shield' else cv.setDash();cv.rect(Yc(a[1]),Z(a[2]),(a[4]-a[1])*mm,(a[5]-a[2])*mm)
                    cv.setDash();cv.drawString(Yc(a[1])+1*mm,Z(a[2])-3.5*mm,{'PMT':'PMT','Analog_shield':'屏蔽罩 H01','PMT线性TIA前端卡':'B01','Guide_shroud_R52':'遮光罩'}[d_['name']])
            cv.circle(Yc(-42),Z(99.9),10*mm);cv.drawString(Yc(-52),Z(112),'入口下辊 φ20');cv.rect(Yc(-115),Z(98),10*mm,8*mm);cv.drawString(Yc(-128),Z(108),'入片传感器 S03')
            cv.setDash(6,3);cv.line(Yc(-150),Z(110),Yc(40),Z(110));cv.setDash();cv.drawString(Yc(20),Z(111.5),'片面 Z=110')
            cv.drawString(Yc(-150),Z(40),f'侧视 1:1（-Y 向左）｜导光板 Z={zc-t/2:g}–{zc+t/2:g}｜筒内径40/内胆46.8/筒壳52｜PMT 较 R5 后移 {abs(g["pmt_shift_y_vs_r5"])} mm')
story=[Paragraph('ZL80 R5.2 补充图册',ST['h1']),Paragraph('2026-11-16｜对 R5-PDR1 图册的补充，不替换原 105 页图册。原图册中 D08（积分筒）、C06/C07/C08、P03、B01、H01 的位置和导光件尺寸以本补充为准；其余页面仍为 R5-PDR1。全部为名义几何与计算，非加工图。',ST['p']),
  Paragraph('S1 设计决策',ST['h2']),table(changes,[18*mm,16*mm,110*mm,120*mm]),PageBreak(),
  Paragraph('S2 梯形 PMMA 导光板 C06-R52',ST['h2']),Drawing('plan'),PageBreak(),Paragraph('S3 收光模块侧视',ST['h2']),Drawing('side'),PageBreak(),
  Paragraph('S4 导光件方案对比（蒙特卡洛筛选，非实测）',ST['h2']),table(mc,[86*mm,22*mm,20*mm,20*mm,20*mm,20*mm,22*mm,22*mm,34*mm]),
  Paragraph('S5 整机名义干涉复核',ST['h2']),table([r for r in inter if r],[90*mm,90*mm,84*mm]),PageBreak(),
  Paragraph('S6 光电预算',ST['h2']),table(budget,[78*mm]+[15.5*mm]*12),Paragraph(sc['note'],ST['p']),
  Paragraph('S7 冻结门槛 G15–G21',ST['h2']),table([gates[0]]+[r for r in gates if r and r[0] in ('G15','G16','G17','G18','G19','G20','G21')],[12*mm,34*mm,34*mm,130*mm,54*mm])]
d=SimpleDocTemplate(str(R/'drawings/ZL80_R52_补充图册.pdf'),pagesize=landscape(A4),leftMargin=15*mm,rightMargin=15*mm,topMargin=12*mm,bottomMargin=14*mm,title='ZL80 R5.2 补充图册')
f=foot('ZL80 R5.2 补充图册 2026-11-16');d.build(story,onFirstPage=f,onLaterPages=f)
print('workbook sheets',wb.sheetnames)
