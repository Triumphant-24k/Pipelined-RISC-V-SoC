// SPDX-License-Identifier: MIT
// Round-robin arbitration; grant is held across request stalls and response wait.
module bus_arbiter #(parameter integer MASTERS=3)(input wire clk,rst,
 input wire [MASTERS-1:0] req,write,output reg [MASTERS-1:0] ready,response,error,
 input wire [MASTERS*32-1:0] addr,wdata,input wire [MASTERS*4-1:0] strobe,
 output reg [MASTERS*32-1:0] rdata,
 output wire mreq,input wire mready,output wire mwrite,output wire [31:0] maddr,mwdata,
 output wire [3:0] mstrobe,input wire mresponse,merror,input wire [31:0] mrdata);
 integer owner,next_owner,candidate,k;reg [1:0] state;reg found;
 assign mreq=state==1;assign mwrite=write[owner];
 assign maddr=addr[32*owner+:32];assign mwdata=wdata[32*owner+:32];assign mstrobe=strobe[4*owner+:4];
 always @*begin
  ready=0;response=0;error=0;rdata=0;
  if(state==1)ready[owner]=mready;
  if((state==2||(state==1&&mready))&&mresponse)begin
   response[owner]=1;error[owner]=merror;rdata[32*owner+:32]=mrdata;
  end
  found=0;candidate=0;
  for(k=0;k<MASTERS;k=k+1)if(!found&&req[(next_owner+k)%MASTERS])begin
   candidate=(next_owner+k)%MASTERS;found=1;
  end
 end
 always @(posedge clk)begin
  if(rst)begin state<=0;owner<=0;next_owner<=0;end
  else case(state)
   0:if(found)begin owner<=candidate;state<=1;end
   1:if(mready)begin state<=2;if(mresponse)begin state<=0;next_owner<=(owner+1)%MASTERS;end end
   2:if(mresponse)begin state<=0;next_owner<=(owner+1)%MASTERS;end
   default:state<=0;
  endcase
 end
endmodule
