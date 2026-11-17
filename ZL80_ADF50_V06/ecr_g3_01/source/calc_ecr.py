"""ECR-G3-01 budgets: coverage of the two follower encoders, resolution, counts rate, added moving mass and its preload effect.
Standard library only. Assumptions, not measurements."""
import json,math
from pathlib import Path
E=Path(__file__).resolve().parents[1];V=E.parent
p=json.loads((V/'engineering/parameters.json').read_text());it=json.loads((E/'interference.json').read_text())
D=20.0;cpr=16384;margin=p['handoff']['grip_margin_mm'];nip=42
out={'basis':'assumptions, not measurements'}
cov=[]
for L in (260,280,300):
    entry=[0,L-(nip+margin)];exit_=[nip+margin,L]
    cov.append(dict(length_mm=L,entry_follower_valid_mm=entry,exit_follower_valid_mm=exit_,union_mm=[min(entry[0],exit_[0]),max(entry[1],exit_[1])],
        gap_mm=max(0,exit_[0]-entry[1]),cross_check_overlap_mm=entry[1]-exit_[0],g3_unchanged_window_mm=[nip+margin,L-(nip+margin)]))
out['coverage']=cov
step=math.pi*D/cpr*1000
out['resolution']=dict(counts_per_rev=cpr,step_um=step,pixel_pitch_um=50,step_over_pixel_pct=100*step/50,rim_equivalent_of_0p2deg_um=math.pi*D*0.2/360*1000,
    note='14-bit class ABI sensor assumed; the datasheet accuracy of the candidate part is not verified here, the budget keeps the 0.2 deg used for the G3 encoders')
out['counts_rate']=[dict(mode=m['name'],feed_mm_s=m['feed_mm_s'],counts_per_s=m['feed_mm_s']*1000/step) for m in p['scan_modes_r52']]
added=it['moving_mass_added_g'];base=200.0;preload=6.06
out['preload']=dict(added_moving_mass_g=added,g3_assumed_moving_mass_g=base,added_pct=100*added/base,added_weight_n=added/1000*9.81,preload_n=preload,preload_change_pct=100*added/1000*9.81/preload)
out['cross_check']=dict(provisional_limit_mm=0.05,basis='provisional; set on the bench from the measured scatter of the two followers on a calibration target; the controller faults FOLLOWER_MISMATCH when the check input is false in the overlap zone')
(E/'ECR_G3_01_计算.json').write_text(json.dumps(out,ensure_ascii=False,indent=1))
with open(E/'ECR_G3_01_计量覆盖.csv','w',encoding='utf-8-sig') as f:
    f.write('片长mm,入口随动有效区段,出口随动有效区段,合并区段,空档mm,互相校核重叠mm,G3不改的窗口\n')
    for c in cov:f.write(f"{c['length_mm']},{c['entry_follower_valid_mm'][0]}..{c['entry_follower_valid_mm'][1]},{c['exit_follower_valid_mm'][0]}..{c['exit_follower_valid_mm'][1]},{c['union_mm'][0]}..{c['union_mm'][1]},{c['gap_mm']},{c['cross_check_overlap_mm']},{c['g3_unchanged_window_mm'][0]}..{c['g3_unchanged_window_mm'][1]}\n")
print(json.dumps({'step_um':round(step,3),'preload_change_pct':round(out['preload']['preload_change_pct'],2),'added_pct':round(out['preload']['added_pct'],2),'coverage':[(c['length_mm'],c['union_mm'],c['cross_check_overlap_mm']) for c in cov]}))
