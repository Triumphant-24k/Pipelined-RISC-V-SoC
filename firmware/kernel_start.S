.section .text.start
.globl _start
_start:
 li sp,0xfff0
 call main
 li t0,0x40000000
 sw a0,0(t0)
1: j 1b
