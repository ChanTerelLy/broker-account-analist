import graphene

from .queries import PortfolioType
from ..models import Portfolio


class PortfolioInput(graphene.InputObjectType):
    id = graphene.ID()
    name = graphene.String()


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
