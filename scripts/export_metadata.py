import argparse
import os
from typing import Iterable

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

    args = parser.parse_args()

    if args.command == "s3":
        items = list(list_s3_objects(args.bucket, args.prefix))
        save_to_duckdb(items, args.table, args.db_path)
    elif args.command == "athena":
        items = list(list_athena_tables(args.catalog, args.database))
        save_to_duckdb(items, args.table, args.db_path)
    else:
        parser.print_help()

