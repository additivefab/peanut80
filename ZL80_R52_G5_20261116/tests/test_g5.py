import unittest,tempfile,struct,random,json,math,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'software'))
from zlraw import *
from geometry import *
from reference_models import *
from import_axis_dump import convert

def valid_records():
    return [Record(START,1,12),Record(ENC_M,1,0,0x8000),Record(ENC_D,1,0,0x8000),
            Record(SOS_UP,100,1),Record(SAMPLE,150,(456<<16)|123),
            Record(EOS_UP,200,1),Record(STATUS,250,0),Record(LOSS,250,0),Record(END,250,12)]
class RecordTests(unittest.TestCase):
    def test_record_size(self):self.assertEqual(RECORD.size,16)
    def test_little_endian_payload(self):self.assertEqual(Record(SAMPLE,1,0x12345678).pack()[:4],b'\x78\x56\x34\x12')
    def test_roundtrip_boundaries(self):
        for x in (0,1,2**64-1):
            r=Record(SAMPLE,x,0xffffffff,0xffff);self.assertEqual(Record.unpack(r.pack()),r)
    def test_types_roundtrip(self):
        for k in TYPES:self.assertEqual(Record.unpack(Record(k,0).pack()).kind,k)
    def test_unsupported_version(self):
        b=bytearray(Record(SAMPLE,0).pack());b[14]=99
        with self.assertRaises(FormatError):Record.unpack(b)
    def test_unknown_type(self):
        with self.assertRaises(FormatError):Record(0x55,0).pack()
    def test_preserve_zero_and_fullscale(self):
        r=Record.unpack(Record(SAMPLE,1,0xffff0000).pack());self.assertEqual((r.a,r.b),(0,65535))
    def test_signed_encoder(self):self.assertEqual(Record(ENC_M,0,0xffffffff).signed_payload,-1)
    def test_truncated_record(self):
        with self.assertRaises(FormatError):Record.unpack(b'123')
    def test_negative_timestamp(self):
        with self.assertRaises(FormatError):Record(SAMPLE,-1).pack()
class ArchiveTests(unittest.TestCase):
    def setUp(self):self.d=tempfile.TemporaryDirectory();self.p=Path(self.d.name)/'x.zlraw'
    def tearDown(self):self.d.cleanup()
    def write(self,records=None,block=3):write_archive(self.p,{'synthetic':True},records or valid_records(),block)
    def test_multiblock_roundtrip(self):self.write();self.assertEqual(list(iter_records(self.p)),valid_records())
    def test_valid_session(self):self.write();self.assertTrue(inspect(self.p)['digital_integrity_eligible'])
    def test_never_metrology_release(self):self.write();self.assertFalse(inspect(self.p)['metrology_release'])
    def test_no_overwrite(self):
        self.write()
        with self.assertRaises(FileExistsError):self.write()
    def test_crc_corruption(self):
        self.write();b=bytearray(self.p.read_bytes());b[-17]^=1;self.p.write_bytes(b)
        with self.assertRaises(FormatError):list(iter_records(self.p))
    def test_truncated_block(self):
        self.write();self.p.write_bytes(self.p.read_bytes()[:-1])
        with self.assertRaises(FormatError):list(iter_records(self.p))
    def test_bad_sequence(self):
        self.write();b=bytearray(self.p.read_bytes());n=int.from_bytes(b[8:12],'little');b[12+n+4]=2;self.p.write_bytes(b)
        with self.assertRaises(FormatError):list(iter_records(self.p))
    def test_missing_end(self):
        self.write(valid_records()[:-1])
        with self.assertRaises(FormatError):inspect(self.p)
    def test_end_id_mismatch(self):
        rr=valid_records();rr[-1]=Record(END,250,13);self.write(rr)
        with self.assertRaises(FormatError):inspect(self.p)
    def test_loss_blocks_integrity(self):
        rr=valid_records();rr[-2]=Record(LOSS,250,1);self.write(rr);self.assertFalse(inspect(self.p)['digital_integrity_eligible'])
    def test_fault_blocks_integrity(self):
        rr=valid_records();rr[-3]=Record(STATUS,250,2);self.write(rr);self.assertFalse(inspect(self.p)['digital_integrity_eligible'])
    def test_time_uncal_blocks_integrity(self):
        rr=valid_records();rr[4]=Record(SAMPLE,150,123,4);self.write(rr);self.assertFalse(inspect(self.p)['digital_integrity_eligible'])
    def test_pair_unknown_blocks_integrity(self):
        rr=valid_records();rr[4]=Record(SAMPLE,150,123,8);self.write(rr);self.assertFalse(inspect(self.p)['digital_integrity_eligible'])
    def test_upstream_loss_blocks_integrity(self):
        rr=valid_records();rr[4]=Record(SAMPLE,150,123,32);self.write(rr);self.assertFalse(inspect(self.p)['digital_integrity_eligible'])
    def test_bad_footer_order(self):
        rr=valid_records();rr[-2],rr[-3]=rr[-3],rr[-2];self.write(rr)
        with self.assertRaises(FormatError):inspect(self.p)
    def test_sample_after_footer(self):
        rr=valid_records();rr.insert(-2,Record(SAMPLE,260,1));self.write(rr)
        with self.assertRaises(FormatError):inspect(self.p)
    def test_duplicate_sample_timestamp(self):
        rr=valid_records();rr.insert(5,rr[4]);self.write(rr);self.assertFalse(inspect(self.p)['digital_integrity_eligible'])
    def test_axis_dump_conversion(self):
        src=Path(self.d.name)/'axis.txt';s=[]
        for j,r in enumerate(valid_records()):
            b=r.pack();s.extend([f'{int.from_bytes(b[:8],"little"):016x} ff 0',f'{int.from_bytes(b[8:],"little"):016x} ff {int(j==len(valid_records())-1)}'])
        src.write_text('\n'.join(s));self.assertTrue(convert(src,self.p)['digital_integrity_eligible'])
    def test_axis_first_half_tlast_rejected(self):
        src=Path(self.d.name)/'axis.txt';src.write_text('0000000000000000 ff 1\n')
        with self.assertRaises(FormatError):convert(src,self.p)
