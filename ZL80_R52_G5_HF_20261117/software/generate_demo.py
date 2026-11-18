"""Generate labelled synthetic archive; never claims measured PMT/ADC evidence."""
from pathlib import Path
import math,json,sys
from zlraw import *
def build_records(nlines:int=3)->list[Record]:
    events=[];sid=1;start=1000;period=333333;first=50000;span=146423
    stop=first+(nlines-1)*period+span+20000
    events.extend([(start,Record(START,start,sid)),(start,Record(ENC_M,start,0,0x8000)),
                   (start,Record(ENC_D,start,0,0x8000))])
    for n in range(nlines):
        s=first+n*period;e=s+span
        events.extend([(s,Record(SOS_UP,s,n+1)),(s+600,Record(SOS_DOWN,s+600,n+1)),
                       (e,Record(EOS_UP,e,n+1)),(e+600,Record(EOS_DOWN,e+600,n+1))])
    step_ticks=math.pi*20/(4096*4)/15*100_000_000
    k=1
    while start+round(k*step_ticks)<stop:
        t=start+round(k*step_ticks)
        events.extend([(t,Record(ENC_M,t,k,1)),(t+2,Record(ENC_D,t+2,k,1))]);k+=1
    for i,t in enumerate(range(start+100,stop-100,5)):
        phase=((t-first)%period)/period
        a=int(30000+20000*math.sin(phase*2*math.pi));b=int(33000+200*math.sin(phase*8*math.pi))
        flags=0
        if i%20000==0:a=0
        elif i%20000==1:a=65535;flags=1
        # 60 ticks of synthetic ADC pipeline delay + 8 adapter cycles.
        events.append((t+68,Record(SAMPLE,t,(b<<16)|a,flags)))
    events.sort(key=lambda p:p[0]);records=[r for _,r in events]
    records.extend([Record(STATUS,stop,0),Record(LOSS,stop,0),Record(END,stop,sid)])
    return records

def main():
    root=Path(__file__).resolve().parents[1];out=root/'examples'/'synthetic_scan.zlraw'
    if out.exists():print('Existing example retained (exclusive write policy):',out);return
    meta={'format':'ZL80RAW1','revision':'R52-G5-F01-D01','synthetic':True,
          'source':'Python algorithm generator, NOT HDL simulator / NOT bench',
          'tick_hz':100000000,'adc_sample_hz':20000000,'session_id':1,
          'sample_flags_semantics':'ideal synthetic normalized interface only',
          'sync_span_mm':92,'film_width_mm':80,'aperture_epoch_hardware_verified':False,
          'calibration_id':None,'facet_absolute':None}
    write_archive(out,meta,build_records())
    (root/'validation/results/synthetic_example.json').write_text(json.dumps(inspect(out),indent=2))
    print(out)
if __name__=='__main__':main()
