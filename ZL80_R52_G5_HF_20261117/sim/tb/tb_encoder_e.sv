`timescale 1ns/1ps
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
  eo=0;{ea,eb}=2'b00;rst=1;repeat(3)@(negedge clk);rst=0;start=1;@(negedge clk);start=0;wait(active);
  {ea,eb}=2'b00;repeat(8)@(negedge clk);{ea,eb}=2'b11;repeat(8)@(negedge clk);
  if(!fault[9])$fatal(1,"E illegal transition must latch fault bit 9");
  $display("PASS tb_encoder_e");$finish;
 end
 initial begin #200000;$fatal(1,"timeout");end
endmodule
