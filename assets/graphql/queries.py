import graphene
from graphene_django.types import DjangoObjectType, ObjectType

from ..models import *

class AccountType(DjangoObjectType):
    class Meta:
        model = Account
        fields = ('__all__')

class PortfolioType(DjangoObjectType):
    class Meta:
        model = Portfolio
        fields = ('__all__')


class Query(ObjectType):
    portfolios = graphene.List(PortfolioType)

    def resolve_portfolios(self, info, **kwargs):
        return Portfolio.objects.all()
