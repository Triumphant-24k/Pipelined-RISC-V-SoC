# Pipelined RISC-V SoC

An RV32IM pipeline, instruction/data caches, shared memory fabric, and autonomous
tiled INT8 GEMM accelerator. Bare-metal firmware demonstrates software/DMA
GEMM, interrupts, and a complete small convolution/dense inference workload.
The processor core has a routed Nangate45 academic GDS. Post-route typical-corner setup/hold slack is +6.44/+0.02 ns at a 10 ns clock. There are 43 independent antenna markers and eight maximum-capacitance violations; LVS remains unexecuted. No SRAM macro or foundry signoff implementation is claimed.

## Processor and memory block diagram

![Whole SoC: five-stage CPU, caches, memory fabric and INT8 accelerator](docs/images/soc-block-diagram.svg)

See [diagram walkthrough](docs/BLOCK_DIAGRAM.md) for instruction execution,
accelerator operation, and memory capacities.

## Regression status: passed

The local regression passed: 520 multiply/divide vectors, independent CPU
retirement comparisons, 49 architectural programs, component and SoC tests,
lint, generic synthesis, and a 25-cycle bounded arbiter safety proof.
See [verification evidence](docs/VERIFICATION.md) and the
[generated verification report](reports/VERIFICATION.md) for scope and results.

![Local regression terminal showing SAT proof success and passing kernel comparisons](docs/images/regression-passed.png)

The screenshot captures the successful bounded SAT proof and passing baseline
kernel comparisons during `make all`; it does not show the final command exit.

See `docs/PROGRESS.md` for the completion matrix and `docs/ARCHITECTURE.md` for
ISA limitations, protocol contracts, arithmetic, memory map, and registers.

## Run on Windows

From PowerShell in this directory, using Ubuntu-22.04 WSL:

```powershell
wsl -d Ubuntu-22.04 --cd "C:\Users\Trium\OneDrive\Desktop\IMP\Pipelined RISC-V SoC" -- make all
```

This cross-compiles firmware and runs CPU differential tests, directed traps,
cache/AXI tests, matrix tests, inference/configuration sweeps, architectural
tests, fatal lint, generic synthesis, bounded arbiter proof, baseline comparisons,
independent models, and report generation. Binaries/traces/logs go in `build/`.

## Run on Linux or the college server

Requirements: Python 3, Make, Icarus Verilog, Verilator, Yosys, and
riscv64-unknown-elf GCC/binutils supporting RV32 ILP32. No Python packages are
needed. Modern and older compiler architecture conventions are detected.

```bash
make all
make baseline
```

Individual targets: test, arch, check, compare, models. `make all` writes reports.
`make baseline` separately reproduces the earlier project's regression.

Dependencies are pinned submodules. A fresh clone needs
`git submodule update --init`. Git is not needed on the college server after
transferring materialized sources: `python3 scripts/package.py` writes
`build/pipelined-soc-source.tar.gz`, excluding Git metadata and build artifacts.

## Layout

| Directory | Content |
|---|---|
| rtl | CPU, M unit, caches, fabric, matrix DMA, SoC, AXI adapter |
| firmware | Startup/traps, linker, GEMM/inference and CPU tests |
| tb | Memory models and self-checking component/system tests |
| models | Instruction interpreter, dataflows, independent inference |
| scripts | Build/regression, lint/synthesis/formal, report generation |
| formal | Arbiter bounded-safety harness |
| asic | SDC, Genus, MMMC, Innovus scripts |
| reports | Measured JSON artifacts and readable reports |
| docs | Architecture, completion matrix, provenance |
| baseline | Pinned original project/license |
| verification | Pinned riscv-tests and adapted environment |

## Evidence and limits

`reports/BENCHMARKS.md` compares DMA invocation against RV32IM software on the
same SoC. A separate uncached experiment compares identical GEMM source/inputs
on the reference RV32I CPU and new RV32IM CPU; this includes ISA changes and is
not an isolated pipeline-speedup claim.

`reports/VERIFICATION.md` lists the tests/properties passed. Configuration and
model results are in design_space.json and dataflow_models.json; tool versions
are recorded in tool_versions.json.

The conservative frontend does not achieve ideal one-instruction-per-cycle
issue. The CPU is machine-only, with documented privileged limitations.
Operand panels are synthesizable arrays/registers, not mapped SRAM banks.
External 256 KiB test memory is not part of the synthesized SoC. Quantization
and activations run in firmware. Weight-stationary dataflow is modeled, not RTL.

## ASIC implementation and assignment reports

The public Nangate45 flow physically implements `rv32_pipeline` and `rv32_muldiv`.
The optional caches, accelerator, external memory and IO pads are outside this GDS.
See `asic/open/README.md` for scope, pinned tools, constraints and reproduction.

```bash
make pipeline
make asic
make physical-checks
make evidence
make submissions
```

A successful physical run exports `build/asic/rv32_pipeline.gds`, final DEF/ODB,
mapped Verilog and extracted SPEF. The die is 292.425 x 292.425 um; the core is
272.270 x 270.200 um. Final cell area is 36,027 um2 (tool-rounded), 49% utilization.
The typical corner is 1.1 V / 25 C. Setup uncertainty is 0.2 ns; hold uncertainty
is 0.05 ns, revised from an initial blanket 0.2 ns assumption that exhausted
hold-repair buffer limits. This is not multi-corner closure.

The detailed router reports zero violations; independent KLayout GDS DRC reports
43 antenna markers. Eight maximum-capacitance violations remain, and the selected
platform has no validated LVS runset. Both power grids pass connectivity checks.
Do not treat zero-delay gate simulation or stream-out completeness as LVS.

Separate proposal, front-end and back-end PDFs are generated in
`reports/submissions`. They include explanations, actual GUI and terminal-log
review screenshots, measured results and contribution/provenance disclosure.
Source RTL and selected constraints/results are embedded as PDF attachments.
Full logs are retained under build/; curated screenshots are in reports/evidence.
Suggested commit groupings are in docs/COMMIT_GUIDE.md. No assistant commits or
pushes were performed. The older Genus/Innovus scripts remain unexecuted.

## License and provenance

The reference project is pinned at 810b92c9a69f451ce9961f773abb726f25609b66 and
retains its MIT license/notices. riscv-tests is pinned at
bcffa2b3188b040c611f90dc0b6e422f54775a09 and retains its upstream license.
See docs/PROVENANCE.json. No GitHub push was performed.
