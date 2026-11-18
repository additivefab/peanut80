
# G5｜FPGA同步与原始采集

首批开发交付 · 归一化数字IP审查版

本轮承接G0/G1扫描时序、G2电路接口、G3双编码器输送和G4板卡边界。G5的目标是建立可追溯的“样本—时间—同步事件—位置”数据链；进入本阶段不代表G4已放行。

| 交付对象 | 本轮内容 | 状态 |

| 逻辑源码 | 11个SystemVerilog模块；原始采集、FIFO、仲裁、分包、编码器（M、D、E 三路）、SPI及前端候选 | 源码已生成；Icarus 行为仿真通过 |

| 自检仿真 | 9个testbench，包括背压、溢出、SPI、CDC FIFO、配对、采集和第三路编码器 | Icarus 13.0 全部 PASS |

| 软件与数据 | RAW协议、CRC/序号检查、诊断坐标映射、C接口、合成示例 | Python / C检查已执行 |

| 集成入口 | Vivado审查项目/OOC脚本，候选引脚审查和12项台架协议 | 板级实现未完成 |

## 必须先看清的边界

73项Python测试和C格式测试通过，9个bench在 Icarus 13.0 下行为仿真通过，不等于时序通过或实物可用。没有 Vivado 综合、实现、时序和 CDC；Yosys 综合只给量级估算。不提供伪造的.bit文件。

zl80_capture_core要求前端已经输出同一逻辑域内、同一模拟采样时刻的A/B样本及正确aperture时间戳。B02板级前端、完整PS/DDR/DMA、真实DMA驱动和硬件空间重采样尚未集成。

激光请求在RTL中固定为0；本包不包含电机执行控制。制造/烧录状态保持BLOCKED。

## 推荐第一入口

```
python tools/run_checks.py
python software/zl80_cli.py inspect examples/synthetic_scan.zlraw
python tools/native_validate.py
```

最后一条仅在实际存在HDL仿真器时运行原生测试；工具缺失时返回NOT_RUN与非零退出码。


# 01｜继承关系与不变约束

| 输入基线 | 采用内容 | 保留限制 |

| G0/G1 | 80mm有效幅宽、100mm光学预留、92mm暂定SOS/EOS跨度；6面、3000rpm、EFL100mm算例 | 面数/转速/焦距均非实测或采购保证 |

| G2 | AD9268双通道16bit、20MSPS预算；1.8V非交织CMOS；SOS/EOS 3.3V候选 | B02电路、共模、时钟和SPI仍未闭合 |

| G3 | Ø20mm辊、4096PPR、四倍频；测量/驱动编码器分开 | 约3.835µm是量化步距，不是位置精度 |

| G4 | B06/B07/B08候选布线；B01部分布线；B02—B05未闭合 | 接口、供电与安全问题不被本轮自动消除 |

## 唯一配置与可追溯来源

config/design.json保存本轮设计假设和未批准状态；G01原参数文件原样复制，不回写上游。sources/input_hashes.json记录7个精确继承文件的SHA-256，用于区分本轮新增设计与历史依据。

候选SP2引脚表保留原编号、引脚和球位，但每项均标为INHERITED_UNAPPROVED。旧XDC仅作文本参考，不自动进入项目。ADC控制/越界线的电平转换及双向SDIO必须在B02关闭。

## 三类时间不能混用

| 时间 | 含义 | 使用规则 |

| ADC aperture | 模拟输入实际被采样的时刻 | pair_tick必须对应这一时刻 |

| FPGA观察事件 | 同步器后检测SOS/EOS/编码器的时刻 | 保留原始观察值；校准偏移单独记录 |

| FIFO/DMA/主机到达 | 数据经过缓冲或软件到达的时刻 | 不能反代光斑或胶片位置 |

物理镜面索引接口在G0仍未知。本版记录相对行号，并将绝对facet留为UNKNOWN；即使后续接入polygon index，也仍需明确索引到具体镜面的相位映射。


# 02｜采集架构与模块职责

