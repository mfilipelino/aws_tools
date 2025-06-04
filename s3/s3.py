import os
import logging

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

profile_name = os.environ.get("PROFILE_NAME", "sandbox")


def create_s3_client(profile_name):
    """Create a boto3 S3 client using the configured AWS profile."""
    return boto3.Session(profile_name=profile_name).client('s3')


class S3:

    def __init__(self):
        self.client = create_s3_client(profile_name)

    def create_folder_if_not_exist(self, bucket_name: str, folder_name: str) -> bool:
        try:
            s3_client = self.client
            result = s3_client.list_objects(Bucket=bucket_name, Prefix=folder_name)
            if result.get('Contents'):
                logger.info(f"Folder {folder_name} already exists")
            else:
                s3_client.put_object(Bucket=bucket_name, Key=folder_name)
                logger.info(f"Folder {folder_name} created")
            return True
        except ClientError as e:
            logger.error(e)
            return False

    def create_bucket_if_not_exist(self, bucket_name: str, region: str = None) -> bool:
        """Create an S3 bucket in a specified region
        If a region is not specified, the bucket is created in the S3 default
        region (us-east-1).
        :param bucket_name: Bucket to create
        :param region: String region to create bucket in, e.g., 'us-west-2'
        :return: True if bucket created, else False
        """

        # Create bucket
        try:
            if region is None:
                s3_client = self.client
                s3_client.create_bucket(Bucket=bucket_name)
            else:
                s3_client = boto3.client('s3', region_name=region)
                location = {'LocationConstraint': region}
                s3_client.create_bucket(Bucket=bucket_name,
                                        CreateBucketConfiguration=location)
            return True

        except ClientError as e:
            if e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                logger.info(f"Bucket {bucket_name} already exists")
            else:
                logger.error(e)
                return False
            return True


s3_client = S3()