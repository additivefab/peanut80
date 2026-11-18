"""CSV tables for ECR-G3-01 channel E (B05 input + harness W13). Reads ECR_G3_01_E_计算.json written by build_electrical.py."""
import csv,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import geom_e as g
EL=g.E/'electrical';C=json.loads((EL/'ECR_G3_01_E_计算.json').read_text())
def w(name,head,rows):
    with open(EL/name,'w',newline='',encoding='utf-8-sig') as f:
        c=csv.writer(f);c.writerow(head);c.writerows(rows)
J5G=g.J5G;L=C['w13']['length_filleted_mm'];cut=int(C['w13']['cut_length_mm'])
# ---- end to end signals
w('ECR_G3_01_E_信号表.csv',['信号','传感器板 G3E-03/08','FFC 6P 脚','转接板 G3E-06','W13 芯线','B05 J5 脚','B05 缓冲 U3','B05 J3 脚','FPGA 板 J5_V1.3B','说明'],[
 ['5V_E','VDD','1','焊盘 1','红 AWG30','1','—（铁氧体+去耦后供电）','—','—','传感器约 30 mA（假设），压降约 %.0f mV'%C['supply']['drop_mV']],
 ['GND','GND','2、6','焊盘 2','黑 AWG30','2','—','11、19、20','—','FFC 第 2、6 脚并联；A 紧邻地，B 夹在 A 与 OPEN 之间'],
 ['ENC_E_A','ABI A','3','焊盘 3','白 AWG30','3','门 1','16','待分配（P0）','5V CMOS，经 470 Ω + 470 pF + 47 kΩ 进 U3'],
 ['ENC_E_B','ABI B','4','焊盘 4','绿 AWG30','4','门 2','17','待分配（P0）','同上，与 A 路布线等长'],
 ['ENC_E_OPEN','焊 0 Ω 接 GND','5','焊盘 5','黄 AWG30','5','门 3','18','待分配（P0，可选）','B05 上拉 10 kΩ 到 3V3：线缆或 FFC 断开为高，插好为低'],
 ['SHIELD','—','—','不接','屏蔽铝箔+排流线','6','—','—','—','只在 B05 端接地，传感器端悬空，避免经支架形成地环'],
])
# ---- J3 pins
J3=[(1,'SCLK','SCLK','不变'),(2,'SDIO','SDIO','不变'),(3,'STEP','STEP','不变'),(4,'DIR','DIR','不变'),(5,'MOT_EN','MOT_EN','不变'),(6,'TMC_UART','TMC_UART','不变'),
    (7,'ENC_A','ENC_M_A','改名：假设原 ENC_A/B/Z 是测量组（G4 未写明）'),(8,'ENC_B','ENC_M_B','同上'),(9,'ENC_Z','ENC_M_Z','同上'),(10,'FAULT','FAULT','不变'),(11,'GND','GND','不变'),(12,'3V3','3V3','不变'),
    (13,'—','ENC_D_A','新增：FPGA 需要驱动组，G4 的 J3 原来没有引出'),(14,'—','ENC_D_B','新增'),(15,'—','ENC_D_Z','新增'),
    (16,'—','ENC_E_A','新增：出口随动'),(17,'—','ENC_E_B','新增'),(18,'—','ENC_E_OPEN','新增'),(19,'—','GND','新增：扁平线上的回流'),(20,'—','GND','新增')]
