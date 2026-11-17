"""ADF50 V0.6 (one-way flow: gravity slide magazine in front, standing output bin behind) first-order budgets:
side-view geometry, separation forces on the inclined stack, bend loads, envelope, option comparison, batch time.
Standard library only. All inputs are assumptions; nothing here is a measurement."""
from pathlib import Path
import json, math
ROOT=Path(__file__).resolve().parents[1]
def dam_lift_factor(beta_deg,mu):
    """Edge-lifting force per unit push force for a sheet edge pushed against a ramp inclined beta to the
    sheet plane with friction mu. <=0 means the edge self-locks."""
    b=math.radians(beta_deg);return (math.cos(b)-mu*math.sin(b))/(math.sin(b)+mu*math.cos(b))
def geometry(p):
    """Side view (Y,Z). Film travels toward +Y everywhere: down the magazine slope, through the entry bend
    (centre above the path), horizontally through the scanner, up the exit bend (centre above the path)."""
    R=p['bend_radius_mm'];zf=p['scan_plane_z_mm'];a=math.radians(p['magazine_angle_deg_from_horizontal']);b=math.radians(p['output_bin_angle_deg_from_horizontal'])
    be=(p['scanner_front_panel_y_mm']-p['bend_gap_from_panel_mm'],zf)                 # entry bend end (horizontal tangent)
    bs=(be[0]-R*math.sin(a),zf+R*(1-math.cos(a)));u=(-math.cos(a),math.sin(a))          # entry bend start, unit vector up the slope
    st=p['slope_station_from_bend_start_mm'];pt=lambda s:(bs[0]+s*u[0],bs[1]+s*u[1])
    s_top=st['dam_top']+p['magazine_support_length_mm']+p['magazine_rear_allowance_mm']
    nt=(-math.sin(a),-math.cos(a))                                                   # normal from the film path toward the tray (down/front)
    xs=(p['scanner_rear_panel_y_mm']+p['rear_bend_gap_mm'],zf)                 # exit bend start
    xe=(xs[0]+R*math.sin(b),zf+R*(1-math.cos(b)));u2=(math.cos(b),math.sin(b))        # exit bend end, unit vector up the bin
    pt2=lambda s:(xe[0]+s*u2[0],xe[1]+s*u2[1]);s2_top=p['eject_nip_after_bend_mm']+p['output_bin_length_mm']
    n2=(math.sin(b),-math.cos(b))                                                    # normal toward the bin back wall (rear)
    return dict(R=R,a=a,b=b,entry_bend_end=be,entry_bend_start=bs,u_in=u,n_tray=nt,
        sensor=pt(st['double_sheet_sensor']),feed_nip=pt(st['feed_retard_nip']),dam=pt(st['dam_top']),pick=pt(st['pick_contact']),mag_top=pt(s_top),s_top=s_top,
        exit_bend_start=xs,exit_bend_end=xe,u_out=u2,n_bin=n2,eject_nip=pt2(p['eject_nip_after_bend_mm']),bin_top=pt2(s2_top),
        entry_arc_mm=R*a,exit_arc_mm=R*b)
def lift_range(p):
    """Crank angle range of the lift arms. Arm tip centre sits 3 mm below the plate axis offset at retraction
    (plate 2 mm thick, arm 5 mm thick, axis 7.5 mm below the plate top at full retraction)."""
    L=p['lift_arm_length_mm'];tr=max(float(k) for k in p['pick_arm_force_recipes_n'])*p['batch_size']+p['plate_margin_mm']
    s0,s1=3.0/L,(3.0+tr)/L
    return [math.degrees(math.asin(s0)),math.degrees(math.asin(s1))] if s1<=1 else None
def idler_support(p,count,od):
    """Polygonal support of an R-radius bend by free rollers: chord and mid-span sagitta of a stiff sheet between rollers."""
    G=geometry(p);R=G['R'];out={}
    for name,ang in (('entry',G['a']),('exit',G['b'])):
        d=ang/(count+1);c=2*R*math.sin(d/2);out[name]=dict(count=count,roller_od_mm=od,pitch_deg=math.degrees(d),chord_mm=c,sagitta_mm=c*c/(8*R),roller_surface_gap_mm=c-od)
    return out
