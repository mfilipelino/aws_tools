from kinesis import kinesis_stream



stream_name = "test-stream-local"
for i in range(10):
    kinesis_stream.put_record(stream_name=stream_name, data={"id": i}, partition_key='1')


response = kinesis_stream.get_shards_info(stream_name=stream_name)
shard_id = response[0]['ShardId']
for records in kinesis_stream.get_records(stream_name=stream_name, shard_id=shard_id, limit=100):
    for record in records:
        print(record)

