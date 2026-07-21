# Elfa Python SDK Makefile

.PHONY: help install install-dev test test-coverage lint format type-check clean build upload upload-test

# Default target
help:
	@echo "Elfa Python SDK - Available commands:"
	@echo ""
	@echo "Development:"
	@echo "  install       Install package in development mode"
	@echo "  install-dev   Install with development dependencies"
	@echo "  test          Run all tests"
	@echo "  test-coverage Run tests with coverage report"
	@echo "  lint          Run linting (flake8)"
	@echo "  format        Format code (black + isort)"
	@echo "  type-check    Run type checking (mypy)"
	@echo ""
	@echo "Release:"
	@echo "  clean         Clean build artifacts"
	@echo "  build         Build distribution packages"
	@echo "  upload-test   Upload to TestPyPI"
	@echo "  upload        Upload to PyPI"
	@echo ""

# Development commands
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

test:
	pytest

test-coverage:
	pytest --cov=elfa --cov-report=html --cov-report=term-missing

lint:
	flake8 elfa/ tests/ examples/

format:
	black elfa/ tests/ examples/
	isort elfa/ tests/ examples/

type-check:
	mypy elfa/

# Quality checks (run all)
check: lint type-check test

# Release commands
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build: clean
	python -m build

upload-test: build
	python -m twine upload --repository testpypi dist/*

upload: build
	python -m twine upload dist/*

# Example commands
examples:
	@echo "Running basic example:"
	python examples/basic_usage.py

examples-async:
	@echo "Running async example:"
	python examples/async_usage.py

examples-auto:
	@echo "Running auto + trade example:"
	python examples/auto_and_trade.py

# CI/CD simulation
ci: install-dev lint type-check test-coverage
	@echo "✅ All CI checks passed!"