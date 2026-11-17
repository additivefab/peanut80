from pathlib import Path
import json,csv,hashlib,sys
R=Path(__file__).resolve().parents[1]
def putcsv(path,rows):
 p=R/path;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',newline='',encoding='utf-8-sig') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
issues=[
('E01-01','ALL','原生ERC/DRC未执行','本地运行native_validate.py，逐项审查报告；不靠PWR_FLAG掩盖信号方向错误'),
('E01-02','B06/B07','幅度相关触发偏移未解决','记录前后沿与幅度；全扫描场/光功率范围实测；确认使用前沿、中心或标定修正'),
('E01-03','B06/B07','S5971低偏置特性未知','在~1V反偏测结电容和脉冲；不套用10V条件下100MHz'),
('E01-04','ALL','四块PCB尚未布线','重排关键反馈/去耦/连接器；完成叠层、回流、阻抗及本地DRC后再评审'),
('E01-05','B01','PMT插座孔径/方向/型号未冻结','实际H10720-20+选定插座实物对照；0.9mm孔不能直插1mm PMT引脚'),
('E01-06','B01','高跨阻档带宽与整机MTF未闭合','有限模型100k/2.2p在628kHz仅约0.80相对响应；先台架测阶跃再分配MTF预算'),
('E01-07','B01/B08','缺厂家宏模型及过载恢复证据','获取授权宏模型，核对其引脚顺序；完成大/小信号及饱和恢复'),
('E01-08','B02','AD9268 CMOS/LVDS历史描述冲突','采用并行CMOS候选；重审Bank33=1.8V、32数据+2DCO/时钟能力、SPI转换及回流线'),
('E01-09','B02','时钟/电平转换/抗混叠未完整设计','选真实MPN并审查抖动、模式、寄存器与外部滤波；不是本次已闭合原理图'),
('E01-10','B03','PMT控制/偏置/低噪声电源功能占位','完成+5PMT、±5AFE、0.5V偏置、0.5~1.1V限制/默认值/读回及启动顺序'),
('E01-11','B04','J1无实际焊盘，独立禁能逻辑未闭合','先定连接器及保护器件；硬件缺省关光，故障不依赖FPGA自报正常'),
('E01-12','B05','TMC2209只有29焊盘无完整逻辑针脚','按实际封装核对芯片/EP/电流采样/UART/限位；polygon驱动与牵引驱动分开'),
('E01-13','B06/B07','探测器与接插件位置需要G1同步','B06 D1(14,6),B07 D1(14,7.5)为本地板坐标；不同孔型引起位置变更，未验证装入原机'),
('E01-14','B01','H10720/-21型号和灵敏度资料冲突','针脚式H10720候选；当前厂家PDF的-20灵敏度与旧报告有十倍差异，不直接用于旧光子预算'),
('E01-15','ALL','无实物台架证据','填写带仪器/接线/版本/Raw路径的bench记录；未测不得填PASS'),
('E01-16','ALL','被动件MPN/封装土地模式未放行','确认精度、温漂、耐压、DC偏置、电容有效值、封装及采购可用性'),
('E01-17','B08','参考通道延迟与增益未标定','~160kHz参考链与PMT链同步处理，不能直接同下标相除'),
('E01-18','ALL','安全/EMC/插拔次序未验证','低压限流台架先行；未核对极性/接地不接PMT/ADC/开发板；禁止绕过激光互锁')]
putcsv('engineering/open_items.csv',[dict(id=i,board=b,issue=s,closure_action=a,status='OPEN',owner='待指派',evidence='') for i,b,s,a in issues])
interface=[
('B06/B07','J1','1','5VA_IN','INPUT','外部5V','旧接口保留；电源合格后LDO生成3.3V'),('B06/B07','J1','2,4','GND','RETURN','0V','短回流；不当作远距离抗干扰差分接口'),('B06/B07','J1','3','SYNC','OUTPUT','3.3V push-pull','接收端必须3.3V兼容；不能接1.8V Bank33'),
('B08','J1','1,2,3,4','+5VA,AGND,-5VA,REF_V','MIXED','±5V / 0..1V nominal','REF_V单端；由B02专用FDA转差分'),
('B01','J1','1,3','ADC_A_P,ADC_A_N','OUTPUT','0.9V共模 / ±0.8076V差分','禁止交流耦合；外部ADC需2Vpp范围'),('B01','J1','5','ADC_VCM','INPUT','来自B02，候选0.9V','不是B01自生电源；本次B02未完成'),('B01','J2','1,3,4','+5VA,-5VA,5VA_PMT','POWER_INPUT','按各器件范围核对','PMT与AFE供电分支分别滤波'),('B01','J2','5','PMT_VCONT','INPUT','推荐0.5..1.1V','限制/启动/故障控制由未闭合B03负责'),('B01','J2','7','OFFSET_0V5','INPUT','0.5V精密低噪声参考','测试可由限流、校准过的台架提供；未设计B03发生器'),('B01','J2','8','PMT_VREF','OUTPUT','模块参考，约1.2V','先核对最大负载，禁止外部强驱动'),
('B02','AD9268','32data+2DCO','CMOS_BUS','OUTPUT','1.8V','必须与SP2 Vadj和真实板卡版本核对；非LVDS')]
putcsv('engineering/interface_control.csv',[dict(board=b,connector=c,pin=p,signal=s,direction=d,level=l,rule=r) for b,c,p,s,d,l,r in interface])
tests=[
('TB01','B06/B07','断电检查','D1 K/A/CASE、IC pin1、短路、焊接、实物方向与原理图逐项比对','全部方向吻合；绝缘/短路按具体量程判定','显微照片/导通表'),
('TB02','B06/B07','限流供电','先不接FPGA，5V台架供电；观察3V3/VBIAS/THRESH及电流；检查无光SYNC','建议3.3V±3%；VBIAS/THRESH按误差预算；无光无多余翻转，阈值需审批','仪器电压/电流/示波器Raw'),
('TB03','B06/B07','反偏与电容','测D1反偏电压及安装后总输入电容；探头不得挂在PD_SUM','记录实测值替换模型Cin；不声称100MHz','LCR/阻抗/脉冲记录'),
('TB04','B06/B07','电流标定','使用验证过的高值注入电阻或PD光电标定；不能把发生器50欧直接接求和节点','5/10/20/50/100uA等效输入与TIA输出可追溯；保持在线性范围','注入电路图/实测电阻/波形'),
('TB05','B06/B07','光幅度时间偏移','固定几何扫描或独立光学参考时刻，扫光强并记录前后沿、中心和漏脉冲','分别报告偏移峰峰值/重复抖动RMS；不得用两种统计量互代','逐次t_rise/t_fall/幅度/温度CSV'),
('TB06','B06/B07','同步扰动','测最低光强到最高光强、遮挡、双脉冲、模拟失扫；记录FPGA输入','每facet事件数和异常标志正确；滤波不得隐藏失扫','逻辑分析/模拟波形'),
('TB07','B01','不接PMT的TIA测试','先验证±5VA、OFFSET0V5、ADCVCM；0/0.1/1/5/10uA电流吸收测试','核实极性、线性、输出共模；确认无ADC端超范围','电流标定与DC曲线'),
('TB08','B01','反馈补偿与阶跃','测5/20/50pF附加输入C的增益/阶跃；不同Rf/Cf逐一焊换','无不受控振荡；实测带宽/过冲/整定进入系统MTF预算','频响/阶跃原始数据'),
('TB09','B01','饱和恢复','先不接真实PMT，注入受控过量电流后恢复弱输入；电压不得超过绝对最大值','报告恢复至指定误差的时间和无效像素窗，不预先填PASS','过载/恢复Raw'),
('TB10','B08','参考通道标定','0..100uA等效光电流、光取样比例、反偏、低通延迟','验证正向0..1V输出及参考延迟；相对PMT时间对齐','DC/频率/时间CSV'),
('TB11','B02','时钟与SPI/测试码','待电路完成后用ADC内置测试码验证32data+2DCO；核对时序和供电','无未解释错误；模式/寄存器/测试次数/时钟与XDC保存','寄存器读回/ILA/测试日志'),
('TB12','B03/B04','上电/掉电/互锁','待电路完成后测试PMT控制限幅与独立关光；不得绕过原有互锁','默认关光；故障限幅/关断由实际硬件证明','电源故障注入/示波器'),
('TB13','B05','电机耦合与编码器','电流限额和机械防护确认后，比较电机停/转/加减速时模拟通道','保存噪声/行抖动/编码器异常；不得宣称编码分辨率=运动精度','同步遥测/模拟Raw'),
('TB14','SYSTEM','光电小台架','已确认PMT型号/允许电流和激光防护后测试暗场/阶梯片/重复扫描','真实SNR/噪声/饱和结果与设定模式对应；至少3次研发重复','Raw/参数哈希/环境/校准版本')]
putcsv('bench/test_matrix.csv',[dict(test_id=i,board=b,test=t,method=m,proposed_criterion=c,required_evidence=e,status='NOT_RUN') for i,b,t,m,c,e in tests])
putcsv('bench/execution_records_TEMPLATE.csv',[dict(test_id=i,run_id='',operator='',date='',board_serial='',schematic_hash='',pcb_hash='',instrument_id='',instrument_calibration='',setup_photo='',supply_settings='',raw_path='',measured_result='',uncertainty='',decision='NOT_RUN',reviewer='') for i,*_ in tests])
putcsv('bench/sync_timing_TEMPLATE.csv',[dict(run_id='',facet_id='',sample_index='',reference_time_s='',rise_time_s='',fall_time_s='',peak_tia_V='',threshold_V='',temperature_C='',laser_or_LED_setting='',valid='',raw_path='',status='NOT_RUN')])
# mechanical board placement contracts only; don't silently claim the R5 sensors fit the G1 bracket.
p=json.loads((R/'engineering/placements.json').read_text());coords=[dict(board=b['board'],ref=b['ref'],x_mm=b['pcb_xy'][0],y_mm=b['pcb_xy'][1],side=b['side'],coordinate_origin='board outline origin(0,0); +X right,+Y down; NOT chassis frame',status='DRAFT_NEEDS_G1_REVIEW') for b in p if b['ref']=='D1']
putcsv('engineering/sensor_locator_changes.csv',coords)
print('Records created:',len(issues),'open items;',len(tests),'bench cases')
