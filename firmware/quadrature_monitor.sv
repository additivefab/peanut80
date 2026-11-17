// Asynchronous inputs require synchronizers. Illegal transition increments fault count.
module quadrature_monitor(input logic clk,rst,a,b,
 output logic signed [63:0] position, output logic [31:0] illegal_count);
 logic [1:0] a_sync,b_sync,prev;
 always_ff @(posedge clk) begin
  if(rst) begin a_sync<=0;b_sync<=0;prev<=0;position<=0;illegal_count<=0;end
  else begin
   a_sync<={a_sync[0],a};b_sync<={b_sync[0],b};prev<={a_sync[1],b_sync[1]};
   case({prev,a_sync[1],b_sync[1]})
    4'b0001,4'b0111,4'b1110,4'b1000: position<=position+1;
    4'b0100,4'b1101,4'b1011,4'b0010: position<=position-1;
    4'b0011,4'b1100,4'b0110,4'b1001: illegal_count<=illegal_count+1;
    default: begin end
   endcase
  end
 end
endmodule
