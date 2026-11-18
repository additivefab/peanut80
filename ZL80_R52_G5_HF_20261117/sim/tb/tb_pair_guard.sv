`timescale 1ns/1ps
module tb_pair_guard;
 reg clk=0;always #5 clk=~clk;reg rst=1,va=0,vb=0,verified=0,take=0;
 reg[48:0]la=0,lb=0;wire pa,pb,pv,err;wire[31:0]seq;wire[15:0]a,b,f;
 adc_pair_guard dut(clk,rst,la,lb,va,vb,verified,take,pa,pb,pv,seq,a,b,f,err);
 initial begin
  repeat(2)@(negedge clk);rst=0;la={1'b0,32'd4,16'd11};lb={1'b1,32'd4,16'd22};va=1;vb=1;
  #1;if(!pv||f[3]!=1||f[2]!=1||f[1]!=1)$fatal(1,"unverified flags");
  take=1;#1;if(!pa||!pb)$fatal(1,"pair pop");
  @(negedge clk);lb={1'b0,32'd5,16'd22};
  @(posedge clk);#1;if(!err||pv)$fatal(1,"mismatch must latch and halt");
  $display("PASS tb_pair_guard");$finish;
 end
endmodule
