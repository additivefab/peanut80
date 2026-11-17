from pathlib import Path
import json,csv,math,uuid,collections,re
R=Path(__file__).resolve().parents[2];E=R/'electronics';B=json.loads((E/'board_definitions.json').read_text())
for b in B:
 if b['id']=='B01':b['origin'][1]=-91
(E/'board_definitions.json').write_text(json.dumps(B,ensure_ascii=False,indent=2))
sensors=json.loads((R/'engineering/sensors.json').read_text())
for s in sensors:
 if s['id']=='S_TEMP_O':s['center']=[72,57.2,220]
 if s['id']=='S_TEMP_D':s['center']=[-115,50,46]
(R/'engineering/sensors.json').write_text(json.dumps(sensors,ensure_ascii=False,indent=2))
def csvout(path,rows,cols=None):
 with open(path,'w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=cols or list(rows[0]));w.writeheader();w.writerows(rows)
rows=[]
for b in B:rows.append({'板号':b['id'],'功能':b['name'],'尺寸mm':str(b['size']),'世界原点mm':str(b['origin']),'平面/器件侧':b['plane']+'/'+b['normal'],'顶部mm':b['top'],'底部mm':b['bottom'],'层数':b['layers'],'安装孔':str(b['holes']),'状态':b['status'],'拔出方向':b['removal'],'备注':b['notes']})
csvout(R/'engineering/PCB空间接口.csv',rows)
csvout(R/'engineering/传感器安装表.csv',[{'ID':s['id'],'型号功能':s['type'],'中心mm':str(s['center']),'空间限界mm':str(s['envelope']),'板号':s['board'],'安装':s['install'],'目的':s['role']} for s in sensors])
parts=[]
def add(board,ref,val,xy,body,kind='module',pins=None,nets=None,source='设计分配',note='',rot=0):
 p=dict(board=board,ref=ref,value=val,xy=xy,body=body,kind=kind,pins=pins or {},nets=nets or {},source=source,note=note,rotation=rot)
 parts.append(p);return p
# Primitive land patterns are nominal reimplementations; package land patterns still require vendor review.
def pinrow(names):return {str(i+1):n for i,n in enumerate(names)}
def hdr(board,ref,xy,names,rows=1,pitch=2.54,body=None,rot=0):
 n=len(names);body=body or ([5,(n//2-1)*pitch+5,6] if rows==2 else [(n-1)*pitch+5,5,6])
 p=add(board,ref,'HEADER_'+str(rows)+'x'+str(n//rows)+'_P'+str(pitch),xy,body,'header',pinrow(names),pinrow(names),note='接口分配；锁扣与具体料号待定',rot=rot);p.update(rows=rows,pitch=pitch);return p
SOIC8={str(i):'' for i in range(1,9)}
opa=pinrow(['NC','IN-','IN+','V-','NC','OUT','V+','NC'])
fda=pinrow(['IN-','VOCM','V+','OUT+','OUT-','V-','NC','IN+'])
def passive(board,ref,val,xy,n1,n2,kind='R'):
 return add(board,ref,val,xy,[1.6,.8,.6],'0603',{'1':kind+'1','2':kind+'2'},{'1':n1,'2':n2},note='0603名义焊盘；电压/精度/温漂按BOM冻结')
# B01: current input kept on PMT board. Exact package and pin labels present, but no routing.
# PMT sockets are separately placed single-pole contacts, not a fabricated pin-array guess.
pp=[(1,4.68,7.62),(2,40.24,7.62),(3,45.32,7.62),(8,4.68,-7.62),(7,17.38,-7.62),(6,22.46,-7.62),(5,40.24,-7.62),(4,45.32,-7.62)]
pmtn={1:'NC',2:'PMT_VREF',3:'PMT_VCONT',4:'5VA_PMT',5:'AGND',6:'AGND',7:'PMT_I',8:'NC'}
for pin,x,z in pp:
 add('B01','JP'+str(pin),'PMT_SOCKET_SINGLE',[x+16,100-(83.1+z)],[2.4,2.4,6],'socket',{'1':pmtn[pin]},{'1':pmtn[pin] if pmtn[pin]!='NC' else ''},source='S01 p5',note='可拆单孔插座；坐标须按厂家底视图二次核对镜像；预计插入约3.1mm')
add('B01','U1','OPA828ID',[33.4,33],[5,6.2,1.75],'soic8',opa,{'2':'PMT_I','3':'AGND','4':'-5VA','6':'TIA_OUT','7':'+5VA'},'S04')
passive('B01','R1','100k_0.1%',[27.5,31],'PMT_I','TIA_OUT');passive('B01','C1','1.5p_C0G',[27.5,34],'PMT_I','TIA_OUT','C')
passive('B01','C2','100n',[39.5,30],'+5VA','AGND','C');passive('B01','C3','100n',[39.5,36],'-5VA','AGND','C')
add('B01','U2','AD8138ARZ',[59,33],[5,6.2,1.75],'soic8',fda,{'1':'FDA_N','2':'ADC_VCM','3':'+5VA','4':'D_A_P','5':'D_A_N','6':'-5VA','8':'FDA_P'},'S12')
for args in [('R2','499_0.1%',(50,29),'TIA_OUT','FDA_P'),('R3','1k_0.1%',(49,23),'D_A_N','FDA_P'),('R4','499_0.1%',(50,36),'OFFSET_0V5','FDA_N'),('R5','1k_0.1%',(55,41),'D_A_P','FDA_N'),('R6','33R',(68,30),'D_A_P','ADC_A_P'),('R7','33R',(68,36),'D_A_N','ADC_A_N')]:passive('B01',*args)
passive('B01','C4','100n',(64,25),'+5VA','AGND','C');passive('B01','C5','100n',(64,41),'-5VA','AGND','C');passive('B01','C6','330p_DIFF_TRIAL',(74,33),'ADC_A_P','ADC_A_N','C')
hdr('B01','J1',[83,35],['ADC_A_P','AGND','ADC_A_N','AGND','ADC_VCM','AGND'],rows=2,body=[7,11,6])
hdr('B01','J2',[76,12],['+5VA','AGND','-5VA','5VA_PMT','PMT_VCONT','AGND','OFFSET_0V5','PMT_VREF'],rows=2,body=[7,14,6])
# ADC pin map verified from CMOS figure; no automatic assignment from LVDS pinout.
adc={1:'CLK_P',2:'CLK_N',3:'SYNC'}
for i,p in enumerate([4,5,6,7,8,9,11,12,13,14,15,16,17,18,20,21]):adc[p]='DB'+str(i)
for i,p in enumerate([25,26,27,29,30,31,32,33,34,35,36,38,39,40,41,42]):adc[p]='DA'+str(i)
for p in [10,19,28,37]:adc[p]='1V8D'
adc.update({22:'ORB',23:'DCOB',24:'DCOA',43:'ORA',44:'SDIO_1V8',45:'SCLK_1V8',46:'CSB_1V8',47:'OEB_1V8',48:'PDWN_1V8',49:'1V8A',50:'1V8A',51:'ADC_A_P',52:'ADC_A_N',53:'1V8A',54:'1V8A',55:'ADC_VREF',56:'ADC_SENSE',57:'ADC_VCM',58:'ADC_RBIAS',59:'1V8A',60:'1V8A',61:'ADC_B_N',62:'ADC_B_P',63:'1V8A',64:'1V8A',65:'AGND'})
add('B02','U1','AD9268BCPZ-80',[30,36],[9,9,.85],'qfn64', {str(k):v for k,v in adc.items()}, {str(k):v for k,v in adc.items()},'S02 p13','64LFCSP 9mm; EP示意6.5mm需厂家推荐焊盘复核；20MSPS CMOS')
# Header J6 assignment uses clock-capable pins 13 and 17.
j6pins=['U22','T22','W22','V22','Y21','Y20','AB22','AA22','AB21','AA21','AB19','AB20','AA19','Y19','AB16','AA16','Y18','AA18','AB14','AB15','Y13','AA13','V13','W13','W18','W17','AA17','AB17','W16','Y16','Y14','AA14','V15','V14']
sig={13:'DCOA',17:'DCOB'};free=[i for i in range(1,35) if i not in sig]
for i,p in enumerate(free[:16]):sig[p]='DA'+str(i)
for i,p in enumerate(free[16:]):sig[p]='DB'+str(i)
sig.update({35:'AGND',36:'AGND',37:'NC_3V3_DNP',38:'NC_3V3_DNP',39:'NC_5V_DNP',40:'NC_5V_DNP'})
hdr('B02','J1',[30,10],[sig[i] for i in range(1,41)],2,body=[8,54,9],rot=90)
# Mark the power pads as unconnected, do not propagate source-board 3.3V into an ADC domain.
parts[-1]['nets'].update({str(i):'' for i in (37,38,39,40)});parts[-1]['note']='J6 Bank33设1.8V；37-40电源触点不装/不接；短控阻转接板待SP2实测冻结'
hdr('B02','J2',[7,58],['ADC_A_P','AGND','ADC_A_N','AGND','ADC_VCM','AGND'],2,body=[7,11,7])
hdr('B02','J3',[7,43],['REF_V','AGND','REF_V','AGND'],2,body=[7,8,7])
add('B02','U2','AD8138ARZ',[19,51],[5,6.2,1.75],'soic8',fda,{'1':'REF_FDA_N','2':'ADC_VCM','3':'+5VA','4':'D_B_P','5':'D_B_N','6':'-5VA','8':'REF_FDA_P'},'S12')
for args in [('R1','499',(11,50),'REF_V','REF_FDA_P'),('R2','499',(17,58),'D_B_N','REF_FDA_P'),('R3','499',(14,54),'AGND','REF_FDA_N'),('R4','499',(23,58),'D_B_P','REF_FDA_N'),('R5','33R',(28,49),'D_B_P','ADC_B_P'),('R6','33R',(28,53),'D_B_N','ADC_B_N'),('R7','10k_1%',(38,45),'ADC_RBIAS','AGND'),('R8','0R',(39,42),'ADC_SENSE','AGND')]:passive('B02',*args)
passive('B02','C1','330p_DIFF_TRIAL',[33,51],'ADC_B_P','ADC_B_N','C');passive('B02','C2','1u',[40,38],'ADC_VREF','AGND','C');passive('B02','C3','100n',[40,35],'ADC_VREF','AGND','C')
for i,xy in enumerate([(24,28),(28,28),(32,28),(36,28),(41,30),(20,32),(20,36),(20,40)]):passive('B02','C'+str(i+4),'100n',xy,'1V8A' if i%2 else '1V8D','AGND','C')
add('B02','Y1','20MHz_1V8_OSC_RFQ',[14,20],[5,3.2,1.2],'module',source='RFQ',note='振荡器输出与ADC时钟耦合/抖动预算待原理细化')
add('B02','U3','SPI_3V3_1V8_TRANSLATOR_RFQ',[46,53],[6,6,1.2],'module',note='必须明确双向SDIO；禁止直接3.3V驱动ADC；未定引脚')
hdr('B02','J4',[30,73],['3V3IO','AGND','SCLK_3V3','SDIO_3V3','CSB_3V3','PDWN_3V3','ORA_3V3','ORB_3V3'],2,body=[8,14,8],rot=90)
hdr('B02','J5',[51,72],['1V8A','AGND','1V8D','AGND','+5VA','-5VA'],2,body=[8,11,8])
# Remaining boards are defined functional footprints/ports, not masquerading as detailed circuits.
add('B03','F1','INPUT_FILTER_ZONE',[12,12],[14,10,5]);add('B03','U1','QUIET_5V_REG_RFQ',[35,12],[15,12,8]);add('B03','U2','NEG5_REG_RFQ',[35,31],[15,12,8]);add('B03','U3','PMT_GAIN_DAC_BUFFER_RFQ',[12,31],[16,12,3],note='Vcont默认0.5V且激光锁闭；只在线间/任务间改变并等待10s级稳定')
hdr('B03','J1',[12,42],['PRE_6V','AGND','PRE_N6V','AGND'],1,body=[13,5,7]);hdr('B03','J2',[42,44],['+5VA','AGND','-5VA','5VA_PMT','PMT_VCONT','AGND','OFFSET_0V5','PMT_VREF'],2,body=[8,14,8],rot=90)
add('B04','J1','24V_LOCKING_IN_RFQ',[10,17],[14,20,12],pins=pinrow(['24V','RETURN','CHASSIS']),note='面板锁紧入口+反接/保险/浪涌；主机内部无市电')
for ref,val,xy,dim in [('F1','INPUT_PROTECTION_ZONE',[30,17],[16,20,10]),('U1','TPS54360B_5VD_ZONE',[56,18],[24,24,16]),('U2','TPS54360B_12VM_ZONE',[89,18],[24,24,16]),('U3','ANALOG_PREREG_ZONE',[50,48],[25,18,12]),('U4','INDEPENDENT_INHIBIT_ZONE',[87,48],[26,18,10])]:add('B04',ref,val,xy,dim,note='功能占位含外围；不是该IC的实体尺寸/完整焊盘',source='S09' if 'TPS' in val else '设计待定')
hdr('B04','J2',[112,31],['5VD','DGND','12VM','PGND','PRE_6V','AGND','PRE_N6V','AGND'],2,body=[7,14,10]);hdr('B04','J3',[15,50],['LID_A','LID_B','SCAN_ALIVE','WATCHDOG','OVERTEMP','LASER_HW_EN','SHUTTER_PWR','GND'],2,body=[7,14,10])
add('B05','U1','TMC2209_LA_PADS_PENDING',[18,28],[5,5,1],'qfn28',source='S08',note='芯片焊盘位置起点；引脚未在本版落网；供电12V，0.4A相电流候选')
add('B05','C1','VM_BULK_ZONE',[18,13],[10,12,12]);add('B05','R1','SENSE_NETWORK_ZONE',[18,40],[12,8,2]);add('B05','U2','ENC_LEVEL_BUFFER_ZONE',[43,24],[14,16,2],source='S13',note='2×SN74LVC3G17；5V输入→3.3V；禁止5V直入FPGA')
hdr('B05','J1',[10,61],['A1','A2','B1','B2'],1,body=[13,7,10]);hdr('B05','J2',[11,85],['5V','GND','A_M','B_M','Z_M','5V','GND','A_D','B_D','Z_D'],2,body=[8,17,9]);hdr('B05','J3',[52,74],['SCLK','SDIO','STEP','DIR','MOT_EN','TMC_UART','ENC_A','ENC_B','ENC_Z','FAULT','GND','3V3'],2,body=[7,19,9]);hdr('B05','J4',[50,48],['ENTRY_L','ENTRY_R','EXIT','LID','RELEASE','IR_GATE','GND','5V'],2,body=[7,14,9])
for bid in ('B06','B07'):
 add(bid,'D1','S5971_PIN_INTERFACE',[15 if bid=='B06' else 3,4],[6,6,11.2],'module',source='S06',note='光电管头+引脚突出11.2mm；针脚与具体封装仍需厂家正式图复核')
 add(bid,'U1','FAST_TIA_COMPARATOR_ZONE',[9,15],[8,4,1.5],note='比较器输出3.3V；系统延迟/幅值相关时间漂移待测')
 hdr(bid,'J1',[6 if bid=='B06' else 12,9],['5VA','GND','SYNC','GND'],1,pitch=1.27,body=[8,3,4])
add('B08','D1','S5971_REF_PD',[13,10],[6,6,11.2],'module',source='S06')
add('B08','U1','REF_TIA_BUFFER_ZONE',[19,10],[5,9,1.5],note='参考光电流就地转电压；长线只传缓冲电压')
hdr('B08','J1',[12.5,3],['+5VA','AGND','-5VA','REF_V'],1,pitch=1.27,body=[8,3,4])
# R5 intentionally includes no pretend routed manufacturing output.
for p in parts:
 p['maturity']='PIN_NET_DRAFT' if p['pins'] and p['kind'] not in ('module','qfn28') else 'PLACEMENT_FUNCTION_ONLY'
# Pads in local component coords; nominal packages, rotation applied by board instance.
def pads(p):
 k=p['kind'];pds=[]
 def pad(n,x,y,w,h,drill=0):pds.append(dict(number=str(n),x=x,y=y,w=w,h=h,drill=drill,net=p['nets'].get(str(n),'')))
 if k=='soic8':
  for i in range(4):pad(i+1,-2.7,(i-1.5)*1.27,1.55,.6);pad(8-i,2.7,(i-1.5)*1.27,1.55,.6)
 elif k=='0603':pad(1,-.825,0,.95,.95);pad(2,.825,0,.95,.95)
 elif k=='socket':pad(1,0,0,2,2,.9)
 elif k=='header':
  n=len(p['pins']);r=p['rows'];q=p['pitch'];nc=n//r
  for i in range(n):
   if r==2:x=((i%2)-.5)*q;y=((i//2)-(nc-1)/2)*q
   else:x=(i-(n-1)/2)*q;y=0
   pad(i+1,x,y,1.7 if q==2.54 else .8,1.7 if q==2.54 else .8,1.0 if q==2.54 else .45)
 elif k in ('qfn64','qfn28'):
  n=64 if k=='qfn64' else 28;nside=n//4;pitch=.5;r=4.45 if n==64 else 2.45
  for i in range(nside):
   t=(i-(nside-1)/2)*pitch
   pad(i+1,-r,t,.7,.25);pad(nside+i+1,t,r,.25,.7);pad(nside*2+i+1,r,-t,.7,.25);pad(nside*3+i+1,-t,-r,.25,.7)
  pad(n+1,0,0,6.5 if n==64 else 3.1,6.5 if n==64 else 3.1)
 return pds
for p in parts:p['pads']=pads(p)
(E/'component_placements.json').write_text(json.dumps(parts,ensure_ascii=False,indent=2))
# KiCad6 S-expressions use generated local footprints, no external library dependency.
def esc(t):return str(t).replace('\\','\\\\').replace('"','\\"').replace('\n',' ')
errors=[];footpin=[]
for b in B:
 if b['layers']==0:continue
 bid=b['id'];ps=[p for p in parts if p['board']==bid];w,h,t=b['size'];netnames=sorted({q['net'] for p in ps for q in p['pads'] if q['net']});netids={n:i+1 for i,n in enumerate(netnames)}
 nlayer=b['layers'];layers=['(0 "F.Cu" signal)']+['('+str(i)+' "In'+str(i)+'.Cu" signal)' for i in range(1,nlayer-1)]+['(31 "B.Cu" signal)','(36 "B.SilkS" user "b.silkscreen")','(37 "F.SilkS" user "f.silkscreen")','(38 "B.Mask" user)','(39 "F.Mask" user)','(44 "Edge.Cuts" user)','(46 "B.CrtYd" user)','(47 "F.CrtYd" user)','(49 "F.Fab" user)']
 layers += ['(34 \"B.Paste\" user)', '(35 \"F.Paste\" user)']
 z=[f'(kicad_pcb (version 20221018) (generator zl80_pdr) (general (thickness {t})) (paper "A4") (layers '+ ' '.join(layers)+')', '(setup (pad_to_mask_clearance 0))']
 z+=['(net 0 "")']+[f'(net {v} "{esc(k)}")' for k,v in netids.items()]
 for (x1,y1),(x2,y2) in zip([(0,0),(w,0),(w,h),(0,h)],[(w,0),(w,h),(0,h),(0,0)]):z.append(f'(gr_line (start {x1} {y1}) (end {x2} {y2}) (stroke (width 0.05) (type default)) (layer "Edge.Cuts"))')
 z.append(f'(gr_text "{bid} R5-PDR / UNROUTED / NO FAB" (at {w/2} {h/2}) (layer "F.Fab") (effects (font (size 1 1) (thickness .15))))')
 for j,(x,y) in enumerate(b['holes']):z.append(f'(footprint "ZL80:NPTH" (layer "F.Cu") (at {x} {y}) (attr exclude_from_pos_files exclude_from_bom) (fp_text reference "MH{j+1}" (at 0 -3) (layer "F.Fab") (effects (font (size .8 .8) (thickness .12)))) (pad "" np_thru_hole circle (at 0 0) (size {b["mount_dia"]} {b["mount_dia"]}) (drill {b["mount_dia"]}) (layers "*.Cu" "*.Mask")))')
 for p in ps:
  x,y=p['xy'];ww,hh,zz=p['body'];a=p['rotation'];cw,ch=(hh,ww) if a%180 else (ww,hh)
  if x-cw/2<0 or x+cw/2>w or y-ch/2<0 or y+ch/2>h:errors.append({'board':bid,'ref':p['ref'],'issue':'body outside board'})
  for hx,hy in b['holes']:
   dx=max(abs(hx-x)-cw/2,0);dy=max(abs(hy-y)-ch/2,0)
   if math.hypot(dx,dy)<b['mount_dia']/2+.3:errors.append({'board':bid,'ref':p['ref'],'issue':'mount hole clearance'})
  z.append(f'(footprint "ZL80:{p["kind"]}" (layer "F.Cu") (at {x} {y} {a}) (attr {"through_hole" if p["kind"] in ("header","socket") else "smd"})')
  for typ,txt,yy,ly in [('reference',p['ref'],-hh/2-1,'F.SilkS'),('value',p['value'],hh/2+1,'F.Fab')]:z.append(f'(fp_text {typ} "{esc(txt)}" (at 0 {yy}) (layer "{ly}") (effects (font (size .7 .7) (thickness .12))))')
  for ly,delta in [('F.Fab',0),('F.CrtYd',.25)]:z.append(f'(fp_rect (start {-ww/2-delta} {-hh/2-delta}) (end {ww/2+delta} {hh/2+delta}) (stroke (width .05) (type default)) (fill none) (layer "{ly}"))')
  for q in p['pads']:
   nn=netids.get(q['net'],0);dr=q['drill'];nt=f'(net {nn} "{esc(q["net"])}")' if nn else '';dt=f'(drill {dr})' if dr else '';knd='thru_hole' if dr else 'smd';ly='"*.Cu" "*.Mask"' if dr else '"F.Cu" "F.Paste" "F.Mask"'
   z.append(f'(pad "{q["number"]}" {knd} rect (at {q["x"]} {q["y"]}) (size {q["w"]} {q["h"]}) {dt} (layers {ly}) {nt})')
   footpin.append(dict(board=bid,reference=p['ref'],part=p['value'],pin=q['number'],pin_name=p['pins'].get(q['number'],''),net=q['net'],status=p['maturity']))
  z.append(')')
 for i,a in enumerate(ps):
  ax,ay=a['xy'];aw,ah=a['body'][:2];aw,ah=(ah,aw) if a['rotation']%180 else (aw,ah)
  for d in ps[i+1:]:
   dx,dy=d['xy'];dw,dh=d['body'][:2];dw,dh=(dh,dw) if d['rotation']%180 else (dw,dh)
   if min(ax+aw/2,dx+dw/2)-max(ax-aw/2,dx-dw/2)>.01 and min(ay+ah/2,dy+dh/2)-max(ay-ah/2,dy-dh/2)>.01:errors.append({'board':bid,'ref':a['ref']+'/'+d['ref'],'issue':'component body overlap'})
 z.append(')');txt='\n'.join(z);(E/'boards'/f'{bid}_R5_placement.kicad_pcb').write_text(txt)
 # Explicit uncompleted scope protects against mistaking pin labels for ERC.
 (E/'boards'/f'{bid}_STATUS.md').write_text(f'# {bid} {b["name"]}\n\nR5-PDR；{w}×{h}×{t} mm；{nlayer}层建议。\n\n已给：板框、安装孔、关键器件/功能区位置、名义焊盘与部分网表。\n未给：完整外围、布线、叠层阻抗、回流路径、阻抗/EMC/热验证、ERC/DRC。\n没有制造放行，也未提供Gerber。FUNCTION_ONLY 区块不是器件本体，不得直接下单制板。\n坐标变换参见 electronics/README.md。\n')
# Machine-readable connections and pin constraints.
csvout(E/'pin_nets.csv',footpin)
csvout(E/'component_placement.csv',[{'board':p['board'],'ref':p['ref'],'part':p['value'],'u_mm':p['xy'][0],'v_mm':p['xy'][1],'rotation_deg':p['rotation'],'width_mm':p['body'][0],'depth_mm':p['body'][1],'height_mm':p['body'][2],'status':p['maturity'],'source':p['source'],'note':p['note']} for p in parts])
pmap=[dict(connector='J6_V1.3B',pin=i,fpga_ball=j6pins[i-1],signal=sig[i],voltage='1.8V Bank33',note='ADC DCO capture; remove 37-40 power contacts') for i in range(1,35)]
j5balls=['H19','H20','E18','F18','F17','G17','C17','C18','G19','F19','E20','E19','D22','C22','B22','B21','B17','B16','A17','A16','D20','C20','B15','C15','D17','D16','D15','E15']
j5names=['SOS','EOS','ENC_M_A','ENC_M_B','ENC_M_Z','ENC_D_A','ENC_D_B','ENC_D_Z','STEP','DIR','MOT_EN','LASER_EN','SHUTTER_EN','FAULT','I2C_SCL','I2C_SDA','ADC_SCLK','ADC_SDIO','ADC_CSB','ADC_PDWN','ORA','ORB','TMC_UART','ENTRY_L','ENTRY_R','EXIT','ADF_READY','ADF_REQUEST']
for i,(ball,nm) in enumerate(zip(j5balls,j5names),7):pmap.append(dict(connector='J5_V1.3B',pin=i,fpga_ball=ball,signal=nm,voltage='3.3V Bank35',note='Sensor 5V must level convert; ADC control translate 1.8V'))
csvout(E/'SP2_V13B_pin_assignment.csv',pmap)
xdc=['# DRAFT ONLY / source U04 p10,p12. Verify actual board silk-screen V1.3B.','# Set Bank33 physically to 1.8 V before connecting. J6 supply pins remain 3.3/5V.','# No timing closure, input-delay budget or board skew constraints claimed.']
for r in pmap:xdc.append('set_property -dict {PACKAGE_PIN '+r['fpga_ball']+' IOSTANDARD '+('LVCMOS18' if r['connector'].startswith('J6') else 'LVCMOS33')+'} [get_ports {'+r['signal']+'}]')
xdc+=['create_clock -period 50.000 -name adc_dcoa [get_ports DCOA]','create_clock -period 50.000 -name adc_dcob [get_ports DCOB]','# DCOA/B domain crossing and input delays MUST be added from ADC timing and actual routing.']
(R/'firmware/SP2_V13B_draft.xdc').write_text('\n'.join(xdc))
# Legacy KiCad schematics are self-contained pin breakout drafts with named nets.
# They intentionally cover only pin-reviewed circuitry, leaving FUNCTION_ONLY zones in interface documentation.
lib=['EESchema-LIBRARY Version 2.4','#encoding utf-8'];schematic_count=0
for bid in [b['id'] for b in B if b['layers']]:
 ps=[p for p in parts if p['board']==bid and p['pads'] and p['maturity']=='PIN_NET_DRAFT']
 chunks=[ps[i:i+6] for i in range(0,len(ps),6)]
 for pg,chunk in enumerate(chunks,1):
  sh=['EESchema Schematic File Version 4','LIBS:ZL80_R5-cache','EELAYER 29 0','EELAYER END','$Descr A3 16535 11693','encoding utf-8','Sheet 1 1',f'Title "ZL80 {bid} PIN-NET DRAFT {pg}"','Date "2026-11-14"','Rev "R5-PDR"','Comp "NOT ROUTED / NO ERC / REVIEW REQUIRED"','$EndDescr','Text Notes 800 650 0 90 ~ 0','PIN-NET REVIEW SHEET - not a manufacturing schematic. Named nets connect globally.']
  for j,p in enumerate(chunk):
   sx=3000+(j%3)*5000;sy=3000+(j//3)*4700;key=f'{bid}_{p["ref"]}';pins=p['pads'];nn=len(pins);ns=math.ceil(nn/2);spacing=100 if nn>24 else 180;hh=max(400,ns*spacing/2+120)
   lib+=['# '+key,f'DEF {key} U 0 40 Y Y 1 F N',f'F0 "{p["ref"]}" 0 {int(hh+150)} 50 H V C CNN',f'F1 "{p["value"]}" 0 {int(-hh-150)} 40 H V C CNN','DRAW',f'S -700 {int(hh)} 700 {int(-hh)} 0 1 10 f']
   for k,q in enumerate(pins):
    right=k>=ns;col=k-ns if right else k;yy=(ns-1)*spacing/2-col*spacing;xx=1000 if right else -1000;orient='L' if right else 'R';nm=p['pins'].get(q['number'],q['number']) or q['number'];nm=nm.replace(' ','_')
    lib.append(f'X {nm} {q["number"]} {xx} {int(yy)} 300 {orient} 35 35 1 1 P')
   lib+=['ENDDRAW','ENDDEF']
   sh+=['$Comp',f'L {key} {p["ref"]}',f'U 1 1 {uuid.uuid4().hex[:8]}',f'P {sx} {sy}',f'F 0 "{p["ref"]}" H {sx} {sy-int(hh+150)} 50 0000 C CNN',f'F 1 "{p["value"]}" H {sx} {sy+int(hh+150)} 40 0000 C CNN',f'\t1 {sx} {sy}','\t1 0 0 -1','$EndComp']
   for k,q in enumerate(pins):
    right=k>=ns;col=k-ns if right else k;yy=sy-int((ns-1)*spacing/2-col*spacing);xx=sx+(1000 if right else -1000);nt=q['net']
    if nt:
     ex=xx+(500 if right else -500);sh+=['Wire Wire Line',f'\t{xx} {yy} {ex} {yy}',f'Text Label {min(xx,ex)} {yy} 0 35 ~ 0',nt]
    else:sh.append(f'NoConn ~ {xx} {yy}')
  sh+=['$EndSCHEMATC'];(E/'schematics'/f'{bid}_pins_{pg:02d}.sch').write_text('\n'.join(sh));schematic_count+=1
lib+=['#End Library'];(E/'schematics/ZL80_R5-cache.lib').write_text('\n'.join(lib))
(E/'schematics/sym-lib-table').write_text('(sym_lib_table (lib (name "ZL80_R5-cache")(type "Legacy")(uri "${KIPRJMOD}/ZL80_R5-cache.lib")(options "")(descr "PDR pin net symbols")))')
# Structural parse only: check balanced S-expressions while honoring quotes.
def balanced(s):
 n=0;q=False;escp=False
 for ch in s:
  if escp:escp=False;continue
  if ch=='\\' and q:escp=True;continue
  if ch=='"':q=not q;continue
  if not q:
   n+=(ch=='(')-(ch==')')
   if n<0:return False
 return n==0 and not q
syntax={p.name:balanced(p.read_text()) for p in (E/'boards').glob('*.kicad_pcb')}
(R/'tests/ecad_geometry.json').write_text(json.dumps(dict(scope='body rectangles and board holes only; no pad, trace, netlist or KiCad ERC/DRC validation',components=len(parts),boards=len(syntax),syntax_balanced=syntax,issues=errors,schematic_pages=schematic_count),ensure_ascii=False,indent=2))
(E/'README.md').write_text('''# ZL80 R5 电气/PCB文件边界

本目录是 PDR 级板框、关键布局、接口、针脚网表和原理草图，不是已布线 PCB。8块定制板＋1块SP2安装托板；SP2是购买/已有开发板，不在本目录重新设计DDR/FPGA电源。

## 文件与坐标
`boards/*.kicad_pcb` 为 KiCad 7+ 风格文本，可导入检查。无需外部封装库。`schematics/*.sch` 为旧版KiCad可导入的独立针脚-网名审查图；同名网连接。`ZL80_R5-cache.lib` 随包。没有运行KiCad ERC/DRC或原生解析器，结构括号检查不等于软件验证。

板上坐标(u,v)以板框(0,0)为基准，单位mm。XY板：世界X=ox+u，Y=oy+v；器件在+Z。XZ且器件+Y：X=ox+u，Z=oz+板高-v；XZ且器件-Y：X=ox+u，Z=oz+v。这个镜像关系尤其要在PMT底视针脚与B01焊接面上复核。B01单孔插座按6mm装配高度起算，预计12mm引脚插入约3.1mm，不是已完成针脚配合认证。

## 重要电气决策
- B01基线为线性TIA：OPA828、Rf100k/Cf1.5p起点；10k/4.7p和1M/0.5p为换焊实验档。不能把RfCf看成已验证带宽。输入寄生、PMT输出极性、过载恢复需台架确认。AD8138偏置与VCM均保留DC。330p差分电容只是试验值，正式抗混叠滤波未完成。
- 原机LOG链作为同尺寸替换卡，不与TIA并接PMT阳极。ADL5304极性转换与低电流带宽仍待闭合，未给虚假可生产LOG网表。
- B02为20MSPS连续采样AD9268，Bank33实际设为1.8V。J6 37/38仍为3.3V、39/40为5V，必须不接。CMOS12周期转换延迟与后续数字处理延迟分别标定。
- B03/B04/B05的FUNCTION_ONLY区是功能及外围占位，不是芯片封装。未定具体稳压、SPI电平转换和安全比较逻辑的引脚，禁止按这些区域直接贴片。
- TMC2209用12V受控母线；5V编码器先经容忍5V输入的3.3V缓冲再入FPGA。外部24V不直接接SP2或PMT。PMT内部高压封装在模块内，禁止另接裸高压。
- PCB地平面建议连续，模拟/功率靠布局与回流回路分区；不可机械地把高速返回路径割断。电机PWM线与PMT输入分舱走线。

## 放行前必须补齐
所有FUNCTION_ONLY模块定型、全外围元件和去耦、厂商推荐焊盘、丝印极性、连接器确切MPN、供应商层叠阻抗、完整布线、SI/PI与EMC、整机安全故障注入、ERC/DRC及第三人复核。本包没有Gerber和生产BOM，不应送厂生产。
''')
print('PCB files',len(syntax),'components',len(parts),'schematic pages',schematic_count,'issues',errors,'syntax',syntax)
