# B08 G2-E01

打开 B08_G2E01.kicad_pro。原理图是元件级候选；PCB有板框/孔/封装/网络及初排，尚无布线。

- Preserves R51 four-pin interface; bipolar supply required.
- Photodiode nominal reverse bias 5V. Current into cathode is sunk to negative bias; output is positive.
- 0..100uA input corresponds approximately 0..1V output. Confirm pickoff power before connecting.
- RF=10k / CF=100p is a ~159kHz feedback pole; reference and PMT channel delays must be aligned.
- This reference signal feeds B02 channel B through its own FDA; not directly a differential ADC input.

状态：NOT_RELEASED。仿真为有限模型证据；没有台架结果。
