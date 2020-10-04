from django.conf.urls import url
from django.urls import path
from .views import *
urlpatterns = [
    path('update_bounds/', update_bounds, name='update_bounds'),
    path('assets/', assets, name='assets'),
    path('upload_deals/', upload_deals, name='upload_deals'),
]