归一化样本 + 同步事件 → 独立记录FIFO → 公平仲裁 → 128bit记录转64bit AXI-Stream → 后续DMA/DDR。样本与各类事件分别缓存，不使用单个优先级if链吞掉同时发生的事件。

| 模块 | 职责 | 边界 |

| zl80_capture_core | 会话、样本/事件记录、故障锁存、正常/故障收尾 | 归一化接口，不是ADC板级top |

| sync_bits / reset_release | 独立位同步、异步复位同步释放候选 | 不用于多位ADC总线逐位同步 |

| quad_decoder | 正反向计数、索引观测、非法跳转与回卷保护 | Z不自动清零 |

| record_fifo | 单时钟FWFT记录缓存；满时计数 | 同步读（2026-11-17 起）：深度≥256用BRAM；push到有效多1拍；Yosys估算已做，Vivado未做 |

| rr_record_merge | 6路公平仲裁，输出寄存保持 | 跨来源时间可不排序 |

| record_to_axis64 | 低64位先发；背压保持；TLAST分包 | 无DMA寄存器/DDR控制器 |

| ad9268_spi_byte | 24bit单字节读写；SDIO读方向释放 | 独立模块，未接PS控制桥 |

| adc_cmos_lane | 单路DCO捕获和序号 | 前端候选，未接入核心 |

| async_fifo_gray | Gray指针跨域候选 | 两侧复位和物理CDC约束待验证 |

| adc_pair_guard | 本地序号一致性保护；错误锁停 | 相同序号不是共同采样epoch证据 |

## 数据路径与控制路径分别处理

归一化pair_valid为一周期有效脉冲，核心不向ADC背压。满缓冲会记录损失并停止当前会话。START/STOP接口必须先处于clk域；PS侧AXI-Lite桥尚未实现。

同步比较器输入仅作观测，不能取代G4独立硬件关光。逻辑时钟停止时，本核心也不可能继续执行看门狗，因此不能把FPGA软件状态机作为唯一安全链。


# 03｜128bit记录与存储协议

| 位段 / 字节偏移 | 字段 | 定义 |

| 31:0 / 0—3 | payload32 | ADC B:A、位置计数、行号或状态 |

| 95:32 / 4—11 | tick64 | 共享逻辑时基，设计假设100MHz |

| 111:96 / 12—13 | flags16 | 类型相关的质量状态 |

| 119:112 / 14 | version8 | 当前为1 |

| 127:120 / 15 | type8 | 记录类型 |

序列化采用小端。C内存结构可能有填充字节，必须使用software/include/zl80_raw.h的显式编码函数，不可直接写sizeof(struct)。

| 类型 | 记录 | payload含义 |

| 01 | 采样 | 低16位A、高16位B，原始码不裁剪 |

| 10/11、12/13 | SOS上/下沿、EOS上/下沿 | 相对line_id |

| 20、21 | 测量编码器、驱动编码器 | 有符号32位位置；bit15为初始快照 |

| 22 | 出口随动编码器E（ECR-G3-01） | 有符号32位位置；bit0变化、bit2非法、bit15初始快照；无索引 |

| 30 | polygon索引观察 | 当时相对line_id |

| 70、71、72、7F | START、STATUS、LOSS、END | 会话ID、故障字、丢失记录数、会话ID |

## AXI-Stream包边界

每条记录两个64bit beat，先低后高，TKEEP=FF。默认每256条记录/4096字节产生TLAST；最后END记录可终止不足一整块的尾包。TVALID置位但TREADY为0时，TDATA/TKEEP/TLAST必须保持不变。

## 主机归档不是RTL CRC

ZL80RAW1文件头带JSON元数据；随后各块包含BLK1、递增序号、字节长度、CRC32和记录正文。CRC由本轮主机归档程序计算，RTL并未生成CRC。缺块、换序、翻转字节或缺END均拒绝，不静默补零。


# 04｜时序与带宽预算

以下均为G0/G1暂定算例：六面、3000rpm、EFL100mm、50µm采样、20MSPS双通道。真实扫描头变化时必须重新计算。

| 项目 | 结果 | 解释 |

| 理论行频 | 300 行/s | 6×3000/60 |

