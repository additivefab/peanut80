from pathlib import Path
import json,csv
import numpy as np
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];d=R/'simulations/results';o=R/'simulations/plots';o.mkdir(exist_ok=True)

def save(fig,name):
 fig.tight_layout();fig.savefig(o/name,dpi=170);plt.close(fig)
p=np.load(d/'B06_pulse_traces.npz');fig,ax=plt.subplots(figsize=(8.4,4.7))
for amp in [5,10,20,50,100]:ax.plot(p['t_s']*1e6,p[f'v_{amp}uA'],label=f'{amp} uA (assumed)')
ax.axhline(json.loads((d/'summary.json').read_text())['B06']['threshold_V'],linestyle='--',label='Threshold')
ax.set(xlabel='Time (us)',ylabel='TIA output (V)',title='B06: finite-model pulse response / NOT bench data',xlim=(1.2,4.4));ax.legend(fontsize=8);ax.grid(True,alpha=.25);save(fig,'B06_pulse_response.png')
with (d/'B06_amplitude_timewalk.csv').open(encoding='utf-8-sig') as f:rows=list(csv.DictReader(f))
amp=[float(x['input_peak_uA']) for x in rows];rise=np.array([float(x['rise_ns']) for x in rows]);mid=np.array([float(x['midpoint_ns']) for x in rows]);fig,ax=plt.subplots(figsize=(8.4,4.7));ax.semilogx(amp,rise-rise[0],'o-',label='Leading edge, relative to 5 uA');ax.semilogx(amp,mid-mid[0],'s-',label='Pulse midpoint, relative to 5 uA');ax.set(xlabel='Assumed peak photocurrent (uA)',ylabel='Amplitude-dependent shift (ns)',title='B06: amplitude walk is NOT random jitter / finite model');ax.legend(fontsize=8);ax.grid(True,alpha=.25);save(fig,'B06_amplitude_timewalk.png')
p=np.load(d/'B01_step_traces.npz');fig,ax=plt.subplots(figsize=(8.4,4.7));ax.plot(p['t_s']*1e6,p['tia_V'],label='TIA 100k / 2.2p');ax.plot(p['t_s']*1e6,p['differential_external_rc_V'],label='Ideal FDA gain + external RC');ax.set(xlabel='Time (us)',ylabel='Voltage (V)',title='B01: 0 to 10 uA current step / finite-model evidence',xlim=(.5,4));ax.legend(fontsize=8);ax.grid(True,alpha=.25);save(fig,'B01_step_response.png')
fig,ax=plt.subplots(figsize=(8.4,4.7))
for bid in ['B06','B08']:
 p=np.load(d/f'{bid}_AC.npz');ax.semilogx(p['frequency_Hz'],20*np.log10(p['transimpedance_ohm']/p['transimpedance_ohm'][0]),label=bid)
ax.set(xlabel='Frequency (Hz)',ylabel='Relative transimpedance (dB)',title='B06 / B08 normalized bandwidth / single-pole amplifier model',xlim=(1e3,1e8),ylim=(-50,5));ax.legend();ax.grid(True,alpha=.25);save(fig,'B06_B08_AC.png')
print('已保存4张数值模型曲线；不是实测波形。')
