`default_nettype none
// REVIEW IP: normalized, coherent two-channel frontend is REQUIRED.
// pair_tick MUST identify the aperture time in this core's shared tick epoch.
// This is NOT a board-level DCO/ADC adapter. No laser or motor actuation exists.
module zl80_capture_core #(
 parameter integer SAMPLE_DEPTH=1024,EVENT_DEPTH=32,RECORDS_PER_PACKET=256,
 parameter integer SOS_TIMEOUT_TICKS=2000000,PAIR_TIMEOUT_TICKS=1000)(
 input wire clk,input wire rst,input wire start,input wire stop,
 input wire [31:0] session_id,
 input wire pair_valid,input wire [15:0] pair_a,input wire [15:0] pair_b,
 input wire [63:0] pair_tick,input wire [15:0] pair_flags,
 input wire sos_async,input wire eos_async,input wire polygon_index_async,
 input wire enc_m_a_async,input wire enc_m_b_async,input wire enc_m_z_async,
 input wire enc_d_a_async,input wire enc_d_b_async,input wire enc_d_z_async,
 input wire external_fault_async,
 output wire [63:0] m_axis_tdata,output wire [7:0] m_axis_tkeep,
 output wire m_axis_tvalid,output wire m_axis_tlast,input wire m_axis_tready,
 output wire capture_active,output wire busy,output reg [63:0] tick,
 output reg [31:0] fault_status,output wire [31:0] dropped_total,
 output wire laser_request);
 localparam IDLE=0,HEADER=1,SNAP_M=2,SNAP_D=3,RUN=4,DRAIN=5,STATUS=6,LOSS=7,ENDREC=8,WAIT_TX=9;
 reg [3:0] state;
 reg [31:0] sid,line_no;reg [63:0] start_tick,end_tick;
 reg signed [31:0] start_m,start_d;
 reg [9:0] prev;wire [9:0] sy;
 sync_bits #(.WIDTH(10)) u_sync(.clk(clk),.rst(rst),
  .async_in({external_fault_async,enc_d_z_async,enc_d_b_async,enc_d_a_async,
             enc_m_z_async,enc_m_b_async,enc_m_a_async,polygon_index_async,eos_async,sos_async}),
  .sync_out(sy));
 wire sos_up=sy[0] & ~prev[0],sos_dn=~sy[0] & prev[0];
 wire eos_up=sy[1] & ~prev[1],eos_dn=~sy[1] & prev[1];
 wire idx_up=sy[2] & ~prev[2];
 wire signed [31:0] pm,npm,pd,npd;wire cm,zm,im,cd,zd,id;
 quad_decoder u_m(.clk(clk),.rst(rst),.a(sy[3]),.b(sy[4]),.z(sy[5]),
  .position(pm),.next_position(npm),.changed(cm),.index_rise(zm),.illegal(im));
 quad_decoder u_d(.clk(clk),.rst(rst),.a(sy[6]),.b(sy[7]),.z(sy[8]),
  .position(pd),.next_position(npd),.changed(cd),.index_rise(zd),.illegal(id));
 reg stop_pending;reg seen_sos,wait_eos,seen_pair;reg [31:0] silence,pair_silence;reg [63:0] last_pair_tick;
 wire collect=(state==RUN)&&!stop&&!stop_pending&&(fault_status==0);
 wire collect_events=((state==HEADER)||(state==SNAP_M)||(state==SNAP_D)||(state==RUN))
                     && !stop && !stop_pending && (fault_status==0);
 assign capture_active=collect;assign busy=(state!=IDLE);assign laser_request=1'b0;
 function [127:0] rec;
  input [7:0] typ;input [15:0] flags;input [63:0] ts;input [31:0] payload;
  begin rec={typ,8'h01,flags,ts,payload};end
 endfunction
 wire [5:0] sv,sr,fv,fr,ov;wire [767:0] sd,fd;
 wire [31:0] drops[0:5];reg [63:0] sum_drops;integer di;
 always @* begin sum_drops=0;for(di=0;di<6;di=di+1)sum_drops=sum_drops+drops[di];end
 assign dropped_total=(sum_drops>64'hffffffff)?32'hffffffff:sum_drops[31:0];
 assign sv[0]=collect&&pair_valid;
 assign sd[0+:128]=rec(8'h01,pair_flags,pair_tick,{pair_b,pair_a});
 assign sv[1]=collect_events&&(sos_up||sos_dn);
 assign sd[128+:128]=rec(sos_up?8'h10:8'h11,16'd0,tick,sos_up?line_no+1'b1:line_no);
 assign sv[2]=collect_events&&(eos_up||eos_dn);
 assign sd[256+:128]=rec(eos_up?8'h12:8'h13,16'd0,tick,line_no);
 assign sv[3]=collect_events&&(cm||zm);
 assign sd[384+:128]=rec(8'h20,{13'd0,im,zm,cm},tick,npm);
 assign sv[4]=collect_events&&(cd||zd);
 assign sd[512+:128]=rec(8'h21,{13'd0,id,zd,cd},tick,npd);
 assign sv[5]=collect_events&&idx_up;
 assign sd[640+:128]=rec(8'h30,16'd0,tick,line_no);
 genvar g;
 generate for(g=0;g<6;g=g+1)begin:Q
  record_fifo #(.DEPTH((g==0)?SAMPLE_DEPTH:EVENT_DEPTH)) u_q(
   .clk(clk),.rst(rst),.clear_stats((state==IDLE)&&start),
   .s_data(sd[g*128+:128]),.s_valid(sv[g]),.s_ready(sr[g]),
   .m_data(fd[g*128+:128]),.m_valid(fv[g]),.m_ready(fr[g]),
   .dropped(drops[g]),.overflow(ov[g]));
 end endgenerate
 wire [127:0] merged;wire mv,mr;
 rr_record_merge u_merge(.clk(clk),.rst(rst),.s_data(fd),.s_valid(fv),.s_ready(fr),
  .m_data(merged),.m_valid(mv),.m_ready(mr));
 reg [127:0] pout;reg pv;wire pr,packet_idle;
 assign mr=pr&&((state==RUN)||(state==DRAIN));
 always @* begin
  pout=0;pv=0;
  case(state)
   HEADER:begin pout=rec(8'h70,16'd0,start_tick,sid);pv=1;end
   SNAP_M:begin pout=rec(8'h20,16'h8000,start_tick,start_m);pv=1;end
   SNAP_D:begin pout=rec(8'h21,16'h8000,start_tick,start_d);pv=1;end
   RUN,DRAIN:begin pout=merged;pv=mv;end
   STATUS:begin pout=rec(8'h71,16'd0,end_tick,fault_status);pv=1;end
   LOSS:begin pout=rec(8'h72,16'd0,end_tick,dropped_total);pv=1;end
   ENDREC:begin pout=rec(8'h7f,16'd0,end_tick,sid);pv=1;end
   default:;
  endcase
 end
 record_to_axis64 #(.RECORDS_PER_PACKET(RECORDS_PER_PACKET)) u_packet(
  .clk(clk),.rst(rst),.s_data(pout),.s_valid(pv),.s_ready(pr),
  .m_axis_tdata(m_axis_tdata),.m_axis_tkeep(m_axis_tkeep),
  .m_axis_tvalid(m_axis_tvalid),.m_axis_tlast(m_axis_tlast),
  .m_axis_tready(m_axis_tready),.idle(packet_idle));
 always @(posedge clk) begin
  if(rst) begin
   state<=IDLE;tick<=0;prev<=0;sid<=0;start_tick<=0;end_tick<=0;
   start_m<=0;start_d<=0;line_no<=0;fault_status<=0;
   stop_pending<=0;seen_sos<=0;wait_eos<=0;silence<=0;pair_silence<=0;seen_pair<=0;last_pair_tick<=0;
  end else begin
   tick<=tick+1'b1;prev<=sy;
   if(busy && stop)stop_pending<=1;
   if(collect_events)begin
    if(sy[9])fault_status[0]<=1;
    if(|ov)fault_status[1]<=1;
    if(im)fault_status[2]<=1;
    if(id)fault_status[3]<=1;
    if(sos_up)begin
     line_no<=line_no+1'b1;seen_sos<=1;wait_eos<=1;silence<=0;
     if(seen_sos&&wait_eos)fault_status[4]<=1;
    end else if(state==RUN)begin
     if(silence<SOS_TIMEOUT_TICKS)silence<=silence+1'b1;
     else fault_status[5]<=1;
    end
    if(eos_up&&seen_sos)begin
     if(!wait_eos)fault_status[4]<=1;
     wait_eos<=0;
    end
   end
   case(state)
    IDLE:if(start)begin
     sid<=session_id;start_tick<=tick;start_m<=npm;start_d<=npd;stop_pending<=0;
     fault_status<=0;line_no<=0;seen_sos<=0;wait_eos<=0;
     silence<=0;pair_silence<=0;seen_pair<=0;state<=HEADER;
    end
    HEADER:if(pr)state<=SNAP_M;
    SNAP_M:if(pr)state<=SNAP_D;
    SNAP_D:if(pr)state<=RUN;
    RUN:begin
     if(stop || stop_pending || (fault_status!=0)) begin state<=DRAIN;end_tick<=tick;end
     if(collect) begin
      if(pair_valid)begin
       pair_silence<=0;
       if(pair_flags[5])fault_status[6]<=1;
       if(pair_tick>tick || (seen_pair&&pair_tick<=last_pair_tick))fault_status[7]<=1;
       last_pair_tick<=pair_tick;seen_pair<=1;
      end else if(pair_silence<PAIR_TIMEOUT_TICKS)pair_silence<=pair_silence+1'b1;
      else fault_status[8]<=1;
     end
    end
    DRAIN:if((fv==0)&&!mv)state<=STATUS;
    STATUS:if(pr)state<=LOSS;
    LOSS:if(pr)state<=ENDREC;
    ENDREC:if(pr)state<=WAIT_TX;
    WAIT_TX:if(packet_idle)state<=IDLE;
    default:state<=IDLE;
   endcase
  end
 end
endmodule
`default_nettype wire
