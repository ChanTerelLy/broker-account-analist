import graphene
from graphene import relay, ObjectType
from graphene.utils.str_converters import to_camel_case
from graphene_django import DjangoObjectType

from assets.helpers.utils import convert_devided_number
from assets.models import Account, MoexPortfolio, Transfer, Deal, Template
from graphene_django.types import DjangoObjectType

class AccountNode(DjangoObjectType):
    class Meta:
        model = Account
        fields = ('__all__')
        filter_fields = ['id', ]
        interfaces = (relay.Node,)


class PortfolioType(DjangoObjectType):
    help_text_map = graphene.String()

    class Meta:
        model = MoexPortfolio
        fields = ('__all__')
        interfaces = (relay.Node,)


class TransferType(DjangoObjectType):
    help_text_map = graphene.String()
    type_sum = graphene.Float()

    class Meta:
        model = Transfer
        fields = ('__all__')
        interfaces = (relay.Node,)


class ChoicesPropertyEnum(graphene.Enum):
    BUY = "Покупка"
    SELL = "Продажа"


class DealsType(DjangoObjectType):
    help_text_map = graphene.String()
    transaction_volume = graphene.Int()
    volume_rub = graphene.Int()

    class Meta:
        model = Deal
        fields = "__all__"


class TemplateType(DjangoObjectType):
    class Meta:
        model = Template
        fields = ('__all__')
        interfaces = (relay.Node,)


class XirrType(ObjectType):
    account_name = graphene.String()
    avg_percent = graphene.Float()
    total_percent = graphene.Float()
    earn_sum = graphene.Float()


class ReportData(ObjectType):
    date = graphene.Date()
    sum = graphene.Float()
    income_sum = graphene.Float()


class ReportType(ObjectType):
    account_name = graphene.String()
    data = graphene.List(ReportData)


class PortfolioReportType(ObjectType):
    name = graphene.String()
    isin = graphene.String()
    currency = graphene.String()
    start_amount = graphene.Int()
    start_denomination = graphene.Int()
    start_market_total_sum = graphene.Float()
    start_market_total_sum_without_nkd = graphene.Float()
    start_nkd = graphene.Float()
    end_amount = graphene.Int()
    end_denomination = graphene.Int()
    end_market_total_sum = graphene.Float()
    end_market_total_sum_without_nkd = graphene.Float()
    end_nkd = graphene.Float()
    changes_amount = graphene.Int()
    changes_total_sum = graphene.Float()
    scheduled_enrolment_amount = graphene.Int()
    scheduled_charges_amount = graphene.Int()
    scheduled_outbound_amount = graphene.Int()
    account = graphene.String()
    coupon_percent = graphene.Float()
    coupon_date = graphene.Date()
    purchase_coupon_percent = graphene.Float()
    real_price = graphene.Float()

    @classmethod
    def convert_name_for_dict(cls, data):
        return {cls.convert_names(key): convert_devided_number(value) for key, value in data.items()}

    @classmethod
    def get_map(cls):
        return {'Аккаунт': 'account', 'Наименование': 'name', 'ISIN ценной бумаги': 'isin',
                'Валюта рыночной цены': 'currency',
                'Количество, шт (Начало Периода)': 'start_amount', 'Номинал (Начало Периода)': 'start_denomination',
                'Рыночная цена  (Начало Периода)': 'start_market_total_sum',
                'Рыночная стоимость, без НКД (Начало Периода)': 'start_market_total_sum_without_nkd',
                'НКД (Начало Периода)': 'start_nkd', 'Количество, шт (Конец Периода)': 'end_amount',
                'Номинал (Конец Периода)': 'end_denomination',
                'Рыночная цена  (Конец Периода)': 'end_market_total_sum',
                'Рыночная стоимость, без НКД (Конец Периода)': 'end_market_total_sum_without_nkd',
                'НКД (Конец Периода)': 'end_nkd', 'Количество, шт (Изменение за период)': 'changes_amount',
                'Рыночная стоимость (Изменение за период)': 'changes_total_sum',
                'Плановые зачисления по сделкам, шт': 'scheduled_enrolment_amount',
                'Плановые списания по сделкам, шт': 'scheduled_charges_amount',
                'Плановый исходящий остаток, шт': 'scheduled_outbound_amount',
                'Процент купона': 'coupon_percent',
                'Дата выплаты ближайшего купона': 'coupon_date',
                'Средний % купона покупки': 'purchase_coupon_percent',
                'Текущая стоимость': 'real_price'
                }

    @classmethod
    def convert_names(cls, field):
        map = cls.get_map()
        return map.get(field)


