# ZL80 ADF50 V0.3：同平面直通进片（并入 ZL80 本体）

修订 ADF50-V0.3-PDR，2026-11-16。初步设计，只有计算和名义外形占位，不是制造放行。取代 V0.2（折回式，已撤回）和 V0.1；那两个文件夹保持原样。

先看 `docs/ZL80_ADF50_V03_一体化直通进片设计.pdf`（或同名 .md）。

| 路径 | 内容 |
|---|---|
| `docs/` | 设计说明（md / pdf）、整机侧视布局图、进片区放大图 |
| `engineering/parameters.json` | 全部输入假设 |
| `engineering/calculate.py` | 分片力学、路线站位、包络、架构对比、节拍 |
| `engineering/*.csv` | 架构对比、分片配方、节拍、路线站位、风险与门槛 |
| `cad/build_envelope.py` | 外形占位体与 R5 整机干涉检查（需 cadquery） |
| `cad/ADF50_V03_envelope.step` | 外形占位体 |
| `tests/` | 17 项测试；干涉结果 `envelope_interference.json` |
| `control/` | V0.1 状态机与台账的原样拷贝，尚未按 V0.3 流程修改 |

复算：

```bash
python3 engineering/calculate.py
python3 engineering/write_tables.py
python3 tests/test_adf50_v03.py
```
