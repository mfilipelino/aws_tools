import argparse
from collections.abc import Iterable
from datetime import datetime, timedelta

import duckdb
import pandas as pd

from aws_clients import create_aws_client


def create_client(service_name: str):
    return create_aws_client(service_name)


def list_s3_objects(bucket: str, prefix: str = "") -> Iterable[dict]:
    client = create_client("s3")
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            yield {
                "key": obj.get("Key"),
                "last_modified": obj.get("LastModified"),
                "size": obj.get("Size"),
                "storage_class": obj.get("StorageClass"),
            }


def list_athena_tables(catalog: str, database: str) -> Iterable[dict]:
    client = create_client("athena")
    paginator = client.get_paginator("list_table_metadata")
    for page in paginator.paginate(CatalogName=catalog, DatabaseName=database):
        for meta in page.get("TableMetadataList", []):
            yield {
                "name": meta.get("Name"),
                "create_time": meta.get("CreateTime"),
                "last_access_time": meta.get("LastAccessTime"),
                "table_type": meta.get("TableType"),
            }


def list_glue_jobs() -> Iterable[dict]:
    client = create_client("glue")
    paginator = client.get_paginator("get_jobs")
    for page in paginator.paginate():
        for job in page.get("Jobs", []):
            yield {
                "name": job.get("Name"),
                "role": job.get("Role"),
                "created_on": job.get("CreatedOn"),
                "last_modified_on": job.get("LastModifiedOn"),
                "max_capacity": job.get("MaxCapacity"),
            }


def list_glue_job_runs(job_name: str, days: int = 7) -> Iterable[dict]:
    client = create_client("glue")
    paginator = client.get_paginator("get_job_runs")
    cutoff = datetime.utcnow() - timedelta(days=days)
    for page in paginator.paginate(JobName=job_name):
        for run in page.get("JobRuns", []):
            started = run.get("StartedOn")
            if started and started < cutoff:
                continue
            yield {
                "job_name": job_name,
                "id": run.get("Id"),
                "status": run.get("JobRunState"),
                "started_on": started,
                "completed_on": run.get("CompletedOn"),
            }


def batch_get_query_execution(client, query_ids: list[str]):
    return client.batch_get_query_execution(QueryExecutionIds=query_ids)


def list_athena_query_errors(workgroup: str = "primary", days: int = 7) -> Iterable[dict]:
    client = create_client("athena")
    paginator = client.get_paginator("list_query_executions")
    cutoff = datetime.utcnow() - timedelta(days=days)
    for page in paginator.paginate(WorkGroup=workgroup):
        qids = page.get("QueryExecutionIds", [])
        for i in range(0, len(qids), 50):
            batch = qids[i : i + 50]
            resp = batch_get_query_execution(client, batch)
            for qe in resp.get("QueryExecutions", []):
                status = qe.get("Status", {})
                submit = status.get("SubmissionDateTime")
                if status.get("State") == "FAILED" and submit and submit >= cutoff:
                    yield {
                        "query_id": qe.get("QueryExecutionId"),
                        "workgroup": qe.get("WorkGroup"),
                        "submission_time": submit,
                        "failure_reason": status.get("StateChangeReason"),
                    }


def list_sagemaker_pipeline_executions(pipeline_name: str, days: int = 7) -> Iterable[dict]:
    client = create_client("sagemaker")
    paginator = client.get_paginator("list_pipeline_executions")
    cutoff = datetime.utcnow() - timedelta(days=days)
    for page in paginator.paginate(PipelineName=pipeline_name):
        for pe in page.get("PipelineExecutionSummaries", []):
            start = pe.get("StartTime")
            if start and start < cutoff:
                continue
            yield {
                "pipeline_name": pipeline_name,
                "execution_arn": pe.get("PipelineExecutionArn"),
                "status": pe.get("PipelineExecutionStatus"),
                "start_time": start,
                "last_modified_time": pe.get("LastModifiedTime"),
            }


