import graphene
from graphene_django.types import DjangoObjectType, ObjectType

from ..models import Portfolio


class PortfolioType(DjangoObjectType):
    class Meta:
        model = Portfolio


class Query(ObjectType):
    portfolios = graphene.List(PortfolioType)

    def resolve_portfolios(self, info, **kwargs):
        return Portfolio.objects.all()
