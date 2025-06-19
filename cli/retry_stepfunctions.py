"""Retry failed Step Functions executions with prefix filtering."""

from typing import Optional

import click

from cli.base import common_options
from cli.list_stepfunctions import list_stepfunctions
from stepfunctions.stepfunctions import StepFunctions


@click.command("aws-retry-stepfunctions")
@click.option("--prefix", "-p", required=True, help="Filter state machines by name prefix.")
@click.option("--days", "-d", default=7, help="Number of days to look back for failed executions (default: 7).")
@click.option("--dry-run", is_flag=True, default=True, help="Show what would be retried without executing (default: true).")
@click.option("--execute", is_flag=True, help="Actually execute the retries (overrides --dry-run).")
@common_options
def cli(
    prefix: str,
    days: int,
    dry_run: bool,
    execute: bool,
    profile: Optional[str],
    region: Optional[str],
    output_format: str,
    limit: Optional[int],
    output_fields: Optional[str],
    no_header: bool,
    verbose: bool,
):
    """Retry failed executions for Step Functions with the given prefix.

    This command will:
    1. List all Step Functions that start with the given prefix
    2. Check the last executions for each one
    3. For failed executions, retry them with the same input

    By default, this runs in dry-run mode. Use --execute to actually retry the executions.
    """
    # Suppress unused parameter warnings - these are required by common_options
    _ = output_format, limit, output_fields, no_header
    # Override dry_run if execute is specified
    if execute:
        dry_run = False

    stepfunctions = StepFunctions(profile_name=profile, region_name=region)

    # Get all state machines with the given prefix
    state_machines = list(list_stepfunctions(
        prefix=prefix,
        profile=profile,
        region=region
    ))

    if not state_machines:
        click.echo(f"No Step Functions found with prefix '{prefix}'")
        return

    click.echo(f"Found {len(state_machines)} Step Functions with prefix '{prefix}'")

    total_failed = 0
    total_retried = 0

    for sm in state_machines:
        state_machine_arn = sm["arn"]
        state_machine_name = sm["name"]

        if verbose:
            click.echo(f"\nChecking {state_machine_name}...")

        try:
            # Get failed executions
            failed_executions = stepfunctions.get_failed_executions(state_machine_arn, days)

            if not failed_executions:
                if verbose:
                    click.echo(f"  No failed executions in the last {days} days")
                continue

            total_failed += len(failed_executions)
            click.echo(f"\n{state_machine_name}: Found {len(failed_executions)} failed execution(s)")

            # Retry failed executions
            retry_results = stepfunctions.retry_failed_executions(
                state_machine_arn,
                days,
                dry_run=dry_run
            )

            for result in retry_results:
                if dry_run:
                    click.echo(f"  [DRY RUN] Would retry: {result['original_execution']}")
                    if verbose:
                        click.echo(f"    Input: {result['input']}")
                else:
                    if result.get("retry_started"):
                        click.echo(f"  ✓ Retried: {result['original_execution']}")
                        click.echo(f"    New execution: {result['retry_execution']}")
                        total_retried += 1
                    else:
                        click.echo(f"  ✗ Failed to retry: {result['original_execution']}")
                        click.echo(f"    Error: {result.get('error', 'Unknown error')}", err=True)

        except Exception as e:
            click.echo(f"  Error processing {state_machine_name}: {e}", err=True)
            continue

    # Summary
    click.echo("\nSummary:")
    click.echo(f"  State machines checked: {len(state_machines)}")
    click.echo(f"  Failed executions found: {total_failed}")

    if dry_run:
        click.echo(f"  Would retry: {total_failed} execution(s)")
        click.echo("\nTo actually execute the retries, use --execute")
    else:
        click.echo(f"  Successfully retried: {total_retried}")
        click.echo(f"  Failed to retry: {total_failed - total_retried}")


if __name__ == "__main__":
    cli()
