# B01 G2-E01

打开 B01_G2E01.kicad_pro。原理图是元件级候选；PCB有板框/孔/封装/网络及初排，尚无布线。

- PMT current is modeled as a sink at PMT_I; verify output polarity with manufacturer/sample.
- RF/CF are solder-selected gain pairs: baseline100k/2.2p; alternatives10k/6.8p and1k/22p.
- AD8138 differential gain=806/499=1.6152, offset=0.5V. 0..1V TIA maps to +/-0.8076V differential.
- ADC full scale assumed2Vpp differential, SENSE=GND. ADC_VCM is supplied by B02 (nominal0.9V).
- OPA828 and FDA decouplers must sit at their power pins. Do not parallel a LOG amplifier at PMT_I.
- PMT socket mechanical pattern is provisional: inherited pads are NOT manufacturer-approved sockets.

状态：NOT_RELEASED。仿真为有限模型证据；没有台架结果。
