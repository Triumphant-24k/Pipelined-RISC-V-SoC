# KLayout batch audit: topology, named top ports, nonempty content and matched pairs.
import pya,json,hashlib,os
from pathlib import Path
root=Path(os.getcwd());stage=Path.home()/'riscv-lvs-run'
case=globals().get('case','processor')
db=pya.LayoutVsSchematic();db.read(str(stage/(case+'.lvsdb')))
for circuit in db.netlist().each_circuit():
 for net in circuit.each_net():
  aliases=set(net.name.split(','))
  if 'VDD'in aliases and aliases<=set(['NWELL','VDD']):net.name='VDD'
  if 'VSS'in aliases and aliases<=set(['BULK','PWELL','VSS']):net.name='VSS'
# SPICE identifiers are case-insensitive and KLayout uppercases their names.
for circuit in db.netlist().each_circuit():
 for net in circuit.each_net():net.name=net.name.upper()
reference=db.reference.top_circuit();layout=db.netlist().top_circuit()
labels=db.flag_missing_ports(reference)
def stats(c):
 return {'name':c.name,'pins':sum(1 for _ in c.each_pin()),'nets':sum(1 for _ in c.each_net()),'devices':sum(1 for _ in c.each_device()),'subcircuits':sum(1 for _ in c.each_subcircuit())}
def prop(obj,name):
 value=getattr(obj,name);return value()if callable(value)else value
pairs=[]
for pair in db.xref().each_circuit_pair():
 left=prop(pair,'first');right=prop(pair,'second')
 pairs.append({'layout':left.name if left else None,'reference':right.name if right else None,'status':str(prop(pair,'status'))})
relations={}
for kind,items in [('nets',db.xref().each_net_pair(layout)),('pins',db.xref().each_pin_pair(layout)),('subcircuits',db.xref().each_subcircuit_pair(layout))]:
 counts={}
 for pair in items:status=str(prop(pair,'status'));counts[status]=counts.get(status,0)+1
 relations[kind]=counts
summary={'layout':stats(layout),'reference':stats(reference),'port_labels_match':labels,'circuit_pairs':pairs,'top_relations':relations}
if case=='processor':
 inputs={n:hashlib.sha256((stage/f).read_bytes()).hexdigest()for n,f in [('gds','processor.gds'),('reference','processor_reference.cdl'),('library','library.cdl')]}
 summary['sha256']=inputs
 summary['pass']=labels and bool(pairs) and all(p['status']=='Match'for p in pairs) and summary['layout']['subcircuits']>0 and all(set(v)=={'Match'} for v in relations.values())
 db.write(str(root/'build/lvs/processor.lvsdb'))
 text=(root/'build/lvs/processor.lvsdb').read_text()
 summary['comparison_warning_count']=text.count('entry(warning')
 summary['comparison_error_count']=text.count('entry(error')
 summary['pass']=summary['pass']and summary['comparison_error_count']==0
 (root/'reports/lvs_audit.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
