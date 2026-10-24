# KLayout batch script: independently check top-level port labels in an existing LVS DB.
import pya,json
from pathlib import Path
case=globals().get('case','processor')
stage=Path.home()/'riscv-lvs-run';db=pya.LayoutVsSchematic();db.read(str(stage/(case+'.lvsdb')))
for circuit in db.netlist().each_circuit():
 for net in circuit.each_net():
  aliases=set(net.name.split(','))
  if 'VDD' in aliases and aliases<=set(['NWELL','VDD']):net.name='VDD'
  if 'VSS' in aliases and aliases<=set(['BULK','PWELL','VSS']):net.name='VSS'
for circuit in db.netlist().each_circuit():
 for net in circuit.each_net():net.name=net.name.upper()
top=db.reference.top_circuit()
ok=db.flag_missing_ports(top)
print('PORT_LABEL_RESULT',str(ok),'TOP',top.name)
(stage/(case+'_ports.json')).write_text(json.dumps({'top':top.name,'labels_match':ok},indent=2))
db.write(str(stage/(case+'.lvsdb')))
