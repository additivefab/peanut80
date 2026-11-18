import csv,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];EL=ROOT/'ecr_g3_01'/'electrical'
C=json.loads((EL/'ECR_G3_01_E_计算.json').read_text())
def rows(n):return list(csv.DictReader(open(EL/n,encoding='utf-8-sig')))
class T(unittest.TestCase):
    def test_b05_layout_clean(self):
        b=C['b05_layout'];self.assertEqual(b['overlaps'],[]);self.assertEqual(b['edge'],[]);self.assertEqual(b['holes'],[]);self.assertGreaterEqual(b['min_gap_mm'],1.0)
    def test_no_interference_three_heights(self):
        self.assertEqual(set(C['interference']),{'dz_+0','dz_+5','dz_-1'})
        for k,v in C['interference'].items():self.assertEqual(v['overlaps'],[],k)
    def test_bend_radius_fits(self):
        for f in C['w13']['fillet']:self.assertTrue(f['ok']);self.assertGreaterEqual(f['r_max_mm'],C['w13']['min_bend_mm'])
        for v in C['ffc']['by_height'].values():self.assertGreaterEqual(v['radius_mm'],8)
    def test_harness_separation(self):
        g=C['w13']['gap_to_other_harness_mm'];self.assertGreaterEqual(g['W09'],10);self.assertGreaterEqual(g['W05'],10);self.assertGreaterEqual(g['W12'],5)
    def test_timing_margin(self):
        for v in C['timing'].values():self.assertLess(v['filter_over_state_pct'],1.0);self.assertGreater(v['fpga_clocks_per_state'],1000)
    def test_ffc_force_small(self):
        self.assertLess(C['ffc']['force_at_0p35mm_pct_of_preload'],1.0)
    def test_j3_has_all_three_encoder_groups(self):
        n=[r['新网名'] for r in rows('ECR_G3_01_E_B05_J3引脚.csv')];self.assertEqual(len(n),20)
        for s in ('ENC_M_A','ENC_D_A','ENC_E_A','ENC_E_B','ENC_E_OPEN'):self.assertIn(s,n)
    def test_signal_table_five_wires_and_open_items(self):
        self.assertEqual(len(rows('ECR_G3_01_E_信号表.csv')),6)
        self.assertTrue(any('P0' in r['优先级'] for r in rows('ECR_G3_01_E_G5接口变更.csv')))
    def test_step_files(self):
        for k in ('G3E-05','G3E-06','G3E-07','G3E-08','ECR_G3_01_E_link'):self.assertTrue((EL/'step'/f'{k}.step').exists(),k)
if __name__=='__main__':unittest.main()
