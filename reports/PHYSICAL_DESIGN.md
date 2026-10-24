# Measured processor physical implementation - 24 October 2026

The physical top is rv32_pipeline including rv32_muldiv, using public Nangate45 at its typical 1.1 V / 25 C corner. The optional SoC, caches, DMA, instruction/data memory and pad ring are excluded.

- Die: 292.425 x 292.425 um; square requested aspect ratio.
- Core: 272.270 x 270.200 um; 73,567.354 um2, snapped to rows/sites.
- Initial utilization target: 40%; placement density target: 0.55.
- Synthesis: 17,853 cells and 29,685.866 um2 mapped area.
- Final logic/repair cell area: 36,027 um2, 49% utilization (tool-rounded).
- Clock: 10 ns; setup uncertainty 0.2 ns; hold uncertainty 0.05 ns; IO budgets 1 ns.
- Extracted post-route setup slack +6.44 ns, hold slack +0.02 ns; setup TNS 0.
- CTS: 442 buffers, 405 leaf buffers; 3-4 reported path depth; max tree level 5.
- Global routing: zero overflow on every layer, 31.78% resource use, 562,947 um guide-based wirelength.
- Detailed-router final DRVs: 0.
- KLayout public FreePDK45 independent GDS DRC: 43 antenna markers (M4:7, M5:11, M6:15, M7:5, M9:5). Other enabled groups report zero markers.
- Electrical constraints: eight maximum-capacitance violations, worst excess 11.10 fF. These remain unresolved.
- Both VDD and VSS power-grid connectivity checks pass.
- LVS: PASS using the externally pinned/adapted FreePDK45 KLayout deck. 83 circuit pairs, 443 named top pins, 21,418 top nets and 18,862 cell instances match. All 82 functional masters pass independent cell LVS; both width and label-swap negative controls are rejected. The comparison log has zero errors and 108 internal-net ambiguity warnings. See lvs_summary.json, lvs_audit.json and asic/open/lvs/README.md. Gate simulation remains a separate logical check.

The initial blanket 0.2 ns hold uncertainty exhausted hold-buffer insertion limits at 20% and 50% allowances. The revised hold uncertainty is explicitly an assumption change, not closure under the original budget. Failed attempt logs remain in build/evidence. No slow/fast PVT or foundry signoff claim is made.

All standard-cell masters have GDS geometry. The stream-out tool rescaled DEF database units (0.0005 um) into its 0.0001 um reader grid; the final bounding box is preserved exactly. There are no empty library masters. Routed output is build/asic/rv32_pipeline.gds, with corresponding DEF/ODB/Verilog/SPEF. Source scripts and setup are in asic/open. Exact metrics/checks are in asic_metrics.json and physical_checks.json.

The separate Assignment IX and X PDFs discuss these measured outcomes with stage screenshots. The Genus/Innovus scripts were not executed and no SRAM macro integration is claimed.

The LVS deck assumes the documented Nangate implicit well-bias convention, corrects PWELL to VSS and canonicalizes only well aliases and SPICE letter case. MOS W/L tolerance is 1 nm absolute plus 0.1%. No functional black boxes are used. This is an academic public-PDK verification result and does not waive the remaining antenna or electrical violations.
