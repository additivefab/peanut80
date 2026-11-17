from pathlib import Path
import unittest,json,sys,math,tempfile
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'engineering'),str(R/'software')]
from calculate import calculate
from reference_model import *
class Budget(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.p=json.loads((R/'engineering/parameters.json').read_text());cls.c=calculate(cls.p)
 def test_width_order(self):self.assertLess(self.p['film_width'],self.p['scan_span']);self.assertLess(self.p['scan_span'],self.p['slot_length'])
 def test_facet_rate(self):self.assertEqual(self.c['line_hz'],300)
 def test_period(self):self.assertAlmostEqual(self.c['period_ms'],10/3)
 def test_dwell(self):self.assertAlmostEqual(self.c['pixel_dwell_us'],.795774715,places=8)
 def test_valid_duty(self):self.assertTrue(0<self.c['geometric_active_fraction']<1)
 def test_adc_continuous(self):self.assertEqual(self.c['adc_raw_MB_s'],80)
 def test_image_size(self):self.assertEqual(self.c['pixels_per_roi'],1600)
 def test_storage(self):self.assertEqual(self.c['image_MB_m'],64)
 def test_encoder_quantization(self):self.assertAlmostEqual(self.c['encoder_step_um'],3.8349519697)
 def test_accuracy_not_quantization(self):self.assertGreater(self.c['encoder_typ_angle_equiv_um'],self.c['encoder_step_um']*8)
 def test_pmt_fits(self):self.assertLess(self.c['guide_exit_diagonal_mm']+2*.2,8)
 def test_slot_margin(self):self.assertEqual(self.c['slit_each_end_margin_mm'],2)
 def test_photon_density(self):self.assertAlmostEqual(self.c['photon_example'][1]['photoelectrons_per_pixel']/self.c['photon_example'][2]['photoelectrons_per_pixel'],10)
 def test_box(self):self.assertAlmostEqual(self.c['box_litres'],28.8)
 def test_cad_valid(self):self.assertTrue(json.loads((R/'tests/cad_validity.json').read_text())['all_valid'])
 def test_core_overlap(self):self.assertEqual(json.loads((R/'tests/cad_overlap_raw.json').read_text()),[])
 def test_ecad_body_geometry(self):self.assertEqual(json.loads((R/'tests/ecad_geometry.json').read_text())['issues'],[])
 def test_ecad_text_balance(self):self.assertTrue(all(json.loads((R/'tests/ecad_geometry.json').read_text())['syntax_balanced'].values()))
 def test_harness_budget(self):
  for h in json.loads((R/'electronics/harness_routes.json').read_text()):self.assertGreater(h['cut_length_budget_mm'],h['polyline_length_mm'])
 def test_board_count(self):self.assertEqual(sum(x['layers']>0 for x in json.loads((R/'electronics/board_definitions.json').read_text())),8)
class Signals(unittest.TestCase):
 def test_zero_density(self):self.assertEqual(transmission_to_density(100,0,100),0)
 def test_density_3(self):self.assertAlmostEqual(transmission_to_density(.1,0,100),3)
 def test_dark_rejection(self):
  with self.assertRaises(ValueError):transmission_to_density(1,2,100)
 def test_flat_rejection(self):
  with self.assertRaises(ValueError):transmission_to_density(2,2,2)
 def test_power_normalization(self):self.assertAlmostEqual(transmission_to_density(50,0,100,2),math.log10(4))
 def test_sync_mapping(self):self.assertEqual(position_from_sync(150,100,200),0)
 def test_bad_sync(self):
  with self.assertRaises(ValueError):position_from_sync(2,3,1)
 def test_quad_forward(self):self.assertEqual(sum(quadrature(a,b)[0] for a,b in zip([0,1,3,2],[1,3,2,0])),4)
 def test_quad_reverse(self):self.assertEqual(sum(quadrature(a,b)[0] for a,b in zip([0,2,3,1],[2,3,1,0])),-4)
 def test_quad_illegal(self):self.assertEqual(quadrature(0,3),(0,True))
 def test_tag_alignment(self):self.assertEqual(delay_tags([10,11,12],2),[None,None,10,11,12])
 def test_chunk_64bit(self):
  with tempfile.TemporaryDirectory() as t:
   w=ChunkWriter(t,2,'R5');p=w.write(2**40,[[1,65535],[10,20]],{'gap':False});self.assertEqual(w.verify(p)['first_row'],2**40)
 def test_immutable(self):
  with tempfile.TemporaryDirectory() as t:
   w=ChunkWriter(t,2,'R5');w.write(0,[[1,2]],{})
   with self.assertRaises(FileExistsError):w.write(0,[[3,4]],{})
 def test_corrupt(self):
  with tempfile.TemporaryDirectory() as t:
   w=ChunkWriter(t,2,'R5');p=w.write(0,[[1,2]],{});p.write_bytes(p.read_bytes()+b'x')
   with self.assertRaises(ValueError):w.verify(p)
 def test_invalid_range(self):
  with tempfile.TemporaryDirectory() as t:
   w=ChunkWriter(t,2,'R5')
   with self.assertRaises(ValueError):w.write(0,[[1,70000]],{})
if __name__=='__main__':unittest.main()
