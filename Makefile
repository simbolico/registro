PYTHON ?= python

.PHONY: install-dev format lint type test coverage pre-commit

install-dev:
	$(PYTHON) -m pip install -U pip
	$(PYTHON) -m pip install -e .[dev]
	$(PYTHON) -m pip install pre-commit
	pre-commit install

format:
	black .
	ruff format .

lint:
	ruff check .
	black --check .

type:
	mypy registro

test:
	pytest -q

coverage:
	pytest -q --cov=registro --cov-report=term-missing --cov-report=xml

pre-commit:
	pre-commit run --all-files

