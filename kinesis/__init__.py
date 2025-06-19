"""AWS Kinesis utilities package."""
from .kinesis import KinesisStream, create_kinesis_client

__all__ = ["create_kinesis_client", "KinesisStream"]
