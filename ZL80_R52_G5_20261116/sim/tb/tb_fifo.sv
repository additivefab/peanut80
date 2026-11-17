`timescale 1ns/1ps
module tb_fifo;
 reg clk=0;always #5 clk=~clk;reg rst=1,clear_stats=0,sv=0,mr=0;
 reg[127:0]sd=0;wire sr,mv,ov;wire[127:0]md;wire[31:0]dropped;
 record_fifo #(.DEPTH(4))dut(clk,rst,clear_stats,sd,sv,sr,md,mv,mr,dropped,ov);
 task push(input integer x);begin @(negedge clk);sd=x;sv=1;@(posedge clk);#1;end endtask
 initial begin
  $dumpfile("tb_fifo.vcd");$dumpvars(0,tb_fifo);
  repeat(2)@(negedge clk);rst=0;
  push(1);push(2);push(3);push(4);
  @(negedge clk);sd=5;sv=1;
  @(posedge clk);#1;if(dropped!=1)$fatal(1,"overflow count");
  @(negedge clk);mr=1;sd=6;
  if(md!=1)$fatal(1,"FIFO head");
  @(posedge clk);#1;
  @(negedge clk);sv=0;
  if(md!=2)$fatal(1,"FIFO order2");
  @(posedge clk);#1; if(md!=3)$fatal(1,"FIFO order3");
  @(posedge clk);#1; if(md!=4)$fatal(1,"FIFO order4");
  @(posedge clk);#1; if(md!=6)$fatal(1,"simultaneous full pop/push");
  @(posedge clk);#1; if(mv)$fatal(1,"FIFO empty");
  $display("PASS tb_fifo");$finish;
 end
 initial begin #10000;$fatal(1,"timeout");end
endmodule
