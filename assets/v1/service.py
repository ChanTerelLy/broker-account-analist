import asyncio
import csv
import json

import aiohttp
import aiomoex
from aiomoex.request_helpers import get_long_data
import requests
import pandas as pd
from datetime import date, timedelta
from assets.models import *

from django.db import transaction
from django.utils.decorators import method_decorator

from assets.v1.utils import chunks


class Moex():
    def __init__(self):
        self.session = requests.Session()
        self.data = {}
        self.headers = {}
        self.headers['user-agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, likeGecko) Chrome/70.0.3538.110 Safari/537.36'
        self.headers['content-type'] = 'application/x-www-form-urlencoded'
        self.headers['upgrade-insecure-requests'] = '1'

    def get_corp_bound_tax_free(self):
        begin_date=(date.today() - timedelta(days=1)).strftime('%d.%m.%Y')
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

    async def bounds(self):
        async with aiohttp.ClientSession() as session:
            dict = {
                'iss.meta': 'off',
                'sort_order': 'asc',
                'sort_column': 'SECID',
                'start': 0,
                'sec_type': "stock_exchange_bond,stock_corporate_bond"
            }
            data = await aiomoex.request_helpers.get_long_data(session, 'https://iss.moex.com/iss/apps/infogrid/stock/rates.json', 'rates',
                                       dict)
            df = pd.DataFrame(data)
        return df

    def get_moex_columns_description(self):
        self.request = self.session.get('https://iss.moex.com/iss/apps/infogrid/stock/columns.json?_'
                                        '=1600420993828&lang=ru&iss.meta=off').json()
        return self.request

    def get_portfolio(self, data: list) -> list:
        deals = []
        #moex total response
        yield_count = 0  #calculate avg position from chuncks
        total = {
            'BUYCLOSEPRICE': None,
            'BUYSUM': None,
            'CASHFLOW': None,
            'EARNINGS': 0,
            'ERROR': None,
            'FROM': None,
            'SECID': "_TOTAL_",
            'SELLCLOSEPRICE': None,
            'SELLSUM': None,
            'TILL': None,
            'VOLUME': None,
            'YIELD': 0
        }
        #calculate data in moex portfolio page
        for chunk in chunks(data, 15):
            self.headers['content-type'] = 'application/json;charset=UTF-8'
            self.request = self.session.post('https://iss.moex.com/iss/apps/bondization/securities_portfolio.json?'
                                             'iss.meta=off&iss.json=extended&lang=ru',
                                             json=chunk, headers=self.headers)
            content = self.request.content
            portfolio = json.loads(content)[1]['portfolio']
            deals_portfolio = portfolio[:-1]
            total['EARNINGS'] += portfolio[-1]['EARNINGS']
            total['YIELD'] += portfolio[-1]['YIELD']
            deals += deals_portfolio
            yield_count += 1
        total['YIELD'] = total['YIELD'] / yield_count if yield_count else 0
        deals.append(total)
        return deals



if __name__ == '__main__':
    data = Moex().get_moex_columns_description()
    print(data)
