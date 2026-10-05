# Simulation benchmarks

| Tile | K panel | Cache lines | Delay | Software cycles | Poll cycles | IRQ cycles | Poll speedup |
|---|---|---|---|---|---|---|---|
| 4 | 4 | 16 | 0 | 64295 | 2660 | 2636 | 24.17× |
| 4 | 4 | 16 | 5 | 70973 | 4022 | 4121 | 17.65× |
| 8 | 8 | 16 | 5 | 70973 | 2498 | 2794 | 28.41× |
| 8 | 8 | 32 | 5 | 70752 | 2539 | 2722 | 27.87× |
| 8 | 16 | 16 | 5 | 70973 | 2361 | 2693 | 30.06× |
| 4 | 8 | 16 | 9 | 74193 | 4211 | 4575 | 17.62× |

Times include descriptor programming and completion waiting; outputs are checked afterward. The software baseline uses compiler-generated RV32IM multiplication on the same SoC. UART is absent. Frequency is not measured, so these cycle counts are not converted to seconds or claimed GOPS. Random memory acceptance/delays vary with configuration timing.

## Original CPU comparison

| CPU | Delay | GEMM cycles |
|---|---|---|
| reference RV32I multicycle | 0 | 421228 |
| reference RV32I multicycle | 5 | 830632 |
| new pipeline running RV32I | 0 | 540035 |
| new pipeline running RV32I | 5 | 938953 |
| new RV32IM pipeline | 0 | 72029 |
| new RV32IM pipeline | 5 | 105566 |

Identical GEMM source and inputs; both uncached standalone configurations. The reference and new pipeline RV32I runs use byte-identical binaries with a shift/add multiplication helper; they isolate the microarchitecture change under the stated memory model. RV32IM additionally changes multiplication to iterative hardware MUL. It is a separate experiment from the cached SoC table.

## Dataflow models

Output-stationary and weight-stationary models are bit-exactly compared on three workloads and two tile sizes. Traffic assumptions and results are in dataflow_models.json. Model byte counts exclude bus alignment/refill overhead and predict no RTL performance.
