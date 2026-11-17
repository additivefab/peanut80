# ZL80 ADF50 V0.4：单向走片，两处 R80 弯道（并入 ZL80 本体）

修订 ADF50-V0.4-PDR，2026-11-16。初步设计，只有计算和名义外形占位，不是制造放行。现行方案；取代 V0.3（直通，995 mm 放不下）、V0.2（折回式，已撤回）和 V0.1，那三个文件夹保持原样。

设计条件：进深约 700 mm，高度 650 mm 以内，片不能先朝外走再折回。结果：320×695×557 mm。

先看 `docs/ZL80_ADF50_V04_单向走片一体化设计.pdf`（或同名 .md）。

| 路径 | 内容 |
|---|---|
| `docs/` | 设计说明（md / pdf）、整机侧视布局图 |
| `engineering/parameters.json` | 全部输入假设和设计条件 |
| `engineering/calculate.py` | 侧视几何、分片力学、弯道受力、包络、架构对比、节拍 |
| `engineering/*.csv` | 架构对比、分片配方、弯道受力、节拍、路线点位、风险与门槛 |
| `cad/build_envelope.py` | 外形占位体与 R5 整机干涉检查（需 cadquery） |
| `cad/ADF50_V04_envelope.step` | 外形占位体 |
| `tests/` | 19 项方案测试 + 10 项机械模型测试；干涉结果 `envelope_interference.json` |
| `mechanical/` | 零件级机械设计：77 个件号的 STEP、总装、侧板 DXF、BOM、外购件清单、13 页图册、机械设计说明 |
| `control/` | V0.1 状态机与台账的原样拷贝，尚未按 V0.4 流程修改 |

复算：

```bash
python3 engineering/calculate.py
python3 engineering/write_tables.py
python3 tests/test_adf50_v04.py
python3 tests/test_mechanical.py
```
