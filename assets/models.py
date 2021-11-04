import json
import logging
import traceback

import jmespath
from django.db.models import UniqueConstraint, Window, Sum, F, Q, Case, When, Count
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from accounts.models import User
from django.db import models, transaction, IntegrityError
import uuid
from graphene.utils.str_converters import to_camel_case
from django.utils.decorators import method_decorator

from assets.helpers.service import TinkoffApi as tapi
from moex.helpers.service import Moex, Cbr
from assets.helpers.utils import dmYHM_to_date, xirr, weird_division, conver_to_number, get_value, dmY_to_date, \
    date_to_dmY


class Modify(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    @property
    def help_text_map(self):
        l = list([{to_camel_case(field.name): field.help_text} for field in self._meta.fields])
        l.append({'typeSum': 'Сумма с вычетами'})
        return json.dumps(l)

    @staticmethod
    def help_text_map_table(cls):
        return list([field.help_text for field in cls._meta.fields if field.help_text])

    @classmethod
    def help_text_map_resolver(cls):
        return {field.attname: field.help_text for field in cls._meta.fields if field.help_text}


class Account(Modify):
    name = models.CharField(max_length=255, help_text='Номер счета или название')
    description = models.TextField(null=True, blank=True, help_text='Описание')
    amount = models.FloatField(default=0, help_text='Итоговая сумма')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    broker_id = models.CharField(max_length=50, blank=True, null=True)

    @classmethod
    def get_with_reports(cls, **kwargs):
        return cls.objects.filter(**kwargs).exclude(accountreport__isnull=True)

    @classmethod
    def get_or_create_tinkoff_account(cls, **kwarg):
        account, _ = cls.objects.get_or_create(**kwarg, name='Tinkoff')
        return account

    def __str__(self):
        return f'{self.user} - {self.name} - {self.amount}'


class Deal(Modify):
    account = models.ForeignKey(to=Account, on_delete=models.CASCADE)
    number = models.CharField(max_length=50, help_text='Номер сделки')
    conclusion_date = models.DateTimeField(help_text='Дата заключения')
    settlement_date = models.DateTimeField(help_text='Дата расчётов')
    isin = models.CharField(max_length=50, help_text='Код финансового инструмента')
    type = models.CharField(max_length=50, help_text='Операция',
                            choices=[('Покупка', 'Покупка'), ('Продажа', 'Продажа')])
    amount = models.IntegerField(help_text='Количество')
    price = models.FloatField(help_text='Цена')
    price_rub = models.FloatField(help_text='Цена в рублях', default=0)
    nkd = models.FloatField(help_text='НКД')
    volume = models.FloatField(help_text='Объём сделки')
    currency = models.CharField(max_length=10, help_text='Валюта')
    service_fee = models.FloatField(help_text='Комиссия')

    @classmethod
    # @method_decorator(transaction.atomic, name='dispatch')
    def save_from_list(cls, deals):
        for deal in deals:
            account_income = Account.objects.filter(name=deal['Номер договора']).first()
            if not account_income:
                account_income = Account.objects.create(name=deal['Номер договора'])
            isin = deal.get('Код финансового инструмента')
            isin = isin if isin else deal.get('Код ЦБ')
            type = deal.get('Операция')
            type = type if type else deal.get('Вид')
            amount = deal.get('Количество')
            amount = amount if amount else deal.get('Количество, шт.')
            price = deal.get('Цена')
            price = price if price else conver_to_number(deal.get('Цена**'))
            volume = deal.get('Объём сделки')
            volume = volume if volume else conver_to_number(deal.get('Сумма'))
            Deal.objects.create(
                account=account_income,
                number=deal.get('Номер сделки'),
                conclusion_date=dmYHM_to_date(deal.get('Дата заключения')),
                settlement_date=dmYHM_to_date(deal.get('Дата расчётов')),
                isin=isin,
                type=type,
                amount=amount,
                price=price,
                nkd=deal.get('НКД'),
                volume=volume,
                currency=deal.get('Валюта'),
                service_fee=(deal.get('Комиссия') if deal.get('Комиссия') else 0),
            )

    @classmethod
    def convert_tinkoff_deal(cls, operation, account, figis):
        if Deal.objects.filter(account=account, number=operation.id).exists():
            return
        try:
            Deal.objects.create(
                account=account,
                number=operation.id,
                conclusion_date=operation.date,
                settlement_date=operation.date,
                isin=tapi.extract_figi(operation.figi, figis),
                type=tapi.resolve_operation_type(get_value(operation.operation_type)),
                amount=operation.quantity,
                price=conver_to_number(operation.price),
                nkd=0,
                volume=conver_to_number(operation.payment),
                currency=get_value(operation.currency),
                service_fee=conver_to_number(operation.commission.value)
            )
        except Exception as e:
            if isinstance(e, IntegrityError):
                logging.warning(e)
            else:
                logging.info(traceback.format_exc())

    @method_decorator(transaction.atomic)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    @property
    def transaction_volume(self):
        return self.price_rub * self.amount * (1 if self.type == 'Покупка' else -1)

    @property
    def transaction_amount(self):
        return self.amount * (1 if self.type == 'Покупка' else -1)


    @classmethod
    def get_balance_price(self, isins, accounts):
        values = []
        for isin in isins:
            aggr_deals = Deal.objects.filter(isin=isin, account__in=accounts).annotate(
                type_sum=Case(
                    When(type='Продажа', then=F('volume') * -1),
                    default=F('volume')
                ),
                amount_sum=Case(
                    When(type='Продажа', then=F('amount') * -1),
                    default=F('amount')
                ),
                nkd_sum=Case(
                    When(type='Покупка', then=F('nkd')),
                    default=0
                ),
                sum_volume=Window(
                    expression=Sum(F('type_sum')),
                ),
                sum_amount=Window(
                    expression=Sum(F('amount_sum'))
                ),
                sum_nkd=Window(
                    expression=Sum(F('nkd_sum'))
                )
            ).values('sum_volume', 'sum_amount', 'sum_nkd').distinct()
            aggr_deals = [i for i in aggr_deals]
            if aggr_deals:
                aggr_deals[0]['avg_price'] = int((aggr_deals[0]['sum_volume'] / aggr_deals[0]['sum_amount']))
                aggr_deals[0]['isin'] = isin
            values.append(aggr_deals)
        return values

    @property
    def volume_rub(self):
        return self.price_rub * self.amount * (-1 if self.type == 'Покупка' else 1)

    def update_price_rub(self):
        if self.currency != 'RUB':
            currency_value = Cbr(date_to_dmY(self.conclusion_date)).__getattr__(self.currency)
            self.price_rub = currency_value * self.price
        else:
            self.price_rub = self.price

    def validate_isin(self):
        if self.isin and len(str(self.isin)) < 12:
            isins = Moex().get_isin_by_name(self.isin)
            isins = jmespath.search(f"securities.data[?[1] == '{self.isin}'][05]", isins)
            if len(isins):
                self.isin = isins[0]

    def __str__(self):
        return f'{self.number} - {self.isin}'


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

    def __str__(self):
        return f'{self.short_name} - {self.assessed_return}'


class MoexPortfolio(Modify):
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

    @classmethod
    @method_decorator(transaction.atomic, name='dispatch')
    def save_from_list(cls, deals):
        for deal in deals:
            MoexPortfolio.objects.create(
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
                account=deal['account']
            )

    @method_decorator(transaction.atomic)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    class Meta:
        db_table = 'assets_moex_portfolio'


class AccountReport(models.Model):
    account = models.ForeignKey(Account, models.CASCADE)
    start_date = models.DateField(help_text='Дата начала отчета')
    end_date = models.DateField(help_text='Дата конца отчета')
    asset_estimate = models.JSONField(help_text='Оценка активов')
    iis_income = models.JSONField(help_text='Информация о зачислениях денежных средств на ИИС')
    portfolio = models.JSONField(help_text='Портфель Ценных Бумаг')
    money_flow = models.JSONField(help_text='Денежные средства')
    tax = models.JSONField(help_text='Расчет и удержание налога')
    handbook = models.JSONField(help_text='Справочник Ценных Бумаг')
    transfers = models.JSONField(help_text='Движение денежных средств за период', default=dict)
    deals = models.JSONField(help_text='Сделки купли/продажи ценных бумаг', default=dict)
    source = models.CharField(max_length=50, choices=(('sberbank', 'sberbank'), ('tinkoff', 'tinkoff')))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            UniqueConstraint(fields=['start_date', 'end_date', 'account_id'], name='unique_report')
        ]

    @classmethod
    def save_from_dict(cls, data, source):
        data['asset_estimate'] = json.dumps(data['asset_estimate'])
        data['portfolio'] = json.dumps(data['portfolio'])
        data['handbook'] = json.dumps(data['handbook'])
        data['money_flow'] = json.dumps(data['money_flow'])
        data['transfers'] = json.dumps(data['transfers'])
        data['iis_income'] = json.dumps(data['iis_income'])
        data['source'] = source
        try:
            cls.objects.create(**data)
        except Exception as e:
            if isinstance(e, IntegrityError):
                logging.error(e)
            else:
                logging.error(traceback.format_exc())

    @classmethod
    def save_from_tinkoff(cls, **kwargs):
        try:
            cls.objects.create(**kwargs)
        except Exception as e:
            logging.error(e)


