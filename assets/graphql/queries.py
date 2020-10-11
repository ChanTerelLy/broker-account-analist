import graphene
from graphene import relay
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType, ObjectType

from ..models import *

class AccountNode(DjangoObjectType):
    class Meta:
        model = Account
        fields = ('__all__')
        filter_fields = ['id', ]
        interfaces = (relay.Node, )

class PortfolioNode(DjangoObjectType):
    help_text_map = graphene.JSONString()

    class Meta:
        model = Portfolio
        fields = ('__all__')
        filter_fields = ['id', ]
        interfaces = (relay.Node,)


class Query(ObjectType):
    account = relay.Node.Field(AccountNode)
    my_accounts = DjangoFilterConnectionField(AccountNode)
    my_portfolio = DjangoFilterConnectionField(PortfolioNode)

    def resolve_my_accounts(self, info):
        # context will reference to the Django request
        if not info.context.user.is_authenticated:
            return Account.objects.none()
        else:
            return Account.objects.filter(user=info.context.user)

    def resolve_my_portfolio(self, info):
        # context will reference to the Django request
        if not info.context.user.is_authenticated:
            return Portfolio.objects.none()
        else:
            return Portfolio.objects.filter(account__user=info.context.user)
