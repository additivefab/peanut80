"""ADF50 V0.2 first-order budgets: magazine forces, dam/retard separation windows, folded path geometry,
envelope and batch time for the R5.2 scan modes. Python standard library only; no hardware claims."""
from pathlib import Path
import json, math
ROOT=Path(__file__).resolve().parents[1]
def dam_lift_factor(beta_deg,mu):
    """Lateral (edge-lifting) force per unit push force for a sheet edge pushed against a dam inclined
    beta to the sheet plane, with dam friction mu. <=0 means the edge self-locks."""
    b=math.radians(beta_deg);return (math.cos(b)-mu*math.sin(b))/(math.sin(b)+mu*math.cos(b))
def calculate(p):
    g=p['g_m_s2'];n=p['batch_size'];a=math.radians(p['magazine_angle_deg_from_horizontal'])
    W,Lf=p['film_width_mm']/1000,p['film_length_mm']/1000
    out={}
    # ---- per-thickness magazine and separation budget
    rows=[]
    for key in sorted(p['pick_arm_force_recipes_n'],key=float):
        t=float(key)/1000;m=W*Lf*t*p['equivalent_density_assumed_kg_m3'];w=m*g
        EI=p['film_modulus_assumed_gpa']*1e9*W*t**3/12
        need_lift=3*EI*(p['dam_height_mm']/1000)/(p['pick_to_dam_free_length_mm']/1000)**3
        k=dam_lift_factor(p['dam_angle_recipes_deg'][key],p['dam_friction_assumed'])
        push_need=need_lift/k
        N=p['pick_arm_force_recipes_n'][key];Gs=w*math.sin(a)
        push_top=(p['pick_roller_friction_assumed']-p['intersheet_friction_assumed'])*N+Gs       # top sheet: roller drive minus drag from sheet 2
        push_second_max_adhesion=push_need-Gs                                                    # sheet 2 sees equal friction on both faces; only weight + adhesion push it
        retard_lo=p['intersheet_friction_assumed']*N+p['residual_adhesion_example_n']+Gs          # must stop a dragged second sheet
        retard_hi=p['pick_roller_friction_assumed']*N+Gs-p['path_drag_example_n']                 # must not stop the top sheet
        rows.append(dict(thickness_mm=float(key),single_mass_g=m*1000,stack_mass_g=n*m*1000,stack_thickness_mm=n*float(key),
            stack_down_slope_on_dam_n=n*Gs,stack_normal_on_tray_n=n*w*math.cos(a),
            pick_interface_force_full_stack_n=N+w*math.cos(a),pick_interface_force_last_sheet_n=N+w*math.cos(a),
            v01_interface_force_full_stack_n=max(p['v01_reference']['front_contact_force_target_n'],n*w*math.cos(math.radians(p['v01_reference']['magazine_angle_deg']))),
            v01_natural_normal_full_stack_n=n*w*math.cos(math.radians(p['v01_reference']['magazine_angle_deg'])),
            bending_stiffness_EI_Nm2=EI,dam_angle_deg=p['dam_angle_recipes_deg'][key],dam_lift_factor=k,
            edge_lift_force_needed_n=need_lift,push_needed_to_climb_dam_n=push_need,pick_arm_force_n=N,
            top_sheet_push_available_n=push_top,top_sheet_margin_ratio=push_top/push_need,
            self_feed_push_by_weight_n=Gs,self_feed_ratio=Gs/push_need,
            second_sheet_adhesion_allowed_n=push_second_max_adhesion,
            retard_window_n=[retard_lo,retard_hi],retard_window_width_n=retard_hi-retard_lo,
            retard_torque_mid_mNm=(retard_lo+retard_hi)/2*p['retard_radius_mm']))
    out['per_thickness']=rows
    # ---- folded path (side view Y,Z). Horizontal run from the park position out of the front panel, then a C-turn
    # up and back over the scanner so the steep run and magazine rise toward +Y.
    R=p['guided_turn_radius_mm'];zf=p['scan_plane_z_mm'];yh=p['horizontal_run_start_y_mm'];turn=math.pi-a
    arc_end=(yh-R*math.sin(turn),zf+R*(1-math.cos(turn)));u=(math.cos(a),math.sin(a))                       # unit vector up the slope (+Y, +Z)
    pt=lambda s:(arc_end[0]+s*u[0],arc_end[1]+s*u[1])
    s_ds=p['steep_run_to_double_station_mm'];s_ret=s_ds+p['double_sheet_station_after_retard_mm'];s_dam=s_ret+p['retard_nip_after_dam_mm']
    s_top=s_dam+p['magazine_support_length_mm']
    h_run=p['parked_leading_edge_y_mm']-yh;arc_len=R*turn
    v,td,dec=p['prefeed_speed_mm_s'],p['fault_detection_delay_s'],p['prefeed_deceleration_mm_s2']
    stop=v*td+v*v/(2*dec)+p['stop_margin_mm'];path=h_run+arc_len+s_ds
    nrm=(u[1],-u[0])                                                                                       # normal pointing to the tray side (+Y, -Z)
    depth=p['magazine_stack_depth_budget_mm']+p['magazine_tray_thickness_mm']
    corner=(p['scanner_front_panel_y_mm'],p['scanner_top_z_mm'])
    perp=(corner[0]-arc_end[0])*(-u[1])+(corner[1]-arc_end[1])*u[0]                                         # signed distance, positive = corner below the path
    perp=abs((corner[0]-arc_end[0])*u[1]-(corner[1]-arc_end[1])*u[0])
    tray_low=(pt(s_top)[0]+depth*nrm[0],pt(s_top)[1]+depth*nrm[1])
    y_front=yh-R-20;z_top=pt(s_top)[1]+40;y_rear=p['scanner_rear_panel_y_mm']+10+p['output_tray_size_mm'][1]*math.cos(math.radians(p['output_tray_tilt_deg']))
    env=[p['scanner_width_mm'],y_rear-y_front,z_top]
    v01=p['v01_reference']['working_envelope_mm_WDH']
    out['path']=dict(turn_angle_deg=math.degrees(turn),arc_length_mm=arc_len,horizontal_run_mm=h_run,arc_end_yz=arc_end,
        double_station_yz=pt(s_ds),retard_nip_yz=pt(s_ret),dam_yz=pt(s_dam),magazine_top_yz=pt(s_top),
        stop_budget_mm=stop,qualified_path_to_park_mm=path,qualified_path_required_mm=p['film_length_mm']+stop,
        qualified_path_margin_mm=path-p['film_length_mm']-stop,
        clearance_magazine_tray_to_scanner_top_front_corner_mm=perp-depth,
        magazine_overhang_over_scanner_mm=pt(s_top)[0]-p['scanner_front_panel_y_mm'],
        film_bending_strain=[float(k)/(2*R) for k in sorted(p['pick_arm_force_recipes_n'],key=float)])
    out['envelope']=dict(working_envelope_mm_WDH=env,front_y_mm=y_front,rear_y_mm=y_rear,top_z_mm=z_top,
        front_protrusion_beyond_scanner_mm=p['scanner_front_panel_y_mm']-y_front,
        v01_envelope_mm_WDH=v01,footprint_m2=env[0]*env[1]/1e6,v01_footprint_m2=v01[0]*v01[1]/1e6,
        footprint_reduction_pct=100*(1-env[0]*env[1]/(v01[0]*v01[1])),volume_m3=env[0]*env[1]*env[2]/1e9,v01_volume_m3=v01[0]*v01[1]*v01[2]/1e9)
    # ---- batch time: only the 300 mm image length runs at scan speed; lead-in and tail isolation at fast traverse
    lead=-p['parked_leading_edge_y_mm']+p['output_isolated_tail_y_mm'];T=[]
    for m_ in p['scan_modes_r52']:
        per=p['film_length_mm']/m_['feed_mm_s']+lead/p['fast_traverse_mm_s']+p['per_sheet_extra_time_budget_s']
        allslow=(p['film_length_mm']+lead)/m_['feed_mm_s']+p['per_sheet_extra_time_budget_s']
        T.append(dict(mode=m_['name'],line_average=m_['line_average'],feed_mm_s=m_['feed_mm_s'],density_to=m_['density_to'],
            per_sheet_min=per/60,batch_hours=n*per/3600,batch_hours_if_whole_travel_at_scan_speed=n*allslow/3600,
            sheets_per_8h=int(8*3600//per)))
    out['batch_time']=T
    out['independent_per_sheet_success_required']=p['batch_success_probability_target_example']**(1/n)
    out['note']='All values are calculated from assumed inputs. Nothing here is a measurement.'
    return out
if __name__=='__main__':
    p=json.loads((ROOT/'engineering/parameters.json').read_text());r=calculate(p)
    (ROOT/'engineering/calculated_results.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
    print(json.dumps(r,ensure_ascii=False,indent=1))