class Transfer(Modify):
    TYPE_CHOICES = (('Ввод ДС', 'Ввод ДС'), ("Вывод ДС", "Вывод ДС"),
                    ('Списание комиссии', 'Списание комиссии'), ('Зачисление купона', 'Зачисление купона'),
                    ('Зачисление суммы от погашения ЦБ', 'Зачисление суммы от погашения ЦБ'),
                    ('Списание налогов', 'Списание налогов'),
                    ('Зачисление дивидендов', 'Зачисление дивидендов'),
                    ('Перевод между счетами', 'Перевод между счетами'))
    account_income = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='account_income',
                                       help_text='Зачисление на')
    account_charge = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='account_charge',
                                       help_text='Списание с', blank=True, null=True)
    date_of_application = models.DateTimeField(null=True, blank=True, help_text='Дата подачи поручения')
    execution_date = models.DateTimeField(null=True, blank=True, help_text='Дата исполнения поручения')
    type = models.CharField(max_length=50,
                            # choices=TYPE_CHOICES, TODO:automatic transliterate russian value
                            help_text='Операция')
    sum = models.FloatField(help_text='Сумма')
    sum_rub = models.FloatField(help_text='Сумма в рублях', default=0)
    currency = models.CharField(max_length=5, help_text='Валюта')
    description = models.CharField(max_length=255, help_text='Содержание операции', blank=True, null=True)
    status = models.CharField(max_length=50, help_text='Статус')
    transfer_id = models.CharField(max_length=50, blank=True, null=True, help_text='ID операции')
    report = models.ForeignKey(to=AccountReport, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['account_income', 'execution_date', 'type', 'sum', 'currency', 'transfer_id'],
                name='unique_transfer')
        ]

    @classmethod
    def convert_tinkoff_transfer(cls, operation, account, figis):
        if Transfer.objects.filter(account_income=account, transfer_id=operation.id).count():
            return
        figi = tapi.extract_figi(operation.figi, figis) if operation.figi else None
        descriptions = [figi, get_value(operation.instrument_type),
                        get_value(operation.operation_type)]
        try:
            Transfer.objects.create(
                account_income=account,
                date_of_application=operation.date,
                execution_date=operation.date,
                type=tapi.resolve_operation_type(get_value(operation.operation_type)),
                sum=conver_to_number(operation.payment) + conver_to_number(operation.commission),
                currency=get_value(operation.currency),
                description=' '.join(filter(None, descriptions)),
                status='Исполнено',
                transfer_id=operation.id
            )
        except Exception as e:
            if isinstance(e, IntegrityError):
                logging.warning(e)
            else:
                logging.info(traceback.format_exc())

    @property
    def type_sum(self):
        if self.type == self.TYPE_CHOICES[2][0]:
            return self.sum_rub * -1
        elif self.type == self.TYPE_CHOICES[5][0]:
            return self.sum_rub * -1
        elif self.type == self.TYPE_CHOICES[1][0]:
            return self.sum_rub * -1
        else:
            return self.sum_rub

    @classmethod
    @method_decorator(transaction.atomic, name='dispatch')
    def save_from_list(cls, transfers):
        for transfer in transfers:
            account_charge = Account.objects.none()  # TODO:add account instance
            account_income = Account.objects.filter(name=transfer['Номер договора']).first()
            execution_date = dmYHM_to_date(transfer.get('Дата исполнения поручения'))
            sum = transfer.get('Сумма')
            type = transfer.get('Операция')
            transfer_exist = Transfer.objects.filter(
                account_income=account_income,
                execution_date=execution_date,
                type=type,
                sum=sum
            ).count()
            if transfer_exist:
                continue
            if not account_income:
                account_income = Account.objects.create(name=transfer['Номер договора'])
            cls.objects.create(
                account_income=account_income,
                # account_charge=account_charge,
                date_of_application=dmYHM_to_date(transfer.get('Дата подачи поручения')),
                execution_date=execution_date,
                type=type,
                sum=sum,
                currency=transfer.get('Валюта операции'),
                description=transfer.get('Содержание операции'),
                status=transfer.get('Статус'),
            )

    @classmethod
    def save_from_sberbank_report(cls, rows: list, params):
        map = {
            # other
            'Перевод д/с для проведения расчетов по клирингу': 'Другое',
            'Сделка от': 'Другое',
            # commission
            'Списание комиссии': 'Списание комиссии',
            'Комиссия Биржи': 'Списание комиссии',
            'Комиссия Брокера': 'Списание комиссии',
            # outcome money
            'Перевод д/с': 'Вывод ДС',
            'Списание д/с': 'Вывод ДС',
            # income money
            'Зачисление купона': 'Зачисление купона',
            'Амортизация по': 'Зачисление суммы от погашения ЦБ',
            'Зачисление д/с (амортизация': 'Зачисление суммы от погашения ЦБ',
            'Зачисление д/с (купон': 'Зачисление купона',
            'Зачисление д/с': 'Ввод ДС',
        }
        if isinstance(rows, list):
            for row in rows[:-1]:
                type = [v for k, v in map.items() if row.get('Описание операции').startswith(k)]
                type = type[0] if type else 'Другое'
                date = dmY_to_date(row.get('Дата'))
                try:
                    cls.objects.create(
                        execution_date=date,
                        date_of_application=date,
                        type=type,
                        currency=row.get('Валюта'),
                        sum=abs(conver_to_number(row.get('Сумма зачисления')) - conver_to_number(
                            row.get('Сумма списания'))),
                        status='Исполнено',
                        description=row.get('Описание операции'),
                        account_income=params['account'],
                        report=params['report']
                    )
                except Exception as e:
                    logging.error(e)

    @property
    def xirr_sum(self):
        sum = self.sum_rub
        if self.type == self.TYPE_CHOICES[0][0]:
            sum = sum * -1
        return sum

    @classmethod
    def get_previous_sum_for_days(cls, user: User, **kwargs):
        result = []
        if kwargs.get('account_name'):
            accounts = Account.objects.filter(user=user, name=kwargs.get('account_name'))
        else:
            accounts = Account.objects.filter(user=user)
        for account in accounts:
            account_data = {'account_name': account.name, 'data': []}
            q = Q(type='Ввод ДС') | Q(type='Вывод ДС')
            transfers = cls.objects.filter(q, account_income=account).annotate(
                type_sum=Case(
                    When(type='Вывод ДС', then=F('sum_rub') * -1),
                    default=F('sum')
                ),
                SumAmount=Window(
                    Sum(F('type_sum')),
                    order_by=F('execution_date').asc())). \
                values('execution_date', 'SumAmount')
            data = list(
                [{'date': transfer['execution_date'], 'sum': transfer['SumAmount']} for transfer in transfers])
            account_data['data'] = data
            result.append(account_data)
        return result

    @staticmethod
    def get_sum_with_converted_currency(transfers, type):
        income_sum = transfers.filter(type=type).values('currency').annotate(sum=Sum('sum_rub'))
        total_sum = 0
        for sum in income_sum:
            total_sum += sum['sum']
        return total_sum

    def update_sum_rub(self):
        if self.currency != 'RUB':
            currency_value = Cbr(date_to_dmY(self.execution_date)).__getattr__(self.currency)
            self.sum_rub = currency_value * self.sum
        else:
            self.sum_rub = self.sum

    @method_decorator(transaction.atomic)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class Template(models.Model):
    name = models.CharField(max_length=250)
    description = models.TextField()
    url = models.URLField()
    key = models.CharField(max_length=25)


