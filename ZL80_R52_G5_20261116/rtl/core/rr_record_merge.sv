`default_nettype none
// Registered round-robin merge. All sources and sink share clk.
module rr_record_merge #(parameter integer N=6,WIDTH=128)(
 input wire clk,input wire rst,input wire [N*WIDTH-1:0] s_data,
 input wire [N-1:0] s_valid,output reg [N-1:0] s_ready,
 output reg [WIDTH-1:0] m_data,output reg m_valid,input wire m_ready);
 integer rr,k,idx,chosen; reg found;
 always @* begin
  s_ready=0; chosen=0; found=0;
  if(!m_valid || m_ready) begin
   for(k=0;k<N;k=k+1) begin
    idx=rr+k; if(idx>=N) idx=idx-N;
    if(!found && s_valid[idx]) begin chosen=idx;found=1;end
   end
   if(found) s_ready[chosen]=1;
  end
 end
 always @(posedge clk) begin
  if(rst) begin rr<=0;m_data<=0;m_valid<=0;end
  else if(!m_valid || m_ready) begin
   m_valid<=found;
   if(found) begin
    m_data<=s_data[chosen*WIDTH+:WIDTH];
    if(chosen==N-1) rr<=0; else rr<=chosen+1;
   end
  end
 end
endmodule
`default_nettype wire
