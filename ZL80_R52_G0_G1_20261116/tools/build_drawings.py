from pathlib import Path
import math,json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A3,landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.colors import HexColor
R=Path(__file__).resolve().parents[1]
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
W,H=landscape(A3);MM=72/25.4
C=canvas.Canvas(str(R/'drawings/ZL80_G0_G1_接口与时序图册.pdf'),pagesize=(W,H))
navy='#173A55';teal='#087F8C';grey='#5D6A74';orange='#AD5F12';red='#BA3434'
def text(x,y,t,size=10,col=navy):
 C.setFillColor(HexColor(col));C.setFont('STSong-Light' if any(ord(z)>255 for z in t) else 'Helvetica',size);C.drawString(x*MM,y*MM,t)
def line(x1,y1,x2,y2,col=grey,width=.7,dash=None):
 C.setStrokeColor(HexColor(col));C.setLineWidth(width);C.setDash(dash or []);C.line(x1*MM,y1*MM,x2*MM,y2*MM);C.setDash([])
def rect(x,y,w,h,fill=None,col=grey):
 C.setStrokeColor(HexColor(col));C.setLineWidth(.7)
 if fill:C.setFillColor(HexColor(fill))
 C.rect(x*MM,y*MM,w*MM,h*MM,fill=bool(fill),stroke=1)
def arrow(x1,y1,x2,y2,col=teal,width=1):
 line(x1,y1,x2,y2,col,width);a=math.atan2(y2-y1,x2-x1);l=2
 for b in (-.45,.45):line(x2,y2,x2-l*math.cos(a+b),y2-l*math.sin(a+b),col,width)
def dim(x1,x2,y,label,col=navy):
 line(x1,y-2,x1,y+2,col);line(x2,y-2,x2,y+2,col)
 arrow(x1,y,x2,y,col,.6);arrow(x2,y,x1,y,col,.6)
 text((x1+x2)/2-len(label)*.7,y+3,label,10,col)
def page(code,title,scope):
 rect(8,8,404,281,None,navy);rect(8,267,404,22,navy,navy)
 text(15,276,code+'  '+title,21,'#FFFFFF');text(15,257,scope,11,grey)
 line(8,24,412,24,navy);text(15,15,'ZL80 / R52-G01-D01 / 2026-11-16',10)
 text(150,15,'名义接口 / 理想模型，非加工放行图；毫米单位；示意不按比例',10,orange)
def notes(x,y,lines):
 for t in lines:text(x,y,t,11);y-=8
