"""Generate traceable, review-stage G3 reports from actual registers and check results."""
from pathlib import Path
import json,csv,html
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image,KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.colors import HexColor,white
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
R=Path(__file__).resolve().parents[1]; reg=json.loads((R/'engineering/registers.json').read_text());p=reg['params'];sm=reg['summary'];audit=json.loads((R/'validation/results/geometry_audit.json').read_text());motion=json.loads((R/'validation/results/release_position_audit.json').read_text())
font=Path('/usr/share/fonts/truetype/arphic/uming.ttc')
if not font.exists():raise RuntimeError('CJK report font unavailable; install a local CJK font. Never bundle fonts into deliverables.')
pdfmetrics.registerFont(TTFont('CJK',str(font)))
NAVY='#183B56';TEAL='#117C83';LIGHT='#EDF4F7';ORANGE='#A7511C'
style=ParagraphStyle('body',fontName='CJK',fontSize=10.5,leading=16.3,spaceAfter=8,wordWrap='CJK',textColor=HexColor('#243C4A'))
small=ParagraphStyle('small',parent=style,fontSize=8.6,leading=12,spaceAfter=0)
head=ParagraphStyle('head',parent=style,fontSize=18,leading=25,spaceAfter=15,textColor=HexColor(NAVY))
sub=ParagraphStyle('sub',parent=style,fontSize=12.5,leading=18,spaceBefore=10,spaceAfter=6,textColor=HexColor(TEAL))
cap=ParagraphStyle('cap',parent=small,textColor=HexColor(ORANGE),spaceAfter=10)
W=499
md=[]
def para(t,sty=style):return Paragraph(html.escape(str(t)).replace('\n','<br/>'),sty)
def P(t):md.append(t+'\n');return para(t)
def H(t):md.append('## '+t+'\n');return para(t,head)
def S(t):md.append('### '+t+'\n');return para(t,sub)
def tab(headers,rows,widths=None,fs=8.6):
 data=[[para(h,ParagraphStyle('th',parent=small,textColor=white,fontSize=fs)) for h in headers]]+[[para(x,ParagraphStyle('td',parent=small,fontSize=fs)) for x in row] for row in rows]
 t=Table(data,colWidths=widths or [W/len(headers)]*len(headers),repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),HexColor(NAVY)),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('ROWBACKGROUNDS',(0,1),(-1,-1),[white,HexColor(LIGHT)]),('LINEBELOW',(0,0),(-1,0),.5,HexColor(TEAL))]))
 md.append('| '+' | '.join(map(str,headers))+' |\n|'+'---|'*len(headers)+'\n'+'\n'.join('| '+' | '.join(map(str,r))+' |' for r in rows)+'\n')
 return t
def figure(rel,width=499,maxh=250):
 from PIL import Image as PI
 q=R/rel;im=PI.open(q);w,h=im.size;sc=min(width/w,maxh/h);return Image(str(q),width=w*sc,height=h*sc,hAlign='CENTER')
def footer(c,d):
 c.saveState();c.setFillColor(HexColor(NAVY));c.rect(0,814,A4[0],28,fill=1,stroke=0);c.setFont('CJK',9);c.setFillColor(white);c.drawString(47,824,'ZL80  /  R52-G3-M01-D01  /  四辊输送与机械集成')
 c.setFillColor(HexColor('#647C8D'));c.setFont('CJK',8);c.drawString(47,27,'2026-11-16  |  设计审查稿，非制造放行；所有台架实测为 NOT_RUN');c.drawRightString(548,27,str(d.page));c.restoreState()
def build(name,story):
 SimpleDocTemplate(str(R/'docs'/f'{name}.pdf'),pagesize=A4,rightMargin=48,leftMargin=48,topMargin=48,bottomMargin=47).build(story,onFirstPage=footer,onLaterPages=footer)
 (R/'docs'/f'{name}.md').write_text('# '+name+'\n\n'+'\n'.join(md),encoding='utf-8');md.clear()

