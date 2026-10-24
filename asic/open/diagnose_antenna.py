#!/usr/bin/env python3
"""Map independent antenna marker geometry to routed OpenDB net names."""
from pathlib import Path
import xml.etree.ElementTree as ET
import re,json,hashlib,odb
root=Path(__file__).resolve().parents[2]
db=odb.dbDatabase.create();odb.read_db(db,str(root/'build/asic/7_final.odb'))
block=db.getChip().getBlock();scale=block.getDbUnitsPerMicron()
markers=[]
for item in ET.parse(root/'build/asic/klayout_drc.lyrdb').findall('.//items/item'):
 vals=[v.text for v in item.findall('values/value')]
 poly=next(v for v in vals if v.startswith('polygon:'))
 nums=[float(x) for x in re.findall(r'-?[0-9]+(?:\.[0-9]+)?',poly)]
 xs=nums[::2];ys=nums[1::2]
 markers.append({'category':item.findtext('category'),'box':[min(xs),min(ys),max(xs),max(ys)],'values':vals,'nets':[]})
for net in block.getNets():
 wire=net.getWire()
 if not wire:continue
 dec=odb.dbWireDecoder();dec.begin(wire)
 while True:
  op=dec.next()
  if op==dec.END_DECODE:break
  if op!=dec.POINT:continue
  point=dec.getPoint();x,y=point[0]/scale,point[1]/scale
  layer=dec.getLayer().getName()
  for m in markers:
   b=m['box'];n=int(re.search(r'METAL([0-9]+)',m['category'])[1])
   if layer==f'metal{n}' and b[0]-0.001<=x<=b[2]+0.001 and b[1]-0.001<=y<=b[3]+0.001:
    if net.getName() not in m['nets']:m['nets'].append(net.getName())
summary={n:{'ports':[b.getName() for b in block.findNet(n).getBTerms()],'iterms':[t.getInst().getName()+'/'+t.getMTerm().getName() for t in block.findNet(n).getITerms()]} for m in markers for n in m['nets']}
result={'markers':markers,'nets':summary,'gds_sha256':hashlib.sha256((root/'build/asic/rv32_pipeline.gds').read_bytes()).hexdigest(),'scope':'Coordinate candidates for diagnostic review, not a connectivity proof'}
(root/'build/asic/antenna_diagnosis.json').write_text(json.dumps(result,indent=2))
print(json.dumps(summary,indent=2))

