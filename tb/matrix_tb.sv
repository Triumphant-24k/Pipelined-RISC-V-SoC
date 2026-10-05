`timescale 1ns/1ps
module matrix_tb;
 parameter integer TILE=4,DELAY=3;
 reg clk=0,rst=1;always #5 clk=~clk;
 reg cfg_write=0;reg [7:0] cfg_addr=0;reg [31:0] cfg_data=0;wire [31:0] cfg_read;
 wire req,write,busy,done,fault,irq;wire [31:0] addr,wdata;wire [3:0] strobe;
 reg ready,response=0,error=0,inject_error=0;reg [31:0] rdata;
 reg pending=0;integer wait_cycles;reg [31:0] pending_addr,pending_data;
 reg pending_write;reg [31:0] rng=32'h671abc23;
 reg [7:0] mem[0:262143];
 integer m,n,k,sa,sb,sc,i,j,q,t,expected,actual,clocks=0,cases=0;
 wire [63:0] elapsed,mac_cycles,read_bytes,write_bytes;
 matrix_dma #(.TILE(TILE)) dut(.*);
 always @*ready=!rst&&!pending&&(!DELAY||rng[0]);
 always @(posedge clk)begin
  clocks<=clocks+1;response<=0;rng<={rng[30:0],rng[31]^rng[21]^rng[1]^rng[0]};
  if(rst)begin pending<=0;response<=0;error<=0;end
  else begin
  if(req&&ready)begin
   pending<=1;pending_addr<=addr;pending_data<=wdata;pending_write<=write;
   wait_cycles<=DELAY?1+rng[5:2]%DELAY:0;
   if(addr[1:0]!=0||addr>=262144)$fatal(1,"bad DMA address %h",addr);
  end
  if(pending)begin
   if(wait_cycles==0)begin
    pending<=0;response<=1;error<=inject_error;rdata<={mem[pending_addr+3],mem[pending_addr+2],mem[pending_addr+1],mem[pending_addr]};
    if(pending_write&&!inject_error)begin
     if(strobe!=15)$fatal(1,"bad store strobes");
     for(t=0;t<4;t=t+1)mem[pending_addr+t]<=pending_data[t*8+:8];
    end
   end else wait_cycles<=wait_cycles-1;
  end
  end
  if(clocks>1000000)$fatal(1,"matrix timeout");
 end
 task cfg(input [7:0] a,input [31:0] v);
 begin @(negedge clk);cfg_write=1;cfg_addr=a;cfg_data=v;@(negedge clk);cfg_write=0;end endtask
 initial begin
  for(i=0;i<262144;i=i+1)mem[i]=8'h55;
  repeat(4)@(negedge clk);rst=0;
  for(q=0;q<6;q=q+1)begin
   m=q==0?1:q+3;n=q==0?1:2*q+1;k=q==0?1:q*7+1;
   sa=k+3;sb=n+5;sc=4*(n+2);
   for(i=0;i<m;i=i+1)for(j=0;j<k;j=j+1)mem[65536+i*sa+j]=(i*57+j*23+q*79)%256;
   for(i=0;i<k;i=i+1)for(j=0;j<n;j=j+1)mem[81920+i*sb+j]=(i*33+j*47+q*11)%256;
   cfg('h10,65536);cfg('h14,81920);cfg('h18,98304);
   cfg('h1c,m);cfg('h20,n);cfg('h24,k);cfg('h28,sa);cfg('h2c,sb);cfg('h30,sc);cfg(0,3);
   wait(done);@(negedge clk);
   if(fault||!irq)$fatal(1,"matrix fault/IRQ");
   for(i=0;i<m;i=i+1)for(j=0;j<n;j=j+1)begin
    expected=0;
    for(t=0;t<k;t=t+1)expected=expected+$signed(mem[65536+i*sa+t])*$signed(mem[81920+t*sb+j]);
    actual={mem[98304+i*sc+4*j+3],mem[98304+i*sc+4*j+2],mem[98304+i*sc+4*j+1],mem[98304+i*sc+4*j]};
    if(actual!==expected)$fatal(1,"matrix mismatch %0d %0d %0d: got %0d expected %0d",q,i,j,actual,expected);
   end
   if(write_bytes!=4*m*n)$fatal(1,"write traffic mismatch");
   $display("PASS MATRIX tile=%0d delay=%0d shape=%0dx%0dx%0d cycles=%0d mac_cycles=%0d reads=%0d writes=%0d",TILE,DELAY,m,n,k,elapsed,mac_cycles,read_bytes,write_bytes);
   cases=cases+1;cfg(0,4);if(done||irq)$fatal(1,"ack failed");
  end
  cfg('h24,0);cfg(0,1);if(!done||!fault||busy)$fatal(1,"zero dimension not rejected");
  cfg('h1c,1);cfg('h20,1);cfg('h24,1);cfg('h28,1);cfg('h2c,1);cfg('h30,4);
  inject_error=1;cfg(0,1);wait(done);@(negedge clk);
  if(!fault||busy||write_bytes!=0)$fatal(1,"DMA error not contained");
  inject_error=0;
  // Reset during operand loading, array computation, and output transfer.
  for(q=0;q<3;q=q+1)begin
   mem[65536]=8'h80;mem[81920]=8'h80;
   cfg('h10,65536);cfg('h14,81920);cfg('h18,98304);
   cfg('h1c,1);cfg('h20,1);cfg('h24,1);cfg('h28,1);cfg('h2c,1);cfg('h30,4);cfg(0,1);
   if(q==0)wait(req&&!write);else if(q==1)wait(dut.compute_active);else wait(req&&write);
   @(negedge clk);rst=1;repeat(2)@(negedge clk);rst=0;
   if(busy||done||fault||irq)$fatal(1,"reset did not abort operation");
  end
  cfg('h10,65536);cfg('h14,81920);cfg('h18,98304);
  cfg('h1c,1);cfg('h20,1);cfg('h24,1);cfg('h28,1);cfg('h2c,1);cfg('h30,4);cfg(0,1);
  cfg('h10,0);cfg_addr='h10;if(cfg_read!=65536)$fatal(1,"busy config write accepted");
  wait(done);@(negedge clk);
  actual={mem[98307],mem[98306],mem[98305],mem[98304]};
  if(fault||actual!=16384)$fatal(1,"post-reset recovery failed");
  $display("PASS MATRIX %0d cases, invalid descriptor, DMA error, busy writes, three reset phases and recovery",cases);$finish;
 end
endmodule