story=[]
def page(title,items):
 if story:story.append(PageBreak())
 story.append(H(title));story.extend(items)
page('G3 交付总览与状态',[
 P('本轮在G0/G1扫描接口和R5.1机械坐标基础上，深化四辊输送、轴系、提辊、机箱及板卡空间。这里的G3指机械输送工作包；不替代G2-E01的电路闭合。交付状态为 DESIGN_REVIEW_NOT_FOR_PRODUCTION。'),
 figure('drawings/png/01_FourRoller_Assembly.png',maxh=245),
 tab(['用户交付项','实际文件'],[
 ['完整四辊STEP','闭合、抬升5mm、爆炸三种总成；并附光机电上下文'],['采购与制造图','12项选型；23页图册；辊芯尺寸与工艺；基座及六平板DXF'],['材料与公差','18组×3重复材料DOE；17项关键公差；5项片底间隙链'],['线束与验证','12条中心线路线；14项台架协议；计算模型、空白数据、分析程序']], [120,379]),
 P('本包不是实机验收报告。新结构、采购包络、继承接口和未知细节分别标识；原厂孔位未确认的编码器底座、部分紧固件及提辊锁定件仍未冻结。')])
page('01 继承接口与变更控制',[
 tab(['接口','G3基线','来源／边界'],[
 ['X / Y / Z','横扫及辊轴 / 连续进片 / 向上','沿用R5统一坐标'],['胶片','80mm宽；厚0.2mm名义','0.15~0.35mm是试验范围'],['扫描线','X[-40,+40]，Y0，Z110名义','100mm光学预留不是100mm片道'],['辊系','Ø20×100；Y±42；轴承X±72','两辊距84；8只6×12×4轴承'],['片底与薄唇','Z109.9 / Z109.4，净距0.5','依赖局部片底支承；不能挡住通光'],['机箱','320×300×300名义','不含外置卷架、托板和脚垫']], [100,195,204]),
 S('本轮必须审批的变更'),
 P('基座由300×280×6改为300×288×6，保留电路板坐标，解决B04后排安装孔Y139靠近旧边缘的问题。四个脚位改为X±132、Y±120，避开B03安装孔。不能混用旧底板DXF。'),
 P('联轴器由旧16mm长占位改为NBK候选总长30mm；电机前安装面改到X121.5。侧框由6mm改8mm，并添加轴承台阶孔、浮动槽、弹簧调节井及释放通道。详见CR01~CR11。'),
 P('G2的新器件空间STEP另放sources/G2_reference，仅作对照。本次主总装沿用R5板框位姿。G2与R5的XZ板法向/元件面必须先做坐标转换核对，不能宣称所有新PCB元件均已清空。')])
page('02 四辊机构与装配策略',[
 P('当前采用入口测量随动下辊、出口主动牵引下辊，分别配编码器；两只上辊弹性压紧。只有一个走片执行电机，不是双电机张力伺服。外置放收卷负责低张力供给；扫描计量不能直接采用卷轴转速。'),
 tab(['组件','具体实现','仍需关闭'],[
 ['入口下辊','G3-R01轴总长189；左端接编码器','有效滚径、滑移和周期误差实测'],['出口下辊','G3-R02轴总长196；右端接5/6联轴器','低速转矩纹波、驱动电流及温升'],['上辊×2','G3-R03轴总长168；浮动块与M5锁定','锁紧方式、预载和释放操作评审'],['轴承×8','左端定位、右端游动；外圈压盖','样品配合、游隙、启动阻力'],['胶层','粘结/硫化后整辊磨削，Ø20成品','附着、迁移、掉屑、划伤DOE'],['释放','两端同步提辊，名义行程5mm','停驱动/禁光互锁、锁定件及人体操作']], [85,220,194]),
 S('轴系尺寸不是一根直径6mm通轴'),
 P('工作芯Ø14×100，两侧Ø7.4肩段、Ø6轴承位与不同轴端分开定义。左右轴承中心距144mm。左下辊夹紧轴环移动到X=-83.6，窄垫套伸至轴承端面；避免与轴承压盖和编码器安装板冲突。'),
 P('上辊采用较小M5螺母和窄垫片，不再在上下20.2mm轴距内叠放两个带约20.8mm螺钉扫掠包络的轴环。CAD表示螺纹名义包络而非真实牙型。')])
