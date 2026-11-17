# 数据参考实现

R5.2 短时调试归档使用 [G5 ZL80RAW1](../ZL80_R52_G5_20261116/docs/ZL80_RAW_v1_数据协议.md)。本目录的 ChunkWriter 是 R5-PDR1 格式。G5 的 inspect 结果仅供诊断，正式成像验收须另查测试码和采样覆盖，见 [融合设计基线第 8 节](../docs/ZL80_R52_融合评估与设计基线.md)。

`reference_model.py` 为Python标准库参考。ChunkWriter按uint64行号/uint16数组写不可覆盖chunk，并保留SHA256与quality元数据；不是最终文件标准、数据库或DICONDE认证。

每条物理扫描记录facet、SOS/EOS时刻、编码位置、ADC码、功率参考、增益、温度、质量标志。增益/标定ID按块索引也可以，但必须能回溯到每样本。二维重采样先保留坐标和有效性；遇到缺口标注gap，不插出合格Master。停止请求时关光、受控停片并保留边界和未写完块的状态。

线性/LOG输入不能混用：LOG必须先根据校准反演为线性信号再扣除暗场。示例函数禁止把非正透射率强行夹到最黑灰度并宣称测量有效。

Host预览/AI输出只在派生目录；Raw和Calibrated Master不覆盖。软件还缺实时采集驱动、DMA/GigE回压、稳健恢复、标定LUT与实际二维重采样性能实现。
