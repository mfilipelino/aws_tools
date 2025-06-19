# stepfunctions/stepfunctions.py
from typing import Optional

import boto3


def create_stepfunctions_client(profile_name: Optional[str] = None, region_name: Optional[str] = None):
    """Create a Step Functions client."""
    session = boto3.Session(profile_name=profile_name, region_name=region_name)
    return session.client("stepfunctions")
