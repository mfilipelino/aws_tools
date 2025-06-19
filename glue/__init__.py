"""AWS Glue utilities package."""

from .glue import create_glue_client, glue_client

__all__ = ["create_glue_client", "glue_client"]
