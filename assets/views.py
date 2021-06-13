import asyncio

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import TemplateView, ListView
from .helpers.google_services import provides_credentials
from .models import *
from moex.helpers.service import Moex
import pandas as pd
from django.http import HttpResponse


@staff_member_required
def update_bounds(requests):
    moex = Moex()
    tax_free_bounds = moex.get_corp_bound_tax_free()
    corp_bounds = asyncio.run(moex.bounds())
    data = pd.merge(corp_bounds, tax_free_bounds, right_on='ISIN', left_on='SECID', how='left')
    CorpBound.objects.all().delete()
    for index, row in data.iterrows():
        tax_free = True if row['Эмитент'] else False
        # TODO:find out field match
        CorpBound.objects.create(
            name=row['EMITENTNAME'],
            isin=row['ISIN_x'],
            last_price=row['PRICE_RUB'],
            assessed_return=row['YIELDATWAP'],
            maturity_date=row['MATDATE'] or datetime.now(),
            coupon_date_return=row['MATDATE'],
            coupon_price=row['RTH1'],
            # capitalization=row[''],
            # coupon_duration=row[''],
            listing=row['LISTLEVEL'],
            # demand_volume=row[''],
            # duration=row[''],
            nkd=0,
            tax_free=tax_free,
        )
    return JsonResponse({'data': data.to_json()}, safe=False)


def assets(request):
    return render(request, 'assets/assets.html')


class MoexPortfolioView(TemplateView):
    template_name = 'assets/moex-portfolio.html'


class TransfersView(TemplateView):
    template_name = 'assets/transfers.html'


class DealsView(TemplateView):
    template_name = 'assets/deals.html'


class CorpBounView(ListView):
    template_name = 'assets/corp-bounds.html'
    model = CorpBound
    context_object_name = 'corp_bounds'
    paginate_by = 100

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['help_text'] = CorpBound.help_text_map_table
        return context


class ReportPortfolioView(TemplateView):
    template_name = 'assets/report-portfolio-sberbank.html'

class TinkoffPortfolioView(TemplateView):
    template_name = 'assets/portfolio-tinkoff.html'

class CouponsDividendsView(TemplateView):
    template_name = 'assets/coupons-dividends.html'

class VueTest(TemplateView):
    template_name = 'assets/test_vue.html'



@provides_credentials
def google_callback(request, *args, **kwargs):
    return HttpResponse('Auth complete!')