class GeometryTests(unittest.TestCase):
    def test_linear_center(self):self.assertEqual(x_mm(150,ScanLine(1,100,200,0)),0)
    def test_sync_edges(self):
        l=ScanLine(1,100,200,0);self.assertEqual(x_mm(100,l),-46);self.assertEqual(x_mm(200,l),46)
    def test_latency_correction(self):self.assertEqual(x_mm(140,ScanLine(1,100,200,0),sensor_delay_ticks=10),0)
    def test_relative_facet_not_absolute(self):
        l=lines_from_records(valid_records())[0];self.assertEqual(l.relative_facet,0);self.assertIsNone(l.absolute_facet)
    def test_missing_eos_not_filled(self):self.assertEqual(lines_from_records([Record(SOS_UP,1,1)]),[])
    def test_missing_eos_between_lines_rejected(self):
        with self.assertRaises(FormatError):lines_from_records([Record(SOS_UP,1,1),Record(SOS_UP,2,2)])
    def test_eos_wrong_line_rejected(self):
        with self.assertRaises(FormatError):lines_from_records([Record(SOS_UP,1,1),Record(EOS_UP,2,2)])
    def test_y_bracketed(self):
        self.assertAlmostEqual(interpolate_y(5,[(0,0),(10,10)]),5*math.pi*20/16384)
    def test_y_no_extrapolation(self):self.assertIsNone(interpolate_y(15,[(0,0),(10,1)]))
    def test_y_no_pre_extrapolation(self):self.assertIsNone(interpolate_y(1,[(5,0),(10,1)]))
    def test_encoder_invalid_rejected(self):
        with self.assertRaises(FormatError):encoder_points([Record(ENC_M,1,0,4)])
    def test_encoder_discontinuity_rejected(self):
        with self.assertRaises(FormatError):encoder_points([Record(ENC_M,1,0),Record(ENC_M,2,10,1)])
class ModelTests(unittest.TestCase):
    def test_full_pop_push_not_loss(self):
        f=FIFOModel(2);f.cycle(1);f.cycle(2);self.assertEqual(f.cycle(3,True),1);self.assertEqual(list(f.q),[2,3]);self.assertEqual(f.dropped,0)
    def test_fifo_overflow_counter(self):
        f=FIFOModel(2);[f.cycle(i) for i in range(5)];self.assertEqual(f.dropped,3)
    def test_random_fifo_scoreboard(self):
        rng=random.Random(52);f=FIFOModel(16);expect=[];drops=0
        for i in range(10000):
            pop=rng.random()<.45;push=i if rng.random()<.6 else None
            want=expect.pop(0) if pop and expect else None
            if push is not None:
                if len(expect)<16:expect.append(push)
                else:drops+=1
            self.assertEqual(f.cycle(push,pop),want)
        self.assertEqual(list(f.q),expect);self.assertEqual(f.dropped,drops)
    def test_quad_forward_reverse(self):
        q=QuadModel()
        for ab in [1,3,2,0]:q.step(ab)
        self.assertEqual(q.pos,4)
        for ab in [2,3,1,0]:q.step(ab)
        self.assertEqual(q.pos,0)
    def test_quad_index_does_not_zero(self):
        q=QuadModel();q.step(1);q.step(1,True);self.assertEqual(q.pos,1)
    def test_quad_illegal_no_position_change(self):q=QuadModel();q.step(3);self.assertEqual((q.pos,q.illegal),(0,1))
    def test_axis_backpressure_stability(self):
        p=AxisPacketModel();p.put(Record(SAMPLE,5,123));x=p.output()
        for _ in range(500):self.assertEqual(p.cycle(False),x)
    def test_axis_early_end_partial_packet(self):
        p=AxisPacketModel(256);p.put(Record(END,5,1));self.assertFalse(p.cycle(True)[2]);self.assertTrue(p.cycle(True)[2])
    def test_axis_normal_packet_boundary(self):
        p=AxisPacketModel(4);lasts=[]
        for i in range(9):p.put(Record(SAMPLE,i));p.cycle(True);lasts.append(p.cycle(True)[2])
        self.assertEqual(lasts,[False,False,False,True,False,False,False,True,False])
    def test_spi_write_frame(self):self.assertEqual(int(''.join(map(str,spi_frame(False,13,4))),2),0x000d04)
    def test_spi_read_frame(self):self.assertEqual(int(''.join(map(str,spi_frame(True,1))),2),0x800100)
    def test_adc_latency_units(self):self.assertEqual(12/20_000_000*100_000_000,60)
    def test_raw_bandwidth(self):self.assertEqual(20_000_000*16,320_000_000)
    def test_capture_depth_budget(self):self.assertAlmostEqual(1024/20_000_000*1e6,51.2)
class GateTests(unittest.TestCase):
    def test_hardware_disabled(self):self.assertFalse(json.loads((R/'config/design.json').read_text())['hardware_enable'])
    def test_no_bitstream(self):self.assertEqual(list(R.rglob('*.bit')),[])
    def test_no_fake_absolute_facet(self):self.assertIsNone(json.loads((R/'config/design.json').read_text())['facet_absolute_reference'])
    def test_laser_tied_off(self):self.assertIn("assign laser_request=1'b0",(R/'rtl/core/zl80_capture_core.sv').read_text())
if __name__=='__main__':unittest.main(verbosity=2)
