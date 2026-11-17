# ZL80 G4｜PCB与结构联动首批工程包

修订：R52-G4-E02-D01；日期：2026-11-16。

**本包是工程审查候选，不是制造放行。** G4整体尚未完成：B06/B07/B08已生成实际铜线候选，B01仅关键网；B02—B05仍未闭合。没有KiCad原生ERC/DRC、厂家SPICE、实物台架或制造批准。制造状态为BLOCKED。

## 快速入口
- `START_HERE.html`：离线浏览。
- `docs/ZL80_G4_PCB与结构联动设计说明.pdf`：10页设计说明与证据。
- `drawings/ZL80_G4_PCB与装配审查图册.pdf`：9页真实PCB铜线/STEP投影/接口图。
- `docs/ZL80_G4_四板原理图审查.pdf`：4页独立矢量原理图。
- `engineering/ZL80_G4_接口变更与板卡验证.xlsx`：12个工作表；公式预算不自动驱动CAD。
- `electronics/projects/B06/B06_G4.kicad_pro`：建议最先用KiCad打开。
- `cad/assemblies/ZL80_G4_Core_Integration.step`：去罩回装总装。
- `cad/assemblies/ZL80_G4_G3_Integration.step`：含机箱上下文。
- `cad/assemblies/ZL80_G4_4Boards_Installed.step`：四块PCB的安装坐标模型。

## 交付完成度
|对象|本轮结果|未完成项|
|---|---|---|
|B06|336条铜线段、25过孔；几何回读未连0|原生解析/填铜/ERC/DRC/回流/台架|
|B07|354条铜线段、33过孔；几何回读未连0|同上；光轴与实物极性复核|
|B08|212条铜线段、9过孔；几何回读未连0|同上；背面运放装配与参考光台架|
|B01|72条关键网铜线段、0过孔|14网络共43条最少连接关系、插座定型、台架|
|B02—B05|仅保留未闭合基线|真实电路/选型/原理图/PCB/验证均需继续|

PCB内层地平面已定义但没有伪造填充多边形。请在KiCad填铜、保存，再执行原生验证。断网为零不等于电气、噪声、回流或生产合格。

## 打开方式
完整解压，不移动单个PCB。KiCad使用File/Open打开对应`.kicad_pro`，板卡库和3D模型使用相对路径。若原生程序提示解析/版本差异，保留日志，不覆盖唯一原始候选。

STEP可用FreeCAD或其他机械CAD导入。`cad/freecad/import_G4.FCMacro`可生成导入审查FCStd；这不是恢复参数化特征历史。机架坐标单位为mm。局部板坐标见`board_transforms.json`；不要将局部STEP当作已经安装的模型。

## 可复现工具
```bash
python -m pip install -r requirements.txt
python tools/run_checks.py
python tools/native_validate.py
python tools/release_check.py
```
后两项缺失工具/不具备制造条件时返回非零，属预期，不要删掉门禁。

原生KiCad执行器可以显式指定：
```bash
python tools/native_validate.py --kicad-cli "C:/Program Files/KiCad/9.0/bin/kicad-cli.exe"
```
这里是路径格式示例，不要求该版本；填写实际安装路径。先原生填铜。脚本不生成Gerber。

重建候选：`python tools/rebuild_candidates.py`。源头是`prepare_design.py`中的明确布局与继承电路，`route_candidates.py`产生候选铜线。重建不自动刷新PDF和Excel；PDF可另运行`render_drawings.py`、`render_schematic_pdf.py`、`build_report.py`，工作簿需同步审核更新。

## 已执行与未执行证据
已执行：233针脚原理图网络回读；四板铜几何/焊盘网络回读；三块小板连通；123个新STEP对象有效；与G3保留实体交叉检查；29项Python测试。详见`validation/results`。

未执行：KiCad原生解析、ERC/DRC及地平面填充；FreeCAD原生打开/保存；厂家SPICE；任何实物测试。台架矩阵12项全部NOT_RUN，原始记录为空。

8处PMT针脚与插座占位重叠已保留为预期接合，不是配合通过。0.9mm插座尾针孔不能直接解释为裸PMT针脚孔。J2插拔空间已调整，但真实对接件与线束尚未冻结。

## 安全与设计门禁
先确认供电、电平、接地、引脚方向及器件型号，再按批准台架方案试验。B06/B07的SYNC为3.3V候选，不能直接接1.8V域。B03/B04未闭合，禁止把本包作为整机供电/激光互锁实现。真实激光、PMT与电机测试要遵守实验室和设备安全规程。

## 继续开发优先级
先完成B06原生闭环→封装/MPN/清洗与DFM→小板受控样件与恒幅/变幅同步测试。B07/B08沿同一流程。然后闭合B03供电/偏置和B01余下网络，再推进B02 ADC与B04/B05。G1对光和G3实物装配必须共同签署坐标变更。
