"""ZL80 G1 analytical scan budget + finite-polygon chief-ray geometry.
No optical prescription, aberration, scatter, or manufacturing qualification.
All lengths are mm; angles are radians inside this module.
"""
from __future__ import annotations
import csv, json, math
from pathlib import Path
from typing import Any
ROOT = Path(__file__).resolve().parents[1]

def load_parameters(path: str | Path | None = None) -> dict[str, Any]:
    doc = json.loads(Path(path or ROOT/'config/master_parameters.json').read_text(encoding='utf-8'))
    p = {k: v['value'] for k, v in doc['parameters'].items()}
    validate(p)
    return p

def validate(p: dict[str, Any]) -> None:
    for k in ('film_width_mm','scan_span_mm','sync_span_mm','slot_length_mm','efl_mm',
              'rpm_nominal','pixel_x_um','pixel_y_um','adc_msps','beam_diameter_mm','wavelength_nm'):
        if not isinstance(p.get(k),(int,float)) or not math.isfinite(p[k]) or p[k] <= 0:
            raise ValueError(f'{k} must be positive and finite')
    n = p['facet_count']
    if not isinstance(n,int) or n < 3: raise ValueError('facet_count must be integer >= 3')
    if not p['film_width_mm'] < p['sync_span_mm'] <= p['scan_span_mm'] < p['slot_length_mm']:
        raise ValueError('expected film < sync <= scan < slot')
    if p['beam_m2'] < 1: raise ValueError('M2 must be >= 1')
    if p['scan_span_mm'] / p['efl_mm'] >= 4*math.pi/n:
        raise ValueError('requested ideal angular span exceeds one facet period')

def budget(p: dict[str, Any], rpm: float | None = None, px_um: float | None = None,
           py_um: float | None = None) -> dict[str,float]:
    rpm = p['rpm_nominal'] if rpm is None else rpm
    px = (p['pixel_x_um'] if px_um is None else px_um)/1000
    py = (p['pixel_y_um'] if py_um is None else py_um)/1000
    if min(rpm,px,py) <= 0: raise ValueError('rpm and pitch must be positive')
    n, f, w, span, sy = (p[k] for k in ('facet_count','efl_mm','film_width_mm','scan_span_mm','sync_span_mm'))
    omega = 2*math.pi*rpm/60
    vx = 2*f*omega
    fl = n*rpm/60
    t_roi = w/vx
    t_scan = span/vx
    fs = p['adc_msps']*1e6
    return {'rpm':rpm,'pixel_x_um':px*1000,'pixel_y_um':py*1000,
        'line_hz':fl,'line_period_ms':1000/fl,'x_velocity_mm_s':vx,'feed_mm_s':fl*py,
        'scan_time_ms':1000*t_scan,'roi_time_ms':1000*t_roi,'sync_time_ms':1000*sy/vx,
        'scan_duty':t_scan*fl,'roi_duty':t_roi*fl,'optical_half_deg':span/(2*f)*180/math.pi,
        'mechanical_half_deg':span/(4*f)*180/math.pi,'pixel_dwell_us':px/vx*1e6,
        'instant_pixel_MHz':vx/px/1e6,'average_pixel_MHz':w/px*fl/1e6,
        'pixels_per_roi':w/px,'adc_samples_per_pixel':fs*px/vx,'adc_samples_per_roi_nominal':fs*t_roi,
        'feed_during_roi_um':fl*py*t_roi*1000,'roi_start_after_sos_us':(sy-w)/2/vx*1e6,
        'timing_rms_budget_ns':p['jitter_target_um']/1000/vx*1e9,
        'raw_MB_s':fs*p['adc_bits']/8*p['adc_channels']/1e6,
        'image_MB_s':w/px*fl*p['adc_bits']/8/1e6,
        'roller_rpm':fl*py/(math.pi*p['roller_diameter_mm'])*60,
        'encoder_quantization_um':math.pi*p['roller_diameter_mm']/(p['encoder_ppr']*p['quadrature_factor'])*1000}

def gaussian_budget(p: dict[str, Any]) -> dict[str,float]:
    # M² parameter is a single named beam-quality value, not squared again.
    lam = p['wavelength_nm']*1e-6
    d = 4*p['beam_m2']*lam*p['efl_mm']/(math.pi*p['beam_diameter_mm'])
    zr = math.pi*(d/2)**2/(p['beam_m2']*lam)
    return {'ideal_diameter_1e2_um':d*1000,'ideal_fwhm_um':d*1000*math.sqrt(math.log(2)/2),
            'rayleigh_range_mm':zr,
            'diameter_at_0p1mm_defocus_um':d*1000*math.sqrt(1+(0.1/zr)**2)}

def gaussian_mtf(nu_lp_mm: float, diameter_um: float, integration_pitch_um: float = 0) -> float:
    if nu_lp_mm < 0 or diameter_um <= 0 or integration_pitch_um < 0: raise ValueError('invalid MTF input')
    sigma = diameter_um/4000
    opt = math.exp(-2*math.pi**2*sigma**2*nu_lp_mm**2)
    q = math.pi*nu_lp_mm*integration_pitch_um/1000
    return opt*(abs(math.sin(q)/q) if q else 1.0)

def reflect(direction, normal):
    d = math.sqrt(sum(t*t for t in direction)); n=math.sqrt(sum(t*t for t in normal))
    if d == 0 or n == 0: raise ValueError('zero vector')
    u=[t/d for t in direction]; v=[t/n for t in normal]
    dot=sum(a*b for a,b in zip(u,v))
    return tuple(a-2*dot*b for a,b in zip(u,v))

