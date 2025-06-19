"""List Athena tables with prefix filtering."""
import os
from collections.abc import Iterator
from typing import Any, Optional

import boto3
import click

from cli.base import apply_limit, common_options, format_output


def create_athena_client(profile_name: Optional[str] = None, region_name: Optional[str] = None):
    """Create an Athena client with the specified profile."""
    profile_name = profile_name or os.environ.get("PROFILE_NAME", "sandbox")
    session = boto3.Session(profile_name=profile_name)
    return session.client('athena', region_name=region_name)


def create_glue_client(profile_name: Optional[str] = None, region_name: Optional[str] = None):
    """Create a Glue client for accessing the data catalog."""
    profile_name = profile_name or os.environ.get("PROFILE_NAME", "sandbox")
    session = boto3.Session(profile_name=profile_name)
    return session.client('glue', region_name=region_name)


def list_athena_tables(database: str, prefix: str = '', profile: Optional[str] = None,
                      region: Optional[str] = None, verbose: bool = False) -> Iterator[dict[str, Any]]:
    """List Athena tables from the Glue Data Catalog."""
    glue_client = create_glue_client(profile_name=profile, region_name=region)

    paginator = glue_client.get_paginator('get_tables')
    page_iterator = paginator.paginate(DatabaseName=database)

    for page in page_iterator:
        for table in page.get('TableList', []):
            table_name = table['Name']

            # Apply prefix filter
            if prefix and not table_name.startswith(prefix):
                continue

            result = {
                'database': database,
                'table': table_name,
                'type': table.get('TableType', 'EXTERNAL_TABLE'),
                'created_time': table.get('CreateTime', '').isoformat() if table.get('CreateTime') else '',
                'updated_time': table.get('UpdateTime', '').isoformat() if table.get('UpdateTime') else ''
            }

            # Add storage info
            storage_desc = table.get('StorageDescriptor', {})
            if storage_desc:
                result['location'] = storage_desc.get('Location', '')
                result['input_format'] = storage_desc.get('InputFormat', '').split('.')[-1] if storage_desc.get('InputFormat') else ''
                result['output_format'] = storage_desc.get('OutputFormat', '').split('.')[-1] if storage_desc.get('OutputFormat') else ''

                # Try to get compressed format
                serde_info = storage_desc.get('SerdeInfo', {})
                if serde_info:
                    result['serde'] = serde_info.get('SerializationLibrary', '').split('.')[-1]

            if verbose:
                # Add column information
                columns = storage_desc.get('Columns', [])
                result['column_count'] = len(columns)
                result['columns'] = [{'name': col['Name'], 'type': col.get('Type', '')} for col in columns]

                # Add partition information
                partition_keys = table.get('PartitionKeys', [])
                result['partition_count'] = len(partition_keys)
                result['partition_keys'] = [col['Name'] for col in partition_keys]

                # Add table properties
                result['properties'] = table.get('Parameters', {})

                # Try to get table size from properties
                if 'totalSize' in result['properties']:
                    result['size_bytes'] = int(result['properties']['totalSize'])
                elif 'rawDataSize' in result['properties']:
                    result['size_bytes'] = int(result['properties']['rawDataSize'])

            yield result


@click.command('aws-list-athena-tables')
@click.option('--database', '-d', default='default', help='Athena database name')
@click.option('--prefix', '-p', default='', help='Table name prefix filter')
@common_options
def cli(database, prefix, profile, region, output_format, limit, output_fields, no_header, verbose):
    """List Athena tables with prefix filtering.

    Examples:

        # List all tables in default database
        aws-list-athena-tables

        # List tables in specific database with prefix
        aws-list-athena-tables --database analytics --prefix raw_

        # Get detailed table information
        aws-list-athena-tables --verbose --format table

        # Find partitioned tables
        aws-list-athena-tables --verbose | jq 'select(.partition_count > 0)'

        # Export table schema to JSON
        aws-list-athena-tables --database prod --verbose --format json > schema.json

        # Find tables by location pattern
        aws-list-athena-tables --verbose | jq 'select(.location | contains("s3://my-bucket"))'
    """
    # Get tables
    tables = list_athena_tables(
        database=database,
        prefix=prefix,
        profile=profile,
        region=region,
        verbose=verbose
    )

    # Apply limit and format output
    limited_tables = apply_limit(tables, limit)
    format_output(limited_tables, output_format, output_fields, no_header)


if __name__ == '__main__':
    cli()
