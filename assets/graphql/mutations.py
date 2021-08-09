import json

import dateutil
import graphene

from accounts.models import Profile
from .models import *
from ..helpers.google_services import get_gmail_reports, provides_credentials, get_money_manager_database
from ..helpers.service import SberbankReport, MoneyManager, TinkoffApi
from moex.helpers.service import Moex
from ..helpers.utils import parse_file, timestamp_to_string, asyncio_helper, list_to_dict, \
    dt_now, dt_year_before
from ..models import Portfolio, Transfer, Deal, AccountReport, Account, MoneyManagerTransaction
from graphene_file_upload.scalars import Upload

from google.oauth2.credentials import Credentials


class UploadTransfers(graphene.Mutation):
    """Get income file from client and save values to Transfer table"""

    class Arguments:
        file = Upload(required=True)

    success = graphene.Boolean()

    def mutate(self, info, file, **kwargs):
        files = info.context.FILES
        transfers = parse_file(files['0'])
        Transfer.save_from_list(transfers)
        return UploadTransfers(success=True)

class UploadPortfolio(graphene.Mutation):
    class Arguments:
        file = Upload(required=True)

    success = graphene.Boolean()

    def mutate(self, info, file, **kwargs):
        files = info.context.FILES
        data = parse_file(files['0'])
        request_payload = []
        for attr in data:
            request_payload.append({
                "DIVIDENDS": [],
                "FROM": timestamp_to_string(attr['Дата покупки']),
                "SECID": attr['Код финансового инструмента'],
                "TILL": timestamp_to_string(attr['Дата продажи']),
                "VOLUME": int(attr['Продано']),
                "account": Account.objects.get_or_create(name=attr['Договор'], user=info.context.user)[0]
            })
        func = Moex().get_portfolio
        portfolio = asyncio_helper(func, request_payload)
        Portfolio.save_from_list(portfolio)
        return UploadTransfers(success=True)

class UploadDeals(graphene.Mutation):
    """Get income file from client and save values to Deals table"""

    class Arguments:
        file = Upload(required=True)

    success = graphene.Boolean()

    def mutate(self, info, file, **kwargs):
        files = info.context.FILES
        deals = parse_file(files['0'])
        Deal.save_from_list(deals)
        return UploadTransfers(success=True)

class CreatePortfolio(graphene.Mutation):
    """Get income file from client and save values to Portfolio (MOEX) table"""

    class Arguments:
        input = PortfolioInput(required=True)

    portfolio = graphene.Field(PortfolioType)

    @staticmethod
    def mutate(root, info, input=None):
        portfolio_instance = Portfolio(name=input.name)
        portfolio_instance.save()
        return CreatePortfolio(name=portfolio_instance)

class UploadSberbankReport(graphene.Mutation):
    """Get income file from client and save values to Report table"""

    class Arguments:
        file = Upload(required=True)

    success = graphene.Boolean()

    def mutate(self, info, file, **kwargs):
        files = info.context.FILES
        html = parse_file(files['0'])
        data = SberbankReport().parse_html(html)
        AccountReport.save_from_dict(data, source='sberbank')
        return UploadSberbankReport(success=True)

class ParseReportsFromGmail(graphene.Mutation):
    """IF user already grant permissions, start uploading report from gmail
    If user is not authorized on oauth2, return redirect_uri for gmail grant auth.
    """

    class Arguments:
        account_name = graphene.String()
        limit = graphene.Int()
        max_page = graphene.Int()

    success = graphene.Boolean()
    redirect_uri = graphene.String()

    @provides_credentials
    def mutate(self, info, *args, **kwargs):
        cr = json.loads(kwargs['credentials'])
        cr['expiry'] = dateutil.parser.isoparse(cr['expiry']).replace(tzinfo=None)
        kwargs['credentials'] = Credentials(**cr)
        htmls = get_gmail_reports(**kwargs)
        for html in htmls:
            try:
                data = SberbankReport().parse_html(html)
                source = 'sberbank'
                AccountReport.save_from_dict(data, source)
            except Exception as e:
                print(e)
        return ParseReportsFromGmail(success=True)

class LoadDataFromMoneyManager(graphene.Mutation):
    success = graphene.Boolean()
    redirect_uri = graphene.String()

    @provides_credentials
    def mutate(self, info, *args, **kwargs):
        cr = json.loads(kwargs['credentials'])
        cr['expiry'] = dateutil.parser.isoparse(cr['expiry']).replace(tzinfo=None)
        credentials = Credentials(**cr)
        response = get_money_manager_database(credentials, info.context.user.id)
        if response.get('error'):
            return response
        else:
            rows = MoneyManager(response['file']).get_invest_values()
            MoneyManagerTransaction.save_from_rows(rows, info.context.user)
            return {'success': True}
        return {}

class ClearReportsInfo(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        report_count = graphene.Int()
        type = graphene.String()

    @staticmethod
    def mutate(cls, info, report_count, type):
        last_rows = AccountReport.objects.filter(source=type)[:report_count]
        [row.delete() for row in last_rows]
        return {'success': True}

class UpdateTinkoffOperations(graphene.Mutation):
    success = graphene.Boolean()

    class Arguments:
        _from = graphene.Date(required=False)
        till = graphene.Date(required=False)

    @staticmethod
    def mutate(cls, info, _from=None, till=None):
        _from = dt_year_before() if not _from else _from
        till = dt_now() if not till else till
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
            return {'success': True}


class Mutation(graphene.ObjectType):
    create_author = CreatePortfolio.Field()
    upload_transfers = UploadTransfers.Field()
    upload_deals = UploadDeals.Field()
    upload_portfolio = UploadPortfolio.Field()
    upload_sberbank_report = UploadSberbankReport.Field()
    parse_reports_from_gmail = ParseReportsFromGmail.Field()
    load_data_from_money_manager = LoadDataFromMoneyManager.Field()
    clear_reports_info = ClearReportsInfo.Field()
    update_tinkoff_operations = UpdateTinkoffOperations.Field()
