// SPDX-License-Identifier: MIT
// Output-stationary TILE x TILE MAC array, ping-pong A/B panels, autonomous DMA.
module matrix_dma #(parameter integer TILE=4)(
 input wire clk,rst,input wire cfg_write,input wire [7:0] cfg_addr,
 input wire [31:0] cfg_data,output reg [31:0] cfg_read,
 output wire req,input wire ready,output wire write,
 output wire [31:0] addr,wdata,output wire [3:0] strobe,
 input wire response,input wire [31:0] rdata,input wire error,
 output reg busy,done,fault,output wire irq,
 output reg [63:0] elapsed,mac_cycles,read_bytes,write_bytes
);
 reg [31:0] base_a,base_b,base_c,dim_m,dim_n,dim_k,stride_a,stride_b,stride_c;
 reg irq_enable;
 reg signed [7:0] bank_a[0:1][0:TILE-1][0:TILE-1];
 reg signed [7:0] bank_b[0:1][0:TILE-1][0:TILE-1];
 reg signed [31:0] accum[0:TILE-1][0:TILE-1];
 reg [1:0] panel_ready;
 reg active_bank,load_bank,compute_active;
 reg [31:0] row_tile,col_tile,load_k,compute_k;
 integer load_i,load_j,compute_step,store_i,store_j;
 // loader 0 idle,1 A,2 B; bus phase 0 idle,1 request,2 wait.
 reg [1:0] loader,bus_phase;
 reg storing;
 reg [31:0] bus_addr,bus_wdata;
 reg bus_write;
 reg [1:0] byte_offset;
 reg [31:0] cached_word_addr,cached_word;
 reg cached_word_valid;
 wire [31:0] element_addr=loader==1?
  base_a+(row_tile+load_i)*stride_a+load_k+load_j:
  base_b+(load_k+load_i)*stride_b+col_tile+load_j;
 wire element_valid=loader==1?row_tile+load_i<dim_m&&load_k+load_j<dim_k:
  load_k+load_i<dim_k&&col_tile+load_j<dim_n;
 wire [31:0] shifted_word=rdata>>(8*byte_offset);
 wire [31:0] cached_shift=cached_word>>(8*element_addr[1:0]);
 wire transfer_done=response&&(bus_phase==2||(bus_phase==1&&ready));
 assign req=bus_phase==1;assign addr=bus_addr;assign wdata=bus_wdata;
 assign write=bus_write;assign strobe=bus_write?4'hf:0;assign irq=done&&irq_enable;
 integer i,j;
 always @*begin
  case(cfg_addr)
   8'h00:cfg_read={30'd0,irq_enable,1'b0};8'h04:cfg_read={29'd0,fault,done,busy};
   8'h10:cfg_read=base_a;8'h14:cfg_read=base_b;8'h18:cfg_read=base_c;
   8'h1c:cfg_read=dim_m;8'h20:cfg_read=dim_n;8'h24:cfg_read=dim_k;
   8'h28:cfg_read=stride_a;8'h2c:cfg_read=stride_b;8'h30:cfg_read=stride_c;
   8'h40:cfg_read=elapsed[31:0];8'h44:cfg_read=mac_cycles[31:0];
   8'h48:cfg_read=read_bytes[31:0];8'h4c:cfg_read=write_bytes[31:0];
   default:cfg_read=0;
  endcase
 end
 task advance_load;
 begin
  if(load_j==TILE-1)begin
   load_j<=0;
   if(load_i==TILE-1)begin
    load_i<=0;
    if(loader==1)loader<=2;
    else begin loader<=0;panel_ready[load_bank]<=1;end
   end else load_i<=load_i+1;
  end else load_j<=load_j+1;
 end endtask
 task next_tile;
 begin
  storing<=0;compute_active<=0;panel_ready<=0;cached_word_valid<=0;
  load_bank<=0;active_bank<=0;load_k<=0;compute_k<=0;load_i<=0;load_j<=0;loader<=1;
  for(i=0;i<TILE;i=i+1)for(j=0;j<TILE;j=j+1)accum[i][j]<=0;
  if(col_tile+TILE<dim_n)col_tile<=col_tile+TILE;
  else if(row_tile+TILE<dim_m)begin col_tile<=0;row_tile<=row_tile+TILE;end
  else begin busy<=0;done<=1;loader<=0;end
 end endtask
 always @(posedge clk)begin
  if(rst)begin
   busy<=0;done<=0;fault<=0;irq_enable<=0;bus_phase<=0;loader<=0;
   storing<=0;compute_active<=0;panel_ready<=0;cached_word_valid<=0;
   base_a<=0;base_b<=0;base_c<=0;dim_m<=0;dim_n<=0;dim_k<=0;
   stride_a<=0;stride_b<=0;stride_c<=0;elapsed<=0;mac_cycles<=0;read_bytes<=0;write_bytes<=0;
  end else begin
   if(cfg_write&&!busy)case(cfg_addr)
    8'h00:begin
     irq_enable<=cfg_data[1];
     if(cfg_data[2])begin done<=0;fault<=0;end
     if(cfg_data[0])begin
      done<=0;fault<=0;
      // Require uncached RAM, bounded dimensions/strides, aligned C, no output overlap.
      if(dim_m==0||dim_n==0||dim_k==0||dim_m>256||dim_n>256||dim_k>256||
        stride_a<dim_k||stride_b<dim_n||stride_c<4*dim_n||stride_a>4096||stride_b>4096||stride_c>4096||
        base_c[1:0]!=0||stride_c[1:0]!=0||base_a<32'h10000||base_b<32'h10000||base_c<32'h10000||
        {32'd0,base_a}+dim_m*{32'd0,stride_a}>64'h40000||
        {32'd0,base_b}+dim_k*{32'd0,stride_b}>64'h40000||
        {32'd0,base_c}+dim_m*{32'd0,stride_c}>64'h40000||
        (base_c<base_a+dim_m*stride_a&&base_a<base_c+dim_m*stride_c)||
        (base_c<base_b+dim_k*stride_b&&base_b<base_c+dim_m*stride_c))begin done<=1;fault<=1;end
      else begin
       busy<=1;elapsed<=0;mac_cycles<=0;read_bytes<=0;write_bytes<=0;
       row_tile<=0;col_tile<=0;load_k<=0;compute_k<=0;load_bank<=0;active_bank<=0;
       load_i<=0;load_j<=0;loader<=1;panel_ready<=0;compute_active<=0;storing<=0;cached_word_valid<=0;
       for(i=0;i<TILE;i=i+1)for(j=0;j<TILE;j=j+1)accum[i][j]<=0;
      end
     end
    end
    8'h10:base_a<=cfg_data;8'h14:base_b<=cfg_data;8'h18:base_c<=cfg_data;
    8'h1c:dim_m<=cfg_data;8'h20:dim_n<=cfg_data;8'h24:dim_k<=cfg_data;
    8'h28:stride_a<=cfg_data;8'h2c:stride_b<=cfg_data;8'h30:stride_c<=cfg_data;
    default:begin end
   endcase
   if(busy)begin
    elapsed<=elapsed+1;
    if(bus_phase==1&&ready)bus_phase<=2;
    if(bus_phase==0)begin
     if(storing)begin
      if(row_tile+store_i>=dim_m||col_tile+store_j>=dim_n)begin
       if(store_j==TILE-1)begin store_j<=0;if(store_i==TILE-1)next_tile();else store_i<=store_i+1;end
       else store_j<=store_j+1;
      end else begin
       bus_addr<=base_c+(row_tile+store_i)*stride_c+4*(col_tile+store_j);
       bus_wdata<=accum[store_i][store_j];bus_write<=1;bus_phase<=1;
      end
     end else if(loader!=0)begin
      if(!element_valid||(cached_word_valid&&cached_word_addr=={element_addr[31:2],2'b00}))begin
       if(loader==1)bank_a[load_bank][load_i][load_j]<=element_valid?cached_shift[7:0]:0;
       else bank_b[load_bank][load_i][load_j]<=element_valid?cached_shift[7:0]:0;
       advance_load();
      end else begin
       bus_addr<={element_addr[31:2],2'b00};byte_offset<=element_addr[1:0];
       bus_write<=0;bus_wdata<=0;bus_phase<=1;
      end
     end
    end
    if(transfer_done)begin
     bus_phase<=0;
     if(error)begin busy<=0;done<=1;fault<=1;loader<=0;compute_active<=0;storing<=0;end
     else if(bus_write)begin
      write_bytes<=write_bytes+4;
      if(store_j==TILE-1)begin store_j<=0;if(store_i==TILE-1)next_tile();else store_i<=store_i+1;end
      else store_j<=store_j+1;
     end else begin
      read_bytes<=read_bytes+4;cached_word_addr<=bus_addr;cached_word<=rdata;cached_word_valid<=1;
      if(loader==1)bank_a[load_bank][load_i][load_j]<=shifted_word[7:0];
      else bank_b[load_bank][load_i][load_j]<=shifted_word[7:0];
      advance_load();
     end
    end
    if(!storing&&!compute_active&&panel_ready[active_bank])begin
     compute_active<=1;compute_step<=0;panel_ready[active_bank]<=0;
     // Start loading the next K panel into the other bank while the array computes.
     if(compute_k+TILE<dim_k)begin
      load_bank<=!active_bank;load_k<=compute_k+TILE;load_i<=0;load_j<=0;loader<=1;
     end
    end
    if(compute_active)begin
     mac_cycles<=mac_cycles+1;
     for(i=0;i<TILE;i=i+1)for(j=0;j<TILE;j=j+1)
      accum[i][j]<=accum[i][j]+$signed(bank_a[active_bank][i][compute_step])*$signed(bank_b[active_bank][compute_step][j]);
     if(compute_step==TILE-1)begin
      compute_active<=0;
      if(compute_k+TILE>=dim_k)begin storing<=1;store_i<=0;store_j<=0;end
      else begin compute_k<=compute_k+TILE;active_bank<=!active_bank;end
     end else compute_step<=compute_step+1;
    end
   end
  end
 end
endmodule

