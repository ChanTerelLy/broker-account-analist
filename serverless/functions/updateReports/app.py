import json
import logging

import boto3
import requests


def lambda_handler(event, context):
    from ssm_parameter_store import SSMParameterStore
    ssm_client = boto3.client('ssm', region_name='us-west-1')
    store = SSMParameterStore(ssm_client=ssm_client, prefix='/projects/baa/env/')
    r = requests.session()
    headers = {
        'x-api-auth': store.get('INTERNAL_API_TOKEN')
    }
    query = """
        mutation {
          updateReports{
            success
          }
        }
    """
    print("START")
    resp = r.post(f"{store.get('SITE_URL')}/graphql", json={'query': query}, headers=headers)
    print(f"{resp.text}")
    return {"success": True}
