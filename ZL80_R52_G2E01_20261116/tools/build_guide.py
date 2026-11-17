from pathlib import Path
import json,csv,html
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,PageBreak,Image,KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.pagesizes import A4
R=Path(__file__).resolve().parents[1];D=R/'docs';D.mkdir(exist_ok=True)
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
navy=colors.HexColor('#123047');muted=colors.HexColor('#536572');pale=colors.HexColor('#EBF1F5')
styles={
 'title':ParagraphStyle('title',fontName='STSong-Light',fontSize=25,leading=33,textColor=navy,spaceAfter=15),
 'h1':ParagraphStyle('h1',fontName='STSong-Light',fontSize=18,leading=25,textColor=navy,spaceAfter=13),
 'h2':ParagraphStyle('h2',fontName='STSong-Light',fontSize=12,leading=18,textColor=navy,spaceBefore=8,spaceAfter=5),
 'body':ParagraphStyle('body',fontName='STSong-Light',fontSize=10,leading=16,spaceAfter=8,wordWrap='CJK'),
 'small':ParagraphStyle('small',fontName='STSong-Light',fontSize=8.5,leading=12,spaceAfter=5,wordWrap='CJK'),
 'cell':ParagraphStyle('cell',fontName='STSong-Light',fontSize=8.5,leading=12,wordWrap='CJK'),
 'th':ParagraphStyle('th',fontName='STSong-Light',fontSize=8.5,leading=12,textColor=colors.white,wordWrap='CJK'),
 'code':ParagraphStyle('code',fontName='Courier',fontSize=8,leading=12,spaceAfter=6,wordWrap='LTR'),}
story=[]
def norm(t):
 return str(t).replace('−','-').replace('µ','u').replace('μ','u').replace('Ω','ohm').replace('⁵','^5').replace('⁴','^4').replace('σ','sigma').replace('×',' x ')
def P(t,k='body'):story.append(Paragraph(norm(t),styles[k]))
def H(t):P(t,'h2')
def T(headers,rows,widths):
 data=[[Paragraph(html.escape(norm(x)),styles['th']) for x in headers]]+[[Paragraph(html.escape(norm(x)),styles['cell']) for x in row] for row in rows]
 t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),navy),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,0),.6,navy),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,pale]),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#CCD7DE'))]));story.extend([t,Spacer(1,8)])
def page(title):
 if story:story.append(PageBreak())
 P(title,'h1')
def fig(name,caption):
 story.append(Image(str(R/'simulations/plots'/name),width=475,height=266));P(caption,'small')
def footer(c,doc):
 w,h=A4;c.setStrokeColor(colors.HexColor('#B7C7D2'));c.line(40,38,w-40,38);c.setFont('STSong-Light',8);c.setFillColor(muted);c.drawString(40,25,'ZL80 · R52-G2E01-D01 · 工程候选 / NOT RELEASED');c.drawRightString(w-40,25,str(doc.page))

P('ZL80 R5.2<br/>G2-E01 电路闭合候选','title')
P('首批小板与模拟前端｜设计说明、计算证据、台架执行协议','h2')
P('2026-11-16 · 本阶段名称采用R5.1 AI工程路线：G2为电路闭合；不与早期“G2积分筒”混用。')
T(['范围','本次交付状态'],[
['B06 / B07','同步接收小板：元件级原理图、正确针脚类型、18×20mm板框和空间初排。'],
['B08','参考光板：元件级原理图、±5V接口、25×20mm板框。'],
['B01','PMT TIA与直流差分输出：元件级原理图、90×50mm板框、模型及工作点审查。'],
['B02—B05','继承稿保持UNCLOSED；新增ADC针脚审查与后续电路闭合任务，不宣称完整。'],
['验证','执行数值模型、35项Python测试、文本网络回读、焊盘网名对照；原生ERC/DRC/SPICE、台架均未执行。'],
['制造','BLOCKED：PCB尚未布线，缺真实封装/供应链确认及台架证据；没有Gerber。']],[87,388])
H('来源与新设计分开')
P('继承R5.1的板框、孔位、接插件信号和PMT/TIA/ADC技术路线，并读取G0/G1的80mm成像、100mm扫描、六面/3000rpm及同步预算。新选择为OPA356＋TLV3501同步接收、实际偏置/反馈网络、B01差分余量及参考板低通。它们是本批候选，不是原机已证实电路。')
P('输入归档SHA256见reference/input_hashes.json；元件原厂依据见V01—V08与vendor_source_register.json。示意图、AI建议和历史报告都不替代器件数据手册或实测。','small')
H('建议先看')
P('先开B06原理图，复核器件脚号、光电二极管方向及J1接口；再看本册第3页的触发偏移模型。通过本机原生检查后，才开展台架与PCB布线。')

