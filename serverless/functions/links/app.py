import json
from service import Moex
import asyncio

def lambda_handler(event, context):
    loop = asyncio.get_event_loop()
    data = loop.run_until_complete(Moex().get_assets_links(event['isins']))
    return data
