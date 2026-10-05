# Simulation benchmarks

| Tile | K panel | Cache lines | Delay | Software cycles | Poll cycles | IRQ cycles | Poll speedup |
|---|---|---|---|---|---|---|---|
| 4 | 4 | 16 | 0 | 55383 | 2689 | 2584 | 20.60× |
| 4 | 4 | 16 | 5 | 61933 | 3946 | 4134 | 15.70× |
| 8 | 8 | 16 | 5 | 61933 | 2496 | 2801 | 24.81× |
| 8 | 8 | 32 | 5 | 61996 | 2442 | 2739 | 25.39× |
| 8 | 16 | 16 | 5 | 61933 | 2316 | 2638 | 26.74× |
| 4 | 8 | 16 | 9 | 65344 | 4215 | 4476 | 15.50× |

Times include descriptor programming and completion waiting; outputs are checked afterward. The software baseline uses compiler-generated RV32IM multiplication on the same SoC. UART is absent. Frequency is not measured, so these cycle counts are not converted to seconds or claimed GOPS. Random memory acceptance/delays vary with configuration timing.

## Original CPU comparison

| CPU | Delay | GEMM cycles |
|---|---|---|
| reference RV32I multicycle | 0 | 421228 |
| reference RV32I multicycle | 5 | 830632 |
| new pipeline running RV32I | 0 | 371361 |
| new pipeline running RV32I | 5 | 850609 |
| new RV32IM pipeline | 0 | 57138 |
| new RV32IM pipeline | 5 | 94397 |

Identical GEMM source and inputs; both uncached standalone configurations. The reference and new pipeline RV32I runs use byte-identical binaries with a shift/add multiplication helper; they isolate the microarchitecture change under the stated memory model. RV32IM additionally changes multiplication to iterative hardware MUL. It is a separate experiment from the cached SoC table.

## Dataflow models

Output-stationary and weight-stationary models are bit-exactly compared on three workloads and two tile sizes. Traffic assumptions and results are in dataflow_models.json. Model byte counts exclude bus alignment/refill overhead and predict no RTL performance.

## Traffic and utilization

| Tile | K panel | Cache lines | Delay | DMA read bytes | DMA write bytes | Array active fraction | Useful MAC fraction while active |
|---|---|---|---|---|---|---|---|
| 4 | 4 | 16 | 0 | 972 | 252 | 3.89% | 53.32% |
| 4 | 4 | 16 | 5 | 972 | 252 | 2.65% | 53.32% |
| 8 | 8 | 16 | 5 | 432 | 252 | 1.48% | 39.99% |
| 8 | 8 | 32 | 5 | 432 | 252 | 1.50% | 39.99% |
| 8 | 16 | 16 | 5 | 352 | 252 | 1.61% | 39.99% |
| 4 | 8 | 16 | 9 | 852 | 252 | 2.50% | 53.32% |

Array active fraction is MAC cycles divided by accelerator elapsed cycles. Useful MAC fraction excludes padded rows/columns/K. Whole-demo fetch/data/execute stall counters and CPI are recorded separately in design_space.json; the stall counters overlap and must not be added together. These results identify remaining memory/control bottlenecks rather than assuming more MACs are always faster.
