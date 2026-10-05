#ifndef SOC_RISCV_TEST_H
#define SOC_RISCV_TEST_H
#define RVTEST_RV32U
#define RVTEST_RV64U
#define RVTEST_RV32M
#define RVTEST_RV64M
#define TESTNUM x28
#define RVTEST_CODE_BEGIN .section .text.start; .globl _start; _start:; li TESTNUM,0
#define RVTEST_CODE_END
#define RVTEST_PASS li t0,0x40000000; li t1,1; sw t1,0(t0); 1: j 1b
#define RVTEST_FAIL li t0,0x40000000; slli t1,TESTNUM,1; ori t1,t1,1; sw t1,0(t0); 1: j 1b
#define RVTEST_DATA_BEGIN .balign 16; .globl begin_signature; begin_signature:
#define RVTEST_DATA_END .balign 16; .globl end_signature; end_signature:
#endif
