`default_nettype none
// Single-clock FWFT record FIFO, DEPTH must be a power of two >=2 (adopted 2026-11-17 from the former BRAM variant).
// Synchronous read: the memory read register is the FIFO output word, so push-to-m_valid takes at least 2 cycles from empty.
// Depth >= 256 uses block RAM; shallower FIFOs use LUT RAM. Replaces the earlier asynchronous-read, LUT-RAM-only version.
module record_fifo #(parameter integer WIDTH=128,DEPTH=32,AW=$clog2(DEPTH))(
 input wire clk,input wire rst,input wire clear_stats,
 input wire [WIDTH-1:0] s_data,input wire s_valid,output wire s_ready,
 output wire [WIDTH-1:0] m_data,output wire m_valid,input wire m_ready,
 output reg [31:0] dropped,output wire overflow);
 reg [WIDTH-1:0] out_data;reg out_valid;
 reg [AW-1:0] wp,rp;reg [AW:0] mcount;
 wire [AW+1:0] total={1'b0,mcount}+out_valid;
 wire pop=out_valid && m_ready;wire push=s_valid && s_ready;
 wire load=(mcount!=0)&&(!out_valid||pop);
 assign m_data=out_data;assign m_valid=out_valid;
 assign s_ready=(total<DEPTH)||pop;assign overflow=s_valid && !s_ready;
 generate if(DEPTH>=256)begin:G_BLK
  (* ram_style="block" *) reg [WIDTH-1:0] mem[0:DEPTH-1];
  always @(posedge clk)begin if(push)mem[wp]<=s_data;if(load)out_data<=mem[rp];end
 end else begin:G_DST
  (* ram_style="distributed" *) reg [WIDTH-1:0] mem[0:DEPTH-1];
  always @(posedge clk)begin if(push)mem[wp]<=s_data;if(load)out_data<=mem[rp];end
 end endgenerate
 always @(posedge clk)begin
  if(rst)begin wp<=0;rp<=0;mcount<=0;out_valid<=0;dropped<=0;end
  else begin
   if(clear_stats)dropped<=0;else if(overflow&&dropped!=32'hffffffff)dropped<=dropped+1'b1;
   if(push)wp<=wp+1'b1;
   if(load)rp<=rp+1'b1;
   case({push,load})2'b10:mcount<=mcount+1'b1;2'b01:mcount<=mcount-1'b1;default:;endcase
   if(load)out_valid<=1'b1;else if(pop)out_valid<=1'b0;
  end
 end
endmodule
`default_nettype wire
