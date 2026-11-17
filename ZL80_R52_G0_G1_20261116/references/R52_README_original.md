# ZL80 R5.2 全套工程设计文件包

**项目：80mm连续式工业射线底片扫描仪**  
**版本：R5.2 / 2026-11-15**  
**状态：初步工程设计，不是加工/投板放行版。**

## 1. 核心方案

635nm CW激光 → 准直/整形 → 六面旋转多面镜 → f-θ镜头 → 连续走片胶片 → 顶部矩形狭缝 → 横置积分筒 → -Y径向侧窗 → PMMA导光件 → H10720-20单PMT → OPA828 TIA/AD8138 → AD9268双ADC → Zynq-7020 FPGA。

80mm为有效成像宽度，100mm为光学扫描预留，SOS/EOS标称92mm。积分筒内腔Ø40×120mm，狭缝104×1.2mm，侧窗8×10mm，PMMA 8×10→5.2×5.2×32mm。

## 2. 建议先看这些文件

1. `docs/ZL80_R5.2_总体工程设计说明.pdf` — 总体设计与边界。
2. `mechanical/drawings/ZL80_R52_机械关键零件与接口图.pdf` — 12张机械关键零件/接口图。
3. `optics/drawings/ZL80_R5.2_光学设计与预算报告.pdf` — 扫描几何、积分筒、PMT光子预算。
4. `electronics/drawings/ZL80_R5.2_电气设计与FPGA接口参考图册.pdf` — B01…B08功能级电气架构。
5. `engineering/ZL80_R5.2_工程参数_公差_BOM_光子预算.xlsx` — 参数、扫描时序、光子预算、器件选型、PCB、公差和风险。
6. `mechanical/step/ZL80_R52_OptoMechanical_Review.step` — R5.2关键光机电空间装配。
7. `mechanical/freecad/build_r52_review_assembly.FCMacro` — 在本地FreeCAD中导入STEP并保存FCStd审查工程。
8. `electronics/firmware/rtl/` — FPGA RTL起点；`electronics/pinmap/` — SP2 V1.3B XDC草案。

## 3. 目录结构

- `mechanical/cadquery/`：参数化零件生成脚本。
- `mechanical/step/`：27+个R5.2关键零件/接口STEP和评审总装。
- `mechanical/dxf/`：关键零件二维DXF。
- `mechanical/drawings/`：机械PDF和PNG。
- `mechanical/tolerances/`：关键公差和装配公差链。
- `mechanical/assembly/`：坐标、PCB板位置、器件空间包络、装配顺序。
- `optics/`：参数、扫描时序、积分筒Monte Carlo、PMT光子预算、RFQ。
- `electronics/`：B01…B08参考电路、SPICE、PCB叠层、SP2 pinmap、XDC和FPGA RTL。
- `docs/`：总体设计、机械/光学/电子说明、制造发布清单。
- `engineering/`：BOM、功耗、风险、验证矩阵、Excel和图表脚本。
- `references/user_sources/`：用户提供的拆机记录、PPT和SP2原理图。
- `references/vendor_sources/`：官方数据表链接。
- `validation/`：几何、计算和文件检查。

## 4. 软件环境

推荐 Windows 11 + Python 3.12/3.13 + FreeCAD 1.1.x + KiCad 9/10 + LTspice + AMD Vivado（版本需与Zynq-7020/SP2工程匹配）。Blender用于外观渲染，不作为加工CAD主软件。

Python依赖：`pip install -r requirements.txt`。CadQuery安装请按平台选择官方wheel/conda环境；FreeCAD自带Python与普通Python环境分开管理。

## 5. 重新生成衍生文件

在包根目录运行：

```bash
python tools/rebuild_calculations.py
```

此命令重建STEP/DXF、扫描/积分筒模型结果、图表、Excel和报告，并运行Python/CAD几何检查。它不会运行FreeCAD GUI、KiCad ERC/DRC、Vivado综合/STA、LTspice厂商模型或物理台架测试。

## 6. 在FreeCAD中生成原生审查工程

1. 安装FreeCAD。
2. 打开FreeCAD → Macro → Macros。
3. 选择 `mechanical/freecad/build_r52_review_assembly.FCMacro` → Execute。
4. 宏将导入 `mechanical/step/*.step`，创建对象树并保存 `mechanical/freecad/ZL80_R52_Review_Assembly.FCStd`。
5. 该FCStd是从STEP导入的审查工程，不等于已完成全部草图约束、参数驱动、运动副和GD&T的制造原生模型。

## 7. 在KiCad/Vivado中使用

- `electronics/pinmap/ZL80_R5_2_SP2_V13B_draft.xdc` 是SP2 V1.3B约束草案。必须核对实物丝印、J5/J6针脚和Bank33 VADJ；J6/Bank33设1.8V是ADC数据直连前提。
- B01…B08的电路说明、SPICE和RTL是功能级设计输入；当前没有完整布线/制造Gerber。必须完成真实MPN、ERC/DRC、SI/PI、STA、CDC和上板测试。
- `electronics/firmware/tb/run_iverilog.sh` 可在安装Icarus Verilog后运行RTL testbench；当前生成环境未执行。

## 8. 关键假设和安全边界

- 635nm片面功率50µW、积分筒收光效率5%、H10720-20在Vcont=0.5V时增益约1000均为光子预算假设/曲线数量级，不是实测。
- f-θ EFL=100mm、polygon 300…3000rpm、内胆反射率0.90/0.95/0.98均为设计/仿真假设。
- 高速polygon转子必须由专业供应商提供并做动平衡、超速和防护；不允许根据STEP包络自行加工旋转转子。
- H10720-20集成高压，PMT仍需封闭防触及；激光硬件互锁和机械快门不得只依赖FPGA软件。
- 未经制造发布检查清单签署，不得投板、加工或对外承诺性能。
