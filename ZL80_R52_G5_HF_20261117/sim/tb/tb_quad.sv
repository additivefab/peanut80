`timescale 1ns/1ps
module tb_quad;
 reg clk=0;always #5 clk=~clk;reg rst=1,a=0,b=0,z=0;
 wire signed[31:0]pos,npos;wire changed,idx,illegal;
 quad_decoder dut(clk,rst,a,b,z,pos,npos,changed,idx,illegal);
 task step(input[1:0]ab);begin @(negedge clk);{a,b}=ab;@(posedge clk);#1;end endtask
 initial begin
  repeat(2)@(negedge clk);rst=0;
  step(1);step(3);step(2);step(0);
  if(pos!=4)$fatal(1,"forward");
  step(2);step(3);step(1);step(0);
  if(pos!=0)$fatal(1,"reverse");
  step(1);@(negedge clk);z=1;
  @(posedge clk);#1;if(pos!=1)$fatal(1,"index must not zero");
  @(negedge clk);{a,b}=2'b10;#1;if(!illegal)$fatal(1,"invalid transition not flagged");
  @(posedge clk);#1;if(pos!=1)$fatal(1,"invalid transition changed count");
  $display("PASS tb_quad");$finish;
 end
endmodule
