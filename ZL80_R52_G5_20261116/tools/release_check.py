from pathlib import Path
import json,sys
R=Path(__file__).resolve().parents[1]
reasons=['B02 coherent dual-channel ADC adapter not integrated',
 'ADC aperture epoch and sensor delay not measured','SP2 Vadj/IO translators/pin map not approved',
 'No approved Zynq PS/DDR/AXI DMA integration','No placed-and-routed timing/CDC report',
 'G4 B01/B02/B03/B04/B05 unresolved circuit and safety issues',
 'No electrical, optical, laser/interlock or transport bench qualification']
report={'status':'BLOCKED','bitstream_allowed':False,'laser_or_motor_enable_allowed':False,'reasons':reasons}
(R/'validation/results/release_gate.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2));sys.exit(2)
