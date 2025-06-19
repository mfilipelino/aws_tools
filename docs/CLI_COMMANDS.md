# AWS Tools CLI Commands

This document provides comprehensive documentation for the prefix-based AWS CLI commands provided by this toolkit.

## Overview

The AWS Tools CLI provides focused, Unix-friendly commands that complement the AWS CLI with prefix-based filtering and pipe-friendly output formats. Each command does one thing well and can be easily combined with other Unix tools.

## Installation

```bash
# Install in development mode
pip install -e .

# Or install normally
pip install .
```

## Common Options

All commands share these common options:

- `--profile`: AWS profile to use (default: from environment/config)
- `--region`: AWS region (default: from environment/config)  
- `--format`: Output format: `jsonl` (default), `json`, `tsv`, `csv`, `table`
- `--limit`: Maximum number of results to return
- `--output-fields`: Comma-separated list of fields to output
- `--no-header`: Omit header row for tsv/csv formats
- `--verbose`: Include additional metadata

## Commands

### aws-list-s3-objects

List S3 objects with prefix and size filtering.

#### Options
- `--bucket, -b` (required): S3 bucket name
- `--prefix, -p`: Object key prefix filter
- `--min-size`: Minimum object size (e.g., 1MB, 500KB)
- `--max-size`: Maximum object size (e.g., 1GB, 100MB)
- `--newer-than`: Objects newer than (e.g., "2 days ago", "2024-01-01")
- `--older-than`: Objects older than (e.g., "1 hour ago", "2024-12-01")

#### Examples

```bash
# List all objects in a bucket
aws-list-s3-objects --bucket my-bucket

# Filter by prefix and size
aws-list-s3-objects --bucket my-bucket --prefix logs/2024/ --min-size 1MB

# Find large old files
aws-list-s3-objects --bucket backups --min-size 1GB --older-than "30 days ago"

# Calculate total size of objects matching pattern
aws-list-s3-objects --bucket data --prefix archives/ | \
  jq -r '.size' | awk '{sum+=$1} END {print sum}'

# Find and delete empty objects
aws-list-s3-objects --bucket temp --max-size 0B | \
  jq -r '.key' | \
  xargs -I {} aws s3 rm "s3://temp/{}"

# Generate storage report
aws-list-s3-objects --bucket prod --format csv --output-fields key,size,storage_class > storage-report.csv
```

### aws-list-glue-jobs

List Glue jobs with prefix filtering and last run status.

#### Options
- `--prefix, -p`: Job name prefix filter
- `--status, -s`: Filter by last run status (STARTING, RUNNING, SUCCEEDED, FAILED, etc.)

#### Examples

```bash
# List all Glue jobs
aws-list-glue-jobs

# Filter by prefix
aws-list-glue-jobs --prefix etl-

# Show only failed jobs
aws-list-glue-jobs --status FAILED

# Get job details in table format
aws-list-glue-jobs --prefix prod- --verbose --format table

# Restart failed jobs
aws-list-glue-jobs --status FAILED --prefix nightly- | \
  jq -r '.name' | \
  xargs -I {} aws glue start-job-run --job-name {}

# Monitor long-running jobs
aws-list-glue-jobs --format jsonl | \
  jq 'select(.last_run_status == "RUNNING" and .last_run_duration > 3600)'
```

### aws-list-sagemaker-jobs

List SageMaker jobs (training, processing, transform) with prefix filtering.

#### Options
- `--prefix, -p`: Job name prefix filter
- `--type, -t`: Type of job (training, processing, transform, all)
- `--status, -s`: Filter by status (InProgress, Completed, Failed, etc.)

#### Examples

```bash
# List all SageMaker jobs
aws-list-sagemaker-jobs

# Filter training jobs by prefix
aws-list-sagemaker-jobs --type training --prefix model-v2-

# Show failed processing jobs
aws-list-sagemaker-jobs --type processing --status Failed

# Monitor active training jobs
watch 'aws-list-sagemaker-jobs --type training --status InProgress --format table'

# Calculate training costs (approximate)
aws-list-sagemaker-jobs --type training --status Completed | \
  jq -r 'select(.instance_type == "ml.p3.2xlarge") | .training_time_seconds' | \
  awk '{sum+=$1} END {print "Total hours:", sum/3600}'

# Find jobs using specific instance types
aws-list-sagemaker-jobs --verbose | \
  jq 'select(.instance_type | startswith("ml.p3"))'
```

### aws-list-kinesis-streams

List Kinesis streams with prefix filtering.

#### Options
- `--prefix, -p`: Stream name prefix filter

#### Examples

```bash
# List all Kinesis streams
aws-list-kinesis-streams

# Filter by prefix
aws-list-kinesis-streams --prefix clickstream-

# Get detailed stream information
aws-list-kinesis-streams --verbose --format table

# Find on-demand streams
aws-list-kinesis-streams --verbose | jq 'select(.mode == "ON_DEMAND")'

# Monitor stream health
aws-list-kinesis-streams --verbose --format jsonl | \
  jq 'select(.status != "ACTIVE")'

# Generate stream inventory
aws-list-kinesis-streams --verbose --format csv > kinesis-inventory.csv
```

### aws-list-athena-tables

List Athena tables from the Glue Data Catalog with prefix filtering.

#### Options
- `--database, -d`: Database name (default: "default")
- `--prefix, -p`: Table name prefix filter

#### Examples

