import json,sys,unittest,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'engineering'));import calculate as C
P=json.loads((ROOT/'engineering/parameters.json').read_text());R=C.calculate(P)
class T(unittest.TestCase):
    def test_pick_force_independent_of_stack(self):
        for x in R['per_thickness']:self.assertAlmostEqual(x['pick_interface_force_full_stack_n'],x['pick_interface_force_last_sheet_n'])
    def test_top_sheet_climbs_dam(self):
        for x in R['per_thickness']:self.assertGreater(x['top_sheet_margin_ratio'],1.4)
    def test_no_self_feed_by_weight(self):
        for x in R['per_thickness']:self.assertLess(x['self_feed_ratio'],0.25)
    def test_second_sheet_margin_exceeds_example_adhesion(self):
        for x in R['per_thickness']:self.assertGreater(x['second_sheet_adhesion_allowed_n'],2*P['residual_adhesion_example_n'])
    def test_retard_window_positive(self):
        for x in R['per_thickness']:self.assertGreater(x['retard_window_width_n'],0.2)
    def test_dam_lift_factor_self_lock(self):
        self.assertLess(C.dam_lift_factor(80,0.3),0);self.assertGreater(C.dam_lift_factor(45,0.3),C.dam_lift_factor(60,0.3))
    def test_qualified_path(self):
        self.assertGreaterEqual(R['path']['qualified_path_margin_mm'],20)
        self.assertAlmostEqual(R['path']['qualified_path_required_mm'],329.5)
    def test_path_geometry_consistent(self):
        ae=R['path']['arc_end_yz'];ds=R['path']['double_station_yz']
        self.assertAlmostEqual(math.hypot(ds[0]-ae[0],ds[1]-ae[1]),P['steep_run_to_double_station_mm'])
        self.assertAlmostEqual(R['path']['turn_angle_deg'],180-P['magazine_angle_deg_from_horizontal'])
    def test_clears_scanner_corner(self):
        self.assertGreater(R['path']['clearance_magazine_tray_to_scanner_top_front_corner_mm'],10)
    def test_envelope_smaller_footprint_than_v01(self):
        self.assertLess(R['envelope']['footprint_m2'],0.7*R['envelope']['v01_footprint_m2'])
    def test_bending_strain_not_worse_than_v01(self):
        self.assertLessEqual(max(R['path']['film_bending_strain']),0.35/(2*60)+1e-9)
    def test_batch_time_modes(self):
        bt=R['batch_time'];self.assertEqual(len(bt),4)
        self.assertTrue(all(a['batch_hours']<b['batch_hours'] for a,b in zip(bt,bt[1:])))
        self.assertTrue(all(x['batch_hours']<=x['batch_hours_if_whole_travel_at_scan_speed'] for x in bt))
    def test_results_file_current(self):
        saved=json.loads((ROOT/'engineering/calculated_results.json').read_text())
        self.assertAlmostEqual(saved['envelope']['footprint_m2'],R['envelope']['footprint_m2'])
    def test_envelope_interference_zero(self):
        f=ROOT/'tests/envelope_interference.json'
        if f.exists():self.assertEqual(json.loads(f.read_text())['overlaps'],[])
    def test_control_reference_copied(self):
        self.assertTrue((ROOT/'control/batch_reference.py').exists() and (ROOT/'control/state_transition_table.csv').exists())
if __name__=='__main__':unittest.main()
