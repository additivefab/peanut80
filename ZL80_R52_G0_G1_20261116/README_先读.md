# ZL80 R5.2 · G0与G1交付包

修订：R52-G01-D01 / 2026-11-16。请完整解压后打开 `START_HERE.html`。

## 交付状态

文件包已形成；G0需要审批才能冻结，G1仍需供应商真实镜头模型和台架验证。当前发现名义镜面场边截光风险。制造状态：NOT_RELEASED。

## 先看文件

- `docs/ZL80_G0_G1_工程交付总册.pdf`：22页合订阅读版。
- `docs/ZL80_G0_需求与接口基线.docx/.pdf`：7页，需求/接口/来源/冻结条件。
- `docs/ZL80_G1_扫描光学头预设计.docx/.pdf`：8页，计算/风险/CAD/验证。
- `engineering/ZL80_G0_G1_Master_Parameters.xlsx`：10个工作表，29项需求、14项接口、13项风险、31个参数、6组扫描场景。
- `drawings/ZL80_G0_G1_接口与时序图册.pdf`：4张矢量接口/光路/收光/时序图。
- `rfq/ZL80_G1_扫描头联合询价书.docx/.pdf`：3页，附供应商答复CSV、视场点CSV。
- `cad/G1_Inherited_ScanHead_Review.step`：继承R5的扫描头参考总装，不是制造图。
- `src/scan_model.py`：可复算解析模型及名义正六面镜主光线追迹。

## 参数主源

`config/master_parameters.json` 是唯一机器可读主参数。Excel允许场景试算，但不会回写JSON、CAD或文档。任何跨版本改动必须使用变更单并更新受影响衍生文件。本包保留50um采样、100mm EFL、3000rpm等值的假设状态；未知WD/入瞳/MPN用null，不填0。

## 运行计算（无需第三方库）

```bash
python tools/rebuild_calculations.py
python tools/run_checks.py
```

第一条更新 `results/` 的CSV/JSON；第二条运行32条测试并写日志/状态。它们不运行真实镜头软件、不做台架、不改CAD/XLSX/PDF。

## 查看和重组CAD

任意支持STEP的CAD软件可直接打开总装。需要FreeCAD对象树时，运行 `cad/freecad/open_G1_review.FCMacro`，生成 `generated/` 下FCStd；本环境没有执行FreeCAD。对象是可选择/移动的导入实体，不恢复全部参数化设计历史。

需要从部件重组STEP/DXF时，创建独立虚拟环境，安装 `requirements-optional.txt` 后运行：

```bash
python tools/build_cad_review.py
```

22个部件STEP从R5.1原样继承，26个装配实例仍用R5全局坐标。局部片面坐标转换为 `(x,y,z+110)`。`G1_ChiefRay_InputGeometry.step` 只有进入镜头前的名义射线和理想焦面标记，不是真实透镜追迹。

## 关键计算结果

六面、3000rpm、EFL100、50um：300行/s；80mm有效扫描1.273240ms；瞬时像素率1.256637MHz，平均输出0.48Mpixel/s；单像素驻留0.795775us；Y进片15mm/s；一条ROI内仍移动19.10um。

本模型R20mm/束径5mm在+50mm场边的1/e2足迹余量约-0.093mm，必须处理。测试通过只是验证程序暴露该风险，不能称镜面设计合格。完整光斑/MTF/CRA需要供应商处方和实测。

## 不包含/未完成

不包含真实f-theta处方、伪造Zemax文件、完整PCB/Gerber、可上板bitstream、精密转子加工图。没有实测光斑/MTF/密度性能、完整干涉/公差或安全等级验证。G2-G7只保留接口，不在本包中冒充完成。

## 下一步

先签G0建议指标，再发联合RFQ，优先关闭镜面孔径/低速稳定性和镜头WD/入瞳/处方，之后执行10项G1台架测试。任务文件在 `ai/tasks/`。
