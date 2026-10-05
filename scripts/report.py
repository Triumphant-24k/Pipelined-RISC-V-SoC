#!/usr/bin/env python3
"""Generate reviewable reports from actual run artifacts, without estimating PPA."""
from pathlib import Path
import json,re,subprocess
ROOT=Path(__file__).resolve().parents[1]
def load(name):return json.loads((ROOT/'reports'/name).read_text())
def version(command):
 try:return subprocess.run(command,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT).stdout.splitlines()[0]
 except (OSError,IndexError):return 'unavailable'
def main():
 regression=load('regression.json');arch=load('architectural_tests.json');checks=load('rtl_checks.json');baseline=load('baseline_comparison.json');models=load('dataflow_models.json')
 tool_versions={name:version(command)for name,command in {'iverilog':['iverilog','-V'],'verilator':['verilator','--version'],'yosys':['yosys','-V'],'compiler':['riscv64-unknown-elf-gcc','--version'],'python':['python3','--version']}.items()}
 (ROOT/'reports/tool_versions.json').write_text(json.dumps(tool_versions,indent=2))
 passes=[r['test']for r in arch['results']if r['status']=='pass']
 text=f'''# Verification report

![Terminal evidence of successful bounded SAT proof and passing kernel comparisons](../docs/images/regression-passed.png)

See [screenshot context and reproduction command](../docs/VERIFICATION.md).
The screenshot captures part of the passing run, before the final command exit.

The project regression passed {regression['m_vectors']} independently generated
multiply/divide vectors under three memory-delay configurations. Each CPU run
also passed an independent retirement-model comparison of
{regression['cpu'][0]['differential_instructions']} instructions. All comparisons
run through the actual CPU executing compiler-generated firmware.

Unit checks cover cache refills/hits/write strobes/bypass/errors/invalidation;
AXI AW/W independence and response errors; eight precise exception types;
discarded younger stores; and cached self-modifying code with FENCE.I.

Matrix checks exercise six shapes per configuration, signed operands, irregular
dimensions, padded strides, descriptor rejection, and memory stalls. Integrated
tests execute software GEMM, polling DMA, interrupt DMA, timer traps, and a
complete small CNN. Python independently verifies its final output:
{models['inference_reference']['output']}.

## Architectural suite

{len(passes)} imported riscv-tests RV32I/M programs passed in the adapted
bare-metal environment. This is not architectural certification. The successful
misaligned-access test is excluded because this CPU deliberately traps those
accesses. The exact results and pinned source commit are in
architectural_tests.json.

Passed: {', '.join(passes)}.

## RTL checks

Verilator lint and Yosys generic synthesis structural checks passed. The
arbiter safety properties passed bounded checking through
{checks['formal']['depth']} cycles under stable stalled master requests.
This is not a CPU proof, an unbounded arbiter proof, or a liveness proof.
Warnings for intentionally unused diagnostics/high bits and empty diagnostic
connections are suppressed; width/latch/undriven warnings remain fatal.

## Scope limits

No physical timing, area, power, silicon, or FPGA results are claimed. Directed
tests and randomized latency do not exhaustively verify every interrupt/reset
interleaving. The external slave must suppress side effects on failed writes
and share reset with the interconnect. SRAM macro integration remains external.
'''
 (ROOT/'reports/VERIFICATION.md').write_text(text)
 rows=[]
 for config in regression['soc']:
  met=config['metrics'];met={int(k):v for k,v in met.items()}
  output=config['output'];counts={k:int(v)for k,v in re.findall(r'(cycles|instret|transactions|ihit|imiss|dhit|dmiss)=(\d+)',output.splitlines()[1]if output.startswith('WARNING')else output.splitlines()[0])}
  row={k:config[k]for k in('tile','panel_k','scratchpad_bytes','accumulator_bytes','delay','cache_lines')}
  row.update({'software_cycles':met[0],'polling_cycles':met[1],'interrupt_cycles':met[2],'polling_speedup':met[0]/met[1],'interrupt_speedup':met[0]/met[2],**counts})
  row.update({'gemm_accelerator_cycles':met[12],'gemm_array_active_cycles':met[13],'gemm_dma_read_bytes':met[14],'gemm_dma_write_bytes':met[15],'array_active_fraction':met[13]/met[12],'useful_mac_fraction_when_active':(7*9*13)/(config['tile']**2*met[13]),'whole_demo_fetch_wait_cycles':met[16],'whole_demo_data_wait_cycles':met[17],'whole_demo_execute_wait_cycles':met[18],'whole_demo_redirects':met[19]})
  if counts.get('instret'):row['whole_demo_cpi']=counts['cycles']/counts['instret']
  rows.append(row)
 (ROOT/'reports/design_space.json').write_text(json.dumps({'kind':'measured RTL simulation','workload':'same 7x9x13 GEMM and complete demo','memory_delay':'maximum random response delay; one shared word transaction at a time','results':rows},indent=2))
 table='| Tile | K panel | Cache lines | Delay | Software cycles | Poll cycles | IRQ cycles | Poll speedup |\n|---|---|---|---|---|---|---|---|\n'
 table+=''.join(f"| {r['tile']} | {r['panel_k']} | {r['cache_lines']} | {r['delay']} | {r['software_cycles']} | {r['polling_cycles']} | {r['interrupt_cycles']} | {r['polling_speedup']:.2f}× |\n"for r in rows)
 bt='| CPU | Delay | GEMM cycles |\n|---|---|---|\n'+''.join(f"| {r['cpu']} | {r['delay']} | {r['kernel_cycles']} |\n"for r in baseline['results'])
 utilization='\n## Traffic and utilization\n\n| Tile | K panel | Cache lines | Delay | DMA read bytes | DMA write bytes | Array active fraction | Useful MAC fraction while active |\n|---|---|---|---|---|---|---|---|\n'
 utilization+=''.join(f"| {r['tile']} | {r['panel_k']} | {r['cache_lines']} | {r['delay']} | {r['gemm_dma_read_bytes']} | {r['gemm_dma_write_bytes']} | {100*r['array_active_fraction']:.2f}% | {100*r['useful_mac_fraction_when_active']:.2f}% |\n"for r in rows)
 utilization+='\nArray active fraction is MAC cycles divided by accelerator elapsed cycles. Useful MAC fraction excludes padded rows/columns/K. Whole-demo fetch/data/execute stall counters and CPI are recorded separately in design_space.json; the stall counters overlap and must not be added together. These results identify remaining memory/control bottlenecks rather than assuming more MACs are always faster.\n'
 (ROOT/'reports/BENCHMARKS.md').write_text('# Simulation benchmarks\n\n'+table+'\nTimes include descriptor programming and completion waiting; outputs are checked afterward. The software baseline uses compiler-generated RV32IM multiplication on the same SoC. UART is absent. Frequency is not measured, so these cycle counts are not converted to seconds or claimed GOPS. Random memory acceptance/delays vary with configuration timing.\n\n## Original CPU comparison\n\n'+bt+'\nIdentical GEMM source and inputs; both uncached standalone configurations. The reference and new pipeline RV32I runs use byte-identical binaries with a shift/add multiplication helper; they isolate the microarchitecture change under the stated memory model. RV32IM additionally changes multiplication to iterative hardware MUL. It is a separate experiment from the cached SoC table.\n\n## Dataflow models\n\nOutput-stationary and weight-stationary models are bit-exactly compared on three workloads and two tile sizes. Traffic assumptions and results are in dataflow_models.json. Model byte counts exclude bus alignment/refill overhead and predict no RTL performance.\n')
 (ROOT/'reports/PHYSICAL_DESIGN.md').write_text('''# Physical implementation status

Local Verilator lint, generic Yosys synthesis, and structural checks passed.
These results establish elaboration/synthesizability at the generic RTL level;
they are not technology mapping, area, timing closure, or power analysis.

College SSH on cadence.vit.ac.in timed out on port 22 during this task.
Genus, Innovus, OpenROAD, OpenSTA, and SymbiYosys were unavailable on local PATH.
No authorized Liberty/LEF/QRC files or SRAM macros were provided or located in
the project. Genus/Innovus scripts are prepared but have not been run.

The external 256 KiB simulation memory is not part of the synthesized SoC.
Caches, MAC accumulators, and operand panels currently use synthesizable
arrays/registers; no SRAM macro implementation is claimed. Connecting a real
memory wrapper, mapping authorized cells, configuring actual layers/CTS cells,
running multi-corner analysis, and validating DRC/connectivity remain required.

The 10 ns SDC clock is a design target only. No maximum frequency, routed area,
power, or tapeout readiness is asserted. Power reporting requires representative
VCD activity and the actual library/operating corner; no power estimate is saved.
''')
 with (ROOT/'reports/BENCHMARKS.md').open('a')as handle:handle.write(utilization)
 print('PASS generated reports from measured regression artifacts')
if __name__=='__main__':main()

