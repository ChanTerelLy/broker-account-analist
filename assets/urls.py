from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.urls import path
from .views import *
urlpatterns = [
    path('update_bounds/', login_required(update_bounds), name='update_bounds'),
    path('assets/', login_required(assets), name='assets'),
    path('', login_required(assets), name='home'), #TODO:change to normal redirect
    path('deals/', login_required(upload_agr_deals), name='portfolio'),
    path('transfers/', login_required(upload_transers), name='transfers'),
    path('corp-bounds/', login_required(update_bounds), name='corp-bounds'),
]