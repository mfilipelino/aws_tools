import importlib
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError

# Patch boto3.Session before importing the module so that module-level code
# does not try to load AWS configuration.
with patch("boto3.Session") as mock_session:
    mock_session.return_value.client.return_value = MagicMock()
    cf_module = importlib.import_module("cloudformation.cloudformation")

CloudFormation = cf_module.CloudFormation


class TestCloudFormationListStacks(unittest.TestCase):
    @patch("cloudformation.cloudformation.create_cloudformation_client")
    def test_list_stacks_success(self, mock_create_client):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        # Mock paginator response
        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator

        mock_page = {
            "StackSummaries": [
                {
                    "StackName": "test-stack-1",
                    "StackId": "arn:aws:cloudformation:us-east-1:123456789012:stack/test-stack-1/uuid",
                    "CreationTime": datetime(2024, 1, 1, 12, 0, 0),
                    "StackStatus": "CREATE_COMPLETE",
                    "TemplateDescription": "Test stack 1"
                },
                {
                    "StackName": "test-stack-2",
                    "StackId": "arn:aws:cloudformation:us-east-1:123456789012:stack/test-stack-2/uuid",
                    "CreationTime": datetime(2024, 1, 2, 12, 0, 0),
                    "StackStatus": "UPDATE_COMPLETE",
                    "TemplateDescription": "Test stack 2"
                }
            ]
        }
        mock_paginator.paginate.return_value = [mock_page]

        cf_instance = CloudFormation()
        stacks = list(cf_instance.list_stacks())

        self.assertEqual(len(stacks), 2)
        self.assertEqual(stacks[0]["stack_name"], "test-stack-1")
        self.assertEqual(stacks[1]["stack_name"], "test-stack-2")
        mock_client.get_paginator.assert_called_once_with("list_stacks")

    @patch("cloudformation.cloudformation.create_cloudformation_client")
    def test_list_stacks_with_name_prefix_filter(self, mock_create_client):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        # Mock paginator response
        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator

        mock_page = {
            "StackSummaries": [
                {
                    "StackName": "app-prod-stack",
                    "StackId": "arn:aws:cloudformation:us-east-1:123456789012:stack/app-prod-stack/uuid",
                    "CreationTime": datetime(2024, 1, 1, 12, 0, 0),
                    "StackStatus": "CREATE_COMPLETE",
                },
                {
                    "StackName": "database-stack",
                    "StackId": "arn:aws:cloudformation:us-east-1:123456789012:stack/database-stack/uuid",
                    "CreationTime": datetime(2024, 1, 2, 12, 0, 0),
                    "StackStatus": "CREATE_COMPLETE",
                }
            ]
        }
        mock_paginator.paginate.return_value = [mock_page]

        cf_instance = CloudFormation()
        stacks = list(cf_instance.list_stacks(name_prefix="app-"))

        self.assertEqual(len(stacks), 1)
        self.assertEqual(stacks[0]["stack_name"], "app-prod-stack")

    @patch("cloudformation.cloudformation.create_cloudformation_client")
    def test_list_stacks_with_regex_filter(self, mock_create_client):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        # Mock paginator response
        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator

        mock_page = {
            "StackSummaries": [
                {
                    "StackName": "app-prod-stack",
                    "StackId": "arn:aws:cloudformation:us-east-1:123456789012:stack/app-prod-stack/uuid",
                    "CreationTime": datetime(2024, 1, 1, 12, 0, 0),
                    "StackStatus": "CREATE_COMPLETE",
                },
                {
                    "StackName": "app-dev-stack",
                    "StackId": "arn:aws:cloudformation:us-east-1:123456789012:stack/app-dev-stack/uuid",
                    "CreationTime": datetime(2024, 1, 2, 12, 0, 0),
                    "StackStatus": "CREATE_COMPLETE",
                },
                {
                    "StackName": "database-stack",
                    "StackId": "arn:aws:cloudformation:us-east-1:123456789012:stack/database-stack/uuid",
                    "CreationTime": datetime(2024, 1, 3, 12, 0, 0),
                    "StackStatus": "CREATE_COMPLETE",
                }
            ]
        }
        mock_paginator.paginate.return_value = [mock_page]

        cf_instance = CloudFormation()
        stacks = list(cf_instance.list_stacks(name_regex=r".*-prod-.*"))

        self.assertEqual(len(stacks), 1)
        self.assertEqual(stacks[0]["stack_name"], "app-prod-stack")

    @patch("cloudformation.cloudformation.create_cloudformation_client")
    def test_list_stacks_with_status_filter(self, mock_create_client):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        # Mock paginator response
        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator

        mock_page = {
            "StackSummaries": [
                {
                    "StackName": "test-stack-1",
                    "StackId": "arn:aws:cloudformation:us-east-1:123456789012:stack/test-stack-1/uuid",
                    "CreationTime": datetime(2024, 1, 1, 12, 0, 0),
                    "StackStatus": "CREATE_COMPLETE",
                }
            ]
        }
        mock_paginator.paginate.return_value = [mock_page]

        cf_instance = CloudFormation()
        stacks = list(cf_instance.list_stacks(stack_status_filter=["CREATE_COMPLETE"]))

        self.assertEqual(len(stacks), 1)
        mock_paginator.paginate.assert_called_once_with(StackStatusFilter=["CREATE_COMPLETE"])

    @patch("cloudformation.cloudformation.create_cloudformation_client")
    def test_list_stacks_with_tag_filter(self, mock_create_client):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        # Mock paginator response
        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator

        mock_page = {
            "StackSummaries": [
                {
                    "StackName": "test-stack-1",
                    "StackId": "arn:aws:cloudformation:us-east-1:123456789012:stack/test-stack-1/uuid",
                    "CreationTime": datetime(2024, 1, 1, 12, 0, 0),
                    "StackStatus": "CREATE_COMPLETE",
                }
            ]
        }
        mock_paginator.paginate.return_value = [mock_page]

        # Mock describe_stacks response for tag matching
        mock_client.describe_stacks.return_value = {
            "Stacks": [
                {
                    "Tags": [
                        {"Key": "Environment", "Value": "production"},
                        {"Key": "Team", "Value": "backend"}
                    ]
                }
            ]
        }

        cf_instance = CloudFormation()
        stacks = list(cf_instance.list_stacks(tag_filters={"Environment": "production"}))

        self.assertEqual(len(stacks), 1)
        mock_client.describe_stacks.assert_called_once_with(StackName="test-stack-1")

    @patch("cloudformation.cloudformation.create_cloudformation_client")
    def test_get_stack_details_success(self, mock_create_client):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        mock_client.describe_stacks.return_value = {
            "Stacks": [
                {
                    "StackName": "test-stack",
                    "StackId": "arn:aws:cloudformation:us-east-1:123456789012:stack/test-stack/uuid",
                    "Description": "Test stack description",
                    "CreationTime": datetime(2024, 1, 1, 12, 0, 0),
                    "StackStatus": "CREATE_COMPLETE",
                    "Parameters": [{"ParameterKey": "Environment", "ParameterValue": "prod"}],
                    "Tags": [{"Key": "Team", "Value": "backend"}],
                    "Outputs": [{"OutputKey": "WebsiteURL", "OutputValue": "https://example.com"}]
                }
            ]
        }

        cf_instance = CloudFormation()
        details = cf_instance.get_stack_details("test-stack")

        self.assertEqual(details["stack_name"], "test-stack")
        self.assertEqual(details["description"], "Test stack description")
        self.assertEqual(len(details["parameters"]), 1)
        self.assertEqual(len(details["tags"]), 1)
        mock_client.describe_stacks.assert_called_once_with(StackName="test-stack")

    @patch("cloudformation.cloudformation.create_cloudformation_client")
    def test_get_stack_details_not_found(self, mock_create_client):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        mock_client.describe_stacks.return_value = {"Stacks": []}

        cf_instance = CloudFormation()

        with self.assertRaises(ValueError) as context:
            cf_instance.get_stack_details("nonexistent-stack")

        self.assertIn("Stack nonexistent-stack not found", str(context.exception))

    @patch("cloudformation.cloudformation.create_cloudformation_client")
    def test_list_stack_resources_success(self, mock_create_client):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        # Mock paginator response
        mock_paginator = MagicMock()
        mock_client.get_paginator.return_value = mock_paginator

        mock_page = {
            "StackResourceSummaries": [
                {
                    "LogicalResourceId": "WebServerInstance",
                    "PhysicalResourceId": "i-1234567890abcdef0",
                    "ResourceType": "AWS::EC2::Instance",
                    "ResourceStatus": "CREATE_COMPLETE",
                    "LastUpdatedTimestamp": datetime(2024, 1, 1, 12, 0, 0)
                }
            ]
        }
        mock_paginator.paginate.return_value = [mock_page]

        cf_instance = CloudFormation()
        resources = list(cf_instance.list_stack_resources("test-stack"))

        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0]["logical_resource_id"], "WebServerInstance")
        self.assertEqual(resources[0]["resource_type"], "AWS::EC2::Instance")
        mock_client.get_paginator.assert_called_once_with("list_stack_resources")
        mock_paginator.paginate.assert_called_once_with(StackName="test-stack")

    @patch("cloudformation.cloudformation.create_cloudformation_client")
    def test_list_stacks_client_error(self, mock_create_client):
        mock_client = MagicMock()
        mock_create_client.return_value = mock_client

        error_response = {"Error": {"Code": "AccessDenied", "Message": "User not authorized"}}
        mock_client.get_paginator.side_effect = ClientError(error_response, "ListStacks")

        cf_instance = CloudFormation()

        with self.assertRaises(ClientError):
            list(cf_instance.list_stacks())


if __name__ == "__main__":
    unittest.main()
