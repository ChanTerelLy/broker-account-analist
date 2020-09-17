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
    name = models.CharField(max_length=255)
    isin = models.CharField(max_length=50)
    last_price = models.FloatField(null=True, blank=True)
    assessed_return = models.FloatField(null=True, blank=True)
    maturity_date = models.DateTimeField()
    coupon_date_return = models.DateTimeField(null=True, blank=True)
    coupon_price = models.FloatField(null=True, blank=True)
    capitalization = models.IntegerField(null=True, blank=True)
    coupon_duration = models.IntegerField(null=True, blank=True)
    listing = models.IntegerField(choices=((1,1),(2,2),(3,3)))
    demand_volume = models.IntegerField(null=True, blank=True)
    duration = models.FloatField(null=True, blank=True)
    tax_free = models.BooleanField()