| 80mm有效扫描时间 | 1.273240 ms | 不是整个3.333ms行周期 |

| 92mm同步跨度时间 | 1.464225 ms | 名义SOS/EOS位置算例 |

| 50µm驻留 / 瞬时像素率 | 0.795775µs / 1.256637MHz | 不能用平均像素率替代 |

| 胶片速度 | 15 mm/s | 50µm×300行/s |

| ADC CMOS流水线 | 12采样周期 / 600ns | 20MSPS；等于60个100MHz tick |

| 双通道原始码流 | 80 MB/s | 20M×2通道×2字节 |

| 逐样本记录流 | 约320 MB/s | 20M×16字节，不含事件 |

| 64bit AXI理论峰值 | 800 MB/s | 100MHz，未扣背压/DDR开销 |

| 1024样本FIFO全停余量 | 约51.2µs | 只缓解短暂停顿 |

| 5ms调试抓取 | 约1.6MB | 逐样本记录，不含小量事件 |

ADC的12周期来自原厂CMOS接口规格[W01]，不能误写成12个FPGA逻辑周期。实际总延迟还包括采样相位、IO捕获与跨域适配，不能简单在FIFO出队时间减600ns就声称完成标定。

当前选择有限长度RAW调试抓取。千兆链路理论上限只有125MB/s，还未扣协议开销，不能承诺320MB/s记录长期直接落盘。连续图像路径需要后续实现和验证抗混叠、空间重采样与流控。


# 05｜会话、故障和数据有效性

会话流程：IDLE → START与编码器快照 → RUN → DRAIN → STATUS → LOSS → END → 等待尾包发出 → IDLE。STOP请求在忙时锁存；不会在背压下任意丢弃尾部。

| 故障字位 | 含义 | 处理 |

| 0 | 外部故障观察 | 停止新采集，保留已收记录 |

| 1 | 某记录FIFO溢出 | 计数丢失，故障收尾 |

| 2/3 | 测量/驱动编码器非法跳转或范围回卷 | 不更新错误位置，标记故障 |

| 9 | 出口随动编码器E非法跳转 | 仅在 E_REQUIRED=1 时置位；会话故障收尾 |

| 10 | E的线缆/FFC断开观测（ENC_E_OPEN 为高） | 仅在 E_REQUIRED=1 时置位；会话故障收尾 |

| 4 | SOS/EOS次序异常 | 不伪造结束事件 |

| 5 | SOS超时 | 设计默认20ms，必须按真实转速审核 |

| 6 | 前端上报丢样 | 禁止会话作为有效扫描 |

| 7 | 样本时间倒退/重复/未来值 | 时间关联失效 |

| 8 | 归一化ADC样本流超时 | 设计默认10µs；ARM前先完成ADC预热 |

START/END的时间表示控制边界，不保证有效ADC数据覆盖到该时刻。真正采集覆盖范围以首末SAMPLE和完整扫描窗为准；停止后未进入核心的ADC流水线尾部不应被主机补齐。

## 样本标志

bit0/1：A/B越界；bit2：时间未标定；bit3：两路同epoch未验证；bit4：ADC测试码；bit5：上游丢样。0或65535原始码原样保存，越界状态单独记录，不能夹断或改成“正常灰度”。

协议检查中的digital_integrity_eligible仅表示本轮格式与数字完整性条件；metrology_release始终为false。即使没有丢样，也不能据此宣称OD、DCS、MTF或激光安全通过。


# 06｜离线关联与诊断重建

## 本轮实际实现

主机程序读取并校验RAW块，保留原始记录；根据同一时基内的完整SOS/EOS区间估计X坐标，根据测量编码器事件插值得到Y诊断坐标。输出CSV而不是伪造已校准密度图。

```
x = -sync_span/2 + sync_span * (t - t_SOS) / (t_EOS - t_SOS)
y = interpolated_encoder_count * pi * roller_diameter / (PPR * 4)
```

公式仅为理想线性诊断。真实f-θ畸变、逐镜面位置LUT、模拟群延迟及非线性密度标定没有被这两个公式取代。校准必须逐版本保存。

