.PHONY: venv install install-dev build test tests lint format clean security bandit safety typecheck quality sync

# Create virtual environment using UV
venv:
	uv venv .venv --python 3.9

# Install project dependencies using UV
install:
	uv sync

# Install development dependencies including security tools
install-dev:
	uv sync --dev

# Build project (create venv and install dependencies)
build: venv install-dev

# Sync dependencies (alias for install)
sync:
	uv sync --dev

# Run tests
test tests:
	uv run python -m pytest

# Run linter
lint:
	uv run ruff check .

# Format code
format:
	uv run ruff format .

# Fix linting issues automatically
fix:
	uv run ruff check --fix .

# Security scanning with bandit
bandit:
	@echo "🔒 Running security scan with bandit..."
	uv run bandit -r cli/ s3/ kinesis/ glue/ scripts/ cloudformation/ -f json -o bandit-report.json || true
	@echo "📄 JSON report saved to bandit-report.json"
	uv run bandit -r cli/ s3/ kinesis/ glue/ scripts/ cloudformation/ --severity-level medium --confidence-level medium

# Check for known security vulnerabilities in dependencies
safety:
	@echo "🛡️  Checking dependencies for security vulnerabilities..."
	uv run safety check --output json > safety-report.json 2>/dev/null || true
	@echo "📄 JSON report saved to safety-report.json"
	@echo "⚠️  Note: safety check is deprecated, consider upgrading for newer features"
	uv run safety check || echo "❌ Some vulnerabilities found in dependencies"

# Run all security checks
security: bandit safety
	@echo "✅ Security checks completed. Check bandit-report.json and safety-report.json for details."

# Type checking with mypy
typecheck:
	@echo "🔍 Running type checks with mypy..."
	uv run mypy . --ignore-missing-imports --show-error-codes || true

# Run comprehensive quality checks
quality: lint typecheck security
	@echo "🎯 All quality checks completed!"

# Clean up
clean:
	rm -rf venv .venv __pycache__ */__pycache__ */*/__pycache__
	find . -type f -name "*.pyc" -delete
	rm -f bandit-report.json safety-report.json