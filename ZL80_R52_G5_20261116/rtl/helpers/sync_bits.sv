`default_nettype none
// Independent single-bit controls only. NEVER use this to synchronize an ADC bus.
module sync_bits #(parameter integer WIDTH=1)(
 input wire clk, input wire rst, input wire [WIDTH-1:0] async_in,
 output wire [WIDTH-1:0] sync_out);
 (* ASYNC_REG="TRUE" *) reg [WIDTH-1:0] meta, synced;
 always @(posedge clk) begin
   if(rst) begin meta<=0; synced<=0; end
   else begin meta<=async_in; synced<=meta; end
 end
 assign sync_out=synced;
endmodule
`default_nettype wire
