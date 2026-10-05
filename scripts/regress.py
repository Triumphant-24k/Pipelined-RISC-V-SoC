#!/usr/bin/env python3
"""Reproducible local regressions; run from the repository under Linux/WSL."""
from pathlib import Path
import subprocess,random,json,time,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'models'))
from isa_reference import check_trace
def isa_flag():
 probe=subprocess.run(['riscv64-unknown-elf-gcc','-march=rv32im_zicsr_zifencei','-mabi=ilp32','-E','-x','c','-'],input='',text=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 return '-march=rv32im_zicsr_zifencei'if probe.returncode==0 else '-march=rv32im'
ISA_FLAG=isa_flag()
def run(args):
 if args[0]=='iverilog':args=[args[0],'-DSIM_ASSERT',*args[1:]]
 if args[0]=='riscv64-unknown-elf-gcc':args=[ISA_FLAG if arg=='-march=rv32im'else arg for arg in args]
 p=subprocess.run(args,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 print(p.stdout,end='')
 if p.returncode:raise RuntimeError(f'failed: {args}')
 return p.stdout
def signed(x):return x-(1<<32) if x&(1<<31) else x
def hex_image(name):
 run(['riscv64-unknown-elf-objcopy','-O','binary',f'build/{name}.elf',f'build/{name}.bin'])
 data=(ROOT/f'build/{name}.bin').read_bytes();data+=bytes((-len(data))%4)
 (ROOT/f'build/{name}.hex').write_text(''.join(f'{int.from_bytes(data[i:i+4],"little"):08x}\n'for i in range(0,len(data),4)))
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
 unit=[]
 for name,rtl in [('cache','word_cache'),('axi','axi_lite_adapter')]:
  run(['iverilog','-g2012','-s',f'{name}_tb','-o',f'build/{name}_tb',f'rtl/{rtl}.sv',f'tb/{name}_tb.sv'])
  unit.append({'unit':name,'output':run(['vvp',f'build/{name}_tb'])})
 run(['riscv64-unknown-elf-gcc','-march=rv32im','-mabi=ilp32','-nostdlib','-Wl,-T,firmware/link.ld','firmware/trap_test.S','-o','build/traps.elf'])
 hex_image('traps')
 run(['iverilog','-g2012','-s','cpu_tb','-Pcpu_tb.DELAY=5','-Pcpu_tb.FAULTS=1','-o','build/traps_tb','rtl/rv32_pipeline.sv','rtl/rv32_muldiv.sv','tb/cpu_tb.sv'])
 unit.append({'unit':'precise_traps','output':run(['vvp','build/traps_tb','+IMAGE=build/traps.hex','+TRACE=build/traps.trace'])})
 for delay,seed in [(0,1),(3,123),(7,20261005)]:
  run(['iverilog','-g2012','-s','cpu_tb',f'-Pcpu_tb.DELAY={delay}',f'-Pcpu_tb.SEED={seed}','-o','build/cpu_tb','rtl/rv32_muldiv.sv','rtl/rv32_pipeline.sv','tb/cpu_tb.sv'])
  output=run(['vvp','build/cpu_tb',f'+TRACE=build/cpu_trace_{delay}.txt'])
  compared=check_trace(ROOT/'build/cpu.bin',ROOT/f'build/cpu_trace_{delay}.txt')
  print('PASS independent retirement comparison:',compared,'instructions')
  results.append({'delay':delay,'seed':seed,'output':output,'differential_instructions':compared})
 matrix=[]
 for tile,delay in [(4,0),(4,5),(8,0),(8,7)]:
  run(['iverilog','-g2012','-s','matrix_tb',f'-Pmatrix_tb.TILE={tile}',f'-Pmatrix_tb.DELAY={delay}','-o','build/matrix_tb','rtl/matrix_dma.sv','tb/matrix_tb.sv'])
  matrix.append({'tile':tile,'delay':delay,'output':run(['vvp','build/matrix_tb'])})
 run(['riscv64-unknown-elf-gcc','-march=rv32im','-mabi=ilp32','-O2','-nostdlib','-ffreestanding','-fno-builtin','-msmall-data-limit=0','-Wl,-T,firmware/link.ld','firmware/soc_start.S','firmware/soc_demo.c','-o','build/soc.elf'])
 run(['riscv64-unknown-elf-objcopy','-O','binary','build/soc.elf','build/soc.bin'])
 data=(ROOT/'build/soc.bin').read_bytes();data+=bytes((-len(data))%4)
 (ROOT/'build/soc.hex').write_text(''.join(f'{int.from_bytes(data[i:i+4],"little"):08x}\n'for i in range(0,len(data),4)))
 symbols=run(['riscv64-unknown-elf-nm','build/soc.elf'])
 metrics_addr=next(line.split()[0]for line in symbols.splitlines()if line.endswith(' metrics'))
 soc=[]
 for tile,delay,lines,panel in [(4,0,16,4),(4,5,16,4),(8,5,16,8),(8,5,32,8),(8,5,16,16),(4,9,16,8)]:
  run(['iverilog','-g2012','-s','soc_tb',f'-Psoc_tb.TILE={tile}',f'-Psoc_tb.DELAY={delay}',f'-Psoc_tb.CACHE_LINES={lines}',f'-Psoc_tb.PANEL_K={panel}','-o','build/soc_tb',*[str(p.relative_to(ROOT))for p in (ROOT/'rtl').glob('*.sv')],'tb/soc_tb.sv'])
  output=run(['vvp','build/soc_tb',f'+METRICS={metrics_addr}'])
  from dataflows import inference
  metrics={int(row.split()[1]):int(row.split()[2])for row in output.splitlines()if row.startswith('METRIC ')}
  assert [signed(metrics[i])for i in (3,4,5)]==inference()['output']
  soc.append({'tile':tile,'panel_k':panel,'scratchpad_bytes':4*tile*panel,'accumulator_bytes':4*tile*tile,'delay':delay,'cache_lines':lines,'metrics':metrics,'output':output})
 run(['riscv64-unknown-elf-gcc','-march=rv32im','-mabi=ilp32','-nostdlib','-Wl,-T,firmware/link.ld','-DEXIT_ADDR=0x40000200','-Iverification/env','-Iverification/riscv-tests/isa/macros/scalar','verification/riscv-tests/isa/rv32ui/fence_i.S','-o','build/fence.elf'])
 hex_image('fence')
 unit.append({'unit':'cached_self_modifying_code','output':run(['vvp','build/soc_tb','+IMAGE=build/fence.hex','+METRICS=0'])})
 (ROOT/'reports/regression.json').write_text(json.dumps({'timestamp':time.time(),'m_vectors':cases,'unit':unit,'cpu':results,'matrix':matrix,'soc':soc},indent=2))
if __name__=='__main__':main()
