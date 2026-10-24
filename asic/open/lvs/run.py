#!/usr/bin/env python3
from pathlib import Path
import os,subprocess,json,shutil,sys,time
root=Path(__file__).resolve().parents[3];os.chdir(root)
stage=Path.home()/'riscv-lvs-run';out=root/'build/lvs'
cases=['INV_X1','DFF_X1','INV_X1_negative'] if '--processor' not in sys.argv else ['processor']
results=[]
for case in cases:
 cell='INV_X1' if case=='INV_X1_negative' else case
 schematic='INV_X1_bad.cdl' if case=='INV_X1_negative' else ('processor_reference.cdl' if case=='processor' else cell+'.cdl')
 for suffix in ['status','lvsdb','cir']:
  target=stage/(case+'.'+suffix)
  if target.exists():target.unlink()
 command=['klayout','-b','-r',str(stage/'processor.lvs'),'-rd','input='+str(stage/(cell+'.gds')),'-rd','schematic='+str(stage/schematic),'-rd','report='+str(stage/(case+'.lvsdb')),'-rd','target_netlist='+str(stage/(case+'.cir')),'-rd','status='+str(stage/(case+'.status'))]
 start=time.time()
 with (out/(case+'.log')).open('w')as log:r=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
 status=(stage/(case+'.status')).read_text().strip() if (stage/(case+'.status')).exists() else 'ERROR'
 result={'case':case,'exit_code':r.returncode,'comparison':status,'expected':'FAIL' if 'negative'in case else 'PASS','seconds':round(time.time()-start,2)}
 results.append(result)
 for suffix in ['status','lvsdb','cir']:
  if (stage/(case+'.'+suffix)).exists():shutil.copy2(stage/(case+'.'+suffix),out/(case+'.'+suffix))
 print(json.dumps(result),flush=True)
 print((out/(case+'.log')).read_text()[-1700:],flush=True)
report=root/'reports'/('lvs_processor.json' if '--processor'in sys.argv else 'lvs_cells.json')
report.write_text(json.dumps(results,indent=2))
if any(x['comparison']!=x['expected'] or x['exit_code']!=0 for x in results):sys.exit(1)
