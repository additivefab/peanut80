import unittest,json,csv,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'software'))
from zlraw import *
from geometry import *
def recs(slip_every=0):
    out=[Record(START,1,5),Record(ENC_M,1,0,0x8000),Record(ENC_D,1,0,0x8000),Record(ENC_E,1,0,0x8000)]
    for k in range(1,41):
        t=1000*k;out+=[Record(ENC_M,t,k,1),Record(ENC_E,t+3,k-(k//slip_every if slip_every else 0),1)]
    return out
class EncoderE(unittest.TestCase):
    def test_type_code(self):self.assertEqual(ENC_E,0x22);self.assertIn(ENC_E,TYPES)
    def test_roundtrip(self):
        r=Record(ENC_E,7,0xffffffff,1);self.assertEqual(Record.unpack(r.pack()),r);self.assertEqual(r.signed_payload,-1)
    def test_identical_followers_agree(self):
        d=follower_difference(recs());self.assertLess(d['max_abs_difference_mm'],0.01);self.assertTrue(follower_agree(recs()))
    def test_slip_is_detected(self):
        self.assertFalse(follower_agree(recs(slip_every=4),limit_mm=0.02))
    def test_not_enough_evidence_is_unknown(self):
        self.assertIsNone(follower_agree([Record(START,1,5),Record(ENC_M,1,0,0x8000)]))
    def test_missing_counts_are_not_bridged(self):
        with self.assertRaises(FormatError):follower_difference(recs()+[Record(ENC_E,10**6,99,1)])
    def test_e_point_beyond_last_m_is_not_extrapolated(self):
        r=recs()+[Record(ENC_E,10**6,41,1)];self.assertLess(follower_difference(r)['max_abs_difference_mm'],0.01)
    def test_illegal_quadrature_still_rejected(self):
        with self.assertRaises(FormatError):follower_difference([Record(ENC_M,1,0),Record(ENC_M,2,1),Record(ENC_E,1,0),Record(ENC_E,2,1,4)])
class RtlAndPins(unittest.TestCase):
    core=(R/'rtl/core/zl80_capture_core.sv').read_text()
    def test_ports_and_decoder(self):
        for s in ('enc_e_a_async','enc_e_b_async','enc_e_open_async','quad_decoder u_e',"8'h22",'SNAP_E','fault_status[9]','fault_status[10]','.N(7)'):self.assertIn(s,self.core)
    def test_laser_still_tied_off(self):self.assertIn("assign laser_request=1'b0",self.core)
    def test_bench_exists(self):self.assertTrue((R/'sim/tb/tb_encoder_e.sv').exists())
    def test_pin_map(self):
        core=json.loads((R/'sources/hellofpga/core_pins.json').read_text());by={p['ball']:p for p in core}
        rows=list(csv.DictReader(open(R/'interfaces/pin_review.csv',encoding='utf-8-sig')))
        balls=[r['ball'] for r in rows];self.assertEqual(len(balls),len(set(balls)));sig=[r['signal'] for r in rows];self.assertEqual(len(sig),len(set(sig)))
        for r in rows:
            p=by[r['ball']];self.assertTrue(p['exposed']);self.assertEqual('Bank'+p['bank'],r['bank']);self.assertEqual(p['net'],r['core_net'])
            self.assertEqual(r['status'],'CANDIDATE_UNAPPROVED')
            if r['signal'] not in ('DCOA','DCOB'):self.assertFalse(p['cc'],r['signal'])
        self.assertEqual(sum(r['bank']=='Bank34' for r in rows),36)
        self.assertTrue(all(r['io_standard']=='LVCMOS18' for r in rows if r['bank']=='Bank34'))
        self.assertTrue(all(r['io_standard']=='LVCMOS33' for r in rows if r['bank']=='Bank35'))
        for s in ('ENC_E_A','ENC_E_B','ENC_E_OPEN','ENC_M_A','ENC_D_A'):self.assertIn(s,sig)
        d={r['signal']:r for r in rows};self.assertTrue(by[d['DCOA']['ball']]['cc'] and by[d['DCOB']['ball']]['cc'])
    def test_xdc_matches_csv(self):
        x=(R/'constraints/hf_core_pins_NOT_APPROVED.xdc').read_text();self.assertIn('NOT APPROVED',x)
        for r in csv.DictReader(open(R/'interfaces/pin_review.csv',encoding='utf-8-sig')):
            self.assertIn('PACKAGE_PIN %s IOSTANDARD %s} [get_ports %s]'%(r['ball'],r['io_standard'],r['signal'].lower()),x)
    def test_design_json_part(self):
        d=json.loads((R/'config/design.json').read_text());self.assertEqual(d['device_part'],'xc7z020clg400-1');self.assertFalse(d['hardware_enable'])
if __name__=='__main__':unittest.main()
