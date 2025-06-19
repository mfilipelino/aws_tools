"""List Kinesis streams with prefix filtering."""
from collections.abc import Iterator
from typing import Any, Optional

import click

from cli.base import apply_limit, common_options, format_output
from kinesis.kinesis import create_kinesis_client


def list_kinesis_streams(prefix: str = '', profile: Optional[str] = None,
                        region: Optional[str] = None, verbose: bool = False) -> Iterator[dict[str, Any]]:
    """List Kinesis streams with filtering."""
    client = create_kinesis_client(profile_name=profile, region_name=region)

    paginator = client.get_paginator('list_streams')
    page_iterator = paginator.paginate()

    for page in page_iterator:
        for stream_name in page.get('StreamNames', []):
            # Apply prefix filter
            if prefix and not stream_name.startswith(prefix):
                continue

            result = {
                'name': stream_name
            }

            # Get detailed info if verbose
            if verbose:
                try:
                    describe_response = client.describe_stream(StreamName=stream_name)
                    stream_desc = describe_response['StreamDescription']

                    result.update({
                        'status': stream_desc['StreamStatus'],
                        'mode': stream_desc.get('StreamModeDetails', {}).get('StreamMode', 'PROVISIONED'),
                        'retention_hours': stream_desc['RetentionPeriodHours'],
                        'shard_count': len(stream_desc['Shards']),
                        'created_at': stream_desc['StreamCreationTimestamp'].isoformat(),
                        'arn': stream_desc['StreamARN']
                    })

                    # Get enhanced monitoring if available
                    monitoring = stream_desc.get('EnhancedMonitoring', [])
                    if monitoring:
                        result['monitoring_level'] = monitoring[0].get('ShardLevelMetrics', [])
                except Exception as e:
                    # If we can't get details, just include basic info
                    result['error'] = str(e)

            yield result


@click.command('aws-list-kinesis-streams')
@click.option('--prefix', '-p', default='', help='Stream name prefix filter')
@common_options
def cli(prefix, profile, region, output_format, limit, output_fields, no_header, verbose):
    """List Kinesis streams with prefix filtering.

    Examples:

        # List all Kinesis streams
        aws-list-kinesis-streams

        # Filter by prefix
        aws-list-kinesis-streams --prefix clickstream-

        # Get detailed information
        aws-list-kinesis-streams --verbose --format table

        # Export to JSON with full details
        aws-list-kinesis-streams --verbose --format json > streams.json

        # Count streams by prefix
        aws-list-kinesis-streams --prefix prod- | wc -l

        # Find on-demand streams
        aws-list-kinesis-streams --verbose | jq 'select(.mode == "ON_DEMAND")'
    """
    # Get streams
    streams = list_kinesis_streams(
        prefix=prefix,
        profile=profile,
        region=region,
        verbose=verbose
    )

    # Apply limit and format output
    limited_streams = apply_limit(streams, limit)
    format_output(limited_streams, output_format, output_fields, no_header)


if __name__ == '__main__':
    cli()
