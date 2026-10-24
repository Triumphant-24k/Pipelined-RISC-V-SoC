# Completion matrix

| Requirement | Implementation and evidence |
|---|---|
| Preserve baseline | Pinned snapshot; original CPU/accelerator/firmware regression reproduced |
| RV32IM pipeline | Elastic stages, forwarding/interlocks, flushes, iterative M; instruction reference comparison |
| Machine traps/interrupts | Limited machine CSRs, precise exceptions, MRET, external/timer IRQ; directed and firmware tests |
| Retirement/counters | Retire PC/instruction/rd/value, cycle/instret, cache and DMA counters |
| Interconnect/errors | Round-robin arbitration, strobes, completion/errors; bounded safety checks |
| AXI adapter | Single-outstanding AXI4-Lite, independent AW/W; directed tests |
| DMA | Autonomous descriptor loads/stores and completion IRQ; integrated contention |
| Matrix array | 4×4 and 8×8 output-stationary RTL, INT8/INT32, edge tiles |
| Scratchpad/overlap | Logical banked ping-pong arrays; panel depth sweeps; load/compute overlap |
| Alternate dataflow | Executable weight-stationary functional/traffic model, not alternate RTL |
| Quantized inference | Firmware bias/requantization/saturation/ReLU, convolution/dense; Python output check |
| Caches | Parameterized direct-mapped lines, write-through/no-allocate, uncached DMA, FENCE.I |
| Reset/error checks | DMA error, descriptor rejection, busy writes, reset during load/compute/store, recovery |
| Software/baselines | Cross-build, startup/linker/drivers, polling/IRQ, same GEMM on reference CPU |
| Architectural tests | Exact riscv-tests result list; misaligned-success case excluded; no certification |
| Formal | 25-cycle bounded arbiter safety proof; no whole-CPU or unbounded proof |
| Exploration | RTL tile/panel/cache/latency sweeps; separate dataflow models |
| Synthesis | Fatal local lint and generic Yosys structural synthesis checks |
| Open-source ASIC implementation | Processor mapped and routed on Nangate45; DEF/ODB/SPEF/GDS and reports generated |
| Physical checks | Router DRV=0; KLayout antenna markers=43; max-capacitance violations=8; LVS not run; no SRAM macro implementation |
| Reproducibility/CI | make all, PowerShell WSL wrapper, CI workflow; remote CI not run |

Read reports/VERIFICATION.md, BENCHMARKS.md, PHYSICAL_DESIGN.md and their JSON
artifacts for evidence and limits. The commercial scripts are unexecuted; the public Nangate45 processor flow has measured physical output.
No GitHub push is authorized or performed.

The public core flow now runs locally. Next signoff steps are antenna/electrical repair, a validated LVS runset and multi-corner timing. SRAM macros and the commercial lab flow remain outside the completed core run. See reports/asic_metrics.json, physical_checks.json and the separate assignment PDFs.