## 不外推、不混淆

找不到编码器前后证据时，Y坐标留空。行中缺EOS不补线；连续两次SOS而没有对应EOS时直接报错。记录流跨来源不保证全局时间有序，软件按共享时基处理，样本流自身必须单调。

facet_relative来自相对行号模6，绝对镜面始终为UNKNOWN。未标定polygon索引不能用于绝对逐镜面校准。

## 本轮合成示例结果

| 内容 | 实际生成结果 |

| 原始样本 | 176,378对A/B样本 |

| 同步事件 | 3组完整扫描线，保留SOS/EOS双边沿 |

| 位置诊断 | 76,394条80mm ROI内样本坐标 |

| 原始码边界 | 18处0/满量程样本保持不变 |

| 来源 | Python算法合成；synthetic=true |

| 用途限制 | 不是HDL波形、不是PMT实测、不是已标定Master |

逐样本附带位置/时间的诊断路径适合查错。产品化连续成像应另行实现基于真实时戳的空间重采样，并在有效强度域做必要平均；不能用任意抽样掩盖吞吐瓶颈。


# 07｜SPI、ADC与电压边界

SPI候选模块采用模式0、MSB先行、16bit指令加8bit数据。读数据阶段释放SDIO，避免与ADC同时驱动；模块没有自动初始化ADC或自动启用真实硬件。[W01]

| 步骤 | 审查计划 | 待关闭项 |

| 识别 | 只读0x01，AD9268预期ID=0x32；读grade | 实物型号、仪器和供电确认 |

| 通道 | 0x05选择A+B；读回时逐通道选择 | 不可将同时选择时单路读值当两路验证 |

| 模式 | 0x14=0x00候选：非交织CMOS、offset binary | B02实际引脚和电平必须吻合 |

| 诊断码 | 0x0D=0x04棋盘格；之后切回0x00 | 验证位序、相位和丢样 |

| 影子寄存器 | 写0xFF=0x01提交相关更改 | 不能漏掉提交而误认配置生效 |

| 时钟/参考 | 20MSPS+DCS；2Vpp候选 | SENSE实际连接、时钟与DCO延时待核对 |

详细审查计划在config/ad9268_spi_review_plan.json；它不是已经执行的寄存器日志，更不是可以未经审核自动上电的脚本。

## 1.8V和3.3V不得直接混用

历史J6分配把Bank33的34个IO用于32位数据和两路DCO。Vadj必须按实际板卡核实和测量。B06/B07的SYNC候选为3.3V，应接兼容域；ADC控制和ORA/ORB走其他域时必须核对转换。J6电源针脚不能因Vadj变化就假定变成1.8V。

完整板级XDC被显式阻止：未批准针脚、电平、真实路由和时序前，不生成可烧录文件。OOC中仅定义100MHz逻辑假设；不能通过宽泛false_path把所有CDC问题隐藏。[W04/W05]


# 08｜验证证据与未运行项

| 证据类别 | 本轮结果 | 它能证明什么 |

| Python单元测试 | 73项通过，0失败/错误 | 字节协议、CRC/丢块拒绝、算法模型、诊断几何与门禁 |

| C ABI测试 | GCC C11严格警告编译并执行通过 | 16字节编码/解码、边界检查与Python布局一致 |

| 合成端到端 | 176,378对样本归档并读取；3行坐标关联 | 算法示例闭环，不是物理性能 |

| RTL自检bench | 9个，Icarus 13.0 全部 PASS；slang 编译 0 错误 | 行为级正确；不证明时序和跨时钟域 |

| Yosys 综合（xc7，估算） | LUT 2371、触发器 2081、RAMB36 4 个 | 可综合性和资源量级；record_fifo 已改同步读 BRAM 写法，push 到有效多 1 拍 |

| Vivado OOC/实现 | NOT_RUN | 无资源、时序、CDC收敛结论 |

| 真实ADC/传感器/DDR台架 | 12项协议均NOT_RUN | 不提供实测成功宣称 |

## 九个testbench覆盖内容