w('ECR_G3_01_E_B05_J3引脚.csv',['脚','G4 现有网名','新网名','说明'],[list(r) for r in J3])
# ---- B05 change list
w('ECR_G3_01_E_B05变更清单.csv',['编号','项','G4 现状','本设计','位置（板坐标 mm）','状态'],[
 ['B05-E1','U3 缓冲','U2 为 2×SN74LVC3G17（6 路，正好用于 M、D 两组）','增加第 3 片 SN74LVC3G17，3 路：A、B、OPEN','区域 12×10，中心 (26,80)','设计；原理图未改'],
 ['B05-E2','J5 传感器 E 输入','无','1×6 2.54 mm 排针：5V、GND、A、B、OPEN、屏蔽','18×7×10，中心 (40,93.5)，沿 X','设计；料号与防反插未定'],
 ['B05-E3','J3 板到 FPGA 板','2×6，仅一组 ENC_A/B/Z','2×10：补全 M/D/E 三组编码器信号和回流地','7×29.2×9，中心 (52,72)','设计；对接件未定'],
 ['B05-E4','5V_E 供电','—','铁氧体磁珠 + 4.7 µF + 100 nF；短路保护随 G4 电源方案闭合','U3 区域内','占位，值未核算'],
 ['B05-E5','ESD','—','5V 单向 TVS 阵列 ×1（A、B、OPEN、5V 各一路），型号待选','J5 旁','占位'],
 ['B05-E6','输入网络','M、D 路同类（G4 未写值）','A、B：串 470 Ω、对地 470 pF、47 kΩ 下拉；OPEN：10 kΩ 上拉到 3V3','U3 区域内','值是本设计提出，台架整定'],
 ['B05-E7','板上干涉','—','新旧器件间距最小 %.1f mm，边缘 3 mm、孔位 %.1f mm 禁区均满足'%(C['b05_layout']['min_gap_mm'],4.5),'—','已检查（矩形近似）'],
])
# ---- harness W13
w('ECR_G3_01_E_线束表.csv',['线束','段','类型','起点','终点','长度 mm','外径/宽 mm','最小弯曲半径 mm','备注'],[
 ['W13','FFC','FFC 6P 0.5 mm，0.3 mm 厚','传感器板连接器（x=93.4，z=122.6）','转接板连接器（x=117.0，z=127.8）',C['ffc']['length_mm'],'宽 4.5','预成形拱半径 %.1f–%.1f（随上辊 −1…+5 mm）'%(min(v['radius_mm'] for v in C['ffc']['by_height'].values()),max(v['radius_mm'] for v in C['ffc']['by_height'].values())),'上拱 5.0–5.6 mm；曲线上拱方向要预成形并加 PET 加强'],
 ['W13','圆线','5 芯屏蔽 AWG30，外径 4 mm','转接板焊盘（119.3,39,131）','B05 J5 上方 12 mm（%.1f,%.1f,%.1f）'%(J5G[0],J5G[1],J5G[2]+22),L,4.0,15.0,'走线 (119.3,39,131)→(119.3,39,150)→(119.3,78.5,150)→(%.1f,78.5,150)→(%.1f,78.5,%.1f)；下料 %d mm（含两端 20 mm 和 30 mm 服务量）'%(J5G[0],J5G[0],J5G[2]+22,cut)],
])
# ---- G5 interface changes
w('ECR_G3_01_E_G5接口变更.csv',['编号','对象','现状','需要的改动','优先级','状态'],[
 ['G5-E1','FPGA 板 J5_V1.3B 引脚','第 7–34 脚已分配，第 1–6 脚在包内无说明','查板卡手册，为 ENC_E_A、ENC_E_B（可选 ENC_E_OPEN）找 3 个 3.3V Bank35 输入；找不到时的备选是让出 ENC_M_Z、ENC_D_Z 两脚','P0','未做'],
 ['G5-E2','zl80_capture_core 端口','enc_m_*、enc_d_* 共 6 个异步输入','增加 enc_e_a/b（enc_e_open）；同样两级同步；再例化一个 quad_decoder','P0','未做'],
 ['G5-E3','记录类型','0x20 测量、0x21 驱动','新增 0x22 出口随动编码器 position32；bit 定义同 0x20；START 时快照','P0','未做'],
 ['G5-E4','故障位','faults 含编码器非法跳转','增加 E 路非法跳转和 OPEN 置位','P1','未做'],
 ['G5-E5','host 程序','按 0x20 插值得 Y','同时解码 0x22；输出 E 与 M 的差；follower_agree 供状态机使用','P1','未做'],
 ['G5-E6','自检 bench','8 个 testbench','增加 E 路正反转、非法跳转、OPEN 三项','P1','未做'],
])
# ---- parts
M=C['mass_g']
w('ECR_G3_01_E_件表.csv',['件号','名称','材料','单件质量 g','类别','备注'],[
 ['G3E-05','FFC 固定端支架 L 形 t1.5，贴在 G3-M12 顶面','5052-H32',M['G3E-05'],'自制','VHB 粘贴或两颗 M3；打孔需要追加批准，G3-M12 本包不改'],
 ['G3E-06','转接小板 9×8.5×1.6（FFC 连接器 + 5 路焊盘）','FR4+外购',M['G3E-06'],'外购','质量为假设；固定端，不加载上辊'],
 ['G3E-07','FFC 6P 0.5 mm，长 27 mm','PI/Cu',M['G3E-07'],'外购','预成形上拱'],
 ['G3E-08','传感器端 FFC 连接器 6P 0.5 mm 竖直进线','外购',M['G3E-08'],'外购','质量为假设；焊在 G3E-03 +x 面'],
 ['W13','5 芯屏蔽线 AWG30 外径 4 mm，两端压接','外购','—','外购','长度 %d mm；两端接插件型号待定'%cut],
])
print('tables ok')
