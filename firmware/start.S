.section .text.start
.globl _start
_start:
 li sp, 0x3fff0
 la t0, trap_handler
 csrw mtvec, t0
 call main
 li t0, 0x40000000
 sw a0, 0(t0)
1: j 1b
.balign 4
trap_handler:
 csrr t0, mcause
 li t1, 11
 bne t0, t1, trap_fail
 csrr t0, mepc
 addi t0, t0, 4
 csrw mepc, t0
 mret
trap_fail:
 li t0,0x40000000
 csrr t1,mcause
 addi t1,t1,100
 sw t1,0(t0)
 j trap_fail
