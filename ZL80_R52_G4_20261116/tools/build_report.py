"""Data-driven G4 review report. Source values are emitted from actual audits."""
from pathlib import Path
import json,csv,html
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
R=Path(__file__).resolve().parents[1];pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
S={
 'title':ParagraphStyle('title',fontName='STSong-Light',fontSize=25,leading=34,textColor=colors.HexColor('#183A55'),spaceAfter=18),
 'h':ParagraphStyle('h',fontName='STSong-Light',fontSize=16,leading=22,textColor=colors.HexColor('#183A55'),spaceAfter=12),
 'sub':ParagraphStyle('sub',fontName='STSong-Light',fontSize=11.5,leading=17,textColor=colors.HexColor('#254C67'),spaceBefore=10,spaceAfter=6),
 'body':ParagraphStyle('body',fontName='STSong-Light',fontSize=10,leading=16,wordWrap='CJK',spaceAfter=8),
 'small':ParagraphStyle('small',fontName='STSong-Light',fontSize=8.3,leading=12,wordWrap='CJK',spaceAfter=6),
 'tab':ParagraphStyle('tab',fontName='STSong-Light',fontSize=8.4,leading=12,wordWrap='CJK'),
 'thead':ParagraphStyle('thead',fontName='STSong-Light',fontSize=8.5,leading=12,textColor=colors.white,wordWrap='CJK')}
flow=[];md=[]
def p(s,style='body'):
 flow.append(Paragraph(html.escape(s).replace('\n','<br/>'),S[style]));md.append(s+'\n')
def h(s):p(s,'h')
def sub(s):p(s,'sub')
def page(title):
 if flow:flow.append(PageBreak())
 h(title);md.append('\n---\n')
