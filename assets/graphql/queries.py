import os

import boto3
import numpy as np
import pytz
from codetiming import Timer
import pandas as pd
from django.core import serializers
from graphql import GraphQLError
from datetime import datetime as dt

from more_itertools import flatten

from accounts.models import Profile
from .models import *
from ..helpers.service import TinkoffApi, SberbankReport
from ..models import *
from assets.helpers.utils import xirr, get_total_xirr_percent, convert_devided_number, asyncio_helper, \
    dmY_hyphen_to_date, dt_to_date, get_summed_values, dt_now
import graphene_django_optimizer as gql_optimizer


class Query(ObjectType):
    account = relay.Node.Field(AccountNode)
    my_portfolio = graphene.List(PortfolioType)
    my_transfers = graphene.List(TransferType)
    my_deals = graphene.List(DealsType)
    account_chart = graphene.JSONString(description="""Return data from bar chart on dashboard""")
    my_transfer_xirr = graphene.List(XirrType, description="""
    Return avg xirr(the same as xirr in excel), and total xirr for transfer income, charge values""")
    get_template_by_key = graphene.List(TemplateType, key=graphene.String(),
                                        description="""Return filtered templates""")
    report_asset_estimate_dataset = graphene.List(ReportType, account_name=graphene.String(), description=
    """
      Calculate value from AccountReport:
      date - get date from start_date or Transfer execution date
      sum - return total price estimate from report
      income_sum - calculate sum previous by date range amount of money
    """)
    income_transfers_sum = graphene.List(ReportType, account_name=graphene.String())
    user_accounts = graphene.List(AccountNode, exclude=graphene.String(),
                                  description="""Return accounts owned by active user""")
    portfolio_by_date = graphene.Field(PortfolioReportMapType, date=graphene.Date(), account_name=graphene.String())
    portfolio_combined = graphene.Field(PortfolioReportMapType)
    tinkoff_portfolio = graphene.Field(PortfolioReportMapType)
    test = graphene.Boolean()
    coupon_chart = graphene.List(CouponAggregated)
    iis_income = graphene.List(IISIncomeAggregated)
    assets_remains = graphene.JSONString()
    coupon_aggregated = graphene.List(CouponAverage)

    def resolve_my_portfolio(self, info) -> MoexPortfolio:
        return MoexPortfolio.objects.filter(account__user=info.context.user)

    def resolve_my_transfers(self, info) -> Transfer:
        return gql_optimizer.query(Transfer.objects.filter(account_income__user=info.context.user).all(), info)

    def resolve_my_deals(self, info) -> Deal:
        return gql_optimizer.query(Deal.objects.filter(account__user=info.context.user).all(), info)

    def resolve_account_chart(self, info) -> dict:
        data = {'data': []}
        for account in Account.objects.filter(~Q(amount=0), user=info.context.user).all():
            type_sum = account.amount
            data['data'].append(
                {
                    'name': account.name,
                    'total': int(type_sum)
                }
            )
        return data

    def resolve_my_transfer_xirr(self, info) -> list:
        result = []
        for account in Account.objects.filter(user=info.context.user):
            transfers = Transfer.objects.filter(account_income=account,
                                                type__in=['Вывод ДС', 'Ввод ДС']).all()
            if not transfers:
                continue
            income_sum = Transfer.get_sum_with_converted_currency(transfers, 'Ввод ДС')
            outcome_sum = Transfer.get_sum_with_converted_currency(transfers, 'Вывод ДС')
            outcome_sum = 0 if outcome_sum is None else outcome_sum
            total_income_outcome = income_sum - outcome_sum
            earn_sum = account.amount - total_income_outcome
            dates = list([t.execution_date for t in transfers])
            sum = list([t.xirr_sum for t in transfers])
            dates.append(dt.now(tz=pytz.UTC))  # get current date
            sum.append(account.amount)
            df = pd.DataFrame({
                'sum': sum,
                'execution_date': dates
            })
            x = xirr(df)
            days = (account.updated_at - transfers[0].execution_date).days
            y = get_total_xirr_percent(x, days)
            result.append({
                'account_name': account.name,
                'avg_percent': round(x, 3),
                'total_percent': round(y, 3),
                'earn_sum': round(earn_sum, 0)
            })
        for income in AdditionalInvestmentIncome.objects.filter(user=info.context.user).values('type').annotate(
                total=Sum('sum')):
            result.append(
                {'account_name': income['type'],
                 'avg_percent': 0,
                 'total_percent': 0,
                 'earn_sum': income['total']
                 }
            )
        return result

    def resolve_assets_remains(self, info, **kwargs) -> list:
        if kwargs.get('account_name'):
            accounts = Account.get_with_reports(user=info.context.user, name=kwargs.get('account_name'))
        else:
            accounts = Account.get_with_reports(user=info.context.user)
        result = {}
        for account in accounts:
            report = AccountReport.objects.filter(account=account).order_by('start_date').last()
            ac_dic = {'account_name': account.name, 'value': 0}
            if report:
                if report.source == 'sberbank':
                    data = json.loads(report.asset_estimate)
                    sum = data[-1]['Денежные средства, руб.']
                    result[account.name] = int(convert_devided_number(sum))
                elif report.source == 'tinkoff':
                    pass
        return result

    def resolve_get_template_by_key(self, info, key):
        return Template.objects.filter(key=key)

    def resolve_report_asset_estimate_dataset(self, info, **kwargs) -> list:
        result = []
        if kwargs.get('account_name'):
            accounts = Account.get_with_reports(user=info.context.user, name=kwargs.get('account_name'))
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
                        ReportData(date=dt_to_date(report.start_date), sum=convert_devided_number(sum),
                                   income_sum=None)
                    )
                elif report.source == 'tinkoff':
                    ac_dic['data'].append(
                        ReportData(date=dt_to_date(report.start_date), sum=report.asset_estimate, income_sum=None)
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
                        ReportData(date=dt_to_date(income['date']), sum=None, income_sum=income['sum'])
                    )
            if real_income[0]['data']:
                ac_dic['data'].append(
                    ReportData(date=dt_to_date(dt.today()), sum=None, income_sum=real_income[0]['data'][-1]['sum']))
        summed_values = get_summed_values(result)
        result.append({'account_name': 'Total',
                       'data': [ReportData(date=k, sum=s['sum'], income_sum=s['income_sum']) for k, s in
                                summed_values.items()]})
        return result

    def resolve_user_accounts(self, info, exclude=None):
        context = info.context or info.root_value
        user = context.user
        if exclude == 'without-report':
            return Account.get_with_reports(user=user)
        else:
            return Account.objects.filter(user=user)

    def resolve_portfolio_by_date(self, info, account_name, date):
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
        accounts = Account.get_with_reports(user=info.context.user)
        reports = []
        for account in accounts:
            reports.append(AccountReport.objects.filter(account=account).order_by('-start_date').first())
        # generate data from portfolio report
        portfolious = list(
            [{'portfolio': json.loads(r.portfolio), 'account': r.account.name, 'source': r.source} for r in reports
             if r])
        assets = {}
        # agrate value from portfolious
        for value in portfolious:
            if value['source'] == 'sberbank':
                assets = SberbankReport.extract_assets(assets, value)
        # get coupon data from moex
        isins = list(assets.keys())
        client = None
        start_sync_execution = []
        if os.getenv('STEP_FUNCTION_ARN', None):
            client = boto3.client('stepfunctions', region_name=os.getenv('AWS_REGION'))
            start_sync_execution = client.start_execution(
                stateMachineArn=os.getenv('STEP_FUNCTION_ARN'),
                input=json.dumps({'isins': isins})
            )
        # get data from deals
        isins_with_balance_price = Deal.get_balance_price(isins, accounts)
        for balance_price in isins_with_balance_price:
            assets[balance_price[0].get('isin')]['Средняя цена покупки'] = balance_price[0]['avg_price']
        avg_percents = asyncio_helper(Moex().coupon_calculator, isins_with_balance_price)
        isins_with_avg_percents = {}
        for v in avg_percents:
            if not v['calculated'].get('error'):
                isin = v['calculated']['SECID']
                percent = v['calculated']['CURRENTYIELD']
                isins_with_avg_percents[isin] = percent
        for isin, percent in isins_with_avg_percents.items():
            avg_price = isin
            if avg_price:
                assets[isin]['Средний % купона покупки'] = percent * 10
        if os.getenv('STEP_FUNCTION_ARN', None):
            data = client.describe_execution(executionArn=start_sync_execution['executionArn'])
            while data['status'] == 'RUNNING':
                data = client.describe_execution(executionArn=start_sync_execution['executionArn'])
            # convert naming
            if data:
                output = json.loads(data['output'])
                for i, o in enumerate(output[1]):
                    output[1][i][2] *= 10  # multiplie price to 10 for bounds
                pricing = flatten(output[:4])
                for price in pricing:
                    assets[price[0]]['Текущая цена'] = price[2]
                # coupons
                for index, d in enumerate(output[4]):
                    if len(d):
                        assets[d[0]['isin']]['Процент купона'] = d[0].get('valueprc', [None])
                        assets[d[0]['isin']]['Выплата купона'] = dmY_hyphen_to_date(
                            d[0].get('coupondate', [None]))
        for index, asset in assets.items():
            assets[index]['Стоимость на момент покупки'] = assets[index]['Средняя цена покупки'] \
                                                           * assets[index]['Количество, шт (Начало Периода)']
            assets[index]['Ликвидационная стоимость'] = assets[index].get('Текущая цена', 0) \
                                                        * assets[index]['Количество, шт (Начало Периода)']
            assets[index]['Доход'] = assets[index]['Ликвидационная стоимость'] - assets[index][
                'Стоимость на момент покупки']
        conv_assets = [PortfolioReportType.convert_name_for_dict(asset) for index, asset in assets.items()]
        return {'data': [PortfolioReportType(**asst) for asst in conv_assets], 'map': ''}

    def resolve_tinkoff_portfolio(self, info, **kwargs):
        TOKEN = Profile.objects.get(user=info.context.user).tinkoff_token
        if TOKEN:
            account = Account.get_or_create_tinkoff_account(user=info.context.user)
            tapi = TinkoffApi(TOKEN)
            portfolio = asyncio_helper(tapi.get_portfolio)
            j_positions = json.loads(portfolio)['positions']
            portfolio_currencies = asyncio_helper(tapi.get_portfolio_currencies)
            portfolio_currencies = [cur for cur in portfolio_currencies if cur['currency'] == 'RUB']
            usd_price = Cbr().USD
            euro = Cbr().EURO
            data = [TinkoffPortfolioType(**p, usd_price=usd_price, euro_price=euro,
                                         currency=p['average_position_price']['currency'])
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
                'start_date': dt_now(),
                'end_date': dt_now(),
                'asset_estimate': sum(total_sum),
                'iis_income': {},
                'portfolio': json.dumps(j_positions),
                'money_flow': {},
                'tax': {},
                'handbook': {},
                'source': 'tinkoff'
            })
            portfolio_data = []
            for d in data:
                if d.instrument_type != "Currency":
                    start_amount = d.balance
                    avg_price_of_buying = round(d.resolve_average_position_price(None), 0)
                    sum_of_buying = round(start_amount * avg_price_of_buying, 0)
                    income = round(d.resolve_expected_yield(None), 0)
                    sum_of_liquidation = sum_of_buying + income
                    portfolio_data.append(
                        PortfolioReportType(
                            name=d.name,
                            isin=d.isin,
                            currency=d.currency,
                            start_amount=start_amount,
                            start_denomination=None,
                            start_market_total_sum=None,
                            start_market_total_sum_without_nkd=sum_of_liquidation,
                            start_nkd=None,
                            end_amount=None,
                            end_denomination=None,
                            end_market_total_sum=None,
                            end_market_total_sum_without_nkd=None,
                            end_nkd=None,
                            changes_amount=None,
                            changes_total_sum=None,
                            scheduled_enrolment_amount=None,
                            scheduled_charges_amount=None,
                            scheduled_outbound_amount=None,
                            account="Tinkoff",
                            coupon_percent=None,
                            coupon_date=None,
                            purchase_coupon_percent=None,
                            real_price=None,
                            avg_price_of_buying=avg_price_of_buying,
                            sum_of_buying=sum_of_buying,
                            sum_of_liquidation=sum_of_liquidation,
                            income=income,
                        )
                    )
            return {'data': portfolio_data, 'map': ''}
        else:
            return {'data': [], 'map': ''}

    def resolve_coupon_chart(self, info):
        aggr_by_month = Transfer.objects.filter(type='Зачисление купона', account_income__user=info.context.user) \
            .values('execution_date__month', 'execution_date__year') \
            .annotate(sum=Sum('sum')).order_by('execution_date__year', 'execution_date__month')
        for index, month in enumerate(aggr_by_month):
            date = dt(month['execution_date__year'], month['execution_date__month'], 1)
            aggr_by_month[index]['date'] = date
            del aggr_by_month[index]['execution_date__month']
            del aggr_by_month[index]['execution_date__year']
        return [CouponAggregated(**aggr) for aggr in aggr_by_month]

    def resolve_iis_income(self, info):
        aggr_by_year = IISIncome.objects.filter(account__user=info.context.user) \
            .values('operation_date__year').annotate(sum=Sum('sum')).order_by('operation_date__year')
        return [IISIncomeAggregated(sum=aggr['sum'], year=aggr['operation_date__year']) for aggr in aggr_by_year]

    def resolve_coupon_aggregated(self, info):
        aggr_values = Transfer.objects \
            .filter(type='Зачисление купона', account_income__user=info.context.user) \
            .values('execution_date__month', 'execution_date__year', 'sum')
        df = pd.DataFrame(aggr_values)
        grouped_by_year = df.groupby(['execution_date__year', 'execution_date__month'], as_index=False).agg(
            {'sum': 'sum'})
        d = grouped_by_year.groupby(['execution_date__year'], as_index=False).agg(
            {'execution_date__month': 'count', 'sum': 'sum'})
        d.columns = ['year', 'month_count', 'sum']
        d['avg_month'] = d['sum'] / d['month_count']
        d['sum'] = d['sum'].astype(np.int64)
        d['avg_month'] = d['avg_month'].astype(np.int64)
        values = d.to_dict(orient='row')
        return [CouponAverage(**i) for i in values]
