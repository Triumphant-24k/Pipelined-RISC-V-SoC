`timescale 1ns/1ps
module axi_tb;
 reg clk=0,rst=1;always #5 clk=~clk;
 reg req=0,write=0;wire ready,response,error;reg [31:0] addr=0,wdata=0;reg [3:0] strobe=15;wire [31:0] rdata;
 wire awvalid,wvalid,bready,arvalid,rready;wire [31:0] awaddr,araddr,axi_wdata;wire [3:0] wstrb;
 reg awready=0,wready=0,bvalid=0,arready=0,rvalid=0;reg [1:0] bresp=0,rresp=0;reg [31:0] axi_rdata=0;
 axi_lite_adapter dut(.*);
 initial begin
  repeat(4)@(negedge clk);rst=0;
  req=1;write=1;addr='h100;wdata='h12345678;
  @(negedge clk);req=0;wready=1;
  @(negedge clk);wready=0;
  repeat(3)@(negedge clk);
  if(wvalid||!awvalid||bready||awaddr!='h100||axi_wdata!='h12345678)$fatal(1,"independent AW/W handling");
  awready=1;@(negedge clk);awready=0;
  bvalid=1;bresp=2;@(negedge clk);bvalid=0;
  if(!response||!error)$fatal(1,"write response error propagation");
  req=1;write=0;addr='h104;@(negedge clk);req=0;
  repeat(2)@(negedge clk);arready=1;@(negedge clk);arready=0;
  rvalid=1;axi_rdata='hfeed0123;@(negedge clk);rvalid=0;
  if(!response||error||rdata!='hfeed0123)$fatal(1,"read response");
  $display("PASS AXI independent AW/W stalls, read and write error response");$finish;
 end
 initial begin #100000;$fatal(1,"AXI timeout");end
endmodule
