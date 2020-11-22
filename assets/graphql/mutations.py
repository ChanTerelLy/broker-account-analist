import graphene

from .queries import PortfolioType
from ..helpers.service import Moex
from ..helpers.utils import parse_file
from ..models import Portfolio, Transfer, Deal
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
        transfers = list([dict(zip(transfers[0], c)) for c in transfers[1:]])
        Transfer.save_csv(transfers)
        return UploadTransfers(success=True)

class UploadPortfolio(graphene.Mutation):
    class Arguments:
        file = Upload(required=True)

    success = graphene.Boolean()

    def mutate(self, info, file, **kwargs):
        files = info.context.FILES
        portfolio = parse_file(files['0'])
        data = list([dict(zip(portfolio[0], c)) for c in portfolio[1:]])
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
        Portfolio.save_csv(portfolio)
        return UploadTransfers(success=True)

class UploadDeals(graphene.Mutation):
    class Arguments:
        file = Upload(required=True)

    success = graphene.Boolean()

    def mutate(self, info, file, **kwargs):
        files = info.context.FILES
        deals = parse_file(files['0'])
        deals = list([dict(zip(deals[0], c)) for c in deals[1:]])
        Deal.save_csv(deals)
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


class Mutation(graphene.ObjectType):
    create_author = CreatePortfolio.Field()
    upload_transfers = UploadTransfers.Field()
