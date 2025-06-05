import argparse
import os
from datetime import datetime, timedelta
from typing import Iterable, List

import boto3
import duckdb
import pandas as pd

profile_name = os.environ.get("PROFILE_NAME", "sandbox")


def create_client(service_name: str):
    return boto3.Session(profile_name=profile_name).client(service_name)


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


def batch_get_query_execution(client, query_ids: List[str]):
    return client.batch_get_query_execution(QueryExecutionIds=query_ids)


def list_athena_query_errors(workgroup: str = "primary", days: int = 7) -> Iterable[dict]:
    client = create_client("athena")
    paginator = client.get_paginator("list_query_executions")
    cutoff = datetime.utcnow() - timedelta(days=days)
    for page in paginator.paginate(WorkGroup=workgroup):
        qids = page.get("QueryExecutionIds", [])
        for i in range(0, len(qids), 50):
            batch = qids[i:i + 50]
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


def save_to_duckdb(rows: Iterable[dict], table_name: str, db_path: str) -> None:
    con = duckdb.connect(db_path)
    df = pd.DataFrame(rows)
    con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM df")
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
    else:
        parser.print_help()

