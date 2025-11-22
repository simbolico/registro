PYTHON ?= python

.PHONY: install-dev install format lint type test coverage clean pre-commit build publish check-release

# Installation
install-dev:
	$(PYTHON) -m pip install -U pip
	$(PYTHON) -m pip install -e .[dev]
	$(PYTHON) -m pip install pre-commit twine build
	pre-commit install

install:
	$(PYTHON) -m pip install .

# Code Quality
format:
	black .
	ruff format .

lint:
	ruff check .
	black --check .

type:
	mypy registro

fix:
	ruff check --fix .
	black .
	ruff format .

# Testing
test:
	pytest -q

test-verbose:
	pytest -v

coverage:
	pytest --cov=registro --cov-report=term-missing --cov-report=xml --cov-fail-under=100

coverage-html:
	pytest --cov=registro --cov-report=html
	@echo "Coverage report generated in htmlcov/index.html"

# Pre-commit
pre-commit:
	pre-commit run --all-files

pre-commit-update:
	pre-commit autoupdate

# Build and Release
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +

build: clean
	$(PYTHON) -m build

check-release: build
	twine check dist/*

publish-test: check-release
	twine upload --repository testpypi dist/*

publish: check-release
	twine upload dist/*

# Development workflow
dev-setup: install-dev
	@echo "Development environment setup complete!"
	@echo "Run 'make test' to verify everything is working."

dev-test: lint type test
	@echo "All checks passed!"

# Version and Release
version:
	@$(PYTHON) -c "import registro; print(registro.__version__)"

tag:
	git tag v$$($(PYTHON) -c "import registro; print(registro.__version__)")
	git push origin v$$($(PYTHON) -c "import registro; print(registro.__version__)")

# Help
help:
	@echo "Available targets:"
	@echo "  install-dev    - Install development dependencies"
	@echo "  install        - Install package"
	@echo "  format         - Format code with black and ruff"
	@echo "  lint           - Check code with ruff and black"
	@echo "  type           - Run mypy type checking"
	@echo "  fix            - Auto-fix code formatting issues"
	@echo "  test           - Run tests"
	@echo "  test-verbose   - Run tests with verbose output"
	@echo "  coverage       - Run tests with coverage"
	@echo "  coverage-html  - Generate HTML coverage report"
	@echo "  pre-commit     - Run pre-commit hooks"
	@echo "  build          - Build package"
	@echo "  check-release  - Check package before release"
	@echo "  publish        - Publish to PyPI"
	@echo "  clean          - Clean build artifacts"
	@echo "  dev-setup      - Set up development environment"
	@echo "  dev-test       - Run lint, type check and tests"
	@echo "  version        - Show current version"
	@echo "  tag            - Create and push git tag"