def table(headers,rows,widths):
 data=[[Paragraph(html.escape(str(v)),S['thead']) for v in headers]]+[[Paragraph(html.escape('' if v is None else str(v)),S['tab']) for v in row] for row in rows]
 t=Table(data,colWidths=[w*mm for w in widths],repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#183A55')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#F1F5F8'),colors.white]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#56768C'))]));flow.append(t);flow.append(Spacer(1,7*mm));md.append('| '+' | '.join(headers)+' |\n|'+ '|'.join(['---']*len(headers))+'|\n'+'\n'.join('| '+' | '.join(str(v) for v in row)+' |' for row in rows)+'\n')
audit=json.loads((R/'validation/results/copper_audit.json').read_text());mcad=json.loads((R/'validation/results/mcad_audit.json').read_text());source=list(csv.DictReader((R/'sources/source_register.csv').open(encoding='utf-8-sig')))
p('ZL80  /  G4','sub');p('PCB与机械结构联动\n首批工程交付', 'title')
p('修订 R52-G4-E02-D01   |   2026-11-16','sub')
p('基线：G2-E01电路候选 + G3四辊/机箱实际几何。本版不改变635 nm、旋转多面镜、80 mm有效片宽、100 mm扫描预留、横置狭缝积分筒和单PMT的系统路线。')
table(['交付层次','实际完成','边界'],[
['小板布线','B06、B07、B08实际铜线与过孔候选','自编回读连通；不是KiCad原生DRC通过'],
['PMT前端','B01输入/TIA输出关键网；重新排布与机械回装','其余14个网络、43条最少待连接关系未闭合'],
['机械接口','4板、123个新几何对象回装到231个保留对象','8处预期PMT插座/插针占位；插座型号未冻结'],
['验证','原理图/铜几何回读、STEP交叉检查、29项Python测试','没有原生KiCad、厂家SPICE或实物台架证据']], [30,76,68])
p('制造状态：BLOCKED。文件包可以交给AI/工程师继续审查和开发，但不能据此直接下单、接线或上电。','sub')
p('不提供Gerber、生产钻孔、生产贴片坐标或自动制造放行。文件中的器件、叠层及安装变更均属于待批准候选。','small')
page('01  基线、范围与交付目录')
p('本阶段名称以近期路线的“PCB与结构联动”为准。它不是旧分阶段描述中的整个ADC/电源研发完成声明，也不包括重新设计高速转子或真实f-theta处方。')
table(['目录','用途'],[
['electronics/projects/B06、B07、B08','原理图 + 已布铜线PCB候选 + 本地库 + 工程规则'],['electronics/projects/B01','原理图 + 关键网部分布线PCB；其余未连明确保留'],['electronics/downstream_R51_UNCLOSED','B02—B05未闭合继承稿；不参与本轮电路完成统计'],['cad/boards、cad/assemblies','单板局部/安装STEP、去罩回装总装、含壳总装、插拔空间模型'],['engineering','84器件BOM、233针脚/类型、变更、接口、叠层、走线和风险'],['validation/results','实际自编检查结果、原生NOT_RUN记录与制造阻止原因'],['tools、tests','可重建脚本、独立回读、真实工具调用与测试'],['sources/inherited','不可覆盖的输入快照与ZIP哈希；主输入来源可追溯']], [65,109])
p('更新原则：PCB网表与G2拓扑保持一致；板面、安装方向、器件位置与封装是本轮变更。每次变更必须同时重建源文件、STEP和接口表。不能仅在Blender里移动模型后认为工程文件已更新。')
page('02  B06 / B07 / B08布线候选')
p('B06/B07采用OPA356 TIA与TLV3501比较器的G2电路；B08保留OPA828参考光电流链。关键反馈与去耦改为紧凑候选封装；B07部分电容和B08运放位于背面。原理图网络未改变。')
table(['板','线段/过孔','焊盘','最少未连','总分支线长'],[[v['board'],str(v['segments'])+' / '+str(v['vias']),v['pads'],v['unconnected_min_links'],str(v['track_length_mm'])+' mm'] for v in audit if v['board']!='B01'],[20,39,24,38,53])
p('上述线长是所有已布分支铜线之和，不是某两针之间的路径长度，也不能直接代入信号延迟或环路寄生计算。所有数据由最终.kicad_pcb重新解析，不依赖布线器声称“已连”的边表。')
sub('输入节点与地回流')
p('PD_SUM只在顶层、REF_SUM只在底层布线，关键求和网不使用过孔；内层保留输入节点禁布区。地网络有显式铜线，同时定义In1地平面；当前没有伪造filled_polygons。必须在KiCad重新填铜，检查地岛、回流和电源阻抗。')
sub('候选封装不是采购冻结')
p('0402电阻/电容需重新选定真实MPN、额定功率、电压、精度、介质和偏压特性。S5971按原厂底视图转换候选顶视引脚位置；需要实物确认。TMS-104-02-L-S仅是小板J1候选，对接件、锁止和防反插未冻结。[V_G4_01—05]')
sub('本轮没有证明的性能')
p('G2的变幅时间偏移、低光噪声和比较器边沿问题仍然存在。布通铜线不证明79.58 ns同步预算通过；不能把比较器典型传播延迟当成端到端抖动。')
page('03  B01前端与B02—B05边界')
p('B01板框仍为90×50 mm。PMT输入与TIA反馈/输出已布候选铜线，AD8138及偏置、供电、控制和输出接口已重新排布但尚未全部连接。')
table(['内容','状态与下一步'],[
['PMT_I与TIA_OUT','72个铜线段、0个过孔；输入/反馈的真实寄生仍未提取。'],['其余B01网络','14个网络仍有43条最少连接关系；不得认为B01可上电。'],['PMT插座','八针X/Z名义坐标对应；0.9mm孔是历史假设插座尾针孔，不是裸1mm PMT引脚直插许可。'],['B02 ADC','1.8V CMOS/LVDS模式、时钟、驱动、SPI、电平与约束必须按最终方案闭合；不新增虚构连接。'],['B03电源/偏置','必须先确定前端台架供电、PMT控制限幅与读回、OFFSET_0V5和ADC_VCM。'],['B04/B05','输入保护、硬件关光、运动驱动、编码器及真实接插件仍未闭合。']], [40,134])
p('G2的100kΩ/2.2pF高跨阻模型整定风险并未因本次布线而自动消失。保留原模型作为历史分析，待真实器件模型、输入电容和板级寄生确定后重新仿真并做注入电流台架。不得补造“实测曲线”。')
page('04  坐标、感光面与机械回装')
p('所有板使用右手局部坐标。局部x/y是PCB数值坐标；z=0为板底、z=1.6为顶面。B01/B08以局部v对应世界−Z、正面法向+Y；B06/B07以v对应世界+Z、正面法向−Y。')
photo=list(csv.DictReader((R/'engineering/photodiode_coordinates.csv').open(encoding='utf-8-sig')))
table(['探测板','局部D1','世界感光面 XYZ / mm'],[[r['board'],{'B06':'(15,4)','B07':'(3,4)，旋转180°','B08':'(13,10)'}[r['board']],f"({r['x_mm']}, {r['y_mm']}, {r['z_mm']})"] for r in photo],[30,55,89])
p('S5971原厂尺寸图的感光面距法兰2.8 mm，并不是3.6±0.2 mm壳顶。引脚架高3.6 mm是本项目候选装配值，不能当作厂家要求。[V_G4_03]')
p('X/Z回到原名义扫描坐标只证明坐标表一致，不证明实际光线穿过窗口。G1仍必须验证窗口姿态、有效面Y位置、安装公差以及SOS/EOS真实时刻。')
sub('PMT接插件变更')
p('B01/J2初排(14,35)的假设插拔走廊与PMT本体相交，已改为(10,37)。本轮按“接插件宽高外加3mm、接合后10mm操作空间”检查后不再相交；真正对接件和线缆未定，不能将假设走廊视为最终维护性证明。')
p('STEP总装含123个新板卡/器件/引脚对象和231个保留G3对象。8处PMT插座与旧针脚重叠是预期接合占位，逐条保留记录，不作为加工配合通过。')
page('05  叠层、电源、接地与接口约束')
table(['层','厚度 / mm','用途'],[['F.Cu',.035,'顶层信号/器件'],['介质1',.18,'候选FR4'],['In1.Cu',.035,'地平面，尚未原生填铜'],['介质2',1.10,'候选芯板'],['In2.Cu',.035,'电源/信号；输入高阻区避让'],['介质3',.18,'候选FR4'],['B.Cu',.035,'背面信号/器件'],['合计',1.60,'不含阻焊；板厂实物叠层待审']], [35,40,99])
p('候选线宽/间距0.15/0.15 mm；过孔铜径/孔径0.60/0.30 mm，名义环宽0.15 mm。数值是几何起点，不是载流、温升、阻抗或板厂DFM批准。模拟高阻节点附近的寄生、污染与清洗必须用样板验证。')
p('B06/B07的SYNC是本地3.3V逻辑候选，不可直接接入未核对的1.8V输入。J1电源与地是外部供给假设；PWR_FLAG只是ERC驱动声明，不代表电源电路已实现。B02—B05未闭合，禁止据此整机上电。')
p('线束保留G3的12条中心线走廊，另外给出5个G4接口端点与引出方向。折线路径没有圆滑、连接器拉出没有真实线材模型，不能宣称弯曲半径与线束干涉已经通过。')
page('06  实际检查结果与证据等级')
table(['证据','结果','不能据此得出的结论'],[
['原理图标签/线段/针脚回读','233条针脚网络记录一致，无局部标签短接','不是原生ERC，不证明器件工作点正确'],['铜几何与连通回读','三小板最少未连0；四板本轮间距检查无冲突','不是KiCad DRC；未覆盖填铜、阻焊、丝印、回流或DFM'],['跨机械上下文检查','48个包络候选对进入实际实体求交；8处预期插座接合','不含紧固公差、弹性、热变形、真实线束与连续运动'],['STEP有效性','123个新几何对象有效','有效实体不等于可加工或已装配'],['Python测试','29项通过','包含检查“未完成仍保持未完成”的测试；不是产品性能'],['KiCad/FreeCAD/SPICE/台架','NOT_RUN','没有原生软件或实际测量通过记录']], [42,63,69])
p('检查程序从输出文件回读实际几何与网络，未把布线器路由成功列表当成独立证据。本轮曾发现过孔与异网焊盘间距、输入禁布区冲突以及GND断连；修正后重新执行，最终记录存放validation/results。')
p('原生工具缺失已被native_validate.py实际记录。任何人不得用修改状态字段、忽略警告、添加虚假台架数值的方式将制造门禁改为通过。')
page('07  本机打开、复算与原生审查')
sub('先打开文件，不先接线')
p('完整解压后，从electronics/projects/B06/B06_G4.kicad_pro进入。符号、封装与STEP使用包内相对路径；不要只拷贝单个PCB文件。原生程序若提示解析或字段错误，保留日志和软件版本，不直接保存覆盖唯一来源。')
sub('推荐执行顺序')
table(['顺序','操作','输出'],[
['1','python tools/run_checks.py','自编回读与29项测试；需要numpy/shapely'],['2','在KiCad检查方向、库、封装、NC与板框','保存独立审核副本并核对差异'],['3','在KiCad填充全部铜区并重新保存','原生填充结果；不能跳过地平面审查'],['4','python tools/native_validate.py','真实ERC/DRC/原理图一致性；缺工具返回NOT_RUN'],['5','FreeCAD运行cad/freecad/import_G4.FCMacro','STEP审查工程；不是重建参数化机械历史'],['6','python tools/release_check.py','当前预期BLOCKED；禁止为变绿删除门禁']], [14,91,69])
p('KiCad原生命令支持sch erc、pcb drc与--schematic-parity，本包调用真实执行器而不是模拟输出。G4不要求盲目升级到最新版本；记录实际版本并以实际打开/保存/重开结果验证兼容性。[V_G4_06]')
p('重建：python tools/rebuild_candidates.py，会重新生成布局、铜线候选、STEP及数据表。它不自动运行KiCad，也不自动重做文档/Excel。设计变更后必须重新检查和更新所有发布件。')
page('08  台架与制造放行顺序')
p('本包有12项G4验证协议和空白测量记录，全部实物结果为NOT_RUN。先完成B06/B07的小信号板审核；电源与端口未确认前，不连接SP2、PMT或激光。')
table(['验证组','核心动作','保留的证据'],[
['文件/制造接口','原生解析、填铜、ERC/DRC、BOM/封装/孔位/丝印DFM','工具版本、源哈希、报告与人工处理记录'],['小板电气','批准电源后的限流静态检查，阈值、极性、迟滞和输出','实物序号、供电、温度、注入源、Raw波形'],['扫描同步','恒幅重复抖动与变幅时间偏移分别测量','前沿/后沿/中心时间戳，不用单个典型延迟代替'],['参考/前端','B08线性与噪声，B01完成后再做频响和阶跃','真实原始数据；不得用分析模型冒充实测'],['回装/干扰','实物接插件、光轴、线束和电机负载逐步加入','单变量对照、安装照片、扫描位置与数据版本']], [30,84,60])
p('制造放行仍被七类问题阻止：B01未连、B02—B05未闭合、原生验证未执行、插座与对接件未定、G1光轴变更未批准、台架/EMC/热/DFM未做，以及没有负责人的制造批准。')
p('下一份实施任务应是小板原生闭环，而不是直接生成全套Gerber。先对B06执行打开—填铜—ERC/DRC—封装核验—受控样板—台架测试，再复制该闭环到B07/B08。','sub')
page('09  可追溯来源与未冻结项')
p('来源分三类：用户工程包是设计基线；本轮程序输出是计算/几何证据；厂家文件是器件尺寸与使用限制依据。三者不相互替代。输入ZIP哈希位于sources/input_hashes.json。')
for s in source:
 p(s['id']+'  '+s['title'],'sub');p(s['use'],'small');p(s['url'],'small')
p('本文件所有坐标、线长和交叉检查结果均可在engineering与validation/results中找到对应记录。图册为实际PCB铜几何和STEP投影的独立矢量渲染，不是原生KiCad截图。')
p('归档建议：把本包作为一个待审核候选修订，不覆盖G2/G3原始包。实测数据存储在项目规定的Raw归档位置，仓库只保存测试方法、结果摘要及证据路径。')
def footer(c,doc):
 c.setStrokeColor(colors.HexColor('#CCD8E1'));c.line(18*mm,17*mm,192*mm,17*mm);c.setFont('STSong-Light',8);c.setFillColor(colors.HexColor('#496275'));c.drawString(18*mm,12*mm,'ZL80  |  G4-E02-D01  |  REVIEW ONLY · 制造状态 BLOCKED');c.drawRightString(192*mm,12*mm,str(doc.page))
file=R/'docs/ZL80_G4_PCB与结构联动设计说明.pdf'
SimpleDocTemplate(str(file),pagesize=(210*mm,297*mm),leftMargin=18*mm,rightMargin=18*mm,topMargin=18*mm,bottomMargin=24*mm).build(flow,onFirstPage=footer,onLaterPages=footer)
(R/'docs/ZL80_G4_PCB与结构联动设计说明.md').write_text('\n'.join(md),encoding='utf8')
print(file)
