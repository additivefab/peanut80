"""First-order budgets. No hardware claims; Python standard library only."""
from pathlib import Path
import json, math
ROOT=Path(__file__).resolve().parents[1]
def calculate(p):
    m=p['film_width_mm']*p['film_length_mm']*p['film_thickness_nominal_mm']*1e-9*p['equivalent_density_assumed_kg_m3']
    a=math.radians(p['magazine_angle_deg_from_horizontal']); w=m*p['g_m_s2']; n=p['batch_size']
    v=p['prefeed_speed_mm_s']; t=p['fault_detection_delay_s']; dec=p['prefeed_deceleration_mm_s2']; margin=p['stop_margin_mm']
    gravity=w*math.sin(a); lower=p['intersheet_friction_example_n']+p['residual_adhesion_example_n']+gravity
    upper=p['pickup_tangential_force_example_n']+gravity-p['path_drag_example_n']
    d=v*t+v*v/(2*dec)+margin; available=p['parked_leading_edge_y_mm']-p['double_sheet_station_y_mm']
    scantravel=p['film_length_mm']-p['parked_leading_edge_y_mm']+p['output_isolated_tail_y_mm']
    r=p['guided_turn_radius_mm']; ang=a
    return {
      'single_mass_g_assumed':m*1000,'batch_mass_g_assumed':n*m*1000,
      'stack_thickness_nominal_mm':n*p['film_thickness_nominal_mm'],
      'stack_thickness_range_mm':[n*x for x in p['film_thickness_trial_range_mm']],
      'single_weight_n':w,'single_down_slope_n':gravity,
      'stack_down_slope_n':n*gravity,'stack_normal_n':n*w*math.cos(a),
      'normal_single_sheet_n':w*math.cos(a),
      'thick_stack_normal_n':n*w*math.cos(a)*max(p['film_thickness_trial_range_mm'])/p['film_thickness_nominal_mm'],
      'thick_stack_follower_headroom_n':p['front_contact_force_target_n']-n*w*math.cos(a)*max(p['film_thickness_trial_range_mm'])/p['film_thickness_nominal_mm'],
      'follower_added_force_full_stack_n':p['front_contact_force_target_n']-n*w*math.cos(a),
      'follower_added_force_last_sheet_n':p['front_contact_force_target_n']-w*math.cos(a),
      'retard_lower_bound_example_n':lower,'retard_upper_bound_example_n':upper,
      'retard_window_width_example_n':upper-lower,
      'retard_torque_example_mNm':p['retard_effective_force_example_n']*p['retard_radius_mm'],
      'stop_budget_mm':d,'qualified_path_to_park_mm':available,
      'qualified_path_required_mm':p['film_length_mm']+d,
      'qualified_path_margin_mm':available-p['film_length_mm']-d,
      'turn_arc_length_mm':r*ang,'turn_y_span_mm':r*math.sin(ang),'turn_z_drop_mm':r*(1-math.cos(ang)),
      'film_bending_strain_example':p['film_thickness_nominal_mm']/(2*r),
      'film_bending_strain_thick_example':max(p['film_thickness_trial_range_mm'])/(2*r),
      'slow_scan_transport_length_mm':scantravel,
      'time_examples':[{'v_mm_s':v,'scan_only_batch_min':n*p['film_length_mm']/v/60,'serial_batch_budget_min':n*(scantravel/v+p['per_sheet_extra_time_budget_s'])/60} for v in p['scan_speed_examples_mm_s']],
      'independent_per_sheet_success_required':p['batch_success_probability_target_example']**(1/n),
      'zero_failure_95_upper_bound_15000':1-0.05**(1/15000),
      'independence_warning':'Reliability products and bounds assume independent representative trials; humidity, aging and contamination correlate failures.'
    }
if __name__=='__main__':
    p=json.loads((ROOT/'engineering/parameters.json').read_text());r=calculate(p)
    (ROOT/'engineering/calculated_results.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
    print(json.dumps(r,ensure_ascii=False,indent=2))
