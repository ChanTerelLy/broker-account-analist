from django.contrib.auth.models import User
from django.db import models, transaction
import uuid

from graphene.utils.str_converters import to_camel_case
from toolz import curry

from django.utils.decorators import method_decorator

from assets.helpers.utils import dmYHM_to_date


class Modify(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Account(Modify):
    name = models.CharField(max_length=255, help_text='Номер счета или название')
    description = models.TextField(null=True, blank=True, help_text='Описание')
    amount = models.FloatField(default=0, help_text='Итоговая сумма')
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.user} - {self.name} - {self.amount}'


class Asset(Modify):
    full_name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=50, null=True, blank=True)
    isin = models.CharField(max_length=50)
    current_price = models.FloatField()
    buying_price = models.FloatField()
    current_return = models.FloatField()
    buying_return = models.FloatField()
    account = models.ManyToManyField(Account)

    def __str__(self):
        return f'{self.short_name} - {self.current_return}'


class Deal(Modify):
    bound_id = models.ForeignKey(to=Asset, on_delete=models.CASCADE, null=True, blank=True)
    account_id = models.ForeignKey(to=Account, on_delete=models.CASCADE)
    price = models.FloatField()
    transaction_number = models.IntegerField()
    service_fee = models.FloatField()
    currency = models.CharField(max_length=10)
    date = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=50, choices=[('Покупка', 'Покупка'), ('Продажа', 'Продажа')])

    @property
    def transaction_volume(self):
        return self.price * self.transaction_number

    def __str__(self):
        return f'{self.type} - {self.price}'


class CorpBound(Modify):
    name = models.CharField(max_length=255, help_text='Полное наименование')
    short_name = models.CharField(max_length=255, help_text='Сокращенное наименование')
    isin = models.CharField(max_length=50, help_text='ISIN')
    last_price = models.FloatField(null=True, blank=True, help_text='Цена последней сделки')
    assessed_return = models.FloatField(null=True, blank=True, help_text='Доход оценочный в %')
    maturity_date = models.DateTimeField(help_text='Дата погашения')
    coupon_date_return = models.DateTimeField(null=True, blank=True, help_text='Ближайшая дата выплаты купона')
    coupon_price = models.FloatField(null=True, blank=True, help_text='Размер купона')
    capitalization = models.IntegerField(null=True, blank=True, help_text='Оборот')
    coupon_duration = models.IntegerField(null=True, blank=True, help_text='Длительность купона')
    listing = models.IntegerField(choices=((1, 1), (2, 2), (3, 3)), help_text='Листинг')
    demand_volume = models.IntegerField(null=True, blank=True, help_text='Общий спрос')
    duration = models.FloatField(null=True, blank=True, help_text='Дюрация')
    nkd = models.FloatField(help_text='НКД')
    tax_free = models.BooleanField(help_text='Свободна от уплаты налогов')

    @property
    def help_text_map(self):
        return list([field.help_text for field in self._meta.fields if field.help_text])

    def __str__(self):
        return f'{self.short_name} - {self.assessed_return}'


