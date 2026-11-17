"""Analyze real bench CSV. Refuses empty inputs; never treats encoder steps as ground truth.
python tools/analyze_transport.py input.csv --target-speed 15 --output output.json
Required fields time_s,reference_position_mm,tension_N; other template fields retained.
Reports raw linear-position residual and average speed, no hidden smoothing/window change.
"""
from pathlib import Path
import csv,json,math,argparse,statistics

def analyze(path,target_speed):
 with open(path,encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
 if len(rows)<20:raise ValueError('At least 20 measured rows required; blank template is NOT_RUN.')
 try:
  t=[float(r['time_s']) for r in rows];x=[float(r['reference_position_mm']) for r in rows];force=[float(r['tension_N']) for r in rows]
 except (KeyError,ValueError) as e:raise ValueError('Real time, independent reference position and calibrated tension data required.') from e
 if not all(math.isfinite(v) for a in [t,x,force] for v in a):raise ValueError('Non-finite measured data.')
 if not all(b>a for a,b in zip(t,t[1:])):raise ValueError('Timestamps must be strictly increasing.')
 if target_speed<=0:raise ValueError('Positive target speed required.')
 mt=statistics.mean(t);mx=statistics.mean(x);sxx=sum((v-mt)**2 for v in t)
 v=sum((a-mt)*(b-mx) for a,b in zip(t,x))/sxx;offset=mx-v*mt
 residual=[b-(offset+v*a) for a,b in zip(t,x)]
 return {'status':'ANALYZED_NOT_REVIEWED','n':len(t),'duration_s':t[-1]-t[0],'mean_speed_mm_s':v,'mean_speed_error_pct':100*(v-target_speed)/target_speed,'position_residual_rms_um':math.sqrt(statistics.mean(e*e for e in residual))*1000,'position_residual_p2p_um':(max(residual)-min(residual))*1000,'tension_mean_N':statistics.mean(force),'tension_rms_about_mean_N':statistics.pstdev(force),'tension_min_N':min(force),'tension_max_N':max(force),'sample_interval_min_s':min(b-a for a,b in zip(t,t[1:])),'sample_interval_max_s':max(b-a for a,b in zip(t,t[1:])),'method':'least-squares linear reference-position fit; unfiltered residual; no compliance PASS inferred','boundary':'operator must supply specimen/calibration/configuration, settle window, instrument bandwidth/uncertainty and approval'}
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('csv');a.add_argument('--target-speed',type=float,required=True);a.add_argument('--output',default='transport_analysis.json');args=a.parse_args()
 try:result=analyze(args.csv,args.target_speed)
 except ValueError as e:a.error(str(e))
 Path(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False,indent=2))
