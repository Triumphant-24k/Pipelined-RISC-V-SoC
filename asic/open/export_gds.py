# Run inside KLayout: klayout -b -r asic/open/export_gds.py
import pya,os
from pathlib import Path
root=Path(os.getcwd())
platform=Path(os.environ.get('NANGATE45',str(Path.home()/'OpenROAD-flow-scripts/flow/platforms/nangate45')))
tech=pya.Technology();tech.load(str(platform/'FreePDK45.lyt'))
options=tech.load_layout_options
options.lefdef_config.lef_files=[str(platform/'lef/NangateOpenCellLibrary.tech.lef'),str(platform/'lef/NangateOpenCellLibrary.macro.mod.lef')]
layout=pya.Layout();layout.read(str(root/'build/asic/7_final.def'),options)
for cell in layout.each_cell():
 if cell.name!='rv32_pipeline' and not cell.name.startswith('VIA_'):cell.clear()
layout.read(str(platform/'gds/NangateOpenCellLibrary.gds'))
final=pya.Layout();final.dbu=layout.dbu
top=final.create_cell('rv32_pipeline');top.copy_tree(layout.cell('rv32_pipeline'))
empty=[c.name for c in final.each_cell() if c.is_empty()]
assert not empty,'Unresolved GDS masters: '+str(empty)
final.write(str(root/'build/asic/rv32_pipeline.gds'))
print('PASS DEF to GDS stream-out; every cell master has geometry')
print('TOP',top.name,'DBU',final.dbu,'BBOX',top.dbbox(),'CELLS',final.cells())
