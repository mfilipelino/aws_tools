import logging
import os
import re
from collections.abc import Iterator
from typing import Any, Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

profile_name = os.environ.get("PROFILE_NAME", "sandbox")


def create_cloudformation_client(profile_name: str) -> Any:
    """Create a boto3 CloudFormation client using the configured AWS profile."""
    session = boto3.Session(profile_name=profile_name)
    return session.client("cloudformation")


class CloudFormation:
    def __init__(self):
        self.client = create_cloudformation_client(profile_name)

    def list_stacks(
        self,
        name_prefix: Optional[str] = None,
        tag_filters: Optional[dict[str, str]] = None,
        name_regex: Optional[str] = None,
        stack_status_filter: Optional[list[str]] = None,
    ) -> Iterator[dict[str, Any]]:
        """
        List CloudFormation stacks with filtering options.
        :param name_prefix: Filter stacks by name prefix
        :param tag_filters: Filter stacks by tags (key-value pairs)
        :param name_regex: Filter stacks by name using regex pattern
        :param stack_status_filter: Filter by stack status
        :return: Iterator of stack dictionaries
        """
        try:
            paginator = self.client.get_paginator("list_stacks")

            # Build pagination parameters
            params = {}
            if stack_status_filter:
                params["StackStatusFilter"] = stack_status_filter

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
                    if tag_filters and not self._match_tags(stack_name, tag_filters):
                        continue

                    yield {
                        "stack_name": stack_name,
                        "stack_id": stack.get("StackId"),
                        "creation_time": stack.get("CreationTime"),
                        "last_updated_time": stack.get("LastUpdatedTime"),
                        "deletion_time": stack.get("DeletionTime"),
                        "stack_status": stack.get("StackStatus"),
                        "stack_status_reason": stack.get("StackStatusReason"),
                        "template_description": stack.get("TemplateDescription"),
                        "drift_information": stack.get("DriftInformation"),
                    }

        except ClientError as e:
            logger.error(f"Error listing CloudFormation stacks: {e}")
            raise

    def _match_tags(self, stack_name: str, tag_filters: dict[str, str]) -> bool:
        """
        Check if a stack matches the specified tag filters.

        :param stack_name: Name of the stack
        :param tag_filters: Dictionary of tag key-value pairs to match
        :return: True if stack matches all tag filters, False otherwise
        """
        try:
            response = self.client.describe_stacks(StackName=stack_name)
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

        except ClientError as e:
            logger.warning(f"Error getting tags for stack {stack_name}: {e}")
            return False

    def get_stack_details(self, stack_name: str) -> dict[str, Any]:
        """
        Get detailed information about a specific stack.

        :param stack_name: Name or ID of the stack
        :return: Dictionary with stack details
        """
        try:
            response = self.client.describe_stacks(StackName=stack_name)
            stacks = response.get("Stacks", [])

            if not stacks:
                raise ValueError(f"Stack {stack_name} not found")

            stack = stacks[0]
            return {
                "stack_name": stack.get("StackName"),
                "stack_id": stack.get("StackId"),
                "description": stack.get("Description"),
                "parameters": stack.get("Parameters", []),
                "creation_time": stack.get("CreationTime"),
                "last_updated_time": stack.get("LastUpdatedTime"),
                "stack_status": stack.get("StackStatus"),
                "stack_status_reason": stack.get("StackStatusReason"),
                "disable_rollback": stack.get("DisableRollback"),
                "notification_arns": stack.get("NotificationARNs", []),
                "timeout_in_minutes": stack.get("TimeoutInMinutes"),
                "capabilities": stack.get("Capabilities", []),
                "outputs": stack.get("Outputs", []),
                "role_arn": stack.get("RoleARN"),
                "tags": stack.get("Tags", []),
                "enable_termination_protection": stack.get("EnableTerminationProtection"),
                "parent_id": stack.get("ParentId"),
                "root_id": stack.get("RootId"),
                "drift_information": stack.get("DriftInformation"),
            }

        except ClientError as e:
            logger.error(f"Error getting stack details for {stack_name}: {e}")
            raise

    def list_stack_resources(self, stack_name: str) -> Iterator[dict[str, Any]]:
        """
        List resources in a CloudFormation stack.

        :param stack_name: Name or ID of the stack
        :return: Iterator of resource dictionaries
        """
        try:
            paginator = self.client.get_paginator("list_stack_resources")
            page_iterator = paginator.paginate(StackName=stack_name)

            for page in page_iterator:
                for resource in page.get("StackResourceSummaries", []):
                    yield {
                        "logical_resource_id": resource.get("LogicalResourceId"),
                        "physical_resource_id": resource.get("PhysicalResourceId"),
                        "resource_type": resource.get("ResourceType"),
                        "last_updated_timestamp": resource.get("LastUpdatedTimestamp"),
                        "resource_status": resource.get("ResourceStatus"),
                        "resource_status_reason": resource.get("ResourceStatusReason"),
                        "drift_information": resource.get("DriftInformation"),
                        "module_info": resource.get("ModuleInfo"),
                    }

        except ClientError as e:
            logger.error(f"Error listing resources for stack {stack_name}: {e}")
            raise


cloudformation_client = CloudFormation()
