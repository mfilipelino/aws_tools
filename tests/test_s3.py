import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError

# Patch boto3.Session before importing the module so that module-level code
# does not try to load AWS configuration.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

with patch("boto3.Session") as mock_session:
    mock_session.return_value.client.return_value = MagicMock()
    s3_module = importlib.import_module("s3.s3")

S3 = s3_module.S3


@patch("s3.s3.create_s3_client")
def test_create_bucket_success(mock_create_client):
    mock_client = MagicMock()
    mock_create_client.return_value = mock_client

    s3_instance = S3()
    result = s3_instance.create_bucket_if_not_exist("mybucket")

    mock_client.create_bucket.assert_called_once_with(Bucket="mybucket")
    assert result


@patch("s3.s3.create_s3_client")
def test_create_bucket_already_owned(mock_create_client):
    mock_client = MagicMock()
    mock_create_client.return_value = mock_client

    error_response = {"Error": {"Code": "BucketAlreadyOwnedByYou", "Message": "Bucket already exists"}}
    mock_client.create_bucket.side_effect = ClientError(error_response, "CreateBucket")

    s3_instance = S3()
    result = s3_instance.create_bucket_if_not_exist("existingbucket")

    mock_client.create_bucket.assert_called_once_with(Bucket="existingbucket")
    assert result
