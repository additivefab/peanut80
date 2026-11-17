`default_nettype none
// 128-bit record -> two 64-bit beats, low half first; stable under backpressure.
// TLAST at RECORDS_PER_PACKET, or on the END record (type 0x7f).
module record_to_axis64 #(parameter integer RECORDS_PER_PACKET=256)(
 input wire clk,input wire rst,input wire [127:0] s_data,input wire s_valid,
 output wire s_ready,output wire [63:0] m_axis_tdata,output wire [7:0] m_axis_tkeep,
 output wire m_axis_tvalid,output wire m_axis_tlast,input wire m_axis_tready,
 output wire idle);
 reg [127:0] hold;reg valid,high_half;integer rec_count;
 wire take=m_axis_tvalid && m_axis_tready;
 assign s_ready=!valid || (take && high_half);
 assign m_axis_tvalid=valid;assign m_axis_tkeep=8'hff;
 assign m_axis_tdata=high_half?hold[127:64]:hold[63:0];
 assign m_axis_tlast=valid && high_half &&
                   ((rec_count==RECORDS_PER_PACKET-1)||(hold[127:120]==8'h7f));
 assign idle=!valid;
 always @(posedge clk) begin
  if(rst) begin hold<=0;valid<=0;high_half<=0;rec_count<=0;end
  else begin
   if(take) begin
    if(high_half) begin
     valid<=0;high_half<=0;
     if(m_axis_tlast) rec_count<=0;else rec_count<=rec_count+1;
    end else high_half<=1;
   end
   if(s_valid && s_ready) begin hold<=s_data;valid<=1;high_half<=0;end
  end
 end
endmodule
`default_nettype wire
