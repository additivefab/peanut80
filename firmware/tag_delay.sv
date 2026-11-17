// Reference only: synthesis/timing and ADC IO capture are NOT supplied.
// Acquisition metadata must follow ADC+digital latency; data already has ADC latency.
module tag_delay #(parameter int W=128, parameter int LATENCY=20) (
 input logic clk, rst, input logic [W-1:0] acquisition_tag,
 input logic acquisition_valid, output logic [W-1:0] aligned_tag,
 output logic aligned_valid);
 generate if (LATENCY==0) begin
  assign aligned_tag=acquisition_tag; assign aligned_valid=acquisition_valid;
 end else begin
  logic [W-1:0] tags[0:LATENCY-1]; logic [LATENCY-1:0] valid_q;
  integer i;
  always_ff @(posedge clk) begin
   if (rst) begin valid_q <= '0; for(i=0;i<LATENCY;i=i+1) tags[i]<='0; end
   else begin
    tags[0] <= acquisition_tag; valid_q[0] <= acquisition_valid;
    for(i=1;i<LATENCY;i=i+1) begin tags[i]<=tags[i-1];valid_q[i]<=valid_q[i-1];end
   end
  end
  assign aligned_tag=tags[LATENCY-1]; assign aligned_valid=valid_q[LATENCY-1];
 end endgenerate
endmodule
