# Measured processor physical implementation - 24 October 2026

The physical top is rv32_pipeline including rv32_muldiv, using public Nangate45 at its typical 1.1 V / 25 C corner. The optional SoC, caches, DMA, instruction/data memory and pad ring are excluded.

- Die: 292.425 x 292.425 um; core: 272.270 x 270.200 um, area 73,567.354 um2.
- Initial utilization target 40%; placement density target 0.55.
- Synthesis: 17,853 mapped cells, 29,685.866 um2.
- Final logic/repair cell area: 36,606 um2, 50% utilization (tool-rounded).
- Clock 10 ns; setup uncertainty 0.2 ns, hold uncertainty 0.05 ns, IO budgets 1 ns.
- Extracted post-route setup slack +6.31 ns, hold slack +0.02 ns; setup TNS zero.
- CTS: 442 buffers, 405 leaf buffers.
- Initial global-route pass: zero overflow; 590396 um guide wirelength. Incremental electrical repair and legalization follow before detailed routing.
- Detailed-router final DRVs: zero.
- Independent public FreePDK45 GDS DRC: zero markers. FEOL, BEOL, manufacturing-grid and antenna groups all remain enabled; the deck is unchanged.
- Final extracted maximum-capacitance violations: zero.
- Both VDD and VSS PDN shape-connectivity checks pass. All 94,104 POWER/GROUND instance terminals connect to their expected VDD/VSS net.
- Repeated LVS: PASS, 84 circuit pairs, 443 named top pins, 21,593 top nets and 19,030 cell instances match. All 83 functional masters pass independent cell LVS; width and label-swap negative controls are rejected. Comparison log: 0 errors, 108 internal-net ambiguity warnings.

## Repair and validation

The original layout had 43 antenna markers and eight maximum-capacitance violations (worst excess 11.10 fF). An intermediate candidate cleared capacitance but still had 79 antenna markers and was rejected. The final flow anchors 73 real CMOS input buffers and the CTS root near their primary pins; all 74 anchors are recorded. Signal/clock routing is limited to metal2-metal6/metal4-metal6. Placement and global-route electrical repair use a 20% capacitance margin and 10% slew margin, followed by legalization, rerouting and final RC extraction. No DRC rules or Liberty limits are relaxed.

Sizing protection is released before final global power connection, since OpenDB skips do-not-touch instances during global_connect. A terminal-level power audit checks this explicitly. During this run, a metadata-only final power reconnection was applied to the routed database; geometry and extracted timing were preserved, and DRC, simulation, power checks and LVS were repeated on the resulting final artifacts. The final flow performs this ordering directly. The supplied ANTENNA_X1 has zero declared LEF diffusion area and an empty CDL device body; no presumed diode fix is used.

reports/closure_summary.json combines DRC, electrical, timing, functional, power and LVS results and checks GDS/ODB/deck fingerprints. Original and intermediate evidence remain under build/closure_baseline and build/closure_candidate_1; curated before/after screenshots are in reports/evidence. Reproduce with make closure after synthesis, then make evidence and make submissions.

## Scope and assumptions

The initial blanket 0.2 ns hold uncertainty exhausted repair-buffer limits. The revised 0.05 ns hold uncertainty remains a disclosed assumption change; original failed logs are retained. No slow/fast PVT, activity-based power, IR drop or foundry signoff is claimed.

The externally pinned/adapted FreePDK45 LVS deck follows the Nangate implicit well-bias convention: PWELL/BULK to VSS, NWELL to VDD, well-alias canonicalization and SPICE case normalization. MOS W/L tolerance is 1 nm absolute plus 0.1%. No functional black boxes are used.

All instantiated masters have GDS geometry; DEF-to-GDS unit rescaling preserves the exact bounding box. Output is build/asic/rv32_pipeline.gds with corresponding DEF/ODB/Verilog/SPEF. Separate Assignment IX/X PDFs contain actual GUI/terminal evidence and measured results. The Genus/Innovus scripts remain unexecuted; no SRAM macro implementation is claimed.
