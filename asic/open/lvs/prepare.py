#!/usr/bin/env python3
"""Prepare a pinned, inspectable adaptation of the FreePDK45 LVS deck."""
from pathlib import Path
import xml.etree.ElementTree as ET,hashlib,json,os,subprocess,shutil,re
root=Path(__file__).resolve().parents[3];os.chdir(root)
base=root/'asic/open/lvs';out=root/'build/lvs';out.mkdir(exist_ok=True)
platform=Path(os.environ.get('NANGATE45',str(Path.home()/'OpenROAD-flow-scripts/flow/platforms/nangate45')))
s=ET.parse(base/'vendor/lvs_freepdk45.lylvs').getroot().findtext('text')
s=s[s.index('# layers definitions'):s.index('if ! compare')]
s=re.sub(r'cheat\([^\n]+\) \{\n','',s)
s=s.replace('\n}\n\n# Define connectivity','\n\n# Define connectivity')
# Names in the upstream tolerance statements are inconsistent with its extractors.
for a,b in [('PMOS_LVT','PMOS_VTL'),('PMOS_GVT','PMOS_VTG'),('PMOS_HVT','PMOS_VTH'),('NMOS_LVT','NMOS_VTL'),('NMOS_GVT','NMOS_VTG'),('NMOS_HVT','NMOS_VTH')]:s=s.replace(a,b)
s=s.replace('netlist # ... not really required', '''netlist
# Canonicalize only the aliases introduced by the explicit well/body rules.
netlist.each_circuit do |c|
  c.each_net do |n|
    aliases = n.name.split(',')
    n.name = 'VDD' if aliases.include?('VDD') && (aliases - ['NWELL','VDD']).empty?
    n.name = 'VSS' if aliases.include?('VSS') && (aliases - ['BULK','PWELL','VSS']).empty?
    n.name = n.name.upcase # SPICE uses case-insensitive identifiers
  end
end''')
s=s.replace('connect_explicit(pat, [ "BULK", "VSS" ])','connect_explicit(pat, [ "BULK", "PWELL", "VSS" ])')
header='# Adapted from pinned BSD-3-Clause FreePDK45_for_KLayout; see vendor/LICENSE.\nsource($input)\nreport_lvs($report)\nschematic($schematic)\ntarget_netlist($target_netlist, write_spice(true, false))\ndeep\nthreads(4)\nverbose(true)\n'
footer='\nresult = compare\nif result\n  result = lvs_data.flag_missing_ports(schematic.top_circuit)\nend\nputs(result ? "LVS_RESULT PASS" : "LVS_RESULT FAIL")\n# An exit code alone is insufficient; upstream compare can fail without an exception.\nFile.write($status, result ? "PASS\\n" : "FAIL\\n")\n'
(base/'processor.lvs').write_text(header+s+footer)
provenance={'repository':'https://github.com/laurentc2/FreePDK45_for_KLayout','commit':'d15da945559773854ca04aeb9bc2c150d55a1e6c','upstream_sha256':hashlib.sha256((base/'vendor/lvs_freepdk45.lylvs').read_bytes()).hexdigest(),'adaptations':['Explicit batch inputs and native LVS cross-reference database','Remove unrelated OpenRAM cheat wrapper; extract every processor/library device','Correct tolerance class names to match extracted MOS classes: 1 nm absolute + 0.1 percent','Bind the Nangate pwell body to VSS alongside BULK, matching the library CDL and implicit-well convention','Uppercase extracted names for SPICE case-insensitive port comparison; preserve bus indices','Canonicalize only well/body alias names to VDD/VSS before checking labels','Check top-level port labels after topology comparison','Explicit machine-readable PASS/FAIL from compare; do not trust exit code alone']}
(base/'PROVENANCE.json').write_text(json.dumps(provenance,indent=2))
# Native Linux staging keeps EDA paths simple and improves layout IO performance.
stage=Path.home()/'riscv-lvs-run';stage.mkdir(exist_ok=True)
shutil.copy2(base/'processor.lvs',stage/'processor.lvs')
shutil.copy2(platform/'cdl/NangateOpenCellLibrary.cdl',stage/'library.cdl')
shutil.copy2(root/'build/asic/rv32_pipeline.gds',stage/'processor.gds')
script=f'read_db {{{root}/build/asic/7_final.odb}}\nwrite_cdl -masters {{{platform}/cdl/NangateOpenCellLibrary.cdl}} {stage}/processor.cdl\n'
(out/'export_reference.tcl').write_text(script)
(stage/'export_reference.tcl').write_text(script)
with (out/'export_reference.log').open('w')as log:subprocess.run(['openroad','-exit',str(stage/'export_reference.tcl')],check=True,stdout=log,stderr=subprocess.STDOUT)
shutil.copy2(stage/'processor.cdl',out/'processor.cdl')
(stage/'processor_reference.cdl').write_text('.include "'+str(stage/'library.cdl')+'"\n'+(stage/'processor.cdl').read_text())
print(json.dumps(provenance,indent=2))
