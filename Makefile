.PHONY: test baseline arch check compare models all
test:
	python3 scripts/regress.py
baseline:
	$(MAKE) -C baseline test
arch:
	python3 scripts/arch_tests.py
check:
	python3 scripts/check_rtl.py
compare:
	python3 scripts/compare_baseline.py
models:
	python3 models/dataflows.py
all: test arch check compare models
	python3 scripts/report.py

.PHONY: pipeline asic physical-checks evidence submissions
pipeline:
	python3 scripts/pipeline_evidence.py
asic:
	python3 asic/open/synth.py
	python3 asic/open/run_physical.py
	python3 asic/open/gate_check.py
physical-checks:
	python3 asic/open/physical_checks.py
evidence:
	python3 scripts/collect_asic_evidence.py
	python3 scripts/capture_evidence.py
submissions:
	python3 scripts/compile_assignment_reports.py
