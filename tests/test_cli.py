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


if __name__ == '__main__':
    unittest.main()
