.section .text.start
.globl _start
_start:
 li sp,0xfff0
 la t0,trap_handler
 csrw mtvec,t0
 call main
 li t0,0x40000200
 sw a0,0(t0)
1: j 1b
.balign 4
trap_handler:
 addi sp,sp,-16
 sw t0,0(sp)
 sw t1,4(sp)
 sw t2,8(sp)
 csrr t0,mcause
 li t1,0x8000000b
 beq t0,t1,external_handler
 li t1,0x80000007
 beq t0,t1,timer_handler
 li t1,0x40000200
 addi t0,t0,100
 sw t0,0(t1)
2: j 2b
external_handler:
 la t0,irq_count
 lw t1,0(t0)
 addi t1,t1,1
 sw t1,0(t0)
 li t0,0x40000000
 li t1,6
 sw t1,0(t0)
 j return_trap
timer_handler:
 la t0,timer_count
 lw t1,0(t0)
 addi t1,t1,1
 sw t1,0(t0)
 li t0,0x40000110
 li t1,-1
 sw t1,0(t0)
 sw t1,4(t0)
return_trap:
 lw t0,0(sp)
 lw t1,4(sp)
 lw t2,8(sp)
 addi sp,sp,16
 mret
