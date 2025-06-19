# Data engineer toolkit

This repository provides utilities for interacting with AWS services.

## Scripts

- test
- `scripts/kinesis_cli.py` - example of writing records to Kinesis.
- `scripts/export_metadata.py` - extract metadata from AWS services and store it in a local DuckDB database. Supported resources include S3 objects, Athena tables and errors, Glue jobs and runs, and Sagemaker pipelines, training, and processing jobs.
