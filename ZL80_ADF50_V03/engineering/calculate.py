"""ADF50 V0.3 (in-plane straight-through, integrated into ZL80) first-order budgets: separation forces on a flat
stack, lift plate, path stations, envelope, architecture comparison and batch time. Standard library only.
All inputs are assumptions; nothing here is a measurement."""
from pathlib import Path
import json, math
ROOT=Path(__file__).resolve().parents[1]
def dam_lift_factor(beta_deg,mu):
    """Edge-lifting force per unit push force for a sheet edge pushed against a ramp inclined beta to the
    sheet plane with friction mu. <=0 means the edge self-locks."""
    b=math.radians(beta_deg);return (math.cos(b)-mu*math.sin(b))/(math.sin(b)+mu*math.cos(b))
def calculate(p):
    g=p['g_m_s2'];n=p['batch_size'];W,Lf=p['film_width_mm']/1000,p['film_length_mm']/1000;out={}
    mur,mus=p['pick_roller_friction_assumed'],p['intersheet_friction_assumed']
    rows=[]
    for key in sorted(p['pick_arm_force_recipes_n'],key=float):
        t=float(key)/1000;m=W*Lf*t*p['equivalent_density_assumed_kg_m3'];w=m*g
        EI=p['film_modulus_assumed_gpa']*1e9*W*t**3/12
        k=dam_lift_factor(p['dam_angle_recipes_deg'][key],p['dam_friction_assumed'])
        need=lambda h:3*EI*(h/1000)/(p['pick_to_dam_free_length_mm']/1000)**3/k
        N=p['pick_arm_force_recipes_n'][key];push_top=(mur-mus)*N           # roller drive minus drag from sheet 2
        Nn=p['feed_nip_force_recipes_n'][key]
        lo=mus*Nn+p['residual_adhesion_example_n'];hi=mur*Nn-p['path_drag_example_n']
        rows.append(dict(thickness_mm=float(key),single_mass_g=m*1000,stack_mass_g=n*m*1000,stack_thickness_mm=n*float(key),
            pick_interface_force_full_stack_n=N+w,pick_interface_force_last_sheet_n=N+w,
            dam_angle_deg=p['dam_angle_recipes_deg'][key],dam_lift_factor=k,
            push_needed_nominal_n=need(p['dam_height_mm']),push_needed_worst_level_n=need(p['dam_height_mm']+p['top_sheet_level_tolerance_mm']),
            top_sheet_push_available_n=push_top,top_sheet_margin_nominal=push_top/need(p['dam_height_mm']),
            top_sheet_margin_worst_level=push_top/need(p['dam_height_mm']+p['top_sheet_level_tolerance_mm']),
            second_sheet_adhesion_allowed_n=need(p['dam_height_mm']-p['top_sheet_level_tolerance_mm']),
            feed_nip_force_n=Nn,retard_window_n=[lo,hi],retard_window_width_n=hi-lo,retard_torque_mid_mNm=(lo+hi)/2*p['retard_radius_mm'],
            tail_drag_on_stack_max_n=mus*w,
            lift_force_at_front_full_n=(n*w+p['lift_plate_mass_g']/1000*g)/2))
    out['per_thickness']=rows
    # ---- stations along the straight path (Y), everything at Z = scan plane
    dam=p['dam_top_y_mm'];pick=dam-p['pick_to_dam_free_length_mm'];rear=dam-p['lift_plate_length_mm']-p['magazine_rear_allowance_mm']
    travel=max(float(k) for k in p['pick_arm_force_recipes_n'])*n+p['lift_margin_mm']
    st=dict(magazine_rear_y=rear,pick_contact_y=pick,dam_top_y=dam,front_panel_y=p['scanner_front_panel_y_mm'],feed_nip_y=p['feed_nip_y_mm'],
        double_sheet_sensor_y=p['double_sheet_sensor_y_mm'],film_sensor_entry_y=p['film_sensor_entry_y_mm'],input_scan_nip_y=p['input_scan_nip_y_mm'],
        scan_line_y=0,output_scan_nip_y=p['output_scan_nip_y_mm'],film_sensor_exit_y=p['film_sensor_exit_y_mm'],eject_nip_y=p['eject_nip_y_mm'],
        rear_panel_y=p['scanner_rear_panel_y_mm'])
    t=math.radians(p['output_tray_tilt_deg']);y_out=p['scanner_rear_panel_y_mm']+p['output_tray_gap_from_panel_mm']+p['output_tray_size_mm'][1]*math.cos(t)
    st['output_tray_end_y']=y_out
    Lfm=p['film_length_mm']
    out['path']=dict(stations_y_mm=st,bends=0,max_guided_turn_deg=0,film_bending_strain=0.0,
        stack_top_ramp_deg=math.degrees(math.atan(travel/p['lift_plate_length_mm'])),lift_travel_mm=travel,
        dam_to_feed_nip_mm=p['feed_nip_y_mm']-dam,feed_nip_to_scan_nip_mm=p['input_scan_nip_y_mm']-p['feed_nip_y_mm'],
        unsupported_span_max_mm=max(p['feed_nip_y_mm']-dam,p['input_scan_nip_y_mm']-p['feed_nip_y_mm'],p['eject_nip_y_mm']-p['output_scan_nip_y_mm']),
        tail_on_stack_when_scan_starts_mm=Lfm-(p['parked_leading_edge_y_mm']-dam),
        sensor_to_park_mm=p['parked_leading_edge_y_mm']-p['double_sheet_sensor_y_mm'],
        precheck_forward_travel_mm=Lfm-(p['parked_leading_edge_y_mm']-p['double_sheet_sensor_y_mm'])+p['precheck_overrun_mm'],
        precheck_lead_max_y_mm=p['double_sheet_sensor_y_mm']+Lfm+p['precheck_overrun_mm'],
        tail_clear_of_exit_nip_when_lead_at_y_mm=p['output_isolated_tail_y_mm']+Lfm)
    env=[p['scanner_size_mm_WDH'][0],y_out-rear,p['scanner_size_mm_WDH'][2]]
    ref=p['reference_envelopes_mm_WDH'];c=p['tilted_alternative'];a=math.radians(c['path_angle_deg']);hb=c['core_section_mm']*(math.cos(a)+math.sin(a))/2
    up=-rear;zs=hb+c['base_allowance_mm'];tt=math.radians(c['output_tray_tilt_deg'])
    tilt=[env[0],max(hb,up*math.cos(a))+p['scanner_rear_panel_y_mm']*math.cos(a)+p['output_tray_size_mm'][1]*math.cos(tt),zs+up*math.sin(a)]
    def row(name,e,bend,core,longfilm):return dict(option=name,envelope_mm_WDH=[round(x) for x in e],footprint_m2=e[0]*e[1]/1e6,volume_m3=e[0]*e[1]*e[2]/1e9,
        guided_bend_deg=bend,scanner_core_change=core,long_film_through_same_path=longfilm)
    out['architecture_options']=[
        row('A V0.1 外置模块，片仓80°，R60弯道，整张缓冲',ref['V0.1'],100,'无',False),
        row('B V0.2 片仓65°折回扫描仪上方，R60弯道',ref['V0.2'],115,'无',False),
        row('C 整机倾斜60°直通（估算）',tilt,0,'光学核心整体旋转，新机架和机箱',False),
        row('D V0.3 同平面直通，分离器并入前面板',env,0,'前后面板开口，迷宫换成辊组',True)]
    out['envelope']=dict(working_envelope_mm_WDH=env,front_y_mm=rear,rear_y_mm=y_out,top_z_mm=env[2],footprint_m2=env[0]*env[1]/1e6,volume_m3=env[0]*env[1]*env[2]/1e9,
        added_height_over_scanner_mm=0,magazine_lid_top_z_mm=p['magazine_lid_top_z_mm'])
    # ---- batch time
    T=[];lead=-p['parked_leading_edge_y_mm']+p['output_isolated_tail_y_mm']
    pc=out['path']['precheck_forward_travel_mm']
    for m_ in p['scan_modes_r52']:
        feed_in=(p['parked_leading_edge_y_mm']-dam)/p['prefeed_speed_mm_s'];pre=2*pc/p['precheck_speed_mm_s'] if m_['precheck'] else 0.0
        eject=(p['scanner_rear_panel_y_mm']+20-p['output_isolated_tail_y_mm'])/p['eject_speed_mm_s']
        per=Lfm/m_['feed_mm_s']+lead/p['fast_traverse_mm_s']+feed_in+pre+eject+p['per_sheet_extra_time_budget_s']
        T.append(dict(mode=m_['name'],line_average=m_['line_average'],feed_mm_s=m_['feed_mm_s'],density_to=m_['density_to'],precheck=m_['precheck'],
            precheck_s=pre,per_sheet_min=per/60,batch_hours=n*per/3600,sheets_per_8h=int(8*3600//per),
            worst_loss_if_double_found_at_tail_min=0.0 if m_['precheck'] else Lfm/m_['feed_mm_s']/60))
    out['batch_time']=T
    out['independent_per_sheet_success_required']=p['batch_success_probability_target_example']**(1/n)
    out['note']='All values are calculated from assumed inputs. Nothing here is a measurement.'
    return out
if __name__=='__main__':
    p=json.loads((ROOT/'engineering/parameters.json').read_text());r=calculate(p)
    (ROOT/'engineering/calculated_results.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
    print(json.dumps(r,ensure_ascii=False,indent=1))
