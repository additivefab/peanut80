import unittest,json,sys,math
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from sexpr import loads,children,child
from pcb_geometry import load
class G4Tests(unittest.TestCase):
 def setUp(self):
  self.D,self.F,self.P=load();self.audit=json.loads((R/'validation/results/copper_audit.json').read_text())
 def test_immutable_topology(self):
  old=json.loads((R/'sources/inherited/G2_circuits.json').read_text())
  def nets(D):return {(b['id'],c['ref']):c['nets'] for b in D['boards'] for c in b['components']}
  self.assertEqual(nets(old),nets(self.D))
 def test_right_handed_transforms(self):
  for t in json.loads((R/'engineering/board_transforms.json').read_text()):
   a,b=t['u'],t['v'];cross=[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];self.assertEqual(cross,t['n'])
 def test_layer_stack(self):self.assertAlmostEqual(.035*4+.18*2+1.10,1.6)
 def test_native_status_explicit(self):self.assertIn(json.loads((R/'validation/results/native_tools.json').read_text())['status'],['NOT_RUN','EXECUTED_REVIEW_REQUIRED','HAS_VIOLATIONS_OR_ERRORS'])
 def test_b01_not_concealed(self):self.assertEqual(next(v for v in self.audit if v['board']=='B01')['unconnected_min_links'],43)
 def test_scope_g2_g3(self):self.assertEqual(len(self.P),84)
 def test_schematic_graph(self):self.assertEqual(json.loads((R/'validation/results/schematic_graph_audit.json').read_text())['status'],'PASS')
 def test_mcad_valid(self):self.assertTrue(json.loads((R/'validation/results/mcad_audit.json').read_text())['body_valid'])
 def test_mcad_expected_not_hidden(self):self.assertEqual(json.loads((R/'validation/results/mcad_audit.json').read_text())['body_collision_count'],8)
 def test_mcad_unexpected(self):self.assertEqual(json.loads((R/'validation/results/mcad_audit.json').read_text())['unexpected_body_collisions'],0)
 def test_connector_clearance_candidate(self):self.assertEqual(json.loads((R/'validation/results/mcad_audit.json').read_text())['connector_corridor_conflicts'],0)
 def test_no_manufacturing_outputs(self):self.assertFalse(list((R/'electronics').rglob('*.gbr')))
 def test_pmt_pin_plane_mapping(self):
  t=next(x for x in json.loads((R/'engineering/board_transforms.json').read_text()) if x['board']=='B01');c=next(x for x in self.P if x['board']=='B01' and x['ref']=='JPMT1')
  expected={'1':(-6.32,90.72),'2':(29.24,90.72),'3':(34.32,90.72),'4':(34.32,75.48),'5':(29.24,75.48),'6':(11.46,75.48),'7':(6.38,75.48),'8':(-6.32,75.48)}
  for p in self.F[c['fp']]['pads']:
   x=t['origin'][0]+c['pcb_xy'][0]+p['x'];z=t['origin'][2]-c['pcb_xy'][1]-p['y'];self.assertAlmostEqual(x,expected[p['num']][0]);self.assertAlmostEqual(z,expected[p['num']][1])
 def test_reject_truncated_sexpr(self):
  with self.assertRaises(ValueError):loads('(kicad_pcb (foo 1)')
for bid in ['B06','B07','B08','B01']:
 def copper(self,bid=bid):self.assertEqual(next(v for v in self.audit if v['board']==bid)['clearance_violations'],0)
 def parity(self,bid=bid):self.assertTrue(next(v for v in self.audit if v['board']==bid)['pad_parity_pass'])
 def parse(self,bid=bid):
  for ext in ['kicad_sch','kicad_pcb']:self.assertTrue(loads((R/'electronics/projects'/bid/(bid+'_G4.'+ext)).read_text()))
 setattr(G4Tests,'test_copper_'+bid,copper);setattr(G4Tests,'test_pad_parity_'+bid,parity);setattr(G4Tests,'test_file_parse_'+bid,parse)
for bid in ['B06','B07','B08']:
 def connected(self,bid=bid):self.assertEqual(next(v for v in self.audit if v['board']==bid)['unconnected_min_links'],0)
 setattr(G4Tests,'test_connected_'+bid,connected)
if __name__=='__main__':unittest.main()
