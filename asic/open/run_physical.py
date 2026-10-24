#!/usr/bin/env python3
"""Stage into a native Linux path to avoid OpenSTA path-with-spaces limitations."""
import os,subprocess,shutil
from pathlib import Path
root=Path(__file__).resolve().parents[2]
stage=Path.home()/'riscv-lab-run'
for name in ('asic/open','rtl','tb'):
 shutil.copytree(root/name,stage/name,dirs_exist_ok=True)
(stage/'build/asic').mkdir(parents=True,exist_ok=True)
shutil.copy2(root/'build/asic/1_synth.v',stage/'build/asic/1_synth.v')
with (stage/'build/asic/flow.log').open('w') as log:
 result=subprocess.run(['openroad','-exit','asic/open/flow.tcl'],cwd=stage,stdout=log,stderr=subprocess.STDOUT)
shutil.copytree(stage/'build/asic',root/'build/asic',dirs_exist_ok=True)
if result.returncode==0:
 subprocess.run(['openroad','-python','-exit','asic/open/check_power_pins.py'],cwd=root,check=True)
print((stage/'build/asic/flow.log').read_text()[-5000:])
raise SystemExit(result.returncode)
