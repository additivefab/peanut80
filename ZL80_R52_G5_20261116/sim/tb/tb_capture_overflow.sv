`timescale 1ns/1ps
module tb_capture_overflow;
 reg clk=0;always #5 clk=~clk;reg rst=1,start=0,pv=0,ready=1;
 wire[63:0]data,tick;wire[7:0]keep;wire valid,last,active,busy,laser;wire[31:0]fault,drops;
 zl80_capture_core #(.SAMPLE_DEPTH(4),.EVENT_DEPTH(4),.RECORDS_PER_PACKET(4),.SOS_TIMEOUT_TICKS(10000))dut(
 .clk(clk),.rst(rst),.start(start),.stop(1'b0),.session_id(32'd2),
 .pair_valid(pv),.pair_a(16'd123),.pair_b(16'd456),.pair_tick(tick),.pair_flags(16'd0),
 .sos_async(1'b0),.eos_async(1'b0),.polygon_index_async(1'b0),
 .enc_m_a_async(1'b0),.enc_m_b_async(1'b0),.enc_m_z_async(1'b0),
 .enc_d_a_async(1'b0),.enc_d_b_async(1'b0),.enc_d_z_async(1'b0),.external_fault_async(1'b0),
 .m_axis_tdata(data),.m_axis_tkeep(keep),.m_axis_tvalid(valid),.m_axis_tlast(last),.m_axis_tready(ready),
 .capture_active(active),.busy(busy),.tick(tick),.fault_status(fault),.dropped_total(drops),.laser_request(laser));
 integer endseen=0;reg half=0;reg[63:0]lo;reg[127:0]r;
 always @(posedge clk)if(!rst&&valid&&ready)begin
  if(!half)begin lo=data;half=1;end else begin
   r={data,lo};half=0;
   if(r[127:120]==8'h72 && r[31:0]==0)$fatal(1,"zero reported loss");
   if(r[127:120]==8'h7f)begin endseen=endseen+1;if(!last)$fatal(1,"END TLAST");end
  end
 end
 initial begin
  repeat(4)@(negedge clk);rst=0;start=1;@(negedge clk);start=0;wait(active);
  @(negedge clk);ready=0;pv=1;repeat(40)@(negedge clk);
  if(!fault[1]||drops==0||active)$fatal(1,"overflow must fault-stop");
  pv=0;ready=1;wait(!busy);@(negedge clk);
  if(endseen!=1)$fatal(1,"fault session not closed");
  $display("PASS tb_capture_overflow lost=%0d",drops);$finish;
 end
 initial begin #100000;$fatal(1,"timeout");end
endmodule
