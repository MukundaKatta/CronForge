.PHONY: install test lint format clean help

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install package and dev dependencies
	pip install -e ".[dev]"

test: ## Run tests with pytest
	pytest tests/ -v --tb=short

lint: ## Run linter (ruff)
	ruff check src/ tests/

format: ## Format code with ruff
	ruff format src/ tests/

typecheck: ## Run mypy type checking
	mypy src/cronforge/ --ignore-missing-imports

clean: ## Remove build artifacts
	rm -rf build/ dist/ *.egg-info src/*.egg-info .pytest_cache .mypy_cache __pycache__
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

all: install lint typecheck test ## Install, lint, typecheck, and test
