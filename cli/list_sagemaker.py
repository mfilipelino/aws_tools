"""List SageMaker jobs with prefix filtering."""

import os
from collections.abc import Iterator
from typing import Any, Optional

import boto3
import click

from cli.base import apply_limit, common_options, format_output


def create_sagemaker_client(profile_name: Optional[str] = None, region_name: Optional[str] = None):
    """Create a SageMaker client with the specified profile."""
    profile_name = profile_name or os.environ.get("PROFILE_NAME", "sandbox")
    session = boto3.Session(profile_name=profile_name)
    return session.client("sagemaker", region_name=region_name)


def list_training_jobs(
    client, prefix: str = "", status: Optional[str] = None, verbose: bool = False
) -> Iterator[dict[str, Any]]:
    """List SageMaker training jobs."""
    paginator = client.get_paginator("list_training_jobs")

    params = {}
    if prefix:
        params["NameContains"] = prefix
    if status:
        params["StatusEquals"] = status

    page_iterator = paginator.paginate(**params)

    for page in page_iterator:
        for job in page.get("TrainingJobSummaries", []):
            result = {
                "name": job["TrainingJobName"],
                "status": job["TrainingJobStatus"],
                "created_time": job["CreationTime"].isoformat(),
                "training_time_seconds": job.get("TrainingTimeInSeconds", 0),
                "type": "training",
            }

            if "TrainingEndTime" in job:
                result["end_time"] = job["TrainingEndTime"].isoformat()

            if verbose:
                # Get detailed info
                try:
                    details = client.describe_training_job(TrainingJobName=job["TrainingJobName"])
                    result["instance_type"] = details.get("ResourceConfig", {}).get("InstanceType", "")
                    result["instance_count"] = details.get("ResourceConfig", {}).get("InstanceCount", 0)
                    result["role_arn"] = details.get("RoleArn", "")
                except Exception:
                    pass

            yield result


def list_processing_jobs(
    client, prefix: str = "", status: Optional[str] = None, verbose: bool = False
) -> Iterator[dict[str, Any]]:
    """List SageMaker processing jobs."""
    paginator = client.get_paginator("list_processing_jobs")

    params = {}
    if prefix:
        params["NameContains"] = prefix
    if status:
        params["StatusEquals"] = status

    page_iterator = paginator.paginate(**params)

    for page in page_iterator:
        for job in page.get("ProcessingJobSummaries", []):
            result = {
                "name": job["ProcessingJobName"],
                "status": job["ProcessingJobStatus"],
                "created_time": job["CreationTime"].isoformat(),
                "processing_time_seconds": job.get("ProcessingTimeInSeconds", 0),
                "type": "processing",
            }

            if "ProcessingEndTime" in job:
                result["end_time"] = job["ProcessingEndTime"].isoformat()

            if verbose:
                # Get detailed info
                try:
                    details = client.describe_processing_job(ProcessingJobName=job["ProcessingJobName"])
                    result["instance_type"] = (
                        details.get("ProcessingResources", {}).get("ClusterConfig", {}).get("InstanceType", "")
                    )
                    result["instance_count"] = (
                        details.get("ProcessingResources", {}).get("ClusterConfig", {}).get("InstanceCount", 0)
                    )
                    result["role_arn"] = details.get("RoleArn", "")
                except Exception:
                    pass

            yield result


def list_transform_jobs(
    client, prefix: str = "", status: Optional[str] = None, verbose: bool = False
) -> Iterator[dict[str, Any]]:
    """List SageMaker transform jobs."""
    paginator = client.get_paginator("list_transform_jobs")

    params = {}
    if prefix:
        params["NameContains"] = prefix
    if status:
        params["StatusEquals"] = status

    page_iterator = paginator.paginate(**params)

    for page in page_iterator:
        for job in page.get("TransformJobSummaries", []):
            result = {
                "name": job["TransformJobName"],
                "status": job["TransformJobStatus"],
                "created_time": job["CreationTime"].isoformat(),
                "type": "transform",
            }

            if "TransformEndTime" in job:
                result["end_time"] = job["TransformEndTime"].isoformat()
                # Calculate duration
                duration = (job["TransformEndTime"] - job["CreationTime"]).total_seconds()
                result["transform_time_seconds"] = int(duration)

            if verbose:
                # Get detailed info
                try:
                    details = client.describe_transform_job(TransformJobName=job["TransformJobName"])
                    result["instance_type"] = details.get("TransformResources", {}).get("InstanceType", "")
                    result["instance_count"] = details.get("TransformResources", {}).get("InstanceCount", 0)
                    result["model_name"] = details.get("ModelName", "")
                except Exception:
                    pass

            yield result


@click.command("aws-list-sagemaker-jobs")
@click.option("--prefix", "-p", default="", help="Job name prefix filter")
@click.option(
    "--type",
    "-t",
    "job_type",
    type=click.Choice(["training", "processing", "transform", "all"]),
    default="all",
    help="Type of SageMaker job",
)
@click.option(
    "--status",
    "-s",
    type=click.Choice(["InProgress", "Completed", "Failed", "Stopping", "Stopped"]),
    help="Filter by job status",
)
@common_options
def cli(prefix, job_type, status, profile, region, output_format, limit, output_fields, no_header, verbose):
    """List SageMaker jobs (training, processing, transform) with prefix filtering.

    Examples:

        # List all SageMaker jobs
        aws-list-sagemaker-jobs

        # Filter training jobs by prefix
        aws-list-sagemaker-jobs --type training --prefix model-v2-

        # Show only failed jobs
        aws-list-sagemaker-jobs --status Failed

        # Get processing jobs in table format
        aws-list-sagemaker-jobs --type processing --format table

        # Find long-running training jobs
        aws-list-sagemaker-jobs --type training | jq 'select(.training_time_seconds > 3600)'

        # Export completed jobs to CSV
        aws-list-sagemaker-jobs --status Completed --format csv > completed-jobs.csv
    """
    client = create_sagemaker_client(profile_name=profile, region_name=region)

    # Collect jobs based on type
    all_jobs = []

    if job_type in ["training", "all"]:
        all_jobs.extend(list_training_jobs(client, prefix, status, verbose))

    if job_type in ["processing", "all"]:
        all_jobs.extend(list_processing_jobs(client, prefix, status, verbose))

    if job_type in ["transform", "all"]:
        all_jobs.extend(list_transform_jobs(client, prefix, status, verbose))

    # Sort by creation time (newest first)
    all_jobs.sort(key=lambda x: x["created_time"], reverse=True)

    # Convert to iterator
    jobs_iter = iter(all_jobs)

    # Apply limit and format output
    limited_jobs = apply_limit(jobs_iter, limit)
    format_output(limited_jobs, output_format, output_fields, no_header)


if __name__ == "__main__":
    cli()