```bash
# List all tables in default database
aws-list-athena-tables

# List tables in specific database with prefix
aws-list-athena-tables --database analytics --prefix raw_

# Find large tables
aws-list-athena-tables --verbose | \
  jq 'select(.size_bytes > 1073741824) | {table, size_gb: (.size_bytes/1073741824)}'

# Find partitioned tables
aws-list-athena-tables --verbose | jq 'select(.partition_count > 0)'

# Export table schemas
aws-list-athena-tables --database prod --verbose --format json > table-schemas.json

# Find tables by location
aws-list-athena-tables --verbose | \
  jq 'select(.location | contains("s3://data-lake"))'

# Generate DDL statements
aws-list-athena-tables --prefix user_ | \
  jq -r '.table' | \
  xargs -I {} aws athena get-table-metadata --database-name default --table-name {}
```

## Advanced Use Cases

### Cross-Service Workflows

#### 1. Data Pipeline Monitoring
```bash
# Check if Glue job completed before querying Athena
JOB_STATUS=$(aws-list-glue-jobs --prefix daily-etl- --format jsonl | jq -r '.last_run_status' | head -1)
if [ "$JOB_STATUS" = "SUCCEEDED" ]; then
  aws-list-athena-tables --prefix daily_ | jq -r '.table' | head -1 | \
    xargs -I {} aws athena start-query-execution --query-string "SELECT COUNT(*) FROM {}"
fi
```

#### 2. Cost Optimization
```bash
# Find and report on expensive resources
{
  echo "=== Large S3 Objects ==="
  aws-list-s3-objects --bucket data --min-size 10GB --format jsonl | \
    jq '{key, size_gb: (.size/1073741824)}' | head -10
  
  echo -e "\n=== Long Running SageMaker Jobs ==="
  aws-list-sagemaker-jobs --type training --verbose | \
    jq 'select(.training_time_seconds > 7200) | {name, hours: (.training_time_seconds/3600), instance_type}'
  
  echo -e "\n=== High Shard Count Kinesis Streams ==="
  aws-list-kinesis-streams --verbose | \
    jq 'select(.shard_count > 10) | {name, shard_count}'
} > cost-report.txt
```

#### 3. Automated Cleanup
```bash
# Clean up old failed jobs
aws-list-glue-jobs --status FAILED --format jsonl | \
  jq -r 'select(.last_run_time | fromdateiso8601 < (now - 86400*7)) | .name' | \
  while read job; do
    echo "Deleting old failed job: $job"
    aws glue delete-job --job-name "$job"
  done

# Archive old S3 objects
aws-list-s3-objects --bucket logs --prefix app/ --older-than "90 days ago" | \
  jq -r '.key' | \
  xargs -P 10 -I {} aws s3 cp "s3://logs/{}" "s3://archive/{}" --storage-class GLACIER
```

#### 4. Resource Tagging Audit
```bash
# Find untagged resources by checking multiple services
{
  aws-list-glue-jobs --verbose | jq 'select(.properties.tags == null) | {service: "glue", name}'
  aws-list-kinesis-streams | jq '{service: "kinesis", name}'
  aws-list-athena-tables | jq '{service: "athena", name: .table}'
} | jq -s 'flatten | group_by(.service) | map({service: .[0].service, count: length})'
```

### Integration with Other Tools

#### With GNU Parallel
```bash
# Process multiple prefixes in parallel
echo -e "logs/\ndata/\nbackups/" | \
  parallel -j 3 'aws-list-s3-objects --bucket mybucket --prefix {} | wc -l'
```

#### With SQLite
```bash
# Import data into SQLite for complex queries
aws-list-sagemaker-jobs --verbose --format csv > jobs.csv
sqlite3 jobs.db <<EOF
.mode csv
.import jobs.csv jobs
SELECT type, status, COUNT(*), AVG(training_time_seconds) 
FROM jobs 
GROUP BY type, status;
EOF
```

#### With Python
```python
import subprocess
import json

# Get all failed jobs and analyze patterns
result = subprocess.run(
    ['aws-list-glue-jobs', '--status', 'FAILED', '--format', 'jsonl'],
    capture_output=True, text=True
)

failed_jobs = [json.loads(line) for line in result.stdout.strip().split('\n')]
failure_patterns = {}
for job in failed_jobs:
    prefix = job['name'].split('-')[0]
    failure_patterns[prefix] = failure_patterns.get(prefix, 0) + 1

print("Failure patterns by prefix:", failure_patterns)
```

## Performance Tips

1. **Use --limit for testing**: When developing scripts, use `--limit 10` to test with small datasets
2. **Leverage streaming**: The default `jsonl` format streams results, allowing processing to start immediately
3. **Combine filters**: Use multiple filters (prefix, status, time) to reduce the result set at the source
4. **Cache results**: For expensive operations, cache results: `aws-list-* > cache.jsonl`

## Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   # Check your AWS credentials
   aws sts get-caller-identity
   
   # Use a different profile
   aws-list-s3-objects --profile prod --bucket my-bucket
   ```

2. **Rate Limiting**
   ```bash
   # Add delays between calls
   aws-list-glue-jobs | while read -r line; do
     echo "$line" | jq -r '.name'
     sleep 0.1
   done
   ```

3. **Large Result Sets**
   ```bash
   # Use pagination with limit
   OFFSET=0
   while true; do
     RESULTS=$(aws-list-s3-objects --bucket huge-bucket --limit 1000)
     if [ -z "$RESULTS" ]; then break; fi
     echo "$RESULTS"
     OFFSET=$((OFFSET + 1000))
   done
   ```