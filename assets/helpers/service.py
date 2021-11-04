import json
from tinvest import AsyncClient
from bs4 import BeautifulSoup
from assets.helpers.utils import *
import assets.models


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
        # asset estimate table
        asset_estimate_table = find_by_text(soup, 'Оценка активов', 'p').find_next_sibling('table')
        table_data = [[cell.text.strip() for cell in row("td")] for row in asset_estimate_table.find_all('tr')]
        json_asset_estimate = pd.DataFrame(table_data[1:], columns=table_data[0]).to_dict(orient='records')
        # portfolio table
        portfolio_table = find_by_text(soup, 'Портфель Ценных Бумаг', 'p').find_next_sibling('table')
        table_data = [self._cell_generator(row) for row in portfolio_table.find_all('tr')]
        json_portfolio = pd.DataFrame(table_data[2:], columns=self._generate_header_for_portfel(table_data[1])).to_dict(orient='records')
        # hand book table
        handbook_table = find_by_text(soup, 'Справочник Ценных Бумаг', 'p').find_next_sibling('table')
        table_data = [self._cell_generator(row) for row in handbook_table.find_all('tr')]
        json_handbook = pd.DataFrame(table_data[1:], columns=table_data[0]).to_dict(orient='records')
        # money flow table
        money_flow_table = find_by_text(soup, 'Денежные средства', 'p').find_next_sibling('table')
        table_data = [self._cell_generator(row) for row in money_flow_table.find_all('tr')]
        json_money_flow = pd.DataFrame(table_data[1:], columns=table_data[0]).to_dict(orient='records')
        # transfers
        transfer_text = find_by_text(soup, 'Движение денежных средств за период', 'p')
        json_transfers = {}
        if transfer_text:
            transfers_table = transfer_text.find_next_sibling('table')
            table_data = [self._cell_generator(row) for row in transfers_table.find_all('tr')]
            json_transfers = pd.DataFrame(table_data[1:], columns=table_data[0]).to_dict(orient='records')
        # iis_income
        iis_income_text = find_by_text(soup, 'Информация о зачислениях денежных средств на ИИС', 'p')
        json_iis_income = {}
        if iis_income_text:
            iis_table = iis_income_text.find_next_sibling('table')
            table_data = [self._cell_generator(row) for row in iis_table.find_all('tr')]
            json_iis_income = pd.DataFrame(table_data[1:], columns=table_data[0]).to_dict(orient='records')
        # deals
        deals_text = find_by_text(soup, 'Сделки купли/продажи ценных бумаг', 'p')
        json_deals = {}
        if deals_text:
            deal_table = deals_text.find_next_sibling('table')
            table_data = [self._cell_generator(row) for row in deal_table.find_all('tr')]
            json_deals = pd.DataFrame(table_data[1:], columns=table_data[0]).to_dict(orient='records')
        return {
            'account': account,
            'start_date': start_date,
            'end_date': end_date,
            'asset_estimate': json_asset_estimate,
            'iis_income': json_iis_income,
            'portfolio': json_portfolio,
            'tax': {},
            'handbook': json_handbook,
            'money_flow': json_money_flow,
            'transfers': json_transfers,
            'deals': json_deals
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
        'Dividend': 'Зачисление дивидендов',
        'Tax': 'Списание налогов',
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

    async def get_portfolio(self):
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

    async def get_market_bonds(self):
        async with AsyncClient(self.TOKEN) as client:
            response = await client.get_market_bonds()
        return response

    async def get_market_stocks(self):
        async with AsyncClient(self.TOKEN) as client:
            response = await client.get_market_stocks()
        return response

    async def get_market_candles(self, figi, from_, to, interval):
        async with AsyncClient(self.TOKEN) as client:
            return await client.get_market_candles(figi, from_, to, interval)

    async def get_market_etfs(self):
        async with AsyncClient(self.TOKEN) as client:
            return await client.get_market_etfs()

    async def resolve_list_figis(self, figis):
        result = await self.gather_requests(figis, self.get_market_search_by_figi)
        self.figis = result
        return result

    async def get_market_orderbook(self, figi, depth):
        async with AsyncClient(self.TOKEN) as client:
            return await client.get_market_orderbook(figi, depth)

    @staticmethod
    def extract_figi(figi, figis):
        return figis[figi].ticker