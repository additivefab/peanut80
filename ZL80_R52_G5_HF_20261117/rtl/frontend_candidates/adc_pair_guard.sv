`default_nettype none
// Equal local counters do NOT prove common analog sample epoch.
// epoch_verified must come from approved B02 alignment tests, never a constant 1.
module adc_pair_guard(input wire clk,input wire rst,
 input wire [48:0] lane_a,input wire [48:0] lane_b,input wire va,input wire vb,
 input wire epoch_verified,input wire take,
 output wire pop_a,output wire pop_b,output wire pair_valid,
 output wire [31:0] sequence_out,output wire [15:0] a,output wire [15:0] b,
 output wire [15:0] flags,output reg mismatch_latched);
 wire equal=(lane_a[47:16]==lane_b[47:16]);
 assign pair_valid=va&&vb&&equal&&!mismatch_latched;
 assign pop_a=pair_valid&&take;assign pop_b=pop_a;
 assign sequence_out=lane_a[47:16];assign a=lane_a[15:0];assign b=lane_b[15:0];
 assign flags={12'd0,!epoch_verified,1'b1,lane_b[48],lane_a[48]};
 // bit2 TIME_UNCAL remains set: timestamp mapping is a separate closure task.
 always @(posedge clk)begin
  if(rst)mismatch_latched<=0;
  else if(va&&vb&&!equal)mismatch_latched<=1;
 end
endmodule
`default_nettype wire
