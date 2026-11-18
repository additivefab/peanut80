# ZL80 ADF50 V0.6：评估第三方 V05 包并修改设计

修订 ADF50-V0.6-PDR，2026-11-17。初步设计：名义几何和解析计算，没有样机和实测，不是制造放行。现行方案；取代 V0.4。V0.1–V0.4 和第三方包 `ZL80_ADF50_V05_20261117` 保持原样。

设计条件：进深约 700 mm，高度 650 mm 以内，片不能先朝外走再折回。结果：320×680.4×567.4 mm（高度自脚底 Z=−8 起算）。

先看 `docs/ZL80_ADF50_V06_评估与修改说明.pdf`（或同名 .md）。

| 路径 | 内容 |
|---|---|
| `docs/` | 评估与修改说明（md / pdf）、整机侧视布局图 |
| `engineering/parameters.json` | 全部输入假设、设计条件、G3 事实、V05 引用值 |
| `engineering/calculate.py` | 侧视几何、分片力学、弯道受力和托辊支撑、交接与计量窗口、包络、架构对比、节拍 |
| `engineering/*.csv` | 架构对比、分片配方、弯道受力、弯道托辊、交接与计量、节拍、路线点位 |
| `mechanical/` | 零件级机械设计：86 个件号的 STEP、总装与部件 STEP、侧板 DXF、BOM、外购件清单、14 页图册、干涉结果 |
| `control/` | 状态机参考模型（改自 V05 包），含示例 |
| `ecr_g3_01/` | 已批准的 ECR-G3-01：出口上压辊磁编码器（4 个零件、STEP、干涉检查、计量覆盖、变更登记、PDF） |
| `ecr_g3_01/electrical/`（FPGA 侧见主目录 `ZL80_R52_G5_HF_20261117`） | ECR 配套：B05 第三路编码器输入、FFC、圆线 W13、G5 接口变更清单 |
| `tests/` | 74 项测试：方案计算 22、机械模型 14、控制参考 21、ECR 8、ECR 电气 9 |

复算（机械部分需要 cadquery、ezdxf、pymupdf、reportlab）：

```bash
python3 engineering/calculate.py
python3 engineering/write_tables.py
python3 tests/test_adf50_v06.py
python3 tests/test_control.py
python3 ecr_g3_01/source/build_ecr.py
python3 ecr_g3_01/source/calc_ecr.py
python3 tests/test_ecr.py
python3 mechanical/source/build_mechanical.py
python3 tests/test_mechanical.py
```

旧版 V01–V05（含第三方评审包 V05_20261117）和原 G5 包已于 2026-11-17 删除，只保留本版；取舍结论见 `docs/ZL80_ADF50_V06_评估与修改说明.md`。
