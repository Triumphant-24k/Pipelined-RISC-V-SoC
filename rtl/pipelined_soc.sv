// SPDX-License-Identifier: MIT
// External memory port allows an SRAM wrapper or a latency/bandwidth simulation model.
module pipelined_soc #(parameter integer TILE=4,CACHE_LINES=16,CACHE_WORDS=4)(
 input wire clk,rst,output wire req,input wire ready,output wire write,
 output wire [31:0] addr,wdata,output wire [3:0] strobe,
 input wire response,input wire [31:0] rdata,input wire error,
 output reg exit_valid,output reg [31:0] exit_code,
 output wire [63:0] cpu_cycles,cpu_instret,
 output wire [63:0] ic_hits,ic_misses,dc_hits,dc_misses,
 output wire [63:0] acc_cycles,acc_mac_cycles,acc_reads,acc_writes
);
 wire iv,ir,ip,ie,dv,dr,dw,dp,de,fi;wire [31:0] ia,id,da,wd,rd;wire [3:0] ws;
 wire [2:0] br,bready,bwrite,bresponse,berror;wire [95:0] ba,bwd,brd;wire [11:0] bws;
 wire retire_valid,trap_valid;wire [31:0] retire_pc,retire_insn,retire_value,trap_cause;wire [4:0] retire_rd;
 wire acc_busy,acc_done,acc_fault,acc_irq;wire [31:0] cfg_read;
 wire xreq,xwrite,xready,xresponse,xerror;wire [31:0] xaddr,xwdata,xrdata;wire [3:0] xstrobe;
 reg io_response,io_error;reg [31:0] io_rdata;
 reg [63:0] mtime,mtimecmp;
 wire is_mem=xaddr<32'h40000;
 wire is_acc=xaddr[31:8]==24'h400000;
 wire is_timer=xaddr>=32'h40000100&&xaddr<=32'h40000114&&xaddr[1:0]==0;
 wire is_exit=xaddr==32'h40000200;
 wire io_accept=xreq&&!is_mem&&xready;
 wire io_legal=(is_acc||is_timer||is_exit)&&xaddr[1:0]==0&&(!xwrite||xstrobe==15);
 assign req=xreq&&is_mem;assign write=xwrite;assign addr=xaddr;assign wdata=xwdata;assign strobe=xstrobe;
 assign xready=is_mem?ready:!io_response;
 assign xresponse=response||io_response;assign xrdata=io_response?io_rdata:rdata;
 assign xerror=io_response?io_error:error;
 rv32_pipeline cpu(.clk(clk),.rst(rst),.iv(iv),.ir(ir),.ia(ia),.ip(ip),.insn(id),.ierr(ie),
  .dv(dv),.dr(dr),.dw(dw),.da(da),.wd(wd),.ws(ws),.dp(dp),.rd(rd),.derr(de),
  .timer_irq(mtime>=mtimecmp),.external_irq(acc_irq),.retire_valid(retire_valid),.retire_pc(retire_pc),
  .retire_insn(retire_insn),.retire_value(retire_value),.retire_rd(retire_rd),.trap_valid(trap_valid),
  .trap_cause(trap_cause),.fence_i(fi),.cycles(cpu_cycles),.instret(cpu_instret));
 word_cache #(.LINES(CACHE_LINES),.WORDS(CACHE_WORDS)) icache(.clk(clk),.rst(rst),.invalidate(fi),
  .req(iv),.ready(ir),.write(1'b0),.addr(ia),.wdata(32'd0),.strobe(4'd0),.response(ip),.rdata(id),.error(ie),
  .mreq(br[0]),.mready(bready[0]),.mwrite(bwrite[0]),.maddr(ba[31:0]),.mwdata(bwd[31:0]),.mstrobe(bws[3:0]),
  .mresponse(bresponse[0]),.mrdata(brd[31:0]),.merror(berror[0]),.hits(ic_hits),.misses(ic_misses),.traffic());
 word_cache #(.LINES(CACHE_LINES),.WORDS(CACHE_WORDS)) dcache(.clk(clk),.rst(rst),.invalidate(1'b0),
  .req(dv),.ready(dr),.write(dw),.addr(da),.wdata(wd),.strobe(ws),.response(dp),.rdata(rd),.error(de),
  .mreq(br[1]),.mready(bready[1]),.mwrite(bwrite[1]),.maddr(ba[63:32]),.mwdata(bwd[63:32]),.mstrobe(bws[7:4]),
  .mresponse(bresponse[1]),.mrdata(brd[63:32]),.merror(berror[1]),.hits(dc_hits),.misses(dc_misses),.traffic());
 matrix_dma #(.TILE(TILE)) accelerator(.clk(clk),.rst(rst),.cfg_write(io_accept&&is_acc&&xwrite&&io_legal),
  .cfg_addr(xaddr[7:0]),.cfg_data(xwdata),.cfg_read(cfg_read),
  .req(br[2]),.ready(bready[2]),.write(bwrite[2]),.addr(ba[95:64]),.wdata(bwd[95:64]),.strobe(bws[11:8]),
  .response(bresponse[2]),.rdata(brd[95:64]),.error(berror[2]),.busy(acc_busy),.done(acc_done),.fault(acc_fault),
  .irq(acc_irq),.elapsed(acc_cycles),.mac_cycles(acc_mac_cycles),.read_bytes(acc_reads),.write_bytes(acc_writes));
 bus_arbiter fabric(.clk(clk),.rst(rst),.req(br),.write(bwrite),.ready(bready),.response(bresponse),.error(berror),
  .addr(ba),.wdata(bwd),.strobe(bws),.rdata(brd),.mreq(xreq),.mready(xready),.mwrite(xwrite),.maddr(xaddr),
  .mwdata(xwdata),.mstrobe(xstrobe),.mresponse(xresponse),.mrdata(xrdata),.merror(xerror));
 always @(posedge clk)begin
  if(rst)begin io_response<=0;io_error<=0;mtime<=0;mtimecmp<=64'hffffffffffffffff;exit_valid<=0;exit_code<=0;end
  else begin
   mtime<=mtime+1;io_response<=0;exit_valid<=0;
   if(io_accept)begin
    io_response<=1;io_error<=!io_legal;io_rdata<=0;
    if(is_acc)io_rdata<=cfg_read;
    else case(xaddr)
     32'h40000100:io_rdata<=mtime[31:0];32'h40000104:io_rdata<=mtime[63:32];
     32'h40000110:begin io_rdata<=mtimecmp[31:0];if(xwrite&&io_legal)mtimecmp[31:0]<=xwdata;end
     32'h40000114:begin io_rdata<=mtimecmp[63:32];if(xwrite&&io_legal)mtimecmp[63:32]<=xwdata;end
     32'h40000200:if(xwrite&&io_legal)begin exit_valid<=1;exit_code<=xwdata;end
     default:begin end
    endcase
   end
  end
 end
endmodule
