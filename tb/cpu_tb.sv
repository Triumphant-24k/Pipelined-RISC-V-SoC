`timescale 1ns/1ps
module cpu_tb;
 parameter integer SEED=1,DELAY=3;
 reg clk=0,rst=1;always #5 clk=~clk;
 wire iv,dv,dw;reg ir,ip=0,dr,dp=0;wire [31:0] ia,da,wd;wire [3:0] ws;
 reg [31:0] insn,rd;wire retire_valid,trap_valid;wire [31:0] retire_pc,retire_insn,retire_value,trap_cause;
 wire [4:0] retire_rd;wire [63:0] cycles,instret;
 reg [31:0] mem[0:65535];
 reg [31:0] rng=SEED;
 reg ibusy=0,dbusy=0;integer iticks,dticks;reg [31:0] saved_ia,saved_da,saved_wd;
 reg saved_dw;reg [3:0] saved_ws;integer j,trace_fd,stores=0;
 string image,trace_path;
 rv32_pipeline cpu(.clk(clk),.rst(rst),.iv(iv),.ir(ir),.ia(ia),.ip(ip),.insn(insn),.ierr(1'b0),
 .dv(dv),.dr(dr),.dw(dw),.da(da),.wd(wd),.ws(ws),.dp(dp),.rd(rd),.derr(1'b0),
 .timer_irq(1'b0),.external_irq(1'b0),.retire_valid(retire_valid),.retire_pc(retire_pc),
 .retire_insn(retire_insn),.retire_value(retire_value),.retire_rd(retire_rd),.trap_valid(trap_valid),
 .trap_cause(trap_cause),.fence_i(),.cycles(cycles),.instret(instret));
 always @*begin ir=!rst&&!ibusy&&(!DELAY||rng[0]);dr=!rst&&!dbusy&&(!DELAY||rng[1]);end
 initial begin
  for(j=0;j<65536;j=j+1)mem[j]=0;
  if(!$value$plusargs("IMAGE=%s",image))image="build/cpu.hex";
  if(!$value$plusargs("TRACE=%s",trace_path))trace_path="build/trace.txt";
  $readmemh(image,mem);trace_fd=$fopen(trace_path,"w");
  repeat(4)@(negedge clk);rst=0;
 end
 always @(posedge clk)begin
  ip<=0;dp<=0;rng<={rng[30:0],rng[31]^rng[21]^rng[1]^rng[0]};
  if(!rst)begin
   if(iv&&ir)begin ibusy<=1;saved_ia<=ia;iticks<=DELAY?1+rng[4:2]%DELAY:0;end
   if(ibusy)begin
    if(iticks==0)begin ip<=1;insn<=mem[saved_ia[17:2]];ibusy<=0;end else iticks<=iticks-1;
   end
   if(dv&&dr)begin dbusy<=1;saved_da<=da;saved_dw<=dw;saved_wd<=wd;saved_ws<=ws;dticks<=DELAY?1+rng[7:5]%DELAY:0;end
   if(dbusy)begin
    if(dticks==0)begin
     dp<=1;rd<=mem[saved_da[17:2]];dbusy<=0;
     if(saved_dw)begin
      stores<=stores+1;
      if(saved_da==32'h40000000)begin
       if(saved_wd!=1)$fatal(1,"firmware failure code %h",saved_wd);
       $display("PASS CPU seed=%0d delay=%0d cycles=%0d retired=%0d stores=%0d",SEED,DELAY,cycles,instret,stores);
       $fclose(trace_fd);$finish;
      end
      for(j=0;j<4;j=j+1)if(saved_ws[j])mem[saved_da[17:2]][j*8+:8]<=saved_wd[j*8+:8];
     end
    end else dticks<=dticks-1;
   end
   if(retire_valid)$fdisplay(trace_fd,"%08h %08h %02h %08h",retire_pc,retire_insn,retire_rd,retire_value);
   if(trap_valid)$fdisplay(trace_fd,"TRAP %08h",trap_cause);
   if(cycles>200000)$fatal(1,"timeout pc=%h ex=%h mem=%h",ia,cpu.ex_pc,cpu.mem_pc);
  end
 end
endmodule
