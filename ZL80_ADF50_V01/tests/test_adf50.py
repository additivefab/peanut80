from pathlib import Path
import sys,json,unittest,math
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'engineering'),str(R/'control')]
from calculate import calculate
from batch_reference import Batch,State,HandoffEvidence
P=json.loads((R/'engineering/parameters.json').read_text());C=calculate(P)
def ev(**changes):
 d={k:True for k in HandoffEvidence.__dataclass_fields__};d.update(changes);return HandoffEvidence(**d)
def park(b):
 b.request();b.neutralized();b.lead_arrived();b.qualify(True,True,True,True);b.park()
class Calculations(unittest.TestCase):
 def test_mass(self):self.assertAlmostEqual(C['single_mass_g_assumed'],6.72)
 def test_thickness(self):self.assertEqual(C['stack_thickness_range_mm'],[7.5,17.5])
 def test_gravity_stack_not_sheet(self):self.assertAlmostEqual(C['stack_down_slope_n']/C['single_down_slope_n'],50)
 def test_constant_spring_not_constant_total(self):self.assertGreater(C['follower_added_force_last_sheet_n'],C['follower_added_force_full_stack_n'])
 def test_thick_stack_needs_different_recipe(self):self.assertLess(C['thick_stack_follower_headroom_n'],0)
 def test_torque_units(self):self.assertEqual(C['retard_torque_example_mNm'],4.5)
 def test_friction_window(self):self.assertLess(C['retard_lower_bound_example_n'],.45);self.assertLess(.45,C['retard_upper_bound_example_n'])
 def test_static_closes_window(self):
  p=dict(P);p['residual_adhesion_example_n']=.55;self.assertLess(calculate(p)['retard_window_width_example_n'],0)
 def test_whole_sheet_buffer(self):self.assertGreater(C['qualified_path_margin_mm'],0);self.assertEqual(C['stop_budget_mm'],29.5)
 def test_not_tiny_buffer(self):self.assertGreater(C['qualified_path_required_mm'],300)
 def test_slow_scan_time(self):self.assertGreater(C['time_examples'][-1]['serial_batch_budget_min'],200)
 def test_batch_reliability(self):self.assertGreater(C['independent_per_sheet_success_required'],.9997)
class Controls(unittest.TestCase):
 def test_no_scan_before_full_length(self):
  b=Batch();b.request();b.neutralized();b.lead_arrived();b.qualify(False,True,True,True);self.assertEqual(b.state,State.QUALIFY);self.assertFalse(b.scan_permission(True))
 def test_no_scan_after_detected_double(self):
  b=Batch();b.request();b.neutralized();b.lead_arrived();b.qualify(True,False,True,True);self.assertEqual(b.state,State.HOLD);self.assertEqual(b.completed,0)
 def test_retard_release_required(self):
  b=Batch();park(b);b.handoff(ev(retard_released=False));self.assertEqual(b.state,State.HOLD)
 def test_input_drive_required(self):
  b=Batch();park(b);b.handoff(ev(input_scan_nip_engaged=False));self.assertFalse(b.scan_permission(True))
 def test_air_off_required(self):
  b=Batch();park(b);b.handoff(ev(air_off=False));self.assertEqual(b.state,State.HOLD)
 def test_hardware_gate(self):
  b=Batch();park(b);b.handoff(ev());self.assertTrue(b.scan_permission(True));self.assertFalse(b.scan_permission(False))
 def test_no_count_after_file_only(self):
  b=Batch();park(b);b.handoff(ev());b.scan_end(True,True);self.assertEqual(b.completed,0)
 def test_no_count_after_delivery_failure(self):
  b=Batch();park(b);b.handoff(ev());b.scan_end(True,True);b.receive(True,False);self.assertEqual(b.completed,0)
 def test_no_good_raw_from_fault(self):
  b=Batch();park(b);b.handoff(ev());b.scan_end(False,True);self.assertEqual(b.state,State.HOLD)
 def test_retry_same_candidate(self):
  b=Batch();b.request();j=b.job_id;b.neutralized();b.retry_before_scan(True,True);self.assertEqual(b.job_id,j);self.assertEqual(b.completed,0)
 def test_retry_limit(self):
  b=Batch();b.request()
  for _ in range(3):b.neutralized();b.retry_before_scan(True,True)
  self.assertEqual(b.state,State.HOLD)
 def test_unknown_double_bundle_not_counted(self):
  b=Batch();b.request();b.neutralized();b.retry_before_scan(True,False);self.assertEqual(b.completed,0);self.assertEqual(b.state,State.HOLD)
 def test_no_reverse_in_scan(self):
  b=Batch();park(b);b.handoff(ev())
  with self.assertRaises(RuntimeError):b.retry_before_scan(True,True)
 def test_50_jobs(self):
  b=Batch()
  for i in range(50):park(b);b.handoff(ev());b.scan_end(True,True);b.receive(True,True,stock_empty=(i==49))
  self.assertEqual(b.state,State.DONE);self.assertEqual(b.completed,50);self.assertEqual(len({r['job_id'] for r in b.records}),50)
 def test_remaining_stock_blocks_complete(self):
  b=Batch(1);park(b);b.handoff(ev());b.scan_end(True,True);b.receive(True,True,False);self.assertEqual(b.state,State.HOLD)
 def test_early_empty(self):
  b=Batch();b.request(stock=False);self.assertEqual(b.state,State.HOLD)
 def test_emergency_disables(self):
  b=Batch();park(b);b.handoff(ev());b.emergency();self.assertFalse(b.scan_permission(True))
if __name__=='__main__':unittest.main()
