import json
import urllib
import aiohttp
import aiomoex
from tinvest import AsyncClient
from aiomoex.request_helpers import get_long_data
import requests
from datetime import date, timedelta
from bs4 import BeautifulSoup
from assets.helpers.utils import *
import assets.models


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

    def get_usd(self):
        """Return current value of USD in RUB"""
        request = self.session.get('https://iss.moex.com/iss/statistics/engines/currency/markets/selt/rates.json')
        response = request.json()['cbrf']['data'][0]
        return response

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
                account = assets.models.Account.objects.filter(name=account).first()
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
        #transfers
        transfer_text = find_by_text(soup, 'Движение денежных средств за период', 'p')
        json_transfers = {}
        if transfer_text:
            transfers_table = transfer_text.find_next_sibling('table')
            table_data = [self._cell_generator(row) for row in transfers_table.find_all('tr')]
            json_transfers = pd.DataFrame(table_data[1:], columns=table_data[0]).to_dict(orient='records')
        return {
            'account': account,
            'start_date': start_date,
            'end_date': end_date,
            'asset_estimate': json_asset_estimate,
            'iis_income': {},
            'portfolio': json_portfolio,
            'tax': {},
            'handbook': json_handbook,
            'money_flow': json_money_flow,
            'transfers': json_transfers
        }

    @classmethod
    def extract_assets(self, assets, value):
        portfolio, account = value['portfolio'], value['account']
        for attr in portfolio:
            if attr.get('Плановый исходящий остаток, шт') != '0':
                attr = {key: convert_devided_number(value) for key, value in
                        attr.items()}
                key = attr.get('ISIN ценной бумаги')
                if not key:
                    continue
                if key not in assets:
                    assets[key] = attr
                    assets[key]['Аккаунт'] = account
                else:
                    assets[key]['Аккаунт'] += ', ' + account
                    assets[key]['Количество, шт (Начало Периода)'] += attr['Количество, шт (Начало Периода)']
                    assets[key]['Рыночная стоимость, без НКД (Начало Периода)'] += attr[
                        'Рыночная стоимость, без НКД (Начало Периода)']
                    assets[key]['НКД (Начало Периода)'] += attr['НКД (Начало Периода)']
                    assets[key]['Количество, шт (Конец Периода)'] += attr['Количество, шт (Конец Периода)']
                    assets[key]['Рыночная стоимость, без НКД (Конец Периода)'] += attr[
                        'Рыночная стоимость, без НКД (Конец Периода)']
                    assets[key]['НКД (Конец Периода)'] += attr['НКД (Конец Периода)']
                    assets[key]['Количество, шт (Изменение за период)'] += attr[
                        'Количество, шт (Изменение за период)']
                    assets[key]['Рыночная стоимость (Изменение за период)'] += attr[
                        'Рыночная стоимость (Изменение за период)']
                    assets[key]['Плановые зачисления по сделкам, шт'] += attr['Плановые зачисления по сделкам, шт']
                    assets[key]['Плановые списания по сделкам, шт'] += attr['Плановые списания по сделкам, шт']
                    assets[key]['Плановый исходящий остаток, шт'] += attr['Плановый исходящий остаток, шт']
        return assets


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

class MoneyManager:

    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = self._connect(db_path)


    def _connect(self, db_path):
        import sqlite3
        return sqlite3.connect(db_path)

    def get_invest_values(self):
        c = self.conn.cursor()
        c.execute("""
        SELECT NIC_NAME, ZCONTENT, WDATE, DO_TYPE, ZMONEY, I.uid
        FROM INOUTCOME I
        LEFT JOIN ASSETS A on I.assetUid = A.uid
        LEFT JOIN ASSETGROUP AG on A.groupUid = AG.uid
        WHERE ACC_GROUP_NAME = 'Investments'
        """)
        return c.fetchall()

class TinkoffApi:

    _operation_type_map = {
        'Dividend': 'Зачисление дивидентов',
        'Buy': 'Покупка',
        'Sell': 'Продажа',
        'BrokerCommission': 'Списание Комиссии',
        'ServiceCommission': 'Сервисная комиссия',
        'PayIn': 'Ввод ДС',
        'PayOut': 'Вывод ДС'
    }

    _instrument_type_map = {
        'Stock': 'Акции',
        'Bound': 'Облигации'
    }

    def __init__(self, token):
        self.TOKEN = token
        self.figis = []

    @classmethod
    def resolve_operation_type(cls, field):
        return cls._operation_type_map.get(field, 'Undefined type')

    async def gather_requests(self, list, func):
        return await asyncio.gather(*[asyncio.ensure_future(func(item)) for item in list])

    async def get_portfolio(self, ):
        async with AsyncClient(self.TOKEN) as client:
            response = await client.get_portfolio()
        return response.payload.json()

    async def get_operations(self, from_, to):
        async with AsyncClient(self.TOKEN) as client:
            response = await client.get_operations(from_, to)
        return response.payload

    async def get_portfolio_currencies(self):
        async with AsyncClient(self.TOKEN) as client:
            result = await client.get_portfolio_currencies()
            result = result.payload.json()
        return json.loads(result)['currencies']

    async def get_accounts(self):
        async with AsyncClient(self.TOKEN) as client:
            return await client.get_accounts()

    async def get_market_currencies(self):
        async with AsyncClient(self.TOKEN) as client:
            result = await client.get_market_currencies()
            result = result.payload.json()
        return json.loads(result)['instruments']

    async def get_market_search_by_figi(self, figi):
        async with AsyncClient(self.TOKEN) as client:
            response = await client.get_market_search_by_figi(figi)
        return {figi: response.payload}

    async def resolve_list_figis(self, figis):
        result = await self.gather_requests(figis, self.get_market_search_by_figi)
        self.figis = result
        return result

    @staticmethod
    def extract_figi(figi, figis):
        return figis[figi].ticker


if __name__ == '__main__':
    response = asyncio_helper(TinkoffApi('token').get_portfolio)
    print(response)