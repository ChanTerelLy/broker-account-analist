import graphene
from graphene import relay
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType, ObjectType
import pandas as pd
from ..models import *
from assets.helpers.utils import dmYHM_to_date, xirr, get_total_xirr_percent
from django.db.models import Sum


class AccountNode(DjangoObjectType):
    class Meta:
        model = Account
        fields = ('__all__')
        filter_fields = ['id', ]
        interfaces = (relay.Node,)


class PortfolioType(DjangoObjectType):
    help_text_map = graphene.String()

    class Meta:
        model = Portfolio
        fields = ('__all__')
        interfaces = (relay.Node,)


class TransferType(DjangoObjectType):
    help_text_map = graphene.String()
    type_sum = graphene.Float()

    class Meta:
        model = Transfer
        fields = ('__all__')
        interfaces = (relay.Node,)


class DealsType(DjangoObjectType):
    help_text_map = graphene.String()
    transaction_volume = graphene.Int()

    class Meta:
        model = Deal
        fields = ('__all__')
        interfaces = (relay.Node,)

class XirrType(ObjectType):
    account_name = graphene.String()
    avg_percent = graphene.Float()
    total_percent = graphene.Float()


class Query(ObjectType):
    account = relay.Node.Field(AccountNode)
    my_accounts = DjangoFilterConnectionField(AccountNode)
    my_portfolio = graphene.List(PortfolioType)
    my_transfers = graphene.List(TransferType)
    my_deals = graphene.List(DealsType)
    account_chart = graphene.JSONString()
    my_transfer_xirr = graphene.List(XirrType)

    def resolve_my_accounts(self, info):
        # context will reference to the Django request
        if not info.context.user.is_authenticated:
            return Account.objects.none()
        else:
            return Account.objects.filter(user=info.context.user)

    def resolve_my_portfolio(self, info):
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
        # context will reference to the Django request
        if not info.context.user.is_authenticated:
            return Deal.objects.none()
        else:
            return Deal.objects.filter(account__user=info.context.user).all()

    def resolve_account_chart(self, info) -> dict:
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
