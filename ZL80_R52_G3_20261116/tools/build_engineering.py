"""Regenerate calculation evidence and engineering registers. No measured result is invented."""
from pathlib import Path
import json,csv,math,itertools,statistics,hashlib
R=Path(__file__).resolve().parents[1];p=json.loads((R/'config/mechanical_parameters.json').read_text())
def writecsv(name,headers,rows):
 with open(R/name,'w',encoding='utf-8-sig',newline='') as f:w=csv.writer(f);w.writerow(headers);w.writerows(rows)
D=p['roller_diameter'];circ=math.pi*D;q=circ/(p['encoder_ppr']*p['quadrature']);spring_force=p['spring_k_N_mm']*(p['spring_free_length']-p['spring_installed_length'])*2;nip=spring_force+p['upper_moving_mass_kg_assumed']*p['gravity_m_s2']
alpha=p['acceleration_m_s2']/(D/2000)
loadtorque=p['design_pull_force_N']*D/2000+p['drag_torque_Nm']+p['reflected_inertia_kg_m2']*alpha
Treq=loadtorque*p['torque_safety_factor']
mode=[]
for rpm in p['calculation_rpm']:
 for pitch in [25,50,100]:
  fl=p['poly_facets']*rpm/60;v=fl*pitch/1000;vx=4*math.pi*p['EFL_mm']*rpm/60
  mode.append([rpm,pitch,fl,v,v/circ*60,v/circ*200*p['microsteps'],80*1000/pitch,80/vx*1e3,pitch/1000/vx*1e6,1000/v])
writecsv('engineering/speed_modes.csv',['polygon_rpm','pitch_um','line_Hz','feed_mm_s','roller_rpm','STEP_Hz_at_16micro','pixels_per_80mm','active_window_ms','pixel_dwell_us','seconds_per_m'],mode)
traction=[]
for normal,mu,tension in itertools.product([2,4.1,6],[.15,.3,.5],[.2,.5,1]):traction.append([normal,mu,tension,normal*mu,(normal*mu)/tension,'SCREEN_ONLY_NOT_MEASURED'])
writecsv('engineering/traction_sensitivity.csv',['nip_normal_N','assumed_mu','web_tension_N','friction_limit_N','ratio','evidence'],traction)
# Euler-Bernoulli stepped steel mandrel deflection (simple supports, distributed estimated nip-normal face load).
N=2880;L=.144;dx=L/N;E=193e9;F=nip;xs=[i*dx for i in range(N+1)];curv=[]
for x in xs:
 # load distributed from x=.022 to .122, totalF; reactionsF/2.
 M=F/2*x-F/.1/2*max(0,x-.022)**2+F/.1/2*max(0,x-.122)**2
 xc=x-.072;diam=.014 if abs(xc)<=.05 else .0074 if abs(xc)<=.07 else .006
 I=math.pi*diam**4/64;curv.append(M/(E*I))
slope=[0.];defl=[0.]
for i in range(1,N+1):
 slope.append(slope[-1]+(curv[i]+curv[i-1])/2*dx)
 defl.append(defl[-1]+(slope[i]+slope[i-1])/2*dx)
