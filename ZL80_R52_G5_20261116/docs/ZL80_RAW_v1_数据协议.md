# ZL80 RAW v1：接口与文件格式

修订R52-G5-F01-D01；源代码：`software/zlraw.py`与`software/include/zl80_raw.h`。

## 记录格式
每条16字节，小端。Python结构为`<IQHBB`；C结构体可能有填充，禁止直接写`sizeof(struct)`。

|偏移|位域|长度|字段|
|---|---|---|---|
|0|31:0|4|payload32|
|4|95:32|8|tick64，公共采样时基的计数值|
|12|111:96|2|flags16|
|14|119:112|1|version=1|
|15|127:120|1|record type|

SAMPLE payload低16位为A、高16位为B。0与65535保留，不在RAW阶段裁剪或补偿。不同来源的输出先后次序不是全局时间次序；合并时使用tick和原始事件类型，不能用到达时间替代。

## 类型

|type|name|payload|time_semantics|note|
|---|---|---|---|---|
|0x01|SAMPLE|B[15:0]:A[15:0]|真实aperture时刻|flags见sample_flags|
|0x10/11|SOS上/下沿|line_id|同步后逻辑时间|保留双沿不默认中心法|
|0x12/13|EOS上/下沿|line_id|同步后逻辑时间|对应同一行|
|0x20|测量编码器|signed position32|同步后逻辑时间|bit0变化 bit1索引 bit2非法 bit15初始快照|
|0x21|驱动编码器|signed position32|同步后逻辑时间|同上；不能将分辨率当精度|
|0x30|polygon索引|观察时line_id|同步后逻辑时间|绝对相位对应未标定|
|0x70|START|session_id|开始请求时刻|不等于第一ADC有效时刻|
|0x71|STATUS|sticky faults32|停止控制时刻|faults字段见文档|
|0x72|LOSS|dropped total32|停止控制时刻|非零禁止正式成像|
|0x7F|END|session_id|停止控制时刻|最后一半AXI beat必须TLAST|

## 样本标志

|bit|name|meaning|
|---|---|---|
|0|ADC_A_OR|A通道硬件越界|
|1|ADC_B_OR|B通道硬件越界|
|2|TIME_UNCAL|采样时基未标定|
|3|PAIR_UNVERIFIED|两通道共同采样epoch未验证|
|4|TEST_PATTERN|ADC测试码而非光学数据|
|5|UPSTREAM_LOSS|前端发现丢样或序号错误|

## AXI-Stream
每条记录两个64位beat，低半先发；TKEEP=0xFF；默认256条/4096字节一包。END记录的高半beat总是TLAST，包括不足一包的尾包。TVALID=1且TREADY=0时TDATA/TKEEP/TLAST保持不变。配置DMA与足够接收缓存后再开始采集。

## 会话
START → 两路编码器初始快照 → 样本/同步/编码事件 → STATUS → LOSS → END。采集核心在快照头输出期间也缓存控制事件；样本只在RUN接收。开始和结束控制时间不是ADC有效覆盖区边界。最后一个缺少EOS的扫描段不得补成完整行。

TIME_UNCAL、PAIR_UNVERIFIED、UPSTREAM_LOSS、非零STATUS/LOSS与不单调样本时间必须拒绝正式成像。TEST_PATTERN是测试码，不能作为光学数据。数字检查通过仍不等于计量放行。物理绝对facet未经标定时保持UNKNOWN。

## 归档
文件头8字节ASCII `ZL80RAW1`；后接uint32小端JSON字节长度，再接UTF-8 JSON元数据。随后重复块头`<4sIII`：`BLK1`、块序号、正文长度、CRC32；正文是完整16字节记录的串联。块序号从0连续增加，正文非零且为16的整数倍。当前实现最大JSON为1MiB、最大块正文16MiB。CRC由主机归档层计算，不是FPGA端CRC；它不能证明AXI之前数据未被错误采样。

文件只以独占新建方式写入；任何截断、CRC错误、块次序错误或缺END均报错，不静默填零。真实RAW应另存采集硬件版本、固件哈希、时基校准、ADC输出模式、PMT/AFE设置、标定文件哈希和传感器延迟。示例明确synthetic=true；不得当成台架证据。

## 当前实现边界
没有完整DMA驱动；`import_axis_dump.py`只导入未来testbench产生的离线beat文件。本版几何映射为诊断：暂定92mm SOS/EOS跨度，理想线性X关系，Y由测量编码器插值，不外推，未实现硬件空间重采样、真实f-theta LUT或密度标定。
