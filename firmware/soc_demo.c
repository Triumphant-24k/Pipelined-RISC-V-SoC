typedef unsigned int u32;typedef signed char i8;typedef int i32;
volatile u32 irq_count,timer_count;
volatile u32 metrics[12];
#define REG(off) (*(volatile u32*)(0x40000000u+(off)))
static volatile i8 *const A=(volatile i8*)0x10000;
static volatile i8 *const B=(volatile i8*)0x14000;
static volatile i32 *const C=(volatile i32*)0x18000;
static inline u32 tick(void){u32 v;__asm__ volatile("rdcycle %0":"=r"(v));return v;}
static void gemm(u32 m,u32 n,u32 k,int interrupt) {
 REG(0x10)=(u32)A;REG(0x14)=(u32)B;REG(0x18)=(u32)C;
 REG(0x1c)=m;REG(0x20)=n;REG(0x24)=k;REG(0x28)=k;REG(0x2c)=n;REG(0x30)=4*n;
 u32 before=irq_count;REG(0)=interrupt?3:1;
 if(interrupt){while(irq_count==before)__asm__ volatile("nop");}
 else {while(!(REG(4)&2));}
}
static i8 quant(i32 x,i32 bias,int relu) {
 x=(x+bias)>>5;if(relu&&x<0)x=0;if(x>127)x=127;if(x<-128)x=-128;return (i8)x;
}
int main(void) {
 irq_count=0;timer_count=0;
 __asm__ volatile("csrw mie,%0; csrs mstatus,%1"::"r"(0x880),"r"(8):"memory");
 // Exercise a timer trap, then have the handler disable its comparator.
 REG(0x114)=0;REG(0x110)=tick()+500;
 while(timer_count==0)__asm__ volatile("nop");
 // Same matrices for RV32IM software and DMA baselines.
 const u32 m=7,n=9,k=13;
 for(u32 i=0;i<m*k;i++)A[i]=(i*23+17)%255-127;
 for(u32 i=0;i<k*n;i++)B[i]=(i*41+3)%255-127;
 i32 reference[63];
 u32 start=tick();
 for(u32 i=0;i<m;i++)for(u32 j=0;j<n;j++){
  i32 v=0;for(u32 z=0;z<k;z++)v+=(i32)A[i*k+z]*(i32)B[z*n+j];reference[i*n+j]=v;
 }
 metrics[0]=tick()-start;start=tick();gemm(m,n,k,0);metrics[1]=tick()-start;
 for(u32 i=0;i<m*n;i++)if(C[i]!=reference[i])return 2+i;
 REG(0)=4;
 start=tick();gemm(m,n,k,1);metrics[2]=tick()-start;
 for(u32 i=0;i<m*n;i++)if(C[i]!=reference[i])return 100+i;
 // Tiny complete CNN: 4x4 image -> 3x3 valid convolution (2 channels)
 // -> bias/ReLU/requantization -> flattened 8 features -> 3-class dense layer.
 const i8 image[16]={1,-2,3,4,5,6,-7,8,9,-10,11,12,13,14,15,-16};
 i32 conv_ref[8];i8 features[8];
 for(u32 r=0;r<2;r++)for(u32 c=0;c<2;c++)for(u32 x=0;x<3;x++)for(u32 y=0;y<3;y++)
  A[(r*2+c)*9+x*3+y]=image[(r+x)*4+c+y];
 for(u32 z=0;z<9;z++)for(u32 f=0;f<2;f++)B[z*2+f]=(z*3+f*7)%9-4;
 for(u32 p=0;p<4;p++)for(u32 f=0;f<2;f++){
  i32 v=0;for(u32 z=0;z<9;z++)v+=(i32)A[p*9+z]*(i32)B[z*2+f];conv_ref[p*2+f]=v;
 }
 gemm(4,2,9,1);
 for(u32 p=0;p<8;p++){
  if(C[p]!=conv_ref[p])return 200+p;
  features[p]=quant(C[p],(p%2)?-16:48,1);
 }
 for(u32 p=0;p<8;p++)A[p]=features[p];
 for(u32 p=0;p<8;p++)for(u32 c=0;c<3;c++)B[p*3+c]=(p*5+c*3)%11-5;
 i32 dense_ref[3];
 for(u32 c=0;c<3;c++){i32 v=0;for(u32 p=0;p<8;p++)v+=(i32)features[p]*(i32)B[p*3+c];dense_ref[c]=v;}
 gemm(1,3,8,1);
 for(u32 c=0;c<3;c++){
  if(C[c]!=dense_ref[c])return 220+c;
  metrics[3+c]=(u32)(i32)quant(C[c],(i32)c*16-16,0);
 }
 metrics[6]=irq_count;metrics[7]=timer_count;
 metrics[8]=REG(0x40);metrics[9]=REG(0x44);metrics[10]=REG(0x48);metrics[11]=REG(0x4c);
 return irq_count==3&&timer_count==1?1:240;
}
