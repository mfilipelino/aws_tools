# Security Tools Integration

This document explains how to use the integrated security tools in the AWS Tools project.

## Available Security Commands

### Quick Start
```bash
# Install development dependencies (includes security tools)
make install-dev

# Run all security checks
make security

# Run comprehensive quality checks (lint + typecheck + security)
make quality
```

## Individual Commands

### 🔒 **Bandit - Security Vulnerability Scanner**

Scans Python code for common security issues:

```bash
# Run security scan
make bandit

# Output: Shows security issues in terminal + JSON report
```

**What Bandit Checks:**
- Hardcoded passwords/secrets
- SQL injection vulnerabilities
- Shell injection risks
- Insecure cryptographic practices
- Unsafe file operations

**Current Findings in Project:**
- ⚠️ **Medium Severity**: SQL injection in `scripts/export_metadata.py:161`
  - Issue: `f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df"`
  - Recommendation: Use parameterized queries

### 🛡️ **Safety - Dependency Vulnerability Scanner**

Checks for known security vulnerabilities in dependencies:

```bash
# Check dependencies
make safety

# Output: Shows vulnerable packages with CVE details
```

**Current Vulnerabilities Found:**
- `urllib3 1.26.10` - 3 vulnerabilities (CVE-2024-37891, CVE-2023-43804, CVE-2023-45803)
- `ipython 8.4.0` - 1 vulnerability (CVE-2023-24816)

**Recommendations:**
```bash
# Update vulnerable packages
uv pip install urllib3>=1.26.18 ipython>=8.10.0
```

### 🔍 **MyPy - Static Type Checking**

Validates type annotations and catches type-related bugs:

```bash
# Run type checking
make typecheck

# Output: Shows type errors and missing type stubs
```

**Current Issues:**
- Missing type stubs for `tabulate` library
- Duplicate module detection for `glue.glue`

## Reports Generated

All commands generate both console output and JSON reports:

- `bandit-report.json` - Detailed security findings
- `safety-report.json` - Dependency vulnerability details

## Integration Examples

### CI/CD Pipeline
```yaml
# .github/workflows/security.yml
name: Security Checks
on: [push, pull_request]
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - run: make install-dev
      - run: make security
      - uses: actions/upload-artifact@v4
        with:
          name: security-reports
          path: '*-report.json'
```

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/PyCQA/bandit
    rev: 1.8.5
    hooks:
      - id: bandit
        args: ['-r', 'cli/', 's3/', 'kinesis/', 'glue/', 'scripts/']
```

### Development Workflow
```bash
# Before committing code
make quality

# Fix any issues found
# For security issues in bandit:
# - Add # nosec comment if false positive
# - Fix the actual security issue

# For dependency vulnerabilities:
uv pip install package>=secure_version
```

## Security Issue Resolution

### SQL Injection Fix Example
```python
# Before (flagged by bandit)
con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df")

# After (secure)
con.execute("CREATE OR REPLACE TABLE ? AS SELECT * FROM df", (table_name,))
# or use DuckDB's identifier escaping
import duckdb
safe_table_name = duckdb.identifier(table_name)
con.execute(f"CREATE OR REPLACE TABLE {safe_table_name} AS SELECT * FROM df")
```

### Dependency Updates
```bash
# Check current versions
uv pip freeze | grep -E "(urllib3|ipython)"

# Update to secure versions
uv pip install "urllib3>=1.26.18" "ipython>=8.10.0"

# Verify fixes
make safety
```

## Configuration Files

### Bandit Configuration (`.bandit`)
```ini
[bandit]
exclude_dirs = ['tests', '.venv', 'venv', '__pycache__', '.git']
skips = ['B101']  # Skip assert usage warnings
```

### MyPy Configuration (Optional: `mypy.ini`)
```ini
[mypy]
python_version = 3.9
warn_return_any = True
warn_unused_configs = True
ignore_missing_imports = True
```

## Best Practices

1. **Run security checks regularly** - Include in CI/CD
2. **Fix high/medium severity issues** immediately
3. **Keep dependencies updated** - Use dependabot or regular manual updates
4. **Review bandit findings** - Don't blindly ignore with # nosec
5. **Use type hints** - Helps catch bugs early with mypy

## Troubleshooting

### Common Issues

1. **Bandit timeout on large codebases**
   - Solution: Scan specific directories as configured

2. **Safety requires registration**
   - Current: Using deprecated `check` command
   - Future: Consider upgrading to commercial license

3. **MyPy missing type stubs**
   ```bash
   # Install missing stubs
   uv pip install types-tabulate
   ```

4. **False positives in bandit**
   ```python
   # Use nosec with specific test ID
   password = get_password()  # nosec B105
   ```

## Summary

The integrated security tools provide comprehensive coverage:
- **Code vulnerabilities** (bandit)
- **Dependency vulnerabilities** (safety)  
- **Type safety** (mypy)
- **Code quality** (ruff)

Regular use of `make quality` ensures high code quality and security standards.