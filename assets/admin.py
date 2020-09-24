from django.contrib import admin
from .models import Account, Asset, Deal
from django.template.response import TemplateResponse
from django.urls import path

admin.site.register(Account)
admin.site.register(Asset)
admin.site.register(Deal)
