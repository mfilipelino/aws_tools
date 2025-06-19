#!/usr/bin/env python3

import subprocess
import json
import argparse
from datetime import datetime, timedelta, timezone

def main():
    parser = argparse.ArgumentParser(description="Check Step Function executions and optionally generate rerun commands for failed ones.")
    parser.add_argument("--state-machine-arn", type=str, required=True, help="ARN of the Step Function state machine.")
    parser.add_argument("--days", type=int, required=True, help="Number of past days to check for failed executions.")
    parser.add_argument("--output-rerun-commands", action="store_true", default=False, help="Flag to generate rerun commands for failed executions.")

    args = parser.parse_args()

    start_date_threshold = datetime.now(timezone.utc) - timedelta(days=args.days)

    print(f"Checking for failed executions for state machine {args.state_machine_arn} since {start_date_threshold.isoformat()}...")

    try:
        # List Executions
        list_executions_cmd = [
            "aws", "stepfunctions", "list-executions",
            "--state-machine-arn", args.state_machine_arn,
            "--status-filter", "FAILED",
            "--output", "json",
            "--no-cli-pager"
        ]
        completed_process = subprocess.run(list_executions_cmd, capture_output=True, text=True, check=True)
        executions_data = json.loads(completed_process.stdout)

        if not executions_data.get("executions"):
            print("No executions found or an error occurred while listing executions.")
            return

        failed_executions_in_window = 0
        for execution in executions_data["executions"]:
            # AWS CLI returns startDate as a datetime object with timezone info when using boto3,
            # but as a string when calling CLI directly. We need to parse it.
            # Example: "2023-10-26T10:30:00.123Z" or "2023-10-26T10:30:00+00:00"
            # The datetime.fromisoformat() method can parse these.
            try:
                execution_date_str = execution["startDate"]
                # Ensure the string is parsed correctly into a timezone-aware datetime object
                # The fromisoformat method handles Z (Zulu time, UTC) correctly.
                # If there's a chance of other timezone offsets, more robust parsing might be needed.
                execution_date = datetime.fromisoformat(execution_date_str.replace('Z', '+00:00'))

            except ValueError as e:
                print(f"Error parsing date for execution {execution['executionArn']}: {execution['startDate']}. Error: {e}")
                continue # Skip this execution if date parsing fails

            if execution_date > start_date_threshold:
                failed_executions_in_window += 1
                print(f"\nFound failed execution:")
                print(f"  Execution ARN: {execution['executionArn']}")
                print(f"  Start Date: {execution_date.isoformat()}")

                # Describe Execution
                describe_execution_cmd = [
                    "aws", "stepfunctions", "describe-execution",
                    "--execution-arn", execution['executionArn'],
                    "--output", "json",
                    "--no-cli-pager"
                ]
                describe_process = subprocess.run(describe_execution_cmd, capture_output=True, text=True, check=True)
                execution_details = json.loads(describe_process.stdout)

                execution_input_str = execution_details.get("input", "{}") # Default to empty JSON string
                try:
                    # Pretty print the JSON input
                    execution_input_obj = json.loads(execution_input_str)
                    print(f"  Input: {json.dumps(execution_input_obj, indent=2)}")
                except json.JSONDecodeError:
                    print(f"  Input (raw string, not valid JSON): {execution_input_str}")


                if args.output_rerun_commands:
                    # The input needs to be a JSON string, suitable for CLI.
                    # json.dumps on the original string (if it was valid JSON) or the parsed object ensures it's a compact JSON string.
                    # For the --input argument, the string itself doesn't need further shell escaping
                    # if the command is passed as a list of arguments to subprocess.run.
                    # However, we are printing the command for the user, so we need to be careful.
                    # The AWS CLI --input parameter expects a JSON string.
                    # If the input_str was already a valid JSON string, json.dumps(json.loads(input_str)) would effectively normalize it.
                    # If input_str was not valid JSON (e.g. just a number or simple string not enclosed in quotes),
                    # json.loads would fail. So using execution_input_obj is safer.

                    # Re-serialize the parsed input object to ensure it's a valid JSON string.
                    escaped_input_json_string = json.dumps(execution_input_obj)

                    rerun_command = (
                        f"aws stepfunctions start-execution \\\n"
                        f"  --state-machine-arn \"{args.state_machine_arn}\" \\\n"
                        f"  --input '{escaped_input_json_string}'"
                    )
                    print(f"\n  # To rerun the above failed execution, use the following command:")
                    print(f"  {rerun_command}\n")

        if failed_executions_in_window == 0:
            print(f"No failed executions found within the last {args.days} days.")

    except subprocess.CalledProcessError as e:
        print(f"AWS CLI command failed:")
        print(f"  Command: {' '.join(e.cmd)}")
        print(f"  Return code: {e.returncode}")
        print(f"  Stdout: {e.stdout}")
        print(f"  Stderr: {e.stderr}")
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON output: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
