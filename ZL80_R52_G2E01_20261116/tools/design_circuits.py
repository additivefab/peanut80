"""G2-E01 circuit source. Explicit board-boundary supplies; no fabricated bench data.
B06/B07 start from the same circuit, with independent mechanical hole patterns.
All resistors/capacitors require procurement MPN/tolerance approval before release.
"""
from pathlib import Path
import json,copy
ROOT=Path(__file__).resolve().parents[1]

def p(num,name,typ,x,y,angle):return dict(num=str(num),name=name,type=typ,x=x,y=y,angle=angle)
S={
 'R_H':dict(shape='res_h',pins=[p(1,'~','passive',-7.62,0,0),p(2,'~','passive',7.62,0,180)],fp='0603'),
 'R_V':dict(shape='res_v',pins=[p(1,'~','passive',0,7.62,270),p(2,'~','passive',0,-7.62,90)],fp='0603'),
 'C_H':dict(shape='cap_h',pins=[p(1,'~','passive',-7.62,0,0),p(2,'~','passive',7.62,0,180)],fp='0603'),
 'C_V':dict(shape='cap_v',pins=[p(1,'~','passive',0,7.62,270),p(2,'~','passive',0,-7.62,90)],fp='0603'),
 'S5971':dict(shape='pd',pins=[p(1,'K','passive',10.16,0,180),p(3,'A','passive',-10.16,0,0),p(2,'CASE','passive',0,-10.16,90)],fp='S5971_TO18_TOP',source='V03'),
 'OPA356_DBV':dict(shape='opamp',pins=[p(3,'IN+','input',-12.7,5.08,0),p(4,'IN-','input',-12.7,-5.08,0),p(1,'OUT','output',12.7,0,180),p(5,'V+','power_in',0,12.7,270),p(2,'V-','power_in',0,-12.7,90)],fp='SOT23_5',source='V01'),
 'OPA828_SOIC':dict(shape='opamp',pins=[p(3,'IN+','input',-12.7,5.08,0),p(2,'IN-','input',-12.7,-5.08,0),p(6,'OUT','output',12.7,0,180),p(7,'V+','power_in',0,12.7,270),p(4,'V-','power_in',0,-12.7,90),p(1,'NC','no_connect',5.08,-17.78,90),p(5,'NC','no_connect',7.62,-17.78,90),p(8,'NC','no_connect',10.16,-17.78,90)],fp='SOIC8',source='V05'),
 'TLV3501_DBV':dict(shape='comp',pins=[p(3,'IN+','input',-12.7,5.08,0),p(1,'IN-','input',-12.7,-5.08,0),p(5,'OUT','output',12.7,0,180),p(4,'V+','power_in',0,12.7,270),p(2,'V-','power_in',0,-12.7,90),p(6,'SHDN','input',5.08,-12.7,90)],fp='SOT23_6',source='V02'),
 'TLV75533_DBV':dict(shape='box',pins=[p(1,'IN','power_in',-15.24,5.08,0),p(3,'EN','input',-15.24,-5.08,0),p(2,'GND','power_in',0,-15.24,90),p(5,'OUT','power_out',15.24,5.08,180),p(4,'NC','no_connect',15.24,-5.08,180)],fp='SOT23_5',source='V04'),
 'AD8138_SOIC':dict(shape='fda',pins=[p(8,'IN+','input',-15.24,5.08,0),p(1,'IN-','input',-15.24,-5.08,0),p(4,'OUT+','output',15.24,5.08,180),p(5,'OUT-','output',15.24,-5.08,180),p(2,'VOCM','input',-5.08,-17.78,90),p(3,'V+','power_in',0,17.78,270),p(6,'V-','power_in',5.08,-17.78,90),p(7,'NC','no_connect',10.16,-17.78,90)],fp='SOIC8',source='V06'),
 'TP':dict(shape='tp',pins=[p(1,'TP','passive',0,-5.08,90)],fp='TP1'),
 'PWR_FLAG':dict(shape='flag',pins=[p(1,'pwr','power_out',0,0,90)],fp=None),
}
for num in [1,4,6,8]:
 S['CONN'+str(num)]=dict(shape='connector',pins=[p(i,str(i),'passive',12.7,(num+1-2*i)*2.54,180) for i in range(1,num+1)],fp='HDR'+str(num))

# Treat the fitted PMT module electrically, not as an eight-passive-pin black box.
S['H10720_MODULE']=copy.deepcopy(S['CONN8'])
S['H10720_MODULE']['fp']='H10720_SOCKET_DRAFT'
S['H10720_MODULE']['source']='V08'
for pp in S['H10720_MODULE']['pins']:
 info={1:('NC','no_connect'),2:('VREF','output'),3:('VCONT','input'),4:('V+','power_in'),5:('GND','power_in'),6:('SGND','power_in'),7:('IOUT','output'),8:('NC','no_connect')}[int(pp['num'])]
 pp['name'],pp['type']=info

