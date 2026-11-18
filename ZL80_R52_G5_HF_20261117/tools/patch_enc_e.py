"""One-shot patch record: adds encoder channel E (ECR-G3-01 exit-follower) to zl80_capture_core and the benches.
Kept in the package so the change is reproducible from the G5-20261116 sources. Each replacement must match exactly once."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def edit(p,pairs):
    s=p.read_text()
    for a,b in pairs:
        assert s.count(a)==1,(p.name,a[:50],s.count(a));s=s.replace(a,b)
    p.write_text(s)
edit(R/'rtl/core/zl80_capture_core.sv',[
 (" parameter integer SOS_TIMEOUT_TICKS=2000000,PAIR_TIMEOUT_TICKS=1000)("," parameter integer SOS_TIMEOUT_TICKS=2000000,PAIR_TIMEOUT_TICKS=1000,\n parameter integer E_REQUIRED=1)("),
 (" input wire enc_d_a_async,input wire enc_d_b_async,input wire enc_d_z_async,\n"," input wire enc_d_a_async,input wire enc_d_b_async,input wire enc_d_z_async,\n input wire enc_e_a_async,input wire enc_e_b_async,input wire enc_e_open_async,\n"),
 ("SNAP_D=3,RUN=4,DRAIN=5,STATUS=6,LOSS=7,ENDREC=8,WAIT_TX=9;","SNAP_D=3,RUN=4,DRAIN=5,STATUS=6,LOSS=7,ENDREC=8,WAIT_TX=9,SNAP_E=10;"),
 ("reg signed [31:0] start_m,start_d;","reg signed [31:0] start_m,start_d,start_e;"),
 (" reg [9:0] prev;wire [9:0] sy;"," reg [12:0] prev;wire [12:0] sy;"),
 ("sync_bits #(.WIDTH(10))","sync_bits #(.WIDTH(13))"),
 (".async_in({external_fault_async,",".async_in({enc_e_open_async,enc_e_b_async,enc_e_a_async,external_fault_async,"),
 (" wire signed [31:0] pm,npm,pd,npd;wire cm,zm,im,cd,zd,id;"," wire signed [31:0] pm,npm,pd,npd,pe,npe;wire cm,zm,im,cd,zd,id,ce,ze,ie;"),
 (" reg stop_pending;reg seen_sos"," // Channel E: exit pressure-roller follower (ECR-G3-01). No index line is used; sy[12] is the OPEN (cable/FFC absent) observation.\n quad_decoder u_e(.clk(clk),.rst(rst),.a(sy[10]),.b(sy[11]),.z(1'b0),\n  .position(pe),.next_position(npe),.changed(ce),.index_rise(ze),.illegal(ie));\n reg stop_pending;reg seen_sos"),
 ("((state==HEADER)||(state==SNAP_M)||(state==SNAP_D)||(state==RUN))","((state==HEADER)||(state==SNAP_M)||(state==SNAP_D)||(state==SNAP_E)||(state==RUN))"),
 (" wire [5:0] sv,sr,fv,fr,ov;wire [767:0] sd,fd;\n wire [31:0] drops[0:5];"," wire [6:0] sv,sr,fv,fr,ov;wire [895:0] sd,fd;\n wire [31:0] drops[0:6];"),
 ("for(di=0;di<6;di=di+1)","for(di=0;di<7;di=di+1)"),
 (" genvar g;\n generate for(g=0;g<6;g=g+1)"," assign sv[6]=collect_events&&ce;\n assign sd[768+:128]=rec(8'h22,{13'd0,ie,1'b0,ce},tick,npe);\n genvar g;\n generate for(g=0;g<7;g=g+1)"),
 (" rr_record_merge u_merge("," rr_record_merge #(.N(7)) u_merge("),
 ("   SNAP_D:begin pout=rec(8'h21,16'h8000,start_tick,start_d);pv=1;end\n","   SNAP_D:begin pout=rec(8'h21,16'h8000,start_tick,start_d);pv=1;end\n   SNAP_E:begin pout=rec(8'h22,16'h8000,start_tick,start_e);pv=1;end\n"),
 ("   start_m<=0;start_d<=0;line_no<=0;","   start_m<=0;start_d<=0;start_e<=0;line_no<=0;"),
 ("start_m<=npm;start_d<=npd;stop_pending<=0;","start_m<=npm;start_d<=npd;start_e<=npe;stop_pending<=0;"),
 ("    SNAP_D:if(pr)state<=RUN;\n","    SNAP_D:if(pr)state<=SNAP_E;\n    SNAP_E:if(pr)state<=RUN;\n"),
 ("    if(id)fault_status[3]<=1;\n","    if(id)fault_status[3]<=1;\n    if(E_REQUIRED!=0)begin\n     if(ie)fault_status[9]<=1;       // illegal E quadrature transition\n     if(sy[12])fault_status[10]<=1;  // E cable/FFC open observed\n    end\n"),
])
edit(R/'sim/tb/tb_capture_core.sv',[
 ("mz=0,da=0,db=0,dz=0,ext=0;","mz=0,da=0,db=0,dz=0,ext=0,ea=0,eb=0,eo=0;"),
 (".enc_d_a_async(da),.enc_d_b_async(db),.enc_d_z_async(dz),.external_fault_async(ext),",".enc_d_a_async(da),.enc_d_b_async(db),.enc_d_z_async(dz),.external_fault_async(ext),\n .enc_e_a_async(ea),.enc_e_b_async(eb),.enc_e_open_async(eo),"),
 ("   {da,db}={ma,mb};","   {da,db}={ma,mb};{ea,eb}={ma,mb};"),
])
edit(R/'sim/tb/tb_capture_overflow.sv',[
 (".enc_d_a_async(1'b0),.enc_d_b_async(1'b0),.enc_d_z_async(1'b0),.external_fault_async(1'b0),",".enc_d_a_async(1'b0),.enc_d_b_async(1'b0),.enc_d_z_async(1'b0),.external_fault_async(1'b0),\n .enc_e_a_async(1'b0),.enc_e_b_async(1'b0),.enc_e_open_async(1'b0),")])
(R/'sim/tb/tb_encoder_e.sv').write_text('''`timescale 1ns/1ps
// Channel E: (1) forward counts produce 0x22 records after the 0x22 start snapshot, (2) OPEN latches fault bit 10 and ends the session,
// (3) an illegal transition latches fault bit 9. Not run by this package's author (no HDL simulator); NOT_RUN until executed.
module tb_encoder_e;
 reg clk=0;always #5 clk=~clk;reg rst=1,start=0,stop=0,ea=0,eb=0,eo=0;
 wire[63:0]data,tick;wire[7:0]keep;wire valid,last,active,busy,laser;wire[31:0]fault,drops;
 zl80_capture_core #(.SAMPLE_DEPTH(8),.EVENT_DEPTH(8),.RECORDS_PER_PACKET(8),.SOS_TIMEOUT_TICKS(100000))dut(
 .clk(clk),.rst(rst),.start(start),.stop(stop),.session_id(32'd7),
 .pair_valid(1'b0),.pair_a(16'd0),.pair_b(16'd0),.pair_tick(64'd0),.pair_flags(16'd0),
 .sos_async(1'b0),.eos_async(1'b0),.polygon_index_async(1'b0),
 .enc_m_a_async(1'b0),.enc_m_b_async(1'b0),.enc_m_z_async(1'b0),
 .enc_d_a_async(1'b0),.enc_d_b_async(1'b0),.enc_d_z_async(1'b0),.external_fault_async(1'b0),
 .enc_e_a_async(ea),.enc_e_b_async(eb),.enc_e_open_async(eo),
 .m_axis_tdata(data),.m_axis_tkeep(keep),.m_axis_tvalid(valid),.m_axis_tlast(last),.m_axis_tready(1'b1),
 .capture_active(active),.busy(busy),.tick(tick),.fault_status(fault),.dropped_total(drops),.laser_request(laser));
 integer e_records=0,snap=0;reg half=0;reg[63:0]lo;reg[127:0]r;
 always @(posedge clk)if(!rst&&valid)begin
  if(!half)begin lo=data;half=1;end else begin
   r={data,lo};half=0;
   if(r[127:120]==8'h22)begin if(r[111:96]==16'h8000)snap=snap+1;else e_records=e_records+1;end
  end
 end
 task st(input [1:0] v);begin @(negedge clk);{ea,eb}=v;repeat(6)@(negedge clk);end endtask
 initial begin
  repeat(4)@(negedge clk);rst=0;start=1;@(negedge clk);start=0;wait(active);
  st(2'b01);st(2'b11);st(2'b10);st(2'b00);st(2'b01);st(2'b11);
  if(fault!=0)$fatal(1,"E forward counting must not fault");
  eo=1;repeat(8)@(negedge clk);
  if(!fault[10])$fatal(1,"E OPEN must latch fault bit 10");
  wait(!busy);@(negedge clk);
  if(snap!=1)$fatal(1,"missing 0x22 start snapshot");
  if(e_records<5)$fatal(1,"missing 0x22 count records");
  // second session: illegal transition 00 -> 11
  eo=0;rst=1;repeat(3)@(negedge clk);rst=0;start=1;@(negedge clk);start=0;wait(active);
  {ea,eb}=2'b00;repeat(8)@(negedge clk);{ea,eb}=2'b11;repeat(8)@(negedge clk);
  if(!fault[9])$fatal(1,"E illegal transition must latch fault bit 9");
  $display("PASS tb_encoder_e");$finish;
 end
 initial begin #200000;$fatal(1,"timeout");end
endmodule
''')
print('patched')