def polygon_ray(p: dict[str, Any], alpha: float) -> dict[str,float]:
    """Chief ray from -X to an actual hexagon edge, rotating about +Y.
    Regular-hexagon geometry is inherited nominal geometry, not a vendor model.
    Positive alpha produces positive scan angle with the convention below.
    """
    if p['facet_count'] != 6: raise ValueError('finite polygon geometry currently validates six facets only')
    R = p['polygon_radius_mm']; h=p['polygon_hit_z_mm']
    c = R*math.cos(math.pi/6)/math.sqrt(2)
    cx,cz = c,h+c
    vertices=[]
    for i in range(6):
        a=math.radians(-165+60*i)+alpha
        vertices.append((cx+R*math.cos(a),cz+R*math.sin(a)))
    hits=[]
    for i in range(6):
        a,b=vertices[i],vertices[(i+1)%6]
        if abs(b[1]-a[1]) < 1e-12: continue
        t=(h-a[1])/(b[1]-a[1])
        if -1e-10 <= t <= 1+1e-10:
            x=a[0]+t*(b[0]-a[0]); nx=b[1]-a[1]; nz=-(b[0]-a[0])
            hits.append((x,a,b,nx,nz))
    if not hits: raise ValueError('beam misses polygon')
    x,a,b,nx,nz=min(hits,key=lambda r:r[0])
    dx,_,dz=reflect((1,0,0),(nx,0,nz))
    if dz >= 0: raise ValueError('selected facet is not directed toward lens')
    theta=math.atan2(dx,-dz)
    plane=p['lens_reference_z_mm']
    xp=x+dx*(plane-h)/dz
    edge_margin=min(math.hypot(x-a[0],h-a[1]),math.hypot(x-b[0],h-b[1]))
    cosi=abs(nx)/math.hypot(nx,nz)
    half_footprint=p['beam_diameter_mm']/(2*cosi)
    return {'alpha_deg':math.degrees(alpha),'theta_deg':math.degrees(theta),
        'hit_x_mm':x,'hit_z_mm':h,'ray_dx':dx,'ray_dz':dz,
        'lens_reference_x_mm':xp,'ideal_f_theta_x_mm':p['efl_mm']*theta,
        'edge_distance_mm':edge_margin,'beam_half_footprint_1e2_mm':half_footprint,
        'edge_margin_1e2_mm':edge_margin-half_footprint}

def write_csv(path: Path, rows: list[dict]):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def run(output: Path | None = None) -> dict:
    p=load_parameters(); out=output or ROOT/'results';out.mkdir(parents=True,exist_ok=True)
    modes=[budget(p,rpm,px,py) for rpm,px,py in [(300,50,50),(600,50,50),(1200,50,50),(3000,50,50),(3000,25,25),(3000,100,100)]]
    write_csv(out/'scan_modes.csv',modes)
    rays=[]
    for i in range(101):
        target=-p['scan_span_mm']/2+i*p['scan_span_mm']/100
        # Geometry orientation is chosen so alpha is the beam mechanical half-angle.
        row=polygon_ray(p,target/(2*p['efl_mm']))
        row['field_request_mm']=target;rays.append(row)
    write_csv(out/'polygon_chief_rays.csv',rays)
    sensitivity=[]
    for radius in (20,22,24,26,30):
        for beam in (4,5,6):
            q=dict(p,polygon_radius_mm=radius,beam_diameter_mm=beam)
            rr=[polygon_ray(q,(-p['scan_span_mm']/2+p['scan_span_mm']*i/100)/(2*q['efl_mm'])) for i in range(101)]
            scale99=math.sqrt(math.log(100)/2)
            sensitivity.append({'polygon_radius_mm':radius,'beam_diameter_1e2_mm':beam,
                'min_edge_margin_1e2_mm':min(r['edge_margin_1e2_mm'] for r in rr),
                'min_edge_margin_99pct_radial_contour_mm':min(r['edge_distance_mm']-scale99*r['beam_half_footprint_1e2_mm'] for r in rr),
                'ideal_spot_1e2_um':gaussian_budget(q)['ideal_diameter_1e2_um']})
    write_csv(out/'polygon_aperture_sensitivity.csv',sensitivity)
    g=gaussian_budget(p)
    mtf=[{'spatial_frequency_lp_mm':i/4,'ideal_gaussian_mtf':gaussian_mtf(i/4,g['ideal_diameter_1e2_um']),
          'ideal_with_50um_box_mtf':gaussian_mtf(i/4,g['ideal_diameter_1e2_um'],50)} for i in range(81)]
    write_csv(out/'ideal_mtf_budget_NOT_LENS_PERFORMANCE.csv',mtf)
    report={'model_status':'IDEAL_ANALYTICAL_PLUS_NOMINAL_POLYGON_GEOMETRY',
            'baseline':budget(p),'gaussian_ideal':g,'warnings':[
              'No actual lens prescription: no full-field spot, aberration, MTF or telecentricity verification.',
              'EFL is not working distance; lens_reference_z is only a CAD plane.',
              'Fixed angle-to-position map ignores performance changes due to beam walk.',
              'Minimum motor speed, laser working point, power, and facet optical efficiency require supplier/bench evidence.',
              'Reference source geometry retained; mount drawings are not manufacturing release.'],
            'finite_polygon':{'min_edge_margin_1e2_mm':min(r['edge_margin_1e2_mm'] for r in rays),
               'max_chief_ray_walk_mm':max(abs(r['hit_x_mm']) for r in rays)},
            'real_lens_raytrace':'NOT_RUN_NO_PRESCRIPTION','bench_tests':'NOT_RUN'}
    (out/'calculation_summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    return report
if __name__=='__main__':
    print(json.dumps(run(),ensure_ascii=False,indent=2))