def list_sagemaker_training_jobs(name_contains: str = "", days: int = 7) -> Iterable[dict]:
    client = create_client("sagemaker")
    paginator = client.get_paginator("list_training_jobs")
    cutoff = datetime.utcnow() - timedelta(days=days)
    params = {"SortBy": "CreationTime", "SortOrder": "Descending"}
    if name_contains:
        params["NameContains"] = name_contains
    for page in paginator.paginate(**params):
        for tj in page.get("TrainingJobSummaries", []):
            creation = tj.get("CreationTime")
            if creation and creation < cutoff:
                continue
            yield {
                "training_job_name": tj.get("TrainingJobName"),
                "status": tj.get("TrainingJobStatus"),
                "creation_time": creation,
                "end_time": tj.get("TrainingEndTime"),
            }


def list_sagemaker_processing_jobs(name_contains: str = "", days: int = 7) -> Iterable[dict]:
    client = create_client("sagemaker")
    paginator = client.get_paginator("list_processing_jobs")
    cutoff = datetime.utcnow() - timedelta(days=days)
    params = {"SortBy": "CreationTime", "SortOrder": "Descending"}
    if name_contains:
        params["NameContains"] = name_contains
    for page in paginator.paginate(**params):
        for pj in page.get("ProcessingJobSummaries", []):
            creation = pj.get("CreationTime")
            if creation and creation < cutoff:
                continue
            yield {
                "processing_job_name": pj.get("ProcessingJobName"),
                "status": pj.get("ProcessingJobStatus"),
                "creation_time": creation,
                "end_time": pj.get("ProcessingEndTime"),
            }


def list_cloudformation_stacks(name_prefix: str = "", days: int = 7) -> Iterable[dict]:
    client = create_client("cloudformation")
    paginator = client.get_paginator("list_stacks")
    cutoff = datetime.utcnow() - timedelta(days=days)

    for page in paginator.paginate():
        for stack in page.get("StackSummaries", []):
            creation = stack.get("CreationTime")
            stack_name = stack.get("StackName", "")

            # Apply time filter
            if creation and creation < cutoff:
                continue

            # Apply name prefix filter
            if name_prefix and not stack_name.startswith(name_prefix):
                continue

            yield {
                "stack_name": stack_name,
                "stack_id": stack.get("StackId"),
                "creation_time": creation,
                "last_updated_time": stack.get("LastUpdatedTime"),
                "deletion_time": stack.get("DeletionTime"),
                "stack_status": stack.get("StackStatus"),
                "stack_status_reason": stack.get("StackStatusReason"),
                "template_description": stack.get("TemplateDescription"),
            }


