import asyncio

from django.http import JsonResponse
from django.shortcuts import render
from .models import CorpBound
from .v1.service import Moex
import pandas as pd
# Create your views here.

def update_bounds(requests):
    moex = Moex()
    tax_free_bounds = moex.get_corp_bound_tax_free()
    corp_bounds = asyncio.run(moex.bounds())
    data = pd.merge(corp_bounds, tax_free_bounds, right_on='ISIN', left_on='SECID', how='left')
    CorpBound.objects.all().delete()
    for index, row in data.iterrows():
        tax_free = True if row['Эмитент'] else False
        CorpBound.objects.create(
            name=row['EMITENTNAME'],
            isin=row['ISIN_x'],
            last_price=row['PRICE_RUB'],
            assessed_return=row['YIELDATWAP'],
            maturity_date=row['MATDATE'],
            coupon_date_return=row['MATDATE'],
            coupon_price=row['RTH1'],
            # capitalization=row[''],
            # coupon_duration=row[''],
            listing=row['LISTLEVEL'],
            # demand_volume=row[''],
            # duration=row[''],
            tax_free= tax_free,
        )
    return JsonResponse({'data': data.to_json()}, safe=False)

def calculate_portfolio(request):
    if request.method == "POST":
        data = request.body
        moex = Moex().get_portfolio(data)
        return JsonResponse({'data' : moex[1]['portfolio']})

def assets(request):
    return render(request, 'assets/assets.html')