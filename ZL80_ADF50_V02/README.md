# ZL80 ADF50 V0.2 · 50 张自动馈片重新设计

2026-11-16 / ADF50-V0.2-PDR / **初步设计，不是制造放行**。在 V0.1（`../ZL80_ADF50_V01`，保持原样）基础上重新设计。

## 先看

- `docs/ZL80_ADF50_V02_评估与重新设计.pdf`（或同名 .md）：对 V0.1 的评估和 V0.2 方案。
- `docs/ADF50_V02_布局.png`：侧视布局。
- `engineering/V01_V02_对比.csv`：两版逐项对比。

## 与 V0.1 的四处不同

1. 片堆靠在托板上，拾取辊用配重臂压自由面；拾取界面压力不随片数变化。
2. 被动斜坝代替托趾和主动剥离靴。
3. 路径上折 115° 回到扫描仪上方：包络 320×785×639 mm（V0.1 为 350×1100×550），占地减 35%，高度增 89 mm。
4. 扫描段两只下辊单电机同步带联动。

节拍按 R5.2 三档扫描模式重算。状态机、账本、除静电、整张双张确认规则沿用 V0.1。

## 重算与测试

```
python engineering/calculate.py
python engineering/draw_layout.py
python -m unittest discover -s tests -v
```

以上只用 Python 标准库。`cad/build_envelope.py` 需要 cadquery，`docs/build_pdf.py` 需要 reportlab。

## 证据边界

全部是假设输入下的计算和名义外形占位。15 项测试只检查算例和几何自洽。斜坝分片、配重压力下的划伤、弯道推片、双张检测、50 张批次可靠性都没有实物验证。没有机构零件 CAD、B10 电路或硬件测试。
