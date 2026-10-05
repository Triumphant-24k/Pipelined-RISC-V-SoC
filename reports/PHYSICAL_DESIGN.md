# Physical implementation status

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
