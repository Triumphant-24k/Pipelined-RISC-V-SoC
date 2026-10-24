# Assignment requirements and implementation scope

Source documents reviewed on 24 October 2026:
- Assignment VIII proposal and Submission 8 contain the same five-stage processor proposal.
- Assignment IX (QP 9): RTL hierarchy/decisions, functional verification, technology synthesis area/timing, discussion, team details and contributions. Due 31 October (year not printed).
- Assignment X (QP 0): floorplan dimensions/aspect/utilization, power planning, placement/utilization/timing/congestion, CTS, routing/DRC, timing closure, physical verification including LVS where available, final area/limitations and contributions. Due 3 November (year not printed).

## Scope
The physical design top is `rv32_pipeline`, including `rv32_muldiv`, implementing the proposed five-stage processor with external instruction/data interfaces. Existing SoC caches, interconnect and GEMM accelerator remain separately verified extensions; they are not included in the processor GDS. All memories in the processor (register file) map to standard cells. No integrated instruction/data SRAM or pad ring is claimed.

The public Nangate45/FreePDK45 platform is an educational implementation target. Its typical Liberty corner supports measured single-corner results, not foundry signoff or multi-corner closure. Tool versions, platform commit, constraints and all unresolved checks must be recorded.

## Evidence checklist
| Stage | Required evidence |
|---|---|
| RTL | Source hierarchy, pipeline behavior and synthesis hierarchy |
| Verification | Self-checking hazards, ISA retirement comparison, full regression logs, waveform GUI |
| Synthesis | Mapped cell count/area, constraints, STA paths, terminal screenshot |
| Floorplan | Die/core dimensions, aspect ratio, utilization, layout GUI and log |
| Power | Rails/stripes/ring where used, connectivity checks, layout GUI and log |
| Placement | Placed layout, legality, utilization, congestion/timing |
| CTS | Tree buffers/skew/latency and timing, GUI and log |
| Routing | Final routing, congestion, detailed-router violations, GUI and log |
| Timing | Post-placement/CTS/route setup/hold, critical paths and limitations |
| Physical checks | Independent DRC where supported; LVS/connectivity scope stated precisely |
| Submission | Separate IX/X PDF reports with team details, explanation/captions, contribution disclosure |

Team details from proposal: Shiv Sriram V, 24BVD0168, L21+L22. Contributions will distinguish pre-existing code and AI-assisted work; no unverified team-member work is invented.
