import graphene
from codetiming import Timer
from graphene import relay
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType, ObjectType
import pandas as pd
from graphql import GraphQLError

from accounts.models import Profile
from ..helpers.service import Moex, TinkoffApi, SberbankReport
from ..models import *
from assets.helpers.utils import dmYHM_to_date, xirr, get_total_xirr_percent, convert_devided_number, safe_list_get, \
    asyncio_helper, dmY_hyphen_to_date, list_to_dict
from datetime import datetime as dt, timedelta
from django.db.models import Sum, Window, F

DT_NOW = dt.now()
DT_YEAR_BEFORE = dt.now() - timedelta(days=365)


class AccountNode(DjangoObjectType):
    class Meta:
        model = Account
        fields = ('__all__')
        filter_fields = ['id', ]
        interfaces = (relay.Node,)


class PortfolioType(DjangoObjectType):
    help_text_map = graphene.String()

    class Meta:
        model = Portfolio
        fields = ('__all__')
        interfaces = (relay.Node,)


class TransferType(DjangoObjectType):
    help_text_map = graphene.String()
    type_sum = graphene.Float()

    class Meta:
        model = Transfer
        fields = ('__all__')
        interfaces = (relay.Node,)


class ChoicesPropertyEnum(graphene.Enum):
    BUY = "Покупка"
    SELL = "Продажа"


class DealsType(DjangoObjectType):
    help_text_map = graphene.String()
    transaction_volume = graphene.Int()
    type = ChoicesPropertyEnum()

    class Meta:
        model = Deal
        fields = ('__all__')
        interfaces = (relay.Node,)
        exclude_fields = ['type']

    def resolve_type(self, info, **kwargs):
        return self.type


class TemplateType(DjangoObjectType):
    class Meta:
        model = Template
        fields = ('__all__')
        interfaces = (relay.Node,)


class XirrType(ObjectType):
    account_name = graphene.String()
    avg_percent = graphene.Float()
    total_percent = graphene.Float()


class ReportData(ObjectType):
    date = graphene.Date()
    sum = graphene.Float()
    income_sum = graphene.Float()


class ReportType(ObjectType):
    account_name = graphene.String()
    data = graphene.List(ReportData)


class PortfolioReportType(ObjectType):
    name = graphene.String()
    isin = graphene.String()
    currency = graphene.String()
    start_amount = graphene.Int()
    start_denomination = graphene.Int()
    start_market_total_sum = graphene.Float()
    start_market_total_sum_without_nkd = graphene.Float()
    start_nkd = graphene.Float()
    end_amount = graphene.Int()
    end_denomination = graphene.Int()
    end_market_total_sum = graphene.Float()
    end_market_total_sum_without_nkd = graphene.Float()
    end_nkd = graphene.Float()
    changes_amount = graphene.Int()
    changes_total_sum = graphene.Float()
    scheduled_enrolment_amount = graphene.Int()
    scheduled_charges_amount = graphene.Int()
    scheduled_outbound_amount = graphene.Int()
    account = graphene.String()
    coupon_percent = graphene.Float()
    coupon_date = graphene.Date()
    purchase_coupon_percent = graphene.Float()

    @classmethod
    def convert_name_for_dict(cls, data):
        return {cls.convert_names(key): convert_devided_number(value) for key, value in data.items()}

    @classmethod
    def get_map(cls):
        return {'Аккаунт': 'account', 'Наименование': 'name', 'ISIN ценной бумаги': 'isin',
                'Валюта рыночной цены': 'currency',
                'Количество, шт (Начало Периода)': 'start_amount', 'Номинал (Начало Периода)': 'start_denomination',
                'Рыночная цена  (Начало Периода)': 'start_market_total_sum',
                'Рыночная стоимость, без НКД (Начало Периода)': 'start_market_total_sum_without_nkd',
                'НКД (Начало Периода)': 'start_nkd', 'Количество, шт (Конец Периода)': 'end_amount',
                'Номинал (Конец Периода)': 'end_denomination',
                'Рыночная цена  (Конец Периода)': 'end_market_total_sum',
                'Рыночная стоимость, без НКД (Конец Периода)': 'end_market_total_sum_without_nkd',
                'НКД (Конец Периода)': 'end_nkd', 'Количество, шт (Изменение за период)': 'changes_amount',
                'Рыночная стоимость (Изменение за период)': 'changes_total_sum',
                'Плановые зачисления по сделкам, шт': 'scheduled_enrolment_amount',
                'Плановые списания по сделкам, шт': 'scheduled_charges_amount',
                'Плановый исходящий остаток, шт': 'scheduled_outbound_amount',
                'Процент купона': 'coupon_percent',
                'Дата выплаты ближайшего купона': 'coupon_date',
                'Средний % купона покупки': 'purchase_coupon_percent'
                }

    @classmethod
    def convert_names(cls, field):
        map = cls.get_map()
        return map.get(field)