class PortfolioReportMapType(ObjectType):
    map = graphene.JSONString()
    data = graphene.List(PortfolioReportType)

    def resolve_map(self, *args):
        return {key: to_camel_case(value) for key, value in PortfolioReportType.get_map().items()}


class TinkoffPrice(ObjectType):
    currency = graphene.String()
    value = graphene.Float()


class TinkoffPortfolioType(ObjectType):
    name = graphene.String()
    average_position_price = graphene.Int()
    average_position_price_no_nkd = graphene.Int()
    balance = graphene.Int()
    blocked = graphene.Int()
    expected_yield = graphene.Int()
    figi = graphene.String()
    instrument_type = graphene.String()
    isin = graphene.String()
    lots = graphene.Int()
    ticker = graphene.String()
    currency = graphene.String()
    start_market_total_sum_without_nkd = graphene.Int()
    usd_price = graphene.Float()
    euro_price = graphene.Float()

    def resolve_average_position_price(self, info, *args):
        return self.average_position_price.get('value')

    def resolve_average_position_price_no_nkd(self, info):
        return self.average_position_price_no_nkd.get('value') if self.average_position_price_no_nkd else None

    def resolve_expected_yield(self, info):
        price = self.expected_yield.get('value') if self.expected_yield else 0
        if self.currency == 'USD' and self.instrument_type != 'Currency':
            price *= self.usd_price
        if self.currency == 'EUR' and self.instrument_type != 'Currency':
            price *= self.euro_price
        return price

    def resolve_start_market_total_sum_without_nkd(self, info):
        expected_yield = self.expected_yield.get('value') if self.expected_yield else 0
        price = self.average_position_price.get('value') * self.balance + expected_yield
        if self.currency == 'USD' and self.instrument_type != 'Currency':
            price *= self.usd_price
        if self.currency == 'EUR' and self.instrument_type != 'Currency':
            price *= self.usd_price
        return price


    @staticmethod
    def joined_value(value):
        if value:
            amount = "{:10.1f}".format(value['value']) if value['value'] else ''
            return amount + ' ' + value['currency']
        else:
            return ''

    @staticmethod
    def get_map():
        return {
            'Наименование': "name",
            'Средняя цена покупки': "average_position_price",
            'Средняя цена покупки (без НКД)': "average_position_price_no_nkd",
            'Баланс': "balance",
            'Заблокировано': "blocked",
            'Ликвидационная доходность': "expected_yield",
            'FIGI': "figi",
            'Тип инструмента': "instrument_type",
            'ISIN': "isin",
            'Колличество': "lots",
            'Тикер': "ticker",
            'Валюта': "currency",
            'Ликвидационная сумма': "start_market_total_sum_without_nkd"
        }


class TinkoffPortfolioMapType(ObjectType):
    map = graphene.JSONString()
    data = graphene.List(TinkoffPortfolioType)

    def resolve_map(self, *args):
        return {key: to_camel_case(value) for key, value in TinkoffPortfolioType.get_map().items()}


class PortfolioInput(graphene.InputObjectType):
    id = graphene.ID()
    name = graphene.String()

class CouponAggregated(ObjectType):
    date = graphene.Date()
    sum = graphene.Float()

class IISIncomeAggregated(ObjectType):
    year = graphene.Int()
    sum = graphene.Float()

class CouponAverage(ObjectType):
    year = graphene.Int()
    month_count = graphene.Int()
    sum = graphene.Int()
    avg_month = graphene.Int()