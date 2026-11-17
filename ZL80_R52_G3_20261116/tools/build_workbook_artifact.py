"""Exact artifact_tool workbook recipe; requires artifact_tool in the local environment."""
from pathlib import Path
import json,csv
from artifact_tool import Workbook,SpreadsheetFile
R=Path(__file__).resolve().parents[1]
regs=json.loads((R/'engineering/registers.json').read_text())
wb=Workbook.create()
navy='#183B56'; teal='#117C83'; light='#EDF4F7'
def col(n):
    s=''
    while n:
        n,a=divmod(n-1,26);s=chr(65+a)+s
    return s
def grid(name,title,headers,rows,widths=None):
    s=wb.worksheets.add(name);nc=len(headers);end=col(nc);n=len(rows)+4
    s.merge_cells(f'A1:{end}1');s.get_range('A1').values=[[title]]
    s.get_range(f'A1:{end}1').format={'fill':navy,'font':{'bold':True,'color':'#FFFFFF','size':15},'row_height':30}
    s.merge_cells(f'A2:{end}2');s.get_range('A2').values=[['R52-G3-M01-D01 | 候选设计 / 非加工放行 | 台架 NOT_RUN']]
    s.get_range(f'A2:{end}2').format={'font':{'size':10,'color':'#9B4C18'},'row_height':24}
    s.get_range(f'A4:{end}4').values=[headers]
    s.get_range(f'A4:{end}{n}').format={'font':{'name':'Microsoft YaHei','size':10},'wrap_text':True,'vertical_alignment':'center','row_height':44}
    s.get_range(f'A4:{end}4').format={'fill':teal,'font':{'bold':True,'color':'#FFFFFF'},'row_height':32}
    if rows:s.get_range(f'A5:{end}{n}').values=rows
    for j in range(nc):s.get_range(f'{col(j+1)}1:{col(j+1)}{n}').format.column_width=(widths[j] if widths else 25)
    for i in range(5,n+1,2):s.get_range(f'A{i}:{end}{i}').format.fill=light
    s.freeze_panes.freeze_rows(4)
    return s
s=grid('使用说明','ZL80 G3｜四辊与机械集成工作簿',['内容','结论／入口','边界'],[
 ['交付范围','四辊STEP、辊芯图、材料DOE、基座/机箱、线束、公差链、验证协议','非量产放行；没有实测数据'],
 ['版本依赖','G0/G1扫描线和积分筒接口 + G2E01电子边界','G2器件朝向/实际接插件仍待回装'],
 ['候选方式','出口单电机牵引；入口随动测量；两下辊编码','不是双驱动张力伺服'],
 ['修改权威源','config/mechanical_parameters.json + cad/source/build_mechanics.py','Excel用于试算；不会回写CAD'],
 ['新接口变更','基座300×288；侧框8厚；NBK联轴器20×30','必须批准ECR再加工'],
 ['编码器风险','4096PPR计数量化不等于位置精度','0.2°原厂角精度约35μm/20mm辊'],
 ['夹紧力','弹簧、移动自重、导向摩擦共同决定法向力','4.1N只是两根弹簧合力'],
 ['张力证据','14项台架协议、18组材料DOE','所有实测栏为空；NOT_RUN'],
 ['软件检查','30项Python测试；STEP形体与局部静态碰撞检查','不等同于FreeCAD重算、全运动、台架合格'],
 ['文件入口','START_HERE.html；docs/；drawings/；cad/','每次正式发布保留哈希/审批/原始数据']], [20,52,47])
