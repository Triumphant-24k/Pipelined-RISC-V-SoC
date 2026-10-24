# KLayout batch script: independently check top-level port labels in an existing LVS DB.
import pya,json
from pathlib import Path
case=globals().get('case','processor')
stage=Path.home()/'riscv-lvs-run';db=pya.LayoutVsSchematic();db.read(str(stage/(case+'.lvsdb')))
top=db.reference.top_circuit()
ok=db.flag_missing_ports(top)
print('PORT_LABEL_RESULT',str(ok),'TOP',top.name)
(stage/(case+'_ports.json')).write_text(json.dumps({'top':top.name,'labels_match':ok},indent=2))
db.write(str(stage/(case+'.lvsdb')))
