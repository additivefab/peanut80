import json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'ecr_g3_01'
I=json.loads((E/'interference.json').read_text());C=json.loads((E/'ECR_G3_01_计算.json').read_text());P=json.loads((ROOT/'engineering/parameters.json').read_text())
class T(unittest.TestCase):
    def test_no_interference_at_three_roller_heights(self):
        self.assertEqual(set(I['interference']),{'dz_+0','dz_+5','dz_-1'})
        for k,v in I['interference'].items():self.assertEqual(v['overlaps'],[],k)
    def test_only_two_g3_screws_replaced_and_no_g3_part_cut(self):
        self.assertEqual(I['replaced_g3_screws'],['CAP_SCREW_72_42_120.1_-7_7','CAP_SCREW_72_42_120.1_7_7'])
    def test_clearances_to_coupler_guard(self):
        self.assertGreaterEqual(I['board_over_guard_clearance_mm'],2.0);self.assertGreaterEqual(I['carrier_over_guard_clearance_mm'],2.0)
    def test_added_mass_small(self):
        self.assertLess(I['moving_mass_added_g'],6);self.assertLess(C['preload']['preload_change_pct'],1.0);self.assertLess(C['preload']['added_pct'],3.0)
    def test_step_files(self):
        for k in ('G3E-01','G3E-02','G3E-03','G3E-04','ECR_G3_01_exit_follower_encoder'):self.assertTrue((E/'step'/f'{k}.step').exists(),k)
    def test_coverage_is_continuous_and_overlap_is_L_minus_94(self):
        for c in C['coverage']:
            L=c['length_mm'];self.assertEqual(c['union_mm'],[0,L]);self.assertEqual(c['gap_mm'],0);self.assertEqual(c['cross_check_overlap_mm'],L-94)
        self.assertEqual([c['g3_unchanged_window_mm'] for c in C['coverage'] if c['length_mm']==300][0],[47,253])
    def test_resolution_same_as_g3_encoders(self):
        self.assertAlmostEqual(C['resolution']['step_um'],3.835,places=3);self.assertLess(C['resolution']['step_over_pixel_pct'],10)
    def test_parameters_record_the_approval(self):
        self.assertIn('APPROVED',P['metrology']['ecr_g3_01_status']);self.assertIn('NOT_RUN',P['metrology']['ecr_g3_01_status'])
if __name__=='__main__':unittest.main()