def newboard(bid,name,wh,holes):return dict(id=bid,name=name,size_mm=wh,holes=holes,thickness_mm=1.6,layers=4,components=[],routes=[],notes=[],external_drivers={},stage='SCHEMATIC_CANDIDATE_NOT_RELEASED')
def add(b,ref,value,kind,xy,nets,**kwargs):
 b['components'].append(dict(ref=ref,value=value,kind=kind,xy=list(xy),nets={str(k):v for k,v in nets.items()},mpn=kwargs.pop('mpn',value if kind not in ['R_H','R_V','C_H','C_V','TP','PWR_FLAG'] else ''),**kwargs))
def pas(b,ref,val,x,y,n1,n2,vertical=False):add(b,ref,val,ref[0]+('_V' if vertical else '_H'),(x,y),{1:n1,2:n2},source='DESIGN_PROPOSED')
def tp(b,ref,x,y,net):add(b,ref,net,'TP',(x,y),{1:net})
def powerflags(b,nets,x=25.4,y=261.62):
 for i,net in enumerate(nets):add(b,'#FLG'+str(i+1),net,'PWR_FLAG',(x+i*35.56,y),{1:net},mpn='',in_bom=False)

def sync(bid,holes):
 b=newboard(bid,'SOS/EOS receiver: current -> TIA -> comparator -> 3V3 logic',[18,20],holes)
 add(b,'D1','S5971','S5971',(38.1,81.28),{1:'PD_SUM',3:'GND',2:'GND'},source='V03',pcb_anchor=[14,6])
 add(b,'U1','OPA356AIDBVR','OPA356_DBV',(116.84,81.28),{3:'VBIAS',4:'PD_SUM',1:'TIA_OUT',5:'3V3',2:'GND'},source='V01',pcb_anchor=[8.5,7.5])
 pas(b,'R1','10k 0.1%',116.84,40.64,'PD_SUM','TIA_OUT')
 pas(b,'C1','2.2p C0G',116.84,22.86,'PD_SUM','TIA_OUT')
 add(b,'U2','TLV3501AIDBVR','TLV3501_DBV',(251.46,81.28),{3:'CMP_P',1:'THRESH',5:'CMP_OUT',4:'3V3',2:'GND',6:'GND'},source='V02',pcb_anchor=[12,12])
 pas(b,'R2','1k 1%',190.5,76.2,'TIA_OUT','CMP_P')
 pas(b,'R3','1M 1%',251.46,40.64,'CMP_P','CMP_OUT')
 pas(b,'R4','33R 1%',307.34,81.28,'CMP_OUT','SYNC')
 pas(b,'R5','100k 1%',345.44,127,'SYNC','GND',True)
 add(b,'J1','HEADER 1x4 P1.27','CONN4',(360.68,76.2),{1:'5VA_IN',2:'GND',3:'SYNC',4:'GND'},mpn='',source='R51_HEADER_INTERFACE_UNCHANGED',pcb_anchor=[2.3,8.5])
 # Low-Z bias avoids need for an additional high-speed buffer. Include loading in simulation.
 pas(b,'R6','232R 0.1%',30.48,175.26,'3V3','VBIAS',True)
 pas(b,'R7','100R 0.1%',30.48,213.36,'VBIAS','GND',True)
 pas(b,'C2','1u X7R 10V',60.96,213.36,'VBIAS','GND',True)
 pas(b,'R8','100k 0.1%',106.68,175.26,'3V3','THRESH',True)
 pas(b,'R9','1k 0.1%',106.68,213.36,'THRESH','VBIAS',True)
 pas(b,'C3','10n C0G',137.16,213.36,'THRESH','GND',True)
 add(b,'U3','TLV75533PDBVR','TLV75533_DBV',(228.6,190.5),{1:'5VA_IN',3:'5VA_IN',2:'GND',5:'3V3',4:''},source='V04',pcb_anchor=[5,13])
 pas(b,'C4','2.2u X7R 10V',177.8,213.36,'5VA_IN','GND',True)
 pas(b,'C5','2.2u X7R 10V',279.4,213.36,'3V3','GND',True)
 pas(b,'C6','100n X7R 10V',309.88,213.36,'3V3','GND',True)
 pas(b,'C7','100n X7R 10V',340.36,213.36,'3V3','GND',True)
 tp(b,'TP1',76.2,116.84,'TIA_OUT');tp(b,'TP2',195.58,116.84,'THRESH');tp(b,'TP3',299.72,116.84,'SYNC')
 powerflags(b,['5VA_IN','GND'])
 b['notes']=['3V3 push-pull SYNC; J1 pin1 remains +5V input, NOT 3V3 input.',
 'S5971: 1=K, 3=A, 2=CASE. Case tied GND. Reverse bias ~1V; no 100MHz claim.',
 'R3 adds positive feedback; TLV3501 SHDN tied low. Full light pulse is outside image ROI.',
 'Threshold/optical amplitude not measured. 5um timing budget is NOT yet passed.',
 'C6 at U1 and C7 at U2. Keep PD_SUM/feedback short; do not connect a long test lead to PD_SUM.',
 'Use short grounded harness for PoC. Long cable requires a differential link change request.']
 b['model']=dict(rf_ohm=1e4,cf_F=2.2e-12,a0=1e5,gbw_Hz=200e6,cin_F=15e-12,vcc=3.3,vbias_Rtop=232,vbias_Rbottom=100,threshold_Rtop=1e5,threshold_Rbottom=1000,cmp_series_R=1000,cmp_feedback_R=1e6,cmp_hysteresis_V=0.006,cmp_delay_s=4.5e-9)
 return b
