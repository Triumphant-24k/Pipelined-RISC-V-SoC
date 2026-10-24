# Open-source processor RTL-to-GDS flow

Scope: `rv32_pipeline` plus `rv32_muldiv`; the optional caches and matrix SoC are not in this GDS. External instruction/data memory and chip IO pads are outside this core boundary.

Tested with Ubuntu 22.04 WSL, Yosys 0.9, OpenROAD v2.0-17598-ga008522d8 and KLayout 0.30.12. The public platform is the `flow/platforms/nangate45` directory of OpenROAD-flow-scripts commit 6101364b2d7909dd797e1e3e7f80695401cfa4e4. Its Liberty nominal corner is 1.1 V, 25 C. Existing project compiler/simulation prerequisites are listed in the main README.

## Reproduce

Run from the project root in Ubuntu/WSL:

```bash
python3 scripts/pipeline_evidence.py
python3 asic/open/synth.py
python3 asic/open/run_physical.py
python3 asic/open/gate_check.py
python3 asic/open/physical_checks.py
make lvs
python3 scripts/collect_asic_evidence.py
python3 scripts/capture_evidence.py
python3 scripts/compile_assignment_reports.py
```

`NANGATE45` can override the platform directory. Otherwise it defaults to `$HOME/OpenROAD-flow-scripts/flow/platforms/nangate45`. Physical implementation is staged in `$HOME/riscv-lab-run`; its generated files are copied back to `build/asic`. No source files in the upstream platform checkout are modified.

GUI captures use actual GTKWave, OpenROAD, KLayout and xterm windows on an isolated Xvfb display. Terminal images show explicit reviews of recorded logs. They are not synthetic terminal drawings. Full original logs, Verilog, DEF, ODB, extracted SPEF, GDS and DRC database are retained under build/asic and build/evidence. Curated screenshots are in reports/evidence.

Constraints target 10 ns. Setup uncertainty is 0.2 ns, hold uncertainty 0.05 ns; input and output budgets are 1 ns. The earlier blanket 0.2 ns hold assumption exhausted buffer limits; failed-run logs are retained and this revision must be disclosed with results. No slow/fast PVT corner or signoff closure is asserted.

KLayout runs the public FreePDK45 DRC deck on merged standard-cell GDS geometry. Report every remaining marker. The selected platform checkout does not bundle an LVS deck; the externally pinned FreePDK45 deck is now adapted and validated in asic/open/lvs. `make lvs` performs independent transistor/connectivity comparison and named top-port checks. See its README and reports/lvs_summary.json for scope and assumptions. Gate-level simulation, stream-out checks and power connectivity remain separate checks. Zero-delay mapped/post-route functional simulation is a supplemental logical check and has no SDF timing annotation.

## Tool installation

The OpenROAD binary was obtained from the official Precision-Innovations/OpenROAD release dated 2024-12-14 (Ubuntu 22.04 amd64). Its download URL and SHA256 are recorded in reports/toolchain_installation.json. Use the Ubuntu packages `klayout xvfb xdotool imagemagick xterm python3-reportlab python3-fitz poppler-utils` for evidence and PDF generation. The OpenROAD package overlaps the legacy Ubuntu opensta `/usr/bin/sta`; resolve that package conflict explicitly before installation. This environment installed it using dpkg's force-overwrite option and apt dependency repair.

Final PDFs must be reviewed visually after regeneration; the source report generator asserts missing evidence instead of substituting placeholders.

The Ubuntu archive KLayout 0.26.2 package crashed during script startup. The official KLayout 0.30.12 Ubuntu-22 binary replaced it; its download and SHA256 are also recorded in toolchain_installation.json.

Report generation also requires the `pypdf` Python package for embedded source attachments (available in the bundled desktop Python runtime; install with pip for standalone Linux use).
