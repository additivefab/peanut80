"""ECR-G3-01 elevation (X horizontal, Z vertical, looking along -Y) of the right end of the exit upper roller, drawn from the
nominal coordinates of the G3 instance list and the ECR parts. Schematic; not CAD. 12 px per mm."""
from pathlib import Path
import fitz
E=Path(__file__).resolve().parents[1];k=12;X0,Z0=60,140
X=lambda x:(x-X0)*k;Z=lambda z:(Z0-z)*k
o=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {int((130-X0)*k)} {int((Z0-76)*k)}" font-family="PingFang SC,Microsoft YaHei,sans-serif" font-size="14"><rect width="100%" height="100%" fill="#fff"/>']
def r(x0,x1,z0,z1,f,s,lab=None,lx=None,lz=None,anchor='start',c=None):
    o.append(f'<rect x="{X(x0)}" y="{Z(z1)}" width="{(x1-x0)*k}" height="{(z1-z0)*k}" fill="{f}" stroke="{s}" stroke-width="1.4"/>')
    if lab:o.append(f'<text x="{X(lx if lx is not None else x0)}" y="{Z(lz if lz is not None else z1)-5}" fill="{c or s}" text-anchor="{anchor}">{lab}</text>')
r(66.4,67.9,108.1,132.1,'#dde','#889');r(68,76,111.1,129.1,'#e8eef4','#556','滑块 G3-M04',68,111.1,c='#556')
r(74.5,78.1,111.1,129.1,'#cfd8e3','#556','右压盖 G3-M06',74.5,129.1)
r(70,84,117.1,123.1,'#e9e9e9','#444')                        # shaft Ø6 (right end)
r(80.3,116.4,87.4,112.4,'#f2f2f2','#889','联轴器护罩',82,87.4,c='#889');r(101,147.5,82.3,117.5,'#f2f2f2','#889','驱动电机',103,82.3,c='#889')
r(80,88.2,115.6,124.6,'#fde3c4','#c60','磁铁载体 G3E-01',80,115.6,c='#c60')
r(85.7,88.2,117.1,123.1,'#f9b','#a05','磁铁 G3E-02',86,123.1,c='#a05')
r(89.2,90.2,117.9,122.3,'#ccf','#339');r(90.2,91.8,115.1,125.1,'#bfe3c8','#195','小板 G3E-03',90,115.1,c='#195')
r(78.1,91.8,130.2,131.7,'#fde3c4','#c60');r(78.1,79.6,124.6,131.7,'#fde3c4','#c60','支架 G3E-04',70,133.5,c='#c60')
r(90.2,91.8,125.1,131.7,'#fde3c4','#c60')
o.append(f'<line x1="{X(70)}" y1="{Z(120.1)}" x2="{X(100)}" y2="{Z(120.1)}" stroke="#c33" stroke-dasharray="6 4"/><text x="{X(92)}" y="{Z(120.1)-7}" fill="#c33">上辊轴线 Z=120.1</text>')
o.append(f'<line x1="{X(88.2)}" y1="{Z(112)}" x2="{X(89.2)}" y2="{Z(112)}" stroke="#333"/><text x="{X(84)}" y="{Z(112)+16}" fill="#333">气隙 1.0</text>')
o.append(f'<text x="{X(61)}" y="{Z(77.5)}" fill="#333">扫描仪右侧、出口上压辊（Y=+42）右端立面；颜色：橙=新增机械件，红紫=磁铁，绿=传感器小板，灰=G3 原件</text></svg>')
svg=E/'_sec.svg';svg.write_text('\n'.join(o),encoding='utf-8')
pm=fitz.open(str(svg))[0].get_pixmap(matrix=fitz.Matrix(1.4,1.4));pm.save(str(E/'ECR_G3_01_安装立面.png'));svg.unlink();print('section ok')
