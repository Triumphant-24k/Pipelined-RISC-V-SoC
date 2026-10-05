#!/usr/bin/env python3
from regress import ROOT,run
import json,time
def main():
 root=ROOT/'verification/riscv-tests/isa';results=[]
 run(['iverilog','-g2012','-s','cpu_tb','-Pcpu_tb.DELAY=5','-Pcpu_tb.SEED=371','-o','build/arch_tb','rtl/rv32_pipeline.sv','rtl/rv32_muldiv.sv','tb/cpu_tb.sv'])
 for family in ('rv32ui','rv32um'):
  for path in sorted((root/family).glob('*.S')):
   name=family+'-'+path.stem
   if path.stem=='ma_data':
    results.append({'test':name,'status':'excluded','reason':'requires successful misaligned accesses; this implementation traps them'})
    continue
   run(['riscv64-unknown-elf-gcc','-march=rv32im','-mabi=ilp32','-nostdlib','-ffreestanding','-Wl,-T,firmware/link.ld','-Iverification/env','-Iverification/riscv-tests/isa/macros/scalar',str(path),'-o','build/arch.elf'])
   run(['riscv64-unknown-elf-objcopy','-O','binary','build/arch.elf','build/arch.bin'])
   data=(ROOT/'build/arch.bin').read_bytes();data+=bytes((-len(data))%4)
   (ROOT/'build/arch.hex').write_text(''.join(f'{int.from_bytes(data[i:i+4],"little"):08x}\n'for i in range(0,len(data),4)))
   output=run(['vvp','build/arch_tb','+IMAGE=build/arch.hex',f'+TRACE=build/{name}.trace'])
   results.append({'test':name,'status':'pass','output':output})
   print('PASS',name,flush=True)
 (ROOT/'reports/architectural_tests.json').write_text(json.dumps({'suite':'riscv-tests; adapted bare-metal environment, not certification','source_commit':'bcffa2b3188b040c611f90dc0b6e422f54775a09','timestamp':time.time(),'results':results},indent=2))
if __name__=='__main__':main()
