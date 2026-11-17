`timescale 1ns/1ps
module tb_packetizer;
 reg clk=0;always #5 clk=~clk;reg rst=1,sv=0,ready=1;
 reg[127:0]sd=0;wire sr,v,last,idle;wire[63:0]data;wire[7:0]keep;
 record_to_axis64 #(.RECORDS_PER_PACKET(2))dut(clk,rst,sd,sv,sr,data,keep,v,last,ready,idle);
 integer beats=0,lasts=0;reg[63:0]held;reg heldlast;reg stalled=0;
 always @(posedge clk)if(!rst)begin
  if(stalled && (!v || data!==held || last!==heldlast))$fatal(1,"AXIS unstable under stall");
  stalled<=v&&!ready;held<=data;heldlast<=last;
  if(v&&ready)begin
   if(keep!=255)$fatal(1,"keep");
   if(last)begin
    if(beats!=3 && beats!=5)$fatal(1,"TLAST placement");
    lasts=lasts+1;
   end
   beats=beats+1;
  end
 end
 task send(input[7:0]typ,input integer payload);begin
  @(negedge clk);sd={typ,8'h01,16'd0,64'd100,32'(payload)};sv=1;
  @(posedge clk);while(!sr)@(posedge clk);
  @(negedge clk);sv=0;
 end endtask
 initial begin
  $dumpfile("tb_packetizer.vcd");$dumpvars(0,tb_packetizer);
  repeat(2)@(negedge clk);rst=0;
  send(8'h70,1);ready=0;repeat(8)@(negedge clk);ready=1;
  send(8'h01,123);send(8'h7f,1);
  wait(idle);@(negedge clk);
  if(beats!=6||lasts!=2)$fatal(1,"packet lengths");
  $display("PASS tb_packetizer");$finish;
 end
 initial begin #20000;$fatal(1,"timeout");end
endmodule
