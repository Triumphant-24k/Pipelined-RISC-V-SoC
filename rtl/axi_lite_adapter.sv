// SPDX-License-Identifier: MIT
// Single outstanding 32-bit AXI4-Lite master. AW and W complete independently.
module axi_lite_adapter(input wire clk,rst,
 input wire req,output wire ready,input wire write,input wire [31:0] addr,wdata,input wire [3:0] strobe,
 output reg response,output reg [31:0] rdata,output reg error,
 output wire awvalid,input wire awready,output wire [31:0] awaddr,
 output wire wvalid,input wire wready,output wire [31:0] axi_wdata,output wire [3:0] wstrb,
 input wire bvalid,output wire bready,input wire [1:0] bresp,
 output wire arvalid,input wire arready,output wire [31:0] araddr,
 input wire rvalid,output wire rready,input wire [31:0] axi_rdata,input wire [1:0] rresp);
 reg busy,is_write,aw_done,w_done,ar_done;reg [31:0] saved_addr,saved_data;reg [3:0] saved_strobe;
 assign ready=!busy&&!rst;assign awvalid=busy&&is_write&&!aw_done;
 assign wvalid=busy&&is_write&&!w_done;assign arvalid=busy&&!is_write&&!ar_done;
 assign awaddr=saved_addr;assign araddr=saved_addr;assign axi_wdata=saved_data;assign wstrb=saved_strobe;
 assign bready=busy&&is_write&&aw_done&&w_done;assign rready=busy&&!is_write&&ar_done;
 always @(posedge clk)begin
  if(rst)begin busy<=0;response<=0;error<=0;aw_done<=0;w_done<=0;ar_done<=0;end
  else begin
   response<=0;
   if(req&&ready)begin busy<=1;is_write<=write;saved_addr<=addr;saved_data<=wdata;saved_strobe<=strobe;aw_done<=0;w_done<=0;ar_done<=0;end
   if(awvalid&&awready)aw_done<=1;
   if(wvalid&&wready)w_done<=1;
   if(arvalid&&arready)ar_done<=1;
   if(bvalid&&bready)begin busy<=0;response<=1;error<=bresp!=0;rdata<=0;end
   if(rvalid&&rready)begin busy<=0;response<=1;error<=rresp!=0;rdata<=axi_rdata;end
  end
 end
endmodule
