import asyncio
import time

from django.http import JsonResponse
from django.shortcuts import render
from django.views.generic import TemplateView, ListView

from .models import *
from .helpers.service import Moex
import pandas as pd
from .forms import UploadFile, UploadTransferFile
# Create your views here.
from .helpers.utils import parse_file


def update_bounds(requests):
    moex = Moex()
    tax_free_bounds = moex.get_corp_bound_tax_free()
    corp_bounds = asyncio.run(moex.bounds())
    data = pd.merge(corp_bounds, tax_free_bounds, right_on='ISIN', left_on='SECID', how='left')
    CorpBound.objects.all().delete()
    for index, row in data.iterrows():
        tax_free = True if row['Эмитент'] else False
        #TODO:find out field match
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
            tax_free= tax_free,
        )
    return JsonResponse({'data': data.to_json()}, safe=False)


def assets(request):
    return render(request, 'assets/assets.html')

def upload_portfolio(request):
    form = UploadFile()
    fields = Portfolio._meta._get_fields()
    help_text = []
    for field in fields:
        help_text.append(field.help_text)
    portfolio = Portfolio.objects.filter(account__user=request.user).all()
    if request.method == 'POST':
        form = UploadFile(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['file']
            data = parse_file(file)
            request_payload = []
            data = list([dict(zip(data[0], c)) for c in data[1:]])
            for attr in data:
                request_payload.append({
                    "DIVIDENDS" : [],
                    "FROM": attr['Дата покупки'],
                    "SECID": attr['Код финансового инструмента'],
                    "TILL": attr['Дата продажи'],
                    "VOLUME": int(attr['Продано'])
                })
            #load data from moex
            portfolio = Moex().get_portfolio(request_payload)
            #write to database
            Portfolio.save_csv(portfolio)
            return JsonResponse(portfolio, safe=False)

    return render(request, 'assets/upload_porfolio.html', {'form':form})

class PortfolioView(TemplateView):
    template_name = 'assets/portfolio.html'

class CorpBounView(ListView):
    template_name = 'assets/corp-bounds.html'
    model = CorpBound
    context_object_name = 'corp_bounds'
    paginate_by = 100

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # Add in the publisher
        context['help_text'] = CorpBound.objects.first().help_text_map
        return context


def upload_transers(requests):
    form = UploadTransferFile(user=requests.user)
    if requests.method == 'POST':
        form = UploadTransferFile(requests.POST, requests.FILES)
        if form.is_valid():
            file = requests.FILES['file']
            transfers = parse_file(file)
            transfers = list([dict(zip(transfers[0], c)) for c in transfers[1:]])
            Transfer.save_csv(transfers, form)
    return render(requests, 'assets/upload_transfers.html', {'form' : form})
