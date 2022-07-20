import json
import logging
import os


import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

profile_name = os.environ.get("PROFILE_NAME", "sandbox")


def create_kinesis_client(profile_name):
    return boto3.Session(profile_name=profile_name).client('kinesis')


class KinesisStream:

    def __init__(self):
        self.client = create_kinesis_client(profile_name)


    def create_stream(self, stream_name, shard_count):
        """
        Create
        :param stream_name:
        :param shard_count:
        :return:
        """
        try:
            return self.client.create_stream(StreamName=stream_name, ShardCount=shard_count)
        except ClientError as e:
            if "already exists" in e.response.get("Error").get("Message"):
                logger.info("stream 5% already exists")
            else:
                raise


    def describe(self, stream_name):
        """
        Describre stream
        :param stream_name:
        :return:
        """
        try:
            return self.client.describe_stream(StreamName=stream_name)
        except ClientError:
            logger.exception("Couldn't describe %s.", stream_name)
            raise


    def delete(self, stream_name):
        try:
            self.client.delete_stream(StreamName=stream_name)
            logger.info("Delete stream %s", stream_name)
        except ClientError:
            logger.exception("Couldn't delete stream %s", stream_name)
            raise

    def list_streams(self):
        try:
            return self.client.list_streams()
        except ClientError:
            logger.exception("Coundn't list streams")


    def put_record(self, stream_name, data, partition_key):
        """
        Put data into the stream. The data is formatted as JSON before it is passed to the stream.
        :param data:
        :param partition_key:
        :return:
        """
        try:
            return self.client.put_record(
                StreamName=stream_name,
                Data=json.dumps(data),
                PartitionKey=partition_key
            )
            logger.info("Put record in stream")

        except ClientError:
            logger.exception("Couldn't put record in stream %s", stream_name)
            raise
        else:
            return response

    def put_records(self, stream_name: str, data: list[dict], partition_key: str):
        try:
            return self.client.put_records(
                StreamName=stream_name,
                Records = list(
                    map(lambda e: { "Data": json.dumps(e), "PartitionKey": partition_key},
                        data
                    )
                )
            )
        except ClientError:
            logger.exception("Error to push records on %s", stream_name)
            raise

    def get_shards_info(self, stream_name: str):
        try:
            response =self.describe(stream_name=stream_name)
            return [shard for shard in response.get("StreamDescription").get("Shards")]
        except ClientError:
            logger.exception("Error on client describe %s", stream_name)
            raise

    def get_records(self, stream_name, shard_id, limit=100, shard_interator_types="TRIM_HORIZON"):
        shard_interator = self.client.get_shard_iterator(StreamName=stream_name,
                                                         ShardId=shard_id,
                                                         ShardIteratorType=shard_interator_types)
        shard_interator = shard_interator['ShardIterator']
        while True:
            response = self.client.get_records(ShardIterator=shard_interator, Limit=limit)
            records = response['Records']
            if len(records) == 0:
                break
            yield records
            shard_interator = response['NextShardIterator']

kinesis_stream = KinesisStream()

