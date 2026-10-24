#!/usr/bin/env python3
"""Technology mapping of the proposed processor core, not the optional SoC."""
from pathlib import Path
import os,subprocess
root=Path(__file__).resolve().parents[2]
os.chdir(root)
platform=Path(os.environ.get('NANGATE45',str(Path.home()/'OpenROAD-flow-scripts/flow/platforms/nangate45')))
lib=platform/'lib/NangateOpenCellLibrary_typical.lib'
assert lib.is_file(),lib
out=root/'build/asic';out.mkdir(parents=True,exist_ok=True)
script=f"""read_liberty -lib {lib}
read_verilog -sv rtl/rv32_pipeline.sv rtl/rv32_muldiv.sv
hierarchy -check -top rv32_pipeline
synth -top rv32_pipeline -flatten
check -assert
dfflibmap -liberty {lib}
abc -liberty {lib} -D 10000
hilomap -hicell LOGIC1_X1 Z -locell LOGIC0_X1 Z
clean
check -assert
stat -liberty {lib}
write_verilog -noattr -noexpr build/asic/1_synth.v
write_json build/asic/1_synth.json
"""
(out/'synth.ys').write_text(script)
subprocess.run(['yosys','-Q','-T','-l','build/asic/1_synth.log','-s',str(out/'synth.ys')],check=True)
