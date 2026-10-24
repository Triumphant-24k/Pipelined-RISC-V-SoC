#!/usr/bin/env python3
from pathlib import Path
import subprocess,os
root=Path(__file__).resolve().parents[1];os.chdir(root)
out=root/'build/evidence';out.mkdir(parents=True,exist_ok=True)
def I(imm,rs,f,rd,op=0x13):return ((imm&4095)<<20)|(rs<<15)|(f<<12)|(rd<<7)|op
def S(imm,rs2,rs1):return ((imm>>5)<<25)|(rs2<<20)|(rs1<<15)|(2<<12)|((imm&31)<<7)|0x23
def B(imm,rs2,rs1):return (((imm>>12)&1)<<31)|(((imm>>5)&63)<<25)|(rs2<<20)|(rs1<<15)|(((imm>>1)&15)<<8)|(((imm>>11)&1)<<7)|0x63
def J(imm,rd):return (((imm>>20)&1)<<31)|(((imm>>1)&1023)<<21)|(((imm>>11)&1)<<20)|(((imm>>12)&255)<<12)|(rd<<7)|0x6f
program=[I(7,0,0,1),I(5,1,0,2),S(256,2,0),I(256,0,2,3,3),(2<<20)|(3<<15)|(4<<7)|0x33,B(8,0,4),I(24,0,0,5),B(8,5,4),I(99,0,0,6),J(8,7),I(98,0,0,6),I(0,7,0,8),0x400004b7,I(1,0,0,10),S(0,10,9),J(0,0)]
(out/'hazards.hex').write_text(''.join(f'{x:08x}\n'for x in program))
subprocess.run(['iverilog','-g2012','-DSIM_ASSERT','-s','pipeline_evidence_tb','-o','build/evidence/hazards_tb','rtl/rv32_pipeline.sv','rtl/rv32_muldiv.sv','tb/pipeline_evidence_tb.sv'],check=True)
r=subprocess.run(['vvp','build/evidence/hazards_tb'],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(out/'hazards.log').write_text(r.stdout);print(r.stdout);r.check_returncode()
