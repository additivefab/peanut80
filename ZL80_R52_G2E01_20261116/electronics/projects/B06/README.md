# B06 G2-E01

打开 B06_G2E01.kicad_pro。原理图是元件级候选；PCB有板框/孔/封装/网络及初排，尚无布线。

- 3V3 push-pull SYNC; J1 pin1 remains +5V input, NOT 3V3 input.
- S5971: 1=K, 3=A, 2=CASE. Case tied GND. Reverse bias ~1V; no 100MHz claim.
- R3 adds positive feedback; TLV3501 SHDN tied low. Full light pulse is outside image ROI.
- Threshold/optical amplitude not measured. 5um timing budget is NOT yet passed.
- C6 at U1 and C7 at U2. Keep PD_SUM/feedback short; do not connect a long test lead to PD_SUM.
- Use short grounded harness for PoC. Long cable requires a differential link change request.

状态：NOT_RELEASED。仿真为有限模型证据；没有台架结果。
