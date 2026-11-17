"""Nominal scan / packaging budgets, not measured performance. Python standard library only."""
from pathlib import Path
import json, math
ROOT=Path(__file__).resolve().parents[1]
def calculate(p):
    fline=p['facet_count']*p['polygon_rpm']/60
    vx=4*math.pi*p['scan_efl']*p['polygon_rpm']/60
    pix=p['pixel_x_um']/1000
    dwell=pix/vx
    out={"line_hz":fline,"vx_mm_s":vx,"period_ms":1000/fline,
      "scan_100_time_ms":p['scan_span']/vx*1000,"roi_time_ms":p['film_width']/vx*1000,
      "geometric_active_fraction":p['scan_span']/vx*fline,
      "pixel_dwell_us":dwell*1e6,"adc_samples_per_50um":p['adc_msps']*1e6*dwell,
      "pixels_per_roi":round(p['film_width']/pix),"feed_mm_s":p['pixel_y_um']/1000*fline,
      "feed_os16_mm_s":p['pixel_y_um']/1000*fline/16,
      "encoder_step_um":math.pi*p['roller_diameter']/(p['encoder_ppr']*p['quadrature'])*1000,
      "encoder_typ_angle_equiv_um":math.pi*p['roller_diameter']*p['encoder_accuracy_deg_typ']/360*1000,
      "adc_raw_MB_s":p['adc_msps']*p['adc_bits']/8*p['adc_channels'],
      "image_MB_s":round(p['film_width']/pix)*fline*2/1e6,
      "image_MB_m":round(p['film_width']/pix)*1000/(p['pixel_y_um']/1000)*2/1e6,
      "adc_latency_ns":p['adc_cmos_latency']/p['adc_msps']*1000,
      "guide_exit_diagonal_mm":math.hypot(*p['guide_output']),
      "slit_each_end_margin_mm":(p['slot_length']-p['scan_span'])/2,
      "nominal_power_w":32.3,"peak_power_budget_w":52.0,
      "ideal_airflow_cfm_delta10K":32.3/(1.2*1005*10)*2118.88,
      "box_litres":math.prod(p['enclosure'])/1e6}
    eph=6.62607015e-34*299792458/(p['wavelength_nm']*1e-9)
    photon=[]
    for od in [.5,3.5,4.5]:
        ne=p['film_power_example_w']*10**(-od)*p['collection_example']*p['qe_example']*dwell/eph
        current=ne/dwell*1.602176634e-19*p['gain_example']
        photon.append(dict(od=od,photoelectrons_per_pixel=ne,shot_only_sigma_D=(p['excess_noise_example']/ne)**.5/math.log(10),mean_illuminated_anode_A=current))
    out['photon_example']=photon
    if 'signal_chain_review' in p:
        out['signal_chain_review']=signal_chain_review(p)
    return out

K_B=1.380649e-23
Q_E=1.602176634e-19

def cavity_collection(p, port_area, guide_out_area, rho, fresnel):
    """Ideal integrating-cavity estimate (sphere multiplier applied to the closed cylinder).
    Ignores first-strike geometry, liner seams and axial non-uniformity. A Lambertian port
    cannot be concentrated: a guide whose exit is smaller than the port passes at most the
    area ratio (etendue), light it rejects is treated as lost."""
    d,l=p['cavity_id'],p['cavity_length']
    wall=math.pi*d*l+2*math.pi*(d/2)**2
    openings=p['slot_length']*p['slot_width']+port_area
    multiplier=rho/(1-rho*(1-openings/wall))
    port_fraction=port_area/wall*multiplier
    coupling=min(1.0,guide_out_area/port_area)*fresnel
    return dict(port_fraction=port_fraction,guide_coupling=coupling,collection=port_fraction*coupling)

