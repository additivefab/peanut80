#!/usr/bin/env python3
"""Reproducible finite single-pole amplifier calculations, NOT vendor SPICE/bench.
All photodiode pulse shapes, amplifier DC gains and parasitic sweeps are explicit assumptions.
The small-signal model cannot establish overload recovery, PCB stability, EMC or product SNR.
"""
from pathlib import Path
import json, math, csv, sys
import numpy as np
from scipy import signal, special
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from design_circuits import B01,B06,B08
OUT=ROOT/'simulations/results';OUT.mkdir(parents=True,exist_ok=True)

def tia_tf(rf,cf,cin,gbw,a0):
    wp=2*math.pi*gbw/a0
    return signal.TransferFunction([a0*wp*rf], [rf*(cf+cin),1+wp*rf*((1+a0)*cf+cin),wp*(1+a0)])

def response(m,t,current):
    tf=tia_tf(m['rf_ohm'],m['cf_F'],m['cin_F'],m['gbw_Hz'],m['a0'])
    return signal.lsim(tf,U=current,T=t)[1]

def ac(m):
    f=np.logspace(1,9,1601);s=2j*np.pi*f
    A=m['a0']/(1+s/(2*np.pi*m['gbw_Hz']/m['a0']))
    Y=1/m['rf_ohm']+s*m['cf_F']
    Z=A/((1+A)*Y+s*m['cin_F']);loop=A/(1+s*m['cin_F']/Y)
    gain=np.abs(Z); dc=m['rf_ohm']*m['a0']/(1+m['a0'])
    crossing=np.where(gain<=dc/np.sqrt(2))[0];bw=float(f[crossing[0]]) if len(crossing) else None
    cross=np.where(np.abs(loop)<=1)[0];pm=float(180+np.degrees(np.angle(loop[cross[0]]))) if len(cross) else None
    return f,Z,dict(dc_ohm=dc,bandwidth_3db_Hz=bw,phase_margin_deg_singlepole=pm,peaking_dB=float(20*np.log10(gain.max()/dc)),all_poles_lhp=bool(np.all(np.real(tia_tf(m['rf_ohm'],m['cf_F'],m['cin_F'],m['gbw_Hz'],m['a0']).poles)<0)))

def bias(vcc=3.3,rt=232.,rb=100.,rth=1e5,rlo=1e3):
    # Two-node exact DC including threshold-divider loading; ignores bias current.
    G=np.array([[1/rt+1/rb+1/rlo,-1/rlo],[-1/rlo,1/rlo+1/rth]])
    return np.linalg.solve(G,[vcc/rt,vcc/rth])

def cmp_model(t,vin,vth,vcc=3.3,offset=0.,hyst=.006,series=1e3,feedback=1e6,delay=4.5e-9):
    """Schmitt decision with finite constant delay, ideal rails and no metastability."""
    state=False;out=np.zeros_like(vin);trans=[]
    for j,v in enumerate(vin):
        vp=(v*feedback+(vcc if state else 0)*series)/(feedback+series)
        threshold=vth+offset+(-hyst/2 if state else hyst/2)
        new=(vp>threshold)
        if new!=state:trans.append((float(t[j]+delay),int(new)))
        state=new;out[j]=vcc if state else 0
    # Sample a zero-order hold delayed decision; timestamps above retain fractional-delay value.
    d=int(round(delay/(t[1]-t[0])))
    if d:out=np.r_[np.zeros(d),out[:-d]]
    return out,trans

def edges(trans):
    rise=next((t for t,s in trans if s==1),None)
    fall=next((t for t,s in trans if s==0 and rise is not None and t>rise),None)
    return rise,fall,((rise+fall)/2 if rise is not None and fall is not None else None)

