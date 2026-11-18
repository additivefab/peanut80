`timescale 1ns/1ps
module tb_spi;
 reg clk=0;always #5 clk=~clk;reg rst=1,start=0,rd=0;
 reg[12:0]addr=13'h0d;reg[7:0]wd=8'h04;reg si=0;
 wire so,oe,sclk,cs,busy,done;wire[7:0]rdata;
 ad9268_spi_byte #(.HALF_PERIOD(5))dut(clk,rst,start,rd,addr,wd,si,so,oe,sclk,cs,busy,done,rdata);
 integer rises=0;reg[23:0]observed=0;reg[7:0]reply=8'h32;
 always @(negedge cs)begin rises=0;observed=0;end
 always @(posedge sclk)if(!cs)begin
  if(rises<16 || !rd)begin
   if(!oe)$fatal(1,"SPI missing drive");
   observed={observed[22:0],so};
  end else if(oe)$fatal(1,"readback contention");
  rises=rises+1;
 end
 always @(negedge sclk)if(!cs && rd && rises>=16 && rises<24)si=reply[23-rises];
 task launch;begin @(negedge clk);start=1;@(negedge clk);start=0;wait(done);#1;end endtask
 initial begin
  $dumpfile("tb_spi.vcd");$dumpvars(0,tb_spi);
  repeat(2)@(negedge clk);rst=0;
  launch();if(observed!==24'h000d04||rises!=24)$fatal(1,"SPI frame");
  @(negedge clk);rd=1;addr=1;
  launch();if(rdata!==8'h32||rises!=24)$fatal(1,"SPI readback");
  $display("PASS tb_spi");$finish;
 end
 initial begin #50000;$fatal(1,"timeout");end
endmodule