FIFO（深度2/4/32/256，数据顺序、s_ready、溢出、复位、清计数）；AXI背压稳定和尾包；编码器正反向/索引/非法转移；SPI写帧/读释放；异步FIFO次序；双路配对错误；归一化端到端采集；故意溢出后的故障收尾；第三路编码器 E 的计数、OPEN 和非法跳转。

所有bench在 Icarus Verilog 13.0 中实际运行。native_validate.py保存编译/仿真日志，只有仿真器正常返回且出现对应PASS标志才记通过。缺少工具时不生成假VCD或测试通过记录。

当前9个bench不是形式验证或全覆盖。CDC亚稳态、时钟停止、IO电气、硬件安全、实际DMA、资源/功耗等都不能由算法测试替代。

## 继续开发的首要关口

HDL 自检已在 Icarus 通过；下一步在 Vivado 做综合、时序和 CDC，并确认 BRAM 推断；再做B02测试码、同epoch配对和时间标定。若任一项没有证据，保持TIME_UNCAL或PAIR_UNVERIFIED，禁止将标志硬接为“已验证”。


# 09｜Vivado、DMA与实机接入顺序

Vivado审查工程由Tcl在本机生成，不交付伪造的已打开.xpr。器件参数必须由实物确认，xc7z020clg484-1只作为命令格式示例。

```
vivado -mode batch -source vivado/create_project.tcl \
  -tclargs xc7z020clg484-1

vivado -mode batch -source vivado/synthesize_ooc.tcl \
  -tclargs xc7z020clg484-1
```

create_project只创建归一化逻辑/仿真工程；synthesize_ooc只尝试OOC综合并保存报告和checkpoint，不进行板级布局布线、bitstream或硬件下载。

## 后续DMA集成约定

S2MM应在采样开始前配置好缓存、描述符及中断。AMD文档说明，DMA未配置时TREADY可能很快拉低，因此不能先ARM、再慢慢启动DMA。[W02]

本轮每4096字节一包，尾部END可形成短包。S2MM缓冲应按可能最大包长预留并读取实际完成长度；TLAST位置、DRE/对齐、缓存一致性、DDR带宽及中断服务必须由实际系统验证。[W03]

跨DMA时钟域时使用经验证的AXI-Stream时钟转换模块。不能只给TDATA加两级寄存器而漏掉TVALID、TREADY、TLAST。当前未交付可运行的PS/DDR Block Design、驱动或网络接收程序。

## 实机顺序

断电核对 → 电源与电平 → SPI只读 → ADC测试码 → 两路DCO/epoch → aperture标定 → 编码器和SOS/EOS → 短时DDR抓取 → 再接光学台架。全程不依赖本包启用激光/电机，真实互锁仍须由G4电气方案闭合。


# 10｜交付文件、后续任务与来源

| 路径 | 用途 |

| rtl/、sim/tb/ | 11模块与8bench；前端候选单独隔离 |

| software/、tests/ | 离线归档解析/映射、C接口、59项Python测试 |

| vivado/、constraints/ | 审查项目/OOC脚本；未批准板级约束明确阻止执行 |

| interfaces/、config/ | 端口、针脚、记录类型、标志、预算、SPI计划与未关闭项 |

| validation/results/ | 实际测试日志、合成示例、原生NOT_RUN、BLOCKED门禁 |

| validation/bench/ | 12项实测协议与空白执行记录 |

| sources/ | 精确继承文件哈希和外部原厂参考 |

## 下一轮最小任务

T001：执行8个HDL自检。T002：B02电路与测试码闭环。T003：双DCO同epoch及时间适配。T004：PS/DDR/DMA真实回环。T005：SOS/EOS恒幅抖动与变幅时间偏移。T006：受控滤波、空间重采样和连续落盘。

## 参考依据

[U] G0/G1、G2、G4及R5.1精确文件见sources/input_hashes.json；它们分别支持设计暂定参数、接口电压和未完成项。未将历史候选改写为实物确认。

[W01] Analog Devices, AD9268 Rev.A，页9—10、33、35、37—39：CMOS时序、SPI及寄存器。

