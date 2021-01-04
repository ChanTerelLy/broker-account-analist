from django.contrib import admin
from .models import *

admin.site.register(Account)
admin.site.register(Asset)
admin.site.register(Deal)
admin.site.register(Portfolio)
admin.site.register(Transfer)
