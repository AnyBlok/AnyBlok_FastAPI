.PHONY: clean clean-build clean-pyc lint test setup help
.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

setup: ## install python project dependencies
	uv sync --no-dev
	uv run  --no-dev anyblok_createdb -c app.cfg || uv run  --no-dev anyblok_updatedb -c app.cfg

setup-tests: ## install python project dependencies for tests
	uv sync
	uv run anyblok_createdb -c app.test.cfg || uv run anyblok_updatedb -c app.test.cfg

clean: clean-build clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

clean-test: ## remove test artifacts
	rm -fr htmlcov
	rm -fr .pytest_cache
	rm -f .coverage

test: ## run tests
	ANYBLOK_CONFIG_FILE=app.test.cfg uv run pytest -v -s anyblok_fastapi