class MoneyManagerTransaction(Modify):
    account = models.ForeignKey(Account, models.CASCADE)
    type = models.CharField(max_length=50)
    sum = models.FloatField()
    mm_uid = models.UUIDField(unique=True)
    operation_date = models.DateField()

    @classmethod
    def save_from_rows(cls, rows, user):
        """
        :param rows: (NIC_NAME, ZCONTENT, WDATE, DO_TYPE, ZMONEY, I.uid)
        :return:
        """
        POSITIVE = [7, 4]
        NEGATIVE = [8, 3]
        for row in rows:
            account, _ = Account.objects.get_or_create(name=row[0], user=user)
            type = row[1]
            operation_date = row[2]
            sum = float(row[4]) * (-1 if int(row[3]) in NEGATIVE else 1)
            mm_uid = row[5]
            try:
                cls.objects.create(
                    account=account,
                    type=type,
                    operation_date=operation_date,
                    sum=sum,
                    mm_uid=mm_uid
                )
            except Exception as e:
                logging.error(e)


class AdditionalInvestmentIncome(Modify):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=50, choices=[('Налоговый вычет', 'nalog')])
    sum = models.FloatField()
    receipt_date = models.DateField()
    note = models.TextField(blank=True, null=True)


class IISIncome(Modify):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    report = models.ForeignKey(AccountReport, on_delete=models.CASCADE)
    operation_date = models.DateField()
    sum = models.FloatField()
    description = models.TextField()
    remainder_limit = models.FloatField()

    class Meta:
        constraints = [
            UniqueConstraint(fields=['operation_date', 'sum', 'account'], name='unique_iis_income')
        ]

    @classmethod
    def save_from_sberbank_report(cls, data, params):
        for income in data:
            try:
                cls(
                    account=params['account'],
                    report=params['report'],
                    operation_date=dmY_to_date(income['Дата операции']),
                    sum=conver_to_number(income['Сумма, руб.']),
                    description=income['Основание операции'],
                    remainder_limit=conver_to_number(income['Остаток лимита (сумма к внесению), руб.']),
                ).save()
            except Exception as e:
                logging.error(e)


