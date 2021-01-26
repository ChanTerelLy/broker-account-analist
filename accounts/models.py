from django.db import models

# Create your models here.

from django.contrib.auth.models import AbstractUser, User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    google_service_token = models.JSONField(default=dict)
    tinkoff_token = models.CharField(max_length=255, blank=True, null=True)