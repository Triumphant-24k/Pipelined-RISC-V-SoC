`timescale 1ns/1ps
module soc_tb;
 parameter integer TILE=4,PANEL_K=TILE,DELAY=3,CACHE_LINES=16;
 reg clk=0,rst=1;always #5 clk=~clk;
 wire req,write,exit_valid;wire [31:0] addr,wdata,exit_code;wire [3:0] strobe;
 reg ready,response=0,error=0;reg [31:0] rdata;reg pending=0;
 reg [31:0] saved_addr,saved_wdata;reg [3:0] saved_strobe;reg saved_write;
 reg [31:0] mem[0:65535];reg [31:0] rng=32'h428abcee;integer wait_cycles,i,transactions=0;
 wire [63:0] cpu_cycles,cpu_instret,ic_hits,ic_misses,dc_hits,dc_misses,acc_cycles,acc_mac_cycles,acc_reads,acc_writes;
 integer metrics_addr;string path;
 pipelined_soc #(.TILE(TILE),.PANEL_K(PANEL_K),.CACHE_LINES(CACHE_LINES)) dut(.*);
 always @*ready=!rst&&!pending&&(!DELAY||rng[0]);
 initial begin
  for(i=0;i<65536;i=i+1)mem[i]=0;
  if(!$value$plusargs("IMAGE=%s",path))path="build/soc.hex";
  $readmemh(path,mem);
  if(!$value$plusargs("METRICS=%h",metrics_addr))$fatal(1,"missing metrics address");
  repeat(4)@(negedge clk);rst=0;
 end
 always @(posedge clk)begin
  response<=0;rng<={rng[30:0],rng[31]^rng[21]^rng[1]^rng[0]};
  if(req&&ready)begin
   transactions<=transactions+1;pending<=1;saved_addr<=addr;saved_wdata<=wdata;saved_strobe<=strobe;saved_write<=write;
   wait_cycles<=DELAY?1+rng[6:2]%DELAY:0;
   if(addr>=262144)$fatal(1,"out of range memory");
  end
  if(pending)begin
   if(wait_cycles==0)begin
    pending<=0;response<=1;rdata<=mem[saved_addr[17:2]];
    if(saved_write)for(i=0;i<4;i=i+1)if(saved_strobe[i])mem[saved_addr[17:2]][8*i+:8]<=saved_wdata[8*i+:8];
   end else wait_cycles<=wait_cycles-1;
  end
  if(exit_valid)begin
   if(exit_code!=1)$fatal(1,"SoC firmware failure %0d mcause=%h pc=%h",exit_code,dut.cpu.mcause,dut.cpu.mepc);
   $display("PASS SOC tile=%0d delay=%0d cache_lines=%0d cycles=%0d instret=%0d transactions=%0d ihit=%0d imiss=%0d dhit=%0d dmiss=%0d",TILE,DELAY,CACHE_LINES,cpu_cycles,cpu_instret,transactions,ic_hits,ic_misses,dc_hits,dc_misses);
   if(metrics_addr!=0)for(i=0;i<12;i=i+1)$display("METRIC %0d %0d",i,mem[(metrics_addr>>2)+i]);
   $finish;
  end
  if(cpu_cycles>2000000)$fatal(1,"SoC timeout pc=%h mcause=%h pendingirq=%b",dut.ia,dut.cpu.mcause,dut.cpu.irq_pending);
 end
endmodule

