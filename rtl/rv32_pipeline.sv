// SPDX-License-Identifier: MIT
// Five-stage elastic RV32IM/Zicsr/Zifencei, single outstanding fetch/data request.
module rv32_pipeline(
 input wire clk,rst,
 output wire iv,input wire ir,output wire [31:0] ia,
 input wire ip,input wire [31:0] insn,input wire ierr,
 output wire dv,input wire dr,output wire dw,output wire [31:0] da,wd,
 output wire [3:0] ws,input wire dp,input wire [31:0] rd,input wire derr,
 input wire timer_irq,external_irq,
 output reg retire_valid,output reg [31:0] retire_pc,retire_insn,retire_value,
 output reg [4:0] retire_rd,output reg trap_valid,output reg [31:0] trap_cause,
 output reg fence_i,output reg [63:0] cycles,instret
);
 reg [31:0] regs[0:31];
 reg [31:0] fetch_pc,fetch_addr;
 reg fetch_pending,fetch_queued,fetch_killed;
 reg id_valid,ex_valid,mem_valid,wb_valid;
 reg [31:0] id_pc,id_insn,ex_pc,ex_insn,ex_a,ex_b;
 reg id_error,ex_error;
 reg [31:0] mem_pc,mem_insn,mem_result,mem_addr,mem_store,mem_cause,mem_tval;
 reg [4:0] mem_rd,wb_rd;
 reg [31:0] wb_value;
 reg mem_write,mem_load,mem_regwrite,mem_trap,mem_sent;
 reg [2:0] mem_size;
 reg [3:0] mem_strobe;
 reg mem_csrwrite,mem_mret,mem_fencei;
 reg [11:0] mem_csraddr;
 reg [31:0] mem_csrvalue;
 reg [31:0] mstatus,mie,mtvec,mscratch,mepc,mcause,mtval;
 reg [63:0] fetch_wait_cycles,data_wait_cycles,execute_wait_cycles,redirects;
 wire [31:0] mip={20'd0,external_irq,3'd0,timer_irq,7'd0};
 wire irq_pending=mstatus[3] && ((mie&mip)!=0);
 wire [31:0] irq_cause=(mie[11]&&external_irq)?32'h8000000b:32'h80000007;
 wire mem_done=mem_valid && (!(mem_load||mem_write) || (dp&&(mem_sent||(dv&&dr))));
 wire mem_fault=mem_valid&&(mem_trap || ((mem_load||mem_write)&&derr&&dp));
 wire [31:0] load_shift=rd >> (8*mem_addr[1:0]);
 wire [31:0] load_value=mem_size==0?{{24{load_shift[7]}},load_shift[7:0]}:
   mem_size==1?{{16{load_shift[15]}},load_shift[15:0]}:
   mem_size==4?{24'd0,load_shift[7:0]}:mem_size==5?{16'd0,load_shift[15:0]}:rd;
 wire [31:0] mem_value=mem_load?load_value:mem_result;
 wire serial_ex=ex_insn[6:0]==7'h73 || ex_insn[6:0]==7'h0f;
 wire is_m=ex_insn[6:0]==7'h33&&ex_insn[31:25]==1;
 wire md_busy,md_done;
 wire [31:0] md_result;
 wire ex_go=ex_valid && (!mem_valid||mem_done) && !(mem_done&&mem_fault) && !(serial_ex&&mem_valid) && (!is_m||md_done);
 rv32_muldiv md(.clk(clk),.rst(rst||(mem_done&&mem_fault)),
  .start(ex_valid&&is_m&&!md_busy&&!md_done&&(!mem_valid||mem_done)&&!mem_fault),.consume(ex_go&&is_m),
  .op(ex_insn[14:12]),.a(a),.b(b),.busy(md_busy),.done(md_done),.result(md_result));
 wire [4:0] ex_rs1=ex_insn[19:15],ex_rs2=ex_insn[24:20];
 wire [31:0] a=(mem_valid&&mem_regwrite&&!mem_fault&&mem_rd!=0&&mem_rd==ex_rs1&&(!mem_load||mem_done))?mem_value:
   (wb_valid&&wb_rd!=0&&wb_rd==ex_rs1)?wb_value:ex_a;
 wire [31:0] b=(mem_valid&&mem_regwrite&&!mem_fault&&mem_rd!=0&&mem_rd==ex_rs2&&(!mem_load||mem_done))?mem_value:
   (wb_valid&&wb_rd!=0&&wb_rd==ex_rs2)?wb_value:ex_b;
 reg [31:0] result,address,store_data,next_pc,tval,csr_old,csr_new;
 reg [31:0] cause;
 reg regwrite,isload,isstore,illegal,taken,exception,csrwrite,is_mret,is_fencei,csr_ok;
 reg [3:0] strobes;
 wire [2:0] f3=ex_insn[14:12];
 wire [6:0] op=ex_insn[6:0],f7=ex_insn[31:25];
 wire [31:0] ii={{20{ex_insn[31]}},ex_insn[31:20]};
 wire [31:0] si={{20{ex_insn[31]}},ex_insn[31:25],ex_insn[11:7]};
 wire [31:0] bi={{19{ex_insn[31]}},ex_insn[31],ex_insn[7],ex_insn[30:25],ex_insn[11:8],1'b0};
 wire [31:0] ji={{11{ex_insn[31]}},ex_insn[31],ex_insn[19:12],ex_insn[20],ex_insn[30:21],1'b0};
 reg [31:0] operand,csr_operand;
 always @* begin
   csr_ok=1; csr_old=0;
   case(ex_insn[31:20])
    12'h300:csr_old=mstatus;12'h301:csr_old=32'h40001100;
    12'h304:csr_old=mie;12'h305:csr_old=mtvec;12'h340:csr_old=mscratch;
    12'h341:csr_old=mepc;12'h342:csr_old=mcause;12'h343:csr_old=mtval;12'h344:csr_old=mip;
    12'hb00,12'hc00:csr_old=cycles[31:0];12'hb80,12'hc80:csr_old=cycles[63:32];
    12'hb02,12'hc02:csr_old=instret[31:0];12'hb82,12'hc82:csr_old=instret[63:32];
    12'hf11,12'hf12,12'hf13,12'hf14:csr_old=0;
    12'hfc0:csr_old=fetch_wait_cycles[31:0];12'hfc1:csr_old=data_wait_cycles[31:0];
    12'hfc2:csr_old=execute_wait_cycles[31:0];12'hfc3:csr_old=redirects[31:0];
    default:csr_ok=0;
   endcase
   result=0;address=0;store_data=0;next_pc=ex_pc+4;tval=ex_insn;cause=2;
   regwrite=0;isload=0;isstore=0;illegal=0;taken=0;exception=0;csrwrite=0;
   is_mret=0;is_fencei=0;strobes=0;operand=op==7'h13 ?ii:b;csr_new=csr_old;
   csr_operand=f3[2]?{27'd0,ex_rs1}:a;
   case(op)
    7'h37:begin result={ex_insn[31:12],12'd0};regwrite=1;end
    7'h17:begin result=ex_pc+{ex_insn[31:12],12'd0};regwrite=1;end
    7'h6f:begin result=ex_pc+4;regwrite=1;taken=1;next_pc=ex_pc+ji;end
    7'h67:begin result=ex_pc+4;regwrite=1;taken=1;next_pc=(a+ii)&32'hfffffffe;illegal=f3!=0;end
    7'h63:begin
      case(f3)
       0:taken=a==b;1:taken=a!=b;4:taken=$signed(a)<$signed(b);
       5:taken=$signed(a)>=$signed(b);6:taken=a<b;7:taken=a>=b;default:illegal=1;
      endcase
      next_pc=ex_pc+bi;
    end
    7'h13,7'h33:begin
     regwrite=1;
     if(op==7'h33&&f7==1) begin
      result=md_result;
     end else begin
      case(f3)
       0:begin result=(op==7'h33&&f7==32)?a-b:a+operand;if(op==7'h33&&f7!=0&&f7!=32)illegal=1;end
       1:begin result=a<<operand[4:0];if(f7!=0)illegal=1;end
       2:result={31'd0,$signed(a)<$signed(operand)};
       3:result={31'd0,a<operand};4:result=a^operand;
       5:begin if(f7==32)result=$signed(a)>>>operand[4:0];else result=a>>operand[4:0];if(f7!=0&&f7!=32)illegal=1;end
       6:result=a|operand;7:result=a&operand;
      endcase
      if(op==7'h33&&f3!=0&&f3!=5&&f7!=0)illegal=1;
     end
    end
    7'h03,7'h23:begin
     isload=op==7'h03;isstore=op==7'h23;regwrite=isload;address=a+(isload?ii:si);
     illegal=isload?!(f3==0||f3==1||f3==2||f3==4||f3==5):f3>2;
     strobes=f3==0?4'b0001<<address[1:0]:f3==1?4'b0011<<address[1:0]:4'b1111;
     store_data=b<<(8*address[1:0]);
     if((f3[1:0]==1&&address[0])||(f3==2&&address[1:0]!=0)) begin
      exception=1;cause=isload?4:6;tval=address;
     end
    end
    7'h0f:begin illegal=f3!=0&&f3!=1;is_fencei=f3==1;taken=is_fencei;end
    7'h73:begin
     if(f3==0) begin
      case(ex_insn)
       32'h00000073:begin exception=1;cause=11;tval=0;end
       32'h00100073:begin exception=1;cause=3;tval=ex_pc;end
       32'h30200073:begin is_mret=1;taken=1;next_pc=mepc;end
       32'h10500073:begin end // WFI is implemented as a permitted no-op.
       default:illegal=1;
      endcase
     end else begin
      regwrite=1;result=csr_old;
      case(f3[1:0])
       1:begin csrwrite=1;csr_new=csr_operand;end
       2:begin csrwrite=ex_rs1!=0;csr_new=csr_old|csr_operand;end
       3:begin csrwrite=ex_rs1!=0;csr_new=csr_old&~csr_operand;end
       default:illegal=1;
      endcase
      if(!csr_ok||(csrwrite&&ex_insn[31:30]==2'b11))illegal=1;
     end
    end
    default:illegal=1;
   endcase
   if(taken&&next_pc[1:0]!=0)begin exception=1;cause=0;tval=next_pc;end
   if(illegal)begin exception=1;cause=2;tval=ex_insn;end
   if(ex_error)begin exception=1;cause=1;tval=ex_pc;end
   if(exception)begin regwrite=0;isload=0;isstore=0;csrwrite=0;end
 end
 wire ex_redirect=ex_go&&(taken||exception);
 wire ex_load_hazard=ex_valid&&isload&&ex_insn[11:7]!=0&&
  (ex_insn[11:7]==id_insn[19:15]||ex_insn[11:7]==id_insn[24:20]);
 wire id_go=id_valid&&(!ex_valid||ex_go)&&!ex_load_hazard&&!ex_redirect&&!(mem_done&&mem_fault);
 wire fetch_accept=iv&&ir;
 assign iv=!rst&&fetch_queued;
 assign ia=fetch_addr;
 assign dv=mem_valid&&(mem_load||mem_write)&&!mem_sent&&!mem_trap;
 assign da=mem_addr;assign dw=mem_write;assign wd=mem_store;assign ws=mem_write?mem_strobe:0;
 integer n;
 task enter_trap(input [31:0] pc_value,input [31:0] cause_value,input [31:0] tval_value);
 begin
  mepc<=pc_value;mcause<=cause_value;mtval<=tval_value;
  mstatus[7]<=mstatus[3];mstatus[3]<=0;mstatus[12:11]<=3;
  fetch_pc<={mtvec[31:2],2'b00}+((mtvec[1:0]==1&&cause_value[31])?4*{1'b0,cause_value[30:0]}:0);
  id_valid<=0;ex_valid<=0;mem_valid<=0;fetch_killed<=(fetch_pending||fetch_queued)&&!ip;
  trap_valid<=1;trap_cause<=cause_value;
 end endtask
 always @(posedge clk) begin
  if(rst)begin
   fetch_pc<=0;fetch_pending<=0;fetch_queued<=0;fetch_killed<=0;fetch_addr<=0;
   id_valid<=0;ex_valid<=0;mem_valid<=0;wb_valid<=0;mem_sent<=0;
   retire_valid<=0;trap_valid<=0;fence_i<=0;cycles<=0;instret<=0;
   fetch_wait_cycles<=0;data_wait_cycles<=0;execute_wait_cycles<=0;redirects<=0;
   mstatus<=32'h1800;mie<=0;mtvec<=0;mscratch<=0;mepc<=0;mcause<=0;mtval<=0;
   for(n=0;n<32;n=n+1)regs[n]<=0;
  end else begin
   cycles<=cycles+1;retire_valid<=0;trap_valid<=0;fence_i<=0;wb_valid<=0;regs[0]<=0;
   if((fetch_queued&&!ir)||(fetch_pending&&!ip))fetch_wait_cycles<=fetch_wait_cycles+1;
   if(mem_valid&&(mem_load||mem_write)&&!mem_done)data_wait_cycles<=data_wait_cycles+1;
   if(ex_valid&&!ex_go)execute_wait_cycles<=execute_wait_cycles+1;
   if(ex_redirect)redirects<=redirects+1;
   if(!fetch_pending&&!fetch_queued&&!id_valid&&!irq_pending&&!ex_redirect&&!(mem_done&&mem_fault))begin
    fetch_queued<=1;fetch_addr<=fetch_pc;fetch_pc<=fetch_pc+4;fetch_killed<=0;
   end
   if(fetch_accept)begin fetch_pending<=1;fetch_queued<=0;end
   if(ip&&(fetch_pending||fetch_accept))begin
    fetch_pending<=0;fetch_killed<=0;
    if(!fetch_killed&&!ex_redirect&&!(mem_done&&mem_fault))begin
     id_valid<=1;id_pc<=fetch_addr;id_insn<=insn;id_error<=ierr;
    end
   end
   if(id_go)begin
    id_valid<=0;ex_valid<=1;ex_pc<=id_pc;ex_insn<=id_insn;ex_error<=id_error;
    ex_a<=id_insn[19:15]==0?0:
      (ex_go&&regwrite&&ex_insn[11:7]==id_insn[19:15])?result:
      (mem_valid&&mem_regwrite&&!mem_fault&&mem_rd==id_insn[19:15]&&(!mem_load||mem_done))?mem_value:regs[id_insn[19:15]];
    ex_b<=id_insn[24:20]==0?0:
      (ex_go&&regwrite&&ex_insn[11:7]==id_insn[24:20])?result:
      (mem_valid&&mem_regwrite&&!mem_fault&&mem_rd==id_insn[24:20]&&(!mem_load||mem_done))?mem_value:regs[id_insn[24:20]];
   end
   if(dv&&dr)mem_sent<=1;
   if(mem_done)begin
    mem_valid<=0;mem_sent<=0;
    if(mem_fault)enter_trap(mem_pc,mem_trap?mem_cause:mem_write?7:5,mem_trap?mem_tval:mem_addr);
    else begin
     retire_valid<=1;retire_pc<=mem_pc;retire_insn<=mem_insn;
     retire_rd<=mem_regwrite?mem_rd:0;retire_value<=mem_value;instret<=instret+1;
     wb_valid<=mem_regwrite;wb_rd<=mem_rd;wb_value<=mem_value;
     if(mem_regwrite&&mem_rd!=0)regs[mem_rd]<=mem_value;
     if(mem_csrwrite)case(mem_csraddr)
      12'h300:mstatus<=(mem_csrvalue&32'h88)|32'h1800;
      12'h304:mie<=mem_csrvalue&32'h880;
      12'h305:mtvec<={mem_csrvalue[31:2],1'b0,mem_csrvalue[0]};12'h340:mscratch<=mem_csrvalue;
      12'h341:mepc<={mem_csrvalue[31:2],2'd0};12'h342:mcause<=mem_csrvalue;12'h343:mtval<=mem_csrvalue;
      12'hb00:cycles[31:0]<=mem_csrvalue;12'hb80:cycles[63:32]<=mem_csrvalue;
      12'hb02:instret[31:0]<=mem_csrvalue;12'hb82:instret[63:32]<=mem_csrvalue;
      default:begin end
     endcase
     if(mem_mret)begin mstatus[3]<=mstatus[7];mstatus[7]<=1;mstatus[12:11]<=3;end
     if(mem_fencei)fence_i<=1;
    end
   end
   if(ex_go)begin
    if(!id_go)ex_valid<=0;
    mem_valid<=1;mem_sent<=0;mem_pc<=ex_pc;mem_insn<=ex_insn;mem_result<=result;
    mem_addr<=address;mem_store<=store_data;mem_rd<=ex_insn[11:7];mem_regwrite<=regwrite;
    mem_load<=isload;mem_write<=isstore;mem_size<=f3;mem_strobe<=strobes;
    mem_trap<=exception;mem_cause<=cause;mem_tval<=tval;
    mem_csrwrite<=csrwrite;mem_csraddr<=ex_insn[31:20];mem_csrvalue<=csr_new;
    mem_mret<=is_mret;mem_fencei<=is_fencei;
    if(taken||exception)begin
     id_valid<=0;ex_valid<=0;fetch_killed<=(fetch_pending||fetch_queued)&&!ip;
     fetch_pc<=exception?ex_pc:next_pc;
    end
   end
   if(irq_pending&&!id_valid&&!ex_valid&&!mem_valid&&!fetch_pending&&!fetch_queued)
     enter_trap(fetch_pc,irq_cause,0);
  end
 end
`ifdef SIM_ASSERT
 reg monitor_valid=0,previous_iv,previous_ir,previous_dv,previous_dr;
 reg [31:0] previous_ia,previous_da,previous_wd;reg [3:0] previous_ws;reg previous_dw;
 always @(posedge clk)begin
  if(rst)monitor_valid<=0;
  else begin
   if(monitor_valid)begin
    if(previous_iv&&!previous_ir)assert(iv&&ia==previous_ia)else $fatal(1,"unstable fetch request");
    if(previous_dv&&!previous_dr)assert(dv&&da==previous_da&&wd==previous_wd&&ws==previous_ws&&dw==previous_dw)else $fatal(1,"unstable data request");
    assert(regs[0]==0)else $fatal(1,"x0 modified");
    if(mem_valid&&mem_trap)assert(!dv)else $fatal(1,"trapping instruction issued memory request");
   end
   monitor_valid<=1;previous_iv<=iv;previous_ir<=ir;previous_ia<=ia;
   previous_dv<=dv;previous_dr<=dr;previous_da<=da;previous_wd<=wd;previous_ws<=ws;previous_dw<=dw;
  end
 end
`endif
endmodule


