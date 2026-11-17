# ZL80 R5.2 / G3 四辊输送与机械集成

**版本：R52-G3-M01-D01；日期2026-11-16。状态：DESIGN_REVIEW_NOT_FOR_PRODUCTION。**

本次是机械开发交付，不是实机验证或制造放行。实测速度、张力、划伤和温升记录均为NOT_RUN。

## 直接打开

- `START_HERE.html`：离线导航。
- `cad/assemblies/ZL80_G3_FourRoller_Assembly.step`：四辊闭合总成。
- `cad/assemblies/ZL80_G3_FourRoller_Released.step`：上辊抬升5mm的总成。
- `cad/assemblies/ZL80_G3_FourRoller_Exploded.step`：爆炸位置；不能用爆炸坐标加工。
- `cad/assemblies/ZL80_G3_Core_Review.step`：包含R5光学和板框的去罩回装。
- `cad/assemblies/ZL80_G3_Integrated_Context.step`：机箱、基座和内部上下文。
- `drawings/ZL80_G3_机械加工与装配图册.pdf`：23页，所有加工要求为候选。
- `docs/ZL80_G3_机械设计与集成说明.pdf`：11页。
- `docs/ZL80_G3_速度张力计算与验证报告.pdf`：7页，计算/几何已执行，台架未执行。
- `engineering/ZL80_G3_选型BOM公差与验证.xlsx`：13个工作表、116个公式。

## 九项交付的索引

|交付项|目录/文件|
|---|---|
|四辊完整STEP|cad/assemblies；零件在cad/parts|
|电机、轴承、联轴器选型|engineering/selection.csv与工作簿“选型”|
|辊轮加工图|图册D12-D15；G3-R01/R02/R03/R04 STEP|
|辊轮材料矩阵|engineering/roller_material_DOE.csv；18组×3重复|
|机箱钣金与基座|图册D09-D11/D18-D20；7个mm单位切割DXF|
|线束和走线|D21、engineering/harness.csv、config/harness_routes_G3.json|
|关键公差|engineering/critical_tolerances.csv；17项|
|装配公差链|D05/D07/D22、engineering/tolerance_stack.csv|
|速度与张力验证报告|docs/速度张力报告；validation/test_matrix.csv；真实数据分析程序|

## 重要设计与变更

1. 80mm片宽、100mm光学预留、片面名义Z110、两组辊中心Y±42保留。辊成品Ø20×100；入口随动测量，出口单电机牵引。
2. 这不是双电机恒张力伺服。外置收放卷提供低张力；上辊夹紧力并不是片张力。
3. 联轴器候选NBK MJC-20CS-WH-5-6，OD20、**总长30**，不是原16长占位。电机前面X121.5，轴端插入按D07。
4. 基座改为**300×288×6**；保留B04孔位，解决旧280深底板后排孔开边。脚位改X±132/Y±120。旧DXF不能混用。
5. 包胶按粘结/硫化后整辊磨削，不采用自由滑移胶套。材料和工艺仍需DOE批准。
6. 4096PPR的计数量化3.835μm不等于精度。AMT原厂0.2°约对应34.91μm/20mm辊，5μm位置指标未闭合。
7. 4.1N是两根弹簧贡献；0.2kg移动自重假设加上后约6.06N。实际法向力必须测力，不能照公式直接认定。
8. G2新板卡空间STEP在sources/G2_reference原样保留，未冒充已回装。XZ板法向及连接器需ECAD-MCAD核对。

## 软件与复算

STEP可用支持STEP装配的CAD打开。所有模型单位mm。FreeCAD用户可先导入STEP；也可运行`cad/freecad/Open_G3_Review.FCMacro`，选完整包根目录，生成本机.FCStd审查树。
**宏未在本环境运行；它导入实体和位姿，不恢复草图约束或生产特征历史。**

仅解析预算与测试需要Python标准库：

```bash
python tools/build_engineering.py
python tools/run_checks.py
```

CAD重建需要`requirements_geometry.txt`所列依赖：

```bash
python -m venv .venv
# 激活虚拟环境后
python -m pip install -r requirements_geometry.txt
python cad/source/build_mechanics.py
python tools/check_geometry.py
python tools/check_release_positions.py
python tools/build_engineering.py
python tools/run_checks.py
```

图册/报告脚本依赖reportlab、svglib、numpy、Pillow和本机中文字体。字体仅供本机使用，不随包分发。

**参数修改边界：**JSON提供当前接口与计算输入，但源程序仍含固定几何值；不是所有特征都已参数化。修改后必须核对CAD源码、实例坐标、BOM、图纸及测试，而非只改JSON或Excel。Excel不会反向修改源文件；已有PDF/XLSX也不会自动刷新。

## 台架数据

`validation/templates/transport_raw_EMPTY.csv`是空模板，不能直接用来获得通过结果。真实数据副本至少包括time_s、独立reference_position_mm和标定tension_N，正式试验按测试矩阵。

```bash
python tools/analyze_transport.py my_measured_data.csv --target-speed 15 --output my_analysis.json
```

脚本拒绝空值、不递增时标和不足数据；输出ANALYZED_NOT_REVIEWED，保留原始数据，不做隐藏平滑。程序用的合成数据只用于单元测试，不能充当实测。

## 已执行和未执行

- 94种STEP形体有效；238个上下文实例。
- 静态324候选相交对，54处预期螺纹名义重叠，未解释重叠0；排除项见日志。
- 上辊0/2.5/5mm位置各170候选对，未解释重叠0；不是连续扫掠或弹簧物理仿真。
- 30项Python测试通过，含真实记录分析程序的合成输入检查和空模板拒绝。
- FreeCAD原生、DFM、真实器件尺寸复核、连续运动、台架和安全验收均未完成。
- **制造状态BLOCKED**。不提供G-code，不将未批准DXF/STEP作为制造放行。

## 先审哪些文件

D04片道接口 → D05轴承定位 → D07驱动尺寸链 → D09基座变更 → D21走线 → D22间隙公差。
关闭基座ECR、采购件孔位、G2朝向、配合/胶料工艺和安全测试后，再决定首轮试制范围。
