`timescale 1ns/1ps
module tb_capture_core;
 reg clk=0;always #5 clk=~clk;reg rst=1,start=0,stop=0,pv=0;
 reg[15:0]a=0,b=0,flags=0;reg[63:0]pt=0;reg sos=0,eos=0,idx=0,ma=0,mb=0,mz=0,da=0,db=0,dz=0,ext=0,ea=0,eb=0,eo=0;
 reg ready=1;wire[63:0]data,tick;wire[7:0]keep;wire valid,last,active,busy,laser;
 wire[31:0]fault,drops;
 zl80_capture_core #(.SAMPLE_DEPTH(32),.EVENT_DEPTH(8),.RECORDS_PER_PACKET(16),.SOS_TIMEOUT_TICKS(5000))dut(
 .clk(clk),.rst(rst),.start(start),.stop(stop),.session_id(32'd1),
 .pair_valid(pv),.pair_a(a),.pair_b(b),.pair_tick(pt),.pair_flags(flags),
 .sos_async(sos),.eos_async(eos),.polygon_index_async(idx),
 .enc_m_a_async(ma),.enc_m_b_async(mb),.enc_m_z_async(mz),
 .enc_d_a_async(da),.enc_d_b_async(db),.enc_d_z_async(dz),.external_fault_async(ext),
 .enc_e_a_async(ea),.enc_e_b_async(eb),.enc_e_open_async(eo),
 .m_axis_tdata(data),.m_axis_tkeep(keep),.m_axis_tvalid(valid),.m_axis_tlast(last),.m_axis_tready(ready),
 .capture_active(active),.busy(busy),.tick(tick),.fault_status(fault),.dropped_total(drops),.laser_request(laser));
 integer n=0,sent=0,received=0,ends=0,fh;reg half=0;reg[63:0]lo;
 reg[127:0]record_word;reg stalled=0;reg[63:0]held;reg held_last;
 always @(posedge clk)if(!rst)begin
  if(laser!==0)$fatal(1,"laser must remain disabled");
  if(stalled&&(!valid||data!==held||last!==held_last))$fatal(1,"AXIS stalled data changed");
  stalled<=valid&&!ready;held<=data;held_last<=last;
  if(valid&&ready)begin
   $fwrite(fh,"%016h %02h %0d\n",data,keep,last);
   if(!half)begin lo=data;half=1;if(last)$fatal(1,"early TLAST");end
   else begin
    record_word={data,lo};half=0;
    if(record_word[127:120]==8'h01)begin
     if(record_word[15:0]!==received || record_word[31:16]!==(16'hffff-received))$fatal(1,"sample order/payload");
     received=received+1;
    end
    if(record_word[127:120]==8'h7f)begin ends=ends+1;if(!last)$fatal(1,"missing final TLAST");end
   end
  end
 end
 initial begin
  fh=$fopen("axis_capture.txt","w");$dumpfile("tb_capture_core.vcd");$dumpvars(0,tb_capture_core);
  repeat(4)@(negedge clk);rst=0;start=1;@(negedge clk);start=0;
  wait(active);
  for(n=0;n<500;n=n+1)begin
   @(negedge clk);
   ready=(n%17<13);pv=(n%5==0);
   if(pv)begin a=sent;b=16'hffff-sent;pt=tick;sent=sent+1;end
   sos=(n>=10&&n<16)||(n>=200&&n<206);
   eos=(n>=150&&n<156)||(n>=350&&n<356);
   {ma,mb}=(n<100)?2'b00:((n<200)?2'b01:((n<300)?2'b11:((n<400)?2'b10:2'b00)));
   {da,db}={ma,mb};{ea,eb}={ma,mb};
  end
  @(negedge clk);pv=0;stop=1;ready=1;@(negedge clk);stop=0;
  wait(!busy);@(negedge clk);
  if(fault!=0||drops!=0||sent!=received||ends!=1)$fatal(1,"normal capture evidence mismatch");
  $fclose(fh);$display("PASS tb_capture_core samples=%0d",received);$finish;
 end
 initial begin #200000;$fatal(1,"timeout");end
endmodule
