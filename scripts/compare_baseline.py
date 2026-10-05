#!/usr/bin/env python3
from regress import ROOT,run,hex_image
import json,re
def main():
 results=[]
 a=[[(i*13+z)*23+17 for z in range(13)]for i in range(7)]
 a=[[(v%255)-127 for v in row]for row in a]
 b=[[((z*9+j)*41+3)%255-127 for j in range(9)]for z in range(13)]
 values=[sum(a[i][z]*b[z][j]for z in range(13))for i in range(7)for j in range(9)]
 expected_hash=0
 for v in values:expected_hash=(expected_hash*33+v)&0xffffffff
 base=[str(p.relative_to(ROOT))for p in (ROOT/'baseline/rtl').glob('*.v')if p.stem not in ('cpu_sim_top','simulation_memory')]
 for pipeline in(0,1):
  name=f'kernel_{pipeline}'
  run(['riscv64-unknown-elf-gcc',f'-march=rv32i{"m"if pipeline else ""}','-mabi=ilp32','-O2','-nostdlib','-ffreestanding','-fno-builtin','-msmall-data-limit=0',*(['-DSOFTWARE_MUL']if not pipeline else []),'-Wl,-T,firmware/link.ld','firmware/kernel_start.S','firmware/kernel.c','-o',f'build/{name}.elf'])
  hex_image(name)
  symbols=run(['riscv64-unknown-elf-nm',f'build/{name}.elf'])
  address=next(row.split()[0]for row in symbols.splitlines()if row.endswith(' kernel_metrics'))
  for delay in(0,5):
   run(['iverilog','-g2012','-s','kernel_tb',f'-Pkernel_tb.PIPELINE={pipeline}',f'-Pkernel_tb.DELAY={delay}','-o','build/kernel_tb','rtl/rv32_pipeline.sv','rtl/rv32_muldiv.sv',*base,'tb/kernel_tb.sv'])
   output=run(['vvp','build/kernel_tb',f'+IMAGE=build/{name}.hex',f'+METRICS={address}'])
   assert int(re.search(r'hash=([0-9a-f]+)',output)[1],16)==expected_hash
   results.append({'cpu':'new RV32IM pipeline'if pipeline else 'reference RV32I multicycle','cache':'none','delay':delay,'kernel_cycles':int(re.search(r'kernel_cycles=(\d+)',output)[1]),'hash':f'{expected_hash:08x}','output':output})
 (ROOT/'reports/baseline_comparison.json').write_text(json.dumps({'workload':'7x9x13 signed INT8 GEMM with INT32 outputs','compiler':'-O2, identical source; RV32I uses shift/add helper, RV32IM uses iterative MUL','scope':'CPU/ISA combined comparison; not isolated pipeline speedup; not the original eight-element dot-product benchmark','results':results},indent=2))
if __name__=='__main__':main()
