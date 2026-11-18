# 时钟与引脚约束边界

`logic_ooc.xdc`只定义本轮归一化逻辑IP的100 MHz设计假设，不是整机XDC。
`BOARD_NOT_APPROVED.xdc`故意阻止未批准的板级约束进入实现流程。
历史R5.1针脚表（SP2/CLG484）以只读来源复制到`sources/inherited`，不自动导入Vivado。
本修订面向Hello-FPGA ZYNQ7020核心板（xc7z020clg400）：候选引脚在`hf_core_pins_NOT_APPROVED.xdc`，由`tools/gen_hf_pins.py`从`sources/hellofpga/core_pins.json`生成。Bank34的VCCIO由底板供给，ADC 1.8 V CMOS要求它为1.8 V，尚未核实；Bank35在核心板上是3.3 V。

必须关闭：B02两路DCO与数据的建立/保持、真实PCB/线缆偏斜、时钟专用引脚、IO电压、SPI双向转换、ORA/ORB转换、SP2实物版本与速度等级。

AD9268 CMOS默认上升沿捕获是数据手册的接口定义，不等于当前布线已经有足够建立/保持裕量。DCO延时寄存器和捕获相位必须通过台架/时序预算设置。

候选异步FIFO的Gray指针跨域需要逐位同步器、有效最大延时与总线偏斜限制。不能用一条全局`set_clock_groups -asynchronous`掩盖所有问题；AMD指出该异常优先级可能覆盖`set_max_delay`。

上板前必留：`report_cdc`、`report_timing_summary`、`check_timing`、IO标准/电压核对、实际路径延时和两通道样本对应测试。当前均未执行。
