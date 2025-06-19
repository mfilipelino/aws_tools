import json

from mimesis.locales import Locale
from mimesis.schema import Field, Schema

from aws_clients import create_aws_client


def create_stream(client, stream_name, shard_count=None):
    """Create a Kinesis stream."""
    try:
        if shard_count is None:
            client.create_stream(StreamName=stream_name, StreamModeDetails={"StreamMode": "ON_DEMAND"})
        else:
            client.create_stream(
                StreamName=stream_name, ShardCount=shard_count, StreamModeDetails={"StreamMode": "PROVISIONED"}
            )
        print(f"Created stream {stream_name}")
    except client.exceptions.ResourceInUseException:
        print(f"Stream {stream_name} already exists")

def put_record(client, stream_name, data, partition_key):
    """Put a record to the stream."""
    try:
        response = client.put_record(StreamName=stream_name, Data=json.dumps(data), PartitionKey=partition_key)
        print(f"Put record in stream {stream_name}")
        return response
    except Exception as e:
        print(f"Error putting record in stream {stream_name}: {e}")
        raise

if __name__ == "__main__":
    stream_name = "person-input"
    client = create_aws_client("kinesis")

    create_stream(client, stream_name)

    field = Field(locale=Locale.EN_CA)
    schema = Schema(
        lambda: {
            "id": field("uuid"),
            "name": field("name"),
            "surname": field("surname"),
            "email": field("email"),
            "age": field("age"),
            "username": field("username"),
            "occupation": field("occupation"),
            "address": {
                "street": field("street_name"),
                "city": field("city"),
                "zipcode": field("zip_code"),
            },
        }
    )

    # Generate data and optionally send to Kinesis
    for data in schema.create():  # Reduced for testing
        put_record(client, stream_name, data, partition_key='1')

    # Also save to JSON file
    schema.to_json(file_path="data.json", iterations=600)