[W02/W03] AMD AXI DMA PG021：Typical System Interconnect、S2MM包/TLAST语义。

[W04/W05] AMD UG903：异步时钟约束优先级与source-synchronous输入延时。

完整标题、定位与网址在sources/external_references.csv。厂商资料支持接口规则，不代表本项目硬件已验证。

最终状态：开发文件已交付；G5整机实现与制造/烧录资格未放行。

## Hello-FPGA 核心板修订（R52-G5-HF-D02，2026-11-17）

本修订由 R52-G5-F01-D01 复制而来；原包已于 2026-11-17 删除，本包是唯一的 G5 现行版本。依据：Hello-FPGA 的 `ZYNQ7020_Core_Board` 原理图（`sources/hellofpga/`，约 1.2 MB，SHA-256 835d50e1…），核心板芯片 xc7z020clg400，Bank13/34/35 为高性能 IO（HR）。

### 引脚

- 核心板原理图第 7 页：VCCO_13、VCCO_35 接 +3.3 V；VCCO_34 接网络 VCCIO，由底板供给。因此 AD9268 的 1.8 V CMOS 总线（32 位数据、2 路 DCO、2 路 OR，共 36 脚）放在 Bank34，并要求底板把 VCCIO 设为 1.8 V。这个电压没有核实。
- 其余 29 个信号放在 Bank35（3.3 V）：SOS、EOS、三组编码器（M、D、E 共 9 脚）、STEP/DIR/MOT_EN、LASER_EN/SHUTTER_EN/FAULT、I2C、ADC_SPI 4 脚、TMC_UART、ENTRY_L/R、EXIT、ADF_READY/REQUEST。
- 两路 DCO 放在 Bank34 的时钟专用 P 脚：DCOA 在 N18（B34_L13_P，MRCC），DCOB 在 U14（B34_L11_P，SRCC）；其他信号不占时钟专用脚。
- 只使用核心板连接器引出的脚（Bank34、Bank35 各 49 个，B34_L12_P 与 B35_L24_N 未引出）。继承的原 SP2 引脚表里只有 7 个球位同时存在于 Bank35（E18、F17、G17、G19、F19、E19、H20），保持不变；其余 21 个重新分配。
- 底板上的连接器脚号不知道，所以表中只给核心板球位和核心板网名。第三路编码器：ENC_E_A 在 D18、ENC_E_B 在 E17、ENC_E_OPEN 在 D20。
- 生成脚本 `tools/gen_hf_pins.py`，约束 `constraints/hf_core_pins_NOT_APPROVED.xdc`；状态全部是 CANDIDATE_UNAPPROVED。

### 第三路编码器 E（ECR-G3-01）

- 端口：`enc_e_a_async`、`enc_e_b_async`、`enc_e_open_async`；两级同步后接第三个 `quad_decoder`，不使用索引线。
- 记录：类型 0x22，START 后有一条初始快照（bit15），之后每次计数变化一条；第 7 个记录 FIFO，合并器 N=7。
- 故障：bit9 为 E 非法跳转，bit10 为 OPEN；由参数 `E_REQUIRED`（默认 1）控制。E 未装时设为 0，并在 metadata 记录。
- 主机：`follower_difference`、`follower_agree` 比较 M 与 E 从首个公共点起的位移；限值 0.05 mm 是占位，有效滚动半径比 `e_scale` 要用标定靶整定。
- 台架：`tb_encoder_e` 检查正向计数、OPEN、非法跳转三项。

### 检查状态

- Python 算法与格式测试：见 `validation/results/python_tests.json`。
- HDL：Icarus Verilog 13.0（conda-forge，x86_64）运行全部 9 个 bench 通过，含新增的 tb_encoder_e；另有 slang 编译检查 0 个错误。bench 是行为级自检，不证明时序和跨时钟域。第一次运行 tb_encoder_e 因 bench 自己的错误超时（第二个会话开始时 E 输入仍为 11，复位后被当成非法跳转），已修 bench，RTL 未改。
- 没有 Vivado 综合、实现、时序和 CDC。
