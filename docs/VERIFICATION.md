# Regression verification evidence

The local regression passed. The [generated verification report](../reports/VERIFICATION.md)
records 520 multiply/divide vectors, CPU retirement-model comparisons, 49
architectural programs, component and integrated SoC tests, lint, generic
synthesis, and the 25-cycle bounded arbiter safety check.

## Terminal screenshot

![Local terminal showing SAT proof success and passing kernel comparisons](images/regression-passed.png)

User-provided screenshot captured on 5 October 2026 during `make all` in
Ubuntu-22.04 WSL from Windows PowerShell. It shows `SAT proof finished - no
model found: SUCCESS!` and multiple `PASS KERNEL` results with matching output
hash `2e60bc73`. The SAT result concerns bounded arbiter safety under the
documented assumptions; it is not a proof of the entire SoC.

The screenshot captures part of the run, before the final command exit.
The full regression status is supported by the recorded test artifacts and
verification report. The `$readmemh` warnings indicate that the firmware image
is shorter than the testbench memory array; the displayed kernel checks pass.

## Reproduce

```powershell
wsl -d Ubuntu-22.04 --cd "C:\Users\Trium\OneDrive\Desktop\IMP\Pipelined RISC-V SoC" -- make all
```

Machine-readable evidence is stored in `reports/regression.json`,
`reports/architectural_tests.json`, and `reports/rtl_checks.json`.
Physical implementation and measured PPA remain outside this verification result.
