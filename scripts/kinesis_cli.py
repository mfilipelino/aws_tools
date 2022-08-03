from kinesis.kinesis import kinesis_stream
from mimesis import Person
from mimesis.locales import Locale
from mimesis.schema import Field, Schema
import sys


if __name__ == '__main__':

    stream_name = "person-input"
    kinesis_stream.create_stream(stream_name=stream_name)
    field = Field(locale=Locale.EN_CA)
    schema = Schema(
        lambda: {
            'id': field('uuid'),
            'name': field('name'),
            'surname': field('surname'),
            'email': field('email'),
            'age': field('age'),
            'username': field('username'),
            'occupation': field('occupation'),
            "address": {
                "street": field('street_name'),
                "city": field('city'),
                "zipcode": field('zip_code'),
            },
        }
    )
    # for data in schema.create(iterations=1000):
    #     kinesis_stream.put_record(stream_name=stream_name,
    #                               data=data,
    #                               partition_key='1')
    schema.to_json(file_path="data.json", iterations=600)