# D01
page('D01','坐标系与四种宽度边界','G0 ICD-01 / 02 / 03 / 05 / 06  |  使用R5坐标，明确区分物理宽度、光学范围和同步点')
cx=145;s=2.1
rect(cx-40*s,117,80*s,103,'#EFF4F7')
text(91,225,'俯视：80 mm 胶片沿 +Y 连续前进',13)
line(cx-52*s,165,cx+52*s,165,red,2)
C.setFillColor(HexColor(red));C.circle((cx-14*s)*MM,165*MM,1.4*MM,fill=1,stroke=0)
arrow(cx-12*s,171,cx+25*s,171,red,1.2)
arrow(249,133,249,206,teal,1.2);text(253,200,'+Y 走片',11)
for x in [-46,46]:rect(cx+x*s-2,162,4,6,'#F8E8CB',orange)
text(30,156,'SOS 目标 X=-46',10,orange);text(205,156,'EOS 目标 X=+46',10,orange)
for w,y,label in [(80,104,'80 mm 有效成像'),(92,88,'92 mm 标称同步跨度'),(100,72,'100 mm 光学预留'),(104,56,'104 mm 实体狭缝')]:dim(cx-w*s/2,cx+w*s/2,y,label)
rect(278,51,124,186,'#F6F8FA')
notes(286,224,['局部右手坐标：','X：横向扫描，正向单扫。','Y：连续走片方向。','Z：垂直片面向上。','','局部原点 = 扫描线中心。','R5绝对坐标 = 局部 + (0,0,110)。','','参考区间：','图像：[-40,+40] mm','同步：[-46,+46] mm','预留：[-50,+50] mm','狭缝：[-52,+52] mm','','红色粗线是狭缝/扫线位置；','圆点才是瞬时曝光点。','不是整条线同时照明。'])
C.showPage()
# D02: real inlet rays, black box lens
page('D02','扫描头光路：真实入口几何 + 理想映射','G1 只提供名义多面镜反射与理想 f-theta 映射；真实镜头处方、主平面、像差尚未取得')
X=lambda x:210+x*1.18;Z=lambda z:64+z*.95
# incoming line
rect(X(-145),Z(129),50*1.18,12*.95,'#DDE7EF');text(X(-145),Z(147),'635 nm激光 / APC',11)
rect(X(-90),Z(127),16*1.18,16*.95,'#E2F0F0');text(X(-92),Z(116),'准直整形',10)
rect(X(-69),Z(126),14*1.18,18*.95,'#E2F0F0');text(X(-70),Z(110),'ND / 参考取光',10)
rect(X(-52),Z(123),18*1.18,24*.95,'#E6E9ED');text(X(-54),Z(153),'失电关闭快门',10)
arrow(X(-95),Z(135),X(0),Z(135),red,1.1)
# polygon outline local
c=20*math.cos(math.pi/6)/math.sqrt(2);pts=[(X(c+20*math.cos(math.radians(-165+60*i))),Z(135+c+20*math.sin(math.radians(-165+60*i)))) for i in range(6)]
for a,b in zip(pts,pts[1:]+pts[:1]):line(*a,*b,navy,1.2)
text(262,225,'反射式六面polygon',12);text(262,216,'中心反射点：(0,0,135)',10)
# reference box, not lens surfaces
rect(X(-55),Z(70),110*1.18,37*.95,'#E8F1F4',teal)
text(X(-49),Z(96),'f-theta镜组 / 处方待定',14)
text(X(-49),Z(86),'EFL=100 mm仅为预算参数',11)
text(X(-49),Z(76),'本区不绘制虚构透镜曲面或折射线',10,orange)
import sys
sys.path.insert(0,str(R/'src'));from scan_model import load_parameters,polygon_ray
p=load_parameters()
for xf in (-50,-40,0,40,50):
 q=polygon_ray(p,xf/200);line(X(q['hit_x_mm']),Z(q['hit_z_mm']),X(q['lens_reference_x_mm']),Z(107),red,.75)
 # dashed output maps, not asserted physical ray
 line(X(xf),Z(70),X(xf),Z(0),red,.7,[3,3])
