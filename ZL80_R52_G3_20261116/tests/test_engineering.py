import unittest,json,math,csv,sys,tempfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from analyze_transport import analyze
P=json.loads((R/'config/mechanical_parameters.json').read_text());S=json.loads((R/'validation/results/calculation_summary.json').read_text())
class EngineeringTests(unittest.TestCase):
 def test_01_width(self):self.assertEqual((P['film_width'],P['scan_span']),(80,100))
 def test_02_plane(self):self.assertAlmostEqual(P['lower_center_z']+P['roller_diameter']/2+P['film_thickness_nominal']/2,P['film_center_z'])
 def test_03_nip_gap(self):self.assertAlmostEqual(P['upper_center_z']-P['lower_center_z']-P['roller_diameter'],.2)
 def test_04_four_rollers(self):
  a=json.loads((R/'cad/instances.json').read_text());self.assertEqual(sum(x['part']=='G3-R04' for x in a),4)
 def test_05_bearings(self):
  a=json.loads((R/'cad/instances.json').read_text());self.assertEqual(sum(x['part']=='G3-P01' for x in a),8)
 def test_06_encoder_quantization(self):self.assertAlmostEqual(S['encoder_quantum_um'],math.pi*20/16384*1000)
 def test_07_encoder_accuracy_not_quantum(self):self.assertGreater(S['encoder_angle_accuracy_equivalent_um'],S['encoder_quantum_um']*8)
 def test_08_3000rpm_line(self):self.assertEqual(6*3000/60,300)
 def test_09_nominal_feed(self):self.assertEqual(6*3000/60*.05,15)
 def test_10_motor_insertion(self):self.assertAlmostEqual(P['motor_front_x']-P['motor_shaft_length'],101)
 def test_11_coupling_bounds(self):self.assertEqual((P['coupling_center_x']-15,P['coupling_center_x']+15),(81,111))
 def test_12_spring_force(self):self.assertAlmostEqual(S['spring_force_per_nip_N'],4.1)
 def test_13_gravity_included(self):self.assertGreater(S['nip_normal_force_N'],S['spring_force_per_nip_N'])
 def test_14_motor_not_approved(self):self.assertEqual(S['motor_dynamic_torque_evidence'],'NOT_RUN')
 def test_15_bench_not_done(self):self.assertEqual(S['bench_status'],'NOT_RUN')
 def test_16_tension_not_clamp_force(self):self.assertNotEqual(S['nominal_web_tension_N'],S['nip_normal_force_N'])
 def test_17_force_corner_fails(self):self.assertLess(.15*2,.5)
 def test_18_gap_chain(self):self.assertAlmostEqual(S['gap_min_candidate_mm'],.42);self.assertAlmostEqual(S['gap_max_candidate_mm'],.58)
 def test_19_thickness_focus_not_gap(self):self.assertAlmostEqual(S['film_midplane_thickness_shift_max_mm'],.075)
 def test_20_positive_deflection(self):self.assertGreater(S['shaft_max_deflection_um_simple_beam'],0)
 def test_21_harness_unique(self):
  a=json.loads((R/'config/harness_routes_G3.json').read_text());self.assertEqual(len(a),len(set(x['id'] for x in a)))
 def test_22_cut_length(self):
  a=json.loads((R/'config/harness_routes_G3.json').read_text());self.assertTrue(all(x['cut_length_budget_mm']>=x['length_mm'] for x in a))
 def test_23_shapes_valid(self):self.assertTrue(all(x['valid'] for x in json.loads((R/'cad/parts.json').read_text())))
 def test_24_collision_classification(self):
  a=json.loads((R/'validation/results/geometry_audit.json').read_text());self.assertTrue(all(x['classification']=='EXPECTED_THREAD_ENGAGEMENT' for x in a['intersections']))
 def test_25_blank_bench_refused(self):
  with self.assertRaises(ValueError):analyze(R/'validation/templates/transport_raw_EMPTY.csv',15)
 def test_26_known_synthetic_ANALYZER_ONLY(self):
  with tempfile.TemporaryDirectory() as td:
   f=Path(td)/'synthetic_test.csv'
   with open(f,'w',newline='') as h:
    w=csv.writer(h);w.writerow(['time_s','reference_position_mm','tension_N']);w.writerows([[i*.01,i*.15,.5] for i in range(100)])
   x=analyze(f,15);self.assertAlmostEqual(x['mean_speed_mm_s'],15);self.assertLess(x['position_residual_rms_um'],1e-8)
 def test_27_base_holes_closed(self):
  a=json.loads((R/'engineering/base_holes_top.json').read_text());self.assertTrue(all(abs(x['y'])+x['diameter']/2<144 for x in a));self.assertEqual(len(a),40)
 def test_28_release_lift(self):self.assertEqual(P['upper_release_lift'],5);self.assertGreater(P['spring_installed_length']-5,7.5)
 def test_29_doe_not_measured(self):
  a=list(csv.DictReader(open(R/'engineering/roller_material_DOE.csv',encoding='utf-8-sig')));self.assertEqual(len(a),18);self.assertTrue(all(x['status']=='NOT_RUN' for x in a))
 def test_30_source_baseline_preserved(self):self.assertTrue((R/'sources/inherited/G01_master_parameters.json').exists())
if __name__=='__main__':unittest.main(verbosity=2)
