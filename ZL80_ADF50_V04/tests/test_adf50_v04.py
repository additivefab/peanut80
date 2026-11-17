import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'engineering'));import calculate as C
P=json.loads((ROOT/'engineering/parameters.json').read_text());R=C.calculate(P);G=C.geometry(P);E=R['envelope'];PA=R['path']
class T(unittest.TestCase):
    def test_user_constraints(self):
        c=P['user_constraints_2026_11_16'];e=E['working_envelope_mm_WDH']
        self.assertLessEqual(e[1],c['depth_along_film_travel_mm']);self.assertLessEqual(e[2],c['height_max_mm'])
    def test_one_way_flow(self):
        self.assertTrue(PA['y_monotonic'])
        self.assertGreater(G['u_in'][1],0);self.assertLess(G['u_in'][0],0)          # magazine rises away from the scanner
        self.assertGreater(G['u_out'][0],0)                                         # bin rises away from the scanner on the other side
    def test_bends_below_90_and_large_radius(self):
        self.assertLess(PA['entry_bend_deg'],90);self.assertLess(PA['exit_bend_deg'],90);self.assertGreaterEqual(PA['bend_radius_mm'],80)
        for x in R['per_thickness']:self.assertLess(x['bend_strain_pct'],0.25)
    def test_nothing_over_scanner_top(self):
        self.assertEqual(E['magazine_overhang_over_scanner_mm'],0);self.assertGreater(E['lid_to_front_panel_clearance_mm'],30)
        self.assertGreater(G['exit_bend_end'][0]-P['output_bin_front_cover_mm'],P['scanner_rear_panel_y_mm'])
    def test_pick_force_independent_of_stack(self):
        for x in R['per_thickness']:self.assertEqual(x['pick_interface_force_full_stack_n'],x['pick_interface_force_last_sheet_n'])
    def test_top_sheet_climbs_dam_even_at_level_error(self):
        for x in R['per_thickness']:self.assertGreater(x['top_sheet_margin_worst_level'],1.4)
    def test_no_self_feed_by_weight(self):
        for x in R['per_thickness']:self.assertLess(x['self_feed_by_weight_ratio'],0.35)
    def test_second_sheet_margin(self):
        for x in R['per_thickness']:self.assertGreater(x['second_sheet_adhesion_allowed_n'],2*P['residual_adhesion_example_n'])
    def test_retard_window_positive(self):
        for x in R['per_thickness']:self.assertGreater(x['retard_window_width_n'],0.2)
    def test_dam_lift_factor_self_lock(self):
        self.assertLess(C.dam_lift_factor(80,0.3),0);self.assertGreater(C.dam_lift_factor(38,0.3),C.dam_lift_factor(62,0.3))
    def test_bend_drag_small_with_idlers(self):
        for x in R['per_thickness']:
            self.assertLess(x['bend_drag_idler_n'],0.03);self.assertLess(max(abs(v) for v in x['scan_axial_force_range_n']),0.15)
    def test_geometry_consistent(self):
        import math
        bs,be=G['entry_bend_start'],G['entry_bend_end'];c=(be[0],be[1]+G['R'])
        self.assertAlmostEqual(math.hypot(bs[0]-c[0],bs[1]-c[1]),G['R']);self.assertAlmostEqual(be[1],P['scan_plane_z_mm'])
        xs,xe=G['exit_bend_start'],G['exit_bend_end'];c=(xs[0],xs[1]+G['R']);self.assertAlmostEqual(math.hypot(xe[0]-c[0],xe[1]-c[1]),G['R'])
    def test_double_check_coverage(self):
        self.assertGreater(PA['fraction_checked_before_scan'],0.75);self.assertAlmostEqual(PA['unchecked_tail_mm']+PA['sensor_to_park_mm'],P['film_length_mm'])
    def test_lead_reaches_eject_nip_before_tail_released(self):
        self.assertGreater(PA['lead_past_eject_nip_when_tail_isolated_mm'],50)
    def test_batch_time_modes(self):
        bt=R['batch_time'];self.assertEqual(len(bt),4);self.assertTrue(all(a['batch_hours']<b['batch_hours'] for a,b in zip(bt,bt[1:])))
    def test_only_v04_fits(self):
        self.assertEqual([o['fits_700x650'] for o in R['architecture_options']],[False,False,False,False,True])
    def test_results_file_current(self):
        saved=json.loads((ROOT/'engineering/calculated_results.json').read_text());self.assertEqual(saved['envelope'],E)
    def test_envelope_interference_zero_and_matches(self):
        j=json.loads((ROOT/'tests/envelope_interference.json').read_text());self.assertEqual(j['overlaps'],[])
        bb=j['overall_aabb_of_adf_solids'];self.assertAlmostEqual(bb[1],E['front_y_mm'],delta=0.2);self.assertAlmostEqual(bb[4],E['rear_y_mm'],delta=0.2)
    def test_control_reference_copied(self):
        self.assertTrue((ROOT/'control/batch_reference.py').exists() and (ROOT/'control/state_transition_table.csv').exists())
if __name__=='__main__':unittest.main()
