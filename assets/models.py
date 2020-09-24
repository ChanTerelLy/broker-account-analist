from django.db import models
import uuid

class Modify(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Account(Modify):
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    amount = models.FloatField(default=0)

    def __repr__(self):
        return f'{self.name} - {self.amount}'

class Asset(Modify):
    full_name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=50, null=True, blank=True)
    isin = models.CharField(max_length=50)
    current_price = models.FloatField()
    buying_price = models.FloatField()
    current_return = models.FloatField()
    buying_return = models.FloatField()
    account = models.ManyToManyField(Account)

    def __repr__(self):
        return f'{self.short_name} - {self.current_return}'

class Deal(Modify):
    bound_id = models.ForeignKey(to=Asset, on_delete=models.CASCADE)
    account_id = models.ForeignKey(to=Account, on_delete=models.CASCADE)
    price = models.FloatField()
    transaction_number = models.IntegerField()
    service_fee = models.FloatField()
    currency = models.CharField(max_length=10)
    date = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=50, choices=[('Buy', 'Buy'), ('Sell', 'Sell')])

    @property
    def transaction_volume(self):
        return self.price * self.transaction_number

    def __repr__(self):
        return f'{self.type} - {self.price}'

class CorpBound(Modify):
    name = models.CharField(max_length=255, help_text='Полное наименование')
    short_name = models.CharField(max_length=255, help_text='Сокращенное наименование')
    isin = models.CharField(max_length=50)
    last_price = models.FloatField(null=True, blank=True, help_text='Цена последней сделки')
    assessed_return = models.FloatField(null=True, blank=True, help_text='Доход оценочный в %')
    maturity_date = models.DateTimeField(help_text='Дата погашения')
    coupon_date_return = models.DateTimeField(null=True, blank=True, help_text='Ближайшая дата выплаты купона')
    coupon_price = models.FloatField(null=True, blank=True, help_text='Размер купона')
    capitalization = models.IntegerField(null=True, blank=True, help_text='Оборот')
    coupon_duration = models.IntegerField(null=True, blank=True, help_text='Длительность купона')
    listing = models.IntegerField(choices=((1,1),(2,2),(3,3)), help_text='Листинг')
    demand_volume = models.IntegerField(null=True, blank=True, help_text='Общий спрос')
    duration = models.FloatField(null=True, blank=True, help_text='Дюрация')
    nkd = models.FloatField()
    tax_free = models.BooleanField(help_text='Свободна от уплаты налогов')