"""Write the comparison, recipe, takt and station CSV tables from calculated results."""
import csv,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'engineering'));import calculate as C
p=json.loads((ROOT/'engineering/parameters.json').read_text());r=C.calculate(p)
def w(name,head,rows):
    with open(ROOT/'engineering'/name,'w',newline='',encoding='utf-8-sig') as f:c=csv.writer(f);c.writerow(head);c.writerows(rows)
w('架构对比.csv',['方案','宽mm','深mm','高mm','占地m2','体积m3','导向弯道deg','对扫描仪本体的改动','长片同通道'],
  [[o['option'],*o['envelope_mm_WDH'],round(o['footprint_m2'],3),round(o['volume_m3'],3),o['guided_bend_deg'],o['scanner_core_change'],'是' if o['long_film_through_same_path'] else '否'] for o in r['architecture_options']])
w('分片配方.csv',['片厚mm','单张g','50张g','片堆厚mm','配重压力N','坝角deg','爬坝所需推力N','可用推力N','余量名义','余量顶面偏高','送片夹持力N','限矩下限N','限矩上限N','限矩中值mNm','片尾阻力上限N','升片力N'],
  [[x['thickness_mm'],round(x['single_mass_g'],2),round(x['stack_mass_g']),x['stack_thickness_mm'],p['pick_arm_force_recipes_n']['%.2f'%x['thickness_mm']],x['dam_angle_deg'],round(x['push_needed_nominal_n'],3),round(x['top_sheet_push_available_n'],3),round(x['top_sheet_margin_nominal'],2),round(x['top_sheet_margin_worst_level'],2),x['feed_nip_force_n'],round(x['retard_window_n'][0],2),round(x['retard_window_n'][1],2),round(x['retard_torque_mid_mNm'],2),round(x['tail_drag_on_stack_max_n'],3),round(x['lift_force_at_front_full_n'],2)] for x in r['per_thickness']])
w('节拍.csv',['扫描档','行平均','走片mm/s','覆盖密度','预检往返','每张min','50张h','8小时张数','片尾才发现双张的最大损失min'],
  [[x['mode'],x['line_average'],x['feed_mm_s'],x['density_to'],'是' if x['precheck'] else '否',round(x['per_sheet_min'],2),round(x['batch_hours'],2),x['sheets_per_8h'],round(x['worst_loss_if_double_found_at_tail_min'],2)] for x in r['batch_time']])
w('路线站位.csv',['位置','Y_mm'],[[k,round(v,1)] for k,v in r['path']['stations_y_mm'].items()])
