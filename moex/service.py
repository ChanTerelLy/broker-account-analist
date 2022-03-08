import asyncio
import json
import logging
import urllib
from datetime import date, timedelta, datetime
from datetime import datetime as dt
import aiohttp
import aiomoex
import jmespath
import pandas as pd
import requests
import xmltodict
from more_itertools import flatten, chunked
log = logging.getLogger("django")

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

    ### SUPPORT FUNCTIONS ###

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
                log.error(e)

    async def _build_url(self, query, url):
        url = url + '?' + query
        return url

    ### SERVERLESS ###

    def get_asset_type_path(self, type):
        output_format = 'securities.json'
        paths = []
        types = {
            'etf': {'market': 'shares', 'boards': ['TQTF']},
            'bonds': {'market': 'bonds', 'boards': ['TQCB', 'TQIR', 'TQRD']},
            'shares': {'market': 'shares', 'boards': ['TQBR']},
            'foreignshares': {'market': 'foreignshares', 'boards': ['FQBR']}
        }
        type = types[type]
        for board in type['boards']:
            paths.append(f'/engines/stock/markets/{type["market"]}/boards/{board}/{output_format}')
        return paths

    def filtering_shares(self, data, isins):
        ids = []
        if len(data) != 0:
            data = list(flatten(jmespath.search(f"[*].securities.data", data)))
            for isin in isins:
                result = list(flatten(jmespath.search(f"data[?[0] == '{isin}']", {'data': data})))
                if result:
                    ids.append(result)
        return ids

    async def get_shares(self, type, isins):
        urls = []
        for path in self.get_asset_type_path(type):
            basic_url = self.moex_url + path
            urls.append(await self._build_url(self.params + '&securities.columns=ISIN,SECID,PREVADMITTEDQUOTE', basic_url))
        await self.aiohttp_generator(urls)
        data = self.request_jsons
        data = self.filtering_shares(data, isins)
        return data

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
        data = [pd.DataFrame(j['coupons']['data'], columns=j['coupons']['columns']).to_dict(orient='records') for j in
                self.request_jsons]
        return data

    async def get_assets_links(self, isins):
        urls = {}
        assets = await self.search_assets(isins)
        for asset in assets:
            asset_values = jmespath.search(f"securities.data[0]", asset)
            if asset_values:
                urls[asset_values[5]] = f'https://www.moex.com/ru/issue.aspx?board={asset_values[14]}&code={asset_values[1]}'
        return urls

    ### MOEX Portfolio calculation ###

    async def get_portfolio(self, data: list) -> list:
        # TODO: for now is working synchronously replace by aiohttpgenerator
        def exclude_keys(list, *args):
            new_list = []
            for dict in list:
                new_list.append({key: value for key, value in dict.items() if key not in args})
            return new_list

        deals = []
        yield_count = 0
        async with aiohttp.ClientSession() as session:
            for chunk in chunked(data, 15):
                self.headers['content-type'] = 'application/json;charset=UTF-8'
                response = await session.post(f'{self.moex_url}/apps/bondization/securities_portfolio.json?'
                                              'iss.meta=off&iss.json=extended&lang=ru',
                                              json=exclude_keys(chunk, 'account'), headers=self.headers)
                response = await response.json()
                portfolio = response[1]['portfolio']
                deals_portfolio = portfolio[:-1]
                for index, value in enumerate(chunk):
                    deals_portfolio[index]['account'] = chunk[index]['account']
                deals += deals_portfolio
                yield_count += 1
        return deals

    ### Bounds ###

    async def bounds(self):
        async with aiohttp.ClientSession() as session:
            dict = {
                'iss.meta': 'off',
                'sort_order': 'asc',
                'sort_column': 'SECID',
                'start': 0,
                'sec_type': "stock_exchange_bond,stock_corporate_bond"
            }
            data = await aiomoex.request_helpers.get_short_data(session,
                                                                f'{self.moex_url}/apps/infogrid/stock/rates.json',
                                                                'rates',
                                                                dict)
            df = pd.DataFrame(data)
        return df

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

    ### Searching ###

    def generate_search_url(self, isin):
        url = f'{self.moex_url}/securities.json?iss.meta=off'
        return url + f'&q={isin}'

    def search_asset(self, isin: str):
        url = self.generate_search_url(isin)
        r = requests.session().get(url)
        return r.json()

    async def search_assets(self, isins: list):
        urls = [self.generate_search_url(isin) for isin in isins]
        await self.aiohttp_generator(urls)
        data = self.request_jsons
        return data

    ###########################
    def get_corp_bound_tax_free(self):
        pass


class Cbr:

    def __init__(self, date=None):
        self._url = 'http://www.cbr.ru/scripts/XML_daily.asp'
        self._date = f'?date_req={date}' if date else ''
        s = requests.session()
        self.xml = s.get(f'{self._url}{self._date}').text

    def __getattr__(self, item):
        r = jmespath.search(f"ValCurs.Valute[?CharCode=='{item}'].Value", self.__dict__())
        value = r[0] if len(r) else None
        if isinstance(value, str):
            value = round(float(value.replace(',', '.')), 2)
        return value

    def __dict__(self):
        r = xmltodict.parse(self.xml)
        return json.loads(json.dumps(r))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    data = loop.run_until_complete(Moex().search_assets(['RU000A1015P6', 'RU000A1005T9']))
    print(data)
