VERSION = 0.3.1

PACKAGE = rstbuddy

#======================================================================


clean:
	rm -rf *.tar.gz dist *.egg-info
	find . -name "*.pyc" -exec rm '{}' ';' 2>/dev/null
	find . -name "*.pyo" -exec rm '{}' ';' 2>/dev/null
	find . -name "*.pyd" -exec rm '{}' ';' 2>/dev/null
	find ./tests -name "__pycache__" -exec rm -rf '{}' ';' 2>/dev/null
	find ./rstbuddy -name "__pycache__" -exec rm -rf '{}' ';' 2>/dev/null
	rm -rf .pytest_cache
	rm -rf build
	rm -rf dist

dist: clean
	@python -m build --sdist --wheel

compile:
	@uv pip compile --group=docs pyproject.toml -o requirements.txt

release:
	@bin/release.sh

docs:
	@echo "Generating docs..."
	@cd doc && rm -rf build && make html
	@open doc/build/html/index.html

.PHONY: docs release compile dist clean list
list:
	@$(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | egrep -v -e '^[^[:alnum:]]' -e '^$@$$' | xargs
