import json
import logging

import boto3
import requests


def lambda_handler(event, context):
    """
    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format
        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes
        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """
    from ssm_parameter_store import SSMParameterStore
    ssm_client = boto3.client('ssm', region_name='us-west-1')
    store = SSMParameterStore(ssm_client=ssm_client, prefix='/projects/baa/env/')
    r = requests.session()
    headers = {
        'x-api-auth': store.get('INTERNAL_API_TOKEN')
    }
    query = """
            {
            "data": {
                "updateReports": {
                    "success": false
                }
            }
        }
    """
    print("START")
    resp = r.post(f"{store.get('SITE_URL')}/graphql", json={'query': query}, headers=headers)
    print(f"{resp.text}")
    return {"success": True}
