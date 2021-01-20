from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.urls import path
from .views import *
urlpatterns = [
    path('update-bounds/', login_required(update_bounds), name='update_bounds'),
    path('assets/', login_required(assets), name='assets'),
    path('', login_required(assets), name='home'), #TODO:change to normal redirect
    path('moex-portfolio/', login_required(PortfolioView.as_view()), name='portfolio'),
    path('transfers/', login_required(TransfersView.as_view()), name='transfers'),
    path('deals/', login_required(DealsView.as_view()), name='deals'),
    path('corp-bounds/', login_required(CorpBounView.as_view()), name='corp-bounds'),
    path('report-portfolio/', login_required(ReportPortfolioView.as_view()), name='report-portfolio'),
    path('update-bounds/', login_required(update_bounds), name='update-bounds'),
    path('google-callback/', google_callback, name='google-callback'),
]