corr=defl[-1]/L;defl=[y-corr*x for x,y in zip(xs,defl)];beam_um=max(abs(v) for v in defl)*1e6
# Gap stack: supported film bottom to slit lip; candidate +/- limits treated as halfwidth, not measured sigma.
stack=[['base-to-roller datum','机架加工／配磨',.020,1],['bearing center residual','轴承／定位',.010,1],['loaded radius residual','包胶磨削及负载标定',.010,1],['collector saddle residual','鞍座/垫片调整',.020,-1],['slit lip height residual','薄唇/筒体接口',.020,-1]]
wc=sum(abs(x[2]*x[3]) for x in stack);rss=math.sqrt(sum((x[2]*x[3])**2 for x in stack))
summary={'evidence':'ANALYTICAL_CANDIDATE_NOT_BENCH','revision':p['revision'],'encoder_quantum_um':q*1000,'encoder_angle_accuracy_equivalent_um':math.pi*D*p['encoder_accuracy_deg']/360*1000,'full_step_um':circ/200*1000,'microstep16_um':circ/(200*16)*1000,'spring_force_per_nip_N':spring_force,'upper_weight_N_ASSUMED':p['upper_moving_mass_kg_assumed']*p['gravity_m_s2'],'nip_normal_force_N':nip,'friction_limit_N_at_assumed_mu':nip*p['mu_assumed'],'nominal_web_tension_N':p['web_tension_target_N'],'torque_before_factor_Nm':loadtorque,'design_torque_Nm':Treq,'holding_torque_to_required_ratio_INSUFFICIENT_FOR_SELECTION':p['motor_holding_torque_Nm']/Treq,'motor_dynamic_torque_evidence':'NOT_RUN','coupling_twist_equivalent_um':loadtorque/p['coupling_torsional_stiffness_Nm_rad']*(D/2)*1000,'shaft_max_deflection_um_simple_beam':beam_um,'steel_E_GPa_assumption':193,'gap_nominal_mm':109.9-p['slot_top_z'],'gap_stack_wc_mm':wc,'gap_stack_rss_HALF_WIDTH_NOT_SIGMA_mm':rss,'gap_min_candidate_mm':.5-wc,'gap_max_candidate_mm':.5+wc,'film_midplane_thickness_shift_min_mm':(.15-.2)/2,'film_midplane_thickness_shift_max_mm':(.35-.2)/2,'traction_margin_vs_design_pull':nip*p['mu_assumed']/p['design_pull_force_N'],'normal_force_for_2x_design_pull_N':2*p['design_pull_force_N']/p['mu_assumed'],'base_to_film_z':110,'encoder_target_5um':'NOT_CLOSED','tension_control':'external low-tension supply / bench force reference; inlet idler not a closed-loop tension actuator','bench_status':'NOT_RUN'}
(R/'validation/results/calculation_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
writecsv('engineering/tolerance_stack.csv',['term','meaning','halfwidth_mm','signed_sensitivity'],stack)
writecsv('validation/results/shaft_deflection_MODEL.csv',['x_from_left_support_mm','deflection_um'],[[x*1000,y*1e6] for x,y in zip(xs[::20],defl[::20])])

selection=[
['SEL01','出口牵引电机','14HS10-0404S','1','35.2×35.2×26；5轴长20.5；0.4A；保持0.14Nm','S01','候选/低速台架验证','0.045Nm动态需求需实测；保持转矩不能替代运行转矩；电流限幅由B05闭合','同安装接口更低转矩脉动电机：RFQ'],
['SEL02','辊轴轴承','NMB L-1260ZZ','8','6×12×4；Cr831N；C0r363N','S02','候选/样品批准','精度等级/润滑/游隙/启动阻力；严禁只按MR126族名称替代','必须复核宽度：部分MR126公开型号宽3，不是4'],
['SEL03','柔性联轴器','NBK MJC-20CS-WH-5-6','1','外径20；总长30；两端孔5/6；静扭转刚度29Nm/rad','S03','候选/机械接口重排','与旧16长占位不互换；对中目标0.03mm/0.1deg为本设计建议','低回差金属膜片/波纹管，需重新验接口'],
['SEL04','位置编码器','Same Sky AMT112S＋6mm套','2','5V CMOS A/B/Z；4096PPR需配置；0.2deg精度','S04','PoC候选，不满足5um宣称','量化3.835um≠准确度；按轴向/负载标定并以独立位移参考验收','高准确度编码器/直接片面测量 RFQ'],
['SEL05','低辊定位轴环','Ruland MCL-6-A','2','6孔；16外径；9宽；旋转扫掠20.8','S05','候选','移到X=-83.6；上辊改用M5锁紧，避免两只大轴环相撞','自制小直径轴环须重新计算夹紧力'],
['SEL06','上辊弹簧','RFQ-SPR-05-018-050','4','自由18；工作13.9；OD<=5；k0.5N/mm；压并<=7.5','D01','规格询价未定MPN','k±10%；刚度/并圈/疲劳/端面方正实测','弹簧材质与线径由厂家设计'],
['SEL07','上辊材料A','PU 50±5 Shore A','4试样','整辊粘结后磨削；不得散套打滑','U03/D01','DOE','擦拭残留、磨耗、静电、压痕、划伤实测','硅胶/防静电PU并行'],
['SEL08','上辊材料B','后硫化硅胶50±5 Shore A','4试样','批次/后硫化记录；整辊磨削','U03/D01','DOE','游离物/粘污风险必须实际验证','不能以硅胶材料名称宣称无污染'],
['SEL09','电机驱动接口','B05/TMC2209继承候选','1','24V母线；STEP/DIR/EN；相电流0.4A起点','G2-E01','电路未闭合','具体限流/模式/温升、信号电平、故障关断需G2关闭','禁止直接采购空PCB上电'],
['SEL10','张力测量','0~5N测力台架/标定砝码','1','建议扩展不确定度<=0.02N；不纳入主机结构冻结','D01','台架待采购','用于独立张力证据，不能用弹簧预压推算张力','产品内张力闭环另行RFQ'],
['SEL11','上辊释放检测','NC机械行程开关','1','沿用R5空间；触发/复位行程待测','U02','接口候选','未锁紧时禁驱动/禁光；安全功能需独立评审','不能用软件状态替代机械位置'],
['SEL12','机箱面板','5052-H32 平板1.5mm','6','螺接角撑；没有折弯；接口片可替换','D01','DFM前审查','切口去毛刺、导电接地点、遮光迷宫；板厚减薄需刚度测试','保留2mm旧稿对照，不混用重量']]
writecsv('engineering/selection.csv',['id','function','candidate','qty','known_dimensions_specs','source','status','release_blocker','alternative_note'],selection)

tols=[
['T01','G3-M01','基准A上面','300×288','平面度0.05mm；局部装调区0.02mm','研磨/精铣后测量','建议，待工艺确认'],
['T02','G3-M02/L','下辊中心高度','Z99.900','装配后相对片面基准±0.020mm；可配磨脚垫','高度规/坐标测量','不以单零件公差代替装配结果'],
['T03','G3-R01/02/03','轴承配合段','φ6','6.000~6.004mm候选；过盈/游隙经厂家批准后冻结','千分尺+轴承实测','当前不可按此批量压装'],
['T04','G3-M02/M04','轴承外圈座','φ12','12.000~12.010mm候选','气动量仪/塞规','左右台阶深度分别定位/游动'],
['T05','G3-R01/02','编码器/联轴器轴端','φ6','5.988~6.000mm；安装处不涂覆','千分尺','与厂家推荐轴公差复核'],
['T06','G3-R04装配','工作外径','φ20','磨削后20.000±0.010mm；加载有效径单独标定','双截面测径+加载标定','几何直径不直接当编码尺长'],
['T07','G3-R04装配','辊面径向跳动','工作面100','相对两轴承基准总跳动<=0.010mm候选','慢转V块/实装表测','轴承运行跳动和胶层压陷不包含'],
['T08','四辊总成','上下辊平行度','100面长','<=0.020mm/100mm候选','两端间隙/压力膜','负载下核验，不损伤胶片'],
['T09','四辊总成','两下辊相对平行','84中心距','<=0.020mm/100mm候选','基准轴/坐标测量','片道蛇行仍需长片实测'],
['T10','G3-M04','滑块Y宽与槽','18.00/18.15','槽18.150±0.025；块18.000±0.025','塞规+自由下落/回差','总间隙0.10~0.20；释放不可卡滞'],
['T11','左定位轴承','轴向端隙','4mm轴承','测量后垫片调整至0.02~0.05mm候选','百分表轴向推拉','不能用拧紧压盖预紧所有轴承'],
['T12','右游动轴承','轴向浮动余量','名义0.40mm','装配后0.20~0.50mm','推拉测量','覆盖热膨胀；不得胶粘锁死'],
['T13','电机联轴器','两轴对中','5/6轴','偏心<=0.030mm；偏角<=0.1deg建议','表测或激光对中','厂家允许极限不是验收目标'],
['T14','导光/片口接口','片底至狭缝','0.5mm','调整后0.40~0.60mm建议；厚度范围单独验证','薄膜规/非接触位移','不得接触刮片'],
['T15','槽唇与扫线','Y向中心','Y0','装调残差±0.10mm起点','扫描靶+功率响应','G1光学角度/光斑仍需验证'],
['T16','钣金外壳','面板轮廓/孔','1.5板厚','外形±0.20；普通孔位±0.15mm建议','卡尺/检具','基准孔另行标注，不套用同公差'],
['T17','所有胶片接触件','边缘与表面','按图','不得有毛刺/锐边/残胶；胶层纹理初轮不加','显微镜+擦拭+前后片对比','Ra不能替代无划伤试验']]
writecsv('engineering/critical_tolerances.csv',['id','part','feature','nominal','proposed_requirement','verification','boundary'],tols)

# Explicit differences to prevent silent mixing of model versions.
changes=[
['CR01','联轴器','旧OD16×16L占位','NBK候选OD20×30L；X96；电机前面X121.5','轴端/支架/护罩重做','待接口签署'],
['CR02','辊芯','Ø14和Ø6简单组合','增加Ø7.4肩段、定位端与编码器延长端','R01/R02/R03不可混用','待加工评审'],
['CR03','包胶','自由可换套假设','候选粘结/硫化后整辊磨削；更换整辊','避免胶套相对轴滑移','材料工艺待实测'],
['CR04','片道侧框','6mm及简单孔','8mm台阶孔、浮动槽、弹簧/提辊通道、定位脚','保持X±72、Y±42、片面Z110','静态实体审查已运行'],
['CR05','夹紧力','未定义','弹簧贡献4.1N/组；加0.2kg移动质量假设后约6.06N/组，必须测力','不是纵向张力','未实测'],
['CR06','编码器','仅PPR量化','加入原厂0.2deg精度；等效约34.9um','5um运动预算尚未闭合','需更换/标定/独立测量'],
['CR07','外壳','2mm未展开板','六块1.5mm平板＋角撑；均有切割DXF','无折弯补偿；未宣称刚度达标','DFM待做'],
['CR08','驱动分工','前稿文字含双驱动建议','当前一台出口电机＋入口测量随动辊','上片/外置收卷与扫描计量解耦','张力执行器未冻结'],
['CR09','线束','继承W11重复编号','去重；明确分区和电平接口；保留原始JSON','没有伪造针脚表','G2 B05未闭合'],
['CR10','G2板卡','R5板框＋G2新占位','分别打包，未默认为元件方向一致','XZ板法向/导入旋转需原生回装确认','整机ECAD闭环仍BLOCKED']]
changes.append(['CR11','基座后排孔与脚孔','旧280深基座，B04后孔Y139开边；脚孔贴近B03孔','基座深288；脚孔改X±132/Y±120','保持四辊/光学/板卡坐标，重新生成所有孔；旧DXF作废','需G0接口签署'])
writecsv('engineering/change_register.csv',['id','subject','before','after','impact','status'],changes)

# Deterministic material-screen matrix. Randomised specimen/run order must be recorded by operator.
doe=[]
for i,(mat,normal,speed) in enumerate(itertools.product(['PU50A','post_cured_silicone50A','ESD_PU50A'],[2,4.1,6],[3,15]),1):
 doe.append([f'MAT-{i:02d}',mat,normal,speed,.2,.2,3,'fresh film then registered aged film','smooth ground; no texture','NOT_RUN','','','','',''])
writecsv('engineering/roller_material_DOE.csv',['id','material','nip_normal_N','feed_mm_s','web_tension_N','film_thickness_mm','replicates','specimen_condition','surface','status','friction_measured','slip_um','scratch_result','residue_result','Raw_path'],doe)
# Actual inherited harness rows deduplicated; changed route to actual G3 motor point.
raw=json.loads((R/'sources/inherited/R51_harness_routes.json').read_text());routes=[];seen=set()
for row in raw:
 if row['id'] in seen:continue
 seen.add(row['id']);r=dict(row)
 if r['id']=='W05':r['points'][-1]=[145,42,100];r['cut_length_budget_mm']=650
 length=sum(math.dist(a,b) for a,b in zip(r['points'],r['points'][1:]));r['length_mm']=round(length,2)
 r['status']='ROUTE_CORRIDOR_NOT_CONNECTOR_PINOUT';routes.append(r)
routes.append({'id':'W12','start':'上辊释放NC开关','end':'B04硬禁能/B05状态','points':[[95,-42,147],[105,-42,160],[125,80,160],[125,120,45],[50,120,40]],'type':'独立常闭互锁回路','diameter':4,'min_bend':12,'cut_length_budget_mm':450,'length_mm':0,'status':'ROUTE_CORRIDOR_NOT_CONNECTOR_PINOUT','notes':'失电/断线禁止驱动与激光；安全等级需评估'})
routes[-1]['length_mm']=round(sum(math.dist(a,b) for a,b in zip(routes[-1]['points'],routes[-1]['points'][1:])),2)
(R/'config/harness_routes_G3.json').write_text(json.dumps(routes,ensure_ascii=False,indent=2))
writecsv('engineering/harness.csv',['id','from','to','type','OD_mm','min_bend_mm_ASSUMED','centerline_mm','cut_budget_mm','status','notes'],[[r['id'],r['start'],r['end'],r['type'],r['diameter'],r['min_bend'],r['length_mm'],r['cut_length_budget_mm'],r['status'],r.get('notes','')] for r in routes])

bench=[
['TB-G3-01','尺寸与轴承配合','测轴/孔/轴承实际尺寸与装配力；左右端隙；每根记录','T01~T12候选表','NOT_RUN'],
['TB-G3-02','辊面跳动/平行','无负载和4.1N负载，各辊慢转三圈；左右/中心读数','总跳动<=10um、平行<=20um/100待签署','NOT_RUN'],
['TB-G3-03','夹紧力标定','逐端测力，记录调压圈数/弹簧压缩；三次装夹','总法向力2/4.1/6N；两端不平衡<=10%建议','NOT_RUN'],
['TB-G3-04','静态牵引/打滑','在无光状态逐渐增加拉力，记录初滑与稳态滑；不用胶片试样反复磨损','mu与正常负载实测；设计牵引1.2N保留余量','NOT_RUN'],
['TB-G3-05','平均速度','独立位移参考与编码器同步采1kHz；加速结束后至少10s，0.5/3/15/30mm/s','平均误差<=1%建议；不以STEP脉冲作独立真值','NOT_RUN'],
['TB-G3-06','位置纹波/几何','保存原始独立位移；报线性拟合残差RMS/频谱，声明带宽；分别报编码器误差','5um RMS目标待批准，AMT角精度风险未关闭','NOT_RUN'],
['TB-G3-07','张力','标定0~5N传感器或独立载荷夹具，扫0.2/0.5/1N；记录上游/下游受力位置','均值误差<=0.1N、RMS<=0.05N建议','NOT_RUN'],
['TB-G3-08','片材厚度与偏斜','0.15/0.2/0.35mm样品，片首/片尾/长片三次；记录蛇行','无卡片；不接触狭缝；实际可扫首尾范围报告','NOT_RUN'],
['TB-G3-09','材料划伤污染','按18组DOE，登记前后显微图、擦拭残留、静电/粉尘；每组3片','零新增可见划伤，显微限值由片材验收签署','NOT_RUN'],
['TB-G3-10','提辊与互锁','断电确认抬升5mm；开盖/提辊/断线/卡死各故障；禁止带光手动放片','NC失效测试通过才准上电','NOT_RUN'],
['TB-G3-11','温升与长期运行','电机4.5~28.6rpm候选，0.4A限流；记录胶辊/板卡/电机温度','温升限值与器件/胶层材料商共同冻结','NOT_RUN'],
['TB-G3-12','线束/连接器维护','实装插头并执行维护拆出；检查USB调试口、弯曲和运动干涉','可插拔；无夹伤/拖曳；实际弯曲半径满足线厂','NOT_RUN'],
['TB-G3-13','机箱刚度/漏光','提手载荷、搬运与重复开盖；无片/窄片/片尾漏光检查','结构与激光安全需专业实测，不从CAD推定','NOT_RUN'],
['TB-G3-14','长片累计误差','独立长度基准1m/10m；记录温度、辊压、单圈标定、无强制图像对齐','报告尺度/局部误差/打滑，不用软件填补丢失','NOT_RUN']]
writecsv('validation/test_matrix.csv',['id','name','method','proposed_acceptance','status'],bench)
writecsv('validation/templates/bench_results_EMPTY.csv',['TestID','date','operator','instrument_id','calibration_id','specimen_id','configuration_hash','raw_path','measured_value','uncertainty','status','reviewer'],[[r[0],'','','','','','','','','','NOT_RUN',''] for r in bench])
writecsv('validation/templates/transport_raw_EMPTY.csv',['time_s','reference_position_mm','inlet_encoder_count','outlet_encoder_count','tension_N','motor_steps','film_present','interlock_ok'],[])
writecsv('validation/templates/material_observations_EMPTY.csv',['run_id','specimen_id','pre_image_path','post_image_path','cycles','residue','scratch','slip','temperature_C','humidity_pct','decision'],[])

# BOM links to exact model geometry, not all imported optical items counted as new mechanics.
parts=json.loads((R/'cad/parts.json').read_text());inst=json.loads((R/'cad/instances.json').read_text())
from collections import Counter
qty=Counter(x['part'] for x in inst)
bom=[[x['id'],x['name'],qty[x['id']],x['material'],x['status'],f'cad/parts/{x["id"]}.step',x['note']] for x in parts if x['id'].startswith('G3-')]
bom += [['HW-OPEN-01','电机/护罩/编码器/机箱其他紧固件','TBD','标准件','NOT_FULLY_MODELED','', '应按装配实物完成长度/防松/扳手空间；不能把当前STEP称为全部标准件已齐全'],['MFG-OPEN-01','端盖垫片、胶辊粘结工艺、传感器安装小件','TBD','工艺件','DFM_REQUIRED','','按台架及签署图补齐']]
writecsv('engineering/mechanical_BOM.csv',['id','name','qty','material','status','model_path','notes'],bom)
register={'params':p,'summary':summary,'selection':selection,'tolerances':tols,'stack':stack,'changes':changes,'doe':doe,'bench':bench,'bom':bom,'routes':routes,'modes':mode}
(R/'engineering/registers.json').write_text(json.dumps(register,ensure_ascii=False,indent=2))
print(json.dumps(summary,ensure_ascii=False,indent=2))
