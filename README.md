# Data engineer toolkit

This repository provides utilities for interacting with AWS services.

## Prerequisites

Before getting started, ensure you have the following tools installed:

### Required Tools

1. **UV** - Modern Python package manager
   ```bash
   # Install via official installer
   curl -LsSf https://astral.sh/uv/install.sh | sh
   # Or via Homebrew (macOS)
   brew install uv
   ```

2. **Python 3.9+** - Required Python version
   ```bash
   # UV can install Python for you
   uv python install 3.9
   ```

3. **Make** - Build automation tool
   - Usually pre-installed on macOS/Linux
   - macOS: `xcode-select --install` if not present

4. **AWS CLI** - For AWS credentials management
   ```bash
   brew install awscli  # macOS
   # Or see: https://aws.amazon.com/cli/
   ```

### Optional Tools

- **act** - Run GitHub Actions locally
  ```bash
  brew install act  # macOS
  # Or see: https://github.com/nektos/act
  ```

### Quick Setup

```bash
# 1. Clone the repository
git clone <repository-url>
cd aws_tools

# 2. Set up the development environment
make build  # Creates venv and installs all dependencies

# 3. Configure AWS credentials
aws configure --profile sandbox
# Or use a different profile:
export PROFILE_NAME=your-profile

# 4. Verify installation
make test
```

## CLI Commands

Prefix-based CLI commands that complement AWS CLI with pipe-friendly output:

- `aws-list-s3-objects` - List S3 objects with prefix/size/time filtering
- `aws-list-glue-jobs` - List Glue jobs with prefix and status filtering  
- `aws-list-sagemaker-jobs` - List SageMaker training/processing/transform jobs
- `aws-list-kinesis-streams` - List Kinesis streams with prefix filtering
- `aws-list-athena-tables` - List Athena tables from Glue Data Catalog

See [CLI_COMMANDS.md](docs/CLI_COMMANDS.md) for detailed usage examples.

## Scripts

- `scripts/kinesis_cli.py` - example of writing records to Kinesis.
- `scripts/export_metadata.py` - extract metadata from AWS services and store it in a local DuckDB database. Supported resources include S3 objects, Athena tables and errors, Glue jobs and runs, and Sagemaker pipelines, training, and processing jobs.
- `scripts/stepfunctions_cli.py` - Lists failed AWS Step Function executions within a specified number of days and can generate rerun commands.
  - **Purpose**: Helps identify and optionally prepare rerun commands for failed Step Function executions.
  - **Prerequisites**:
    - AWS CLI installed and configured with necessary permissions (`states:ListExecutions`, `states:DescribeExecution`, `states:StartExecution`).
  - **Usage**:
    ```bash
    python scripts/stepfunctions_cli.py --state-machine-arn <YOUR_STATE_MACHINE_ARN> --days <NUMBER_OF_DAYS> [--output-rerun-commands]
    ```
  - **Arguments**:
    - `--state-machine-arn YOUR_STATE_MACHINE_ARN`: (Required) The ARN of the AWS Step Function state machine.
    - `--days NUMBER_OF_DAYS`: (Required) The number of past days to check for failed executions (e.g., 7 for the last 7 days).
    - `--output-rerun-commands`: (Optional) If specified, the script will generate `aws stepfunctions start-execution` commands for each failed execution. Otherwise, it will only list the failed executions and their inputs.
  - **Example**:
    To list failed executions for `arn:aws:states:us-east-1:123456789012:stateMachine:MyStateMachine` in the last 3 days:
    ```bash
    python scripts/stepfunctions_cli.py --state-machine-arn arn:aws:states:us-east-1:123456789012:stateMachine:MyStateMachine --days 3
    ```
    To also generate rerun commands:
    ```bash
    python scripts/stepfunctions_cli.py --state-machine-arn arn:aws:states:us-east-1:123456789012:stateMachine:MyStateMachine --days 3 --output-rerun-commands
    ```
  - **Note**: This script generates AWS CLI commands for inspection. You need to copy, review, and execute these commands in your terminal if you choose to rerun the Step Functions. It also mentions the `aws stepfunctions redrive-execution` command as a potential alternative for compatible (Standard) workflows if the failure is within the last 14 days, which can be simpler as it doesn't require providing the input again.
