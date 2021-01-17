import asyncio
import codecs
import csv
import json

import aiohttp
import aiomoex
import re
from aiomoex.request_helpers import get_long_data
import requests
import pandas as pd
from datetime import date, timedelta
from bs4 import BeautifulSoup
from assets.helpers.utils import *


class Moex:
    def __init__(self):
        self.session = requests.Session()
        self.data = {}
        self.headers = {}
        self.headers[
            'user-agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, likeGecko) Chrome/70.0.3538.110 Safari/537.36'
        self.headers['content-type'] = 'application/x-www-form-urlencoded'
        self.headers['upgrade-insecure-requests'] = '1'

    def get_corp_bound_tax_free(self):
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

    async def bounds(self):
        async with aiohttp.ClientSession() as session:
            dict = {
                'iss.meta': 'off',
                'sort_order': 'asc',
                'sort_column': 'SECID',
                'start': 0,
                'sec_type': "stock_exchange_bond,stock_corporate_bond"
            }
            data = await aiomoex.request_helpers.get_long_data(session,
                                                               'https://iss.moex.com/iss/apps/infogrid/stock/rates.json',
                                                               'rates',
                                                               dict)
            df = pd.DataFrame(data)
        return df

    def get_moex_columns_description(self):
        self.request = self.session.get('https://iss.moex.com/iss/apps/infogrid/stock/columns.json?_'
                                        '=1600420993828&lang=ru&iss.meta=off').json()
        return self.request

    async def get_portfolio(self, data: list) -> list:
        deals = []
        # moex total response
        yield_count = 0  # calculate avg position from chuncks
        # calculate data in moex portfolio page
        async with aiohttp.ClientSession() as session:
            async for chunk in chunks(data, 15):
                self.headers['content-type'] = 'application/json;charset=UTF-8'
                response = await session.post('https://iss.moex.com/iss/apps/bondization/securities_portfolio.json?'
                                              'iss.meta=off&iss.json=extended&lang=ru',
                                              json=chunk, headers=self.headers)
                response = await response.json()
                portfolio = response[1]['portfolio']
                deals_portfolio = portfolio[:-1]
                deals += deals_portfolio
                yield_count += 1
        return deals


class Report:
    def _cell_generator(self, row):
        """Replace calspans by empty values in row"""
        cells = []
        for cell in row("td"):
            cells.append(cell.text.strip())
            if cell.get('colspan', None):
                cells.extend(['' for _ in range(int(cell['colspan']) - 1)])
        return cells


class SberbankReport(Report):

    def parse_html(self, html):
        soup = BeautifulSoup(html, features="html.parser")
        dates = full_strip(soup.find('h3').text)
        start_date, end_date = self._get_dates(dates)
        start_date = dmY_to_date(start_date)
        end_date = dmY_to_date(end_date)
        account = find_by_text(soup, 'Торговый код:', 'p').text
        if account:
            match = re.search(r'Торговый код:(.*)', account)
            if match:
                account = full_strip(match.group(1))
        #asset estimate table
        asset_estimate_table = find_by_text(soup, 'Оценка активов', 'p').find_next_sibling('table')
        table_data = [[cell.text.strip() for cell in row("td")] for row in asset_estimate_table.find_all('tr')]
        json_asset_estimate = pd.DataFrame(table_data[1:], columns=table_data[0]).to_dict(orient='records')
        #portfolio table
        portfolio_table = find_by_text(soup, 'Портфель Ценных Бумаг', 'p').find_next_sibling('table')
        table_data = [self._cell_generator(row) for row in portfolio_table.find_all('tr')]
        json_portfolio = pd.DataFrame(table_data[2:], columns=self._generate_header_for_portfel(table_data[1])).to_dict(orient='records')
        #hand book table
        handbook_table = find_by_text(soup, 'Справочник Ценных Бумаг', 'p').find_next_sibling('table')
        table_data = [self._cell_generator(row) for row in handbook_table.find_all('tr')]
        json_handbook = pd.DataFrame(table_data[1:], columns=table_data[0]).to_dict(orient='records')
        # money flow table
        money_flow_table = find_by_text(soup, 'Денежные средства', 'p').find_next_sibling('table')
        table_data = [self._cell_generator(row) for row in money_flow_table.find_all('tr')]
        json_money_flow = pd.DataFrame(table_data[1:], columns=table_data[0]).to_dict(orient='records')
        return {
            'account': account,
            'start_date': start_date,
            'end_date': end_date,
            'asset_estimate': json_asset_estimate,
            'iis_income': '',
            'portfolio': json_portfolio,
            'tax': '',
            'handbook': json_handbook,
            'money_flow': json_money_flow
        }



    def _get_dates(self, dates: str):
        result = re.search('Отчет брокера за период с (.*) по (.*), дата создания .*', dates)
        if result:
            return result.group(1), result.group(2)
        else:
            return None, None

    def _generate_header_for_portfel(self, row: list) -> list:
        for index, attr in enumerate(row[3:8]):
            row[row.index(attr)] = self._clear_asterics(attr) + ' (Начало Периода)'
        for index, attr in enumerate(row[8:13]):
            row[row.index(attr)] = self._clear_asterics(attr) + ' (Конец Периода)'
        for index, attr in enumerate(row[13:15]):
            row[row.index(attr)] = self._clear_asterics(attr) + ' (Изменение за период)'
        return row

    def _clear_asterics(self, string: str):
        return string.replace('*','')

if __name__ == '__main__':
    with codecs.open("../../data/examples/4NDKP.html", "r", "utf-8") as html:
        data = SberbankReport().parse_html(html)
        print(data)