def save_to_duckdb(rows: Iterable[dict], table_name: str, db_path: str) -> None:
    # Validate table name to prevent SQL injection
    if not table_name.replace("_", "").replace("-", "").isalnum():
        raise ValueError(f"Invalid table name: {table_name}")

    con = duckdb.connect(db_path)
    df = pd.DataFrame(rows)
    # Table names cannot be parameterized, so we validate the input instead
    con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df")  # nosec B608
    con.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export AWS metadata to DuckDB")
    subparsers = parser.add_subparsers(dest="command")

    s3_parser = subparsers.add_parser("s3")
    s3_parser.add_argument("--bucket", required=True)
    s3_parser.add_argument("--prefix", default="")
    s3_parser.add_argument("--db-path", default="aws_metadata.duckdb")
    s3_parser.add_argument("--table", default="s3_objects")

    athena_parser = subparsers.add_parser("athena")
    athena_parser.add_argument("--catalog", required=True)
    athena_parser.add_argument("--database", required=True)
    athena_parser.add_argument("--db-path", default="aws_metadata.duckdb")
    athena_parser.add_argument("--table", default="athena_tables")

    glue_jobs_parser = subparsers.add_parser("glue-jobs")
    glue_jobs_parser.add_argument("--db-path", default="aws_metadata.duckdb")
    glue_jobs_parser.add_argument("--table", default="glue_jobs")

    glue_runs_parser = subparsers.add_parser("glue-job-runs")
    glue_runs_parser.add_argument("--job-name", required=True)
    glue_runs_parser.add_argument("--days", type=int, default=7)
    glue_runs_parser.add_argument("--db-path", default="aws_metadata.duckdb")
    glue_runs_parser.add_argument("--table", default="glue_job_runs")

    athena_err_parser = subparsers.add_parser("athena-errors")
    athena_err_parser.add_argument("--workgroup", default="primary")
    athena_err_parser.add_argument("--days", type=int, default=7)
    athena_err_parser.add_argument("--db-path", default="aws_metadata.duckdb")
    athena_err_parser.add_argument("--table", default="athena_query_errors")

    sm_pipe_parser = subparsers.add_parser("sm-pipeline-executions")
    sm_pipe_parser.add_argument("--pipeline-name", required=True)
    sm_pipe_parser.add_argument("--days", type=int, default=7)
    sm_pipe_parser.add_argument("--db-path", default="aws_metadata.duckdb")
    sm_pipe_parser.add_argument("--table", default="sm_pipeline_executions")

    sm_train_parser = subparsers.add_parser("sm-training-jobs")
    sm_train_parser.add_argument("--name-contains", default="")
    sm_train_parser.add_argument("--days", type=int, default=7)
    sm_train_parser.add_argument("--db-path", default="aws_metadata.duckdb")
    sm_train_parser.add_argument("--table", default="sm_training_jobs")

    sm_proc_parser = subparsers.add_parser("sm-processing-jobs")
    sm_proc_parser.add_argument("--name-contains", default="")
    sm_proc_parser.add_argument("--days", type=int, default=7)
    sm_proc_parser.add_argument("--db-path", default="aws_metadata.duckdb")
    sm_proc_parser.add_argument("--table", default="sm_processing_jobs")

    cf_parser = subparsers.add_parser("cloudformation")
    cf_parser.add_argument("--name-prefix", default="", help="Filter stacks by name prefix")
    cf_parser.add_argument("--days", type=int, default=7, help="Filter stacks created in the last N days")
    cf_parser.add_argument("--db-path", default="aws_metadata.duckdb")
    cf_parser.add_argument("--table", default="cloudformation_stacks")

    args = parser.parse_args()

    if args.command == "s3":
        items = list(list_s3_objects(args.bucket, args.prefix))
        save_to_duckdb(items, args.table, args.db_path)
    elif args.command == "athena":
        items = list(list_athena_tables(args.catalog, args.database))
        save_to_duckdb(items, args.table, args.db_path)
    elif args.command == "glue-jobs":
        items = list(list_glue_jobs())
        save_to_duckdb(items, args.table, args.db_path)
    elif args.command == "glue-job-runs":
        items = list(list_glue_job_runs(args.job_name, args.days))
        save_to_duckdb(items, args.table, args.db_path)
    elif args.command == "athena-errors":
        items = list(list_athena_query_errors(args.workgroup, args.days))
        save_to_duckdb(items, args.table, args.db_path)
    elif args.command == "sm-pipeline-executions":
        items = list(list_sagemaker_pipeline_executions(args.pipeline_name, args.days))
        save_to_duckdb(items, args.table, args.db_path)
    elif args.command == "sm-training-jobs":
        items = list(list_sagemaker_training_jobs(args.name_contains, args.days))
        save_to_duckdb(items, args.table, args.db_path)
    elif args.command == "sm-processing-jobs":
        items = list(list_sagemaker_processing_jobs(args.name_contains, args.days))
        save_to_duckdb(items, args.table, args.db_path)
    elif args.command == "cloudformation":
        items = list(list_cloudformation_stacks(args.name_prefix, args.days))
        save_to_duckdb(items, args.table, args.db_path)
    else:
        parser.print_help()
