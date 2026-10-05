// SPDX-License-Identifier: MIT
// Direct mapped multiword lines; write-through/no-write-allocate; one transaction.
module word_cache #(parameter integer LINES=16,WORDS=4,UNCACHED_BASE=65536)(
 input wire clk,rst,invalidate,
 input wire req,output wire ready,input wire write,input wire [31:0] addr,wdata,input wire [3:0] strobe,
 output reg response,output reg [31:0] rdata,output reg error,
 output wire mreq,input wire mready,output wire mwrite,output wire [31:0] maddr,mwdata,
 output wire [3:0] mstrobe,input wire mresponse,input wire [31:0] mrdata,input wire merror,
 output reg [63:0] hits,misses,traffic
);
 localparam LB=$clog2(LINES),WB=$clog2(WORDS),TAG=32-2-WB-LB;
 reg valid[0:LINES-1];reg [TAG-1:0] tags[0:LINES-1];reg [31:0] data[0:LINES-1][0:WORDS-1];
 reg [31:0] saved_addr,saved_wdata;reg [3:0] saved_strobe;reg saved_write,bypass;
 reg [2:0] state;reg [WB-1:0] refill;
 reg [31:0] requested_word;reg fill_killed;
 wire [LB-1:0] line=addr[2+WB+:LB],sline=saved_addr[2+WB+:LB];
 wire [WB-1:0] word_index=addr[2+:WB],sword=saved_addr[2+:WB];
 wire [TAG-1:0] tag=addr[31:2+WB+LB],stag=saved_addr[31:2+WB+LB];
 wire hit=valid[line]&&tags[line]==tag;
 assign ready=state==0&&!rst&&!invalidate;
 assign mreq=state==1||state==3;
 assign mwrite=state==1&&saved_write;
 assign maddr=state==1?saved_addr:{saved_addr[31:2+WB],refill,2'b00};
 assign mwdata=saved_wdata;assign mstrobe=mwrite?saved_strobe:0;
 wire complete=mresponse&&(state==2||state==4||((state==1||state==3)&&mready));
 integer i,j;
 always @(posedge clk)begin
  response<=0;error<=0;
  if(rst)begin state<=0;hits<=0;misses<=0;traffic<=0;fill_killed<=0;for(i=0;i<LINES;i=i+1)valid[i]<=0;end
  else begin
   if(invalidate)begin for(i=0;i<LINES;i=i+1)valid[i]<=0;fill_killed<=1;end
   if(req&&ready)begin
    saved_addr<=addr;saved_write<=write;saved_wdata<=wdata;saved_strobe<=strobe;
    bypass<=addr>=UNCACHED_BASE;fill_killed<=0;
    if(addr<UNCACHED_BASE&&hit&&!write)begin hits<=hits+1;rdata<=data[line][word_index];response<=1;end
    else if(write||addr>=UNCACHED_BASE)state<=1;
    else begin misses<=misses+1;refill<=0;valid[line]<=0;state<=3;end
   end
   if(mreq&&mready)begin traffic<=traffic+4;state<=state==1?2:4;end
   if(complete)begin
    if(merror)begin state<=0;response<=1;error<=1;valid[sline]<=0;end
    else if(state==1||state==2)begin
     state<=0;response<=1;rdata<=mrdata;
     if(saved_write&&!bypass&&valid[sline]&&tags[sline]==stag)
      for(j=0;j<4;j=j+1)if(saved_strobe[j])data[sline][sword][8*j+:8]<=saved_wdata[8*j+:8];
    end else begin
     data[sline][refill]<=mrdata;
     if(refill==sword)requested_word<=mrdata;
     if(refill==WORDS-1)begin
      tags[sline]<=stag;valid[sline]<=!fill_killed&&!invalidate;state<=0;response<=1;
      rdata<=refill==sword?mrdata:requested_word;
     end else begin refill<=refill+1'b1;state<=3;end
    end
   end
  end
 end
endmodule
