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

class Bound(Modify):
    full_name = models.CharField(max_length=255)
    short_name = models.CharField(max_length=50, null=True, blank=True)
    isin = models.CharField(max_length=50)
    current_price = models.FloatField()
    buying_price = models.FloatField()
    current_return = models.FloatField()
    buying_return = models.FloatField()
    account = models.ManyToManyField(Account)

class Deal(Modify):
    bound_id = models.ForeignKey(to=Bound, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=50)
    price = models.FloatField()