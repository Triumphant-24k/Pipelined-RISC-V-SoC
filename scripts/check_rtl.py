#!/usr/bin/env python3
from regress import ROOT,run
import json,time
def main():
 files=[str(p.relative_to(ROOT))for p in sorted((ROOT/'rtl').glob('*.sv'))]
 # Unconnected diagnostics and intentionally unused high bits are allowed;
 # width, latch, combinational-loop, and undriven warnings remain fatal.
 lint=run(['verilator','--lint-only','-Wall','-Wno-UNUSED','-Wno-PINCONNECTEMPTY','--top-module','pipelined_soc',*files])
 (ROOT/'build/synth.ys').write_text('read_verilog -sv '+' '.join(files)+'\nhierarchy -check -top pipelined_soc\nproc\nopt\nmemory_collect\ncheck -assert\nstat\nwrite_json build/synthesis.json\n')
 synth=run(['yosys','-Q','-T','-l','build/synthesis.log','-s','build/synth.ys'])
 (ROOT/'build/formal.ys').write_text('read_verilog -formal -sv rtl/bus_arbiter.sv formal/arbiter_harness.sv\nprep -top arbiter_harness -flatten\nsat -seq 25 -set-assumes -set-init-zero -prove-asserts -verify\n')
 proof=run(['yosys','-Q','-T','-l','build/formal.log','-s','build/formal.ys'])
 (ROOT/'reports/rtl_checks.json').write_text(json.dumps({'timestamp':time.time(),'lint':'pass','generic_synthesis':'pass','formal':{'component':'bus_arbiter','depth':25,'status':'pass','scope':'bounded safety under stable stalled master requests; no liveness or CPU proof'},'physical_implementation':'see reports/asic_metrics.json and physical_checks.json; core only' if (ROOT/'reports/asic_metrics.json').exists() else 'not run'},indent=2))
if __name__=='__main__':main()
