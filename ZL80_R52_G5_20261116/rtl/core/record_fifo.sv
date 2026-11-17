`default_nettype none
// Portable single-clock FWFT FIFO, DEPTH must be a power of two >=2.
// No pretend BRAM inference: asynchronous read is intentional for review IP.
module record_fifo #(parameter integer WIDTH=128,DEPTH=32,AW=$clog2(DEPTH))(
 input wire clk,input wire rst,input wire clear_stats,
 input wire [WIDTH-1:0] s_data,input wire s_valid,output wire s_ready,
 output wire [WIDTH-1:0] m_data,output wire m_valid,input wire m_ready,
 output reg [31:0] dropped,output wire overflow);
 (* ram_style="distributed" *) reg [WIDTH-1:0] mem[0:DEPTH-1];
 reg [AW-1:0] wp,rp; reg [AW:0] count;
 wire pop=m_valid && m_ready; wire push=s_valid && s_ready;
 assign m_valid=(count!=0); assign m_data=mem[rp];
 assign s_ready=(count<DEPTH)||pop;
 assign overflow=s_valid && !s_ready;
 always @(posedge clk) begin
  if(rst) begin wp<=0;rp<=0;count<=0;dropped<=0;end
  else begin
   if(clear_stats) dropped<=0;
   else if(overflow && dropped!=32'hffffffff) dropped<=dropped+1'b1;
   if(push) begin mem[wp]<=s_data;wp<=wp+1'b1;end
   if(pop) rp<=rp+1'b1;
   case({push,pop}) 2'b10:count<=count+1'b1;2'b01:count<=count-1'b1;default:;endcase
  end
 end
endmodule
`default_nettype wire
