`default_nettype none
// Mode-0, MSB-first, one byte per CS frame: R/W,W1=0,W0=0,A[12:0],D[7:0].
// sdio_o/oe/i must connect to an approved voltage translator and IOBUF externally.
// No automatic register writes; shadow-register commit is the caller's duty.
module ad9268_spi_byte #(parameter integer HALF_PERIOD=50)(
 input wire clk,input wire rst,input wire start,input wire read_cmd,
 input wire [12:0] address,input wire [7:0] write_data,
 input wire sdio_i,output reg sdio_o,output reg sdio_oe,
 output reg sclk,output reg cs_n,output reg busy,output reg done,
 output reg [7:0] read_data);
 reg [23:0] word;reg rd;integer divider,bitno;
 always @(posedge clk) begin
  if(rst) begin word<=0;rd<=0;divider<=0;bitno<=23;sdio_o<=0;sdio_oe<=0;
   sclk<=0;cs_n<=1;busy<=0;done<=0;read_data<=0;end
  else begin
   done<=0;
   if(!busy)begin
    if(start)begin
     word<={read_cmd,2'b00,address,write_data};rd<=read_cmd;bitno<=23;
     sdio_o<=read_cmd;sdio_oe<=1;cs_n<=0;sclk<=0;
     divider<=HALF_PERIOD-1;read_data<=0;busy<=1;
    end
   end else if(divider!=0)divider<=divider-1;
   else begin
    divider<=HALF_PERIOD-1;
    if(!sclk)begin
     sclk<=1;
     if(rd && bitno<8)read_data<={read_data[6:0],sdio_i};
    end else begin
     sclk<=0;
     if(bitno==0)begin cs_n<=1;busy<=0;done<=1;sdio_oe<=0;end
     else begin
      bitno<=bitno-1;
      if(rd && bitno==8)sdio_oe<=0;
      if(!(rd && bitno<=8))sdio_o<=word[bitno-1];
     end
    end
   end
  end
 end
endmodule
`default_nettype wire
