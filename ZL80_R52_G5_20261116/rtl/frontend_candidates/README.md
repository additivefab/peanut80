# 未集成的板级前端候选

这里有真实RTL候选，但不是可以直接连接SP2和B02的完整前端。

`adc_cmos_lane.sv`：在每路DCO上捕获数据、OR、32位本地序号，再经Gray FIFO进入logic clk域。ADC引脚与DCO的时序必须来自B02真实板级预算；本模块未验证IOB/时钟路由和跨域约束。

`async_fifo_gray.sv`：二侧共同复位，分别同步释放。不可单侧复位后假装仍为同一session。地址参数至少为2；读为异步FWFT，综合资源与实现待检验。Gray指针各位延时/偏斜约束必须保留。

`adc_pair_guard.sv`：仅检查两个本地序号一致，不会自动丢弃不同序号以强行对齐。不同序号将锁定错误。共同模拟采样epoch需要外部证据，未验证时bit3置位；bit2 TIME_UNCAL在此候选里始终置位。

尚缺的集成层必须完成：
1. 实际B02 ADC配置、双DCO相位、共同计数起点和启停验证。
2. 将DCO域overflow_sticky通过安全同步进入逻辑域；用pair_flags[5]记录上游丢样，不能直接混接域。
3. 根据已验证的共同epoch、样本序号和采样频率产生pair_tick，包含ADC 12周期/额外捕获等总延迟的明确定义。不能直接将FIFO出队tick作为pair_tick。
4. 生成每clk一周期的pair_valid。当前core没有ADC背压输出，前端丢样必须保留标志。
5. 将板级复位与正常stop区分。32位序号回卷会置故障，需要受控重新建session，不能静默续扫。

这三个候选没有在zl80_capture_core中实例化。它们是下一任务的输入，不是已完成的链路。
