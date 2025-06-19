# Data engineer toolkit

This repository provides utilities for interacting with AWS services.

## Scripts

- test
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
