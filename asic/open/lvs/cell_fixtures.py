# Executed with klayout -b -r; produce real GDS/CDL standard-cell fixtures.
import pya,os,re,json
from pathlib import Path
stage=Path.home()/'riscv-lvs-run'
platform=Path(os.environ.get('NANGATE45',str(Path.home()/'OpenROAD-flow-scripts/flow/platforms/nangate45')))
lib=pya.Layout();lib.read(str(platform/'gds/NangateOpenCellLibrary.gds'))
cdl=(platform/'cdl/NangateOpenCellLibrary.cdl').read_text()
names=['INV_X1','DFF_X1']
if globals().get('all_cells'):
 logical=re.sub(r'\n\+',' ',(stage/'processor.cdl').read_text())
 names=sorted(set(line.split()[-1]for line in logical.splitlines() if line.startswith('X')))
(stage/'cells.json').write_text(json.dumps(names))
for name in names:
 target=pya.Layout();target.dbu=lib.dbu;cell=target.create_cell(name);cell.copy_tree(lib.cell(name));target.write(str(stage/(name+'.gds')))
 match=re.search(r'(?ims)^\.SUBCKT '+name+r'\b.*?^\.ENDS[^\n]*',cdl);assert match,name
 text=match.group(0)+'\n';(stage/(name+'.cdl')).write_text(text)
 print(name,'bbox',cell.dbbox(),'layer polygons',[(str(lib.get_info(li)),sum(1 for _ in lib.cell(name).begin_shapes_rec(li)))for li in lib.layer_indices()])
 # Negative control: change transistor width; comparison must reject it.
 if name=='INV_X1':(stage/'INV_X1_bad.cdl').write_text(re.sub(r'W=([0-9.]+)U',lambda m:'W='+str(float(m[1])*2)+'U',text))
