`timescale 1ns/1ps
module cache_tb;
 reg clk=0,rst=1;always #5 clk=~clk;
 reg invalidate=0,req=0,write=0;reg [31:0] addr=0,wdata=0;reg [3:0] strobe=0;
 wire ready,response,error,mreq,mwrite;wire [31:0] rdata,maddr,mwdata;wire [3:0] mstrobe;
 reg mready,mresponse=0,merror=0;reg [31:0] mrdata;
 wire [63:0] hits,misses,traffic;
 reg [31:0] mem[0:32767];integer i,transactions=0,ticks;
 reg pending=0;reg [31:0] saved_addr,saved_data;reg [3:0] saved_strobe;reg saved_write;
 word_cache dut(.*);
 always @*mready=!rst&&!pending;
 always @(posedge clk)begin
  mresponse<=0;
  if(mreq&&mready)begin
   transactions<=transactions+1;pending<=1;ticks<=3;saved_addr<=maddr;saved_data<=mwdata;
   saved_write<=mwrite;saved_strobe<=mstrobe;
  end
  if(pending)begin
   if(ticks==0)begin
    pending<=0;mresponse<=1;mrdata<=mem[saved_addr>>2];merror<=saved_addr==32'h3000;
    if(saved_write&&saved_addr!=32'h3000)for(i=0;i<4;i=i+1)if(saved_strobe[i])mem[saved_addr>>2][8*i+:8]<=saved_data[8*i+:8];
   end else ticks<=ticks-1;
  end
 end
 task transact(input wr,input [31:0] a,d,input [3:0] s,input [31:0] expected,input err);
 begin
  @(negedge clk);wait(ready);req=1;write=wr;addr=a;wdata=d;strobe=s;
  @(negedge clk);req=0;wait(response);@(negedge clk);
  if(error!==err||(!wr&&!err&&rdata!==expected))$fatal(1,"cache mismatch addr=%h got=%h expected=%h err=%b",a,rdata,expected,error);
 end endtask
 initial begin
  for(i=0;i<32768;i=i+1)mem[i]=i;
  repeat(4)@(negedge clk);rst=0;
  transact(0,'h100,0,0,'h40,0);if(transactions!=4)$fatal(1,"refill traffic");
  transact(0,'h104,0,0,'h41,0);if(transactions!=4)$fatal(1,"hit went to memory");
  transact(1,'h104,'haabbccdd,4'b0101,0,0);
  transact(0,'h104,0,0,'h00bb00dd,0);if(transactions!=5)$fatal(1,"write hit did not update");
  transact(0,'h10000,0,0,'h4000,0);transact(0,'h10000,0,0,'h4000,0);
  if(transactions!=7)$fatal(1,"uncached traffic");
  transact(0,'h3000,0,0,0,1);transact(1,'h3000,123,15,0,1);
  @(negedge clk);invalidate=1;@(negedge clk);invalidate=0;
  transact(0,'h104,0,0,'h00bb00dd,0);if(transactions!=13)$fatal(1,"invalidate failed");
  @(negedge clk);wait(ready);req=1;write=0;addr='h200;
  @(negedge clk);req=0;wait(mreq&&mready);
  @(negedge clk);invalidate=1;@(negedge clk);invalidate=0;
  wait(response);@(negedge clk);if(rdata!='h80)$fatal(1,"invalidated refill response");
  transact(0,'h200,0,0,'h80,0);if(transactions!=21)$fatal(1,"invalidated refill installed a line");
  $display("PASS CACHE refill/hit/strobes/bypass/errors/invalidation traffic=%0d",traffic);$finish;
 end
 initial begin #100000;$fatal(1,"cache timeout");end
endmodule