page('03 电机、轴承与联轴器选型',[
 tab(['用途','候选与核验结果','选择边界'],[
 ['牵引电机','14HS10-0404S；0.4A；保持0.14Nm；35级×26长；5轴长20.5 [S01]','需动态曲线及低速台架；限流驱动，不把12V铭牌等同24V直连'],['轴承','NMB L-1260ZZ；6×12×4；Cr831N/C0r363N [S02]','不能仅凭MR126族名替代；精度、润滑及启动摩擦另审'],['联轴器','MJC-20CS-WH-5-6；OD20、总长W30、静刚度29Nm/rad [S03]','L10是端毂长，不是总长；允许偏差不等于装调目标'],['编码器','AMT112S，6mm套；5V CMOS；4096PPR为配置值 [S04]','0.2°角精度不满足5μm宣称；原厂安装孔仍须确认'],['轴环','Ruland MCL-6-A；6孔、OD16、宽9；螺钉扫掠20.8 [S05]','安装轴端按厂家公差与夹紧转矩复核']], [70,220,209],8.6),
 S('供应商文件优先级'),
 P('原厂具体料号图纸、样品与检验记录优先于通用CAD模型。NMB日文原厂页与美国页面的倒角字段存在转录差异，本轮取日文页0.15mm作审查依据，并保留供应商确认项。AMT机械图的精确孔位未完成视觉核验，因此自定义适配板孔不能冒充原厂孔。'),
 P('完整12项选型表包含弹簧、胶料、基座、接触材料和未冻结的外置张力附件。无报价的项目保持RFQ，不写成0元，也不宣称现货。')])
page('04 夹紧力、牵引力和动态裕量',[
 P('必须把三个量分开：上辊法向夹紧力N、辊面可传递切向力μN、胶片纵向张力T。调压螺钉改变第一项，不能据此宣称第三项被闭环控制。'),
 tab(['计算项','本版结果','前提'],[
 ['双弹簧合力','4.100 N/组','2×0.5N/mm×(18−13.9)mm'],['上运动件自重','1.961 N/组','0.2kg是假设，须称重'],['总法向力估算','6.061 N/组','尚未含滑块摩擦及胶层压陷'],['摩擦牵引极限','1.818 N','μ=0.3假设'],['设计拉力/裕量','1.2 N / 1.515倍','目标2倍尚未满足'],['需2倍裕量时','8.0 N法向力','不允许未经划伤验证直接加压'],['转矩预算','0.015025Nm；系数3后0.045075Nm','外部阻力0.003Nm、惯量等假设']], [135,130,234]),
 P('上辊释放5mm时，弹簧工作长度由13.9变为8.9mm；采购压并长度要求不超过7.5mm仍需厂家确认。弹簧在STEP中是包络圆环，不是可计算疲劳与屈曲的实体弹簧。'),
 P('保持转矩与所需转矩约3.11倍只作初筛。步进电机低速微步非线性、槽转矩、驱动限流、联轴器扭转及真实滚阻共同决定实际输送；通过台架后再决定是否换低纹波闭环驱动。')])
