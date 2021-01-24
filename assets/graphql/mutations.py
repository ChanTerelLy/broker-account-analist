import json

import dateutil
import graphene

from .queries import PortfolioType
from ..helpers.google_services import get_gmail_reports, provides_credentials, get_money_manager_database
from ..helpers.service import Moex, SberbankReport, MoneyManager
from ..helpers.utils import parse_file, timestamp_to_string, asyncio_helper
from ..models import Portfolio, Transfer, Deal, AccountReport, Account, MoneyManagerTransaction
from graphene_file_upload.scalars import Upload

from google.oauth2.credentials import Credentials


class PortfolioInput(graphene.InputObjectType):
    id = graphene.ID()
    name = graphene.String()

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
    """NOT working because of AsyncioExecutor is not return right thread, wait update from graphene"""
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
        AccountReport.save_from_dict(data)
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
                AccountReport.save_from_dict(data)
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


class Mutation(graphene.ObjectType):
    create_author = CreatePortfolio.Field()
    upload_transfers = UploadTransfers.Field()
    upload_deals = UploadDeals.Field()
    upload_portfolio = UploadPortfolio.Field()
    upload_sberbank_report = UploadSberbankReport.Field()
    parse_reports_from_gmail = ParseReportsFromGmail.Field()
    LoadDataFromMoneyManager = LoadDataFromMoneyManager.Field()
