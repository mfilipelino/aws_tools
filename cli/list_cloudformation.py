"""List CloudFormation stacks with filtering options."""

import re
from collections.abc import Iterator
from typing import Any, Optional

import click

from aws_clients import create_aws_client
from cli.base import apply_limit, common_options, format_output


def list_cloudformation_stacks(
    name_prefix: Optional[str] = None,
    tag_filters: Optional[dict[str, str]] = None,
    name_regex: Optional[str] = None,
    stack_status_filter: Optional[list[str]] = None,
    profile: Optional[str] = None,
    verbose: bool = False,
) -> Iterator[dict[str, Any]]:
    """List CloudFormation stacks with filtering."""
    client = create_aws_client("cloudformation", profile_name=profile)

    # Build pagination parameters
    params = {}
    if stack_status_filter:
        params["StackStatusFilter"] = stack_status_filter

    paginator = client.get_paginator("list_stacks")
    page_iterator = paginator.paginate(**params)

    # Compile regex pattern if provided
    regex_pattern = re.compile(name_regex) if name_regex else None

    for page in page_iterator:
        for stack in page.get("StackSummaries", []):
            stack_name = stack.get("StackName", "")

            # Apply name prefix filter
            if name_prefix and not stack_name.startswith(name_prefix):
                continue

            # Apply regex filter
            if regex_pattern and not regex_pattern.search(stack_name):
                continue

            # Apply tag filters if specified
            if tag_filters and not _match_tags(client, stack_name, tag_filters):
                continue

            result = {
                "stack_name": stack_name,
                "stack_id": stack.get("StackId"),
                "creation_time": stack.get("CreationTime").isoformat() if stack.get("CreationTime") else None,
                "last_updated_time": stack.get("LastUpdatedTime").isoformat() if stack.get("LastUpdatedTime") else None,
                "stack_status": stack.get("StackStatus"),
                "template_description": stack.get("TemplateDescription"),
            }

            if verbose:
                result.update(
                    {
                        "deletion_time": stack.get("DeletionTime").isoformat() if stack.get("DeletionTime") else None,
                        "stack_status_reason": stack.get("StackStatusReason"),
                        "drift_information": stack.get("DriftInformation"),
                    }
                )

            yield result


def _match_tags(client, stack_name: str, tag_filters: dict[str, str]) -> bool:
    """Check if a stack matches the specified tag filters."""
    try:
        response = client.describe_stacks(StackName=stack_name)
        stacks = response.get("Stacks", [])

        if not stacks:
            return False

        stack_tags = stacks[0].get("Tags", [])
        stack_tag_dict = {tag["Key"]: tag["Value"] for tag in stack_tags}

        # Check if all tag filters match
        for key, value in tag_filters.items():
            if key not in stack_tag_dict or stack_tag_dict[key] != value:
                return False

        return True

    except Exception:
        return False


def parse_tag_filters(tag_string: str) -> dict[str, str]:
    """Parse tag filter string like 'Environment=prod,Team=backend' into dict."""
    if not tag_string:
        return {}

    tags = {}
    for pair in tag_string.split(","):
        if "=" in pair:
            key, value = pair.split("=", 1)
            tags[key.strip()] = value.strip()

    return tags


def parse_status_filters(status_string: str) -> list[str]:
    """Parse status filter string like 'CREATE_COMPLETE,UPDATE_COMPLETE' into list."""
    if not status_string:
        return []

    return [status.strip() for status in status_string.split(",")]


@click.command("aws-list-cloudformation-stacks")
@click.option("--name-prefix", "-p", help="Filter stacks by name prefix")
@click.option("--name-regex", "-r", help="Filter stacks by name regex pattern")
@click.option("--tags", "-t", help="Filter by tags (format: key1=value1,key2=value2)")
@click.option("--status", "-s", help="Filter by stack status (comma-separated)")
@common_options
def cli(
    name_prefix, name_regex, tags, status, profile, region, output_format, limit, output_fields, no_header, verbose
):
    """List CloudFormation stacks with filtering options.

    Examples:

        # List all stacks
        aws-list-cloudformation-stacks

        # Filter by name prefix
        aws-list-cloudformation-stacks --name-prefix my-app

        # Filter by regex pattern
        aws-list-cloudformation-stacks --name-regex ".*-prod-.*"

        # Filter by tags
        aws-list-cloudformation-stacks --tags "Environment=production,Team=backend"

        # Filter by status
        aws-list-cloudformation-stacks --status "CREATE_COMPLETE,UPDATE_COMPLETE"

        # Combine filters
        aws-list-cloudformation-stacks --name-prefix app --tags "Environment=prod" --status "CREATE_COMPLETE"

        # Output as CSV with specific fields
        aws-list-cloudformation-stacks --format csv --output-fields stack_name,stack_status,creation_time

        # Get verbose output with all details
        aws-list-cloudformation-stacks --verbose
    """
    _ = region  # Suppress unused parameter warning

    # Parse filters
    tag_filters = parse_tag_filters(tags) if tags else None
    status_filters = parse_status_filters(status) if status else None

    # Get stacks
    stacks = list_cloudformation_stacks(
        name_prefix=name_prefix,
        tag_filters=tag_filters,
        name_regex=name_regex,
        stack_status_filter=status_filters,
        profile=profile,
        verbose=verbose,
    )

    # Apply limit and format output
    limited_stacks = apply_limit(stacks, limit)
    format_output(limited_stacks, output_format, output_fields, no_header)


if __name__ == "__main__":
    cli()