def handoff(p,G,Lfm):
    """Hand-off numbers along the path length s (scan line s=0). Head position h, tail t=h-L."""
    h=p['handoff'];m=h['grip_margin_mm'];dn,mn=h['drive_nip_s_mm'],h['measure_nip_s_mm']
    exit_s=G['exit_bend_start'][0]+G['exit_arc_mm']+p['eject_nip_after_bend_mm']
    out=dict(exit_nip_s_mm=exit_s,exit_span_mm=exit_s-dn)
    out['overlap_mm_L300']=Lfm-(exit_s-dn)
    out['grip_depth_at_follow_trigger_mm']=(h['exit_follow_tail_s_mm']+Lfm)-exit_s
    out['master_remaining_grip_at_trigger_mm']=dn-h['exit_follow_tail_s_mm']
    out['min_length_overlap_mm']=h['min_length_mm']-(exit_s-dn)
    out['head_at_follow_trigger_mm']=h['exit_follow_tail_s_mm']+Lfm
    out['v04_claimed_overlap_mm']=93.0
    # metrology windows, G3 unchanged vs with an exit follower encoder
    out['g3_unchanged_window_mm']=[dn+m,Lfm-(abs(mn)+m)];out['g3_unchanged_window_length_mm']=Lfm-2*(dn+m)
    out['with_exit_follower_window_mm']=[0,Lfm]
    out['head_zone_driven_by_entry_rollers_mm']=dn+m
    out['tail_zone_without_independent_measure_mm']=abs(mn)
    out['entry_hold_until_head_mm']=h['entry_hold_head_s_mm'];out['entry_rollers_still_gripping_at_hold_release']=(-(p['entry_nip_y_mm'])<=Lfm-h['entry_hold_head_s_mm'])
    out['entry_nip_leaves_sheet_when_head_mm']=Lfm+p['entry_nip_y_mm']      # tail passes the entry nip
    st=p['stop_budget'];out['stop_distance_mm']=st['speed_mm_s']*(st['detect_ms']+st['filter_ms']+st['actuate_ms'])/1000+st['speed_mm_s']**2/(2*st['decel_mm_s2'])+st['guard_mm']
    return out
