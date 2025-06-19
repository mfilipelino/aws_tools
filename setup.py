"""Setup configuration for AWS Tools."""
from setuptools import find_packages, setup

setup(
    name="aws-tools",
    version="0.1.0",
    description="AWS utilities toolkit with prefix-based CLI commands",
    author="AWS Tools Contributors",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "boto3>=1.26.0",
        "click>=8.0.0",
        "tabulate>=0.9.0",
        "mimesis>=11.1.0",
        "duckdb>=0.9.0",
    ],
    entry_points={
        "console_scripts": [
            "aws-list-s3-objects=cli.list_s3:cli",
            "aws-list-glue-jobs=cli.list_glue:cli",
            "aws-list-sagemaker-jobs=cli.list_sagemaker:cli",
            "aws-list-kinesis-streams=cli.list_kinesis:cli",
            "aws-list-athena-tables=cli.list_athena:cli",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
