.PHONY: venv install build test tests lint format clean

# Create virtual environment using UV
venv:
	uv venv .venv --python 3.9

# Install dependencies using UV
install:
        uv pip install -r requirements.txt
        uv pip install ruff pytest

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

# Clean up
clean:
	rm -rf venv .venv __pycache__ */__pycache__ */*/__pycache__
	find . -type f -name "*.pyc" -delete