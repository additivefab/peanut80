`default_nettype none
// Inputs must already be synchronized. 00->01->11->10->00 is positive.
// Index is an observation; it NEVER zeroes the running count.
module quad_decoder(input wire clk,input wire rst,input wire a,input wire b,
 input wire z,output reg signed [31:0] position,
 output reg signed [31:0] next_position,
 output wire changed,output wire index_rise,output reg illegal);
 reg [1:0] old_ab; reg old_z; wire [1:0] ab={a,b};
 assign changed=(ab!=old_ab); assign index_rise=z & ~old_z;
 always @* begin
  next_position=position; illegal=0;
  case({old_ab,ab})
   4'b0001,4'b0111,4'b1110,4'b1000:next_position=position+32'sd1;
   4'b0010,4'b1011,4'b1101,4'b0100:next_position=position-32'sd1;
   4'b0000,4'b0101,4'b1010,4'b1111: ;
   default:illegal=1;
  endcase
  // Finite 32-bit position range: stop rather than silently wrap long scans.
  if((position==32'sh7fffffff && next_position==32'sh80000000) ||
     (position==32'sh80000000 && next_position==32'sh7fffffff)) begin
    illegal=1;next_position=position;
  end
 end
 always @(posedge clk) begin
  if(rst) begin old_ab<=0;old_z<=0;position<=0;end
  else begin old_ab<=ab;old_z<=z;position<=next_position;end
 end
endmodule
`default_nettype wire
