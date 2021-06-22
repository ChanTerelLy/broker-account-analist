import asyncio
import urllib
from datetime import date, timedelta, datetime
from datetime import datetime as dt
import aiohttp
import pandas as pd
import requests


class Moex:
    def __init__(self):
        self.session = requests.Session()
        self.data = {}
        self.headers = {}
        self.headers[
            'user-agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, likeGecko) Chrome/70.0.3538.110 Safari/537.36'
        self.headers['content-type'] = 'application/x-www-form-urlencoded'
        self.headers['upgrade-insecure-requests'] = '1'
        self.request_jsons = []
        self.moex_url = 'https://iss.moex.com/iss'
        self.params = 'iss.meta=off&iss.only=securities'

    def get_asset_type_path(self, type):
        output_format = 'securities.json'
        types = {
            'etf': {'market': 'shares', 'board': 'TQTF'},
            'bonds': {'market': 'bonds', 'board': 'TQCB'},
            'shares': {'market': 'shares', 'board': 'TQBR'},
            'foreignshares': {'market': 'foreignshares', 'board': 'FQBR'}
        }
        path = f'/engines/stock/markets/{types[type]["market"]}/boards/{types[type]["board"]}/{output_format}'
        return path

    async def aiohttp_generator(self, urls):
        async with aiohttp.ClientSession(headers=self.headers) as client:
            await asyncio.gather(*[
                asyncio.ensure_future(self.extract_request_data(client, item))
                for item in urls
            ])

    async def extract_request_data(self, client, url):
        async with client.get(url) as resp:
            try:
                json = await resp.json()
                self.request_jsons.append(json)
            except Exception as e:
                print(e)

    async def get_coupon_by_isins(self, isins):
        query = {
            "from": dt.now().strftime('%Y-%m-%d'),
            "till": (dt.now() + timedelta(days=365)).strftime('%Y-%m-%d'),
            'iss.only': 'coupons,coupons.cursor',
            'limit': 1,
            'sord_order': 'desc',
            'is_traded': 1
        }
        query = urllib.parse.urlencode(query, doseq=False)
        urls = []
        data = []
        for isin in isins:
            url = f'{self.moex_url}/statistics/engines/stock/markets/bonds/bondization/{isin}.json'
            url = await self._build_url(query, url)
            urls.append(url)
        await self.aiohttp_generator(urls)
        data = [pd.DataFrame(j['coupons']['data'],columns=j['coupons']['columns']).to_dict(orient='records') for j in self.request_jsons]
        return data

    async def coupon_calculator(self, isins_values):
        urls = []
        data = []
        for isin in isins_values:
            if len(isin) and isin[0].get('avg_price'):
                query = {
                    "tradedate": dt.now().strftime('%Y-%m-%d'),
                    'calc_value': isin[0].get('avg_price'),
                    'secid': isin[0].get('isin'),
                    'calc_method': 'by_price_to_offer',
                    'accint_source': 't0'
                }
                query = urllib.parse.urlencode(query, doseq=False)
                url = f'{self.moex_url}/apps/bondization/yieldscalculator'
                url = await self._build_url(query, url)
                urls.append(url)
        await self.aiohttp_generator(urls)
        data = self.request_jsons
        return data

    async def _build_url(self, query, url):
        url = url + '?' + query
        return url
    def filtering_shares(self, data, isins):
        ids = []
        if len(data) != 0:
            for id in data[0]['securities']['data']:
                if id[0] in isins:
                    ids.append(id)
        return ids


    async def get_shares(self, type, isins):
        urls = []
        basic_url = self.moex_url + self.get_asset_type_path(type)
        url = await self._build_url(self.params + '&securities.columns=ISIN,SECID,PREVADMITTEDQUOTE', basic_url)
        urls.append(url)
        await self.aiohttp_generator(urls)
        data = self.request_jsons
        data = self.filtering_shares(data, isins)
        return data

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    data = loop.run_until_complete(Moex().get_shares('foreignshares', ['US0231351067']))
    print(data)