import json,csv,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'mechanical'
R=json.loads((M/'interference.json').read_text());P=json.loads((M/'parts.json').read_text());I=json.loads((M/'instances.json').read_text())
C=json.loads((ROOT/'engineering/parameters.json').read_text())['user_constraints_2026_11_16']
class T(unittest.TestCase):
    def test_counts_consistent(self):
        self.assertEqual(R['part_numbers'],len(P));self.assertEqual(R['instances'],len(I))
        in_asm=sum(p['qty'] for p in P if p['id'] not in ('AF10A','AF10C'));self.assertEqual(in_asm,len(I))
    def test_all_parts_valid_solids(self):
        self.assertTrue(all(p['valid'] and p['volume_mm3']>0 for p in P))
    def test_no_self_interference(self):
        self.assertEqual(R['self_overlaps'],[]);self.assertGreater(R['self_pairs_intersected'],100)
    def test_no_scanner_interference(self):
        self.assertEqual(R['scanner_overlaps'],[])
        self.assertEqual({m['r5_part'] for m in R['scanner_modifications_from_contacts']},{'H02','H02R'})
    def test_envelope_within_user_constraints(self):
        e=R['working_envelope_mm_WDH'];self.assertLessEqual(e[1],C['depth_along_film_travel_mm']);self.assertLessEqual(e[2],C['height_max_mm'])
        bb=R['overall_aabb'];self.assertLessEqual(bb[3]-bb[0],320);self.assertGreaterEqual(bb[2],0)
    def test_nothing_above_scanner_top_cover(self):
        for r in I:
            a=r['aabb']
            if a[5]>300:self.assertTrue(a[4]<-150 or a[1]>150,r['name'])
    def test_three_dam_blocks(self):
        self.assertEqual(sorted(p['id'] for p in P if p['id'].startswith('AF10')),['AF10A','AF10B','AF10C'])
    def test_step_and_dxf_files_exist(self):
        for p in P:self.assertTrue((M/'step'/f"{p['id']}.step").exists(),p['id'])
        self.assertTrue((M/'step'/'ADF50_V04_mechanical_assembly.step').exists());self.assertEqual(len(list((M/'dxf').glob('*.dxf'))),4)
    def test_bom_matches_parts(self):
        rows=list(csv.reader(open(M/'ADF50_V04_机械BOM.csv',encoding='utf-8-sig')))[1:]
        self.assertEqual({r[0]:int(r[2]) for r in rows},{p['id']:p['qty'] for p in P})
    def test_keepout_only_pmt_service_space_by_entry_unit(self):
        self.assertEqual({k['keepout'] for k in R['keepout_aabb_overlaps']},{'KO_PMT'})
        ent={r['name'] for r in I if r['group']=='ENT'};self.assertTrue(all(k['adf'] in ent for k in R['keepout_aabb_overlaps']))
if __name__=='__main__':unittest.main()
