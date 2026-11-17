# 可编辑源文件与复核入口

CAD生成器：`cad/source/build_cad.py`，输入为本包engineering/parameters.json及electronics/board_definitions.json。需要Python、cadquery、ezdxf。重建会覆盖CAD导出及几何检查记录，请先复制工作目录。

板框/针脚网表生成器：`tools/source/build_electronics.py`。图册生成器按`render_design.py`、`patch_diagrams.py`顺序运行；后者补入明确比例的积分筒剖面并合并PDF。需要numpy、Pillow、cairosvg、PyMuPDF及本机中文字体（字体不随包提供）。`build_report.py`生成DOCX；PDF可通过本机Word/兼容办公软件导出。新导出必须重新做版面检查。

`check_integration.py`用于核心名义B-rep与关键器件空间盒复核，不是容差/软线束/安全认证工具。它不能代替KiCad原生导入、ERC/DRC。

纯Python预算：`python engineering/calculate.py`。参考数据链测试：`python -m unittest discover -s tests -v`。SystemVerilog和XDC未经过综合/时序分析。

XLSX为可编辑设计预算，公式与输入已保留。修改JSON或CAD源后，Excel、说明书、图纸与BOM需同版本更新；本包不是自动PLM系统。