class Portfolio(Modify):
    buycloseprice = models.FloatField(help_text='Цена закрытия в дату покупки, в рублях', null=True, blank=True)
    buysum = models.FloatField(help_text='Сумма покупки', null=True, blank=True)
    cashflow = models.FloatField(help_text='Купоны/ дивиденды', null=True, blank=True)
    earnings = models.FloatField(help_text='Доход', null=True, blank=True)
    error = models.TextField(null=True, blank=True)
    from_date = models.DateField(help_text='Дата покупки', null=True, blank=True)
    secid = models.CharField(help_text="Инструмент", max_length=255)
    sellcloseprice = models.FloatField(help_text='Цена закрытия в дату продажи, в рублях', null=True, blank=True)
    sellsum = models.FloatField(help_text='Сумма продажи', null=True, blank=True)
    till_date = models.DateField(help_text='Дата продажи', null=True, blank=True)
    volume = models.IntegerField(help_text='Количество бумаг', null=True, blank=True)
    yield_percent = models.FloatField(help_text='Внутр. ставка доходности', null=True, blank=True)
    account = models.ForeignKey(Account, related_name='account', on_delete=models.CASCADE, help_text='Аккаунт')

    def __str__(self):
        return f'{self.secid} - {self.earnings}'

    @property
    def help_text_map(self):
        return list([{to_camel_case(field.name) : field.help_text} for field in self._meta.fields])

    def _get_help_text(self, field_name):
        """Given a field name, return it's help text."""
        for field in self._meta.fields:
            if field.name == field_name:
                return field.help_text

    def __init__(self, *args, **kwargs):
        # Call the superclass first; it'll create all of the field objects.
        super(Portfolio, self).__init__(*args, **kwargs)

        # Again, iterate over all of our field objects.
        for field in self._meta.fields:
            # Create a string, get_FIELDNAME_help text
            method_name = "get_{0}_help_text".format(field.name)

            # We can use curry to create the method with a pre-defined argument
            curried_method = curry(self._get_help_text, field_name=field.name)

            # And we add this method to the instance of the class.
            setattr(self, method_name, curried_method)

    @classmethod
    @method_decorator(transaction.atomic, name='dispatch')
    def save_csv(cls, deals):
        for deal in deals:
            Portfolio.objects.create(
                buycloseprice=deal['BUYCLOSEPRICE'],
                buysum=deal['BUYSUM'],
                cashflow=deal['CASHFLOW'],
                earnings=deal['EARNINGS'],
                error=deal['ERROR'],
                from_date=deal['FROM'],
                secid=deal['SECID'],
                sellcloseprice=deal['SELLCLOSEPRICE'],
                sellsum=deal['SELLSUM'],
                till_date=deal['TILL'],
                volume=deal['VOLUME'],
                yield_percent=deal['YIELD'],
            )

    @method_decorator(transaction.atomic)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

class Transfer(Modify):
    account_income = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='account_income', help_text='Зачисление на')
    account_charge = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='account_charge',
                                       help_text='Списание с', blank=True, null=True)
    date_of_application = models.DateTimeField(null=True, blank=True, help_text='Дата подачи поручения')
    execution_date = models.DateTimeField(null=True, blank=True, help_text='Дата исполнения поручения')
    type = models.CharField(max_length=50, choices=(('Ввод ДС', 'Ввод ДС'),("Вывод ДС", "Вывод ДС"),
                                     ('Списание комиссии', 'Списание комиссии'),('Зачисление купона','Зачисление купона'),
                                     ('Зачисление суммы от погашения ЦБ', 'Зачисление суммы от погашения ЦБ'),
                                     ('Списание налогов', 'Списание налогов'),
                                     ('Зачисление дивидендов', 'Зачисление дивидендов'),
                                     ('Перевод между счетами', 'Перевод между счетами')), help_text='Операция')
    sum = models.FloatField(help_text='Сумма')
    currency = models.CharField(max_length=5, help_text='Валюта')
    description = models.CharField(max_length=255, help_text='Содержание операции', blank=True, null=True)
    status = models.CharField(max_length=50, help_text='Статус')

    @classmethod
    @method_decorator(transaction.atomic, name='dispatch')
    def save_csv(cls, transfers, form):
        account_income_id = form['account_income'].value()[0]
        account_charge_id = form['account_charge'].value()[0] if form['account_charge'].value() else None
        for transfer in transfers:
            Transfer.objects.create(
                account_income=Account.objects.filter(id=account_income_id).first(),
                account_charge=Account.objects.filter(id=account_charge_id).first(),
                date_of_application=dmYHM_to_date(transfer['Дата подачи поручения']),
                execution_date=dmYHM_to_date(transfer['Дата исполнения поручения']),
                type=transfer['Операция'],
                sum=transfer['Сумма'],
                currency=transfer['Валюта операции'],
                description=transfer['Содержание операции'],
                status=transfer['Статус'],
            )

    @method_decorator(transaction.atomic)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)