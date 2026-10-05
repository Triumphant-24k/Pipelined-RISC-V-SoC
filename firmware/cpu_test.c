typedef unsigned int u32;
typedef int i32;
static volatile u32 words[16];
static u32 calc(u32 a,u32 b,int op) {
 u32 v;
 switch(op) {
  case 0: __asm__ volatile("mul %0,%1,%2":"=r"(v):"r"(a),"r"(b));break;
  case 1: __asm__ volatile("mulh %0,%1,%2":"=r"(v):"r"(a),"r"(b));break;
  case 2: __asm__ volatile("mulhsu %0,%1,%2":"=r"(v):"r"(a),"r"(b));break;
  case 3: __asm__ volatile("mulhu %0,%1,%2":"=r"(v):"r"(a),"r"(b));break;
  case 4: __asm__ volatile("div %0,%1,%2":"=r"(v):"r"(a),"r"(b));break;
  case 5: __asm__ volatile("divu %0,%1,%2":"=r"(v):"r"(a),"r"(b));break;
  case 6: __asm__ volatile("rem %0,%1,%2":"=r"(v):"r"(a),"r"(b));break;
  default: __asm__ volatile("remu %0,%1,%2":"=r"(v):"r"(a),"r"(b));break;
 }return v;
}
#include "m_vectors.h"
int main(void) {
 for(u32 i=0;i<sizeof(m_cases)/sizeof(m_cases[0]);i++)
  if(calc(m_cases[i][0],m_cases[i][1],m_cases[i][2])!=m_cases[i][3])return 2+i;
 for(u32 i=0;i<16;i++)words[i]=i*7+3;
 u32 sum=0;for(u32 i=0;i<16;i++)sum+=words[i];
 if(sum!=888)return 500;
 volatile signed char *p=(volatile signed char*)words;
 p[1]=-128;p[2]=127;if(p[1]!=-128||p[2]!=127)return 501;
 volatile short *h=(volatile short*)words;h[2]=-32768;if(h[2]!=-32768)return 502;
 u32 old;__asm__ volatile("csrrw %0,mscratch,%1":"=r"(old):"r"(0x12345678));
 __asm__ volatile("csrr %0,mscratch":"=r"(old));if(old!=0x12345678)return 503;
 __asm__ volatile("fence; fence.i; ecall":::"memory");
 return 1;
}
