.PHONY: test baseline
test:
	python3 scripts/regress.py
baseline:
	$(MAKE) -C baseline test
