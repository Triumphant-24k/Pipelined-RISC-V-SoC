#!/usr/bin/env python3
"""Independently validate every functional standard-cell master in the routed netlist."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess,os,json,shutil,time
root=Path(__file__).resolve().parents[3];os.chdir(root)
stage=Path.home()/'riscv-lvs-run';out=root/'build/lvs'
env=dict(os.environ,QT_QPA_PLATFORM='offscreen')
with (out/'fixtures_all.log').open('w')as log:subprocess.run(['klayout','-b','-rd','all_cells=true','-r','asic/open/lvs/cell_fixtures.py'],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
names=json.loads((stage/'cells.json').read_text())
def check(name):
 case='cell_'+name
 for suffix in ['status','lvsdb','cir']:
  target=stage/(case+'.'+suffix)
  if target.exists():target.unlink()
 command=['klayout','-b','-r',str(stage/'processor.lvs'),'-rd','input='+str(stage/(name+'.gds')),'-rd','schematic='+str(stage/(name+'.cdl')),'-rd','report='+str(stage/(case+'.lvsdb')),'-rd','target_netlist='+str(stage/(case+'.cir')),'-rd','status='+str(stage/(case+'.status'))]
 with (out/(case+'.log')).open('w')as log:r=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,env=env)
 status=(stage/(case+'.status')).read_text().strip()if(stage/(case+'.status')).exists()else'ERROR'
 return {'cell':name,'comparison':status,'exit_code':r.returncode}
with ThreadPoolExecutor(max_workers=2)as pool:results=list(pool.map(check,names))
report={'scope':'all functional masters instantiated by final routed CDL; fillers have no transistors','count':len(results),'results':results,'passed':sum(r['comparison']=='PASS'and r['exit_code']==0 for r in results)}
(root/'reports/lvs_library.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
if report['passed']!=report['count']:raise SystemExit(1)
