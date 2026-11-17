import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'engineering'));import calculate as C
P=json.loads((ROOT/'engineering/parameters.json').read_text());R=C.calculate(P);S=R['path']['stations_y_mm']
class T(unittest.TestCase):
    def test_no_bend(self):
        self.assertEqual(R['path']['bends'],0);self.assertEqual(R['architecture_options'][-1]['guided_bend_deg'],0)
    def test_stations_monotonic(self):
        v=list(S.values());self.assertEqual(v,sorted(v))
    def test_separator_inside_scanner_dam_outside(self):
        self.assertLess(S['dam_top_y'],S['front_panel_y']);self.assertGreater(S['feed_nip_y'],S['front_panel_y'])
        self.assertLess(S['eject_nip_y'],S['rear_panel_y'])
    def test_rollers_fit_between_panel_and_sensor(self):
        r=P['feed_roller_od_mm']/2
        self.assertGreaterEqual(S['feed_nip_y']-r,S['front_panel_y']+2)
        self.assertGreaterEqual(S['double_sheet_sensor_y']-P['double_sheet_sensor_diameter_mm']/2,S['feed_nip_y']+r+2)
    def test_pick_force_independent_of_stack(self):
        for x in R['per_thickness']:self.assertAlmostEqual(x['pick_interface_force_full_stack_n'],x['pick_interface_force_last_sheet_n'])
    def test_top_sheet_climbs_dam_even_at_level_error(self):
        for x in R['per_thickness']:self.assertGreater(x['top_sheet_margin_worst_level'],1.4)
    def test_second_sheet_margin(self):
        for x in R['per_thickness']:self.assertGreater(x['second_sheet_adhesion_allowed_n'],2*P['residual_adhesion_example_n'])
    def test_retard_window_positive(self):
        for x in R['per_thickness']:self.assertGreater(x['retard_window_width_n'],0.2)
    def test_dam_lift_factor_self_lock(self):
        self.assertLess(C.dam_lift_factor(80,0.3),0);self.assertGreater(C.dam_lift_factor(35,0.3),C.dam_lift_factor(60,0.3))
    def test_tail_drag_small(self):
        for x in R['per_thickness']:self.assertLess(x['tail_drag_on_stack_max_n'],0.05)
    def test_lift_travel_covers_thickest_stack(self):
        self.assertGreaterEqual(R['path']['lift_travel_mm'],50*0.35)
    def test_envelope(self):
        e=R['envelope']['working_envelope_mm_WDH'];self.assertEqual(e[2],300);self.assertLess(e[1],1000)
        self.assertLess(R['envelope']['volume_m3'],min(o['volume_m3'] for o in R['architecture_options'][:3]))
    def test_precheck_geometry(self):
        self.assertAlmostEqual(R['path']['precheck_lead_max_y_mm']-P['film_length_mm'],S['double_sheet_sensor_y']+P['precheck_overrun_mm'])
    def test_batch_time_modes(self):
        bt=R['batch_time'];self.assertEqual(len(bt),4);self.assertTrue(all(a['batch_hours']<b['batch_hours'] for a,b in zip(bt,bt[1:])))
    def test_results_file_current(self):
        saved=json.loads((ROOT/'engineering/calculated_results.json').read_text());self.assertEqual(saved['envelope'],R['envelope'])
    def test_envelope_interference_zero(self):
        self.assertEqual(json.loads((ROOT/'tests/envelope_interference.json').read_text())['overlaps'],[])
    def test_control_reference_copied(self):
        self.assertTrue((ROOT/'control/batch_reference.py').exists() and (ROOT/'control/state_transition_table.csv').exists())
if __name__=='__main__':unittest.main()
