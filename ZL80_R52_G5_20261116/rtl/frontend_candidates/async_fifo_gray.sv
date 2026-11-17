`default_nettype none
// Candidate CDC primitive; no physical CDC/MTBF proof. Two-sided reset required.
// ADDR>=2. Gray buses require per-bit delay/skew constraints; see constraints/README.
module async_fifo_gray #(parameter integer WIDTH=49,ADDR=4)(
 input wire wclk,input wire wrst,input wire wen,input wire [WIDTH-1:0] wdata,
 output reg full,input wire rclk,input wire rrst,input wire ren,
 output wire [WIDTH-1:0] rdata,output reg empty);
 reg [WIDTH-1:0] mem[0:(1<<ADDR)-1];
 reg [ADDR:0] wbin,wgray,rbin,rgray;
 (* ASYNC_REG="TRUE" *)reg [ADDR:0] rg1,rg2,wg1,wg2;
 wire [ADDR:0] wnext=wbin+((wen&&!full)?1'b1:1'b0);
 wire [ADDR:0] rnext=rbin+((ren&&!empty)?1'b1:1'b0);
 wire [ADDR:0] wg_next=(wnext>>1)^wnext;
 wire [ADDR:0] rg_next=(rnext>>1)^rnext;
 assign rdata=mem[rbin[ADDR-1:0]];
 always @(posedge wclk)begin
  if(wrst)begin wbin<=0;wgray<=0;rg1<=0;rg2<=0;full<=0;end
  else begin
   rg1<=rgray;rg2<=rg1;
   if(wen&&!full)mem[wbin[ADDR-1:0]]<=wdata;
   wbin<=wnext;wgray<=wg_next;
   full<=(wg_next=={~rg2[ADDR:ADDR-1],rg2[ADDR-2:0]});
  end
 end
 always @(posedge rclk)begin
  if(rrst)begin rbin<=0;rgray<=0;wg1<=0;wg2<=0;empty<=1;end
  else begin
   wg1<=wgray;wg2<=wg1;rbin<=rnext;rgray<=rg_next;empty<=(rg_next==wg2);
  end
 end
endmodule
`default_nettype wire