params=[
 ['辊直径',20,'mm','继承/加载有效径需标定'],
 ['面长',100,'mm','继承'],
 ['辊芯直径',14,'mm','继承'],
 ['辊距',84,'mm','继承'],
 ['有效片宽',80,'mm','用户要求'],
 ['光学扫描预留',100,'mm','用户要求'],
 ['多面镜面数',6,'面','G1假设'],
 ['f-theta EFL',100,'mm','G1假设/非工作距离'],
 ['编码器PPR',4096,'PPR','S04须配置'],
 ['编码倍频',4,'倍','设计'],
 ['编码器角精度',0.2,'deg','S04'],
 ['电机步距',1.8,'deg','S01'],
 ['微步',16,'细分','试验候选'],
 ['弹簧数量每组',2,'根','设计'],
 ['弹簧刚度',0.5,'N/mm','待询价/测量'],
 ['弹簧自由长',18,'mm','候选'],
 ['弹簧工作长',13.9,'mm','候选'],
 ['移动上辊质量',0.2,'kg','假设，须称重'],
 ['重力加速度',9.80665,'m/s²','计算常数'],
 ['摩擦系数',0.3,'无量纲','假设，须材料试验'],
 ['设计牵引力',1.2,'N','内部预算非片张力'],
 ['标称张力',0.5,'N','台架目标'],
 ['轴系摩擦转矩',0.003,'N m','估算，须实测'],
 ['等效转动惯量',0.000005,'kg m²','估算'],
 ['线加速度',0.05,'m/s²','候选'],
 ['转矩安全系数',3,'倍','内部预算'],
 ['电机保持转矩',0.14,'N m','S01，不是运行转矩'],
 ['联轴器静扭转刚度',29,'N m/rad','S03'],
 ['片底到薄唇',0.5,'mm','继承/调装'],
 ['基座长X',300,'mm','继承'],
 ['基座深Y',288,'mm','本轮变更280→288'],
 ['基座厚',6,'mm','继承'],
 ['片底Z',109.9,'mm','设计基准'],
 ['名义片中面Z',110,'mm','名义t0.2'],
 ['片厚名义',0.2,'mm','验证范围待样片确认']]
ps=grid('参数','计算输入｜蓝色数值为试算输入',['参数','数值','单位','来源／状态'],params,[28,16,17,50])
ps.get_range(f'B5:B{len(params)+4}').format.font.color='#1452A0'
prows={row[0]:i+5 for i,row in enumerate(params)}
def ref(k):return f"'参数'!$B${prows[k]}"
crows=[
 ['计数量化','', 'μm','仅几何周长/计数，未包含精度、压陷和滑移'],
 ['角精度等效位移','', 'μm','原厂角精度换算，不称为RMS'],
 ['全步位移','', 'μm','脉冲位移不等于真实分辨率'],
 ['16微步名义位移','', 'μm','微步非线性和负载需实测'],
 ['弹簧合力','', 'N','每组两根弹簧；未加自重'],
 ['移动件重力','', 'N','0.2kg是假设'],
 ['法向夹紧力估算','', 'N','未包含导向摩擦方向性，须测力'],
 ['摩擦牵引极限','', 'N','μ假设；初滑/稳滑应实测'],
 ['牵引余量倍数','', '倍','本设计希望≥2时仍不足'],
 ['运行转矩预算','', 'N m','拉力+阻力+加速'],
 ['含系数需求转矩','', 'N m','不能用保持转矩直接证明运行通过'],
 ['保持/需求比较','', '倍','仅初筛，动态NOT_RUN'],
 ['变化载荷扭转位移','', 'μm','不是全部系统位置误差'],
 ['达到2倍牵引的法向力','', 'N','不允许未经划伤验证盲目加压'],
 ['片底间隙最坏半宽','', 'mm','确定性容差代数，不包含动态翘曲'],
 ['片底间隙RSS半宽','', 'mm','不是标准差，独立分布尚未证明'],
 ['候选最小间隙','', 'mm','名义-最坏半宽'],
 ['候选最大间隙','', 'mm','名义+最坏半宽']]
cs=grid('计算','预算结果｜全部为模型，不是台架结果',['指标','公式结果','单位','解释'],crows,[31,21,16,60])
forms=[
 f'=PI()*{ref("辊直径")}*1000/({ref("编码器PPR")}*{ref("编码倍频")})',
 f'=PI()*{ref("辊直径")}*1000*{ref("编码器角精度")}/360',
 f'=PI()*{ref("辊直径")}*1000*{ref("电机步距")}/360',
 f'=B7/{ref("微步")}',
 f'={ref("弹簧数量每组")}*{ref("弹簧刚度")}*({ref("弹簧自由长")}-{ref("弹簧工作长")})',
 f'={ref("移动上辊质量")}*{ref("重力加速度")}',
 '=B9+B10',
 f'=B11*{ref("摩擦系数")}',
 f'=B12/{ref("设计牵引力")}',
 f'={ref("设计牵引力")}*{ref("辊直径")}/2000+{ref("轴系摩擦转矩")}+{ref("等效转动惯量")}*{ref("线加速度")}/({ref("辊直径")}/2000)',
 f'=B14*{ref("转矩安全系数")}',
 f'={ref("电机保持转矩")}/B15',
 f'=B14/{ref("联轴器静扭转刚度")}*{ref("辊直径")}/2000*1000000',
 f'=2*{ref("设计牵引力")}/{ref("摩擦系数")}',
 "=SUM('公差链'!C5:C9)",
 "=SQRT(SUMSQ('公差链'!C5:C9))",
 f'={ref("片底到薄唇")}-B19',
 f'={ref("片底到薄唇")}+B19']
