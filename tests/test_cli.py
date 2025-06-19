"""Tests for CLI commands."""
import json
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from cli.list_athena import cli as athena_cli
from cli.list_glue import cli as glue_cli
from cli.list_kinesis import cli as kinesis_cli

# Import CLI commands
from cli.list_s3 import cli as s3_cli
from cli.list_sagemaker import cli as sagemaker_cli
from cli.list_stepfunctions import cli as sfn_cli  # New import


class TestCLICommands(unittest.TestCase):
    """Test CLI commands with mocked AWS services."""

    def setUp(self):
        self.runner = CliRunner()

    @patch('cli.list_s3.create_s3_client')
    def test_s3_list_basic(self, mock_client):
        """Test basic S3 listing functionality."""
        # Mock S3 client and paginator
        mock_s3 = MagicMock()
        mock_client.return_value = mock_s3

        mock_paginator = MagicMock()
        mock_s3.get_paginator.return_value = mock_paginator

        # Mock response
        mock_paginator.paginate.return_value = [
            {
                'Contents': [
                    {
                        'Key': 'test-prefix-file1.txt',
                        'Size': 1024,
                        'LastModified': datetime(2024, 1, 1),
                        'StorageClass': 'STANDARD'
                    }
                ]
            }
        ]

        # Test the command
        result = self.runner.invoke(s3_cli, [
            '--bucket', 'test-bucket',
            '--prefix', 'test-prefix-',
            '--format', 'json'
        ])

        self.assertEqual(result.exit_code, 0)
        # Verify JSON output contains expected data
        output_data = json.loads(result.output)
        self.assertEqual(len(output_data), 1)
        self.assertEqual(output_data[0]['key'], 'test-prefix-file1.txt')

    @patch('cli.list_glue.create_glue_client')
    def test_glue_list_basic(self, mock_client):
        """Test basic Glue jobs listing functionality."""
        mock_glue = MagicMock()
        mock_client.return_value = mock_glue

        mock_paginator = MagicMock()
        mock_glue.get_paginator.return_value = mock_paginator

        # Mock response
        mock_paginator.paginate.return_value = [
            {
                'Jobs': [
                    {
                        'Name': 'etl-test-job',
                        'Role': 'arn:aws:iam::123456789012:role/GlueRole',
                        'CreatedOn': datetime(2024, 1, 1),
                        'MaxCapacity': 2.0
                    }
                ]
            }
        ]

        result = self.runner.invoke(glue_cli, [
            '--prefix', 'etl-',
            '--format', 'json'
        ])

        self.assertEqual(result.exit_code, 0)
        output_data = json.loads(result.output)
        self.assertEqual(len(output_data), 1)
        self.assertEqual(output_data[0]['name'], 'etl-test-job')

    @patch('cli.list_kinesis.create_kinesis_client')
    def test_kinesis_list_basic(self, mock_client):
        """Test basic Kinesis streams listing functionality."""
        mock_kinesis = MagicMock()
        mock_client.return_value = mock_kinesis

        mock_paginator = MagicMock()
        mock_kinesis.get_paginator.return_value = mock_paginator

        # Mock response
        mock_paginator.paginate.return_value = [
            {
                'StreamNames': ['clickstream-prod', 'clickstream-dev']
            }
        ]

        result = self.runner.invoke(kinesis_cli, [
            '--prefix', 'clickstream-',
            '--format', 'json'
        ])

        self.assertEqual(result.exit_code, 0)
        output_data = json.loads(result.output)
        self.assertEqual(len(output_data), 2)
        self.assertEqual(output_data[0]['name'], 'clickstream-prod')

    def test_help_messages(self):
        """Test that help messages work for all commands."""
        commands = [s3_cli, glue_cli, kinesis_cli, sagemaker_cli, athena_cli]

        for cmd in commands:
            result = self.runner.invoke(cmd, ['--help'])
            self.assertEqual(result.exit_code, 0)
            self.assertIn('Examples:', result.output)


