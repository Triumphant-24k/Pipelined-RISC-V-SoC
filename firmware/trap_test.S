.section .text.start
.globl _start
_start:
 la t0,handler
 csrw mtvec,t0
 li s0,0
 li s5,0x6000
 sw zero,0(s5)
 li s1,2
 la s2,after_illegal
 li s3,-1
 la s4,illegal
illegal: .word 0xffffffff
 sw s1,0(s5)
after_illegal:
 li s1,3
 la s2,after_break
 la s3,breakpoint
 mv s4,s3
breakpoint: ebreak
 sw s1,0(s5)
after_break:
 li s1,4
 la s2,after_load
 li s3,0x6001
 la s4,badload
badload: lw t0,1(s5)
 sw s1,0(s5)
after_load:
 li s1,6
 la s2,after_store
 li s3,0x6002
 la s4,badstore
badstore: sw s1,2(s5)
 sw s1,0(s5)
after_store:
 li s1,0
 la s2,after_jump
 li s3,2
 la s4,badjump
badjump: jalr zero,zero,2
 sw s1,0(s5)
after_jump:
 li s1,5
 la s2,after_accessload
 li s3,0x30000
 la s4,accessload
accessload: lw t0,0(s3)
 sw s1,0(s5)
after_accessload:
 li s1,7
 la s2,after_accessstore
 li s3,0x30000
 la s4,accessstore
accessstore: sw s1,0(s3)
 sw s1,0(s5)
after_accessstore:
 li s1,1
 la s2,after_fetch
 li s3,0x20000
 mv s4,s3
 jalr zero,s3,0
 sw s1,0(s5)
after_fetch:
 li t0,8
 bne s0,t0,fail
 lw t0,0(s5)
 bnez t0,fail
 li t0,0x40000000
 li t1,1
 sw t1,0(t0)
1: j 1b
.balign 4
handler:
 csrr t0,mcause
 bne t0,s1,fail
 csrr t0,mtval
 bne t0,s3,fail
 csrr t0,mepc
 bne t0,s4,fail
 addi s0,s0,1
 csrw mepc,s2
 mret
fail:
 li t0,0x40000000
 li t1,99
 sw t1,0(t0)
2: j 2b
