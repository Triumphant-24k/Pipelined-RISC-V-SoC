module arbiter_harness(input wire clk);
 reg rst=1;always @(posedge clk)rst<=0;
 (* anyseq *)reg [2:0] req,write;
 (* anyseq *)reg [95:0] addr,wdata;
 (* anyseq *)reg [11:0] strobe;
 (* anyseq *)reg mready,mresponse,merror;
 (* anyseq *)reg [31:0] mrdata;
 wire [2:0] ready,response,error;wire [95:0] rdata;
 wire mreq,mwrite;wire [31:0] maddr,mwdata;wire [3:0] mstrobe;
 bus_arbiter dut(.clk(clk),.rst(rst),.req(req),.write(write),.addr(addr),.wdata(wdata),.strobe(strobe),
  .ready(ready),.response(response),.error(error),.rdata(rdata),.mreq(mreq),.mready(mready),.mwrite(mwrite),
  .maddr(maddr),.mwdata(mwdata),.mstrobe(mstrobe),.mresponse(mresponse),.merror(merror),.mrdata(mrdata));
 reg past_valid=0;integer i;
 always @(posedge clk)begin
  past_valid<=1;
  if(past_valid&&!rst)begin
   assert((ready&(ready-1))==0);
   assert((response&(response-1))==0);
   assert((error&~response)==0);
   if($past(mreq&&!mready))begin
    assert(mreq);assert(maddr==$past(maddr));assert(mwrite==$past(mwrite));
    assert(mwdata==$past(mwdata));assert(mstrobe==$past(mstrobe));
   end
   for(i=0;i<3;i=i+1)begin
    if($past(req[i]&&!ready[i]))begin
     assume(req[i]);assume(addr[32*i+:32]==$past(addr[32*i+:32]));
     assume(write[i]==$past(write[i]));assume(wdata[32*i+:32]==$past(wdata[32*i+:32]));
     assume(strobe[4*i+:4]==$past(strobe[4*i+:4]));
    end
   end
  end
 end
endmodule
