# cli/__init__.py
import click

from cli.list_athena import cli as aws_list_athena_cli
from cli.list_glue import cli as aws_list_glue_cli
from cli.list_kinesis import cli as aws_list_kinesis_cli
from cli.list_s3 import cli as aws_list_s3_objects_cli
from cli.list_sagemaker import cli as aws_list_sagemaker_cli
from cli.list_stepfunctions import cli as aws_list_stepfunctions_cli


@click.group()
def cli_group():
    """AWS Operations CLI tool"""
    pass

# Add commands to the group
cli_group.add_command(aws_list_athena_cli)
cli_group.add_command(aws_list_glue_cli)
cli_group.add_command(aws_list_kinesis_cli)
cli_group.add_command(aws_list_s3_objects_cli)
cli_group.add_command(aws_list_sagemaker_cli)
cli_group.add_command(aws_list_stepfunctions_cli)

# For setup.py entry_points
main = cli_group

if __name__ == '__main__':
    main()