def signal_chain_review(p):
    """Design-review estimate of density noise per 50um pixel for alternative signal chains.
    Assumptions, not measurements. Noise terms: PMT shot noise with excess factor, feedback
    resistor thermal noise in the pixel noise bandwidth 1/(2*dwell), ADC noise averaged over
    the samples in one pixel (treated as independent). Op-amp voltage/current noise, dark
    current, stray light, laser noise, drift and overload recovery are NOT included."""
    r=p['signal_chain_review']
    eph=6.62607015e-34*299792458/(p['wavelength_nm']*1e-9)
    cathode_a_per_w=p['qe_example']*Q_E/eph
    pix=p['pixel_x_um']/1000
    adc_rms_diff=r['adc_full_scale_vpp_diff']/(2*math.sqrt(2))/10**(r['adc_snr_dbfs']/20)
    oem=r.get('oem_measured')
    def oem_sigma(od):
        """Log-linear interpolation of the measured OEM curve; None outside the measured range."""
        xs,ys=oem['od'],oem['sigma_d']
        if od<xs[0] or od>xs[-1]: return None
        for k in range(len(xs)-1):
            if xs[k]<=od<=xs[k+1]:
                t=(od-xs[k])/(xs[k+1]-xs[k])
                return math.exp(math.log(ys[k])*(1-t)+math.log(ys[k+1])*t)
    result=[]
    for v in r['variants']:
        rpm=v['line_hz']*60/v['facets']
        vx=4*math.pi*p['scan_efl']*rpm/60
        dwell=pix/vx
        duty=p['scan_span']/vx*v['line_hz']
        col=cavity_collection(p,v['port_area_mm2'],v['guide_out_area_mm2'],r['wall_reflectance'],r['guide_fresnel'])
        if 'collection_override' in v:  # e.g. Monte-Carlo value for the R5.2 guide plate
            col=dict(col,collection=v['collection_override'],source='override')
        fs_low=r['tia_full_scale_v']/v['rf_ohm']
        gain_hi=v['high_gain']
        fs_high=fs_low/gain_hi if gain_hi else None
        gain=v.get('pmt_gain',p['gain_example'])  # PMT gain; H10720 recommended control range gives ~5e3 minimum
        n_lines=v.get('line_average',1)           # polygon lines averaged into one image row (feed slowed by the same factor)
        fda=v.get('fda_gain',r['fda_gain'])
        anode_per_w=col['collection']*cathode_a_per_w*gain
        power=v['film_power_w']
        auto=power is None
        if auto:  # largest film power that keeps the brightest film density inside PMT and TIA limits
            power=r['bright_fill']*min(r['pmt_anode_max_a'],fs_low)/(anode_per_w*10**(-r['bright_od']))
        noise_bw=1/(2*dwell)
        johnson_a=math.sqrt(4*K_B*r['temperature_k']/v['rf_ohm']*noise_bw)
        n_avg=max(1.0,p['adc_msps']*1e6*dwell)
        rows=[]
        for od in r['od_list']:
            anode=power*10**(-od)*anode_per_w
            ne=anode/gain/Q_E*dwell*n_lines
            use_high=bool(gain_hi) and anode<=0.9*fs_high
            saturated=anode>fs_low or anode>r['pmt_anode_max_a']
            row=dict(od=od,photoelectrons_per_pixel=ne,anode_A=anode,
                     channel='high' if use_high else 'low',saturated=saturated)
            if not saturated:
                adc_a=adc_rms_diff/fda/(gain_hi if use_high else 1)/v['rf_ohm']/math.sqrt(n_avg*n_lines)
                rel=dict(shot=math.sqrt(p['excess_noise_example']/ne),johnson=johnson_a/anode/math.sqrt(n_lines),adc=adc_a/anode,
                         floor=r.get('noise_floor_sigma_d',0.0)*math.log(10))
                if oem: row['oem_measured_sigma_D']=oem_sigma(od)
                for k,x in rel.items():row['sigma_D_'+k]=x/math.log(10)
                row['sigma_D_total']=math.sqrt(sum(x*x for x in rel.values()))/math.log(10)
            rows.append(row)
        ok=[x['od'] for x in rows if not x['saturated'] and x['sigma_D_total']<=r['sigma_d_target']]
        tia_bw=1/(2*math.pi*v['rf_ohm']*v['cf_pf']*1e-12)
        result.append(dict(id=v['id'],facets=v['facets'],line_hz=v['line_hz'],polygon_rpm=rpm,
            scan_duty=duty,pixel_dwell_us=dwell*1e6,pmt_gain=gain,line_average=n_lines,
            feed_mm_s=p['pixel_y_um']/1000*v['line_hz']/n_lines,seconds_per_metre=1000/(p['pixel_y_um']/1000*v['line_hz']/n_lines),
            collection=col,film_power_w=power,film_power_auto_scaled=auto,
            anode_at_od0_A=power*anode_per_w,od0_over_pmt_limit=power*anode_per_w/r['pmt_anode_max_a'],
            tia_full_scale_A=fs_low,high_gain_full_scale_A=fs_high,
            tia_rc_bandwidth_hz=tia_bw,pixel_nyquist_hz=noise_bw,tia_bandwidth_ok=tia_bw>=2*noise_bw,
            max_od_meeting_target=max(ok) if ok else None,per_od=rows))
    out=dict(note=r['note'],sigma_d_target=r['sigma_d_target'],variants=result)
    refs={}
    fl=r.get('noise_floor_sigma_d',0.0)
    for key in ('oem_measured','microtek_measured'):
        ref=r.get(key)
        if not ref: continue
        # Effective photoelectrons per pixel referred to T=1, assuming the noise above the floor is shot noise.
        # Upper bound: lateral correlation in the measured images means several pixels were averaged.
        n0=[p['excess_noise_example']/((s*s-fl*fl)*math.log(10)**2)*10**d
            for d,s in zip(ref['od'],ref['sigma_d']) if 2.3<=d<=4.5 and s>fl]
        refs[key]=dict(note=ref['note'],pixel_um=ref['pixel_um'],od=ref['od'],sigma_d=ref['sigma_d'],
            effective_photoelectrons_at_T1=n0,
            sigma_ratio_per_step=[ref['sigma_d'][k+1]/ref['sigma_d'][k] for k in range(len(ref['od'])-1)])
    out['measured_references']=refs
    out['shot_noise_expected_ratio_per_0p5D']=10**0.25
    out['required_effective_photoelectrons_at_T1_for_target_at_OD4.5']=(
        p['excess_noise_example']/((r['sigma_d_target']**2-fl*fl)*math.log(10)**2)*10**4.5)
    return out
if __name__=='__main__':
    p=json.loads((ROOT/'engineering/parameters.json').read_text())
    v=calculate(p)
    (ROOT/'engineering/calculated_results.json').write_text(json.dumps(v,indent=2))
    print(json.dumps(v,indent=2))