page('05 零件工艺与装配公差',[
 P('物理基准A为基座上表面；B/C为主框圆销与菱形销定位特征。片面F=Z110是名义功能平面，不是可直接加工的基准面。每框一圆销一菱形销，避免两个圆销过约束强装。'),
 tab(['对象','候选要求','检验与限制'],[
 ['基座','300×288×6，6061-T6；A平面0.05，局部0.02mm','先消除加工应力，坐标测量；强度/热漂移未验证'],['轴承轴颈','Ø6.000~6.004mm候选；Ra≤0.4μm','先核准轴承配合和装配力，不能批量强压'],['外圈座','Ø12.000~12.010mm候选','左端隙0.02~0.05；右浮动0.20~0.50待样品审'],['编码器/联轴器端','Ø5.988~6.000mm','夹紧区无涂层，满足两供应商实际公差'],['成品胶辊','Ø20±0.010；轴承基准总跳动≤0.010mm候选','加载有效径另标定；几何尺寸不代表计量精度'],['两下辊','平行≤0.020mm/100mm建议','加载后验证，不用单件图替代装配测量'],['联轴器','偏心≤0.03mm，偏角≤0.1°建议','低于厂家上限；扭转/位置影响实测']], [90,220,189]),
 P('23页图册给出三种辊芯的分段尺寸、胶层处理与检验要求、底板40孔坐标、侧框及轴承/释放装配示意。没有完整标注的螺纹有效深度、倒角、定位销/锁定件与采购件细节须经DFM冻结，不应只凭STEP自动生成NC下单。')])
page('06 片底间隙与误差链',[
 P('设g=(下辊轴心高度+加载有效半径)−(积分筒鞍座高度+薄唇高度)。片底由下部支承决定时，片材厚度不直接加入g；厚度变化影响片中面焦点及上辊位置。'),
 tab(['分项','半宽mm','符号'],[[r[1],f'{r[2]:.3f}',r[3]] for r in reg['stack']], [300,100,99]),
 Spacer(1,12),
 tab(['结果','数值','解释'],[['名义间隙','0.500mm','片底109.9−薄唇109.4'],['最坏累积半宽','0.080mm','各绝对半宽相加'],['RSS半宽','0.03742mm','不是1σ；分布/独立性未证明'],['候选范围','0.420~0.580mm','不含动态卷曲、污染颗粒、张力变化'],['厚度0.15~0.35','片中面−0.025~+0.075mm','相对名义0.2mm；交G1评价离焦']], [140,120,239]),
 S('位置误差不是同一条尺寸链'),
 P('AMT计数量化3.835μm、0.2°角精度等效34.91μm、联轴器变化转矩扭转约5.18μm、简支阶梯轴挠度约1.18μm来自不同定义。不能直接把它们当相互独立的高斯RMS值平方和。胶片滑移、有效径、跳动、编码器周期校准需分别实测，再建立系统位置预算。')])
page('07 机箱、基座与线束空间',[
 figure('drawings/png/04_Case.png',maxh=190),
 P('本版选六块1.5mm 5052-H32平板＋独立角撑，均提供mm单位切割DXF。它是平板钣金方案，没有虚构折弯展开、K因子或折弯半径。若改为U形折弯件，需要另建折弯模型、回弹与装配接口。'),
 P('基座40孔从实际CAD顶面完整圆孔提取；不以开边圆弧的质心当作孔心。螺纹仅用底孔/名义杆表示；切割图不能替代沉孔、精孔、攻牙工序。机箱载荷、提手可靠性、刚度、振动和漏光均未实测。'),
 tab(['线束分组','空间与接口规则'],[
 ['W01模拟 / W02数字','模拟对短线屏蔽；ADC数字接口电平与G2一致，J6真实位置待审'],['W03/W04编码','5V CMOS经适当电平转换后入FPGA；远离电机相线'],['W05/W06动力与数字电源','电机走后侧通道；SP2只接其规定5V，不接24V母线'],['W07/W08弱光控制','PMT控制与参考缓冲信号单独走线，远离PWM'],['W09/W10/W12同步及互锁','SOS/EOS保留回流；激光/快门和释放互锁分别核对'],['W11总电源','左侧24V口到B04保护输入，保留机壳端接与维护空间']], [145,354]),
 P('12条路线是中心线和长度预算，不是已经通过柔性线束干涉或SI验证的成品线。插头外形、应力释放、维修拆出空间需实装；USB调试口可接近性列为强制检查项，吸取原机被ADC模块挡住的经验。')])