class PortfolioReportMapType(ObjectType):
    map = graphene.JSONString()
    data = graphene.List(PortfolioReportType)

    def resolve_map(self, *args):
        return {key: to_camel_case(value) for key, value in PortfolioReportType.get_map().items()}

class TinkoffPrice(ObjectType):
    currency = graphene.String()
    value = graphene.Float()

class TinkoffPortfolioType(ObjectType):
    name = graphene.String()
    average_position_price = graphene.Float()
    average_position_price_no_nkd = graphene.Float()
    balance = graphene.Float()
    blocked = graphene.Float()
    expected_yield = graphene.Float()
    figi = graphene.String()
    instrument_type = graphene.String()
    isin = graphene.String()
    lots = graphene.Int()
    ticker = graphene.String()
    currency = graphene.String()
    start_market_total_sum_without_nkd = graphene.Float()

    def resolve_average_position_price(self, info, *args):
        self.currency = self.average_position_price['currency']
        return self.average_position_price['value']

    def resolve_average_position_price_no_nkd(self, info):
        return self.average_position_price_no_nkd['value'] if self.average_position_price_no_nkd else None

    def resolve_expected_yield(self, info):
        return self.expected_yield['value']

    def resolve_start_market_total_sum_without_nkd(self, info):
        return self.average_position_price['value'] * self.balance


    @staticmethod
    def joined_value(value):
        if value:
            amount = "{:10.1f}".format(value['value']) if value['value'] else ''
            return amount + ' ' + value['currency']
        else:
            return ''

    @staticmethod
    def get_map():
        return {
            'Наименование': "name",
            'Средняя цена покупки': "average_position_price",
            'Средняя цена покупки (без НКД)': "average_position_price_no_nkd",
            'Баланс': "balance",
            'Заблокировано': "blocked",
            'Ликвидационная доходность': "expected_yield",
            'FIGI': "figi",
            'Тип инструмента': "instrument_type",
            'ISIN': "isin",
            'Колличество': "lots",
            'Тикер': "ticker",
            'Валюта': "currency",
            'Ликвидационная сумма': "start_market_total_sum_without_nkd"
        }

class TinkoffPortfolioMapType(ObjectType):
    map = graphene.JSONString()
    data = graphene.List(TinkoffPortfolioType)

    def resolve_map(self, *args):
        return {key: to_camel_case(value) for key, value in TinkoffPortfolioType.get_map().items()}


