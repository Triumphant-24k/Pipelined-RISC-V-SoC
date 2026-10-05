typedef unsigned int u32;typedef int i32;typedef signed char i8;
volatile u32 kernel_metrics[4];
// Compiler helper for the RV32I baseline. RV32IM uses hardware MUL instead.
#ifdef SOFTWARE_MUL
u32 __mulsi3(u32 a,u32 b){u32 v=0;while(b){if(b&1)v+=a;a<<=1;b>>=1;}return v;}
u32 __umodsi3(u32 a,u32 b){u32 r=0;for(u32 i=0;i<32;i++){r=(r<<1)|(a>>31);a<<=1;if(r>=b)r-=b;}return r;}
#endif
int main(void){
 volatile i8 *a=(volatile i8*)0x10000,*b=(volatile i8*)0x14000;
 volatile i32 *c=(volatile i32*)0x18000;
 const u32 m=7,n=9,k=13;
 for(u32 i=0;i<m*k;i++)a[i]=(i*23+17)%255-127;
 for(u32 i=0;i<k*n;i++)b[i]=(i*41+3)%255-127;
 volatile u32 *tick=(volatile u32*)0x40000100;
 u32 start=*tick;
 for(u32 i=0;i<m;i++)for(u32 j=0;j<n;j++){
  i32 v=0;for(u32 z=0;z<k;z++)v+=(i32)a[i*k+z]*(i32)b[z*n+j];c[i*n+j]=v;
 }
 kernel_metrics[0]=*tick-start;
 u32 hash=0;for(u32 i=0;i<m*n;i++)hash=hash*33+(u32)c[i];
 kernel_metrics[1]=hash;kernel_metrics[2]=m*n*k;
 return 1;
}
