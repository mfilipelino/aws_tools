"""AWS Glue client factory and utilities."""
import os
from typing import Optional

import boto3


def create_glue_client(profile_name: Optional[str] = None, region_name: Optional[str] = None):
    """Create an AWS Glue client with the specified profile."""
    profile_name = profile_name or os.environ.get("PROFILE_NAME", "sandbox")

    session = boto3.Session(profile_name=profile_name)
    return session.client('glue', region_name=region_name)


# Module-level client instance
glue_client = create_glue_client()