class Query(ObjectType):
    account = relay.Node.Field(AccountNode)
    my_portfolio = graphene.List(PortfolioType)
    my_transfers = graphene.List(TransferType)
    my_deals = graphene.List(DealsType)
    account_chart = graphene.JSONString()
    my_transfer_xirr = graphene.List(XirrType)
    get_template_by_key = graphene.List(TemplateType, key=graphene.String())
    report_asset_estimate_dataset = graphene.List(ReportType, account_name=graphene.String())
    income_transfers_sum = graphene.List(ReportType, account_name=graphene.String())
    user_accounts = graphene.List(AccountNode, exclude=graphene.String())
    portfolio_by_date = graphene.Field(PortfolioReportMapType, date=graphene.Date(), account_name=graphene.String())
    portfolio_combined = graphene.Field(PortfolioReportMapType)
    tinkoff_portfolio = graphene.Field(TinkoffPortfolioMapType)
    tinkoff_operations = graphene.Boolean(_from=graphene.String(), till=graphene.String())
    test = graphene.Boolean()

    def resolve_my_portfolio(self, info) -> Portfolio:
        if not info.context.user.is_authenticated:
            return Portfolio.objects.none()
        else:
            return Portfolio.objects.filter(account__user=info.context.user)

    def resolve_my_transfers(self, info) -> Transfer:
        if not info.context.user.is_authenticated:
            return Transfer.objects.none()
        else:
            return Transfer.objects.filter(account_income__user=info.context.user).all()

    def resolve_my_deals(self, info) -> Transfer:
        if not info.context.user.is_authenticated:
            return Deal.objects.none()
        else:
            return Deal.objects.filter(account__user=info.context.user).all()

    def resolve_account_chart(self, info) -> dict:
        """Return data from bar chart on dashboard"""
        data = {'data': []}
        if not info.context.user.is_authenticated:
            pass
        else:
            for account in Account.objects.filter(user=info.context.user).all():
                type_sum = account.amount
                data['data'].append(
                    {
                        'name': account.name,
                        'total': int(type_sum)
                    }
                )
        return data

    def resolve_my_transfer_xirr(self, info) -> list:
        """Return avg xirr(the same as xirr in excel), and total xirr for transfer income, charge values"""
        if not info.context.user.is_authenticated:
            return 0
        else:
            result = []
            for account in Account.objects.filter(user=info.context.user):
                transfers = Transfer.objects.filter(account_income=account,
                                                    type__in=['Вывод ДС', 'Ввод ДС']).order_by('execution_date').all()
                if not transfers:
                    continue
                dates = list([t.execution_date for t in transfers])
                sum = list([t.xirr_sum for t in transfers])
                dates.append(datetime.now(tz=pytz.UTC))  # get current date
                sum.append(account.amount)
                df = pd.DataFrame({
                    'sum': sum,
                    'execution_date': dates
                })
                x = xirr(df)
                days = (transfers.reverse()[0].execution_date - transfers[0].execution_date).days
                y = get_total_xirr_percent(x, days)
                result.append({
                    'account_name': account.name,
                    'avg_percent': round(x, 3),
                    'total_percent': round(y, 3),
                })
            return result

    def resolve_get_template_by_key(self, info, key):
        """Return filtered templates"""
        return Template.objects.filter(key=key)

    def resolve_report_asset_estimate_dataset(self, info, **kwargs) -> list:
        """Calculate value from AccountReport:
        date - get date from start_date or Transfer execution date
        sum - return total price estimate from report
        income_sum - calculate sum previous by date range amount of money
        """
        if not info.context.user.is_authenticated:
            return []
        else:
            result = []
            if kwargs.get('account_name'):
                account = Account.get_with_reports(user=info.context.user, name=kwargs.get('account_name'))
            else:
                accounts = Account.get_with_reports(user=info.context.user)
            for account in accounts:
                reports = AccountReport.objects.filter(account=account).order_by('start_date')
                ac_dic = {'account_name': account.name, 'data': []}
                for report in reports:
                    if report.source == 'sberbank':
                        data = json.loads(report.asset_estimate)
                        sum = data[-1]['Оценка, руб.']
                        ac_dic['data'].append(
                            ReportData(date=report.start_date, sum=convert_devided_number(sum), income_sum=None)
                        )
                    elif report.source == 'tinkoff':
                        ac_dic['data'].append(
                            ReportData(date=report.start_date, sum=report.asset_estimate, income_sum=None)
                        )
                result.append(ac_dic)
                real_income = Transfer.get_previous_sum_for_days(user=info.context.user, account_name=account.name)
                for income in real_income[0]['data']:
                    elem = [i for i in ac_dic['data'] if income['date'] == i.date]
                    index = None
                    if elem:
                        index = ac_dic['data'].index(elem)
                    if index:
                        ac_dic['data'][index].income_sum = income['sum']
                    else:
                        ac_dic['data'].append(
                            ReportData(date=income['date'], sum=None, income_sum=income['sum'])
                        )
                if real_income[0]['data']:
                    ac_dic['data'].append(
                        ReportData(date=datetime.now(), sum=None, income_sum=real_income[0]['data'][-1]['sum']))
            return result

    def resolve_user_accounts(self, info, exclude=None):
        """Return accounts owned by active user"""
        if not info.context.user.is_authenticated:
            return []
        else:
            if exclude == 'without-report':
                return Account.get_with_reports(user=info.context.user)
            else:
                return Account.objects.filter(user=info.context.user)

    def resolve_portfolio_by_date(self, info, account_name, date):
        if not info.context.user.is_authenticated:
            return []
        else:
            account = Account.get_with_reports(name=account_name, user=info.context.user)
            report = AccountReport.objects.get(account=account, start_date=date)
            portfolio = json.loads(report.portfolio)
            new_portfolio = []
            for data in portfolio[1:]:
                new_data = {PortfolioReportType.convert_names(key): convert_devided_number(value) for key, value in
                            data.items()}
                new_portfolio.append(PortfolioReportType(**new_data))
            return {'data': new_portfolio, 'map': ''}

    @Timer(name="decorator")
    def resolve_portfolio_combined(self, info):
        if not info.context.user.is_authenticated:
            return []
        else:
            accounts = Account.get_with_reports(user=info.context.user)
            reports = []
            for account in accounts:
                reports.append(AccountReport.objects.filter(account=account).order_by('-start_date').first())
            #generate data from portfolio report
            portfolious = list(
                [{'portfolio': json.loads(r.portfolio), 'account': r.account.name, 'source': r.source} for r in reports
                 if r])
            assets = {}
            #agrate value from portfolious
            for value in portfolious:
                if value['source'] == 'sberbank':
                    assets = SberbankReport.extract_assets(assets, value)
            # get coupon data from moex
            isins = list(assets.keys())
            data = asyncio_helper(Moex().get_coupon_by_isins, isins)
            for index, d in enumerate(data):
                if len(d):
                    assets[d[0]['isin']]['Процент купона'] = d[0].get('valueprc', [None])
                    assets[d[0]['isin']]['Дата выплаты ближайшего купона'] = dmY_hyphen_to_date(d[0].get('coupondate', [None]))
            # get data from deals
            for isin in isins:
                avg_price = Deal.get_avg_price(isin, accounts)
                if avg_price:
                    avg_percent = assets[isin]['Рыночная цена  (Начало Периода)']/avg_price
                    purchase_coupon_percent = assets[isin]['Процент купона']/avg_percent
                    assets[isin]['Средний % купона покупки'] = purchase_coupon_percent
            # convert naming
            conv_assets = [PortfolioReportType.convert_name_for_dict(asset) for index, asset in assets.items()]
            return {'data': [PortfolioReportType(**asst) for asst in conv_assets], 'map': ''}

    def resolve_tinkoff_portfolio(self, info, **kwargs):
        if not info.context.user.is_authenticated:
            return []
        else:
            TOKEN = Profile.objects.get(user=info.context.user).tinkoff_token
            if TOKEN:
                account = Account.get_or_create_tinkoff_account(user=info.context.user)
                tapi = TinkoffApi(TOKEN)
                portfolio = asyncio_helper(tapi.get_portfolio)
                j_positions = json.loads(portfolio)['positions']
                AccountReport.save_from_tinkoff(
                    **{
                        'account': account,
                        'start_date': DT_NOW,
                        'end_date': DT_NOW,
                        'asset_estimate': {},
                        'iis_income': {},
                        'portfolio': json.dumps(j_positions),
                        'money_flow': {},
                        'tax': {},
                        'handbook': {},
                        'source': 'tinkoff'
                    }
                )
                data = [TinkoffPortfolioType(**p) for p in j_positions]
                return {'data': data, 'map': ''}
            else:
                GraphQLError('No token provided')

    def resolve_tinkoff_operations(self, info, _from=DT_YEAR_BEFORE, till=DT_NOW, **kwargs):
        if not info.context.user.is_authenticated:
            return []
        else:
            TOKEN = Profile.objects.get(user=info.context.user).tinkoff_token
            if TOKEN:
                account = Account.get_or_create_tinkoff_account(user=info.context.user)
                tapi = TinkoffApi(TOKEN)
                payload = asyncio_helper(tapi.get_operations, _from, till)
                operations = payload.operations
                figis = [item['figi'] for item in payload.dict()['operations']]
                figis = list(set(filter(None, figis)))
                figis = asyncio_helper(tapi.resolve_list_figis, figis)
                figis = list_to_dict(figis)
                for operation in operations:
                    if operation.operation_type.value in ['Buy', 'Sell']:
                        Deal.convert_tinkoff_deal(operation, account, figis)
                    else:
                        Transfer.convert_tinkoff_transfer(operation, account, figis)
                return True