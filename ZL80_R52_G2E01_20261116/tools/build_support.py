from pathlib import Path
import json,csv,sys,shutil
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from build_kicad import libsym,S
from design_circuits import p
# Primary-source mapping, not an inferred translation from the draft symbol.
mp={1:('CLK+','input'),2:('CLK-','input'),3:('SYNC','input'),22:('ORB','output'),23:('DCOB','output'),24:('DCOA','output'),43:('ORA','output'),44:('SDIO','bidirectional'),45:('SCLK','input'),46:('CSB','input'),47:('OEB','input'),48:('PDWN','input'),51:('VIN+A','input'),52:('VIN-A','input'),55:('VREF','bidirectional'),56:('SENSE','input'),57:('VCM','output'),58:('RBIAS','passive'),61:('VIN-B','input'),62:('VIN+B','input'),65:('EP_AGND','power_in')}
for i,k in enumerate([4,5,6,7,8,9,11,12,13,14,15,16,17,18,20,21]):mp[k]=(f'D{i}B','output')
for i,k in enumerate([25,26,27,29,30,31,32,33,34,35,36,38,39,40,41,42]):mp[k]=(f'D{i}A','output')
for k in [10,19,28,37]:mp[k]=('DRVDD','power_in')
for k in [49,50,53,54,59,60,63,64]:mp[k]=('AVDD','power_in')
assert len(mp)==65
rows=[dict(pad=str(i),manufacturer_pin='0 / EP' if i==65 else str(i),name=mp[i][0],electrical_type=mp[i][1],mode='PARALLEL_CMOS_1V8',source='V07 pp13-14',note='RBIAS passive reflects external bias resistor terminal; datasheet I/O. EP renumbered65 only for footprint.' if i in [58,65] else '') for i in range(1,66)]
with (ROOT/'engineering/AD9268_CMOS_pin_audit.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
# Dedicated symbol is deliberately not placed into the incomplete B02 board.
S['AD9268_CMOS_AUDITED']=dict(shape='box',fp='AD9268_PACKAGE_TBD',source='V07',pins=[p(i,mp[i][0],mp[i][1],-35.56 if i<=33 else 35.56,(17-(i-1)%33)*2.54,0 if i<=33 else 180) for i in range(1,66)])
# Custom tall symbol body for ADC, replace generic20mm body.
txt=libsym('AD9268_CMOS_AUDITED',False)
old='(polyline (pts (xy -10.16 10.16) (xy 10.16 10.16) (xy 10.16 -10.16) (xy -10.16 -10.16) (xy -10.16 10.16))'
new='(polyline (pts (xy -30.48 48.26) (xy 30.48 48.26) (xy 30.48 -43.18) (xy -30.48 -43.18) (xy -30.48 48.26))'
txt=txt.replace(old,new).replace('ZL80_G2:AD9268_PACKAGE_TBD','')
(ROOT/'electronics/libraries/AD9268_CMOS_Audited.kicad_sym').write_text('(kicad_symbol_lib (version 20231120) (generator "zl80_g2_engineering")\n'+txt+'\n)')
# Retain downstream inherited files with their correct relative libraries and model paths.
base=ROOT/'downstream/R51_UNCLOSED'
# R51_UNCLOSED archive and its models are supplied as input data; do not overwrite them here.
# generic single-pole SPICE deck; no proprietary macromodel represented by this file.
sub='''\n* Educational finite open-loop model. Power pins are NOT modeled.
.subckt AMP_1P P M O VP VN params: A0=1e5 GBW=200e6
EERR NERR 0 P M {A0}
RP NERR NPOLE 1k
CP NPOLE 0 {A0/(6.283185307179586*GBW*1000)}
EBUF O 0 NPOLE 0 1
.ends AMP_1P
'''
common='''* NOT a manufacturer macro; NOT bench evidence. No overload/slew/supply behavior.
.options reltol=1e-5 abstol=1e-14
'''
# Separate .ac and .tran analyses work in ngspice and are standard SPICE syntax.
sync='''ZL80 B06 TIA equivalent model -- UNVALIDATED BY SPICE ENGINE
VCC 3V3 0 3.3
RT 3V3 BIAS 232
RB BIAS 0 100
RTH 3V3 THRESH 100k
RLO THRESH BIAS 1k
CBIAS BIAS 0 1u
CTH THRESH 0 10n
IPD SUM 0 DC 0 AC 1 PULSE(0 20u 2u 150n 150n 1.6u 6u)
CIN SUM 0 15p
RF SUM TIA 10k
CF SUM TIA 2.2p
XU1 BIAS SUM TIA 3V3 0 AMP_1P A0=1e5 GBW=200e6
* Comparator not included: timed hysteresis is in run_models.py.
* SPICE PULSE is trapezoidal; Python optical test pulse has erf edges.
'''
b01='''ZL80 B01 TIA equivalent model -- UNVALIDATED BY SPICE ENGINE
VP VP 0 5
VN VN 0 -5
IPMT SUM 0 DC 0 AC 1 PULSE(0 10u 1u 1n 1n 4u 8u)
CIN SUM 0 20p
RF SUM TIA 100k
CF SUM TIA 2.2p
XU1 0 SUM TIA VP VN AMP_1P A0=1e6 GBW=45e6
* FDA omitted: differential ideal-gain and external RC modeled separately in Python.
'''
b08='''ZL80 B08 reference TIA equivalent model -- UNVALIDATED BY SPICE ENGINE
VP VP 0 5
VN VN 0 -5
IPD SUM NBIAS DC 0 AC 1 PULSE(0 100u 1u 1n 1n 8u 16u)
RBIAS VN NBIAS 1k
CBIAS NBIAS 0 100n
CIN SUM 0 20p
RF SUM TIA 10k
CF SUM TIA 100p
XU1 0 SUM TIA VP VN AMP_1P A0=1e6 GBW=45e6
'''
for bid,text in [('B06',sync),('B01',b01),('B08',b08)]:
 (ROOT/'simulations/spice'/f'{bid}_TIA_equivalent.cir').write_text(text+common+sub+'\n.ac dec 60 10 1e9\n.tran 2n 20u\n.print ac vm(TIA) vp(TIA)\n.print tran v(TIA)\n.end\n')
print('Support generated: audited65pin ADC library and3SPICE decks.')
