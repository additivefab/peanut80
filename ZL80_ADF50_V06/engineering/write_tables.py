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
ho=r['handoff'];bsup=r['bend_support']
w('交接与计量.csv',['项','值','说明'],[
 ['排片辊夹点路径位置 s mm',round(ho['exit_nip_s_mm'],1),'扫描线 s=0，沿片路径弧长计算'],['主牵引到排片夹点 mm',round(ho['exit_span_mm'],1),'(152-42)+弧长+8'],
 ['300 mm 片重叠量 mm',round(ho['overlap_mm_L300'],1),'V0.4 原文 93 mm 是片尾已脱离主辊后的量，不是重叠量'],['260 mm 片重叠量 mm',round(ho['min_length_overlap_mm'],1),'最短片长下限'],
 ['跟随触发时排片夹入深度 mm',round(ho['grip_depth_at_follow_trigger_mm'],1),'片尾 s=+12'],['跟随触发时主辊剩余夹持 mm',ho['master_remaining_grip_at_trigger_mm'],'42-12'],
 ['G3 不改的计量窗口 mm',f"{ho['g3_unchanged_window_mm'][0]}..{ho['g3_unchanged_window_mm'][1]}",'长度 206；前后各含 5 mm 夹持余量'],
 ['加出口随动编码器后的窗口 mm','0..300','ECR-G3-01；头部由入口随动测量，尾部由出口随动测量'],
 ['入口辊保持到片头 s mm',ho['entry_hold_until_head_mm'],'主辊夹持确认后才释放'],['入口辊离开片尾时片头位置 mm',round(ho['entry_nip_leaves_sheet_when_head_mm'],1),'此前入口辊仍夹着片'],
 ['停车距离 mm',round(ho['stop_distance_mm'],2),'50 mm/s，70 ms 延迟，200 mm/s²，保护量 2 mm']])
w('弯道托辊.csv',['弯道','托辊数','托辊直径mm','节距deg','弦长mm','弦中矢高mm','辊面间隙mm','版本'],
 [[k,v[k]['count'],v[k]['roller_od_mm'],round(v[k]['pitch_deg'],2),round(v[k]['chord_mm'],2),round(v[k]['sagitta_mm'],3),round(v[k]['roller_surface_gap_mm'],2),n] for n,v in (('V0.6',bsup['v06']),('V0.4',bsup['v04'])) for k in ('entry','exit')])
w('路线点位.csv',['位置','Y_mm','Z_mm'],[[k,*v] for k,v in r['path']['points_yz'].items()])
