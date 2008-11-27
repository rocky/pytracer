# Compatibility for us old-timers.
PHONY=check test dist
all: check
dist: 
	python ./setup.py bdist
check: 
	nosetests
test: check
.PHONY: $(PHONY)
