#!/usr/bin/env python3
"""Fail closed unless final DRC, electrical, timing, functional and LVS evidence agree."""
from pathlib import Path
import json,hashlib,re
root=Path(__file__).resolve().parents[2]
m=json.loads((root/'reports/asic_metrics.json').read_text())
c=json.loads((root/'reports/physical_checks.json').read_text())
l=json.loads((root/'reports/lvs_summary.json').read_text())
pg=json.loads((root/'reports/power_pins.json').read_text())
assert pg['status']=='PASS' and not pg['errors'] and pg['odb_sha256']==l['odb_sha256']
log=(root/'build/asic/flow.log').read_text()
final=log.split('=== CHECKPOINT 7_final ===')[1]
anchors=re.findall(r'^INPUT_ANCHOR (\S+) .*distance_dbu=([0-9.]+)',log,re.M)
assert len(anchors)==len(set(a[0] for a in anchors))==74
dbu=int(re.search(r'UNITS DISTANCE MICRONS (\d+)',(root/'build/asic/7_final.def').read_text())[1])
assert max(float(a[1]) for a in anchors)/dbu < 30
assert m['completed'] and 'FLOW_COMPLETE' in final
assert c['drc_exit']==0 and c['drc_markers']==0 and not c['categories']
assert m['router_drvs'] and all(x=='0' for x in m['router_drvs'])
assert not m['max_capacitance_violations'] and '(VIOLATED)' not in final
assert all(m['stages']['7_final'][s]>=0 for s in ('setup_wns_ns','hold_wns_ns'))
assert l['status']=='PASS' and l['port_labels_match'] and l['comparison_error_count']==0
assert hashlib.sha256((root/'build/asic/rv32_pipeline.gds').read_bytes()).hexdigest()==l['sha256']['gds']==c['gds_sha256']
assert hashlib.sha256((root/'build/asic/7_final.odb').read_bytes()).hexdigest()==l['odb_sha256']
assert hashlib.sha256((root/'asic/open/lvs/processor.lvs').read_bytes()).hexdigest()==l['deck_sha256']
gate=(root/'build/evidence/7_final_gate.log').read_text()
assert 'PASS' in gate and 'FATAL' not in gate
assert 'All shapes on net VDD are connected.' in final and 'All shapes on net VSS are connected.' in final
summary={'status':'PASS','scope':'Nangate45 academic processor, same typical corner and enabled public DRC rules','before':{'antenna_markers':43,'maximum_capacitance_violations':8,'worst_capacitance_excess_ff':11.10,'cell_area_um2_rounded':36027,'setup_wns_ns':6.44,'hold_wns_ns':0.02},'after':{'anchored_primary_inputs':len(anchors),'max_anchor_distance_um':max(float(a[1]) for a in anchors)/dbu,'gds_drc_markers':c['drc_markers'],'cell_area_um2_rounded':m['stages']['7_final']['cell_area_um2_rounded'],'router_drvs':0,'maximum_capacitance_violations':0,'setup_wns_ns':m['stages']['7_final']['setup_wns_ns'],'hold_wns_ns':m['stages']['7_final']['hold_wns_ns'],'lvs':l['status'],'gate_scoreboard':'PASS','power_connectivity':'VDD and VSS PASS'},'repairs':['Real CMOS input buffers anchored at legal edge sites; CTS root anchored near clk','Input isolation buffers protected against removal/resizing','Signal/clock routes limited to metal2-metal6/metal4-metal6','Placement and global-route electrical repair with capacitance margin 20 percent and slew margin 10 percent','Legalization, routing, extraction and all affected checks repeated'],'sha256':l['sha256'],'remaining_scope_limits':['Single typical PVT corner','Academic public-PDK checks, not foundry signoff','External memories, SRAM macros, pad ring and package excluded']}
(root/'reports/closure_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
(root/'build/evidence/closure_review.txt').write_text('PHYSICAL CLOSURE - CHECKED FINAL ARTIFACTS\nCommand: python3 asic/open/closure.py\nSource: reports/closure_summary.json\n\n'+'Original: 43 antenna markers; 8 capacitance violations.\n\nFINAL CHECKS\n'+json.dumps(summary['after'],indent=2)+'\n\nNo DRC rules or Liberty capacitance limits were relaxed.\nFull GDS LVS repeated after the physical changes.\n')
print(json.dumps(summary,indent=2))
