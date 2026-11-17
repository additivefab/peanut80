"""Write the comparison, recipe, bend-load, takt and path-point CSV tables from calculated results."""
import csv,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'engineering'));import calculate as C
p=json.loads((ROOT/'engineering/parameters.json').read_text());r=C.calculate(p)
def w(name,head,rows):
    with open(ROOT/'engineering'/name,'w',newline='',encoding='utf-8-sig') as f:c=csv.writer(f);c.writerow(head);c.writerows(rows)
w('架构对比.csv',['方案','宽mm','深mm','高mm','占地m2','弯道deg','单向走片','对扫描仪本体的改动','满足进深700高650'],
  [[o['option'],*o['envelope_mm_WDH'],round(o['footprint_m2'],3),'+'.join(str(x) for x in o['bends_deg']) or '0','是' if o['one_way'] else '否',o['core_change'],'是' if o['fits_700x650'] else '否'] for o in r['architecture_options']])
w('分片配方.csv',['片厚mm','单张g','50张g','配重压力N','坝角deg','爬坝所需推力N','可用推力N','余量名义','余量顶面偏高','自重自滑比','第二张允许粘附N','送片夹持力N','限矩下限N','限矩上限N','限矩中值mNm','整叠压坝N','推片板力N'],
  [[x['thickness_mm'],round(x['single_mass_g'],2),round(x['stack_mass_g']),x['pick_interface_force_full_stack_n'],x['dam_angle_deg'],round(x['push_needed_nominal_n'],3),round(x['top_sheet_push_available_n'],3),round(x['top_sheet_margin_nominal'],2),round(x['top_sheet_margin_worst_level'],2),round(x['self_feed_by_weight_ratio'],2),round(x['second_sheet_adhesion_allowed_n'],3),x['feed_nip_force_n'],round(x['retard_window_n'][0],2),round(x['retard_window_n'][1],2),round(x['retard_torque_mid_mNm'],2),round(x['stack_load_on_dam_n'],2),round(x['plate_force_full_stack_n'],2)] for x in r['per_thickness']])
w('弯道受力.csv',['片厚mm','弯曲应变%','外侧导向正压力N','托辊阻力N','若滑动导板阻力N','扫描时轴向力最小N','扫描时轴向力最大N','出口上推所需N','100mm自由跨失稳载荷N'],
  [[x['thickness_mm'],round(x['bend_strain_pct'],3),round(x['bend_outer_guide_normal_n'],3),round(x['bend_drag_idler_n'],4),round(x['bend_drag_if_sliding_n'],3),round(x['scan_axial_force_range_n'][0],3),round(x['scan_axial_force_range_n'][1],3),round(x['exit_push_needed_max_n'],3),round(x['free_span_100mm_buckling_load_n'],3)] for x in r['per_thickness']])
w('节拍.csv',['扫描档','行平均','走片mm/s','覆盖密度','每张min','50张h','8小时张数','尾段才发现双张的最大损失min'],
  [[x['mode'],x['line_average'],x['feed_mm_s'],x['density_to'],round(x['per_sheet_min'],2),round(x['batch_hours'],2),x['sheets_per_8h'],round(x['worst_loss_if_late_double_min'],1)] for x in r['batch_time']])
w('路线点位.csv',['位置','Y_mm','Z_mm'],[[k,*v] for k,v in r['path']['points_yz'].items()])
