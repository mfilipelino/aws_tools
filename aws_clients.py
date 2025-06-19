"""Unified AWS client factory for all services.

This module provides a single, consistent way to create AWS service clients
across the entire codebase, replacing the individual client creation functions
in each service module.
"""

import os
from typing import Optional

import boto3


def create_aws_client(service: str, profile_name: Optional[str] = None, region_name: Optional[str] = None):
    """Create any AWS service client with consistent configuration.

    Args:
        service: AWS service name (e.g., 's3', 'kinesis', 'glue')
        profile_name: AWS profile name. Defaults to PROFILE_NAME env var or 'sandbox'
        region_name: AWS region name. Uses default region if not specified

    Returns:
        boto3 client for the specified service
    """
    profile_name = profile_name or os.environ.get("PROFILE_NAME", "sandbox")
    session = boto3.Session(profile_name=profile_name)
    return session.client(service, region_name=region_name)

