`timescale 1ns/1ps
module kernel_tb;
 parameter integer PIPELINE=1,DELAY=5;
 reg clk=0,rst=1;always #5 clk=~clk;
 wire iv,dv,dw;wire [31:0] ia,da,wd;wire [3:0] ws;reg ir,dr,ip=0,dp=0;reg [31:0] id,rd;
 wire trap_valid;wire [31:0] trap_cause;wire [63:0] pc_cycles,pc_instret;
 reg [63:0] clocks=0;reg [31:0] mem[0:65535];reg [31:0] rng=32'h734defff;
 reg ibusy=0,dbusy=0;reg [31:0] saved_ia,saved_da,saved_wd;reg saved_dw;reg [3:0] saved_ws;
 integer iticks,dticks,i,metrics_addr;string image;
 generate if(PIPELINE)begin
  rv32_pipeline cpu(.clk(clk),.rst(rst),.iv(iv),.ir(ir),.ia(ia),.ip(ip),.insn(id),.ierr(1'b0),
   .dv(dv),.dr(dr),.dw(dw),.da(da),.wd(wd),.ws(ws),.dp(dp),.rd(rd),.derr(1'b0),
   .timer_irq(1'b0),.external_irq(1'b0),.retire_valid(),.retire_pc(),.retire_insn(),.retire_value(),.retire_rd(),
   .trap_valid(trap_valid),.trap_cause(trap_cause),.fence_i(),.cycles(pc_cycles),.instret(pc_instret));
 end else begin
  wire [3:0] cause;wire [31:0] trap_pc;
  cpu_core cpu(.clk(clk),.rst(rst),.instr_req_valid(iv),.instr_req_ready(ir),.instr_req_addr(ia),.instr_rsp_valid(ip),.instr_rsp_data(id),
   .data_req_valid(dv),.data_req_ready(dr),.data_req_write(dw),.data_req_addr(da),.data_req_wdata(wd),.data_req_wstrb(ws),
   .data_rsp_valid(dp),.data_rsp_rdata(rd),.trap_valid(trap_valid),.trap_cause(cause),.trap_pc(trap_pc));
  assign trap_cause={28'd0,cause};assign pc_cycles=clocks;assign pc_instret=0;
 end endgenerate
 always @*begin ir=!rst&&!ibusy&&(!DELAY||rng[0]);dr=!rst&&!dbusy&&(!DELAY||rng[1]);end
 initial begin
  for(i=0;i<65536;i=i+1)mem[i]=0;
  if(!$value$plusargs("IMAGE=%s",image)||!$value$plusargs("METRICS=%h",metrics_addr))$fatal(1,"missing image/metrics");
  $readmemh(image,mem);repeat(4)@(negedge clk);rst=0;
 end
 always @(posedge clk)begin
  ip<=0;dp<=0;rng<={rng[30:0],rng[31]^rng[21]^rng[1]^rng[0]};
  if(!rst)begin
   clocks<=clocks+1;
   if(iv&&ir)begin ibusy<=1;saved_ia<=ia;iticks<=DELAY?1+rng[5:2]%DELAY:0;end
   if(ibusy)begin
    if(iticks==0)begin ibusy<=0;ip<=1;id<=mem[saved_ia>>2];end else iticks<=iticks-1;
   end
   if(dv&&dr)begin
    dbusy<=1;saved_da<=da;saved_dw<=dw;saved_wd<=wd;saved_ws<=ws;dticks<=DELAY?1+rng[9:6]%DELAY:0;
    if(dw&&da==32'h40000000)begin
     if(wd!=1)$fatal(1,"kernel failure");
     $display("PASS KERNEL pipeline=%0d delay=%0d clocks=%0d kernel_cycles=%0d hash=%08h",PIPELINE,DELAY,clocks,mem[metrics_addr>>2],mem[(metrics_addr>>2)+1]);
     $finish;
    end
   end
   if(dbusy)begin
    if(dticks==0)begin
     dbusy<=0;dp<=1;rd<=saved_da==32'h40000100 ?clocks[31:0]:mem[saved_da>>2];
     if(saved_dw)for(i=0;i<4;i=i+1)if(saved_ws[i])mem[saved_da>>2][8*i+:8]<=saved_wd[8*i+:8];
    end else dticks<=dticks-1;
   end
   if(trap_valid)$fatal(1,"kernel trap %0d",trap_cause);
   if(clocks>2000000)$fatal(1,"kernel timeout");
  end
 end
endmodule

