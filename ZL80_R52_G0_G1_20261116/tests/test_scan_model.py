import unittest,math,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import scan_model as m
class ScanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.p=m.load_parameters();cls.b=m.budget(cls.p)
    def test_line_rate(self):self.assertAlmostEqual(self.b['line_hz'],300)
    def test_period(self):self.assertAlmostEqual(self.b['line_period_ms'],10/3)
    def test_scan_velocity(self):self.assertAlmostEqual(self.b['x_velocity_mm_s'],20000*math.pi)
    def test_roi_duration(self):self.assertAlmostEqual(self.b['roi_time_ms'],4/math.pi)
    def test_scan_duration(self):self.assertAlmostEqual(self.b['scan_time_ms'],5/math.pi)
    def test_sync_duration(self):self.assertAlmostEqual(self.b['sync_time_ms'],4.6/math.pi)
    def test_dwell(self):self.assertAlmostEqual(self.b['pixel_dwell_us'],2.5/math.pi)
    def test_average_not_instant(self):self.assertGreater(self.b['instant_pixel_MHz'],self.b['average_pixel_MHz'])
    def test_rate_duty_relation(self):self.assertAlmostEqual(self.b['instant_pixel_MHz']*self.b['roi_duty'],self.b['average_pixel_MHz'])
    def test_feed(self):self.assertAlmostEqual(self.b['feed_mm_s'],15)
    def test_motion_within_line(self):self.assertAlmostEqual(self.b['feed_during_roi_um'],60/math.pi)
    def test_adc_samples(self):self.assertAlmostEqual(self.b['adc_samples_per_pixel'],50/math.pi)
    def test_raw_rate(self):self.assertAlmostEqual(self.b['raw_MB_s'],80)
    def test_image_rate(self):self.assertAlmostEqual(self.b['image_MB_s'],.96)
    def test_slow_rpm_dwell(self):self.assertAlmostEqual(m.budget(self.p,300)['pixel_dwell_us'],self.b['pixel_dwell_us']*10)
    def test_duty_independent_of_rpm(self):self.assertAlmostEqual(m.budget(self.p,300)['roi_duty'],self.b['roi_duty'])
    def test_negative_input(self):
        with self.assertRaises(ValueError):m.budget(self.p,-1)
    def test_illegal_spans(self):
        with self.assertRaises(ValueError):m.validate(dict(self.p,sync_span_mm=79))
    def test_excess_sweep(self):
        with self.assertRaises(ValueError):m.validate(dict(self.p,efl_mm=10))
    def test_m2(self):
        with self.assertRaises(ValueError):m.validate(dict(self.p,beam_m2=.9))
    def test_zero_normal(self):
        with self.assertRaises(ValueError):m.reflect((1,0,0),(0,0,0))
    def test_reflection(self):
        out=m.reflect((1,0,0),(1,0,1));self.assertAlmostEqual(out[0],0);self.assertAlmostEqual(out[2],-1)
    def test_norm_preserved(self):
        out=m.reflect((1,2,3),(2,1,4));self.assertAlmostEqual(sum(x*x for x in out),1)
    def test_mirror_half_angle(self):
        for i in range(-25,26):
            a=i*.01;r=m.polygon_ray(self.p,a);self.assertAlmostEqual(r['theta_deg'],math.degrees(2*a),places=9)
    def test_polygon_center(self):
        r=m.polygon_ray(self.p,0);self.assertAlmostEqual(r['hit_x_mm'],0,places=9)
    def test_edge_clipping_is_exposed(self):
        self.assertLess(m.polygon_ray(self.p,.25)['edge_margin_1e2_mm'],0)
    def test_radius_sensitivity(self):
        self.assertGreater(m.polygon_ray(dict(self.p,polygon_radius_mm=26),.25)['edge_margin_1e2_mm'],0)
    def test_beam_walk(self):self.assertGreater(abs(m.polygon_ray(self.p,.25)['hit_x_mm']),1)
    def test_mtf_dc(self):self.assertEqual(m.gaussian_mtf(0,35,50),1)
    def test_mtf_monotonic_gaussian(self):self.assertGreater(m.gaussian_mtf(5,35),m.gaussian_mtf(10,35))
    def test_gaussian_size(self):self.assertAlmostEqual(m.gaussian_budget(self.p)['ideal_diameter_1e2_um'],21.0211848836,places=7)
    def test_default_disabled(self):
        d=json.loads((m.ROOT/'config/master_parameters.json').read_text());self.assertIs(d['laser_enable_default'],False)
if __name__=='__main__':unittest.main()