page('08 材料DOE与装配验证',[
 P('用户调研资料提出PU/硅胶约Shore A50试样，并提示长期运行、析出及污染风险[U03]。本轮不将这些经验写成材料性能保证；增加防静电PU作为试验候选，必须取得配方、批次和固化记录。'),
 tab(['DOE维度','水平／记录'],[['材料','PU50A、后硫化硅胶50A、防静电PU50A'],['实测法向力','2 / 4.1 / 6 N；不是弹簧理论值'],['速度','3 / 15 mm/s'],['保持条件','片厚0.2mm，张力0.2N，光面无纹理'],['重复','18组合×每组3片；保留片号与前后照片'],['观察','初滑/稳滑、可见/显微划伤、擦拭残留、掉屑、静电、有效径漂移']], [130,369]),
 P('如果移动件自重大于低法向目标，不能强行靠调松螺钉得到2N，应使用更轻上辊、替代弹簧或独立材料夹具，并将夹具变化记录进试验。禁止在同一片样品磨损后继续当“新片”比较。'),
 P('没有执行测试，因此材料结果栏、张力和速度实测栏均为空。14项验证协议从尺寸配合、辊跳动、测力、牵引到运动/材料/互锁/温升/维修/长片累计误差逐项记录。报告结论必须引用真实Raw文件及校准。')])
page('09 检查证据与制造放行边界',[
 tab(['检查','本轮状态','不能推出什么'],[
 ['STEP形体有效性',f'{audit["valid_parts"]}/{audit["total_parts"]} 有效','未含所有采购件真实内部/螺纹'],['静态相交',f'{audit["candidate_pairs"]}候选对；54处预期螺纹啮合；未解释重叠0','排除了继承-继承、参考体、机箱相互项；非整机证书'],['释放位置','0/2.5/5mm各170候选对，未解释重叠0','非连续扫掠、胶层变形、弹簧屈曲或实机安全'],['Python测试','30项通过，含空数据拒绝和合成参考测试','合成测试不是走片实测'],['FreeCAD原生','NOT_RUN；提供导入宏','无原生约束、原生重算通过宣称'],['台架 / DFM / G2回装','NOT_RUN / 未关闭','制造状态仍 BLOCKED']], [105,210,184]),
 P('相交阈值为体积>0.01mm³，包围盒预筛重叠>0.002mm。螺纹底孔与名义杆的相交按列明规则分类，未删除记录；54项明细均在validation/results/intersections.csv中。'),
 S('先关闭这些事项'),
 P('批准基座与轴系接口变更；取得编码器/电机/联轴器厂家正式图；补齐编码器底座、标准紧固件及护罩固定；核对G2板法向和接插件；完成轴承配合/弹簧/胶辊材料DFM；台架验证速度、位置、张力及划伤；独立检查互锁与激光/夹伤防护。随后才能发布加工与采购版本。'),
 P('任何修改都需要重建对应CAD/参数/图册并复测，不能只手工改Excel或平移Blender网格。源程序中仍有固定几何值，JSON并不自动驱动全部特征；变更者必须逐项审查。')])
# Source page: source registry full URLs in manageable table
sources=list(csv.DictReader(open(R/'sources/source_register.csv',encoding='utf-8-sig')))
page('10 来源与文件使用',[
 P('U来源是项目原件，S来源是本次核验的原厂公开资料；D来源是本轮设计假设。它们并不具有相同成熟度。下载/读取失败及字段冲突见sources/records/网页核验说明.md。'),
 tab(['ID','来源／用途'],[[r['source_id'],r['名称']+'\n'+r['支持范围与限制']+'\n'+r['来源']] for r in sources],[38,461],8),
 Spacer(1,8),P('先打开START_HERE.html；审D04/D05/D07/D09/D21/D22。机械工程师确认接口和工艺后，按验证报告执行台架。源文件、版本、检查日志与审批应一同进入受控仓库；本包不改写旧R5/R5.1。')])
build('ZL80_G3_机械设计与集成说明',story)

