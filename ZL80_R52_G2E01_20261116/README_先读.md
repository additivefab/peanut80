# ZL80 R5.2 · G2-E01 电路闭合候选交付包

修订：R52-G2E01-D01；日期：2026-11-16。这里的 G2 是 R5.1 AI 工程路线中的“电路闭合”，不是早期路线中同名的积分筒阶段。

**本批完成四块板的元件级原理图候选、针脚审查、未布线PCB、空间限界和可复算的数值模型；没有把全部八板、厂家SPICE或实物台架标成通过。制造状态：BLOCKED。**

## 先打开什么

- `docs/ZL80_G2E01_设计说明与证据.pdf`：设计选择、模型结果、后续任务与台架方法。
- `docs/ZL80_G2E01_原理图与PCB空间审查.pdf`：四板实际电路图和空间初排，共8页。由同一电路源图独立矢量渲染，不是KiCad原生导出。
- `electronics/projects/B06/B06_G2E01.kicad_pro`：第一块同步接收小板。然后依次B07、B08、B01。

完整解压再打开工程，保留 `electronics/projects/` 与 `electronics/libraries/` 相对位置。不要只复制一个原理图到别处。

## 本批电路

B06/B07：S5971三脚光电二极管 → OPA356 TIA → TLV3501比较器 → 3.3V同步输出。5V输入经TLV75533产生3.3V；保留R5四针J1接口、18×20mm板框与各自孔位。S5971的CASE接地，SHDN接低，反馈/阈值/迟滞/去耦均为实际元件。

B08：S5971 → OPA828，±5V供电、约5V反偏、10k/100p反馈，参考通道低通。保留25×20mm板框和四针接口。

B01：H10720-20针脚模块候选 → OPA828 TIA → AD8138直流差分驱动。基线100k/2.2p；差分电阻比806/499=1.6152；外部0.5V偏置。保留90×50mm板框。PMT插座/引脚方向仍需要实际型号核对。

B02~B05：`downstream/R51_UNCLOSED/` 是**原样保留的未闭合旧稿**，不是本批完成板。新增AD9268并行CMOS针脚审查与独立符号库，不把时钟、电平转换、电源、互锁、运动功能方框伪装成完整电路。

## 关键边界

本批PCB没有铜线、过孔和铺铜，没有Gerber。自动空间初排只是可继续布板的起点，不是模拟性能布局。四个STEP只表示板框、孔与器件空间包络，不是厂家精细实体，也不是KiCad三维导出。B06/B07探测器位置有差别，必须由G1复核安装支架。

原理图使用真实网络标签连接；PDF中相同名称即相同电气网络。PWR_FLAG仅声明台架/板外供电的边界，不表示本板已经设计出该电源。真实模块/IC针脚类型已经区分input/output/power_in/power_out/bidirectional/no_connect；接插件和电阻电容保持passive属于正常语义。

## 实际证据与未执行项

已执行：有限单极点运放数值模型、B06幅度时间偏移、B01反馈补偿与ADC余量、B08带宽、35项Python测试、独立原理图文字图网络回读、PCB焊盘网络对照、STEP包络形体有效性检查。

未执行：KiCad本机打开/重保存/ERC/DRC；ngspice/LTspice和厂家宏模型；实物台架；真实光脉冲、温漂、电机EMI、扫描MTF/DCS。相关状态为NOT_RUN或OPEN，台架记录的实测栏故意留空。

有限模型的结果不是器件保证值。当前固定阈值B06在假定5~100uA脉冲扫幅中有约306ns前沿峰峰偏移；脉冲中心法约23ns，但真实光脉冲对称性未验证。79.58ns是G1暂定5um对应的时间预算；确定性峰峰偏移不能直接和随机RMS混成一个合格结论。

B01的100k/2.2p高增益档在20pF假设下，单极点模型带宽约0.84MHz，0.1%阶跃整定约1.29us，长于0.796us名义像素驻留。不能据此宣布整机失败或通过，必须测真实边缘/频响并纳入空间MTF预算。

## 本地使用

安装已核对版本的KiCad（本包采用8系文件语法，较新版本打开后建议另存副本）及Python。先备份，不覆盖R5.1基线。

```bash
python -m venv .venv
# Windows激活：.venv\Scripts\activate
# Linux/macOS激活：source .venv/bin/activate
python -m pip install -r requirements.txt
python simulations/run_models.py
python tools/check_native_graph.py
python tools/run_checks.py
python tools/native_validate.py
```

`native_validate.py`可通过`--kicad-cli`和`--ngspice`指定安装路径；找不到工具就写NOT_RUN。PCB无布线时DRC出现未连接项属于预期，不能删除规则或忽略错误来“通过”。

源文件修改入口：`tools/design_circuits.py`。修改后执行`python tools/design_circuits.py`、`python tools/build_kicad.py`重建四板；后续在KiCad手工修改的文件不能直接被重建脚本覆盖，应先建立Git分支并明确哪个文件为权威源。

## 推进顺序

先用真实KiCad检查B06/B07，复核S5971实物方向和反馈布局，制作可审查的试验板并完成TB01~TB06。B08与B01可以并行做等效电流台架，但在B03/B02尚未完成时，必须由已验证的台架供电/参考替代板外接口。获得实际脉冲、噪声和增益需求后，再闭合B02、B03、B04、B05，不先将全机设计当成制造版本。
