`default_nettype none
// Captures one 16-bit CMOS lane on its own DCO. NOT a two-channel epoch solution.
module adc_cmos_lane #(parameter integer FIFO_ADDR=6)(
 input wire dco,input wire arst,input wire enable_async,input wire [15:0] data_in,
 input wire overrange_in,input wire clk,input wire pop,
 output wire [48:0] record_out,output wire valid,output reg overflow_sticky);
 wire wrst,rrst,en;wire full,empty;reg [31:0] seq;
 reset_release rw(.clk(dco),.arst(arst),.rst(wrst));
 reset_release rr(.clk(clk),.arst(arst),.rst(rrst));
 sync_bits se(.clk(dco),.rst(wrst),.async_in(enable_async),.sync_out(en));
 async_fifo_gray #(.WIDTH(49),.ADDR(FIFO_ADDR)) q(
  .wclk(dco),.wrst(wrst),.wen(en),.wdata({overrange_in,seq,data_in}),.full(full),
  .rclk(clk),.rrst(rrst),.ren(pop),.rdata(record_out),.empty(empty));
 assign valid=!empty;
 always @(posedge dco)begin
  if(wrst)begin seq<=0;overflow_sticky<=0;end
  else if(en)begin seq<=seq+1'b1;if(full||seq==32'hffffffff)overflow_sticky<=1;end
 end
endmodule
`default_nettype wire
