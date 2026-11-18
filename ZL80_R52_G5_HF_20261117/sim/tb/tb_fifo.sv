`timescale 1ns/1ps
// Self-checking bench for rtl/core/record_fifo.sv. Scoreboard model checks, every cycle:
//  data order and no loss, s_ready law (cnt<DEPTH || pop), overflow flag and dropped counter, m_valid/m_data hold while not accepted,
//  empty-to-valid latency <= 2 cycles. Directed: fill to DEPTH, overflow, drain, clear_stats, reset mid-run. Then random traffic at several valid/ready rates.
module fifo_check #(parameter integer DEPTH=4,SEED=1,CYCLES=20000)(input wire clk,output reg done,output reg fail);
 reg rst=1,clear_stats=0,sv=0,mr=0;reg [127:0] sd=0;wire sr,mv,ov;wire [127:0] md;wire [31:0] dropped;
 record_fifo #(.DEPTH(DEPTH)) dut(clk,rst,clear_stats,sd,sv,sr,md,mv,mr,dropped,ov);
 reg [127:0] q[0:DEPTH-1];integer cnt=0,rd=0,wr=0,drops=0,stall=0,errors=0,pops=0,pushes=0;reg [127:0] seq=1;
 reg held=0;reg [127:0] held_d=0;
 task err(input [255:0] m);begin errors=errors+1;if(errors<5)$display("ERR %0s depth=%0d t=%0t",m,DEPTH,$time);end endtask
 always @(posedge clk)begin
  if(rst)begin cnt=0;rd=0;wr=0;drops=0;stall=0;held=0;end
  else begin
   if(sr!==((cnt<DEPTH)||(mv&&mr)))err("s_ready law");
   if(ov!==(sv&&!sr))err("overflow flag");
   if(held&&(!mv||md!==held_d))err("output not held");
   if(mv&&!mr)begin held=1;held_d=md;end else held=0;
   if(mv&&mr)begin
    if(cnt==0)err("pop from empty");
    else begin if(md!==q[rd])err("data order/loss");rd=(rd+1)%DEPTH;cnt=cnt-1;pops=pops+1;end
   end
   if(sv&&sr)begin q[wr]=sd;wr=(wr+1)%DEPTH;cnt=cnt+1;pushes=pushes+1;end
   if(sv&&!sr)drops=drops+1;
   if(cnt>0&&!mv)begin stall=stall+1;if(stall>2)err("valid latency >2");end else stall=0;
   if(cnt>DEPTH)err("occupancy above DEPTH");
  end
 end
 integer i,s=SEED,fill,seen;
 task step(input v,input r);begin @(negedge clk);sv=v;mr=r;if(v)begin sd=seq;if(sr)seq=seq+1;end end endtask
 task push1;begin @(negedge clk);sv=1;sd=seq;mr=0;@(posedge clk);#1;if(sr)seq=seq+1;end endtask
 task random_run(input integer pv,input integer pr,input integer n);integer k;begin
  for(k=0;k<n;k=k+1)begin @(negedge clk);sv=(($urandom(s)%100)<pv);mr=(($urandom(s)%100)<pr);s=s+7;sd=seq;
   // seq advances only when the DUT accepts: decided at the following posedge
   @(posedge clk);#1;if(sv&&sr)seq=seq+1;end end endtask
 initial begin
  done=0;fail=0;repeat(3)@(negedge clk);rst=0;
  // 1 fill to DEPTH and one beyond
  for(i=0;i<DEPTH;i=i+1)push1;
  push1;push1;
  @(negedge clk);sv=0;repeat(4)@(posedge clk);#1;
  if(drops!==2)err("expected 2 drops");if(dropped!==2)err("dropped counter");
  @(negedge clk);clear_stats=1;@(negedge clk);clear_stats=0;@(posedge clk);#1;if(dropped!==0)err("clear_stats");
  // 2 drain fully
  @(negedge clk);mr=1;repeat(DEPTH+4)@(posedge clk);#1;if(cnt!==0)err("not drained");
  // 3 simultaneous push/pop at full
  @(negedge clk);mr=0;for(i=0;i<DEPTH;i=i+1)push1;
  @(negedge clk);mr=1;sv=1;sd=seq;@(posedge clk);#1;if(sr)seq=seq+1;
  @(negedge clk);sv=0;repeat(DEPTH+4)@(posedge clk);#1;if(cnt!==0)err("not drained after full push/pop");
  // 4 random traffic
  random_run(90,30,CYCLES/4);random_run(30,90,CYCLES/4);random_run(60,60,CYCLES/4);random_run(100,100,CYCLES/4);
  @(negedge clk);sv=0;mr=1;repeat(DEPTH+4)@(posedge clk);#1;if(cnt!==0)err("final drain");
  if(pushes<DEPTH*10||pops!==pushes)begin err("traffic counts");end
  // 5 reset mid-run
  @(negedge clk);mr=0;push1;push1;@(negedge clk);sv=0;rst=1;repeat(2)@(negedge clk);rst=0;@(negedge clk);
  if(mv!==0)err("valid after reset");
  push1;@(negedge clk);sv=0;mr=1;repeat(4)@(posedge clk);#1;if(cnt!==0)err("post-reset drain");
  fail=(errors!=0);done=1;
 end
endmodule
module tb_fifo;
 reg clk=0;always #5 clk=~clk;wire d4,f4,d8,f8,d256,f256,d32,f32;
 fifo_check #(.DEPTH(2),.SEED(11))   c2(clk,d4,f4);      // smallest legal depth
 fifo_check #(.DEPTH(4),.SEED(3))    c4(clk,d8,f8);
 fifo_check #(.DEPTH(32),.SEED(5))   c32(clk,d32,f32);    // event FIFO size (LUT RAM branch)
 fifo_check #(.DEPTH(256),.SEED(9))  c256(clk,d256,f256); // block-RAM branch threshold
 initial begin
  wait(d4&&d8&&d32&&d256);#20;
  if(f4||f8||f32||f256)$fatal(1,"FAIL tb_fifo");
  $display("PASS tb_fifo depths 2,4,32,256");$finish;
 end
 initial begin #50000000;$fatal(1,"timeout");end
endmodule
