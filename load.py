from decimal import Decimal
import json
import boto3


def load_movies(movies, dynamodb=None):
    if not dynamodb:
        dynamodb = boto3.resource('dynamodb')

    table = dynamodb.Table('transfers')
    for movie in movies:
        table.put_items(Item=movie)


if __name__ == '__main__':
    with open("transfers.json") as json_file:
        table_data = json.load(json_file, parse_float=Decimal)
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('transfers')

        with table.batch_writer() as writer:
            for item in table_data:
                writer.put_item(Item=item)