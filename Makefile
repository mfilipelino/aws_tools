.PHONY: venv install install-dev build test tests lint format clean security bandit safety typecheck quality

# Create virtual environment using UV
venv:
	uv venv .venv --python 3.9

# Install dependencies using UV
install:
        uv pip install -r requirements.txt
        uv pip install ruff pytest

# Install development dependencies including security tools
install-dev: install
	uv pip install bandit safety mypy

# Build project (create venv and install dependencies)
build: venv install

# Run tests
test tests:
        .venv/bin/python -m pytest

# Run linter
lint:
	.venv/bin/ruff check .

# Format code
format:
	.venv/bin/ruff format .

# Fix linting issues automatically
fix:
	.venv/bin/ruff check --fix .

# Security scanning with bandit
bandit:
	@echo "🔒 Running security scan with bandit..."
	.venv/bin/bandit -r cli/ s3/ kinesis/ glue/ scripts/ -f json -o bandit-report.json || true
	@echo "📄 JSON report saved to bandit-report.json"
	.venv/bin/bandit -r cli/ s3/ kinesis/ glue/ scripts/ --severity-level medium --confidence-level medium

# Check for known security vulnerabilities in dependencies
safety:
	@echo "🛡️  Checking dependencies for security vulnerabilities..."
	.venv/bin/safety check --output json > safety-report.json 2>/dev/null || true
	@echo "📄 JSON report saved to safety-report.json"
	@echo "⚠️  Note: safety check is deprecated, consider upgrading for newer features"
	.venv/bin/safety check || echo "❌ Some vulnerabilities found in dependencies"

# Run all security checks
security: bandit safety
	@echo "✅ Security checks completed. Check bandit-report.json and safety-report.json for details."

# Type checking with mypy
typecheck:
	@echo "🔍 Running type checks with mypy..."
	.venv/bin/mypy . --ignore-missing-imports --show-error-codes || true

# Run comprehensive quality checks
quality: lint typecheck security
	@echo "🎯 All quality checks completed!"

# Clean up
clean:
	rm -rf venv .venv __pycache__ */__pycache__ */*/__pycache__
	find . -type f -name "*.pyc" -delete
	rm -f bandit-report.json safety-report.json