#!/usr/bin/env python3
from pathlib import Path
import subprocess,os
root=Path(__file__).resolve().parents[2];os.chdir(root)
platform=Path(os.environ.get('NANGATE45',str(Path.home()/'OpenROAD-flow-scripts/flow/platforms/nangate45')))
lib=platform/'lib/NangateOpenCellLibrary_typical.lib'
script=f'read_liberty -ignore_miss_func {lib}\nwrite_verilog -noattr build/asic/cells_sim.v\n'
(root/'build/asic/cells.ys').write_text(script)
subprocess.run(['yosys','-Q','-T','-s','build/asic/cells.ys'],check=True,stdout=subprocess.DEVNULL)
for name in ['1_synth','7_final']:
 if not (root/f'build/asic/{name}.v').exists():continue
 subprocess.run(['iverilog','-g2012','-DGATE_SIM','-s','pipeline_evidence_tb','-o','build/evidence/gate_tb','build/asic/cells_sim.v',f'build/asic/{name}.v','tb/pipeline_evidence_tb.sv'],check=True)
 result=subprocess.run(['vvp','build/evidence/gate_tb',f'+WAVE=build/evidence/{name}_gate.vcd'],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 (root/f'build/evidence/{name}_gate.log').write_text(result.stdout)
 print(name,result.stdout);result.check_returncode()
