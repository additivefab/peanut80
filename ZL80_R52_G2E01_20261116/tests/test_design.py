from pathlib import Path
import sys,json,unittest,math,csv
import numpy as np
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'simulations')]
from design_circuits import S,BOARDS,B06,B07,B08,B01
from sexpr import loads,child,children,walk
from run_models import tia_tf,bias,response,cmp_model,edges
class TestDesign(unittest.TestCase):
 def test_01_four_boards(self):self.assertEqual({b['id'] for b in BOARDS},{'B01','B06','B07','B08'})
 def test_02_pin_ids_unique(self):
  for k,s in S.items():self.assertEqual(len(s['pins']),len({p['num'] for p in s['pins']}),k)
 def test_03_all_pins_mapped(self):
  for b in BOARDS:
   for c in b['components']:self.assertEqual(set(c['nets']),{p['num'] for p in S[c['kind']]['pins']},c['ref'])
 def test_04_sources_on_ics(self):
  for b in BOARDS:
   for c in b['components']:
    if c['ref'].startswith('U'):self.assertTrue(c['source'].startswith('V'))
 def test_05_diode_three_pins(self):self.assertEqual({p['num']:p['name'] for p in S['S5971']['pins']},{'1':'K','3':'A','2':'CASE'})
 def test_06_opa356_types(self):self.assertEqual({p['num']:p['type'] for p in S['OPA356_DBV']['pins']},{'1':'output','2':'power_in','3':'input','4':'input','5':'power_in'})
 def test_07_comparator_shutdown(self):
  for b in [B06,B07]:self.assertEqual(next(c for c in b['components'] if c['ref']=='U2')['nets']['6'],'GND')
 def test_08_opa828_nc(self):self.assertEqual({p['num'] for p in S['OPA828_SOIC']['pins'] if p['type']=='no_connect'},{'1','5','8'})
 def test_09_regulator_output(self):self.assertEqual(next(p for p in S['TLV75533_DBV']['pins'] if p['num']=='5')['type'],'power_out')
 def test_10_pmt_direction(self):self.assertEqual(next(p for p in S['H10720_MODULE']['pins'] if p['num']=='2')['type'],'output')
 def test_11_all_nc_empty(self):
  for b in BOARDS:
   for c in b['components']:
    for p in S[c['kind']]['pins']:
     if p['type']=='no_connect':self.assertEqual(c['nets'][p['num']],'')
 def test_12_references_unique(self):
  for b in BOARDS:self.assertEqual(len(b['components']),len({c['ref'] for c in b['components']}))
 def test_13_generated_syntax(self):
  for p in (R/'electronics').rglob('*'):
   if p.suffix in ['.kicad_sym','.kicad_sch','.kicad_pcb','.kicad_mod']:loads(p.read_text())
 def test_14_native_instance_count(self):
  for b in BOARDS:
   f=R/'electronics/projects'/b['id']/(b['id']+'_G2E01.kicad_sch');self.assertEqual(len(children(loads(f.read_text()),'symbol')),len(b['components']))
 def test_15_native_uuid_unique(self):
  for b in BOARDS:
   sc=loads((R/'electronics/projects'/b['id']/(b['id']+'_G2E01.kicad_sch')).read_text());vals=[x[1] for x in walk(sc,'uuid')];self.assertEqual(len(vals),len(set(vals)))
 def test_16_not_all_passive(self):
  a=json.loads((R/'engineering/pin_net_type_audit.json').read_text());self.assertGreater(sum(x['pin_type']=='input' for x in a),10)
 def test_17_pcb_pad_net_agrees(self):
  for b in BOARDS:
   d={c['ref']:c for c in b['components']};pc=loads((R/'electronics/projects'/b['id']/(b['id']+'_G2E01.kicad_pcb')).read_text())
   for fp in children(pc,'footprint'):
    props={x[1]:x[2] for x in children(fp,'property')};ref=props.get('Reference','')
    if ref not in d:continue
    for pad in children(fp,'pad'):
     net=child(pad,'net');actual=net[2] if net else '';self.assertEqual(actual,d[ref]['nets'].get(pad[1],''),(b['id'],ref,pad[1]))
 def test_18_pcb_no_copper_claim(self):
  for p in (R/'electronics/projects').rglob('*.kicad_pcb'):
   pc=loads(p.read_text());self.assertEqual(len(children(pc,'segment')),0)
 def test_19_floorplan_no_parked(self):self.assertEqual(json.loads((R/'evidence/placement_open_issues.json').read_text()),[])
 def test_20_floorplan_inside_bounds(self):
  F=json.loads((R/'engineering/footprints.json').read_text());dims={b['id']:b['size_mm'] for b in BOARDS}
  for c in json.loads((R/'engineering/placements.json').read_text()):
   w,h=dims[c['board']];x,y=c['pcb_xy'];f=F[c['fp']];self.assertTrue(0<=x-f['w']/2<x+f['w']/2<=w);self.assertTrue(0<=y-f['h']/2<y+f['h']/2<=h)
 def test_21_tia_poles(self):
  for b in [B01,B06,B08]:
   m=b['model'];tf=tia_tf(m['rf_ohm'],m['cf_F'],m['cin_F'],m['gbw_Hz'],m['a0']);self.assertTrue(np.all(tf.poles.real<0))
 def test_22_tia_dc(self):
  m=B01['model'];tf=tia_tf(m['rf_ohm'],m['cf_F'],m['cin_F'],m['gbw_Hz'],m['a0']);self.assertAlmostEqual(tf.num[0]/tf.den[-1],m['rf_ohm']*m['a0']/(1+m['a0']),places=5)
 def test_23_bias_loaded(self):
  v,t=bias();self.assertLess(v,1.0);self.assertGreater(v,.99);self.assertGreater(t-v,.02);self.assertLess(t-v,.03)
 def test_24_fda_headroom(self):self.assertLess(B01['model']['fda_gain']*.5,.9)
 def test_25_bipolar_model_not_rail_blowup(self):
  d=np.load(R/'simulations/results/B01_step_traces.npz');self.assertLess(np.max(np.abs(d['differential_external_rc_V'])),1.)
 def test_26_report_limits(self):
  d=json.loads((R/'simulations/results/summary.json').read_text());self.assertEqual(d['bench'],'NOT_RUN');self.assertEqual(d['judgement']['timing_5um_compliance'],'NOT_DEMONSTRATED')
 def test_27_timewalk_exposes_risk(self):
  d=json.loads((R/'simulations/results/summary.json').read_text())['B06'];self.assertGreater(d['leading_edge_amplitude_timewalk_pp_ns'],200)
 def test_28_not_fake_bench(self):
  with (R/'bench/execution_records_TEMPLATE.csv').open(encoding='utf-8-sig') as f:
   for row in csv.DictReader(f):self.assertEqual(row['decision'],'NOT_RUN');self.assertEqual(row['measured_result'],'')
 def test_29_adc_65pins(self):
  with (R/'engineering/AD9268_CMOS_pin_audit.csv').open(encoding='utf-8-sig') as f:a=list(csv.DictReader(f))
  self.assertEqual(len(a),65);self.assertEqual(next(x for x in a if x['pad']=='44')['electrical_type'],'bidirectional')
 def test_30_adc_cmos_not_lvds(self):
  with (R/'engineering/AD9268_CMOS_pin_audit.csv').open(encoding='utf-8-sig') as f:
   self.assertEqual({x['mode'] for x in csv.DictReader(f)},{'PARALLEL_CMOS_1V8'})
 def test_31_source_register(self):self.assertEqual(len(json.loads((R/'reference/vendor_source_register.json').read_text())),8)
 def test_32_synccircuits_identical_except_mechanics(self):
  self.assertEqual([(x['ref'],x['kind'],x['nets'],x['value']) for x in B06['components']],[(x['ref'],x['kind'],x['nets'],x['value']) for x in B07['components']])
 def test_33_derived_proposed_timing(self):
  d=json.loads((R/'simulations/results/summary.json').read_text())['B06'];self.assertAlmostEqual(d['proposed_5um_timing_budget_ns'],79.5774715,places=5)
 def test_34_no_dummy_gain_switch(self):self.assertNotIn('GAIN_SW',str(B01['components']))
 def test_35_pads_inside_courtyard(self):
  F=json.loads((R/'engineering/footprints.json').read_text())
  for k,f in F.items():
   for p in f['pads']:
    self.assertLessEqual(abs(p['x'])+p['w']/2,f['w']/2+1e-6,k)
    self.assertLessEqual(abs(p['y'])+p['h']/2,f['h']/2+1e-6,k)
if __name__=='__main__':unittest.main(verbosity=2)