# Separate transport verification report
story=[]
page('走片速度与张力：计算及验证报告',[
 P('报告编号 R52-G3-VAL-D01。设备状态：未建实物台架；实际速度、张力、滑移、划伤、温升数据均未取得。本文件给出可复算设计预算、验证协议及记录入口，而不是通过报告。'),
 tab(['证据类别','现有证据','状态'],[['解析计算','速度/行频、编码量化、牵引、轴挠度、扭转与间隙','已运行，模型假设'],['几何计算','闭合态及3个释放位置；STEP有效性','已运行，有限范围'],['程序逻辑','30项单元测试；合成输入仅验证算法','已运行，不是台架'],['实物测试','14项协议、18组材料筛选、空白记录','NOT_RUN'],['制造放行','等待DFM、采购细节、独立计量与安全评审','BLOCKED']], [95,280,124]),
 S('禁止把三种力混用'),P('法向力N由弹簧、自重和摩擦决定；牵引上限近似μN；片张力由上/下游边界和传动决定。单电机出口牵引＋入口随动辊只提供低张力运行的机构基础，不是张力闭环。必须在试验中测上游/下游受力位置并保持一致。'),
 S('证据文件'),P('calculation_summary.json、speed_modes.csv、traction_sensitivity.csv、tolerance_stack.csv均为模型输出。bench_results_EMPTY.csv、transport_raw_EMPTY.csv及material_observations_EMPTY.csv为待填模板，不含编造数据。')])
page('V1 扫描时序与送片速度预算',[
 P('按每面产生一条有效扫描、所有6面均可用且G1理想f-θ映射计算。行频=6×rpm/60；v=行频×Y间距；辊速=60v/(πD)。不同转速的可用性必须由polygon供应商确认。'),
 tab(['棱镜rpm','间距μm','行频Hz','片速mm/s','辊rpm','微步Hz'],[[int(m[0]),int(m[1]),f'{m[2]:.0f}',f'{m[3]:.2f}',f'{m[4]:.3f}',f'{m[5]:.1f}'] for m in reg['modes']],[77,75,75,91,90,91]),
 Spacer(1,10),P('3000rpm、50μm候选模式为300行/s、15mm/s、约14.324辊rpm；80mm有效区用时1.27324ms，胶片同时前进约19.10μm。必须按每个采样时刻关联Y位置，不可把整条斜轨迹当作同一水平行。'),
 P('4096PPR四倍频，名义量化为3.83495μm；原厂0.2°角精度换算34.9066μm，二者性质不同。当前不能宣称满足5μm RMS运动目标。电机全步314.159μm、16微步19.635μm同样不是真实位移精度。')])
page('V2 夹紧、牵引与转矩预算',[
 tab(['参数/公式','数值/条件'],[['弹簧力 2k(L0−L)','4.1N，k0.5，L0=18，L=13.9'],['移动质量/自重','0.2kg假设 / 1.96133N'],['法向力近似','6.06133N；实际含导向摩擦，须测力'],['μ=0.3的牵引极限','1.818399N；不是实测摩擦系数'],['与1.2N设计拉力比较','1.51533倍；低于本轮建议的2倍'],['需要2倍时的N','8.0N，未验证划伤不得直接加压'],['运行转矩','0.015025Nm，拉力/拖曳/加速相加'],['×3后的需求','0.045075Nm；电机动态证据缺失'],['联轴器扭转等效','约5.181μm，对应这组变化负载'],['轴简支挠度','约1.178μm；E193GPa、线弹性阶梯梁模型']], [250,249]),
 S('必须补的模型输入'),P('真实湿度/污染下静动摩擦、加载有效径、上辊移动质量、预载不平衡、启动轴承阻力、弹簧散差、真实惯量、速度转矩曲线、底片抗划伤上限。保持转矩与需求的比值不作为PASS。'),
 P('摩擦敏感性表覆盖μ=0.15/0.3/0.5、法向力2/4.1/6N及设计拉力多档，仅作设计筛选。若滑移出现，应停机记录，不用图像插值修复后宣称机械通过。')])
