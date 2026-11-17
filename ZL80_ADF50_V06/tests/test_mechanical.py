import json,csv,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'mechanical'
R=json.loads((M/'interference.json').read_text());P=json.loads((M/'parts.json').read_text());I=json.loads((M/'instances.json').read_text())
PR=json.loads((ROOT/'engineering/parameters.json').read_text());C=PR['user_constraints_2026_11_16']
class T(unittest.TestCase):
    def test_counts_consistent(self):
        self.assertEqual(R['part_numbers'],len(P));self.assertEqual(R['instances'],len(I))
        off={p['id'] for p in P if p['note'] and '不在装配体中' in p['note']};self.assertEqual(sum(p['qty'] for p in P if p['id'] not in off),len(I))
    def test_all_parts_valid_solids(self):
        self.assertTrue(all(p['valid'] and p['volume_mm3']>0 for p in P))
    def test_no_self_interference(self):
        self.assertEqual(R['self_overlaps'],[]);self.assertGreater(R['self_pairs_intersected'],100)
    def test_no_interference_with_g3_context_with_panel_cutouts(self):
        self.assertEqual(R['scanner_overlaps'],[]);self.assertIn('G3',R['scanner_context']);self.assertGreater(R['scanner_pairs_intersected'],0)
        self.assertTrue(any('184×112' in t for t in R['scanner_modifications_required']))
    def test_envelope_within_user_constraints(self):
        e=R['working_envelope_mm_WDH'];self.assertLessEqual(e[1],C['depth_along_film_travel_mm']);self.assertLessEqual(e[2],C['height_max_mm'])
        bb=R['overall_aabb'];self.assertLessEqual(bb[3]-bb[0],320)
    def test_feet_reach_the_g3_bench_plane(self):
        self.assertEqual(R['overall_aabb'][2],PR['scanner_g3']['foot_bottom_z_mm']);feet=[r for r in I if r['part']=='ST01'];self.assertEqual(len(feet),8)
        self.assertTrue(all(abs(r['aabb'][2]+8)<1e-6 for r in feet))
    def test_nothing_above_scanner_top_cover(self):
        for r in I:
            a=r['aabb']
            if a[5]>300:self.assertTrue(a[4]<-150 or a[1]>150,r['name'])
    def test_flange_outside_front_panel(self):
        f=[r for r in I if r['part']=='EN12'][0]['aabb'];self.assertLessEqual(f[4],-150+1e-6)
    def test_dam_blocks_and_gap_variants(self):
        self.assertEqual(sorted(p['id'] for p in P if p['id'].startswith('AF10')),['AF10A','AF10B','AF10C'])
        self.assertEqual(sorted(p['id'] for p in P if p['id'].startswith('AF31_')),['AF31_0.8','AF31_2','AF31_3'])
    def test_seven_idlers_per_bend(self):
        self.assertEqual(sum(1 for r in I if r['part']=='AF29'),14)
    def test_return_gate_parts_present_old_ones_gone(self):
        ids={p['id'] for p in P};self.assertTrue({'XB20','XB21','XB22','XB23'}<=ids);self.assertFalse({'XB04','XB07'}&ids)
    def test_step_and_dxf_files_exist(self):
        for p in P:self.assertTrue((M/'step'/f"{p['id']}.step").exists(),p['id'])
        self.assertTrue((M/'step'/'ADF50_V06_mechanical_assembly.step').exists());self.assertEqual(len(list((M/'dxf').glob('*.dxf'))),4)
    def test_bom_matches_parts(self):
        rows=list(csv.reader(open(M/'ADF50_V06_机械BOM.csv',encoding='utf-8-sig')))[1:]
        self.assertEqual({r[0]:int(r[2]) for r in rows},{p['id']:p['qty'] for p in P})
    def test_keepout_only_pmt_service_space_by_removable_cartridge(self):
        self.assertEqual({k['keepout'] for k in R['keepout_aabb_overlaps']},{'KO_PMT'})
        ent={r['name'] for r in I if r['group']=='ENT'};self.assertTrue(all(k['adf'] in ent for k in R['keepout_aabb_overlaps']))
if __name__=='__main__':unittest.main()
