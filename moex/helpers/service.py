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
from django.core.cache import cache

from assets.helpers.utils import chunks, exclude_keys


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

    def get_corp_bound_tax_free(self):
        """Legacy, all bounds are taxed now from 01.01.2021"""
        begin_date = (date.today() - timedelta(days=1)).strftime('%d.%m.%Y')
        self.data = f'__EVENTTARGET=ctl00%24PageContent%24ctrlPrivilege%24DownCSV&__EVENTARGUMENT=&__VIEWSTATE=&__EVENTVALIDATION=%2FwEdABCvVXD1oYELeveMr0vHCmYPwaDSaUlVxBvR8swwp5V2bkCrzVsnCXEftxh8yu5XrI1wsOBwYZCjQDcRnEDHN%2FoVT8KU5%2Bz2UsdG3ULNV4%2BdsCzk2G%2BZ3EJfyjp1rhAoEp84DZs%2FwSUfyvtEF83piNDc%2B%2FPivpJxB7iJpU3%2B%2BtL1%2FoNvurASTA64JjG%2FUDcxYwsNirEaq0XvNcxGTLQrUOVNbQd6BXdjKzUgM6fhlk13Kighytrs7iWDvRido%2FVpD31dDWT41Pph6cnCUUhoab%2F9LSx3pPZlZJaAE2o5gPcXP0BWD1vP%2FwqkkPMp0nZeRXPqwbIccLdsbMTH014a4s0LoKLELXuIKxhOyEQBrhpqi1bfa%2F9dDsMxo9LUHBt8cL4%3D&ctl00%24PageContent%24ctrlPrivilege%24hidden_sort_column=&ctl00%24PageContent%24ctrlPrivilege%24hidden_current_page_index=0&ctl00%24PageContent%24ctrlPrivilege%24hidden_current_page_index_change=&ctl00%24PageContent%24ctrlPrivilege%24hidden_direction_desc=&ctl00%24PageContent%24ctrlPrivilege%24beginDate={begin_date}&ctl00%24PageContent%24ctrlPrivilege%24txtSearch='
        self.request = self.session.post('https://www.moex.com/ru/markets/stock/privilegeindividuals.aspx',
                                         self.data, headers=self.headers)
        self.response = self.request.content
        data = []
        text = self.response.decode("windows-1251")
        for row in text.splitlines():
            data.append(row.split(';'))
        data = list([dict(zip(data[0], c)) for c in data[1:]])

        data = pd.DataFrame(data)
        return data

    def get_currency(self):
        """Return current value of USD in RUB"""
        if cache.get('usd'):
            return cache.get('usd')
        else:
            request = self.session.get('https://iss.moex.com/iss/statistics/engines/currency/markets/selt/rates.json?iss.meta=off&iss.only=securities&cbrf.columns=USDTOM_UTS_CLOSEPRICE,CBRF_EUR_LAST')
            data = request.json()['cbrf']['data'][0]
            usd = data[0]
            euro = data[1]
            cache.set('usd', usd, 86400)
            cache.set('euro', euro, 86400)

    def get_usd(self):
        if cache.get('usd'):
            return cache.get('usd')
        else:
            self.get_currency()
            return cache.get('usd')

    def get_euro(self):
        if cache.get('euro'):
            return cache.get('euro')
        else:
            self.get_currency()
            return cache.get('euro')

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
                logging.error(e)

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
                                                               'https://iss.moex.com/iss/apps/infogrid/stock/rates.json',
                                                               'rates',
                                                               dict)
            df = pd.DataFrame(data)
        return df

    def get_moex_columns_description(self):
        self.request = self.session.get('https://iss.moex.com/iss/apps/infogrid/stock/columns.json?_'
                                        '=1600420993828&lang=ru&iss.meta=off').json()
        return self.request

    async def get_secure_by_isin(self, isins):
        datas = []
        async with aiohttp.ClientSession() as session:
            for isin in isins:
                data = await aiomoex.find_securities(session, isin, None)
                datas.append(data)
        return datas

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
            url = f'https://iss.moex.com/iss/statistics/engines/stock/markets/bonds/bondization/{isin}.json'
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
                url = f'https://iss.moex.com/iss/apps/bondization/yieldscalculator'
                url = await self._build_url(query, url)
                urls.append(url)
        await self.aiohttp_generator(urls)
        data = self.request_jsons
        return data

    async def _build_url(self, query, url):
        url = url + '?' + query
        return url

    async def get_portfolio(self, data: list) -> list:
        #TODO: for now is working synchronously replace by aiohttpgenerator
        deals = []
        # moex total response
        yield_count = 0  # calculate avg position from chuncks
        # calculate data in moex portfolio page
        async with aiohttp.ClientSession() as session:
            async for chunk in chunks(data, 15):
                self.headers['content-type'] = 'application/json;charset=UTF-8'
                response = await session.post('https://iss.moex.com/iss/apps/bondization/securities_portfolio.json?'
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
            value = float(value.replace(',','.'))
        return value

    def __dict__(self):
        r = xmltodict.parse(self.xml)
        return json.loads(json.dumps(r))

if __name__ == '__main__':
    cbr = Cbr('01.01.2021')
    print(cbr.USD)