page('01  B06/B07：同步接收小板')
P('电路：S5971三脚PIN二极管 → OPA356跨阻放大 → TLV3501迟滞比较 → 33Ω串阻 → 3.3V SYNC。外部5V仅用于TLV75533供电，本板模拟与比较器为3.3V。J1的电源脚仍是5V输入，不是3.3V输入。')
T(['功能','候选电路/数值','来源或边界'],[
['PD与外壳','S5971：1=K，3=A，2=CASE；A/CASE接GND，K接PD_SUM','V03；约1V反偏，不套用10V条件的100MHz'],
['TIA','OPA356，Rf=10kΩ/0.1%，Cf=2.2pF C0G','V01脚号；Rf/Cf为本次提议'],
['偏置','3.3V→232Ω→VBIAS→100Ω→GND；1µF旁路','考虑阈值分支负载后VBIAS约0.99557V'],
['阈值','3.3V→100kΩ→THRESH→1kΩ→VBIAS；10nF旁路','THRESH约1.01839V，高于偏置22.82mV'],
['迟滞','TIA到IN+串1kΩ；输出到IN+反馈1MΩ；IN−接阈值','TLV3501典型内部迟滞6mV；SHDN绑低 [V02]'],
['供电','TLV75533；输入/输出2.2µF；U1/U2各100nF','V04；有效输出电容须考虑DC偏置和器件选型'],
['接口','J1: 1=5V，2=GND，3=SYNC，4=GND','3.3V推挽输出，不可接1.8V Bank33']],[65,215,195])
H('启动与空间')
P('上电偏置未稳定时可能产生额外边沿，FPGA须在供电/参考稳定及合法扫描窗口确认后接收事件；本小板不是激光安全执行器。18×20mm板框保留，但B06的D1中心为(14,6)mm，B07为(14,7.5)mm；不同孔型导致位置差别，必须回写G1支架/光轴接口。')
P('空间初排以反馈和去耦优先，但仍需在原生PCB逐个优化其实际环路；未完成布线、铜面或真实回流验证。高阻求和节点不引出长测试线；台架只观察低阻TP1/TIA_OUT。光电封装方向和安装高度必须与样品复核。')

page('02  B06：实际执行的模型揭示什么')
P('运行条件：单极点A(s)、A0=10⁵、GBW=200MHz、总输入C=15pF；输入为假定的对称光电流脉冲，边沿σ=150ns、平台约1.6µs。5~100µA仅为模型扫幅，不是已经测出的扫描头光强。比较器以6mV典型迟滞和固定4.5ns延迟建模，未包含实际过驱相关延迟。[V01,V02]')
fig('B06_amplitude_timewalk.png','图1｜已执行的数值模型：前沿幅度偏移峰峰值约306ns；脉冲中心法约23ns。不是台架数据，不代表真实脉冲具备对称性。')
T(['量','结果','解释'],[
['瞬时扫速','62,831.85mm/s','G1算例：6面、3000rpm、EFL100mm'],
['5µm时间预算','约79.58ns','建议预算，未批准/未验证；不是比较器数据手册指标'],
['前沿偏移','306ns峰峰值','固定阈值对幅度敏感，不等于随机抖动'],
['局部白噪声子集','约0.296mV RMS；局部等效约1.0ns','仅模型中的电阻/散粒/OPA白噪声，不含全部噪声'],
['结论','同步精度 NOT_DEMONSTRATED','前后沿、中心、光幅度校正方案必须实测比较']],[102,145,228])

