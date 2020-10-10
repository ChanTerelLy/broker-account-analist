from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.urls import path
from .views import *
urlpatterns = [
    path('update_bounds/', login_required(update_bounds), name='update_bounds'),
    path('assets/', login_required(assets), name='assets'),
    path('', login_required(assets), name='home'), #TODO:change to normal redirect
    path('upload_deals/', login_required(upload_agr_deals), name='upload_deals'),
    path('upload_transers/', login_required(upload_transers), name='upload_transers'),
]