page('V3 台架、计量与采样方法',[
 tab(['通道/器具','最低记录要求'],[['独立位移参考','不能用被评估编码器或STEP脉冲作真值；记录量程、校准、分辨率、带宽和不确定度'],['编码器A/B/Z','同时采入口/出口轴；登记PPR、倍频、方向、轮径标定、角周期修正表'],['张力','标定0~5N量程候选；注明受力位置/包角/安装，不把压辊法向测力当张力'],['时间','同一时间基准或有已知误差的同步；建议1kHz开始，并声明抗混叠与实际采样间隔'],['样片/环境','FilmID、厚度、宽度、批次、前后面、温湿度、清洁/已用次数'],['驱动','B05版本、电流、细分、供电、实际棱镜/辊速、加速度、热机时间'],['安全','先无光、无贵重原片；核对禁能、开盖/提辊互锁、夹点和回退方案']], [120,379]),
 P('每一速度至少3次独立装片。加速段与稳态段分别保存；用于分析的稳定窗口在试验前定义。低速0.5mm/s至少10s只有5mm样程，不能据此证明1m尺度或全辊周精度，长片和全周试验另做。'),
 P('若报告5μm级RMS，应使参考仪器不确定度对目标有足够区分能力，并公开仪器带宽、滤波、时钟误差和空间对准。不可靠任意平滑、重新对齐或缩短窗口获得好看的数字。')])
page('V4 测试协议 01—07',[
 tab(['ID / 项目','方法','候选判据'],[[r[0]+'\n'+r[1],r[2],r[3]+'\n状态：NOT_RUN'] for r in reg['bench'][:7]],[100,228,171],8.8),
 Spacer(1,14),P('上述误差、公差和力值是内部候选判据，尚未签署。检验设备、材料商和整机目标不一致时必须更新测试版本，不能在看到结果后修改门槛。')])
page('V5 测试协议 08—14',[
 tab(['ID / 项目','方法','候选判据'],[[r[0]+'\n'+r[1],r[2],r[3]+'\n状态：NOT_RUN'] for r in reg['bench'][7:]],[100,228,171],8.8),
 Spacer(1,14),P('张力范围、无划伤、长期热稳定和激光泄漏必须用实际材料与实机验证。程序不会自动依据一个数字把整机标成合格。')])
page('V6 分析程序与结论签署',[
 P('执行示例：python tools/analyze_transport.py validation/templates/transport_raw_EMPTY.csv --target-speed 15 --output transport_analysis.json。空模板会被拒绝，这是正确行为；正式分析先使用真实数据副本。'),
 P('程序要求至少20行有效数据，time_s严格递增；读取独立reference_position_mm与已标定tension_N。20行只是程序最低数据校验，不满足正式至少10s、建议1kHz的试验方案。'),
 tab(['输出','计算定义'],[['平均速度','参考位置与时间的最小二乘斜率，保留设定速度的百分误差'],['位置残差RMS/P2P','原始独立位移减去线性拟合后统计；不自动滤波'],['张力均值与RMS','均值、围绕均值的总体标准差及最小/最大'],['采样间隔','实际最小/最大间隔，便于发现时标异常'],['状态','ANALYZED_NOT_REVIEWED，绝不自动给制造PASS']], [135,364]),
 S('完整闭环还需人工完成'),P('将Raw、仪器校准、TestID、参数哈希、照片、环境和异常记录归档；比较分析结果与预先批准的判据；解释编码器周期项、滑移、温漂和重复装夹差异；审核后才能签署。未运行、无法判定和不适用必须保留原状态。'),
 S('本轮结论'),P('几何和解析预算已经形成可继续设计的证据；编码器角精度、牵引裕量、低速纹波、G2接口、材料无损性及安全仍未闭合。因此G3开发文件包交付完成，实物验证未完成，制造状态BLOCKED。')])
build('ZL80_G3_速度张力计算与验证报告',story)
print('reports built')