page('03  B08：参考光通道')
P('保留±5V供电的四针接口：J1/1=+5VA，2=AGND，3=−5VA，4=REF_V。S5971阴极接虚地求和点，阳极经1kΩ接−5V并由100nF旁路，外壳接AGND。OPA828的+输入接AGND，反馈10kΩ//100pF，输出经33Ω到REF_V。[V03,V05]')
T(['设计点','内容'],[
['极性','按光电流从K流向A建立等效电流吸收模型，输出为正；上台架必须先实测确认。'],
['电流范围','候选0~100µA对应约0~1V；先测实际取光功率，不能用该范围替代PD线性测试。'],
['带宽','有限模型约160kHz；这是故意较慢的参考通道，不是PMT像素级信号链。'],
['参考位置','建议监测片前、ND之后的有效光功率；实际取光位置由G1确认。'],
['时间对齐','B08与B01有不同群延迟；必须记录采样时刻并对齐/标定，不可直接按同一下标相除。'],
['ADC接口','REF_V是单端输出，B02的独立差分驱动仍需闭合，不能直接接成完整ADC通道。']],[90,385])
fig('B06_B08_AC.png','图2｜有限运放模型下的归一化频率响应；没有包含实际PCB、器件高阶极点或电源噪声。')

page('04  B01：PMT TIA与差分驱动')
P('针脚式H10720-20仍为候选：1/8=NC，2=Vref输出，3=Vcont输入，4=供电，5=GND，6=信号地，7=电流输出。原理图将其作为具有正确电气方向的模块，而不是全passive黑盒；H10721为线缆版本，不能直接替换机械接口。[V08]')
T(['功能','候选实现','状态'],[
['TIA','OPA828，±5V；100kΩ/2.2pF基线；输入按电流吸收建模','元件级候选；真实过载/高阶稳定性未验证'],
['增益配置','10kΩ/6.8pF、1kΩ/22pF为替代焊装组合','不是逐像素开关；不能三档同时并联'],
['差分驱动','AD8138；Rg=499Ω，Rf=806Ω，外部OFFSET=0.5V','直流耦合；增益1.61523'],
['输出隔离','每腿33Ω＋差分330pF','外部RC约7.31MHz，不等于完整抗混叠系统'],
['ADC共模','B02提供ADC_VCM，算例0.9V','B02仍未闭合；台架必须提供已验证参考'],
['供电/控制','B03负责+5PMT、±5VA、0.5V偏置、VCONT','未把这些外部供电假装成本板自产']],[66,220,189])
H('为什么把差分增益改为1.615')
P('在0~1V的TIA工作窗口内，差分输出为−0.8076~+0.8076V。假设ADC使用2Vpp差分满量程，即±1V，每端留约0.1924V差分余量，避免零光恰落到负满量程。输出脚各为0.9V±Vdiff/2。这个余量不能修复PMT本体饱和，也不能替代偏置漂移和ADC共模实测。[V06,V07]')
H('不能直接制造的机械点')
P('H10720插座沿用旧孔位包络，插座MPN及顶/底视图方向尚未冻结；旧0.9mm孔仅能解释为假设插座尾针，不能直插约1mm PMT引脚。制造前必须由实物和厂家图纸关闭此项。')

page('05  B01：带宽、整定与模型边界')
fig('B01_step_response.png','图3｜0→10µA等效电流阶跃。实际执行单极点运放模型及理想差分增益＋外部RC；不是厂商AD8138宏模型，也未测板卡。')
T(['配置/条件','模型计算','不能推出的结论'],[
['100kΩ/2.2pF，Cin=20pF','−3dB约0.84MHz；0.1%阶跃整定约1.29µs','不能声称在0.796µs像素驻留内已充分整定'],
['在约628kHz','TIA与外部RC相对幅度约0.80','不是完整扫描仪MTF；还缺光斑、运动和采样滤波'],
['输入C=5/20/50pF','已输出9组Rf/Cf/Cin角落表','单极点模型相位裕度不能证明实际PCB稳定'],
['1kΩ档','1V需1mA；100µA仅0.1V','不能强行用真实PMT提供1mA；需尊重其工作点和限制']],[130,170,175])
P('原厂V08给出的最大平均信号电流不是任意瞬态条件下的线性保证。当前厂家PDF中-20阳极辐射灵敏度为规定条件下1.5×10⁴A/W，而早期项目曾使用1.5×10⁵A/W；本批因此使用电流输入模型，不悄悄更新旧光子预算。控制电压调整的稳定时间也需按实际条件确认，不能当纳秒增益开关。')