# Signals
@receiver(post_save, sender=MoneyManagerTransaction)
def update_amount_accounts(sender, **kwargs):
    account = kwargs['instance'].account
    account.amount += kwargs['instance'].sum
    account.save()


@receiver(post_save, sender=AccountReport)
def update_transfers_from_sbr_report(sender, **kwargs):
    json_transfers = kwargs['instance'].transfers
    json_iis_income = kwargs['instance'].iis_income
    params = {}
    params['report'] = kwargs['instance']
    params['account'] = kwargs['instance'].account
    if json_transfers:
        json_transfers = json.loads(json_transfers)
        Transfer.save_from_sberbank_report(json_transfers, params)
    if json_iis_income:
        json_iis_income = json.loads(json_iis_income)
        IISIncome.save_from_sberbank_report(json_iis_income, params)


@receiver(pre_save, sender=Deal)
def update_deal_price_rub(sender, **kwargs):
    deal = kwargs['instance']
    deal.update_price_rub()
    logging.info(f'{deal.number} was updated')


@receiver(pre_save, sender=Transfer)
def update_transfer_sum_rub(sender, **kwargs):
    transfer = kwargs['instance']
    transfer.update_sum_rub()
    logging.info(f'{transfer.description} was updated')

@receiver(pre_save, sender=Deal)
def check_isin(sender, **kwargs):
    deal = kwargs['instance']
    deal.validate_isin()