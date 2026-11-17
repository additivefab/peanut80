import json,sys,unittest,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'engineering'));import calculate as C
P=json.loads((ROOT/'engineering/parameters.json').read_text());R=C.calculate(P);G=C.geometry(P);E=R['envelope'];PA=R['path'];H=R['handoff']
class T(unittest.TestCase):
    def test_user_constraints(self):
        c=P['user_constraints_2026_11_16'];e=E['working_envelope_mm_WDH']
        self.assertLessEqual(e[1],c['depth_along_film_travel_mm']);self.assertLessEqual(e[2],c['height_max_mm'])
    def test_depth_margin_better_than_v04(self):
        self.assertGreater(E['depth_margin_to_constraint_mm'],15);self.assertEqual(P['magazine_angle_deg_from_horizontal'],78)
    def test_one_way_flow(self):
        self.assertTrue(PA['y_monotonic']);self.assertGreater(G['u_in'][1],0);self.assertLess(G['u_in'][0],0);self.assertGreater(G['u_out'][0],0)
    def test_bends(self):
        self.assertLess(PA['entry_bend_deg'],90);self.assertLess(PA['exit_bend_deg'],90);self.assertGreaterEqual(PA['bend_radius_mm'],80)
        for x in R['per_thickness']:self.assertLess(x['bend_strain_pct'],0.25)
    def test_seven_rollers_reduce_polygon_error(self):
        b=R['bend_support'];self.assertEqual(b['v06']['entry']['count'],7);self.assertEqual(b['v06']['entry']['roller_od_mm'],12)
        for k in ('entry','exit'):
            self.assertLess(b['v06'][k]['sagitta_mm'],0.6*b['v04'][k]['sagitta_mm']);self.assertGreater(b['v06'][k]['roller_surface_gap_mm'],1.0)
    def test_nothing_over_scanner_top(self):
        self.assertEqual(E['magazine_overhang_over_scanner_mm'],0);self.assertGreater(E['lid_to_front_panel_clearance_mm'],30)
    def test_front_gap_carries_flange_rear_gap_small(self):
        self.assertGreaterEqual(P['bend_gap_from_panel_mm']-P['cartridge']['flange_thickness_mm'],2);self.assertEqual(P['rear_bend_gap_mm'],2)
    def test_pick_force_independent_of_stack(self):
        for x in R['per_thickness']:self.assertEqual(x['pick_interface_force_full_stack_n'],x['pick_interface_force_last_sheet_n'])
    def test_dam_and_second_sheet(self):
        for x in R['per_thickness']:
            self.assertGreater(x['top_sheet_margin_worst_level'],1.4);self.assertLess(x['self_feed_by_weight_ratio'],0.35)
            self.assertGreater(x['second_sheet_adhesion_allowed_n'],2*P['residual_adhesion_example_n']);self.assertGreater(x['retard_window_width_n'],0.2)
    def test_dam_lift_factor_self_lock(self):
        self.assertLess(C.dam_lift_factor(80,0.3),0);self.assertGreater(C.dam_lift_factor(38,0.3),C.dam_lift_factor(62,0.3))
    def test_plate_stroke_22(self):
        self.assertAlmostEqual(PA['plate_travel_mm'],22.0);lo,hi=PA['lift_arm_angle_range_deg']
        self.assertAlmostEqual(P['lift_arm_length_mm']*(math.sin(math.radians(hi))-math.sin(math.radians(lo))),22.0,places=6);self.assertLess(hi,75)
    def test_bend_drag_small_with_idlers(self):
        for x in R['per_thickness']:self.assertLess(x['bend_drag_idler_n'],0.03);self.assertLess(max(abs(v) for v in x['scan_axial_force_range_n']),0.15)
    def test_exit_overlap_is_path_based(self):
        self.assertAlmostEqual(H['exit_nip_s_mm'],152+G['exit_arc_mm']+P['eject_nip_after_bend_mm'])
        self.assertAlmostEqual(H['overlap_mm_L300'],300-(H['exit_nip_s_mm']-42));self.assertGreater(abs(H['overlap_mm_L300']-H['v04_claimed_overlap_mm']),15)
        self.assertGreater(H['grip_depth_at_follow_trigger_mm'],30);self.assertEqual(H['master_remaining_grip_at_trigger_mm'],30);self.assertGreater(H['min_length_overlap_mm'],20)
    def test_metrology_windows(self):
        self.assertEqual(H['g3_unchanged_window_mm'],[47,253]);self.assertEqual(H['g3_unchanged_window_length_mm'],206);self.assertEqual(H['with_exit_follower_window_mm'],[0,300])
        self.assertTrue(H['entry_rollers_still_gripping_at_hold_release']);self.assertGreater(H['entry_nip_leaves_sheet_when_head_mm'],H['entry_hold_until_head_mm'])
    def test_g3_drive_not_changed(self):
        g=P['scanner_g3'];self.assertIn('NOT changed',g['drive']);self.assertEqual(g['metrology_nips_s_mm'],{'entry_follower':-42,'exit_drive':42});self.assertEqual(g['foot_bottom_z_mm'],-8)
    def test_stop_distance(self):
        self.assertAlmostEqual(H['stop_distance_mm'],11.75)
    def test_double_check_coverage(self):
        self.assertGreater(PA['fraction_checked_before_scan'],0.75);self.assertAlmostEqual(PA['unchecked_tail_mm']+PA['sensor_to_park_mm'],P['film_length_mm'])
    def test_slide_back_requires_gate(self):
        for x in R['per_thickness']:self.assertGreater(x['slide_back_force_in_bin_n'],10*x['slide_back_wall_friction_n'])
    def test_batch_time_modes_and_labels(self):
        bt=R['batch_time'];self.assertEqual(len(bt),4);self.assertTrue(all(a['batch_hours']<b['batch_hours'] for a,b in zip(bt,bt[1:])))
        self.assertTrue(all('unverified' in x['status'] for x in bt))
    def test_only_v06_fits(self):
        self.assertEqual([o['fits_700x650'] for o in R['architecture_options']],[False,False,False,False,True])
    def test_results_file_current(self):
        self.assertEqual(json.loads((ROOT/'engineering/calculated_results.json').read_text())['envelope'],E)
    def test_control_reference_present(self):
        self.assertTrue((ROOT/'control/adf_controller.py').exists())
if __name__=='__main__':unittest.main()