page('06  后续B02：ADC闭合的接口依据')
P('旧R5/R5.1布局采用AD9268并行CMOS连接。本批纠正之前说明中将其称为LVDS的冲突，不擅自更换架构。随包提供65焊盘针脚表和独立审核符号；B02旧原理图仍为UNCLOSED。[V07]')
T(['必须核对','本批给出的约束'],[
['模式/电平','AVDD/DRVDD名义1.8V；并行CMOS数据；SP2 Bank33必须按真实Vadj、电压和版本验证。'],
['数据/时钟','两路16位＋DCOA/DCOB为34条关键线；接头针数不证明所有脚空闲或可作时钟。需审查源同步捕获/回流/时序。'],
['配置','SDIO双向，SCLK/CSB输入；OEB、PDWN、SYNC有明确启动状态；时钟与SPI转换器均需真实MPN。'],
['参考/共模','VREF是输入/输出，VCM是输出，SENSE输入；2Vpp差分模式需明确SENSE=GND；外部FDA负载需核对。'],
['采样/延迟','DCS开启时最低20MSPS；CMOS模式12周期流水线起算。数据、位置、ROI标签和滤波延迟一起对齐。'],
['验证','先电源、SPI读回、内置测试码、32位数据重组、双通道相位，再接模拟输入；保存ILA和Raw。']],[95,380])
H('未完成而不能省略的设计')
P('时钟源、SPI电平转换、两路FDA与抗混叠、AVDD/DRVDD电源、实际封装、34路I/O分配、XDC和信号完整性尚待闭合。不能只把针脚类型改正确，就宣称ADC板已经可投板。独立符号库也没有自动写入旧PCB，避免绕过网表/封装复核。')
H('下游文件的位置')
P('downstream/R51_UNCLOSED/B02~B05保留来源版本；相对库及旧空间模型也一并保留。查看这些文件时，应以UNCLOSED标记和open_items.csv为准，不以文件扩展名判断完成度。')

page('07  B03/B04/B05：下一批闭合任务')
T(['板卡','下一批必须落实','先满足的条件'],[
['B03 PMT/参考','+5PMT与±5AFE、0.5V低噪声偏置、0.5~1.1V控制限制/读回/故障默认、滤波和启动顺序','冻结实际PMT订货型号与工作点；集成HV模块不额外设计裸管千伏电源'],
['B04 电源/禁能','真实输入连接器/保险限流/反接浪涌/DC-DC/LDO/支路与状态、独立关光及快门接口','关闭旧J1无焊盘缺口；明确激光使能极性及故障安全状态'],
['B05 运动','TMC2209真实29焊盘逻辑/EP/采样/功率/UART、编码器接收器、限位与温升','实际牵引电机和编码器输出定型；polygon继续由专用总成驱动'],
['共通','元件级原理图、MPN/封装、供电/地回路、PCB布局布线、ERC/DRC、台架','不可用全passive符号、功能方块或AI截图替代']],[66,235,174])
H('保持工程分工')
P('同步接收、光电采集与运动板有依赖，但不必等整机机箱完成后再做试验。B06/B07先证明事件质量，B01/B08先证明电流—电压链；随后使用真实数据确定B02带宽和工作范围，再闭合B03/B04电源与保护、B05真实电机接口。')
P('安全链不能只依赖FPGA“正常”标志。开盖、失扫或控制异常的默认关光需要实际硬件与整机验证；本包未完成相关安全认证，也没有提供绕过互锁的方法。')
H('每个AI任务的退出物')
P('修改清单与源文件、数据手册版本、引脚审查表、实际运行日志、未运行项、未关闭风险、试验数据路径。实施AI与审查AI不能相互确认后跳过原生工具和实测；人工负责采购/台架/发布批准。')