B06=sync('B06',[[2.5,2.5],[9,2.5],[15.5,17.5],[2.5,17.5]])
B07=sync('B07',[[9,2.5],[15.5,2.5],[15.5,17.5],[2.5,17.5]])
B07['components'][0]['pcb_anchor']=[14,7.5]  # different hole pattern: optical locator needs G1 review
# Same circuit; photosensitive diode is mirrored in mechanical assembly, not on PCB artwork.
B08=newboard('B08','Post-ND reference photodiode and low-pass current amplifier',[25,20],[[2.5,2.5],[22.5,2.5],[22.5,17.5],[2.5,17.5]])
add(B08,'D1','S5971','S5971',(45.72,83.82),{1:'REF_SUM',3:'PD_NBIAS',2:'AGND'},source='V03',pcb_anchor=[7,8])
add(B08,'U1','OPA828ID','OPA828_SOIC',(132.08,83.82),{1:'',2:'REF_SUM',3:'AGND',4:'-5VA',5:'',6:'REF_TIA',7:'+5VA',8:''},source='V05',pcb_anchor=[15,8])
pas(B08,'R1','10k 0.1%',132.08,40.64,'REF_SUM','REF_TIA');pas(B08,'C1','100p C0G',132.08,22.86,'REF_SUM','REF_TIA')
pas(B08,'R2','33R 1%',223.52,83.82,'REF_TIA','REF_V');pas(B08,'R3','1k 1%',55.88,170.18,'-5VA','PD_NBIAS')
pas(B08,'C2','100n X7R 16V',91.44,195.58,'PD_NBIAS','AGND',True)
for i,(net,x) in enumerate([('+5VA',175.26),('-5VA',215.9)],3):pas(B08,'C'+str(i),'100n X7R 16V',x,180.34,net,'AGND',True)
for i,(net,x) in enumerate([('+5VA',256.54),('-5VA',297.18)],5):pas(B08,'C'+str(i),'2.2u X7R 16V',x,180.34,net,'AGND',True)
add(B08,'J1','HEADER 1x4 P1.27','CONN4',(317.5,76.2),{1:'+5VA',2:'AGND',3:'-5VA',4:'REF_V'},mpn='',source='R51_HEADER_UNCHANGED',pcb_anchor=[22,10])
tp(B08,'TP1',254,116.84,'REF_V');powerflags(B08,['+5VA','-5VA','AGND'])
B08['notes']=['Preserves R51 four-pin interface; bipolar supply required.', 'Photodiode nominal reverse bias 5V. Current into cathode is sunk to negative bias; output is positive.', '0..100uA input corresponds approximately 0..1V output. Confirm pickoff power before connecting.', 'RF=10k / CF=100p is a ~159kHz feedback pole; reference and PMT channel delays must be aligned.', 'This reference signal feeds B02 channel B through its own FDA; not directly a differential ADC input.']
B08['model']=dict(rf_ohm=1e4,cf_F=100e-12,a0=1e6,gbw_Hz=45e6,cin_F=20e-12)
B01=newboard('B01','H10720-20 current TIA and DC-coupled differential ADC driver',[90,50],[[3,3],[87,3],[87,47],[3,47]])
# Module pin mapping is represented as a true 8-pin connector; mechanical socket is provisional.
add(B01,'JPMT1','H10720-20 MODULE','H10720_MODULE',(33.02,81.28),{1:'',2:'PMT_VREF',3:'PMT_VCONT',4:'5VA_PMT',5:'AGND',6:'AGND',7:'PMT_I',8:''},mpn='H10720-20',source='V08; socket MPN/land pattern TBD',pcb_anchor=[42,17])
add(B01,'U1','OPA828ID','OPA828_SOIC',(132.08,91.44),{1:'',2:'PMT_I',3:'AGND',4:'-5VA',5:'',6:'TIA_OUT',7:'+5VA',8:''},source='V05',pcb_anchor=[34,33])
pas(B01,'R1','100k 0.1%',132.08,48.26,'PMT_I','TIA_OUT');pas(B01,'C1','2.2p C0G',132.08,30.48,'PMT_I','TIA_OUT')
# Shared-net FDA circuit is on the same native sheet, not a black box.
add(B01,'U2','AD8138ARZ','AD8138_SOIC',(281.94,91.44),{1:'FDA_N',2:'ADC_VCM',3:'+5VA',4:'D_A_P',5:'D_A_N',6:'-5VA',7:'',8:'FDA_P'},source='V06',pcb_anchor=[61,33])
pas(B01,'R2','499R 0.1%',218.44,76.2,'TIA_OUT','FDA_P');pas(B01,'R3','806R 0.1%',281.94,35.56,'D_A_N','FDA_P')
pas(B01,'R4','499R 0.1%',218.44,116.84,'OFFSET_0V5','FDA_N');pas(B01,'R5','806R 0.1%',281.94,149.86,'D_A_P','FDA_N')
pas(B01,'R6','33R 1%',335.28,81.28,'D_A_P','ADC_A_P');pas(B01,'R7','33R 1%',335.28,111.76,'D_A_N','ADC_A_N')
pas(B01,'C2','330p C0G',370.84,96.52,'ADC_A_P','ADC_A_N',True)
add(B01,'J1','HEADER 2x3 P2.54','CONN6',(378.46,190.5),{1:'ADC_A_P',2:'AGND',3:'ADC_A_N',4:'AGND',5:'ADC_VCM',6:'AGND'},mpn='',source='R51_INTERFACE',pcb_anchor=[78,34])
add(B01,'J2','HEADER 2x4 P2.54','CONN8',(38.1,210.82),{1:'+5VA',2:'AGND',3:'-5VA',4:'5VA_PMT',5:'PMT_VCONT',6:'AGND',7:'OFFSET_0V5',8:'PMT_VREF'},mpn='',source='R51_INTERFACE',pcb_anchor=[14,35])
for i,(net,x) in enumerate([('+5VA',99.06),('-5VA',129.54),('+5VA',160.02),('-5VA',190.5)],3):pas(B01,'C'+str(i),'100n X7R 16V',x,210.82,net,'AGND',True)
for i,(net,x) in enumerate([('+5VA',220.98),('-5VA',251.46),('5VA_PMT',281.94)],7):pas(B01,'C'+str(i),'2.2u X7R 16V',x,210.82,net,'AGND',True)
tp(B01,'TP1',170.18,134.62,'TIA_OUT');tp(B01,'TP2',322.58,157.48,'ADC_VCM');powerflags(B01,['+5VA','-5VA','5VA_PMT','AGND'])
B01['notes']=['PMT current is modeled as a sink at PMT_I; verify output polarity with manufacturer/sample.', 'RF/CF are solder-selected gain pairs: baseline100k/2.2p; alternatives10k/6.8p and1k/22p.', 'AD8138 differential gain=806/499=1.6152, offset=0.5V. 0..1V TIA maps to +/-0.8076V differential.', 'ADC full scale assumed2Vpp differential, SENSE=GND. ADC_VCM is supplied by B02 (nominal0.9V).', 'OPA828 and FDA decouplers must sit at their power pins. Do not parallel a LOG amplifier at PMT_I.', 'PMT socket mechanical pattern is provisional: inherited pads are NOT manufacturer-approved sockets.']
B01['model']=dict(rf_ohm=1e5,cf_F=2.2e-12,a0=1e6,gbw_Hz=45e6,cin_F=20e-12,fda_gain=806/499,offset_V=.5,adc_vcm_V=.9,adc_diff_fullspan_V=2.,r_series_each_ohm=33,c_diff_F=330e-12)
BOARDS=[B06,B07,B08,B01]
if __name__=='__main__':
 (ROOT/'engineering/circuits.json').write_text(json.dumps(dict(revision='R52-G2E01-D01',symbols=S,boards=BOARDS),ensure_ascii=False,indent=2))
 print('Circuit design source written:',len(BOARDS),'boards',sum(len(b['components']) for b in BOARDS),'instances')
