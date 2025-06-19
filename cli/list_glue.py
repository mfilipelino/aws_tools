"""List Glue jobs with prefix filtering."""

from collections.abc import Iterator
from typing import Any, Optional

import click

from aws_clients import create_aws_client
from cli.base import apply_limit, common_options, format_output


def list_glue_jobs(
    prefix: str = "",
    status: Optional[str] = None,
    profile: Optional[str] = None,
    region: Optional[str] = None,
    verbose: bool = False,
) -> Iterator[dict[str, Any]]:
    """List Glue jobs with filtering."""
    client = create_aws_client("glue", profile_name=profile, region_name=region)

    paginator = client.get_paginator("get_jobs")
    page_iterator = paginator.paginate()

    for page in page_iterator:
        for job in page.get("Jobs", []):
            job_name = job["Name"]

            # Apply prefix filter
            if prefix and not job_name.startswith(prefix):
                continue

            # Get last run info if needed
            last_run_info = {}
            if status or verbose:
                try:
                    runs_response = client.get_job_runs(JobName=job_name, MaxResults=1)
                    if runs_response.get("JobRuns"):
                        last_run = runs_response["JobRuns"][0]
                        last_run_info = {
                            "last_run_status": last_run.get("JobRunState"),
                            "last_run_time": last_run.get("StartedOn", "").isoformat()
                            if last_run.get("StartedOn")
                            else "",
                            "last_run_duration": last_run.get("ExecutionTime", 0),
                        }

                        # Apply status filter
                        if status and last_run_info.get("last_run_status") != status:
                            continue
                except Exception:
                    # If we can't get run info, include the job anyway
                    if status:
                        continue

            result = {
                "name": job_name,
                "role": job.get("Role", ""),
                "created_on": job.get("CreatedOn", "").isoformat() if job.get("CreatedOn") else "",
                "max_capacity": job.get("MaxCapacity", 0),
                **last_run_info,
            }

            if verbose:
                result["description"] = job.get("Description", "")
                result["command"] = job.get("Command", {}).get("Name", "")
                result["script_location"] = job.get("Command", {}).get("ScriptLocation", "")
                result["max_retries"] = job.get("MaxRetries", 0)
                result["timeout"] = job.get("Timeout", 0)

            yield result


@click.command("aws-list-glue-jobs")
@click.option("--prefix", "-p", default="", help="Job name prefix filter")
@click.option(
    "--status",
    "-s",
    type=click.Choice(["STARTING", "RUNNING", "STOPPING", "STOPPED", "SUCCEEDED", "FAILED", "TIMEOUT"]),
    help="Filter by last run status",
)
@common_options
def cli(prefix, status, profile, region, output_format, limit, output_fields, no_header, verbose):
    """List Glue jobs with prefix filtering and status information.

    Examples:

        # List all Glue jobs
        aws-list-glue-jobs

        # Filter by prefix
        aws-list-glue-jobs --prefix etl-

        # Show only failed jobs
        aws-list-glue-jobs --status FAILED

        # Get detailed information in table format
        aws-list-glue-jobs --prefix prod- --verbose --format table

        # Export to CSV
        aws-list-glue-jobs --format csv > glue-jobs.csv

        # Find long-running jobs
        aws-list-glue-jobs --format jsonl | jq 'select(.last_run_duration > 3600)'
    """
    # Get jobs
    jobs = list_glue_jobs(prefix=prefix, status=status, profile=profile, region=region, verbose=verbose)

    # Apply limit and format output
    limited_jobs = apply_limit(jobs, limit)
    format_output(limited_jobs, output_format, output_fields, no_header)


if __name__ == "__main__":
    cli()