page('08  台架证据：有协议，没有假结果')
P('本次bench目录提供14项试验方法、执行记录模板和同步时间戳模板。所有测量值留空、状态为NOT_RUN。等效模型、测试模板和示波器插图都不属于台架证据。')
T(['顺序','具体检查','必须留下'],[
['TB01~02','无电/限流供电，PD与IC方向，3.3V/偏置/阈值/电流，上电毛刺','照片、导通表、电源与示波器Raw'],
['TB03~06','实际反偏和输入C、已标定电流、光幅度时间偏移、双/漏脉冲','前沿/后沿/幅度/参考时刻/温度/异常完整记录'],
['TB07~09','不接PMT先测TIA极性/DC、补偿/阶跃、受控过载恢复','注入电路与校准、频响和恢复曲线'],
['TB10~11','参考通道带宽/延迟；B02完成后SPI测试码及数据完整性','带版本的参数、ILA、原始采样'],
['TB12~14','后续电源与互锁、电机耦合、最终光电小台架','故障响应、遥测、重复扫描Raw，不先填PASS']],[65,220,190])
H('接线和测量的边界')
P('先在无激光、无PMT、无开发板条件下验证低压台架。发生器50Ω输出不能直接挂PMT求和节点；注入电阻/校准电流源及探头电容应计入测试说明。接口电平、方向、接地或绝对最大额定值未确认时停止接线。')
P('实物激光必须维持遮光和硬件互锁；板卡模型不提供安全防护保证。不得将导出的模型波形写入实测栏。每次试验要带仪器校准、板卡序列号、原理图/PCB哈希、实装BOM差异和完整Raw路径。')
H('判定原则')
P('数值模型PASS与产品性能PASS分开；固定幅度重复抖动RMS与扫幅确定性偏移峰峰值分开；没有实际光脉冲数据时，中心法只能作为待验证方案。')

page('09  文件、复算和本机验证')
T(['入口','用途'],[
['electronics/projects/B06','先打开B06_G2E01.kicad_pro，再看B07/B08/B01；完整解压保留相对库。'],
['tools/design_circuits.py','本批电路生成的权威源；手工修改KiCad后应先明确权威性，禁止盲目重建覆盖。'],
['engineering/','针脚/网名/MPN候选/接口/位置/18项未关闭问题；CSV为设计数据，不替代项目正式试验台账。'],
['simulations/results','可复算CSV、NPZ、summary.json与运行环境；全部是模型数据。'],
['simulations/spice','3个通用有限运放TIA网表；非厂家宏模型，SPICE引擎本次未执行。'],
['evidence/','35测试日志、文字图网络回读、模型及工具状态；NOT_RUN不会自动改成PASS。']],[143,332])
for s in ['python simulations/run_models.py','python tools/check_native_graph.py','python tools/run_checks.py','python tools/native_validate.py --kicad-cli "实际路径/kicad-cli"'] :P(s,'code')
P('native_validate会调用真实KiCad ERC/DRC及原理图PDF导出；有ngspice时运行网表并保留日志。工具不存在就记录NOT_RUN。未布线PCB的未连接项是预期阻塞，不能通过删除规则伪造通过。[V09]')
P('本次35项Python测试及独立网络回读通过，证明的是特定结构/模型/连接关系；没有运行KiCad、LTspice/ngspice、厂家宏模型、台架和整机资格验证。制造状态一直为BLOCKED。')

page('10  原厂依据、追溯与发布边界')
P('以下来源在2026-11-16核对；针脚图已做目视核对。库中保留原厂定位与选用条件，原PDF不随包再分发。','small')
for src in json.loads((R/'reference/vendor_source_register.json').read_text()):
 P(f"<b>[{src['id']}] {html.escape(src['part'])}</b> · {html.escape(src['locator'])}",'small')
 P(f'<link href="{html.escape(src["url"],quote=True)}">{html.escape(src["url"])}</link>','small')
P('[V09] KiCad官方CLI文档：ERC、DRC和PDF导出。','small')
P('<link href="https://docs.kicad.org/9.0/en/cli/cli.html">https://docs.kicad.org/9.0/en/cli/cli.html</link>','small')
H('发布声明')
P('本交付为可继续编辑、审查和开展台架的电路候选。文件存在不等于电路闭合；仿真有结果不等于实物通过；封装框不等于真实连接器空间；测试脚本通过不等于可制造。没有Gerber、生产坐标发布、烧录文件或自动上电脚本。')
P('后续制造放行必须关闭：原生检查、关键器件/插座定型、G1传感器位置、实际布线回流、厂家模型/台架、接口/电源/安全链及受控版本批准。详见18项open_items.csv。')

pdf=SimpleDocTemplate(str(D/'ZL80_G2E01_设计说明与证据.pdf'),pagesize=A4,rightMargin=40,leftMargin=40,topMargin=40,bottomMargin=50,title='ZL80 G2-E01 电路闭合候选交付',author='ZL80 Engineering')
pdf.build(story,onFirstPage=footer,onLaterPages=footer)
print('Guide PDF generated')
