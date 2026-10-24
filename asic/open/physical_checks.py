#!/usr/bin/env python3
from pathlib import Path
import subprocess,os,json,xml.etree.ElementTree as ET
root=Path(__file__).resolve().parents[2];os.chdir(root)
platform=Path(os.environ.get('NANGATE45',str(Path.home()/'OpenROAD-flow-scripts/flow/platforms/nangate45')))
env=dict(os.environ,QT_QPA_PLATFORM='offscreen')
with (root/'build/asic/stream.log').open('w') as log:
 subprocess.run(['klayout','-b','-r','asic/open/export_gds.py'],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
with (root/'build/asic/klayout_drc.log').open('w') as log:
 result=subprocess.run(['klayout','-b','-r',str(platform/'drc/FreePDK45.lydrc'),'-rd','in_gds='+str(root/'build/asic/rv32_pipeline.gds'),'-rd','report_file='+str(root/'build/asic/klayout_drc.lyrdb')],env=env,stdout=log,stderr=subprocess.STDOUT)
rpt=root/'build/asic/klayout_drc.lyrdb'
status={'drc_exit':result.returncode,'drc_report':str(rpt.relative_to(root)) if rpt.exists() else None,'lvs':'not run: selected public platform has no LVS deck','lvs_deck_exists':(platform/'lvs/FreePDK45.lylvs').exists()}
if result.returncode==0 and rpt.exists():
 tree=ET.parse(rpt);items=tree.findall('.//items/item');counts={}
 for item in items:
  key=item.findtext('category');counts[key]=counts.get(key,0)+1
 status.update(drc_markers=len(items),categories=counts)
(root/'reports/physical_checks.json').write_text(json.dumps(status,indent=2))
print(json.dumps(status,indent=2));print((root/'build/asic/stream.log').read_text())
