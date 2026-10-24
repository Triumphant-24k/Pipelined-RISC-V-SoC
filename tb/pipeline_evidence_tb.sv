`timescale 1ns/1ps
// Directed, independently checked architectural results plus RTL hazard coverage.
module pipeline_evidence_tb;
 reg clk=0,rst=1; always #5 clk=~clk;
 wire iv,dv,dw,rv,tv; wire [31:0] ia,da,wd,rpc,ri,value,cause;
 wire [4:0] rrd; wire [3:0] ws; wire [63:0] cycles,instret;
 reg dp=0; reg [31:0] rd=0; reg busy=0; integer delay=0;
 reg [31:0] addr,data; reg write_en;reg [3:0] strobe;
 reg [31:0] imem[0:63],dmem[0:127],observed[0:31];
 integer i,j,forwarding=0,load_stalls=0,redirects=0,retired=0;
 reg [31:0] instruction;
 string wave;
 always @* instruction=imem[ia[7:2]];
 rv32_pipeline cpu(.clk(clk),.rst(rst),.iv(iv),.ir(1'b1),.ia(ia),.ip(iv),.insn(instruction),.ierr(1'b0),
 .dv(dv),.dr(!busy),.dw(dw),.da(da),.wd(wd),.ws(ws),.dp(dp),.rd(rd),.derr(1'b0),
 .timer_irq(1'b0),.external_irq(1'b0),.retire_valid(rv),.retire_pc(rpc),.retire_insn(ri),
 .retire_value(value),.retire_rd(rrd),.trap_valid(tv),.trap_cause(cause),.fence_i(),.cycles(cycles),.instret(instret));
 initial begin
  if(!$value$plusargs("WAVE=%s",wave))wave="build/evidence/pipeline.vcd";
  $dumpfile(wave);$dumpvars(0,pipeline_evidence_tb);
  for(i=0;i<64;i=i+1)imem[i]=32'h00000013;
  for(i=0;i<128;i=i+1)dmem[i]=0;
  for(i=0;i<32;i=i+1)observed[i]=0;
  $readmemh("build/evidence/hazards.hex",imem,0,15);
  repeat(4)@(negedge clk);rst=0;
 end
 always @(posedge clk)begin
  dp<=0;
  if(!rst)begin
   if(rv)begin
    retired=retired+1;
    $display("RETIRE pc=%08h insn=%08h rd=%0d value=%08h",rpc,ri,rrd,value);
    if(rrd!=0)observed[rrd]=value;
    if(rpc==32'h20||rpc==32'h28)$fatal(1,"wrong-path instruction retired");
   end
   if(tv)$fatal(1,"unexpected trap %h",cause);
`ifndef GATE_SIM
   if(cpu.ex_go&&cpu.mem_valid&&cpu.mem_regwrite&&cpu.mem_rd!=0&&
     (cpu.mem_rd==cpu.ex_rs1||cpu.mem_rd==cpu.ex_rs2))forwarding=forwarding+1;
   if(cpu.id_valid&&cpu.ex_load_hazard)load_stalls=load_stalls+1;
   if(cpu.ex_redirect)redirects=redirects+1;
`endif
   if(dv&&!busy)begin busy<=1;delay<=12;addr<=da;data<=wd;write_en<=dw;strobe<=ws;end
   if(busy)begin
    if(delay>0)delay<=delay-1;
    else begin
     busy<=0;dp<=1;rd<=dmem[addr[8:2]];
     if(write_en)begin
      if(addr==32'h40000000)begin
       if(data!=1||observed[1]!=7||observed[2]!=12||observed[3]!=12||observed[4]!=24||observed[6]!=0||observed[7]!=40||observed[8]!=40)
        $fatal(1,"architectural scoreboard mismatch");
`ifndef GATE_SIM
       if(forwarding==0||load_stalls==0||redirects<2)$fatal(1,"required hazard coverage missing");
`endif
       $display("PASS directed architectural scoreboard; wrong-path PCs excluded");
`ifndef GATE_SIM
       $display("COVER forwarding=%0d load_use_stall_cycles=%0d redirects=%0d",forwarding,load_stalls,redirects);
`endif
       $display("MEASURE cycles=%0d retired=%0d",cycles,retired);
       $finish;
      end
      for(j=0;j<4;j=j+1)if(strobe[j])dmem[addr[8:2]][j*8+:8]<=data[j*8+:8];
     end
    end
   end
   if(cycles>1000)$fatal(1,"directed test timeout");
  end
 end
endmodule
