"""Render docs/ZL80_ADF50_V02_评估与重新设计.md to PDF (reportlab, built-in CID font)."""
import re
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image
from reportlab.lib.styles import ParagraphStyle
D=Path(__file__).resolve().parent;pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'));F='STSong-Light'
S={k:ParagraphStyle(k,fontName=F,fontSize=fs,leading=ld,spaceBefore=sb,spaceAfter=4,leftIndent=li) for k,fs,ld,sb,li in
   (('h1',16,22,0,0),('h2',13,18,8,0),('h3',11,15,6,0),('p',9.5,14,0,0),('b',9.5,14,0,10),('c',8,10.5,0,0))}
def esc(t):
    t=str(t).replace('Ø','φ').replace('−','-').replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
    return re.sub(r'`(.+?)`',r'\1',re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',t))
out=[];L=(D/'ZL80_ADF50_V02_评估与重新设计.md').read_text().split('\n');i=0;W=180*mm
while i<len(L):
    l=L[i]
    if l.startswith('|'):
        rows=[]
        while i<len(L) and L[i].startswith('|'):
            c=[x.strip() for x in L[i].strip().strip('|').split('|')]
            if not all(re.fullmatch(r':?-+:?',x) for x in c):rows.append([Paragraph(esc(x),S['c']) for x in c])
            i+=1
        t=Table(rows,colWidths=[W/len(rows[0])]*len(rows[0]),repeatRows=1)
        t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),.4,colors.grey),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DDE6EE')),('VALIGN',(0,0),(-1,-1),'TOP')]))
        out+=[t,Spacer(1,4)];continue
    m=re.match(r'!\[.*?\]\((.+?)\)',l)
    if m:out.append(Image(str(D/m.group(1)),width=150*mm,height=150*mm*1584/1834*.76/.76*(760/1000)/(1584/1834)))
    elif l.startswith('### '):out.append(Paragraph(esc(l[4:]),S['h3']))
    elif l.startswith('## '):out.append(Paragraph(esc(l[3:]),S['h2']))
    elif l.startswith('# '):out.append(Paragraph(esc(l[2:]),S['h1']))
    elif re.match(r'^(- |\d+\. )',l):out.append(Paragraph(esc(l),S['b']))
    elif l.strip():out.append(Paragraph(esc(l),S['p']))
    i+=1
def foot(cv,doc):cv.setFont(F,7.5);cv.drawString(15*mm,8*mm,f'ZL80 ADF50 V0.2 2026-11-16｜初步设计，非制造放行｜第 {doc.page} 页')
SimpleDocTemplate(str(D/'ZL80_ADF50_V02_评估与重新设计.pdf'),pagesize=A4,leftMargin=15*mm,rightMargin=15*mm,topMargin=14*mm,bottomMargin=14*mm,title='ZL80 ADF50 V0.2').build(out,onFirstPage=foot,onLaterPages=foot)
