#!/usr/bin/env python3
from pathlib import Path
import re,json,subprocess,hashlib,datetime,os
root=Path(__file__).resolve().parents[1];os.chdir(root)
log=(root/'build/asic/flow.log').read_text()
stages={}
for section in log.split('=== CHECKPOINT ')[1:]:
 name,body=section.split(' ===',1)
 area=re.search(r'Design area ([\d.]+) u\^2 (\d+)% utilization',body)
 slacks=re.findall(r'worst slack ([-\d.]+)',body)
 if area and len(slacks)>=2:stages[name]={'cell_area_um2_rounded':float(area[1]),'utilization_percent_rounded':int(area[2]),'setup_wns_ns':float(slacks[0]),'hold_wns_ns':float(slacks[1])}
versions={}
for name,cmd in {'yosys':['yosys','-V'],'iverilog':['iverilog','-V'],'verilator':['verilator','--version'],'openroad':['openroad','-version'],'klayout':['klayout','-v'],'gcc':['riscv64-unknown-elf-gcc','--version']}.items():
 r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,env=dict(os.environ,QT_QPA_PLATFORM='offscreen'));versions[name]=r.stdout.splitlines()[0]
platform=Path(os.environ.get('NANGATE45',str(Path.home()/'OpenROAD-flow-scripts/flow/platforms/nangate45')))
versions['platform_commit']=subprocess.check_output(['git','-C',str(platform),'rev-parse','HEAD'],text=True).strip()
deftext=(root/'build/asic/2_floorplan.def').read_text()
dbu=int(re.search(r'UNITS DISTANCE MICRONS (\d+)',deftext)[1]);bounds=list(map(int,re.search(r'DIEAREA \( (\d+) (\d+) \) \( (\d+) (\d+) \)',deftext).groups()))
rows=re.findall(r'ROW \S+ \S+ (\d+) (\d+) \S+ DO (\d+) BY 1 STEP (\d+) 0',deftext)
x0=min(int(r[0])for r in rows)/dbu;y0=min(int(r[1])for r in rows)/dbu
x1=max(int(r[0])+int(r[2])*int(r[3])for r in rows)/dbu;y1=max(int(r[1])for r in rows)/dbu+1.4
summary={'top':'rv32_pipeline','corner':'Nangate45 typical, nominal 1.1 V / 25 C','clock_period_ns':10,'setup_uncertainty_ns':0.2,'hold_uncertainty_ns':0.05,'die_um':[x/dbu for x in bounds],'core_um':[x0,y0,x1,y1],'core_area_um2':(x1-x0)*(y1-y0),'stages':stages,'versions':versions,'router_drvs':re.findall(r'FINAL_ROUTER_DRVS (\d+)',log),'completed':'FLOW_COMPLETE'in log}
last=log.rsplit('max capacitance',1)[-1]
caps=re.findall(r'^(\S+/\S+)\s+([\d.]+)\s+([\d.]+)\s+([-\d.]+) \(VIOLATED\)',last,re.M)
summary['max_capacitance_violations']=[{'pin':x[0],'limit_ff':float(x[1]),'actual_ff':float(x[2]),'slack_ff':float(x[3])}for x in caps]
summary['global_wirelength_um']=re.findall(r'Total wirelength: (\d+) um',log)
summary['reported_setup_skew_ns']=re.findall(r'([\d.]+) setup skew',log)[-1:]
(root/'reports/asic_metrics.json').write_text(json.dumps(summary,indent=2))
review=root/'build/evidence'
def put(name,lines): (review/(name+'_review.txt')).write_text('\n'.join(lines)+'\n')
put('rtl',['RTL IMPLEMENTATION - source review','Physical top: rv32_pipeline + rv32_muldiv','Five elastic stages; instruction and data handshake ports','RTL sources: rtl/rv32_pipeline.sv, rtl/rv32_muldiv.sv','',*(root/'rtl/rv32_pipeline.sv').read_text().splitlines()[145:169]])
put('verification',['FUNCTIONAL VERIFICATION - recorded run output','Command: python3 scripts/pipeline_evidence.py','Source log: build/evidence/hazards.log','',*(review/'hazards.log').read_text().splitlines()])
reg=json.loads((root/'reports/regression.json').read_text());arch=json.loads((root/'reports/architectural_tests.json').read_text())
put('regression',['FULL REGRESSION - saved log and JSON artifacts','Command: make all','Source: build/evidence/regression.log','',f'Multiply/divide vectors: {reg["m_vectors"]}',*[f'CPU delay={r["delay"]}: compared {r["differential_instructions"]} retirements'for r in reg['cpu']],f'Architectural result file: reports/architectural_tests.json','',*(root/'build/evidence/regression.log').read_text().splitlines()[-15:]])
synth=(root/'build/asic/1_synth.log').read_text()
put('synthesis',['TECHNOLOGY SYNTHESIS - recorded Yosys output','Command: python3 asic/open/synth.py','Library: NangateOpenCellLibrary_typical.lib','Source log: build/asic/1_synth.log','',*synth.splitlines()[-25:]])
for name,metrics in stages.items():
 lines=[f'PHYSICAL STAGE: {name}','Command: openroad -exit asic/open/flow.tcl','Source: build/asic/flow.log',f'Die: {summary["die_um"]} um',f'Core: {summary["core_um"]} um','',*[f'{k}: {v}'for k,v in metrics.items()],'']
 # First path excerpt supports reported timing and shows a real endpoint.
 lines+=(root/f'build/asic/{name}_setup.rpt').read_text().splitlines()[:18]
 if name=='5_cts':lines+=re.findall(r'^.*(?:Created.*clock|Leaf buffers|Path depth|hold buffers|No hold).*$',log,re.M)[-7:]
 if name=='7_final':lines+=['Router DRVs: '+','.join(summary['router_drvs']),'FLOW_COMPLETE: '+str(summary['completed'])]
 put(name,lines)
if (review/'7_final_gate.log').exists():put('gate',['ZERO-DELAY MAPPED NETLIST CHECK','Command: python3 asic/open/gate_check.py','Source: build/evidence/7_final_gate.log','',*(review/'7_final_gate.log').read_text().splitlines()])
if (root/'reports/physical_checks.json').exists():
 checks=json.loads((root/'reports/physical_checks.json').read_text())
 put('physical_checks',['PHYSICAL VERIFICATION - independent GDS checks','Command: python3 asic/open/physical_checks.py','Source: reports/physical_checks.json and build/asic/klayout_drc.lyrdb','',*(root/'build/asic/stream.log').read_text().splitlines()[-4:],'',*json.dumps(checks,indent=2).splitlines()[:23]])
put('tools',['OPEN-SOURCE TOOLCHAIN - actual installed versions','',*[f'{k}: {v}'for k,v in versions.items()],'','Platform: public Nangate45 / FreePDK45','Physical scope: core only; no SoC SRAM or pad ring','Analysis: typical corner; not foundry signoff'])
print(json.dumps(summary,indent=2))
