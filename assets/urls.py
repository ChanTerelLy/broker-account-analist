from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.urls import path
from django.views.generic import RedirectView

from .views import *
urlpatterns = [
    path('', login_required(assets), name='home'),
    path('assets/', login_required(assets), name='assets'),

    # Data Model views
    path('moex-portfolio/', login_required(MoexPortfolioView.as_view()), name='moex-portfolio'),
    path('transfers/', login_required(TransfersView.as_view()), name='transfers'),
    path('deals/', login_required(DealsView.as_view()), name='deals'),
    path('portfolio/', login_required(ReportPortfolioView.as_view()), name='portfolio'),
    path('coupons-dividends/', login_required(CouponsDividendsView.as_view()), name='coupons-dividends'),

    # Moex operations
    path('update-bounds/', login_required(update_bounds), name='update-bounds'),
    path('corp-bounds/', login_required(CorpBounView.as_view()), name='corp-bounds'),

    # other
    path('google-callback/', google_callback, name='google-callback'),
    path('sentry-debug/', trigger_error),
]