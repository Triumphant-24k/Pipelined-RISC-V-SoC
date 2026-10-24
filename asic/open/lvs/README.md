# Processor LVS on Nangate45 / FreePDK45

This flow uses the pinned BSD-3-Clause extraction deck from laurentc2/FreePDK45_for_KLayout. The original XML macro and license remain under vendor/. PROVENANCE.json records the source revision, digest and each adaptation.

## Inputs and independence

- Layout: build/asic/rv32_pipeline.gds, including actual Nangate transistor geometry and routed wires.
- Reference: OpenROAD write_cdl exports the final logical connectivity from 7_final.odb using the library CDL pin order. The independent library transistor CDL definitions are included explicitly.
- Extraction: KLayout recognizes MOS devices and physical metal/via connectivity from the GDS. Reference connections are not generated from the extracted layout.
- Physical filler cells have no transistors and are omitted from the logical reference; simplify removes empty physical-only circuits. Functional cells, clock load cells, devices and routes are retained. No processor or functional-cell black boxes/cheat blocks are permitted.

The public Nangate standard cells lack internal well taps. The deck's existing explicit/implicit power convention is retained and corrected to bind PWELL to VSS, matching the library CDL. Only aliases created by that well convention (NWELL,VDD and BULK/PWELL,VSS) are canonicalized for strict port-label checking. Signal names are uppercased for the SPICE case-insensitive identifier convention before checking named ports. Bus indices and port identities are preserved. This does not connect VDD to VSS or bridge arbitrary signal opens. Both physical power grids were separately checked for connectivity.

The upstream tolerance class names do not match its extractor class names; this adaptation applies the intended 1 nm absolute plus 0.1% tolerance to the actual VTL/VTG/VTH MOS W/L parameters. All tests and the processor use the same deck.

## Run from the project root (Ubuntu/WSL)

```bash
python3 asic/open/lvs/prepare.py
QT_QPA_PLATFORM=offscreen klayout -b -r asic/open/lvs/cell_fixtures.py
python3 asic/open/lvs/run.py
python3 asic/open/lvs/validate_library.py
python3 asic/open/lvs/run.py --processor
QT_QPA_PLATFORM=offscreen klayout -b -r asic/open/lvs/audit.py
python3 asic/open/lvs/summarize.py
```

The first two fixtures are an inverter and DFF. Width and port-label negative controls must fail. The library sweep checks every functional master instantiated by the routed CDL. Inputs/results are staged in $HOME/riscv-lvs-run for native Linux IO; logs and cross-reference databases are copied back to build/lvs. The authoritative circuit verdict and named-port check are machine-readable; do not infer pass from exit code alone.

This is an academic public-PDK LVS check, not a foundry-qualified signoff flow. DRC and electrical limits are checked separately. The repaired core has zero enabled GDS DRC markers and zero maximum-capacitance violations; see reports/closure_summary.json.

`make lvs` runs the whole sequence. `reports/lvs_summary.json` is the consolidated verdict; `lvs_audit.json` records every circuit pair and all top-level relation counts. The checked .lvsdb can be opened in the KLayout Netlist Database Browser. Symmetric internal net-assignment warnings are counted separately from mismatches/errors. Input fingerprints prevent stale results being reported as current.