cs.get_range('B5:B22').formulas=[[x] for x in forms]
cs.get_range('B5:B22').set_number_format('0.000000')
cs.get_range('B13').conditional_formats.add_cell_is({'operator':'lessThan','formula':2,'format':{'fill':'#FDE9CD'}})
cs.get_range('F4:H7').values=[['指标','计算值','含义'],['计数量化',None,'不等于精度'],['角精度量级',None,'原厂规格换算'],['目标位置RMS',5,'仍未闭合']]
cs.get_range('G5:G6').formulas=[['=B5'],['=B6']]
for cc in ['F','G','H']:cs.get_range(f'{cc}1:{cc}30').format.column_width=19
cs.get_range('F4:H7').format.wrap_text=True
chart=cs.charts.add('bar',cs.get_range('F4:G7'));chart.title_text='位置量级对照（μm；不同统计定义）';chart.set_position('F10','M24')
ss=grid('选型','电机、轴承、联轴器及采购候选',['ID','用途','候选型号','数量','原厂/候选参数','源ID','状态','必须确认','替代边界'],regs['selection'],[12,23,28,9,48,12,28,45,40])
grid('机械BOM','机械BOM｜真实详细度按状态列区分',['编号','名称','数量','材料','详细度','CAD相对路径','说明'],regs['bom'],[16,37,10,18,34,42,55])
grid('关键公差','关键尺寸与验收方法｜未批准制造',['ID','零件','特征','名义','候选公差','测量方式','边界'],regs['tolerances'],[10,22,28,17,50,30,48])
st=grid('公差链','片底—薄唇装配链｜F平面不当加工实体基准',['项','来源','半宽mm','灵敏度符号'],regs['stack'],[38,40,18,18])
st.get_range('C5:C9').set_number_format('0.000')
grid('材料DOE','18组材料与压力筛选｜每组3片，结果留空',['试验ID','材料','实测法向目标N','速度mm/s','张力N','片厚mm','重复数','试片','表面','执行状态','初滑力','划伤','掉屑','残留','结论'],regs['doe'],[14,30,18,16,14,16,12,36,30,18,16,16,16,16,30])
grid('台架测试','走片速度、位置与张力测试协议',['测试ID','项目','方法','候选判据','执行状态'],regs['bench'],[19,28,70,60,18])
grid('变更','与R5/G01/G2接口变更注册表',['ID','对象','旧状态','本轮设计','影响','状态'],regs['changes'],[12,24,44,68,52,28])
with open(R/'engineering/harness.csv',encoding='utf-8-sig') as f: hrows=list(csv.reader(f))
grid('线束','12条线束中心线与检修余量预算',hrows[0],hrows[1:],[16,27,27,30,12,16,18,20,48,55][:len(hrows[0])] if len(hrows[0])<=10 else None)
with open(R/'sources/source_register.csv',encoding='utf-8-sig') as f: srows=list(csv.reader(f))
grid('资料来源','资料依据｜外部参数与内部假设分列',srows[0],srows[1:],None)
# speed scenarios calculated from input columns; no hard-coded outputs
mr=[[m[0],m[1]]+[None]*8 for m in regs['modes']]
ms=grid('扫描与送片','G1行频与G3送片匹配｜单向飞点，所有facet可用假设',['棱镜rpm','采样μm','行频Hz','片速mm/s','辊rpm','16微步Hz','有效像素/行','80mm有效窗ms','驻留μs','秒/米'],mr,[17]*10)
for i in range(5,17):
    ms.get_range(f'C{i}:J{i}').formulas=[[
    f'=A{i}*{ref("多面镜面数")}/60',
    f'=C{i}*B{i}/1000',
    f'=D{i}*60/(PI()*{ref("辊直径")})',
    f'=E{i}*360/{ref("电机步距")}*{ref("微步")}/60',
    f'={ref("有效片宽")}*1000/B{i}',
    f'={ref("有效片宽")}/(2*{ref("f-theta EFL")}*2*PI()*A{i}/60)*1000',
    f'=H{i}*1000/G{i}',
    f'=1000/D{i}']]
ms.get_range('C5:J16').set_number_format('0.000000')
print('created sheets',13,'formula cells',18+2+12*8)
# Recalculate, inspect, and export. artifact_tool is optional for workbook regeneration only.
print(wb.inspect({'kind':'match','search_term':'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A',
 'options':{'use_regex':True,'max_results':30}}).ndjson)
SpreadsheetFile.export_xlsx(wb).save(str(R/'engineering/ZL80_G3_选型BOM公差与验证.xlsx'))
