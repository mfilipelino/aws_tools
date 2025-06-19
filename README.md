# Data engineer toolkit

This repository provides utilities for interacting with AWS services.

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
