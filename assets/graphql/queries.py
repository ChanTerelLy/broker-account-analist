import graphene
from codetiming import Timer
from graphene import relay
from graphene_django.types import ObjectType
import pandas as pd
from graphql import GraphQLError

from accounts.models import Profile
from .models import *
from ..helpers.service import Moex, TinkoffApi, SberbankReport
from ..models import *
from assets.helpers.utils import xirr, get_total_xirr_percent, convert_devided_number, asyncio_helper, dmY_hyphen_to_date, list_to_dict
from datetime import datetime as dt, timedelta

DT_NOW = dt.now()
DT_YEAR_BEFORE = dt.now() - timedelta(days=365)
USD_PRICE = 0


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
                        sum = data[-1]['Оценка портфеля ЦБ, руб.']
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
                        index = ac_dic['data'].index(elem[0])
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
                portfolio_currencies = asyncio_helper(tapi.get_portfolio_currencies)
                portfolio_currencies = [cur for cur in portfolio_currencies if cur['currency'] == 'RUB']
                usd_price = Moex().get_usd()[0]
                data = [TinkoffPortfolioType(**p, usd_price=usd_price, currency=p['average_position_price']['currency'])
                        for p in j_positions]
                data.append(
                    TinkoffPortfolioType(
                        name='Российский рубль',
                        average_position_price={'value': 1, 'currency': 'RUB'},
                        average_position_price_no_nkd={'value': 1, 'currency': 'RUB'},
                        balance=portfolio_currencies[0]['balance'],
                        blocked=None,
                        expected_yield=None,
                        figi=None,
                        instrument_type='Currency',
                        isin=None,
                        lots=None,
                        ticker="RUB",
                        currency="RUB"
                    )
                )
                total_sum = [asset.resolve_start_market_total_sum_without_nkd(None) for asset in data]
                AccountReport.save_from_tinkoff(**{
                        'account': account,
                        'start_date': DT_NOW,
                        'end_date': DT_NOW,
                        'asset_estimate': sum(total_sum),
                        'iis_income': {},
                        'portfolio': json.dumps(j_positions),
                        'money_flow': {},
                        'tax': {},
                        'handbook': {},
                        'source': 'tinkoff'
                    })
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