class TestListStepFunctionsCLI(unittest.TestCase):
    """Test Step Functions listing CLI command."""

    def setUp(self):
        self.runner = CliRunner()

    @patch('cli.list_stepfunctions.create_stepfunctions_client')
    def test_list_stepfunctions_no_filters(self, mock_create_sfn_client):
        """Test basic invocation of aws-list-stepfunctions."""
        mock_sfn_client = MagicMock()
        mock_create_sfn_client.return_value = mock_sfn_client

        mock_sfn_client.get_paginator.return_value.paginate.return_value = [
            {
                'stateMachines': [
                    {'stateMachineArn': 'arn:aws:states:us-east-1:123:stateMachine:MachineA', 'name': 'MachineA', 'type': 'STANDARD', 'creationDate': datetime(2024, 1, 1, 12, 0, 0)},
                    {'stateMachineArn': 'arn:aws:states:us-east-1:123:stateMachine:MachineB', 'name': 'MachineB', 'type': 'EXPRESS', 'creationDate': datetime(2024, 1, 2, 12, 0, 0)},
                ]
            }
        ]

        result = self.runner.invoke(sfn_cli) # Use sfn_cli directly
        self.assertEqual(result.exit_code, 0)
        self.assertIn('MachineA', result.output)
        self.assertIn('MachineB', result.output)
        mock_create_sfn_client.assert_called_once_with(profile_name=None, region_name=None)
        mock_sfn_client.get_paginator.assert_called_once_with('list_state_machines')

    @patch('cli.list_stepfunctions.create_stepfunctions_client')
    def test_list_stepfunctions_prefix_filter(self, mock_create_sfn_client):
        """Test --prefix filter."""
        mock_sfn_client = MagicMock()
        mock_create_sfn_client.return_value = mock_sfn_client
        mock_sfn_client.get_paginator.return_value.paginate.return_value = [
            {
                'stateMachines': [
                    {'stateMachineArn': 'arn:sf:sm:TestMachineA', 'name': 'TestMachineA', 'type': 'STANDARD', 'creationDate': datetime(2024, 1, 1)},
                    {'stateMachineArn': 'arn:sf:sm:AnotherMachineB', 'name': 'AnotherMachineB', 'type': 'EXPRESS', 'creationDate': datetime(2024, 1, 1)},
                ]
            }
        ]
        result = self.runner.invoke(sfn_cli, ['--prefix', 'Test'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('TestMachineA', result.output)
        self.assertNotIn('AnotherMachineB', result.output)

    @patch('cli.list_stepfunctions.create_stepfunctions_client')
    def test_list_stepfunctions_regex_filter(self, mock_create_sfn_client):
        """Test --regex filter."""
        mock_sfn_client = MagicMock()
        mock_create_sfn_client.return_value = mock_sfn_client
        mock_sfn_client.get_paginator.return_value.paginate.return_value = [
            {
                'stateMachines': [
                    {'stateMachineArn': 'arn:sf:sm:Machine-01-Prod', 'name': 'Machine-01-Prod', 'type': 'STANDARD', 'creationDate': datetime(2024, 1, 1)},
                    {'stateMachineArn': 'arn:sf:sm:Machine-02-Dev', 'name': 'Machine-02-Dev', 'type': 'EXPRESS', 'creationDate': datetime(2024, 1, 1)},
                ]
            }
        ]
        result = self.runner.invoke(sfn_cli, ['--regex', r'Machine-\d+-Prod'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Machine-01-Prod', result.output)
        self.assertNotIn('Machine-02-Dev', result.output)

    @patch('cli.list_stepfunctions.create_stepfunctions_client')
    def test_list_stepfunctions_tag_filter_single(self, mock_create_sfn_client):
        """Test single --tag filter."""
        mock_sfn_client = MagicMock()
        mock_create_sfn_client.return_value = mock_sfn_client

        mock_sfn_client.get_paginator.return_value.paginate.return_value = [
            {
                'stateMachines': [
                    {'stateMachineArn': 'arn:sf:sm:TaggedMachine', 'name': 'TaggedMachine', 'type': 'STANDARD', 'creationDate': datetime(2024, 1, 1)},
                    {'stateMachineArn': 'arn:sf:sm:UntaggedMachine', 'name': 'UntaggedMachine', 'type': 'EXPRESS', 'creationDate': datetime(2024, 1, 1)},
                ]
            }
        ]
        mock_sfn_client.list_tags_for_resource.side_effect = [
            {'tags': [{'key': 'Env', 'value': 'Prod'}]}, # Tags for TaggedMachine
            {'tags': []}                                # Tags for UntaggedMachine
        ]

        result = self.runner.invoke(sfn_cli, ['--tag', 'Env=Prod'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('TaggedMachine', result.output)
        self.assertNotIn('UntaggedMachine', result.output)
        mock_sfn_client.list_tags_for_resource.assert_any_call(resourceArn='arn:sf:sm:TaggedMachine')

    @patch('cli.list_stepfunctions.create_stepfunctions_client')
    def test_list_stepfunctions_tag_filter_multiple(self, mock_create_sfn_client):
        """Test multiple --tag filters."""
        mock_sfn_client = MagicMock()
        mock_create_sfn_client.return_value = mock_sfn_client

        mock_sfn_client.get_paginator.return_value.paginate.return_value = [
            {
                'stateMachines': [
                    {'stateMachineArn': 'arn:sf:sm:Machine1', 'name': 'Machine1', 'type': 'STANDARD', 'creationDate': datetime(2024, 1, 1)}, # Matches all tags
                    {'stateMachineArn': 'arn:sf:sm:Machine2', 'name': 'Machine2', 'type': 'EXPRESS', 'creationDate': datetime(2024, 1, 1)},# Matches one tag
                    {'stateMachineArn': 'arn:sf:sm:Machine3', 'name': 'Machine3', 'type': 'STANDARD', 'creationDate': datetime(2024, 1, 1)}, # Matches no tags
                ]
            }
        ]
        mock_sfn_client.list_tags_for_resource.side_effect = [
            {'tags': [{'key': 'Env', 'value': 'Prod'}, {'key': 'Project', 'value': 'Alpha'}]},
            {'tags': [{'key': 'Env', 'value': 'Prod'}, {'key': 'Project', 'value': 'Beta'}]},
            {'tags': [{'key': 'Env', 'value': 'Dev'}]}
        ]

        result = self.runner.invoke(sfn_cli, ['--tag', 'Env=Prod', '--tag', 'Project=Alpha'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('Machine1', result.output)
        self.assertNotIn('Machine2', result.output)
        self.assertNotIn('Machine3', result.output)

    @patch('cli.list_stepfunctions.create_stepfunctions_client')
    def test_list_stepfunctions_tag_filter_value_mismatch(self, mock_create_sfn_client):
        """Test --tag filter where value does not match."""
        mock_sfn_client = MagicMock()
        mock_create_sfn_client.return_value = mock_sfn_client
        mock_sfn_client.get_paginator.return_value.paginate.return_value = [
            {
                'stateMachines': [
                    {'stateMachineArn': 'arn:sf:sm:MachineX', 'name': 'MachineX', 'type': 'STANDARD', 'creationDate': datetime(2024, 1, 1)},
                ]
            }
        ]
        mock_sfn_client.list_tags_for_resource.return_value = {'tags': [{'key': 'Env', 'value': 'Dev'}]}
        result = self.runner.invoke(sfn_cli, ['--tag', 'Env=Prod'])
        self.assertEqual(result.exit_code, 0)
        self.assertNotIn('MachineX', result.output)

    @patch('cli.list_stepfunctions.create_stepfunctions_client')
    def test_list_stepfunctions_tag_filter_missing_tag(self, mock_create_sfn_client):
        """Test --tag filter where a machine is missing the tag."""
        mock_sfn_client = MagicMock()
        mock_create_sfn_client.return_value = mock_sfn_client
        mock_sfn_client.get_paginator.return_value.paginate.return_value = [
            {
                'stateMachines': [
                    {'stateMachineArn': 'arn:sf:sm:MachineY', 'name': 'MachineY', 'type': 'STANDARD', 'creationDate': datetime(2024, 1, 1)},
                ]
            }
        ]
        mock_sfn_client.list_tags_for_resource.return_value = {'tags': [{'key': 'OtherTag', 'value': 'SomeValue'}]}
        result = self.runner.invoke(sfn_cli, ['--tag', 'Env=Prod'])
        self.assertEqual(result.exit_code, 0)
        self.assertNotIn('MachineY', result.output)

    @patch('cli.list_stepfunctions.create_stepfunctions_client')
    def test_list_stepfunctions_verbose_option(self, mock_create_sfn_client):
        """Test --verbose option includes additional fields."""
        mock_sfn_client = MagicMock()
        mock_create_sfn_client.return_value = mock_sfn_client

        machine_arn = 'arn:aws:states:us-east-1:123:stateMachine:VerboseMachine'
        mock_sfn_client.get_paginator.return_value.paginate.return_value = [
            {
                'stateMachines': [
                    {'stateMachineArn': machine_arn, 'name': 'VerboseMachine', 'type': 'STANDARD', 'creationDate': datetime(2024, 1, 1)},
                ]
            }
        ]
        mock_sfn_client.describe_state_machine.return_value = {
            'status': 'ACTIVE',
            'roleArn': 'arn:aws:iam::123:role/sfn_role',
            # Add other fields that describe_state_machine returns if necessary
        }

        result = self.runner.invoke(sfn_cli, ['--verbose', '--format', 'json']) # JSON for easier parsing
        self.assertEqual(result.exit_code, 0)
        output_data = json.loads(result.output)
        self.assertEqual(len(output_data), 1)
        self.assertIn('VerboseMachine', output_data[0]['name'])
        self.assertEqual(output_data[0]['status'], 'ACTIVE')
        self.assertEqual(output_data[0]['roleArn'], 'arn:aws:iam::123:role/sfn_role')
        mock_sfn_client.describe_state_machine.assert_called_once_with(stateMachineArn=machine_arn)

    @patch('cli.list_stepfunctions.create_stepfunctions_client')
    def test_list_stepfunctions_verbose_describe_failure(self, mock_create_sfn_client):
        """Test --verbose option with describe_state_machine failure."""
        mock_sfn_client = MagicMock()
        mock_create_sfn_client.return_value = mock_sfn_client

        machine_arn = 'arn:aws:states:us-east-1:123:stateMachine:FailDescribe'
        mock_sfn_client.get_paginator.return_value.paginate.return_value = [
            {
                'stateMachines': [
                    {'stateMachineArn': machine_arn, 'name': 'FailDescribe', 'type': 'STANDARD', 'creationDate': datetime(2024, 1, 1)},
                ]
            }
        ]
        mock_sfn_client.describe_state_machine.side_effect = Exception("Simulated describe error")

        result = self.runner.invoke(sfn_cli, ['--verbose', '--format', 'json'], catch_exceptions=False)
        self.assertEqual(result.exit_code, 0) # Command should still succeed
        # Clean the output by skipping warning lines
        output_lines = result.output.strip().split('\n')
        json_output = '\n'.join(line for line in output_lines if not line.startswith('Warning:'))
        output_data = json.loads(json_output)
        self.assertEqual(len(output_data), 1)
        self.assertIn('FailDescribe', output_data[0]['name'])
        self.assertEqual(output_data[0]['status'], 'ERROR_FETCHING_DETAILS') # Check for graceful error handling


    @patch('cli.list_stepfunctions.create_stepfunctions_client')
    def test_list_stepfunctions_limit_option(self, mock_create_sfn_client):
        """Test --limit option."""
        mock_sfn_client = MagicMock()
        mock_create_sfn_client.return_value = mock_sfn_client
        mock_sfn_client.get_paginator.return_value.paginate.return_value = [
            {
                'stateMachines': [
                    {'stateMachineArn': 'arn:sf:sm:Machine1', 'name': 'Machine1', 'type': 'STANDARD', 'creationDate': datetime(2024, 1, 1)},
                    {'stateMachineArn': 'arn:sf:sm:Machine2', 'name': 'Machine2', 'type': 'EXPRESS', 'creationDate': datetime(2024, 1, 1)},
                    {'stateMachineArn': 'arn:sf:sm:Machine3', 'name': 'Machine3', 'type': 'STANDARD', 'creationDate': datetime(2024, 1, 1)},
                ]
            }
        ]
        result = self.runner.invoke(sfn_cli, ['--limit', '2', '--format', 'json'])
        self.assertEqual(result.exit_code, 0)
        output_data = json.loads(result.output)
        self.assertEqual(len(output_data), 2)
        self.assertIn('Machine1', output_data[0]['name'])
        self.assertIn('Machine2', output_data[1]['name'])


if __name__ == '__main__':
    unittest.main()
