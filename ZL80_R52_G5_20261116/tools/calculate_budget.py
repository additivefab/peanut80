from pathlib import Path
import json,csv,math
R=Path(__file__).resolve().parents[1];c=json.loads((R/'config/design.json').read_text())
n=c['facet_count'];rpm=c['nominal_rpm'];f=c['efl_mm'];vx=4*math.pi*f*rpm/60
vline=n*rpm/60;px=c['pixel_x_um']/1000;py=c['pixel_y_um']/1000
b={'scope':'IDEAL_GEOMETRY_AND_DIGITAL_BUDGET_NOT_PERFORMANCE',
 'line_frequency_hz':vline,'scan_speed_mm_s':vx,'sync_window_us':c['sync_span_mm']/vx*1e6,
 'image_window_us':c['film_width_mm']/vx*1e6,'pixel_dwell_us':px/vx*1e6,
 'instantaneous_pixel_rate_hz':vx/px,'feed_mm_s':py*vline,
 'adc_pipeline_ns':c['adc_pipeline_sample_cycles']/c['adc_sample_hz']*1e9,
 'adc_pipeline_logic_ticks':c['adc_pipeline_sample_cycles']*c['logic_clock_hz']/c['adc_sample_hz'],
 'raw_adc_bytes_s':c['adc_sample_hz']*4,'tagged_sample_bytes_s':c['adc_sample_hz']*16,
 'axis_peak_bytes_s':c['logic_clock_hz']*8,
 'single_channel_image_bytes_s':round(c['film_width_mm']/px*vline*2),
 'sample_fifo_full_stall_us':c['sample_fifo_depth']/c['adc_sample_hz']*1e6,
 'nominal_5ms_tagged_burst_bytes':round(.005*c['adc_sample_hz']*16),
 'encoder_quantization_um':math.pi*c['roller_diameter_mm']/(c['encoder_ppr']*c['quadrature'])*1000,
 'event_one_tick_x_um':vx/c['logic_clock_hz']*1000,
 'event_3_ticks_x_um':vx/c['logic_clock_hz']*3000,
 'warning':'10ns clock quantization is not total synchronization accuracy; amplifier/comparator timewalk and phase remain'}
(R/'validation/results/budget.json').write_text(json.dumps(b,indent=2))
with (R/'interfaces/timing_bandwidth_budget.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.writer(f);w.writerow(['parameter','value']);w.writerows(b.items())
print(json.dumps(b,indent=2))
