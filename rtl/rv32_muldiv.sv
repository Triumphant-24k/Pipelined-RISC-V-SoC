// SPDX-License-Identifier: MIT
// Iterative magnitude multiply / restoring divide. Completion is held until consume.
module rv32_muldiv(input wire clk,rst,start,consume,input wire [2:0] op,
 input wire [31:0] a,b,output reg busy,done,output reg [31:0] result);
 reg [2:0] operation;
 reg [5:0] count;
 reg [63:0] acc,multiplicand;
 reg [31:0] multiplier,divisor,quotient;
 reg [32:0] remainder;
 reg negative_product,negative_quotient,negative_remainder;
 reg [31:0] original_a,original_b;
 wire signed_a=op==1||op==2||op==4||op==6;
 wire signed_b=op==1||op==4||op==6;
 wire neg_a=signed_a&&a[31],neg_b=signed_b&&b[31];
 wire [31:0] mag_a=neg_a?-a:a,mag_b=neg_b?-b:b;
 wire [63:0] sum=acc+(multiplier[0]?multiplicand:64'd0);
 wire [63:0] signed_product=negative_product?-sum:sum;
 wire [32:0] trial={remainder[31:0],quotient[31]};
 wire subtract=trial>={1'b0,divisor};
 wire [32:0] next_rem=subtract?trial-{1'b0,divisor}:trial;
 wire [31:0] next_quot={quotient[30:0],subtract};
 always @(posedge clk)begin
  if(rst)begin busy<=0;done<=0;result<=0;count<=0;end
  else begin
   if(consume)done<=0;
   if(start&&!busy&&!done)begin
    busy<=1;count<=0;operation<=op;acc<=0;multiplicand<={32'd0,mag_a};multiplier<=mag_b;
    divisor<=mag_b;quotient<=mag_a;remainder<=0;
    negative_product<=neg_a^neg_b;negative_quotient<=neg_a^neg_b;negative_remainder<=neg_a;
    original_a<=a;original_b<=b;
   end else if(busy)begin
    count<=count+1;
    if(!operation[2])begin acc<=sum;multiplicand<=multiplicand<<1;multiplier<=multiplier>>1;end
    else begin remainder<=next_rem;quotient<=next_quot;end
    if(count==31)begin
     busy<=0;done<=1;
     if(!operation[2])result<=operation==0?signed_product[31:0]:signed_product[63:32];
     else if(original_b==0)result<=operation[1]?original_a:32'hffffffff;
     else if(operation[1])result<=negative_remainder?-next_rem[31:0]:next_rem[31:0];
     else result<=negative_quotient?-next_quot:next_quot;
    end
   end
  end
 end
endmodule
