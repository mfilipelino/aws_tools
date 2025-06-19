"""List S3 objects with prefix filtering."""
from collections.abc import Iterator
from datetime import datetime, timedelta
from typing import Any, Optional

import click

from cli.base import apply_limit, common_options, format_output
from s3.s3 import create_s3_client


def parse_size(size_str: str) -> int:
    """Parse size string like '1MB', '500KB' to bytes."""
    size_str = size_str.upper()
    multipliers = {
        'B': 1,
        'KB': 1024,
        'MB': 1024 * 1024,
        'GB': 1024 * 1024 * 1024,
        'TB': 1024 * 1024 * 1024 * 1024
    }

    for suffix, multiplier in multipliers.items():
        if size_str.endswith(suffix):
            number = size_str[:-len(suffix)]
            return int(float(number) * multiplier)

    return int(size_str)


def parse_time_delta(time_str: str) -> datetime:
    """Parse time string like '1 hour ago', '2 days ago' to datetime."""
    parts = time_str.lower().split()
    if len(parts) >= 2 and parts[-1] == 'ago':
        amount = int(parts[0])
        unit = parts[1].rstrip('s')  # Remove plural 's'

        if unit == 'minute':
            delta = timedelta(minutes=amount)
        elif unit == 'hour':
            delta = timedelta(hours=amount)
        elif unit == 'day':
            delta = timedelta(days=amount)
        elif unit == 'week':
            delta = timedelta(weeks=amount)
        else:
            raise ValueError(f"Unknown time unit: {unit}")

        return datetime.now() - delta

    # Try to parse as ISO format
    return datetime.fromisoformat(time_str)


def list_s3_objects(bucket: str, prefix: str = '', min_size: Optional[int] = None,
                   max_size: Optional[int] = None, newer_than: Optional[datetime] = None,
                   older_than: Optional[datetime] = None, profile: Optional[str] = None,
                   region: Optional[str] = None, verbose: bool = False) -> Iterator[dict[str, Any]]:
    """List S3 objects with filtering."""
    client = create_s3_client(profile_name=profile, region_name=region)

    paginator = client.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=bucket, Prefix=prefix)

    for page in page_iterator:
        if 'Contents' not in page:
            continue

        for obj in page['Contents']:
            # Apply filters
            if min_size is not None and obj['Size'] < min_size:
                continue
            if max_size is not None and obj['Size'] > max_size:
                continue
            if newer_than is not None and obj['LastModified'].replace(tzinfo=None) < newer_than:
                continue
            if older_than is not None and obj['LastModified'].replace(tzinfo=None) > older_than:
                continue

            result = {
                'key': obj['Key'],
                'size': obj['Size'],
                'last_modified': obj['LastModified'].isoformat(),
                'storage_class': obj.get('StorageClass', 'STANDARD')
            }

            if verbose:
                result['etag'] = obj.get('ETag', '').strip('"')
                result['owner'] = obj.get('Owner', {}).get('DisplayName', '')

            yield result


@click.command('aws-list-s3-objects')
@click.option('--bucket', '-b', required=True, help='S3 bucket name')
@click.option('--prefix', '-p', default='', help='Object key prefix filter')
@click.option('--min-size', help='Minimum object size (e.g., 1MB, 500KB)')
@click.option('--max-size', help='Maximum object size (e.g., 1GB, 100MB)')
@click.option('--newer-than', help='Objects newer than (e.g., "2 days ago", "2024-01-01")')
@click.option('--older-than', help='Objects older than (e.g., "1 hour ago", "2024-12-01")')
@common_options
def cli(bucket, prefix, min_size, max_size, newer_than, older_than,
        profile, region, output_format, limit, output_fields, no_header, verbose):
    """List S3 objects with prefix and size filtering.

    Examples:

        # List all objects in a bucket
        aws-list-s3-objects --bucket my-bucket

        # Filter by prefix and size
        aws-list-s3-objects --bucket my-bucket --prefix logs/2024/ --min-size 1MB

        # Find large files older than 30 days
        aws-list-s3-objects --bucket backups --min-size 1GB --older-than "30 days ago"

        # Output as CSV with specific fields
        aws-list-s3-objects --bucket data --format csv --output-fields key,size

        # Pipe to jq for further processing
        aws-list-s3-objects --bucket logs --prefix error/ | jq '.size' | awk '{sum+=$1} END {print sum}'
    """
    # Parse size filters
    min_size_bytes = parse_size(min_size) if min_size else None
    max_size_bytes = parse_size(max_size) if max_size else None

    # Parse time filters
    newer_than_dt = parse_time_delta(newer_than) if newer_than else None
    older_than_dt = parse_time_delta(older_than) if older_than else None

    # Get objects
    objects = list_s3_objects(
        bucket=bucket,
        prefix=prefix,
        min_size=min_size_bytes,
        max_size=max_size_bytes,
        newer_than=newer_than_dt,
        older_than=older_than_dt,
        profile=profile,
        region=region,
        verbose=verbose
    )

    # Apply limit and format output
    limited_objects = apply_limit(objects, limit)
    format_output(limited_objects, output_format, output_fields, no_header)


if __name__ == '__main__':
    cli()
