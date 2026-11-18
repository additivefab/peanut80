"""Rebuild docs/ZL80_G5_FPGA同步与原始采集设计说明.docx and .pdf from the .md next to them.
Needs python-docx and reportlab. The md uses: # / ## / ### headings, '|' table rows (blank lines between rows are tolerated; first row is the header),
'- ' bullets, ``` code fences, plain paragraphs. Not a general Markdown converter."""
import re
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'docs';MD=next(D.glob('*设计说明.md'));OUT=MD.with_suffix('')
def parse(text):
    blocks=[];lines=text.splitlines();i=0
    while i<len(lines):
        l=lines[i]
        if l.startswith('```'):
            j=i+1;code=[]
            while j<len(lines) and not lines[j].startswith('```'):code.append(lines[j]);j+=1
            blocks.append(('code','\n'.join(code)));i=j+1;continue
        m=re.match(r'(#{1,3}) (.*)',l)
        if m:blocks.append(('h'+str(len(m.group(1))),m.group(2)));i+=1;continue
        if l.startswith('|'):
            rows=[]
            while i<len(lines) and (lines[i].startswith('|') or (not lines[i].strip() and i+1<len(lines) and lines[i+1].startswith('|'))):
                if lines[i].startswith('|'):
                    c=[x.strip() for x in lines[i].strip().strip('|').split('|')]
                    if not all(re.fullmatch(r'-+:?|:?-+:?',x) for x in c):rows.append(c)
                i+=1
            blocks.append(('table',rows));continue
        if l.startswith('- '):blocks.append(('li',l[2:]));i+=1;continue
        if l.strip():blocks.append(('p',l.strip()))
        i+=1
    return blocks
def plain(t):return re.sub(r'\*\*(.*?)\*\*',r'\1',t.replace('`',''))
def build_docx(blocks):
    from docx import Document
    from docx.shared import Pt,RGBColor
    from docx.oxml.ns import qn
    d=Document();st=d.styles
    for n in ('Normal','Heading 1','Heading 2','Heading 3','Title'):
        st[n].font.name='Noto Sans CJK SC';st[n].element.rPr.rFonts.set(qn('w:eastAsia'),'Noto Sans CJK SC')
    st['Normal'].font.size=Pt(10.5);st['Heading 1'].font.color.rgb=RGBColor(0x14,0x3C,0x61);st['Heading 2'].font.color.rgb=RGBColor(0x22,0x6D,0xA6)
    first=True
    for k,v in blocks:
        if k=='h1':
            d.add_heading(plain(v),0 if first else 1);first=False
        elif k=='h2':d.add_heading(plain(v),2)
        elif k=='h3':d.add_heading(plain(v),3)
        elif k=='p':d.add_paragraph(plain(v))
        elif k=='li':d.add_paragraph(plain(v),style='List Bullet')
        elif k=='code':
            p=d.add_paragraph();r=p.add_run(v);r.font.name='Menlo';r.font.size=Pt(9)
        elif k=='table':
            n=max(len(r) for r in v);t=d.add_table(rows=len(v),cols=n);t.style='Table Grid'
            for i,row in enumerate(v):
                for j in range(n):
                    c=t.cell(i,j);c.text=plain(row[j]) if j<len(row) else ''
                    for p in c.paragraphs:
                        for r in p.runs:
                            r.font.size=Pt(9);r.bold=(i==0)
            d.add_paragraph()
    d.core_properties.title='ZL80 G5 FPGA同步与原始采集设计说明';d.core_properties.author='ZL80 Engineering';d.core_properties.subject='R52-G5-HF-D02'
    d.save(str(OUT)+'.docx')
def build_pdf(blocks):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Table,TableStyle,Spacer,Preformatted
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from xml.sax.saxutils import escape
    pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'));F='STSong-Light'
    S=lambda n,**k:ParagraphStyle(n,fontName=F,**k)
    sty={'h1':S('h1',fontSize=17,leading=24,textColor=colors.HexColor('#143C61'),spaceBefore=14,spaceAfter=8),'h2':S('h2',fontSize=12.5,leading=18,textColor=colors.HexColor('#226DA6'),spaceBefore=10,spaceAfter=4),
         'h3':S('h3',fontSize=11,leading=16,textColor=colors.HexColor('#226DA6'),spaceBefore=8,spaceAfter=3),'p':S('p',fontSize=9.5,leading=15,spaceAfter=4),
         'li':S('li',fontSize=9.5,leading=15,leftIndent=12,bulletIndent=2,spaceAfter=2),'c':S('c',fontSize=8.2,leading=11.5),'code':ParagraphStyle('code',fontName='Courier',fontSize=8,leading=10)}
    x=lambda t:escape(plain(t))
    fl=[];firstH1=True
    for k,v in blocks:
        if k=='h1' and firstH1:fl.append(Paragraph(x(v),S('t',fontSize=24,leading=32,textColor=colors.HexColor('#143C61'),spaceAfter=10)));firstH1=False
        elif k in('h1','h2','h3','p'):fl.append(Paragraph(x(v),sty[k]))
        elif k=='li':fl.append(Paragraph(x(v),sty['li'],bulletText='•'))
        elif k=='code':fl.append(Preformatted(v,sty['code']));fl.append(Spacer(1,4))
        elif k=='table':
            n=max(len(r) for r in v);data=[[Paragraph(x(r[j]) if j<len(r) else '',sty['c']) for j in range(n)] for r in v];w=(A4[0]-36*mm)/n
            t=Table(data,colWidths=[w]*n,repeatRows=1);t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#9FB0C0')),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E5EDF5')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),3),('RIGHTPADDING',(0,0),(-1,-1),3)]))
            fl+= [t,Spacer(1,6)]
    def foot(c,d):c.setFont(F,8);c.setFillColor(colors.HexColor('#5E7180'));c.drawString(18*mm,10*mm,'ZL80 R5.2 · G5-HF · R52-G5-HF-D02');c.drawRightString(A4[0]-18*mm,10*mm,str(d.page))
    SimpleDocTemplate(str(OUT)+'.pdf',pagesize=A4,leftMargin=18*mm,rightMargin=18*mm,topMargin=16*mm,bottomMargin=18*mm,title='ZL80 G5 FPGA同步与原始采集设计说明',author='ZL80 Engineering',subject='R52-G5-HF-D02').build(fl,onFirstPage=foot,onLaterPages=foot)
if __name__=='__main__':
    b=parse(MD.read_text());build_docx(b);build_pdf(b);print(len(b),'blocks',OUT.name)
