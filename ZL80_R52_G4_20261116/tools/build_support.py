from pathlib import Path
import json,csv,math,shutil
from pcb_geometry import ROOT,load,pads_for
from build_mcad import pointworld

def put(path,s):p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf8')
def tab(path,rows):
 p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',encoding='utf-8-sig',newline='') as f:
  if rows:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main():
 D,F,P=load();T={t['board']:t for t in json.loads((ROOT/'engineering/board_transforms.json').read_text())};a=json.loads((ROOT/'validation/results/copper_audit.json').read_text())
 sources=[
 ('V_G4_01','OPA356 datasheet','https://www.ti.com/lit/ds/symlink/opa356.pdf','SOT23 pin definition, feedback and supply layout guidance'),
 ('V_G4_02','TLV3501 datasheet','https://www.ti.com/lit/ds/symlink/tlv3501.pdf','Comparator pin definition; propagation delay is not full-system jitter'),
 ('V_G4_03','S5971 datasheet','https://www.hamamatsu.com/content/dam/hamamatsu-photonics/sites/documents/99_SALES_LIBRARY/ssd/s5971_etc_kpin1025e.pdf','p4 package5.4±0.2, sensitive plane2.8, TO18 bottom pin view; optical alignment requires sample'),
 ('V_G4_04','Samtec TMS-104-02-L-S','https://www.samtec.com/products/tms-104-02-l-s','4 pins,1.27mm pitch,.46mm square post; mating assembly still TBD'),
 ('V_G4_05','Samtec TMS-S footprint','https://suddendocs.samtec.com/prints/tms-s%20footprint-mkt.pdf','Recommended finished hole0.66mm'),
 ('V_G4_06','KiCad CLI9 reference','https://docs.kicad.org/9.0/en/cli/cli.html','sch erc, pcb drc, netlist/STEP; commands must run in actual installed app'),
 ('V_G4_07','KiCad PCB file format','https://dev-docs.kicad.org/en/file-formats/sexpr-pcb/','Candidate file syntax; text parse is not native validation')]
 tab('sources/source_register.csv',[dict(id=i,title=t,url=u,use=s,retrieved='2026-11-16',type='OFFICIAL_PRIMARY') for i,t,u,s in sources])
 statuses=[]
 for bid in ['B01','B02','B03','B04','B05','B06','B07','B08']:
  ar=next((v for v in a if v['board']==bid),None)
  statuses.append(dict(board=bid,schematic='G2_TOPOLOGY_INHERITED' if ar else 'G2_NOT_CLOSED',pcb='ROUTED_CANDIDATE' if bid in ['B06','B07','B08'] else ('CRITICAL_NETS_ONLY' if bid=='B01' else 'R51_UNCLOSED_REFERENCE'),segments=ar['segments'] if ar else None,vias=ar['vias'] if ar else None,unconnected_min_links=ar['unconnected_min_links'] if ar else None,native_erc='NOT_RUN',native_drc='NOT_RUN',bench='NOT_RUN',release='BLOCKED'))
 tab('engineering/board_status.csv',statuses)
 stack=[dict(layer=n,type=ty,thickness_mm=t,status='FAB_STACKUP_TBD') for n,ty,t in [('F.Cu','Copper',.035),('D1','FR4',.18),('In1.Cu','GND copper',.035),('D2','FR4',1.10),('In2.Cu','Signal/power copper',.035),('D3','FR4',.18),('B.Cu','Copper',.035)]]
 tab('engineering/stackup.csv',stack)
 interfaces=[];conn=[]
 for c in P:
  bid=c['board'];t=T[bid]
  if not c['ref'].startswith('J'):continue
  for p in pads_for(bid,P,F):
   if p['ref']!=c['ref']:continue
   xyz=pointworld(p['x'],p['y'],1.6 if c['side']=='F' else 0,t)
   interfaces.append(dict(board=bid,connector=c['ref'],pin=p['pin'],net=p['net'],local_x_mm=p['x'],local_y_mm=p['y'],world_x_mm=round(xyz[0],4),world_y_mm=round(xyz[1],4),world_z_mm=round(xyz[2],4),electrical_level='3.3V_SYNC_NOT_1.8V_DIRECT' if p['net']=='SYNC' else 'SEE_G2_INTERFACE;VERIFY_SUPPLY_AND_DIRECTION',mating='TBD'))
  xyz=pointworld(*c['pcb_xy'],1.6+F[c['fp']]['z'],t)
  conn.append(dict(board=bid,connector=c['ref'],tip_world_mm=xyz,pull_direction=t['n'],budget_pull_mm=10,mpn=c.get('mpn',''),status='MATE_AND_CABLE_TBD'))
 tab('engineering/connector_pin_world.csv',interfaces);put('engineering/connector_clearances.json',json.dumps(conn,ensure_ascii=False,indent=2))
 # Explicit updates to the inherited path endpoints; do not silently claim smooth sweep clearance.
 h=json.loads((ROOT/'sources/inherited/G3_harness_routes.json').read_text());updates=[]
 for c in conn:
  if c['connector']=='JPMT1':continue
  pos=c['tip_world_mm'];t=T[c['board']];end=[pos[i]+20*t['n'][i] for i in range(3)]
  updates.append(dict(id=c['board']+'_'+c['connector'],start_world_mm=pos,service_point_mm=end,service_lead_mm=20,mating_connector='TBD',route_status='ENDPOINT_ONLY;CONNECT_TO_G3_CORRIDOR_AFTER_CONNECTOR_FREEZE'))
 put('engineering/harness_endpoints.json',json.dumps(updates,ensure_ascii=False,indent=2));put('engineering/harness_G3_corridors.json',json.dumps(h,ensure_ascii=False,indent=2))
 changes=[
 ('ECR-G4-01','B06/B07探测器中心','分别改为板坐标(15,4)、(3,4)；B07封装旋转180°','恢复名义世界X=-46/+46、Z=112；感光面Y需G1重新对光','G1/G2/G3','PROPOSED'),
 ('ECR-G4-02','XZ板面与PMT针脚映射','B01/B08局部v=-Z,n=+Y；B06/B07局部v=+Z,n=-Y','建立右手坐标；B01八针仅X/Z重合，不证明插座配合','G2/G3','PROPOSED'),
 ('ECR-G4-03','反馈和去耦尺寸/板面','关键RC改0402候选；C6/C7在背面；B08运放背装','减小回路；可焊性、清洗泄漏、电容偏压和真实MPN仍待审核','G2','PROPOSED'),
 ('ECR-G4-04','小板J1','采用Samtec TMS-104-02-L-S候选；成品孔0.66mm','替代未定型1.27mm连接器；对接件和防反插未定','G2/G3','PROPOSED'),
 ('ECR-G4-05','B01/J2位置','从本轮初排(14,35)改(10,37)','消除假设10mm插拔走廊与PMT本体相交；仍需真实对接件验证','G2/G3','PROPOSED'),
 ('ECR-G4-06','铜层与叠层','四层1.6mm候选；.15mm线宽/.15mm间距；.60/.30mm过孔','小板逐网铜连；In1地平面尚未原生填充；不是阻抗承诺','G2','PROPOSED')]
 tab('engineering/change_register.csv',[dict(id=i,item=j,change=c,rationale=r,affected=f,status=s) for i,j,c,r,f,s in changes])
 issues=[
 ('G4-01','P0','KiCad原生解析/ERC/DRC未执行','实际安装软件打开、补全库、填铜、重算、关闭全部错误与合理审查警告','NOT_RUN'),
 ('G4-02','P0','B01仍有43条最少待连接关系/14个网络','完成供电、FDA、偏置、输出滤波、PMT控制布线，并重新执行电气/三维审查','OPEN'),
 ('G4-03','P0','B02—B05电路未闭合','先补B03台架供电/偏置，再完成ADC、硬件禁能、运动接口；不能全机上电','OPEN'),
 ('G4-04','P0','PMT插座型号与8处针脚接合未确认','取得插座MPN和厂家图纸、确认孔径/插深/绝缘及镜像；包络相交仅是配合占位','OPEN'),
 ('G4-05','P1','SOS/EOS感光面与封装底视图仍需复核','G1名义X/Z回归；实物极性、窗口面位置、正反面装配与姿态量测','OPEN'),
 ('G4-06','P1','G2幅度时间偏移仍未关闭','执行恒幅抖动与变幅时间偏移两类实测；不能把布线变化当成同步通过','OPEN'),
 ('G4-07','P1','B01高跨阻带宽/整定仍未关闭','厂家模型与注入电流台架、频响/阶跃/MTF验证；不以自编模型冒充SPICE','OPEN'),
 ('G4-08','P1','接插件对接件/防反插/弯曲半径未定','替换假设10mm插拔走廊，真实线束扫掠并复查短路与维护路径','OPEN'),
 ('G4-09','P1','铜皮未填与回流未验证','原生填充并检查参考面连续、切分、过孔返回；不得仅看断网为零','OPEN'),
 ('G4-10','P1','0402/低pF寄生与清洗残留','厂家封装/公差/偏压核验、焊接与污染样件；反馈值用实测修正','OPEN'),
 ('G4-11','P1','B06/B07单端SYNC与SP2电平/端接','确认3.3V接收域、线长、回流、串扰和边沿；禁直接接1.8V输入','OPEN'),
 ('G4-12','P1','丝印/装配层/制造公差未完成','原生补极性/定位丝印，板厂DFM及元件真实高度/公差审查','OPEN')]
 tab('engineering/open_issues.csv',[dict(id=i,priority=p,issue=x,closure=e,status=s) for i,p,x,e,s in issues])
 benches=[
 ('G4-T01','原生打开与重新保存','四块工程均打开重算；比较网表、封装和3D方向；记录工具版本/哈希','无解析丢失；差异逐项解释'),
 ('G4-T02','ERC/DRC/原理图一致性','先填铜；执行命令与GUI复核；不可忽略未连接、孤岛和禁布区','错误为零且警告经评审；本轮B01预期不通过'),
 ('G4-T03','小板供电与上电静态','先断开激光与SP2；确认供电后限流上电；记录电压、静态电流、温升','器件绝对额定不触及；工作值由G2及批准台架方案冻结'),
 ('G4-T04','静态阈值和极性','注入已知等效光电流并示波器查看TIA/比较器输出','极性、阈值、迟滞与候选电路一致；数值门限待审'),
 ('G4-T05','恒幅同步抖动','受控光脉冲/电流脉冲，重复记录输入参考与SYNC时间戳','统计RMS/峰峰值；比较G1分配后的预算，不使用典型传播时间代替'),
 ('G4-T06','变幅时间偏移','固定位置与形状、改变幅度；同时记录前沿/后沿/中心','确认真实pulse不对称和noise；分开报告时间偏移与随机抖动'),
 ('G4-T07','B08参考链线性与噪声','稳定输入电流、暗输入、频率扫描','先确认供电、幅度和带宽范围；保存Raw波形，不剪裁负值'),
 ('G4-T08','G3板卡安装/插拔','用真实板/对接件/线束检查固定、插深、正反面和工具空间','不碰PMT/辊系；可拆装且不移动光学基准'),
 ('G4-T09','G1光学对位','按感光面坐标而不是外壳顶面调整；验证SOS/EOS全幅','名义92mm标记不等于实测扫描边界；重新校准'),
 ('G4-T10','电机与电源干扰','模拟台架通过后才加电机负载；分步比较静态/运动噪声','保留每步原始数据，不能归因未测的干扰'),
 ('G4-T11','反馈寄生/清洗','厂家模型与样板注入试验，比较反馈RC和清洗前后','闭合带宽、过冲、泄漏、噪声预算'),
 ('G4-T12','制造放行评审','完整BOM/封装/台架/原生/DFM/MCAD证据与同一版本绑定','人工批准后另发制造包；当前BLOCKED')]
 tab('validation/test_matrix.csv',[dict(id=i,test=t,method=m,criterion=c,status='NOT_RUN',measured='',evidence='') for i,t,m,c in benches])
 tab('validation/templates/measurement_log.csv',[dict(test_id='',run_id='',date='',board_serial='',board_revision='',source_hash='',instrument='',calibration='',stimulus='',voltage_v='',current_ma='',temperature_c='',time_ns='',noise_rms_v='',raw_path='',operator='',result='NOT_RUN')])
 # Route inventory, analytical DC resistance only; no fabricated field extraction.
 rr=[]
 for b in D['boards']:
  bid=b['id'];r=json.loads((ROOT/'engineering'/f'{bid}_routing.json').read_text());nets=sorted({x['net'] for x in r['tracks']})
  for net in nets:
   le=sum(math.dist(p,q) for v in r['tracks'] if v['net']==net for p,q in zip(v['points'],v['points'][1:]));rr.append(dict(board=bid,net=net,total_branch_length_mm=round(le,5),track_width_mm=.15,copper_thickness_mm=.035,via_count=sum(v['net']==net for v in r['vias']),note='TOTAL_BRANCH_LENGTH_NOT_POINT_TO_POINT;NO_PARASITIC_OR_IMPEDANCE_PROOF'))
 tab('engineering/route_inventory.csv',rr)
 tab('engineering/component_BOM_review.csv',[dict(board=c['board'],ref=c['ref'],value=c['value'],package=c['fp'],side=c['side'],mpn=c.get('mpn',''),status='CANDIDATE' if c.get('mpn','') else 'MPN_TBD',source=c.get('source','')) for c in P])
 put('cad/freecad/import_G4.FCMacro','''# Run in a new FreeCAD session. Imports STEP review assembly; no parametric feature history.
from pathlib import Path
import FreeCAD as App
import Import
root=Path(__file__).resolve().parents[2]
p=root/'cad/assemblies/ZL80_G4_G3_Integration.step'
doc=App.newDocument('ZL80_G4_Review')
Import.insert(str(p),doc.Name)
doc.recompute()
out=root/'cad/assemblies/ZL80_G4_Review.FCStd'
if out.exists():
    raise RuntimeError('Refusing overwrite: rename existing FCStd first')
doc.saveAs(str(out))
Gui.activeDocument().activeView().viewAxonometric()
Gui.activeDocument().activeView().fitAll()
''')
 put('requirements.txt','numpy>=1.26\nshapely>=2.0\ncadquery>=2.5\nreportlab>=4\n')
 put('AGENTS.md','''# ZL80 G4 AI engineering contract
Do not change the polygon/film/cavity/PMT architecture. G4 is a review candidate, not manufacture.
Read sources/inherited and engineering/change_register.csv before edits. One working agent per branch.
No fake MPN, vendor macro-model, bench waveform, native-ERC/DRC result or hardware bitstream.
Never waive warnings to make a release green. No energized test when interface is unresolved.
Regenerate source and exports together. Run native tool and package checks separately.
B01 incomplete and B02–B05 unclosed. Planes unfilled until KiCad. Every measured result must have Raw path and serial/revision.
''')
 put('tools/rebuild_candidates.py','''from pathlib import Path
import subprocess,sys
R=Path(__file__).resolve().parents[1]
for s in ['prepare_design.py','route_candidates.py','build_ecad.py','audit_pcb.py','build_mcad.py','build_support.py']:
    subprocess.run([sys.executable,str(R/'tools'/s)],cwd=R,check=True)
print('Candidates rebuilt. Native validation and manual review still required.')
''')
 print('Support records written')
if __name__=='__main__':main()
