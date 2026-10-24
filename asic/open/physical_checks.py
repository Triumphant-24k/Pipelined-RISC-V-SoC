#!/usr/bin/env python3
from pathlib import Path
import subprocess,os,json,hashlib,xml.etree.ElementTree as ET
root=Path(__file__).resolve().parents[2];os.chdir(root)
platform=Path(os.environ.get('NANGATE45',str(Path.home()/'OpenROAD-flow-scripts/flow/platforms/nangate45')))
env=dict(os.environ,QT_QPA_PLATFORM='offscreen')
with (root/'build/asic/stream.log').open('w') as log:
 subprocess.run(['klayout','-b','-r','asic/open/export_gds.py'],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
with (root/'build/asic/klayout_drc.log').open('w') as log:
 result=subprocess.run(['klayout','-b','-r',str(platform/'drc/FreePDK45.lydrc'),'-rd','in_gds='+str(root/'build/asic/rv32_pipeline.gds'),'-rd','report_file='+str(root/'build/asic/klayout_drc.lyrdb')],env=env,stdout=log,stderr=subprocess.STDOUT)
rpt=root/'build/asic/klayout_drc.lyrdb'
status={'gds_sha256':hashlib.sha256((root/'build/asic/rv32_pipeline.gds').read_bytes()).hexdigest(),'drc_deck_sha256':hashlib.sha256((platform/'drc/FreePDK45.lydrc').read_bytes()).hexdigest(),'drc_exit':result.returncode,'drc_report':str(rpt.relative_to(root)) if rpt.exists() else None,'lvs':'not run: selected public platform has no LVS deck','lvs_deck_exists':(platform/'lvs/FreePDK45.lylvs').exists()}
if result.returncode==0 and rpt.exists():
 tree=ET.parse(rpt);items=tree.findall('.//items/item');counts={}
 for item in items:
  key=item.findtext('category');counts[key]=counts.get(key,0)+1
 status.update(drc_markers=len(items),categories=counts)
if (root/'reports/lvs_summary.json').exists():
 lvs=json.loads((root/'reports/lvs_summary.json').read_text())
 same_gds=hashlib.sha256((root/'build/asic/rv32_pipeline.gds').read_bytes()).hexdigest()==lvs['sha256']['gds']
 same_odb=hashlib.sha256((root/'build/asic/7_final.odb').read_bytes()).hexdigest()==lvs['odb_sha256']
 deck=root/'asic/open/lvs/processor.lvs'
 same_deck=deck.exists()and hashlib.sha256(deck.read_bytes()).hexdigest()==lvs['deck_sha256']
 status.update(lvs=('PASS: routed core and named ports match'if same_gds and same_odb and same_deck and lvs['status']=='PASS'else'STALE: rerun LVS on the current generated inputs'),lvs_deck_exists=deck.exists(),lvs_deck='asic/open/lvs/processor.lvs',lvs_summary='reports/lvs_summary.json')
(root/'reports/physical_checks.json').write_text(json.dumps(status,indent=2))
print(json.dumps(status,indent=2));print((root/'build/asic/stream.log').read_text())
