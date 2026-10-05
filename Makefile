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
