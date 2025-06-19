"""Base CLI functionality and common options."""
import json
import sys
from collections.abc import Iterator
from typing import Any, Optional

import click
from tabulate import tabulate


class OutputFormatter:
    """Handle different output formats for CLI commands."""

    @staticmethod
    def format_jsonl(data: Iterator[dict[str, Any]]) -> None:
        """Output as JSON lines (one JSON object per line)."""
        for item in data:
            print(json.dumps(item, default=str))

    @staticmethod
    def format_json(data: Iterator[dict[str, Any]]) -> None:
        """Output as pretty-printed JSON array."""
        items = list(data)
        print(json.dumps(items, indent=2, default=str))

    @staticmethod
    def format_tsv(data: Iterator[dict[str, Any]], fields: Optional[list[str]] = None, no_header: bool = False) -> None:
        """Output as tab-separated values."""
        for i, item in enumerate(data):
            if i == 0:
                if fields is None:
                    fields = list(item.keys())
                if not no_header:
                    print('\t'.join(fields))

            values = [str(item.get(field, '')) for field in fields or []]
            print('\t'.join(values))

    @staticmethod
    def format_csv(data: Iterator[dict[str, Any]], fields: Optional[list[str]] = None, no_header: bool = False) -> None:
        """Output as comma-separated values."""
        import csv
        writer = csv.writer(sys.stdout)

        for i, item in enumerate(data):
            if i == 0:
                if fields is None:
                    fields = list(item.keys())
                if not no_header:
                    writer.writerow(fields)

            values = [item.get(field, '') for field in fields or []]
            writer.writerow(values)

    @staticmethod
    def format_table(data: Iterator[dict[str, Any]], fields: Optional[list[str]] = None) -> None:
        """Output as human-readable table."""
        items = list(data)
        if not items:
            print("No items found.")
            return

        if fields is None:
            fields = list(items[0].keys())

        table_data = []
        for item in items:
            row = [item.get(field, '') for field in fields]
            table_data.append(row)

        print(tabulate(table_data, headers=fields, tablefmt="grid"))


def common_options(f):
    """Decorator to add common CLI options to commands."""
    f = click.option('--profile', envvar='AWS_PROFILE', help='AWS profile to use')(f)
    f = click.option('--region', envvar='AWS_DEFAULT_REGION', help='AWS region')(f)
    f = click.option('--format', 'output_format',
                     type=click.Choice(['jsonl', 'json', 'tsv', 'csv', 'table']),
                     default='jsonl', help='Output format (default: jsonl)')(f)
    f = click.option('--limit', type=int, help='Maximum number of results')(f)
    f = click.option('--output-fields', help='Comma-separated list of fields to output')(f)
    f = click.option('--no-header', is_flag=True, help='Omit header row (for tsv/csv)')(f)
    f = click.option('--verbose', is_flag=True, help='Include additional metadata')(f)
    return f


def format_output(data: Iterator[dict[str, Any]], format_type: str,
                  fields: Optional[str] = None, no_header: bool = False) -> None:
    """Format and output data based on the specified format."""
    formatter = OutputFormatter()

    # Parse fields if provided
    field_list = None
    if fields:
        field_list = [f.strip() for f in fields.split(',')]

    if format_type == 'jsonl':
        formatter.format_jsonl(data)
    elif format_type == 'json':
        formatter.format_json(data)
    elif format_type == 'tsv':
        formatter.format_tsv(data, field_list, no_header)
    elif format_type == 'csv':
        formatter.format_csv(data, field_list, no_header)
    elif format_type == 'table':
        formatter.format_table(data, field_list)


def apply_limit(data: Iterator[dict[str, Any]], limit: Optional[int]) -> Iterator[dict[str, Any]]:
    """Apply limit to iterator if specified."""
    if limit is None:
        yield from data
    else:
        for count, item in enumerate(data):
            if count >= limit:
                break
            yield item
