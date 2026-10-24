# Suggested commits (user performs all commits)

No commits or staging are performed by the assistant. Review diffs before staging. Generated build files are ignored; curated evidence is copied to reports/evidence.

1. `docs: map assignment requirements to implementation and evidence`
   - docs/ASSIGNMENT_REQUIREMENTS.md, docs/COMMIT_GUIDE.md
2. `build: add reproducible Nangate45 processor implementation flow`
   - asic/open, scripts for tool setup, synthesis, constraints and physical stages.
3. `test: add directed pipeline hazard and waveform evidence`
   - directed testbench, waveform configuration and reproducible checks.
4. `feat: complete processor placement clock tree and routing`
   - physical-flow fixes, measured implementation reports, stage evidence.
5. `docs: add assignment IX and X reports with measured results`
   - reports, screenshots, updated README and completion matrix.

Stages may share files. Use `git add -p` to split changes if desired; do not add local tool installations or entire build directories.


## LVS continuation

6. `verify: add FreePDK45 LVS deck and standard-cell validation`
   - asic/open/lvs vendor source/license, adaptation/provenance, fixtures, negative controls and reports/lvs_cells.json, lvs_library.json.
7. `verify: run routed processor LVS and record comparison evidence`
   - final reference export, reproducible comparison, port identity check, measured summary and actual GUI/terminal evidence.
8. `docs: update assignment reports with validated LVS results`
   - revised IX/X PDFs, corrected physical-verification status, reproduction notes and checksums.

A zero KLayout exit code is not sufficient to declare LVS pass: the comparison result and port-label check must pass, with nonempty matched circuits. Negative controls must be rejected. All remaining DRC/electrical limits stay disclosed separately.
