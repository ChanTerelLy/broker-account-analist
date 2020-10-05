import asyncio
import time

from django.http import JsonResponse
from django.shortcuts import render
from .models import CorpBound, Portfolio
from .helpers.service import Moex
import pandas as pd
from .forms import DealsUploadForm
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

def upload_deals(request):
    form = DealsUploadForm()
    if request.method == 'POST':
        form = DealsUploadForm(request.POST, request.FILES)
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
            Portfolio.save_portfolio(portfolio)
            return JsonResponse(portfolio, safe=False)

    return render(request, 'assets/upload_deals.html', {'form':form})

