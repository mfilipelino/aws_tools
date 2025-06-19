"""Step Functions operations for AWS utilities."""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from aws_clients import create_aws_client


def create_stepfunctions_client(profile_name: Optional[str] = None, region_name: Optional[str] = None):
    """Create a Step Functions client with proper configuration."""
    return create_aws_client("stepfunctions", profile_name=profile_name, region_name=region_name)


class StepFunctions:
    """Step Functions operations wrapper."""

    def __init__(self, profile_name: Optional[str] = None, region_name: Optional[str] = None):
        self.client = create_stepfunctions_client(profile_name, region_name)

    def get_failed_executions(self, state_machine_arn: str, days: int = 7) -> list[dict[str, Any]]:
        """Get failed executions for a state machine within the specified days."""
        start_date_threshold = datetime.now(timezone.utc) - timedelta(days=days)

        # List failed executions
        paginator = self.client.get_paginator("list_executions")
        failed_executions = []

        for page in paginator.paginate(
            stateMachineArn=state_machine_arn,
            statusFilter="FAILED"
        ):
            for execution in page["executions"]:
                execution_date = execution["startDate"]
                if execution_date > start_date_threshold:
                    # Get execution details including input
                    details = self.client.describe_execution(executionArn=execution["executionArn"])
                    execution_info = {
                        "executionArn": execution["executionArn"],
                        "name": execution["name"],
                        "startDate": execution_date,
                        "input": details.get("input", "{}"),
                        "stateMachineArn": state_machine_arn
                    }
                    failed_executions.append(execution_info)

        return failed_executions

    def retry_execution(self, state_machine_arn: str, execution_input: str, execution_name: Optional[str] = None) -> dict[str, Any]:
        """Start a new execution with the given input (retry)."""
        params = {
            "stateMachineArn": state_machine_arn,
            "input": execution_input
        }

        if execution_name:
            params["name"] = execution_name

        return self.client.start_execution(**params)

    def retry_failed_executions(self, state_machine_arn: str, days: int = 7, dry_run: bool = True) -> list[dict[str, Any]]:
        """Retry all failed executions for a state machine."""
        failed_executions = self.get_failed_executions(state_machine_arn, days)
        results = []

        for execution in failed_executions:
            if dry_run:
                result = {
                    "original_execution": execution["executionArn"],
                    "would_retry": True,
                    "input": execution["input"]
                }
            else:
                retry_name = f"retry-{execution['name']}-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
                try:
                    retry_result = self.retry_execution(
                        state_machine_arn=execution["stateMachineArn"],
                        execution_input=execution["input"],
                        execution_name=retry_name
                    )
                    result = {
                        "original_execution": execution["executionArn"],
                        "retry_execution": retry_result["executionArn"],
                        "retry_started": True
                    }
                except Exception as e:
                    result = {
                        "original_execution": execution["executionArn"],
                        "retry_started": False,
                        "error": str(e)
                    }
            results.append(result)

        return results


# Create a default instance for easy import
stepfunctions_client = StepFunctions()

