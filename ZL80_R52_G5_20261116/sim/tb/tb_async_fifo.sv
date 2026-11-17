`timescale 1ns/1ps
module tb_async_fifo;
 reg wc=0,rc=0;always #7 wc=~wc;always #5 rc=~rc;
 reg wr=1,rr=1,we=0,re=0;reg[31:0]wd=0;wire full,empty;wire[31:0]rd;
 async_fifo_gray #(.WIDTH(32),.ADDR(3))dut(wc,wr,we,wd,full,rc,rr,re,rd,empty);
 integer sent=0,got=0,cycles=0;
 always @(negedge wc)if(!wr)begin
  we=(sent<100)&&!full;wd=sent;
 end
 always @(posedge wc)if(!wr && we&&!full)sent=sent+1;
 always @(negedge rc)if(!rr)begin cycles=cycles+1;re=(cycles%4!=0);end
 always @(posedge rc)if(!rr && re&&!empty)begin
  if(rd!==got)$fatal(1,"CDC FIFO ordering");got=got+1;
  if(got==100)begin $display("PASS tb_async_fifo");$finish;end
 end
 initial begin repeat(5)@(negedge wc);wr=0;repeat(3)@(negedge rc);rr=0;end
 initial begin #100000;$fatal(1,"timeout");end
endmodule