line(X(-60),Z(0),X(60),Z(0),navy,1.2);text(X(-39),Z(-10),'名义胶片焦面 Z=0；实物焦面待标定',11)
text(24,103,'虚线：理想目标位置映射，非真实镜头光线。',10,orange)
notes(24,88,['镜头几何中心在局部Z=100；不是已确认工作距离。','输入镜面角±14.324 deg → 光学角±28.648 deg。','全幅光斑、远心性、遮挡和回反须由供应商模型关闭。'])
notes(308,193,['参考光路顺序：','激光 → 整形 → ND','→ 快门 → polygon','→ f-theta → 胶片','→ 狭缝积分筒','→ -Y侧窗 → PMMA','→ 单PMT','','积分筒不在片前；','PMT不在入射光路上。'])
C.showPage()
# D03
page('D03','G1 / G2 收光接口与扫描头安装基准','下游结构仅作接口保留；本图不是积分筒加工图，也不是新的PMT封装设计')
# YZ circular section
cy,cz,sc=174,151,2.0
C.setLineWidth(1);C.setStrokeColor(HexColor(navy));C.circle(cy*MM,cz*MM,26*sc*MM,fill=0)
C.circle(cy*MM,cz*MM,20*sc*MM,fill=0)
filmY=cz+26.9*sc
line(50,filmY,257,filmY,navy,1.2)
rect(cy-1.2,filmY-1.2,2.4,.6,None,red)
arrow(cy,238,cy,filmY,red,1.2);arrow(cy,filmY-2,cy,cz-38,red,1)
# side window negative y left
rect(cy-52-4,cz-10,8,20,'#E2F0F0',teal)
rect(cy-52-64,cz-5.2,64,10.4,'#E2F0F0',teal)
rect(cy-52-64-36,cz-15,36,30,'#DDE7EF',navy)
arrow(cy-47,cz,cy-117,cz,teal,1.2)
text(23,120,'单PMT',12);text(60,130,'PMMA导光件',11);text(88,110,'径向 -Y 侧窗',11)
text(175,238,'入射光 → 先透过胶片',12)
text(174,91,'Y-Z剖面；筒轴X垂直纸面',11)
arrow(230,83,260,83);text(261,81,'+Y',11);arrow(230,83,230,111);text(230,115,'+Z',11)
rect(279,62,123,176,'#F6F8FA')
notes(287,224,['继承的名义接口：','筒内径：40 mm','筒内腔长：120 mm（沿X）','狭缝：104 × 1.2 mm','薄唇：0.3 mm','片面与唇口间隙：需按实物复核','侧窗：8 × 10 mm','PMMA长：32 mm','出口：5.2 × 5.2 mm','','两端封闭，禁止改成端面出光。','PMT基线候选H10720-20；','H10721不是相同机械接口。','','G1检查扫线与狭缝不冲突；','收光效率/均匀性留给G2验证。'])
text(26,48,'扫描头CAD使用R5原位姿；旋转件/镜组/激光器是采购包络，不得据此加工。',11,orange)
C.showPage()
# D04
page('D04','扫描同步与有效成像窗：不可把两种窗口混为一谈','名义算例：6面 / 3000 rpm / EFL100 / 50 um / 连续ADC20 MSPS；时间从SOS定义为0')
x0=75;xscale=78 # mm/ms
T=lambda t:x0+t*xscale
for t in (0,.095493,1.368732,1.464225,3.333333):line(T(t),77,T(t),230,'#D7DFE4',.5,[2,2])
for t,lab in [(0,'SOS'),(1.464225,'EOS'),(3.333333,'下一SOS')]:text(T(t)-3,237,lab,11)
def wave(label,y,intervals,col):
 text(17,y+2,label,11);line(T(-.12),y,T(3.5),y,col,.5)
 for a,b in intervals:
  line(T(a),y,T(a),y+9,col,1);line(T(a),y+9,T(b),y+9,col,1);line(T(b),y+9,T(b),y,col,1)
wave('SOS',218,[(0,.025),(3.333,3.358)],teal)
wave('EOS',193,[(1.464225,1.489225)],teal)
wave('光学照明窗口',168,[(-.063662,1.527887),(3.269671,3.5)],orange)
wave('ROI_VALID',143,[(.095493,1.368732),(3.428826,3.5)],red)
text(17,117,'ADC_CLK',11)
for i in range(100):
 a=-.12+i*.036
 line(T(a),112,T(a),119,grey,.45);line(T(a),119,T(a+.018),119,grey,.45);line(T(a+.018),119,T(a+.018),112,grey,.45)
text(118,101,'连续时钟；图中脉冲间距仅示意，不按20 MHz真实比例',10,grey)
text(17,82,'数据与标签',11);arrow(T(0),78,T(3.45),78,navy)
text(97,69,'按“采样时刻”关联时间/面号/编码器；数字延迟同管线匹配，AFE群延迟另校准。',10)
rect(22,34,376,26,'#F6F8FA')
text(28,49,'300 行/s；ROI占空比38.20%；瞬时像素率1.2566 MHz；平均输出0.48 Mpixel/s。',12)
text(28,39,'每ROI期间仍走片19.10 um；不逐行停片；换面期间非成像，不画成反向有效扫描。',11,orange)
C.showPage();C.save()
print('4 drawing pages')
