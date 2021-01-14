import graphene

from .queries import PortfolioType
from ..helpers.service import Moex, SberbankReport
from ..helpers.utils import parse_file
from ..models import Portfolio, Transfer, Deal, AccountReport
from graphene_file_upload.scalars import Upload

class PortfolioInput(graphene.InputObjectType):
    id = graphene.ID()
    name = graphene.String()

class UploadTransfers(graphene.Mutation):
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
                "FROM": attr['Дата покупки'],
                "SECID": attr['Код финансового инструмента'],
                "TILL": attr['Дата продажи'],
                "VOLUME": int(attr['Продано'])
            })
        portfolio = Moex().get_portfolio(request_payload)
        Portfolio.save_from_list(portfolio)
        return UploadTransfers(success=True)

class UploadDeals(graphene.Mutation):
    class Arguments:
        file = Upload(required=True)

    success = graphene.Boolean()

    def mutate(self, info, file, **kwargs):
        files = info.context.FILES
        deals = parse_file(files['0'])
        Deal.save_from_list(deals)
        return UploadTransfers(success=True)


class CreatePortfolio(graphene.Mutation):
    class Arguments:
        input = PortfolioInput(required=True)

    portfolio = graphene.Field(PortfolioType)

    @staticmethod
    def mutate(root, info, input=None):
        portfolio_instance = Portfolio(name=input.name)
        portfolio_instance.save()
        return CreatePortfolio(name=portfolio_instance)

class UploadSberbankReport(graphene.Mutation):
    class Arguments:
        file = Upload(required=True)

    success = graphene.Boolean()

    def mutate(self, info, file, **kwargs):
        files = info.context.FILES
        html = parse_file(files['0'])
        data = SberbankReport().parse_html(html)
        AccountReport.save_from_dict(data)
        return UploadSberbankReport(success=True)

class Mutation(graphene.ObjectType):
    create_author = CreatePortfolio.Field()
    upload_transfers = UploadTransfers.Field()
    upload_deals = UploadDeals.Field()
    upload_portfolio = UploadPortfolio.Field()
    upload_sberbank_report = UploadSberbankReport.Field()
