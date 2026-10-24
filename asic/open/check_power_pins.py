#!/usr/bin/env python3
"""Audit actual POWER/GROUND terminal connectivity, in addition to PDN shapes."""
from pathlib import Path
import odb,json,hashlib
root=Path(__file__).resolve().parents[2]
db=odb.dbDatabase.create();odb.read_db(db,str(root/'build/asic/7_final.odb'))
block=db.getChip().getBlock();bad=[];count=0
for inst in block.getInsts():
 for term in inst.getITerms():
  kind=term.getSigType()
  if kind not in ('POWER','GROUND'):continue
  count+=1;net=term.getNet();expected='VDD' if kind=='POWER' else 'VSS'
  if not net or net.getName()!=expected:bad.append({'inst':inst.getName(),'pin':term.getMTerm().getName(),'net':net.getName() if net else None,'expected':expected})
result={'status':'PASS' if count>0 and not bad else 'FAIL','checked_power_ground_terminals':count,'errors':bad,'odb_sha256':hashlib.sha256((root/'build/asic/7_final.odb').read_bytes()).hexdigest()}
(root/'reports/power_pins.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
assert result['status']=='PASS'