def writecsv(name,rows):
    if rows:
        with (OUT/name).open('w',newline='',encoding='utf-8-sig') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def run():
    result={'evidence_class':'EXECUTED_NUMERICAL_EQUIVALENT_MODEL','date':'2026-11-16','native_spice':'NOT_RUN','bench':'NOT_RUN',
    'assumptions':['Single-pole op-amp A(s); no slew/saturation/overload/extra poles/PCB parasitics except lumped input C.',
    'S5971 actual capacitance at 1V and 5V not measured: lumped C swept, no 100MHz assumption at these biases.',
    'Comparator constant4.5ns is an illustrative typical-delay parameter, NOT jitter or worst-case propagation.',
    'Optical detector input is assumed current. Pulse edge sigma150ns/plateau1.6us is NOT measured from the actual optical head.',
    'AD8138 modeled as ideal DC gain and external RC only; vendor macro/SI/ADC kickback still required.']}
    Vb,Vth=bias();m=B06['model'];t=np.arange(0,6e-6,2e-9)
    pulse=.5*(special.erf((t-2e-6)/(np.sqrt(2)*150e-9))-special.erf((t-3.6e-6)/(np.sqrt(2)*150e-9)))
    # Transfer output is positive for a current sink at the virtual summing junction.
    traces={'t_s':t,'pulse_normalized':pulse};timewalk=[]
    for amp_u in [5,10,20,50,100]:
        v=Vb+response(m,t,pulse*amp_u*1e-6);digital,tr=cmp_model(t,v,Vth)
        r,f,mid=edges(tr);timewalk.append(dict(input_peak_uA=amp_u,rise_ns=r*1e9 if r else None,fall_ns=f*1e9 if f else None,midpoint_ns=mid*1e9 if mid else None,peak_tia_V=float(v.max()),extra_transition_count=max(0,len(tr)-2)))
        traces['v_'+str(amp_u)+'uA']=v;traces['d_'+str(amp_u)+'uA']=digital
    np.savez_compressed(OUT/'B06_pulse_traces.npz',**traces);writecsv('B06_amplitude_timewalk.csv',timewalk)
    nominal_rises=[r['rise_ns'] for r in timewalk if r['rise_ns'] is not None];mids=[r['midpoint_ns'] for r in timewalk if r['midpoint_ns'] is not None]
    speed=2*100*(3000*2*np.pi/60);budget_s=.005/speed
    corners=[]
    for cin in [5e-12,15e-12,30e-12]:
      for gbw in [100e6,200e6]:
       mm={**m,'cin_F':cin,'gbw_Hz':gbw};ff,zz,info=ac(mm)
       corners.append(dict(cin_pF=cin*1e12,gbw_MHz=gbw/1e6,**info))
    writecsv('B06_bandwidth_corners.csv',corners)
    dc_corners=[]
    for vos in [-.015,0,.015]:
      for co in [-.0065,0,.0065]:
        # Equivalent minimum signal using comparator OFF threshold with output LOW.
        required_tia=(Vth+co+.003)*(m['cmp_series_R']+m['cmp_feedback_R'])/m['cmp_feedback_R']
        trigger_u=(required_tia-Vb-vos)/m['rf_ohm']*1e6
        dc_corners.append(dict(opa_equivalent_baseline_offset_mV=vos*1000,comparator_offset_mV=co*1000,nominal_turnon_uA=trigger_u,dark_false_high_if_negative=trigger_u<0))
    writecsv('B06_threshold_offset_corners.csv',dc_corners)
    # Scope limited white-noise estimate, NOT a total input-referred noise specification.
    ff,zz,info=ac(m);I=20e-6;k=1.380649e-23;T=298.15;e=1.602176634e-19
    shot=np.sqrt(2*e*I);thermal=np.sqrt(4*k*T/m['rf_ohm']);s=2j*np.pi*ff
    A=m['a0']/(1+s/(2*np.pi*m['gbw_Hz']/m['a0']));Y=1/m['rf_ohm']+s*m['cf_F'];NG=1+s*m['cin_F']/Y;Hv=A*NG/(A+NG)
    sigma=float(np.sqrt(np.trapezoid(abs(zz)**2*(shot**2+thermal**2)+abs(Hv)**2*(5.8e-9)**2,ff)))
    v=traces['v_20uA'];idx=int(np.argmin(abs(t-timewalk[2]['rise_ns']*1e-9)));slope=float(np.gradient(v,t)[idx]);jitter_ns=sigma/slope*1e9
    result['B06']={'bias_V':float(Vb),'threshold_V':float(Vth),'threshold_above_bias_mV':float((Vth-Vb)*1000),
      'dividers_current_mA':float(((3.3-Vb)/232+(3.3-Vth)/1e5)*1e3),'quiescent_board_mA_estimate':float(((3.3-Vb)/232+(3.3-Vth)/1e5)*1e3+8.3+3.2),
      'scan_speed_mm_s_assumed':speed,'proposed_5um_timing_budget_ns':budget_s*1e9,'leading_edge_amplitude_timewalk_pp_ns':max(nominal_rises)-min(nominal_rises),
      'midpoint_amplitude_timewalk_pp_ns':max(mids)-min(mids),'white_noise_subset_rms_mV':sigma*1000,'illustrative_local_noise_jitter_ns':jitter_ns,
      'timewalk_vs_budget':'OPEN: deterministic peak-to-peak walk and RMS budget are different statistics; amplitude correction or pulse-center method needs optical validation.',
      'ac_nominal':info,'model_scope':'Analog resistor/shot/OPA white noise subset only; no comparator noise,1/f,PMT,laser,power,MCU threshold,or PCB.'}
    np.savez_compressed(OUT/'B06_AC.npz',frequency_Hz=ff,transimpedance_ohm=abs(zz),phase_deg=np.degrees(np.angle(zz)))
    # B01 gain pairs and input-C sweep: run actual finite open-loop models, no fabricated SPICE log.
    b01rows=[]
    for rf,cf in [(1e3,22e-12),(1e4,6.8e-12),(1e5,2.2e-12)]:
      for cin in [5e-12,20e-12,50e-12]:
        mm={**B01['model'],'rf_ohm':rf,'cf_F':cf,'cin_F':cin};ff,zz,inf=ac(mm)
        tf=tia_tf(rf,cf,cin,mm['gbw_Hz'],mm['a0']);st=np.linspace(0,10e-6,10001);_,y=signal.step(tf,T=st);y/=rf
        maxdev=np.abs(y-1);lastbad=np.where(maxdev>.001)[0];settle=float(st[lastbad[-1]+1]) if len(lastbad) and lastbad[-1]+1<len(st) else None
        fny=1.256637061e6/2;zval=np.interp(fny,ff,abs(zz));rc=1/np.sqrt(1+(2*np.pi*fny*66*330e-12)**2)
        b01rows.append(dict(rf_ohm=rf,cf_pF=cf*1e12,cin_pF=cin*1e12,**inf,step_overshoot_percent=float(max(0,y.max()-1)*100),settle_0p1pct_us=settle*1e6 if settle else None,relative_gain_at_628kHz=float(zval/rf*rc),current_for_1V_uA=1e6/rf,at_100uA_tia_V=rf*100e-6,current_for_1V_exceeds_100uA_reference=(1e6/rf>100)))
    writecsv('B01_gain_bandwidth_corners.csv',b01rows)
    t1=np.linspace(0,8e-6,8001);step=np.where(t1>=1e-6,1e-5,0);v1=response(B01['model'],t1,step)
    gain=B01['model']['fda_gain'];diff=gain*(v1-.5);tau=66*330e-12
    vd=diff[0]+signal.lsim(signal.TransferFunction([1],[tau,1]),U=diff-diff[0],T=t1)[1]
    np.savez_compressed(OUT/'B01_step_traces.npz',t_s=t1,tia_V=v1,differential_ideal_gain_V=diff,differential_external_rc_V=vd)
    head=[]
    for out in [0,.1,.5,.9,1,1.1,1.2]:
      d=gain*(out-.5);head.append(dict(tia_V=out,adc_diff_V=d,vin_plus_V=.9+d/2,vin_minus_V=.9-d/2,inside_assumed_ADC_range=abs(d)<=1))
    writecsv('B01_ADC_headroom.csv',head)
    result['B01']={'rf_ohm':1e5,'cf_pF':2.2,'gain_diff':gain,'map_tia_0_to_1V_diff_V':[-.5*gain,.5*gain],'ADC_diff_halfspan_assumed_V':1.,'differential_margin_each_rail_V':1-.5*gain,
      'settling_vs_pixel':'Finite model explicitly not guaranteed to settle0.1% inside0.796us; test edge response/MTF at mode bandwidth.',
      'gain_switch':'Solder-population alternatives only; no pixel-rate gain switch is designed.',
      'PMT_VCONT_and_ADC_VCM':'External B03/B02 contracts remain OPEN; test with verified laboratory references first.'}
    ff,zz,inf=ac(B08['model']);result['B08']={'ac_nominal':inf,'nominal_reverse_bias_V':5.,'output_at_100uA_V':inf['dc_ohm']*1e-4,'delay_alignment':'Reference is band-limited; do not divide PMT samples by unmatched raw reference timestamps.'}
    np.savez_compressed(OUT/'B08_AC.npz',frequency_Hz=ff,transimpedance_ohm=abs(zz))
    result['judgement']={'numerical_execution':'COMPLETED','component_model_validation':'OPEN','timing_5um_compliance':'NOT_DEMONSTRATED','manufacturing_release':'BLOCKED','bench_evidence':'NONE'}
    (OUT/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    (OUT/'run_environment.json').write_text(json.dumps(dict(python=sys.version,numpy=np.__version__,scipy=__import__('scipy').__version__,seed='deterministic; no random sampling'),indent=2))
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':run()
