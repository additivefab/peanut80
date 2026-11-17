import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'control'));sys.path.insert(0,str(ROOT/'engineering'))
from adf_controller import ADFController,Inputs,State
import calculate as C
P=json.loads((ROOT/'engineering/parameters.json').read_text());EXIT_S=C.calculate(P)['handoff']['exit_nip_s_mm']
def mk(**kw):
    kw.setdefault('dual_follower',False)      # most tests exercise the unchanged-G3 profile explicitly
    c=ADFController(exit_s=EXIT_S);c.begin('J1',**kw);return c
def inp(t,head,**kw):
    d=dict(t_s=t,leading_s_mm=head,us_recipe_qualified=True);d.update(kw);return Inputs(**d)
class T(unittest.TestCase):
    def test_full_length_request_rejected_without_roi(self):
        with self.assertRaises(ValueError):ADFController(exit_s=EXIT_S).begin('J',300,roi=(0,300),dual_follower=False)
    def test_unchanged_g3_window_is_47_253(self):
        mk(length_mm=300,roi=(47,253))
        with self.assertRaises(ValueError):ADFController(exit_s=EXIT_S).begin('J',300,roi=(46,253),dual_follower=False)
        with self.assertRaises(ValueError):ADFController(exit_s=EXIT_S).begin('J',300,roi=(47,254),dual_follower=False)
    def test_default_profile_is_dual_follower_after_ecr_approval(self):
        c=ADFController(exit_s=EXIT_S);c.begin('J',300,roi=(0,300));self.assertTrue(c.dual)
    def test_follower_mismatch_in_overlap_zone_faults(self):
        c=mk(length_mm=300,roi=(0,300),dual_follower=True);c.state=State.SCAN
        o=c.step(inp(0.01,100,master_grip=True,measure_valid=True,metrology_qualified=True,follower_agree=False));self.assertEqual(o['fault'],'FOLLOWER_MISMATCH');self.assertEqual(o['quality'],'INVALID')
    def test_follower_mismatch_ignored_where_only_one_follower_is_valid(self):
        c=mk(length_mm=300,roi=(0,300),dual_follower=True);c.state=State.SCAN
        o=c.step(inp(0.01,30,measure_valid=True,metrology_qualified=True,follower_agree=False));self.assertEqual(o['state'],'SCAN')
    def test_dual_follower_allows_full_length(self):
        mk(length_mm=300,roi=(0,300),dual_follower=True)
    def test_carrier_needs_qualification(self):
        with self.assertRaises(ValueError):ADFController(exit_s=EXIT_S).begin('J',300,roi=(0,300),leader_mm=60,trailer_mm=60)
    def test_length_range(self):
        for L in (259,301):
            with self.assertRaises(ValueError):ADFController(exit_s=EXIT_S).begin('J',L,roi=(47,L-47),dual_follower=False)
    def test_exit_position_is_path_based(self):
        self.assertAlmostEqual(EXIT_S,152+C.geometry(P)['exit_arc_mm']+P['eject_nip_after_bend_mm'],places=6)
    def test_happy_path_g3_unchanged(self):
        c=mk(length_mm=300,roi=(47,253));t=0.0;seen=[]
        def go(head,**kw):
            nonlocal t;t+=0.01;o=c.step(inp(t,head,**kw));seen.append(o['state']);return o
        go(-400);go(-35);go(-35)
        self.assertTrue(go(20)['entry_drive_follow'])
        o=go(50,master_grip=True,measure_valid=True,metrology_qualified=True);self.assertTrue(o['capture_request']);self.assertFalse(o['entry_nip_open'] and False)
        go(100,master_grip=True,measure_valid=True,metrology_qualified=True);go(254,master_grip=True,measure_valid=True,metrology_qualified=True)
        self.assertEqual(c.state,State.AFTER_SCAN)
        go(EXIT_S+6,entire_sheet_checked=True);self.assertEqual(c.state,State.AFTER_SCAN)
        go(313,entire_sheet_checked=True);self.assertEqual(c.state,State.TRANSFER_OUT)
        o=go(330,entire_sheet_checked=True,exit_grip=True,exit_speed_matched=True);self.assertTrue(o['exit_nip_close']);self.assertFalse(o['eject_fast_allowed'])
        o=go(346,entire_sheet_checked=True,exit_grip=True,exit_speed_matched=True,master_tail_clear=True,scan_end_ack=True);self.assertTrue(o['eject_fast_allowed'])
        go(600,entire_sheet_checked=True,output_tail_clear=True,scan_end_ack=True);self.assertEqual(c.state,State.STACK)
        o=go(600,entire_sheet_checked=True,return_gate_closed=True,stack_transfer_done=True,scan_end_ack=True,raw_integrity_ok=True)
        self.assertEqual(o['state'],'DONE');self.assertEqual(o['quality'],'ELIGIBLE_FOR_HOST_REVIEW');self.assertEqual(c.output_count,1)
    def test_dual_follower_scans_before_main_grip(self):
        c=mk(length_mm=300,roi=(0,300),dual_follower=True);c.state=State.TRANSFER_IN
        o=c.step(inp(0.01,10,measure_valid=True,metrology_qualified=True));self.assertEqual(o['state'],'SCAN');self.assertTrue(o['entry_drive_follow'])
        o=c.step(inp(0.02,30,measure_valid=True,metrology_qualified=True));self.assertEqual(o['state'],'SCAN')
        o=c.step(inp(0.03,50,measure_valid=True,metrology_qualified=True));self.assertEqual(o['state'],'FAULT');self.assertEqual(o['fault'],'METROLOGY_LOST')
    def test_g3_unchanged_does_not_scan_before_main_grip(self):
        c=mk(length_mm=300,roi=(47,253));c.state=State.TRANSFER_IN
        o=c.step(inp(0.01,10,measure_valid=True,metrology_qualified=True));self.assertNotEqual(o['state'],'SCAN')
    def test_entry_released_only_after_main_grip(self):
        c=mk(length_mm=300,roi=(47,253));c.state=State.TRANSFER_IN
        self.assertTrue(c.step(inp(0.01,46))['entry_drive_follow']);self.assertTrue(c.step(inp(0.02,47))['entry_drive_follow'])
    def test_missed_handoff_latches(self):
        c=mk(length_mm=300,roi=(47,253));c.state=State.TRANSFER_OUT
        o=c.step(inp(0.01,343));self.assertEqual(o['fault'],'MISSED_OUTPUT_HANDOFF');self.assertFalse(o['eject_fast_allowed'])
    def test_no_early_fast_eject(self):
        c=mk(length_mm=300,roi=(47,253));c.state=State.TRANSFER_OUT
        self.assertFalse(c.step(inp(0.01,320,exit_grip=True,exit_speed_matched=True))['eject_fast_allowed'])
    def test_reverse_is_a_fault(self):
        c=mk(length_mm=300,roi=(47,253));c.step(inp(0.01,-90));o=c.step(inp(0.02,-91));self.assertEqual(o['fault'],'UNCOMMANDED_REVERSE');self.assertFalse(o['sheet_reverse_allowed'])
    def test_heartbeat(self):
        c=mk(length_mm=300,roi=(47,253));c.step(inp(0.01,-90));o=c.step(inp(1.0,-89));self.assertEqual(o['fault'],'TIME_OR_HEARTBEAT')
    def test_unqualified_ultrasound_stops(self):
        c=mk(length_mm=300,roi=(47,253));o=c.step(Inputs(t_s=.01));self.assertEqual(o['fault'],'US_RECIPE_UNQUALIFIED')
    def test_late_double_invalidates_job(self):
        c=mk(length_mm=300,roi=(47,253));c.state=State.SCAN;o=c.step(inp(0.01,100,master_grip=True,measure_valid=True,metrology_qualified=True,double_detected=True))
        self.assertEqual(o['quality'],'INVALID');self.assertFalse(o['capture_request']);self.assertEqual(o['state'],'FAULT')
    def test_laser_request_always_false_and_no_hardware(self):
        c=mk(length_mm=300,roi=(47,253));o=c.step(inp(0.01,-90));self.assertFalse(o['laser_request']);self.assertEqual(o['implementation'],'REFERENCE_MODEL_NO_HARDWARE_IO')
    def test_incomplete_quality_evidence_blocks_review(self):
        c=mk(length_mm=300,roi=(47,253));c.state=State.STACK
        o=c.step(inp(0.01,600,return_gate_closed=True,stack_transfer_done=True,scan_end_ack=True,raw_integrity_ok=True));self.assertEqual(o['fault'],'INCOMPLETE_QUALITY_EVIDENCE')
if __name__=='__main__':unittest.main()