def calculate(p):
    g=p['g_m_s2'];n=p['batch_size'];W,Lf=p['film_width_mm']/1000,p['film_length_mm']/1000;out={};G=geometry(p);a=G['a'];R=G['R']
    mur,mus=p['pick_roller_friction_assumed'],p['intersheet_friction_assumed'];Lfm=p['film_length_mm']
    rows=[]
    for key in sorted(p['pick_arm_force_recipes_n'],key=float):
        t=float(key)/1000;m=W*Lf*t*p['equivalent_density_assumed_kg_m3'];w=m*g;Gs=w*math.sin(a)
        EI=p['film_modulus_assumed_gpa']*1e9*W*t**3/12
        k=dam_lift_factor(p['dam_angle_recipes_deg'][key],p['dam_friction_assumed'])
        need=lambda h:3*EI*(h/1000)/(p['pick_to_dam_free_length_mm']/1000)**3/k
        h0,tol=p['dam_height_mm'],p['top_sheet_level_tolerance_mm']
        N=p['pick_arm_force_recipes_n'][key];push_top=(mur-mus)*N+Gs
        Nn=p['feed_nip_force_recipes_n'][key]
        lo=mus*Nn+p['residual_adhesion_example_n']+Gs;hi=mur*Nn+Gs-p['path_drag_example_n']
        bend_normal=4*EI/(R/1000)**2                                    # order-of-magnitude reaction of the film on the outer guide
        euler=math.pi**2*EI/(0.1)**2                                    # pin-ended buckling load of a 100 mm free span, for scale only
        rows.append(dict(thickness_mm=float(key),single_mass_g=m*1000,single_weight_n=w,stack_mass_g=n*m*1000,stack_thickness_mm=n*float(key),
            pick_interface_force_full_stack_n=N,pick_interface_force_last_sheet_n=N,
            stack_load_on_dam_n=n*Gs,plate_force_full_stack_n=(n*w+p['pressure_plate_mass_g']/1000*g)*math.cos(a),
            dam_angle_deg=p['dam_angle_recipes_deg'][key],dam_lift_factor=k,
            push_needed_nominal_n=need(h0),top_sheet_push_available_n=push_top,
            top_sheet_margin_nominal=push_top/need(h0),top_sheet_margin_worst_level=push_top/need(h0+tol),
            self_feed_by_weight_ratio=Gs/need(h0-tol),second_sheet_adhesion_allowed_n=need(h0-tol)-Gs,
            feed_nip_force_n=Nn,retard_window_n=[lo,hi],retard_window_width_n=hi-lo,retard_torque_mid_mNm=(lo+hi)/2*p['retard_radius_mm'],
            slide_back_force_in_bin_n=w*math.sin(G['b']),slide_back_wall_friction_n=p['output_gate']['mu_sheet_wall_assumed']*w*math.cos(G['b']),
            bending_stiffness_EI_Nm2=EI,bend_strain_pct=100*float(key)/(2*R),bend_outer_guide_normal_n=bend_normal,
            bend_drag_idler_n=bend_normal*p['guide_idler_rolling_friction_assumed'],bend_drag_if_sliding_n=bend_normal*p['guide_sliding_friction_assumed'],
            scan_axial_force_range_n=[-(w*math.sin(G['b'])*0.6+2*bend_normal*p['guide_idler_rolling_friction_assumed']),w*math.sin(a)*0.6],
            free_span_100mm_buckling_load_n=euler,exit_push_needed_max_n=w*0.6+bend_normal*p['guide_idler_rolling_friction_assumed']))
    out['per_thickness']=rows
    # ---- path lengths (along the film) from stations to the park position
    st=p['slope_station_from_bend_start_mm'];horiz_in=p['parked_leading_edge_y_mm']-G['entry_bend_end'][0]
    to_park=lambda s:s+G['entry_arc_mm']+horiz_in
    sensor_to_park=to_park(st['double_sheet_sensor']);feed_to_entry=st['feed_retard_nip']+G['entry_arc_mm']+(p['entry_nip_y_mm']-G['entry_bend_end'][0])
    exit_to_eject=(G['exit_bend_start'][0]-p['output_scan_nip_y_mm'])+G['exit_arc_mm']+p['eject_nip_after_bend_mm']
    out['path']=dict(direction='monotonic +Y from magazine top to bin top',
        points_yz={k:[round(v[0],1),round(v[1],1)] for k,v in G.items() if isinstance(v,tuple) and k not in('u_in','n_tray','u_out','n_bin')},
        entry_bend_deg=math.degrees(a),exit_bend_deg=math.degrees(G['b']),bend_radius_mm=R,entry_arc_mm=G['entry_arc_mm'],exit_arc_mm=G['exit_arc_mm'],
        y_monotonic=G['mag_top'][0]<G['dam'][0]<G['entry_bend_start'][0]<G['entry_bend_end'][0]<0<G['exit_bend_start'][0]<G['exit_bend_end'][0]<G['bin_top'][0],
        dam_to_park_mm=to_park(st['dam_top']),sensor_to_park_mm=sensor_to_park,
        fraction_checked_before_scan=min(1.0,sensor_to_park/Lfm),unchecked_tail_mm=max(0.0,Lfm-sensor_to_park),
        feed_nip_to_entry_nip_mm=feed_to_entry,entry_nip_to_scan_nip_mm=p['input_scan_nip_y_mm']-p['entry_nip_y_mm'],
        scan_exit_nip_to_eject_nip_mm=exit_to_eject,lead_past_eject_nip_when_tail_isolated_mm=Lfm-(exit_to_eject-(p['output_isolated_tail_y_mm']-p['output_scan_nip_y_mm'])),
        tail_in_magazine_when_scan_starts_mm=Lfm-to_park(st['dam_top']),
        plate_travel_mm=max(float(k) for k in p['pick_arm_force_recipes_n'])*n+p['plate_margin_mm'],
        lift_arm_angle_range_deg=lift_range(p),entry_nip_to_measure_nip_mm=p['input_scan_nip_y_mm']-p['entry_nip_y_mm'])
    # ---- envelope
    nt,u=G['n_tray'],G['u_in'];hb,hl=p['magazine_housing_below_path_mm'],p['magazine_lid_above_path_mm']
    front=min(G['mag_top'][0]+hb*nt[0],G['entry_bend_start'][0]+hb*nt[0])
    top_in=G['mag_top'][1]-hl*nt[1]+5
    n2=G['n_bin'];rear=max(G['bin_top'][0]+p['output_bin_depth_mm']*n2[0],G['exit_bend_end'][0]+p['output_bin_depth_mm']*n2[0])
    top_out=G['bin_top'][1]+p['output_bin_front_cover_mm']*(-n2[1])+5
    env=[p['scanner_size_mm_WDH'][0],rear-front,max(top_in,top_out,p['scanner_size_mm_WDH'][2])]
    c=p['user_constraints_2026_11_16']
    out['envelope']=dict(working_envelope_mm_WDH=env,front_y_mm=front,rear_y_mm=rear,front_protrusion_mm=p['scanner_front_panel_y_mm']-front,
        rear_protrusion_mm=rear-p['scanner_rear_panel_y_mm'],magazine_top_z_mm=top_in,bin_top_z_mm=top_out,
        footprint_m2=env[0]*env[1]/1e6,volume_m3=env[0]*env[1]*env[2]/1e9,
        depth_margin_to_constraint_mm=c['depth_along_film_travel_mm']-env[1],height_margin_to_constraint_mm=c['height_max_mm']-env[2],
        magazine_overhang_over_scanner_mm=max(0.0,G['mag_top'][0]-hl*nt[0]-p['scanner_front_panel_y_mm']),
        lid_to_front_panel_clearance_mm=p['scanner_front_panel_y_mm']-(G['dam'][0]-hl*nt[0]))
    opts=[dict(o,footprint_m2=o['envelope_mm_WDH'][0]*o['envelope_mm_WDH'][1]/1e6) for o in p['reference_options']]
    opts.append(dict(option='E V0.6 前78°斜仓下滑，7托辊R80弯道，后竖立收片',envelope_mm_WDH=[round(x) for x in env],bends_deg=[round(math.degrees(a)),round(math.degrees(G['b']))],
        one_way=True,core_change='前面板开口装入口辊；后面板不变',footprint_m2=env[0]*env[1]/1e6))
    for o in opts:
        e=o['envelope_mm_WDH'];o['fits_700x650']=e[1]<=c['depth_along_film_travel_mm']+10 and e[2]<=c['height_max_mm']
    out['architecture_options']=opts
    # ---- batch time with the V0.6 hand-off: scan, 45 mm at fast traverse (tail to s=+45), fast eject, bin
    ho=handoff(p,G,Lfm);out['handoff']=ho;out['bend_support']=dict(v06=idler_support(p,p['idler_count_per_bend'],p['idler_od_mm']),v04=idler_support(p,p['v04_idler_count_per_bend'],p['v04_idler_od_mm']))
    T=[];lead=-p['parked_leading_edge_y_mm']+p['handoff']['fast_eject_tail_s_mm']
    for m_ in p['scan_modes_r52']:
        feed_in=to_park(st['dam_top'])/p['prefeed_speed_mm_s']
        eject=(ho['exit_nip_s_mm']+20-p['handoff']['fast_eject_tail_s_mm'])/p['eject_speed_mm_s']
        per=Lfm/m_['feed_mm_s']+lead/p['fast_traverse_mm_s']+feed_in+eject+p['per_sheet_extra_time_budget_s']
        T.append(dict(mode=m_['name'],line_average=m_['line_average'],feed_mm_s=m_['feed_mm_s'],density_to=m_['density_to'],
            per_sheet_min=per/60,batch_hours=n*per/3600,sheets_per_8h=int(8*3600//per),
            worst_loss_if_late_double_min=out['path']['unchecked_tail_mm']/m_['feed_mm_s']/60,status='calculated from the R5.2 photon budget; OD capability unverified'))
    out['batch_time']=T
    out['independent_per_sheet_success_required']=p['batch_success_probability_target_example']**(1/n)
    out['note']='All values are calculated from assumed inputs. Nothing here is a measurement.'
    return out
if __name__=='__main__':
    p=json.loads((ROOT/'engineering/parameters.json').read_text());r=calculate(p)
    (ROOT/'engineering/calculated_results.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
    print(json.dumps(r,ensure_ascii=False,indent=1))
