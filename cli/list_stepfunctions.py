"""List Step Functions state machines with filtering."""
import re  # Import the 're' module for regex operations
import sys
from collections.abc import Iterator
from typing import Any, Optional

import click

from cli.base import apply_limit, common_options, format_output
from stepfunctions.stepfunctions import create_stepfunctions_client  # Correct import


def list_stepfunctions(
    prefix: Optional[str] = None,
    regex_pattern: Optional[str] = None, # Renamed for clarity
    tags_filter: Optional[list[str]] = None, # Renamed for clarity, expecting list of 'Key=Value'
    profile: Optional[str] = None,
    region: Optional[str] = None,
    verbose: bool = False # Added verbose flag
) -> Iterator[dict[str, Any]]:
    """List Step Functions state machines with filtering."""
    client = create_stepfunctions_client(profile_name=profile, region_name=region)
    paginator = client.get_paginator('list_state_machines')

    # Parse tags filter
    parsed_tags_filter = {}
    if tags_filter:
        for tag_item in tags_filter:
            if '=' not in tag_item:
                # Handle error or skip malformed tag
                print(f"Warning: Malformed tag '{tag_item}', skipping. Expected format: Key=Value", file=sys.stderr)
                continue
            key, value = tag_item.split('=', 1)
            parsed_tags_filter[key] = value

    for page in paginator.paginate():
        for sm in page['stateMachines']:
            state_machine_arn = sm['stateMachineArn']
            state_machine_name = sm['name']

            # Apply prefix filter
            if prefix and not state_machine_name.startswith(prefix):
                continue

            # Apply regex filter
            if regex_pattern and not re.search(regex_pattern, state_machine_name):
                continue

            # Apply tags filter
            if parsed_tags_filter:
                try:
                    sm_tags_response = client.list_tags_for_resource(resourceArn=state_machine_arn)
                    sm_tags = {tag['key']: tag['value'] for tag in sm_tags_response.get('tags', [])}

                    match = True
                    for key, value in parsed_tags_filter.items():
                        if sm_tags.get(key) != value:
                            match = False
                            break
                    if not match:
                        continue
                except Exception as e:
                    # Handle cases where tags cannot be fetched (e.g., permissions)
                    print(f"Warning: Could not retrieve tags for {state_machine_arn}: {e}", file=sys.stderr)
                    if parsed_tags_filter: # If filtering by tags is active, skip if tags can't be checked
                        continue


            result = {
                'name': state_machine_name,
                'arn': state_machine_arn,
                'type': sm['type'],
                'creationDate': sm['creationDate'].isoformat(),
            }

            if verbose:
                # Add more details if verbose mode is enabled
                try:
                    description = client.describe_state_machine(stateMachineArn=state_machine_arn)
                    result['status'] = description.get('status', 'UNKNOWN')
                    result['roleArn'] = description.get('roleArn', '')
                    # Potentially add more fields from describe_state_machine if needed
                except Exception as e:
                    print(f"Warning: Could not describe state machine {state_machine_arn}: {e}", file=sys.stderr)
                    result['status'] = 'ERROR_FETCHING_DETAILS'


            yield result

# Placeholder for the CLI command - will be updated in the next step
@click.command('aws-list-stepfunctions')
@click.option('--prefix', '-p', help='Filter state machines by name prefix.')
@click.option('--regex', help='Filter state machines by name regex.')
@click.option('--tag', 'tags_filter', multiple=True, help='Filter state machines by tag (e.g., Key=Value). Can be specified multiple times.')
@common_options
def cli(
    prefix: Optional[str],
    regex: Optional[str],
    tags_filter: Optional[list[str]],
    profile: Optional[str],
    region: Optional[str],
    output_format: str,
    limit: Optional[int],
    output_fields: Optional[str],
    no_header: bool,
    verbose: bool
):
    """List Step Functions state machines with filtering options."""
    state_machines = list_stepfunctions(
        prefix=prefix,
        regex_pattern=regex, # Pass correct parameter name
        tags_filter=tags_filter,
        profile=profile,
        region=region,
        verbose=verbose
    )
    limited_state_machines = apply_limit(state_machines, limit)
    format_output(limited_state_machines, output_format, output_fields, no_header)

if __name__ == '__main__':
    cli()
