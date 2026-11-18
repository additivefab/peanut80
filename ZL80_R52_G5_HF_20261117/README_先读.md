# ZL80 R5.2 / G5 FPGA同步与原始采集（Hello-FPGA核心板修订）
修订：R52-G5-HF-D02｜2026-11-17｜状态：工程审查、禁止直接上板。
本修订由 `ZL80_R52_G5_20261116`（R52-G5-F01-D01）复制而来，原包保持不变。改动：①目标改为Hello-FPGA ZYNQ7020核心板（xc7z020clg400），候选引脚见 `interfaces/pin_review.csv`；②增加第三路编码器E（ECR-G3-01，记录0x22、故障位9/10、`tb_encoder_e`）；③软件增加 `follower_difference/follower_agree`。HDL已用Icarus Verilog 13.0跑通全部9个bench（含tb_encoder_e，原有8个也通过）；Vivado未运行；Bank34的1.8 V和底板均未核实。bench是自检行为级，不是时序/CDC证明。
说明：原包 ZL80_R52_G5_20261116 已于 2026-11-17 删除，本包是唯一的 G5 现行版本。

本轮按前述G5“FPGA同步与数据采集”推进。G4未完成项不会因为进入G5而自动关闭。

## 实际交付
11个SystemVerilog模块、8个自检testbench、归一化双通道采集核心、独立SPI单字节读写、候选DCO/Gray FIFO/配对保护、Vivado审查项目/OOC综合脚本、候选针脚审查、数据协议、Python离线解析和几何诊断、12项台架协议。

## 重要边界
Python算法/格式测试已运行；HDL编译和仿真未运行，Vivado未运行，实物台架未运行。
当前环境没有Icarus/Vivado；尝试安装未成功，证据明确标NOT_RUN，未生成假波形。
数字核心需要一个“同clk域、两通道同采样epoch、正确aperture时间”的前端接口。B02完整适配器并未集成，不能直接把异步ADC总线接到核心。
候选前端计数器相等不证明A/B同时采样；相关不确定标志默认保留。
没有完整Zynq PS/DDR/AXI DMA Block Design、真实DMA驱动、实现后时序、板级bitstream、FPGA硬件重采样或已标定密度输出。
`laser_request`固定为0；无电机执行逻辑。

## 先运行
无需额外Python包（建议Python3.10+）：
```
python tools/run_checks.py
python tools/calculate_budget.py
python software/zl80_cli.py inspect examples/synthetic_scan.zlraw
python software/zl80_cli.py map examples/synthetic_scan.zlraw --out my_coordinates.csv
```
示例是Python生成的合成数据，不是HDL波形、更不是实物扫描；文件内synthetic=true。

安装Icarus Verilog后：
```
python tools/native_validate.py
```
未发现工具时返回NOT_RUN和非零退出码。必须执行并审查全部bench，才可说HDL仿真通过。

Vivado（器件参数必须实物确认；以下只是格式示例）：
```
vivado -mode batch -source vivado/create_project.tcl -tclargs xc7z020clg400-1
vivado -mode batch -source vivado/synthesize_ooc.tcl -tclargs xc7z020clg400-1
```
项目可在本机生成；本包没有伪造已打开的.xpr。OOC仅综合归一化核心，不是整机可烧录工程。

## 文件入口
`docs/`：设计说明、协议与接入边界。
`rtl/core/`：采集状态机、FIFO、公平仲裁、64bit AXI分包、编码器。
`rtl/helpers/`：同步器、复位释放、AD9268 SPI。
`rtl/frontend_candidates/`：未集成的ADC接口候选，需要实际时序/CDC证明。
`software/`：离线RAW归档解析、CRC/序号检查、诊断坐标映射。
`interfaces/`：针脚/接口/时序/记录类型/未关闭项。
`validation/results/`：实际Python结果、合成示例结果、NOT_RUN原生检查。
`validation/bench/`：NOT_RUN台架协议与空白执行记录。

## 带宽与使用模式
20MSPS双通道原始码80MB/s；本版每对样本16字节记录约320MB/s，不含事件。首版用于短时调试抓取。1024深度样本FIFO仅约51.2us全停容限，不能当长时间DDR缓存。
实际连续扫描需要经过真实模拟/数字低通、空间重采样、帧缓存和PS链路验证；不能用随意丢样代替降带宽。

## 归档完整性
记录流不保证不同来源全局时间有序，必须按同一epoch关联。每通道样本序号/时间必须单调。
发生FIFO溢出会停止接收新数据，排空已接收记录，然后输出STATUS、LOSS和END；主机永远不就地补行。
最终END时间是采集控制结束时刻，不代表ADC已有效覆盖直到该时刻；真实覆盖以首末SAMPLE和有效扫描窗为准。
`release_check.py`保持BLOCKED；这不是可通过删除规则解除的程序错误。

## 参数与RTL联动边界
`config/design.json`是预算与接口审查输入，尚不是RTL参数代码生成器。修改频率、FIFO深度、超时或分包长度时，必须同时更新RTL实例参数、testbench、约束和软件元数据；不允许只改JSON就宣称硬件已更新。

## record_fifo 已改为同步读 BRAM 写法（2026-11-17）

`rtl/core/record_fifo.sv` 原来是异步读、只能用分布式 RAM；现在改为同步读，BRAM 读寄存器直接作为 FIFO 输出字，仍是首字直通。深度不小于 256（采样 FIFO，1024）用 BRAM，浅的事件 FIFO 用 LUT RAM。代价是 push 到 m_valid 多 1 拍（从空开始至少 2 拍）。

`python3 tools/yosys_synth.py --yosys <路径>`：用 Yosys 0.71 的 synth_xilinx（xc7）综合 `zl80_capture_core`，写 `validation/results/yosys_summary.json`。这不是 Vivado，没有时序和 CDC，数字只作量级参考。

| | 改前（异步读） | 改后（同步读） |
|---|---|---|
| LUT | 3069 | 2371 |
| 触发器 | 1346 | 2081 |
| RAM64M / RAM32M | 688 / 132 | 0 / 132 |
| RAMB36 | 0 | 4 |

`sim/tb/tb_fifo.sv` 已换成新 bench（深度 2/4/32/256，记分板检查数据顺序、s_ready 规则、溢出计数、输出保持、空到有效延迟≤2 拍、复位和 clear_stats）。故障注入（读指针、满判断、valid 清除）三项都被抓到。9 个 bench 在 Icarus 下全部 PASS。BRAM 推断在 Vivado 里还没有确认。
