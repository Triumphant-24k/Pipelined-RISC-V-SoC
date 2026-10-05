#!/usr/bin/env python3
"""Reproducible local regressions; run from the repository under Linux/WSL."""
from pathlib import Path
import subprocess,random,json,time
ROOT=Path(__file__).resolve().parents[1]
def run(args):
 p=subprocess.run(args,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 print(p.stdout,end='')
 if p.returncode:raise RuntimeError(f'failed: {args}')
 return p.stdout
def signed(x):return x-(1<<32) if x&(1<<31) else x
def mref(a,b,op):
 sa,sb=signed(a),signed(b)
 if op<4:
  v=(a*b,sa*sb,sa*b,a*b)[op]
  return (v if op==0 else v>>32)&0xffffffff
 if b==0:return a if op>=6 else 0xffffffff
 aa,bb=(sa,sb) if op in (4,6) else (a,b)
 q=abs(aa)//abs(bb)
 if (aa<0)!=(bb<0):q=-q
 return (q if op<6 else aa-q*bb)&0xffffffff
def build_cpu():
 rng=random.Random(20261005)
 pairs=[(a,b)for a in (0,1,0xffffffff,0x80000000,0x7fffffff)for b in (0,1,0xffffffff,0x80000000,7)]
 pairs += [(rng.getrandbits(32),rng.getrandbits(32)) for _ in range(40)]
 cases=[(a,b,op,mref(a,b,op))for a,b in pairs for op in range(8)]
 (ROOT/'firmware/m_vectors.h').write_text('static const u32 m_cases[][4]={\n'+''.join('{'+','.join(f'0x{x:08x}u' for x in row)+'},\n'for row in cases)+'};\n')
 run(['riscv64-unknown-elf-gcc','-march=rv32im','-mabi=ilp32','-O2','-nostdlib','-ffreestanding','-fno-builtin','-msmall-data-limit=0','-Wl,-T,firmware/link.ld','firmware/start.S','firmware/cpu_test.c','-o','build/cpu.elf'])
 run(['riscv64-unknown-elf-objcopy','-O','binary','build/cpu.elf','build/cpu.bin'])
 data=(ROOT/'build/cpu.bin').read_bytes();data+=bytes((-len(data))%4)
 (ROOT/'build/cpu.hex').write_text(''.join(f'{int.from_bytes(data[i:i+4],"little"):08x}\n'for i in range(0,len(data),4)))
 return len(cases)
def main():
 (ROOT/'build').mkdir(exist_ok=True)
 cases=build_cpu();results=[]
 for delay,seed in [(0,1),(3,123),(7,20261005)]:
  run(['iverilog','-g2012','-s','cpu_tb',f'-Pcpu_tb.DELAY={delay}',f'-Pcpu_tb.SEED={seed}','-o','build/cpu_tb','rtl/rv32_muldiv.sv','rtl/rv32_pipeline.sv','tb/cpu_tb.sv'])
  output=run(['vvp','build/cpu_tb',f'+TRACE=build/cpu_trace_{delay}.txt'])
  results.append({'delay':delay,'seed':seed,'output':output})
 matrix=[]
 for tile,delay in [(4,0),(4,5),(8,0),(8,7)]:
  run(['iverilog','-g2012','-s','matrix_tb',f'-Pmatrix_tb.TILE={tile}',f'-Pmatrix_tb.DELAY={delay}','-o','build/matrix_tb','rtl/matrix_dma.sv','tb/matrix_tb.sv'])
  matrix.append({'tile':tile,'delay':delay,'output':run(['vvp','build/matrix_tb'])})
 (ROOT/'reports/regression.json').write_text(json.dumps({'timestamp':time.time(),'m_vectors':cases,'cpu':results,'matrix':matrix},indent=2))
if __name__=='__main__':main()
